#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

STATUS = [
    "prompt_ready", "video_ready", "transition_ready", "tts_ready",
    "assets_ready", "draft_written", "verified",
]


def probe(path: Path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height", "-of", "json", str(path)
    ]
    try:
        return json.loads(subprocess.check_output(cmd, text=True))
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def duration(info):
    try:
        return float(info["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Validate a baokuan-fuke-qianchuan handoff")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors, warnings = [], []

    status = data.get("status")
    if status not in STATUS:
        errors.append(f"invalid status: {status!r}")
        target = -1
    else:
        target = STATUS.index(status)

    def need(value, label, stage=0):
        if target >= stage and not value:
            errors.append(f"missing {label} for {STATUS[stage]}")

    need(data.get("prompt"), "prompt")
    need(data.get("dialogue"), "dialogue")
    lead = str(data.get("female_lead_id") or "")
    if target >= 0 and (len(lead) != 3 or not lead.isdigit()):
        errors.append("female_lead_id must be a three-digit string")
    lead_dir = Path(data.get("female_lead_folder") or "/nonexistent")
    if target >= 0 and not lead_dir.is_dir():
        errors.append("female_lead_folder does not exist")
    elif target >= 0 and not lead_dir.name.startswith(lead + "_"):
        errors.append("female_lead_folder does not match female_lead_id")

    video = Path(data.get("generated_video") or "/nonexistent")
    if target >= 1:
        if not video.is_file():
            errors.append("generated_video does not exist")
        else:
            info = probe(video)
            kinds = {x.get("codec_type") for x in (info or {}).get("streams", [])}
            if not {"video", "audio"}.issubset(kinds):
                errors.append("generated_video must contain video and native dialogue audio")

    need(data.get("transition_text"), "transition_text", 2)
    transition_audio = Path(data.get("transition_audio") or "/nonexistent")
    if target >= 3:
        if not transition_audio.is_file():
            errors.append("transition_audio does not exist")
        else:
            seconds = duration(probe(transition_audio))
            if seconds is None:
                errors.append("cannot read transition_audio duration")
            elif seconds > 25.0:
                errors.append(f"transition_audio exceeds 25 seconds: {seconds:.3f}")

    cta = Path(data.get("fixed_cta_audio") or "/nonexistent")
    if target >= 1 and not cta.is_file():
        errors.append("fixed_cta_audio does not exist")
    cta_srt = Path(data.get("fixed_cta_srt") or "/nonexistent")
    if target >= 5 and not cta_srt.is_file():
        errors.append("fixed_cta_srt does not exist")

    selected = data.get("selected_supplemental_videos") or []
    if target >= 4 and not selected:
        errors.append("no selected_supplemental_videos")
    selected_seconds = 0.0
    for entry in selected:
        if not isinstance(entry, dict):
            errors.append("each supplemental video entry must record path/source_start/duration/section")
            continue
        item = Path(entry.get("path") or "/nonexistent")
        if not item.is_file():
            errors.append(f"missing supplemental video: {item}")
        try:
            item.resolve().relative_to(lead_dir.resolve())
        except ValueError:
            errors.append(f"supplemental video is outside female_lead_folder: {item}")
        if entry.get("section") not in {"transition", "cta"}:
            errors.append(f"invalid supplemental section: {entry.get('section')!r}")
        try:
            source_start = float(entry.get("source_start"))
            used = float(entry.get("duration"))
            if source_start < 0 or used <= 0:
                raise ValueError
            selected_seconds += used
        except (TypeError, ValueError):
            errors.append(f"invalid source_start/duration for supplemental video: {item}")
    if target >= 4 and transition_audio.is_file() and cta.is_file():
        required = (duration(probe(transition_audio)) or 0) + (duration(probe(cta)) or 0)
        if selected_seconds + 0.05 < required:
            errors.append(
                f"supplemental coverage is short: {selected_seconds:.3f}s < {required:.3f}s"
            )

    draft = Path(data.get("jianying_draft") or "/nonexistent")
    if target >= 5:
        for name in ("draft_content.json", "draft_info.json"):
            if not (draft / name).is_file():
                errors.append(f"missing Jianying file: {name}")

    if target >= 6 and not (data.get("stage_evidence") or {}).get("structure_qa_passed"):
        errors.append("verified status requires stage_evidence.structure_qa_passed=true")

    result = {
        "manifest": str(args.manifest), "status": status, "valid": not errors,
        "errors": errors, "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
