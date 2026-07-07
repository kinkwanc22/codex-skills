#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = parseArgs(process.argv.slice(2));
if (!args.script || !args.timed || !args.out) {
  fail("Usage: node align_continuous_srt.mjs --script final.txt --timed rough.srt|timed.json --out final.srt [--max-chars 17] [--keep-lines]");
}

const maxChars = Number(args["max-chars"] ?? 17);
const minDuration = Number(args["min-duration"] ?? 0.12);
const keepLines = Boolean(args["keep-lines"]);
const optimizeLines = !keepLines;
const out = path.resolve(String(args.out));
const qaPath = path.resolve(String(args.qa ?? out.replace(/\.srt$/i, "") + ".qa.json"));
const reportPath = path.resolve(String(args.report ?? out.replace(/\.srt$/i, "") + ".report.json"));
const linePath = path.resolve(String(args["line-file"] ?? out.replace(/\.srt$/i, "") + ".lines.txt"));
const zhSegmenter = typeof Intl !== "undefined" && Intl.Segmenter
  ? new Intl.Segmenter("zh-Hans", { granularity: "word" })
  : null;

const protectedTerms = [
  "主动权", "高低位", "冷暴力", "情绪价值", "高密度情绪价值", "沉没成本", "转换成本",
  "亲密关系", "安全感", "安全感黑洞", "自我价值", "不可替代", "隐性价值", "底层逻辑",
  "心理机制", "服从性测试", "确定性惩罚", "管窥效应", "晕轮效应", "断联", "新欢",
  "起死回生", "字斟句酌", "思维导图", "艾特豆包", "探花Gary", "Gary", "KPI",
  "粉丝群", "朋友圈", "实战方案", "四两拨千斤", "底牌", "框架感", "不动如山",
  "外强中干", "全天候", "情绪垃圾桶", "无限提款机", "离家出走", "相亲市场",
  "婚恋市场", "精明现实", "冤大头", "香饽饽", "无缝衔接", "创可贴", "止痛药",
  "定时炸弹", "软骨头", "愁云惨雾", "醍醐灌顶", "一拍两散", "废物测试",
  "心理按摩", "心理七寸", "拿回主动权", "立于不败之地", "具体聊天记录",
  "聊天记录", "每一条消息", "进入正题", "思维导图", "游刃有余", "掀桌子走人",
  "鸡毛蒜皮", "拒绝沟通", "实行冷暴力", "如履薄冰", "死缠烂打",
  "吸血鬼", "能量黑洞", "心理学机制", "框架控制理论", "关系里", "后再回来观看",
  "总结出精髓", "你的情绪价值和物质资源", "情绪价值和物质资源", "时间和精力", "框架和尊严", "认知和操作",
  "事业和生活", "底线和原则", "无数人",
].sort((a, b) => b.length - a.length);

fs.mkdirSync(path.dirname(out), { recursive: true });

const scriptText = fs.readFileSync(args.script, "utf8").replace(/^\uFEFF/, "");
const lines = makeSubtitleLines(scriptText, { maxChars, keepLines });
if (!lines.length) fail("No subtitle lines found after cleaning script.");
const lineQaReport = lineQa(lines, maxChars);

const timed = loadTimedInput(args.timed);
if (!timed.units.length) fail("Timed input has no usable text units.");

const scriptUnits = flattenLineUnits(lines);
const matches = lcsMatches(scriptUnits, timed.units, Number(args["max-lcs-cells"] ?? 220000000));
const aligned = buildAlignedCues(lines, scriptUnits, timed, matches, { minDuration });
const qaReport = qa(aligned.cues, lines, aligned.report, lineQaReport);

fs.writeFileSync(linePath, lines.join("\n") + "\n", "utf8");
fs.writeFileSync(out, writeSrt(aligned.cues), "utf8");
fs.writeFileSync(reportPath, JSON.stringify(aligned.report, null, 2) + "\n", "utf8");
fs.writeFileSync(qaPath, JSON.stringify(qaReport, null, 2) + "\n", "utf8");

