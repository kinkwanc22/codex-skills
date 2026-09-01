---
name: douyin-copy-production-workflow-custom
description: Complete Douyin copy production workflow. Use for 抖音文案工作流, 处理这批文案, Gemini本地命令扩写, 3.1知识库换芯, 3.1中段CTA, 3.2换芯扩写, 3.3独立换芯扩写, 旧版3.1改为3.3, Codex独立设计新观点, 2.5成稿换芯, 三版开头, 长文稿Word导出, 3.0千川素材, 保头压中自然转化, 热门原稿植入CTA, 1500字内成稿, 直接TTS Word, and end-to-end male relationship copy production.
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

Do not add risk suggestions or `[[RISKNOTE:...]]` markers. For 3.1, preserve all Gemini-returned content. Do not delete its Doubao/AI-summary guidance, engagement prompts, fan-group conversion, account language, examples, strong wording, or other content. The only mandatory content replacement is the terminal ending, which must be normalized to `我是探花Gary，我们粉丝群里见，感谢观看。` Source/Gemini body text remains unhighlighted; by default highlight only the normalized fixed ending in yellow.

## Default Paths

- Assistant source folders are often under `/Users/kin/工作用（同步）/素材文稿/助理采集文案/` on Mac or `D:\工作用（同步）\素材文稿\助理采集文案\` on Windows; old `E:\工作用\素材文稿\助理采集文案\` is legacy-only.
- Final Word output folder for current Mac workflow: `/Users/kin/工作用（同步）/7.1后双端同步文件夹`
- Final Word output folder for current Windows workflow: `D:\工作用（同步）\7.1后双端同步文件夹`
- Legacy Windows final Word output folder: `E:\工作用\素材文稿\codex工作流长文稿`
- Expansion tests/comparison runs must also be exported as `.docx` files into the current dual-device synced workflow folder; do not deliver `.txt` unless the user explicitly asks for txt.
- Gemini execution choice: default to the Mac local runner unless the user explicitly asks to use Windows or the task depends on Windows-only files, old Windows Codex projects, or Windows-only tooling.
- Current Mac Gemini expansion command directory: active Codex workspace when it contains `scripts/run_gemini_chat.sh`; current tested workspace is `/Users/kin/Documents/Codex/2026-07-02/gemini`.
- Current Mac Gemini expansion command: `./scripts/run_gemini_chat.sh --prompt-file <prompt.txt> --output-file <expanded.txt>`. For routine 2.5 and 3.2, use the current 2026-06-05 early B direct-draft block from `references/gemini-expansion.md`; for 3.1, use that complete block plus the fixed mother-topic exact-lock block built by `scripts/build_31_gemini_prompt.py`; for 3.3, use the same complete block plus the separate 3.3 exact-lock block built by `scripts/build_33_gemini_prompt.py`. Add `--isolated` for every source. Use `--session 2.5` only when the user explicitly asks to continue that saved conversation. Keep 2.5-transplant, 2.8, and 2.9 in their dedicated sessions unless their rules call for isolation.
- TeamRouter network gate: before the first manuscript request in a task, run `./scripts/run_gemini_chat.sh --print-config --isolated` and verify that `TEAMO_CHAT_COMPLETIONS_URL` is exactly under `https://api.teamorouter.com/v1/`. In restricted Codex sandboxes, run the actual manuscript request with the approved escalated network permission and the reusable prefix `./scripts/run_gemini_chat.sh`; a plain sandbox request can fail DNS with `Errno 8` even while TeamRouter, the API key, and the model are healthy. If this happens, rerun the identical isolated request with authorized network access. Do not change the prompt, model, or source merely because the sandbox transport was blocked. Never send the manuscript if the printed endpoint is a different host.
- Current formal 2.9 active prompt for the Gary project: `/Users/kin/Documents/Codex/2026-07-10/qu/work/ACTIVE_2.9_PROMPT_强结论正式版.txt`. The earlier stable rollback baseline remains `/Users/kin/Documents/Codex/2026-07-10/qu/work/ACTIVE_2.9_PROMPT_昨晚12个男性成长版.txt`; do not delete or silently overwrite it.
- Windows fallback Gemini expansion command directory: `C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api`.
- Windows fallback Gemini expansion command: `.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated`.
- Other-copy Gemini isolation rule: for non-male-relationship copy or unrelated tests, use `--prompt-file <prompt> --isolated` on the selected host so saved male relationship expansion conversation state is preserved; do not use `/new` for this.
- Opening source of truth: invoke `baokuan-kaitou-sheding` / `$爆款开头设定`; do not hand-write openings from memory.

