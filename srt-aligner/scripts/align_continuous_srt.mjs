#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const args = parseArgs(process.argv.slice(2));
if (!args.script || !args.timed || !args.out) {
  fail("Usage: node align_continuous_srt.mjs --script final.txt --timed rough.srt|timed.json --out final.srt [--max-chars 17] [--keep-lines] [--qa final.qa.json] [--line-file final.lines.txt]");
}

const maxChars = Number(args["max-chars"] ?? 17);
const keepLines = Boolean(args["keep-lines"]);
const minDuration = Number(args["min-duration"] ?? 0.2);
const maxDuration = Number(args["max-duration"] ?? 8.0);
const out = path.resolve(String(args.out));
const outDir = path.dirname(out);
const reportPath = path.resolve(String(args.report ?? out.replace(/\.srt$/i, "") + ".report.json"));
const qaPath = path.resolve(String(args.qa ?? out.replace(/\.srt$/i, "") + ".qa.json"));
const linePath = path.resolve(String(args["line-file"] ?? out.replace(/\.srt$/i, "") + ".lines.txt"));
const rawAlignedPath = path.resolve(String(args["raw-out"] ?? out.replace(/\.srt$/i, "") + ".raw.srt"));

const protectedTerms = [
  "主动权", "高低位", "冷暴力", "情绪价值", "高密度情绪价值", "沉没成本", "转换成本",
  "亲密关系", "安全感", "安全感黑洞", "自我价值", "不可替代", "隐性价值", "底层逻辑",
  "心理机制", "服从性测试", "确定性惩罚", "管窥效应", "晕轮效应", "断联", "新欢",
  "起死回生", "字斟句酌", "思维导图", "艾特豆包", "探花Gary", "Gary", "KPI",
  "粉丝群", "朋友圈", "实战方案", "四两拨千斤", "底牌", "框架感", "不动如山",
  "外强中干", "全天候", "情绪垃圾桶", "无限提款机", "离家出走", "相亲市场",
  "婚恋市场", "精明现实", "冤大头", "香饽饽", "无缝衔接", "创可贴", "止痛药",
  "定时炸弹", "软骨头", "愁云惨雾", "醍醐灌顶", "一拍两散", "废物测试",
  "心理按摩", "心理七寸",
].sort((a, b) => b.length - a.length);

fs.mkdirSync(outDir, { recursive: true });

const scriptText = fs.readFileSync(args.script, "utf8").replace(/^\uFEFF/, "");
const lines = makeSubtitleLines(scriptText, { maxChars, keepLines });
if (!lines.length) fail("No subtitle lines found after cleaning script.");
fs.writeFileSync(linePath, lines.join("\n") + "\n", "utf8");

const here = path.dirname(fileURLToPath(import.meta.url));
const aligner = path.join(here, "align_srt.mjs");
const run = spawnSync(process.execPath, [
  aligner,
  "--script", linePath,
  "--timed", args.timed,
  "--out", rawAlignedPath,
  "--report", reportPath,
  "--max-chars", "999",
  "--min-duration", String(minDuration),
  "--max-duration", String(maxDuration),
  "--max-lcs-cells", String(args["max-lcs-cells"] ?? 200000000),
], { encoding: "utf8" });

if (run.status !== 0) {
  console.error(run.stdout);
  console.error(run.stderr);
  process.exit(run.status ?? 1);
}

const timedEnd = getFinalEnd(args.timed);
const finalCues = forceContinuous(parseSrt(fs.readFileSync(rawAlignedPath, "utf8")), timedEnd);
fs.writeFileSync(out, writeSrt(finalCues), "utf8");

const alignerReport = safeJson(run.stdout);
const qaReport = qa(finalCues, lines, alignerReport);
fs.writeFileSync(qaPath, JSON.stringify(qaReport, null, 2) + "\n", "utf8");

