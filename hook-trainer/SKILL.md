---
name: hook-trainer
description: Build and query a local viral opening hook database from folders of scripts. Use when the user asks to train, parse, analyze, classify, store, search, recommend, or learn from 爆款开头 / Hook / short-video openings in `.txt`, `.md`, `.srt`, or `.docx` files, especially for Douyin, TikTok, Chinese relationship copy, or ContentFactory workflows.
---

# Hook Trainer

## Overview

Use this skill to turn a folder of proven short-video scripts into a searchable local hook database.

The pipeline is local and deterministic:

```text
source folder -> parsed.json -> analysis.json -> hooks.json -> search_results.json
              -> formula_library/ -> formulas, opening library, high-frequency words
              -> original_frameworks/ -> original hooks, micro frameworks, reusable skeletons
```

No external AI API is called in the local pipeline.

## Quick Start

Default source folder:

```text
/Users/kin/工作用（同步）/开头hook
```

Default output folder:

```text
/Users/kin/工作用（同步）/开头hook/hook_trainer_output
```

When the user says "分析开头hook文件夹", "分析默认hook素材池", or "用 hook-trainer 分析我放进去的文稿", use the default source folder.

For most requests with the default folder, run:

```bash
python3 scripts/run_pipeline.py --niche 男性情感 --limit 20
```

For a custom source folder, run:

```bash
python3 scripts/run_pipeline.py /path/to/source-folder -o /path/to/output --niche 男性情感 --limit 20
```

Use the user's source folder as input when provided. If no source folder is provided, use the default source folder above. If the user does not specify an output folder, write to `hook_trainer_output` inside the source folder.

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
- `formula_library/formula_library.json`: reusable opening formulas and frameworks
- `formula_library/opening_library.json`: 100-200 reusable opening examples for matching future copy
- `formula_library/high_frequency_words.json`: high-frequency words and phrases
- `formula_library/v2_report.md`: readable V2 summary report
- `original_frameworks/original_frameworks.json`: original-hook skeleton library with source text, micro framework, structure steps, reusable skeleton, suitable topics
- `original_frameworks/original_frameworks.md`: readable original-hook skeleton report; use this first when generated openings feel off
- `generated_openings.json`: V3 generated openings for a new article or topic
- `generated_openings.md`: readable V3 generated opening report

Read `references/data_contracts.md` when you need exact schemas.

## Separate Steps

Use separate scripts when the user asks for only one stage or when debugging:

```bash
python3 scripts/parse_folder.py /path/to/source-folder -o output/parsed.json
python3 scripts/analyze_hooks.py output/parsed.json -o output/analysis.json
python3 scripts/build_hooks_db.py output/analysis.json -o output/hooks.json --replace
python3 scripts/search_hooks.py output/hooks.json --niche 男性情感 --emotion 焦虑 --limit 20 -o output/search_results.json
python3 scripts/build_formula_library.py output/analysis.json -o output/formula_library --limit 200
python3 scripts/build_original_frameworks.py output/formula_library/opening_library.json -o output/original_frameworks --limit 200
python3 scripts/match_openings.py output/formula_library/opening_library.json --text "聊天不要聊事实，要聊情绪" -o output/matched_openings.json
python3 scripts/generate_openings.py --file /path/to/article.docx -o output/generated_openings.json --markdown output/generated_openings.md --limit 20
```

Read `references/workflow.md` for command variations.

## Operating Rules

