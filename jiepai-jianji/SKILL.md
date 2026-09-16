---
name: jiepai-jianji
description: Local street-shot auto editing workflow for Chinese narration videos and Jianying drafts. Use when the user asks for 街拍剪辑, 街拍素材随机剪辑, 口播音频配素材, 按句尾切换素材, 静音点切换素材, 逐字对齐剪视频, 剪映街拍草稿, or wants to turn a video-material folder plus narration audio plus script/docx into a 16:9 horizontal 30fps video.
---

# 街拍剪辑

## Goal

Create a 16:9 horizontal MP4 from:

- a folder of street-shot/B-roll video clips
- one narration audio file
- one narration script, usually `.docx`, `.txt`, or `.md`

Prefer cuts at real sentence endings. Use word timestamps from Whisper/faster-whisper when available, then choose cut points every 5-10 seconds near sentence endings and nearby silence points. Keep 30fps, 1920x1080, H.264, and AAC audio for rendered MP4 output. For Jianying drafts, follow the subtitle, mute, transition, and visual-safety rules below.

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
- Default first-segment material directory: `E:\工作用\视频素材\街拍片段\可用`.
- When the user provides only narration audio and script, use this directory as `--videos` unless they name another material folder.
- For every audio/video render, the first B-roll segment must come from the first-segment material directory. The remaining segments continue to use the full street-shot/B-roll material directory.
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
   - Apply a strict platform-vulgarity gate to every candidate, not merely a nudity check. Reject visible cleavage, deep low-cut/exposed-chest shots, lingerie/bikini-style framing, and shots that deliberately emphasize the chest. Always hard-reject bathrobes, sleep robes, hotel robes, towel robes, bath-towel wraps, and equivalent bathing attire, even when broader clothing or vulgarity screening has been disabled for the candidate pool. Also reject sexually suggestive framing or behavior even when everyone is fully clothed: beds/bedrooms or reclining intimate poses, shower/bath/towel scenes, clothing-removal implications, massage or body-care intimacy, kissing or pressed-body contact, teasing or seductive gestures, suggestive boyfriend-POV touching, and fetish-like close-ups of feet, legs, waist, buttocks, chest, lips, or neck.
   - Treat private-room, nightclub/bar, and night-car scenes conservatively when alcohol, touching, camera proximity, gaze, posture, or body emphasis creates sexual tension. Neutral conversation in those locations is acceptable only when the exact selected range is clearly nonsexual.
   - Prefer public, neutral, everyday alternatives: streets, parks, cafés, restaurants, offices, shopping, travel, ordinary driving, work/life actions, and conversation at a normal interpersonal distance.
   - Sample at least opening, 25%, middle, 75%, and ending frames for AI or unfamiliar footage, then inspect the exact source range that will appear in the timeline. A safe opening/middle/ending does not clear unsafe action between samples. If uncertain, reject the source.
   - Apply the same screening to the `可用` opening-material folder. Maintain a rejected-source list so an excluded source cannot be drawn again in later batches.
   - Apply the same gate to CTA footage, CTA emphasis overlays, and every later-added visual layer. A CTA section is not exempt from visual-safety review.
   - After a platform rejection for `低俗`, mark every source used in the rejected draft as `needs re-review`; do not automatically reuse it merely because it passed an earlier local review.
   - Build a content profile for every accepted source: scene, people, action, mood, relationship state, and useful semantic tags. For each narration segment, select footage by matching the actual copy meaning to those profiles; do not assign sources by simple filename order, round-robin rotation, or pure random concatenation.
   - Detect identical or highly similar opening frames across candidate videos. Within one finished draft, each opening-frame group may be used at most once, even when the underlying files or later motion differ. Also avoid placing several clips from the same scene family consecutively when a semantically suitable alternative exists.
   - For a multi-draft batch, plan footage globally before writing any draft. Maintain a batch-wide usage ledger for source files, opening-frame groups, scene families, and CTA packs. Do not independently run the same greedy selector for every manuscript and then describe the reordered result as varied or semantically matched.
   - Prefer one use per source across the whole batch. When the reviewed pool is too small, distribute reuse evenly at the lowest mathematically feasible ceiling; no small group of high-scoring clips may appear in every draft. Expand and review the pool when the resulting overlap would still be visibly repetitive.
   - Give each draft a distinct visual fingerprint based on its topic, such as observation/analysis, messaging/decision, shared activity, relationship progression, conflict/boundary, business/value, or emotional conversation. Scene quotas and emotional progression should differ between drafts instead of merely changing clip order.
   - For AI-mixed drafts, choose AI versus real footage from the meaning and emotional need of each segment. Fixed AI/real alternation, fixed ratios applied to every manuscript, and category-first assignment are prohibited. Every mixed draft must still contain both types unless the user requests pure AI.
   - Treat the CTA as part of batch diversity rather than an exempt fixed tail. Use at least three visually distinct CTA packs for a batch, never repeat the same complete CTA sequence, and do not give neighboring drafts the same pack. CTA footage remains subject to semantic matching, safety review, muting, and the batch-wide reuse ledger.
   - If a source must be reused in another draft, use a meaningfully different safe source range when duration permits. Reusing the same opening frames with a different order does not count as diversity.

