---
name: douyin-copy-production-workflow-custom
description: Complete Douyin copy production workflow. Use for 抖音文案工作流, 处理这批文案, Gemini本地命令扩写, 三版开头, 长文稿Word导出, and end-to-end male relationship copy production.
---

# Douyin Copy Production Workflow

Use this skill for the user's complete production loop from assistant-collected scripts to publishable long-form Word drafts.

## Core Outcome

Produce final `.docx` files that contain:

1. `爆款心理学标题包装`
2. `开头版本一：高阶认知课式开头`
3. `开头版本二：身份点名式硬核学习开头`
4. `开头版本三：保留原文开头（来自源文档）`
5. `正文`

Do not add risk suggestions, yellow-highlighted annotations, or `[[RISKNOTE:...]]` markers.

## Default Paths

- Assistant source folders are often under `E:\工作用\素材文稿\助理采集文案\`.
- Final Word output folder: `E:\工作用\素材文稿\codex工作流长文稿`
- Current Gemini expansion command directory: `C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api`
- Current Gemini expansion command: `.\outputs\run_gemini_chat.cmd`
- Other-copy Gemini isolation rule: for non-male-relationship copy or unrelated tests, use `.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated` so the saved male relationship expansion conversation in `gemini_session.json` is preserved; do not use `/new` for this.
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

### 2. Expand With Local Gemini

Read `references/gemini-expansion.md`.

Use the local Gemini command for expansion:

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api
.\outputs\run_gemini_chat.cmd
```

For automated expansion, prefer:

```powershell
.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated
```

Build each UTF-8 prompt file with the selected full Gemini instruction block from `references/gemini-expansion.md`, followed immediately by the original source text wrapped as `【原文开始】...【原文结束】`. If the user asks for 单案例、一案到底、一个案例贯穿全文, use the `2.6 Single Case` direction.

Do not use the old web expansion channel. Do not send `/new` unless the user explicitly asks.

### 3. Validate Each Expanded Draft

Read `references/gemini-expansion.md` for the exact checks and retry language.

Verify length, topic relevance, refusal/API failure text, stale-topic contamination, and required ending. Default target length is 6000-8000 Chinese characters. The minimum acceptable length is 6000 Chinese characters unless the user gives a newer threshold.

### 4. Add Openings And Titles

Read `references/openings-and-titles.md`.

For every accepted article, execute these subskills in order:

1. Invoke `baokuan-kaitou-sheding` / `$爆款开头设定` and use its approved learned opening forms as the source of truth for `开头版本一：高阶认知课式开头` and `开头版本二：身份点名式硬核学习开头`. Do not hand-write generic openings from memory.
2. Extract `开头版本三：保留原文开头（来自源文档）` from the source document without rewriting it.
3. Score versions one and two with the mandatory 20-point opening gate; rewrite with `baokuan-kaitou-sheding` until both pass.
4. Invoke `viral-psych-title-wrapper` / `$爆款心理学标题包装器` for the title package. Generate 10 three-line candidates, strongest 3, and recommendation reason.
5. Maintain a batch title ledger to avoid duplicate mechanism chains or generic interchangeable titles.

### 5. Export Clean Word Documents

Read `references/export-and-hard-rules.md`.

Export final `.docx` files to `E:\工作用\素材文稿\codex工作流长文稿` with content/topic-based filenames. Do not leave generic names such as risk-note or timestamp-only filenames.

Before final delivery, verify each `.docx` contains the required headings and has no risk suggestions, yellow highlights, or `[[RISKNOTE:...]]` markers.

### 6. Final Reply

Keep the final answer short. Tell the user the Word file path, character count, and confirm that no risk suggestions, yellow-highlighted annotations, or `[[RISKNOTE:...]]` markers were added.

If optional viral potential review was requested, report it. Otherwise do not add a scoring/pass-fail statement.
