---
name: srt-aligner
description: Match a user-provided script/copy with an audio file or timed transcript and generate clean SRT subtitles. Use when the user says they will provide 文案 and 音频, asks to 匹配文案和音频, generate SRT, create subtitles from a script, align narration copy to audio, or convert ASR/Whisper output into polished subtitle files.
---

# SRT Aligner

Use this skill to turn a final script plus audio into an `.srt` subtitle file.

## Workflow

1. Collect inputs:
   - Audio/video file path.
   - Final script/copy text, preferably as `.txt` or pasted text saved to a file.
   - Output filename, defaulting to the audio basename plus `.srt`.
2. Get timing data from the audio:
   - Prefer a transcript with word timestamps, such as Whisper JSON with `segments[].words[]`.
   - If only segment timestamps are available, use them as a fallback.
   - If no transcript exists yet, use the available local ASR/video subtitle workflow to transcribe the audio first, requesting word timestamps when possible.
3. Run `scripts/align_srt.mjs` to align the final script onto the timed transcript.
4. Inspect the SRT for obvious timing/text problems:
   - Empty subtitles.
   - Overlong lines.
   - Large gaps caused by unmatched text.
   - Garbled ASR words leaking into the final script. The output text should come from the user script, not the raw ASR transcript.
5. Save the final `.srt` in the requested output location.

## Alignment Script

Use the bundled Node script:

```powershell
node scripts/align_srt.mjs --script copy.txt --timed whisper.json --out output.srt
```

Useful options:

```powershell
node scripts/align_srt.mjs `
  --script copy.txt `
  --timed whisper.json `
  --out output.srt `
  --max-chars 32 `
  --min-duration 0.8 `
  --max-duration 6
```

Supported timed inputs:

- Whisper-style JSON: `{ "segments": [{ "start": 0, "end": 1.2, "text": "...", "words": [{ "word": "...", "start": 0, "end": 0.3 }] }] }`
- Whisper segment JSON without word timestamps.
- Existing `.srt` files, used as segment-level timing fallback.

## Heuristics

- Keep Chinese subtitle chunks around 18-32 characters unless the user asks otherwise.
- Keep English subtitle chunks around 42-70 characters.
- Prefer splitting at `。！？；，、,.!?;:` and line breaks.
- When the final script differs slightly from ASR, trust the user's script for subtitle text and use ASR only for timing.
- If word timestamps are missing, distribute script chunks across segment timings by character count.
- If alignment confidence looks poor, tell the user and provide the best-effort SRT plus a short note about where manual review is needed.

## Output

Return the `.srt` file path and mention the timing source used: word timestamps, segment timestamps, or fallback proportional timing.
