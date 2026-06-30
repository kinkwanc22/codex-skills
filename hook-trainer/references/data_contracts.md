# Hook Trainer Data Contracts

## Input Folder

Supported source formats:

- `.txt`
- `.md`
- `.srt`
- `.docx`

Each file is treated as one source script.

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
