#!/usr/bin/env python3
"""Build a reusable original-opening framework library from opening_library.json."""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path


TOPIC_KEYWORDS = [
    "恋爱脑",
    "内耗",
    "追女生",
    "聊天",
    "暧昧",
    "冷淡",
    "不回消息",
    "分手",
    "挽回",
    "付出",
    "主动付出",
    "好人卡",
    "低位",
    "高位",
    "框架",
    "性张力",
    "吸引力",
    "上头",
    "上瘾",
    "离不开",
    "情绪价值",
    "沉没成本",
    "损失厌恶",
    "冷读",
    "废物测试",
    "服从测试",
    "圣母情结",
    "女性思维",
    "强者心态",
    "顶级心态",
]

RHETORICAL_MARKERS = {
    "如果",
    "为什么",
    "不是而是",
    "不要",
    "真相",
    "黑暗",
    "残酷",
    "顶级",
}


ARCHETYPES = [
    {
        "name": "残酷真相反转",
        "needles": ("残忍的真相", "残酷的真相", "黑暗的真相", "不愿意承认的真相", "真相"),
        "steps": ["残酷判断", "具体失控状态", "权威或机制视角", "否定主观感受"],
        "skeleton": "说一个比较残忍的真相。\n如果你正在【失控状态】，不断【痛苦行为】，甚至【极端后果】。\n从【权威/机制视角】来看，这并不是【你以为的原因】，而是【真正原因】。",
    },
    {
        "name": "否定转折纠偏",
        "needles": ("不是", "而是"),
        "steps": ["提出常见误解", "否定表层答案", "给出反常识答案", "留下继续听的原因"],
        "skeleton": "【目标结果】不是因为【常见解释】，也不是因为【另一个误解】。\n真正起作用的，是【反常识机制】。\n如果你没看懂这一点，后面做再多都容易错。",
    },
    {
        "name": "问题追问拆解",
        "needles": ("为什么", "答案", "核心"),
        "steps": ["抛出高痛问题", "承认用户困惑", "给出底层答案入口", "承诺讲透机制"],
        "skeleton": "为什么【反常识现象】？\n很多人以为是【表层原因】，但真正的答案是【底层机制】。\n这期我把【关键逻辑】给你讲透。",
    },
    {
        "name": "高压禁止提醒",
        "needles": ("永远不要", "千万不要", "不要", "别急着", "一定不要"),
        "steps": ["禁止本能动作", "指出低位代价", "给出高位动作", "解释为什么不能这样做"],
        "skeleton": "永远不要【低位行为】。\n哪怕你再【强烈情绪】，也不要急着【本能动作】。\n因为一旦你这么做，对方看到的就不是爱，而是【掉价信号】。",
    },
    {
        "name": "场景痛点推进",
        "needles": ("如果你", "当你", "当一个人", "如果近期", "如果一个"),
        "steps": ["具体痛点场景", "说出用户当前反应", "阻止本能动作", "给出反直觉方向"],
        "skeleton": "如果你正在【具体场景】，你现在最想做的一定是【本能反应】。\n但我告诉你，越是这个时候，越不能【错误动作】。\n真正能翻盘的，是【反直觉动作】。",
    },
    {
        "name": "极端结果诱惑",
        "needles": ("离不开", "上瘾", "死心塌地", "无法抵抗", "主动付出", "翻盘"),
        "steps": ["抛出极端结果", "压缩成关键机制", "否定普通方法", "给出诱惑承诺"],
        "skeleton": "让【对象】真正【极端结果】的核心，不是【普通方法】，而是【关键机制】。\n你只要吃透这一点，她就会从【原状态】变成【目标状态】。",
    },
    {
        "name": "身份碾压宣告",
        "needles": ("顶级", "高段位", "强者", "高手", "天花板", "最稀缺"),
        "steps": ["给出顶级身份或结果", "否定普通答案", "抬高方法段位", "制造身份向往"],
        "skeleton": "真正【高段位身份】的人，从来不是靠【普通做法】。\n他们真正厉害的地方，是掌握了【稀缺能力】。\n这也是普通人和高手之间最大的差距。",
    },
    {
        "name": "禁忌揭露开场",
        "needles": ("脏", "邪恶", "秘密", "禁术", "隐秘", "坏坏", "强行"),
        "steps": ["抛出禁忌词", "声明不是表层误解", "揭开隐藏欲望", "承诺给出方法"],
        "skeleton": "今天聊一个比较【禁忌词】的话题。\n它不是你想的【表层误解】，而是藏在【对象】潜意识里的【隐藏欲望】。\n看懂以后，你会知道关系为什么会被这样推动。",
    },
    {
        "name": "强判断故事入口",
        "needles": (),
        "steps": ["先给强判断", "补一个具体状态", "解释反常识原因", "留下听下去的钩子"],
        "skeleton": "【强判断】。\n很多人遇到【具体状态】时，第一反应都是【错误理解】。\n但真正决定结果的，其实是【反常识原因】。",
    },
]


