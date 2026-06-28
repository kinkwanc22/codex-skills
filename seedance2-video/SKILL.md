---
name: seedance2-video
description: Generate videos through Volcengine Ark Seedance 2.0 API. Use when the user asks to use Seedance, Seedance 2.0, 火山引擎生视频, 火山方舟视频生成, 豆包 Seedance, text-to-video, image/video/audio reference video generation, or wants Codex to generate a video with the configured Volcengine API key.
---

# Seedance 2.0 Video

Use the bundled script `scripts/seedance2.py` to create and monitor asynchronous Seedance 2.0 video-generation tasks.

## Workflow

1. Translate the user's creative request into a concise prompt. Preserve important Chinese copy exactly when provided.
2. Use `--image`, `--video`, and `--audio` for reference media URLs. The script automatically maps them to `role: reference_image`, `role: reference_video`, and `role: reference_audio`.
3. Set `--ratio`, `--duration`, `--generate-audio` or `--no-generate-audio`, and `--watermark` or `--no-watermark` based on the request.
4. Run with `--dry-run` first when validating request shape or when the user is not explicitly asking to spend API credits.
5. For real generation, run the command without `--dry-run`. The script creates a task, polls until completion, saves JSON responses, and downloads the video URL when detected.
6. Report the local video path and the saved response path. Do not print or reveal the API key.

## Commands

Text-to-video:

```powershell
python C:\Users\Administrator\.codex\skills\seedance2-video\scripts\seedance2.py generate "PROMPT" --ratio 9:16 --duration 5 --generate-audio --no-watermark
```

Reference media:

```powershell
python C:\Users\Administrator\.codex\skills\seedance2-video\scripts\seedance2.py generate "PROMPT" --image "IMAGE_URL" --video "VIDEO_URL" --audio "AUDIO_URL" --ratio 16:9 --duration 11 --generate-audio --no-watermark
```

Check an existing task:

```powershell
python C:\Users\Administrator\.codex\skills\seedance2-video\scripts\seedance2.py status TASK_ID --wait
```

## Configuration

The script loads `scripts/.env` from this skill. It is already configured with:

- `SEEDANCE_MODEL=doubao-seedance-2-0-260128`
- Ark task creation endpoint: `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks`
- Ark task query endpoint: `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}`

Keep `ARK_API_KEY` private. If the user provides a new key, update only `scripts/.env`.

## Outputs

By default, when run from a project workspace, files are saved under:

- `outputs/seedance2_tool/runs/`
- `outputs/seedance2_tool/videos/`

Override with `SEEDANCE_OUTPUT_DIR` only when the user needs a different destination.
