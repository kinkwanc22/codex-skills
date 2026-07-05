# Gemini Expansion And Retry Rules

Read this file before sending any source copy to Gemini, building prompt files, retrying failed outputs, or validating expanded drafts.


## Female Edition Prompt Override

This reference file is copied from the male Gary workflow. For this female edition, before building any 2.5 or 2.6 prompt file, semantically apply the following override to the selected full prompt block without shortening it:

```text
【女性版扩写覆盖层】
本轮是女性受众版本。
你要面向女性观众、女性学员、女性咨询案例输出，不要默认写给“兄弟”或男性追女生受众。
核心视角从“男人如何追女生、征服女人、拿回追求主动权”切换为“女人如何看懂男人、筛选男人、守住情绪主权、建立高位框架、识别投入和关系位置”。
案例主角默认是女性学员或女性咨询者，除非原文明确要求男性主角。
可以讲透男人心理、男性动机、暧昧信号、投入成本、承诺意愿、冷淡拉扯、回避和低质量关系筛选。
保持Gary式成熟、犀利、懂人性、懂商业和关系博弈的口播风格，但称呼、案例、痛点、结果必须自然转为女性向。
不要把女性观众写成被动受害者，要写成能识别、筛选、定价、止损、主导自己情绪秩序的人。
固定片尾品牌如用户未另行指定，仍可保留“探花Gary”。
【女性版扩写覆盖层结束】
```

The override is a semantic layer, not a replacement for the full 2.5/2.6 prompt. Keep all length, TTS, no-backend-trace, CTA, retry, and 2.7 fusion rules from the original blocks unless they conflict with this female-facing lens.

## Contents

- Gemini expansion instruction choices
- Local command usage
- Automated prompt-file usage
- Generated-copy checks and retry rules

## Session Isolation Policy

Use the female edition as a separate workflow from the male Gary expansion workflow.

For automated female-facing Douyin expansion, call the Mac runner with `--isolated` by default:

```bash
./scripts/run_gemini_chat.sh --prompt-file work/prompt.txt --isolated --output-file work/expanded.txt
```

The current Mac runner is stateless by default and accepts `--isolated` for compatibility, so this does not clear or overwrite any saved male workflow history. Do not send `/new` unless the user explicitly asks to clear a session.

For unrelated tests or non-female categories, also use `--isolated`.
## Gemini Expansion Instruction Choices

Choose one expansion instruction block before building the prompt file. If the user names a Gemini expansion direction, use that matching block. If the user does not specify a direction, default to `2.5 Direct Draft`. Always paste the selected full instruction block before the original source copy whenever sending a script to the local Gemini command-line chat for expansion, including first attempts, refusal retries, length retries, and hallucination/stale-topic retries. Do not send `/new` unless the user explicitly asks.

Exception: `2.7 Codex Fusion` is not a Gemini prompt-file direction. When the user asks for 2.7/fusion, generate Gemini 2.5 and Gemini 2.6 first, then write the final 2.7 body locally in Codex from those two accepted drafts.

Available directions:

- `2.5 Direct Draft`: 满血扩写2.5模型·直接出稿版, the default broad Gary-style long draft.
- `2.6 Single Case`: 满血扩写2.6模型·单案例讲透版, use when the user asks for 单案例、一案到底、一个案例贯穿全文, or wants a full relationship-event teardown.
- `2.7 Codex Fusion`: Codex本地成稿融合版, use when the user asks for 2.7、融合版、把2.5和2.6融合、机制密度加案例线, or wants the same style as the approved 316 body-signal fusion draft. Do not send this to Gemini as a third source-to-draft expansion; first generate and validate 2.5 and 2.6 with Gemini, then have Codex fuse the two accepted drafts locally.

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
可以重组结构、增强逻辑、补充机制和案例。

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
可以讲透男女相处里的心理学原理、真实动机、情绪拉扯、吸引机制、关系位置和实际案例，但不要直接使用生硬、猎奇、课程包装感太重的标签，可以狠一点，但把高风险表达包装成正常心理学现象或者商业逻辑。
表达要自然，像一个见过很多真实关系案例的人在做深度拆解，少用书面解释，多用口播推进。
不要写成论文，不要写成鸡汤，不要写成普通恋爱咨询。

