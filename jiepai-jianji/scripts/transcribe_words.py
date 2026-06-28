#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper word timestamps.")
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model-size", default="base")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()

    from faster_whisper import WhisperModel

    model = WhisperModel(args.model_size, device=args.device, compute_type=args.compute_type)
    segments, info = model.transcribe(
        str(args.audio),
        language=args.language,
        word_timestamps=True,
        vad_filter=True,
    )

    out_segments = []
    word_count = 0
    for seg in segments:
        words = []
        for word in seg.words or []:
            words.append({"word": word.word, "start": word.start, "end": word.end, "probability": word.probability})
            word_count += 1
        out_segments.append(
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": words,
            }
        )

    payload = {
        "audio": str(args.audio),
        "model_size": args.model_size,
        "language": args.language,
        "duration": getattr(info, "duration", None),
        "language_probability": getattr(info, "language_probability", None),
        "segments": out_segments,
        "word_count": word_count,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "segments": len(out_segments), "words": word_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
