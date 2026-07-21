# Export, Delivery, And Hard Rules

Read this file before exporting Word documents, reporting final delivery, or updating the workflow after a completed batch.

## Contents

- Optional viral potential review
- Word export without risk suggestions
- Final delivery response
- Post-run self optimization
- User hard rules

### 5. Optional Viral Potential Review

Do not run this review as a gating or filtering step by default. Only run the generated output back through the `douyin-emotion-copy-scorer` rubric if the user explicitly asks for scoring/review, or if the run already includes a scoring deliverable.

If requested, use this review language:

- 85+：爆款潜力很强。
- 75-84：可用，但建议优化开头或调整剪辑取舍。
- Below 75：记录弱点，但不要因此阻止 Word 导出，除非用户明确要求只导出高分稿。

Report:

- Total score.
- Strongest viral genes.
- Weakest points.
- Platform risk level.
- Editing suggestions, if any.

### 7. Word Export Without Risk Suggestions

The user now wants final documents to contain only:

- Three opening versions:
  - `开头版本一：高阶认知课式开头`
  - `开头版本二：身份点名式硬核学习开头`
  - `开头版本三：保留原文开头（来自源文档）`
- `正文`
- The generated article text exactly as produced.

Important rules:

- Do **not** add risk suggestions.
- Do **not** add yellow-highlighted annotations.
- Do **not** insert `[[RISKNOTE:...]]` markers.
- Do **not** rewrite or sanitize risky words unless the user explicitly asks for rewriting.
- Export the Word document directly from the final text structure above, with the title package placed before the three opening versions.
- Final file names should be content/topic based, e.g. `编号_内容标题_三版开头_最终版.docx`.
### 8. Final Delivery

Tell the user:

- Word file path.
- Character count.
- Confirm that no risk suggestions, yellow-highlighted annotations, or `[[RISKNOTE:...]]` markers were added.
- If an optional viral potential review was requested, report the review result; otherwise do not add a scoring/pass-fail statement.

Keep the final answer short.

### Post-Run Self Optimization Rules

After every completed batch, perform a short self-optimization pass before final reply:

- Identify what failed, slowed down, or confused the workflow.
- Update this skill or its bundled scripts when the lesson is reusable.
- Prefer hard procedural rules over vague reminders.
- Keep the update concise and focused on preventing the exact failure from recurring.

Latest hard-learned rules from 2026-06-03:

- The current default final output folder is the dual-device synced workflow folder: `/Users/kin/工作用（同步）/7.1后双端同步文件夹` on Mac, and `D:\工作用（同步）\7.1后双端同步文件夹` on Windows. The old Windows folder `E:\工作用\素材文稿\codex工作流长文稿` is legacy-only unless the user explicitly asks for it.
- Final deliverables must be Word `.docx` files by default. Do not deliver `.txt` as the final format unless the user explicitly asks for txt.
- Expansion tests and prompt-comparison runs also count as deliverables: export accepted 2.5/2.6 test results as `.docx`, not `.txt`.
- Current synced output folder is `/Users/kin/工作用（同步）/7.1后双端同步文件夹` on Mac and `D:\工作用（同步）\7.1后双端同步文件夹` on Windows; save generated `.docx` results there by default so both devices can pick them up.
- Temporary `.txt` drafts may be used only as intermediate cache; immediately convert accepted Gemini outputs into `.docx` in the current synced output folder.
- After saving, always verify the exact final folder by checking the expected `.docx` filenames, file sizes, and current timestamps. Do not trust a successful copy/conversion command alone.
- Do not use `soffice`, LibreOffice, or `render_docx.py` for this Douyin copy workflow. The local `soffice` renderer can trigger a macOS crash/update dialog and interrupt the user's work. For these text-first Word deliverables, verify by checking the `.docx` zip/package structure, required headings, absence of risk markers, file size, and current timestamp instead.
- Avoid Chinese text in script glob patterns on old Windows PowerShell. Use ASCII globs such as `*.txt` and then filter by explicit filename list or ASCII substrings related to the generated draft name.
- When writing PowerShell helper scripts that contain Chinese filenames, prompts, or openings, save the script as UTF-8 with BOM before running it in Windows PowerShell 5.1; otherwise Chinese literals can become mojibake and break parsing or filename matching.
- In the local Gemini terminal, do not send `/new` by default; keep the current session unless the user explicitly asks to clear context.
- Never replace, shorten, summarize, rewrite, or downgrade the selected full Gemini expansion instruction block with a short prompt.
- For first attempts, refusal retries, stale-topic retries, hallucination retries, and length retries, always send the selected full Gemini expansion instruction block + its documented direction-specific injection + the original source copy wrapped as `【原文开始】...【原文结束】`; do not prepend `/new` unless explicitly requested. For 2.5, rerun the complete prompt with `--isolated`.
- If Gemini refuses, returns API/tool failure text, reuses a previous article topic, is below the length threshold, or lacks the required ending, do not save it as a final result. For 2.5, rebuild the complete prompt and retry with `--isolated`; for other directions, follow their session rules. Record the failure in a batch log and do not send `/new` unless explicitly requested.
- Preserve the user's high-risk, high-conflict topic direction during expansion, opening writing, and title packaging. Do not proactively downgrade the framing to `机制识别、边界判断、关系主权、健康筛选` unless the user explicitly asks for that safer framing. If Gemini refuses, do the minimum wording adjustment needed to get a complete generation while preserving the original topic's sharpness.
- For `处理这批文案`, treat the default endpoint as final Word documents with three opening versions, opening review scores,正文, and a concise batch log, not merely raw Gemini expansion text.
- Do not treat raw Gemini expansion documents as final deliverables. Final deliverables must include the three opening sections before正文 unless the user explicitly asks for expansion-only drafts.
- Before final delivery, inspect each generated `.docx` package or otherwise verify that it contains these headings: `开头版本一：高阶认知课式开头`, `开头版本二：身份点名式硬核学习开头`, `开头版本三：保留原文开头（来自源文档）`, and `正文`.
- If a post-run self-check finds a missed workflow step, fix the deliverables first, then update this skill with the reusable lesson before final reply.
## User Hard Rules