console.log(JSON.stringify({
  out,
  qa: qaPath,
  report: reportPath,
  lineFile: linePath,
  cues: aligned.cues.length,
  timingMode: timed.mode,
  confidence: aligned.report.summary.confidence,
  matchedUnits: aligned.report.summary.matchedUnits,
  scriptUnits: aligned.report.summary.scriptUnits,
  timedUnits: aligned.report.summary.timedUnits,
  weakCues: aligned.report.summary.weakCues,
  estimatedCues: aligned.report.summary.estimatedCues,
  keepLines,
  optimizeLines,
  qaSummary: {
    blank_text: qaReport.blank_text,
    punctuation_issues: qaReport.punctuation_issues,
    overlaps: qaReport.overlaps,
    max_gap_between_cues_sec: qaReport.max_gap_between_cues_sec,
    max_chars_per_cue: qaReport.max_chars_per_cue,
    lineCountMatches: qaReport.lineCountMatches,
    lineQaIssues: qaReport.lineQa.summary.totalIssues,
  },
}, null, 2));

function makeSubtitleLines(text, opts) {
  if (opts.keepLines) return cleanInputLines(text, false);

  const inputLines = cleanInputLines(text, false);
  if (looksLineBroken(inputLines, opts.maxChars)) {
    return repairInputLines(inputLines, opts.maxChars);
  }

  const pieces = text
    .replace(/\r/g, "\n")
    .replace(/\s+/g, "")
    .split(/(?<=[。！？!?；;，,、：:])/u)
    .map((s) => stripPunctuation(s))
    .filter(Boolean);
  const lines = [];
  for (const piece of pieces) lines.push(...splitPiece(piece, opts.maxChars));
  return polishShortLines(lines, opts.maxChars);
}

function looksLineBroken(lines, maxLen) {
  if (lines.length < 10) return false;
  const lengths = lines.map(visibleLen).sort((a, b) => a - b);
  return quantile(lengths, 0.8) <= maxLen && quantile(lengths, 0.95) <= maxLen + 6;
}

function repairInputLines(inputLines, maxLen) {
  let lines = inputLines.flatMap((line) => visibleLen(line) > maxLen ? splitPiece(line, maxLen) : [line]);
  lines = restoreSentenceAnchors(lines, maxLen);
  for (let pass = 0; pass < 6; pass++) {
    let changed = false;
    const out = [];
    for (let i = 0; i < lines.length; i++) {
      const current = lines[i];
      const next = lines[i + 1];
      if (next && boundaryNeedsRepair(current, next)) {
        out.push(...splitPiece(current + next, maxLen));
        i++;
        changed = true;
      } else {
        out.push(current);
      }
    }
    lines = out.filter(Boolean);
    lines = restoreSentenceAnchors(lines, maxLen);
    if (!changed) break;
  }
  return fixLeadingConnectors(lines, maxLen);
}

function boundaryNeedsRepair(current, next) {
  if (badLineTail(current) || badLineHead(next)) return true;
  const combined = current + next;
  return protectedTerms.some((term) => (
    term.length >= 2 && combined.includes(term) && !current.includes(term) && !next.includes(term)
  ));
}

function fixLeadingConnectors(lines, maxLen) {
  const out = [...lines];
  for (let i = 1; i < out.length; i++) {
    const head = Array.from(out[i])[0];
    if (!"和与跟".includes(head)) continue;
    if (visibleLen(out[i - 1] + head) > maxLen) continue;
    out[i - 1] += head;
    out[i] = Array.from(out[i]).slice(1).join("");
  }
  return out.filter(Boolean);
}

function restoreSentenceAnchors(lines, maxLen) {
  let out = [...lines];
  const anchors = ["为什么", "因为", "只要", "如果", "但是", "那么", "所以", "记住", "好", "当然", "首先", "其次"];
  for (let i = 0; i < out.length; i++) {
    for (const anchor of anchors) {
      const idx = out[i].indexOf(anchor);
      if (idx <= 0) continue;
      const before = out[i].slice(0, idx);
      const after = out[i].slice(idx);
      if (!before || !after) continue;
      if (!shouldSplitAtAnchor(before, anchor)) continue;
      if (visibleLen(after) > maxLen) continue;
      out.splice(i, 1, before, after);
      i++;
      break;
    }
  }
  out = out.flatMap((line) => splitSentenceTail(line, maxLen));
  return mergeIncompleteAnchorLines(out.filter(Boolean), maxLen);
}

function shouldSplitAtAnchor(before, anchor) {
  const len = visibleLen(before);
  if (anchor === "为什么") return len >= 3;
  if (anchor === "好") return len >= 6;
  if (["因为", "如果", "所以", "但", "但是", "只要", "那么"].includes(anchor)) return len >= 7;
  return len >= 5;
}

