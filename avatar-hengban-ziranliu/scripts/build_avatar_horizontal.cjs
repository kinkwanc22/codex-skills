const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const configArg = process.argv.indexOf('--config');
if(configArg<0 || !process.argv[configArg+1]) throw Error('Usage: node build_avatar_horizontal.cjs --config /absolute/config.json');
const cfg=JSON.parse(fs.readFileSync(path.resolve(process.argv[configArg+1]),'utf8'));
for(const k of ['targetDir','heroineDir','avatar','personVideo','still','avatarEndUs','introEndUs','stillStartUs','title','bodyLead','bodyShort'])
  if(cfg[k]===undefined)throw Error(`Missing config field: ${k}`);
const SYSTEM8 = false;
const draftRoot = '/Users/kin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft';
const introSource=cfg.introSource || '/Users/kin/横版通用片头.mp4';
const b05Dir=cfg.donorDir || '/Users/kin/Documents/Codex/2026-09-11/n/work/batch_20260916_gary/backup_before_punctuation_v3_20260917/drafts/B05_六种预选信号_让女人主动投入_音频字幕_0916';
const donorPath=path.join(b05Dir,'draft_content.json');
const overlaySource=cfg.overlaySource || path.join(draftRoot,'8月23日/subdraft/91CA2E80-089F-4FF8-B437-BF2648AB282A/draft_content.json');
const backupRoot=path.join(cfg.targetDir,'avatar_hengban_backup');
const batchReportPath=path.join(cfg.targetDir,'avatar_hengban_build_report.json');
const ffprobe=cfg.ffprobe || '/Users/kin/.local/bin/ffprobe';
const ffmpeg=cfg.ffmpeg || '/Users/kin/.local/bin/ffmpeg';