5. 强制片头结构（钩子+提效引导）：
必须以这种格式开头：
【文章总结金句，短视频开头钩子】，【文案核心】全剖析。
紧接着必须植入引导语：“另外说一下，如果想节省时间的话，可以点个收藏，在评论区艾特豆包，让豆包给你总结出精髓或者思维导图后再回来观看，这样子你们复习和吸收的效率会快很多。好，我们直接进入正题。”

6. 中段动态CTA（粉丝群引导）：
在文章中段的关键转折处，必须自然、动态地植入引导粉丝进**“粉丝群”**的话术（绝对禁止使用“私董会”等词汇），引导他们来找我做深度咨询。

7. 强制片尾结构（动态CTA与固定Slogan）：
自然、动态地植入引导粉丝进**“粉丝群”**的话术（绝对禁止使用“私董会”等词汇），引导他们来找我做深度咨询+固定Slogan：“我是探花Gary，我们内部群里见，感谢观看”

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
案例的主角优先保持为Gary的咨询客户、学员。注意，学员只是身份和信任背书，不是固定剧情模板。不要默认写成“男方低位失败 -> 找Gary咨询 -> Gary指导 -> 女方主动 -> 最终翻盘”的流水线。
案例形式必须根据【原文】灵活变化，不要每篇都写成同一种固定模板。可以是学员正在参加饭局、酒局、约会、相亲、公司聚会的现场局；也可以是学员发来一段聊天记录，Gary逐句拆解；也可以是学员已经做对了某个动作，Gary拆他为什么有效；也可以是学员失败了，但这篇只拆崩盘原因，不强行大团圆翻盘；也可以是学员在长期关系里遇到冷淡、吵架、边界、分手边缘；也可以是学员在群里发来截图或语音复盘，Gary拆关键节点；也可以是学员不是来“求救”，而是拿一个正在发生的关系现场给Gary复盘。全文仍然只能围绕一个主案例展开，不能写成多个案例合集。
案例冲突必须从【原文】最核心的心理机制、技巧、信号、步骤或情绪矛盾里长出来。案例形式可以变化，但不能为了变化形式，把原文主题替换成泛关系场景。比如原文讲补偿心理，案例就必须在人物的互动、投入、等待、补偿和关系账本里自然展开；原文讲肢体信号，案例就必须通过女生的具体动作、距离、眼神、触碰、停留和男方推进来讲；原文讲聊天技巧，案例就必须通过真实对话、回复节奏、话题推进和女方反馈来讲。
原文的技巧和核心思想不能被端出来当成一个“主题”或“课程模块”讲。它必须被人物自然做出来、说出来、反应出来，再由Gary顺着这个动作拆解。读者应该感觉自己在听一个真实案例，而不是听Gary先给定一个主题再找案例解释。
不要总是写成“男方一开始失败、后来崩盘、最后补救”的固定形式。案例可以自然一点，可以从一次成功的约会、一段正在升温的暧昧、一场现场指导、一次技巧练习、一段聊天复盘、一次关系窗口打开、一次女方主动释放信号、一次学员按原文技巧推进成功开始。只要全文仍然是一个主案例，并且边推进边讲解即可。

正式成稿前，必须先在内部根据原文机制选择一个案例入口，但不要把选择过程写出来。只能选一种入口，并让全文从这个入口自然展开：
1. 学员现场局：从饭局、约会、酒局、健身房、公司聚会、相亲现场切入，边发生边拆解。
2. 学员聊天记录复盘：从三到五轮真实感对话切入，通过每一句话拆出关系位置变化。
3. 学员成功样本拆解：不是失败后补救，而是一开始就拆一个做对的学员，他为什么能自然推进。
4. 学员女方视角反推：从女生的反应、犹豫、试探、主动靠近开始，反推男方做对了什么。
5. 学员失败崩盘型：允许男方失败，但重点不是补救爽文，而是拆清楚哪一步让关系坍塌。
6. 学员现场指导型：Gary可以参与指导，但不能写成“学员求助后照做翻盘”的流水线。指导可以是语音复盘、群里截图点评、线下聊天后的二次调整。
7. 学员长期关系切片型：不写追求阶段，而写暧昧、恋爱、冷淡期、吵架、分手边缘里的一个关键切片。
8. 学员反面教材型：可以没有大团圆翻盘，用一个失败案例讲清楚机制，结尾给出正确路径。