## Reference Files

Load only the reference files needed for the current step:

- `references/mother-topic-exact-lock.md`: read for every male Gary rewrite, expansion, 2.5成稿换芯, 3.1, 3.2, 3.3, fixed-topic cycle, or knowledge-base-assisted rewrite. The source body's public mother topic is an exact lock; only content underneath it may change. Knowledge-pack titles and abstract summaries never rename the public topic.
- `references/gemini-expansion.md`: read before sending source text to Gemini, creating prompt files, retrying failures, or checking generated drafts.
- `references/3.1-knowledge-base-transplant.md`: read in full for every `3.1`, `3.1换芯`, `2.5预换芯`, or `原稿预换芯` task. This is the canonical default: Codex selects, excludes, polishes, and transplants only traceable B/X knowledge without inventing content; Gemini then freely expands the frozen source through the complete standard 2.5 prompt with `--isolated` and no knowledge-closure supplement. Its Word export uses the 3.1-specific four-opening package: two generated openings, the verbatim source opening, and a separate source-opening optimized version aligned to the accepted body.
- `references/3.3-codex-designed-pretransplant.md`: read in full for every `3.3`, `3.3独立换芯`, `旧版3.1`, or `让Codex设计新观点` task. This is the former pre-knowledge-base 3.1 workflow under a new formal version number. It uses no knowledge base: Codex independently rebuilds the short source and topic-native conversion route, then Gemini expands it through the complete old 2.5 prompt in an isolated run. Keep its prompt, ledger, validation, Word package, and status separate from 3.1 and 3.2.
- `references/knowledge-lifecycle-feedback.md`: read after any Gary knowledge-base-assisted draft and whenever publication data or opening performance must feed later retrieval. It binds knowledge, route, opening, account, lifecycle state, and data snapshots through one stable work ID.
- `references/3.1-cta-layer.md`: read after every 3.1 Gemini body is accepted and before Word export. It is the Gemini full-retention and terminal-ending-normalization rule: preserve every Gemini content unit in its original order, add no Codex CTA, and replace only the terminal ending with `我是探花Gary，我们粉丝群里见，感谢观看。`; narrow non-deleting grammar/TTS repairs are allowed only when recorded exactly.
- `references/2.5-finished-draft-transplant.md`: read when the user asks for `2.5成稿换芯`, provides an already-expanded approved 2.5 draft as the style parent, or asks to preserve the mother topic while replacing its internal arguments and examples.
- `references/3.2-conversion-transplant.md`: read when the user asks for `3.2`, `3.2换芯`, or `3.2换芯扩写`. This mode keeps its own controlled-inheritance rules and does not automatically inherit 3.1's new Codex closed-set knowledge restriction unless the user explicitly asks to merge them. It preserves 60%-80% of the source's content functions, overlays the approved monetization sequence, and places compact Gary student-case proof after selected theory explanations. It uses one ending fan-group CTA, then runs the frozen source through the same complete 2.5 prompt with `--isolated`.
- `references/gemini-expansion.md`: also read when the user asks for `3.1`, `2.5预换芯`, `原稿预换芯`, or wants to first rebuild the short source manuscript while keeping the exact public topic, then run routine 2.5 expansion.
- `references/2.9-strong-conclusion-layer.md`: approved formal 2.9 enhancement source of truth for strong conclusions, human-nature games, interest judgments, dark insight retention, and the three-topic validation record. Its prompt text is also embedded inside the formal 2.9 block in `references/gemini-expansion.md` so routine prompt builders cannot omit it.
- `references/source-learning-and-style.md`: read when processing a batch, learning source viral logic, classifying source styles, or preserving source openings.
- `references/openings-and-titles.md`: read after expansion passes checks and before Word export to generate openings, score them, and build title packages.
- `references/export-and-hard-rules.md`: read before optional scoring, Word export, final delivery, and post-run workflow updates.
- `references/3.0-qianchuan-tts.md`: read when the user asks for 3.0千川素材、保头压中自然转化、热门原稿植入CTA、1500字内成稿、自然过桥或直接TTS Word交付。

