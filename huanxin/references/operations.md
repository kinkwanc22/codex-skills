# 运行与交接

以下用python3代表当前环境可用的Python。脚本均在本skill/scripts下，工作文件放本次项目的新目录，不放skills仓库。正常稿件无需Word或模型依赖。

## 资料与历史

知识检索默认读取 /Users/kin/Gary 男性情感/Gary 男性情感，跨来源模块与旧历史查询依赖：/Users/kin/Documents/Codex/2026-07-10/qu/work/obsidian_cross_source/final_modules.json 和 qu/scripts/query_31_32_history.py。这些是资料依赖，不导入其旧写作规则。知识脚本的3.1/3.2参数仅是历史检索标签，不选择扩写版本。

```bash
python3 scripts/history.py refresh
python3 scripts/build_knowledge_call_pack.py --source query.txt --version 3.2 --output-dir knowledge
```

query.txt可为选定题目和搜索词。检索包包含候选资料，不等于实际阅读；打开采用的原文。案例候选只是稿外材料，换芯不写完整案例。已剥离开头模板检索。

结构原稿默认 /Users/kin/工作用（同步）/自选起号 30，也可使用用户提供的新原稿。找不到来源时说明具体缺口；不能虚称检索完成。安装到另一台机器不等于知识库和历史也已迁移。

## 换芯与冻结

制作source.txt（第一行完整标题，后接短正文）、route.json、notes.json。route.json 除历史六字段外，必须记录 `mechanism_design` 与 `provocation_design`：

```json
{
  "mechanism_design": {
    "primary_domain": "psychology|sociology|biology|PUA",
    "primary_mechanism": "一个主效应、理论或术语",
    "supporting_mechanism": "可空；最多一个",
    "causal_chain": "男人卡点 -> 机制触发 -> 女人心理变化 -> 位置反转 -> 强结果",
    "why_it_proves_the_title": "该机制如何直接推出题目承诺"
  },
  "provocation_design": {
    "counterintuitive_judgment": "反认知核心判断",
    "interest_conflict": "男女利益或评价权冲突",
    "male_action": "男人可执行动作",
    "female_shift": "女人心理或欲望变化",
    "position_or_result_reversal": "位置反转或强结果",
    "advice_like_rejection_pass": true
  }
}
```

任一块缺失、主机制超出四个允许方向、辅助机制超过一个，或 `advice_like_rejection_pass` 不能人工判定为 true，都不得进入 freeze。notes.json示例字段：

```json
{
  "structure": {"name": "节点推进", "original": "关系推进八个关键节点", "argument_flow": "阶段卡点→原因→动作→下一阶段反馈", "weighting": "关键节点详、过渡节点短"},
  "knowledge_used": [{
    "card_id": "B层卡片ID",
    "card_path": "实际已读卡片路径",
    "source_id": "A层原始片段ID或标题",
    "source_path": "实际已读原文路径",
    "exact_excerpt": "从A层原文摘录的、直接支持该机制的原句",
    "evidence_limit": "如单一来源、待跨源验证；不可省略卡片已有的限制",
    "use": "本稿怎样采用该片段、为何贴题；不把原文未经验证的说法升级成科学定论"
  }],
  "point_count": 5,
  "topic_fidelity_checked": true
}
```

```bash
python3 scripts/history.py screen --source source.txt --proposal route.json --output screen.json
# Codex阅读候选旧稿并完成逐点语义比较后写review.json，不能脚本自动判通过。
python3 scripts/handoff.py freeze --source source.txt --proposal route.json --review review.json --notes notes.json --output frozen
```

冻结前，`knowledge_used` 至少要有一条完整记录：实际读过的B层卡片、其A层原文路径与精确摘录、证据限制、在本稿中的用途。只填卡片ID、贴检索摘要、只引用二次提炼而没有原文片段，均不合格；校验失败不得冻结。冻结包包含manuscript.txt、route.json、notes.json、review.json、screen.json、manifest.json。每个文件记录hash；冻结后不覆盖。需要实质改稿时生成新版本并重新复核。该脚本登记“未扩写”的共享记录，不会调用模型。

示例：B-067《利用心理学效应驯化女人主动付出》标明“单一高赞来源、待跨源验证”；其链接A层原文067有片段“富兰克林效应：人会在帮助别人时获得满足感，并且会对被帮助者产生好感”。调用时既记录B卡的归纳，也记录A原文这句实际依据，并保留“单一来源”的限制。不能把这句话扩张成“必然让女人爱上你”或已证实的普遍定律。此例只演示卡片与片段如何成对追溯，不表示后续每篇都要用B-067；每篇须匹配自己的题目检索对应卡片与原文片段。

当前Gary完整生产流程在冻结正文后、导出扩写输入前调用 `baokuan-kaitou-sheding`。根据冻结题目、承诺数量、核心机制和结果生成一个正式开头，并在工作目录保存：

- `opening_lock.txt`：最终开头纯文本；换新预览时放在短正文上方展示。
- `opening_lock.json`：模板ID、变量替换、母题、数量、结果承诺、正文hash与创建时间。

开头锁与冻结正文分开管理。`manuscript.txt`和送模型的`input.txt`仍保持纯正文，不能把正式开头并入模型输入让其改写。下游扩写完成后，只检查成稿是否仍兑现开头的母题、数量和结果；检查通过就把`opening_lock.txt`原样装到第一个`另外说一下`之前。不得在验收阶段另写一个竞争开头。若用户只要求换新、不要求完整生产流程，可以同时交付“正式开头+换新短正文”的预览，但状态仍是“换芯已冻结，未扩写”。

## 不同扩写线路

```bash
# 旧2.5会话 / 独立3.5的正文加案例输入
python3 scripts/handoff.py export --bundle frozen --target old-2.5-session --case mid-cta --output to-old25
# 任意指定线路接收纯正文，由该线路自己处理案例
python3 scripts/handoff.py export --bundle frozen --target 用户指定线路 --case none --output to-custom
python3 scripts/handoff.py verify --bundle frozen
```

export仅产出input.txt、manuscript.txt、handoff.json。target是用户指定的交接标签，不是模型路由、已连接服务或执行成功声明。两个导出的manuscript.txt完全相同；input只按选项在正文末尾追加一条案例要求。不要附加后台notes、去重报告、结构指令、长度锁或开头模板给扩写。`opening_lock`由编排流程随handoff_id关联，但不拼进input.txt。

- 手动/浏览器旧2.5：把input.txt交给新复制的旧会话；本skill不复制或修改母会话。
- 独立3.5或4.0：下游按明确指定版本执行；保持同一稿件身份，不将注册过的冻结稿再当全新稿重复换芯。尤其4.0不可凭数字更大就自动替换3.5。
- 其他模型、服务或人工：使用input.txt或纯manuscript.txt，线路自行决定模型、提示、案例与验收。
- 当前没有自动执行适配器。旧3.5的flow.py prepare会把共享库已登记的冻结稿视为重复；若要全自动CLI衔接，需要让接收端识别handoff_id并只排除本篇自身记录。不能篡改hash、删除历史或跳过其它文章的复核。当前稳定交接面是文件输入，不虚报已完成自动对接。

下游生成原稿、改开头、验收、排期、发布各自单独记状态。当前用户要求“先原稿直出、之后验修”属于下游本批偏好，不变成上游强制修稿步骤。
