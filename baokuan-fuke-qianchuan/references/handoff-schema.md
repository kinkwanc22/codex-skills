# Handoff schema

每条复刻视频用一个 UTF-8 JSON 文件交接。路径必须是绝对路径。

```json
{
  "schema_version": 1,
  "job_id": "20260920_001",
  "title": "未来女朋友",
  "status": "video_ready",
  "prompt": "完整 Seedance 首帧提示词",
  "story_logic": "女主质疑备注，男主重新定义关系，女主主动靠近",
  "dialogue": [
    {"speaker": "女主", "text": "你为什么这样备注我？"},
    {"speaker": "Gary", "text": "因为备注要写未来用途。"}
  ],
  "generated_video": "/absolute/path/opening.mp4",
  "female_lead_id": "036",
  "female_lead_folder": "/absolute/path/036_女主目录",
  "fixed_cta_audio": "/Users/kin/工作用（同步）/千川音频/固定逻辑cta.wav",
  "fixed_cta_srt": "/Users/kin/Documents/Codex/2026-09-11/new-chat/work/qianchuan_full_0913/fixed_cta/固定转化CTA_语义优化.srt",
  "transition_text": null,
  "transition_audio": null,
  "selected_transition_videos": [
    {
      "path": "/absolute/path/036_女主目录/clip.mp4",
      "source_start": 1.2,
      "duration": 4.5
    }
  ],
  "selected_cta_images": [
    "/absolute/path/036_女主目录/cta-01.png",
    "/absolute/path/036_女主目录/cta-02.png",
    "/absolute/path/036_女主目录/cta-03.png"
  ],
  "cta_image_timeline": [
    {
      "path": "/absolute/path/036_女主目录/cta-01.png",
      "duration": 18.0
    }
  ],
  "jianying_draft": null,
  "stage_evidence": {}
}
```

## Status order

```text
prompt_ready
video_ready
transition_ready
tts_ready
assets_ready
draft_written
verified
```

状态只能由真实产物推进：

- `prompt_ready`：`prompt`、`dialogue`、`female_lead_id`、`female_lead_folder` 完整。
- `video_ready`：生成视频存在并包含可读取的视频流和音轨。
- `transition_ready`：`transition_text` 已完成知识机制匹配和时长估算。
- `tts_ready`：转场 WAV 存在且真实时长不超过 25 秒。
- `assets_ready`：转场视频已逐段记录源起点和使用时长，累计覆盖转场配音；CTA 使用少量同女主图片，图片时间线累计覆盖固定 CTA。
- `vertical_cta_overlay_track`：可选但推荐记录竖版 CTA 固定画中画轨；该轨只覆盖 CTA 区间，素材来自固定预设，不计入转场视频或同女主素材清单。
- `subtitle_position`：固定记录为水平居中 `x=0`、归一化 `y=-0.48`；视觉中心约在画面从上往下 `74%` 处，剧情、转场和 CTA 字幕必须一致。
- `black_filter_intensity`：全程黑曜/耀黑滤镜固定为 `0.5`（剪映界面显示 `50%`）；暗角保持独立设置，不随本字段改变。
- `draft_written`：剪映草稿目录、`draft_content.json` 和 `draft_info.json` 存在。
- `verified`：结构 QA 通过；前台播放或导出状态仍在 `stage_evidence` 中单独记录。

## Default paths

- 女主素材根目录：`/Users/kin/工作用（同步）/图/长视频用图/2026-08-27_56位女主_Lovart五套竖屏`
- 固定 CTA：`/Users/kin/工作用（同步）/千川音频/固定逻辑cta.wav`
- 固定 CTA SRT：`/Users/kin/Documents/Codex/2026-09-11/new-chat/work/qianchuan_full_0913/fixed_cta/固定转化CTA_语义优化.srt`
- 剪映草稿根目录：`/Users/kin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`

固定 CTA 如果项目已有经过验收的清理版，可在清单里明确换成 `acv_固定逻辑cta.wav`；同一批必须统一，不能自动混用两个版本。