## Workflow

### 1. Queue Every Provided Source By Default

When the user provides a batch of `.docx` scripts, do not run pre-expansion scoring, ranking, filtering, or top-N selection unless explicitly asked. Preserve stable filename order unless the user gives another order.

Read `references/source-learning-and-style.md` and create a concise batch learning note in the current workspace outputs folder.

### 2. Expand With Local Gemini

Read `references/gemini-expansion.md`.

Before selecting a route or knowledge, read `references/mother-topic-exact-lock.md`, copy one exact public mother-topic anchor from the source body, and record it. The frozen source, expanded body, Word title, and filename must continue to use that source-derived mother topic. Never replace it with a knowledge-pack title, card summary, course label, safer abstraction, or newly invented umbrella concept. Only the content beneath the locked mother topic may be replaced.

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

If the user asks for `2.5成稿换芯`, `用扩写好的2.5改内容`, `保留母题替换内容`, or says to keep the method approved by the August 1 fixed-mother-topic batch, use the current canonical fixed-mother-topic limited-inheritance mode in `references/2.5-finished-draft-transplant.md`; do not use routine source expansion, the retired layer-only prompt, or the older full-exclusion transplant mode. For every transplant mode, infer the mother topic, audience promise, central claim, and promised count from the manuscript body only. Never use the filename, folder name, Word title/core properties, document heading, stale metadata, or an earlier output title to choose the route or invent a structure; those fields are for file identification only. If any of them conflict with the body, the body wins. Prompt assembly must begin with the complete 2026-06-05 early B 2.5 instruction block from `references/gemini-expansion.md`; append the transplant/strong-attack task layer, an unused article-specific route, a limited-inheritance card, cumulative route exclusions, and the approved 2.5 finished draft. Never use the transplant layer by itself. Retain one central source mechanism and at most two short signature sentences (about 20%-30% of the content role), rebuild the remaining 70%-80% with new scenes, interest changes, consequences, and proof, and run every article through the dedicated copied old conversation with `--session-file work/gemini_session_25_transplant_legacy.json` or the local `--session 2.5-transplant` shortcut. For batches larger than three, work in groups of three and update the cumulative route, similarity, and retry ledgers after each accepted group.

If the user asks for `3.2`, `3.2换芯`, `3.2换芯扩写`, or `带小案例的预换芯`, use `references/3.2-conversion-transplant.md`. The canonical 3.2 starts from the complete 3.1 pre-transplant knowledge workflow but keeps its own conversion and Gemini prompt rules; do not inherit 3.1's mother-topic prompt injection, raw-conversion cleanup, or yellow-highlight default unless the user explicitly asks. Before choosing the route, load both ledgers and build a cross-version exclusion pack. Preserve 60%-80% of viewpoint/mechanism functions, replace the majority of concrete operations, use theory-first compact cases, and keep the separate 3.2 monetization ledger. After freezing, follow the 3.2 reference's current Gemini and CTA instructions rather than saying “exactly like 3.1”.

For 3.2 knowledge retrieval, the standard call pack must include page-anchored `external_atomic_knowledge` and `GCOMP-*` Gary anonymized composite case candidates. A `GCOMP-*` result is not a ready-made case: open its card, use one continuous source scene, and complete the four proof fields before adapting it into Gary narration. If either type is adopted, keep its ID and source status in the internal ledger; an external composite may not be relabelled internally as a verified Gary student record.

For `3.1`, `3.2`, and `3.3`, novelty must stay inside the source's original attack direction. Do not obtain novelty by renaming a direct, provocative promise into neutral abstractions such as `关系权限逐级开放`, `阶段识别`, `边界管理`, `关系治理`, `健康沟通`, or `风险识别`. Preserve the source's force band, target result, conflict object, male desire, and hard-edged framing; replace the internal arguments and operations without converting `推进到暧昧/进入男女框架/让她投入/拿回主动权` into a safer educational meta-topic. If deleting the new abstract label restores the original article's sharper promise, the label is a drift defect and the rebuilt source must be rewritten before Gemini.

This lock also forbids non-neutral renaming. A provocative source topic such as `女人最想要男人的四样东西 / 四个致命需求` may not become `四种心理待遇`, `四种心理营养`, or another newly unified label even when the new wording remains aggressive. Preserve the public mother topic itself; knowledge retrieval may only replace the items, mechanisms, operations, cases, and proof beneath it as allowed by the selected mode.

