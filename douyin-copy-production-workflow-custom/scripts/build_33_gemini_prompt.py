#!/usr/bin/env python3
"""Build a 3.3 prompt from the complete old 2.5 block and exact topic lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


HEADING = "### 2.5 Direct Draft"
SOURCE_MARKER = "【原文开始】"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_complete_25(reference: Path) -> str:
    text = reference.read_text(encoding="utf-8")
    heading_at = text.find(HEADING)
    if heading_at < 0:
        raise ValueError(f"missing heading: {HEADING}")
    match = re.search(r"```text\n(.*?)\n```", text[heading_at:], flags=re.DOTALL)
    if not match:
        raise ValueError("missing fenced 2.5 Direct Draft block")
    block = match.group(1).rstrip()
    if not block.endswith(SOURCE_MARKER):
        raise ValueError(f"2.5 block must end with {SOURCE_MARKER}")
    return block[: -len(SOURCE_MARKER)].rstrip()


def clean_slot(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    if "<" in value or ">" in value:
        raise ValueError(f"{name} contains unresolved placeholder brackets")
    return value


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_reference = script_dir.parent / "references" / "gemini-expansion.md"
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini-reference", type=Path, default=default_reference)
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--mother-topic-source-quote", required=True)
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--public-topic", required=True)
    parser.add_argument("--promised-count", default="无固定数量")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-out", type=Path)
    args = parser.parse_args()

    source_quote = clean_slot("mother-topic-source-quote", args.mother_topic_source_quote)
    anchor = clean_slot("anchor", args.anchor)
    public_topic = clean_slot("public-topic", args.public_topic)
    promised_count = clean_slot("promised-count", args.promised_count)
    if anchor not in source_quote:
        raise ValueError("anchor must occur verbatim in mother-topic-source-quote")
    if public_topic != anchor and public_topic not in source_quote:
        raise ValueError("public-topic must equal the anchor or occur verbatim in the source quote")

    frozen = args.frozen.read_text(encoding="utf-8").strip()
    if not frozen:
        raise ValueError("frozen source is empty")
    if anchor not in frozen or public_topic not in frozen:
        raise ValueError("frozen source must contain the exact anchor and public topic")

    block_25 = extract_complete_25(args.gemini_reference)
    lock = f"""【3.3公开母题逐字锁定｜最高优先级】
本篇公开母题来自源文正文，必须逐字使用：
母题源文句：{source_quote}
母题锚点：{anchor}
公开母题：{public_topic}
原稿数量承诺：{promised_count}

你的第一句必须逐字包含“{public_topic}”。
强制片头结构中的【文案核心】必须直接使用“{public_topic}”，不得用正文内部机制、关系位置、主动权、框架感、总结标签或新概念替代。
正文内部机制只能作为该母题下面的解释和内容，不得提升为新的公开总标题，不得出现在母题之前组织全文。
全文收束时再次逐字使用“{public_topic}”；如有数量承诺，必须完整兑现且不得增减。"""
    prompt = f"{block_25}\n\n{lock}\n\n{SOURCE_MARKER}\n{frozen}\n【原文结束】\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt, encoding="utf-8")
    metadata = {
        "mode": "3.3_codex_designed_pretransplant",
        "knowledge_base_used": False,
        "codex_content_invention": True,
        "gemini_reference": str(args.gemini_reference),
        "frozen": str(args.frozen),
        "mother_topic_source_quote": source_quote,
        "mother_topic_anchor": anchor,
        "mother_topic_public_wording": public_topic,
        "promised_count": promised_count,
        "old_2.5_prompt_sha256": sha256_text(block_25),
        "frozen_sha256": sha256_text(frozen),
        "prompt_sha256": sha256_text(prompt),
    }
    if args.metadata_out:
        args.metadata_out.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_out.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
