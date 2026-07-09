#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const args = parseArgs(process.argv.slice(2));
const scriptPath = args.script;
const outPath = args.out;
const maxChars = Number(args["max-chars"] || 17);

if (!scriptPath || !outPath) {
  console.error("Usage: node scripts/optimize_line_breaks.mjs --script input.txt --out output.txt --max-chars 17");
  process.exit(1);
}

const rawLines = fs.readFileSync(scriptPath, "utf8")
  .split(/\r?\n/)
  .map((line) => normalizeLine(line))
  .filter(Boolean);

const optimized = [];
const splitEvents = [];
const tokenBoundaryMap = buildTokenBoundaryMap(rawLines);

for (const [index, line] of rawLines.entries()) {
  const parts = splitLongLine(line, maxChars, tokenBoundaryMap.get(line));
  if (parts.length > 1) splitEvents.push({ sourceIndex: index + 1, source: line, parts });
  optimized.push(...parts);
}

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, optimized.join("\n") + "\n");

const qaPath = outPath.replace(/\.[^.]+$/, "") + ".qa.json";
const qa = buildQa(rawLines, optimized, splitEvents, maxChars);
fs.writeFileSync(qaPath, JSON.stringify(qa, null, 2));

console.log(JSON.stringify({
  out: path.resolve(outPath),
  qa: path.resolve(qaPath),
  sourceLines: rawLines.length,
  outputLines: optimized.length,
  splitLines: splitEvents.length,
  maxChars: qa.maxChars,
  overMax: qa.overMax.length,
}, null, 2));

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) out[key] = true;
    else out[key] = next, i++;
  }
  return out;
}

function normalizeLine(line) {
  return line
    .trim()
    .replace(/[\p{P}\p{S}]/gu, "")
    .replace(/\s+/g, "");
}

function visibleLen(text) {
  return [...text].length;
}

function splitLongLine(line, maxLen, tokenBoundaries) {
  if (visibleLen(line) <= maxLen) return [line];
  const known = splitByKnownPattern(line, maxLen);
  if (known) return known;

  const chars = [...line];
  const parts = [];
  let rest = chars.join("");

  while (visibleLen(rest) > maxLen) {
    const restBoundaries = tokenBoundaries ? offsetBoundaries(tokenBoundaries, visibleLen(line) - visibleLen(rest)) : null;
    const cut = chooseCut(rest, maxLen, restBoundaries);
    const head = [...rest].slice(0, cut).join("");
    const tail = [...rest].slice(cut).join("");
    if (!head || !tail) break;
    parts.push(head);
    rest = tail;
  }

  if (rest) parts.push(rest);
  return parts.flatMap((part) => visibleLen(part) > maxLen ? hardSplit(part, maxLen) : [part]);
}

function splitByKnownPattern(line, maxLen) {
  const patterns = [
    /^(让豆包给你总结出精髓)(或者.+)$/u,
    /^(这会让你直接从一个)(.+)$/u,
    /^(这种测试在你们刚认识)(或者.+)$/u,
    /^(甚至迫不及待的向她保证)(.+)$/u,
    /^(她的潜意识里其实是希望)(.+)$/u,
    /^(当女人用审视的眼光)(问你.+)$/u,
    /^(这种测试简直就是检验)(一个男人是主导者)(还是.+)$/u,
    /^(你要像一个冷静的商人一样)(提出.+)$/u,
    /^(你一定要学会像一个)(冷静.+)$/u,
    /^(如果你真的因为)(她这.+)$/u,
    /^(你就自动把自己放到了一个)(.+)$/u,
    /^(如果你自己的情况已经不是)(.+)$/u,
    /^(这种测试在表面上看起来)(和.+)$/u,
    /^(你觉得这是展现自己深情)(和.+)$/u,
    /^(或者你热衷于去陪伴女生)(度过.+)$/u,
    /^(往往不会把那个一直见证)(她狼狈的人)(当成.+)$/u,
    /^(很多直男一看到这种)(把.+)$/u,
    /^(但往往也是那些缺乏自信的)(.+)$/u,
    /^(你会把几年时间押在一句)(没有.+)$/u,
    /^(如果你在现实中总是)(被.+)$/u,
  ];

  for (const pattern of patterns) {
    const match = line.match(pattern);
    if (!match) continue;
    const parts = match.slice(1).filter(Boolean);
    if (parts.every((part) => visibleLen(part) <= maxLen)) return parts;
  }
  return null;
}

