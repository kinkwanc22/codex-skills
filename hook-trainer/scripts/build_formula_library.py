#!/usr/bin/env python3
"""Build Hook Trainer V2 formula and opening libraries."""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path
from typing import Iterable


FINE_FRAME_RULES = [
    ("黑暗真相式", ("黑暗", "真相", "血淋淋", "本质", "底层", "现实", "残酷")),
    ("高位警告式", ("永远不要", "千万不要", "不要", "别", "一旦", "代价", "输")),
    ("反人性式", ("人性", "反人性", "本能", "欲望", "圣母情结", "慕强", "上头")),
    ("痛点恐吓式", ("冷淡", "不回", "失去", "低位", "焦虑", "内耗", "搞砸", "辜负")),
    ("结果诱惑式", ("上瘾", "离不开", "主动付出", "死心塌地", "越来越", "翻盘", "逆袭")),
    ("禁忌揭露式", ("脏", "邪恶", "秘密", "禁术", "不愿意承认", "隐秘", "坏坏")),
    ("身份碾压式", ("强者", "顶级", "阿尔法", "高位", "领袖", "王者", "高手")),
    ("底层逻辑式", ("为什么", "核心", "逻辑", "规则", "机制", "原理", "答案")),
]

STOP_WORDS = {
    "一个",
    "这个",
    "那个",
    "就是",
    "因为",
    "如果",
    "不是",
    "但是",
    "所以",
    "什么",
    "怎么",
    "时候",
    "自己",
    "对方",
    "女人",
    "男人",
    "女生",
    "关系",
    "感情",
}

HUMAN_KEYWORDS = [
    "黑暗",
    "真相",
    "残酷",
    "底层逻辑",
    "底层机制",
    "人性",
    "反人性",
    "欲望",
    "本能",
    "慕强",
    "圣母情结",
    "情绪价值",
    "情绪反扑",
    "安全感",
    "不配得感",
    "上头",
    "离不开",
    "上瘾",
    "主动付出",
    "付出",
    "沉没成本",
    "多巴胺",
    "催产素",
    "冷淡",
    "不回消息",
    "冷落",
    "内耗",
    "焦虑",
    "低位",
    "高位",
    "框架",
    "克制",
    "翻盘",
    "拿捏",
    "博弈",
    "拉扯",
    "破防",
    "调情",
    "聊天",
    "暧昧",
    "关系推进",
    "废物测试",
    "服从性测试",
    "性张力",
    "吸引力",
    "强者",
    "阿尔法",
    "领袖",
    "顶级",
    "邪恶",
    "脏",
    "秘密",
    "禁术",
    "冷读",
    "普通男生",
    "漂亮女生",
    "价值",
    "稀缺",
    "挑战",
]

FORMULA_RULES = [
    (re.compile(r"为什么说(.+?)(?:\n|，|。)(.+)"), "为什么说【X】\n【Y】\n因为【底层机制】"),
    (re.compile(r"永远不要(.+?)(?:\n|，|。)(.+)"), "永远不要【行为/心态】\n哪怕【诱惑条件】\n因为一旦【代价】"),
    (re.compile(r"如果(.+?)(?:\n|，|。)(.+)"), "如果【具体场景】\n先不要【本能反应】\n因为【反直觉原因】"),
    (re.compile(r"(.+?)不是(.+?)(?:而是|是)(.+)"), "真正的【结果】\n不是【常见解释】\n而是【反常识答案】"),
    (re.compile(r"(.+?)离不开(.+)"), "让【对象】离不开你的核心\n不是【表层条件】\n而是【关键机制】"),
]


