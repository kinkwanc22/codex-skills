---
name: batch-video-copy-extractor
description: Wenan tiqu / 文案提取. Batch extract Chinese video transcripts/copy from many Douyin or Bilibili links using the user's local Douyin+Bilibili Flask extractor on port 8080. Use when the user sends multiple Douyin, Bilibili, B-site, or video share URLs and asks to 文案提取, 批量提取文案, 批量文案提取, 批量提取字幕, 提取 SRT, extract video copy, or process many links into text files.
---

# 文案提取

## Purpose

Batch process many Douyin or Bilibili video links through the local extractor app at `http://127.0.0.1:8080`, then save per-video transcript text, SRT subtitles, raw JSON, and a summary CSV.

This skill does not use ListenHub/content-parser. It uses the local app installed at:

`E:\非丨链接提取文案（抖+bilibili）\非丨链接提取文案（抖+bilibili）`

Override this path with `DOUYIN_BILIBILI_EXTRACTOR_DIR` if the app is moved.

## Workflow

1. Put the user's links into a UTF-8 `.txt` file, one link or share text per line.
2. Run `scripts/batch_extract.py` with `--input-file`.
3. If `http://127.0.0.1:8080/api/supported_platforms` is unavailable, allow the script to start the local Flask app automatically.
4. Wait for each extraction. The app may take several minutes per video because it downloads video and sends audio to BcutASR.
5. Report success count, failure count, and output directory.

## Command

```powershell
python "<skill-dir>\scripts\batch_extract.py" --input-file "<links.txt>" --output-dir "<output-dir>"
```

You may also pass URLs directly:

```powershell
python "<skill-dir>\scripts\batch_extract.py" "https://v.douyin.com/..." "https://www.bilibili.com/video/..."
```

## Outputs

For each item, the script writes:

- `NNN-title.txt`: plain transcript text
- `NNN-title.srt`: SRT subtitles, when returned
- `NNN-title.json`: raw API response

It also writes:

- `summary.csv`: status, source URL, platform, title, uploader, duration, transcript lengths, and saved paths
- `failures.txt`: failed items and error messages, only when failures occur

## Local Extractor Details

The local app exposes:

- `GET /api/supported_platforms`
- `POST /api/extract_douyin_text` with JSON body `{"url": "..."}`

Supported platforms:

- Douyin: `douyin.com`, `iesdouyin.com`, `v.douyin.com`, normal share text containing a Douyin URL
- Bilibili: `bilibili.com`, `b23.tv`

The app uses its bundled Python runtime at `feige\python.exe`, `launcher.py`, `simple_app.pyd`, `ffmpeg.exe`, `yt-dlp 2023.11.16`, and BcutASR remote transcription endpoints. Failures can come from expired links, private/member-only videos, platform anti-bot blocking, network failures, or BcutASR availability.

## Reporting

After running, keep the final response concise:

- Say where outputs were saved.
- List how many succeeded and failed.
- For failures, include the link and short error.
- If the service was started, mention `http://127.0.0.1:8080/douyin` is available for manual checks.