function splitSentenceTail(line, maxLen) {
  const patterns = [
    /^(.*?)(只要一个男人.+)$/u,
    /^(.*?)(因为觉醒意味着.+)$/u,
    /^(.*?)(他都能.+)$/u,
  ];
  for (const pattern of patterns) {
    const m = line.match(pattern);
    if (!m || !m[1] || !m[2]) continue;
    if (visibleLen(m[1]) <= maxLen && visibleLen(m[2]) <= maxLen) return [m[1], m[2]];
  }
  return [line];
}

function mergeIncompleteAnchorLines(lines, maxLen) {
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    const current = lines[i];
    const next = lines[i + 1];
    if (
      next
      && /^(只要|如果|因为|但是|所以|那么|你要|你会).{0,8}$/.test(current)
      && visibleLen(next) <= 5
      && visibleLen(current + next) <= maxLen
    ) {
      out.push(current + next);
      i++;
    } else {
      out.push(current);
    }
  }
  return out;
}

function cleanInputLines(text, splitLong) {
  return text
    .replace(/\r/g, "\n")
    .split("\n")
    .map((line) => stripPunctuation(line))
    .filter(Boolean)
    .flatMap((line) => splitLong ? splitPiece(line, maxChars) : [line]);
}

function splitPiece(piece, maxLen) {
  const units = protectTokenize(piece);
  const out = [];
  let start = 0;
  while (start < units.length) {
    let hardEnd = start;
    let len = 0;
    while (hardEnd < units.length && len + visibleLen(units[hardEnd]) <= maxLen) {
      len += visibleLen(units[hardEnd]);
      hardEnd++;
    }
    if (hardEnd === start) {
      const chars = Array.from(units[start]);
      out.push(chars.slice(0, maxLen).join(""));
      const rest = chars.slice(maxLen).join("");
      if (rest) units[start] = rest;
      else start++;
      continue;
    }
    if (hardEnd >= units.length) {
      out.push(units.slice(start).join(""));
      break;
    }
    const split = chooseSplit(units, start, hardEnd, maxLen);
    out.push(units.slice(start, split).join(""));
    start = split;
  }
  return out.filter(Boolean);
}

function chooseSplit(units, start, hardEnd, maxLen) {
  const target = Math.max(8, Math.min(14, maxLen - 2));
  let best = hardEnd;
  let bestScore = Infinity;
  for (let i = start + 4; i <= hardEnd; i++) {
    const left = units.slice(start, i).join("");
    const right = units.slice(i, Math.min(units.length, i + 4)).join("");
    const len = visibleLen(left);
    const remaining = visibleLen(units.slice(i).join(""));
    if (len > maxLen) continue;
    let score = Math.abs(len - target) * 2;
    if (badLineTail(left)) score += 120;
    if (badLineHead(right)) score += 120;
    if (remaining > 0 && remaining <= 6) score += 20 - remaining;
    if (strongLineTail(left)) score -= 6;
    if (i === hardEnd) score += 2;
    if (score < bestScore) {
      bestScore = score;
      best = i;
    }
  }
  return best;
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
    const token = nextWordToken(text, i);
    units.push(token);
    i += token.length;
  }
  return units;
}

function nextWordToken(text, index) {
  if (!zhSegmenter) return Array.from(text.slice(index))[0];
  const iterator = zhSegmenter.segment(text.slice(index))[Symbol.iterator]();
  const first = iterator.next().value?.segment;
  if (!first) return Array.from(text.slice(index))[0];
  const chars = Array.from(first);
  if (chars.length > 1 && /^[的地得了和跟与把被对给在从向为而但就能会要想以一这那每某另]/u.test(first)) {
    return chars[0];
  }
  return first;
}

function badLineTail(text) {
  if (/^(好|好的|为什么|那么|所以|当然|首先|其次)$/.test(text)) return false;
  if (/(上的|里的|中的|后的|前的|内的|外的|底下的|基础上的|关系里的|过程里的|搞砸的)$/.test(text)) return false;
  return /(的|地|得|和|跟|与|把|被|对|给|在|从|向|为|是|就|能|会|要|想|可以|以|而|但|因为|所以|如果|只要|就是|这个|那个|一个|一种|一|这|那|每|某|另|什么|怎么)$/.test(text);
}

