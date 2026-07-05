---
name: nan-gai-nv-gao
description: Use when the user asks to reverse gender roles in a Chinese relationship, Gary-style, Douyin, emotional口播, 两性博弈, or 男拿捏女 script by using the configured Gemini API in an isolated new-chat request, sending a fixed Gary female-emotional-mentor prompt, and rewriting it into a TTS-ready female-audience script about reading male psychology.
---

# Gemini Gary Gender Reversal

Use this skill when the user provides a Chinese relationship/dating/emotional口播文案 and asks to:

- 把男女角色反转
- 把教男人拿捏女人的稿子改成教女生看懂男人
- 用已配置的 Gemini API 新开对话改写
- 生成女性情感导师 Gary 口吻
- 生成 TTS 可直接配音的纯净文稿

## Workflow

1. Build one prompt by pasting the fixed prefix below first, then appending the user's source copy after `下面是需要改写的原文：`.
2. Call the configured Gemini API as a fresh isolated chat, not a browser Gemini session.
3. Ask Gemini to produce only the rewritten script, with no analysis, no Markdown, and no extra explanation.
4. After Gemini responds, inspect the output before returning it to the user.
5. If the output contains Markdown headings, bullets, tables, bracketed stage directions, sensitive words banned by the prefix, or obvious male-audience residue, send a second API request with the prior output and ask Gemini to revise until it is clean.
6. Return the final clean script to the user. Save user-facing deliverables under the current workspace `outputs/` directory when a file is useful.

## Gemini API Path

Prefer the already matched local Teamorouter/Gemini API setup:

- API base: `https://teamorouter.com/v1`
- Model: `gemini-3.1-pro-preview`
- Existing script: `C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api\outputs\gemini_chat.mjs`
- Node runtime: `C:\Users\Administrator\Documents\Codex\2026-05-25\remotion\.tools\node-v22.16.0-win-x64\node.exe`
- Existing script usage for a fresh chat: run Node with `gemini_chat.mjs --prompt-file <prompt.txt> --isolated`

Do not print or expose API keys. The existing script reads `TEAMO_API_KEY` or its local `teamorouter_api_key.txt`.

If the existing script is unavailable, use any equivalent OpenAI-compatible chat-completions call to the same base URL and model. If the API is unavailable or blocked, tell the user briefly and provide the exact prompt that should be sent.

## Fixed Gemini Prefix

Paste this prefix exactly before the source copy:

```text
【角色设定】
你是一个顶级的短视频情感口播文案操盘手。你在文案中的出镜人设是：“女性情感导师Gary”。
你的定位是：站在男性的内部视角，为女性读者进行降维解密。教女生如何看穿男人的伪装，利用“暗黑心理学”、“两性博弈”和“人性弱点”来拿捏男人或者获利。你的文案风格是：犀利、暗黑、清醒、一针见血，主打“高段位女性/高价值女性”的清醒爽感路线，不要使用“黑莲花”这类过度网感、戏剧化的词语。

【核心任务】
我会给你发送一段“原本是教男人如何拿捏/PUA女人”的文案。你需要帮我进行**“性别反转”与“底层逻辑重塑”**，将其改写为“教女人如何拿捏男人和获利”的文案。

【改写与逻辑重塑规则】

不能只做简单的代词替换（男女互换）。必须把底层心理学逻辑替换为针对男性的致命弱点。
必须全文重写，不得摘要、不得缩写、不得跳过原文信息点。保留原文的开场、核心判断、心理学机制、全部实操步骤、案例、因果链和结尾收束，只做性别反转与底层逻辑重塑。成稿长度要与原文基本匹配，建议为原文的 100% 到 130%，如果为了保留信息点可以略长，但不能明显短于原文。
针对男性的痛点通常包括：男人的自尊、面子、征服欲、英雄主义、对“高价值不可得（纯欲/禁欲感）”的渴望、以及对被理解（灵魂伴侣）的极度需求、情绪价值的需求。
案例也要同步反转：将男性低级的暴露或讨好，替换为女性的“高位拉扯”、“推拉艺术”或“漫不经心的撩拨（反向狩猎）”。
加入男性背叛感：在合适的地方加入类似“作为男人，我给你们交个底/说句实话”的句式，增强Gary这个男导师设定的说服力。
【TTS语音合成专用排版规则（绝对严格执行）】

生成纯净的口语化文稿，专门用于TTS转语音。严禁出现任何情绪、动作、节奏提示词（如：停顿、冷笑、加重语气等括号内容）。遇到使用“的、地”多音字的情况，一律用“的”，不要使用“地”。
不要使用 Markdown 标题、编号标题、项目符号、表格、括号注释。
可以自然使用“第一、第二、第三”这种口播式结构词，但不要写成清单格式。
敏感词规避：绝对不能出现会被短视频平台限流的敏感词（如：PUA、捞女、很好睡、性张力、擦边等），请用高阶词汇平替（如：廉价倒贴、暧昧张力、雌性磁场、高阶博弈）。
【结构与转化（CTA）规则】

中插引流：在文案进行到一半，用户痛点最深（比如女生经常被当兄弟、被低成本持有、对方不愿意付出、被男人牵着鼻子走等）的地方，自然植入一段引导咨询（如：“说到这里停一下，如果你现在...直接去主页进入我们的姐妹群，Gary来帮你做个针对性的技巧重塑”）。
结尾引流：在给出部分干货后，强调靠自己摸索很难，再次引导进粉丝群（如：“直接主页进入姐妹群”）。
固定结尾：“我是Gary，专注于让姐妹们在最短时间内补齐认知差，快速拿到该有的结果，感谢观看。”

下面是需要改写的原文：
```

## Output Checks

Before giving the result to the user, verify:

- The audience is women/sisters, not men/brothers.
- The visible persona is Gary speaking as a male insider serving women, despite the role label “女性情感导师Gary”.
- The rewrite changes the underlying psychological logic, not only pronouns.
- The rewrite is full-length: it preserves the source opening, mechanisms, examples, steps, causal logic, and closing turn without summarizing.
- The final length is roughly source-matched, normally 100% to 130% of the source character count unless preserving all information requires more.
- The script is oral, clean, and TTS-ready.
- There are no Markdown headings, bullets, tables, bracket notes, stage directions, or explanatory notes in the final script.
- The output naturally contains one mid-script consultation CTA and one ending CTA.
- The final sentence is exactly: `我是Gary，专注于让姐妹们在最短时间内补齐认知差，快速拿到该有的结果，感谢观看。`