If the user asks for `3.1`, `3.1换芯`, `2.5预换芯`, `原稿预换芯`, or `原稿先换芯再2.5`, read and follow `references/3.1-knowledge-base-transplant.md` as the canonical default. Infer and preserve the mother topic/count from the body; retrieve traceable knowledge, exclude accepted routes, and bind every replacement point to exact IDs. Codex may select, merge compatible knowledge, adapt perspective, polish, order, and write transitions, but it may not invent substantive content. Save point-level provenance and freeze a conversion-free source with `codex_content_invention: false`. Build the Gemini request with `scripts/build_31_gemini_prompt.py`: the complete standard 2.5 block remains intact, the fixed public-mother-topic exact-lock block is inserted immediately before the frozen source, and every source runs through `--isolated`. Do not send vault paths, knowledge IDs, provenance, exclusions, or another supplement. Preserve all Gemini-returned content; allow only recorded non-deleting mechanical repair and terminal-ending normalization. If the first retrieval set cannot support the promised count, broaden retrieval and replace weak slots with other traceable B/X/external-atomic modules before blocking; never fill a slot from general model knowledge or silently switch modes.

For 3.1, preserve the complete old 2.5 prompt and preserve every content unit Gemini returns, including Doubao/AI-summary guidance, engagement prompts, fan-group conversion, account language, examples, hard-edged language, and repeated conversion mentions. Save the raw output unchanged. Do not run `scripts/clean_31_gemini_conversion.py` or `scripts/validate_31_gemini_no_cta.py` in the current 3.1 workflow; they are legacy audit tools only. After topic/count/force/length validation, apply `references/3.1-cta-layer.md`: add no Codex CTA and delete no Gemini content. The sole mandatory content replacement is the terminal ending, normalized to exactly `我是探花Gary，我们粉丝群里见，感谢观看。` Narrow grammar, punctuation, obvious broken-word, and TTS repairs are allowed only when they preserve every content claim and are recorded as exact before/after pairs. In the default 3.1 Word, highlight only the normalized fixed ending in yellow; do not highlight source/Gemini text.

After final provenance and the actual opening choice are known, read `references/knowledge-lifecycle-feedback.md` and register the draft under one stable work ID. Record only knowledge and openings actually adopted. When publication data later becomes available, append snapshots under the same ID; never infer confirmation, publication, or data review from file existence.

For 3.1, route diversity must come from selecting different traceable knowledge modules, not from Codex inventing a new thesis, and it must never be purchased by lowering the force band. Every selected replacement point must preserve a memorable Gary judgment and show at least one concrete interest shift, relationship-position change, subconscious revaluation, selection consequence, emotional reward/punishment, or real cost supported by its cited B/X knowledge. Reject a route that is merely accurate, professional, or novel but centers neutral management, risk control, healthy communication, collaboration, psychological nourishment, evidence classification, or counseling language. Record `force_band: old_2.5_hard`, selected knowledge IDs, point provenance, `codex_content_invention: false`, `gemini_closed_set_restriction: false`, `memorable_judgments`, and `interest_shifts` before freezing.

For 3.1 experience judgments, default to one source-supported judgment inside every core point of the frozen source. Treat this as a proof rule, not a visible writing template. Rotate materially different evidence operations across the article, such as observing a small decision, auditing a display surface, checking reaction timing, comparing written screening standards, inspecting a message sequence, or testing continuous behavior. When a long same-topic list genuinely requires reuse of one evidence lane, change the observable criterion, scene, and diagnostic purpose rather than repeating the same paragraph shell. Do not fabricate client volume, identities, screenshots, guaranteed outcomes, or success stories. Reject a source when multiple points repeat `我经常/我复盘过很多/群里有个兄弟` with only the topic noun changed. Record the point number, proof function, observable evidence, and supporting knowledge IDs in provenance. Do not append a Gemini instruction about experience density/count/type, and do not inject experience paragraphs after generation; Gemini still receives only the complete old 2.5 prompt, fixed mother-topic lock, and frozen source.

