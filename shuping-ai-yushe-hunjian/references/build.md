# 构建与原生登记

## 原生预设构建

复用 [千川竖屏混剪的构建入口](../../qianchuan-shuping-hunjian/references/build.md) 和 [build_draft.py](../../qianchuan-shuping-hunjian/scripts/build_draft.py)。同一原生预设构建链可以接竖屏 AI 素材。每句输入源字幕、文字槽映射、同步英文、镜头源路径、原始尺寸、实际源入点和时长。选片及技术复核完成后再构建。母版的全程角标、滤镜和暗角应覆盖新稿全长，配乐须核对实际剩余时长。

复剪优先读取能与冻结原稿和配音摘要对上的时间线。剪映打开工程后可能重写 `draft_info.json`、改轨道显示名并做帧对齐。用户明确要求沿用先前交付的原时间轴时，用经验证的 `draft_content.json` 或相应冻结记录确认实际口播、中文切点和配乐。勿改写用户正在编辑的源稿。

每句保留全部预设子工程。斜切字体、打开字幕等源包可能含多个嵌套工程。应按原组合内的引用核对文字槽、动画和资源，不能只按外层直接引用修剪子工程。一句作为一个可编辑复合片段，所引用的字体、遮罩和动画资源随新草稿落地，普通视频留在独立轨。

## 首页索引和分类

先用新目录和唯一项目身份写齐工程，再登记 `root_meta_info.json` 和 `Config/LocalDraftFolder/draft_folder_mappings.json`，修改前备份。按实际路径核对首页条目、原生草稿 ID 和分类。剪映可能在首页重载或首次打开时把后台登记的 ID 改成原生 ID，这时按项目路径采用原生 ID，并更新同一条分类和交付记录。验证索引经首页刷新仍存在，避免在用户正在编辑或导出时切换窗口或改工程文件。

## 已完成样例

Mac 工作记录在 `/Users/kin/Documents/Codex/2026-09-11/new-chat/outputs/freshness_vertical_ai_dual_1117/`。读 `preset_job.json`、`preset_job.manifest.json` 和 `delivery.json` 查看原句、预设映射、实际视频及原生 ID。样例是《新鲜感与相处边界》，全长 81.41 秒、43 句和 43 镜，选用了 8 款原生预设。预设版已在剪映打开。数目仅属于该样例。
