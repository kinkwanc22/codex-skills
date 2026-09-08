# 跨版本跨账号去重

本条只增加换芯前与交付前排重，不改变母会话、扩写提示词、案例生成分工、导读保留和字数规则。用户授权同主题可重复，但主体内容不得重复。基础概念和整篇写作结构可复用，不能复用整套核心观点、动作链、证明顺序和案例套路。

共享历史：/Users/kin/Documents/Codex/gary-shared-history。两个账号及独立技能的新任务都使用此目录。源3.1账本与标准化记录只读，导入文件在snapshots，旧稿在artifacts，路径缺失清单见import_report.json。每批开工运行 `python3 scripts/dedup.py refresh` 刷新，保留所有状态。不要把失败稿的某个错误扩大为整类概念禁用。

## 换芯前

1. 按原3.1六字段记录route.json：problem_trigger、core_mechanism、action_chain、proof_operation、position_or_interest_shift、desired_result，以及dominant_causal_chain，放mechanism_novelty对象。另记title、account（大号/小号）、viewpoints逐条观点与方法。换芯不写完整案例；proof_operation描述证明方法，不预写故事。
2. 执行 `python3 scripts/dedup.py screen --source <换芯.txt> --proposal <route.json> --output <目录/screen.json>`，对共享库全状态筛查。查看candidates.json，逐项读取高相关旧稿，并按同主题的语义变体在index.json继续检索。标题包含匹配不等于查全同主题；不能只看前30候选就声称穷尽同题。
3. 对比六字段与逐条观点。核心机制+动作链相同，或六项四项实质相同，或多数条目只是换词换例子，拒绝新路线。必要基础机制可以辅助出现，不能主导整篇。不得为了去重偏题、把观点改温和或任意换标题。
4. 旧记录缺字段时直接读原稿核实，不能把空字段/词面不相似视为新颖。遗失原稿明确记录覆盖缺口，不能保证外部平台查重通过。
5. 保存review.json，包含screen绝对路径、pass、same_topic_review_complete、compared_ids、point_comparison（逐点旧内容/新内容及差异）、distinct_action_chain、topic_fidelity。必须实际比较后才能写pass=true，不自动生成通过结论。若无法找出新而贴题的路线，停止扩写并报告具体冲突，不靠同义改写。
6. `flow.py prepare --source ... --run-dir ... --proposal route.json --review review.json` 校验正文/路线/历史哈希、无自动冲突、语义复核字段，然后登记reserved。缺复核记录不可扩写。历史更新后重新筛查，避免同批或跨账号重复。

## 扩写后

案例、话术、比喻、长段及核心论证都要再与历史比较。模型新增的重复也须记录。短CTA、固定结尾、必要术语不算内容重复。机械修词不能补救主体重复；窄处可修，主体重复重设换芯后按已授权任务重跑，保留失败原文。验收仍不判断真伪或删除导读。

导出前保存final_dedup_review.json，字段body_sha256（实际导出文本去除首尾空白后的UTF8哈希）、pass、compared_ids、findings（实际发现及处理）。导出脚本要求该记录。生成后自动登记generated，原始稿已经占用路线；不把generated标记为用户认可或已发布。

脚本只是词面、原文相等、路线字段的初筛，语义比较由Codex执行。不会承诺每个字、常识或术语完全不同，也不声称能保证平台判重结果。
