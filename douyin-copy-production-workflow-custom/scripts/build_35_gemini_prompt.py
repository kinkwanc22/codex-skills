#!/usr/bin/env python3
"""Build a 3.5 prompt with exact topic, content-line, and natural-rhythm locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


HEADING = "### 2.5 Direct Draft"
SOURCE_MARKER = "【原文开始】"
FROZEN_BACKSTAGE_FRAGMENTS = (
    "案例事实必须保留",
    "结果必须明确来自",
    "这就是Gary咨询后调整带来的明确结果",
    "成功结果必须具体",
    "总判断：",
    "总判断:",
    "收束：",
    "收束:",
    "开头逻辑：",
    "开头逻辑:",
    "核心总结：",
    "核心总结:",
    "结尾总结：",
    "结尾总结:",
    "写作说明：",
    "写作说明:",
    "段落任务：",
    "段落任务:",
)


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


def adapt_25_length_for_35(block: str) -> str:
    """Keep the 2.5 surface while giving lean 3.5 one consistent length contract."""
    old_target = "必须极其深入地剖析，正文目标 6000-8000 个中文字符。"
    new_target = "必须深入地剖析，正文目标 4200-5200 个中文字符。"
    old_floor = "如果正文不足 7000 个中文字符，继续扩写，不要提前结束。"
    new_floor = "如果正文不足 4000 个中文字符，继续扩写，不要提前结束；超过4200后以完整和自然为先，不要重复灌水。"
    if block.count(old_target) != 1 or block.count(old_floor) != 1:
        raise ValueError("unexpected 2.5 length contract; update the 3.5 adapter explicitly")
    return block.replace(old_target, new_target).replace(old_floor, new_floor)


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
    default_natural_lock = script_dir.parent / "references" / "3.5-natural-rhythm-lock.txt"
    parser = argparse.ArgumentParser()
    parser.add_argument("--gemini-reference", type=Path, default=default_reference)
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--mother-topic-source-quote", required=True)
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--public-topic", required=True)
    parser.add_argument("--source-promised-count", default="无固定数量")
    parser.add_argument("--promised-count", default="无固定数量")
    parser.add_argument(
        "--content-line",
        required=True,
        choices=("short_term", "growth_psychology"),
        help="Private production line. This label must not appear in public copy.",
    )
    parser.add_argument(
        "--previous-content-line",
        choices=("short_term", "growth_psychology"),
        help="For scheduled sequences, validates that adjacent manuscripts alternate lines.",
    )
    parser.add_argument("--natural-lock", type=Path, default=default_natural_lock)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-out", type=Path)
    args = parser.parse_args()

    source_quote = clean_slot("mother-topic-source-quote", args.mother_topic_source_quote)
    anchor = clean_slot("anchor", args.anchor)
    public_topic = clean_slot("public-topic", args.public_topic)
    source_promised_count = clean_slot("source-promised-count", args.source_promised_count)
    promised_count = clean_slot("promised-count", args.promised_count)
    if args.previous_content_line == args.content_line:
        raise ValueError("scheduled adjacent 3.5 manuscripts must alternate content lines")
    if anchor not in source_quote:
        raise ValueError("anchor must occur verbatim in mother-topic-source-quote")
    if anchor not in public_topic and public_topic not in source_quote:
        raise ValueError("public-topic must contain the exact anchor or occur verbatim in the source quote")

    frozen = args.frozen.read_text(encoding="utf-8").strip()
    natural_lock = args.natural_lock.read_text(encoding="utf-8").strip()
    if not frozen:
        raise ValueError("frozen source is empty")
    if not natural_lock:
        raise ValueError("3.5 natural rhythm lock is empty")
    if anchor not in frozen or public_topic not in frozen:
        raise ValueError("frozen source must contain the exact anchor and public topic")
    frozen_backstage_leaks = [x for x in FROZEN_BACKSTAGE_FRAGMENTS if x in frozen]
    if frozen_backstage_leaks:
        raise ValueError(
            "3.5 frozen source contains backstage or editorial language that may leak into narration: "
            + ", ".join(frozen_backstage_leaks)
        )

    frozen_cjk = len(re.findall(r"[\u4e00-\u9fff]", frozen))
    promised_count_match = re.fullmatch(r"\d+", promised_count)
    selected_count_for_limit = int(promised_count) if promised_count_match else 0
    adaptive_frozen_cjk_limit = max(1800, selected_count_for_limit * 150 + 600)
    if frozen_cjk > adaptive_frozen_cjk_limit:
        raise ValueError(
            "3.5 frozen source is over-developed: "
            f"{frozen_cjk} CJK exceeds adaptive lean limit "
            f"{adaptive_frozen_cjk_limit}; compress it to thesis, point boundaries, "
            "essential scene constraints, and case facts/result before expansion"
        )

    block_25_original = extract_complete_25(args.gemini_reference)
    block_25 = adapt_25_length_for_35(block_25_original)
    lock = f"""【3.5公开母题逐字锁定｜最高优先级】
