#!/usr/bin/env python3
"""Analyze parsed Hook Trainer scripts into analysis.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")

HOOK_TYPE_RULES = [
    ("反常识", ("其实", "不是", "真正", "你以为", "很多人以为", "误会")),
    ("警告提醒", ("不要", "别", "千万", "最容易", "危险", "低位")),
    ("痛点直击", ("冷淡", "不回", "焦虑", "难受", "崩", "失控", "内耗")),
    ("结果承诺", ("学会", "做到", "让她", "上头", "推进", "变快")),
    ("场景切入", ("如果", "当你", "有一天", "突然", "聊天", "关系")),
]

EMOTION_RULES = [
    ("焦虑", ("冷淡", "不回", "焦虑", "解释", "失去", "被动", "低位")),
    ("好奇", ("为什么", "其实", "真正", "你以为", "反而", "秘密")),
    ("压力", ("千万", "不要", "危险", "崩", "代价", "最容易")),
    ("渴望", ("上头", "喜欢", "靠近", "关系变快", "习惯", "情绪波动")),
    ("清醒", ("误会", "不是", "真相", "本质", "位置")),
]


def load_json(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list: {path}")
    return data


def write_json(records: Iterable[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(list(records), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def clean_line(line: str) -> str:
    if MARKDOWN_HEADING_RE.match(line):
        return ""
    return line.strip().strip(" -\t")


def split_sentences(text: str) -> list[str]:
    candidates = [clean_line(part) for part in SENTENCE_SPLIT_RE.split(text)]
    return [part for part in candidates if part]


def extract_hook(text: str, max_sentences: int = 2, max_chars: int = 120) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""

    hook_parts: list[str] = []
    for sentence in sentences:
        if len("".join(hook_parts)) >= max_chars:
            break
        hook_parts.append(sentence)
        if len(hook_parts) >= max_sentences:
            break

    hook = "\n".join(hook_parts).strip()
    if len(hook) <= max_chars:
        return hook
    return hook[:max_chars].rstrip() + "..."


def classify_by_rules(text: str, rules: list[tuple[str, tuple[str, ...]]], fallback: str) -> str:
    scores: dict[str, int] = {}
    for label, keywords in rules:
        scores[label] = sum(1 for keyword in keywords if keyword in text)
    label, score = max(scores.items(), key=lambda item: item[1])
    return label if score > 0 else fallback


def classify_hook_type(hook: str) -> str:
    return classify_by_rules(hook, HOOK_TYPE_RULES, "直接陈述")


def classify_emotion(hook: str) -> str:
    return classify_by_rules(hook, EMOTION_RULES, "中性")


def describe_rhythm(hook: str) -> str:
    sentences = split_sentences(hook)
    if not hook:
        return "空文本"
    avg_len = len(hook) / max(len(sentences), 1)
    if len(sentences) >= 2 and avg_len <= 22:
        return "短句推进"
    if "。" in hook and len(hook) >= 60:
        return "长句铺垫"
    if "\n" in hook:
        return "分行停顿"
    return "单句直给"


def infer_information_gap(hook: str) -> str:
    if "你以为" in hook and "其实" in hook:
        return "表面认知和真实原因之间的反差"
    if "不是" in hook and "而是" in hook:
        return "否定常见解释后给出新答案"
    if "如果" in hook:
        return "提出具体场景但延迟说明原因"
    if "不要" in hook or "别" in hook:
        return "警告行为后延迟说明代价"
    if "为什么" in hook:
        return "提出问题但延迟答案"
    return "开头给出判断，后文需要展开原因"


def build_template(hook: str) -> str:
    if "你以为" in hook and "其实" in hook:
        return "你以为X，其实真正影响结果的是Y"
    if "不是" in hook and "而是" in hook:
        return "不是X，而是Y"
    if hook.startswith("如果"):
        return "如果出现X，先不要Y，因为Z"
    if "不要" in hook:
        return "面对X，不要急着Y，真正要看Z"
    return "先给出强判断，再解释背后的原因"


def infer_niche(record: dict[str, object], hook: str) -> str:
    text = f"{record.get('file_name', '')} {hook} {record.get('text', '')}"
    if any(keyword in text for keyword in ("女生", "关系", "聊天", "表白", "男人", "情绪")):
        return "男性情感"
    return "通用"


def analyze_record(record: dict[str, object]) -> dict[str, object]:
    text = str(record.get("text", ""))
    hook = extract_hook(text)
    return {
        "source_id": record.get("source_id", ""),
        "file_path": record.get("file_path", ""),
        "file_name": record.get("file_name", ""),
        "niche": infer_niche(record, hook),
        "hook": hook,
        "hook_type": classify_hook_type(hook),
        "emotion": classify_emotion(hook),
        "rhythm": describe_rhythm(hook),
        "information_gap": infer_information_gap(hook),
        "template": build_template(hook),
        "notes": "rule-based V1 analysis",
    }


def analyze_records(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    return [analyze_record(record) for record in records]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze parsed scripts into analysis.json.")
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("examples/output/parsed.json"),
        help="Input parsed.json path.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("examples/output/analysis.json"),
        help="Output analysis.json path.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    records = analyze_records(load_json(args.input))
    write_json(records, args.output)
    print(f"Analyzed {len(records)} records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
