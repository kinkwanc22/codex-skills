# Hook Trainer Data Contracts

## Input Folder

Supported source formats:

- `.txt`
- `.md`
- `.srt`
- `.docx`

Each file is treated as one source script.

Hook text should usually be about 50 Chinese characters when the source text is long enough. Skip source metadata such as `标题：` and `点赞量：` before extracting the hook.

## parsed.json

```json
[
  {
    "source_id": "stable-id",
    "file_path": "demo.txt",
    "file_name": "demo.txt",
    "file_type": "txt",
    "text": "full normalized script text",
    "char_count": 1234
  }
]
```

## analysis.json

```json
[
  {
    "source_id": "stable-id",
    "file_path": "demo.txt",
    "file_name": "demo.txt",
    "niche": "男性情感",
    "hook": "opening text",
    "hook_type": "反常识",
    "emotion": "焦虑",
    "rhythm": "短句推进",
    "information_gap": "why the viewer needs to keep watching",
    "template": "你以为X，其实真正影响结果的是Y",
    "notes": "rule-based V1 analysis"
  }
]
```

## hooks.json

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-30T00:00:00+00:00",
  "hooks": []
}
```

## search_results.json

```json
{
  "query": {
    "niche": "男性情感",
    "emotion": "焦虑"
  },
  "count": 20,
  "results": []
}
```

## formula_library/formula_library.json

Contains reusable formulas grouped by:

- `fine_frame`: detailed hook frame such as 黑暗真相式, 高位警告式, 反人性式
- `sentence_pattern`: sentence shape such as 问题追问句, 高压警告句
- `formula`: reusable variable formula
- `count`: number of source openings matching the formula
- `keywords`: frequent words for matching
- `examples`: representative source openings

## formula_library/opening_library.json

Contains 100-200 reusable openings. Each item includes:

- source file
- hook
- coarse type
- fine frame
- sentence pattern
- formula
- keywords
- score
- rank

Use this file to match future topics or draft scripts.

## formula_library/high_frequency_words.json

Contains high-frequency words and phrases extracted from all hook openings.

## generated_openings.json

Generated openings for a new article or topic.

Each result includes:

- `rank`
- `frame`: formula frame such as 黑暗真相式 or 高位警告式
- `opening`: newly generated opening text
- `used_words`: article variables and high-frequency words used in the opening
- `scores`: theme fit, explosive word density, conflict, information gap,口播顺滑度,综合分

Generation rule:

- Do not copy old openings directly.
- Extract variables from the new article.
- Inject high-frequency words naturally.
- Keep openings about 50-70 Chinese characters by default.