For 3.1 technique/how-to manuscripts, changing only the explanation is not a transplant. Keep the body-derived mother topic, target result, relationship stage, and promised item count, but select replacement techniques from traceable B/X knowledge rather than designing them from general model knowledge. Each selected technique must still provide trigger, action/natural line, observable feedback, and next move/failure condition. If the knowledge base lacks enough distinct executable techniques to fulfill the promise, stop before freezing and report the missing slot. Record the knowledge source for each replacement technique together with `content_class`, `source_techniques`, `replacement_techniques`, and `operation_overlap`.

If the user asks for `3.3`, `3.3独立换芯`, `旧版3.1`, `接入知识库前的3.1`, or explicitly asks Codex to design new viewpoints without the knowledge base, follow `references/3.3-codex-designed-pretransplant.md`. Do not retrieve B/X knowledge, do not write knowledge provenance, and do not use the 3.1 conversion cleaner, CTA-layer rule, yellow-highlight rule, four-opening package, or unified 3.1 validator. Use `scripts/inspect_33_recent_routes.py`, the separate 3.3 ledger, and `scripts/build_33_gemini_prompt.py`. The full old 2.5 prompt remains intact, including its conversion instructions; Gemini's direct CTA/fixed-ending output is retained and only narrowly repaired when required. This routing does not change routine 2.5, formal 3.1, or 3.2.

If the user asks for `2.7`, `融合版`, `2.5和2.6融合`, or wants the same effect as the approved 316 body-signal fusion draft, do not ask Gemini to write a separate 2.7 draft from the source. First generate and validate the Gemini 2.5 and 2.6 drafts, then have Codex locally fuse those two accepted drafts using the `2.7 Codex Fusion` rules in `references/gemini-expansion.md`.

If the user asks for `2.9`, `2.5×2.8融合版`, `2.5和2.8融合`, or `融合提示词`, use the saved `2.9 Fusion Draft` direction in `references/gemini-expansion.md`. This is a direct Gemini prompt-file direction: 2.5 supplies Gary voice, sharp judgment, male perspective, business logic, and continuous deduction; 2.8 supplies hidden structure, concrete evidence, reduced adjective pressure, topic isolation, and stable output control. The formally approved strong-conclusion layer is part of 2.9 by default: preserve source-supported human-nature games, interest judgments, dark insights, relationship power changes, and sharp conclusions instead of automatically neutralizing them. Do not substitute the unrelated 2.7 single-case fusion flow.

Do not use the old web expansion channel. Do not send `/new` unless the user explicitly asks. Routine 2.5, 3.1, 3.2, and 3.3 are isolated per source and do not write to a saved conversation; `2.5成稿换芯` remains the exception and uses its copied dedicated old session. Keep 2.5-transplant, 2.8, and 2.9 in separate dedicated sessions, and do not run these directions through the default mixed `gemini_session.json`.

### 3. Validate Each Expanded Draft

Read `references/gemini-expansion.md` for the exact checks and retry language.

Verify length, topic relevance, refusal/API failure text, stale-topic contamination, and required ending. For the current 2.5 baseline, the hard minimum is 4000 Chinese characters with no upper limit; 6000-8000 is a preferred depth range when the source supports it, not a cap or hard gate. Also reject 2.5 drafts whose title, hook, or central argument is built around proactive defensive qualifiers or self-negation unless the requested topic is explicitly a concept distinction. Other directions follow their own rules or the user's newest threshold.

For every rewrite or transplant, run the mother-topic lock before acceptance. Reject when the exact source-derived anchor is absent from the frozen source or final body, when a derived umbrella label organizes the article, or when a knowledge-pack title overrides the source body. Record `mother_topic_source_quote`, `mother_topic_anchor`, `mother_topic_public_wording`, `mother_topic_exact_lock_pass`, and `knowledge_pack_title_ignored_for_topic` in the run ledger.

For every Gary direction, reject forced identity-prefixed narration such as `作为探花Gary`, `作为Gary`, or `以探花Gary的身份`. Enter first-person judgments directly. `Gary哥` may appear only in natural quoted dialogue, and `探花Gary` otherwise belongs in the exact fixed ending unless the user-supplied opening already contains the name.

For `2.5成稿换芯`, also reject any draft that paraphrases the old list, reuses an excluded signature case, carries over old dialogue, changes the mother topic, loses the selected core source mechanism, overuses inherited material, or refers to earlier episodes/rewriting backstage. Every retained mechanism must be extended with at least two new scenes, interest shifts, consequences, or contrary proofs. Run an awkward-expression pass for invented compounds such as `位置稳的男人` or `性缩力`; repair only obvious local wording defects without softening the argument. Verify the new promised count, mid-article and ending fan-group CTAs, the exact fixed ending, and the cumulative route/similarity ledger before accepting the article.

