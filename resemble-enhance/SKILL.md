---
name: resemble-enhance
description: Use Resemble Enhance from the local E:\resemble-enhance-main project to denoise, enhance, or batch-process speech audio files. Trigger when the user asks for audio cleanup, speech denoising, voice enhancement, improving muffled/noisy recordings, running Resemble Enhance, or launching its Gradio demo.
---

# Resemble Enhance

Use this skill for AI speech denoising and enhancement with the local project at:

`E:\resemble-enhance-main`

Resemble Enhance improves speech recordings by separating voice from noise and optionally restoring perceived audio quality/bandwidth. It can run either as a Gradio web demo or as a command-line batch processor.

## Default Workflow

1. Confirm the input audio path or folder from the user request.
2. Check whether `E:\resemble-enhance-main` exists.
3. Prefer a project-local virtual environment if one exists; otherwise use the active Python environment.
4. For one-off interactive use, launch the Gradio app:

```powershell
Set-Location -LiteralPath 'E:\resemble-enhance-main'
python app.py
```

5. For batch processing, use the installed console command when available:

```powershell
resemble-enhance in_dir out_dir
```

Use `--denoise_only` when the user asks only for noise removal:

```powershell
resemble-enhance in_dir out_dir --denoise_only
```

## Environment Checks

Before running processing, inspect:

```powershell
Set-Location -LiteralPath 'E:\resemble-enhance-main'
python --version
python -c "import torch, torchaudio, gradio; print('ok')"
```

If dependencies are missing, install from the project:

```powershell
Set-Location -LiteralPath 'E:\resemble-enhance-main'
python -m pip install -r requirements.txt
python -m pip install -e .
```

Ask before installing large dependencies or downloading model weights. Torch, torchaudio, and model checkpoints may be large.

## Input And Output Conventions

- Keep user originals untouched.
- For batch work, create an output folder with a clear name such as `enhanced`, `denoised`, or a timestamped directory.
- If the user does not specify an output location, place deliverables under the active workspace `outputs` directory when available.
- For Windows paths, use PowerShell `-LiteralPath` for paths containing spaces or non-ASCII characters.

## Gradio App Notes

`app.py` exposes:

- input audio upload
- CFM ODE solver: `Midpoint`, `RK4`, `Euler`
- number of function evaluations
- prior temperature
- optional denoise-before-enhancement checkbox
- outputs for denoised audio and enhanced audio

Use the local web app when the user wants to compare results manually or adjust settings.

## Quality Guidance

- For noisy speech, try enhancement with denoising enabled.
- For simple background noise removal, use denoise-only mode first.
- If processing is slow on CPU, check whether CUDA is available; the app automatically uses `cuda` when `torch.cuda.is_available()` is true.
- If the output sounds over-processed, reduce enhancement intensity through the Gradio controls or try denoise-only.

## Safety

Do not delete source audio. Do not overwrite an existing output directory unless the user explicitly asks.