function chooseCut(text, maxLen, tokenBoundaries) {
  const chars = [...text];
  const preferredMin = Math.max(5, Math.floor(maxLen * 0.45));
  let best = null;

  for (let i = preferredMin; i <= Math.min(maxLen, chars.length - 1); i++) {
    const left = chars.slice(0, i).join("");
    const right = chars.slice(i).join("");
    if (!right) continue;
    const score = boundaryScore(left, right, i, maxLen, tokenBoundaries);
    if (!best || score > best.score) best = { i, score };
  }

  if (best && best.score > -1000) return best.i;

  for (let i = Math.min(maxLen, chars.length - 1); i >= preferredMin; i--) {
    const left = chars.slice(0, i).join("");
    const right = chars.slice(i).join("");
    if (!badTail(left) && !badHead(right)) return i;
  }
  return Math.min(maxLen, chars.length - 1);
}

function boundaryScore(left, right, index, maxLen, tokenBoundaries) {
  let score = -Math.abs(maxLen - index) * 2;
  const last = [...left].at(-1) || "";
  const first = [...right][0] || "";

  if (badTail(left)) score -= 60;
  if (badHead(right)) score -= 60;
  if (tokenBoundaries?.size) {
    if (tokenBoundaries.has(index)) score += 90;
    else score -= 120;
  }
  if (visibleLen(right) < 3) score -= 40;
  if (visibleLen(left) < 4) score -= 30;

  if (/(或者|并且|但是|所以|因为|如果|只要|甚至|而是|就是|以及)$/.test(left)) score += 35;
  if (/^(或者|并且|但是|所以|因为|如果|只要|甚至|而是|就是|以及)/.test(right)) score += 45;
  if (/(的时候|的情况下|之后|之前|以后|之前|过程里|本质上)$/.test(left)) score += 35;
  if (/^(让|把|被|给|在|当|对|从|向|为了|通过)/.test(right)) score += 18;
  if (/^(和|与|跟)/.test(right) && visibleLen(right) >= 6) score += 12;
  if (/(一个|一种|这个|那个|自己|对方)$/.test(left)) score -= 25;
  if (/^(的|地|得|了|吗|呢|啊|吧|个|种|条|些|位|段|套|层|次|点|件)/.test(right)) score -= 80;
  if (/^[一二三四五六七八九十]/.test(first) && last === "第") score -= 100;
  return score;
}

function badTail(text) {
  return /(的|地|得|是|和|与|跟|把|被|对|给|在|从|向|为|到|了|一个|一种|这个|那个|自己|对方)$/.test(text);
}

function badHead(text) {
  return /^(的|地|得|了|吗|呢|啊|吧|个|种|条|些|位|段|套|层|次|点|件|和|与|跟)/.test(text);
}

function hardSplit(text, maxLen) {
  const chars = [...text];
  const parts = [];
  for (let i = 0; i < chars.length; i += maxLen) {
    parts.push(chars.slice(i, i + maxLen).join(""));
  }
  return parts;
}

function buildQa(sourceLines, outputLines, splitEvents, maxLen) {
  const overMax = outputLines
    .map((text, index) => ({ index: index + 1, len: visibleLen(text), text }))
    .filter((line) => line.len > maxLen);
  const punctuation = outputLines
    .map((text, index) => ({ index: index + 1, text }))
    .filter((line) => /[\p{P}\p{S}]/u.test(line.text));
  return {
    sourceLines: sourceLines.length,
    outputLines: outputLines.length,
    splitLines: splitEvents.length,
    maxChars: Math.max(0, ...outputLines.map(visibleLen)),
    maxAllowedChars: maxLen,
    blankLines: outputLines.filter((line) => !line).length,
    overMax,
    punctuation,
    splitEvents,
  };
}

function buildTokenBoundaryMap(lines) {
  const segmented = segmentWithJieba(lines);
  const map = new Map();
  if (!segmented) return map;
  for (let i = 0; i < lines.length; i++) {
    const boundaries = new Set();
    let pos = 0;
    for (const token of segmented[i] || []) {
      pos += visibleLen(token);
      if (pos > 0 && pos < visibleLen(lines[i])) boundaries.add(pos);
    }
    map.set(lines[i], boundaries);
  }
  return map;
}

function segmentWithJieba(lines) {
  const code = [
    "import sys, json",
    "try:",
    "    import jieba",
    "except Exception:",
    "    sys.exit(2)",
    "data = json.loads(sys.stdin.read())",
    "print(json.dumps([list(jieba.cut(x, HMM=True)) for x in data], ensure_ascii=False))",
  ].join("\n");
  const res = spawnSync("python3", ["-c", code], {
    input: JSON.stringify(lines),
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
  });
  if (res.status !== 0) return null;
  try {
    return JSON.parse(res.stdout);
  } catch {
    return null;
  }
}

function offsetBoundaries(boundaries, offset) {
  const out = new Set();
  for (const boundary of boundaries) {
    const shifted = boundary - offset;
    if (shifted > 0) out.add(shifted);
  }
  return out;
}
