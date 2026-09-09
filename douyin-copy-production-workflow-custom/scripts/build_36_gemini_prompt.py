#!/usr/bin/env python3
"""Build a 3.6 prompt: 3.5-style frozen route expanded by complete 2.8."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


HEADING = "### 2.8 Safe Draft / 安全版"
SOURCE_MARKER = "【原文开始】"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_slot(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must not be empty")
    if "<" in value or ">" in value:
        raise ValueError(f"{name} contains unresolved placeholder brackets")
    return value


def extract_complete_28(reference: Path) -> str:
    text = reference.read_text(encoding="utf-8")
    heading_at = text.find(HEADING)
    if heading_at < 0:
        raise ValueError(f"missing heading: {HEADING}")
    match = re.search(r"```text\n(.*?)\n```", text[heading_at:], flags=re.DOTALL)
    if not match:
        raise ValueError("missing fenced 2.8 Safe Draft block")
    block = match.group(1).rstrip()
    if not block.endswith(SOURCE_MARKER):
        raise ValueError(f"2.8 block must end with {SOURCE_MARKER}")
    return block[: -len(SOURCE_MARKER)].rstrip()


def load_build_35(script_dir: Path):
    path = script_dir / "build_35_gemini_prompt.py"
    spec = importlib.util.spec_from_file_location("build_35_for_36", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load 3.5 validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gemini-reference",
        type=Path,
        default=script_dir.parent / "references" / "gemini-expansion.md",
    )
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--engine-plan", required=True, type=Path)
    parser.add_argument("--mother-topic-source-quote", required=True)
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--public-topic", required=True)
    parser.add_argument("--source-promised-count", default="无固定数量")
    parser.add_argument("--promised-count", default="无固定数量")
    parser.add_argument(
        "--content-line",
        required=True,
        choices=("short_term", "growth_psychology"),
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-out", type=Path)
    args = parser.parse_args()

    source_quote = clean_slot("mother-topic-source-quote", args.mother_topic_source_quote)
    anchor = clean_slot("anchor", args.anchor)
    public_topic = clean_slot("public-topic", args.public_topic)
    source_count = clean_slot("source-promised-count", args.source_promised_count)
    selected_count = clean_slot("promised-count", args.promised_count)
    if anchor not in source_quote:
        raise ValueError("anchor must occur verbatim in mother-topic-source-quote")
    if anchor not in public_topic and public_topic not in source_quote:
        raise ValueError("public-topic must contain the anchor or occur in the source quote")

    frozen = args.frozen.read_text(encoding="utf-8").strip()
    if not frozen:
        raise ValueError("frozen source is empty")
    if anchor not in frozen or public_topic not in frozen:
        raise ValueError("frozen source must contain the exact anchor and public topic")

    build_35 = load_build_35(script_dir)
    backstage = [x for x in build_35.FROZEN_BACKSTAGE_FRAGMENTS if x in frozen]
    if backstage:
        raise ValueError("3.6 frozen source contains backstage language: " + ", ".join(backstage))

    frozen_cjk = len(re.findall(r"[\u4e00-\u9fff]", frozen))
    count_int = int(selected_count) if re.fullmatch(r"\d+", selected_count) else 0
    adaptive_limit = min(1599, max(1000, count_int * 60 + 400))
    if frozen_cjk > adaptive_limit:
        raise ValueError(
            f"3.6 frozen source is over-developed: {frozen_cjk} CJK exceeds {adaptive_limit}"
        )

    engine_plan, engine_summary = build_35.load_and_validate_old_25_engine_plan(
        args.engine_plan,
        public_topic=public_topic,
        promised_count=selected_count,
        frozen=frozen,
    )
    block_28 = extract_complete_28(args.gemini_reference)

    content_line_text = (
        "用时间、场域、距离、选择和可观察反馈体现快速吸引与推进；不要公开输出短期线等生产标签。"
        if args.content_line == "short_term"
        else "所有成长、事业、自律和心理内容都必须落回女人的评估、男女吸引、互动选择或关系位置；不要公开输出成长心理线等生产标签。"
    )
    lock = f"""【3.6安全换新锁｜最高优先级】
本稿已经完成3.5式换新设计。你只能扩写这份冻结稿，不得回到旧原文机制，也不得自行换题。
母题源文句：{source_quote}
母题锚点：{anchor}
公开母题：{public_topic}
原稿数量参考：{source_count}
本轮成稿数量承诺：{selected_count}

第一句必须逐字包含“{public_topic}”。公开母题、目标读者、关系阶段、目标结果和核心冲突不得改变。
原稿数量只是历史参考；本轮只以“本轮成稿数量承诺”为准，必须完整兑现，不得临时增减。
冻结稿中的全部公开观点必须被写透，不能把安全表达理解成删掉观点、抽空因果或改成健康沟通科普。
不得创造一个比“{public_topic}”更适合概括全文的新框架、新理论或新总标题。
{content_line_text}
使用完整2.8安全版的真人口播、隐藏六层结构、敏感词弱化和TTS规则。压迫感来自具体判断、场景和后果，不来自高风险词或形容词堆叠。
如冻结稿含“此处植入案例。”，必须删除标记并写成紧凑的说明性案例；不得虚构可核验身份、精确金额、截图、咨询规模、保证结果或独立验证事实。
最后一句必须逐字为：我是探花Gary，我们粉丝群里见，感谢观看。"""

    prompt = f"{block_28}\n\n{lock}\n\n{SOURCE_MARKER}\n{frozen}\n【原文结束】\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt, encoding="utf-8")

    metadata = {
        "mode": "3.6_safe_transplant",
        "design_route": "3.5_pre_expansion",
        "expansion_route": "2.8_safe_draft",
        "recommended_session": "3.6",
        "knowledge_base_used": True,
        "codex_content_invention": True,
        "gemini_reference": str(args.gemini_reference),
        "frozen": str(args.frozen),
        "old_25_engine_plan": str(args.engine_plan),
        "old_25_engine_plan_sha256": sha256_text(
            json.dumps(engine_plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        ),
        **engine_summary,
        "mother_topic_source_quote": source_quote,
        "mother_topic_anchor": anchor,
        "mother_topic_public_wording": public_topic,
        "source_promised_count": source_count,
        "selected_promised_count": selected_count,
        "count_changed_from_source": source_count != selected_count,
        "content_line": args.content_line,
        "content_line_label_internal_only": True,
        "complete_2.8_prompt_sha256": sha256_text(block_28),
        "final_cjk_hard_minimum": 4300,
        "final_cjk_preferred_range": [4800, 5600],
        "frozen_sha256": sha256_text(frozen),
        "frozen_cjk": frozen_cjk,
        "adaptive_frozen_cjk_limit": adaptive_limit,
        "lean_frozen_source_pass": frozen_cjk <= adaptive_limit,
        "frozen_backstage_language_pass": not backstage,
        "prompt_sha256": sha256_text(prompt),
    }
    if args.metadata_out:
        args.metadata_out.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_out.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
