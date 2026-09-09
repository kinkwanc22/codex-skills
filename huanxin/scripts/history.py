from pathlib import Path
import argparse,json,hashlib,re,subprocess,sys,datetime,os
HOME=Path(os.environ.get('HUANXIN_HISTORY_HOME','/Users/kin/Documents/Codex/gary-shared-history'))
LEGACY=Path('/Users/kin/Documents/Codex/2026-07-02/gemini')
SOURCES=[LEGACY/'work/2.5_pretransplant_ledger.json',Path('/Users/kin/Gary 男性情感/Gary 男性情感/03_C_Skill与方法库/换芯历史排重/02_标准化记录/3.1_3.2历史换芯标准化记录.json')]
def digest(b):return hashlib.sha256(b).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
def norm(s):return re.sub(r'[^a-z0-9\u3400-\u9fff]','',s.lower())
def grams(s):s=norm(s);return {s[i:i+3] for i in range(max(0,len(s)-2))}
def sim(a,b):a,b=grams(a),grams(b);return len(a&b)/max(1,len(a|b))
def records(d):return d if isinstance(d,list) else d.get('records',d.get('entries',[]))
def paths(d,key=''):
 if isinstance(d,dict):
  for k,v in d.items():yield from paths(v,k)
 elif isinstance(d,list):
  for v in d:yield from paths(v,key)
 elif isinstance(d,str) and ('path' in key or 'file' in key or key in ('resolved','accepted','pre_source','raw')) and Path(d).suffix.lower() in ('.txt','.md','.docx'):yield d