本篇公开母题来自源文正文，必须逐字使用：
母题源文句：{source_quote}
母题锚点：{anchor}
公开母题：{public_topic}
原稿数量参考：{source_promised_count}
本轮成稿数量承诺：{promised_count}

你的第一句必须逐字包含“{public_topic}”。
强制片头结构中的【文案核心】必须直接使用“{public_topic}”，不得用正文内部机制、关系位置、主动权、框架感、知识卡标题、总结标签或新概念替代。
正文内部机制只能作为该母题下面的解释和内容，不得提升为新的公开总标题，不得出现在母题之前组织全文。
原稿数字不构成本轮硬锁；以“本轮成稿数量承诺”为唯一数量合同。如本轮有数量承诺，必须完整兑现且不得临时增减。
公开母题只需在片头逐字出现一次。正文收束时禁止再次机械重复公开母题，最后一个正文观点或总结完成后，直接进入动态CTA与固定片尾。"""
    lock += "\n片头模板中的方括号内容只是写作说明，必须改写成真实钩子。成稿禁止输出【文章总结金句，短视频开头钩子】、【文案核心】或任何类似提示占位语，禁止把公开母题机械重复两遍。"
    if args.content_line == "short_term":
        line_lock = f"""【3.5内容线表达锁｜短期线｜内部标签禁止外显】
本稿的内部内容线是短期线，但成稿标题和正文禁止出现“短期线”“短期向”等生产标签。
用时间、场域、距离、选择、即时反馈和可观察行为体现快速吸引或靠近，不要反复解释关系类别。
如果且仅如果公开母题“{public_topic}”本身含有“短期关系”，在片头逐字使用母题时保留；除该母题句外，正文原则上不要继续重复“短期关系”四个字。
不得默认写成男朋友女朋友确立后的共同生活、关系修复、责任分配或未来规划。
快速约见、当晚延长、暧昧回传、主动靠近、现实清障和私密转场只是方向示例，不得机械塞进每一篇；公开机制必须由本篇锁定母题自然决定。
成年人双方自愿可以保留为一句背景边界，但除非公开母题本身讨论同意或边界识别，不得把“明确同意”单独升级为编号机制、标题终点或长篇说教。"""
    else:
        line_lock = f"""【3.5内容线表达锁｜成长心理线｜内部标签禁止外显】
本稿的内部内容线是成长心理线，但成稿标题和正文禁止出现“成长/心理线”“长期向”等生产标签。
文章应从公开母题“{public_topic}”自然展开男性成长、女性心理、人性规律、框架与主体性、事业或选择力；用心理机制、现实选择、能力变化和具体行为承载，不要反复解释关系类别。
成长心理线不等于情侣经营。除非公开母题本身明确要求，不得默认把正文写成共同生活、冲突修复、责任分工、未来规划或男朋友女朋友相处守则。
如果公开母题自然涉及关系，用该母题需要的场景证明心理或人性机制即可，不要把“长期关系”当作反复出现的总标签。"""
    case_lock = """【3.5案例完整性锁｜仅在原稿包含案例时生效】
