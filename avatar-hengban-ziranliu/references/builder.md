# 本地构建器

在Mac执行；Windows可承担ASR，但不要把Mac剪映路径直接当Windows路径运行。依赖现有横版B05样式与8月23日包装模板（默认路径在脚本开头）；不可读取时报告具体资源，不用空模板或竖版模板替代。

先使用环境中的 `create_audio_subtitle_draft_styled.py` 或当前可用剪映草稿工具，生成新的、带单一主配音与已锁字幕的音频字幕源草稿。已打开的稿件不能后台重建。构建器拒绝含视频、`.locked`或已升级`Timelines`目录的目标。

开头截取：

```bash
python3 scripts/prepare_avatar_audio.py --audio /absolute/full.wav --srt /absolute/final.srt --marker 今天我们要聊的是 --out /absolute/opening.wav --manifest /absolute/slice.json
```

`--marker`需精确匹配唯一一条当前字幕；不能套旧稿秒数。脚本拒绝覆盖输出，并记录全文与截取文件SHA256及PCM前缀一致性。

下载并校正数字人视频后，准备JSON配置（所有路径绝对；示例中的时间点只用于本次已认可样本）：

```json
{
  "targetDir": "/absolute/数字人横屏自然流｜Gary｜主题｜日期｜女主063｜素材：063_实际女主文件夹",
  "heroineDir": "/absolute/063_实际女主文件夹",
  "avatar": "/absolute/avatar_corrected.mp4",
  "personVideo": "/absolute/063_实际女主文件夹/01_面对面聊天_横_1920x1080.mp4",
  "still": "/absolute/063_实际女主文件夹/063_03_coffee_横屏_通过.png",
  "avatarEndUs": 13340000,
  "introEndUs": 22420000,
  "stillStartUs": 24870000,
  "title": "探花社交\n当前主题完整剖析\n完整未删减版",
  "bodyLead": "当前主题的运行规则",
  "bodyShort": "当前主题完整剖析",
  "sourceSha256": "current-source-docx-sha256",
  "avatarLook": "actual-selected-horizontal-look-id"
}
```

`avatarLook` 必须填写本次实际生成所用的横屏 look ID，用于记录；候选按主技能规则从 Gary 的可用横屏造型中选择。可选字段：`marker`、`introSource`、`donorDir`、`overlaySource`、`ffmpeg`、`ffprobe`。片头与女主区间均必须正数并能被源素材覆盖；时间点要与当前已锁字幕边界一致。若语义结构不同，先分析并适配，不能修改字幕去迎合旧时间点。

```bash
node scripts/build_avatar_horizontal.cjs --config /absolute/config.json
```

构建器在目标内保存原音频字幕JSON备份、复制实际素材和字体、写入结构与QA报告。不会生成HeyGen、打开剪映、导入素材栏或导出成片。之后必须前台导入报告中的`media_bin_sources`并核验缩略图；主音轨和BGM另计，画面源去重数量不能遗漏数字人。
