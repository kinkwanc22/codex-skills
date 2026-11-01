#!/usr/bin/env python3
"""Prepare one 2.2 request and a complete legacy-session copy; never call Gemini."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-file',required=True,type=Path)
    ap.add_argument('--run-dir',required=True,type=Path)
    args=ap.parse_args()
    if args.source_file.suffix.lower() not in {'.txt','.md'}:
        ap.error('Extract the actual source body to UTF-8 .txt or .md first')
    source=args.source_file.read_text(encoding='utf-8-sig').strip()
    if not source:ap.error('Source body is empty')
    skill=Path(__file__).resolve().parents[1]
    prompt=(skill/'references/2.2-direct-draft-prompt.txt').read_text(encoding='utf-8')
    if not prompt.endswith('【原文开始】\n'):
        ap.error('The complete 2.2 prompt is missing its source delimiter')
    run=args.run_dir.resolve()
    if run.exists():ap.error('Run directory already exists; use a fresh directory per article or retry')
    run.mkdir(parents=True)
    (run/'source.txt').write_text(source+'\n',encoding='utf-8')
    (run/'prompt.txt').write_text(prompt+source+'\n',encoding='utf-8')
    subprocess.run([sys.executable,str(skill/'scripts/prepare_legacy_session.py'),'--work-dir',str(run)],check=True,capture_output=True,text=True)
    provenance=json.loads((run/'legacy_session_provenance.json').read_text(encoding='utf-8'))
    manifest={'mode':'2.2','state':'prepared_not_generated','target_cjk_min':8000,'target_cjk_max':12000,'acceptance_cjk_min':8000,'hard_upper_limit':None,'source_original_path':str(args.source_file.resolve()),'frozen_source':str(run/'source.txt'),'source_sha256':hashlib.sha256((run/'source.txt').read_bytes()).hexdigest(),'prompt_file':str(run/'prompt.txt'),'prompt_sha256':hashlib.sha256((run/'prompt.txt').read_bytes()).hexdigest(),'prompt_template_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'legacy_session':provenance,'runner_workdir':'/Users/kin/Documents/Codex/2026-07-02/gemini','runner_argv':['./scripts/run_gemini_chat.sh','--prompt-file',str(run/'prompt.txt'),'--session-file',str(run/'session.json'),'--output-file',str(run/'raw.txt')]}
    (run/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__':main()