const id = () => crypto.randomUUID().replace(/-/g, '');
const deep = (v) => JSON.parse(JSON.stringify(v));
function collectIds(v, out = new Set()) {
  if (!v || typeof v !== 'object') return out;
  if (Array.isArray(v)) { for (const x of v) collectIds(x, out); return out; }
  if (typeof v.id === 'string' && v.id) out.add(v.id);
  for (const x of Object.values(v)) collectIds(x, out);
  return out;
}
function remapIds(v) {
  const map = new Map([...collectIds(v)].map((old) => [old, id()]));
  function walk(x) {
    if (typeof x === 'string') return map.get(x) || x;
    if (!x || typeof x !== 'object') return x;
    if (Array.isArray(x)) return x.map(walk);
    return Object.fromEntries(Object.entries(x).map(([k, child]) => [k, walk(child)]));
  }
  return walk(v);
}
function mergeMaterials(target, source) {
  for (const [key, values] of Object.entries(source.materials || {})) {
    if (!Array.isArray(values)) continue;
    if (!Array.isArray(target.materials[key])) target.materials[key] = [];
    target.materials[key].push(...values);
  }
  for (const [key, values] of Object.entries(source.keyframes || {})) {
    if (!Array.isArray(values)) continue;
    if (!Array.isArray(target.keyframes[key])) target.keyframes[key] = [];
    target.keyframes[key].push(...values);
  }
  if (Array.isArray(source.keyframe_graph_list)) {
    if (!Array.isArray(target.keyframe_graph_list)) target.keyframe_graph_list = [];
    target.keyframe_graph_list.push(...source.keyframe_graph_list);
  }
}
function setRichText(material, text) {
  const rich = JSON.parse(material.content);
  rich.text = text;
  for (const style of rich.styles || []) style.range = [0, text.length];
  material.content = JSON.stringify(rich);
}
function probe(file) {
  const result = spawnSync(ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration', '-of', 'json', file], { encoding: 'utf8' });
  if (result.status !== 0) throw new Error(`ffprobe failed: ${file}\n${result.stderr}`);
  const data = JSON.parse(result.stdout);
  return { duration: Math.round(Number(data.format.duration) * 1e6), width: data.streams[0].width, height: data.streams[0].height };
}
function atomicWrite(file, value) {
  const tmp = `${file}.hengban_ziranliu_tmp`;
  fs.writeFileSync(tmp, value);
  fs.renameSync(tmp, file);
}
function nearestEnd(rows, target, min, max) {
  const candidates = rows.map((r) => r.end).filter((v) => v > min && v < max);
  return candidates.sort((a, b) => Math.abs(a - target) - Math.abs(b - target))[0];
}
function makeVideoMaterial(template, file, info, type, name) {
  const material = deep(template);
  material.id = id();
  material.local_material_id = material.id;
  material.material_id = material.id;
  material.path = file;
  if ('media_path' in material) material.media_path = file;
  material.material_name = name || path.basename(file);
  material.duration = info.duration;
  material.width = info.width;
  material.height = info.height;
  material.type = type;
  material.has_audio = false;
  return material;
}
function makeSegment(template, material, start, duration) {
  const segment = deep(template);
  segment.id = id();
  segment.material_id = material.id;
  segment.target_timerange = { start, duration };
  segment.source_timerange = { start: 0, duration };
  segment.speed = 1;
  segment.volume = 0;
  segment.last_nonzero_volume = 1;
  segment.track_render_index = 1;
  segment.render_index = 1;
  segment.extra_material_refs = [];
  return segment;
}

if (!fs.existsSync(introSource)) throw new Error('fixed intro missing');
const introInfo = probe(introSource);
if (introInfo.width <= introInfo.height) throw new Error('fixed intro is not horizontal');
const donorDraft = JSON.parse(fs.readFileSync(donorPath, 'utf8'));
const donorSubtitleTrack = donorDraft.tracks.find((t) => t.type === 'text' && t.name === '字幕');
const donorSubtitleMaterial = donorDraft.materials.texts.find((m) => m.id === donorSubtitleTrack.segments[0].material_id);
const donorStyle = JSON.parse(donorSubtitleMaterial.content).styles[0];
const donorVisualTrack = donorDraft.tracks.find((t) => t.type === 'video' && t.name === '自然流V2画面｜附加轨道');
const donorVideos = new Map(donorDraft.materials.videos.map((m) => [m.id, m]));
const videoSegmentTemplate = donorVisualTrack.segments.find((s) => donorVideos.get(s.material_id)?.type === 'video');
const photoSegmentTemplate = donorVisualTrack.segments.find((s) => donorVideos.get(s.material_id)?.type === 'photo');
const videoMaterialTemplate = donorVideos.get(videoSegmentTemplate.material_id);
const photoMaterialTemplate = donorVideos.get(photoSegmentTemplate.material_id);
const donorBgmTrack = donorDraft.tracks.find((t) => t.type === 'audio' && t.name === '背景音乐｜我的预设 7');
const donorBgmSegment = donorBgmTrack.segments[0];
const donorBgmMaterial = donorDraft.materials.audios.find((m) => m.id === donorBgmSegment.material_id);
const donorBgmSource = fs.existsSync(donorBgmMaterial.path) ? donorBgmMaterial.path : path.join(b05Dir, 'Resources/natural_flow_v2_0916/我的预设7.m4a');
const wrapper = JSON.parse(fs.readFileSync(overlaySource, 'utf8'));


const targetDir=path.resolve(cfg.targetDir);
if(!path.basename(targetDir).includes('数字人横'))throw Error('Target must be an independent 数字人横屏/横版 draft');
if(fs.existsSync(path.join(targetDir,'Timelines')))throw Error('Refuse editor-upgraded draft; create a fresh audio-subtitle draft');

if(fs.existsSync(path.join(targetDir,'.locked'))) throw Error('Target open');
const contentPath=path.join(targetDir,'draft_content.json');
const draft=JSON.parse(fs.readFileSync(contentPath,'utf8'));
if(draft.tracks.some(t=>t.type==='video'&&t.segments.length))throw Error('Refuse already built draft');
const subtitleTrack=draft.tracks.find(t=>t.name==='字幕');
const narrationTrack=draft.tracks.find(t=>t.name==='配音');
const rows=subtitleTrack.segments.map(s=>({text:JSON.parse(draft.materials.texts.find(m=>m.id===s.material_id).content).text,start:s.target_timerange.start,end:s.target_timerange.start+s.target_timerange.duration}));
const presetStart=cfg.avatarEndUs,presetEnd=cfg.introEndUs,stillStart=cfg.stillStartUs;
if(!(0<presetStart&&presetStart<presetEnd&&presetEnd<stillStart&&stillStart<draft.duration))throw Error('Semantic markers invalid');
if(presetEnd-presetStart>introInfo.duration)throw Error('Intro source too short');
const heroineDir=path.resolve(cfg.heroineDir);
for(const f of [cfg.personVideo,cfg.still])if(!path.resolve(f).startsWith(heroineDir+path.sep))throw Error('Person video/still must belong to the selected heroine directory');
if(!/^\d{3}_/.test(path.basename(heroineDir))||!path.basename(targetDir).includes(path.basename(heroineDir)))throw Error('Draft title must contain the actual three-digit heroine folder');
if(!subtitleTrack || !narrationTrack || narrationTrack.segments.length!==1)throw Error('Need a fresh audio/subtitle source draft');
const marker=cfg.marker || '今天我们要聊的是';
const hit=rows.filter(r=>r.text===marker);
const aside=rows.filter(r=>r.text==='另外说一下');
if(hit.length!==1 || hit[0].end!==presetStart || aside.length!==1 || aside[0].start!==stillStart || !rows.some(r=>r.end===presetEnd))throw Error('Config boundaries must match the current finalized subtitle semantics');
if(cfg.title.split('\n').length!==3)throw Error('Opening title must have three lines');
const videoSources=[cfg.avatar,cfg.personVideo];
const videoInfo=videoSources.map(probe);
if(videoInfo.some(x=>x.width<=x.height))throw Error('All source videos must be horizontal');
const ranges=[[0,presetStart],[presetEnd,stillStart]];
ranges.forEach(([a,b],i)=>{if(b-a>videoInfo[i].duration+1000)throw Error('source coverage');});
const stillSource=cfg.still;
if(probe(stillSource).width<=probe(stillSource).height)throw Error('Still must be horizontal');
const plan={code:'AVATAR_H01',targetDir,contentPath,draft,subtitleTrack,narrationTrack,rows,presetStart,presetEnd,stillStart,heroineDir,videoSources,videoInfo,ranges,stillSource,stillInfo:probe(stillSource),title:cfg.title,bodyLead:cfg.bodyLead,bodyShort:cfg.bodyShort};
const preflight={mode:'applied',source_docx_sha256:cfg.sourceSha256 || '',avatar_look:cfg.avatarLook || '4c028680a6bb4e75a4bdb40ea5087aa5'};
const plans=[plan];
fs.mkdirSync(backupRoot, { recursive: true });
const results = [];
for (const plan of plans) {
  const { draft, targetDir, contentPath, subtitleTrack, narrationTrack, rows, presetStart, presetEnd, stillStart } = plan;
  const backupDir = path.join(backupRoot, path.basename(targetDir));
  fs.mkdirSync(backupDir, { recursive: true });
  for (const name of ['draft_content.json', 'draft_info.json', 'draft_meta_info.json', 'draft_cover.jpg']) {
    const source = path.join(targetDir, name);
    const destination = path.join(backupDir, name);
    if (fs.existsSync(source) && !fs.existsSync(destination)) fs.copyFileSync(source, destination);
  }
  draft.canvas_config = { ...(draft.canvas_config || {}), width: 1920, height: 1080, ratio: 'original' };
  const supportDir = path.join(targetDir, 'Resources/support');
  fs.mkdirSync(supportDir, { recursive: true });
  const localFont = path.join(supportDir, 'Aa研宋.ttf');
  if (!SYSTEM8) {
    const donorFont = fs.existsSync(donorSubtitleMaterial.font_path) ? donorSubtitleMaterial.font_path : path.join(b05Dir, 'Resources/support/Aa研宋.ttf');
    fs.copyFileSync(donorFont, localFont);
  }
  const subtitleIds = new Set(subtitleTrack.segments.map((s) => s.material_id));
  const subtitleMaterials = draft.materials.texts.filter((m) => subtitleIds.has(m.id));
  for (const material of subtitleMaterials) {
    const rich = JSON.parse(material.content);
    const style = SYSTEM8 ? deep((rich.styles || [])[0] || donorStyle) : deep(donorStyle);
    style.range = [0, rich.text.length]; style.size = SYSTEM8 ? 8 : 6; style.strokes = [];
    if (!Array.isArray(style.shadows) || style.shadows.length === 0) style.shadows = deep(donorStyle.shadows || []);
    if (style.font) {
      style.font.path = SYSTEM8 ? '' : localFont;
      if (SYSTEM8) { style.font.id = ''; style.font.resource_id = ''; style.font.name = ''; }
    }
    rich.styles = [style];
    material.content = JSON.stringify(rich);
    material.font_size = SYSTEM8 ? 8 : 6; material.has_shadow = true; material.border_width = 0; material.border_alpha = 0; material.font_path = SYSTEM8 ? '' : localFont;
  }
  for (const segment of subtitleTrack.segments) {
    if (!segment.clip) continue;
    segment.clip.transform = segment.clip.transform || { x: 0, y: 0 };
    segment.clip.transform.y = -0.72;
  }
  const gain10 = Math.pow(10, 10 / 20);
  for (const segment of narrationTrack.segments) { segment.volume = gain10; segment.last_nonzero_volume = gain10; }

  const visualDir = path.join(targetDir, 'Resources/avatar_hengban_ziranliu');
  fs.mkdirSync(visualDir, { recursive: true });
  const personMaterials = [];
  const personSegments = [];
  for (let i = 0; i < plan.videoSources.length; i += 1) {
    const source = plan.videoSources[i];
    const local = path.join(visualDir, `person_${String(i + 1).padStart(2, '0')}_${path.basename(source)}`);
    fs.copyFileSync(source, local);
    const material = makeVideoMaterial(videoMaterialTemplate, local, plan.videoInfo[i], 'video');
    const [start, end] = plan.ranges[i];
    personMaterials.push(material);
    personSegments.push(makeSegment(videoSegmentTemplate, material, start, end - start));
  }
  const localIntro = path.join(visualDir, '横版通用片头.mp4');
  fs.copyFileSync(introSource, localIntro);
  const introMaterial = makeVideoMaterial(videoMaterialTemplate, localIntro, introInfo, 'video');
  const introSegment = makeSegment(videoSegmentTemplate, introMaterial, presetStart, presetEnd - presetStart);
  const localStill = path.join(visualDir, path.basename(plan.stillSource));
  fs.copyFileSync(plan.stillSource, localStill);
  const stillMaterial = makeVideoMaterial(photoMaterialTemplate, localStill, { ...plan.stillInfo, duration: draft.duration }, 'photo');
  const stillSegment = makeSegment(photoSegmentTemplate, stillMaterial, stillStart, draft.duration - stillStart);
  const allSegments = [personSegments[0], introSegment, personSegments[1], stillSegment].sort((a, b) => a.target_timerange.start - b.target_timerange.start);
  if (!Array.isArray(draft.materials.transitions)) draft.materials.transitions = [];
  const transitionIds = [];
  for (const segment of allSegments.slice(0, -1)) {
    const transition = { category_id: '', category_name: '', platform: 'all', type: 'transition', name: '叠化', id: id(), duration: 300_000, effect_id: '322577', is_overlap: true, resource_id: '6724845717472416269' };
    draft.materials.transitions.push(transition); segment.extra_material_refs.push(transition.id); transitionIds.push(transition.id);
  }
  draft.tracks.unshift(
    { attribute: 0, flag: 0, id: id(), is_default_name: false, name: '主轨道｜保持空置', segments: [], type: 'video' },
    { attribute: 0, flag: 2, id: id(), is_default_name: false, name: '横版自然流画面｜附加轨道', segments: allSegments, type: 'video' },
  );
  draft.materials.videos.push(...personMaterials, introMaterial, stillMaterial);

  const overlay = remapIds(deep(wrapper.materials.drafts[0].draft));
  const replacements = new Map([
    ['探花社交\n间歇性冷漠与情绪奖赏反差模型完整剖析\n完整未删减版', plan.title],
    ['掌控冷热反差 奖赏间隔和失去感的运行规则', plan.bodyLead],
    ['间歇性冷漠完整剖析', plan.bodyShort],
  ]);
  for (const material of overlay.materials.texts || []) {
    const oldText = JSON.parse(material.content).text;
    if (replacements.has(oldText)) setRichText(material, replacements.get(oldText));
  }
  const overlayTextById = new Map((overlay.materials.texts || []).map((m) => [m.id, JSON.parse(m.content).text]));
  for (const track of overlay.tracks) {
    if (!track.segments.length) continue;
    track.name = track.type === 'filter' ? '全程黑曜' : track.type === 'effect' ? '全程暗角' : track.type === 'text' ? '横版自然流文字层' : '横版自然流装饰层';
    for (const segment of track.segments) {
      const start = segment.target_timerange?.start || 0;
      const text = overlayTextById.get(segment.material_id) || '';
      if (track.type === 'text' && segment.target_timerange && start === 0 && text.startsWith('探花社交\n')) {
        segment.target_timerange.duration = stillStart;
        segment.clip.transform.x = -0.548; segment.clip.transform.y = 0.82;
      } else if ((track.type === 'text' || track.type === 'sticker') && segment.target_timerange && start > 0 && segment.target_timerange.duration > 13_000_000) {
        segment.target_timerange.start = stillStart; segment.target_timerange.duration = draft.duration - stillStart;
      } else if (segment.target_timerange && segment.target_timerange.duration > 13_000_000) {
        segment.target_timerange.duration = draft.duration - start;
      }
      if (track.type === 'video') segment.volume = 0;
    }
    draft.tracks.push(track);
  }
  mergeMaterials(draft, overlay);

  const localBgm = path.join(visualDir, '我的预设7.m4a');
  fs.copyFileSync(donorBgmSource, localBgm);
  const bgmMaterial = deep(donorBgmMaterial);
  bgmMaterial.id = id(); bgmMaterial.local_material_id = bgmMaterial.id; bgmMaterial.path = localBgm; bgmMaterial.name = '我的预设7';
  draft.materials.audios.push(bgmMaterial);
  const bgmSegment = deep(donorBgmSegment);
  bgmSegment.id = id(); bgmSegment.material_id = bgmMaterial.id;
  bgmSegment.target_timerange = { start: 0, duration: draft.duration };
  bgmSegment.source_timerange = { start: 0, duration: draft.duration };
  bgmSegment.volume = Math.pow(10, 4.9 / 20); bgmSegment.last_nonzero_volume = bgmSegment.volume; bgmSegment.extra_material_refs = [];
  draft.tracks.push({ attribute: 0, flag: 0, id: id(), is_default_name: false, name: '背景音乐｜我的预设 7', segments: [bgmSegment], type: 'audio' });

  let resourceIndex = 0;
  const copied = new Map();
  function localizeFiles(value) {
    if (!value || typeof value !== 'object') return;
    if (Array.isArray(value)) { for (const x of value) localizeFiles(x); return; }
    for (const [key, child] of Object.entries(value)) {
      if ((key === 'path' || key === 'font_path') && typeof child === 'string' && path.isAbsolute(child) && fs.existsSync(child) && fs.statSync(child).isFile() && !child.startsWith(targetDir)) {
        if (!copied.has(child)) {
          resourceIndex += 1;
          const destination = path.join(visualDir, `import_${String(resourceIndex).padStart(2, '0')}${path.extname(child) || '.bin'}`);
          fs.copyFileSync(child, destination); copied.set(child, destination);
        }
        value[key] = copied.get(child);
      } else localizeFiles(child);
    }
  }
  localizeFiles(draft);
  for (const track of draft.tracks.filter((t) => t.type === 'video')) for (const segment of track.segments) segment.volume = 0;
  draft.update_time = Date.now() * 1000;

  const packagingSegments = draft.tracks.filter((t) => t.type === 'text' && t.name === '横版自然流文字层').flatMap((t) => t.segments);
  const offlineFiles = [];
  (function collectPaths(value) {
    if (!value || typeof value !== 'object') return;
    if (Array.isArray(value)) { for (const x of value) collectPaths(x); return; }
    for (const [key, child] of Object.entries(value)) {
      if ((key === 'path' || key === 'font_path') && typeof child === 'string' && path.isAbsolute(child) && !fs.existsSync(child)) offlineFiles.push(child);
      else collectPaths(child);
    }
  })(draft);
  const contiguous = allSegments.every((s, i) => i === 0 || allSegments[i - 1].target_timerange.start + allSegments[i - 1].target_timerange.duration === s.target_timerange.start);
  const subtitleStyleOk = subtitleMaterials.every((material) => {
    const rich = JSON.parse(material.content);
    const expectedSize = SYSTEM8 ? 8 : 6;
    return material.font_size === expectedSize && material.has_shadow === true && Number(material.border_width || 0) === 0 &&
      (rich.styles || []).every((style) => style.size === expectedSize && (!style.strokes || style.strokes.length === 0) && Array.isArray(style.shadows) && style.shadows.length > 0);
  });
  const sourceDraftTitle = path.basename(targetDir);
  const femaleLeadFolderName = path.basename(plan.heroineDir);
  const finalDraftTitle = sourceDraftTitle;
  const mediaBinSources = [...personMaterials.map((material) => material.path), localIntro, localStill];
  const qa = {
    target: targetDir, backup: backupDir, duration_seconds: draft.duration / 1e6, canvas: draft.canvas_config,
    subtitles: subtitleTrack.segments.length, subtitle_style: SYSTEM8 ? '系统 / 8号 / 阴影开 / 描边关' : 'Aa研宋 / 6号 / 阴影开 / 描边关', subtitle_style_ok: subtitleStyleOk,
    semantic_markers: { intro_start_seconds: presetStart / 1e6, intro_end_seconds: presetEnd / 1e6, still_start_seconds: stillStart / 1e6 },
    visual_sequence: allSegments.map((s) => ({ start: s.target_timerange.start / 1e6, end: (s.target_timerange.start + s.target_timerange.duration) / 1e6, kind: s === personSegments[0] ? '数字人一次开场' : s === introSegment ? '横版通用片头' : s === stillSegment ? '正文单图' : '人物视频' })),
    heroine_folder: plan.heroineDir, person_sources: plan.videoSources, video_sequence_signature: plan.videoSources.join('|'), still_source: plan.stillSource,
    source_draft_title: sourceDraftTitle, female_lead_folder_name: femaleLeadFolderName, final_draft_title: finalDraftTitle,
    draft_title_format_ok: finalDraftTitle.includes(femaleLeadFolderName),
    media_bin_sources: mediaBinSources, media_bin_count: mediaBinSources.length, media_bin_frontend_confirmed: false,
    same_female_lead: [...plan.videoSources.slice(1), plan.stillSource].every((source) => source.startsWith(`${plan.heroineDir}${path.sep}`)),
    horizontal_person_sources: plan.videoInfo.every((info) => info.width > info.height), transition_name: '叠化', transition_count: transitionIds.length, transition_duration_seconds: 0.3,
    contiguous_visuals: contiguous, main_track_empty: draft.tracks.some((t) => t.type === 'video' && t.flag === 0 && t.segments.length === 0),
    all_populated_visuals_overlay: draft.tracks.filter((t) => t.type === 'video' && t.segments.length).every((t) => t.flag === 2),
    all_video_muted: draft.tracks.filter((t) => t.type === 'video').every((t) => t.segments.every((s) => s.volume === 0)),
    opening_title_transform: { x: -0.548, y: 0.82 }, opening_title_end_seconds: stillStart / 1e6,
    body_packaging_start_seconds: stillStart / 1e6, body_packaging_text_segments: packagingSegments.filter((s) => s.target_timerange.start === stillStart).length,
    offline_files: [...new Set(offlineFiles)],
  };
  qa.structural_pass = qa.canvas.width === 1920 && qa.canvas.height === 1080 && qa.subtitle_style_ok && qa.same_female_lead && qa.horizontal_person_sources && qa.contiguous_visuals && qa.main_track_empty && qa.all_populated_visuals_overlay && qa.all_video_muted && qa.body_packaging_text_segments === 4 && qa.offline_files.length === 0;
  if (!qa.structural_pass) throw new Error(`${plan.code} structural QA failed: ${JSON.stringify(qa, null, 2)}`);
  const encoded = JSON.stringify(draft);
  atomicWrite(contentPath, encoded);
  atomicWrite(path.join(targetDir, 'draft_info.json'), encoded);
  try {
    const metaPath = path.join(targetDir, 'draft_meta_info.json');
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    meta.tm_draft_modified = Date.now() * 1000; meta.tm_duration = draft.duration;
    atomicWrite(metaPath, JSON.stringify(meta));
  } catch {}
  spawnSync(ffmpeg, ['-loglevel', 'error', '-y', '-ss', '1', '-i', personMaterials[0].path, '-frames:v', '1', '-vf', 'scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2:black', path.join(targetDir, 'draft_cover.jpg')]);
  qa.updated_at = new Date().toISOString();
  fs.writeFileSync(path.join(targetDir, 'avatar_hengban_qa.json'), JSON.stringify(qa, null, 2));
  results.push(qa);
}

const batchReport = { ...preflight, mode: 'applied', applied_count: results.length, results, updated_at: new Date().toISOString() };
fs.writeFileSync(batchReportPath, JSON.stringify(batchReport, null, 2));
console.log(JSON.stringify(batchReport, null, 2));
