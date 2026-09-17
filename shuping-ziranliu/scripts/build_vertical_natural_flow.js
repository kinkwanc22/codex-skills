const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

function requireEnv(name) {
  const value = process.env[name];
  if (!value || !value.trim()) throw new Error(`缺少必填环境变量：${name}`);
  return value.trim();
}

const draftRoot = process.env.DRAFT_ROOT || '/Users/kin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft';
const sourceName = requireEnv('SOURCE_NAME');
const targetName = requireEnv('TARGET_NAME');
const sourceDir = path.join(draftRoot, sourceName);
const targetDir = path.join(draftRoot, targetName);
const metaTemplatePath = path.join(draftRoot, '千川短版_自然流千川_大号07_聊天四种情绪调动技巧_0917', 'draft_meta_info.json');
const presetWrapperPath = path.join(
  draftRoot,
  '大号07_聊天四种情绪调动技巧_音频字幕_0913',
  'subdraft/37CE002D-CD4C-4621-AAF8-FB71455BCC3F/draft_content.json',
);
const bgmPath = '/Users/kin/Library/Containers/com.lemon.lvpro/Data/Movies/JianyingPro/User Data/Presets/Combination/Resources/b04d3d9275dfb64c88a7428af777ad7e.m4a';
const femaleFolder = requireEnv('FEMALE_FOLDER');
const large07OpeningPath = path.join(femaleFolder, requireEnv('OPENING_VIDEO_1'));
const large07OpeningPath2 = path.join(femaleFolder, requireEnv('OPENING_VIDEO_2'));
const bodyStillPath = path.join(femaleFolder, requireEnv('BODY_STILL'));
const openingMarkerText = process.env.OPENING_MARKER_TEXT || '今天我们要聊的是';
const calibratedBodyStart = 8133333;
const bubbleTransitionSource = '/Users/kin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/8月19日/subdraft/33B94B83-7351-47CA-B543-B4AC9EE79A11/draft_content.json';
const localYanSong = '/Users/kin/Documents/Codex/2026-08-31/wo-k/work/vertical_b02_learning/preset22_components/fonts/Aa研宋.ttf';
const systemChineseFont = '/Applications/VideoFusion-macOS.app/Contents/Resources/Font/SystemFont/zh-hans.ttf';
const translationPath = requireEnv('TRANSLATION_PATH');
const bodyTitleText = requireEnv('BODY_TITLE_TEXT');
const openingWidth = Number(process.env.OPENING_WIDTH || 720);
const openingHeight = Number(process.env.OPENING_HEIGHT || 1280);
const narrationVolume10Db = 10 ** (10 / 20);
const gearBridgeDuration = 1833333;
const bodyChineseY = -0.24;
const bodyEnglishY = -0.35;

const clone = (value) => JSON.parse(JSON.stringify(value));
const newId = () => crypto.randomUUID().replace(/-/g, '');

function collectIds(value, output = new Set()) {
  if (!value || typeof value !== 'object') return output;
  if (Array.isArray(value)) {
    for (const item of value) collectIds(item, output);
    return output;
  }
  if (typeof value.id === 'string' && value.id) output.add(value.id);
  for (const item of Object.values(value)) collectIds(item, output);
  return output;
}

function remapIds(value) {
  const mapping = new Map([...collectIds(value)].map((oldId) => [oldId, newId()]));
  function walk(item) {
    if (typeof item === 'string') return mapping.get(item) || item;
    if (!item || typeof item !== 'object') return item;
    if (Array.isArray(item)) return item.map(walk);
    return Object.fromEntries(Object.entries(item).map(([key, child]) => [key, walk(child)]));
  }
  return walk(value);
}

function mergeMaterials(target, donor) {
  for (const [key, values] of Object.entries(donor.materials || {})) {
    if (!Array.isArray(values)) continue;
    if (!Array.isArray(target.materials[key])) target.materials[key] = [];
    target.materials[key].push(...values);
  }
  for (const [key, values] of Object.entries(donor.keyframes || {})) {
    if (!Array.isArray(values)) continue;
    if (!Array.isArray(target.keyframes[key])) target.keyframes[key] = [];
    target.keyframes[key].push(...values);
  }
  if (Array.isArray(donor.keyframe_graph_list)) {
    if (!Array.isArray(target.keyframe_graph_list)) target.keyframe_graph_list = [];
    target.keyframe_graph_list.push(...donor.keyframe_graph_list);
  }
}

