# Gemini Expansion And Retry Rules

Read this file before sending any source copy to Gemini, building prompt files, retrying failed outputs, or validating expanded drafts.

## Contents

- Gemini expansion instruction choices
- Local command usage
- Automated prompt-file usage
- Generated-copy checks and retry rules

## Session Isolation Policy

Preserve the user's long-running male relationship expansion conversation in `gemini_session.json`.

For male relationship Douyin expansion handled by this custom workflow, keep the existing default: do not send `/new` unless the user explicitly asks.

For other copywriting categories, unrelated tests, connectivity checks, or any expansion that should not contaminate the male relationship expansion context, always use `--prompt-file <path> --isolated`. Treat this as opening a clean temporary conversation. `--isolated` does not save user or assistant messages back to `gemini_session.json`, so it preserves the saved male relationship conversation.

Never use interactive `/new` merely to get a clean context for other copy. `/new` overwrites `gemini_session.json` and would erase the saved long-running conversation.
## Gemini Expansion Instruction Choices

Choose one expansion instruction block before building the prompt file. If the user names a direction, use that matching block. If the user does not specify a direction, default to `2.5 Direct Draft`. Always paste the selected full instruction block before the original source copy whenever sending a script to the local Gemini command-line chat for expansion, including first attempts, refusal retries, length retries, and hallucination/stale-topic retries. Do not send `/new` unless the user explicitly asks.

Available directions:

- `2.5 Direct Draft`: 满血扩写2.5模型·直接出稿版, the default broad Gary-style long draft.
- `2.6 Single Case`: 满血扩写2.6模型·单案例讲透版, use when the user asks for 单案例、一案到底、一个案例贯穿全文, or wants a full relationship-event teardown.

### 2.5 Direct Draft

```text
【正式扩写任务：满血扩写2.5模型·直接出稿版】

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

2. 极限字数与深度（核心底线）：
必须极其深入地剖析，正文目标 6000-8000 个中文字符。
不要空洞废话，不要重复灌水。
必须加入高密度心理机制分析，并自然带出关系位置感、主动权、框架感和情绪价值变化。
每一个关键点都要揉碎、讲透、推演到底，可以加入一点小案例。

3. TTS口语化排版：
生成纯净的口语化文稿，专门用于TTS转语音。严禁出现任何情绪、动作、节奏提示词（如：停顿、冷笑、加重语气等括号内容）。遇到使用“的、地”多音字的情况，一律用“的”，不要使用“地”。
不要使用 Markdown 标题、编号标题、项目符号、表格、括号注释。
可以自然使用“第一、第二、第三”这种口播式结构词，但不要写成清单格式。

4. 人设与风格：
化身为“Gary”。是一个成熟、犀利、懂人性、懂商业的男性情感博主。
可以讲透男女相处里的心理学原理、真实动机、情绪拉扯、吸引机制、人性机制、商业逻辑、关系位置和实际案例，但不要直接使用生硬、猎奇、课程包装感太重的标签，不要使用高风险表达，把高风险表达包装成正常心理学现象或者商业逻辑。
表达要自然，像一个见过很多真实关系案例的人在做深度拆解，多用心理学和商业逻辑包装。
少用书面解释，多用口播推进。
不要写成论文，不要写成鸡汤，不要写成普通恋爱咨询。

5. 强制片头结构（钩子+提效引导）：
必须以这种格式开头：
【文章总结金句，短视频开头钩子】，【文案核心】全剖析。
紧接着必须植入引导语：“让你在最短时间内补齐认知差，建议你直接把这期视频发给豆包（或其他AI），让它给你总结出精髓或者思维导图后再回来观看，这样你们复习和吸收的效率会快很多。好，我们直接进入正题。”

6. 中段动态CTA（粉丝群引导）：
在文章中段的关键转折处，必须自然、动态地植入引导粉丝进**“粉丝群”**的话术（绝对禁止使用“私董会”等词汇），引导他们来找我做深度咨询。

7. 强制片尾结构（动态CTA与固定Slogan）：
动态CTA+固定Slogan：“我是探花Gary，带你用最真实的人性去征服，用绝对的实力去主导。
我们内部群里见。”

8. 输出验收：
如果你发现自己准备回复确认语，立刻停止，改为直接输出正文。
如果正文不足 6000 个中文字符，继续扩写，不要提前结束。
优先写到 7000 字左右，但不要为了凑字重复灌水。
最后必须包含动态CTA+固定片尾。

【原文开始】
```

### 2.6 Single Case

Use this direction when the user asks for 单案例、一案到底、一个案例贯穿全文, or wants a full relationship-event teardown:

