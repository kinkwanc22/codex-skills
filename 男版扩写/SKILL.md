---
name: 男版扩写
description: 男性向长文案扩写工作流。Use for 男版扩写, 男号文案, 男性向情感文案, 男性版2.5/2.6/2.7扩写, 4.0换芯扩写, Gemini本地命令扩写, 三版开头, 长文稿Word导出, and end-to-end Gary-style male-audience Douyin copy production.
---

# 男版扩写

This is the short, UI-friendly Chinese alias for the full male-facing skill:

`/Users/kin/.codex/skills/douyin-copy-production-workflow-custom/SKILL.md`

When this alias is invoked, follow the full workflow in `douyin-copy-production-workflow-custom` as the source of truth.

Use it for:

- 男版扩写
- 抖音文案工作流
- 处理这批文案
- Gemini 本地命令扩写
- 三版新版开头
- 长文稿 Word 导出
- Gary-style male relationship copy production

Important:

- 2026-10-09用户校正：每次使用2.5扩写，复制完整固定旧2.5会话，再配完整提示词和本篇稿子；不是空白对话。必须先读主技能的 `references/2.5-legacy-session-copy.md`，该规则优先于旧的 `--isolated` 路由。

- Do not run a pre-expansion filtering step unless the user explicitly asks.
- Expand every provided source document by default.
- Use the original `douyin-copy-production-workflow-custom` skill instructions for all detailed steps, paths, retries, title packaging, openings, scoring, and Word export requirements.

用户指定2.0或未另指定版本的大号扩写，执行 `../douyin-copy-production-workflow-custom/SKILL.md` 中的2.0流程：分段分系统扩写拼接→skill优化AI与衔接→匹配开头→保留扩写前原开头对比；优化后最终正文至少15000中文字；支持按篇扩展独立观点数量，不为凑数拆分或重复观点。

用户明确指定2.2时，读取 `../gary-22-main-account-expansion/SKILL.md`。2.2目标8000—12000中文字、验收最低8000，每篇复制完整固定旧2.5会话；普通2.5不改。
2.2分支统一服从该独立技能的完整历史发送、同篇短稿分段回退、第二版尺度轻改和固定模板/原文双开头合同；不继承本页普通版本的压缩会话、旧字数或三版开头要求。

For `4.0`, route first to the full skill’s `references/4.0-frozen-legacy-session.md`. Each article starts from a fresh copy of the same pinned old-2.5 baseline; never chain article sessions.
