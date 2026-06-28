---
name: douyin-emotion-copy-scorer
description: Score, rank, and select Douyin/TikTok Chinese male relationship/emotional self-media scripts using a reusable viral-copy gene rubric. Use when the user asks to analyze assistant-collected scripts, score 鐖嗘鏂囨, rank topics, choose which copy to expand, build an 鎵╁啓姹? compare titles/like counts, or evaluate 鐢锋€ф儏鎰熼鍩熸枃妗?for hooks, pain points, mechanism strength, expandability, collectability, controversy, and publishability.
---

# Douyin Emotion Copy Scorer

Use this skill to turn a batch of assistant-collected Chinese relationship scripts into a ranked expansion queue.

Core outcome: tell the user which scripts are worth expanding, why, what viral model each script belongs to, how to rewrite risky angles, and which scripts should be rejected or only used as reference material.

## Workflow

1. **Extract Inputs**
   - For `.docx`, extract title, like count, first 300-500 characters, and body length.
   - For pasted text, split by title or item boundary.
   - Treat like count as market validation, not the final ranking.

2. **Score Each Script**
   - Read `references/scoring-rubric.md`.
   - Score each script on the 100-point rubric.
   - Prioritize fit for the user's male emotional self-media account over raw popularity.


2.5. **Apply Expanded-Hit-Sample Fit**
   - Before final ranking, compare every candidate with the user's preferred expanded viral samples.
   - Add priority to scripts that can become a `完整课 / 机制课 / 禁术感长课 / 数字清单课`.
   - Strong sample-fit topics include: 底层逻辑、完整剖析、全套实操、黑暗思维、高阶心理博弈、潜意识、损失厌恶、间歇性强化、恋爱脑、隐秘癖好、女性真实欲望、男性内核、alpha/beta、关系主权、泡妞与赚钱同构.
   - Prefer scripts that can split into 3-6 mechanisms or 8-18 checklist points, with scenes, wrong moves, correct frames, and replay value.
   - Lower the ranking of pure emotional comfort, pure chicken-soup advice, or high-like scripts that lack mechanism depth and male pain-point conversion.

2.6. **Reverse-Select From Source-To-Hit Samples**
   - Prefer source scripts that can grow into the user's preferred expanded-hit forms: 机制禁术型、男性身份逆转型、测试与防御清单型、女性心理侧写型、关系掠夺与防守型、跨域同构型.
   - A strong source does not need to be long, but it must be sharp: one nameable mechanism, one clear male pain point, one conflict, and a structure that can become a long lesson.
   - Give extra rank to sources whose first 300 characters already contain pain/conflict/counterintuitive framing and can split into 3-6 mechanisms or 8-18 laws/signals/habits.
   - Reduce priority for scripts that only provide warmth, empathy, generic gender talk, or scattered chat lines without a mechanism/case/checklist backbone.

2.7. **Score Original Source Opening**
   - Separately score the original source opening before ranking the expansion queue.
   - Use the first 30 / 100 / 300 Chinese characters to judge hook strength, mechanism clarity, male pain-point naming, and structure/collection value.
   - Strong opening archetypes: 黑暗揭底式、结果承诺式、身份羞耻点名式、数字清单收藏式、反常识机制式、危机防御式.
   - Add strong priority when the opening reaches 15+ on the 20-point opening score.
3. **Classify Viral Model**
   Assign one or two models:
   - 榛戞殫绂佹湳鍨?   - 鎬诲亸闆嗘敹钘忓瀷
   - 鐢锋€ц閱掑瀷
   - 鏀婚槻澶嶇洏鍨?   - 濂虫€х敾鍍忓瀷
   - 鎯呯华涓绘潈鍨?   - 浜插瘑鏈哄埗鍨?
4. **Rank And Decide**
   Use these thresholds:
   - 85+: 褰撳ぉ浼樺厛鎵╁啓
   - 75-84: 鏀惧叆搴撳瓨鎴栦簩绾挎墿鍐欐睜
   - 65-74: 鍙繚鐣欓€夐, 闇€瑕侀噸鏋勫紑澶?   - below 65: 涓嶅缓璁姇鍏ュ壀杈戞椂闂?
5. **Output**
   Always provide:
   - 鎬绘帓鍚嶈〃
   - 褰撳ぉ鏈€鍊煎緱鎵╁啓鐨?3-5 鏉?   - 涓嶅缓璁紭鍏堝仛鐨勬潯鐩?   - 鍙粍鍚堟垚绯诲垪鐨勯€夐
   - 缁欏姪鐞嗙殑閲囬泦鍙嶉
   - 鎺ㄨ崘杩涘叆鎵╁啓姹犵殑鍒嗙粍

6. **Risk Handling**
   If a script contains manipulative, coercive, harassment-like, or platform-risk wording, preserve the analytical edge but rewrite the recommendation toward:
   - 鏈哄埗璇嗗埆
   - 椋庨櫓闃插尽
   - 杈圭晫鍒ゆ柇
   - 鎯呯华涓绘潈
   - 鍏崇郴鑺傚绠＄悊

Do not recommend publishing direct coercion, stalking, threats, harassment, non-consensual pressure, or executable manipulation tactics.

## Output Format

Use Chinese. Keep the response practical and decision-oriented.

For batch scoring, use this structure:

```markdown
## 鎬绘帓鍚?
| 鎺掑悕 | 缂栧彿 | 鏍囬绠€鍐?| 鐐硅禐閲?| 鎬诲垎 | 鐖嗘妯″瀷 | 澶勭悊寤鸿 |
|---:|---:|---|---:|---:|---|---|

## 鏈€鍊煎緱鎵╁啓

1. ...

## 涓嶅缓璁紭鍏堝仛

...

## 鍙粍鍚堢郴鍒?
...

## 缁欏姪鐞嗙殑閲囬泦鍙嶉

...
```

If the user asks for a saved report, create a Markdown file in the current workspace.