2. Locate FFmpeg.
   - Prefer an explicit local FFmpeg path if already known in the thread.
   - Otherwise use `ffmpeg`/`ffprobe` on `PATH`.
   - On this Windows setup, a known working pair may be under `ffmpeg-bin\...\bin\ffmpeg.exe` and `ffprobe.exe`.

3. Generate word timestamps when the user asks for real alignment or when quality matters.
   - Run `scripts/transcribe_words.py` with a faster-whisper runtime.
   - Start with `base` for a quick test.
   - Use `medium` or `large-v3` for a more accurate final pass if the user accepts the slower runtime.

4. Render with `scripts/make_street_cut_video.py`.
   - On this Windows setup, pass `--opening-videos "E:\工作用\视频素材\街拍片段\可用"` so the first segment is selected only from the approved opening-material folder.
   - If `--opening-videos` is omitted, the renderer automatically uses a `可用` subfolder under `--videos` when it exists.
   - Use `--cut-mode timed-sentence-silence` when a timed JSON exists.
   - Use `--cut-mode sentence-silence` when no timed JSON exists but the script should still influence cut points.
   - Use `--cut-mode silence` when only audio pauses should drive cuts.
   - Use `--min-source-duration 8` and `--min-source-bitrate 5000000` for cleaner material selection.
   - For direct MP4 renders, keep `--fade-duration 0` unless the user explicitly asks for crossfade. Jianying draft transitions are handled separately under the rules below.

5. Verify before reporting done.
   - `ffprobe` the output video stream: width, height, frame rate, duration.
   - `ffprobe` the audio stream and format duration.
   - Inspect the generated `.manifest.json`.
   - Extract one preview frame and inspect it if visual verification is useful.
   - For street-shot batches, record the number of screened sources, the number rejected for revealing or sexually suggestive imagery, and confirm that both sampled frames and every exact selected source range passed.
   - For semantic B-roll or AI-material drafts, record the narration text covered by every video segment, the chosen source profile, and the matched semantic tags or editorial reason. Verify per draft that source-file duplicates are zero, opening-frame-group duplicates are zero, and consecutive same-scene runs are zero unless a deliberately continuous action requires an exception documented in QA.
   - For every multi-draft batch, also report total placements, unique source count, reuse-frequency distribution, sources appearing in every draft, average pairwise source-set Jaccard overlap, same-position reuse rate, dominant-scene share, and CTA pack/sequence identity. A reordered sequence of substantially the same source set is a QA failure even when each individual draft has no internal duplicates.
   - Default batch diversity gates: no source may appear in every draft; average pairwise source-set Jaccard overlap should be at most `0.35`; same-position reuse should be at most `0.10`; and one scene family should not exceed `35%` of placements unless the manuscript clearly requires it and QA records the reason. If the reviewed pool cannot satisfy these gates, expand/review the pool or report the shortfall before delivery instead of silently recycling it.
   - Report the output path, duration, segment count, and whether word-timestamp alignment was used.
   - Distinguish `local visual QA passed` from `platform approved`. Never describe a draft as platform-safe, approved, or passed review until the platform has actually accepted it.

## Jianying Draft Rules

