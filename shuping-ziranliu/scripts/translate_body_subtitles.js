const fs = require('fs');
const https = require('https');
const path = require('path');

function requireEnv(name) {
  const value = process.env[name];
  if (!value || !value.trim()) throw new Error(`缺少必填环境变量：${name}`);
  return value.trim();
}

const sourcePath = requireEnv('SOURCE_PATH');
const outputPath = requireEnv('OUTPUT_PATH');
const boundary = Number(requireEnv('BOUNDARY_US'));
if (!Number.isFinite(boundary) || boundary < 0) throw new Error('BOUNDARY_US 必须是非负微秒数');

const draft = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
const textById = new Map((draft.materials.texts || []).map((item) => [item.id, item]));
const subtitleTrack = draft.tracks.find((track) => track.name === '字幕');
if (!subtitleTrack) throw new Error('subtitle track missing');

const body = subtitleTrack.segments
  .filter((segment) => segment.target_timerange.start >= boundary)
  .map((segment, index) => {
    const material = textById.get(segment.material_id);
    const text = JSON.parse(material.content).text.trim();
    return {
      index,
      material_id: segment.material_id,
      start: segment.target_timerange.start,
      duration: segment.target_timerange.duration,
      zh: text,
    };
  });

let existing = {};
if (fs.existsSync(outputPath)) {
  const parsed = JSON.parse(fs.readFileSync(outputPath, 'utf8'));
  existing = Object.fromEntries((parsed.items || []).map((item) => [item.material_id, item.en]));
}

function translate(text) {
  const body = new URLSearchParams({ client: 'gtx', sl: 'zh-CN', tl: 'en', dt: 't', q: text }).toString();
  return new Promise((resolve, reject) => {
    const request = https.request('https://translate.google.com/translate_a/single', {
      method: 'POST',
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(body),
      },
    }, (response) => {
      let raw = '';
      response.setEncoding('utf8');
      response.on('data', (chunk) => { raw += chunk; });
      response.on('end', () => {
        if (response.statusCode !== 200) return reject(new Error(`HTTP ${response.statusCode}: ${raw.slice(0, 200)}`));
        try {
          const payload = JSON.parse(raw);
          const translated = (payload[0] || []).map((part) => part[0] || '').join('').trim();
          if (!translated) throw new Error('empty translation');
          resolve(translated);
        } catch (error) {
          reject(error);
        }
      });
    });
    request.setTimeout(15000, () => request.destroy(new Error('translation timeout')));
    request.on('error', reject);
    request.write(body);
    request.end();
  });
}

async function translateWithRetry(text) {
  let last;
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    try { return await translate(text); } catch (error) {
      last = error;
      await new Promise((resolve) => setTimeout(resolve, attempt * 700));
    }
  }
  throw last;
}

async function main() {
  const items = body.map((item) => ({ ...item, en: existing[item.material_id] || '' }));
  const pending = items.filter((item) => !item.en);
  const chunkSize = 70;
  for (let offset = 0; offset < pending.length; offset += chunkSize) {
    const chunk = pending.slice(offset, offset + chunkSize);
    const numbered = chunk.map((item) => `[[${String(item.index + 1).padStart(4, '0')}]] ${item.zh}`).join('\n');
    const translated = await translateWithRetry(numbered);
    const parsed = new Map();
    for (const match of translated.matchAll(/\[\[(\d{4})\]\]\s*([\s\S]*?)(?=\[\[\d{4}\]\]|$)/g))
      parsed.set(Number(match[1]) - 1, match[2].trim().replace(/\s+/g, ' '));
    for (const item of chunk) {
      const en = parsed.get(item.index);
      if (!en) throw new Error(`translation batch lost subtitle index ${item.index + 1}`);
      item.en = en;
    }
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify({
      source: sourcePath,
      boundary_seconds: boundary / 1e6,
      count: items.length,
      translation_provider: 'Google Translate public endpoint',
      items,
    }, null, 2));
    process.stdout.write(`translated ${Math.min(offset + chunk.length, pending.length)}/${pending.length}\n`);
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
  fs.writeFileSync(outputPath, JSON.stringify({
    source: sourcePath,
    boundary_seconds: boundary / 1e6,
    count: items.length,
    translation_provider: 'Google Translate public endpoint',
    items,
  }, null, 2));
  console.log(JSON.stringify({ outputPath, count: items.length, complete: items.every((item) => item.en) }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
