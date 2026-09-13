---
name: teamorouter-image
description: Generate or edit images through the TeamoRouter GPT Image 2 and GPT Image 2.5 Sunburst APIs. Use when a user or agent asks to call TeamoRouter, gpt-image-2, Sunburst, gpt-image-2.5-sunburst, this local image API wrapper, 本地 image2, or 本地 image2.5.
---

# TeamoRouter Image

Use the `scripts/teamorouter_image.py` file resolved relative to this `SKILL.md` as the deterministic API client; do not assume the caller's working directory is the skill folder. It supports GPT Image 2 and GPT Image 2.5 Sunburst generation/editing, local size validation, dry runs, and secure local credential configuration without third-party Python packages.

## User routing aliases

- Treat `本地 image2` as an explicit request to use this TeamoRouter API client with `--model gpt-image-2`.
- Treat `本地 image2.5` as an explicit request to use this TeamoRouter API client with `--model gpt-image-2.5-sunburst`.
- These phrases mean the locally configured API workflow, not an on-device image model or the previous local-machine generation route. Do not silently fall back to another provider or on-device model if the API fails.

## Safety and authorization

- Never ask the user to paste an API key into chat, a prompt, a command argument, or a project file.
- If a key was exposed in chat, tell the user to revoke it and create a new one. Do not save or use the exposed key.
- Generation and editing are paid external actions. Prepare a dry run first unless the user already approved the exact call. Run a paid request only after clear authorization and include `--confirm-spend`.
- Do not retry a failed paid request automatically. Report the HTTP status and sanitized error, then ask before retrying if another charge is possible.
- A successful API response is not delivery. Confirm the output file exists and is non-empty before reporting completion.

## Credential setup

Ask the user to run this themselves in a terminal so the key is entered through hidden input:

```bash
python3 scripts/teamorouter_image.py configure
```

The client first checks `TEAMOROUTER_API_KEY`, then its private per-user credentials file. `configure` creates that file with user-only permissions. Never inspect or print the stored secret.

Verify the stored credential without generating an image:

```bash
python3 scripts/teamorouter_image.py check-auth
```

## Workflow

1. Validate the request locally and show the sanitized payload:

```bash
python3 scripts/teamorouter_image.py generate --prompt "..." --size 1024x1024 --quality high --dry-run
```

Select GPT Image 2 explicitly with `--model gpt-image-2`:

```bash
python3 scripts/teamorouter_image.py generate --model gpt-image-2 --prompt "..." --size 1024x1024 --quality high --dry-run
```

2. After explicit approval, submit with `--confirm-spend` and an explicit output directory:

```bash
python3 scripts/teamorouter_image.py generate --prompt "..." --size 1024x1024 --quality high --output-dir /absolute/output/path --confirm-spend
```

3. For edits, supply one or more existing images and optionally a same-size mask. Repeat `--image` for multiple references:

```bash
python3 scripts/teamorouter_image.py edit --image /absolute/input.png --prompt "..." --size 1024x1024 --input-fidelity high --output-dir /absolute/output/path --dry-run

python3 scripts/teamorouter_image.py edit --image /absolute/identity.png --image /absolute/style.png --prompt "Use the person from image 1 and the composition from image 2" --size 1024x1536 --output-dir /absolute/output/path --dry-run
```

4. Parse the JSON written to stdout. `files` contains the saved image paths. Verify each file before reporting success.

Use `validate-size` for a no-network check. Read [references/api.md](references/api.md) only when parameter or billing details are needed.

## Defaults

- Default model is `gpt-image-2.5-sunburst`; use `--model gpt-image-2` for the Image 2 route.
- `size=1024x1024`, `quality=auto`, `n=1`, `output_format=png`, `background=auto`, and generation `moderation=auto`.
- Explicit size is preferred because billing follows actual returned resolution. Use `auto` only when the user accepts variable output size and tier.
- Transparent generation requires PNG or WebP. The edit endpoint may still return no alpha channel even when transparent is requested.
- Streaming is intentionally omitted because the documented intermediate chunks currently contain no image.