console.log(JSON.stringify({
  out,
  qa: qaPath,
  report: reportPath,
  lineFile: linePath,
  rawOut: rawAlignedPath,
  cues: finalCues.length,
  maxChars,
  keepLines,
  aligner: alignerReport,
  qaSummary: {
    blank_text: qaReport.blank_text,
    punctuation_issues: qaReport.punctuation_issues,
    overlaps: qaReport.overlaps,
    max_gap_between_cues_sec: qaReport.max_gap_between_cues_sec,
    lineCountMatches: qaReport.lineCountMatches,
  },
}, null, 2));

function makeSubtitleLines(text, opts) {
  if (opts.keepLines) {
    return text
      .replace(/\r/g, "\n")
      .split("\n")
      .map((line) => stripPunctuation(line))
      .filter(Boolean);
  }

  const nonempty = text.replace(/\r/g, "\n").split("\n").map((s) => s.trim()).filter(Boolean);
  const lineLike = nonempty.length >= 10 && quantile(nonempty.map((s) => visibleLen(stripPunctuation(s))).sort((a, b) => a - b), 0.8) <= opts.maxChars;
  if (lineLike) return nonempty.map((line) => stripPunctuation(line)).filter(Boolean);

  const pieces = text
    .replace(/\r/g, "\n")
    .replace(/\s+/g, "")
    .split(/(?<=[。！？!?；;，,、：:])/u)
    .map((s) => stripPunctuation(s))
    .filter(Boolean);
  const out = [];
  for (const piece of pieces) out.push(...splitPiece(piece, opts.maxChars));
  return mergeBadTinyLines(out, opts.maxChars);
}

function splitPiece(piece, maxLen) {
  const units = protectTokenize(piece);
  const out = [];
  let start = 0;
  while (start < units.length) {
    let end = start;
    let len = 0;
    while (end < units.length && len + visibleLen(units[end]) <= maxLen) {
      len += visibleLen(units[end]);
      end++;
    }
    if (end >= units.length) {
      out.push(units.slice(start).join(""));
      break;
    }
    const split = chooseSplit(units, start, end);
    out.push(units.slice(start, split).join(""));
    start = split;
  }
  return out.filter(Boolean);
}

function protectTokenize(text) {
  const units = [];
  for (let i = 0; i < text.length;) {
    const hit = protectedTerms.find((term) => text.startsWith(term, i));
    if (hit) {
      units.push(hit);
      i += hit.length;
      continue;
    }
    const cp = Array.from(text.slice(i))[0];
    units.push(cp);
    i += cp.length;
  }
  return units;
}

function chooseSplit(units, start, hardEnd) {
  const goodTail = /[的了呢啊吗吧呀嘛么上里中后前时就也都过到人事者点步层种套回]/u;
  for (let i = hardEnd; i > start + 5; i--) {
    if (goodTail.test(units[i - 1])) return i;
  }
  return hardEnd;
}

function mergeBadTinyLines(lines, maxLen) {
  const out = [];
  for (const line of lines) {
    const prev = out[out.length - 1];
    if (prev && visibleLen(line) <= 2 && visibleLen(prev + line) <= maxLen) out[out.length - 1] = prev + line;
    else out.push(line);
  }
  return out;
}

