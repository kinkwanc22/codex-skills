import { createWriteStream } from "node:fs";
import { mkdir, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { pipeline } from "node:stream/promises";

const BASE_URL = "https://wgpy1nwfc8h7xxk6-80.container.x-gpu.com";
const DEFAULT_VOICE = "浩威青叔4.0.pt";
const DEFAULT_SPEED = 1.0;

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function usage() {
  return [
    "Usage:",
    '  node scripts/generate_xiangongyun_tts.mjs --text "文本" --out outputs/audio.wav',
    "  node scripts/generate_xiangongyun_tts.mjs --text-file work/text.txt --out outputs/audio.wav",
    "",
    "Options:",
    `  --voice      Voice name, default: ${DEFAULT_VOICE}`,
    `  --speed      0.5-2.0, default: ${DEFAULT_SPEED}`,
    "  --text-file  UTF-8 text file to synthesize",
    "  --out        Output .wav path, default: outputs/xiangongyun-tts.wav",
  ].join("\n");
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

  if (error) {
    throw new Error(`TTS failed: ${JSON.stringify(error)}`);
  }
  if (!completed) {
    throw new Error(`TTS did not complete. Last stream data: ${streamText.slice(-1000)}`);
  }

  const output = completed.output?.data;
  const fileUrl = output?.[1]?.[0]?.url || output?.[0]?.url;
  if (!fileUrl) {
    throw new Error(`No output file URL in completed event: ${JSON.stringify(completed)}`);
  }
  return fileUrl;
}

async function downloadFile(url, outPath) {
  const response = await fetch(url);
  if (!response.ok || !response.body) {
    throw new Error(`Download failed: HTTP ${response.status} ${await response.text()}`);
  }

  const absoluteOut = resolve(outPath);
  await mkdir(dirname(absoluteOut), { recursive: true });
  await pipeline(response.body, createWriteStream(absoluteOut));
  return absoluteOut;
}

const args = parseArgs(process.argv.slice(2));
if (args.help || (!args.text && !args["text-file"])) {
  console.log(usage());
  process.exit(args.help ? 0 : 2);
}

const text = args["text-file"]
  ? await readFile(String(args["text-file"]), "utf8")
  : String(args.text);
const voice = String(args.voice || DEFAULT_VOICE);
const speed = Number(args.speed || DEFAULT_SPEED);
const out = String(args.out || "outputs/xiangongyun-tts.wav");

if (!Number.isFinite(speed) || speed < 0.5 || speed > 2.0) {
  throw new Error("--speed must be a number from 0.5 to 2.0");
}
if (!text.trim()) {
  throw new Error("No text to synthesize");
}

const job = await submitJob({ text, voice, speed });
const fileUrl = await pollJob(job);
const savedPath = await downloadFile(fileUrl, out);

console.log(JSON.stringify({ savedPath, fileUrl, voice, speed }, null, 2));