These rules come from the user's live workflow corrections and must override the generic workflow whenever they apply.

- `2.5 Direct Draft` officially uses the approved 2026-07-05 batch logic: full restored 2.5 instruction block + the short `旧2.5风格参照` injection + source manuscript, with one `--isolated` request per source.
- 2.5 remains dark, realistic, harsh, interest-driven, power-sensitive, and conclusion-forward. Do not automatically soften it into safe psychology education, boundary management, self-management, healthy-relationship advice, or neutral communication guidance.
- For 2.5 topic selection, angle rewriting, titles, hooks, and body transitions, remove proactive defensive qualifiers such as `不教操控、不是控制、不是冷漠、不是为了拿捏、看懂不等于拿捏`. Do not foreground limitations or make self-negation the content promise unless the user explicitly requests a concept-comparison or reverse-clarification topic. Preserve the viral mother topic and rebuild the angle through mechanism, interest movement, power change, consequence, or harsh judgment.
- Reject a 2.5 draft when its title or central argument relies on first denying the strong premise and then retreating into healthy-relationship education. This rule does not authorize forced dark-keyword stuffing; pressure must still come from concrete reasoning and consequences.
- Preserve source-supported human-nature games, interest calculations, relationship leverage, emotional reward and punishment, and harsh judgments through scenes and mechanism chains. Darkness must come from the reasoning and consequences, not from forcing a checklist of words such as `拿捏、惩罚、服从、坏男人` into every article. Use such words only when the source and sentence naturally call for them.
- Do not add large sample packs, representative excerpts, or extra topic skeletons to a routine 2.5 prompt. They are reserved for an explicitly requested style-calibration test; routine production uses only the short injection so it does not copy old topics.
- Aggressive does not mean copying an old manuscript. When reusing a viral mother topic, first rebuild a genuinely new content skeleton, then expand it in old 2.5 language movement. Reject both failure modes: `语感对但内容照搬旧稿` and `内容新但被改成温和安全版`.
- Do not impose 2.8 hidden-six-layer control or 2.9 orderly per-item mechanism templates on a 2.5 draft. Let item length, entry style, pressure, analogy, and deduction depth vary naturally like the approved old 2.5 manuscripts.

- Default to the Mac local Gemini runner for expansion unless the user explicitly asks for Windows or the task depends on Windows-only files, old Windows Codex projects, or Windows-only tooling: `cd /Users/kin/Documents/Codex/2026-07-02/gemini` then `./scripts/run_gemini_chat.sh --prompt-file work/prompt.txt --isolated --output-file work/expanded.txt`.
- Use the Windows Gemini runner only when explicitly needed: `cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api` then `.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated`.
- For automated expansion, prefer the selected host runner with a UTF-8 prompt file containing the selected full instruction block + its documented direction-specific injection + original source copy wrapped as `【原文开始】...【原文结束】`.
- Do not open or operate the old web expansion channel in this custom skill.
- Before every new queued 2.5 source, paste the selected full Gemini expansion instruction block, the short legacy injection, and then the original source copy ending with `【原文结束】`; run it with `--isolated`. Do not send `/new` unless explicitly requested.
- When Gemini output is too short, send the retry instruction directly in the current terminal session for that same source.
- After every expansion, verify length, topic relevance, refusal/API failure text, and required ending. Passing length alone is not enough.
- If the output reuses a previous article's theme, switches topic, or comments on the source instead of expanding it, treat it as hallucination/running off-topic. For 2.5, rebuild the complete prompt and retry with `--isolated`; for other directions, follow their session rules. Do not send `/new` unless the user explicitly requests it.
- Do not prepend any extra instructions beyond the selected full mandatory Gemini expansion instruction block and its documented direction-specific injection, unless a retry instruction is explicitly needed.
- When processing a batch, run `viral-psych-title-wrapper` / 「爆款心理学标题包装器」 before Word export and maintain a batch title ledger to avoid repeated mechanism chains, repeated first-line concepts, and generic interchangeable titles.
- Current title-wrapper rule: each title candidate is three lines only; do not add 完整未删减版 as a fourth title line unless the user explicitly asks to restore that older format.
- Do not add risk suggestions or yellow-highlighted annotations during Word export.
- All exported documents must be renamed by the article content/topic, preferably `编号_内容标题_版本.docx`; never leave `.txt` outputs or generic names like `扩写稿-风险旁注版-时间戳.docx` as final deliverables.

Latest hard-learned rules from 2026-06-03 evening:

- Browser automation is not needed for expansion in this custom skill; the expansion channel is the local Gemini terminal command.
- If a 2.5 draft returns below 4000 Chinese characters, do not mark it passed. Retry the complete prompt with `--isolated`, or mark it as not entering the final Word pool if retries trigger refusal. Other directions follow their own current threshold.
