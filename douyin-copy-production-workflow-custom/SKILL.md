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

- Assistant source folders are often under `/Users/kin/工作用（同步）/素材文稿/助理采集文案/` on Mac or `D:\工作用（同步）\素材文稿\助理采集文案\` on Windows; old `E:\工作用\素材文稿\助理采集文案\` is legacy-only.
- Final Word output folder for current Mac workflow: `/Users/kin/工作用（同步）/7.1后双端同步文件夹`
- Final Word output folder for current Windows workflow: `D:\工作用（同步）\7.1后双端同步文件夹`
- Legacy Windows final Word output folder: `E:\工作用\素材文稿\codex工作流长文稿`
- Expansion tests/comparison runs must also be exported as `.docx` files into the current dual-device synced workflow folder; do not deliver `.txt` unless the user explicitly asks for txt.
- Gemini execution choice: default to the Mac local runner unless the user explicitly asks to use Windows or the task depends on Windows-only files, old Windows Codex projects, or Windows-only tooling.
- Current Mac Gemini expansion command directory: active Codex workspace when it contains `scripts/run_gemini_chat.sh`; current tested workspace is `/Users/kin/Documents/Codex/2026-07-02/gemini`.
- Current Mac Gemini expansion command: `./scripts/run_gemini_chat.sh --prompt-file <prompt.txt> --output-file <expanded.txt>`. For 2.5, use the approved July 5 batch method and add `--isolated` for every source. Use `--session 2.5` only when the user explicitly asks to continue that saved conversation. Keep 2.8 and 2.9 in their dedicated sessions unless their rules call for isolation.
- Current formal 2.9 active prompt for the Gary project: `/Users/kin/Documents/Codex/2026-07-10/qu/work/ACTIVE_2.9_PROMPT_强结论正式版.txt`. The earlier stable rollback baseline remains `/Users/kin/Documents/Codex/2026-07-10/qu/work/ACTIVE_2.9_PROMPT_昨晚12个男性成长版.txt`; do not delete or silently overwrite it.
- Windows fallback Gemini expansion command directory: `C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api`.
- Windows fallback Gemini expansion command: `.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated`.
- Other-copy Gemini isolation rule: for non-male-relationship copy or unrelated tests, use `--prompt-file <prompt> --isolated` on the selected host so saved male relationship expansion conversation state is preserved; do not use `/new` for this.
- Opening source of truth: invoke `baokuan-kaitou-sheding` / `$爆款开头设定`; do not hand-write openings from memory.

## Reference Files

Load only the reference files needed for the current step:

- `references/gemini-expansion.md`: read before sending source text to Gemini, creating prompt files, retrying failures, or checking generated drafts.
- `references/2.9-strong-conclusion-layer.md`: approved formal 2.9 enhancement source of truth for strong conclusions, human-nature games, interest judgments, dark insight retention, and the three-topic validation record. Its prompt text is also embedded inside the formal 2.9 block in `references/gemini-expansion.md` so routine prompt builders cannot omit it.
- `references/source-learning-and-style.md`: read when processing a batch, learning source viral logic, classifying source styles, or preserving source openings.
- `references/openings-and-titles.md`: read after expansion passes checks and before Word export to generate openings, score them, and build title packages.
- `references/export-and-hard-rules.md`: read before optional scoring, Word export, final delivery, and post-run workflow updates.

## Workflow

### 1. Queue Every Provided Source By Default

When the user provides a batch of `.docx` scripts, do not run pre-expansion scoring, ranking, filtering, or top-N selection unless explicitly asked. Preserve stable filename order unless the user gives another order.

Read `references/source-learning-and-style.md` and create a concise batch learning note in the current workspace outputs folder.

### 2. Expand With Local Gemini

Read `references/gemini-expansion.md`.

Use the Mac local Gemini runner by default:

```bash
cd /Users/kin/Documents/Codex/2026-07-02/gemini
./scripts/run_gemini_chat.sh --prompt-file work/prompt.txt --isolated --output-file work/expanded.txt
```

Use Windows only when the user explicitly asks for Windows or the task depends on Windows-only files, old Windows projects, or Windows-only tooling:

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api
.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated
```

