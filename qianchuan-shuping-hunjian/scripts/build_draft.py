from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import time
from uuid import uuid4
from zipfile import ZipFile

import argparse
import hashlib
from collections import defaultdict

parser = argparse.ArgumentParser(description='Build an independent Jianying vertical montage from a reviewed JSON plan.')
parser.add_argument('job', type=Path)
parser.add_argument('--workspace', type=Path, required=True, help='Folder containing preset_screen and native_animation_assets')
args = parser.parse_args()
job = json.loads(args.job.read_bytes())
work = args.workspace.resolve()
data = Path.home() / 'Movies/JianyingPro/User Data'
root = data / 'Projects/com.lveditor.draft'
source = Path(job['reference']) if job.get('reference') else next(root.glob('竖屏本地素材混剪｜*一句一镜中英*'))
voice_source = Path(job['source'])
name = job['name']
assert Path(name).name == name and not name.startswith('.')
target = root / name
stage = work / ('.stage-'+uuid4().hex)
assert not target.exists()
def choose_timeline(directory):
    for f in [*directory.glob('Timelines/*/template.json'), directory/'draft_info.json', directory/'draft_content.json']:
        try:
            doc=json.loads(f.read_bytes())
            if doc.get('tracks'):
                return f, doc
        except (OSError, ValueError):
            pass
    raise ValueError(f'No readable timeline: {directory}')
source_file, draft = choose_timeline(source)
voice_file, voice_draft = choose_timeline(voice_source)
source_bytes = source_file.read_bytes()
voice_bytes = voice_file.read_bytes()
catalog = json.loads((work/'preset_screen/metadata.json').read_bytes())
lookup = defaultdict(list)
for location in [data/'Cache/effect', data/'Cache/artistEffect', data/'Cache/AITextTemplate/Resource', data/'Presets/Combination/Resources', Path('/Applications/VideoFusion-macOS.app/Contents/Resources/Font'), Path.home()/'Library/Fonts']:
    for base, dirs, files in os.walk(location):
        for f in dirs+files:
            lookup[f.casefold()].append(Path(base)/f)
def resolve(value, resource=None):
    p=Path(value.replace(chr(92),'/'))
    if p.is_absolute() and p.exists():
        return p
    if p.name.casefold() in lookup:
        return lookup[p.name.casefold()][0]
    for kind in ('effect','artistEffect'):
        children=[f for f in (data/'Cache'/kind/str(resource)).glob('*') if f.is_dir()]
        if len(children)==1:
            return children[0]
    return None

def uid():
    return str(uuid4()).upper()

def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def remap(value, change):
    if isinstance(value, dict):
        return {key:remap(item,change) for key,item in value.items()}
    if isinstance(value, list):
        return [remap(item,change) for item in value]
    return change(value) if isinstance(value,str) else value

guid = re.compile(r'[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}')

def copy_with_new_ids(value):
    ids = {}
    def replace(string):
        if guid.fullmatch(string):
            if string not in ids:
                ids[string] = uid()
            return ids[string]
        return string
    return remap(value, replace)

def index_of(d):
    return {m['id']:m for group in d['materials'].values() if isinstance(group,list)
            for m in group if isinstance(m,dict) and m.get('id')}

def load_preset(preset):
    meta = next(r for r in catalog if r['name'].strip()==preset)
    with ZipFile(work/'preset_screen'/meta['bundle']) as archive:
        return json.loads(archive.read(meta['draft']))

rows = job['rows']
count = len(rows)
assignments = [(r['preset'], r['mapping']) for r in rows]
assert all(p!='渐显' and not any(w in p for w in ('切割','割裂')) for p,_ in assignments)
draft = copy_with_new_ids(draft)
tracks = {t.get('name'):t for t in draft['tracks']}
cn = tracks['中文字幕｜一句一镜']
en = tracks['英文字幕｜逐句对应']
video = tracks['真人实拍｜按文案语义匹配｜全静音']
ix = index_of(draft)
voice_index = index_of(voice_draft)
speech_track = next(t for t in voice_draft['tracks'] if t['name']==job['caption_track'] and t['type']=='text')
assert len(speech_track['segments'])==count>0
first = speech_track['segments']
duration = first[-1]['target_timerange']['start'] + first[-1]['target_timerange']['duration']
cn['segments'] = []
v_template=deepcopy(video['segments'][0])
v_material=deepcopy(ix[v_template['material_id']])
en_template=deepcopy(en['segments'][0])
en_material=deepcopy(ix[en_template['material_id']])
video['segments']=[]
en['segments']=[]
ext_copies={}
def stage_path(raw):
    p=Path(raw)
    assert p.is_file(),p
    sha=hashlib.sha256(str(p).encode()).hexdigest()[:10]
    rel='Resources/assets/'+sha+'_'+p.name
    ext_copies[rel]=p
    return rel
