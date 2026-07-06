#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = parseArgs(process.argv.slice(2));
if (!args.script || !args.timed || !args.out) {
  fail("Usage: node scripts/align_srt.mjs --script copy.txt --timed whisper.json|input.srt --out output.srt [--max-chars 32] [--report report.json]");
}

const scriptText = fs.readFileSync(args.script, "utf8").replace(/^\uFEFF/, "").trim();
const timedText = fs.readFileSync(args.timed, "utf8").replace(/^\uFEFF/, "").trim();
const maxChars = Number(args["max-chars"] ?? 30);
const minDuration = Number(args["min-duration"] ?? 0.7);
const maxDuration = Number(args["max-duration"] ?? 5.5);
const reportPath = args.report === false || args["no-report"]
  ? null
  : String(args.report ?? `${args.out}.report.json`);

if (!scriptText) fail("Script is empty.");
if (!timedText) fail("Timed input is empty.");

const timed = loadTimedInput(args.timed, timedText);
const chunks = chunkScript(scriptText, maxChars);
if (!chunks.length) fail("No subtitle chunks could be created from script.");

const scriptTokens = flattenChunkTokens(chunks);
let timedTokens = timed.words;
let timingMode = timed.wordSource;

if (!timedTokens.length && timed.segments.some((seg) => tokenize(seg.text).length)) {
  timedTokens = timed.segments.flatMap(segmentToPseudoWords);
  timingMode = "segment-text";
}

let result;
if (timedTokens.length) {
  result = alignWithGlobalTokens(chunks, scriptTokens, timedTokens, { minDuration, maxDuration });
} else {
  result = alignWithSegments(chunks, timed.segments, { minDuration, maxDuration });
  timingMode = "segment-proportional";
}

const cues = smoothCues(result.cues, { minDuration, maxDuration });
const report = buildReport({
  out: path.resolve(args.out),
  timingMode,
  chunks,
  cues,
  stats: result.stats,
  timedTokenCount: timedTokens.length,
  scriptTokenCount: scriptTokens.length,
});

const srt = cues.map((cue, i) => {
  const start = formatSrtTime(cue.start);
  const end = formatSrtTime(Math.max(cue.end, cue.start + 0.2));
  return `${i + 1}\n${start} --> ${end}\n${wrapSubtitle(cue.text)}\n`;
}).join("\n");

fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
fs.writeFileSync(args.out, srt, "utf8");
if (reportPath) {
  fs.mkdirSync(path.dirname(path.resolve(reportPath)), { recursive: true });
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
}

console.log(JSON.stringify({
  out: path.resolve(args.out),
  report: reportPath ? path.resolve(reportPath) : null,
  cues: cues.length,
  timingMode,
  confidence: report.summary.confidence,
  estimatedCues: report.summary.estimatedCues,
  weakCues: report.summary.weakCues,
  duration: cues.length ? cues[cues.length - 1].end - cues[0].start : 0,
}, null, 2));

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

function loadTimedInput(filename, text) {
  if (/\.srt$/i.test(filename)) return { ...loadSrt(text), wordSource: "segment-srt" };
  const data = JSON.parse(text);
  const segments = [];
  const words = [];
  for (const seg of data.segments ?? []) {
    const start = Number(seg.start);
    const end = Number(seg.end);
    if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
      segments.push({ start, end, text: String(seg.text ?? "").trim() });
    }
    for (const w of seg.words ?? []) {
      const ws = Number(w.start);
      const we = Number(w.end);
      const raw = String(w.word ?? w.text ?? "").trim();
      if (!raw || !Number.isFinite(ws) || !Number.isFinite(we) || we <= ws) continue;
      for (const token of tokenize(raw)) words.push({ token, start: ws, end: we, source: "word" });
    }
  }
  if (!segments.length && words.length) {
    segments.push({ start: words[0].start, end: words[words.length - 1].end, text: "" });
  }
  if (!segments.length) fail("Timed JSON needs segments with start/end values.");
  return { segments, words, wordSource: words.length ? "word" : "segment-json" };
}

function loadSrt(text) {
  const blocks = text.replace(/\r/g, "").split(/\n\s*\n/);
  const segments = [];
  for (const block of blocks) {
    const lines = block.split("\n").filter(Boolean);
    const timeLine = lines.find((line) => line.includes("-->"));
    if (!timeLine) continue;
    const [a, b] = timeLine.split("-->").map((s) => s.trim());
    const start = parseSrtTime(a);
    const end = parseSrtTime(b);
    if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
      const textLines = lines.slice(lines.indexOf(timeLine) + 1).join(" ").trim();
      segments.push({ start, end, text: textLines });
    }
  }
  if (!segments.length) fail("No subtitle segments found in SRT timed input.");
  return { segments, words: [] };
}