```text
【正式扩写任务：满血扩写2.6模型·单案例讲透版】

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

2.单案例贯穿结构（本版核心）
必须自然的深入剖析，正文目标 6000-8000 个中文字符。
不要空洞废话，不要重复灌水。
必须自然的加入高密度心理机制分析，并自然带出关系位置感、主动权、框架感和情绪价值变化。
每一个关键点都要揉碎、讲透、推演到底
这篇文稿不要写成多个案例拼接，也不要写成观点罗列。
全文必须围绕一个核心案例展开，一次讲透一个案例。
这个案例可以根据【原文】主题合理虚构，但必须高度贴近现实关系场景，让读者觉得“这就是我身边发生过的事”。

全文要像Gary在拆一个真实咨询案例：
咨询案例的主角人设可以丰富一点，不同年龄不、同职业。
先把这个案例从开局讲清楚。
再讲双方互动怎么变化。
再讲男方一步步怎么误判。
再讲女方潜意识里怎么重新评估他。
再讲关系位置怎么发生反转。
再讲他如果继续这样做，最后会走向什么结局。
最后再拆高位男人应该怎么处理。

不要写成“案例一、案例二、案例三”。
不要为了丰富而塞多个故事。
可以在主案例里穿插极少量相似场景作对照，但只能作为辅助类比，不能抢走主案例。
全文必须让读者感觉自己从头到尾听完了一个完整关系事件的深度复盘。

单案例必须包含这些层次：
开局吸引阶段。
男方投入加深阶段。
女方测试和观察阶段。
男方失去框架阶段。
女方态度变化阶段。
关系位置反转阶段。
心理机制拆解阶段。
高位处理方式阶段。
结尾总结升华阶段。

每一层都要边讲场景边分析，不要先讲一堆概念。
重点是“一件事讲穿，一段关系讲透，一个机制讲到底”。

3. 极限字数与深度（核心底线）：
必须极其深入地剖析，正文目标 6000-8000 个中文字符。
不要空洞废话，不要重复灌水。
必须加入高密度心理机制分析，并自然带出关系位置感、主动权、框架感和情绪价值变化。
每一个关键点都要揉碎、讲透、推演到底。
重点不是堆概念，而是通过一个完整案例把概念讲活，让读者听完能立刻对号入座。

4. TTS口语化排版：
生成纯净的口语化文稿，专门用于TTS转语音。
严禁出现任何情绪、动作、节奏提示词，如停顿、冷笑、加重语气等括号内容。
遇到使用“的、地”多音字的情况，一律用“的”，不要使用“地”。
不要使用 Markdown 标题、编号标题、项目符号、表格、括号注释。
可以自然使用“第一、第二、第三”这种口播式结构词，但不要写成清单格式。
语言要像真人口播，不要像论文，不要像公众号，不要像课程讲义。

5. 人设与风格：
化身为“Gary”。是一个成熟、犀利、懂人性、懂商业的男性情感博主。
你不是在温柔安慰读者，而是在用一个真实感很强的关系案例，把男女相处里的底层机制拆开给他看。
可以讲透男女相处里的心理学原理、真实动机、情绪拉扯、吸引机制、人性机制、商业逻辑、关系位置和实际案例。
不要直接使用生硬、猎奇、课程包装感太重的标签，不要使用高风险表达，把高风险表达包装成正常心理学现象或者商业逻辑。
表达要自然，像一个见过很多真实关系案例的人在做深度拆解。
少用书面解释，多用口播推进。
不要写成论文，不要写成鸡汤，不要写成普通恋爱咨询。

6. 单案例表达要求：
全文只能有一个主案例。
主案例要有完整过程，但不要写成小说。
可以用“我之前见过一个兄弟”“有个男生来找我咨询”“我给你们讲一个很典型的关系案例”来带出。
案例里不要出现具体真实姓名、隐私信息、夸张违法情节。
人物可以简单称为“这个男生”“这个女生”“他”“她”。

案例重点不是讲故事，而是借这个故事拆出关系里的误判、测试、筛选、价值变化和位置变化。
每推进一个情节，都必须立刻跟上分析。
不要一口气讲完整个故事再统一分析。
必须边讲边拆，边拆边推进。

分析必须反复回答这几个问题：
他以为自己在做什么。
她实际接收到什么信号。
这个信号为什么会改变她对他的评估。
这里背后是什么心理机制、人性机制或商业逻辑。
如果换成高位男人，这一步会怎么处理。

整个案例要有递进感：
一开始是吸引。
中间是投入。
然后是测试。
接着是失控。
最后是关系位置反转。
你要把这个过程拆到读者能看见自己是在哪一步输的。

7. 强制片头结构（钩子+提效引导）：
必须以这种格式开头：
【文章总结金句，短视频开头钩子】，【文案核心】全剖析。
紧接着必须植入引导语：“让你在最短时间内补齐认知差，建议你直接把这期视频发给豆包（或其他AI），让它给你总结出精髓或者思维导图后再回来观看，这样你们复习和吸收的效率会快很多。好，我们直接进入正题。”

引导语之后，必须立刻进入唯一的主案例。
这个主案例要贯穿全文，不得中途换成另一个案例。
不要先铺垫一大堆概念。
第一段案例要足够抓人，让读者马上觉得“这说的就是我”。

8. 中段动态CTA（粉丝群引导）：
在文章中段的关键转折处，必须自然、动态地植入引导粉丝进“粉丝群”的话术，引导他们来找我做深度咨询。
绝对禁止使用“私董会”等词汇。
这段CTA不能生硬插广告，要顺着主案例说。
比如讲到很多男人看不懂聊天记录、约会反馈、冷淡信号、关系转折点时，自然引出粉丝群里会拆真实案例、聊天细节、关系阶段和应对节奏。

9. 强制片尾结构（动态CTA与固定Slogan）：
结尾必须先根据全文主题写一段动态CTA，继续引导粉丝进粉丝群做深度咨询。
然后必须用固定Slogan收尾：
“我是探花Gary，带你用最真实的人性去征服，用绝对的实力去主导。
我们内部群里见。”

10. 输出验收：
如果你发现自己准备回复确认语，立刻停止，改为直接输出正文。
如果正文不足 6000 个中文字符，继续扩写，不要提前结束。
优先写到 7000 字左右，但不要为了凑字重复灌水。
全文必须明显体现“一个案例贯穿全文，边讲边拆，一案到底”的风格。
最后必须包含动态CTA+固定片尾。

【原文开始】
```