如果原稿没有案例，不得为了套模板强行新增案例。
如果原稿包含“此处植入案例。”，这代表只锁定案例位置，不锁定案例内容。成稿必须删除该占位语，在原位置先逐字加入“我给兄弟们看一个最近咨询的案例。”作为自然转场，再完整生成一个与本篇机制贴合的案例。
如果原稿包含学员或兄弟案例，成稿必须完整保留六项：男性姓名、女性姓名、学员原始问题、Gary的具体指导/陪跑/咨询、学员执行后的行为变化、女生可观察反馈与最终成功结果。
两个人都必须有自然姓名。案例前必须逐字使用：“我给兄弟们看一个最近咨询的案例。”不得输出“下面这个案例根据常见咨询情况重构，人物名称和细节均已处理。”，姓名后不必标注“化名”。
案例说明后的第一句必须自然交代人物背景：男主什么时候来找Gary、当时和女方推进到哪一步，并保留原稿提供的职业、城市、年龄段或认识方式中的至少一个细节。不得把它压缩成“有个兄弟来找我咨询”，也不得自行补充精确日期、金额或可核验履历。
成功结果必须直接用与公开母题一致的可观察行为呈现，例如女生主动约下一次、主动延长互动、增加投入或同意计划中的下一步。成稿禁止讨论结果写得是否空洞、禁止引用内部反例、禁止解释案例验收规则或作者为什么这样写。
案例必须保留原稿冻结的专属场景、失败方式、Gary介入动作和结果形态，不得擅自套回“第一次失败、咨询后第二次见面、女生延长时间并给下次安排”的通用骨架，也不得只换姓名、物件或一句对话制造表面差异。
案例结果必须通过前文的咨询、执行变化和女人反馈自然呈现。禁止在结果后追加总结咨询归因、强调验收合规或解释案例规则的句子。
不得删除Gary的介入，不得把成功改写成学员自己突然醒悟，也不得添加精确日期、金额、截图、咨询数量或保证性结果。Word导出时只将上述案例重构说明整句标黄。"""
    prompt = f"{block_25}\n\n{lock}\n\n{line_lock}\n\n{case_lock}\n\n{natural_lock}\n\n{SOURCE_MARKER}\n{frozen}\n【原文结束】\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt, encoding="utf-8")
    metadata = {
        "mode": "3.5_codex_first_knowledge_supported",
        "knowledge_base_used": True,
        "codex_content_invention": True,
        "gemini_reference": str(args.gemini_reference),
        "frozen": str(args.frozen),
        "mother_topic_source_quote": source_quote,
        "mother_topic_anchor": anchor,
        "mother_topic_public_wording": public_topic,
        "source_promised_count": source_promised_count,
        "promised_count": promised_count,
        "selected_promised_count": promised_count,
        "count_changed_from_source": source_promised_count != promised_count,
        "content_line": args.content_line,
        "content_line_label_internal_only": True,
        "previous_content_line": args.previous_content_line,
        "alternation_applicable": args.previous_content_line is not None,
        "alternation_pass": (
            args.previous_content_line is None
            or args.previous_content_line != args.content_line
        ),
        "natural_lock": str(args.natural_lock),
        "natural_lock_sha256": sha256_text(natural_lock),
        "content_line_lock_sha256": sha256_text(line_lock),
        "named_case_lock_sha256": sha256_text(case_lock),
        "old_2.5_prompt_sha256": sha256_text(block_25_original),
        "effective_3.5_expansion_prompt_sha256": sha256_text(block_25),
        "final_cjk_hard_minimum": 4000,
        "final_cjk_preferred_range": [4200, 5200],
        "frozen_sha256": sha256_text(frozen),
        "frozen_cjk": frozen_cjk,
        "adaptive_frozen_cjk_limit": adaptive_frozen_cjk_limit,
        "lean_frozen_source_pass": frozen_cjk <= adaptive_frozen_cjk_limit,
        "frozen_backstage_language_pass": not frozen_backstage_leaks,
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