案例入口必须由原文机制决定：
原文讲聊天，就优先用学员聊天记录复盘。
原文讲约会，就优先用学员现场局。
原文讲废测，就优先用一次具体试探现场。
原文讲沉没成本，就优先用女方持续投入的过程。
原文讲筛选，就优先用相亲、社交局或多对象选择场景。
原文讲朋友圈，就优先用展示面和女生反馈场景。
原文讲长期关系，就优先用吵架、冷淡、边界、分手边缘场景。
原文讲底层认知合集，才允许使用完整咨询案例，但也必须换一个入口，比如饭局现场、聊天记录、女方视角反推、成功样本拆解或反面教材，禁止再写常规求助翻盘。

硬性禁止：禁止默认使用“男方一开始低位失败 -> 找Gary咨询 -> Gary让他断联或改变聊天 -> 女方主动 -> 关系翻盘”的固定结构。如果生成时发现自己正在写这个结构，必须立刻换成现场切片、聊天记录、女方视角、成功样本、反面教材或长期关系切片。

全文要像Gary在拆一个真实咨询案例，但不要机械套固定顺序。下面这些只是可选骨架，不是每篇必须逐项照抄：
咨询案例的主角人设可以丰富一点，有名字、不同年龄、不同职业。
可以从一个具体场景或具体动作切入，再带出这个学员在真实场景里怎么遇到、怎么判断、怎么操作、怎么得到反馈。
可以讲双方互动怎么自然变化，也可以讲学员如何把【原文】里的技巧用在具体动作里，边推进边解释女方潜意识为什么会这样反应。
可以拆男方误判，也可以拆他做对的地方、Gary现场纠偏的地方、女方释放窗口的地方、关系升温的地方。
可以讲如果继续低位会走向什么结局，但不要每篇都写成灾难预告；更重要的是结合【原文】技巧讲清楚正确处理为什么有效。
最后必须写到这个学员在Gary指导下调整或执行策略，并取得明确成功结果。成功结果必须贴合【原文】主题，比如女生重新主动、关系窗口重新打开、男方拿回主导权、约会顺利推进、冷淡关系升温、对方尊重边界、学员看懂信号后自然推进成功、学员用原文技巧拿到正反馈、男方成功撤离消耗关系并进入更高位状态等。不能只停留在“应该怎么做”的理论建议，必须让读者看到指导后的具体变化和正向结局。

不要写成“案例一、案例二、案例三”。
不要为了丰富而塞多个故事。
可以在主案例里穿插极少量相似场景作对照，但只能作为辅助类比，不能抢走主案例。
全文必须让读者感觉自己从头到尾听完了一个完整关系事件的深度复盘。

单案例要自然包含这些功能层，不要求用固定顺序，也不要写成标题清单：
真实场景进入。
核心技巧或机制通过人物动作、对话和反馈自然出现。
学员的判断、操作或误判。
女方反馈和潜意识评估。
关系位置、主动权、框架感或情绪价值的变化。
心理机制拆解。
Gary指导下的处理方式。
学员执行后的明确成功结果。
结尾总结升华。

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
禁止出现“原文说”“原文里”“这篇原文”“原文提到”“文案里”“这篇文案”“提示词要求”“根据原文”等后台痕迹表达。成稿必须像Gary直接在讲这一期内容，而不是在评论或改写一篇原文。
如果需要承接来源观点，必须自然改写成口播表达，比如“这期我们讲的是”“刚才这个机制”“这个现象背后”“你要听懂这里”“这个案例里”，不要让听众感觉在听一篇改写说明。

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
可以用“我之前见过一个兄弟”“有个男生来找我咨询”“我给你们讲一个很典型的关系案例”来带出，但不要每篇都用求助式开场。也可以用“上个月有个学员在饭局里遇到一个局”“前几天群里有个学员发来一段聊天记录”“我有个学员做对了一个动作”“有个学员把一段长期关系搞崩了，问题就出在一个细节上”等场景式开场。
案例里不要出现具体真实姓名、隐私信息、夸张违法情节。
人物可以简单称为“这个男生”“这个女生”“他”“她”。