function stripPunctuation(s) {
  return s
    .normalize("NFKC")
    .replace(/[“”‘’"'.。,，、！？!?；;：:（）()【】\[\]《》<>—…·\-]/g, "")
    .replace(/\s+/g, "");
}

function parseSrt(text) {
  return text.replace(/\r/g, "").split(/\n\s*\n/).flatMap((block) => {
    const lines = block.split("\n").filter(Boolean);
    const timeIndex = lines.findIndex((line) => line.includes("-->"));
    if (timeIndex < 0) return [];
    const [a, b] = lines[timeIndex].split("-->").map((s) => s.trim());
    const start = parseTime(a);
    const end = parseTime(b);
    const cueText = stripPunctuation(lines.slice(timeIndex + 1).join(""));
    if (!cueText) return [];
    return [{ start, end, text: cueText }];
  });
}

function getFinalEnd(timedPath) {
  const text = fs.readFileSync(timedPath, "utf8").replace(/^\uFEFF/, "").trim();
  if (/\.srt$/i.test(timedPath)) {
    const cues = parseSrt(text);
    return cues.length ? cues.at(-1).end : null;
  }
  try {
    const data = JSON.parse(text);
    const segments = data.segments ?? [];
    for (let i = segments.length - 1; i >= 0; i--) {
      const end = Number(segments[i].end);
      if (Number.isFinite(end)) return end;
    }
  } catch {}
  return null;
}

function forceContinuous(cues, finalEnd) {
  const clean = cues.filter((cue) => cue.text).map((cue) => ({ ...cue }));
  for (let i = 0; i < clean.length; i++) {
    if (i > 0 && clean[i].start < clean[i - 1].end) clean[i].start = clean[i - 1].end;
    if (i > 0) clean[i - 1].end = clean[i].start;
    if (clean[i].end <= clean[i].start) clean[i].end = clean[i].start + 0.2;
  }
  if (clean.length && finalEnd && finalEnd > clean.at(-1).start) clean.at(-1).end = finalEnd;
  return clean;
}

function writeSrt(cues) {
  return cues.map((cue, i) => `${i + 1}\n${fmt(cue.start)} --> ${fmt(cue.end)}\n${cue.text}\n`).join("\n");
}

function qa(cues, sourceLines, alignerReport) {
  let maxGap = 0;
  let overlaps = 0;
  let blanks = 0;
  let punctuation = 0;
  let maxChars = 0;
  const punctuationExamples = [];
  const nonPositive = [];
  for (let i = 0; i < cues.length; i++) {
    const cue = cues[i];
    maxChars = Math.max(maxChars, visibleLen(cue.text));
    if (!cue.text.trim()) blanks++;
    if (cue.end <= cue.start) nonPositive.push(i + 1);
    if (/[“”‘’"'.。,，、！？!?；;：:（）()【】\[\]《》<>—…·\-]/.test(cue.text)) {
      punctuation++;
      if (punctuationExamples.length < 10) punctuationExamples.push({ index: i + 1, text: cue.text });
    }
    if (i + 1 < cues.length) {
      const gap = Math.round((cues[i + 1].start - cue.end) * 1000) / 1000;
      maxGap = Math.max(maxGap, gap);
      if (gap < -0.001) overlaps++;
    }
  }
  return {
    cues: cues.length,
    sourceLines: sourceLines.length,
    lineCountMatches: cues.length === sourceLines.length,
    blank_text: blanks,
    punctuation_issues: punctuation,
    punctuation_examples: punctuationExamples,
    overlaps,
    non_positive_duration_cues: nonPositive.slice(0, 20),
    max_gap_between_cues_sec: maxGap,
    max_chars_per_cue: maxChars,
    starts_at_sec: cues[0]?.start ?? null,
    ends_at_sec: cues.at(-1)?.end ?? null,
    alignerSummary: alignerReport?.confidence ? alignerReport : null,
  };
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (!key.startsWith("--")) continue;
    const name = key.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) out[name] = true;
    else out[name] = argv[++i];
  }
  return out;
}

function parseTime(value) {
  const m = value.match(/(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/);
  if (!m) return NaN;
  return Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) + Number(m[4]) / 1000;
}

function fmt(seconds) {
  const total = Math.max(0, Math.round(seconds * 1000));
  const ms = total % 1000;
  const secTotal = Math.floor(total / 1000);
  const s = secTotal % 60;
  const m = Math.floor(secTotal / 60) % 60;
  const h = Math.floor(secTotal / 3600);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
}

function visibleLen(s) {
  return Array.from(String(s).replace(/\s/g, "")).length;
}

function quantile(values, q) {
  if (!values.length) return 0;
  return values[Math.min(values.length - 1, Math.max(0, Math.floor((values.length - 1) * q)))];
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