Build each UTF-8 prompt file with the selected full Gemini instruction block from `references/gemini-expansion.md`, followed by any required direction-specific injection and the original source text wrapped as `【原文开始】...【原文结束】`. For 2.5, the official baseline is the complete July 5-style block + short `旧2.5风格参照` injection + source, with each source run using `--isolated`. Before expansion, normalize a selected 2.5 topic angle by removing proactive soft guardrails such as `不教操控、不是控制、不是冷漠`; preserve the viral mother topic and rebuild the angle with direct mechanism, interest, power-change, consequence, or harsh-judgment framing. Only retain a distinction when the user explicitly requests that distinction, and do not apply this 2.5-only normalization to 2.9. Do not inject the representative sample excerpts in routine runs. If the user asks for 单案例、一案到底、一个案例贯穿全文, use the `2.6 Single Case` direction.

If the user asks for `2.7`, `融合版`, `2.5和2.6融合`, or wants the same effect as the approved 316 body-signal fusion draft, do not ask Gemini to write a separate 2.7 draft from the source. First generate and validate the Gemini 2.5 and 2.6 drafts, then have Codex locally fuse those two accepted drafts using the `2.7 Codex Fusion` rules in `references/gemini-expansion.md`.

If the user asks for `2.9`, `2.5×2.8融合版`, `2.5和2.8融合`, or `融合提示词`, use the saved `2.9 Fusion Draft` direction in `references/gemini-expansion.md`. This is a direct Gemini prompt-file direction: 2.5 supplies Gary voice, sharp judgment, male perspective, business logic, and continuous deduction; 2.8 supplies hidden structure, concrete evidence, reduced adjective pressure, topic isolation, and stable output control. The formally approved strong-conclusion layer is part of 2.9 by default: preserve source-supported human-nature games, interest judgments, dark insights, relationship power changes, and sharp conclusions instead of automatically neutralizing them. Do not substitute the unrelated 2.7 single-case fusion flow.

Do not use the old web expansion channel. Do not send `/new` unless the user explicitly asks. The official 2.5 workflow is isolated per source and does not write to a saved conversation. Keep 2.8 and 2.9 in their separate dedicated sessions, and do not run these directions through the default mixed `gemini_session.json`.

### 3. Validate Each Expanded Draft

Read `references/gemini-expansion.md` for the exact checks and retry language.

Verify length, topic relevance, refusal/API failure text, stale-topic contamination, and required ending. For the current 2.5 baseline, the hard minimum is 4000 Chinese characters with no upper limit; 6000-8000 is a preferred depth range when the source supports it, not a cap or hard gate. Also reject 2.5 drafts whose title, hook, or central argument is built around proactive defensive qualifiers or self-negation unless the requested topic is explicitly a concept distinction. Other directions follow their own rules or the user's newest threshold.

For `2.9 Fusion Draft`, the user's current rule overrides that generic default: hard minimum 4000 Chinese characters, with no upper limit. Validate promised list counts, hidden structure, repeated pressure words, natural professional-term insertion, mid-article and ending fan-group CTAs, and the exact fixed ending. Also validate that source-supported strong conclusions were not softened into generic advice, every key list item contains a memorable Gary judgment, conditions sharpen rather than cancel the conclusion, and terms such as `位置稳的男人` do not appear as awkward character labels.

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

Export final `.docx` files to the current dual-device synced workflow folder (`/Users/kin/工作用（同步）/7.1后双端同步文件夹` on Mac, `D:\工作用（同步）\7.1后双端同步文件夹` on Windows) with content/topic-based filenames. Do not leave generic names such as risk-note or timestamp-only filenames.

Before final delivery, verify each `.docx` contains the required headings and has no risk suggestions, yellow highlights, or `[[RISKNOTE:...]]` markers.

### 6. Final Reply

Keep the final answer short. Tell the user the Word file path, character count, and confirm that no risk suggestions, yellow-highlighted annotations, or `[[RISKNOTE:...]]` markers were added.

If optional viral potential review was requested, report it. Otherwise do not add a scoring/pass-fail statement.
