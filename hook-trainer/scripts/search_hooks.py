#!/usr/bin/env python3
"""Search hooks.json and return ranked hook results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def load_database(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object database: {path}")
    hooks = data.get("hooks", [])
    if not isinstance(hooks, list):
        raise ValueError(f"Expected database.hooks to be a list: {path}")
    return data


def text_contains(value: object, expected: str | None) -> bool:
    if not expected:
        return True
    return expected.lower() in str(value).lower()


def score_hook(item: dict[str, object], query: dict[str, str | None]) -> float:
    score = 0.0
    if query.get("niche") and text_contains(item.get("niche"), query["niche"]):
        score += 0.35
    if query.get("emotion") and text_contains(item.get("emotion"), query["emotion"]):
        score += 0.25
    if query.get("hook_type") and text_contains(item.get("hook_type"), query["hook_type"]):
        score += 0.25
    keyword = query.get("keyword")
    if keyword:
        searchable = " ".join(
            str(item.get(field, ""))
            for field in ("hook", "template", "information_gap", "notes", "file_name")
        )
        if keyword.lower() in searchable.lower():
            score += 0.15

    hook = str(item.get("hook", ""))
    if 12 <= len(hook) <= 120:
        score += 0.05
    if item.get("template"):
        score += 0.05
    return round(score, 4)


def matches_filters(item: dict[str, object], query: dict[str, str | None]) -> bool:
    return (
        text_contains(item.get("niche"), query.get("niche"))
        and text_contains(item.get("emotion"), query.get("emotion"))
        and text_contains(item.get("hook_type"), query.get("hook_type"))
        and (
            not query.get("keyword")
            or any(
                query["keyword"].lower() in str(item.get(field, "")).lower()
                for field in ("hook", "template", "information_gap", "notes", "file_name")
            )
        )
    )


def search_hooks(
    hooks: Iterable[dict[str, object]],
    query: dict[str, str | None],
    limit: int = 20,
) -> dict[str, object]:
    matched: list[dict[str, object]] = []
    for item in hooks:
        if not matches_filters(item, query):
            continue
        result = {
            "hook_id": item.get("hook_id", ""),
            "source_id": item.get("source_id", ""),
            "file_name": item.get("file_name", ""),
            "niche": item.get("niche", ""),
            "hook": item.get("hook", ""),
            "hook_type": item.get("hook_type", ""),
            "emotion": item.get("emotion", ""),
            "rhythm": item.get("rhythm", ""),
            "information_gap": item.get("information_gap", ""),
            "template": item.get("template", ""),
            "score": score_hook(item, query),
        }
        matched.append(result)

    matched.sort(key=lambda item: (-float(item["score"]), str(item["file_name"]), str(item["hook_id"])))
    ranked = matched[:limit]
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return {
        "query": {key: value for key, value in query.items() if value},
        "count": len(ranked),
        "results": ranked,
    }


def write_json(data: object, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def format_text(results: dict[str, object]) -> str:
    lines = [f"Query: {json.dumps(results.get('query', {}), ensure_ascii=False)}"]
    for item in results.get("results", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"{item.get('rank')}. [{item.get('hook_type')} / {item.get('emotion')}] "
            f"{item.get('hook')} | template: {item.get('template')}"
        )
    return "\n".join(lines) + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search Hook Trainer hooks.json.")
    parser.add_argument(
        "database",
        type=Path,
        nargs="?",
        default=Path("examples/output/hooks.json"),
        help="Input hooks.json path.",
    )
    parser.add_argument("--niche", help="Filter by niche, e.g. 男性情感.")
    parser.add_argument("--emotion", help="Filter by emotion, e.g. 焦虑.")
    parser.add_argument("--hook-type", help="Filter by hook type, e.g. 反常识.")
    parser.add_argument("--keyword", help="Search hook/template/gap text.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum result count.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("examples/output/search_results.json"),
        help="Output path.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    database = load_database(args.database)
    hooks = database.get("hooks", [])
    query = {
        "niche": args.niche,
        "emotion": args.emotion,
        "hook_type": args.hook_type,
        "keyword": args.keyword,
    }
    results = search_hooks(hooks, query, limit=args.limit)
    if args.format == "json":
        write_json(results, args.output)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(format_text(results), encoding="utf-8")
    print(f"Found {results['count']} hooks -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