function setText(material, text) {
  const rich = JSON.parse(material.content);
  rich.text = text;
  for (const style of rich.styles || []) style.range = [0, text.length];
  material.content = JSON.stringify(rich);
  material.translate_original_text = text;
}

function extendLongSegments(donor, finalDuration) {
  const originalDuration = donor.duration;
  for (const track of donor.tracks || []) {
    for (const segment of track.segments || []) {
      const range = segment.target_timerange;
      if (!range) continue;
      const end = range.start + range.duration;
      if (end >= originalDuration - 500000) {
        range.duration = Math.max(0, finalDuration - range.start);
      }
      if (segment.source_timerange && segment.source_timerange.duration > range.duration && track.type !== 'audio') {
        segment.source_timerange.duration = range.duration;
      }
    }
  }
  donor.duration = finalDuration;
}

function localizeFiles(value, supportDir, targetPrefix, copied = new Map()) {
  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) {
    for (const item of value) localizeFiles(item, supportDir, targetPrefix, copied);
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    if ((key === 'path' || key === 'font_path') && typeof child === 'string' && path.isAbsolute(child) && fs.existsSync(child) && fs.statSync(child).isFile()) {
      if (!child.startsWith(targetPrefix)) {
        if (!copied.has(child)) {
          const extension = path.extname(child) || '.bin';
          const destination = path.join(supportDir, `${String(copied.size + 1).padStart(2, '0')}_${path.basename(child, extension).slice(0, 32)}${extension}`);
          fs.copyFileSync(child, destination);
          copied.set(child, destination);
        }
        value[key] = copied.get(child);
      }
    } else {
      localizeFiles(child, supportDir, targetPrefix, copied);
    }
  }
}

if (!fs.existsSync(sourceDir)) throw new Error(`source draft missing: ${sourceDir}`);
if (!fs.existsSync(metaTemplatePath)) throw new Error(`plain metadata template missing: ${metaTemplatePath}`);
if (!fs.existsSync(presetWrapperPath)) throw new Error(`large-07 preset snapshot missing: ${presetWrapperPath}`);
if (!fs.existsSync(bgmPath)) throw new Error(`large-07 background audio missing: ${bgmPath}`);
if (!fs.existsSync(large07OpeningPath)) throw new Error(`large-07 opening video missing: ${large07OpeningPath}`);
if (!fs.existsSync(large07OpeningPath2)) throw new Error(`large-07 second opening video missing: ${large07OpeningPath2}`);
if (!fs.existsSync(bodyStillPath)) throw new Error(`body still missing: ${bodyStillPath}`);
if (!fs.existsSync(bubbleTransitionSource)) throw new Error(`bubble transition source missing: ${bubbleTransitionSource}`);
if (!fs.existsSync(localYanSong)) throw new Error(`YanSong font missing: ${localYanSong}`);
if (!fs.existsSync(systemChineseFont)) throw new Error(`system Chinese font missing: ${systemChineseFont}`);
if (!fs.existsSync(translationPath)) throw new Error(`body translation missing: ${translationPath}`);
if (fs.existsSync(targetDir)) throw new Error(`target already exists: ${targetDir}`);

fs.cpSync(sourceDir, targetDir, { recursive: true });

// B02 has already been opened by the current Jianying version, which adds an
// encrypted Timelines entry that takes precedence over draft_content.json.
// This is an independent test copy, so remove those copied runtime entries and
// let Jianying load the rebuilt portable timeline below.
for (const runtimeEntry of [
  'Timelines', 'subdraft', '.backup', 'deepagent',
  'draft_biz_config.json', 'draft_agency_config.json', 'timeline_layout.json',
  'agent_adoption_ledger.db', 'key_value.json', 'draft.extra', 'draft_settings',
  'template-2.tmp', 'attachment_editing.json', 'attachment_pc_common.json',
  'common_attachment', 'performance_opt_info.json', 'draft_virtual_store.json',
]) {
  fs.rmSync(path.join(targetDir, runtimeEntry), { recursive: true, force: true });
}

