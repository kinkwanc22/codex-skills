# 本机素材与构建参考

- 下载包在 Windows `win-codex`：`E:\工作用\视频素材\女课素材\剪映900款口播字幕动态排版`。Mac 本轮工作区：`/Users/kin/Documents/Codex/2026-11-16/new-chat-2/work`，`preset_screen/` 含七个 ZIP 和源格式索引，`native_animation_assets/` 含已定位的剪映原动画文件，`rebuilt_native_styles_manifest.json` 是 13 款已验收参考的逐句映射。源包、字体和下载资产不进技能 Git。
- 画面基准是 0926 的「竖屏本地素材混剪｜他的情商突然变得很高｜一句一镜中英字幕｜0926」。真人视频池在 `/Users/kin/男性素材库/10_可用素材汇总_真人实拍_20260926`。现有素材编号/缩略图见 `/Users/kin/Documents/Codex/2026-09-26/shuping-ziranliu/work/real_pool`，实际选片确认源文件、尺寸、使用范围、首中尾画面。
- 本机 Mac 草稿根目录：`~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`。优先从剪映当前有效时间线读取可解析 JSON。组合预设以原嵌套草稿移植；映射全部文字槽（包括重复层），重新生成素材/片段/组合 ID。将外来路径重绑为目标草稿资源路径，包括富文本中的 `font.path` 和 `effectStyle.path`、动画和蒙版。不要伪造缺失效果。
- 历史上的扩选稿曾在已登记的路径更换实体后打不开。以未占用的全新路径和身份写入，待文件全部写齐才让应用发现。不要在剪映打开期间重写文件。用真正要交付的新草稿做前台播放验证。
- 正常以参考的 1080×1920、30fps、黑曜50%、暗角、左上角标和短叠化为基线；试剪留独立口播、配乐、下方同步英文及原中文预设。

## 复用构建脚本（Mac）

`python3 scripts/build_draft.py <job.json> --workspace <含预设 ZIP 索引及动画资源的目录>`。已验证样例为上述工作区 `liaodao_job.json`。输入包含新草稿 `name`、现有完整口播源草稿路径 `source`、源 `caption_track`、可选的竖屏样式草稿 `reference`。按源字幕逐句给 `rows`，每行含 `preset`、按中文原顺序排列的 `mapping`（源文字槽→本句片段）、`english`、`shot`（`path`、`width`、`height`、秒为单位的 `start` / `duration`、`reason`）。构建脚本使用实际已对齐的源字幕时间；脚本不负责写稿、配音或选片。先保证所有原预设资源找得到，并在产出后打开剪映复核。
