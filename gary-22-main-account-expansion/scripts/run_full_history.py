#!/usr/bin/env python3
"""Run 2.2 through the existing Gemini transport, without history compaction."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

RUNNER = Path('/Users/kin/Documents/Codex/2026-07-02/gemini/scripts/run_gemini_chat.py')
BASELINE = Path('/Users/kin/Documents/Codex/2026-07-02/gemini/work/4.0_legacy_baseline/session.json')
BASELINE_SHA256 = '30c4109b440815e5c1c668d188ae72723f9eef99ac4fee5e49ae5377e8fbfb3c'


def configure(base, audit):
    """Keep the shared runner unchanged; patch only this process's adapter."""
    audit = Path(audit)
    if audit.exists() and any(audit.iterdir()):
        raise SystemExit('Audit directory is not empty; choose a new directory per request.')
    audit.mkdir(parents=True, exist_ok=True)
    metadata = {'compaction': False, 'state': 'configured_not_sent'}

    def save_metadata():
        (audit / 'response_metadata.json').write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def strict_load():
        if hashlib.sha256(BASELINE.read_bytes()).hexdigest() != BASELINE_SHA256:
            raise SystemExit('Legacy baseline hash mismatch; request not sent.')
        anchors = json.loads(BASELINE.read_text(encoding='utf-8'))['messages']
        path = base.CURRENT_SESSION_FILE
        try:
            messages = json.loads(path.read_text(encoding='utf-8'))['messages']
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise SystemExit('Missing or invalid copied session; request not sent.') from exc
        if not isinstance(messages, list) or messages[:len(anchors)] != anchors:
            raise SystemExit('Session does not retain the full fixed legacy history; request not sent.')
        if messages[0].get('content') != base.SYSTEM_PROMPT:
            raise SystemExit('Runner system prompt differs from legacy session; request not sent.')
        return messages

    class AuditedJson:
        def __getattr__(self, name):
            return getattr(json, name)

        def loads(self, value, *args, **kwargs):
            data = json.loads(value, *args, **kwargs)
            if isinstance(data, dict) and 'choices' in data:
                choices = data.get('choices') or []
                if data.get('id') is not None:
                    metadata['response_id'] = data['id']
                if data.get('model') is not None:
                    metadata['response_model'] = data['model']
                if data.get('usage') is not None:
                    metadata['usage'] = data['usage']
                if choices and choices[0].get('finish_reason') is not None:
                    metadata['finish_reason'] = choices[0]['finish_reason']
                save_metadata()
            return data

    original_chat = base.chat_completion

    def audited_chat(messages):
        payload = {
            'model': os.environ.get('TEAMO_MODEL', 'gemini-3.1-pro-preview'),
            'messages': messages,
            'temperature': float(os.environ.get('TEAMO_TEMPERATURE', '0.8')),
            'max_tokens': int(os.environ.get('TEAMO_MAX_TOKENS', '24000')),
        }
        request_file = audit / 'request.json'
        request_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        request_file.chmod(0o600)
        metadata.update(state='request_prepared', request_model=payload['model'],
                        max_tokens=payload['max_tokens'], message_count=len(messages))
        save_metadata()
        try:
            result = original_chat(messages)
        except BaseException:
            metadata['state'] = 'request_failed'
            save_metadata()
            raise
        metadata['state'] = 'response_received'
        save_metadata()
        return result

    base.load_messages = strict_load
    base.compact_messages = lambda messages: messages
    base.chat_completion = audited_chat
    base.json = AuditedJson()
    return base


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--audit-dir', type=Path)
    args, remaining = parser.parse_known_args()
    if any(x in remaining for x in ('--isolated', '--new-session')):
        parser.error('2.2 requires a copied legacy session; resets and isolation are forbidden.')
    if '--help' not in remaining:
        if not args.audit_dir or '--session-file' not in remaining or '--output-file' not in remaining:
            parser.error('Use --audit-dir, --session-file and --output-file for each 2.2 request.')
        output_index = remaining.index('--output-file') + 1
        if output_index < len(remaining) and Path(remaining[output_index]).exists():
            parser.error('Output exists; do not overwrite an earlier raw response.')
    if not RUNNER.exists():
        parser.error('Local Gemini runner is missing; do not switch to an empty session or another host.')
    spec = importlib.util.spec_from_file_location('gary22_shared_gemini_runner', RUNNER)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    if '--help' not in remaining:
        configure(base, args.audit_dir)
    sys.argv = [str(RUNNER)] + remaining
    return base.main()


if __name__ == '__main__':
    raise SystemExit(main())
