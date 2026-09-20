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
  "transition_style": {
    "name": "泡泡模糊",
    "duration_seconds": 1.0,
    "apply_to": "all_visual_boundaries"
  },
  "audio_levels_db": {
    "opening_dialogue": 11.6,
    "transition_tts": 10.0,
    "fixed_cta": 10.0,
    "preset7_bgm": 0.0
  },
  "subtitle_style": {
    "font": "研宋体",
    "ui_font_size": 9,
    "color": "#FFFFFF",
    "align": "center",
    "letter_spacing": 0,
    "line_spacing": 0,
    "scale_percent": 100,
    "stroke_enabled": false,
    "shadow": {
      "enabled": true,
      "color": "#000000",
      "opacity_percent": 90,
      "blur_percent": 15,
      "distance": 5,
      "angle_degrees": -45
    }
  },
  "subtitle_position": {
    "jianying_x": 0,
    "jianying_y": -819,
    "normalized_x": 0,
    "normalized_y": -0.48,
    "applies_to": ["opening_dialogue", "transition", "fixed_cta"]
  },
  "effect_settings": {
    "black_filter_intensity": 0.5,
    "dark_corner_intensity": 100
  },
  "cta_packaging_layout": {
    "scope": "cta_only",
    "disclaimer": {"font": "系统", "ui_font_size": 14, "scale_percent": 23, "x": 0, "y": 1891, "rotation_degrees": 0},
    "brand_three_lines": {"font": "俪金黑", "font_resource_id": "6740499317733200388", "ui_font_size": 15, "scale_percent": 105, "x": 0, "y": 1206, "rotation_degrees": 0},
    "course_badge": {"font": "俪金黑", "font_resource_id": "6740499317733200388", "ui_font_size": 14, "scale_percent": 66, "x": 171, "y": 768, "rotation_degrees": 0, "stroke_opacity_percent": 100, "stroke_width": 40}
  },
  "vertical_cta_overlay_track": {"present": true, "scope": "cta_only", "material_type": "sticker", "resource_id": "6940208530096016671", "segment_count": 1, "muted": true, "scale_percent": 43, "jianying_x": 795, "jianying_y": 774, "rotation_degrees": 0},
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
- `vertical_cta_overlay_track`：从 `draft_written` 起必须记录竖版 CTA 固定贴纸轨；固定资源为 `6940208530096016671`，只允许 1 段并覆盖 CTA 区间，剪映参数为缩放 43%、X 795、Y 774、旋转 0°，不计入转场视频或同女主素材清单。
- `transition_style`：全部画面边界固定为 `泡泡模糊 1.0 秒`。
- `audio_levels_db`：固定记录剧情原声 11.6、转场 10、CTA 10、预设 7 BGM 0。
- `subtitle_style`：固定记录研宋体、剪映界面 9 号、白色、居中、描边关，以及完整阴影参数。
- `subtitle_position`：同时记录剪映界面坐标 X 0、Y -819 和后台兼容归一化坐标 X 0、Y -0.48；前台验收以剪映坐标为准。
- `effect_settings`：黑曜/耀黑为 `0.5`（界面 50%），暗角边缘暗度为 `100`。
- `cta_packaging_layout`：记录三条 CTA 包装文字的字体、字号、缩放、坐标和旋转；只允许覆盖 CTA 区间。
- `draft_written`：剪映草稿目录、`draft_content.json` 和 `draft_info.json` 存在。
- `verified`：结构 QA 通过；前台播放或导出状态仍在 `stage_evidence` 中单独记录。

## Default paths

- 女主素材根目录：`/Users/kin/工作用（同步）/图/长视频用图/2026-08-27_56位女主_Lovart五套竖屏`
- 固定 CTA：`/Users/kin/工作用（同步）/千川音频/固定逻辑cta.wav`
- 固定 CTA SRT：`/Users/kin/Documents/Codex/2026-09-11/new-chat/work/qianchuan_full_0913/fixed_cta/固定转化CTA_语义优化.srt`
- 剪映草稿根目录：`/Users/kin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`

固定 CTA 如果项目已有经过验收的清理版，可在清单里明确换成 `acv_固定逻辑cta.wav`；同一批必须统一，不能自动混用两个版本。