function chunkScript(text, maxChars) {
  const normalized = text.replace(/\r/g, "\n").replace(/[ \t]+/g, " ").trim();
  const rough = normalized
    .split(/(?<=[。！？!?；;])|\n+/g)
    .map((s) => s.trim())
    .filter(Boolean);
  const chunks = [];
  for (const piece of rough) splitPiece(piece, maxChars, chunks);
  return chunks;
}

function splitPiece(piece, maxChars, chunks) {
  let rest = piece.trim();
  while (visibleLength(rest) > maxChars) {
    let idx = bestSplit(rest, maxChars);
    if (idx <= 0) idx = Array.from(rest).slice(0, maxChars).join("").length;
    chunks.push(rest.slice(0, idx).trim());
    rest = rest.slice(idx).trim();
  }
  if (rest) chunks.push(rest);
}

function bestSplit(text, maxChars) {
  const chars = Array.from(text);
  let pos = 0;
  const candidates = [];
  for (const ch of chars) {
    pos += ch.length;
    if ("，、,.：: ".includes(ch)) candidates.push(pos);
    if (visibleLength(text.slice(0, pos)) >= maxChars) break;
  }
  return candidates.length ? candidates[candidates.length - 1] : 0;
}

function flattenChunkTokens(chunks) {
  const out = [];
  chunks.forEach((text, chunkIndex) => {
    tokenize(text).forEach((token) => out.push({ token, chunkIndex }));
  });
  return out;
}

function segmentToPseudoWords(segment) {
  const tokens = tokenize(segment.text);
  if (!tokens.length) return [];
  const duration = segment.end - segment.start;
  return tokens.map((token, i) => {
    const start = segment.start + duration * (i / tokens.length);
    const end = segment.start + duration * ((i + 1) / tokens.length);
    return { token, start, end, source: "segment-text" };
  });
}

function alignWithGlobalTokens(chunks, scriptTokens, timedTokens, opts) {
  const matches = lcsMatches(scriptTokens, timedTokens);
  const byChunk = chunks.map(() => []);
  for (const match of matches) byChunk[scriptTokens[match.scriptIndex].chunkIndex].push(timedTokens[match.timedIndex]);

  const cues = byChunk.map((times, i) => {
    if (times.length) {
      const start = times[0].start;
      const end = times[times.length - 1].end;
      const tokenCount = tokenize(chunks[i]).length || 1;
      const confidence = times.length / tokenCount;
      return clampCue({ text: chunks[i], start, end, confidence, matchedTokens: times.length, estimated: false }, opts);
    }
    const bounds = estimateBounds(i, byChunk, timedTokens, chunks);
    return clampCue({ text: chunks[i], ...bounds, confidence: 0, matchedTokens: 0, estimated: true }, opts);
  });

  return {
    cues,
    stats: {
      matchedTokens: matches.length,
      totalScriptTokens: scriptTokens.length,
      totalTimedTokens: timedTokens.length,
      estimatedCues: cues.filter((cue) => cue.estimated).length,
    },
  };
}

