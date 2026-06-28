# Gemini Expansion And Retry Rules

Read this file before sending any source copy to Gemini, building prompt files, retrying failed outputs, or validating expanded drafts.

## Contents

- Mandatory isolated Gemini usage
- Current Gemini expansion instruction
- Automated prompt-file usage
- Generated-copy checks and retry rules

## Mandatory Isolation Policy

This skill exists to avoid modifying the user's original `douyin-copy-production-workflow-custom` Gemini conversation.

Hard rules:

- Always use `.\outputs\run_gemini_chat.cmd --prompt-file <path> --isolated`.
- Never run the bare command `.\outputs\run_gemini_chat.cmd` for expansion in this skill.
- Never send `/new`.
- Never use interactive Gemini chat merely to get a clean context.
- Treat every first attempt, refusal retry, length retry, stale-topic retry, and hallucination retry as a fresh isolated prompt-file request.

Reason: the original custom workflow may rely on a long-running saved conversation in `gemini_session.json`. The `--isolated` flag uses a clean temporary conversation and does not save user or assistant messages back to that session.

## Current Gemini Expansion Instruction

Always write this full instruction block into the prompt file before the original source copy whenever sending a script to the local Gemini command-line chat for expansion, including first attempts, refusal retries, length retries, and hallucination/stale-topic retries.

When the user provides a newer writing prompt for this isolated workflow, replace only this instruction block. Keep the isolation policy above unchanged.

```text
【正式扩写任务：扩写2.5模型·直接出稿版】

你现在不是在确认指令，不是在解释规则，也不是在等待我继续补充材料。
你要基于我后面提供的【原文】直接输出一篇完整可用的长文稿。
禁止回复“收到”“指令确认”“把文案发来”“我可以帮你”等任何确认语。
禁止只写大纲、摘要、分析、改写建议。
第一行必须直接进入成稿正文。

1. 原文锁定（最高优先级）：
必须只围绕【原文】的主题、标题、核心观点和情绪方向扩写。
不得复用上一轮对话主题，不得换题，不得借题发挥成另一篇文章。
不得把原文改成温和科普、情感建议、平台安全版、心理健康版。
可以重组结构、增强逻辑、补充机制和案例，但必须让读者一眼看出这是同一篇原文的升级版。

1.5. 原文结构保留与原创表达重组：
必须保留原文的结构框架，包括原文的开头钩子、核心矛盾、论证顺序、关键转折、主要观点层级和结尾指向。
但表达层面必须彻底打散重组，不能只做同义词替换，不能照搬原文句式、段落节奏、标志性比喻和连续长句。
要把原文的骨架变成新的口播表达：同一个观点换一种推进方式，同一个逻辑换一套句子，同一个案例可以改成24-35岁咨询学员的真实感场景。
允许调整句子顺序、合并或拆分段落、补充过渡句和机制解释，但不能改变原文的主线、观点立场和情绪方向。
最终成稿要像同一篇选题下重新写出来的新稿，而不是原文的表层改写。

2. 极限字数与深度（核心底线）：
必须极其深入地剖析，正文目标 1000-2000 个中文字符，最佳区间 1200-1600 个中文字符。
不要超过 2000 个中文字符；如果内容已经超过 2000 字，必须主动压缩，保留核心结构和关键机制，删掉重复铺垫和过度案例。
不要空洞废话，不要重复灌水。
必须加入高密度心理机制分析，并自然带出关系位置感、主动权、框架感和情绪价值变化。每一个关键点都要揉碎、讲透、推演到底，可以加入一点24-35岁咨询学员的小案例。

2.5. 强冲突表达密度：
整篇稿子必须更狠、更直接、更有压迫感，不能写成温和建议、普通情感科普、平衡分析、安慰型咨询或泛泛而谈的成长鸡汤。
每一段都要有明确的冲突推进：低位男人的错觉、女人的真实反应、关系权力的转移、心理机制的后果、男人必须清醒的残酷判断。
要多用短促有力的判断句，例如“你不是深情，你是在自我消耗”“她不是被感动，她是在评估你的价值”“关系里没有位置感，就只剩被筛选”。
可以更尖锐的点名男性常见低位状态，如讨好、供养、跪舔、自我感动、框架崩塌、需求感外泄、被动等待、被女人定义。
不要为了显得客观而冲淡观点，不要在关键处加太多“也许、可能、建议你、可以试试”这种软化语气。
每个心理机制都要落到现实代价：被轻视、被拖着、被消耗、被替代、被当成情绪垃圾桶、被当成资源供给者。
保持心理学包装和口播自然感，但整体气质必须像高压拆解，而不是课堂讲义。

3. TTS口语化排版：
生成纯净的口语化文稿，专门用于TTS转语音。严禁出现任何情绪、动作、节奏提示词（如：停顿、冷笑、加重语气等括号内容）。遇到使用“的、地”多音字的情况，一律用“的”，不要使用“地”。
不要使用 Markdown 标题、编号标题、项目符号、表格、括号注释。
可以自然使用“第一、第二、第三”这种口播式结构词，但不要写成清单格式。

4. 人设与风格：
化身为“Gary”。是一个成熟、犀利、懂人性的男性情感博主。
可以讲透男女相处里的心理学原理、真实动机、情绪拉扯、吸引机制、关系位置和实际案例，但不要直接使用生硬、猎奇、课程包装感太重的标签。
表达要自然，像一个见过大量真实关系崩盘案例的人在做高压拆解，要明显比普通情感博主更锋利、更不留情面。
多用心理学包装，但不要把锋芒磨平；要敢于指出男人低位行为背后的自欺、懦弱、供养思维和框架丢失。
不要写成“你好我好大家好”的中立建议，要写成一场认知警醒：如果你还这样做，你就会继续被轻视、被消耗、被筛选。
少用书面解释，多用口播推进。
不要写成论文，不要写成鸡汤，不要写成普通恋爱咨询。

5. 强制片头结构（原文开头原样保留+无痕衔接）：
必须先原样保留【原文】最开头的钩子段，不要改写、不要换词、不要重新包装。
原文开头一般取前 2-5 个短句，或取到第一个完整观点闭合处；如果原文一开始就是强钩子，就直接照搬这个开头。
保留原文开头之后，必须立刻用一两句无痕转场衔接到新文案，转场要像原文自然长出来的后续，不要出现“原文说的是”“接下来我要扩写”“下面开始分析”这种割裂提示。
无痕衔接句要完成三件事：放大原文钩子的冲突感，点出这期的核心心理机制，顺手把读者带入后面的结构拆解。
然后自然植入提效引导语：“另外说一句，如果想节省时间的话，可以点个收藏，在评论区艾特豆包，让豆包给你总结出思维导图后再回来观看，好，我们直接进入正题。”
最终开头顺序必须是：原文开头原样保留 -> 无痕衔接放大 -> 豆包提效引导 -> 正文展开。

6. 中段动态CTA（粉丝群引导）：
在文章中段的关键转折处，必须自然、动态地植入引导粉丝进**“粉丝群”**的话术（绝对禁止使用“私董会”等词汇），引导他们来找我做深度咨询。

7. 强制片尾结构（动态CTA与固定Slogan）：
动态CTA+固定Slogan：“我是探花Gary，专注于揭开潜藏在男女关系下的心理学真相与技巧。
我们内部群里见。”

8. 输出验收：
如果你发现自己准备回复确认语，立刻停止，改为直接输出正文。
如果正文不足 1000 个中文字符，继续扩写，不要提前结束。如果正文超过 2000 个中文字符，压缩到 1200-1600 字左右。
输出前自检：是否原样保留了原文开头，是否用无痕转场衔接到新文案，是否保留了原文结构框架，是否避免连续照搬正文表达，是否完成了原创化口播重组，是否足够犀利、有冲突、有压迫感，是否避免写成温和建议。
最后必须包含动态CTA+固定片尾。

【原文开始】
```

