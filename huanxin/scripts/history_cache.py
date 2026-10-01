"""Compact local retrieval cache. No model calls or automatic semantic verdicts."""
from pathlib import Path
import argparse
import hashlib
import json
import re

FIELDS = ('core_mechanism', 'action_chain', 'dominant_causal_chain', 'desired_result')

def fingerprint(record):
    # Include actual archived text, not just declared artifact hashes.
    return hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def cache_path(home, record):
    key = hashlib.sha256(str(record['id']).encode()).hexdigest()
    return home / 'summary-cache' / (key + '.json')

def summary(home, record):
    path = cache_path(home, record)
    stamp = fingerprint(record)
    if path.exists():
        cached = json.loads(path.read_text())
        if cached.get('record_sha256') == stamp:
            return cached, True
    route = record.get('mechanism_novelty') or {}
    points = record.get('viewpoints') or record.get('replacement_operations') or []
    result = {'id': record['id'], 'title': record.get('title', ''),
              'record_sha256': stamp, 'summary_origin': 'existing_metadata',
              'mechanism_novelty': route, 'viewpoints': points,
              'summary_sufficient': bool(route.get('action_chain') and points),
              'semantic_summary_verified': False}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result, False

def save_summary(home, record, supplied):
    # Caller must have read this exact revision. Reject stale notes.
    if supplied.get('record_sha256') != fingerprint(record):
        raise ValueError('Record changed; read current source before saving summary')
    if not all(supplied.get(k) for k in ('operations', 'core_mechanism', 'desired_result', 'evidence')):
        raise ValueError('Summary needs operations, mechanism, result and read evidence')
    cached, _ = summary(home, record)
    cached.update({'viewpoints': supplied['operations'], 'summary_origin': 'reader_reviewed',
                   'summary_sufficient': True, 'semantic_summary_verified': True,
                   'evidence': supplied['evidence']})
    cached['mechanism_novelty'] = {**cached['mechanism_novelty'],
                                  'core_mechanism': supplied['core_mechanism'],
                                  'action_chain': supplied['operations'],
                                  'desired_result': supplied['desired_result']}
    cache_path(home, record).write_text(json.dumps(cached, ensure_ascii=False, indent=2))
    return cached

def excerpt(record, query, limit=2400):
    terms = [t for t in re.split(r'\s+', query.strip()) if t]
    blocks = []
    for artifact in record.get('artifacts_copied', []):
        paragraphs = [p.strip() for p in re.split(r'\n+|(?<=[。！？])', artifact.get('text', '')) if p.strip()]
        hits = [i for i, p in enumerate(paragraphs) if any(t in p for t in terms)]
        selected = sorted({j for i in hits for j in range(max(0, i-1), min(len(paragraphs), i+2))})
        if not selected:
            continue
        blocks.append({'source': artifact.get('original', artifact.get('copy', '')),
                       'text': '\n'.join(paragraphs[i] for i in selected)})
    remaining = limit
    shown = []
    for block in blocks:
        if remaining <= 0:
            break
        shown.append({**block, 'text': block['text'][:remaining]})
        remaining -= len(shown[-1]['text'])
    return {'id': record['id'], 'record_sha256': fingerprint(record),
            'query': query, 'matched': bool(blocks), 'excerpts': shown,
            'truncated': sum(len(b['text']) for b in blocks) > limit,
            'note': 'Only matching passages; no match is not evidence of novelty.'}

def main():
    import history
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['build', 'excerpt', 'save'])
    p.add_argument('--id')
    p.add_argument('--query')
    p.add_argument('--summary', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    records = json.loads((history.HOME / 'index.json').read_text())
    if a.action == 'build':
        rows = [summary(history.HOME, r) for r in records]
        result = {'records': len(rows), 'cache_hits': sum(hit for _, hit in rows),
                  'summary_sufficient': sum(s['summary_sufficient'] for s, _ in rows)}
    else:
        record = next(r for r in records if r['id'] == a.id)
        if a.action == 'excerpt':
            if not a.query:
                p.error('excerpt requires --query')
            result = excerpt(record, a.query)
        else:
            result = save_summary(history.HOME, record, json.loads(a.summary.read_text()))
    history.dump(a.output, result)
    print(a.output)

if __name__ == '__main__':
    main()
