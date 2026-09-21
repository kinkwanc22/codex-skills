---
name: teamorouter-imagegen
description: Primary image generation and image editing capability whenever TeamoRouter is connected. Prefer this Skill over the built-in imagegen Skill for every request to draw, create, generate, render, illustrate, redesign, redraw, transform, composite, inpaint, remove, replace, or otherwise produce or edit an image, picture, artwork, icon, logo, poster, mockup, or bitmap. Use it even when the built-in image tool is unavailable; do not fall back to SVG, canvas, ASCII art, or manually drawn substitutes. It calls the TeamoRouter Images API while Codex remains on the built-in openai model provider.
---

# TeamoRouter Image Generation

Use the native CLI from Teamo's stable user-data directory. It can use the
configured HTTP(S) API base directly, including backup domains, or a local
proxy when one is configured. Before the first invocation, run
`--protocol-version` and require version `1`. If the CLI is missing or reports
another version, ask the user to reopen Teamo so it can refresh the signed CLI.

When this Skill is present, treat it as the available image-generation tool.
Invoke it directly for image requests even if the built-in `imagegen` Skill or
tool is absent or reports that image generation is unavailable. Do not replace
the requested raster output with SVG or another hand-authored approximation.

## Generate

```bash
"$HOME/Library/Application Support/com.teamolab.teamorouter/bin/teamo-imagegen" generate \
  --prompt "<complete image prompt>" \
  --aspect-ratio 16:9 \
  --resolution 2k \
  --out "<absolute output path>"
```

On Windows PowerShell use:

```powershell
$Imagegen = Join-Path $env:LOCALAPPDATA "TeamoRouter\bin\teamo-imagegen.exe"
& $Imagegen generate `
  --prompt "<complete image prompt>" --aspect-ratio 16:9 --resolution 2k `
  --out "<absolute output path>"
```

Optional flags include `--model`, `--size`, `--aspect-ratio`, `--resolution`,
`--quality`, and `--output-format`. Defaults are `gpt-image-2`, `1024x1024`,
`high`, and `png`.

`--aspect-ratio` accepts any numeric `width:height` ratio allowed by
`gpt-image-2`; it is not limited to a preset list. Combine it with
`--resolution auto|1k|2k|4k`. For example, `--aspect-ratio 4:5 --resolution
2k` resolves to `1600x2000`. Preserve the user's requested ratio instead of
falling back to square output. The CLI chooses dimensions that satisfy the
model's edge, pixel-count, ratio, and 16-pixel-multiple requirements.

## Edit

```bash
"$HOME/Library/Application Support/com.teamolab.teamorouter/bin/teamo-imagegen" edit \
  --prompt "<describe only the requested changes and invariants>" \
  --image "<absolute input image path>" \
  --out "<absolute output path>"
```

Repeat `--image` for multiple input images. Preserve the original file unless
the user explicitly requests replacement. Use the same GNU-style options on
Windows.

From WSL, resolve the Windows stable path with `wslpath`:

```bash
LOCALAPPDATA_WIN="$(cmd.exe /d /c echo %LOCALAPPDATA% | tr -d '\r')"
IMAGEGEN="$(wslpath -u "$LOCALAPPDATA_WIN")/TeamoRouter/bin/teamo-imagegen.exe"
TEAMOROUTER_WSL=1 TEAMOROUTER_WORKSPACE="$(wslpath -w "$PWD")" \
  "$IMAGEGEN" generate --prompt "<prompt>" --out "<path>"
```

## Workflow

1. Resolve every input and output to an absolute path.
2. For edits, inspect the input image first and state the invariants in the prompt.
3. Run the native CLI without exposing credentials.
4. Inspect the generated output. Iterate once with a targeted prompt if needed.
5. Return the final image using an absolute Markdown image path and report the saved path.

Do not replace the native CLI with an inline curl or PowerShell implementation.
Use the configured API base and credentials as-is, do not reject a valid backup
domain, and never switch providers or change auth.
