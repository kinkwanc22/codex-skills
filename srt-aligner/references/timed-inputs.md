# Timed Input Notes

Prefer Whisper JSON with word timestamps because it gives the best subtitle timing.

If the ASR tool only returns plain text, rerun transcription with word timestamps if possible. If that is not possible, create a rough SRT from segment timings, then use `align_srt.mjs` with that SRT as `--timed`.

For heavily edited scripts, ask for the final audio or a closer script draft. Alignment quality depends on the script and spoken audio being mostly the same sequence.