function lcsMatches(a, b) {
  const n = a.length;
  const m = b.length;
  const maxCells = Number(args["max-lcs-cells"] ?? 45000000);
  if ((n + 1) * (m + 1) > maxCells) return anchoredGreedyMatches(a, b);

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

function anchoredGreedyMatches(a, b) {
  const matches = [];
  let cursor = 0;
  const windowSize = Number(args["greedy-window"] ?? 300);
  for (let i = 0; i < a.length; i++) {
    const found = findNext(b, a[i].token, cursor, windowSize);
    if (found >= 0) {
      matches.push({ scriptIndex: i, timedIndex: found });
      cursor = found + 1;
    }
  }
  return matches;
}

function findNext(words, token, cursor, windowSize) {
  const end = Math.min(words.length, cursor + windowSize);
  for (let i = cursor; i < end; i++) if (words[i].token === token) return i;
  return -1;
}

function estimateBounds(index, byChunk, timedTokens, chunks) {
  const prev = previousMatchedToken(index, byChunk);
  const next = nextMatchedToken(index, byChunk);
  if (prev && next && next.start > prev.end) {
    const emptySpan = countEmptyChunksBetween(index, byChunk);
    const slot = emptySpan.position / emptySpan.total;
    const nextSlot = (emptySpan.position + 1) / emptySpan.total;
    const gap = next.start - prev.end;
    return { start: prev.end + gap * slot, end: prev.end + gap * nextSlot };
  }
  if (prev) {
    const start = prev.end;
    return { start, end: Math.min(timedTokens.at(-1).end, start + estimateDuration(chunks[index])) };
  }
  if (next) {
    const end = next.start;
    return { start: Math.max(0, end - estimateDuration(chunks[index])), end };
  }
  return { start: timedTokens[0].start, end: timedTokens.at(-1).end };
}

function previousMatchedToken(index, byChunk) {
  for (let i = index - 1; i >= 0; i--) if (byChunk[i].length) return byChunk[i].at(-1);
  return null;
}

function nextMatchedToken(index, byChunk) {
  for (let i = index + 1; i < byChunk.length; i++) if (byChunk[i].length) return byChunk[i][0];
  return null;
}

function countEmptyChunksBetween(index, byChunk) {
  let first = index;
  let last = index;
  while (first - 1 >= 0 && !byChunk[first - 1].length) first--;
  while (last + 1 < byChunk.length && !byChunk[last + 1].length) last++;
  return { total: last - first + 2, position: index - first };
}

function alignWithSegments(chunks, segments, opts) {
  const totalChars = chunks.reduce((sum, c) => sum + visibleLength(c), 0) || chunks.length;
  const start = segments[0].start;
  const end = segments[segments.length - 1].end;
  const totalDuration = Math.max(0.1, end - start);
  let t = start;
  const cues = chunks.map((text, i) => {
    const isLast = i === chunks.length - 1;
    const share = visibleLength(text) / totalChars;
    const duration = isLast ? end - t : totalDuration * share;
    const cue = clampCue({ text, start: t, end: t + duration, confidence: 0, matchedTokens: 0, estimated: true }, opts);
    t = cue.end;
    return cue;
  });
  return {
    cues,
    stats: {
      matchedTokens: 0,
      totalScriptTokens: flattenChunkTokens(chunks).length,
      totalTimedTokens: 0,
      estimatedCues: cues.length,
    },
  };
}

function smoothCues(cues, opts) {
  return cues.map((cue, i) => {
    const prev = i > 0 ? cues[i - 1] : null;
    const next = i + 1 < cues.length ? cues[i + 1] : null;
    let start = prev ? Math.max(cue.start, prev.end) : cue.start;
    let end = Math.max(cue.end, start + opts.minDuration);
    if (next && end > next.start) end = Math.max(start + 0.2, next.start);
    const clamped = clampCue({ ...cue, start, end }, opts);
    if (next && clamped.end > next.start) {
      return { ...clamped, end: Math.max(clamped.start + 0.2, next.start) };
    }
    return clamped;
  });
}

function clampCue(cue, { minDuration, maxDuration }) {
  let start = Number(cue.start);
  let end = Number(cue.end);
  if (!Number.isFinite(start)) start = 0;
  if (!Number.isFinite(end) || end <= start) end = start + estimateDuration(cue.text);
  const desired = Math.max(minDuration, Math.min(maxDuration, end - start));
  return { ...cue, start, end: start + desired };
}

function buildReport({ out, timingMode, chunks, cues, stats, timedTokenCount, scriptTokenCount }) {
  const weak = cues
    .map((cue, i) => ({ cue, i }))
    .filter(({ cue }) => cue.estimated || cue.confidence < 0.45);
  return {
    out,
    timingMode,
    summary: {
      cues: cues.length,
      confidence: round(stats.matchedTokens / Math.max(1, scriptTokenCount)),
      matchedTokens: stats.matchedTokens,
      scriptTokenCount,
      timedTokenCount,
      estimatedCues: cues.filter((cue) => cue.estimated).length,
      weakCues: weak.length,
    },
    weakCues: weak.map(({ cue, i }) => ({
      index: i + 1,
      start: round(cue.start),
      end: round(cue.end),
      confidence: round(cue.confidence),
      estimated: Boolean(cue.estimated),
      text: chunks[i],
    })),
  };
}

function tokenize(text) {
  const tokens = [];
  const re = /[\p{Script=Han}]|[a-zA-Z0-9]+/gu;
  for (const match of text.normalize("NFKC").toLowerCase().matchAll(re)) tokens.push(match[0]);
  return tokens;
}

function visibleLength(text) {
  return Array.from(text.replace(/\s/g, "")).length;
}

function estimateDuration(text) {
  return Math.max(0.8, Math.min(5.5, visibleLength(text) / 7));
}

function wrapSubtitle(text) {
  const chars = Array.from(text.trim());
  if (chars.length <= 24) return text.trim();
  const mid = Math.ceil(chars.length / 2);
  let split = mid;
  for (let i = mid; i > Math.max(0, mid - 8); i--) {
    if ("，、,.：: ".includes(chars[i])) {
      split = i + 1;
      break;
    }
  }
  return `${chars.slice(0, split).join("").trim()}\n${chars.slice(split).join("").trim()}`.trim();
}

function parseSrtTime(value) {
  const m = value.match(/(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/);
  if (!m) return NaN;
  return Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) + Number(m[4]) / 1000;
}

function formatSrtTime(seconds) {
  const msTotal = Math.max(0, Math.round(seconds * 1000));
  const ms = msTotal % 1000;
  const totalSec = Math.floor(msTotal / 1000);
  const s = totalSec % 60;
  const m = Math.floor(totalSec / 60) % 60;
  const h = Math.floor(totalSec / 3600);
  return `${pad(h)}:${pad(m)}:${pad(s)},${String(ms).padStart(3, "0")}`;
}

function round(value) {
  return Math.round(Number(value) * 1000) / 1000;
}

function pad(n) {
  return String(n).padStart(2, "0");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
