#!/usr/bin/env python3
"""Build and validate a 3.1+3.2 cross-version novelty exclusion pack."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FIELD_SPECS = {
    "route_signature": {
        "prior": ("route_signature", "route"),
        "threshold": 0.62,
    },
    "scene_anchors": {
        "prior": ("scene_anchors", "avoid_next_time"),
        "threshold": 0.68,
    },
    "replacement_operation_units": {
        "prior": ("replacement_operation_units", "new_operation_units"),
        "threshold": 0.66,
    },
    "case_signatures": {
        "prior": ("case_signatures", "case_avoid_next_time"),
        "threshold": 0.60,
    },
    "conversion_signature": {
        "prior": ("conversion_signature", "conversion_structure_signature"),
        "threshold": 0.60,
    },
}


def load_entries(path: Path, version: str) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict) and isinstance(data.get("entries"), list):
        raw = data["entries"]
    else:
        raise ValueError(f"{path}: ledger must be a JSON list or an object with entries")
    result = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", "")).strip().lower()
        review = str(entry.get("review_state", "")).strip().lower()
        usable = (
            status.startswith("accepted")
            or status.startswith("generated")
            or status.startswith("user_confirmed")
            or "正文待确认" in review
        )
        if usable:
            item = dict(entry)
            item["_version"] = version
            result.append(item)
    return result


def values(entry: dict, keys: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for key in keys:
        value = entry.get(key)
        if isinstance(value, list):
            result.extend(str(x) for x in value if str(x).strip())
        elif value is not None and str(value).strip():
            result.append(str(value))
    return result


def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text.lower())


def grams(text: str, size: int = 2) -> set[str]:
    clean = normalize(text)
    if len(clean) <= size:
        return {clean} if clean else set()
    return {clean[i : i + size] for i in range(len(clean) - size + 1)}


def similarity(left: str, right: str) -> float:
    a, b = grams(left), grams(right)
    if not a or not b:
        return 0.0
    if normalize(left) == normalize(right):
        return 1.0
    return len(a & b) / len(a | b)


def compact_record(entry: dict) -> dict:
    return {
        "version": entry.get("_version", ""),
        "title": entry.get("title", ""),
        "source_path": entry.get("source_path", ""),
        "route_signature": entry.get("route_signature", ""),
        "scene_anchors": values(entry, ("scene_anchors", "avoid_next_time")),
        "replacement_operation_units": values(
            entry, ("replacement_operation_units", "new_operation_units")
        ),
        "case_signatures": values(entry, ("case_signatures", "case_avoid_next_time")),
        "conversion_signature": entry.get("conversion_signature", "")
        or entry.get("conversion_structure_signature", ""),
    }


def proposed_values(proposal: dict, field: str) -> list[str]:
    value = proposal.get(field)
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if value is None or not str(value).strip():
        return []
    return [str(value)]


def validate_proposal(proposal: dict, prior: list[dict]) -> list[dict]:
    collisions: list[dict] = []
    for field, spec in FIELD_SPECS.items():
        candidates = proposed_values(proposal, field)
        for candidate in candidates:
            best = None
            for entry in prior:
                for previous in values(entry, spec["prior"]):
                    score = similarity(candidate, previous)
                    if best is None or score > best[0]:
                        best = (score, entry, previous)
            if best and best[0] >= spec["threshold"]:
                score, entry, previous = best
                collisions.append(
                    {
                        "field": field,
                        "score": round(score, 3),
                        "threshold": spec["threshold"],
                        "candidate": candidate,
                        "prior_version": entry.get("_version", ""),
                        "prior_title": entry.get("title", ""),
                        "prior_value": previous,
                    }
                )
    return collisions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger31", required=True, type=Path)
    parser.add_argument("--ledger32", required=True, type=Path)
    parser.add_argument("--recent31", type=int, default=30)
    parser.add_argument("--recent32", type=int, default=20)
    parser.add_argument("--proposed-file", type=Path)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()

    accepted31 = load_entries(args.ledger31, "3.1")
    accepted32 = load_entries(args.ledger32, "3.2")
    comparison = accepted31[-args.recent31 :] + accepted32[-args.recent32 :]

    report = {
        "accepted_total": {"3.1": len(accepted31), "3.2": len(accepted32)},
        "comparison_window": {
            "3.1": len(accepted31[-args.recent31 :]),
            "3.2": len(accepted32[-args.recent32 :]),
        },
        "comparison_rule": (
            "Preserve the public mother topic and topic-defining mechanisms; "
            "avoid collisions in supporting route, concrete operation, scene, case, "
            "and conversion chains."
        ),
        "recent_entries": [compact_record(entry) for entry in comparison],
    }

    exit_code = 0
    if args.proposed_file:
        proposal = json.loads(args.proposed_file.read_text(encoding="utf-8"))
        if not isinstance(proposal, dict):
            raise ValueError("proposed file must contain a JSON object")
        required = (
            "route_signature",
            "replacement_operation_units",
            "case_signatures",
            "conversion_signature",
        )
        missing = [name for name in required if not proposed_values(proposal, name)]
        collisions = validate_proposal(proposal, comparison)
        report["proposal_title"] = proposal.get("title", "")
        report["missing_required_fields"] = missing
        report["collisions"] = collisions
        report["cross_version_collision_pass"] = not missing and not collisions
        if missing or collisions:
            exit_code = 2

    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(output + "\n", encoding="utf-8")
    if exit_code:
        print("REJECT: proposed 3.2 route collides with prior 3.1/3.2 records", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
