"""Freeze and export upstream manuscripts. No model calls or credentials."""
from pathlib import Path
import argparse,json,hashlib,shutil,re,os,uuid,tempfile
import history

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):history.dump(Path(p),x)
def verify_bundle(bundle):
 m=read(bundle/'manifest.json')
 for name,value in m['files'].items():
  if Path(name).name!=name or sha(bundle/name)!=value:raise ValueError('Frozen file changed: '+name)
 return m

def freeze(a):
 source=a.source.resolve();route=read(a.proposal);notes=read(a.notes);review=history.verify(source,a.review);screen=read(review['screen'])
 if screen['proposal_sha256']!=sha(a.proposal):raise ValueError('Route changed after screen')
 body=source.read_text();n=len(re.findall('[\u3400-\u9fff]',body))
 if not 0<n<2000:raise ValueError('Source must be nonempty and under 2000 CJK')
 if body.splitlines()[0].strip()!=route['title']:raise ValueError('Title does not match first source line')
 if not notes.get('structure') or not notes.get('knowledge_used'):raise ValueError('Record actual structure and read knowledge sources in notes.json')
 points=route.get('viewpoints',[])
 if notes.get('point_count')!=len(points) or len(review['point_comparison'])!=len(points):raise ValueError('Point count/review coverage differs')
 if not notes.get('topic_fidelity_checked'):raise ValueError('Topic fidelity must be reviewed')
 dest=a.output.resolve()
 if dest.exists():raise ValueError('Use a new bundle directory; frozen packages are immutable')
 dest.parent.mkdir(parents=True,exist_ok=True)
 tmp=Path(tempfile.mkdtemp(prefix='.huanxin-',dir=dest.parent))
 try:
  for src,name in [(source,'manuscript.txt'),(a.proposal,'route.json'),(a.review,'review.json'),(a.notes,'notes.json'),(Path(review['screen']),'screen.json')]:shutil.copy2(src,tmp/name)
  ident='huanxin-'+uuid.uuid4().hex
  m={'schema_version':1,'handoff_id':ident,'title':route['title'],'account':route.get('account'),'state':'换芯已冻结，未扩写','source_cjk':n,'expansion_executed':False,'target_route':None,'case_instruction':'在中段 CTA 前插入一个符合主题的案例','files':{p.name:sha(p) for p in tmp.iterdir()}}
  dump(tmp/'manifest.json',m)
  # Recheck current history just before committing an upstream record.
  if sha(history.HOME/'index.json')!=screen['history_sha256']:raise ValueError('History changed; review new records and screen again')
  row={**route,'id':ident,'handoff_id':ident,'status':'transplant_ready','source_sha256':sha(source),'bundle':str(dest),'search_text':json.dumps(route,ensure_ascii=False),'artifacts_copied':[{'original':str(dest/'manuscript.txt'),'sha256':sha(source),'text':body}]}
  os.replace(tmp,dest)
  dump(history.HOME/'new'/(ident+'.json'),row)
  rows=read(history.HOME/'index.json');rows.append(row);dump(history.HOME/'index.json',rows)
  print(json.dumps({'bundle':str(dest),'handoff_id':ident,'state':m['state']},ensure_ascii=False))
 finally:
  if tmp.exists():shutil.rmtree(tmp)

def export(a):
 bundle=a.bundle.resolve();m=verify_bundle(bundle);out=a.output.resolve()
 if out.exists():raise ValueError('Use a new export directory')
 out.mkdir(parents=True)
 raw=(bundle/'manuscript.txt').read_text();suffix='\n\n'+m['case_instruction'] if a.case=='mid-cta' else ''
 (out/'input.txt').write_text(raw+suffix)
 (out/'manuscript.txt').write_bytes((bundle/'manuscript.txt').read_bytes())
 plan={'schema_version':1,'handoff_id':m['handoff_id'],'title':m['title'],'account':m['account'],'target_route':a.target,'case_option':a.case,'frozen_bundle':str(bundle),'source_sha256':m['files']['manuscript.txt'],'input_sha256':sha(out/'input.txt'),'state':'扩写输入已导出，未调用线路','expansion_executed':False,'payload_prefix_is_exact_source':(out/'input.txt').read_text().startswith(raw),'same_article_history_id':m['handoff_id']}
 dump(out/'handoff.json',plan)
 print(json.dumps(plan,ensure_ascii=False))

def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='action',required=True)
 f=sp.add_parser('freeze')
 for name in ['source','proposal','review','notes','output']:f.add_argument('--'+name,type=Path,required=True)
 e=sp.add_parser('export');e.add_argument('--bundle',type=Path,required=True);e.add_argument('--target',required=True);e.add_argument('--case',choices=['mid-cta','none'],default='mid-cta');e.add_argument('--output',type=Path,required=True)
 v=sp.add_parser('verify');v.add_argument('--bundle',type=Path,required=True)
 a=p.parse_args()
 if a.action=='freeze':freeze(a)
 elif a.action=='export':export(a)
 else:print(json.dumps(verify_bundle(a.bundle),ensure_ascii=False))
if __name__=='__main__':main()
