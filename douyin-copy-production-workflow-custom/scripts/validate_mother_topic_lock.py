#!/usr/bin/env python3
"""Verify that a source-derived public mother-topic anchor survives a rewrite."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".rtf":
        return subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    if suffix == ".docx":
        with ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        return "\n".join(
            "".join(node.text or "" for node in paragraph.iter(namespace + "t"))
            for paragraph in root.iter(namespace + "p")
        )
    raise ValueError(f"Unsupported source type: {path}")


def normalize(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value).lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--final", type=Path)
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--forbidden-label", action="append", default=[])
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()

    source = normalize(read_text(args.source))
    frozen = normalize(read_text(args.frozen))
    final = normalize(read_text(args.final)) if args.final else ""
    anchor = normalize(args.anchor)

    forbidden = [normalize(item) for item in args.forbidden_label if normalize(item)]
    report = {
        "source": str(args.source),
        "frozen": str(args.frozen),
        "final": str(args.final) if args.final else None,
        "anchor": args.anchor,
        "source_contains_anchor": bool(anchor and anchor in source),
        "frozen_contains_anchor": bool(anchor and anchor in frozen),
        "final_contains_anchor": None if not args.final else bool(anchor and anchor in final),
        "forbidden_label_hits": {
            raw: {
                "frozen": normalized in frozen,
                "final": bool(args.final and normalized in final),
            }
            for raw, normalized in zip(args.forbidden_label, forbidden)
        },
    }
    forbidden_hit = any(
        state["frozen"] or state["final"]
        for state in report["forbidden_label_hits"].values()
    )
    report["mother_topic_exact_lock_pass"] = (
        report["source_contains_anchor"]
        and report["frozen_contains_anchor"]
        and (not args.final or report["final_contains_anchor"])
        and not forbidden_hit
    )

    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(output + "\n", encoding="utf-8")
    if not report["mother_topic_exact_lock_pass"]:
        print("REJECT: public mother topic was renamed, omitted, or replaced", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