- Body and fixed Qianchuan CTA subtitles in `千川短版` drafts use Jianying `研宋`, size `7`, with shadow enabled and stroke/outline disabled. If stroke is already on, turn it off. Keep fixed brand-packaging text in its template style. This size-7 rule applies to the new Qianchuan-short paradigm and supersedes earlier size-6 Qianchuan-short settings; do not retroactively alter unrelated or already accepted non-short drafts unless requested.
- For Qianchuan short-version drafts with the fixed conversion CTA, keep the confirmed CTA text, audio, subtitle content, and structure unchanged. The expanded body must not contain another CTA. Measure the merged audio rather than estimating from character count: body narration plus fixed CTA must be at most `298` seconds so the finished video remains safely under five minutes. If it exceeds the gate, compress and regenerate only the body; never speed up, trim, or rewrite the fixed CTA.
- Set every video-type segment volume to `0`, including body footage, CTA footage, CTA emphasis overlays, brand video layers, and video overlays added later. Keep sound only on explicitly designated narration or music tracks.
- In the new `千川短版` paradigm, keep the main video track empty. Put every visual material on overlay/PIP tracks (`flag: 2` in plaintext Jianying draft JSON), including ordinary video, still images, CTA visuals, emphasis clips, brand images, and decorative visual layers. Text, subtitles, narration, and music remain on their own track types. Verify that no populated video track is marked as the main track.
- In the new `千川短版` paradigm, determine the opening/body boundary from copy meaning, never from a fixed timestamp. The opening includes the result promise (`能拿到什么样的结果`), inventory/setup phrasing (`盘点`), `这个感觉`-style setup, and all continuation before formal instruction begins. The body begins only at the first real teaching unit, commonly `第一…`, `一、…`, or an equivalent reviewed transition. The decomposed preset body-packaging texts (for example `完整未删减版`, `2026年最新社交技巧`, the topic-analysis line, and the explanatory line) must all start exactly at that semantic body boundary and must not appear during the opening. Keep the opening title and full-duration disclaimer governed by their own template timings. Record the detected marker text and timestamp in QA; if no reliable boundary is found, require manual review instead of guessing.
- Use that same semantic boundary for the visual mode switch. All dynamic opening videos must end exactly at the body boundary; from the first body frame through the end, the main visual must be a still image rather than video. The small icon/sticker on the yellow preset track must start at the same body boundary as the four body-packaging text layers. Verify `dynamic_video_end == body_start == still_image_start == yellow_icon_start`, with no dynamic video leaking into the body.
- In this new Qianchuan-short paradigm, the body uses exactly one still image from the locked female folder; do not rotate multiple body images. The opening may use multiple horizontal videos from that same female folder. Keep every opening clip at normal playback speed, never stretch a shorter source to fill time, and trim before any generated-video tail hold. Place opening cuts roughly every `3-5s` at subtitle boundaries or nearby genuine silence whenever possible.
- The semi-transparent title in the upper-left is opening-only. It must begin at the start of the timeline and extend through the complete opening, ending exactly at the same semantic body boundary. Its text box is left-aligned and placed flush to the left canvas edge; do not preserve the template's inset margin. Verify both the horizontal transform and `opening_title_end == dynamic_video_end == body_start == still_image_start == body_packaging_start == yellow_icon_start`.
- For the 56-female-lead material paradigm, lock exactly one top-level female folder before selecting visuals for a finished video. Every opening horizontal video and every body horizontal still in that finished video must come from that same female folder; never mix female identities within one timeline. Reject `错误版` assets, verify actual horizontal dimensions rather than trusting file names, and record `female_lead_folder`, source paths, and a `same_female_lead` assertion in QA. A later finished video may use a different female folder, but it must independently satisfy the same one-lead rule.
- Use Jianying's native `叠化` at every visual-material boundary in this new paradigm, including video-to-video and the final opening-video-to-body-image boundary. Use another native transition only when a clear change in action, scene, time, meaning, or the move into CTA materially benefits from it; record the exception and its reason in QA. Do not rotate effects merely for variety.
- Verify that transitions create no black frames, gaps, abnormal overlap, subtitle obstruction, or offline media.

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
  --opening-videos "E:\工作用\视频素材\街拍片段\可用" `
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
- Direct MP4 render: no crossfade by default. Jianying draft: default to native `叠化`, with other transitions only for justified exceptions.
- Add a small audio-duration cushion on the last segment so FFmpeg does not truncate narration.
- Use a random seed for reproducibility when iterating.
- First segment: use the approved `可用` subfolder first; later segments remain randomized from the full material pool.
- Candidate safety: strict platform-vulgarity review of sampled frames and exact selected ranges is mandatory; clothing coverage, file names, and folder placement are not sufficient evidence that a clip is acceptable.
- Material selection: narration-to-picture semantic matching is mandatory. Pure rotation, random stacking, or repeatedly using different videos generated from the same opening image is not acceptable.
- Batch diversity: passing single-draft duplicate checks is insufficient. Optimize assignments across the entire batch, enforce the overlap gates above, and preserve distinct visual identities for separate manuscripts.
- Qianchuan duration gate: when a fixed conversion CTA is used, reject any draft whose actual merged audio or timeline exceeds `298` seconds; character-count compliance alone is not acceptance.

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
