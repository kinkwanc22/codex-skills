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
DEFAULT_OPENING_GUIDANCE = "另外说一下，想节省时间的话，可以点个收藏，在评论区艾特豆包，让豆包给你总结出精髓或者思维导图后再回来观看，如果现实中有任何推进问题的话，也可以随时进入我的粉丝群提问。"
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


def run_is_yellow(run: ElementTree.Element) -> bool:
    rpr = run.find(W_NS + "rPr")
    if rpr is None:
        return False
    highlight = rpr.find(W_NS + "highlight")
    if highlight is not None and (highlight.get(W_NS + "val") or "").lower() == "yellow":
        return True
    shading = rpr.find(W_NS + "shd")
    if shading is not None and (shading.get(W_NS + "fill") or "").upper() == "FFFF00":
        return True
    return False


def collect_yellow_segments(word_xml: list[str]) -> tuple[list[str], int, int]:
    segments: list[str] = []
    yellow_run_count = 0
    yellow_other_count = 0
    for xml in word_xml:
        root = ElementTree.fromstring(xml)
        all_yellow_nodes = [
            node
            for node in root.iter()
            if (
                node.tag == W_NS + "highlight"
                and (node.get(W_NS + "val") or "").lower() == "yellow"
            )
            or (
                node.tag == W_NS + "shd"
                and (node.get(W_NS + "fill") or "").upper() == "FFFF00"
            )
        ]
        run_yellow_nodes = 0
        for paragraph in root.iter(W_NS + "p"):
            current = ""
            for run in paragraph.iter(W_NS + "r"):
                text = "".join(node.text or "" for node in run.iter(W_NS + "t"))
                if run_is_yellow(run):
                    yellow_run_count += 1
                    run_yellow_nodes += 1
                    current += text
                elif current:
                    segments.append(current)
                    current = ""
            if current:
                segments.append(current)
        yellow_other_count += max(0, len(all_yellow_nodes) - run_yellow_nodes)
    return segments, yellow_run_count, yellow_other_count


