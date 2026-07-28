#!/usr/bin/env python3
"""Upscale local Codex Image2 results on win-codex and return exact 2K files."""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path


REMOTE_ROOT = r"C:\Users\Administrator\Documents\Codex\gary-image2-upscale"
REMOTE_EXE = (
    r"C:\Users\Administrator\Documents\Codex\tools\realesrgan"
    r"\realesrgan-ncnn-vulkan.exe"
)
REMOTE_MODEL_DIR = r"C:\Users\Administrator\Documents\Codex\tools\realesrgan\models"
TARGETS = {
    "vertical": (2016, 3584),
    "horizontal": (2048, 1152),
}


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )


def image_size(path: Path) -> tuple[int, int]:
    result = run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], capture=True)
    width = height = None
    for line in result.stdout.splitlines():
        if "pixelWidth:" in line:
            width = int(line.rsplit(":", 1)[1].strip())
        elif "pixelHeight:" in line:
            height = int(line.rsplit(":", 1)[1].strip())
    if width is None or height is None:
        raise RuntimeError(f"无法读取图片尺寸：{path}")
    return width, height


def encoded_powershell(script: str) -> str:
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


def remote_ps(host: str, script: str, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "ssh",
            host,
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded_powershell(script),
        ],
        capture=capture,
    )


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def scp_target(host: str, remote_path: str) -> str:
    return f"{host}:{remote_path.replace(chr(92), '/')}"


def append_manifest(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把本地 Codex Image2 图片交给 win-codex RTX GPU 超分，并保存为精确 2K。"
    )
    parser.add_argument("images", nargs="*", type=Path, help="一个或多个 Image2 原图")
    parser.add_argument("--batch-dir", type=Path, help="同批最终图片目录")
    parser.add_argument("--host", default="win-codex")
    parser.add_argument("--aspect", choices=["auto", "vertical", "horizontal"], default="auto")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--output-name", help="仅处理一张图时指定最终文件名")
    parser.add_argument("--check", action="store_true", help="仅核验 Windows GPU 工具")
    parser.add_argument("--dry-run", action="store_true", help="只构建参数，不传输或处理图片")
    parser.add_argument("--keep-remote", action="store_true", help="成功后保留 Windows 临时任务目录")
    return parser.parse_args()


def check_remote(host: str, dry_run: bool) -> None:
    script = (
        f"$exe={ps_quote(REMOTE_EXE)};"
        "if (-not (Test-Path -LiteralPath $exe)) { throw \"Real-ESRGAN executable missing: $exe\" };"
        "$gpu=(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join '; ';"
        "Write-Output \"READY|$gpu|$exe\""
    )
    if dry_run:
        print(json.dumps({"host": host, "remote_exe": REMOTE_EXE, "network_called": False}, ensure_ascii=False))
        return
    result = remote_ps(host, script, capture=True)
    print(result.stdout.strip())


