---
name: jiepai-jianji
description: Local street-shot auto editing workflow for Chinese narration videos. Use when the user asks for 街拍剪辑, 街拍素材随机剪辑, 口播音频配素材, 按句尾切换素材, 静音点切换素材, 逐字对齐剪视频, or wants to turn a video-material folder plus narration audio plus script/docx into a 16:9 horizontal 30fps MP4.
---

# 街拍剪辑

## Goal

Create a 16:9 horizontal MP4 from:

- a folder of street-shot/B-roll video clips
- one narration audio file
- one narration script, usually `.docx`, `.txt`, or `.md`

Prefer hard cuts at real sentence endings. Use word timestamps from Whisper/faster-whisper when available, then choose cut points every 5-10 seconds near sentence endings and nearby silence points. Keep 30fps, 1920x1080, H.264, AAC audio, and no crossfade by default.

## Capabilities

- Resolve input directories into one audio file, one script file, and a pool of B-roll clips.
- Filter source clips by duration and bitrate before rendering.
- Detect narration silence points with FFmpeg.
- Read `.docx`, `.txt`, and `.md` narration scripts.
- Split scripts into sentence candidates.
- Optionally transcribe narration with faster-whisper word timestamps.
- Align script sentence endings to ASR word timestamps when `--timed-json` is available.
- Cut clips every 5-10 seconds near sentence endings and silence points.
- Randomize B-roll source clips while avoiding repeated adjacent source files when possible.
- Render 1920x1080 30fps H.264/AAC MP4 output.
- Write a `.manifest.json` with cut points, source clips, segment durations, and alignment stats.

## Resources

- `scripts/make_street_cut_video.py`: Main renderer. Selects source clips, calculates cut points, renders silent segments, concatenates them, adds narration audio, and writes a manifest.
- `scripts/transcribe_words.py`: Optional faster-whisper transcription helper. Generates word-level timestamp JSON for tighter sentence-end alignment.
- `agents/openai.yaml`: UI metadata for display name, short description, and default prompt.

## Default Paths

- Default Windows street-shot/B-roll material directory: `E:\工作用\视频素材\街拍片段`.
- When the user provides only narration audio and script, use this directory as `--videos` unless they name another material folder.
- Keep outputs in the current thread's `outputs/` folder unless the user asks for another destination.

## Requirements

- Use Python 3.
- Use FFmpeg and ffprobe, either on `PATH` or passed explicitly through `--ffmpeg` and `--ffprobe`.
- Use `faster-whisper` only when generating word timestamps with `scripts/transcribe_words.py`.
- On Windows, run validation or Chinese-output Python commands with `python -X utf8` if default GBK decoding causes Unicode errors.

## Workflow

1. Resolve inputs.
   - If the user provides a directory for audio, choose the most relevant audio file inside it.
   - If the user provides a directory for script, choose the most relevant `.docx`/`.txt`/`.md` inside it.
   - Use `rg --files`, `Get-ChildItem`, `ffprobe`, and short metadata checks before rendering.

2. Locate FFmpeg.
   - Prefer an explicit local FFmpeg path if already known in the thread.
   - Otherwise use `ffmpeg`/`ffprobe` on `PATH`.
   - On this Windows setup, a known working pair may be under `ffmpeg-bin\...\bin\ffmpeg.exe` and `ffprobe.exe`.

3. Generate word timestamps when the user asks for real alignment or when quality matters.
   - Run `scripts/transcribe_words.py` with a faster-whisper runtime.
   - Start with `base` for a quick test.
   - Use `medium` or `large-v3` for a more accurate final pass if the user accepts the slower runtime.

4. Render with `scripts/make_street_cut_video.py`.
   - Use `--cut-mode timed-sentence-silence` when a timed JSON exists.
   - Use `--cut-mode sentence-silence` when no timed JSON exists but the script should still influence cut points.
   - Use `--cut-mode silence` when only audio pauses should drive cuts.
   - Use `--min-source-duration 8` and `--min-source-bitrate 5000000` for cleaner material selection.
   - Keep `--fade-duration 0` unless the user explicitly asks for crossfade.

5. Verify before reporting done.
   - `ffprobe` the output video stream: width, height, frame rate, duration.
   - `ffprobe` the audio stream and format duration.
   - Inspect the generated `.manifest.json`.
   - Extract one preview frame and inspect it if visual verification is useful.
   - Report the output path, duration, segment count, and whether word-timestamp alignment was used.

## Commands

Example word timestamp pass:

```powershell
& "E:\path\to\python.exe" ".\scripts\transcribe_words.py" `
  --audio "E:\path\to\narration.wav" `
  --output ".\work\narration_words.json" `
  --model-size base `
  --language zh
```

Example final render:

```powershell
python ".\scripts\make_street_cut_video.py" `
  --videos "E:\工作用\视频素材\街拍片段" `
  --audio "E:\path\to\narration.wav" `
  --script "E:\path\to\script.docx" `
  --output ".\outputs\final_16x9_30fps.mp4" `
  --ffmpeg "C:\path\to\ffmpeg.exe" `
  --ffprobe "C:\path\to\ffprobe.exe" `
  --timed-json ".\work\narration_words.json" `
  --cut-mode timed-sentence-silence `
  --fps 30 `
  --width 1920 `
  --height 1080 `
  --min-source-duration 8 `
  --min-source-bitrate 5000000 `
  --fade-duration 0
```

## Quality Defaults

- Output: `1920x1080`, `30fps`, `libx264`, `yuv420p`, AAC.
- Segment cadence: choose cuts roughly every `5-10s`.
- Preferred cut target: true sentence end from word timestamps; fallback to nearby silence; fallback to regular timing.
- No transitions by default. The user disliked 0.15-0.25 second crossfade for this workflow.
- Add a small audio-duration cushion on the last segment so FFmpeg does not truncate narration.
- Use a random seed for reproducibility when iterating.

## Troubleshooting

- If no video clips pass the filters, lower `--min-source-duration` or `--min-source-bitrate`.
- If FFmpeg is not found, pass explicit `--ffmpeg` and `--ffprobe` paths.
- If sentence alignment quality is low, rerun transcription with `medium` or `large-v3`, or fall back to `--cut-mode sentence-silence`.
- If the output seems clipped, compare `audio_duration` and `output_duration` in the manifest.
- If validation fails with a UnicodeDecodeError on Windows, rerun with `python -X utf8`.

## Notes

- Whisper output for Chinese may use Traditional characters. Normalize Simplified/Traditional enough to map script characters to ASR characters before taking sentence-end timestamps.
- A high match ratio is helpful but not mandatory. For rough production, `base` may be acceptable; for tighter sentence endings, rerun transcription with `medium` or `large-v3`.
- Keep deliverables in the current thread's `outputs/` folder unless the user asks for another destination.
- Keep generated caches such as `__pycache__` out of the skill package when preparing a clean version.
