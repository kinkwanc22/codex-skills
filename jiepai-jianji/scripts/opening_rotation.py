"""Persistent visual-group rotation; no media or draft mutation."""
import argparse, copy, datetime, hashlib, json, os, pathlib, sys

DEFAULT = '/Users/kin/工作用（同步）/千川素材文稿/.records/street_opening_rotation.json'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def allocate(state, batch_id, count):
    groups = [g for g in state['groups'] if g.get('enabled', True) and any(a.get('readable') for a in g['assets'])]
    if count < 1 or count > len(groups):
        raise ValueError(f'本批需要{count}组，可供不重复的启用组只有{len(groups)}组')
    cycle = state['cycle']; used = set(state['used_in_cycle']); chosen = []; selected = set()
    recent = set(state.get('last_batch_groups', []))
    while len(chosen) < count:
        pending = [g for g in groups if g['id'] not in used]
        if not pending:
            cycle += 1; used = set(); pending = groups
        candidates = [g for g in pending if g['id'] not in selected]
        if not candidates:
            raise ValueError('当前轮剩余组与本批已选冲突，禁止提前跳轮或同批复用')
        def rank(g):
            tie = hashlib.sha256((batch_id + g['id']).encode()).hexdigest()
            return (g['id'] in recent, g.get('last_used_at') or '', tie)
        g = min(candidates, key=rank)
        assets = sorted((a for a in g['assets'] if a.get('readable')), key=lambda a: (a.get('use_count', 0), a.get('last_used_at') or '', a['sha256']))
        chosen.append({'group_id': g['id'], 'label': g['label'], 'cycle': cycle, 'candidates': assets})
        selected.add(g['id']); used.add(g['id'])
    return {'batch_id': batch_id, 'created_at': now(), 'selections': chosen,
            'result_cycle': cycle, 'result_used_in_cycle': sorted(used),
            'starts_cycle': state['cycle'], 'crosses_cycle': cycle != state['cycle']}

def commit(state, batch_id, delivery):
    if any(h.get('batch_id') == batch_id and h.get('status') == 'committed' for h in state.get('history', [])):
        raise ValueError('该批已提交，禁止重复消耗轮回名额')
    plan = state.get('active_plan')
    if not plan or plan['batch_id'] != batch_id:
        raise ValueError('没有对应活动计划')
    selections = plan['selections']
    if len(delivery) != len(selections) or len({d['group_id'] for d in delivery}) != len(delivery):
        raise ValueError('交付数量或组去重不匹配')
    for s in selections:
        d = next((v for v in delivery if v['group_id'] == s['group_id']), None)
        if not d or not any(a['sha256'] == d['source_sha256'] for a in s['candidates']):
            raise ValueError('交付组/所选源与计划不符')
        if not (pathlib.Path(d['draft_path']) / 'draft_content.json').is_file():
            raise ValueError('正式后台草稿不存在')
    stamp = now()
    for s in selections:
        d = next(v for v in delivery if v['group_id'] == s['group_id'])
        g = next(g for g in state['groups'] if g['id'] == s['group_id'])
        g['last_used_at'] = stamp; g['use_count'] = g.get('use_count', 0) + 1
        a = next(a for a in g['assets'] if a['sha256'] == d['source_sha256'])
        a['last_used_at'] = stamp; a['use_count'] = a.get('use_count', 0) + 1
    state['cycle'] = plan['result_cycle']; state['used_in_cycle'] = plan['result_used_in_cycle']
    state['last_batch_groups'] = [s['group_id'] for s in selections]
    state.setdefault('history', []).append({'batch_id': batch_id, 'status': 'committed', 'at': stamp,
                                          'selections': selections, 'deliveries': delivery})
    state['active_plan'] = None

def main():
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['status', 'plan', 'commit', 'cancel'])
    p.add_argument('--state', default=DEFAULT); p.add_argument('--batch-id'); p.add_argument('--count', type=int)
    p.add_argument('--out'); p.add_argument('--delivery'); args = p.parse_args()
    target = pathlib.Path(args.state)
    if not target.is_file():
        raise ValueError('权威台账不存在；不能自动初始化空台账')
    if args.action == 'status':
        s = json.loads(target.read_text(encoding='utf8')); enabled = [g for g in s['groups'] if g.get('enabled', True) and any(a.get('readable') for a in g['assets'])]
        print(json.dumps({'cycle': s['cycle'], 'groups': len(s['groups']), 'enabled_groups': len(enabled),
                          'used_this_cycle': len(set(s['used_in_cycle']) & {g['id'] for g in enabled}),
                          'remaining_groups': [g['id'] for g in enabled if g['id'] not in s['used_in_cycle']],
                          'active_batch': (s.get('active_plan') or {}).get('batch_id')}, ensure_ascii=False, indent=2)); return
    if not args.batch_id:
        raise ValueError('必须指定batch-id')
    lock = pathlib.Path(str(target) + '.lock'); fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(fd); raw = target.read_bytes(); s = json.loads(raw)
        if args.action == 'plan':
            active = s.get('active_plan')
            if active and active['batch_id'] != args.batch_id:
                raise ValueError('另一个批次仍有活动计划：' + active['batch_id'])
            if any(h.get('batch_id') == args.batch_id and h.get('status') == 'committed' for h in s.get('history', [])):
                raise ValueError('此批已提交，不能重新随机')
            if not args.count or not args.out:
                raise ValueError('plan必须给count和out')
            if active and len(active['selections']) != args.count:
                raise ValueError('活动计划数量不同；不能静默改计划')
            result = active or allocate(s, args.batch_id, args.count)
            out = pathlib.Path(args.out)
            if out.exists() and json.loads(out.read_text(encoding='utf8')) != result:
                raise ValueError('不能覆盖不同的计划文件')
            out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
            s['active_plan'] = result
        elif args.action == 'commit':
            if not args.delivery: raise ValueError('commit必须给delivery')
            commit(s, args.batch_id, json.loads(pathlib.Path(args.delivery).read_text(encoding='utf8')))
        else:
            active = s.get('active_plan')
            if not active or active['batch_id'] != args.batch_id: raise ValueError('没有对应活动计划')
            s.setdefault('history', []).append({'batch_id': args.batch_id, 'status': 'cancelled', 'at': now(), 'plan': active})
            s['active_plan'] = None
        if target.read_bytes() != raw: raise ValueError('台账发生并发变化，停止覆盖')
        backups = target.parent / 'rotation_backups'; backups.mkdir(exist_ok=True)
        (backups / (str(s.get('revision', 0)) + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + '.json')).write_bytes(raw)
        s['revision'] = s.get('revision', 0) + 1; s['updated_at'] = now()
        temp = pathlib.Path(str(target) + '.tmp'); temp.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf8'); os.replace(temp, target)
        print(json.dumps({'action': args.action, 'batch_id': args.batch_id, 'revision': s['revision'], 'cycle': s['cycle']}, ensure_ascii=False))
    finally:
        lock.unlink()

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, KeyError) as e: print(str(e), file=sys.stderr); sys.exit(1)
