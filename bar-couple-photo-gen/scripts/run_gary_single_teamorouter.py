#!/usr/bin/env python3
"""Run the existing random heroine workflow through TeamoRouter Sunburst."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import secrets
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
LEGACY_RUNNER = HERE / "run_gary_batch_lovart_mac.py"
TEAMOROUTER_CLIENT = (
    Path.home() / ".codex" / "skills" / "teamorouter-image" / "scripts" / "teamorouter_image.py"
)
DEFAULT_FEMALE_DIR = Path("/Users/kin/工作用（同步）/图/人物设定/精品")
DEFAULT_OUTPUT_DIR = Path("/Users/kin/工作用（同步）/图/长视频用图")
SINGLE_PRESETS = (
    "single_female_hotel_door_cctv",
    "single_female_restaurant_low_angle",
)
PRESET_FILENAMES = {
    "single_female_hotel_door_cctv": "01_单女主酒店走廊敲门CCTV",
    "single_female_restaurant_low_angle": "01_单女主西餐厅低机位抓拍",
}
SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".webp"}


class IntegrationError(RuntimeError):
    pass


def load_prompt_module():
    spec = importlib.util.spec_from_file_location("gary_prompt_workflow", LEGACY_RUNNER)
    if spec is None or spec.loader is None:
        raise IntegrationError(f"Cannot load prompt workflow: {LEGACY_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def choose_female(directory: Path, explicit: str | None, rng: random.Random) -> Path:
    if not directory.is_dir():
        raise IntegrationError(f"Heroine library not found: {directory}")
    candidates = sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGES
    )
    if explicit:
        selected = Path(explicit).expanduser().resolve()
        if selected.parent != directory.resolve() or selected not in [item.resolve() for item in candidates]:
            raise IntegrationError("The selected heroine must be an image in the current heroine library root.")
        return selected
    if not candidates:
        raise IntegrationError(f"Heroine library is empty: {directory}")
    return rng.choice(candidates)


def image_dimensions(path: Path) -> dict[str, int] | None:
    try:
        proc = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    values: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        if "pixelWidth:" in line:
            values["width"] = int(line.rsplit(":", 1)[1].strip())
        elif "pixelHeight:" in line:
            values["height"] = int(line.rsplit(":", 1)[1].strip())
    return values if set(values) == {"width", "height"} else None


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_client(command: list[str]) -> tuple[int, dict[str, Any]]:
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = proc.stdout.strip() if proc.returncode == 0 else proc.stderr.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"ok": False, "error": raw[:2000] or "TeamoRouter client returned no JSON."}
    return proc.returncode, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--female-dir", default=str(DEFAULT_FEMALE_DIR))
    parser.add_argument("--female-path")
    parser.add_argument("--female-count", type=int, choices=(1,), default=1)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--prompt-preset", choices=("random", *SINGLE_PRESETS), default="random")
    parser.add_argument("--aspect", choices=("9x16", "16x9"), default="9x16")
    parser.add_argument("--quality", choices=("low", "medium", "high", "auto"), default="medium")
    parser.add_argument("--input-fidelity", choices=("high", "low"), default="high")
    parser.add_argument("--seed", type=int)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm-spend", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not TEAMOROUTER_CLIENT.is_file():
        raise IntegrationError(f"TeamoRouter client not installed: {TEAMOROUTER_CLIENT}")

    seed = args.seed if args.seed is not None else secrets.randbits(63)
    rng = random.Random(seed)
    female_dir = Path(args.female_dir).expanduser()
    female = choose_female(female_dir, args.female_path, rng)
    preset = rng.choice(SINGLE_PRESETS) if args.prompt_preset == "random" else args.prompt_preset

    prompt_workflow = load_prompt_module()
    prompt_workflow.random.seed(seed)
    settings = prompt_workflow.generation_settings(args.aspect, args.quality, 1, "default")
    settings["model_family"] = "GPT Image 2.5 Sunburst"
    settings["preferred_model_display_name"] = f"GPT Image 2.5 Sunburst {args.quality}"
    settings["preferred_model"] = "gpt-image-2.5-sunburst"
    scene = "五星级酒店走廊" if preset == SINGLE_PRESETS[0] else "高级西餐厅"
    interaction = "女主准备敲左侧房间门" if preset == SINGLE_PRESETS[0] else "女主与画外左侧的人开心又害羞地聊天"
    prompt = prompt_workflow.build_prompt(scene, interaction, args.aspect, preset, settings)
    size = f"{settings['width']}x{settings['height']}"

    client_command = [
        sys.executable,
        str(TEAMOROUTER_CLIENT),
        "edit",
        "--image",
        str(female),
        "--prompt",
        prompt,
        "--size",
        size,
        "--quality",
        args.quality,
        "--input-fidelity",
        args.input_fidelity,
        "--output-format",
        "png",
    ]

    base_record: dict[str, Any] = {
        "provider": "teamorouter",
        "model": "gpt-image-2.5-sunburst",
        "seed": seed,
        "female_path": str(female.resolve()),
        "prompt_preset": preset,
        "prompt": prompt,
        "request": {
            "size": size,
            "quality": args.quality,
            "input_fidelity": args.input_fidelity,
            "n": 1,
        },
        "identity_reference_count": 1,
        "male_reference_used": False,
    }

    if args.dry_run:
        code, result = run_client([*client_command, "--dry-run"])
        output = {
            **base_record,
            "dry_run": True,
            "network_called": False,
            "uploads_performed": False,
            "client_validation": result,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return code

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(args.output_dir).expanduser() / f"{datetime.now():%Y-%m-%d}_随机女主_TeamoRouter测试_{run_id}"
    batch_dir.mkdir(parents=True, exist_ok=False)
    manifest_path = batch_dir / "manifest.json"
    pending = {**base_record, "status": "submitting", "started_at": datetime.now().astimezone().isoformat()}
    write_manifest(manifest_path, pending)

    code, result = run_client([
        *client_command,
        "--output-dir",
        str(batch_dir),
        "--confirm-spend",
    ])
    if code != 0:
        write_manifest(manifest_path, {**pending, "status": "failed", "error": result.get("error", result)})
        print(json.dumps({"ok": False, "manifest": str(manifest_path), "error": result}, ensure_ascii=False, indent=2))
        return code

    produced = [Path(path) for path in result.get("files", [])]
    if len(produced) != 1 or not produced[0].is_file() or produced[0].stat().st_size == 0:
        raise IntegrationError("The API call completed but exactly one non-empty output image was not verified.")
    final_path = batch_dir / f"{PRESET_FILENAMES[preset]}.png"
    produced[0].replace(final_path)
    dimensions = image_dimensions(final_path)
    completed = {
        **pending,
        "status": "success",
        "completed_at": datetime.now().astimezone().isoformat(),
        "output_paths": [str(final_path.resolve())],
        "actual_dimensions": dimensions,
        "bytes": final_path.stat().st_size,
    }
    write_manifest(manifest_path, completed)
    print(json.dumps({"ok": True, "image": str(final_path), "manifest": str(manifest_path), "record": completed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IntegrationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