def refresh():
 HOME.mkdir(parents=True,exist_ok=True);out=[];missing=set();copied={}
 srcs=SOURCES+list(Path('/Users/kin/Documents/Codex/2026-08-30/gary-31-production/work').rglob('*ledger_record.json'))+list(Path('/Users/kin/Documents/Codex/2026-08-30/gary-31-production/work').rglob('route_ledger_record.json'))
 for src in dict.fromkeys(srcs):
  if not src.exists():missing.add(str(src));continue
  data=src.read_bytes();dump(HOME/'snapshots'/(digest(str(src).encode())[:12]+'.json'),json.loads(data));d=json.loads(data);rs=records(d)
  if not rs and isinstance(d,dict):rs=[d]
  for i,x in enumerate(rs):
   if not isinstance(x,dict):continue
   row=dict(x);row['id']=digest((str(src)+':'+str(i)).encode())[:16];row['origin_ledger']=str(src);row['original_record']=x;arts=[]
   if not row.get('mechanism_novelty'):
    row['mechanism_novelty']={k:v for k,v in {'core_mechanism':x.get('mechanism_families',[]),'action_chain':x.get('replacement_operations',[]),'proof_operation':x.get('case_signatures',[]),'dominant_causal_chain':x.get('route_signature') or x.get('route','')}.items() if v}
   for val in set(paths(x)):
    p=Path(val);p=p if p.is_absolute() else LEGACY/p
    if not p.is_file():missing.add(str(p));continue
    if p.suffix.lower() not in ('.txt','.md','.docx'):continue
    raw=p.read_bytes();h=digest(raw);dst=HOME/'artifacts'/(h+p.suffix.lower())
    if not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
    assert digest(dst.read_bytes())==h
    t=''
    if p.suffix.lower() in ('.txt','.md'):t=raw.decode('utf-8',errors='replace')
    else:
     import zipfile,xml.etree.ElementTree as ET
     try:
      with zipfile.ZipFile(p) as z:t='\n'.join(''.join(n.itertext()) for n in ET.fromstring(z.read('word/document.xml')).iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
     except Exception:pass
    arts.append({'original':str(p),'copy':str(dst),'sha256':h,'text':t});copied[h]=str(dst)
   row['artifacts_copied']=arts;row['search_text']=json.dumps(x,ensure_ascii=False);out.append(row)
 # Include every generated/local draft, so pending articles and both accounts cannot bypass history.
 root=Path('/Users/kin/Documents/Codex/2026-09-07/gary-35-production/work')
 for p in root.rglob('*.txt'):
  if p.name not in ('approved_source.txt','expanded_raw.txt','expanded_delivery.txt','source.txt','source_v2.txt'):continue
  s=p.read_text(errors='replace');out.append({'id':digest(str(p).encode())[:16],'title':s.splitlines()[0] if s else p.parent.name,'status':'generated_or_draft','source_path':str(p),'search_text':s,'artifacts_copied':[{'original':str(p),'sha256':digest(s.encode()),'text':s}]})
 for p in sorted((HOME/'new').glob('*.json')) if (HOME/'new').exists() else []:out.append(json.loads(p.read_text()))
 dump(HOME/'index.json',out);report={'records':len(out),'unique_archived_artifacts':len(copied),'missing_paths':sorted(missing),'complete_six_field_records':sum(all(x.get('mechanism_novelty',{}).get(k) for k in ['problem_trigger','core_mechanism','action_chain','proof_operation','position_or_interest_shift','desired_result']) for x in out),'sources':[str(s) for s in srcs]};dump(HOME/'import_report.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('missing_paths','sources')},ensure_ascii=False))

def screen(source,proposal,output):
 rs=json.loads((HOME/'index.json').read_text());rs=[x for x in rs if not (x.get('status')=='generated_or_draft' and x.get('source_path')==str(source.resolve()))];s=source.read_text();q=json.loads(proposal.read_text());wanted=json.dumps(q,ensure_ascii=False);rank=[];exact=[]
 for x in rs:
  texts=[a.get('text','') for a in x.get('artifacts_copied',[])];score=max([sim(s,t) for t in texts]+[sim(wanted,x.get('search_text',json.dumps(x,ensure_ascii=False)))])
  if any(norm(s)==norm(t) and norm(s) for t in texts):exact.append(x['id'])
  rank.append({'id':x['id'],'title':x.get('title',''),'score':round(score,4),'record':x})
 rank.sort(key=lambda x:x['score'],reverse=True)
 dump(output.parent/'candidates.json',rank[:30]);dump(output.parent/'all_routes.json',rs)
 cmd=[sys.executable,str(Path(__file__).with_name('legacy_novelty.py')),'--proposal',str(proposal),'--ledger',str(output.parent/'all_routes.json'),'--recent','0','--all-statuses','--report-out',str(output.parent/'mechanism_screen.json')]
 subprocess.run(cmd,capture_output=True,text=True)
 mech=json.loads((output.parent/'mechanism_screen.json').read_text())
 dump(output,{'source_sha256':digest(source.read_bytes()),'proposal_sha256':digest(proposal.read_bytes()),'history_sha256':digest((HOME/'index.json').read_bytes()),'records':len(rs),'exact_duplicates':exact,'mechanism_screen':mech,'lexical_high_similarity':[{'id':x['id'],'score':x['score']} for x in rank if x['score']>=.65],'candidate_file':str((output.parent/'candidates.json').resolve()),'semantic_review_required':True,'automatic_block':bool(exact or not mech['mechanism_novelty_pass'])})
 print(output)

def verify(source,review):
 r=json.loads(review.read_text());p=Path(r['screen']);s=json.loads(p.read_text())
 assert s['source_sha256']==digest(source.read_bytes()),'source changed'
 assert s['history_sha256']==digest((HOME/'index.json').read_bytes()),'history changed; rerun screen'
 assert not s['automatic_block'],'duplicate or missing mechanism fields'
 assert r.get('pass') is True and r.get('same_topic_review_complete') is True,'semantic review missing'
 assert (r.get('compared_ids') or s['records']==0) and r.get('point_comparison') and r.get('distinct_action_chain') and r.get('topic_fidelity'),'semantic evidence missing'
 return r

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['refresh','screen','verify']);p.add_argument('--source',type=Path);p.add_argument('--proposal',type=Path);p.add_argument('--output',type=Path);p.add_argument('--review',type=Path);a=p.parse_args()
 if a.action=='refresh':refresh()
 elif a.action=='screen':screen(a.source,a.proposal,a.output)
 else:verify(a.source,a.review);print('semantic record verified')
