---
name: video-subtitle
description: Windows/macOS 本地视频字幕整合包。用户要求给视频加字幕、识别视频语音、生成 SRT/ASS、烧录硬字幕、内嵌字幕、video subtitle、burn subtitles 时使用。通过本地 whisper.cpp 模型和 ffmpeg 处理重活，Agent 只负责读取转写字幕并生成 corrections.txt 纠错表。
---

# Video Subtitle Agent Pack

当用户要给视频加字幕时，使用本地整合包，不要求用户安装 ffmpeg、whisper.cpp 或模型。

## 找到整合包目录

本 skill 目录里有 `pack-root.txt`，内容是整合包根目录。先读取它。

如果不存在，提示用户重新运行整合包里的安装脚本：

- Windows: `install-codex.bat`
- macOS: `bin/install-codex.command`

## 运行命令选择

Windows 使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<PACK_ROOT>\bin\vsub.ps1" <args>
```

macOS 使用：

```bash
bash "<PACK_ROOT>/bin/vsub.sh" <args>
```

## 标准模式流程

1. 运行环境检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<PACK_ROOT>\bin\doctor.ps1"
```

macOS:

```bash
bash "<PACK_ROOT>/bin/vsub.sh" doctor
```

2. 本地转写视频：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<PACK_ROOT>\bin\vsub.ps1" prepare --video "<VIDEO_PATH>"
```

macOS:

```bash
bash "<PACK_ROOT>/bin/vsub.sh" prepare --video "<VIDEO_PATH>"
```

3. 阅读输出工作目录里的 `video_whisper.srt`。

4. 只纠正明显识别错误，不润色、不改原意。把修正写入同一工作目录的 `corrections.txt`，格式：

```text
错词=>对词
```

可以加 `#` 注释。没有明确错误时保留空修正。

5. 本地生成最终字幕并烧录。

默认使用单字幕。根据用户需求选择样式预设：

- `--preset short`：短视频/竖屏，大字黑底，适合抖音、视频号、小红书。
- `--preset clean`：干净描边，适合横屏或不想要黑底的成片。
- `--preset course`：课程讲解，字号和边距更稳。
- `--position bottom|safe|high`：字幕位置。竖屏、容易挡脸时优先用 `safe`。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<PACK_ROOT>\bin\vsub.ps1" finalize --work-dir "<WORK_DIR>" --preset short --position safe
```

macOS:

```bash
bash "<PACK_ROOT>/bin/vsub.sh" finalize --work-dir "<WORK_DIR>" --preset short --position safe
```

如果用户明确要求固定字体/字号，可以追加 `--font`、`--fontsize`、`--style box|outline`、`--margin-v`。

## 双字幕可选模式

默认不要生成双字幕。只有用户明确说“双字幕”“中英字幕”“加英文字幕”“第二语言字幕”时才启用。

双字幕需要第二份字幕文件：

- 用户提供第二语言 SRT：使用 `--secondary-srt "<SECONDARY_SRT>"`
- Agent 翻译生成第二语言 SRT：会额外消耗文本推理额度，必须先告知用户

示例：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<PACK_ROOT>\bin\vsub.ps1" finalize --work-dir "<WORK_DIR>" --preset short --position safe --secondary-srt "<ENGLISH_SRT>"
```

macOS:

```bash
bash "<PACK_ROOT>/bin/vsub.sh" finalize --work-dir "<WORK_DIR>" --preset short --position safe --secondary-srt "<ENGLISH_SRT>"
```

6. 向用户汇报：

- 工作目录
- 最终视频路径
- 最终 SRT 路径
- 纠正了哪些词

## 约束

- 原始视频不要改。
- 不要要求用户手动下载模型。
- 标准模式会消耗当前 Agent 的少量文本纠错算力，但识别和烧录都在本地完成。
- 下载模型或 runtime 不是日常使用步骤；如果缺文件，让用户运行整合包准备脚本。