def load_analysis(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected analysis JSON list: {path}")
    return data


def write_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def classify_fine_frame(hook: str) -> str:
    scores = {
        label: sum(1 for keyword in keywords if keyword in hook)
        for label, keywords in FINE_FRAME_RULES
    }
    label, score = max(scores.items(), key=lambda item: item[1])
    return label if score > 0 else "强判断解释式"


def infer_sentence_pattern(hook: str) -> str:
    stripped = hook.strip()
    if stripped.startswith("为什么"):
        return "问题追问句"
    if "永远不要" in stripped or "千万不要" in stripped or stripped.startswith("不要"):
        return "高压警告句"
    if stripped.startswith("如果"):
        return "场景假设句"
    if "不是" in stripped and ("而是" in stripped or "是" in stripped):
        return "否定转折句"
    if "离不开" in stripped or "上瘾" in stripped:
        return "结果诱惑句"
    if "今天聊" in stripped or "我会" in stripped:
        return "主题宣告句"
    return "强判断开场句"


def infer_formula(hook: str) -> str:
    for pattern, formula in FORMULA_RULES:
        if pattern.search(hook):
            return formula
    frame = classify_fine_frame(hook)
    if frame == "黑暗真相式":
        return "今天聊一个【黑暗/残酷真相】\n我会告诉你【普通人不知道的规则】\n看懂越早越能【改变结果】"
    if frame == "高位警告式":
        return "永远不要【低位行为】\n哪怕你再【强烈情绪】\n因为一旦【失控表现】就会【掉价后果】"
    if frame == "反人性式":
        return "真正让【对象】产生【强情绪】的\n不是【表层条件】\n而是【人性底层机制】"
    if frame == "痛点恐吓式":
        return "当【痛点场景】发生时\n你越【本能反应】\n越会【关系恶化】"
    if frame == "结果诱惑式":
        return "让【对象】越来越【目标状态】的\n不是【常见做法】\n而是【关键动作/机制】"
    return "先给出【强判断】\n再补充【反常识解释】\n最后留下【必须听下去的原因】"


def extract_keywords(text: str) -> list[str]:
    words = [word for word in HUMAN_KEYWORDS if word in text]
    if "为什么" in text:
        words.append("为什么")
    if "永远不要" in text or "不要" in text:
        words.append("不要")
    if "不是" in text and ("而是" in text or "是" in text):
        words.append("不是而是")
    if "如果" in text:
        words.append("如果")
    return words


def score_opening(item: dict[str, object], high_freq: collections.Counter[str]) -> float:
    hook = str(item.get("hook", ""))
    frame = str(item.get("fine_frame", ""))
    score = 0.0
    length = len(hook.replace("\n", ""))
    if 45 <= length <= 70:
        score += 2.0
    if frame != "强判断解释式":
        score += 1.5
    if item.get("formula"):
        score += 1.0
    score += min(sum(high_freq[word] for word in item.get("keywords", [])[:8]) / 100, 2.0)
    return round(score, 3)


def enrich_item(record: dict[str, object]) -> dict[str, object]:
    hook = str(record.get("hook", ""))
    keywords = extract_keywords(hook)
    return {
        "source_id": record.get("source_id", ""),
        "file_name": record.get("file_name", ""),
        "hook": hook,
        "coarse_type": record.get("hook_type", ""),
        "emotion": record.get("emotion", ""),
        "rhythm": record.get("rhythm", ""),
        "fine_frame": classify_fine_frame(hook),
        "sentence_pattern": infer_sentence_pattern(hook),
        "formula": infer_formula(hook),
        "keywords": keywords[:20],
        "template": record.get("template", ""),
    }


def build_libraries(records: Iterable[dict[str, object]], limit: int = 200) -> dict[str, object]:
    enriched = [enrich_item(record) for record in records if str(record.get("hook", "")).strip()]
    high_freq = collections.Counter()
    for item in enriched:
        high_freq.update(item["keywords"])

    for item in enriched:
        item["score"] = score_opening(item, high_freq)

    opening_library = sorted(
        enriched,
        key=lambda item: (-float(item["score"]), str(item["fine_frame"]), str(item["file_name"])),
    )[:limit]
    for index, item in enumerate(opening_library, start=1):
        item["rank"] = index

    formulas_by_key: dict[tuple[str, str, str], dict[str, object]] = {}
    for item in enriched:
        key = (str(item["fine_frame"]), str(item["sentence_pattern"]), str(item["formula"]))
        bucket = formulas_by_key.setdefault(
            key,
            {
                "fine_frame": item["fine_frame"],
                "sentence_pattern": item["sentence_pattern"],
                "formula": item["formula"],
                "count": 0,
                "examples": [],
                "keywords": collections.Counter(),
            },
        )
        bucket["count"] += 1
        bucket["keywords"].update(item["keywords"])
        if len(bucket["examples"]) < 5:
            bucket["examples"].append(item["hook"])

    formula_library = []
    for bucket in formulas_by_key.values():
        formula_library.append(
            {
                "fine_frame": bucket["fine_frame"],
                "sentence_pattern": bucket["sentence_pattern"],
                "formula": bucket["formula"],
                "count": bucket["count"],
                "keywords": [word for word, _count in bucket["keywords"].most_common(15)],
                "examples": bucket["examples"],
            }
        )
    formula_library.sort(key=lambda item: (-int(item["count"]), str(item["fine_frame"])))

    frame_counts = collections.Counter(item["fine_frame"] for item in enriched)
    pattern_counts = collections.Counter(item["sentence_pattern"] for item in enriched)
    return {
        "summary": {
            "records": len(enriched),
            "opening_library_size": len(opening_library),
            "formula_count": len(formula_library),
            "frame_counts": frame_counts.most_common(),
            "sentence_pattern_counts": pattern_counts.most_common(),
        },
        "formula_library": formula_library,
        "opening_library": opening_library,
        "high_frequency_words": high_freq.most_common(200),
    }


def write_report(data: dict[str, object], path: Path) -> None:
    summary = data["summary"]
    lines = [
        "# Hook Trainer V2 Report",
        "",
        f"Records: {summary['records']}",
        f"Opening library size: {summary['opening_library_size']}",
        f"Formula count: {summary['formula_count']}",
        "",
        "## Fine Frames",
    ]
    lines.extend([f"- {label}: {count}" for label, count in summary["frame_counts"]])
    lines.append("")
    lines.append("## Top Formulas")
    for item in data["formula_library"][:20]:
        lines.append(f"- {item['fine_frame']} / {item['sentence_pattern']} / {item['count']}")
        lines.append(f"  {item['formula'].replace(chr(10), ' / ')}")
    lines.append("")
    lines.append("## Top Openings")
    for item in data["opening_library"][:30]:
        lines.append(f"- [{item['rank']}] {item['fine_frame']} / {item['emotion']} / score {item['score']}")
        lines.append(f"  {item['hook'].replace(chr(10), ' / ')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Hook Trainer V2 formula libraries.")
    parser.add_argument("analysis", type=Path, help="Input analysis.json path.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for V2 libraries.",
    )
    parser.add_argument("--limit", type=int, default=200, help="Opening library size.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build_libraries(load_analysis(args.analysis), limit=args.limit)
    write_json(data["formula_library"], args.output_dir / "formula_library.json")
    write_json(data["opening_library"], args.output_dir / "opening_library.json")
    write_json(data["high_frequency_words"], args.output_dir / "high_frequency_words.json")
    write_json(data["summary"], args.output_dir / "v2_summary.json")
    write_report(data, args.output_dir / "v2_report.md")
    print(
        f"Built {data['summary']['formula_count']} formulas and "
        f"{data['summary']['opening_library_size']} openings -> {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
