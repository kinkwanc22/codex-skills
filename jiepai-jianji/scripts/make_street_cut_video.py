#!/usr/bin/env python
import argparse
import json
import math
import random
import re
import shutil
import subprocess
import sys
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
SCRIPT_EXTS = {".docx", ".txt", ".md"}
SENTENCE_RE = re.compile(r"[^\u3002\uff01\uff1f!?;\uff1b\n]+[\u3002\uff01\uff1f!?;\uff1b]?")
ALIGN_CHAR_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]")

TRAD_TO_SIMP = str.maketrans(
    {
        "納": "纳",
        "應": "应",
        "讓": "让",
        "對": "对",
        "關": "关",
        "愛": "爱",
        "過": "过",
        "個": "个",
        "會": "会",
        "這": "这",
        "點": "点",
        "樣": "样",
        "頭": "头",
        "裡": "里",
        "麼": "么",
        "說": "说",
        "時": "时",
        "現": "现",
        "認": "认",
        "識": "识",
        "係": "系",
        "簡": "简",
        "單": "单",
        "實": "实",
        "際": "际",
        "無": "无",
        "別": "别",
        "選": "选",
        "來": "来",
        "點": "点",
        "難": "难",
        "氣": "气",
        "從": "从",
        "長": "长",
        "聽": "听",
        "項": "项",
        "視": "视",
        "變": "变",
        "體": "体",
        "層": "层",
        "過": "过",
        "學": "学",
        "術": "术",
        "條": "条",
        "內": "内",
        "開": "开",
        "斷": "断",
        "錯": "错",
        "後": "后",
        "給": "给",
        "產": "产",
        "聲": "声",
        "像": "像",
        "總": "总",
        "般": "般",
        "嗚": "呜",
        "為": "为",
        "將": "将",
        "請": "请",
        "與": "与",
        "萬": "万",
        "還": "还",
        "發": "发",
        "進": "进",
        "嗎": "吗",
        "著": "着",
        "聰": "聪",
        "優": "优",
        "壓": "压",
        "輸": "输",
        "贏": "赢",
        "鋪": "铺",
        "級": "级",
        "權": "权",
        "數": "数",
        "種": "种",
        "話": "话",
    }
)


def run(cmd, capture=False):
    kwargs = {"check": True, "text": True}
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE})
    return subprocess.run(cmd, **kwargs)


def resolve_tool(path_or_name, fallback_name):
    if path_or_name:
        p = Path(path_or_name)
        if p.exists():
            return p
    found = shutil.which(path_or_name or fallback_name)
    if found:
        return Path(found)
    raise FileNotFoundError(f"Cannot find {fallback_name}; pass --{fallback_name}.")


def first_file(path, exts):
    path = Path(path)
    if path.is_file():
        return path
    files = sorted([p for p in path.rglob("*") if p.suffix.lower() in exts], key=lambda p: (len(p.name), p.name))
    if not files:
        raise FileNotFoundError(f"No matching file under {path}")
    return files[0]


def read_docx(path):
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paras = []
    for para in root.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in para.findall(".//w:t", ns))
        if text.strip():
            paras.append(text.strip())
    return "\n".join(paras)


def read_script(path):
    path = first_file(path, SCRIPT_EXTS)
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return path.read_text(encoding="utf-8-sig")


def split_sentences(text):
    text = re.sub(r"\s+", "", text)
    return [m.group(0).strip() for m in SENTENCE_RE.finditer(text) if m.group(0).strip()]


def norm_text(text):
    text = text.translate(TRAD_TO_SIMP).lower()
    return "".join(ALIGN_CHAR_RE.findall(text))


def probe_json(ffprobe, path, stream=None):
    cmd = [str(ffprobe), "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", "format=duration,bit_rate,size", "-show_entries", "stream=duration,bit_rate,width,height,r_frame_rate", "-of", "json", str(path)]
    return json.loads(run(cmd, capture=True).stdout)


def probe_duration(ffprobe, path):
    data = probe_json(ffprobe, path)
    return float(data.get("format", {}).get("duration") or 0)


def probe_bitrate(ffprobe, path):
    data = probe_json(ffprobe, path, "v:0")
    streams = data.get("streams") or []
    bit_rate = None
    if streams:
        bit_rate = streams[0].get("bit_rate")
    bit_rate = bit_rate or data.get("format", {}).get("bit_rate")
    return float(bit_rate or 0)


def list_videos(video_dir, ffprobe, min_duration, min_bitrate):
    candidates = sorted([p for p in Path(video_dir).rglob("*") if p.suffix.lower() in VIDEO_EXTS])
    videos = []
    for p in candidates:
        try:
            duration = probe_duration(ffprobe, p)
            bitrate = probe_bitrate(ffprobe, p)
        except Exception:
            continue
        if duration >= min_duration and bitrate >= min_bitrate:
            videos.append({"path": p, "duration": duration, "bitrate": bitrate})
    if not videos:
        raise RuntimeError("No video clips passed the duration/bitrate filters.")
    return videos