- Preserve the staged pipeline. Do not merge Parser, Analyzer, Database, and Search into one hidden blob.
- Keep user source files unchanged.
- Prefer source-local output folders for user-provided directories.
- Use `/Users/kin/工作用（同步）/开头hook` as the default Hook Trainer source pool.
- Extract Hook text at about 50 Chinese characters when source text is long enough; skip title/like-count metadata before extracting.
- Treat V1 labels as first-pass rule-based labels, not final human truth.
- For V2, always preserve three separate layers: fine frame, sentence formula, and reusable opening example.
- For V2.5 original frameworks, preserve the original hook text first. Treat labels like 黑暗真相式 as coarse tags; the useful layer is `micro_framework`, `structure_steps`, and `reusable_skeleton`.
- When using a selected framework library, do not merely "reference the theme." Strictly paste the source opening's sentence movement: keep its opening move, line order, contrast shape, and rhythm, then replace only the topic variables. Label each generated candidate with the source framework number. Example: if source #29 is `女人其实都是脏的 / 不是身体 / 是欲望 / ...背后藏着...`, the adapted opening should keep `女人真正隐秘的地方 / 不是【表层】 / 是【深层机制】 / 是她【外在形象】背后藏着的...`; do not rewrite it as a generic summary question.
- When the user approves a manually spliced opening, learn it as a composite opening frame, not as one sentence. Preserve its chain: `absolute claim -> visible body/behavior evidence -> named relationship mechanism -> subconscious test -> experienced-man interpretation -> forward answer`. Example: `女人的身体是很诚实的 -> 只要她有一点兴趣身体马上有反应 -> 恋爱里有个现实的动态价值测试 -> 她通过身体释放信号观察你能不能接住 -> 经验丰富的男生看到信号就知道 -> 她已经把推进答案告诉你了`. Use this frame for signal/body-language topics and similar drafts where the hook should feel like several strong openings stitched into one smooth 50-90 character lead, not a summary.
- To avoid homogeneous openings, treat repeated words such as `诚实`, `兴趣`, `测试`, `接住`, and `女人不是...而是...` as interchangeable slots, not fixed phrases. For every batch, rotate slot families: entry judgment (`藏不住`, `会先露馅`, `比嘴更快`, `先给答案`, `最先出卖她`), weak trigger (`窗口`, `好感`, `情绪波动`, `投入迹象`, `接纳感`, `试探欲`), visible signal (`眼神停留`, `语气变软`, `回复节奏变乱`, `身体距离`, `废测变多`, `主动制造话题`), mechanism name (`潜意识筛选`, `关系窗口测试`, `推进资格测试`, `高位框架测试`, `损失厌恶开关`, `投入成本机制`), and expert interpretation (`老手一看就懂`, `答案已经出现`, `窗口已经打开`, `她已经把下一步告诉你`). Prefer "live signal reading" over abstract viewpoints: write as if the viewer is watching a woman reveal a signal right now, then explain the mechanism behind it.
- Use `opening_library.json` to match new drafts or topics against the learned opening library.
- When the user says the generated opening is not right, feels stiff, or feels like 生搬硬套, inspect `original_frameworks/original_frameworks.md` before changing the generator.
- Preserve the title's core hook theme before applying safety or polish. If the source title or draft contains words such as `隐秘`, `禁忌`, `不愿意承认`, `潜意识`, `深处`, or `难以启齿`, the opening must keep the hidden/forbidden contrast: public claim vs private pull, mouth-denial vs subconscious reaction, decent surface vs darker mechanism. Do not flatten it into generic advice like "别低位讨好" or "保持边界".
- For hidden/forbidden psychology topics, use sharp but speakable high-frequency words naturally: `黑暗`, `真相`, `隐秘`, `潜意识`, `反人性`, `上头`, `上瘾`, `离不开`, `沉没成本`, `损失厌恶`, `高位`, `框架`, `稀缺`, `臣服`, `掌控`, `博弈`, `人性`. Avoid over-sanitizing into bland terms such as only `边界感`, `价值感`, `社交认同`, or `关系投入`.
- When rewriting risky or provocative source material, reduce explicit vulgarity but keep the contradiction and pressure. Preferred direction: 黑暗但可播, 狠但不脏, 压迫但不露骨.
- For V3 generation, do not copy old openings. Extract article variables, inject high-frequency words naturally, apply learned formulas, and score each new opening.
- Generated openings should be about 50-70 Chinese characters unless the user asks otherwise.
- When the user provides `.docx`, parse it directly; do not ask them to manually convert unless parsing fails.
- When reporting results, show the output folder, record count, top hooks, and any known limitations.

## When Improving The Skill

If the user asks to improve accuracy, add V2 behavior as a new layer instead of breaking V1:

1. Keep local Parser unchanged unless input formats change.
2. Add model-assisted analysis after `parsed.json`.
3. Keep human correction records separate from generated `analysis.json`.
4. Re-run tests after changes.