const contentPath = path.join(targetDir, 'draft_content.json');
const draft = JSON.parse(fs.readFileSync(contentPath, 'utf8'));
const sourceDuration = draft.duration;
const finalDuration = sourceDuration + gearBridgeDuration;
function relinkSourcePaths(value) {
  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) return value.forEach(relinkSourcePaths);
  for (const [key, child] of Object.entries(value)) {
    if (typeof child === 'string' && child.includes(sourceDir)) value[key] = child.split(sourceDir).join(targetDir);
    else relinkSourcePaths(child);
  }
}
relinkSourcePaths(draft);
if (draft.tracks.some((track) => track.type === 'video' && (track.segments || []).length)) {
  throw new Error('B02 source unexpectedly already has visual tracks');
}

// Resolve the opening/body boundary from the actual subtitle semantics. The
// marker itself belongs to the opening; the next subtitle starts the body.
const textById = new Map((draft.materials.texts || []).map((material) => [material.id, material]));
const subtitleTrackIndex = draft.tracks.findIndex((track) => track.name === '字幕');
const narrationTrackIndex = draft.tracks.findIndex((track) => track.name === '配音');
if (subtitleTrackIndex < 0 || narrationTrackIndex < 0) throw new Error('source subtitle or narration track missing');
const subtitleTrack = draft.tracks[subtitleTrackIndex];
const markerSegment = subtitleTrack.segments.find((segment) => {
  const material = textById.get(segment.material_id);
  if (!material) return false;
  return JSON.parse(material.content).text.trim() === openingMarkerText;
});
if (!markerSegment) throw new Error(`opening marker missing: ${openingMarkerText}`);
const openingBoundary = markerSegment.target_timerange.start + markerSegment.target_timerange.duration;
const bodyStart = openingBoundary + gearBridgeDuration;
const packagingShift = bodyStart - calibratedBodyStart;

const openingSubtitleSegments = subtitleTrack.segments.filter((segment) =>
  segment.target_timerange.start + segment.target_timerange.duration <= openingBoundary,
);
const bodySubtitleSegments = subtitleTrack.segments.filter((segment) =>
  segment.target_timerange.start >= openingBoundary,
);
if (openingSubtitleSegments.length + bodySubtitleSegments.length !== subtitleTrack.segments.length) {
  throw new Error('a subtitle crosses the semantic opening boundary');
}
for (const segment of bodySubtitleSegments) segment.target_timerange.start += gearBridgeDuration;
subtitleTrack.name = `字幕｜${(openingBoundary / 1e6).toFixed(3)}秒语义分界`;
const fontLocalDir = path.join(targetDir, 'Resources', 'vertical_natural_flow', 'fonts');
fs.mkdirSync(fontLocalDir, { recursive: true });
const fontLocal = path.join(fontLocalDir, 'Aa研宋.ttf');
fs.copyFileSync(localYanSong, fontLocal);
for (const segment of subtitleTrack.segments) {
  const material = (draft.materials.texts || []).find((item) => item.id === segment.material_id);
  if (!material) continue;
  const content = JSON.parse(material.content);
  const isOpening = segment.target_timerange.start < openingBoundary;
  material.alignment = 1;
  material.font_path = isOpening ? fontLocal : systemChineseFont;
  material.font_name = isOpening ? 'Aa研宋' : '系统';
  material.font_title = isOpening ? 'none' : '系统';
  if (isOpening) {
    material.font_resource_id = '7130644288047682085';
    material.font_source_platform = 1;
    material.fonts = [{
      category_id: 'user',
      category_name: '最近使用',
      effect_id: '7130644288047682085',
      file_uri: '',
      id: material.id,
      path: fontLocal,
      request_id: '',
      resource_id: '7130644288047682085',
      source_platform: 1,
      team_id: '',
      third_resource_id: '',
      title: '研宋体',
    }];
  } else {
    delete material.font_resource_id;
    delete material.font_source_platform;
    delete material.fonts;
  }
  material.has_shadow = isOpening;
  material.shadow_alpha = 0.9;
  material.shadow_angle = -45;
  material.shadow_color = '#000000';
  material.shadow_distance = 5;
  material.shadow_point = { x: 0.636396103067893, y: -0.636396103067893 };
  material.shadow_smoothing = 0.45;
  for (const style of content.styles || []) {
    style.size = isOpening ? 9 : 8;
    style.font = isOpening ? { path: fontLocal, id: '7130644288047682085' } : { path: systemChineseFont, id: '' };
    style.fill = { alpha: 1, content: { render_type: 'solid', solid: { alpha: 1, color: [1, 1, 1] } } };
    style.strokes = isOpening ? [] : [{
      content: { render_type: 'solid', solid: { alpha: 1, color: [0, 0, 0] } },
      width: 0.08,
      mode: 0,
    }];
    // Jianying's inspector only treats the shadow as enabled when the rich
    // text style contains a native `shadows` entry. The outer has_shadow /
    // shadow_* fields alone are not sufficient after the timeline is upgraded.
    if (isOpening) {
      style.shadows = [{
        thickness_projection_distance: 0,
        diffuse: 0.02500000037252903,
        angle: -45,
        thickness_projection_enable: false,
        content: { solid: { color: [0, 0, 0] }, render_type: 'solid' },
        distance: 4.999999523162842,
        thickness_projection_angle: -45,
        alpha: 0.899999976158142,
      }];
    } else {
      delete style.shadows;
    }
  }
  material.content = JSON.stringify(content);
  if (!segment.clip) segment.clip = {};
  // Source subtitle clips may carry stale unresolved style refs. Jianying can
  // interpret those as a 50% blend even when clip/global/fill alpha are 1.
  // The rebuilt captions are fully self-contained, so discard those refs.
  segment.extra_material_refs = [];
  segment.clip.alpha = 1;
  segment.clip.transform = { x: 0, y: isOpening ? 0 : bodyChineseY };
}

