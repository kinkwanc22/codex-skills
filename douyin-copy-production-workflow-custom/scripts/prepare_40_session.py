#!/usr/bin/env python3
"""Stage one 4.0 article from the immutable legacy baseline. No model call."""
import argparse
import hashlib
import json
from pathlib import Path

BASELINE = Path('/Users/kin/Documents/Codex/2026-07-02/gemini/work/4.0_legacy_baseline/session.json')
BASELINE_SHA = '30c4109b440815e5c1c668d188ae72723f9eef99ac4fee5e49ae5377e8fbfb3c'
PROMPT_SHA = 'a0d27aa2d81a314cf5286499a2bae9ed7997f4468767a867cc0d077ebe204898'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--work-dir', required=True, type=Path)
    p.add_argument('--baseline', type=Path, default=BASELINE,
                   help='Alternate location allowed only with the same pinned hash')
    a = p.parse_args()
    baseline = a.baseline.read_bytes()
    if digest(baseline) != BASELINE_SHA:
        p.error('Baseline hash mismatch. Do not substitute a live or generated session.')
    prompt_path = Path(__file__).resolve().parents[1] / 'references/4.0-old25-prompt.txt'
    block = prompt_path.read_bytes()
    if digest(block) != PROMPT_SHA:
        p.error('Pinned 4.0 prompt hash mismatch.')
    source = a.source.read_text(encoding='utf-8').strip()
    if not source:
        p.error('Source manuscript is empty.')
    if a.work_dir.exists():
        p.error('Article directory already exists. Use a fresh directory; never reuse sessions.')
    a.work_dir.mkdir(parents=True, exist_ok=False)
    (a.work_dir / 'session.json').write_bytes(baseline)
    (a.work_dir / 'source.txt').write_text(source + '\n', encoding='utf-8')
    (a.work_dir / 'prompt.txt').write_text(block.decode('utf-8') + source + '\n【原文结束】\n', encoding='utf-8')
    manifest = {'version': '4.0', 'baseline': str(a.baseline.resolve()),
                'baseline_sha256': BASELINE_SHA, 'prompt_block_sha256': PROMPT_SHA,
                'source_sha256': digest((source + '\n').encode('utf-8')),
                'session': str((a.work_dir / 'session.json').resolve()),
                'state': 'prepared_not_generated'}
    (a.work_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))

if __name__ == '__main__':
    main()
