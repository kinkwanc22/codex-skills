#!/usr/bin/env python3
"""Run the final 3.1 mother-topic, text, ending, and DOCX checks once."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from validate_mother_topic_lock import normalize, read_text


W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DEFAULT_ENDING = "我是探花Gary，我们粉丝群里见，感谢观看"
DEFAULT_FORBIDDEN_TERMS = [
    "内部群",
    "私董会",
    "[[RISKNOTE:",
    "作为Gary",
    "作为探花Gary",
    "以探花Gary的身份",
]
DEFAULT_REQUIRED_HEADINGS = [
    "爆款心理学标题包装",
    "开头版本一：高阶认知课式开头",
    "开头版本二：身份点名式硬核学习开头",
    "开头版本三：保留原文开头（来自源文档）",
    "开头版本四：原文开头优化版（贴合正文）",
    "正文",
]


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def cjk_count(value: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", value))


def read_docx_package(path: Path) -> tuple[list[str], str, list[str]]:
    with ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise BadZipFile(f"corrupt member: {bad_member}")
        names = archive.namelist()
        if "word/document.xml" not in names:
            raise BadZipFile("missing word/document.xml")
        document_xml = archive.read("word/document.xml")
        word_xml = [
            archive.read(name).decode("utf-8", errors="replace")
            for name in names
            if name.startswith("word/") and name.endswith(".xml")
        ]

    root = ElementTree.fromstring(document_xml)
    paragraphs = [
        "".join(node.text or "" for node in paragraph.iter(W_NS + "t"))
        for paragraph in root.iter(W_NS + "p")
    ]
    return paragraphs, "\n".join(paragraphs), word_xml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--docx", required=True, type=Path)
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--forbidden-label", action="append", default=[])
    parser.add_argument("--forbidden-term", action="append", default=[])
    parser.add_argument("--required-heading", action="append", default=[])
    parser.add_argument("--exact-ending", default=DEFAULT_ENDING)
    parser.add_argument("--min-cjk", type=int, default=4000)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()

    checks: dict[str, object] = {}
    errors: list[str] = []

    try:
        source_text = read_text(args.source)
        frozen_text = read_text(args.frozen)
        final_text = read_text(args.final).strip()
    except Exception as exc:
        source_text = frozen_text = final_text = ""
        errors.append(f"text read failed: {exc}")

    anchor = normalize(args.anchor)
    source_norm = normalize(source_text)
    frozen_norm = normalize(frozen_text)
    final_norm = normalize(final_text)
    label_hits = {
        label: {
            "frozen": normalize(label) in frozen_norm,
            "final": normalize(label) in final_norm,
        }
        for label in args.forbidden_label
        if normalize(label)
    }
    checks["mother_topic"] = {
        "anchor": args.anchor,
        "source_contains_anchor": bool(anchor and anchor in source_norm),
        "frozen_contains_anchor": bool(anchor and anchor in frozen_norm),
        "final_contains_anchor": bool(anchor and anchor in final_norm),
        "forbidden_label_hits": label_hits,
    }
    if not checks["mother_topic"]["source_contains_anchor"]:
        errors.append("mother-topic anchor missing from source")
    if not checks["mother_topic"]["frozen_contains_anchor"]:
        errors.append("mother-topic anchor missing from frozen source")
    if not checks["mother_topic"]["final_contains_anchor"]:
        errors.append("mother-topic anchor missing from final body")
    if any(hit["frozen"] or hit["final"] for hit in label_hits.values()):
        errors.append("forbidden mother-topic replacement label found")

    final_cjk = cjk_count(final_text)
    checks["final_text"] = {
        "cjk_characters": final_cjk,
        "minimum_cjk": args.min_cjk,
        "ends_with_exact_ending": final_text.endswith(args.exact_ending),
        "exact_ending_count": final_text.count(args.exact_ending),
    }
    if final_cjk < args.min_cjk:
        errors.append(f"final body below minimum CJK count: {final_cjk} < {args.min_cjk}")
    if not final_text.endswith(args.exact_ending):
        errors.append("final body does not end with the exact ending")
    if final_text.count(args.exact_ending) != 1:
        errors.append("final body must contain the exact ending exactly once")

    forbidden_terms = list(dict.fromkeys(DEFAULT_FORBIDDEN_TERMS + args.forbidden_term))
    final_forbidden_hits = [term for term in forbidden_terms if term and term in final_text]
    checks["forbidden_terms"] = {"terms": forbidden_terms, "final_hits": final_forbidden_hits}
    if final_forbidden_hits:
        errors.append("forbidden term found in final body")

    paragraphs: list[str] = []
    docx_text = ""
    word_xml: list[str] = []
    try:
        paragraphs, docx_text, word_xml = read_docx_package(args.docx)
        checks["docx_package_readable"] = True
    except Exception as exc:
        checks["docx_package_readable"] = False
        errors.append(f"DOCX package check failed: {exc}")

    required_headings = args.required_heading or DEFAULT_REQUIRED_HEADINGS
    missing_headings = [heading for heading in required_headings if heading not in paragraphs]
    checks["word_structure"] = {
        "required_headings": required_headings,
        "missing_headings": missing_headings,
        "paragraph_count": len(paragraphs),
    }
    if missing_headings:
        errors.append("required Word heading missing")

    word_forbidden_hits = [term for term in forbidden_terms if term and term in docx_text]
    checks["forbidden_terms"]["word_hits"] = word_forbidden_hits
    if word_forbidden_hits:
        errors.append("forbidden term found in Word document")

    word_ending_count = docx_text.count(args.exact_ending)
    checks["word_ending"] = {
        "exact_ending_count": word_ending_count,
        "last_nonempty_paragraph": next((item for item in reversed(paragraphs) if item.strip()), ""),
    }
    if word_ending_count != 1:
        errors.append("Word document must contain the exact ending exactly once")
    if checks["word_ending"]["last_nonempty_paragraph"] != args.exact_ending:
        errors.append("Word document does not end with the exact ending")

    word_anchor_ok = bool(anchor and anchor in normalize(docx_text))
    checks["word_contains_mother_topic_anchor"] = word_anchor_ok
    if not word_anchor_ok:
        errors.append("mother-topic anchor missing from Word document")

    body_match = False
    if "正文" in paragraphs:
        body_start = len(paragraphs) - 1 - list(reversed(paragraphs)).index("正文")
        word_body = "\n".join(paragraphs[body_start + 1 :]).strip()
        body_match = compact(word_body) == compact(final_text)
    checks["word_body_matches_final"] = body_match
    if not body_match:
        errors.append("Word body does not match the accepted final text")

    yellow_patterns = [
        re.compile(r'<w:highlight[^>]+w:val=["\']yellow["\']', re.IGNORECASE),
        re.compile(r'<w:shd[^>]+w:fill=["\']FFFF00["\']', re.IGNORECASE),
    ]
    yellow_hits = sum(bool(pattern.search(xml)) for xml in word_xml for pattern in yellow_patterns)
    checks["yellow_annotation_hits"] = yellow_hits
    if yellow_hits:
        errors.append("yellow highlight or yellow shading found in Word document")

    checks["libreoffice_rendering"] = "disabled_for_3.1"
    report = {
        "mode": "3.1_unified_final_validation",
        "source": str(args.source),
        "frozen": str(args.frozen),
        "final": str(args.final),
        "docx": str(args.docx),
        "checks": checks,
        "errors": errors,
        "pass": not errors,
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(output + "\n", encoding="utf-8")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
