#!/usr/bin/env python3
"""Draw candidates without recording them; record only a delivered topic batch."""
import argparse
import datetime
import json
import random
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

def canonical(name):
    for aliases, normalized in [
        (('蔡加尼克', '蔡格尼克', '蔡加尼格'), '蔡格尼克效应'),
        (('晕轮效应', '光环效应'), '光环效应'),
        (('熟人效应',), '熟人效应'),
        (('父母投射',), '父母投射'),
        (('最小兴趣原则', '最小利益原则'), '最小利益原则'),
    ]:
        if any(a in name for a in aliases):
            return normalized
    return re.sub(r'[\W_]+', '', name)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--count', type=int, default=7)
    p.add_argument('--domain', choices=['心理学', '生物学', '社会学', 'PUA'])
    p.add_argument('--exclude', default='')
    p.add_argument('--out', type=Path)
    p.add_argument('--record', type=Path)
    p.add_argument('--history', type=Path, default=Path.home()/'.codex/topic-system/usage.jsonl')
    p.add_argument('--knowledge-root', type=Path, default=Path('/Users/kin/Gary 男性情感/Gary 男性情感'))
    a = p.parse_args()
    index = json.loads((SKILL/'references/mechanism-index.json').read_text(encoding='utf-8'))
    result_text = (SKILL/'references/strong-result-pool.md').read_text(encoding='utf-8')
    results = [dict(result_id=m[0], result=m[1].strip()) for m in
               re.findall(r'^\|\s*(SR-\d+)\s*\|\s*([^|]+)\|', result_text, re.M)]
    known_cards = {x['card_id'] for x in index}
    known_results = {x['result_id'] for x in results}
    if a.record:
        batch = json.loads(a.record.read_text(encoding='utf-8'))
        if not isinstance(batch, list) or not batch:
            p.error('record must contain a nonempty JSON array')
        seen = set()
        for row in batch:
            if not all(k in row for k in ['card_id', 'mechanism', 'result_id', 'count', 'title']):
                p.error('record row missing required fields')
            if row['card_id'] not in known_cards or row['result_id'] not in known_results:
                p.error('unknown card or result ID')
            if not isinstance(row['count'], int) or row['count'] < 1:
                p.error('operation count must be positive')
            key = canonical(row['mechanism'])
            if not key or key in seen or not row['title'].strip():
                p.error('empty or repeated mechanism/title in batch')
            seen.add(key)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        a.history.parent.mkdir(parents=True, exist_ok=True)
        with a.history.open('a', encoding='utf-8') as f:
            for row in batch:
                f.write(json.dumps(dict(row, recorded_at=timestamp), ensure_ascii=False)+'\n')
        print(json.dumps(dict(recorded=len(batch), history=str(a.history)), ensure_ascii=False))
        return
    if a.count < 1:
        p.error('count must be positive')
    history = [json.loads(line) for line in a.history.read_text(encoding='utf-8').splitlines()
               if line.strip()] if a.history.exists() else []
    recent = history[-30:]
    excluded = set(filter(None, a.exclude.split(','))) | {x['card_id'] for x in recent}
    recent_names = {canonical(x['mechanism']) for x in recent}
    pool = [x for x in index if x['card_id'] not in excluded
            and canonical(x['name']) not in recent_names
            and (not a.domain or x['domain'] == a.domain)]
    rng = random.SystemRandom()
    rng.shuffle(pool)
    selected = []
    seen = set()
    for row in pool:
        key = canonical(row['name'])
        if key in seen:
            continue
        seen.add(key)
        shuffled = results.copy()
        rng.shuffle(shuffled)
        selected.append(dict(row, source_path=str(a.knowledge_root/row['source']),
                             result_candidates=shuffled))
        if len(selected) == a.count:
            break
    if len(selected) < a.count:
        p.error(f'only {len(selected)} distinct eligible candidates; reduce count or exclusions')
    data = dict(history_rows=len(history), recent_window=30, pool_size=len(pool), candidates=selected)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text+'\n', encoding='utf-8')
        print(json.dumps(dict(drawn=len(selected), out=str(a.out), history_rows=len(history)), ensure_ascii=False))
    else:
        print(text)

if __name__ == '__main__':
    main()
