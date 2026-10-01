# 去重与记录

继承3.1六字段与当前3.5共享历史。默认 /Users/kin/Documents/Codex/gary-shared-history；可用 HUANXIN_HISTORY_HOME 指向隔离测试库。独立的是流程代码，不是另建一个看不到旧稿的内容历史孤岛。

每批先用history.py refresh导入现有3.1账本、项目稿件及shared-history/new登记。不要在其他任务已prepare、尚未expand的间隙刷新共享索引；顺序处理新稿注册，避免历史变化。源账本只读；失联文件缺口在import_report.json，不承诺平台绝对不判重。

route.json记录title、account、viewpoints，以及mechanism_novelty：problem_trigger、core_mechanism、action_chain、proof_operation、position_or_interest_shift、desired_result、dominant_causal_chain。proof_operation只记录证明方式，不预写完整案例。

## 默认：相似提示，正文决定

screen后读candidates.json，再按主题语义变体检索all_routes.json，优先阅读与具体操作最接近的旧稿；旧字段缺失时读正文，不能把空字段当新颖。跨大小号及本批逐点比较，但不要求每个观点和机制都前所未有。

- 同一机制、同一强结果或相同结构，具体操作与作用路径不同：允许。
- 一两处基础动作或例子相同：提示并核对，可保留；不是按重合数量机械判断。如果重合的是整篇唯一核心打法，仍须重写。
- 多数核心观点、具体操作及推进顺序实质相同，只换词或换案例：正文复核判不通过，重写重复部分或主链。
- 完全相同正文：自动拦截。识别已知标题后比较正文，改标题、标点或换行不能成为新稿。未能识别的复杂旧稿包装仍靠正文复核补查。

六字段是检索线索，不是六项重复票数。尤其problem_trigger、proof_operation和position_or_interest_shift中的通用模板不能当作内容重复证据。核心机制加动作链、四字段相似或因果链相似只提示优先复核，不自动要求换机制。相似度是字串指标，不表示内容抄袭百分比，也不能仅凭低相似度放行。

正常screen使用review_first策略，automatic_block仅针对完全相同正文或新稿路线字段缺失；后者是资料不完整，不是判重。mechanism_screen的similarity_warnings/collisions均为相似线索，旧mechanism_novelty_pass与deterministic_zero_overlap_pass保留为历史诊断字段，不再作默认门禁。legacy_novelty.py正常遇到相似提示返回0，缺字段返回2；--strict-zero-overlap是明确请求严格实验时的旧模式，日常换新不调用。

review.json必须由执行者实际读稿后写：screen绝对路径、pass、same_topic_review_complete、compared_ids、point_comparison（每个新点对应旧内容与差异）、distinct_action_chain、topic_fidelity。重合点写清是否基础动作、为何不主导全篇，其他点说明操作差异；不要为了通过编造差异或把所有相似提示逐条变成硬门禁。多数实质重复时pass=false。不能仅按分数自动生成“通过”；机器只验证字段、哈希及明确冲突，语义结论由执行者负责。改稿后重新screen，历史变化后重新比新增记录再screen。

冻结时写入shared-history/new，旧3.5刷新也会看见这条稿件。冻结状态不是已扩写或已认可。一个handoff_id就是同一篇文章的身份，多线路导出的同稿不能被当作不同新内容。

下游若再次查重：只可凭交接包中同一handoff_id和相同正文hash识别“本篇已登记”，其它文章仍要比较。现有3.5 flow.py不识别该身份，直接把冻结稿当新稿prepare会被重复检查阻断；不能删除共享历史来绕过。默认通过export生成的正文输入文件交给目标线路，见operations.md。需要对现有runner做身份兼容时另行实现并测试，不谎称已经接好。
