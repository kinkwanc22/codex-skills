#!/usr/bin/env python3
"""Run the Hook Trainer local pipeline end to end."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = Path("/Users/kin/工作用（同步）/开头hook")


def run_step(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Hook Trainer V1/V2 pipeline.")
    parser.add_argument(
        "input_dir",
        type=Path,
        nargs="?",
        default=DEFAULT_SOURCE_DIR,
        help="Folder containing .txt/.md/.srt/.docx files. Defaults to the user's 开头hook folder.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to hook_trainer_output inside the source folder.",
    )
    parser.add_argument("--niche", default="男性情感", help="Search niche.")
    parser.add_argument("--emotion", help="Search emotion.")
    parser.add_argument("--hook-type", dest="hook_type", help="Search hook type.")
    parser.add_argument("--keyword", help="Search keyword.")
    parser.add_argument("--limit", type=int, default=20, help="Top N search results.")
    parser.add_argument(
        "--library-size",
        type=int,
        default=200,
        help="Maximum reusable opening library size.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    output_dir = args.output_dir or (args.input_dir / "hook_trainer_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = output_dir / "parsed.json"
    analysis = output_dir / "analysis.json"
    hooks = output_dir / "hooks.json"
    search_results = output_dir / "search_results.json"
    formulas_dir = output_dir / "formula_library"

    run_step([str(SCRIPT_DIR / "parse_folder.py"), str(args.input_dir), "-o", str(parsed)])
    run_step([str(SCRIPT_DIR / "analyze_hooks.py"), str(parsed), "-o", str(analysis)])
    run_step([str(SCRIPT_DIR / "build_hooks_db.py"), str(analysis), "-o", str(hooks), "--replace"])
    run_step(
        [
            str(SCRIPT_DIR / "build_formula_library.py"),
            str(analysis),
            "-o",
            str(formulas_dir),
            "--limit",
            str(args.library_size),
        ]
    )

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
    print(f"Hook Trainer V2 libraries -> {formulas_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
