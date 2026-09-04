#!/usr/bin/env python3
"""Validate the six-field causal route of a proposed Gary transplant."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FIELDS = (
    "problem_trigger",
    "core_mechanism",
    "action_chain",
    "proof_operation",
    "position_or_interest_shift",
    "desired_result",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def usable(entry: dict) -> bool:
    status = str(entry.get("status", "")).strip().lower()
    review = str(entry.get("review_state", "")).strip().lower()
    return (
        status.startswith("accepted")
        or status.startswith("generated")
        or status.startswith("user_confirmed")
        or "正文待确认" in review
    )


def raw_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = load_json(path)
    raw = data if isinstance(data, list) else data.get("entries", [])
    single_record_keys = set(FIELDS) | {
        "mechanism_novelty",
        "article_level_thesis",
        "point_hierarchy",
        "viewpoints",
        "mechanisms",
        "source_viewpoints",
        "source_mechanisms",
    }
    if isinstance(data, dict) and not raw and any(key in data for key in single_record_keys):
        raw = [data]
    return [entry for entry in raw if isinstance(entry, dict)]


def ledger_entries(path: Path, include_all_statuses: bool = False) -> list[dict]:
    entries = raw_records(path)
    if include_all_statuses:
        return entries
    return [entry for entry in entries if usable(entry)]


def text(value) -> str:
    if isinstance(value, list):
        return " -> ".join(str(item) for item in value if str(item).strip())
    return str(value or "")


def normalize(value) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text(value).lower())


def grams(value, size: int = 2) -> set[str]:
    clean = normalize(value)
    if not clean:
        return set()
    if len(clean) <= size:
        return {clean}
    return {clean[index : index + size] for index in range(len(clean) - size + 1)}


def similarity(left, right) -> float:
    a, b = grams(left), grams(right)
    if not a or not b:
        return 0.0
    if normalize(left) == normalize(right):
        return 1.0
    return len(a & b) / len(a | b)


def mechanism_block(record: dict) -> dict:
    block = record.get("mechanism_novelty")
    return block if isinstance(block, dict) else {}


def list_text(value) -> list[str]:
    if isinstance(value, list):
        return [text(item) for item in value if text(item).strip()]
    value_text = text(value).strip()
    return [value_text] if value_text else []


def viewpoint_items(record: dict) -> list[str]:
    block = mechanism_block(record)
    values = []
    for key in (
        "proposed_viewpoints",
        "viewpoints",
        "source_viewpoints",
        "source_viewpoints_excluded",
        "point_hierarchy",
        "article_level_thesis",
    ):
        values.extend(list_text(record.get(key)))
    values.extend(list_text(block.get("problem_trigger")))
    values.extend(list_text(block.get("position_or_interest_shift")))
    return values


def mechanism_items(record: dict) -> list[str]:
    block = mechanism_block(record)
    values = []
    for key in (
        "proposed_mechanisms",
        "mechanisms",
        "source_mechanisms",
        "source_mechanisms_excluded",
        "route_signature",
    ):
        values.extend(list_text(record.get(key)))
    for key in ("core_mechanism", "action_chain", "proof_operation", "dominant_causal_chain"):
        values.extend(list_text(block.get(key)))
    return values


def strongest_pair(left: list[str], right: list[str]) -> dict:
    best = {"score": 0.0, "proposal": "", "prior": ""}
    for proposed_item in left:
        for prior_item in right:
            score = round(similarity(proposed_item, prior_item), 3)
            if score > best["score"]:
                best = {"score": score, "proposal": proposed_item, "prior": prior_item}
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--ledger", action="append", default=[], type=Path)
    parser.add_argument("--exclusion-record", action="append", default=[], type=Path)
    parser.add_argument("--recent", type=int, default=10)
    parser.add_argument("--all-statuses", action="store_true")
    parser.add_argument("--strict-zero-overlap", action="store_true")
    parser.add_argument("--strict-threshold", type=float, default=0.58)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()

    proposal = load_json(args.proposal)
    proposed = mechanism_block(proposal)
    missing = [field for field in FIELDS if not normalize(proposed.get(field))]
    if not normalize(proposed.get("dominant_causal_chain")):
        missing.append("dominant_causal_chain")

    prior: list[dict] = []
    for ledger in args.ledger:
        entries = ledger_entries(ledger, include_all_statuses=args.all_statuses)
        prior.extend(entries if args.recent == 0 else entries[-args.recent :])
    for exclusion in args.exclusion_record:
        prior.extend(raw_records(exclusion))

    collisions = []
    for entry in prior:
        previous = mechanism_block(entry)
        if not previous and not args.strict_zero_overlap:
            continue
        scores = {
            field: round(similarity(proposed.get(field), previous.get(field)), 3)
            for field in FIELDS
        }
        matched = [field for field, score in scores.items() if score >= 0.58]
        core_action = scores["core_mechanism"] >= 0.55 and scores["action_chain"] >= 0.55
        chain_score = round(
            similarity(
                proposed.get("dominant_causal_chain"),
                previous.get("dominant_causal_chain"),
            ),
            3,
        )
        viewpoint_pair = strongest_pair(viewpoint_items(proposal), viewpoint_items(entry))
        mechanism_pair = strongest_pair(mechanism_items(proposal), mechanism_items(entry))
        strict_overlap = args.strict_zero_overlap and (
            viewpoint_pair["score"] >= args.strict_threshold
            or mechanism_pair["score"] >= args.strict_threshold
        )
        if core_action or len(matched) >= 4 or chain_score >= 0.62 or strict_overlap:
            collisions.append(
                {
                    "prior_work_id": entry.get("work_id", entry.get("id", "")),
                    "prior_title": entry.get("title", ""),
                    "prior_source": entry.get("source_path", ""),
                    "prior_status": entry.get("status", ""),
                    "matched_fields": matched,
                    "field_scores": scores,
                    "dominant_chain_score": chain_score,
                    "core_mechanism_plus_action_chain": core_action,
                    "strict_viewpoint_pair": viewpoint_pair,
                    "strict_mechanism_pair": mechanism_pair,
                    "strict_zero_overlap_collision": strict_overlap,
                }
            )

    report = {
        "proposal": str(args.proposal),
        "comparison_records": len(prior),
        "missing_required_fields": missing,
        "collisions": collisions,
        "mechanism_novelty_pass": not missing and not collisions,
        "deterministic_zero_overlap_pass": not missing and not collisions,
        "all_statuses_included": args.all_statuses,
        "recent_limit": args.recent,
        "strict_zero_overlap": args.strict_zero_overlap,
        "strict_threshold": args.strict_threshold,
        "note": "Deterministic screen only; semantic zero-overlap review remains mandatory.",
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(output + "\n", encoding="utf-8")
    if missing or collisions:
        print("REJECT: mechanism-level route is incomplete or collides", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
