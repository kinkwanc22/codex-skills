#!/usr/bin/env python3
"""Build an auditable same-topic knowledge + history + hook call pack."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


VAULT = Path("/Users/kin/Gary 男性情感/Gary 男性情感")
B_LEDGER = VAULT / "02_B高价值知识/08_提炼记录/万赞文案_B层提炼记录.jsonl"
EXTERNAL_B_LEDGER = VAULT / "02_B高价值知识/08_提炼记录/外部资料_B层提炼记录.jsonl"
EXTERNAL_CHUNK_LEDGER = VAULT / "02_B高价值知识/08_提炼记录/外部资料_原子知识块.jsonl"
EXTERNAL_CASE_LEDGER = VAULT / "02_B高价值知识/08_提炼记录/外部资料_Gary匿名复合案例.jsonl"
HISTORICAL_PERFORMANCE_LEDGER = VAULT / "05_复盘与自生长/02_发布数据/历史作品效果证据.jsonl"
CROSS = Path("/Users/kin/Documents/Codex/2026-07-10/qu/work/obsidian_cross_source/final_modules.json")
HOOKS = VAULT / "03_C_Skill与方法库/爆款开头知识库/03_运行时数据/opening_records.json"
HISTORY_SCRIPT = Path("/Users/kin/Documents/Codex/2026-07-10/qu/scripts/query_31_32_history.py")
STOP = set("一个一种什么怎么为什么我们你们他们女生女人男人关系感情自己对方就是这个那个可以不是因为所以其实如果时候真的更加已经没有进行以及通过里面这样这种那些对于" )
CONCEPT_GROUPS = {
    "高颜值对象": ("顶美", "美女", "漂亮", "好看", "高颜值", "高分女", "美貌", "外貌"),
    "追求推进": ("追女生", "好追", "追求", "推进", "搭讪", "邀约", "认识女生"),
    "聊天表达": ("聊天", "话题", "话术", "表达", "回复", "消息"),
    "戒上头": ("上头", "内耗", "沦陷", "痴迷", "期待消息"),
    "吸引": ("吸引", "魅力", "性张力", "抵抗不了", "着迷"),
    "投入付出": ("投入", "付出", "沉没成本", "主动", "顺从"),
    "高低位": ("高位", "低位", "框架", "主权", "卑微", "讨好"),
    "筛选择偶": ("筛选", "择偶", "标准", "匹配", "不合适"),
    "关系修复": ("复合", "修复", "冷淡", "下头", "分手"),
    "女性核心需求": ("被认同", "认同感", "安全感", "被理解", "懂她", "特殊感", "偏爱", "独一无二", "致命需求", "四样东西", "女人最想要"),
    "生理欲望": ("生理需求", "生理欲望", "性欲", "身体反应", "本能", "欲望开关"),
    "男性内核": ("男性内核", "八大内核", "顶级男人", "强者内核", "内核稳定", "核心自信", "精神力量"),
}
FOCUS_TERMS = (
    "认同感", "被认同", "安全感", "被理解", "懂她", "偏爱", "独一无二", "特殊感", "占有欲",
    "生理需求", "生理欲望", "性欲", "本能", "需求感", "从认识到邀约", "关系推进", "暧昧", "邀约",
    "冷淡", "秒回", "主动回复", "沉没成本", "投入", "框架", "筛选", "高位", "低位",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def load_b_items() -> list[dict]:
    items = load_jsonl(B_LEDGER)
    present = {int(x["id"]) for x in items}
    trials = {
        3: ("兄弟们给女生情绪价值，记住这六个词就够了", "恋爱技巧", "直接", "02_B高价值知识/03_恋爱技巧/003_六类情绪价值表达.md"),
        40: ("所有的相见恨晚，背后往往都藏着一场算计", "人性博弈", "暗黑冒犯", "02_B高价值知识/04_人性博弈/040_委屈补偿与撤退放大.md"),
        94: ("恋爱中必须具备的强者思维", "爆款母题", "强硬", "02_B高价值知识/01_爆款母题/094_强者思维_只筛选不改变.md"),
    }
    for source_id, (title, knowledge_type, force, card) in trials.items():
        if source_id not in present:
            items.append({"id": source_id, "title": title, "knowledge_type": knowledge_type, "force": force, "card": card})
    return items


def load_external_b_items() -> list[dict]:
    if not EXTERNAL_B_LEDGER.exists():
        return []
    items = load_jsonl(EXTERNAL_B_LEDGER)
    return [
        {
            "id": str(item["id"]),
            "title": item["title"],
            "knowledge_type": item["knowledge_type"],
            "force": item["force"],
            "card": item["card"],
            "evidence_level": item.get("evidence_level", "单一外部来源"),
            "content_role": item.get("content_role", "外部知识源索引"),
            "gary_student_case": item.get("gary_student_case", False),
        }
        for item in items
    ]


def load_external_chunks() -> list[dict]:
    return load_jsonl(EXTERNAL_CHUNK_LEDGER) if EXTERNAL_CHUNK_LEDGER.exists() else []


def load_external_composite_cases() -> list[dict]:
    return load_jsonl(EXTERNAL_CASE_LEDGER) if EXTERNAL_CASE_LEDGER.exists() else []


def load_historical_performance() -> list[dict]:
    return load_jsonl(HISTORICAL_PERFORMANCE_LEDGER) if HISTORICAL_PERFORMANCE_LEDGER.exists() else []


def read_source(path: Path) -> str:
    if path.suffix.lower() == ".rtf":
        return subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)], check=True, capture_output=True, text=True).stdout.strip()
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    if path.suffix.lower() == ".docx":
        from zipfile import ZipFile
        from xml.etree import ElementTree
        with ZipFile(path) as zf:
            root = ElementTree.fromstring(zf.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        return "\n".join("".join(t.text or "" for t in p.iter(ns+"t")) for p in root.iter(ns+"p")).strip()
    raise ValueError(f"Unsupported source: {path}")


def infer_body_title(body: str, fallback: str) -> str:
    lines = [re.sub(r"\s+", " ", x).strip(" ，。！？") for x in body.splitlines() if x.strip()][:14]
    if not lines:
        return fallback
    promise_words = ("女人", "女生", "男人", "关系", "聊天", "邀约", "吸引", "需求", "心理", "为什么", "怎么", "几个", "几种", "几句话", "东西", "信号", "节点", "方法")
    def score(line: str, index: int) -> float:
        length = len(line)
        value = sum(3 for word in promise_words if word in line)
        value += 4 if re.search(r"[一二三四五六七八九十两0-9]+(?:大|个|种|条|句|点|步|关|样)", line) else 0
        value += 2 if 8 <= length <= 32 else 0
        value -= 3 if length < 7 or length > 45 else 0
        value -= 2 if line.endswith(("啊", "呢", "吧")) else 0
        value -= index * 0.12
        return value
    return max(enumerate(lines), key=lambda pair: score(pair[1], pair[0]))[1]


def tokens(text: str) -> set[str]:
    clean = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)
    grams = {clean[i:i+2] for i in range(max(0, len(clean)-1))}
    words = set(re.findall(r"[\u4e00-\u9fff]{2,8}", text))
    return {x for x in grams | words if x not in STOP and len(x) >= 2}


def concepts(text: str) -> set[str]:
    return {name for name, words in CONCEPT_GROUPS.items() if any(word in text for word in words)}


def focus_terms(text: str) -> set[str]:
    return {term for term in FOCUS_TERMS if term in text}


def normalized_key(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()


def relevance(query: set[str], query_concepts: set[str], title: str, body: str) -> float:
    title_tokens = tokens(title)
    body_tokens = tokens(body[:5000])
    title_hit = len(query & title_tokens)
    body_hit = len(query & body_tokens)
    title_concept_hit = len(query_concepts & concepts(title))
    body_concept_hit = len(query_concepts & concepts(body))
    return round(title_hit * 3.0 + body_hit / max(len(query) ** 0.5, 1) + title_concept_hit * 15.0 + body_concept_hit * 3.0, 3)


def infer_force(text: str) -> str:
    dark = sum(text.count(x) for x in ("黑暗", "很脏", "拿捏", "驯化", "强行", "惩罚", "报复", "操控", "虐", "邪"))
    hard = sum(text.count(x) for x in ("顶级", "高位", "低位", "必须", "永远", "绝对", "淘汰", "输", "竞争"))
    if dark >= 2: return "暗黑冒犯"
    if hard >= 3: return "强硬"
    return "直接"


def history_pack(source: Path, title: str) -> dict:
    result = subprocess.run(["python3", str(HISTORY_SCRIPT), "--source-path", str(source), "--title", title], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--version", choices=("3.1", "3.2"), default="3.2")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    body = read_source(args.source)
    title = args.title or infer_body_title(body, args.source.stem)
    query_text = title + "\n" + body[:2200]
    query = tokens(query_text)
    query_concepts = concepts(title) or concepts(query_text)
    query_focus = focus_terms(query_text)
    force = infer_force(body[:3000])

    b_items = []
    for meta in load_b_items() + load_external_b_items():
        card = VAULT / meta["card"]
        card_text = card.read_text(encoding="utf-8")
        score = relevance(query, query_concepts, meta["title"], card_text)
        b_items.append({"source_id": meta["id"], "title": meta["title"], "score": score, "force": meta["force"], "knowledge_type": meta["knowledge_type"], "card": meta["card"], "evidence_level": meta.get("evidence_level", "单一高赞来源"), "content_role": meta.get("content_role", "高赞文案知识"), "gary_student_case": meta.get("gary_student_case"), "preview": re.sub(r"\s+", " ", card_text.split("## 来源",1)[0])[:500]})
    b_items.sort(key=lambda x: (-x["score"], str(x["source_id"])))
    selected_b = b_items[:8]

    external_chunks = []
    for item in load_external_chunks():
        score = round(relevance(query, query_concepts, item["title"], item["text"]) + len(query_concepts & concepts(item["text"])) * 15.0 + len(query_focus & focus_terms(item["title"] + "\n" + item["text"])) * 8.0, 3)
        external_chunks.append({
            "chunk_id": item["chunk_id"], "source_id": item["source_id"], "title": item["title"],
            "score": score, "force": item["force"], "knowledge_type": item["knowledge_type"],
            "stages": item.get("stages", []), "page_start": item.get("page_start"),
            "page_end": item.get("page_end"), "source_path": item["source_path"],
            "a_markdown": item["a_markdown"], "exact_excerpt": item["text"][:1600],
            "use_rule": "只润色和嫁接来源知识，不把来源力度自动改温和；采用后记录chunk_id",
        })
    external_chunks.sort(key=lambda x: (-x["score"], x["chunk_id"]))
    selected_chunks = external_chunks[:10]

    composite_cases = []
    for item in load_external_composite_cases():
        if not item.get("runtime_eligible", False):
            continue
        case_text = item.get("source_case_excerpt", "")
        score = round(relevance(query, query_concepts, item["title"], case_text) + len(query_concepts & concepts(case_text)) * 15.0 + len(query_focus & focus_terms(item["title"] + "\n" + case_text)) * 8.0, 3)
        composite_cases.append({
            "case_id": item["id"], "title": item["title"], "score": score,
            "force": item["force"], "stages": item.get("stages", []), "card": item["card"],
            "source_id": item["source_id"], "source_path": item["source_path"],
            "case_source_status": item["case_source_status"], "gary_student_case": False,
            "adaptation_status": item["adaptation_status"], "evidence_status": item["evidence_status"],
            "source_case_excerpt": item["source_case_excerpt"],
            "use_rule": "采用前必须打开卡片，只从同一连续场景提取四字段，再改成Gary第一人称匿名复合案例；不得直接拼接自动线索或补来源没有的结果",
        })
    composite_cases.sort(key=lambda x: (-x["score"], x["case_id"]))
    selected_cases = composite_cases[:3]

    cross_items = []
    for module in load_json(CROSS)["modules"]:
        path = VAULT / module["file"]
        text = path.read_text(encoding="utf-8")
        score = relevance(query, query_concepts, module["title"], text)
        cross_items.append({"module_id": module["module_id"], "title": module["title"], "score": score, "evidence_level": module["evidence_level"], "source_ids": module["source_ids"], "file": module["file"], "preview": re.sub(r"\s+", " ", text.split("## 来源",1)[0])[:700]})
    cross_items.sort(key=lambda x: (-x["score"], x["module_id"]))
    selected_cross = cross_items[:5]

    hook_items = []
    for hook in load_json(HOOKS):
        score = relevance(query, query_concepts, hook["title"], hook["hook"])
        force_bonus = 2 if hook["force"] == force else 0
        hook_items.append({"source_number": hook["source_number"], "title": hook["title"], "score": round(score+force_bonus,3), "force": hook["force"], "hook_category": hook["hook_category"], "micro_framework": hook["micro_framework"], "structure_steps": hook["structure_steps"], "original_hook": hook["hook"], "use_rule": "只复用结构顺序和信息缺口，不逐字复制"})
    hook_items.sort(key=lambda x: (-x["score"], x["source_number"]))
    selected_hooks = hook_items[:6]
    history = history_pack(args.source, title)

    historical_performance = []
    for item in load_historical_performance():
        evidence_text = "\n".join((
            item.get("published_title", ""),
            item.get("published_mother_topic", ""),
            item.get("source_body_mother_topic_anchor", ""),
            item.get("source_opening_preview", ""),
        ))
        score = relevance(query, query_concepts, item.get("published_mother_topic", ""), evidence_text)
        query_title_key = normalized_key(title)
        published_title_key = normalized_key(item.get("published_mother_topic", ""))
        anchor_key = normalized_key(item.get("source_body_mother_topic_anchor", ""))
        if query_title_key and (query_title_key in published_title_key or published_title_key in query_title_key):
            score += 120
        if query_title_key and len(query_title_key) >= 6 and query_title_key in anchor_key:
            score += 80
        if str(args.source.resolve()) == str(Path(item.get("source_path", "")).resolve()):
            score += 240
        score = round(score, 3)
        historical_performance.append({
            "work_id": item["work_id"], "account": item.get("account", ""),
            "published_at": item.get("published_at", ""),
            "published_title": item.get("published_title", ""),
            "source_body_mother_topic_anchor": item.get("source_body_mother_topic_anchor", ""),
            "topic_alignment": item.get("topic_alignment", ""),
            "score": score, "views": item.get("views"), "likes": item.get("likes"),
            "favorites": item.get("favorites"), "follows": item.get("follows"),
            "favorite_rate": item.get("favorite_rate"), "follow_rate": item.get("follow_rate"),
            "average_play_seconds": item.get("average_play_seconds"),
            "evidence_grade": item.get("evidence_grade", ""),
            "use_boundary": item.get("use_boundary", ""),
        })
    historical_performance.sort(key=lambda x: (-x["score"], -(x.get("views") or 0), x["work_id"]))
    selected_historical_performance = [x for x in historical_performance if x["score"] > 0][:5]

    pack = {
        "schema_version": 1,
        "workflow_state": "knowledge_pack_generated_not_manuscript",
        "source": {"path": str(args.source), "title": title, "version": args.version, "characters": len(body), "force_band": force, "opening_excerpt": "\n".join(body.splitlines()[:12])},
        "mother_topic_guard": {"public_topic": title, "must_inherit": ["原稿的公开母题", "原稿核心判断与因果主轴", "原稿中有辨识度且仍适用的机制或金句", "原稿力度档位"], "may_replace": ["具体操作方式", "案例", "场景", "证明路线", "盘点项目；若更改数量须完整兑现"], "forbidden_drift": ["把母题改成泛化关系建议", "为了安全而抽象成温和表达", "为了暗黑而给原本温和来源强加攻击性", "只改词不改内容路线"]},
        "same_topic_b_knowledge": selected_b,
        "external_atomic_knowledge": selected_chunks,
        "gary_anonymized_composite_cases": selected_cases,
        "cross_source_modules": selected_cross,
        "history_collision_pack": history,
        "gary_historical_performance_evidence": selected_historical_performance,
        "opening_matches": selected_hooks,
        "recommended_call": {"primary_cross_module": selected_cross[0] if selected_cross else None, "supporting_b_cards": selected_b[:4], "external_atomic_knowledge": selected_chunks[:5], "gary_anonymized_composite_cases": selected_cases, "historical_performance_evidence": selected_historical_performance[:3], "opening_framework_choices": selected_hooks[:3], "instruction": "先锁定母题与原文因果主轴；只调用能自然接在该母题后的知识点。外部知识只润色和嫁接，不由Codex另造观点。历史接收路线完整排除，历史拒绝记录只排除失败方式。历史发布表现只能用于同账号同母题候选的辅助排序，不能反向证明某个知识点或开头造成结果。案例可用Gary第一人称匿名复合叙述，但不得冒充可核验的Gary学员档案，也不得补来源没有的结果。"},
        "audit_notes": ["匹配分为本地可审计文本相似度，不代表知识已被人工确认适用", "原子知识块保留来源编号与页码，实际采用后必须回写chunk_id", "匿名复合案例是叙事适配，不等于Gary真实学员证据", "跨来源模块保留证据等级，单一来源不升级为已验证规律", "历史发布证据来自扩写前原稿与后台数据连接；发布正文和实际开头未核验时不得做知识点或开头归因", "开头来自高赞样本，但点赞不被归因于单一开头", "本文件不是成稿，也没有调用扩写模型"],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[/:*?\"<>|]", "_", title)[:60]
    json_path = args.output_dir / f"{slug}_知识调用包.json"
    md_path = args.output_dir / f"{slug}_知识调用包.md"
    json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = [f"# {title}｜{args.version}知识调用包", "", f"> 状态：只完成知识匹配，尚未生成换芯稿。原文力度：{force}。", "", "## 母题保护", "", f"- 公开母题：{title}", "- 必须保留原文因果主轴；可换操作、案例、场景和证明路线。", "- 不得为了变化而写成泛化建议，也不得自动安全化。", "", "## 同母题B层知识", ""]
    lines += [f"- {x['score']}分｜[[{x['card'].removesuffix('.md')}|{x['title']}]]｜{x['knowledge_type']}｜{x['force']}" for x in selected_b]
    lines += ["", "## 跨来源模块", ""] + [f"- {x['score']}分｜[[{x['file'].removesuffix('.md')}|{x['module_id']} {x['title']}]]｜{x['evidence_level']}" for x in selected_cross]
    lines += ["", "## 外部原子知识", ""] + [f"- {x['score']}分｜`{x['chunk_id']}`｜{x['force']}｜页{x['page_start']}-{x['page_end']}｜[[{x['a_markdown'].removesuffix('.md')}|{x['title']}]]" for x in selected_chunks]
    lines += ["", "## Gary匿名复合案例候选", ""] + [f"- {x['score']}分｜`{x['case_id']}`｜{x['evidence_status']}｜[[{x['card'].removesuffix('.md')}|{x['title']}]]" for x in selected_cases]
    lines += ["", "## 历史碰撞", "", f"- 同源历史：{history['match_count']}条", f"- 已接收路线：{len(history['same_source_exclusions']['route_signatures'])}条，必须排除", f"- 同源失败方式：{len(history['same_source_rejected_patterns'])}条，只排除失败方式", f"- 近期窗口：3.1共{history['recent_cross_article_window']['3.1_count']}条；3.2共{history['recent_cross_article_window']['3.2_count']}条", ""]
    lines += ["## Gary历史发布证据", ""]
    if selected_historical_performance:
        for x in selected_historical_performance:
            follow = "—" if x.get("follow_rate") is None else f"{x['follow_rate']:.2%}"
            favorite = "—" if x.get("favorite_rate") is None else f"{x['favorite_rate']:.2%}"
            lines.append(f"- {x['score']}分｜{x['work_id']}｜{x['published_at']}｜播放{x.get('views') or 0:,}｜收藏率{favorite}｜转粉率{follow}｜{x['topic_alignment']}｜只作候选权重")
    else:
        lines.append("- 暂无同母题历史发布证据。")
    lines += ["", "> 历史表现不证明某个知识点或开头造成结果；发布正文和实际开头未核验的记录不得做对应归因。", ""]
    lines += ["## 开头结构候选", ""] + [f"- {x['score']}分｜{x['hook_category']}｜{x['micro_framework']}｜来源{x['source_number']:03d}《{x['title']}》｜只复用结构，不复制句子" for x in selected_hooks]
    lines += ["", "## 本次建议", "", f"- 主知识模块：{selected_cross[0]['module_id']} {selected_cross[0]['title']}" if selected_cross else "- 暂无足够匹配模块，需人工补充", "- 辅助知识只选能自然接在原母题后的2至4张卡，不做知识堆砌。", "- 完稿后必须回写实际使用的机制、操作、场景、案例、开头框架和状态。", ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "b_matches": len(selected_b), "external_chunk_matches": len(selected_chunks), "composite_case_matches": len(selected_cases), "cross_matches": len(selected_cross), "history_matches": history["match_count"], "historical_performance_matches": len(selected_historical_performance)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
