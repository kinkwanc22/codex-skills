#!/usr/bin/env python3
"""Small CLI wrapper for Volcengine Ark Seedance video-generation tasks."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = Path(os.environ.get("SEEDANCE_OUTPUT_DIR", Path.cwd() / "outputs" / "seedance2_tool")).resolve()
RUNS_DIR = OUTPUT_ROOT / "runs"
VIDEOS_DIR = OUTPUT_ROOT / "videos"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing {name}. Put it in {ROOT / '.env'} or your shell environment.")
    return value


def media_url(value: str) -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value

    path = Path(value).expanduser()
    if not path.exists():
        return value

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def api_request(method: str, url: str, api_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error: {exc}") from exc

    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Response is not JSON:\n{data}") from exc


def build_content(
    prompt: str,
    images: list[str],
    first_frames: list[str],
    last_frames: list[str],
    videos: list[str],
    audios: list[str],
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in first_frames:
        content.append({"type": "image_url", "image_url": {"url": media_url(url)}, "role": "first_frame"})
    for url in last_frames:
        content.append({"type": "image_url", "image_url": {"url": media_url(url)}, "role": "last_frame"})
    for url in images:
        content.append({"type": "image_url", "image_url": {"url": media_url(url)}, "role": "reference_image"})
    for url in videos:
        content.append({"type": "video_url", "video_url": {"url": media_url(url)}, "role": "reference_video"})
    for url in audios:
        content.append({"type": "audio_url", "audio_url": {"url": media_url(url)}, "role": "reference_audio"})
    return content


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()

    payload: dict[str, Any] = {
        "model": args.model,
        "content": build_content(prompt, args.image, args.first_frame, args.last_frame, args.video, args.audio),
        "generate_audio": args.generate_audio,
        "ratio": args.ratio,
        "duration": args.duration,
        "watermark": args.watermark,
    }
    if args.resolution:
        payload["resolution"] = args.resolution
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.extra:
        try:
            payload.update(json.loads(args.extra))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--extra must be valid JSON: {exc}") from exc
    return payload


def first_existing(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        current: Any = data
        ok = True
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                ok = False
                break
        if ok:
            return current
    return None


def find_task_id(resp: dict[str, Any]) -> str:
    task_id = first_existing(resp, ["id", "task_id", "data.id", "data.task_id"])
    if not task_id:
        raise SystemExit(f"Could not find task id in response:\n{json.dumps(resp, ensure_ascii=False, indent=2)}")
    return str(task_id)


def find_status(resp: dict[str, Any]) -> str:
    status = first_existing(resp, ["status", "data.status"])
    return str(status or "unknown").lower()


def walk_json(value: Any) -> list[Any]:
    items = [value]
    if isinstance(value, dict):
        for child in value.values():
            items.extend(walk_json(child))
    elif isinstance(value, list):
        for child in value:
            items.extend(walk_json(child))
    return items


def find_video_url(resp: dict[str, Any]) -> str | None:
    preferred = first_existing(
        resp,
        [
            "video_url",
            "url",
            "data.video_url",
            "data.url",
            "data.content.video_url",
            "data.result.video_url",
            "data.outputs.0.video_url",
            "data.outputs.0.url",
        ],
    )
    if isinstance(preferred, str) and preferred.startswith(("http://", "https://")):
        return preferred

    for item in walk_json(resp):
        if isinstance(item, str) and item.startswith(("http://", "https://")):
            parsed = urllib.parse.urlparse(item)
            suffix = Path(parsed.path).suffix.lower()
            if suffix in {".mp4", ".mov", ".webm", ".m4v"} or "video" in item.lower():
                return item
    return None


def save_json(name: str, data: dict[str, Any]) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def download_video(url: str, task_id: str) -> Path:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix
    if not suffix:
        content_type = ""
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                content_type = resp.headers.get("content-type", "")
                data = resp.read()
        except urllib.error.URLError as exc:
            raise SystemExit(f"Could not download video: {exc}") from exc
        suffix = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".mp4"
    else:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()

    path = VIDEOS_DIR / f"{task_id}{suffix}"
    path.write_bytes(data)
    return path


def create_task(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return {"id": "dry-run", "status": "dry-run"}

    api_key = require_env("ARK_API_KEY")
    create_url = require_env("SEEDANCE_CREATE_URL")
    print("Creating Seedance task...")
    resp = api_request("POST", create_url, api_key, payload)
    task_id = find_task_id(resp)
    save_json(f"{task_id}.created.json", resp)
    print(f"Task id: {task_id}")
    return resp


def get_task(task_id: str) -> dict[str, Any]:
    api_key = require_env("ARK_API_KEY")
    template = require_env("SEEDANCE_TASK_URL_TEMPLATE")
    url = template.format(task_id=urllib.parse.quote(task_id, safe=""))
    return api_request("GET", url, api_key)


def wait_for_task(task_id: str, interval: int, timeout: int, download: bool = True) -> dict[str, Any]:
    deadline = time.time() + timeout
    last_resp: dict[str, Any] = {}
    while time.time() < deadline:
        last_resp = get_task(task_id)
        status = find_status(last_resp)
        print(f"Status: {status}")
        save_json(f"{task_id}.latest.json", last_resp)

        if status in {"succeeded", "success", "completed", "done"}:
            video_url = find_video_url(last_resp)
            if video_url:
                print(f"Video URL: {video_url}")
                if download:
                    path = download_video(video_url, task_id)
                    print(f"Downloaded: {path}")
            else:
                print("Task succeeded, but no video URL was auto-detected. Check the saved JSON.")
            return last_resp

        if status in {"failed", "error", "cancelled", "canceled"}:
            raise SystemExit(f"Task ended with status {status}. See {RUNS_DIR / (task_id + '.latest.json')}")

        time.sleep(interval)

    raise SystemExit(f"Timed out after {timeout}s. Last response saved in {RUNS_DIR}.")


def main() -> int:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Generate videos with Seedance 2.0 on Volcengine Ark.")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Create a video-generation task.")
    gen.add_argument("prompt", nargs="?", default="")
    gen.add_argument("--prompt-file", help="Read prompt text from a UTF-8 file.")
    gen.add_argument("--model", default=os.environ.get("SEEDANCE_MODEL", DEFAULT_MODEL))
    gen.add_argument("--image", action="append", default=[], help="Reference image URL. Can be repeated.")
    gen.add_argument("--first-frame", action="append", default=[], help="First-frame image URL or local path. Can be repeated.")
    gen.add_argument("--last-frame", action="append", default=[], help="Last-frame image URL or local path. Can be repeated.")
    gen.add_argument("--video", action="append", default=[], help="Reference video URL. Can be repeated.")
    gen.add_argument("--audio", action="append", default=[], help="Reference audio URL. Can be repeated.")
    gen.add_argument("--ratio", default=os.environ.get("SEEDANCE_RATIO", "9:16"))
    gen.add_argument("--duration", type=int, default=int(os.environ.get("SEEDANCE_DURATION", "5")))
    gen.add_argument("--resolution", default=os.environ.get("SEEDANCE_RESOLUTION", ""))
    gen.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=env_bool("SEEDANCE_GENERATE_AUDIO", True))
    gen.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=env_bool("SEEDANCE_WATERMARK"))
    gen.add_argument("--seed", type=int)
    gen.add_argument("--extra", help="Extra JSON fields merged into the request payload.")
    gen.add_argument("--dry-run", action="store_true", help="Print the request payload without calling the API.")
    gen.add_argument("--no-wait", action="store_true")
    gen.add_argument("--no-download", action="store_true")
    gen.add_argument("--poll-interval", type=int, default=int(os.environ.get("SEEDANCE_POLL_INTERVAL", "10")))
    gen.add_argument("--timeout", type=int, default=int(os.environ.get("SEEDANCE_TIMEOUT", "1800")))

    status = sub.add_parser("status", help="Query an existing task.")
    status.add_argument("task_id")
    status.add_argument("--wait", action="store_true")
    status.add_argument("--no-download", action="store_true")
    status.add_argument("--poll-interval", type=int, default=int(os.environ.get("SEEDANCE_POLL_INTERVAL", "10")))
    status.add_argument("--timeout", type=int, default=int(os.environ.get("SEEDANCE_TIMEOUT", "1800")))

    args = parser.parse_args()

    if args.command == "generate":
        resp = create_task(args)
        task_id = find_task_id(resp)
        if not args.no_wait and not args.dry_run:
            wait_for_task(task_id, args.poll_interval, args.timeout, download=not args.no_download)
    elif args.command == "status":
        if args.wait:
            wait_for_task(args.task_id, args.poll_interval, args.timeout, download=not args.no_download)
        else:
            resp = get_task(args.task_id)
            save_json(f"{args.task_id}.latest.json", resp)
            print(json.dumps(resp, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