def load_insertion_manifest(path: Path, exact_ending: str) -> tuple[dict[str, object], list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    soft = data.get("soft_placements")
    opening_guidance = data.get("opening_guidance")
    mid_cta = data.get("mid_cta")
    fixed_ending = data.get("fixed_ending")
    highlight_texts = data.get("highlight_texts")
    if not isinstance(soft, list):
        raise ValueError("manifest soft_placements must be a list")
    if soft:
        raise ValueError("manifest soft_placements must be empty; 3.1 uses fixed opening guidance plus one mid CTA")
    if opening_guidance != DEFAULT_OPENING_GUIDANCE:
        raise ValueError("manifest opening_guidance does not match the fixed 3.1 opening guidance")
    if not isinstance(mid_cta, str) or not mid_cta:
        raise ValueError("manifest mid_cta must be a nonempty string")
    if fixed_ending != exact_ending:
        raise ValueError("manifest fixed_ending does not match --exact-ending")
    if not isinstance(highlight_texts, list) or not highlight_texts or not all(isinstance(item, str) and item for item in highlight_texts):
        raise ValueError("manifest highlight_texts must be a nonempty string list")
    required = [opening_guidance, mid_cta, fixed_ending]
    if highlight_texts != required:
        raise ValueError("manifest highlight_texts must be exactly [opening_guidance, mid_cta, fixed_ending] in Word-body order")
    return data, highlight_texts


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
    parser.add_argument("--require-anchor-in-closing", action="store_true")
    highlight_group = parser.add_mutually_exclusive_group()
    highlight_group.add_argument("--insertion-manifest", type=Path)
    highlight_group.add_argument("--allow-no-yellow", action="store_true")
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
        "final_opening_contains_anchor": False,
        "final_closing_contains_anchor": False,
        "forbidden_label_hits": label_hits,
    }
    final_paragraphs = [item.strip() for item in re.split(r"\n\s*\n", final_text) if item.strip()]
    if final_paragraphs:
        checks["mother_topic"]["final_opening_contains_anchor"] = bool(
            anchor and anchor in normalize(final_paragraphs[0])
        )
        conclusion_text = final_text
        if conclusion_text.endswith(args.exact_ending):
            conclusion_text = conclusion_text[: -len(args.exact_ending)].rstrip()
        checks["mother_topic"]["final_closing_contains_anchor"] = bool(
            anchor and anchor in normalize(conclusion_text[-1200:])
        )
    if not checks["mother_topic"]["source_contains_anchor"]:
        errors.append("mother-topic anchor missing from source")
    if not checks["mother_topic"]["frozen_contains_anchor"]:
        errors.append("mother-topic anchor missing from frozen source")
    if not checks["mother_topic"]["final_contains_anchor"]:
        errors.append("mother-topic anchor missing from final body")
    if not checks["mother_topic"]["final_opening_contains_anchor"]:
        errors.append("mother-topic anchor missing from final opening paragraph")
    if args.require_anchor_in_closing and not checks["mother_topic"]["final_closing_contains_anchor"]:
        errors.append("mother-topic anchor missing from final closing section")
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

    scan_paragraphs = list(paragraphs)
    try:
        verbatim_start = scan_paragraphs.index("开头版本三：保留原文开头（来自源文档）")
        optimized_start = scan_paragraphs.index("开头版本四：原文开头优化版（贴合正文）")
        if optimized_start > verbatim_start:
            scan_paragraphs = scan_paragraphs[:verbatim_start + 1] + scan_paragraphs[optimized_start:]
            checks["word_structure"]["verbatim_source_opening_excluded_from_forbidden_scan"] = True
    except ValueError:
        checks["word_structure"]["verbatim_source_opening_excluded_from_forbidden_scan"] = False
    word_forbidden_scan_text = "\n".join(scan_paragraphs)
    word_forbidden_hits = [term for term in forbidden_terms if term and term in word_forbidden_scan_text]
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

    yellow_segments: list[str] = []
    yellow_run_count = 0
    yellow_other_count = 0
    if word_xml:
        try:
            yellow_segments, yellow_run_count, yellow_other_count = collect_yellow_segments(word_xml)
        except Exception as exc:
            errors.append(f"yellow highlight extraction failed: {exc}")

    highlight_check: dict[str, object] = {
        "mode": "required_manifest" if args.insertion_manifest else ("explicit_clean_override" if args.allow_no_yellow else "missing_mode"),
        "yellow_run_count": yellow_run_count,
        "yellow_other_markup_count": yellow_other_count,
        "actual_segments": yellow_segments,
    }
    if args.insertion_manifest:
        try:
            manifest, expected_highlights = load_insertion_manifest(args.insertion_manifest, args.exact_ending)
            actual_compact = [compact(item) for item in yellow_segments]
            expected_compact = [compact(item) for item in expected_highlights]
            final_counts = {item: final_text.count(item) for item in expected_highlights}
            opening_guidance = str(manifest["opening_guidance"])
            mid_cta = str(manifest["mid_cta"])
            opening_guidance_index = final_paragraphs.index(opening_guidance) if opening_guidance in final_paragraphs else -1
            mid_cta_index = final_paragraphs.index(mid_cta) if mid_cta in final_paragraphs else -1
            highlight_check.update({
                "manifest": str(args.insertion_manifest),
                "expected_segments": expected_highlights,
                "expected_count": len(expected_highlights),
                "actual_count": len(yellow_segments),
                "exact_ordered_match": actual_compact == expected_compact,
                "expected_text_final_counts": final_counts,
                "opening_guidance_paragraph_index": opening_guidance_index,
                "mid_cta_paragraph_index": mid_cta_index,
            })
            if actual_compact != expected_compact:
                errors.append("Word yellow-highlight segments do not exactly match insertion manifest")
            if any(count != 1 for count in final_counts.values()):
                errors.append("each insertion manifest text must appear exactly once in final body")
            if opening_guidance_index != 1:
                errors.append("fixed opening guidance must be the paragraph immediately after the first substantive opening paragraph")
            if mid_cta_index <= opening_guidance_index or mid_cta_index >= len(final_paragraphs) - 1:
                errors.append("mid CTA must appear after the opening guidance and before the fixed ending")
            if yellow_other_count:
                errors.append("yellow markup found outside text runs")
            if not manifest:
                errors.append("insertion manifest is empty")
        except Exception as exc:
            errors.append(f"insertion manifest check failed: {exc}")
    elif args.allow_no_yellow:
        highlight_check["exact_ordered_match"] = not yellow_segments and yellow_run_count == 0 and yellow_other_count == 0
        if yellow_segments or yellow_run_count or yellow_other_count:
            errors.append("yellow highlight found despite --allow-no-yellow")
    else:
        highlight_check["exact_ordered_match"] = False
        errors.append("3.1 default requires --insertion-manifest; use --allow-no-yellow only for an explicit clean-copy request")
    checks["yellow_highlight_manifest"] = highlight_check

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
