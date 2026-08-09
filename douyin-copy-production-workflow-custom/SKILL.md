---
name: douyin-copy-production-workflow-custom
description: Complete Douyin copy production workflow. Use for 抖音文案工作流, 处理这批文案, Gemini本地命令扩写, 三版开头, 长文稿Word导出, 3.0千川素材, 热门原稿保留植入CTA, 1500字内成稿, 直接TTS Word, and end-to-end male relationship copy production.
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
- Current Mac Gemini expansion command: `./scripts/run_gemini_chat.sh --prompt-file <prompt.txt> --output-file <expanded.txt>`. For routine 2.5, use the current 2026-06-05 early B direct-draft block from `references/gemini-expansion.md` and add `--isolated` for every source. Use `--session 2.5` only when the user explicitly asks to continue that saved conversation. Keep 2.8 and 2.9 in their dedicated sessions unless their rules call for isolation.
- TeamRouter network gate: before the first manuscript request in a task, run `./scripts/run_gemini_chat.sh --print-config --isolated` and verify that `TEAMO_CHAT_COMPLETIONS_URL` is exactly under `https://api.teamorouter.com/v1/`. In restricted Codex sandboxes, run the actual manuscript request with the approved escalated network permission and the reusable prefix `./scripts/run_gemini_chat.sh`; a plain sandbox request can fail DNS with `Errno 8` even while TeamRouter, the API key, and the model are healthy. If this happens, rerun the identical isolated request with authorized network access. Do not change the prompt, model, or source merely because the sandbox transport was blocked. Never send the manuscript if the printed endpoint is a different host.
- Current formal 2.9 active prompt for the Gary project: `/Users/kin/Documents/Codex/2026-07-10/qu/work/ACTIVE_2.9_PROMPT_强结论正式版.txt`. The earlier stable rollback baseline remains `/Users/kin/Documents/Codex/2026-07-10/qu/work/ACTIVE_2.9_PROMPT_昨晚12个男性成长版.txt`; do not delete or silently overwrite it.
- Windows fallback Gemini expansion command directory: `C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api`.
- Windows fallback Gemini expansion command: `.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated`.
- Other-copy Gemini isolation rule: for non-male-relationship copy or unrelated tests, use `--prompt-file <prompt> --isolated` on the selected host so saved male relationship expansion conversation state is preserved; do not use `/new` for this.
- Opening source of truth: invoke `baokuan-kaitou-sheding` / `$爆款开头设定`; do not hand-write openings from memory.

## Reference Files

Load only the reference files needed for the current step:

- `references/gemini-expansion.md`: read before sending source text to Gemini, creating prompt files, retrying failures, or checking generated drafts.
- `references/2.5-finished-draft-transplant.md`: read when the user asks for `2.5成稿换芯`, provides an already-expanded approved 2.5 draft as the style parent, or asks to preserve the mother topic while replacing its internal arguments and examples.
- `references/2.9-strong-conclusion-layer.md`: approved formal 2.9 enhancement source of truth for strong conclusions, human-nature games, interest judgments, dark insight retention, and the three-topic validation record. Its prompt text is also embedded inside the formal 2.9 block in `references/gemini-expansion.md` so routine prompt builders cannot omit it.
- `references/source-learning-and-style.md`: read when processing a batch, learning source viral logic, classifying source styles, or preserving source openings.
- `references/openings-and-titles.md`: read after expansion passes checks and before Word export to generate openings, score them, and build title packages.
- `references/export-and-hard-rules.md`: read before optional scoring, Word export, final delivery, and post-run workflow updates.
- `references/3.0-qianchuan-tts.md`: read when the user asks for 3.0千川素材、热门原稿保留植入CTA、1500字内成稿、自然过桥或直接TTS Word交付。

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

Build each UTF-8 prompt file with the selected full Gemini instruction block from `references/gemini-expansion.md`, followed by any required direction-specific injection and the original source text wrapped as `【原文开始】...【原文结束】`. For routine 2.5, the official baseline is the complete 2026-06-05 early B direct-draft block + source, with each source run using `--isolated`. Do not append the old `旧2.5风格参照` injection in routine 2.5 runs unless the user explicitly asks for a separate style-calibration test. If the user asks for 单案例、一案到底、一个案例贯穿全文, use the `2.6 Single Case` direction.

