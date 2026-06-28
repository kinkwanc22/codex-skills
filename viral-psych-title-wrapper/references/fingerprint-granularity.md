# 精细文章指纹与颗粒度协议

当用户要求“更精细的指纹”“颗粒度”“同题材去重”“批量不雷同”时，使用本协议补强主流程。目标不是多填字段，而是让每篇文章形成可被标题继承的独立身份。

硬性红线：指纹必须来自逐篇深读后的人工语义判断。不得用脚本、关键词扫描、文件名拆词、开头句模板或字段规则自动生成指纹；脚本只能用于生成后的质检、去重、薄指纹报警和相似度检查。标题生成顺序必须是「读懂正文 -> 文案理解 -> 机制包装 -> 标题命名」，不得反过来用标题模板倒推指纹。

## 指纹拆解顺序

按以下顺序抽取，不要先套心理学术语：

1. 事实锚点：从正文找具体动作、场景、对话、案例、物件、时间点、关系阶段。
2. 行为信号：把事实锚点压缩成一个可识别行为，例如“不解释直接离场”“饭局只夹一次菜”“朋友圈只露半张侧脸”。
3. 情绪按钮：判断这个行为触发恐惧、羞耻、嫉妒、损失厌恶、慕强、戒断、被筛选、被看见中的哪一种。
4. 权力位移：写清谁从什么位置移到什么位置，例如“读者从索取回应移到筛选投入”。
5. 机制命名：把行为信号 + 情绪按钮 + 权力位移翻译成一个专属机制名。
6. 标题继承：标题第一行必须继承事实锚点、行为信号或专属机制名之一。

继承不等于照搬。专属锚点是语义来源，不是封面标题原词。标题第一行优先写成暗黑心理学、PUA知识付费、关系博弈、训练系统风格的概念名；只允许保留 2-4 字短锚点，并且必须完成二次命名。

生活场景锚点只负责保证文章专属性，不直接进入标题第一行。遇到“倒水、做饭、拍照、改造形象、约饭、回消息、发朋友圈、买礼物、接送”等细节，必须转译成机制词，例如“付出绑定、奖赏驯化、价值证明诱导、沉没成本锁定、索取框架、延迟反馈控制、情绪奖赏定价权”。

转译示例：

- `约饭取消只回“行”` -> `废测反制免疫术`
- `无底线付出被当资源工具` -> `供养者剥离模型`
- `她发现你的世界不是围着她转` -> `不可控框架植入术`
- `温柔奖励后突然抽离关注` -> `奖惩戒断回路`
- `倒水/做饭/拍照后的反馈循环` -> `付出绑定操盘术`

## 必填字段分级

P0 字段缺失时不得生成标题：

- `source_id`
- `body_claim`
- `scene_anchor`
- `behavior_signal`
- `behavior_chain`
- `emotional_trigger`
- `power_shift`
- `non_reusable_anchor`
- `fingerprint_key`

P1 字段用于拉开同题材差异，批量模式至少命中 6 项：

- `opening_hook`
- `case_or_example`
- `audience_state`
- `desire_vector`
- `fear_vector`
- `core_conflict`
- `relationship_mechanism`
- `novelty_point`
- `unique_term_seed`
- `result_promise`

P2 字段用于防抄和输出控制：

- `raw_title_digest`
- `mistaken_belief`
- `anti_copy_terms`
- `forbidden_generic_terms`
- `title_anchor_map`
- `specificity_diagnosis`

## 颗粒度评分

给每篇文章内部计算 `fingerprint_granularity_score`，默认可输出。满分 10 分：

- 2 分：P0 字段齐全，且 `scene_anchor`、`behavior_signal`、`non_reusable_anchor` 都不是泛词。
- 2 分：至少 3 个字段直接来自正文细节，不来自文件名或原文标题。
- 2 分：`behavior_chain` 有 3 段以上，并包含具体动作，不只是“建立框架/提升价值”。
- 1 分：`power_shift` 写清双方位置变化。
- 1 分：`unique_term_seed` 至少 2 个词能从正文锚点推导。
- 1 分：`fingerprint_key` 同时包含专属锚点、行为链、情绪按钮、权力位移。
- 1 分：标题1第一行能回扣 `scene_anchor`、`behavior_signal`、`unique_term_seed` 任一项。

评分规则：

- 8-10 分：可进入标题生成。
- 6-7 分：只能生成初稿，必须在输出前补强 `scene_anchor`、`behavior_signal` 或 `non_reusable_anchor`。
- 5 分及以下：指纹失败，先重读正文；不得靠换标题词库硬写。

## 失败诊断

若出现以下任一情况，在 `specificity_diagnosis` 中标记原因，并重写指纹：

- `non_reusable_anchor` 可以套到同目录另一篇文章。
- `scene_anchor` 只是“聊天/关系/吸引/成长/自律”等泛场景。
- `behavior_signal` 是“高价值/低需求/冷淡/主动/被动”等抽象标签。
- `core_conflict` 没有“表层动作 vs 底层动机”的具体对照。
- `fingerprint_key` 删除 `source_id` 后仍与上一篇高度相似。
- 标题1第一行不能说明来自哪一个正文锚点。

## 标题映射表

生成 10 个标题前，内部建立 `title_anchor_map`。默认不完整输出；批量排查或用户要求“看指纹映射”时输出精简版：

```text
title_anchor_map：
1｜第一行概念｜scene_anchor + behavior_signal｜专属锚点｜低/中/高风险
2｜第一行概念｜audience_state + power_shift｜专属锚点｜低/中/高风险
```

同一篇 10 个标题至少覆盖 5 种不同字段组合。若 4 个以上标题映射到同一组字段，整组重写。
