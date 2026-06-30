#!/usr/bin/env python3
"""Run the Hook Trainer local pipeline end to end."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def run_step(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Hook Trainer V1 pipeline.")
    parser.add_argument("input_dir", type=Path, help="Folder containing .txt/.md/.srt/.docx files.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("hook_trainer_output"),
        help="Output directory for parsed, analysis, database, and search results.",
    )
    parser.add_argument("--niche", default="男性情感", help="Search niche.")
    parser.add_argument("--emotion", help="Search emotion.")
    parser.add_argument("--hook-type", dest="hook_type", help="Search hook type.")
    parser.add_argument("--keyword", help="Search keyword.")
    parser.add_argument("--limit", type=int, default=20, help="Top N search results.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = output_dir / "parsed.json"
    analysis = output_dir / "analysis.json"
    hooks = output_dir / "hooks.json"
    search_results = output_dir / "search_results.json"

    run_step([str(SCRIPT_DIR / "parse_folder.py"), str(args.input_dir), "-o", str(parsed)])
    run_step([str(SCRIPT_DIR / "analyze_hooks.py"), str(parsed), "-o", str(analysis)])
    run_step([str(SCRIPT_DIR / "build_hooks_db.py"), str(analysis), "-o", str(hooks), "--replace"])

    search_args = [
        str(SCRIPT_DIR / "search_hooks.py"),
        str(hooks),
        "--niche",
        args.niche,
        "--limit",
        str(args.limit),
        "-o",
        str(search_results),
    ]
    if args.emotion:
        search_args.extend(["--emotion", args.emotion])
    if args.hook_type:
        search_args.extend(["--hook-type", args.hook_type])
    if args.keyword:
        search_args.extend(["--keyword", args.keyword])
    run_step(search_args)

    print(f"Hook Trainer pipeline complete -> {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

