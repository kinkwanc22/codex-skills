---

display_name: 语音生成
description: Generate Chinese speech through the user's Xiangongyun Gradio TTS instance. Use when the user asks to generate, regenerate, synthesize, read aloud, TTS, 配音, 语音生成, or make audio using the Xiangongyun instance at wgpy1nwfc8h7xxk6, especially with the default voice 浩威青叔4.0.pt.
---

# 语音生成

Xiangongyun TTS workflow for Chinese speech generation.
Generate speech through the running Xiangongyun Gradio app:

```text
https://wgpy1nwfc8h7xxk6-80.container.x-gpu.com
```

Default settings:

```text
voice: 浩威青叔4.0.pt
speed: 1.0
output: wav
final output directory: E:\工作用\GARY素材音频\扩写长音频
```

## Workflow

1. Extract the text to synthesize from the user's request.
2. Use `浩威青叔4.0.pt` unless the user names another voice.
3. Use speed `1.0` unless the user gives a value from `0.5` to `2.0`.
4. Choose the synthesis strategy:
   - Short text or quick test: run `scripts/generate_xiangongyun_tts.mjs`.
   - Long narration: prefer `scripts/generate_hybrid_xiangongyun_tts.mjs`.
   - Full segmentation is a fallback only when long-body synthesis repeatedly misreads content.
5. Save final deliverable audio under `E:\工作用\GARY素材音频\扩写长音频` by default. Use the current project's `outputs/` directory only when the user explicitly asks for workspace-local output.
6. Automatically run the AutoCutVideo-style silence/pause filter on the generated WAV unless the user explicitly asks to keep the raw TTS audio.
7. Treat the filtered WAV as the final deliverable. Keep raw WAVs as intermediates under the current project's `work/` directory when possible; do not leave raw WAVs in the final output directory unless the user explicitly asks to keep them there.
8. Generate a matching `.srt` subtitle file for every final filtered WAV when source text is available. Use only original-script + ASR timestamp sequence alignment; never use proportional duration allocation. Save it next to the final WAV in `E:\工作用\GARY素材音频\扩写长音频` by default.
9. Return links to the filtered `.wav` and `.srt`, then summarize QC findings.

Do not echo API tokens or hidden credentials. This Gradio app does not require the Xiangongyun API token for TTS generation; it uses the public container URL.

## Recommended Long-Form Strategy

For long Chinese scripts, do **hybrid synthesis** by default:

1. Split only the opening hook, usually the first `200-300` Chinese characters or up to an explicit marker such as `好，我们直接进入正题。`.
2. Synthesize that intro as several small, natural chunks. This protects the most important opening where titles, promises, and dense value statements are easiest to misread.
3. Synthesize the remaining body as one long audio file to preserve continuity, tone, and emotional flow.
4. Concatenate the intro chunks and body WAV files with short silence:
   - intro chunk gap: about `320ms`
   - intro-to-body gap: about `650ms`
5. If a local problem is found, regenerate only the affected intro chunk or body file and rebuild the final WAV.

This is preferred over full-document segmentation because full segmentation can reduce small TTS mistakes but often creates a choppy "each paragraph starts over" feeling.

## Commands

Short text:

```powershell
node scripts/generate_xiangongyun_tts.mjs `
  --text "你好，欢迎来到仙宫云。" `
  --voice "浩威青叔4.0.pt" `
  --speed 1.0 `
  --out "work/xiangongyun-tts.raw.wav"
```

Long narration, hybrid mode:

```powershell
node scripts/generate_hybrid_xiangongyun_tts.mjs `
  --source-file "work/source.txt" `
  --intro-end-marker "好，我们直接进入正题。" `
  --voice "浩威青叔4.0.pt" `
  --speed 1.0 `
  --work-dir "work/hybrid-tts" `
  --out "work/xiangongyun-hybrid.raw.wav"
```

If there is no reliable intro marker, use `--intro-chars 280` and let the script split at the nearest sentence boundary:

```powershell
node scripts/generate_hybrid_xiangongyun_tts.mjs `
  --source-file "work/source.txt" `
  --intro-chars 280 `
  --out "work/xiangongyun-hybrid.raw.wav"