def default_opening_video_dir(video_dir):
    candidate = Path(video_dir) / "可用"
    return candidate if candidate.exists() and candidate.is_dir() else None


def detect_silence_points(ffmpeg, audio, noise="-35dB", min_silence=0.18):
    cmd = [
        str(ffmpeg),
        "-hide_banner",
        "-nostats",
        "-i",
        str(audio),
        "-af",
        f"silencedetect=noise={noise}:d={min_silence}",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    points = []
    start = None
    for line in proc.stderr.splitlines():
        m = re.search(r"silence_start: ([0-9.]+)", line)
        if m:
            start = float(m.group(1))
        m = re.search(r"silence_end: ([0-9.]+)", line)
        if m:
            end = float(m.group(1))
            if start is not None:
                points.append((start + end) / 2)
            else:
                points.append(end)
            start = None
    return sorted(set(points))


def load_timed_words(path):
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []) or []:
            token = w.get("word", "")
            start = w.get("start")
            end = w.get("end")
            if token and start is not None and end is not None:
                words.append({"text": token, "start": float(start), "end": float(end)})
    return words


def timed_sentence_ends(sentences, words):
    if not words:
        return [], None
    script_norm = norm_text("".join(sentences))
    asr_chars = []
    char_times = []
    for word in words:
        chars = list(norm_text(word["text"]))
        if not chars:
            continue
        for char in chars:
            asr_chars.append(char)
            char_times.append(word["end"])
    asr_norm = "".join(asr_chars)
    matcher = SequenceMatcher(None, script_norm, asr_norm, autojunk=False)
    script_to_asr = {}
    matched = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                script_to_asr[i1 + offset] = j1 + offset
                matched += 1
    ends = []
    pos = 0
    for sentence in sentences:
        pos += len(norm_text(sentence))
        target = pos - 1
        asr_i = script_to_asr.get(target)
        if asr_i is None:
            for delta in range(1, 8):
                asr_i = script_to_asr.get(target - delta)
                if asr_i is not None:
                    break
        if asr_i is not None and 0 <= asr_i < len(char_times):
            ends.append(char_times[asr_i])
    stats = {
        "matched_chars": matched,
        "script_chars": len(script_norm),
        "asr_chars": len(asr_norm),
        "match_ratio": matched / max(1, len(script_norm)),
        "timed_sentence_points": len(ends),
    }
    return sorted(set(ends)), stats


def proportional_sentence_ends(sentences, audio_duration):
    lengths = [max(1, len(norm_text(s))) for s in sentences]
    total = sum(lengths)
    acc = 0
    ends = []
    for length in lengths:
        acc += length
        ends.append(audio_duration * acc / total)
    return ends


def nearest(points, target, window):
    candidates = [p for p in points if abs(p - target) <= window]
    if not candidates:
        return None
    return min(candidates, key=lambda p: abs(p - target))


def choose_cut_points(audio_duration, sentence_points, silence_points, min_len, max_len):
    cuts = []
    current = 0.0
    while current + max_len < audio_duration:
        low = current + min_len
        high = current + max_len
        target = (low + high) / 2
        candidates = [p for p in sentence_points if low <= p <= high]
        if candidates:
            cut = min(candidates, key=lambda p: abs(p - target))
            near_silence = nearest(silence_points, cut, 0.45)
            if near_silence is not None and low <= near_silence <= high:
                cut = near_silence
        else:
            candidates = [p for p in silence_points if low <= p <= high]
            cut = min(candidates, key=lambda p: abs(p - target)) if candidates else target
        if cuts and cut <= cuts[-1] + 1:
            cut = cuts[-1] + min_len
        cuts.append(min(cut, audio_duration - 0.25))
        current = cuts[-1]
    return [p for p in cuts if 0 < p < audio_duration - 0.25]


