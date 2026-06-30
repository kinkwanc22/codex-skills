#!/usr/bin/env python3
"""Parse Hook Trainer source scripts into parsed.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {".txt", ".md", ".srt", ".docx"}
SRT_TIMESTAMP_RE = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s+-->\s+"
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}.*$"
)
SRT_SEQUENCE_RE = re.compile(r"^\s*\d+\s*$")
WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def discover_files(input_dir: Path) -> list[Path]:
    """Return supported source files in stable path order."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {input_dir}")

    files = [
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda path: str(path.relative_to(input_dir)).lower())


def read_text(path: Path) -> str:
    """Read text with UTF-8 first, then tolerate common legacy encodings."""
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_docx_text(path: Path) -> str:
    """Extract paragraph text from a .docx file without external packages."""
    with zipfile.ZipFile(path) as docx:
        document_xml = docx.read("word/document.xml")

    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NAMESPACE}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{WORD_NAMESPACE}tab":
                parts.append("\t")
            elif node.tag == f"{WORD_NAMESPACE}br":
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def normalize_plain_text(text: str) -> str:
    """Normalize line endings and trim only outer whitespace."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def normalize_srt(text: str) -> str:
    """Remove SRT sequence numbers and timestamps while preserving dialogue."""
    lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if SRT_TIMESTAMP_RE.match(line):
            continue
        if SRT_SEQUENCE_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def normalize_text(text: str, file_type: str) -> str:
    if file_type == "srt":
        return normalize_srt(text)
    return normalize_plain_text(text)


def make_source_id(relative_path: str, text: str) -> str:
    """Build a stable ID from relative path and normalized text."""
    digest = hashlib.sha256()
    digest.update(relative_path.encode("utf-8"))
    digest.update(b"\0")
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()[:16]


def parse_file(path: Path, input_dir: Path) -> dict[str, object]:
    relative_path = path.relative_to(input_dir).as_posix()
    file_type = path.suffix.lower().lstrip(".")
    raw_text = read_docx_text(path) if file_type == "docx" else read_text(path)
    text = normalize_text(raw_text, file_type)

    return {
        "source_id": make_source_id(relative_path, text),
        "file_path": relative_path,
        "file_name": path.name,
        "file_type": file_type,
        "text": text,
        "char_count": len(text),
    }


def parse_folder(input_dir: Path) -> list[dict[str, object]]:
    return [parse_file(path, input_dir) for path in discover_files(input_dir)]


def write_parsed_json(records: Iterable[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(list(records), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse .txt, .md, .srt, and .docx scripts into parsed.json."
    )
    parser.add_argument("input_dir", type=Path, help="Folder containing source scripts.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("examples/output/parsed.json"),
        help="Output JSON path. Defaults to examples/output/parsed.json.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    records = parse_folder(args.input_dir)
    write_parsed_json(records, args.output)
    print(f"Parsed {len(records)} files -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
