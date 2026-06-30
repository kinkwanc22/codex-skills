# Hook Trainer Workflow

## End-to-End Command

Run this from the skill folder to analyze the default Hook pool:

```bash
python3 scripts/run_pipeline.py --niche 男性情感 --limit 20
```

Default source folder:

```text
/Users/kin/工作用（同步）/开头hook
```

Default output folder:

```text
/Users/kin/工作用（同步）/开头hook/hook_trainer_output
```

For a custom source folder, pass absolute paths:

```bash
python3 scripts/run_pipeline.py /path/to/source-folder -o /path/to/output --niche 男性情感 --limit 20
```

This writes:

- `parsed.json`
- `analysis.json`
- `hooks.json`
- `search_results.json`
- `formula_library/formula_library.json`
- `formula_library/opening_library.json`
- `formula_library/high_frequency_words.json`
- `formula_library/v2_report.md`

## Separate Commands

```bash
python3 scripts/parse_folder.py /path/to/source-folder -o output/parsed.json
python3 scripts/analyze_hooks.py output/parsed.json -o output/analysis.json
python3 scripts/build_hooks_db.py output/analysis.json -o output/hooks.json --replace
python3 scripts/search_hooks.py output/hooks.json --niche 男性情感 --emotion 焦虑 --limit 20 -o output/search_results.json
python3 scripts/build_formula_library.py output/analysis.json -o output/formula_library --limit 200
python3 scripts/match_openings.py output/formula_library/opening_library.json --text "聊天不要聊事实，要聊情绪" -o output/matched_openings.json
python3 scripts/generate_openings.py --file /path/to/article.docx -o output/generated_openings.json --markdown output/generated_openings.md --limit 20
```

## V1 Behavior

- Parser extracts text locally.
- Analyzer uses deterministic rule-based classification.
- Database writes local JSON.
- Search filters and ranks locally.
- Formula Builder extracts fine frames, sentence patterns, formulas, high-frequency words, and a reusable opening library.
- Matcher compares a future topic or draft against `opening_library.json`.
- Generator creates new openings by extracting article variables, injecting high-frequency words, applying formulas, and scoring candidates.

No external AI API is called in V1/V2 local mode.

## Known Limits

- `.docx` support reads the main document body only.
- V1 classification is rule-based and should be treated as a first-pass label.
- For better labels, run V2 with model-assisted analysis after the local database is stable.