const narrationTrack = draft.tracks[narrationTrackIndex];
if ((narrationTrack.segments || []).length !== 1) throw new Error('source narration is not a single segment');
narrationTrack.name = `配音｜${(openingBoundary / 1e6).toFixed(3)}秒语义分界`;
const narrationOriginal = narrationTrack.segments[0];
const narrationOpening = clone(narrationOriginal);
narrationOpening.id = newId();
narrationOpening.target_timerange = { start: 0, duration: openingBoundary };
narrationOpening.source_timerange = { start: 0, duration: openingBoundary };
narrationOpening.volume = narrationVolume10Db;
narrationOpening.last_nonzero_volume = narrationVolume10Db;
const narrationBody = clone(narrationOriginal);
narrationBody.id = newId();
narrationBody.target_timerange = { start: bodyStart, duration: sourceDuration - openingBoundary };
narrationBody.source_timerange = { start: openingBoundary, duration: sourceDuration - openingBoundary };
narrationBody.volume = narrationVolume10Db;
narrationBody.last_nonzero_volume = narrationVolume10Db;
narrationTrack.segments = [narrationOpening, narrationBody];

const translation = JSON.parse(fs.readFileSync(translationPath, 'utf8'));
const englishByMaterialId = new Map((translation.items || []).map((item) => [item.material_id, item.en]));
if (englishByMaterialId.size !== bodySubtitleSegments.length) throw new Error('body translation count mismatch');
const englishTrack = {
  attribute: 0,
  flag: 0,
  id: newId(),
  is_default_name: false,
  name: '正文英文字幕｜外部翻译逐条对齐',
  type: 'text',
  segments: [],
};
for (const sourceSegment of bodySubtitleSegments) {
  const sourceMaterial = (draft.materials.texts || []).find((item) => item.id === sourceSegment.material_id);
  const englishText = englishByMaterialId.get(sourceSegment.material_id);
  if (!sourceMaterial || !englishText) throw new Error(`missing English subtitle for ${sourceSegment.material_id}`);
  const englishMaterial = clone(sourceMaterial);
  englishMaterial.id = newId();
  englishMaterial.local_material_id = englishMaterial.id;
  englishMaterial.font_path = systemChineseFont;
  englishMaterial.font_name = '系统';
  englishMaterial.font_title = '系统';
  englishMaterial.has_shadow = false;
  setText(englishMaterial, englishText);
  const englishContent = JSON.parse(englishMaterial.content);
  for (const style of englishContent.styles || []) {
    style.size = 8;
    style.font = { path: systemChineseFont, id: '' };
    style.fill = { alpha: 1, content: { render_type: 'solid', solid: { alpha: 1, color: [1, 1, 1] } } };
    style.strokes = [{
      content: { render_type: 'solid', solid: { alpha: 1, color: [0, 0, 0] } },
      width: 0.08,
      mode: 0,
    }];
  }
  englishMaterial.content = JSON.stringify(englishContent);
  draft.materials.texts.push(englishMaterial);
  const englishSegment = clone(sourceSegment);
  englishSegment.id = newId();
  englishSegment.material_id = englishMaterial.id;
  if (!englishSegment.clip) englishSegment.clip = {};
  englishSegment.clip.alpha = 1;
  englishSegment.clip.transform = { x: 0, y: bodyEnglishY };
  englishTrack.segments.push(englishSegment);
}
draft.tracks.splice(subtitleTrackIndex + 1, 0, englishTrack);