案例重点不是讲故事，而是借这个故事拆出【原文】里的技巧、信号、机制、误判、测试、筛选、价值变化和位置变化。但这些东西不能像知识点一样被生硬点名，必须从人物当下的动作、对话、表情、选择、反馈和关系变化里自然长出来。
每推进一个情节，都必须立刻跟上分析。
不要一口气讲完整个故事再统一分析。
必须边讲边拆，边拆边推进。
可以使用【原文】里的技巧、步骤、信号和判断标准来推动案例，不要把案例写成脱离原文的泛关系故事。不要说“这个主题讲的是”“这套机制是”“四个按钮分别是”这种课程讲义式表达；要说“你看她这个动作”“他这句话真正传递的信号”“这个时候女生接收到的不是A而是B”“所以他下一步才这样做”。

分析必须反复回答这几个问题：
他以为自己在做什么。
她实际接收到什么信号。
这个信号为什么会改变她对他的评估。
这里背后是什么心理机制、人性机制或商业逻辑。
如果换成高位男人，这一步会怎么处理。

整个案例要有递进感，但递进方式必须跟【原文】匹配。可以是“识别信号 -> 判断窗口 -> 使用技巧 -> 女方反馈 -> Gary纠偏 -> 成功推进”，也可以是“原本误判 -> 拆出机制 -> 调整动作 -> 关系升温”，还可以是其他更贴近原文的自然推进。不要每篇都写成吸引、投入、测试、失控、反转的固定套路。你要把这个过程拆到读者能看见自己应该在哪一步判断、怎么做、为什么有效。

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
最终正文不得出现“原文说”“原文里”“这篇原文”“原文提到”“文案里”“这篇文案”“提示词要求”“根据原文”等后台痕迹词；如出现，必须改写成自然口播再输出。

