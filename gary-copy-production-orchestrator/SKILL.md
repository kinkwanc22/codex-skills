---
name: gary-copy-production-orchestrator
description: Orchestrate Gary male-account topic, knowledge-supported transplant, one-piece calibration, 2.8 expansion, learned-opening matching, and acceptance without skipping the user's approval gates.
---

# Gary 文案生产总控

Use this skill when the user asks to process a Gary male-account topic batch, send a batch for expansion, redo a batch after route drift, or connect knowledge-base transplant, Gemini expansion, opening matching, and acceptance.

This is an orchestration layer. It does not replace the specialist skills:

- Read `huanxin` for topic/knowledge route design and mechanism deduplication. For Gary topic requests during 2026-09-24 through 2026-10-24, first apply [the monthly topic standard](../huanxin/references/topic-standard-2026-09-24.md): every title has a technique/operation count and concise male benefit plus strong outcome. This supersedes older optional-number title guidance.
- Read `男版扩写` and `douyin-copy-production-workflow-custom` for Gemini expansion and version contracts.
- Read `baokuan-kaitou-sheding` for learned opening matching. Never hand-write a production opening from memory.
- Read `humanize-copy` only when the user explicitly asks for AI-tone cleanup after content acceptance.

## Mandatory sequence

1. **Freeze the current request.** Identify account, batch, titles, version, and whether the user wants topic work, source-route work, expansion, opening matching, or acceptance. Treat `2.8` as ordinary 2.8 Safe Draft unless the user explicitly names another route.
2. **Preflight the batch.** Preserve the user's exact titles. Check topic fingerprint, promised count, mechanism, result, relationship relevance, and within-batch/history similarity. Build one route per article with one primary mechanism and at most one supporting mechanism.
3. **Build the short source.** Use traceable knowledge cards for mechanism explanation and case material. Keep the source lean and public-facing. Do not write `知识库案例`, source labels, prompt instructions, or backstage process language into the manuscript. Do not expose knowledge IDs to Gemini.
4. **Run one calibration article first.** For a new batch or after a route failure, expand only one article. Send the complete selected Gemini prompt plus the article-specific route lock and source. Do not batch-run the remaining articles until the user explicitly approves the test direction.
5. **Keep body and opening separate.** Gemini's first paragraph is not the formal opening. After the body route is accepted, use `baokuan-kaitou-sheding` to choose an existing approved template by topic fingerprint, count, action, and result. Keep fixed template text unchanged; replace only permitted variables. Do not let a generic 2.8 hook become the production opening.
6. **Batch only after approval.** Once the user says the calibration is acceptable, apply the approved route method to the remaining articles, with separate mechanism locks and anti-cross-contamination rules for each.
7. **Accept narrowly.** For ordinary 2.8, require at least 3000 Chinese characters, promised points, a complete natural case before the mid-body CTA, natural professional terminology, the fixed ending, and no backstage leakage. Repair only definite wording, grammar, TTS, or formal-label defects. Do not redesign an otherwise complete article without user instruction.
8. **Learn every manual correction.** When the user rewrites a title or opening, preserve the assistant original, the user's exact version, the differences, and the transferable reason in a dated knowledge-base record. Put only the generalized rule in the relevant rule page or skill reference. Approval without a manual rewrite is a positive candidate signal, not a universal rule.
9. **Verify the learning loop.** Before the next batch, consult the newest correction pairs and run a regression check for mechanism, result, count, title skeleton, forbidden wording, and within-batch similarity. Never claim a correction was learned unless both the exact pair and its generalized rule have a recorded location.

## User-calibrated writing rules

- Preserve the exact public topic and promised number. `六个步骤` or `六个节点` is usable when the body contains executable actions; reject vague structural labels that do not create operational value.
- The user's accepted opening logic prioritizes: strong judgment or observable condition -> low-cost learnable action -> strong male result -> professional topic/mechanism later. Weak benefits such as `理解心理`, `提升认知`, or `愿意回复` cannot carry the hook.
- Do not use `礼貌回应` or similar weak intermediate outcomes as the main opening reward. Avoid `挑选你`, `见面前`, and `普通聊天` when they weaken the intended relationship stage.
- Do not reuse the generic body opening skeleton `女人拿走了什么 / 你留下了什么 / 全砸在你身上 / 卡在这个死局里` across articles. Sympathy is an optional low-frequency entry, not the default. Choose and rotate one topic-native reasoning entry: a hard judgment, contrarian conclusion, immediate conflict, mechanism suspense, behavior diagnosis, or result-backtracking.
- Do not place the complete named case immediately after the formal opening. Unless the route is explicitly approved as a long-case dissection, first establish the mechanism thesis and at least two substantive judgments or operating distinctions, then use the case as proof before the mid-body CTA.
- Separate near mechanisms. Projection is not Barnum self-disclosure; intermittent reinforcement is not expectation design; relationship-battle rules are not random rewards; self-iteration is not a generic self-improvement list.
- Cases are evidence, not point substitutes. They must naturally convey the man's initial problem, the adjustment, observable female feedback, and the result; never expose QA field labels in public copy.
- AI-tone cleanup is local. Remove repeated formulaic phrases and rigid transitions without weakening force, relationship specificity, or valid mechanism vocabulary.

## State boundaries

Record and report these states separately: `source-route-ready`, `calibration-generated`, `user-approved`, `batch-generated`, `正文待确认`, `opening-matched`, `Word-exported`, and `published`. A generated file is never silently treated as accepted.

## Stop conditions

- Stop after the calibration article when user approval is missing.
- Stop and report a route failure when the article drifts from its mother topic, promised count, primary mechanism, or relationship relevance.
- Do not rerun a full batch merely for local wording defects; repair narrowly after acceptance review.

Read the relevant specialist skill and the user-calibrated reference before acting. The companion reference is [references/user-calibrated-rules.md](references/user-calibrated-rules.md).