def load_openings(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list: {path}")
    return data


def write_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def split_units(hook: str) -> list[str]:
    parts = re.split(r"[\n。！？!?；;]+", hook)
    return [part.strip(" ，,、") for part in parts if part.strip(" ，,、")]


def choose_archetype(hook: str) -> dict[str, object]:
    text = compact(hook)
    if ("真相" in text or "黑暗" in text or "残酷" in text or "残忍" in text) and (
        text.startswith("说一个") or text.startswith("今天聊") or "不愿意承认" in text
    ):
        return ARCHETYPES[0]
    best = ARCHETYPES[-1]
    best_score = -1
    for archetype in ARCHETYPES:
        needles = archetype["needles"]
        score = sum(1 for needle in needles if needle and needle in text)
        if archetype["name"] == "否定转折纠偏" and "不是" in text and ("而是" in text or "是" in text):
            score += 2
        if score > best_score:
            best = archetype
            best_score = score
    return best


def extract_topics(hook: str, existing_keywords: list[object]) -> list[str]:
    topics = [word for word in TOPIC_KEYWORDS if word in hook]
    topics.extend(
        str(word)
        for word in existing_keywords
        if isinstance(word, str) and len(str(word)) >= 2 and str(word) not in RHETORICAL_MARKERS
    )
    seen: set[str] = set()
    result = []
    for topic in topics:
        if topic not in seen:
            result.append(topic)
            seen.add(topic)
    return result[:10]


def extract_rhetorical_markers(hook: str, existing_keywords: list[object]) -> list[str]:
    markers = [marker for marker in RHETORICAL_MARKERS if marker in hook]
    markers.extend(str(word) for word in existing_keywords if isinstance(word, str) and str(word) in RHETORICAL_MARKERS)
    seen: set[str] = set()
    result = []
    for marker in markers:
        if marker not in seen:
            result.append(marker)
            seen.add(marker)
    return result


def extract_signature_lines(hook: str) -> list[str]:
    units = split_units(hook)
    if len(units) <= 5:
        return units
    return units[:5]


def build_original_framework(item: dict[str, object]) -> dict[str, object]:
    hook = str(item.get("hook", "")).strip()
    archetype = choose_archetype(hook)
    topics = extract_topics(hook, list(item.get("keywords", [])))
    markers = extract_rhetorical_markers(hook, list(item.get("keywords", [])))
    return {
        "source_id": item.get("source_id", ""),
        "file_name": item.get("file_name", ""),
        "rank": item.get("rank", ""),
        "score": item.get("score", ""),
        "fine_frame": item.get("fine_frame", ""),
        "sentence_pattern": item.get("sentence_pattern", ""),
        "micro_framework": archetype["name"],
        "original_hook": hook,
        "signature_lines": extract_signature_lines(hook),
        "structure_steps": archetype["steps"],
        "reusable_skeleton": archetype["skeleton"],
        "best_for_topics": topics,
        "rhetorical_markers": markers,
        "keywords": item.get("keywords", []),
    }


def build_framework_library(openings: list[dict[str, object]], limit: int = 200) -> dict[str, object]:
    selected = openings[:limit]
    frameworks = [build_original_framework(item) for item in selected if str(item.get("hook", "")).strip()]
    micro_counts = collections.Counter(item["micro_framework"] for item in frameworks)
    frame_counts = collections.Counter(item["fine_frame"] for item in frameworks)
    topic_counts = collections.Counter(topic for item in frameworks for topic in item["best_for_topics"])
    marker_counts = collections.Counter(marker for item in frameworks for marker in item["rhetorical_markers"])
    summary = {
        "records": len(frameworks),
        "micro_framework_counts": micro_counts.most_common(),
        "fine_frame_counts": frame_counts.most_common(),
        "top_topics": topic_counts.most_common(40),
        "rhetorical_marker_counts": marker_counts.most_common(),
    }
    return {"summary": summary, "frameworks": frameworks}


def write_markdown(data: dict[str, object], path: Path, examples_per_type: int = 8) -> None:
    summary = data["summary"]
    frameworks = data["frameworks"]
    lines = [
        "# Original Opening Framework Library",
        "",
        f"Records: {summary['records']}",
        "",
        "## Micro Framework Counts",
    ]
    lines.extend(f"- {name}: {count}" for name, count in summary["micro_framework_counts"])
    lines.append("")
    lines.append("## Top Topics")
    lines.extend(f"- {name}: {count}" for name, count in summary["top_topics"][:25])
    lines.append("")
    lines.append("## Rhetorical Markers")
    lines.extend(f"- {name}: {count}" for name, count in summary["rhetorical_marker_counts"][:25])
    grouped: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for item in frameworks:
        grouped[str(item["micro_framework"])].append(item)
    for framework_name, items in sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        lines.extend(["", f"## {framework_name}", ""])
        first = items[0]
        lines.append("结构：")
        lines.append(" → ".join(str(step) for step in first["structure_steps"]))
        lines.append("")
        lines.append("可复用骨架：")
        lines.append("```text")
        lines.append(str(first["reusable_skeleton"]))
        lines.append("```")
        lines.append("")
        lines.append("原文样本：")
        for index, item in enumerate(items[:examples_per_type], start=1):
            lines.append("")
            lines.append(f"### {index}. {item['fine_frame']} / score {item['score']}")
            lines.append(f"来源：{item['file_name']}")
            lines.append("")
            lines.append("```text")
            lines.append(str(item["original_hook"]).replace("\n", " / "))
            lines.append("```")
            if item["best_for_topics"]:
                lines.append(f"适合主题：{' / '.join(item['best_for_topics'])}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build original hook framework library from opening_library.json.")
    parser.add_argument("opening_library", type=Path, help="Input opening_library.json path.")
    parser.add_argument("-o", "--output-dir", type=Path, required=True, help="Output directory.")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--examples-per-type", type=int, default=8)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    data = build_framework_library(load_openings(args.opening_library), limit=args.limit)
    write_json(data["frameworks"], args.output_dir / "original_frameworks.json")
    write_json(data["summary"], args.output_dir / "original_frameworks_summary.json")
    write_markdown(data, args.output_dir / "original_frameworks.md", examples_per_type=args.examples_per_type)
    print(f"Built {data['summary']['records']} original frameworks -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
