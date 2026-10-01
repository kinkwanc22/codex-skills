"""Cheap ordinary-2.8 mechanical facts; never a semantic acceptance verdict."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ENDING = '我是探花Gary，我们粉丝群里见，感谢观看。'
HINTS = ('知识库案例', '学员原始问题', '我的具体指导', '可观察反馈',
         '原稿', '提示词', '换芯', 'source_path', 'mechanism_novelty')

def check(draft, minimum=3000):
    raw = draft.read_bytes()
    text = raw.decode('utf-8-sig')
    count = len(re.findall(r'[\u3400-\u9fff]', text))
    clean = lambda s: re.sub(r'\s+', '', s)
    return {'schema_version': 1, 'route': 'ordinary_2.8',
            'draft_sha256': hashlib.sha256(raw).hexdigest(),
            'cjk': count, 'minimum_cjk': minimum, 'length_met': count >= minimum,
            'terminal_ending_met': clean(text).endswith(clean(ENDING)),
            'wording_hints': [{'term': term, 'count': text.count(term)}
                              for term in HINTS if term in text],
            'semantic_review_required': True,
            'note': 'Hints need context review. No automatic acceptance or rerun decision.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--draft', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--minimum-cjk', type=int, default=3000)
    a = p.parse_args()
    if a.minimum_cjk <= 0:
        p.error('minimum must be positive')
    if a.output.resolve() == a.draft.resolve():
        p.error('output cannot overwrite draft')
    report = check(a.draft, a.minimum_cjk)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(a.output)

if __name__ == '__main__':
    main()
