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


def ledger_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = load_json(path)
    raw = data if isinstance(data, list) else data.get("entries", [])
    return [entry for entry in raw if isinstance(entry, dict) and usable(entry)]


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--ledger", action="append", default=[], type=Path)
    parser.add_argument("--recent", type=int, default=10)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()

    proposal = load_json(args.proposal)
    proposed = mechanism_block(proposal)
    missing = [field for field in FIELDS if not normalize(proposed.get(field))]
    if not normalize(proposed.get("dominant_causal_chain")):
        missing.append("dominant_causal_chain")

    prior: list[dict] = []
    for ledger in args.ledger:
        prior.extend(ledger_entries(ledger)[-args.recent :])

    collisions = []
    for entry in prior:
        previous = mechanism_block(entry)
        if not previous:
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
        if core_action or len(matched) >= 4 or chain_score >= 0.62:
            collisions.append(
                {
                    "prior_title": entry.get("title", ""),
                    "prior_source": entry.get("source_path", ""),
                    "matched_fields": matched,
                    "field_scores": scores,
                    "dominant_chain_score": chain_score,
                    "core_mechanism_plus_action_chain": core_action,
                }
            )

    report = {
        "proposal": str(args.proposal),
        "comparison_records": len(prior),
        "missing_required_fields": missing,
        "collisions": collisions,
        "mechanism_novelty_pass": not missing and not collisions,
        "note": "Deterministic screen; Codex semantic review remains mandatory.",
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
