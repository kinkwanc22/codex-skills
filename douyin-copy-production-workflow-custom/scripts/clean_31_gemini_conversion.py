#!/usr/bin/env python3
"""Remove only clearly separable old-2.5 conversion units from 3.1 Gemini raw text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from validate_31_gemini_no_cta import PATTERNS
from validate_mother_topic_lock import read_text


SENTENCE_RE = re.compile(r".*?(?:[。！？!?][”’\"']?|$)", re.DOTALL)

DOUBAO_RE = re.compile(r"豆包|(?:AI|人工智能).{0,16}(?:总结|精髓|思维导图)|思维导图", re.IGNORECASE)
ENGAGEMENT_RE = re.compile(
    r"(?:点个赞|(?:请|记得|别忘了|顺手|帮我|可以)点赞|点赞(?:收藏|[、/和并与]收藏)|点个收藏|收藏一下|评论区(?:留言|告诉|打出)|转发给|艾特(?:给|一下)?|@豆包)",
    re.IGNORECASE,
)
GROUP_RE = re.compile(r"粉丝群|内部群|进群|加入.{0,6}群|群里见")
GROUP_ACTION_RE = re.compile(
    r"加我的?粉丝群|(?:直接|现在|赶紧|马上|先)?进(?:我的?)?粉丝群|"
    r"加入.{0,6}群|入口就在|发到群里|来找我|深度咨询|策略指导|群里见"
)
CONTACT_RE = re.compile(r"(?:私信|咨询|点开|打开|点击|去主页|关注我|来找我).{0,24}(?:分析|诊断|咨询|解决|入口|主页|Gary|探花Gary)?")
DIRECT_ACTION_RE = re.compile(
    r"(?:请|记得|欢迎|直接|现在|赶紧|马上|可以|点开|打开|点击|去).{0,16}(?:关注|私信|咨询|主页|找我)"
    r"|来(?:找我|咨询|私信|关注我)"
    r"|(?:关注|私信|咨询).{0,6}(?:我|Gary|探花Gary)"
)
ACCOUNT_RE = re.compile(r"我是探花Gary|我是Gary")
INLINE_ACCOUNT_RE = re.compile(r"(?:我)?作为(?:探花)?Gary[,，]?", re.IGNORECASE)
ENDING_RE = re.compile(r"我是探花Gary.{0,100}(?:感谢观看|群里见)|我们(?:粉丝群|内部群)里见|感谢观看\s*$", re.DOTALL)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))


def classify(sentence: str, paragraph: str) -> str | None:
    if DOUBAO_RE.search(sentence):
        return "doubao_or_ai_summary_prompt"
    if ENDING_RE.search(sentence) or (ACCOUNT_RE.search(sentence) and GROUP_RE.search(paragraph)):
        return "old_or_fixed_ending"
    if GROUP_RE.search(sentence) and (GROUP_ACTION_RE.search(sentence) or CONTACT_RE.search(sentence)):
        return "fan_group_or_contact_cta"
    if ENGAGEMENT_RE.search(sentence):
        return "engagement_prompt"
    if ACCOUNT_RE.search(sentence):
        return "account_self_introduction"
    if DIRECT_ACTION_RE.search(sentence):
        return "direct_contact_cta"
    if CONTACT_RE.search(sentence) and re.search(r"(?:你|兄弟|大家|观众|粉丝).{0,30}(?:私信|咨询|主页|关注|找我)", sentence):
        return "direct_contact_cta"
    return None


def split_sentences(paragraph: str) -> list[str]:
    return [match.group(0) for match in SENTENCE_RE.finditer(paragraph) if match.group(0)]


def residual_hits(text: str) -> dict[str, list[str]]:
    hits = {
        name: [m.group(0) for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE)]
        for name, pattern in PATTERNS.items()
    }
    return {name: values for name, values in hits.items() if values}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest-out", required=True, type=Path)
    args = parser.parse_args()

    raw = read_text(args.input)
    paragraphs = re.split(r"\n\s*\n", raw.strip())
    cleaned_paragraphs: list[str] = []
    removals: list[dict[str, object]] = []

    for paragraph_index, paragraph in enumerate(paragraphs):
        if (
            GROUP_RE.search(paragraph)
            and GROUP_ACTION_RE.search(paragraph)
            and not (ACCOUNT_RE.search(paragraph) and ENDING_RE.search(paragraph))
        ):
            removals.append(
                {
                    "category": "fan_group_or_contact_cta",
                    "text": paragraph,
                    "paragraph_index": paragraph_index,
                    "sentence_index": None,
                }
            )
            continue
        kept: list[str] = []
        for sentence_index, sentence in enumerate(split_sentences(paragraph)):
            inline_account_matches = list(INLINE_ACCOUNT_RE.finditer(sentence))
            if inline_account_matches:
                for match in inline_account_matches:
                    removals.append(
                        {
                            "category": "inline_account_self_introduction",
                            "text": match.group(0),
                            "paragraph_index": paragraph_index,
                            "sentence_index": sentence_index,
                        }
                    )
                sentence = INLINE_ACCOUNT_RE.sub("", sentence)
            category = classify(sentence, paragraph)
            if category:
                removals.append(
                    {
                        "category": category,
                        "text": sentence,
                        "paragraph_index": paragraph_index,
                        "sentence_index": sentence_index,
                    }
                )
            else:
                kept.append(sentence)
        residual = "".join(kept).strip()
        if residual:
            cleaned_paragraphs.append(residual)

    cleaned = "\n\n".join(cleaned_paragraphs).strip() + "\n"
    hits = residual_hits(cleaned)
    substantive_loss_ratio = 1 - (cjk_count(cleaned) / max(cjk_count(raw), 1))
    requires_regeneration = bool(hits) or substantive_loss_ratio > 0.20
    report = {
        "mode": "3.1_gemini_conversion_cleanup",
        "input": str(args.input),
        "output": str(args.output),
        "raw_sha256": sha256_text(raw),
        "clean_sha256": sha256_text(cleaned),
        "raw_cjk": cjk_count(raw),
        "clean_cjk": cjk_count(cleaned),
        "removed_cjk": cjk_count(raw) - cjk_count(cleaned),
        "substantive_loss_ratio_guard": round(substantive_loss_ratio, 6),
        "removal_count": len(removals),
        "removals": removals,
        "residual_hits": hits,
        "requires_regeneration": requires_regeneration,
        "pass": not requires_regeneration,
    }
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if requires_regeneration:
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(cleaned, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