transition_ids = {m['id'] for m in draft['materials']['transitions']}
def fresh_material(template):
    out=deepcopy(template)
    new=uid()
    for key in ('id','material_id','local_material_id'):
        if key in out:
            out[key]=new
    return out
for i,(row,cap) in enumerate(zip(rows,first)):
    time_range=deepcopy(cap['target_timerange'])
    du=time_range['duration']
    assert du>=200000
    shot=row['shot']
    assert shot['width']<shot['height']
    source_start=round(shot['start']*1000000)
    total=round(shot['duration']*1000000)
    assert 0<=source_start<source_start+du<=total
    assert i==count-1 or source_start+du+200000<=total
    vmat=fresh_material(v_material)
    vmat.update(path=stage_path(shot['path']), media_path='', material_name=Path(shot['path']).name,
                width=shot['width'], height=shot['height'], duration=total, has_audio=False)
    vmat['media_path']=vmat['path']
    v=deepcopy(v_template)
    v.update(id=uid(),material_id=vmat['id'],target_timerange=time_range,
             source_timerange={'start':source_start,'duration':du},volume=0,last_nonzero_volume=0)
    if i==count-1:
        v['extra_material_refs']=[x for x in v['extra_material_refs'] if x not in transition_ids]
    # Match the canvas even for sources a few pixels wider or narrower than 9:16.
    scale=max(1,(shot['width']/shot['height'])/(1080/1920),(1080/1920)/(shot['width']/shot['height']))
    v['clip']['scale']={'x':scale,'y':scale}
    video['segments'].append(v)
    draft['materials']['videos'].append(vmat)
    mat=fresh_material(en_material)
    rich=json.loads(mat['content'])
    rich['text']=row['english']
    for style in rich['styles']:
        style['range']=[0,len(rich['text'])]
    mat['content']=json.dumps(rich,ensure_ascii=False)
    eng=deepcopy(en_template)
    eng.update(id=uid(),material_id=mat['id'],target_timerange=deepcopy(time_range))
    eng['clip']['transform']['y']=-0.82
    en['segments'].append(eng)
    draft['materials']['texts'].append(mat)
for t in draft['tracks']:
    for seg in t['segments']:
        timing=seg['target_timerange']
        if timing['start']+timing['duration']>duration:
            timing['duration']=duration-timing['start']
            if seg.get('source_timerange'):
                seg['source_timerange']['duration']=timing['duration']
audio_tracks=[t for t in voice_draft['tracks'] if t['type']=='audio' and len(t['segments'])==1]
def route_audio(dtr, str_, volume):
    dest=dtr['segments'][0]
    src=str_['segments'][0]
    assert src['target_timerange']['start']==0 and src['target_timerange']['duration']>=duration
    au=fresh_material(voice_index[src['material_id']])
    raw=Path(au['path'])
    au.update(path=stage_path(voice_source/raw if not raw.is_absolute() else raw),music_id=au['id'])
    draft['materials']['audios'].append(au)
    dest.update(material_id=au['id'],target_timerange={'start':0,'duration':duration},
                source_timerange={'start':src['source_timerange']['start'],'duration':duration},
                volume=volume,last_nonzero_volume=volume)
    assert dest['source_timerange']['start']+duration<=au['duration']
speech=next(t for t in audio_tracks if '口播' in t.get('name','') or t.get('name')=='配音')
bgm=next(t for t in audio_tracks if '背景音乐' in t.get('name',''))
route_audio(tracks['配音'],speech,speech['segments'][0]['volume'])
route_audio(tracks['背景音乐｜我的预设 7'],bgm,10**(5/20))
kept_ids={r for t in draft['tracks'] for seg in t['segments'] for r in [seg['material_id'],*seg['extra_material_refs']]}
for key in ('videos','texts','transitions','audios'):
    draft['materials'][key]=[m for m in draft['materials'][key] if m['id'] in kept_ids]

resource_names = {}

def local_path(string):
    if string.startswith('Resources/'):
        return str(target / string)
    if str(source) in string:
        return string.replace(str(source),str(target))
    return string

