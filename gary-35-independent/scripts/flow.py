#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,os,sys,importlib.util
ROOT=Path(__file__).resolve().parents[1]
BASE_HASH='30c4109b440815e5c1c668d188ae72723f9eef99ac4fee5e49ae5377e8fbfb3c'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','expand']);p.add_argument('--source',type=Path);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args();r=a.run_dir.resolve()
 if a.action=='prepare':
  if not a.source:p.error('--source required')
  b=(ROOT/'.local/legacy_baseline.json').read_bytes();assert sha(b)==BASE_HASH,'baseline hash changed'
  s=a.source.read_text(encoding='utf-8');n=sum('\u3400'<=c<='\u9fff' for c in s)
  if n>=2000:raise SystemExit('换芯须低于2000中文字')
  if r.exists() and any(r.iterdir()):raise SystemExit('Use a fresh empty run directory')
  r.mkdir(parents=True,exist_ok=True)
  (r/'approved_source.txt').write_text(s,encoding='utf-8');(r/'session_clone.json').write_bytes(b)
  prompt=(ROOT/'references/expansion_prompt.txt').read_text().replace('{{换芯正文}}',s.strip())
  (r/'prompt.txt').write_text(prompt,encoding='utf-8')
  (r/'run_manifest.json').write_text(json.dumps({'baseline_sha256':sha(b),'source_sha256':sha(s.encode()),'prompt_sha256':sha(prompt.encode()),'source_cjk':n,'model':'gemini-3.1-pro-preview','temperature':0.8,'max_tokens':24000},ensure_ascii=False,indent=2))
  print(json.dumps({'prepared':str(r),'source_cjk':n},ensure_ascii=False));return
 for f in ['session_clone.json','prompt.txt','run_manifest.json']:assert (r/f).exists(),f
 m=json.loads((r/'run_manifest.json').read_text());assert sha((r/'prompt.txt').read_bytes())==m['prompt_sha256']
 assert sha((r/'session_clone.json').read_bytes())==BASE_HASH,'Never reuse a generated session'
 if (r/'expanded_raw.txt').exists():raise SystemExit('Existing result must not be overwritten')
 spec=importlib.util.spec_from_file_location('gary_legacy',ROOT/'scripts/legacy_runner.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 mod.load_env_file(Path(os.environ.get('GARY35_ENV_FILE','/Users/kin/Documents/Codex/2026-07-02/gemini/.env.local')))
 os.environ['TEAMO_MODEL']='gemini-3.1-pro-preview';os.environ['TEAMO_TEMPERATURE']='0.8';os.environ['TEAMO_MAX_TOKENS']='24000'
 url=os.environ.get('TEAMO_CHAT_COMPLETIONS_URL',os.environ.get('TEAMO_BASE_URL','https://api.teamorouter.com/v1').rstrip('/')+'/chat/completions')
 if not url.startswith('https://api.teamorouter.com/v1/'):raise SystemExit('Unexpected endpoint')
 if a.check_only:print(json.dumps({'endpoint':url,'model':os.environ['TEAMO_MODEL'],'fresh_baseline':True,'prompt_hash_match':True}));return
 sys.argv=[str(ROOT/'scripts/legacy_runner.py'),'--prompt-file',str(r/'prompt.txt'),'--session-file',str(r/'session_clone.json'),'--output-file',str(r/'expanded_raw.txt')]
 raise SystemExit(mod.main())
if __name__=='__main__':main()
