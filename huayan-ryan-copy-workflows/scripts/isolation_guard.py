#!/usr/bin/env python3
"""Fail-closed isolation checks for the Huayan Ryan copy workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


MALE_ROOTS = (
    Path("/Users/kin/.codex/skills/douyin-copy-production-workflow-custom"),
    Path("/Users/kin/.codex/skills/gary-35-independent"),
    Path("/Users/kin/.codex/skills/huanxin"),
    Path("/Users/kin/.codex/skills/qianchuan-hook-continuation"),
    Path("/Users/kin/.codex/skills/男版扩写"),
)

ALLOWED_OUTPUT_ROOTS = (
    Path("/Users/kin/Documents/Codex/花研Ryan工作台"),
    Path("/Users/kin/工作用（同步）/花研Ryan"),
)

BANNED_RESIDUE = (
    "探花Gary",
    "Gary哥",
    "兄弟们",
    "哥们",
    "男性学员",
    "我是探花Ryan",
)


def digest_tree(root: Path) -> str:
    h = hashlib.sha256()
    if not root.exists():
        h.update(b"MISSING")
        return h.hexdigest()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if ".git" in path.parts or ".local" in path.parts:
            continue
        h.update(path.relative_to(root).as_posix().encode())
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()


def current_snapshot() -> dict[str, str]:
    return {str(root): digest_tree(root) for root in MALE_ROOTS}


def inside(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve(strict=False)
    return any(resolved == root or root in resolved.parents for root in roots)


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as archive:
            return "\n".join(
                archive.read(name).decode("utf-8", errors="ignore")
                for name in archive.namelist()
                if name.startswith("word/") and name.endswith(".xml")
            )
    return path.read_text(encoding="utf-8", errors="ignore")


def cmd_snapshot(output: Path) -> int:
    resolved = output.resolve(strict=False)
    if not inside(output, ALLOWED_OUTPUT_ROOTS) and not str(resolved).startswith("/private/tmp/"):
        print(f"REFUSE: baseline output is outside the female workspace: {output}", file=sys.stderr)
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(current_snapshot(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK snapshot {output}")
    return 0


def cmd_verify(baseline: Path) -> int:
    before = json.loads(baseline.read_text(encoding="utf-8"))
    after = current_snapshot()
    changed = {key: (before.get(key), value) for key, value in after.items() if before.get(key) != value}
    if changed:
        print(json.dumps({"status": "STOP", "male_roots_changed": changed}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 3
    print("OK male workflow unchanged")
    return 0


def cmd_check_artifact(path: Path) -> int:
    if not inside(path, ALLOWED_OUTPUT_ROOTS):
        print(f"REFUSE: artifact is outside the female output roots: {path}", file=sys.stderr)
        return 4
    if not path.exists() or not path.is_file():
        print(f"REFUSE: artifact does not exist: {path}", file=sys.stderr)
        return 5
    found = [token for token in BANNED_RESIDUE if token in extract_text(path)]
    if found:
        print(json.dumps({"status": "STOP", "artifact": str(path), "male_residue": found}, ensure_ascii=False), file=sys.stderr)
        return 6
    print(f"OK artifact isolated {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_snapshot = sub.add_parser("snapshot")
    p_snapshot.add_argument("--output", type=Path, required=True)
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--baseline", type=Path, required=True)
    p_artifact = sub.add_parser("check-artifact")
    p_artifact.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "snapshot":
        return cmd_snapshot(args.output)
    if args.command == "verify":
        return cmd_verify(args.baseline)
    return cmd_check_artifact(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