draft = remap(draft, local_path)
native_fade = data/'Cache/effect/6724916044072227332/8aad5add2c87ca5154b841b00f890479'
assert native_fade.is_dir()
stage.mkdir()
(stage/'Resources/assets').mkdir(parents=True)
preset_resources = stage/'Resources/原预设资源'
preset_resources.mkdir()

def copy_resource(value, resource_id=None):
    if not value:
        return value
    p = native_fade if resource_id == '6724916044072227332' else resolve(value,resource_id)
    if not p and resource_id:
        asset = work/'native_animation_assets'/str(resource_id)
        if (asset/'anim.prefab').is_file():
            p = asset
    assert p, (value,resource_id)
    p = Path(p)
    if p not in resource_names:
        folder = str(len(resource_names)+1).zfill(2)
        dest = preset_resources / folder / p.name
        dest.parent.mkdir()
        if p.is_dir():
            shutil.copytree(p,dest)
        else:
            shutil.copy2(p,dest)
        resource_names[p] = dest.relative_to(stage)
    return str(target/resource_names[p])

def retime_range(timerange, ratio):
    a = round(timerange['start']*ratio)
    b = round((timerange['start']+timerange['duration'])*ratio)
    return {'start':a,'duration':b-a}

def retime_segment(seg,ratio):
    for field in ('target_timerange','source_timerange'):
        if seg.get(field):
            seg[field] = retime_range(seg[field],ratio)
    for group in seg.get('common_keyframes') or []:
        for frame in group['keyframe_list']:
            frame['time_offset'] = round(frame['time_offset']*ratio)

overlay = deepcopy(load_preset(assignments[0][0])['tracks'][0])
overlay.update(id=uid(),name='原预设复合片段｜逐句',is_default_name=False,flag=2,segments=[])
manifest = []
for (preset,mapping),cue,eng,shot in zip(assignments,first,en['segments'],video['segments']):
    line = json.loads(voice_index[cue['material_id']]['content'])['text']
    # An original decorative question-mark slot may remain on a question.
    assert ''.join(v for k,v in mapping.items() if not (k==v=='?'))==line,(preset,line,mapping)
    timing = cue['target_timerange']
    assert timing==eng['target_timerange']==shot['target_timerange']
    wrapper = copy_with_new_ids(load_preset(preset))
    top = wrapper['tracks'][0]['segments'][0]
    ratio = timing['duration']/top['target_timerange']['duration']
    removed_sounds = set()
    for combo in wrapper['materials']['drafts']:
        combo.update(draft_config_path='',draft_cover_path='',draft_file_path='')
        inner = combo['draft']
        mats = inner['materials']
        removed_sounds.update(m.get('name','') for m in mats.get('audios',[]))
        inner['tracks'] = [t for t in inner['tracks'] if t['type']!='audio']
        mats['audios'] = []
        mats['beats'] = []
        for mat in mats.get('texts',[]):
            rich = json.loads(mat['content'])
            previous = rich['text']
            rich['text'] = mapping[previous]
            for style in rich['styles']:
                if style['range'] == [0,len(previous)]:
                    style['range'] = [0,len(rich['text'])]
                else:
                    lo,hi = style['range']
                    style['range'] = [round(pos*len(rich['text'])/len(previous)) for pos in (lo,hi)]
                fx_style = style.get('effectStyle') or {}
                if fx_style.get('path'):
                    fx_style['path'] = copy_resource(fx_style['path'],fx_style['id'])
                font = style.get('font') or {}
                if font.get('path'):
                    font['path'] = copy_resource(font['path'])
            mat['content'] = json.dumps(rich,ensure_ascii=False)
            if mat.get('font_path'):
                mat['font_path'] = copy_resource(mat['font_path'])
            for f in mat.get('fonts') or []:
                if f.get('path'):
                    f['path'] = copy_resource(f['path'])
        for mat in mats.get('effects',[]):
            if mat.get('path'):
                mat['path'] = copy_resource(mat['path'],mat.get('resource_id'))
        for mat in mats.get('common_mask',[]):
            mat['path'] = copy_resource(mat['path'],mat['resource_id'])
        for group in mats.get('material_animations',[]):
            for fx in group['animations']:
                fx['path'] = copy_resource(fx['path'],fx['resource_id'])
                fx['duration'] = round(fx['duration']*ratio)
                fx['start'] = round(fx['start']*ratio)
        for t in inner['tracks']:
            for s in t['segments']:
                retime_segment(s,ratio)
        inner['duration'] = round(inner['duration']*ratio)
        for m in mats.get('videos',[]):
            m['duration'] = round(m['duration']*ratio)
    top['target_timerange'] = deepcopy(timing)
    top['source_timerange'] = {'start':0,'duration':timing['duration']}
    top.update(render_index=14003,track_render_index=2,volume=0,last_nonzero_volume=0)
    for m in wrapper['materials']['videos']:
        m.update(duration=timing['duration'],has_audio=False,material_name=f'{preset}｜{line}')
    for key,value in wrapper['materials'].items():
        if isinstance(value,list) and value:
            draft['materials'].setdefault(key,[]).extend(value)
    overlay['segments'].append(top)
    manifest.append(dict(preset=preset,line=line,**timing,missing_original_audio=sorted(removed_sounds)))