```

If `node` is unavailable, use the bundled Node runtime if present in the workspace.

## AutoCutVideo Silence Filtering

After every successful WAV generation, automatically remove pauses/silence with the same rule the user selected in AutoCutVideo:

```text
custom rule: 自定义规则2
filter level: -30 dB
segment interval: 0.3 seconds
```

Use `scripts/remove_silence_autocut_style.mjs` from this skill when it is available. It calls the installed AutoCutVideo binaries directly:

```text
C:\Program Files\AutoCutVideo\ffmpeg.exe
C:\Program Files\AutoCutVideo\ffprobe.exe
```

Recommended command after generating `work/raw.wav`:

```powershell
node C:\Users\Administrator\.codex\skills\xiangongyun-tts\scripts\remove_silence_autocut_style.mjs `
  --input "work/raw.wav" `
  --output "E:\工作用\GARY素材音频\扩写长音频\final.filtered.wav" `
  --filterLevel -30 `
  --interval 0.3
```

If plain `node` is blocked or unavailable on Windows, use the bundled Node runtime already present in the workspace when available. If AutoCutVideo is not installed at `C:\Program Files\AutoCutVideo`, skip the filter, return the raw WAV, and clearly tell the user that AutoCutVideo post-processing could not be run.
## Post-Generation QC

Always offer or run QC for long-form narration before calling the audio final. QC must check both content accuracy and listening flow:

1. **Technical integrity**: duration, sample rate, file size, and abnormal silence.
2. **Content match**: ASR transcript vs source text for missing sections, skipped ending, number changes, and obvious misreads.
3. **Sentence-flow issues**: detect places where the audio/ASR creates a hard sentence break but the source only has a comma or no punctuation. Treat these as likely "气口不自然 / 没连起来读" candidates.
4. **Pause placement**: flag token timestamp gaps over `0.45s` that do not land near `。！？；：` or a paragraph boundary.
5. **Manual spot-check**: listen to the first 60 seconds, every flagged candidate, every paragraph opening, and the intro-to-body join. ASR can miss prosody problems when the words are still correct.

Use the local ASR skill/tooling when available. If using `coli asr`, split audio into 2-minute chunks first for long files to avoid memory errors:

```powershell
ffmpeg -y -i "outputs/audio.wav" -f segment -segment_time 120 -c copy "work/asr-chunks/chunk_%03d.wav"
```

Then transcribe each chunk and run:

```powershell
node scripts/qc_xiangongyun_tts.mjs `
  --source-file "work/source.txt" `
  --asr-dir "work/asr-chunks" `
  --audio "outputs/audio.wav" `
  --out "work/tts-qc-report.md"
```

If `coli asr` writes UTF-16 JSON on Windows, the QC script handles it.

Important: content-equivalence QC is not enough. If the user asks about "句子内部断开", "气口不自然", "没有连起来读", or "听感质检", explicitly inspect sentence-flow candidates and, when possible, replay the surrounding audio region.

## SRT Subtitle Generation

For long-form narration, generate an SRT subtitle after the final filtered WAV is ready.

1. Use the original source text as subtitle text. Do not use raw ASR text as the subtitle body because ASR often introduces homophone mistakes such as `术/数`, `Gary/gry`, or `群里见/群里间`.
2. Use ASR only as the timing source. For `coli asr` output in `{ tokens, timestamps }` format, align the original source-token sequence against the ASR-token sequence, then assign each subtitle chunk to the matched ASR timestamps.
3. Do **not** use proportional duration allocation, average time distribution, or character-count time spreading. If source-to-ASR sequence alignment fails or has poor coverage, stop and report the subtitle generation as failed; rerun ASR or request manual handling instead of emitting a fake-timed SRT.
4. Use Chinese-friendly subtitle chunks, usually `18-24` Chinese characters per cue, and split preferably at punctuation or natural phrase boundaries.
5. Inspect the generated SRT for empty subtitles, time overlap, timing collapse near the beginning, garbled ASR text in subtitle bodies, and an ending cue that reaches the final sentence of the source text.
6. Save the `.srt` next to the final `.filtered.wav` using the same basename.

## Available Voices

- 使用参考音频
- 疗愈育儿.pt
- 徐健君.pt
- 陈一言.pt
- 4.27Gary.pt
- 4.0混剪.pt
- 超超女课确定版.pt
- GARY.pt
- 浩威Gary.pt
- 浩威青叔4.0.pt
- 浩威女课.pt

For `使用参考音频`, upload the reference audio through Gradio first or extend the script with Gradio file upload support. Only use reference audio the user owns or is authorized to use.

## Implementation Notes

The Gradio endpoint is queue-based:

- Join: `POST /gradio_api/queue/join`
- Stream: `GET /gradio_api/queue/data?session_hash=...`
- Function index: `3`
- Trigger id: `14`
- Data order: `[voice, reference_audio_or_null, text, speed]`

Use the queue protocol instead of `/gradio_api/call/infer`; `/call/infer` may return a misleading `404: Not Found` even when the queue protocol works.