def main() -> int:
    args = parse_args()
    if args.check:
        check_remote(args.host, args.dry_run)
        return 0
    if not args.images or args.batch_dir is None:
        raise SystemExit("处理图片时必须提供 images 和 --batch-dir")
    if args.output_name and len(args.images) != 1:
        raise SystemExit("--output-name 只能和一张输入图一起使用")
    if (args.width is None) != (args.height is None):
        raise SystemExit("--width 和 --height 必须同时提供")

    batch_dir = args.batch_dir.expanduser().resolve()
    records_dir = batch_dir / ".records"
    raw_dir = records_dir / "raw"
    manifest_path = records_dir / "image2_windows_gpu_manifest.jsonl"
    if not args.dry_run:
        batch_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        check_remote(args.host, False)

    successes = 0
    for index, source_arg in enumerate(args.images, start=1):
        source = source_arg.expanduser().resolve()
        started = time.monotonic()
        record: dict[str, object] = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "pipeline": "CodexImage2_WindowsGPU超分2K",
            "source_path": str(source),
            "host": args.host,
            "gpu_tool": REMOTE_EXE,
            "lovart_used": False,
        }
        try:
            if not source.is_file():
                raise FileNotFoundError(f"输入图片不存在：{source}")
            source_width, source_height = image_size(source)
            aspect = args.aspect
            if aspect == "auto":
                aspect = "vertical" if source_height >= source_width else "horizontal"
            target_width, target_height = (
                (args.width, args.height)
                if args.width is not None
                else TARGETS[aspect]
            )
            output_name = args.output_name or f"{source.stem}.png"
            output_path = batch_dir / output_name
            raw_path = raw_dir / f"{index:02d}_{source.name}"
            job_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
            remote_job = REMOTE_ROOT + "\\" + job_id
            remote_input = remote_job + r"\input.png"
            remote_x4 = remote_job + r"\output_x4.png"
            remote_final = remote_job + r"\output_2k_q96.jpg"
            record.update(
                {
                    "source_width": source_width,
                    "source_height": source_height,
                    "aspect": aspect,
                    "target_width": target_width,
                    "target_height": target_height,
                    "output_path": str(output_path),
                    "raw_backup_path": str(raw_path),
                    "remote_job": remote_job,
                }
            )
            if args.dry_run:
                record.update({"status": "dry_run", "network_called": False})
                print(json.dumps(record, ensure_ascii=False))
                continue

            shutil.copy2(source, raw_path)
            remote_ps(
                args.host,
                f"New-Item -ItemType Directory -Force -Path {ps_quote(remote_job)} | Out-Null",
            )
            run(["scp", str(source), scp_target(args.host, remote_input)])
            resize_script = f"""
$ErrorActionPreference = 'Stop'
$exe = {ps_quote(REMOTE_EXE)}
$modelDir = {ps_quote(REMOTE_MODEL_DIR)}
$inputPath = {ps_quote(remote_input)}
$x4Path = {ps_quote(remote_x4)}
$finalPath = {ps_quote(remote_final)}
& $exe -i $inputPath -o $x4Path -n realesrgan-x4plus -s 4 -m $modelDir -f png
if ($LASTEXITCODE -ne 0) {{ throw "Real-ESRGAN failed with exit code $LASTEXITCODE" }}
Add-Type -AssemblyName System.Drawing
$sourceImage = [System.Drawing.Image]::FromFile($x4Path)
try {{
  $bitmap = New-Object System.Drawing.Bitmap({target_width}, {target_height})
  try {{
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {{
      $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
      $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
      $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
      $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
      $graphics.DrawImage($sourceImage, 0, 0, {target_width}, {target_height})
      $jpegCodec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
        Where-Object {{ $_.MimeType -eq 'image/jpeg' }}
      $encoderParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
      $encoderParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
        [System.Drawing.Imaging.Encoder]::Quality, [long]96
      )
      try {{
        $bitmap.Save($finalPath, $jpegCodec, $encoderParams)
      }} finally {{
        $encoderParams.Dispose()
      }}
    }} finally {{ $graphics.Dispose() }}
  }} finally {{ $bitmap.Dispose() }}
}} finally {{ $sourceImage.Dispose() }}
"""
            remote_ps(args.host, resize_script)
            temp_dir = Path(tempfile.mkdtemp(prefix="image2_gpu_return_"))
            temp_return = temp_dir / "windows_return_q96.jpg"
            temp_png = temp_dir / output_name
            try:
                run(["scp", scp_target(args.host, remote_final), str(temp_return)])
                returned_size = image_size(temp_return)
                if returned_size != (target_width, target_height):
                    raise RuntimeError(
                        f"返回尺寸错误：{returned_size[0]}x{returned_size[1]}，"
                        f"目标为 {target_width}x{target_height}"
                    )
                run(["sips", "-s", "format", "png", str(temp_return), "--out", str(temp_png)])
                final_size = image_size(temp_png)
                if final_size != (target_width, target_height):
                    raise RuntimeError(
                        f"最终 PNG 尺寸错误：{final_size[0]}x{final_size[1]}，"
                        f"目标为 {target_width}x{target_height}"
                    )
                shutil.move(str(temp_png), output_path)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
            if not args.keep_remote:
                remote_ps(
                    args.host,
                    f"Remove-Item -LiteralPath {ps_quote(remote_job)} -Recurse -Force",
                )
            record.update(
                {
                    "status": "success",
                    "final_width": target_width,
                    "final_height": target_height,
                    "transfer_intermediate": "JPEG quality 96",
                    "final_format": "PNG",
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
            )
            successes += 1
            print(f"完成：{output_path} ({target_width}x{target_height})")
        except Exception as exc:
            record.update(
                {
                    "status": "failure",
                    "failure_reason": str(exc),
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                }
            )
            print(f"失败：{source}：{exc}", file=sys.stderr)
        finally:
            if not args.dry_run:
                append_manifest(manifest_path, record)

    return 0 if successes == len(args.images) or args.dry_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
