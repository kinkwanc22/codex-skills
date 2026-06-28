# Source Learning And Style Rules

Read this file when processing a batch, learning source viral logic, classifying source styles, preserving source openings, or shaping later openings/title packaging.

## Contents

- Direct batch expansion policy
- Source and expanded-copy learning note
- Expanded-hit sample style
- Source-to-hit reverse style
- Source opening style scoring

### 1. Direct Batch Expansion

When the user provides a batch of `.docx` scripts, do not run a pre-expansion scoring, ranking, filtering, or top-N selection step by default. Treat every user-provided source document as part of the expansion queue unless the user explicitly asks to process only specific files.

Do not invoke `douyin-emotion-copy-scorer` for upfront screening. Use it only if the user explicitly asks for scoring/review, or for a post-generation viral potential check after a draft already exists.

Batch order:

- Preserve the source folder's stable filename order unless the user provides an explicit order.
- Expand each source from its original text with the full Gemini instruction block.
- If a source cannot be read or repeatedly fails generation, record it in the batch log and continue to the next source.
- Do not reject files merely because their topic, opening, likes, or structure seem weaker than others.

### 1.5. Learn Source And Expanded Viral Logic

Every time the user provides source documents, learn and record the viral-copy logic from both the source documents and the expanded outputs without using that learning as a gate that filters documents out of the batch.

Source document learning:

- For each source `.docx`, identify its viral genes:
  - opening hook type
  - core pain point
  - conflict / controversy angle
  - psychological mechanism
  - usable dark/high-level framing
  - collection or replay value
  - platform-risk wording to be aware of, without adding risk suggestions to final Word output
- Summarize what makes the source potentially explosive, but do not exclude it from expansion based on this analysis.
- Extract reusable patterns such as title formula, first 3 seconds hook, topic setup, metaphor, case structure, transition rhythm, and closing call-to-action.

Expanded output learning:

- After each local Gemini expansion passes length and topic checks, analyze the expanded copy's logic:
  - whether it preserved the source topic
  - what new structure the expansion added
  - which sections became stronger than the source
  - which parts became noisy, risky, repetitive, or off-topic
  - what can be reused in later openings, outlines, or expansion prompts
- If a generated output is too sensitive, too short, truncated, or off-topic, record the failure pattern and avoid repeating it when retrying.

Learning artifact:

- For every batch, create or update a concise learning note in the current workspace outputs folder, named like `批次名_爆款逻辑学习.md`.
- The note should include:
  - expansion queue and source order
  - source viral logic summary
  - expanded-copy logic summary
  - reusable opening / structure / metaphor patterns
  - failure patterns and retry lessons
- Keep this learning note separate from the final Word documents.
- Do not let the learning step slow down final delivery; it should be concise and practical.


### Expanded Hit Sample Style Reference

The user has provided expanded long-form viral samples as the preferred future direction. Use this sample-derived style to shape openings, title packaging, retries, and batch learning notes, but do not use it to filter the expansion queue unless the user explicitly requests selection.

Prioritize source scripts that can become a high-density long lesson with these traits:

- **Complete-course framing**: titles or openings like `完整剖析`, `全套实操`, `完整版解析`, `最后一期`, `未删减`, `看我这一期就够了`, `补齐认知差`.
- **Psychological mechanism core**: 损失厌恶、间歇性强化、沉没成本、预选机制、心理逆反、多巴胺、催产素、社交面具、自我暴露、潜意识绑定.
- **Dark/high-level packaging**: 黑暗思维、禁术、隐秘癖好、真实欲望、恋爱脑、上头、沦陷、离不开、拿捏、两性博弈底层代码.
- **Numbered framework expandability**: 三步、六大机制、八大内核、十二个思维、十六个习惯、三十六个问题, or any source that can naturally split into 3-6 mechanisms or 8-18 checklist points.
- **Technique-course packaging**: note when a source can be turned into practical skills, moves, exercises, operating steps, scripts, response templates, chat tactics, screening methods, field drills, or 几招/几步/技巧/话术/方法/策略/训练/操作系统 because these create stronger save/replay value and easier editing hooks.
- **Male identity transformation**: 低位供养者 / 舔狗 / beta / 被动挨打 -> 高位筛选者 / 规则制定者 / alpha / 关系主权.
- **Female psychology portrait**: 试探、慕强、道德伪装、社交认同、不确定性、隐秘欲望, especially when the script exposes a hidden motive or unconscious mechanism.
- **Business and dating analogy**: scripts that connect relationships with money, resources, hierarchy, competition, networks, screening, and leverage.
- **Collection value**: source material that can support 思维导图、复盘、清单、系统课、系列课.

Style risks even if likes are high:

- Pure warm relationship advice with no mechanism, conflict, or male pain point.
- Pure emotional venting that cannot be expanded into a structured lesson.
- Female-oriented material that cannot be converted into male relationship sovereignty, screening, or self-upgrade framing.
- A provocative title whose body lacks pain point, case, mechanism, and executable structure.

If the user explicitly asks for selection, prefer candidates that fit this expanded-hit-sample style over scripts that only have high like counts. In the default workflow, expand all provided files.

### Source-To-Hit Reverse Style Rules

The user has provided paired source + expanded-hit samples. Use these rules to understand which viral features to preserve and amplify during expansion, opening writing, and title packaging.

Primary style principle: a **short but sharp source** often expands better than a long but scattered one. A good source should contain a viral mother-topic that can become a 1000-2000-character complete short lesson, but weaker sources still remain in the default expansion queue.

High-priority source archetypes:

