---
name: humanize-copy
description: Rewrite and polish Chinese copy to reduce obvious AI-generated style while preserving meaning, intent, facts, and the user's target audience. Use when the user asks to 去AI味, 降AI感, 去除AI痕迹, 人味一点, 更像真人写的, 更自然, 更口语, 更有网感, 文案润色, 改写中文文案, polish Chinese copy, humanize Chinese copy, or adapt AI-like drafts for social posts, articles, scripts, newsletters, marketing copy, academic-adjacent prose, and creator content.
---

# Humanize Chinese Copy

## Core Goal

Transform stiff, generic, over-polished Chinese drafts into writing that sounds intentional, lived-in, and context-aware. Preserve the original facts, claims, names, numbers, structure constraints, and user intent unless the user asks for deeper rewriting.

## Workflow

1. Identify the text type: social post, article, short-video script, newsletter, product copy, academic-adjacent prose, speech, or other.
2. Infer the target voice from the user's request and source text. If unspecified, use a natural, clear, moderately conversational Chinese voice.
3. Diagnose AI-like patterns before rewriting:
   - Empty intensifiers: "非常重要", "值得关注", "不容忽视", "显著提升".
   - Template transitions: "首先/其次/最后", "综上所述", "总而言之".
   - Over-balanced parallelism and symmetrical paragraphs.
   - Abstract nouns stacked without concrete scenes or stakes.
   - Smooth but bloodless claims that avoid specificity.
   - Repeated sentence length and identical rhythm.
4. Rewrite in passes:
   - Keep the main meaning and useful structure.
   - Replace generic claims with concrete phrasing, examples, sharper verbs, or real tradeoffs.
   - Vary sentence length and rhythm.
   - Cut filler and slogan-like phrasing.
   - Add light human texture only when it fits: hesitation, observation, context, consequence, or a grounded detail.
   - Keep punctuation natural; avoid excessive exclamation marks, emoji, and internet slang unless the brief calls for it.
5. Self-check the output:
   - Does it still say the same thing?
   - Does it sound like a person with a point of view wrote it?
   - Are there any fake specifics, unsupported claims, or invented facts?
   - Are AI-ish stock phrases still present?

## Rewrite Modes

Choose the mode that best matches the request. If the user does not specify a mode, use `balanced`.

- `light`: Minimal polish. Keep most wording and structure; remove stiffness and repetitive transitions.
- `balanced`: Noticeably more natural. Improve rhythm, wording, and paragraph flow while preserving intent.
- `strong`: Heavier rewrite. Rebuild order, voice, hooks, and expression while preserving the core message.
- `platform`: Adapt for a named platform or format, such as 小红书, 公众号, 短视频口播, 朋友圈, LinkedIn, or email.
- `academic-soften`: Reduce AI-like academic phrasing without making the text unserious or adding unsupported personal claims.

## Style Rules

- Prefer concrete nouns and verbs over abstract summaries.
- Prefer one vivid, accurate detail over several decorative adjectives.
- Keep human texture modest; do not force jokes, slang, or "口水话".
- Do not overdo broken sentences. Natural writing can still be polished.
- Avoid moralizing and inflated certainty unless the source text clearly requires it.
- Preserve domain terms, legal/medical/financial cautions, and citations.
- For sensitive, professional, or academic text, prioritize clarity and authenticity over "网感".

## Output Format

When the user provides only text to rewrite, return:

```markdown
改写版：
<rewritten text>

调整说明：
- <1-3 concise notes about what changed>
```

When the user asks for multiple options, provide 2-3 distinct versions with labels such as `更自然`, `更犀利`, `更口语`.

When the user asks only for the final copy, return just the rewritten copy.

## Constraints

- Do not claim the text can bypass AI detectors or guarantee lower detection scores.
- Do not fabricate personal experience, quotes, data, sources, customer stories, or case details.
- If the source text is too short or context is missing, make a reasonable rewrite and briefly state any assumption.
- If the user asks to preserve length, formatting, headings, keywords, or tone, follow that constraint first.