function badLineHead(text) {
  if (/^(好|好的|为什么|只要|如果|因为|但是|所以|那么|当然|首先|其次)/.test(text)) return false;
  if (/^(你的|她的|他的|我的|我们的|你们的|他们的|自己的|对方的)/.test(text)) return false;
  return /^([\p{Script=Han}]的|个|种|条|些|位|段|套|层|次|点|件|的|地|得|了|吗|呢|啊|吧|和|跟|与|把|被|对|给|在|从|向|为)/u.test(text);
}

function strongLineTail(text) {
  return /(了|吗|呢|啊|吧|呀|么|时候|问题|关系|女人|男人|兄弟|逻辑|价值|主动权|高低位|冷暴力|情绪价值|断联|新欢|框架|底线|尊严)$/.test(text);
}

function polishShortLines(lines, maxLen) {
  const out = [];
  for (const line of lines) {
    const prev = out[out.length - 1];
    if (prev && visibleLen(line) <= 3 && visibleLen(prev + line) <= maxLen && !strongLineTail(prev)) {
      out[out.length - 1] = prev + line;
    } else {
      out.push(line);
    }
  }
  for (let i = 0; i < out.length - 1; i++) {
    if (visibleLen(out[i]) <= 3 && visibleLen(out[i] + out[i + 1]) <= maxLen && !strongLineTail(out[i])) {
      out[i + 1] = out[i] + out[i + 1];
      out.splice(i, 1);
      i--;
    }
  }
  return out;
}

function lineQa(lines, maxLen) {
  const issues = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const next = lines[i + 1] ?? "";
    if (visibleLen(line) > maxLen) {
      issues.push({ index: i + 1, type: "over_max_chars", text: line, len: visibleLen(line) });
    }
    if (badLineTail(line)) {
      issues.push({ index: i + 1, type: "bad_line_tail", text: line });
    }
    if (next && badLineHead(next)) {
      issues.push({ index: i + 2, type: "bad_line_head", text: next, prev: line });
    }
    for (const term of protectedTerms) {
      if (term.length < 2) continue;
      const combined = line + next;
      if (next && combined.includes(term) && !line.includes(term) && !next.includes(term)) {
        issues.push({ index: i + 1, type: "protected_term_split", term, text: line, next });
      }
    }
  }
  return {
    summary: {
      totalIssues: issues.length,
      overMaxChars: issues.filter((x) => x.type === "over_max_chars").length,
      badLineTail: issues.filter((x) => x.type === "bad_line_tail").length,
      badLineHead: issues.filter((x) => x.type === "bad_line_head").length,
      protectedTermSplit: issues.filter((x) => x.type === "protected_term_split").length,
    },
    issues: issues.slice(0, 200),
  };
}

function loadTimedInput(filename) {
  const text = fs.readFileSync(filename, "utf8").replace(/^\uFEFF/, "").trim();
  if (/\.srt$/i.test(filename)) {
    const segments = parseSrtSegments(text);
    return { mode: "srt-char", segments, units: segments.flatMap(segmentToTimedUnits) };
  }

  const data = JSON.parse(text);
  const segments = [];
  const units = [];
  for (const seg of data.segments ?? []) {
    const start = Number(seg.start);
    const end = Number(seg.end);
    const segText = String(seg.text ?? "").trim();
    if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
      segments.push({ start, end, text: segText });
    }
    for (const word of seg.words ?? []) {
      const ws = Number(word.start);
      const we = Number(word.end);
      if (!Number.isFinite(ws) || !Number.isFinite(we) || we <= ws) continue;
      const chars = textUnits(String(word.word ?? word.text ?? ""));
      chars.forEach((token, i) => {
        units.push({ token, start: ws + (we - ws) * (i / chars.length), end: ws + (we - ws) * ((i + 1) / chars.length) });
      });
    }
  }
  if (units.length) return { mode: "word-char", segments, units };
  return { mode: "json-segment-char", segments, units: segments.flatMap(segmentToTimedUnits) };
}

function parseSrtSegments(text) {
  return text.replace(/\r/g, "").split(/\n\s*\n/).flatMap((block) => {
    const lines = block.split("\n").filter(Boolean);
    const timeIndex = lines.findIndex((line) => line.includes("-->"));
    if (timeIndex < 0) return [];
    const [a, b] = lines[timeIndex].split("-->").map((s) => s.trim());
    const start = parseTime(a);
    const end = parseTime(b);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return [];
    return [{ start, end, text: lines.slice(timeIndex + 1).join("") }];
  });
}

