import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) args[key] = true;
    else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function readTextMaybeUtf16(file) {
  const bytes = readFileSync(file);
  if (bytes[0] === 0xff && bytes[1] === 0xfe) return bytes.subarray(2).toString("utf16le");
  if (bytes[0] === 0xfe && bytes[1] === 0xff) return bytes.subarray(2).swap16().toString("utf16le");
  return bytes.toString("utf8");
}

function normalize(text) {
  return text
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[\p{P}\p{S}]/gu, "");
}

function sourceIndexFromNorm(source, normIndex) {
  if (normIndex <= 0) return 0;
  let count = 0;
  for (let i = 0; i < source.length; i += 1) {
    if (normalize(source[i]).length) count += 1;
    if (count >= normIndex) return i;
  }
  return Math.max(0, source.length - 1);
}

function excerpt(text, index, before = 80, after = 160) {
  return text.slice(Math.max(0, index - before), Math.min(text.length, index + after));
}

function readAsrJson(file) {
  return JSON.parse(readTextMaybeUtf16(file).trim());
}

function extractTokenData(json, offset) {
  if (Array.isArray(json.tokens) && Array.isArray(json.timestamps)) {
    return {
      tokens: json.tokens.map((token) => String(token)),
      timestamps: json.timestamps.map((time) => Number(time) + offset),
    };
  }

  const wordItems = json.words || json.tokens || [];
  if (Array.isArray(wordItems) && wordItems.some((item) => typeof item === "object")) {
    return {
      tokens: wordItems.map((item) => String(item.word || item.text || item.token || "")),
      timestamps: wordItems.map((item) => Number(item.start ?? item.t0 ?? item.timestamp ?? 0) + offset),
    };
  }

  const segments = json.segments || [];
  if (Array.isArray(segments) && segments.length) {
    return {
      tokens: segments.map((segment) => String(segment.text || "").trim()).filter(Boolean),
      timestamps: segments.map((segment) => Number(segment.start ?? 0) + offset),
    };
  }

  return { tokens: [], timestamps: [] };
}

function readAsrChunks(asrDir) {
  const files = readdirSync(asrDir).filter((name) => name.endsWith(".json")).sort();
  let offset = 0;
  return files.map((name) => {
    const json = readAsrJson(join(asrDir, name));
    const duration = Number(json.duration || json.audio_duration || 0);
    const { tokens, timestamps } = extractTokenData(json, offset);
    const chunk = {
      name,
      text: String(json.text || json.transcript || ""),
      tokens,
      timestamps,
      duration,
      offset,
    };
    offset += duration;
    return chunk;
  });
}

function missingRuns(sourceNorm, asrNorm) {
  const chunkLen = 30;
  const runs = [];
  let current = [];
  for (let i = 0; i < sourceNorm.length; i += chunkLen) {
    const probe = sourceNorm.slice(i, i + Math.min(12, chunkLen));
    const hit = probe.length < 6 || asrNorm.includes(probe);
    if (!hit) current.push(i);
    else {
      if (current.length >= 2) runs.push([...current]);
      current = [];
    }
  }
  if (current.length >= 2) runs.push(current);
  return runs;
}

function tokenPauseCandidates(chunks) {
  const majorPunctuation = new Set(["。", "！", "？", "；", "："]);
  const candidates = [];
  for (const chunk of chunks) {
    for (let i = 1; i < chunk.tokens.length; i += 1) {
      if (!Number.isFinite(chunk.timestamps[i]) || !Number.isFinite(chunk.timestamps[i - 1])) continue;
      const gap = chunk.timestamps[i] - chunk.timestamps[i - 1];
      const prev = chunk.tokens[i - 1];
      const next = chunk.tokens[i];
      const prevEnd = prev.slice(-1);
      if (gap > 0.45 && !majorPunctuation.has(prevEnd)) {
        candidates.push({
          time: Number(chunk.timestamps[i].toFixed(2)),
          gap: Number(gap.toFixed(2)),
          text: `${prev} / ${next}`,
          chunk: chunk.name,
        });
      }
    }
  }
  return candidates;
}

function hardBreakCandidates(source, asr) {
  const hardPunctuation = /[。！？]/u;
  let normCount = 0;
  const candidates = [];
  for (let i = 0; i < asr.length; i += 1) {
    const ch = asr[i];
    if (normalize(ch).length) normCount += 1;
    if (!hardPunctuation.test(ch)) continue;
    const srcIndex = sourceIndexFromNorm(source, normCount);
    const nearby = source.slice(Math.max(0, srcIndex - 3), Math.min(source.length, srcIndex + 4));
    if (!hardPunctuation.test(nearby)) {
      candidates.push({
        normIndex: normCount,
        sourceExcerpt: excerpt(source, srcIndex, 60, 120),
        asrExcerpt: excerpt(asr, i, 60, 120),
      });
    }
  }
  return candidates.slice(0, 30);
}