const wrapper = JSON.parse(fs.readFileSync(presetWrapperPath, 'utf8'));
const appliedPreset = wrapper.materials.drafts[0].draft;
const donor = remapIds(clone(appliedPreset));
extendLongSegments(donor, finalDuration);
for (const track of donor.tracks || []) {
  for (const segment of track.segments || []) {
    const range = segment.target_timerange;
    if (!range) continue;
    if (track.type === 'filter' || track.type === 'effect') {
      range.start = 0;
      range.duration = finalDuration;
    } else if (track.type === 'text' && range.start >= 6000000) {
      if (range.duration > 100000000) {
        range.start = bodyStart;
        range.duration = finalDuration - bodyStart;
      } else {
        range.start += openingBoundary - 6133333;
      }
    } else if (track.type === 'sticker' && range.start >= 6000000) {
      range.start = bodyStart;
      if (range.duration > 100000000) range.duration = finalDuration - bodyStart;
    }
  }
}

const donorAudioById = new Map((donor.materials.audios || []).map((material) => [material.id, material]));
let gearAligned = false;
let heartbeatAligned = false;
for (const track of (donor.tracks || []).filter((item) => item.type === 'audio')) {
  for (const segment of track.segments || []) {
    const material = donorAudioById.get(segment.material_id);
    const name = material?.name || '';
    if (name.includes('齿轮') || name.includes('闹钟')) {
      segment.target_timerange.start = openingBoundary;
      segment.target_timerange.duration = gearBridgeDuration;
      gearAligned = true;
    } else if (name.includes('心跳')) {
      segment.target_timerange.start = bodyStart;
      heartbeatAligned = true;
    }
  }
}
if (!gearAligned || !heartbeatAligned) throw new Error('gear or heartbeat SFX missing from preset donor');

const replacements = new Map([
  ['卸载压抑的道德面具\n让女人在你面前做自己\n瞬间让她被你吸引', bodyTitleText],
]);
for (const material of donor.materials.texts || []) {
  const text = JSON.parse(material.content).text;
  if (replacements.has(text)) setText(material, replacements.get(text));
}

const supportDir = path.join(targetDir, 'Resources/vertical_natural_flow');
fs.mkdirSync(supportDir, { recursive: true });
localizeFiles(donor, supportDir, targetDir);

// The applied preset contains a generic placeholder opening. Large-07 itself
// replaced that placeholder with this heroine clip, so reproduce that actual
// edit rather than the generic preset thumbnail.
const donorMainVideoTrack = (donor.tracks || []).find((track) =>
  track.type === 'video' && (track.segments || []).length === 2,
);
if (!donorMainVideoTrack) throw new Error('large-07 two-segment visual track missing');
const openingSegment = donorMainVideoTrack.segments[0];
const openingMaterial = (donor.materials.videos || []).find((material) => material.id === openingSegment.material_id);
if (!openingMaterial) throw new Error('large-07 opening material missing');
const firstOpeningDuration = Math.floor(openingBoundary / 2);
// The gear/clock bridge belongs visually to the opening. Keep the final
// opening video on screen until body narration actually starts.
const secondOpeningDuration = bodyStart - firstOpeningDuration;
const openingLocal = path.join(supportDir, 'opening_01_restaurant.mp4');
const openingLocal2 = path.join(supportDir, 'opening_02_conversation.mp4');
fs.copyFileSync(large07OpeningPath, openingLocal);
fs.copyFileSync(large07OpeningPath2, openingLocal2);
openingMaterial.path = openingLocal;
openingMaterial.material_name = path.basename(openingLocal);
openingMaterial.duration = firstOpeningDuration;
openingMaterial.width = openingWidth;
openingMaterial.height = openingHeight;
openingSegment.target_timerange = { start: 0, duration: firstOpeningDuration };
openingSegment.source_timerange = { start: 0, duration: firstOpeningDuration };
openingSegment.volume = 0;