draft['tracks'][draft['tracks'].index(cn)] = overlay
stamp = time.time_ns()//1000
draft.update(name=name,id=uid(),path='',duration=duration,create_time=stamp,update_time=stamp)
# Copy only the local assets referenced by this draft.
prefix = str(target/'Resources/assets') + '/'
used = set()
def collect(value):
    # Match plain paths and font paths embedded in rich text JSON.
    if value.startswith(prefix):
        used.add(value)
    elif value.startswith('{') and prefix in value:
        try:
            embedded = json.loads(value)
        except ValueError:
            return value
        remap(embedded,collect)
    return value

remap(draft,collect)
for raw in used:
    rel = Path(raw).relative_to(target)
    src = ext_copies.get(str(rel),source / rel)
    dst = stage / rel
    if src.is_dir():
        shutil.copytree(src,dst,dirs_exist_ok=True)
    else:
        shutil.copy2(src,dst)
# Use the new opener as the cover, when ffmpeg is available.
import subprocess
try:
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(rows[0]['shot']['start']),'-i',rows[0]['shot']['path'],
                    '-frames:v','1','-vf','scale=270:480','-threads','1',str(stage/'draft_cover.jpg')],check=True,timeout=15)
except (OSError,subprocess.SubprocessError):
    shutil.copy2(source/'draft_cover.jpg',stage/'draft_cover.jpg')
for f in ('draft_content.json','draft_info.json'):
    write(stage/f,draft)
meta_path = root/'数字人竖屏源_020七个底层特质_1104_音频字幕/draft_meta_info.json'
try:
    meta = json.loads(meta_path.read_bytes())
except (OSError,ValueError):
    meta = {}
for key,value in list(meta.items()):
    if key.startswith('tm_draft_cloud'):
        meta[key] = -1 if isinstance(value,int) else ''
meta.update(draft_id=uid(),draft_name=name,draft_fold_path=str(target),draft_root_path=str(root),
            draft_cover='draft_cover.jpg',draft_materials=[],draft_materials_copied_info=[],
            cloud_draft_cover=False,cloud_draft_sync=False,cloud_package_completed_time='',
            tm_draft_create=stamp,tm_draft_modified=stamp,tm_duration=duration,draft_new_version=draft['new_version'],
            draft_timeline_materials_size_=sum(f.stat().st_size for f in (stage/'Resources').rglob('*') if f.is_file()))
write(stage/'draft_meta_info.json',meta)
assert len(manifest) == len(first) == len(video['segments']) == len(en['segments']) == count
assert all(a['preset'] != b['preset'] for a,b in zip(manifest,manifest[1:]))
assert all(a['start']+a['duration']==b['start'] for a,b in zip(manifest,manifest[1:]))
assert manifest[-1]['start']+manifest[-1]['duration']==duration
all_index=index_of(draft)
assert all(ref in all_index for t in draft['tracks'] for s in t['segments']
           for ref in [s['material_id'],*s['extra_material_refs']])
assert source_file.read_bytes()==source_bytes and voice_file.read_bytes()==voice_bytes
def check_paths(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,str) and v.startswith('/') and k in {'path','font_path','media_path'}:
                candidate=stage/Path(v).relative_to(target) if v.startswith(str(target)+'/') else Path(v)
                assert candidate.exists(),v
            check_paths(v)
    elif isinstance(x,list):
        for v in x: check_paths(v)
    elif isinstance(x,str) and x.startswith('{'):
        try: embedded=json.loads(x)
        except ValueError: return
        check_paths(embedded)
check_paths(draft)
assert not target.exists()
stage.rename(target)
for rec,row in zip(manifest,rows):
    rec.update(english=row['english'],shot=row['shot'])
write(args.job.with_name(args.job.stem+'.manifest.json'),manifest)
print(target, duration)
from collections import Counter
print(Counter(r['preset'] for r in manifest))
