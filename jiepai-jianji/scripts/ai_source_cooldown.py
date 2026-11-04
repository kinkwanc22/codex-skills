"""Persistent AI-video source cooldown: appearances must be >=3 deliveries apart."""
import argparse
import hashlib
import json
import os
from pathlib import Path

DEFAULT = '/Users/kin/Documents/Codex/shared_state/ai_mixed_source_cooldown.json'


def read(path):
    return json.loads(Path(path).read_text())


def identify(row):
    p = Path(row.get('path') or row['source']).resolve()
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    keys = {'sha256:' + h.hexdigest(), 'path:' + str(p)}
    if row.get('canonical_source_id'):
        keys.add('canonical:' + str(row['canonical_source_id']))
    if row.get('source_identity'):
        keys.add('identity:' + str(row['source_identity']))
    return {'path': str(p), 'keys': sorted(keys)}


def inspect(state, sources):
    events = state['deliveries']
    seq = len(events) + 1
    conflicts, duplicates = [], []
    # Join aliases transitively across historical identity records.
    records = [s for event in events for s in event['sources']] + sources
    aliases = [set(s['keys']) for s in records]

    def expanded(keys):
        result = set(keys)
        while True:
            before = len(result)
            for group in aliases:
                if result & group:
                    result.update(group)
            if len(result) == before:
                return result

    seen = set()
    for source in sources:
        keys = expanded(source['keys'])
        if seen & keys:
            duplicates.append(source['path'])
        seen.update(keys)
        for event in events[-2:]:
            if any(keys & set(s['keys']) for s in event['sources']):
                conflicts.append({'path': source['path'], 'last_sequence': event['sequence'],
                                  'earliest_sequence': event['sequence'] + 3})
    return {'next_sequence': seq, 'previous_two': [e['draft_key'] for e in events[-2:]],
            'cooldown_conflicts': conflicts, 'within_video_duplicates': duplicates,
            'passed': not conflicts and not duplicates}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['check', 'commit'])
    ap.add_argument('--ledger', default=DEFAULT)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--draft-key')
    args = ap.parse_args()
    ledger = Path(args.ledger)
    if not ledger.exists():
        raise SystemExit('Missing ledger: recover shared history first; do not reset silently')
    lock = Path(str(ledger) + '.lock')
    if args.command == 'commit':
        if not args.draft_key:
            ap.error('--draft-key required for commit')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError:
            raise SystemExit('Ledger locked; inspect active writer, do not overwrite')
    try:
        state = read(ledger)
        if args.command == 'commit' and any(e['draft_key'] == args.draft_key for e in state['deliveries']):
            raise SystemExit('Delivery key already committed; no second sequence consumed')
        sources = [identify(r) for r in read(args.plan) if r.get('kind', 'video') == 'video']
        if not sources:
            raise SystemExit('Empty source plan')
        result = inspect(state, sources)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result['passed']:
            raise SystemExit(1)
        if args.command == 'commit':
            state['deliveries'].append({'sequence': result['next_sequence'],
                                       'draft_key': args.draft_key, 'sources': sources})
            tmp = Path(str(ledger) + '.tmp')
            tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            os.replace(tmp, ledger)
    finally:
        if args.command == 'commit':
            lock.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
