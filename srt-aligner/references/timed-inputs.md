# Timed Input Notes

Prefer Whisper JSON with word timestamps because it gives the best subtitle timing.

If the ASR tool only returns plain text, rerun transcription with word timestamps if possible. If that is not possible, create a rough SRT from segment timings, then use `align_srt.mjs` with that SRT as `--timed`.

Alignment quality tiers:

1. `word`: best. Uses real word or character timestamps from Whisper JSON.
2. `segment-text`: acceptable. Uses segment text as pseudo word timing, then globally matches the final script to it.
3. `segment-proportional`: rough only. Uses empty segment timings and distributes script chunks by character count.

Always open the generated `.report.json` when the user cares about precise sync. Review `weakCues` first; these are usually caused by script/audio mismatch, ASR omissions, repeated phrases, or segment-only timing.

For heavily edited scripts, ask for the final audio or a closer script draft. Alignment quality depends on the script and spoken audio being mostly the same sequence.
