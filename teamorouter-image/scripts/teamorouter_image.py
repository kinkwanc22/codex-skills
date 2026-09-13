#!/usr/bin/env python3
"""Safe, dependency-free TeamoRouter GPT Image 2.5 Sunburst client."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import mimetypes
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


BASE_URL = "https://api.teamorouter.com/v1/images"
MODEL = "gpt-image-2.5-sunburst"
KEY_ENV = "TEAMOROUTER_API_KEY"


class ClientError(RuntimeError):
    pass


def credential_path() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "teamorouter" / "credentials.json"


def configure_key() -> int:
    key = getpass.getpass("New TeamoRouter API key (hidden): ").strip()
    if not key.startswith("sk-teamo-") or len(key) < 20:
        raise ClientError("The key does not look like a TeamoRouter API key.")
    path = credential_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="credentials-", dir=str(path.parent), text=True)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"api_key": key}, handle)
            handle.write("\n")
        os.replace(temp_name, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    print(json.dumps({"configured": True, "path": str(path)}, ensure_ascii=False))
    return 0


def load_key() -> str:
    env_key = os.environ.get(KEY_ENV, "").strip()
    if env_key:
        return env_key
    path = credential_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("api_key", "").strip()
    except FileNotFoundError as exc:
        raise ClientError(f"No API key configured. Run: {sys.executable} {Path(__file__)} configure") from exc
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise ClientError(f"Cannot read credentials at {path}: {exc}") from exc
    if not value:
        raise ClientError(f"No API key found in {path}.")
    return value


def validate_size(value: str) -> tuple[int, int] | None:
    if value == "auto":
        return None
    match = re.fullmatch(r"(\d+)[xX](\d+)", value)
    if not match:
        raise ClientError("Size must be 'auto' or WIDTHxHEIGHT, for example 1024x1024.")
    width, height = (int(match.group(1)), int(match.group(2)))
    issues: list[str] = []
    if width % 16 or height % 16:
        issues.append("width and height must both be multiples of 16")
    if max(width, height) > 3840:
        issues.append("the longest side must not exceed 3840")
    if min(width, height) == 0 or max(width, height) / min(width, height) > 3:
        issues.append("the aspect ratio must not exceed 3:1")
    pixels = width * height
    if not 655_360 <= pixels <= 8_294_400:
        issues.append("total pixels must be between 655360 and 8294400")
    if issues:
        raise ClientError("Invalid size: " + "; ".join(issues) + ".")
    return width, height


def common_payload(args: argparse.Namespace) -> dict[str, Any]:
    validate_size(args.size)
    if args.output_compression is not None and args.output_format == "png":
        raise ClientError("output-compression applies to JPEG/WebP, not PNG.")
    if args.background == "transparent" and args.output_format == "jpeg":
        raise ClientError("Transparent background requires PNG or WebP.")
    payload: dict[str, Any] = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": args.n,
        "output_format": args.output_format,
        "background": args.background,
    }
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    if args.user:
        payload["user"] = args.user
    return payload


def encode_multipart(fields: dict[str, Any], files: dict[str, Path]) -> tuple[bytes, str]:
    boundary = "----teamorouter-" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    for name, path in files.items():
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode())
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        body.extend(path.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def request_json(endpoint: str, body: bytes, content_type: str, timeout: int) -> dict[str, Any]:
    key = load_key()
    request = urllib.request.Request(
        f"{BASE_URL}/{endpoint}",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": content_type, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise ClientError(f"API request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ClientError(f"Network request failed: {exc.reason}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ClientError("API returned a non-JSON response.") from exc


def save_results(response: dict[str, Any], output_dir: Path, extension: str) -> list[str]:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise ClientError("API response contains no image data.")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    paths: list[str] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ClientError(f"Image result {index} has an unexpected format.")
        target = output_dir / f"teamorouter-{stamp}-{index}.{extension}"
        if "b64_json" in item:
            try:
                target.write_bytes(base64.b64decode(item["b64_json"], validate=True))
            except (ValueError, TypeError) as exc:
                raise ClientError(f"Image result {index} contains invalid Base64 data.") from exc
        elif "url" in item:
            try:
                with urllib.request.urlopen(item["url"], timeout=120) as source:
                    target.write_bytes(source.read())
            except urllib.error.URLError as exc:
                raise ClientError(f"Could not download image result {index}: {exc.reason}") from exc
        else:
            raise ClientError(f"Image result {index} has neither b64_json nor url.")
        if not target.is_file() or target.stat().st_size == 0:
            raise ClientError(f"Saved image {target} is empty.")
        paths.append(str(target.resolve()))
    return paths


def sanitized_plan(command: str, payload: dict[str, Any], files: dict[str, Path] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "dry_run": True,
        "paid_action": True,
        "endpoint": f"{BASE_URL}/{command}",
        "payload": payload,
    }
    if files:
        result["files"] = {name: str(path.resolve()) for name, path in files.items()}
    return result


def run_image(args: argparse.Namespace) -> int:
    payload = common_payload(args)
    endpoint = "generations"
    upload_files: dict[str, Path] | None = None
    if args.command == "generate":
        payload["moderation"] = args.moderation
        body = json.dumps(payload).encode("utf-8")
        content_type = "application/json"
    else:
        endpoint = "edits"
        image_path = Path(args.image).expanduser()
        if not image_path.is_file():
            raise ClientError(f"Source image not found: {image_path}")
        upload_files = {"image": image_path}
        if args.mask:
            mask_path = Path(args.mask).expanduser()
            if not mask_path.is_file():
                raise ClientError(f"Mask image not found: {mask_path}")
            upload_files["mask"] = mask_path
        payload["input_fidelity"] = args.input_fidelity
        body, content_type = encode_multipart(payload, upload_files)

    if args.dry_run:
        print(json.dumps(sanitized_plan(endpoint, payload, upload_files), ensure_ascii=False, indent=2))
        return 0
    if not args.confirm_spend:
        raise ClientError("Paid request blocked. Review with --dry-run, then add --confirm-spend after approval.")

    response = request_json(endpoint, body, content_type, args.timeout)
    files = save_results(response, Path(args.output_dir).expanduser(), args.output_format)
    print(json.dumps({"ok": True, "model": MODEL, "files": files}, ensure_ascii=False, indent=2))
    return 0


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", choices=("low", "medium", "high", "auto"), default="auto")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output-format", choices=("png", "jpeg", "webp"), default="png")
    parser.add_argument("--output-compression", type=int, choices=range(0, 101), metavar="0..100")
    parser.add_argument("--background", choices=("transparent", "opaque", "auto"), default="auto")
    parser.add_argument("--user")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--timeout", type=int, default=300)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm-spend", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("configure", help="Store an API key using hidden input and private file permissions.")
    check = sub.add_parser("validate-size", help="Validate a size without network access.")
    check.add_argument("size")
    generate = sub.add_parser("generate", help="Generate images.")
    add_common(generate)
    generate.add_argument("--moderation", choices=("low", "auto"), default="auto")
    edit = sub.add_parser("edit", help="Edit an image.")
    add_common(edit)
    edit.add_argument("--image", required=True)
    edit.add_argument("--mask")
    edit.add_argument("--input-fidelity", choices=("high", "low"), default="high")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "configure":
        return configure_key()
    if args.command == "validate-size":
        dimensions = validate_size(args.size)
        print(json.dumps({"valid": True, "size": args.size, "dimensions": dimensions}))
        return 0
    if args.n < 1:
        raise ClientError("n must be at least 1.")
    if args.timeout < 1:
        raise ClientError("timeout must be at least 1 second.")
    return run_image(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClientError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
