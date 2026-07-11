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
final output directory: /Users/kin/工作用（同步）/GARY素材音频/扩写长音频
```

## Xiangongyun Instance Preflight

Before generating TTS, automatically make sure the user's Xiangongyun `语音生成` instance is running through the logged-in Chrome console.

Do not use the Xiangongyun Open API for this workflow. The stable path is the original Chrome console plus the Gradio queue.

Default console and service URLs:

```text
console: https://www.xiangongyun.com/console/instance
instance name: 语音生成
instance id prefix: WGPY****XXK6
webui: https://wgpy1nwfc8h7xxk6-80.container.x-gpu.com/
default GPU: RTX 4090 D
default GPU count: 1
```

Chrome preflight:

1. Open the Xiangongyun console in Chrome: `https://www.xiangongyun.com/console/instance`.
2. Locate the instance named `语音生成`.
3. If it is already `运行中`, open its `WeBUi` / Gradio URL and continue TTS generation.
4. If it is `已关机`, automatically click `开机`.
5. In the startup popover, keep the default `RTX 4090 D` and `1` GPU unless the user explicitly requested another configuration.
6. Click `确认开机` without asking the user again. The user has approved this recurring default behavior.
7. Wait until the instance state becomes `运行中` and the `WeBUi` link is available.
8. Open `https://wgpy1nwfc8h7xxk6-80.container.x-gpu.com/` and confirm the Gradio page shows `请输入目标文本` and `生成语音` before running the TTS script.
9. Treat `运行中` as container state only. The generation script must still wait for an HTTP 200 Gradio page before joining the queue.

Boundaries:

- Do not create a new instance automatically.
- Do not recharge the account automatically.
- Do not switch to a more expensive GPU automatically.
- Do not change the instance image or persistent configuration automatically.
- If login, CAPTCHA, payment, verification, or account-risk prompts appear, stop and ask the user to handle that step.
- If the WebUi URL is blocked or unavailable after the instance is `运行中`, report the blocker instead of guessing another service URL.

## Workflow

1. Run the Xiangongyun Instance Preflight above and confirm the `语音生成` Gradio WebUi is reachable.
2. Extract the text to synthesize from the user's request, pasted text, or provided document.
3. Use `浩威青叔4.0.pt` unless the user names another voice.
4. Use speed `1.0` unless the user gives a value from `0.5` to `2.0`.
5. Choose the synthesis strategy:
   - Short text or quick test: run `scripts/generate_xiangongyun_tts.mjs`.
   - Long narration: prefer `scripts/generate_hybrid_xiangongyun_tts.mjs`.
   - Full segmentation is a fallback only when long-body synthesis repeatedly misreads content.
6. Save final deliverable audio under `/Users/kin/工作用（同步）/GARY素材音频/扩写长音频` on this Mac by default.
7. Automatically run the AutoCutVideo-style silence/pause filter on the generated WAV unless the user explicitly asks to keep the raw TTS audio.
8. Treat the filtered WAV as the final deliverable. Keep raw WAVs as intermediates under the current project's `work/` directory when possible; do not leave raw WAVs in the final output directory unless the user explicitly asks to keep them there.
9. Do not generate SRT by default. Generate subtitles only when the user explicitly asks.
10. Return the filtered `.wav` and summarize technical QC findings.

This Gradio app uses the public container URL for synthesis and does not need the Xiangongyun Open API.

## Document-To-Audio Automation

The user's desired default is: provide a document, and the skill fully generates final audio without manual intermediate steps.

Accepted inputs:

- Plain text pasted in chat.
- `.txt` / `.md` source files.
- `.docx` Word drafts exported from ContentFactory or the user's Douyin copy workflows.
- A folder containing one or more final manuscripts, when the user asks for batch audio.

Document handling rules:

1. Identify the final body text only. Ignore file metadata, comments, table-of-contents material, revision notes, risk notes, filenames, and non-script instructions.
2. Preserve the spoken order of the manuscript.
3. Keep Chinese punctuation meaningful for TTS pause behavior; do not aggressively strip punctuation.
4. For `.docx`, extract visible paragraph text and skip empty paragraphs. If the document has multiple versions, select the version the user names; otherwise prefer the most final-looking body section.
5. Save the extracted source text to `work/source.txt` before synthesis when a local workspace is available.
6. Run hybrid long-form synthesis by default for long manuscripts.
7. Run silence filtering and technical QC automatically after synthesis.
8. Return the final filtered WAV only unless the user explicitly requests subtitles.

End-to-end default chain:

```text
document/text input
-> extract final spoken text
-> Chrome console starts Xiangongyun instance if needed
-> Gradio TTS synthesis
-> silence filtering
-> technical QC
-> final .wav
```

Batch rule: if multiple documents are provided, process them one by one, keep a manifest in `work/tts-manifest.jsonl` when possible, and resume from the last completed item after interruptions.

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

```bash
node scripts/generate_xiangongyun_tts.mjs \
  --text "你好，欢迎来到仙宫云。" \
  --voice "浩威青叔4.0.pt" \
  --speed 1.0 \
  --out "work/xiangongyun-tts.raw.wav"
```

Long narration, hybrid mode:

```bash
node scripts/generate_hybrid_xiangongyun_tts.mjs \
  --source-file "work/source.txt" \
  --intro-end-marker "好，我们直接进入正题。" \
  --voice "浩威青叔4.0.pt" \
  --speed 1.0 \
  --work-dir "work/hybrid-tts" \
  --out "work/xiangongyun-hybrid.raw.wav"
```

If there is no reliable intro marker, use `--intro-chars 280` and let the script split at the nearest sentence boundary:

```bash
node scripts/generate_hybrid_xiangongyun_tts.mjs \
  --source-file "work/source.txt" \
  --intro-chars 280 \
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

Use `scripts/remove_silence_autocut_style.mjs` from this skill. On Mac, pass the installed local `ffmpeg` and `ffprobe` explicitly:

```bash
node /Users/kin/.codex/skills/xiangongyun-tts/scripts/remove_silence_autocut_style.mjs \
  --input "work/raw.wav" \
  --output "/Users/kin/工作用（同步）/GARY素材音频/扩写长音频/final.filtered.wav" \
  --filterLevel -30 \
  --interval 0.3 \
  --ffmpeg "$(command -v ffmpeg)" \
  --ffprobe "$(command -v ffprobe)"
```

Write the filtered file to a temporary local path first, verify it with `ffprobe`, then copy it atomically into the Mac sync folder. This prevents Syncthing from exposing a partially written WAV.
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

## Audio-Only Delivery

- The default deliverable is one filtered `.wav` file.
- Do not run ASR or create `.srt` files unless the user explicitly asks for subtitles or content-match QC.
- Name the WAV from the manuscript title and save it to the Mac local sync folder.

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