def render_segment(ffmpeg, source, output, duration, start, width, height, fps, fade_duration):
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps={fps},format=yuv420p"
    )
    filters = [vf]
    if fade_duration and fade_duration > 0:
        fade_out = max(0.0, duration - fade_duration)
        filters.append(f"fade=t=in:st=0:d={fade_duration},fade=t=out:st={fade_out}:d={fade_duration}")
    cmd = [
        str(ffmpeg),
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(source),
        "-t",
        f"{duration:.3f}",
        "-an",
        "-vf",
        ",".join(filters),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(cmd)


def write_concat_file(path, segment_paths):
    lines = []
    for p in segment_paths:
        safe = str(p.resolve()).replace("'", "'\\''")
        lines.append(f"file '{safe}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Random street-shot B-roll editor for narration videos.")
    parser.add_argument("--videos", required=True, type=Path)
    parser.add_argument("--opening-videos", type=Path, help="Optional first-segment-only source folder.")
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--timed-json", type=Path)
    parser.add_argument("--cut-mode", choices=["silence", "sentence-silence", "timed-sentence-silence"], default="timed-sentence-silence")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--min-cut", type=float, default=5.0)
    parser.add_argument("--max-cut", type=float, default=10.0)
    parser.add_argument("--min-source-duration", type=float, default=8.0)
    parser.add_argument("--min-source-bitrate", type=float, default=5_000_000)
    parser.add_argument("--fade-duration", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260623)
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()

    ffmpeg = resolve_tool(args.ffmpeg, "ffmpeg")
    ffprobe = resolve_tool(args.ffprobe, "ffprobe")
    audio = first_file(args.audio, AUDIO_EXTS)
    script_path = first_file(args.script, SCRIPT_EXTS)
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir = args.work_dir or output.with_suffix(".work")
    segments_dir = work_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    script_text = read_script(script_path)
    sentences = split_sentences(script_text)
    audio_duration = probe_duration(ffprobe, audio)
    silence_points = detect_silence_points(ffmpeg, audio)

    alignment_stats = None
    if args.cut_mode == "timed-sentence-silence" and args.timed_json:
        words = load_timed_words(args.timed_json)
        sentence_points, alignment_stats = timed_sentence_ends(sentences, words)
        if not sentence_points:
            sentence_points = proportional_sentence_ends(sentences, audio_duration)
    elif args.cut_mode == "sentence-silence":
        sentence_points = proportional_sentence_ends(sentences, audio_duration)
    else:
        sentence_points = []

    cut_points = choose_cut_points(audio_duration, sentence_points, silence_points, args.min_cut, args.max_cut)
    boundaries = [0.0] + cut_points + [audio_duration + 0.25]
    durations = [max(0.1, boundaries[i + 1] - boundaries[i]) for i in range(len(boundaries) - 1)]

    videos = list_videos(args.videos, ffprobe, args.min_source_duration, args.min_source_bitrate)
    opening_video_dir = args.opening_videos or default_opening_video_dir(args.videos)
    opening_videos = None
    if opening_video_dir:
        opening_videos = list_videos(opening_video_dir, ffprobe, args.min_source_duration, args.min_source_bitrate)
    rng = random.Random(args.seed)
    segment_paths = []
    last_source = None
    manifest = {
        "audio": str(audio),
        "script": str(script_path),
        "output": str(output),
        "fps": args.fps,
        "size": f"{args.width}x{args.height}",
        "audio_duration": audio_duration,
        "sentence_count": len(sentences),
        "segment_count": len(durations),
        "cut_mode": args.cut_mode,
        "cut_points": cut_points,
        "detected_silence_points": silence_points,
        "estimated_sentence_end_points": sentence_points,
        "alignment_stats": alignment_stats,
        "opening_video_dir": str(opening_video_dir) if opening_video_dir else None,
        "segments": [],
    }

    for index, duration in enumerate(durations, start=1):
        source_pool = opening_videos if index == 1 and opening_videos else videos
        pool = [v for v in source_pool if v["path"] != last_source] or source_pool
        item = rng.choice(pool)
        source = item["path"]
        last_source = source
        max_start = max(0.0, item["duration"] - min(duration, item["duration"]))
        start = rng.uniform(0, max_start) if max_start > 0.5 else 0.0
        seg_path = segments_dir / f"segment_{index:04d}.mp4"
        print(f"[{index}/{len(durations)}] {source.name} -> {duration:.2f}s", flush=True)
        render_segment(ffmpeg, source, seg_path, duration, start, args.width, args.height, args.fps, args.fade_duration)
        segment_paths.append(seg_path)
        manifest["segments"].append(
            {
                "index": index,
                "source": str(source),
                "opening_segment": bool(index == 1 and opening_videos),
                "duration": duration,
                "source_start": start,
                "source_duration": item["duration"],
                "source_bitrate": item["bitrate"],
            }
        )

    concat_file = work_dir / "concat.txt"
    write_concat_file(concat_file, segment_paths)
    silent_video = work_dir / "silent_video.mp4"
    run([str(ffmpeg), "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(silent_video)])
    run(
        [
            str(ffmpeg),
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )

    actual_duration = probe_duration(ffprobe, output)
    manifest["output_duration"] = actual_duration
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "manifest": str(manifest_path),
                "audio_duration": audio_duration,
                "output_duration": actual_duration,
                "segments": len(segment_paths),
                "alignment_stats": alignment_stats,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"Command failed: {exc}", file=sys.stderr)
        raise
