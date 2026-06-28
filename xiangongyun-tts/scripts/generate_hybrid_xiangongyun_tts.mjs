import { createWriteStream } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";
import { pipeline } from "node:stream/promises";

const BASE_URL = "https://wgpy1nwfc8h7xxk6-80.container.x-gpu.com";
const DEFAULT_VOICE = "浩威青叔4.0.pt";
const DEFAULT_SPEED = 1.0;
const DEFAULT_INTRO_CHARS = 280;
const DEFAULT_INTRO_GAP_MS = 320;
const DEFAULT_BODY_GAP_MS = 650;

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

function usage() {
  return [
    "Usage:",
    "  node scripts/generate_hybrid_xiangongyun_tts.mjs --source-file work/source.txt --out outputs/audio.wav",
    "",
    "Options:",
    `  --voice             Voice name, default: ${DEFAULT_VOICE}`,
    `  --speed             0.5-2.0, default: ${DEFAULT_SPEED}`,
    `  --intro-chars       Intro length when no marker is provided, default: ${DEFAULT_INTRO_CHARS}`,
    "  --intro-end-marker  Prefer splitting after this marker, e.g. \"好，我们直接进入正题。\"",
    "  --work-dir          Segment work dir, default: work/hybrid-tts",
    `  --intro-gap-ms      Silence between intro chunks, default: ${DEFAULT_INTRO_GAP_MS}`,
    `  --body-gap-ms       Silence between intro and body, default: ${DEFAULT_BODY_GAP_MS}`,
  ].join("\n");
}

function splitSentences(text) {
  const sentences = [];
  const pattern = /[^。！？!?；;]+[。！？!?；;]?/g;
  for (const match of text.matchAll(pattern)) {
    const sentence = match[0].trim();
    if (sentence) sentences.push(sentence);
  }
  return sentences.length ? sentences : [text.trim()].filter(Boolean);
}

function findIntroBoundary(text, { marker, introChars }) {
  if (marker) {
    const index = text.indexOf(marker);
    if (index >= 0) return index + marker.length;
  }

  const target = Math.max(80, introChars);
  const searchEnd = Math.min(text.length, target + 180);
  const window = text.slice(0, searchEnd);
  let best = -1;
  for (const match of window.matchAll(/[。！？!?]/g)) {
    if (match.index + 1 >= Math.max(80, target - 120)) best = match.index + 1;
  }
  return best > 0 ? best : Math.min(text.length, target);
}

function splitIntro(intro) {
  const paragraphs = intro.split(/\r?\n\s*\r?\n/u).map((p) => p.trim()).filter(Boolean);
  const units = paragraphs.length ? paragraphs : splitSentences(intro);
  const chunks = [];
  let current = "";

  for (const unit of units) {
    const pieces = unit.length > 110 ? splitSentences(unit) : [unit];
    for (const piece of pieces) {
      const next = current ? `${current}${piece}` : piece;
      if (current && next.length > 120) {
        chunks.push(current.trim());
        current = piece;
      } else {
        current = next;
      }
    }
    if (current && current.length >= 45) {
      chunks.push(current.trim());
      current = "";
    }
  }
  if (current.trim()) chunks.push(current.trim());
  return chunks.filter(Boolean);
}