function segmentToTimedUnits(segment) {
  const units = textUnits(segment.text);
  if (!units.length) return [];
  const duration = segment.end - segment.start;
  return units.map((token, i) => ({
    token,
    start: segment.start + duration * (i / units.length),
    end: segment.start + duration * ((i + 1) / units.length),
  }));
}

function flattenLineUnits(lines) {
  const out = [];
  lines.forEach((line, lineIndex) => {
    textUnits(line).forEach((token) => out.push({ token, lineIndex }));
  });
  return out;
}

function textUnits(text) {
  const out = [];
  const re = /[\p{Script=Han}]|[a-zA-Z0-9]+/gu;
  for (const match of stripPunctuation(text).toLowerCase().matchAll(re)) out.push(match[0]);
  return out;
}

function lcsMatches(a, b, maxCells) {
  const n = a.length;
  const m = b.length;
  if ((n + 1) * (m + 1) > maxCells) return bandedGreedyMatches(a, b);

  const width = m + 1;
  const dp = new Uint16Array((n + 1) * width);
  for (let i = n - 1; i >= 0; i--) {
    const row = i * width;
    const nextRow = (i + 1) * width;
    for (let j = m - 1; j >= 0; j--) {
      dp[row + j] = a[i].token === b[j].token
        ? dp[nextRow + j + 1] + 1
        : Math.max(dp[nextRow + j], dp[row + j + 1]);
    }
  }

  const matches = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (a[i].token === b[j].token) {
      matches.push({ scriptIndex: i, timedIndex: j });
      i++;
      j++;
    } else if (dp[(i + 1) * width + j] >= dp[i * width + j + 1]) {
      i++;
    } else {
      j++;
    }
  }
  return matches;
}

function bandedGreedyMatches(a, b) {
  const matches = [];
  let cursor = 0;
  const windowSize = Number(args["greedy-window"] ?? 1200);
  for (let i = 0; i < a.length; i++) {
    const end = Math.min(b.length, cursor + windowSize);
    let found = -1;
    for (let j = cursor; j < end; j++) {
      if (a[i].token === b[j].token) {
        found = j;
        break;
      }
    }
    if (found >= 0) {
      matches.push({ scriptIndex: i, timedIndex: found });
      cursor = found + 1;
    }
  }
  return matches;
}

function buildAlignedCues(lines, scriptUnits, timed, matches, opts) {
  const byLine = lines.map(() => []);
  for (const match of matches) {
    const lineIndex = scriptUnits[match.scriptIndex].lineIndex;
    byLine[lineIndex].push(timed.units[match.timedIndex]);
  }

  const lineStats = lines.map((text, i) => {
    const units = byLine[i];
    const unitCount = textUnits(text).length || 1;
    return {
      text,
      confidence: units.length / unitCount,
      matchedUnits: units.length,
      estimated: units.length === 0,
      rawStart: units[0]?.start ?? null,
      rawEnd: units.at(-1)?.end ?? null,
      unitCount,
    };
  });

  fillMissingLineTimes(lineStats, timed);
  const boundaries = buildCueBoundaries(lineStats, timed, opts.minDuration);
  const cues = lineStats.map((line, i) => ({
    start: boundaries[i],
    end: boundaries[i + 1],
    text: line.text,
    confidence: line.confidence,
    matchedUnits: line.matchedUnits,
    estimated: line.estimated,
  }));
  for (const cue of cues) {
    if (cue.end <= cue.start) cue.end = cue.start + opts.minDuration;
  }
  if (cues.length) cues.at(-1).end = Math.max(cues.at(-1).end, timed.units.at(-1).end);

  const weak = cues
    .map((cue, i) => ({ cue, index: i + 1 }))
    .filter(({ cue }) => cue.estimated || cue.confidence < 0.45);
  return {
    cues,
    report: {
      timingMode: timed.mode,
      summary: {
        cues: cues.length,
        confidence: round(matches.length / Math.max(1, scriptUnits.length)),
        matchedUnits: matches.length,
        scriptUnits: scriptUnits.length,
        timedUnits: timed.units.length,
        weakCues: weak.length,
        estimatedCues: cues.filter((cue) => cue.estimated).length,
      },
      weakCues: weak.slice(0, 200).map(({ cue, index }) => ({
        index,
        start: round(cue.start),
        end: round(cue.end),
        confidence: round(cue.confidence),
        estimated: cue.estimated,
        text: cue.text,
      })),
    },
  };
}

