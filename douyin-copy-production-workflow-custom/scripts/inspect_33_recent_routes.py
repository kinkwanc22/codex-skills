#!/usr/bin/env python3
"""Report recent 3.3 routes and reject saturated proposals."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


FAMILY_TERMS = {
    "perception_attention": ("观察", "信号", "注意", "知觉", "识别"),
    "language_meaning": ("话术", "措辞", "叙事", "归因", "解释权", "对话"),
    "timing_sequence": ("节奏", "窗口", "时机", "顺序", "时间"),
    "environment_context": ("场景", "空间", "主场", "环境", "地点"),
    "identity_role": ("身份", "角色期待", "自我概念", "认同"),
    "emotion_memory": ("峰终", "记忆", "情绪峰值", "联想", "唤醒"),
    "learning_conditioning": ("强化", "奖惩", "习惯", "预测误差", "条件反射"),
    "incentives_exchange": ("投入", "损失厌恶", "沉没成本", "社会交换", "关系定价", "成本"),
    "social_structure": ("预选", "社会认同", "地位", "圈层", "群体", "符号资本"),
    "competence_behavior": ("执行", "能力", "决策", "行动", "压场", "解决"),
}


def load_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        return [x for x in data["entries"] if isinstance(x, dict)]
    raise ValueError("ledger must be a JSON list or an object with an entries list")


def is_accepted(entry: dict) -> bool:
    status = str(entry.get("status", "")).strip().lower()
    review = str(entry.get("review_state", "")).strip().lower()
    return (
        status.startswith("accepted")
        or status.startswith("generated")
        or status.startswith("user_confirmed")
        or "正文待确认" in review
    )


def entry_text(entry: dict) -> str:
    fields = [entry.get("route", ""), entry.get("route_signature", "")]
    fields.extend(entry.get("avoid_next_time") or [])
    fields.extend(entry.get("embedded_terms") or [])
    return " ".join(str(x) for x in fields)


def infer_families(entry: dict) -> list[str]:
    explicit = entry.get("mechanism_families") or []
    if explicit:
        return [str(x) for x in explicit]
    text = entry_text(entry)
    return [name for name, terms in FAMILY_TERMS.items() if any(term in text for term in terms)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--recent", type=int, default=20)
    parser.add_argument("--proposed-family")
    parser.add_argument("--route-signature")
    args = parser.parse_args()

    accepted = [x for x in load_entries(args.ledger) if is_accepted(x)]
    recent = accepted[-args.recent :]
    recent10 = accepted[-10:]
    counts = Counter(f for entry in recent10 for f in infer_families(entry))
    report = {
        "version": "3.3",
        "accepted_total": len(accepted),
        "recent_family_counts_last_10": dict(counts.most_common()),
        "recent_routes": [
            {
                "title": entry.get("title", ""),
                "families": infer_families(entry),
                "route_signature": entry.get("route_signature", ""),
                "route": entry.get("route", ""),
            }
            for entry in recent
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    errors = []
    if args.proposed_family and counts[args.proposed_family] >= 2:
        errors.append(
            f"primary family '{args.proposed_family}' already appears "
            f"{counts[args.proposed_family]} times in the last 10 accepted entries"
        )
    if args.route_signature:
        prior = {str(x.get("route_signature", "")).strip() for x in recent}
        if args.route_signature.strip() in prior:
            errors.append("route signature already appears in the recent accepted window")
    if errors:
        for error in errors:
            print(f"REJECT: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
