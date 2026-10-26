#!/usr/bin/env python3
"""Extract a semantic opening from the locked full PCM WAV, with provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import wave


def us(timestamp):
    h, m, rest = timestamp.replace('.', ',').split(':')
    s, ms = rest.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1_000_000 + int(ms.ljust(3, '0')) * 1000


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--audio', required=True, type=Path)
    ap.add_argument('--srt', required=True, type=Path)
    ap.add_argument('--marker', default='今天我们要聊的是')
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--manifest', required=True, type=Path)
    a = ap.parse_args()
    for out in [a.out, a.manifest]:
        if out.exists():
            ap.error(f'Refusing to overwrite existing output: {out}')
    normalize = lambda t: re.sub(r'[\W_]', '', t)
    matches = []
    for block in re.split(r'\r?\n\s*\r?\n', a.srt.read_text(encoding='utf-8-sig').strip()):
        lines = block.splitlines()
        if len(lines) >= 3 and normalize(''.join(lines[2:])) == normalize(a.marker):
            left, right = lines[1].split(' --> ')
            matches.append((us(left), us(right)))
    if len(matches) != 1:
        ap.error(f'Expected one unambiguous marker, found {len(matches)}')
    end_us = matches[0][1]
    if end_us <= 0:
        ap.error('Opening end must be positive')
    with wave.open(str(a.audio), 'rb') as source:
        if source.getcomptype() != 'NONE':
            ap.error('Input must be an uncompressed PCM WAV')
        rate = source.getframerate()
        frames = (end_us * rate + 500_000) // 1_000_000
        if frames > source.getnframes():
            ap.error('Opening end exceeds full audio duration')
        params = source.getparams()
        pcm = source.readframes(frames)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(a.out), 'wb') as dst:
        dst.setparams(params)
        dst.writeframes(pcm)
    with wave.open(str(a.out), 'rb') as check:
        assert check.getnframes() == frames
        assert check.readframes(frames) == pcm
    manifest = {
        'full_audio': str(a.audio.resolve()),
        'full_audio_sha256': hashlib.sha256(a.audio.read_bytes()).hexdigest(),
        'subtitle': str(a.srt.resolve()),
        'subtitle_sha256': hashlib.sha256(a.srt.read_bytes()).hexdigest(),
        'marker': a.marker,
        'start_us': 0,
        'semantic_end_us': end_us,
        'sample_rate': rate,
        'channels': params.nchannels,
        'sample_width': params.sampwidth,
        'sample_frames': frames,
        'actual_duration_seconds': frames / rate,
        'output': str(a.out.resolve()),
        'output_sha256': hashlib.sha256(a.out.read_bytes()).hexdigest(),
        'pcm_matches_full_audio_prefix': True,
    }
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
