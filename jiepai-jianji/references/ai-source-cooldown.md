# AI混剪源视频冷却

用户2026-11-04确认：第1条出现的视频，第2、3条不得出现，最早第4条重新恢复候选。是最小间隔，不是每第4条必须复用。

## 持久台账与执行

- Mac统一台账：`/Users/kin/Documents/Codex/shared_state/ai_mixed_source_cooldown.json`。连贯试剪、正式批量及跨批次共享，删除草稿不能清除记录。
- 按实际交付的视频顺序编号；待交付批次先统一分配并用同一台账副本依次模拟检查/提交，再生成。正式登记成功后按相同顺序提交正式台账，失败稿不消耗序号；用户已看过的试剪算交付。
- 普通视频包括开头、正文和CTA视频，156女主库与原AI库一视同仁。固定品牌包装、字幕、BGM不参与冷却。
- 按源视频身份而非路径或入出点去重。完整文件SHA256识别改名/复制；转码、裁切版本需从来源清单显式标相同 `canonical_source_id`，不得视作新源。已知同源副本不能只因哈希不同就入选，来源不明时报告待核。
- 同片同源禁止重复；上两条任一出现的源全部屏蔽。其他旧规则要求全批一次或排除历史源时，取更严格的限制，不因满冷却而豁免。
- 场景多样化独立核对：不同源但同类画面仍不得连续；优先语义、人物状态和情绪匹配，不为去重硬填无关素材。
- 池不足时报告可用源数量、缺口和被冷却数量；不要提前解除限制、冻结、变速、循环或伪造新源。

检查和提交（计划为源路径等字段组成的JSON数组）：

```bash
python3 scripts/ai_source_cooldown.py check --plan /absolute/source_selection.json
python3 scripts/ai_source_cooldown.py commit --plan /absolute/source_selection.json --draft-key UNIQUE_DELIVERY_KEY
```

支持字段：`path`/`source`、`canonical_source_id`（已知同源根身份）、`source_identity`、`source_id`。脚本重新计算源文件完整SHA256，交叉匹配已登记路径/根身份/文件内容；计划中的已知裁切或转码关系必须先填好根身份。`--ledger`可指定离线模拟副本，不要通过换台账绕过正式限制。

QA记录：交付序号、检查过的前两条、冷却冲突数、源内重复数、每源最早可用序号。随机抽取前先屏蔽冷却源；交付前再次检查。历史试稿的旧冲突保留为 `legacy_before_rule`，不倒推为新规则验收通过，也不重做已接受试稿。
