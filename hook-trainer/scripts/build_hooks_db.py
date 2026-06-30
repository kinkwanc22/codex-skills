#!/usr/bin/env python3
"""Import analysis.json into hooks.json."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = 1


def load_json(path: Path, fallback: object | None = None) -> object:
    if not path.exists():
        if fallback is not None:
            return fallback
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(data: object, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def make_hook_id(item: dict[str, object]) -> str:
    source_id = str(item.get("source_id", ""))
    hook = str(item.get("hook", ""))
    digest = hashlib.sha256(f"{source_id}\0{hook}".encode("utf-8")).hexdigest()
    return digest[:16]


def normalize_hook(item: dict[str, object], imported_at: str) -> dict[str, object]:
    hook_id = make_hook_id(item)
    return {
        "hook_id": hook_id,
        "source_id": item.get("source_id", ""),
        "file_path": item.get("file_path", ""),
        "file_name": item.get("file_name", ""),
        "niche": item.get("niche", "通用"),
        "hook": item.get("hook", ""),
        "hook_type": item.get("hook_type", "未分类"),
        "emotion": item.get("emotion", "中性"),
        "rhythm": item.get("rhythm", ""),
        "information_gap": item.get("information_gap", ""),
        "template": item.get("template", ""),
        "notes": item.get("notes", ""),
        "imported_at": imported_at,
    }


def empty_database() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": "",
        "hooks": [],
    }


def import_analysis(
    analysis_records: Iterable[dict[str, object]],
    existing_db: dict[str, object] | None = None,
    imported_at: str | None = None,
) -> dict[str, object]:
    timestamp = imported_at or datetime.now(timezone.utc).isoformat()
    database = existing_db or empty_database()
    existing_hooks = database.get("hooks", [])
    if not isinstance(existing_hooks, list):
        existing_hooks = []

    by_id: dict[str, dict[str, object]] = {
        str(item.get("hook_id")): item
        for item in existing_hooks
        if isinstance(item, dict) and item.get("hook_id")
    }

    for item in analysis_records:
        normalized = normalize_hook(item, timestamp)
        hook_id = str(normalized["hook_id"])
        previous = by_id.get(hook_id)
        if previous and previous.get("imported_at"):
            normalized["imported_at"] = previous["imported_at"]
        by_id[hook_id] = normalized

    hooks = sorted(by_id.values(), key=lambda item: (str(item.get("file_path")), str(item.get("hook_id"))))
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": timestamp,
        "hooks": hooks,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import analysis.json into hooks.json.")
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("examples/output/analysis.json"),
        help="Input analysis.json path.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("examples/output/hooks.json"),
        help="Output hooks.json path.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing hooks.json instead of merging into it.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    analysis_data = load_json(args.input)
    if not isinstance(analysis_data, list):
        raise ValueError(f"Expected a JSON list: {args.input}")

    existing = None
    if not args.replace and args.output.exists():
        loaded = load_json(args.output, fallback=empty_database())
        if isinstance(loaded, dict):
            existing = loaded

    database = import_analysis(analysis_data, existing_db=existing)
    write_json(database, args.output)
    print(f"Imported {len(analysis_data)} records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