const secondOpeningMaterial = clone(openingMaterial);
secondOpeningMaterial.id = newId();
secondOpeningMaterial.local_material_id = secondOpeningMaterial.id;
secondOpeningMaterial.path = openingLocal2;
secondOpeningMaterial.material_name = path.basename(openingLocal2);
secondOpeningMaterial.duration = secondOpeningDuration;
const secondOpeningSegment = clone(openingSegment);
secondOpeningSegment.id = newId();
secondOpeningSegment.material_id = secondOpeningMaterial.id;
secondOpeningSegment.target_timerange = { start: firstOpeningDuration, duration: secondOpeningDuration };
secondOpeningSegment.source_timerange = { start: 0, duration: secondOpeningDuration };
secondOpeningSegment.volume = 0;
donor.materials.videos.push(secondOpeningMaterial);
const bodyStillSegment = donorMainVideoTrack.segments[1];
bodyStillSegment.target_timerange = { start: bodyStart, duration: finalDuration - bodyStart };
bodyStillSegment.source_timerange = { start: 0, duration: finalDuration - bodyStart };
const bodyStillMaterial = (donor.materials.videos || []).find((material) => material.id === bodyStillSegment.material_id);
if (!bodyStillMaterial) throw new Error('large-07 body still material missing');
const bodyStillLocal = path.join(supportDir, '03_coffee.png');
fs.copyFileSync(bodyStillPath, bodyStillLocal);
bodyStillMaterial.path = bodyStillLocal;
bodyStillMaterial.material_name = '03_coffee.png';
bodyStillMaterial.duration = finalDuration - bodyStart;
bodyStillMaterial.width = 1080;
bodyStillMaterial.height = 1920;
bodyStillSegment.volume = 0;
donorMainVideoTrack.segments = [openingSegment, secondOpeningSegment, bodyStillSegment];

const bubbleOuter = JSON.parse(fs.readFileSync(bubbleTransitionSource, 'utf8'));
const bubbleDraft = bubbleOuter.materials.drafts[0].draft;
const bubbleTemplate = (bubbleDraft.materials.transitions || []).find((item) => item.name === '泡泡模糊');
if (!bubbleTemplate) throw new Error('泡泡模糊 transition material missing');
if (!Array.isArray(donor.materials.transitions)) donor.materials.transitions = [];
// Give every visual boundary its own transition material. Reusing a single
// transition id across two cuts can be collapsed by Jianying after native
// timeline upgrade, leaving only one visibly effective cut.
for (const segment of [openingSegment, secondOpeningSegment]) {
  const bubble = clone(bubbleTemplate);
  bubble.id = newId();
  bubble.duration = 1000000;
  donor.materials.transitions.push(bubble);
  if (!Array.isArray(segment.extra_material_refs)) segment.extra_material_refs = [];
  segment.extra_material_refs.push(bubble.id);
}

// Keep the source narration and subtitles, then add the exact applied preset-22
// visual/packaging tracks that form the large-07 editing method.
for (const track of donor.tracks || []) {
  if (track.type === 'video' && track.flag === 0 && !(track.segments || []).length) continue;
  track.name = track === donorMainVideoTrack ? '竖屏自然流｜附加画面轨｜语义开场＋正文单图'
    : track.type === 'filter' ? '大号07逻辑｜全程滤镜'
      : track.type === 'effect' ? '大号07逻辑｜全程暗角'
        : track.type === 'sticker' ? '大号07逻辑｜正文图标'
          : track.type === 'audio' ? '竖屏自然流｜固定短音效'
          : '大号07逻辑｜包装文字';
  draft.tracks.push(track);
}
mergeMaterials(draft, donor);

if (!draft.tracks.some((track) => track.type === 'video' && track.flag === 0 && !(track.segments || []).length)) {
  draft.tracks.unshift({ attribute: 0, flag: 0, id: newId(), is_default_name: false, name: '主视频轨道｜保持空置', type: 'video', segments: [] });
}
for (const track of draft.tracks.filter((item) => item.type === 'video' && (item.segments || []).length)) track.flag = 2;