function uniqueNumbers(text) {
  const pattern = /[0-9]+(?:\.[0-9]+)?|[一二三四五六七八九十百千万亿两]+/g;
  return [...new Set([...text.matchAll(pattern)].map((match) => match[0]))];
}

function audioStats(audioPath) {
  if (!audioPath || !existsSync(audioPath)) return ["Audio file not provided or not found."];
  try {
    const raw = execFileSync(
      "ffprobe",
      [
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=sample_rate,channels,codec_name:format=duration,size",
        "-of",
        "json",
        audioPath,
      ],
      { encoding: "utf8" },
    );
    const info = JSON.parse(raw);
    const stream = info.streams?.[0] || {};
    const format = info.format || {};
    return [
      `Duration: ${Number(format.duration || 0).toFixed(2)}s`,
      `Sample rate: ${stream.sample_rate || "(unknown)"} Hz`,
      `Channels: ${stream.channels || "(unknown)"}`,
      `Codec: ${stream.codec_name || "(unknown)"}`,
      `File size: ${format.size ? `${Math.round(Number(format.size) / 1024)} KB` : "(unknown)"}`,
    ];
  } catch (error) {
    return [`ffprobe unavailable or failed: ${error.message}`];
  }
}

const args = parseArgs(process.argv.slice(2));
if (!args["source-file"] || !args["asr-dir"]) {
  console.error("Usage: node qc_xiangongyun_tts.mjs --source-file work/source.txt --asr-dir work/asr-chunks --audio outputs/audio.wav --out work/qc.md");
  process.exit(2);
}

const source = readTextMaybeUtf16(args["source-file"]).replace(/^\uFEFF/, "");
const chunks = readAsrChunks(args["asr-dir"]);
const asr = chunks.map((chunk) => chunk.text).join("\n\n");
const sourceNorm = normalize(source);
const asrNorm = normalize(asr);
const missing = missingRuns(sourceNorm, asrNorm).map((run) => {
  const srcIndex = sourceIndexFromNorm(source, run[0]);
  return { startNorm: run[0], chunks: run.length, excerpt: excerpt(source, srcIndex) };
});
const pauseCandidates = tokenPauseCandidates(chunks).slice(0, 50);
const breakCandidates = hardBreakCandidates(source, asr);

const md = [
  "# Xiangongyun TTS QC Report",
  "",
  "## Technical Integrity",
  "",
  audioStats(args.audio).map((line) => `- ${line}`).join("\n"),
  "",
  "## Text Metrics",
  "",
  `- Source chars: ${source.length}`,
  `- ASR chars: ${asr.length}`,
  `- Source normalized chars: ${sourceNorm.length}`,
  `- ASR normalized chars: ${asrNorm.length}`,
  `- ASR chunks: ${chunks.length}`,
  `- Audio: ${args.audio || "(not provided)"}`,
  "",
  "## Start / End Check",
  "",
  `Source start: ${source.slice(0, 180)}`,
  "",
  `ASR start: ${asr.slice(0, 180)}`,
  "",
  `Source end: ${source.slice(-180)}`,
  "",
  `ASR end: ${asr.slice(-180)}`,
  "",
  "## Numbers",
  "",
  `Source: ${uniqueNumbers(source).join(", ") || "(none)"}`,
  "",
  `ASR: ${uniqueNumbers(asr).join(", ") || "(none)"}`,
  "",
  "## Possible Missing Sections",
  "",
  missing.length
    ? missing.map((item) => `- Around normalized char ${item.startNorm}: ${item.excerpt}`).join("\n")
    : "No large missing-section candidates found.",
  "",
  "## Possible Unnatural Sentence Breaks",
  "",
  breakCandidates.length
    ? breakCandidates.map((item) => `- ${item.sourceExcerpt}\n  ASR: ${item.asrExcerpt}`).join("\n")
    : "No hard-break candidates found.",
  "",
  "## Possible Bad Pauses",
  "",
  pauseCandidates.length
    ? pauseCandidates.map((item) => `- ${item.time}s gap ${item.gap}s: ${item.text} (${item.chunk})`).join("\n")
    : "No token gap candidates over 0.45s found.",
  "",
  "## Manual Listening Checklist",
  "",
  "- Listen to the first 60 seconds.",
  "- Listen to every hard-break candidate above.",
  "- Listen to every pause candidate above.",
  "- Listen to every paragraph opening.",
  "- Treat correct ASR text as insufficient when the phrase sounds chopped, robotic, or disconnected.",
].join("\n");

if (args.out) {
  writeFileSync(resolve(args.out), md, "utf8");
} else {
  console.log(md);
}
