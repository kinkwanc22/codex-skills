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
   - Strongly prefer Whisper JSON with word timestamps, such as `segments[].words[]`.
   - If no timed transcript exists yet, use the local ASR/video subtitle workflow and request word timestamps whenever the tool supports it.
   - If only segment timestamps or an existing `.srt` are available, the script can still produce a best-effort result, but it must be treated as review-needed.
3. Run `scripts/align_srt.mjs` to align the final script onto the timed transcript.
4. Read the generated report before calling the SRT final:
   - `timingMode: "word"` is the preferred mode.
   - `timingMode: "segment-text"` means segment text was used as pseudo word timing.
   - `timingMode: "segment-proportional"` means the result is rough timing only.
   - Check `weakCues` and `estimatedCues`; these are the subtitles most likely to need manual review.
5. Inspect the SRT for obvious timing/text problems:
   - Empty subtitles.
   - Overlong lines.
   - Large gaps caused by unmatched text.
   - Garbled ASR words leaking into the final script. The output text should come from the user script, not the raw ASR transcript.
6. Save the final `.srt` in the requested output location and mention whether the report found weak cues.

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
  --report output.report.json `
  --max-chars 30 `
  --min-duration 0.8 `
  --max-duration 5.5
```

Supported timed inputs:

- Whisper-style JSON: `{ "segments": [{ "start": 0, "end": 1.2, "text": "...", "words": [{ "word": "...", "start": 0, "end": 0.3 }] }] }`
- Whisper segment JSON without word timestamps.
- Existing `.srt` files, used as segment-level timing fallback.

## Heuristics

- Keep Chinese subtitle chunks around 18-30 characters unless the user asks otherwise.
- Keep English subtitle chunks around 42-70 characters.
- Prefer splitting at `。！？；，、,.!?;:` and line breaks.
- When the final script differs slightly from ASR, trust the user's script for subtitle text and use ASR only for timing.
- The aligner now uses global token matching for word timestamps, so skipped words, repeated phrases, and short ASR insertions should not push the whole SRT off track.
- If word timestamps are missing but segment text exists, it distributes segment time across segment tokens and performs global matching against that pseudo timing.
- If only empty segment timing exists, it distributes script chunks across the full segment duration by character count and marks all cues as estimated.
- If alignment confidence looks poor, tell the user and provide the best-effort SRT plus the report path.

## Output

Return:

- The `.srt` file path.
- The `.report.json` file path.
- The timing source used: word timestamps, segment text pseudo timing, or proportional fallback.
- Whether `weakCues` / `estimatedCues` need review.
