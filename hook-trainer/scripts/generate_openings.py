#!/usr/bin/env python3
"""Generate new openings by combining article variables with learned hook formulas."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

KEYWORD_CATEGORIES = {
    "topic": [
        "追女生",
        "聊天",
        "表白",
        "暧昧",
        "付出",
        "框架",
        "吸引力",
        "性张力",
        "服从测试",
        "废物测试",
        "情绪价值",
        "底层逻辑",
        "损失厌恶",
        "同盟感",
    ],
    "pain": [
        "低位",
        "内耗",
        "冷淡",
        "不回消息",
        "好人卡",
        "备胎",
        "舔狗",
        "卑微",
        "焦虑",
        "被筛选",
        "掉价",
        "追错方向",
    ],
    "action": [
        "讨好",
        "主动付出",
        "频繁聊天",
        "解释",
        "证明",
        "表白",
        "追逐",
        "克制",
        "筛选",
        "推进",
        "制造不确定性",
        "保留底气",
    ],
    "mechanism": [
        "人性",
        "反人性",
        "框架",
        "底层逻辑",
        "不确定性",
        "损失厌恶",
        "间歇性强化",
        "蔡加尼克效应",
        "慕强",
        "高位",
        "价值",
        "稀缺",
    ],
    "result": [
        "上头",
        "离不开",
        "主动靠近",
        "主动付出",
        "翻盘",
        "拿捏",
        "关系升温",
        "心动",
        "追逐你",
        "尊重你",
    ],
}

DEFAULTS = {
    "topic": "这段关系",
    "pain": "低位",
    "action": "讨好",
    "mechanism": "人性底层逻辑",
    "result": "上头",
}

POLISH_MAP = {
    "pain": {
        "低位": "低位感",
        "内耗": "内耗",
        "冷淡": "被冷处理",
        "不回消息": "被晾着的位置",
        "好人卡": "被发好人卡的位置",
        "备胎": "备胎位置",
        "舔狗": "舔狗感",
        "卑微": "卑微感",
        "焦虑": "焦虑感",
        "被筛选": "被筛选的位置",
        "掉价": "掉价感",
        "追错方向": "追错方向的状态",
    },
    "mechanism": {
        "人性": "人性",
        "反人性": "反人性框架",
        "框架": "框架",
        "底层逻辑": "高位逻辑",
        "不确定性": "不确定性",
        "损失厌恶": "稀缺感",
        "间歇性强化": "间歇性反馈",
        "蔡加尼克效应": "未完成感",
        "慕强": "慕强属性",
        "高位": "高位姿态",
        "价值": "价值感",
        "稀缺": "稀缺感",
    },
    "result": {
        "上头": "上头",
        "离不开": "离不开你",
        "主动靠近": "主动靠近",
        "主动付出": "主动付出",
        "翻盘": "重新被你吸引",
        "拿捏": "被你拿捏",
        "关系升温": "投入这段关系",
        "心动": "心动",
        "追逐你": "反过来追逐你",
        "尊重你": "尊重你",
    },
}

FRAME_TEMPLATES = [
    (
        "黑暗真相式",
        [
            "今天聊一个很黑暗的真相。很多人输在【topic】里，不是因为不够真诚，而是太早暴露【action】。你越想证明自己，越容易掉进【pain】，真正决定结果的是【mechanism】。",
            "说一个比较残酷的真相。【topic】最要命的地方，不是你不会技巧，而是你一开始就把位置放错了。你越【action】，对方越难【result】，因为【mechanism】从来不奖励低位的人。",
            "很多人不敢承认，【topic】里最黑暗的真相是，越急着【action】，越容易暴露【pain】。真正让对方【result】的，不是你多用力，而是你身上的【mechanism】。",
            "【topic】最残酷的一点是，你以为【action】是在推进关系，其实是在降低价值。对方真正会【result】的，往往是那个先守住【mechanism】的人。",
        ],
    ),
    (
        "高位警告式",
        [
            "永远不要在【topic】里一上来就【action】。你越急着表现，越容易暴露【pain】。真正的高位不是多做，而是懂得克制，让对方先感受到你的【mechanism】。",
            "千万别把【action】当成深情。很多关系就是从这一步开始掉价的。你以为自己在推进【topic】，其实是在把【pain】递给对方，最后连【result】的机会都没有。",
            "不要在【topic】里太快交出底牌。你越【action】，越容易被看成【pain】。真正有吸引力的人，会先稳住【mechanism】，再让对方慢慢【result】。",
            "如果你在【topic】里已经开始【pain】，先停下【action】。你现在最该补的不是技巧，而是【mechanism】，否则越努力越掉价。",
        ],
    ),
    (
        "反人性式",
        [
            "【topic】真正反人性的地方在于，你越想得到，越不能表现得非要不可。太直接的【action】不会制造【result】，只会让你的价值变便宜，因为【mechanism】只会奖励有框架的人。",
            "真正让人【result】的，从来不是你做了多少【action】，而是你有没有让对方感到【mechanism】。你越怕失去，越容易陷进【pain】，这就是关系里最反人性的地方。",
            "越想在【topic】里赢，你越要反着来。别急着【action】，先让对方感到你的【mechanism】。人性只会对不确定和稀缺【result】。",
            "很多人输在【topic】里，是因为太顺着本能走。越【action】，越容易【pain】；越懂【mechanism】，越容易让对方【result】。",
        ],
    ),
    (
        "底层逻辑式",
        [
            "为什么很多人在【topic】里明明很努力，最后还是被发好人卡？因为他把【action】当成真诚，却没看懂【mechanism】。真正有效的不是追，而是先让自己脱离【pain】。",
            "【topic】的底层逻辑不是你做得越多越有价值，而是谁先掌握【mechanism】。当你用【action】去换结果时，你已经进入【pain】；当你有框架时，对方才可能【result】。",
            "【topic】真正的底层逻辑是，价值不是靠【action】证明出来的，而是靠【mechanism】感受出来的。你越怕【pain】，越难让对方【result】。",
            "你以为【topic】靠的是努力，其实靠的是位置。只要你还在用【action】换回应，对方就很难【result】，因为你已经暴露了【pain】。",
        ],
    ),
    (
        "痛点恐吓式",
        [
            "如果你一进入【topic】，就开始【action】、解释、证明、制造内耗，那你基本已经输了。对方还没开始【result】，你就先把自己的框架和高位交出去了。",
            "当你在【topic】里越来越【pain】的时候，千万别急着加大【action】。你越用力，对方越容易看穿你的需求感，最后不是【result】，而是被彻底拿捏。",
            "一旦你在【topic】里开始【pain】，就不要再加码【action】了。你越补救，对方越能看见你的需求感，最后不是【result】，而是彻底失去框架。",
            "如果你总在【topic】里反复【action】，却换不来【result】，问题多半不是技巧，而是你已经被放进【pain】的位置。",
        ],
    ),
    (
        "结果诱惑式",
        [
            "想让对方真的【result】，你先别急着【action】。先让她感受到你的【mechanism】，再让她发现你不是随时都能得到的人。关系升温，靠的从来不是追，而是价值感。",
            "真正能让【topic】变顺的，不是你拼命【action】，而是你让对方开始投入、猜测和靠近。只要你守住【mechanism】，她才会从观望变成【result】。",
            "想让对方在【topic】里真的【result】，你要先制造价值感，而不是急着【action】。当你的【mechanism】够稳，她才会主动投入。",
            "真正让人【result】的，不是你在【topic】里多主动，而是你有【mechanism】、有边界、有稀缺感。她越猜不透，越容易靠近。",
        ],
    ),
]


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as docx:
        root = ElementTree.fromstring(docx.read("word/document.xml"))
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{WORD_NAMESPACE}t")).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def read_source(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if not args.file:
        raise ValueError("Provide --text or --file.")
    path = args.file
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return path.read_text(encoding="utf-8")


def load_high_frequency_words(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    words: list[str] = []
    for item in data:
        if isinstance(item, list) and item:
            words.append(str(item[0]))
    return words


def extract_category(text: str, category: str, high_frequency_words: list[str]) -> list[str]:
    candidates = KEYWORD_CATEGORIES[category]
    found = [word for word in candidates if word in text]
    seen: set[str] = set()
    unique = []
    for word in found:
        if word not in seen:
            unique.append(word)
            seen.add(word)
    return unique[:8]


def extract_variables(text: str, high_frequency_words: list[str]) -> dict[str, list[str]]:
    return {
        category: extract_category(text, category, high_frequency_words)
        for category in KEYWORD_CATEGORIES
    }


def pick(variables: dict[str, list[str]], category: str, index: int = 0) -> str:
    values = variables.get(category, [])
    if values:
        return values[index % len(values)]
    return DEFAULTS[category]


def polish_variable(category: str, value: str) -> str:
    return POLISH_MAP.get(category, {}).get(value, value)


def fill_template(template: str, variables: dict[str, list[str]], variant: int) -> str:
    replacements = {
        category: polish_variable(category, pick(variables, category, variant))
        for category in ("topic", "pain", "action", "mechanism", "result")
    }
    output = template
    for key, value in replacements.items():
        output = output.replace(f"【{key}】", value)
    return output


def visible_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def polish_sentence(text: str) -> str:
    replacements = {
        "真正让人被你拿捏的": "真正让对方被你拿捏的",
        "陷进被冷处理": "陷进冷处理的被动位置",
        "开始备胎位置": "掉进备胎位置",
        "越来越被发好人卡的位置的时候": "越来越像被发好人卡的时候",
        "不会制造重新被你吸引": "不会让对方重新被你吸引",
        "越难让对方重新被你吸引": "越难重新吸引对方",
        "换不来离不开你": "换不来她离不开你",
        "暴露低位感": "暴露低位",
        "掉进低位感": "掉进低位",
        "脱离卑微感": "脱离卑微的位置",
        "你越怕低位感": "你越怕掉到低位",
        "被看成追错方向的状态": "被看成低价值的追逐者",
        "把卑微感递给对方": "把卑微递给对方",
        "未完成感感受出来": "未完成感制造出来",
        "框架变顺": "关系变顺",
    }
    polished = text
    for before, after in replacements.items():
        polished = polished.replace(before, after)
    return polished


def normalize_opening(text: str, max_chars: int = 78) -> str:
    text = polish_sentence(text)
    compact = re.sub(r"\s+", "", text)
    if len(compact) <= max_chars:
        return text
    # Keep punctuation rhythm where possible by cutting at sentence boundary.
    sentences = re.split(r"(?<=[。！？!?])", text)
    kept = ""
    for sentence in sentences:
        if visible_length(kept + sentence) > max_chars:
            break
        kept += sentence
    if visible_length(kept) >= 45:
        return kept.strip()
    return compact[:max_chars]


def score_opening(text: str, variables: dict[str, list[str]], high_frequency_words: list[str]) -> dict[str, int]:
    length = visible_length(text)
    all_vars = {word for words in variables.values() for word in words}
    var_hits = sum(1 for word in all_vars if word in text)
    freq_hits = sum(1 for word in high_frequency_words[:40] if word in text)
    conflict_hits = sum(1 for word in ("不要", "不是", "而是", "真相", "低位", "反人性", "残酷", "黑暗") if word in text)
    gap_hits = sum(1 for word in ("为什么", "因为", "真正", "从来不是", "其实") if word in text)
    length_score = 10 if 50 <= length <= 70 else 8 if 45 <= length <= 78 else 5
    return {
        "主题贴合度": min(10, 4 + var_hits),
        "爆词密度": min(10, 3 + freq_hits),
        "冲突感": min(10, 4 + conflict_hits * 2),
        "信息缺口": min(10, 4 + gap_hits * 2),
        "口播顺滑度": length_score,
        "综合分": min(10, round((min(10, 4 + var_hits) + min(10, 3 + freq_hits) + min(10, 4 + conflict_hits * 2) + min(10, 4 + gap_hits * 2) + length_score) / 5)),
    }


def generate_openings(text: str, high_frequency_words: list[str], limit: int = 20) -> dict[str, object]:
    variables = extract_variables(text, high_frequency_words)
    candidates: list[dict[str, object]] = []
    variant = 0
    for frame, templates in FRAME_TEMPLATES:
        for template in templates:
            opening = normalize_opening(fill_template(template, variables, variant))
            score = score_opening(opening, variables, high_frequency_words)
            candidates.append(
                {
                    "frame": frame,
                    "opening": opening,
                    "used_words": sorted({word for words in variables.values() for word in words if word in opening}),
                    "used_high_frequency_words": [
                        word for word in high_frequency_words[:60] if word in opening
                    ][:10],
                    "scores": score,
                }
            )
            variant += 1
    candidates.sort(key=lambda item: (-int(item["scores"]["综合分"]), str(item["frame"]), str(item["opening"])))
    selected = candidates[:limit]
    for index, item in enumerate(selected, start=1):
        item["rank"] = index
    return {"variables": variables, "count": len(selected), "results": selected}


def write_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(data: dict[str, object], path: Path) -> None:
    lines = ["# Generated Openings", "", "## Extracted Variables", ""]
    variables = data["variables"]
    for category in ("topic", "pain", "action", "mechanism", "result"):
        lines.append(f"- {category}: {' / '.join(variables.get(category, []))}")
    lines.append("")
    lines.append("## Openings")
    for item in data["results"]:
        lines.append(f"### {item['rank']}. {item['frame']} - {item['scores']['综合分']}/10")
        lines.append("")
        lines.append(str(item["opening"]))
        lines.append("")
        lines.append(f"爆词: {' / '.join(item['used_words'])}")
        high_frequency_hits = item.get("used_high_frequency_words", [])
        if high_frequency_hits:
            lines.append(f"高频词: {' / '.join(high_frequency_hits)}")
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate new hook openings from a draft article.")
    parser.add_argument("--file", type=Path, help="Input .docx/.txt/.md article.")
    parser.add_argument("--text", help="Input article or topic text.")
    parser.add_argument(
        "--high-frequency",
        type=Path,
        default=Path("/Users/kin/工作用（同步）/开头hook/hook_trainer_output/formula_library/high_frequency_words.json"),
        help="High-frequency words JSON from Hook Trainer V2.",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("-o", "--output", type=Path, default=Path("generated_openings.json"))
    parser.add_argument("--markdown", type=Path, help="Optional Markdown output path.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    source = read_source(args)
    data = generate_openings(source, load_high_frequency_words(args.high_frequency), limit=args.limit)
    write_json(data, args.output)
    if args.markdown:
        write_markdown(data, args.markdown)
    print(f"Generated {data['count']} openings -> {args.output}")
    if args.markdown:
        print(f"Markdown report -> {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
