#!/usr/bin/env python3
"""Check a pure 2.2 body mechanically; content acceptance remains a separate read."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ENDING='我是探花Gary，带你用最真实的人性去征服，用绝对的实力去主导。我们内部群里见。'

def inspect(body):
    count=len(re.findall(r'[\u4e00-\u9fff]',body))
    markers=[x for x in ['爆款心理学标题包装','开头版本一：','开头版本二：','开头版本三：','开头一 固定模板匹配版','开头二 扩写前原文开头','开头一：固定模板匹配版','开头二：扩写前原文开头'] if x in body]
    ending_pass=re.sub(r'\s+','',body).endswith(ENDING)
    length_pass=count>=8000
    return {'mode':'2.2','cjk_characters':count,'target_range':[8000,12000],'acceptance_minimum':8000,'hard_upper_limit':None,'length_pass':length_pass,'within_target_range':8000<=count<=12000,'fixed_ending_pass':ending_pass,'packaging_markers_found':markers,'mechanical_pass':length_pass and ending_pass and not markers,'semantic_review_required':True,'user_approved':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--body-file',required=True,type=Path)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    raw=args.body_file.read_bytes();result=inspect(raw.decode('utf-8-sig'))
    result.update(body_path=str(args.body_file.resolve()),body_sha256=hashlib.sha256(raw).hexdigest())
    output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(output,encoding='utf-8')
    print(output,end='')
    raise SystemExit(0 if result['mechanical_pass'] else 1)

if __name__=='__main__':main()
