#!/usr/bin/env python3
"""Prepare a fresh 1.1 request; never calls the paid generation endpoint."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

CTA = '如果你现在【可变量】，可以直接到我的粉丝群。我结合你的情况给你具体的分析。回到刚刚的话题，我给兄弟们详细拆解一下，这里面的逻辑和具体技巧。'
def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-file', type=Path, required=True)
    p.add_argument('--opening-file', type=Path, required=True)
    p.add_argument('--pain-point', required=True)
    p.add_argument('--work-dir', type=Path, required=True)
    a = p.parse_args()
    if not a.pain_point.strip() or any(x in a.pain_point for x in ('\n', '【', '】')):
        p.error('pain-point must be one concrete single-line issue without placeholder brackets')
    source = a.source_file.read_text(encoding='utf-8').strip()
    opening = a.opening_file.read_text(encoding='utf-8').strip()
    if not source or not opening:
        p.error('source and selected opening must be nonempty')
    cta = CTA.replace('【可变量】', a.pain_point.strip())
    locked_n = cjk(opening + cta)
    if locked_n + cjk('我是探花Gary，感谢观看。') >= 1500:
        p.error('selected opening and CTA exhaust the 1.1 budget; review opening selection')
    if a.work_dir.exists() and any(a.work_dir.iterdir()):
        p.error('work-dir must be empty or new; existing session/raw will not be overwritten')
    skill = Path(__file__).resolve().parents[1]
    template = (skill / 'references/prompt.txt').read_text(encoding='utf-8')
    target = max(1, 1300 - locked_n - cjk('我是探花Gary，感谢观看。'))
    values = {'{{LOCKED_CJK}}': str(locked_n), '{{EXPANSION_TARGET_CJK}}': str(target),
              '{{OPENING}}': opening, '{{CTA}}': cta, '{{SOURCE}}': source}
    # Replace placeholders in the template only, never in injected source text.
    prompt = re.sub(r'\{\{(?:LOCKED_CJK|EXPANSION_TARGET_CJK|OPENING|CTA|SOURCE)\}\}',
                    lambda m: values[m.group(0)], template)
    prep = skill.parent / 'douyin-copy-production-workflow-custom/scripts/prepare_25_legacy_session.py'
    if not prep.exists():
        p.error('full legacy-session preparer is unavailable')
    a.work_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(prep), '--work-dir', str(a.work_dir.resolve())], check=True)
    shutil.copy2(a.source_file, a.work_dir / 'source.txt')
    for name, text in [('locked_opening.txt', opening), ('locked_CTA.txt', cta), ('prompt.txt', prompt)]:
        (a.work_dir / name).write_text(text, encoding='utf-8')
    manifest = {'mode': '1.1', 'source': str(a.source_file.resolve()),
                'source_sha256': hashlib.sha256(a.source_file.read_bytes()).hexdigest(),
                'locked_CJK': locked_n, 'new_expansion_target_CJK': target,
                'spoken_total_min_CJK': 1000, 'spoken_total_max_CJK': 1500,
                'includes_opening_CTA_ending': True, 'state': 'prepared_not_generated'}
    (a.work_dir / 'mode_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))
if __name__ == '__main__':
    main()
