# Hook Trainer Workflow

## End-to-End Command

Run this from the skill folder or pass absolute paths:

```bash
python3 scripts/run_pipeline.py /path/to/source-folder -o /path/to/output --niche 男性情感 --limit 20
```

This writes:

- `parsed.json`
- `analysis.json`
- `hooks.json`
- `search_results.json`

## Separate Commands

```bash
python3 scripts/parse_folder.py /path/to/source-folder -o output/parsed.json
python3 scripts/analyze_hooks.py output/parsed.json -o output/analysis.json
python3 scripts/build_hooks_db.py output/analysis.json -o output/hooks.json --replace
python3 scripts/search_hooks.py output/hooks.json --niche 男性情感 --emotion 焦虑 --limit 20 -o output/search_results.json
```

## V1 Behavior

- Parser extracts text locally.
- Analyzer uses deterministic rule-based classification.
- Database writes local JSON.
- Search filters and ranks locally.

No external AI API is called in V1.

## Known Limits

- `.docx` support reads the main document body only.
- V1 classification is rule-based and should be treated as a first-pass label.
- For better labels, run V2 with model-assisted analysis after the local database is stable.