function fillMissingLineTimes(lineStats, timed) {
  for (let i = 0; i < lineStats.length; i++) {
    if (lineStats[i].rawStart !== null) continue;
    let prev = i - 1;
    while (prev >= 0 && lineStats[prev].rawEnd === null) prev--;
    let next = i + 1;
    while (next < lineStats.length && lineStats[next].rawStart === null) next++;
    const first = i;
    let last = i;
    while (last + 1 < lineStats.length && lineStats[last + 1].rawStart === null) last++;
    const start = prev >= 0 ? lineStats[prev].rawEnd : timed.units[0].start;
    const end = next < lineStats.length ? lineStats[next].rawStart : timed.units.at(-1).end;
    const totalChars = lineStats.slice(first, last + 1).reduce((sum, line) => sum + Math.max(1, visibleLen(line.text)), 0);
    let cursor = start;
    for (let j = first; j <= last; j++) {
      const share = Math.max(1, visibleLen(lineStats[j].text)) / Math.max(1, totalChars);
      lineStats[j].rawStart = cursor;
      cursor += Math.max(0, end - start) * share;
      lineStats[j].rawEnd = cursor;
    }
    i = last;
  }
}

function buildCueBoundaries(lineStats, timed, minDur) {
  const finalEnd = timed.units.at(-1).end;
  const boundaries = new Array(lineStats.length + 1);
  boundaries[0] = Number.isFinite(lineStats[0]?.rawStart)
    ? Math.min(lineStats[0].rawStart, timed.units[0].start)
    : timed.units[0].start;
  for (let i = 1; i < lineStats.length; i++) {
    const prevEnd = lineStats[i - 1].rawEnd;
    const currStart = lineStats[i].rawStart;
    if (Number.isFinite(prevEnd) && Number.isFinite(currStart)) {
      boundaries[i] = prevEnd <= currStart ? (prevEnd + currStart) / 2 : currStart;
    } else if (Number.isFinite(currStart)) {
      boundaries[i] = currStart;
    } else if (Number.isFinite(prevEnd)) {
      boundaries[i] = prevEnd;
    } else {
      boundaries[i] = null;
    }
  }
  boundaries[boundaries.length - 1] = finalEnd;

  let anchor = 0;
  for (let i = 1; i < boundaries.length; i++) {
    if (!Number.isFinite(boundaries[i])) continue;
    const span = i - anchor;
    const start = boundaries[anchor];
    const end = boundaries[i];
    if (span > 1) {
      const totalChars = lineStats
        .slice(anchor, i)
        .reduce((sum, line) => sum + Math.max(1, visibleLen(line.text)), 0);
      let cursor = start;
      for (let j = anchor + 1; j < i; j++) {
        const prevChars = Math.max(1, visibleLen(lineStats[j - 1].text));
        cursor += (end - start) * (prevChars / Math.max(1, totalChars));
        boundaries[j] = cursor;
      }
    }
    anchor = i;
  }

  for (let i = 1; i < boundaries.length; i++) {
    if (boundaries[i] < boundaries[i - 1] + minDur) boundaries[i] = boundaries[i - 1] + minDur;
  }
  if (boundaries.at(-1) > finalEnd) {
    boundaries[boundaries.length - 1] = finalEnd;
    for (let i = boundaries.length - 2; i >= 0; i--) {
      if (boundaries[i] > boundaries[i + 1] - minDur) boundaries[i] = boundaries[i + 1] - minDur;
    }
  }
  return boundaries;
}

function qa(cues, sourceLines, alignReport, lineQaReport) {
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
      const gap = round(cues[i + 1].start - cue.end);
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
    alignerSummary: alignReport.summary,
    lineQa: lineQaReport,
  };
}

function writeSrt(cues) {
  return cues.map((cue, i) => `${i + 1}\n${fmt(cue.start)} --> ${fmt(cue.end)}\n${cue.text}\n`).join("\n");
}

function stripPunctuation(s) {
  return String(s)
    .normalize("NFKC")
    .replace(/[“”‘’"'.。,，、！？!?；;：:（）()【】\[\]《》<>—…·\-]/g, "")
    .replace(/\s+/g, "");
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

function round(value) {
  return Math.round(Number(value) * 1000) / 1000;
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
