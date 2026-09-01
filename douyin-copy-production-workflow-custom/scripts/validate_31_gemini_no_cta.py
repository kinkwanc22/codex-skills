#!/usr/bin/env python3
"""Legacy audit only; current 3.1 does not require a zero-CTA Gemini body."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from validate_mother_topic_lock import read_text


PATTERNS = {
    "doubao_or_ai_summary_prompt": r"豆包|AI.{0,12}(总结|精髓|思维导图)|思维导图",
    "engagement_prompt": r"点个赞|(?:请|记得|别忘了|顺手|帮我|可以)点赞|点赞(?:收藏|[、/和并与]收藏)|点个收藏|收藏一下|评论区(?:留言|告诉|打出)|转发给|艾特(?:给|一下)?|@豆包",
    "fan_group": r"粉丝群|内部群|进群|加入.{0,6}群|群里见",
    "profile_action": r"(?:点开|打开|点击|去).{0,8}主页",
    "direct_contact": r"私信(?:我|Gary|探花Gary)|(?:来找我|找我).{0,12}(?:分析|诊断|咨询|解决)",
    "follow_action": r"关注(?:我|Gary|探花Gary)",
    "account_intro": r"我是探花Gary|我是Gary",
    "fixed_ending": r"我是探花Gary，我们粉丝群里见，感谢观看|感谢观看\s*$",
    "backstage_cta_label": r"\bCTA\b|动态CTA|中段CTA|片尾CTA",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--report-out", type=Path)
    parser.add_argument("--legacy-audit", action="store_true")
    args = parser.parse_args()
    if not args.legacy_audit:
        parser.error("legacy-only validator: current 3.1 retains Gemini CTA/account/group content; pass --legacy-audit only for an explicitly requested historical audit")

    text = read_text(args.input)
    hits = {
        name: [match.group(0) for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE)]
        for name, pattern in PATTERNS.items()
    }
    hits = {name: values for name, values in hits.items() if values}
    report = {
        "mode": "3.1_gemini_clean_cta_free_validation",
        "input": str(args.input),
        "hits": hits,
        "pass": not hits,
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(output + "\n", encoding="utf-8")
    return 0 if not hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