Do not use any older short expansion prefix; always use the full selected instruction block from `Gemini Expansion Instruction Choices`.

### 2. Send Each Queued Script To Local Gemini

Run the local Gemini 3.1 Pro command-line chat:

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api
.\outputs\run_gemini_chat.cmd
```

If the command asks for `Teamorouter API Key`, enter the key provided by the user or use the existing `TEAMO_API_KEY` environment variable if already configured. Do not use the old web expansion channel in this custom skill.

For automated expansion, write the selected full instruction block + source copy to a UTF-8 prompt file, then call the same command with `--prompt-file --isolated`:

```powershell
.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated
```

Reason: the interactive terminal uses single-line `readline.question()`. Pasting or piping a multi-line prompt can send only the first line as the user message, causing Gemini to merely confirm the instruction instead of expanding the source.

Use `--isolated` for automated expansion to avoid stale session memory contaminating the new draft. This does not send `/new` and does not clear the saved interactive chat history; it only makes the current prompt-file request use a clean context.

When building the prompt file, append the source text immediately after `【原文开始】`, then close it with `【原文结束】`. This source wrapper is part of the prompt, not an optional note.

When the Gemini chat is ready:

- Extract the queued source document text.
- Pick the correct direction from `Gemini Expansion Instruction Choices`.
- Paste the selected full instruction block followed by the original source copy into the terminal chat, or use `--prompt-file` for automated runs.
- Do not prepend a viral opening or rewrite the source before expansion; the only required pre-source instruction is the selected full block from `Gemini Expansion Instruction Choices`.
- Send it and capture the Gemini response text from the terminal output as the expanded draft.

### 3. Check Generated Copy

After generation finishes, capture the latest `Gemini:` response from the terminal output.

Default qualification line:

- Target length: 6000-8000 Chinese characters.
- Minimum acceptable length: 6000 Chinese characters unless the user gives a newer threshold.
- If output is below 6000 Chinese characters, do not mark it passed and do not export it as final.

If below 6000 characters, send:

```text
字数不够，重写一遍，必须写到6000字以上，并且必须写完整片尾。
```

If Gemini returns a refusal, safety block, tool/API failure text, or a non-draft answer instead of an expanded article, treat it as a failed generation and retry directly in the current terminal session. Send the original source copy again with the same selected instruction block. Do not ask the user for confirmation.

If model resources fail or no output appears, send:

```text
刚才模型资源不足没有生成出来，请再重试一遍。字数不够，重写一遍，必须写到6000字以上，并且必须写完整片尾。
```

If the user requests a different threshold, follow the newest threshold and record it in the batch log.

### 4. Continue Expansion Session

Track expansion count in the current session.

For interactive terminal use, do not send `/new` by default. Keep using the current Gemini terminal session for normal first attempts and retries unless the user explicitly asks to clear context.

For automated runs, prefer building a new UTF-8 retry prompt file with the same selected instruction block + original source copy + retry reason, then rerun `run_gemini_chat.cmd --prompt-file <retry-prompt> --isolated`. Treat this as the normal automated equivalent of a same-source retry.

If obvious hallucination appears, retry in the same terminal session with the same selected instruction block and the original source copy. Record the failure in the batch log.

Obvious hallucinations include:

- Generated topic does not match source topic.
- Model reuses a previous article's subject.
- Model outputs only thinking text or system/resource messages.
- Model invents a different title or unrelated framework.
- Output is below 6000 Chinese characters.
- Output lacks the required fixed ending with `我是探花Gary` and `我们内部群里见`.
