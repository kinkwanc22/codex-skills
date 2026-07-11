import { createWriteStream } from "node:fs";
import { mkdir, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { pipeline } from "node:stream/promises";

const DEFAULT_BASE_URL = "https://wgpy1nwfc8h7xxk6-80.container.x-gpu.com";
const DEFAULT_VOICE = "浩威青叔4.0.pt";
const DEFAULT_SPEED = 1.0;
const DEFAULT_READY_ATTEMPTS = 12;
const DEFAULT_RETRY_ATTEMPTS = 6;
const DEFAULT_RETRY_DELAY_MS = 5000;
const RETRYABLE_HTTP_STATUS = new Set([429, 502, 503, 504]);

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
    `  --base-url   Gradio base URL, default: ${DEFAULT_BASE_URL}`,
    `  --ready-attempts WebUI readiness checks, default: ${DEFAULT_READY_ATTEMPTS}`,
    `  --retry-attempts Queue HTTP retries, default: ${DEFAULT_RETRY_ATTEMPTS}`,
    `  --retry-delay-ms Delay between retries, default: ${DEFAULT_RETRY_DELAY_MS}`,
  ].join("\n");
}

function sleep(ms) {
  return new Promise((resolvePromise) => setTimeout(resolvePromise, ms));
}

async function fetchWithRetry(url, options, { label, attempts, delayMs }) {
  let lastError = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, options);
      if (!RETRYABLE_HTTP_STATUS.has(response.status) || attempt === attempts) return response;
      await response.arrayBuffer();
      console.warn(`[retry ${attempt}/${attempts}] ${label}: HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
      if (attempt === attempts) throw error;
      console.warn(`[retry ${attempt}/${attempts}] ${label}: ${error.message}`);
    }
    await sleep(delayMs);
  }
  throw lastError || new Error(`${label} failed after ${attempts} attempts`);
}

async function waitForWebUi({ baseUrl, attempts, delayMs }) {
  let lastStatus = "unreachable";
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(`${baseUrl}/`);
      lastStatus = `HTTP ${response.status}`;
      if (response.ok) {
        const html = await response.text();
        if (html.includes("gradio") || html.includes("请输入目标文本") || html.includes("生成语音")) {
          console.log(`[ready] Gradio WebUI available after ${attempt} check(s)`);
          return;
        }
        lastStatus = "HTTP 200 without Gradio app markers";
      } else {
        await response.arrayBuffer();
      }
    } catch (error) {
      lastStatus = error.message;
    }
    if (attempt < attempts) {
      console.log(`[wait ${attempt}/${attempts}] Gradio not ready: ${lastStatus}`);
      await sleep(delayMs);
    }
  }
  throw new Error(`Gradio WebUI not ready after ${attempts} checks: ${lastStatus}`);
}

async function submitJob({ text, voice, speed, baseUrl, retryAttempts, retryDelayMs }) {
  const sessionHash = Math.random().toString(36).slice(2);
  const response = await fetchWithRetry(
    `${baseUrl}/gradio_api/queue/join`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        data: [voice, null, text, speed],
        event_data: null,
        fn_index: 3,
        trigger_id: 14,
        session_hash: sessionHash,
      }),
    },
    { label: "queue join", attempts: retryAttempts, delayMs: retryDelayMs },
  );

  if (!response.ok) {
    throw new Error(`Queue join failed: HTTP ${response.status} ${await response.text()}`);
  }

  const body = await response.json();
  if (!body.event_id) {
    throw new Error(`Queue join did not return event_id: ${JSON.stringify(body)}`);
  }

  return { eventId: body.event_id, sessionHash };
}

async function pollJob({ sessionHash, eventId, baseUrl, retryAttempts, retryDelayMs }) {
  const response = await fetchWithRetry(
    `${baseUrl}/gradio_api/queue/data?session_hash=${encodeURIComponent(sessionHash)}`,
    {},
    { label: "queue stream", attempts: retryAttempts, delayMs: retryDelayMs },
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
const baseUrl = String(args["base-url"] || DEFAULT_BASE_URL).replace(/\/+$/u, "");
const readyAttempts = Number(args["ready-attempts"] || DEFAULT_READY_ATTEMPTS);
const retryAttempts = Number(args["retry-attempts"] || DEFAULT_RETRY_ATTEMPTS);
const retryDelayMs = Number(args["retry-delay-ms"] || DEFAULT_RETRY_DELAY_MS);

if (!Number.isFinite(speed) || speed < 0.5 || speed > 2.0) {
  throw new Error("--speed must be a number from 0.5 to 2.0");
}
if (!text.trim()) {
  throw new Error("No text to synthesize");
}
if (!Number.isInteger(readyAttempts) || readyAttempts < 1) throw new Error("--ready-attempts must be >= 1");
if (!Number.isInteger(retryAttempts) || retryAttempts < 1) throw new Error("--retry-attempts must be >= 1");
if (!Number.isFinite(retryDelayMs) || retryDelayMs < 0) throw new Error("--retry-delay-ms must be >= 0");

await waitForWebUi({ baseUrl, attempts: readyAttempts, delayMs: retryDelayMs });
const job = await submitJob({ text, voice, speed, baseUrl, retryAttempts, retryDelayMs });
const fileUrl = await pollJob({ ...job, baseUrl, retryAttempts, retryDelayMs });
const savedPath = await downloadFile(fileUrl, out);

console.log(JSON.stringify({ savedPath, fileUrl, voice, speed }, null, 2));
