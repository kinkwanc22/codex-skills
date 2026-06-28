#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = parseArgs(process.argv.slice(2));
if (!args.script || !args.timed || !args.out) {
  fail("Usage: node scripts/align_srt.mjs --script copy.txt --timed whisper.json|input.srt --out output.srt [--max-chars 32]");
}

const scriptText = fs.readFileSync(args.script, "utf8").replace(/^\uFEFF/, "").trim();
const timedText = fs.readFileSync(args.timed, "utf8").replace(/^\uFEFF/, "").trim();
const maxChars = Number(args["max-chars"] ?? 32);
const minDuration = Number(args["min-duration"] ?? 0.7);
const maxDuration = Number(args["max-duration"] ?? 6);

if (!scriptText) fail("Script is empty.");
if (!timedText) fail("Timed input is empty.");

const timed = loadTimedInput(args.timed, timedText);
const chunks = chunkScript(scriptText, maxChars);
if (!chunks.length) fail("No subtitle chunks could be created from script.");

let cues;
let timingMode;
if (timed.words.length >= Math.max(4, chunks.length)) {
  cues = alignWithWords(chunks, timed.words, { minDuration, maxDuration });
  timingMode = "word";
} else {
  cues = alignWithSegments(chunks, timed.segments, { minDuration, maxDuration });
  timingMode = "segment";
}

const srt = cues.map((cue, i) => {
  const start = formatSrtTime(cue.start);
  const end = formatSrtTime(Math.max(cue.end, cue.start + 0.2));
  return `${i + 1}\n${start} --> ${end}\n${wrapSubtitle(cue.text)}\n`;
}).join("\n");

fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
fs.writeFileSync(args.out, srt, "utf8");
console.log(JSON.stringify({
  out: path.resolve(args.out),
  cues: cues.length,
  timingMode,
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
  if (/\.srt$/i.test(filename)) return loadSrt(text);
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
      for (const token of tokenize(raw)) words.push({ token, start: ws, end: we });
    }
  }
  if (!segments.length && words.length) {
    segments.push({ start: words[0].start, end: words[words.length - 1].end, text: "" });
  }
  if (!segments.length) fail("Timed JSON needs segments with start/end values.");
  return { segments, words };
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

function alignWithWords(chunks, words, opts) {
  const scriptTokens = chunks.map((text) => ({ text, tokens: tokenize(text) }));
  const tokenTimes = [];
  let cursor = 0;
  for (const chunk of scriptTokens) {
    const times = [];
    for (const token of chunk.tokens) {
      const found = findNext(words, token, cursor, 120);
      if (found >= 0) {
        times.push(words[found]);
        cursor = found + 1;
      }
    }
    tokenTimes.push(times);
  }
  return tokenTimes.map((times, i) => {
    if (times.length) {
      return clampCue({ text: chunks[i], start: times[0].start, end: times[times.length - 1].end }, opts);
    }
    const prev = i > 0 ? tokenTimes[i - 1].at(-1) : null;
    const next = tokenTimes.slice(i + 1).find((x) => x.length)?.[0] ?? null;
    const start = prev ? prev.end : (next ? Math.max(0, next.start - 2) : words[0].start);
    const end = next ? next.start : Math.min(words.at(-1).end, start + estimateDuration(chunks[i]));
    return clampCue({ text: chunks[i], start, end }, opts);
  });
}

function findNext(words, token, cursor, windowSize) {
  const end = Math.min(words.length, cursor + windowSize);
  for (let i = cursor; i < end; i++) if (words[i].token === token) return i;
  return -1;
}

function alignWithSegments(chunks, segments, opts) {
  const totalChars = chunks.reduce((sum, c) => sum + visibleLength(c), 0) || chunks.length;
  const start = segments[0].start;
  const end = segments[segments.length - 1].end;
  const totalDuration = Math.max(0.1, end - start);
  let t = start;
  return chunks.map((text, i) => {
    const isLast = i === chunks.length - 1;
    const share = visibleLength(text) / totalChars;
    const duration = isLast ? end - t : totalDuration * share;
    const cue = clampCue({ text, start: t, end: t + duration }, opts);
    t = cue.end;
    return cue;
  });
}

function clampCue(cue, { minDuration, maxDuration }) {
  let start = Number(cue.start);
  let end = Number(cue.end);
  if (!Number.isFinite(start)) start = 0;
  if (!Number.isFinite(end) || end <= start) end = start + estimateDuration(cue.text);
  const duration = Math.max(minDuration, Math.min(maxDuration, end - start));
  return { text: cue.text, start, end: start + duration };
}

function tokenize(text) {
  const tokens = [];
  const re = /[\p{Script=Han}]|[a-zA-Z0-9]+/gu;
  for (const match of text.toLowerCase().matchAll(re)) tokens.push(match[0]);
  return tokens;
}

function visibleLength(text) {
  return Array.from(text.replace(/\s/g, "")).length;
}

function estimateDuration(text) {
  return Math.max(0.8, Math.min(6, visibleLength(text) / 7));
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

function pad(n) {
  return String(n).padStart(2, "0");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
