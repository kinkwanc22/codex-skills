#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const DEFAULT_FFMPEG = process.platform === "win32"
  ? "C:\\Program Files\\AutoCutVideo\\ffmpeg.exe"
  : "ffmpeg";
const DEFAULT_FFPROBE = process.platform === "win32"
  ? "C:\\Program Files\\AutoCutVideo\\ffprobe.exe"
  : "ffprobe";

const args = parseArgs(process.argv.slice(2));
const input = args.input || args.i;
if (!input) {
  fail(
    "Missing --input. Example: node scripts/remove_silence_autocut_style.mjs --input outputs/tts.wav"
  );
}

const filterLevel = Number(args.filterLevel ?? args.level ?? -30);
const minSilenceLength = Number(args.minSilenceLength ?? args.interval ?? 0.3);
const minGapLength = Number(args.minGapLength ?? args.interval ?? 0.3);
const ffmpeg = args.ffmpeg || DEFAULT_FFMPEG;
const ffprobe = args.ffprobe || DEFAULT_FFPROBE;
const output =
  args.output ||
  args.o ||
  path.join("outputs", `${path.parse(input).name}.autocut-silence-filtered.wav`);

await mkdir(path.dirname(output), { recursive: true });

const duration = await probeDuration(ffprobe, input);
const detectLines = await detectSilence(ffmpeg, input, filterLevel, minSilenceLength);
const clips = computeClips(minGapLength, duration, detectLines);
const keepClips = clips.filter((clip) => clip.keep && clip.duration > 0.001);

if (keepClips.length === 0) {
  fail("No keepable audio clips remained after silence filtering.");
}

await renderAudio(ffmpeg, input, output, keepClips);

const removedSeconds = clips
  .filter((clip) => !clip.keep)
  .reduce((sum, clip) => sum + clip.duration, 0);

console.log(JSON.stringify(
  {
    input: path.resolve(input),
    output: path.resolve(output),
    duration: round6(duration),
    outputDurationEstimate: round6(duration - removedSeconds),
    removedSeconds: round6(removedSeconds),
    filterLevel,
    minSilenceLength,
    minGapLength,
    clips: clips.length,
    keptClips: keepClips.length,
  },
  null,
  2
));

function parseArgs(argv) {
  const parsed = {};
  for (let i = 0; i < argv.length; i++) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const eq = item.indexOf("=");
    if (eq !== -1) {
      parsed[item.slice(2, eq)] = item.slice(eq + 1);
    } else {
      const key = item.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith("--")) {
        parsed[key] = next;
        i++;
      } else {
        parsed[key] = true;
      }
    }
  }
  return parsed;
}

async function probeDuration(ffprobePath, src) {
  const result = await run(ffprobePath, [
    "-v",
    "error",
    "-show_entries",
    "format=duration",
    "-of",
    "default=noprint_wrappers=1:nokey=1",
    src,
  ]);
  const duration = Number(result.stdout.trim());
  if (!Number.isFinite(duration) || duration <= 0) {
    fail(`Could not read media duration from ${src}`);
  }
  return duration;
}

async function detectSilence(ffmpegPath, src, level, minLength) {
  const result = await run(ffmpegPath, [
    "-i",
    src,
    "-hide_banner",
    "-af",
    `silencedetect=n=${level}dB:d=${minLength}`,
    "-f",
    "null",
    "-",
  ]);
  return result.stderr
    .split(/\r?\n/g)
    .filter((line) => line.includes("silence_start") || line.includes("silence_duration"));
}

function computeClips(minGapLengthValue, duration, outputLines) {
  const silenceClips = collectSilenceClips(outputLines);
  if (silenceClips.length === 0) {
    return [{ start: 0, duration, keep: true }];
  }

  const paddedSilenceClips = [];
  const padding = minGapLengthValue / 2;
  for (const clip of silenceClips) {
    if (clip.duration > minGapLengthValue) {
      paddedSilenceClips.push({
        start: round6(clip.start + padding),
        duration: round6(clip.duration - padding),
        keep: false,
      });
    }
  }

  if (paddedSilenceClips.length === 0) {
    return [{ start: 0, duration, keep: true }];
  }

  const clips = [];
  for (let i = 0; i < paddedSilenceClips.length - 1; i++) {
    const silenceClip = paddedSilenceClips[i];
    clips.push(silenceClip);
    const clipStart = round6(silenceClip.start + silenceClip.duration);
    clips.push({
      start: clipStart,
      duration: round6(paddedSilenceClips[i + 1].start - clipStart),
      keep: true,
    });
  }

  const lastClip = paddedSilenceClips[paddedSilenceClips.length - 1];
  clips.push(lastClip);

  const firstClip = paddedSilenceClips[0];
  if (firstClip.start > 0) {
    clips.unshift({ start: 0, duration: firstClip.start, keep: true });
  }

  const lastClipEnd = round6(lastClip.start + lastClip.duration);
  if (lastClipEnd < duration) {
    clips.push({
      start: lastClipEnd,
      duration: round6(duration - lastClipEnd),
      keep: !lastClip.keep,
    });
  }

  for (const clip of clips) {
    if (clip.keep && clip.duration < 0.35) {
      clip.keep = false;
    }
  }

  return mergeClips(clips);
}

function collectSilenceClips(lines) {
  const clips = [];
  for (const text of lines) {
    const start = text.match(/silence_start:\s([-\d.]+)/);
    if (start) {
      clips.push({ start: Number(start[1]), duration: 0, keep: false });
      continue;
    }

    const durationMatch = text.match(/silence_duration:\s([-\d.]+)/);
    if (durationMatch && clips.length > 0) {
      clips.at(-1).duration = Number(durationMatch[1]);
    }
  }
  return clips.filter(
    (clip) => Number.isFinite(clip.start) && Number.isFinite(clip.duration) && clip.duration > 0
  );
}

function mergeClips(clips) {
  const mergedClips = [];
  let currentClip = null;
  for (const clip of clips) {
    if (currentClip === null) {
      currentClip = { ...clip };
    } else if (currentClip.keep === clip.keep) {
      currentClip.duration = round6(currentClip.duration + clip.duration);
    } else {
      mergedClips.push(currentClip);
      currentClip = { ...clip };
    }
  }
  if (currentClip !== null) {
    mergedClips.push(currentClip);
  }
  return mergedClips;
}

async function renderAudio(ffmpegPath, src, dest, keepClipsValue) {
  const filterParts = [];
  keepClipsValue.forEach((clip, index) => {
    const end = round6(clip.start + clip.duration);
    filterParts.push(
      `[0:a]atrim=start=${clip.start}:end=${end},asetpts=N/SR/TB[a${index}]`
    );
  });
  filterParts.push(
    `${keepClipsValue.map((_, index) => `[a${index}]`).join("")}concat=n=${
      keepClipsValue.length
    }:v=0:a=1[outa]`
  );

  await run(ffmpegPath, [
    "-y",
    "-hide_banner",
    "-i",
    src,
    "-filter_complex",
    filterParts.join(";"),
    "-map",
    "[outa]",
    "-c:a",
    "pcm_s16le",
    dest,
  ]);
}

async function run(command, commandArgs) {
  return await new Promise((resolve, reject) => {
    const child = spawn(command, commandArgs, { windowsHide: true });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`${command} exited with ${code}\n${stderr || stdout}`));
      }
    });
  });
}

function round6(num) {
  return Number(num.toFixed(6));
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