1. **Mechanism / forbidden-technique type**
   - Examples: 心锚、不配得感、恋爱脑、白月光、训狗式反馈、间歇性强化、沉没成本、潜意识绑定.
   - Source signals: `黑暗`, `很脏`, `禁术`, `无解`, `潜意识`, `沦陷`, `离不开`, `上头`, `拿捏`.

2. **Male identity reversal type**
   - Examples: 八大内核、框架习惯、十六个信号、十个特质.
   - Source signals: 舔狗、beta、供养者、没框架、被动挨打 -> alpha、高位、规则制定者、关系主权.

3. **Technique / practical skill type**
   - Examples: 7招让女生喜欢你、两点让她从冷淡到粘人、夸人技巧、聊天推进方法、低位逆袭高位操作、情绪价值四层级、见面/断联/抽离/筛选实操.
   - Source signals: 招、技巧、方法、策略、步骤、话术、训练、操作、推进、怎么做、如何让、只需要、学会、掌握、实操、案例复盘.
   - Best expansion structure: 场景 -> 错误动作 -> 底层机制 -> 高位动作 -> 话术/动作示范 -> 复盘练习.
   - Style note: if it can become a teachable technique course with concrete viewer actions, preserve that practical structure during expansion.

3. **Test / defense checklist type**
   - Examples: 废物测试、危险信号、十八条法则.
   - Source signals: 测试、信号、法则、类型、图鉴、判断、远离、撤离.
   - Best expansion structure: 表现 -> 潜台词 -> 错误反应 -> 高位处理.

4. **Female psychology profile type**
   - Examples: 隐秘癖好、女性思维、女性行为侧写、利用天性.
   - Source signals: specific behavior portrait + hidden motive + interaction consequence.

5. **Relationship attack/defense type**
   - Examples: 心有所属、挖墙脚、掠夺者、防守关系漏洞.
   - Source signals: 挖墙脚、负罪感、竞争者、关系漏洞、被替代、心有所属.
   - Package as 机制识别、防御风险、关系主权 and boundary judgment.

6. **Cross-domain equivalence type**
   - Examples: 泡妞与赚钱同构、商业/人脉/阶层/资源/竞争.
   - Source signals: 赚钱、资源、阶层、商业、博弈、价值、框架、竞争.

A source has strong expansion potential if it meets at least 4 of these 8 checks:

- The first 300 characters contain pain, conflict, or a counterintuitive claim.
- It clearly explains why the male viewer loses.
- It clearly explains why the woman reacts this way.
- It has a nameable mechanism.
- It can split into 3-6 mechanisms or 8-18 signals/laws/habits/traits.
- It can support concrete scenes or cases.
- It can be packaged as a concrete technique lesson: steps, moves, scripts, drills, templates, or repeatable operations.
- It can convert into male relationship sovereignty, screening, boundary, inner-core, value, or frame.
- It has collection/replay value: checklist, diagram, stages, formula, question bank, or field guide.

Style risks to watch during expansion:

- Emotion-only scripts with no mechanism name.
- Opinion-only scripts with no case, stage, or checklist.
- Provocative titles whose body cannot explain the underlying cause.
- Generic gender-difference talk with no interaction scene.
- Warm advice, pure empathy, or plain chat-line collections.

When processing a batch, optionally classify every source into these archetypes for the learning note and title/opening strategy. Do not use the classification to skip a source unless the user explicitly asks for source selection.

### Source Opening Style Rules

When evaluating unexpanded source files, separately analyze the original source opening, especially the first 30, 100, and 300 Chinese characters. A strong source opening is often useful for preserving the source's viral genes in the expanded draft.

High-performing original opening archetypes learned from the user's samples:

1. **Dark reveal opening**
   - Signals: `今天聊个黑暗的`, `今天讲一个很脏的东西`, `禁术`, `无解`, `很脏`, `毫无下限`.
   - Must connect quickly to a nameable mechanism and a strong result, such as 沦陷、忘不了、依赖、离不开、动心.

2. **Result-promise opening**
   - Signals: `如果你能听懂`, `如果你掌握`, `你会...`, `你的择偶思维会被重塑`, `降维打击`.
   - Best when followed by a clear structure such as 三点、五件事、六个习惯、三十六个问题.

3. **Identity-shame naming opening**
   - Signals: 舔狗、beta、供养者、没框架、工具人、被女人定义、低位.
   - Must also imply a reversal path: 逆转框架、重塑内核、提升吸引、夺回主权.

4. **Numbered collection opening**
   - Signals: 八大、十六个、十八条、三十六个、总偏集、所有类型、所有变种、点赞收藏、随时查阅.
   - Strong because it creates replay and collection value.

5. **Counterintuitive mechanism opening**
   - Signals: `为什么`, `答案只有一个`, `其实很简单`, `底层逻辑`, `本质`, `普通人以为...其实...`.
   - Best when it overturns common male assumptions and immediately names the deeper mechanism.

6. **Crisis-defense opening**
   - Signals: 危险信号、废物测试、挖墙脚、被替代、撤离、重新思考相处策略.
   - Best when it promises identification, defense, and relationship sovereignty.

Optional opening style score: 20 points.

- 5 points: first 30 characters have a strong hook, question, taboo word, or result promise.
- 5 points: first 100 characters include a mechanism name or counterintuitive judgment.
- 5 points: first 300 characters name a male pain point or low-position identity.
- 5 points: first 300 characters show structure and collection value: list, stages, formula, field guide, question bank, or full lesson.

Style interpretation:

- 15-20: preserve and amplify the original opening logic.
- 10-14: keep the hook but strengthen mechanism and structure in generated openings.
- Below 10: rebuild the opening strategy during the three-version opening step, while still expanding the source.
