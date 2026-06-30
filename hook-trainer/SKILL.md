---
name: hook-trainer
description: Build and query a local viral opening hook database from folders of scripts. Use when the user asks to train, parse, analyze, classify, store, search, recommend, or learn from 爆款开头 / Hook / short-video openings in `.txt`, `.md`, `.srt`, or `.docx` files, especially for Douyin, TikTok, Chinese relationship copy, or ContentFactory workflows.
---

# Hook Trainer

## Overview

Use this skill to turn a folder of proven short-video scripts into a searchable local hook database.

The V1 pipeline is local and deterministic:

```text
source folder -> parsed.json -> analysis.json -> hooks.json -> search_results.json
```

No external AI API is called in V1.

## Quick Start

For most requests, run the end-to-end pipeline:

```bash
python3 scripts/run_pipeline.py /path/to/source-folder -o /path/to/output --niche 男性情感 --limit 20
```

Use the user's source folder as input. If the user does not specify an output folder, create a new `hook_trainer_output` folder inside the source folder when permissions allow; otherwise use the current workspace output folder.

## Supported Inputs

- `.txt`
- `.md`
- `.srt`
- `.docx`

Each file is treated as one source script.

## Outputs

The pipeline writes:

- `parsed.json`: normalized text and source metadata
- `analysis.json`: hook, type, emotion, rhythm, information gap, template
- `hooks.json`: durable local hook database
- `search_results.json`: ranked Top N results for the query

Read `references/data_contracts.md` when you need exact schemas.

## Separate Steps

Use separate scripts when the user asks for only one stage or when debugging:

```bash
python3 scripts/parse_folder.py /path/to/source-folder -o output/parsed.json
python3 scripts/analyze_hooks.py output/parsed.json -o output/analysis.json
python3 scripts/build_hooks_db.py output/analysis.json -o output/hooks.json --replace
python3 scripts/search_hooks.py output/hooks.json --niche 男性情感 --emotion 焦虑 --limit 20 -o output/search_results.json
```

Read `references/workflow.md` for command variations.

## Operating Rules

- Preserve the staged pipeline. Do not merge Parser, Analyzer, Database, and Search into one hidden blob.
- Keep user source files unchanged.
- Prefer source-local output folders for user-provided directories.
- Treat V1 labels as first-pass rule-based labels, not final human truth.
- When the user provides `.docx`, parse it directly; do not ask them to manually convert unless parsing fails.
- When reporting results, show the output folder, record count, top hooks, and any known limitations.

## When Improving The Skill

If the user asks to improve accuracy, add V2 behavior as a new layer instead of breaking V1:

1. Keep local Parser unchanged unless input formats change.
2. Add model-assisted analysis after `parsed.json`.
3. Keep human correction records separate from generated `analysis.json`.
4. Re-run tests after changes.
