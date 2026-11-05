---
name: humanize-copy
description: Rewrite and polish Chinese copy to reduce obvious AI-generated style while preserving meaning, intent, facts, and the user's target audience. Use when the user asks to 去AI味, 降AI感, 去除AI痕迹, 人味一点, 更像真人写的, 更自然, 更口语, 更有网感, 文案润色, 改写中文文案, polish Chinese copy, humanize Chinese copy, or adapt AI-like drafts for social posts, articles, scripts, newsletters, marketing copy, academic-adjacent prose, and creator content.
---

# Humanize Chinese Copy

## Core Goal

Transform stiff, generic, over-polished Chinese drafts into writing that sounds intentional, lived-in, and context-aware. Preserve the original facts, claims, names, numbers, structure constraints, and user intent unless the user asks for deeper rewriting.

## Gary 用户表达参考

处理Gary男性情感口播，或用户明确要求按其2026-11-02提供的表达样本与gary文稿全库优化时，先读 [Gary表达参考](references/gary-voice.md)。这些样本呈现的是有术语、有强判断、直接拆因果与操作的讲解口吻；不要把“自然”默认解释成闲聊、降力度或删尽抽象词。此分支默认从light局部优化开始，用户要求整篇重写时服从当次要求；锁定的故事、案例、开头与CTA边界仍优先。

这是特定用户/账号的参考，不改变其他文体的balanced默认值，不把样本中的知识结论、错字或旧CTA自动推广到新稿。

Gary轻修时，原钩子、句式、因果链、反差和排比都是需要保留的结构，不只保留论点或段落数。用户要求“只改词／不改框架”时，以该限制优先于下文通用的换节奏、补细节、重组等建议；没有必要改的原句不动。Gary千川文稿的词级窄修与结果导向边界，见[Gary表达参考的千川校准](references/gary-voice.md#千川轻修校准2026-11-06)；仅千川用途或用户明确调用这套尺度时使用，不接管普通自然流长稿。

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
