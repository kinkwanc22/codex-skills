---
name: duanchongxie
description: 1000-2000字重写 for short Douyin copy rewriting. Use for 短重写, 1000-2000字重写, 原文开头保留无痕衔接, 保留结构框架但表达重组, 更狠更有压迫感的男性情感口播稿, and isolated Gemini prompt-file rewriting that must not modify the original douyin-copy-production-workflow-custom Gemini session.
---

# 1000-2000字重写

Use this skill for the user's 1000-2000 character Douyin copy rewrite workflow when Gemini rewriting must not alter the existing `douyin-copy-production-workflow-custom` conversation or `gemini_session.json`.

## Core Outcome

Produce final `.docx` files that contain:

1. `爆款心理学标题包装`
2. `开头版本一：高阶认知课式开头`
3. `开头版本二：身份点名式硬核学习开头`
4. `开头版本三：保留原文开头（来自源文档）`
5. `正文`

Do not add risk suggestions, yellow-highlighted annotations, or `[[RISKNOTE:...]]` markers.

## Default Paths

- Mac source folders are often under `/Users/kin/工作用（同步）/素材文稿/`.
- Mac final Word output folder: create a content-specific `codex短重写输出_<YYYYMMDD>` folder beside the source folder unless the user gives another output path.
- Mac Gemini expansion command directory: `/Users/kin/Documents/Codex/2026-07-02/gemini`
- Mac Gemini expansion command: `./scripts/run_gemini_chat.sh`
- Mac local command shape: `./scripts/run_gemini_chat.sh --prompt-file <path> --isolated --output-file <path>`
- Windows fallback source folders are often under `D:\工作用（同步）\素材文稿\` or `E:\工作用\素材文稿\助理采集文案\`.
- Windows fallback final Word output folder: `D:\工作用（同步）\素材文稿\codex工作流长文稿` or `E:\工作用\素材文稿\codex工作流长文稿`, depending on where the current synced root lives.
- Windows fallback Gemini expansion command directory: `C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api`
- Windows fallback Gemini expansion command: `.\outputs\run_gemini_chat.cmd`
- Mandatory isolation rule: always call Gemini with `--prompt-file <path> --isolated`; on Mac also pass `--output-file <path>` so the generated draft is saved for validation. Never run the bare interactive command for expansion, because it can read or write the original long-running Gemini conversation.
- Never send `/new`; it can overwrite the saved Gemini session.
- Opening source of truth: invoke `baokuan-kaitou-sheding` / `$爆款开头设定`; do not hand-write openings from memory.

## Reference Files

Load only the reference files needed for the current step:

- `references/gemini-expansion.md`: read before sending source text to Gemini, creating prompt files, retrying failures, or checking generated drafts.
- `references/source-learning-and-style.md`: read when processing a batch, learning source viral logic, classifying source styles, or preserving source openings.
- `references/openings-and-titles.md`: read after expansion passes checks and before Word export to generate openings, score them, and build title packages.
- `references/export-and-hard-rules.md`: read before optional scoring, Word export, final delivery, and post-run workflow updates.

## Workflow

### 1. Queue Every Provided Source By Default

When the user provides a batch of `.docx` scripts, do not run pre-expansion scoring, ranking, filtering, or top-N selection unless explicitly asked. Preserve stable filename order unless the user gives another order.

Read `references/source-learning-and-style.md` and create a concise batch learning note in the current workspace outputs folder.

### 2. Expand With Isolated Local Gemini

Read `references/gemini-expansion.md`.

For every expansion and retry, build a UTF-8 prompt file containing:

1. The full current Gemini instruction block from `references/gemini-expansion.md`.
2. The original source text wrapped as `【原文开始】...【原文结束】`.

Then run only the Mac local command by default:

```bash
cd /Users/kin/Documents/Codex/2026-07-02/gemini
./scripts/run_gemini_chat.sh --prompt-file /path/to/prompt.txt --isolated --output-file /path/to/expanded.txt
```

Use the Windows command only as an explicit fallback:

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api
.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated
```

Do not run either bare interactive command:

```bash
./scripts/run_gemini_chat.sh
```

```powershell
.\outputs\run_gemini_chat.cmd
```

Do not send `/new`. Do not use the old web expansion channel.

### 3. Validate Each Expanded Draft

Read `references/gemini-expansion.md` for the exact checks and retry language.

Verify length, topic relevance, refusal/API failure text, stale-topic contamination, and required ending. Default target length is 1000-2000 Chinese characters, with 1200-1600 preferred. The minimum acceptable length is 1000 Chinese characters and the default maximum is 2000 unless the user gives a newer threshold.

### 4. Add Openings And Titles

Read `references/openings-and-titles.md`.

For every accepted article, execute these subskills in order:

1. Invoke `baokuan-kaitou-sheding` / `$爆款开头设定` and use its approved learned opening forms as the source of truth for `开头版本一：高阶认知课式开头` and `开头版本二：身份点名式硬核学习开头`.
2. Extract `开头版本三：保留原文开头（来自源文档）` from the source document without rewriting it.
3. Score versions one and two with the mandatory 20-point opening gate; rewrite with `baokuan-kaitou-sheding` until both pass.
4. Invoke `viral-psych-title-wrapper` / `$爆款心理学标题包装器` for the title package. Generate 10 three-line candidates, strongest 3, and recommendation reason.
5. Maintain a batch title ledger to avoid duplicate mechanism chains or generic interchangeable titles.

### 5. Export Clean Word Documents

Read `references/export-and-hard-rules.md`.

Export final `.docx` files on Mac into a content-specific `codex短重写输出_<YYYYMMDD>` folder beside the source folder, or the user-specified output folder, with content/topic-based filenames. Do not leave generic names such as risk-note or timestamp-only filenames.

Before final delivery, verify each `.docx` contains the required headings and has no risk suggestions, yellow highlights, or `[[RISKNOTE:...]]` markers.

### 6. Final Reply

Keep the final answer short. Tell the user the Word file path, character count, and confirm that no risk suggestions, yellow-highlighted annotations, or `[[RISKNOTE:...]]` markers were added.

If optional viral potential review was requested, report it. Otherwise do not add a scoring/pass-fail statement.
