#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_SERVICE_DIR = r"E:\非丨链接提取文案（抖+bilibili）\非丨链接提取文案（抖+bilibili）"
DEFAULT_BASE_URL = "http://127.0.0.1:8080"


def read_entries(input_file, positional):
    entries = []
    if input_file:
        text = Path(input_file).read_text(encoding="utf-8-sig")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls = re.findall(r"https?://[^\s，,。；;]+", line)
            if urls:
                entries.extend(urls)
            else:
                entries.append(line)
    for item in positional:
        item = item.strip()
        if item:
            entries.append(item)

    seen = set()
    deduped = []
    for entry in entries:
        key = entry.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped


def request_json(method, url, payload=None, timeout=10):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def service_ready(base_url):
    try:
        result = request_json("GET", base_url.rstrip("/") + "/api/supported_platforms", timeout=3)
        return bool(result.get("success"))
    except Exception:
        return False


def start_service(service_dir, base_url, wait_seconds=60):
    service_path = Path(service_dir)
    python_exe = service_path / "feige" / "python.exe"
    launcher = service_path / "launcher.py"
    if not python_exe.exists() or not launcher.exists():
        raise FileNotFoundError(f"Extractor runtime not found in {service_path}")

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    proc = subprocess.Popen(
        [str(python_exe), str(launcher)],
        cwd=str(service_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if service_ready(base_url):
            return proc.pid
        time.sleep(1)
    raise TimeoutError(f"Started PID {proc.pid}, but {base_url} did not become ready")


def safe_name(value, fallback):
    value = (value or "").strip() or fallback
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    if len(value) > 80:
        value = value[:80].rstrip(" .")
    return value or fallback


def write_text(path, content):
    Path(path).write_text(content or "", encoding="utf-8")


def extract_one(base_url, entry, timeout):
    return request_json(
        "POST",
        base_url.rstrip("/") + "/api/extract_douyin_text",
        payload={"url": entry},
        timeout=timeout,
    )


def main():
    parser = argparse.ArgumentParser(description="Batch extract Douyin/Bilibili transcripts with the local 8080 extractor.")
    parser.add_argument("urls", nargs="*", help="URLs or share texts to process.")
    parser.add_argument("--input-file", help="UTF-8 text file, one URL/share text per line.")
    parser.add_argument("--output-dir", default=None, help="Directory for saved txt/srt/json/summary outputs.")
    parser.add_argument("--service-dir", default=os.environ.get("DOUYIN_BILIBILI_EXTRACTOR_DIR", DEFAULT_SERVICE_DIR))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=300, help="Seconds per extraction request.")
    parser.add_argument("--no-start", action="store_true", help="Do not auto-start the local service.")
    args = parser.parse_args()

    entries = read_entries(args.input_file, args.urls)
    if not entries:
        print("No URLs or share texts found.", file=sys.stderr)
        return 2

    started_pid = None
    if not service_ready(args.base_url):
        if args.no_start:
            print(f"Service is not ready: {args.base_url}", file=sys.stderr)
            return 3
        print(f"Starting local extractor from: {args.service_dir}")
        started_pid = start_service(args.service_dir, args.base_url)
        print(f"Service started, PID {started_pid}")

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or Path.cwd() / f"batch_extract_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    failures = []

    for index, entry in enumerate(entries, start=1):
        print(f"[{index}/{len(entries)}] Extracting: {entry}")
        digest = hashlib.sha1(entry.encode("utf-8", errors="ignore")).hexdigest()[:8]
        prefix_base = f"{index:03d}-{digest}"
        try:
            result = extract_one(args.base_url, entry, args.timeout)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result = {"success": False, "error": str(exc)}

        info = result.get("video_info") or {}
        title = safe_name(info.get("title") or result.get("title"), prefix_base)
        prefix = safe_name(f"{index:03d}-{title}", prefix_base)

        json_path = output_dir / f"{prefix}.json"
        txt_path = output_dir / f"{prefix}.txt"
        srt_path = output_dir / f"{prefix}.srt"

        write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))

        success = bool(result.get("success"))
        transcript_text = result.get("transcript_text") or ""
        transcript_srt = result.get("transcript_srt") or ""

        if success:
            write_text(txt_path, transcript_text)
            if transcript_srt:
                write_text(srt_path, transcript_srt)
            print(f"  OK: {len(transcript_text)} text chars, {len(transcript_srt)} srt chars")
        else:
            txt_path = ""
            srt_path = ""
            err = result.get("error") or "Unknown error"
            failures.append((entry, err))
            print(f"  FAILED: {err}")

        summary_rows.append({
            "index": index,
            "success": success,
            "source": entry,
            "platform": result.get("platform") or "",
            "title": info.get("title") or "",
            "uploader": info.get("uploader") or "",
            "duration": info.get("duration") or "",
            "text_chars": len(transcript_text),
            "srt_chars": len(transcript_srt),
            "error": "" if success else (result.get("error") or "Unknown error"),
            "txt_path": str(txt_path),
            "srt_path": str(srt_path),
            "json_path": str(json_path),
        })

    summary_path = output_dir / "summary.csv"
    with summary_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    if failures:
        failure_path = output_dir / "failures.txt"
        lines = [f"{url}\n  {err}" for url, err in failures]
        write_text(failure_path, "\n\n".join(lines))

    ok_count = sum(1 for row in summary_rows if row["success"])
    fail_count = len(summary_rows) - ok_count
    print("")
    print(f"Done. Success: {ok_count}, failed: {fail_count}")
    print(f"Output directory: {output_dir}")
    print(f"Summary: {summary_path}")
    if started_pid:
        print(f"Started service PID: {started_pid}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
