#!/usr/bin/env python3
"""Copy the complete pinned old 2.5 history; never call a model."""
import argparse
import hashlib
import json
from pathlib import Path

BASELINE=Path('/Users/kin/Documents/Codex/2026-07-02/gemini/work/4.0_legacy_baseline/session.json')
EXPECTED='30c4109b440815e5c1c668d188ae72723f9eef99ac4fee5e49ae5377e8fbfb3c'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',required=True,type=Path)
    args=parser.parse_args()
    data=BASELINE.read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if digest!=EXPECTED: parser.error('Pinned legacy baseline hash mismatch')
    json.loads(data)
    args.work_dir.mkdir(parents=True,exist_ok=True)
    target=args.work_dir/'session.json'
    with target.open('xb') as stream: stream.write(data)
    assert target.read_bytes()==data
    record={'mode':'2.5_complete_legacy_copy','baseline':str(BASELINE),'baseline_sha256':digest,'initial_session_sha256':digest,'session':str(target.resolve()),'state':'prepared_not_generated','baseline_modified':False}
    with (args.work_dir/'legacy_session_provenance.json').open('x',encoding='utf-8') as stream:
        json.dump(record,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print(json.dumps(record,ensure_ascii=False))

if __name__=='__main__': main()