// Large-07 also uses “我的预设7” as a full-length secondary audio bed.
const bgmLocal = path.join(supportDir, '我的预设7.m4a');
fs.copyFileSync(bgmPath, bgmLocal);
const bgmMaterialId = newId();
const bgmSpeedId = newId();
const bgmChannelId = newId();
draft.materials.audios.push({
  id: bgmMaterialId,
  local_material_id: bgmMaterialId,
  music_id: bgmMaterialId,
  unique_id: bgmMaterialId,
  name: '我的预设7',
  path: bgmLocal,
  duration: finalDuration,
  type: 'music',
  category_name: 'local',
  check_flag: 3,
  copyright_limit_type: 'none',
  source_platform: 0,
  wave_points: [],
});
draft.materials.speeds.push({ id: bgmSpeedId, curve_speed: null, mode: 0, speed: 1, type: 'speed' });
if (!Array.isArray(draft.materials.sound_channel_mappings)) draft.materials.sound_channel_mappings = [];
draft.materials.sound_channel_mappings.push({ id: bgmChannelId, audio_channel_mapping: 0, is_config_open: false, type: 'none' });
draft.tracks.push({
  attribute: 0,
  flag: 0,
  id: newId(),
  is_default_name: false,
  name: '背景音乐｜我的预设7｜固定0dB',
  type: 'audio',
  segments: [{
    id: newId(),
    material_id: bgmMaterialId,
    extra_material_refs: [bgmSpeedId, bgmChannelId],
    target_timerange: { start: 0, duration: finalDuration },
    source_timerange: { start: 0, duration: finalDuration },
    speed: 1,
    volume: 1,
    last_nonzero_volume: 1,
    visible: true,
    reverse: false,
  }],
});

draft.canvas_config = { ...(draft.canvas_config || {}), width: 1080, height: 1920, ratio: 'original' };
draft.duration = finalDuration;
draft.id = newId();
draft.name = targetName;
draft.update_time = Date.now() * 1000;

const encoded = JSON.stringify(draft);
fs.writeFileSync(contentPath, encoded);
fs.writeFileSync(path.join(targetDir, 'draft_info.json'), encoded);

const metaPath = path.join(targetDir, 'draft_meta_info.json');
const meta = JSON.parse(fs.readFileSync(metaTemplatePath, 'utf8'));
meta.draft_id = crypto.randomUUID().toUpperCase();
meta.draft_name = targetName;
meta.draft_fold_path = targetDir;
meta.tm_draft_create = Date.now() * 1000;
meta.tm_draft_modified = meta.tm_draft_create;
meta.tm_duration = finalDuration;
fs.writeFileSync(metaPath, JSON.stringify(meta));

const introVideo = draft.materials.videos.find((material) => material.type === 'video' && material.path && fs.existsSync(material.path));
if (introVideo) {
  spawnSync('/Users/kin/.local/bin/ffmpeg', [
    '-loglevel', 'error', '-y', '-ss', '1', '-i', introVideo.path, '-frames:v', '1',
    '-vf', 'scale=360:640:force_original_aspect_ratio=increase,crop=360:640',
    path.join(targetDir, 'draft_cover.jpg'),
  ]);
}

const importedVideoTrack = draft.tracks.find((track) => track.name === '竖屏自然流｜附加画面轨｜语义开场＋正文单图');
const visualSegments = importedVideoTrack.segments.map((segment) => ({
  start_seconds: segment.target_timerange.start / 1e6,
  end_seconds: (segment.target_timerange.start + segment.target_timerange.duration) / 1e6,
  material_id: segment.material_id,
})).sort((a, b) => a.start_seconds - b.start_seconds);
const offlinePaths = [];
function collectOffline(value) {
  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) return value.forEach(collectOffline);
  for (const [key, child] of Object.entries(value)) {
    if ((key === 'path' || key === 'font_path') && typeof child === 'string' && path.isAbsolute(child) && !fs.existsSync(child)) offlinePaths.push(child);
    else collectOffline(child);
  }
}
collectOffline(draft);

