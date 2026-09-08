# 本机运行与历史

技能目录包含独立runner原样副本、知识检索脚本原样副本、独立基准与归档。脚本用相对路径定位技能，安装后不依赖旧综合技能。

本机私有内容在 `.local/`，已从Git同步排除：
- legacy_baseline.json：旧2.5只读基准，SHA256 30c4109b440815e5c1c668d188ae72723f9eef99ac4fee5e49ae5377e8fbfb3c。
- copy_manifest.json：每个原件、复制件、大小和SHA256。复制时逐件核对；历史为快照，原会话后续新增内容不自动回填。
- archive/project：完整work与outputs及当时项目规则/状态/模板。
- archive/conversation：本任务可定位的本地原始会话文件。不是所有可能存在的远程或已丢失历史；不宣称补齐不可取得内容。
- archive/original_manuscripts：用户给出的原稿目录。
- archive/old_skill：旧综合skill及支持文件原样归档。仅查历史，不加载为当前规则。

重点案例：archive/project/work/formal_day01 为A；formal_day01_v2 为用户认可B。B换芯1178字，扩写4115字，无案例换芯+指定案例提示。用户认可发生在归档会话中；当时旧CURRENT_CONTEXT仍写待评价，以上述最新确认覆盖。

知识脚本保留原有外部依赖：/Users/kin/Gary 男性情感/Gary 男性情感（知识库），/Users/kin/Documents/Codex/2026-07-10/qu/work/obsidian_cross_source/final_modules.json，及qu/scripts/query_31_32_history.py。知识库未完整复制；正常检索仍读取现有资料。

API凭据不复制、不显示、不写Git。flow.py读取原运行环境 /Users/kin/Documents/Codex/2026-07-02/gemini/.env.local 或环境变量；只借凭据，runner和母会话已独立。GARY35_ENV_FILE可指定凭据文件。模型参数在flow.py固定为获认可配置。只允许TeamRouter /v1/地址。

Mac为本技能已实测环境。Git同步不等于Windows私有档案、母会话及知识库自动迁移；Windows未另行验证前不可声称双端可用。历史需随迁时单独复制.local并按清单校验，勿发布到共享仓库。