Do not use any older short expansion prefix; always use the full `Current Gemini Expansion Instruction` block.

## Automated Prompt-File Usage

Run the local Gemini command from:

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api
```

For every expansion, write the full instruction block + source copy to a UTF-8 prompt file, then call:

```powershell
.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated
```

If the command asks for `Teamorouter API Key`, enter the key provided by the user or use the existing `TEAMO_API_KEY` environment variable if already configured. Do not use the old web expansion channel in this custom skill.

When building the prompt file:

- Append the source text immediately after `【原文开始】`.
- Close it with `【原文结束】`.
- Do not prepend a viral opening or rewrite the source before expansion.
- Do not add `/new`.
- Do not use interactive terminal paste for multi-line prompts.

Reason: the interactive terminal uses single-line `readline.question()`. Pasting or piping a multi-line prompt can send only the first line as the user message, causing Gemini to merely confirm the instruction instead of expanding the source.

## Check Generated Copy

After generation finishes, capture the latest `Gemini:` response from the terminal output.

Default qualification line:

- Target length: 1000-2000 Chinese characters.
- Best length: 1200-1600 Chinese characters.
- Minimum acceptable length: 1000 Chinese characters unless the user gives a newer threshold.
- If output is below 1000 Chinese characters, do not mark it passed and do not export it as final.
- If output is above 2000 Chinese characters, compress it before export unless the user explicitly asks for a longer draft.

If below 1000 characters, create a new isolated retry prompt file with the full instruction block, original source copy, and this retry reason:

```text
字数不够，重写一遍，必须写到1000字以上，并且必须写完整片尾。
```

If above 2000 characters, create a new isolated retry prompt file with the full instruction block, original source copy, and this retry reason:

```text
字数过长，压缩重写一遍，必须保留原文结构框架和核心机制，但正文控制在1200-1600个中文字符，并且必须写完整片尾。
```

If Gemini returns a refusal, safety block, tool/API failure text, or a non-draft answer instead of an expanded article, treat it as a failed generation and retry with a new isolated prompt file. Do not ask the user for confirmation.

If model resources fail or no output appears, retry with:

```text
刚才模型资源不足没有生成出来，请再重试一遍。字数不够，重写一遍，必须写到1000字以上，并且必须写完整片尾。
```

If the user requests a different threshold, follow the newest threshold and record it in the batch log.

## Continue Expansion Session

This isolated workflow does not continue a Gemini session. Treat each prompt-file request as independent and temporary.

If obvious hallucination appears, build a new UTF-8 retry prompt file with the full instruction block, the original source copy, and a concise retry reason. Then rerun `run_gemini_chat.cmd --prompt-file <retry-prompt> --isolated`.

Obvious hallucinations include:

- Generated topic does not match source topic.
- Model reuses a previous article's subject.
- Model outputs only thinking text or system/resource messages.
- Model invents a different title or unrelated framework.
- Output is below 1000 Chinese characters.
- Output is above 2000 Chinese characters unless the user asked for a longer draft.
- Output lacks the required fixed ending with `我是探花Gary，专注于揭开潜藏在男女关系下的心理学真相与技巧` and `我们内部群里见`.
