#!/usr/bin/env python3
"""Match a draft topic or script to reusable Hook Trainer openings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def read_query(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        return args.file.read_text(encoding="utf-8")
    raise ValueError("Provide --text or --file.")


def tokens(text: str) -> set[str]:
    clean = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", text)
    output = set()
    for size in (2, 3, 4):
        for index in range(0, max(len(clean) - size + 1, 0)):
            output.add(clean[index : index + size])
    return output


def score(query_tokens: set[str], item: dict[str, object]) -> float:
    hook = str(item.get("hook", ""))
    formula = str(item.get("formula", ""))
    keywords = set(str(word) for word in item.get("keywords", []))
    item_tokens = tokens(hook) | tokens(formula) | keywords
    if not item_tokens:
        return 0.0
    overlap = query_tokens & item_tokens
    weighted = len(overlap) + len(overlap & keywords) * 1.5
    return round(weighted / max(len(query_tokens), 1), 4)


def match_openings(query: str, library: list[dict[str, object]], limit: int = 20) -> dict[str, object]:
    query_tokens = tokens(query)
    results = []
    for item in library:
        item_score = score(query_tokens, item)
        if item_score <= 0:
            continue
        results.append(
            {
                "score": item_score,
                "rank": 0,
                "fine_frame": item.get("fine_frame", ""),
                "sentence_pattern": item.get("sentence_pattern", ""),
                "formula": item.get("formula", ""),
                "hook": item.get("hook", ""),
                "keywords": item.get("keywords", [])[:10],
                "source_file": item.get("file_name", ""),
            }
        )
    results.sort(key=lambda item: (-float(item["score"]), str(item["fine_frame"]), str(item["hook"])))
    results = results[:limit]
    for index, item in enumerate(results, start=1):
        item["rank"] = index
    return {"query": query, "count": len(results), "results": results}


def write_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Match topic/script to opening library.")
    parser.add_argument("library", type=Path, help="opening_library.json path.")
    parser.add_argument("--text", help="Draft topic or script text.")
    parser.add_argument("--file", type=Path, help="Draft topic/script file.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("-o", "--output", type=Path, default=Path("matched_openings.json"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    matches = match_openings(read_query(args), load_json(args.library), limit=args.limit)
    write_json(matches, args.output)
    print(f"Matched {matches['count']} openings -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