If the user asks for `2.5成稿换芯`, `用扩写好的2.5改内容`, `保留母题替换内容`, or says to keep the method approved by the August 1 fixed-mother-topic batch, use the current canonical fixed-mother-topic limited-inheritance mode in `references/2.5-finished-draft-transplant.md`; do not use routine source expansion, the retired layer-only prompt, or the older full-exclusion transplant mode. Prompt assembly must begin with the complete 2026-06-05 early B 2.5 instruction block from `references/gemini-expansion.md`; append the transplant/strong-attack task layer, an unused article-specific route, a limited-inheritance card, cumulative route exclusions, and the approved 2.5 finished draft. Never use the transplant layer by itself. Retain one central source mechanism and at most two short signature sentences (about 20%-30% of the content role), rebuild the remaining 70%-80% with new scenes, interest changes, consequences, and proof, and run every article through the dedicated copied old conversation with `--session-file work/gemini_session_25_transplant_legacy.json` or the local `--session 2.5-transplant` shortcut. For batches larger than three, work in groups of three and update the cumulative route, similarity, and retry ledgers after each accepted group.

If the user asks for `2.7`, `融合版`, `2.5和2.6融合`, or wants the same effect as the approved 316 body-signal fusion draft, do not ask Gemini to write a separate 2.7 draft from the source. First generate and validate the Gemini 2.5 and 2.6 drafts, then have Codex locally fuse those two accepted drafts using the `2.7 Codex Fusion` rules in `references/gemini-expansion.md`.

If the user asks for `2.9`, `2.5×2.8融合版`, `2.5和2.8融合`, or `融合提示词`, use the saved `2.9 Fusion Draft` direction in `references/gemini-expansion.md`. This is a direct Gemini prompt-file direction: 2.5 supplies Gary voice, sharp judgment, male perspective, business logic, and continuous deduction; 2.8 supplies hidden structure, concrete evidence, reduced adjective pressure, topic isolation, and stable output control. The formally approved strong-conclusion layer is part of 2.9 by default: preserve source-supported human-nature games, interest judgments, dark insights, relationship power changes, and sharp conclusions instead of automatically neutralizing them. Do not substitute the unrelated 2.7 single-case fusion flow.

Do not use the old web expansion channel. Do not send `/new` unless the user explicitly asks. Routine 2.5 is isolated per source and does not write to a saved conversation; `2.5成稿换芯` is the exception and uses its copied dedicated old session. Keep 2.5-transplant, 2.8, and 2.9 in their separate dedicated sessions, and do not run these directions through the default mixed `gemini_session.json`.

### 3. Validate Each Expanded Draft

Read `references/gemini-expansion.md` for the exact checks and retry language.

Verify length, topic relevance, refusal/API failure text, stale-topic contamination, and required ending. For the current 2.5 baseline, the hard minimum is 4000 Chinese characters with no upper limit; 6000-8000 is a preferred depth range when the source supports it, not a cap or hard gate. Also reject 2.5 drafts whose title, hook, or central argument is built around proactive defensive qualifiers or self-negation unless the requested topic is explicitly a concept distinction. Other directions follow their own rules or the user's newest threshold.

For `2.5成稿换芯`, also reject any draft that paraphrases the old list, reuses an excluded signature case, carries over old dialogue, changes the mother topic, loses the selected core source mechanism, overuses inherited material, or refers to earlier episodes/rewriting backstage. Every retained mechanism must be extended with at least two new scenes, interest shifts, consequences, or contrary proofs. Run an awkward-expression pass for invented compounds such as `位置稳的男人` or `性缩力`; repair only obvious local wording defects without softening the argument. Verify the new promised count, mid-article and ending fan-group CTAs, the exact fixed ending, and the cumulative route/similarity ledger before accepting the article.

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
