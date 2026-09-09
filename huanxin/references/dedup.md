# 去重与记录

继承3.1六字段与当前3.5共享历史。默认 /Users/kin/Documents/Codex/gary-shared-history；可用 HUANXIN_HISTORY_HOME 指向隔离测试库。独立的是流程代码，不是另建一个看不到旧稿的内容历史孤岛。

每批先用history.py refresh导入现有3.1账本、项目稿件及shared-history/new登记。不要在其他任务已prepare、尚未expand的间隙刷新共享索引；顺序处理新稿注册，避免历史变化。源账本只读；失联文件缺口在import_report.json，不承诺平台绝对不判重。

route.json记录title、account、viewpoints，以及mechanism_novelty：problem_trigger、core_mechanism、action_chain、proof_operation、position_or_interest_shift、desired_result、dominant_causal_chain。proof_operation只记录证明方式，不预写完整案例。

screen后读candidates.json，再按主题语义变体检索all_routes.json，阅读高相关旧稿；旧字段缺失时读正文，不能把空字段当新颖。跨大小号及本批逐点比较：核心机制与动作链相同、六字段至少四项实质相同，或多数点只换词换案例，都要改路线。基础概念可重用，但不能占整篇主导。

review.json必须人工写：screen绝对路径、pass、same_topic_review_complete、compared_ids、point_comparison（每个新点对应旧内容与差异）、distinct_action_chain、topic_fidelity。不能自动生成“通过”；机器只验证字段及明显冲突。改稿后重新screen，历史变化后重新比新增记录再screen。

冻结时写入shared-history/new，旧3.5刷新也会看见这条稿件。冻结状态不是已扩写或已认可。一个handoff_id就是同一篇文章的身份，多线路导出的同稿不能被当作不同新内容。

下游若再次查重：只可凭交接包中同一handoff_id和相同正文hash识别“本篇已登记”，其它文章仍要比较。现有3.5 flow.py不识别该身份，直接把冻结稿当新稿prepare会被重复检查阻断；不能删除共享历史来绕过。默认通过export生成的正文输入文件交给目标线路，见operations.md。需要对现有runner做身份兼容时另行实现并测试，不谎称已经接好。