async function submitJob({ text, voice, speed }) {
  const sessionHash = Math.random().toString(36).slice(2);
  const response = await fetch(`${BASE_URL}/gradio_api/queue/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: [voice, null, text, speed],
      event_data: null,
      fn_index: 3,
      trigger_id: 14,
      session_hash: sessionHash,
    }),
  });

  if (!response.ok) {
    throw new Error(`Queue join failed: HTTP ${response.status} ${await response.text()}`);
  }

  const body = await response.json();
  if (!body.event_id) {
    throw new Error(`Queue join did not return event_id: ${JSON.stringify(body)}`);
  }

  return { eventId: body.event_id, sessionHash };
}

async function pollJob({ sessionHash, eventId }) {
  const response = await fetch(
    `${BASE_URL}/gradio_api/queue/data?session_hash=${encodeURIComponent(sessionHash)}`,
  );

  if (!response.ok) {
    throw new Error(`Queue data failed: HTTP ${response.status} ${await response.text()}`);
  }

  const streamText = await response.text();
  const dataLines = streamText
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data: "))
    .map((line) => line.slice("data: ".length));

  let completed = null;
  let error = null;
  for (const line of dataLines) {
    let event;
    try {
      event = JSON.parse(line);
    } catch {
      continue;
    }
    if (event.event_id && event.event_id !== eventId) continue;
    if (event.msg === "process_completed") completed = event;
    if (event.msg === "process_failed" || event.success === false) error = event;
  }

  if (error) throw new Error(`TTS failed: ${JSON.stringify(error)}`);
  if (!completed) throw new Error(`TTS did not complete. Last stream data: ${streamText.slice(-1000)}`);

  const output = completed.output?.data;
  const fileUrl = output?.[1]?.[0]?.url || output?.[0]?.url;
  if (!fileUrl) throw new Error(`No output file URL in completed event: ${JSON.stringify(completed)}`);
  return fileUrl;
}

async function downloadFile(url, outPath) {
  const response = await fetch(url);
  if (!response.ok || !response.body) {
    throw new Error(`Download failed: HTTP ${response.status} ${await response.text()}`);
  }
  await mkdir(dirname(outPath), { recursive: true });
  await pipeline(response.body, createWriteStream(outPath));
}

function readWav(buffer, file) {
  if (buffer.toString("ascii", 0, 4) !== "RIFF" || buffer.toString("ascii", 8, 12) !== "WAVE") {
    throw new Error(`${file} is not a WAV file`);
  }
  let pos = 12;
  let fmt = null;
  let data = null;
  while (pos + 8 <= buffer.length) {
    const id = buffer.toString("ascii", pos, pos + 4);
    const size = buffer.readUInt32LE(pos + 4);
    const start = pos + 8;
    if (id === "fmt ") {
      fmt = {
        audioFormat: buffer.readUInt16LE(start),
        channels: buffer.readUInt16LE(start + 2),
        sampleRate: buffer.readUInt32LE(start + 4),
        byteRate: buffer.readUInt32LE(start + 8),
        blockAlign: buffer.readUInt16LE(start + 12),
        bitsPerSample: buffer.readUInt16LE(start + 14),
      };
    }
    if (id === "data") data = buffer.subarray(start, start + size);
    pos = start + size + (size % 2);
  }
  if (!fmt || !data) throw new Error(`${file} missing fmt or data chunk`);
  return { fmt, data };
}

function wavHeader(fmt, dataSize) {
  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + dataSize, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(fmt.audioFormat, 20);
  header.writeUInt16LE(fmt.channels, 22);
  header.writeUInt32LE(fmt.sampleRate, 24);
  header.writeUInt32LE(fmt.byteRate, 28);
  header.writeUInt16LE(fmt.blockAlign, 32);
  header.writeUInt16LE(fmt.bitsPerSample, 34);
  header.write("data", 36);
  header.writeUInt32LE(dataSize, 40);
  return header;
}

async function concatWavs(parts, outPath) {
  const buffers = [];
  let referenceFmt = null;
  let dataSize = 0;

  for (const part of parts) {
    const parsed = readWav(await readFile(part.file), part.file);
    if (!referenceFmt) referenceFmt = parsed.fmt;
    if (JSON.stringify(referenceFmt) !== JSON.stringify(parsed.fmt)) {
      throw new Error(`WAV format mismatch: ${part.file}`);
    }
    buffers.push(parsed.data);
    dataSize += parsed.data.length;

    if (part.gapMs > 0) {
      const silenceBytes =
        Math.round((referenceFmt.byteRate * part.gapMs) / 1000 / referenceFmt.blockAlign) *
        referenceFmt.blockAlign;
      const silence = Buffer.alloc(silenceBytes);
      buffers.push(silence);
      dataSize += silence.length;
    }
  }

  await mkdir(dirname(outPath), { recursive: true });
  await writeFile(outPath, Buffer.concat([wavHeader(referenceFmt, dataSize), ...buffers]));
  return referenceFmt;
}

const args = parseArgs(process.argv.slice(2));
if (args.help || !args["source-file"] || !args.out) {
  console.log(usage());
  process.exit(args.help ? 0 : 2);
}

const voice = String(args.voice || DEFAULT_VOICE);
const speed = Number(args.speed || DEFAULT_SPEED);
const introChars = Number(args["intro-chars"] || DEFAULT_INTRO_CHARS);
const introGapMs = Number(args["intro-gap-ms"] || DEFAULT_INTRO_GAP_MS);
const bodyGapMs = Number(args["body-gap-ms"] || DEFAULT_BODY_GAP_MS);
if (!Number.isFinite(speed) || speed < 0.5 || speed > 2.0) {
  throw new Error("--speed must be a number from 0.5 to 2.0");
}

const source = (await readFile(String(args["source-file"]), "utf8")).trim();
if (!source) throw new Error("Source file is empty");

const boundary = findIntroBoundary(source, {
  marker: args["intro-end-marker"] ? String(args["intro-end-marker"]) : "",
  introChars,
});
const introText = source.slice(0, boundary).trim();
const bodyText = source.slice(boundary).trim();
if (!introText || !bodyText) throw new Error("Hybrid split produced empty intro or body");

const introChunks = splitIntro(introText);
const workDir = resolve(String(args["work-dir"] || "work/hybrid-tts"));
await mkdir(workDir, { recursive: true });
await writeFile(resolve(workDir, "intro.txt"), introText, "utf8");
await writeFile(resolve(workDir, "body.txt"), bodyText, "utf8");
await writeFile(
  resolve(workDir, "manifest.json"),
  JSON.stringify(
    {
      sourceFile: args["source-file"],
      out: args.out,
      voice,
      speed,
      introChars: introText.length,
      bodyChars: bodyText.length,
      introChunks: introChunks.map((text, index) => ({ index: index + 1, chars: text.length, text })),
      introGapMs,
      bodyGapMs,
    },
    null,
    2,
  ),
  "utf8",
);

console.log(
  JSON.stringify(
    {
      action: "hybrid-split",
      sourceChars: source.length,
      introChars: introText.length,
      bodyChars: bodyText.length,
      introChunks: introChunks.length,
      workDir,
    },
    null,
    2,
  ),
);

const parts = [];
for (let i = 0; i < introChunks.length; i += 1) {
  const outPath = resolve(workDir, `intro-${String(i + 1).padStart(3, "0")}.wav`);
  console.log(`[intro ${i + 1}/${introChunks.length}] ${introChunks[i].length} chars -> ${basename(outPath)}`);
  const job = await submitJob({ text: introChunks[i], voice, speed });
  const fileUrl = await pollJob(job);
  await downloadFile(fileUrl, outPath);
  parts.push({ file: outPath, gapMs: i === introChunks.length - 1 ? bodyGapMs : introGapMs });
}

const bodyPath = resolve(workDir, "body.wav");
console.log(`[body] ${bodyText.length} chars -> ${basename(bodyPath)}`);
const bodyJob = await submitJob({ text: bodyText, voice, speed });
const bodyFileUrl = await pollJob(bodyJob);
await downloadFile(bodyFileUrl, bodyPath);
parts.push({ file: bodyPath, gapMs: 0 });

const fmt = await concatWavs(parts, resolve(String(args.out)));
console.log(JSON.stringify({ savedPath: resolve(String(args.out)), voice, speed, parts: parts.length, format: fmt }, null, 2));