For `3.2换芯扩写`, apply the complete inherited 3.1 validation gate plus the viewpoint-scope control, operation-replacement, theory-first student-case, monetization, and natural-self-reference gates in `references/3.2-conversion-transplant.md`. Reject any run that replaces the source's original answer categories, main causal chain, or topic-defining mechanisms, preserves fewer than 60% of viewpoint functions without authorization, or merely reuses/paraphrases the source's concrete actions, scripts, micro-steps, examples, and proof chain. Every new operating method must still fulfill its preserved viewpoint in the same relationship stage. Also reject a missing frozen source, a second-layer 3.2 prompt, a case placed before its theory, generic/detached cases, a case that lacks student problem/Gary adjustment/observable feedback/theory return, an unsupported verified-result claim, a consultation-flip story, forced identity prefixes such as `作为探花Gary` or `作为Gary`, withheld public value, a mid-article explicit CTA, or more than one conversion action. Verify the separate 3.2 viewpoint/operation/route/case/conversion ledger, the single ending conversion unit, and the exact ending.

For `2.9 Fusion Draft`, the user's current rule overrides that generic default: hard minimum 4000 Chinese characters, with no upper limit. Validate promised list counts, hidden structure, repeated pressure words, natural professional-term insertion, mid-article and ending fan-group CTAs, and the exact fixed ending. Also validate that source-supported strong conclusions were not softened into generic advice, every key list item contains a memorable Gary judgment, conditions sharpen rather than cancel the conclusion, and terms such as `位置稳的男人` do not appear as awkward character labels.

### 4. Add Openings And Titles

Read `references/openings-and-titles.md`.

For every accepted article, execute these subskills in order:

1. Invoke `baokuan-kaitou-sheding` / `$爆款开头设定` and use its approved learned opening forms as the source of truth for `开头版本一：高阶认知课式开头` and `开头版本二：身份点名式硬核学习开头`. Do not hand-write generic openings from memory.
2. Extract `开头版本三：保留原文开头（来自源文档）` from the source document without rewriting it.
   - For 3.1 only, also add `开头版本四：原文开头优化版（贴合正文）` according to `references/3.1-knowledge-base-transplant.md`. Keep version three verbatim and keep version four separate from the accepted body.
3. Score versions one and two with the mandatory 20-point opening gate; rewrite with `baokuan-kaitou-sheding` until both pass.
4. Invoke `viral-psych-title-wrapper` / `$爆款心理学标题包装器` for the title package. Generate 10 three-line candidates, strongest 3, and recommendation reason.
5. Maintain a batch title ledger to avoid duplicate mechanism chains or generic interchangeable titles.

### 5. Export Clean Word Documents

Read `references/export-and-hard-rules.md`.

Export final `.docx` files to the current dual-device synced workflow folder (`/Users/kin/工作用（同步）/7.1后双端同步文件夹` on Mac, `D:\工作用（同步）\7.1后双端同步文件夹` on Windows) with content/topic-based filenames. Do not leave generic names such as risk-note or timestamp-only filenames.

Before final delivery, verify each `.docx` contains the required headings and has no risk suggestions or `[[RISKNOTE:...]]` markers. For 3.1, also verify the yellow-highlight set contains only the normalized fixed ending and exactly matches the Gemini-retention manifest.

For 3.1, do not run LibreOffice, `soffice`, PDF conversion, PNG rendering, or `render_docx.py`. Save a Gemini-retention manifest containing the raw path/hash, empty `removed_content`, any exact mechanical before/after repairs, terminal ending replacement, and `highlight_texts: [fixed_ending]`. Then run `scripts/validate_31_final_package.py --insertion-manifest <manifest.json>` once after Word export. Use `--allow-no-yellow` only when the user explicitly requests a clean unhighlighted 3.1 Word.

### 6. Final Reply

Keep the final answer short. Tell the user the Word file path, character count, that Codex-added 3.1 insertions were highlighted yellow by default, and that no risk suggestions or `[[RISKNOTE:...]]` markers were added.

If optional viral potential review was requested, report it. Otherwise do not add a scoring/pass-fail statement.