【原文开始】
```

### 2.7 Codex Fusion

Use this direction when the user asks for `2.7`, `融合版`, `2.5和2.6融合`, `机制密度加案例线`, or wants the same effect as the approved 316 body-signal fusion draft.

This is not a Gemini prompt. Do not send the original source to Gemini for a separate 2.7 draft. The required flow is:

1. Generate and validate a `2.5 Direct Draft` with Gemini.
2. Generate and validate a `2.6 Single Case` with Gemini.
3. Read both accepted body drafts locally in Codex.
4. Write the 2.7 body directly in Codex by fusing those two accepted drafts.

Codex fusion intent:

- Use the 2.6 draft as the main skeleton: keep its single-case throughline, scene order, character relationship, concrete actions, and real-time progression.
- Use the 2.5 draft as the pressure source: extract its sharpest judgments, mechanism density, human-nature logic, relationship-position language, wrong-path consequences, and high-pressure Gary voice.
- Do not average the two drafts. The correct shape is: 2.6 provides the spine, 2.5 provides the blade.
- Do not invent a brand-new case unless the 2.6 case is obviously off-topic, unusable, or violates the original source. If the 2.6 case is usable, preserve it.
- Do not produce a simple stitched collage. Rewrite into one smooth TTS-ready manuscript that sounds like it was written in one pass.

Fusion rules:

- Start from the 2.6 case opening and make it sharper with the best 2.5 hook or high-pressure opening judgment.
- At every major 2.6 scene beat, insert or rewrite with the strongest relevant 2.5 mechanism analysis.
- Keep the 2.6 story chronology clear: scene -> action/dialogue -> female feedback -> Gary interpretation -> next move.
- Strengthen weak 2.6 explanation with 2.5-style pressure: relation position, active power, frame, emotional reward/punishment, window timing, investment, value assessment, and business logic.
- Keep the 2.5's broad mechanism language only when it directly deepens the current scene. Remove generic or duplicated mechanism paragraphs.
- Preserve the 2.6 single-case feel. The 2.7 draft may contain brief comparisons, but they must serve the main case and must not become a multi-case article.
- Include at least one clear wrong-path consequence: if the man misses the signal, answers wrong, overexplains, rushes, or stays low-position, show how the woman will reinterpret him and how the relationship position collapses.
- Include at least one clear correct-path escalation: show how the man changes the action, wording, rhythm, boundary, or frame, and what concrete feedback he gets.
- Preserve the dynamic mid-article fan-group CTA and final dynamic CTA.
- End with exactly the fixed slogan: `我是探花Gary，我们内部群里见，感谢观看`

Output requirements:

- Target 7000-8500 Chinese characters. Minimum acceptable length is 6500 Chinese characters unless the user gives a newer threshold.
- Pure oral TTS manuscript. No Markdown headings, numbered headings, bullet points, tables, bracketed stage directions, or backend notes.
- Use `的`, not `地`, when a de/di ambiguity appears.
- Do not mention `原文`, `2.5`, `2.6`, `2.7`, `融合`, `Gemini`, `Codex`, `提示词`, or any backend workflow trace in the final body.
- Do not include risk suggestions, yellow-note text, `[[RISKNOTE:...]]`, or `私董会`.
- If the final body feels weaker than either source draft, revise by adding more 2.5 pressure into the 2.6 scene beats, not by inventing a new story.

Do not use any older short expansion prefix. For Gemini-generated 2.5 and 2.6 drafts, always use the full selected instruction block from `Gemini Expansion Instruction Choices`. For 2.7, do not build a Gemini prompt; use `2.7 Codex Fusion` locally after 2.5 and 2.6 pass validation.

### 2. Send Each Queued Script To Local Gemini

Run the local Gemini runner. Default to Mac unless the user explicitly asks for Windows or the task depends on Windows-only files, old Windows Codex projects, or Windows-only tooling.

Mac default:

```bash
cd /Users/kin/Documents/Codex/2026-07-02/gemini
./scripts/run_gemini_chat.sh --prompt-file work/prompt.txt --isolated --output-file work/expanded.txt
```

Windows fallback when explicitly needed:

```powershell
cd C:\Users\Administrator\Documents\Codex\2026-06-04\gemini3-1pro-api
.\outputs\run_gemini_chat.cmd --prompt-file C:\path\to\prompt.txt --isolated
```

If the command asks for `Teamorouter API Key`, enter the key provided by the user or use the existing `TEAMO_API_KEY` environment variable if already configured. Do not use the old web expansion channel in this custom skill.

For automated female-edition relationship expansion, write the selected full instruction block + source copy to a UTF-8 prompt file, then call the selected host runner with `--prompt-file <prompt> --isolated --output-file <expanded>`, keeping the female edition explicit and separate from the male workflow.

Reason: the interactive terminal uses single-line `readline.question()`. Pasting or piping a multi-line prompt can send only the first line as the user message, causing Gemini to merely confirm the instruction instead of expanding the source.

For `2.5 Direct Draft`, also load the local legacy style pack if it exists:

`/Users/kin/Documents/Codex/2026-07-02/gemini/work/legacy_style_samples/2.5_legacy_style_pack.md`

Insert only the pack's `Prompt Injection Block` after the selected 2.5 instruction block and before `【原文开始】`. Do not paste the representative excerpts into routine prompts unless the user explicitly asks for a full style-calibration run. This keeps the old Windows 2.5 pressure and mechanism density without wasting context or copying old topics.

Use `--isolated` only for unrelated tests, connectivity checks, non-male categories, or any request where the user explicitly asks for a clean temporary context. This does not send `/new` and does not clear the saved interactive chat history; it only makes the current prompt-file request use a clean context.

When building the prompt file, append the source text immediately after `【原文开始】`, then close it with `【原文结束】`. This source wrapper is part of the prompt, not an optional note.

When the Gemini chat is ready:

- Extract the queued source document text.
- Pick the correct Gemini direction from `Gemini Expansion Instruction Choices`. If the requested direction is 2.7/fusion, first run 2.5 and 2.6 through Gemini, then stop Gemini work and switch to local Codex fusion.
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

For automated runs, prefer building a new UTF-8 retry prompt file with the same selected instruction block + original source copy + retry reason, then rerun the selected host runner, preferably `./scripts/run_gemini_chat.sh --prompt-file <retry-prompt> --output-file <expanded.txt>` on Mac. Treat this as the normal automated equivalent of a same-source retry in the same long-running expansion conversation.

If obvious hallucination appears, retry in the same terminal session with the same selected instruction block and the original source copy. Record the failure in the batch log.

Obvious hallucinations include:

- Generated topic does not match source topic.
- Model reuses a previous article's subject.
- Model outputs only thinking text or system/resource messages.
- Model invents a different title or unrelated framework.
- Output is below 6000 Chinese characters.
- Output lacks the required fixed ending with `我是探花Gary` and `我们内部群里见`.