const qa = {
  target: targetDir,
  source_untouched: sourceDir,
  reference: `用户手动 B01 标准 / B02逐项校准规则 / ${path.basename(femaleFolder)}素材`,
  female_lead_folder: femaleFolder,
  opening_sources: [large07OpeningPath, large07OpeningPath2],
  opening_video_parts: 2,
  opening_marker_text: openingMarkerText,
  opening_boundary_seconds: openingBoundary / 1e6,
  gear_bridge_start_seconds: openingBoundary / 1e6,
  gear_bridge_duration_seconds: gearBridgeDuration / 1e6,
  body_start_seconds: bodyStart / 1e6,
  source_duration_seconds: sourceDuration / 1e6,
  duration_seconds: finalDuration / 1e6,
  canvas: draft.canvas_config,
  opening_subtitle_count: openingSubtitleSegments.length,
  body_subtitle_count: bodySubtitleSegments.length,
  body_english_subtitle_count: englishTrack.segments.length,
  opening_narration_count: narrationTrack.segments.filter((segment) => segment.target_timerange.start === 0 && segment.target_timerange.duration === openingBoundary).length,
  body_narration_count: narrationTrack.segments.filter((segment) => segment.target_timerange.start === bodyStart).length,
  narration_opening_end_seconds: openingBoundary / 1e6,
  narration_body_target_start_seconds: bodyStart / 1e6,
  narration_body_source_start_seconds: openingBoundary / 1e6,
  narration_volume_linear: narrationVolume10Db,
  narration_volume_db: 10,
  visual_segments: visualSegments,
  expected_logic: `0-${openingBoundary / 1e6}秒为开场口播；${openingBoundary / 1e6}-${bodyStart / 1e6}秒为独立齿轮过桥，画面继续延用最后一条开场视频；${bodyStart / 1e6}秒正文口播与心跳同时开始，正文单图也从此时切入并持续到结尾`,
  background_audio_volume: 1,
  background_audio_db: 0,
  background_audio_trimmed_to_timeline_end: true,
  opening_chinese_style: '研宋体9号/坐标(0,0)/居中/白色100%不透明/无描边/阴影',
  body_chinese_style: `系统字体8号/普通外层字幕轨坐标(0,${bodyChineseY})/居中/白色/黑色描边/画面中位于英文上方`,
  opening_english_subtitles: false,
  body_english_translation_status: '外部翻译已逐条写入并与正文中文时间码一致',
  body_english_style: `系统字体8号/普通外层字幕轨坐标(0,${bodyEnglishY})/居中/白色/黑色描边/画面中位于中文下方`,
  opening_visual_bridge_rule: `最后一条开场视频持续到正文开始 ${bodyStart / 1e6} 秒；正文图片不得在齿轮声期间提前出现`,
  gear_sfx_rule: `开场结束后独立播放：${openingBoundary / 1e6}-${bodyStart / 1e6}秒`,
  heartbeat_sfx_rule: `开始点严格对齐正文口播 ${bodyStart / 1e6} 秒`,
  transition_name: '泡泡模糊',
  transition_duration_seconds: 1,
  main_video_track_empty: draft.tracks.some((track) => track.type === 'video' && track.flag === 0 && !(track.segments || []).length),
  populated_video_tracks_overlay_only: draft.tracks.filter((track) => track.type === 'video' && (track.segments || []).length).every((track) => track.flag === 2),
  offline_paths: [...new Set(offlinePaths)],
};
qa.structural_pass = qa.canvas.width === 1080 && qa.canvas.height === 1920 &&
  qa.opening_subtitle_count + qa.body_subtitle_count === subtitleTrack.segments.length &&
  qa.body_english_subtitle_count === qa.body_subtitle_count &&
  qa.opening_narration_count === 1 && qa.body_narration_count === 1 &&
  qa.opening_video_parts === 2 && visualSegments.length === 3 && visualSegments[0].start_seconds === 0 &&
  visualSegments[1].end_seconds === qa.body_start_seconds &&
  visualSegments[2].start_seconds === qa.body_start_seconds &&
  visualSegments[2].end_seconds === qa.duration_seconds && qa.offline_paths.length === 0 &&
  qa.main_video_track_empty && qa.populated_video_tracks_overlay_only;
fs.writeFileSync(path.join(targetDir, 'vertical_natural_flow_qa.json'), JSON.stringify(qa, null, 2));

console.log(JSON.stringify(qa, null, 2));
