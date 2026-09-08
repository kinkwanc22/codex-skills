#!/usr/bin/env python3
"""Local Gemini/TeamRouter runner for prompt-file based workflows.

By default the runner preserves the workflow chat in a session JSON file under
work/. Male expansion prompts are separated by direction so the old 2.5 Gary
voice and the 2.8 safe voice do not contaminate each other.
Use --isolated for temporary clean-context tests or unrelated copy.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION_FILE = ROOT / "work" / "gemini_session.json"
SESSION_ALIASES = {
    "default": DEFAULT_SESSION_FILE,
    "2.5": ROOT / "work" / "gemini_session_25_legacy.json",
    "25": ROOT / "work" / "gemini_session_25_legacy.json",
    "2.5-transplant": ROOT / "work" / "gemini_session_25_transplant_legacy.json",
    "25-transplant": ROOT / "work" / "gemini_session_25_transplant_legacy.json",
    "transplant25": ROOT / "work" / "gemini_session_25_transplant_legacy.json",
    "2.8": ROOT / "work" / "gemini_session_28_safe.json",
    "28": ROOT / "work" / "gemini_session_28_safe.json",
    "2.9": ROOT / "work" / "gemini_session_29_fusion.json",
    "29": ROOT / "work" / "gemini_session_29_fusion.json",
}
SYSTEM_PROMPT = (
    "你是一个中文对话助手。你可以陪用户聊天、学习、解释概念、整理思路、写作、"
    "改稿、翻译和答疑。回答要清楚、自然、实用；如果用户要创作或改写文案，"
    "就按用户当次要求处理；如果用户只是聊天或学习，就正常对话，不要默认扩写。"
)
CURRENT_SESSION_FILE = DEFAULT_SESSION_FILE


def curl_chat_completion(url: str, api_key: str, payload: dict) -> str:
    """Use macOS curl when Python's older LibreSSL transport drops TLS.

    The API key is provided over stdin instead of the command line, so it is
    not exposed in the process list. The prompt body is stored only in a
    mode-0600 temporary file and is removed when the request finishes.
    """
    payload_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="gemini-payload-", suffix=".json", delete=False) as handle:
            payload_path = Path(handle.name)
            handle.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        payload_path.chmod(0o600)

        marker = "__CODEX_HTTP_STATUS__="
        command = [
            "/usr/bin/curl",
            "--http1.1",
            "--silent",
            "--show-error",
            "--connect-timeout",
            "30",
            "--max-time",
            "600",
            "--header",
            "@-",
            "--data-binary",
            f"@{payload_path}",
            "--write-out",
            f"\n{marker}%{{http_code}}",
            url,
        ]
        headers = (
            f"Authorization: Bearer {api_key}\n"
            "Content-Type: application/json\n"
        ).encode("utf-8")
        result = subprocess.run(
            command,
            input=headers,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=620,
            check=False,
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        marker_pos = stdout.rfind("\n" + marker)
        if marker_pos < 0:
            detail = stderr or stdout[-1000:] or f"curl exit {result.returncode}"
            raise RuntimeError(detail)
        body = stdout[:marker_pos]
        status_text = stdout[marker_pos + len(marker) + 1 :].strip()
        status = int(status_text)
        if result.returncode != 0:
            raise RuntimeError(stderr or f"curl exit {result.returncode}")
        if status >= 400:
            raise RuntimeError(f"HTTP {status}: {body[:2000]}")
        return body
    finally:
        if payload_path is not None:
            payload_path.unlink(missing_ok=True)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def chat_completion(messages: list[dict[str, str]]) -> str:
    api_key = os.environ.get("TEAMO_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing TEAMO_API_KEY. Export it in your shell or add it to .env.local."
        )

    base_url = os.environ.get("TEAMO_BASE_URL", "https://api.teamorouter.com/v1")
    url = os.environ.get(
        "TEAMO_CHAT_COMPLETIONS_URL", base_url.rstrip("/") + "/chat/completions"
    )
    model = os.environ.get("TEAMO_MODEL", "gemini-3.1-pro-preview")
    temperature = float(os.environ.get("TEAMO_TEMPERATURE", "0.8"))
    max_tokens = int(os.environ.get("TEAMO_MAX_TOKENS", "24000"))

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    body = ""
    last_network_error = None
    for attempt in range(3):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                body = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if attempt < 2 and (exc.code == 429 or exc.code >= 500):
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {exc.code} from Gemini runner:\n{detail}") from exc
        except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected) as exc:
            last_network_error = exc
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue

    if not body and last_network_error is not None:
        print(
            "Python TLS transport was interrupted; retrying locally with macOS curl.",
            file=sys.stderr,
        )
        for attempt in range(3):
            try:
                body = curl_chat_completion(url, api_key, payload)
                break
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                last_network_error = exc
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
                    continue
        if not body:
            raise SystemExit(
                "Network error from Gemini runner after local TLS fallback: "
                f"{last_network_error}"
            ) from last_network_error

    if body.lstrip().startswith("data:"):
        return parse_stream_response(body)

    data = json.loads(body)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(
            "Unexpected response shape from Gemini runner:\n"
            + json.dumps(data, ensure_ascii=False, indent=2)
        ) from exc


def new_messages() -> list[dict[str, str]]:
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def choose_session_file(args: argparse.Namespace, prompt: str = "") -> Path:
    if args.session_file:
        return Path(args.session_file)
    if args.session:
        return SESSION_ALIASES.get(args.session, ROOT / "work" / f"gemini_session_{args.session}.json")
    if "旧2.5成稿换芯" in prompt or "2.5成稿换芯" in prompt or "成稿换芯" in prompt:
        return SESSION_ALIASES["2.5-transplant"]
    if "【正式扩写任务：2.8安全版" in prompt or "2.8安全版" in prompt:
        return SESSION_ALIASES["2.8"]
    if "【正式扩写任务：Gary 2.9融合版" in prompt or "2.9融合版" in prompt:
        return SESSION_ALIASES["2.9"]
    if "【正式扩写任务：满血扩写2.5模型" in prompt or "满血扩写2.5模型" in prompt:
        return SESSION_ALIASES["2.5"]
    return DEFAULT_SESSION_FILE


def load_messages() -> list[dict[str, str]]:
    if not CURRENT_SESSION_FILE.exists():
        return new_messages()
    try:
        data = json.loads(CURRENT_SESSION_FILE.read_text(encoding="utf-8"))
        messages = data.get("messages")
    except (OSError, json.JSONDecodeError):
        return new_messages()
    if not isinstance(messages, list) or not messages:
        return new_messages()
    if messages[0].get("role") != "system" or messages[0].get("content") != SYSTEM_PROMPT:
        return new_messages()
    return messages


def save_messages(messages: list[dict[str, str]]) -> None:
    CURRENT_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_SESSION_FILE.write_text(
        json.dumps({"messages": messages}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def compact_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep two legacy anchor pairs, recent complete turns, and any pending user.

    This prevents the full multi-megabyte history from being sent on every
    request while retaining the original 2.5 voice examples at the front.
    The newest prompt is often a pending user message when compaction runs, so
    it must be preserved even before an assistant reply exists.
    """
    if len(messages) <= 13:
        return messages
    system = messages[:1]
    anchor = messages[1:5]
    remainder = messages[5:]
    complete_turns: list[list[dict[str, str]]] = []
    pending_user = None
    for message in remainder:
        role = message.get("role")
        if role == "user":
            pending_user = message
        elif role == "assistant" and pending_user is not None:
            complete_turns.append([pending_user, message])
            pending_user = None
    recent = complete_turns[-4:]
    compacted = system + anchor
    for turn in recent:
        compacted.extend(turn)
    if pending_user is not None:
        compacted.append(pending_user)
    return compacted


def parse_stream_response(body: str) -> str:
    content = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        content.append(
            chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            or chunk.get("choices", [{}])[0].get("message", {}).get("content")
            or ""
        )
    return "".join(content)


def build_messages(prompt: str) -> list[dict[str, str]]:
    if CURRENT_ARGS.isolated:
        messages = new_messages()
    else:
        messages = load_messages()
    messages.append({"role": "user", "content": prompt})
    return messages


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("Paste a prompt, then press Ctrl-D:")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a Gemini/TeamRouter chat completion for this workflow."
    )
    parser.add_argument("--prompt-file", help="UTF-8 prompt file to send.")
    parser.add_argument("--prompt", help="Prompt text to send.")
    parser.add_argument(
        "--isolated",
        action="store_true",
        help="Use a temporary clean context and do not read or write any saved session.",
    )
    parser.add_argument(
        "--session",
        choices=[
            "default",
            "2.5",
            "25",
            "2.5-transplant",
            "25-transplant",
            "transplant25",
            "2.8",
            "28",
            "2.9",
            "29",
        ],
        help="Saved session to use. If omitted, male 2.5/2.8/2.9 prompts are auto-routed. Revised 3.2 uses --isolated.",
    )
    parser.add_argument(
        "--session-file",
        help="Explicit JSON session file path. Overrides --session.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional UTF-8 file path for saving the model response.",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print non-secret runtime configuration and exit.",
    )
    parser.add_argument(
        "--new-session",
        action="store_true",
        help="Clear the saved non-isolated session and exit.",
    )
    args = parser.parse_args()
    global CURRENT_ARGS
    CURRENT_ARGS = args

    load_env_file(ROOT / ".env.local")

    prompt = "" if args.print_config or args.new_session else read_prompt(args).strip()
    global CURRENT_SESSION_FILE
    CURRENT_SESSION_FILE = choose_session_file(args, prompt)

    if args.new_session:
        if CURRENT_SESSION_FILE.exists():
            CURRENT_SESSION_FILE.unlink()
        print(f"Session cleared: {CURRENT_SESSION_FILE}")
        return 0

    if args.print_config:
        base_url = os.environ.get("TEAMO_BASE_URL", "https://api.teamorouter.com/v1")
        url = os.environ.get(
            "TEAMO_CHAT_COMPLETIONS_URL", base_url.rstrip("/") + "/chat/completions"
        )
        print("TEAMO_API_KEY:", "set" if os.environ.get("TEAMO_API_KEY") else "missing")
        print("TEAMO_CHAT_COMPLETIONS_URL:", url)
        print("TEAMO_MODEL:", os.environ.get("TEAMO_MODEL", "gemini-3.1-pro-preview"))
        print("TEAMO_MAX_TOKENS:", os.environ.get("TEAMO_MAX_TOKENS", "24000"))
        print("TEAMO_TEMPERATURE:", os.environ.get("TEAMO_TEMPERATURE", "0.8"))
        print("SESSION_FILE:", CURRENT_SESSION_FILE)
        return 0

    if not prompt:
        raise SystemExit("Prompt is empty.")

    messages = build_messages(prompt)
    if not args.isolated:
        messages = compact_messages(messages)
    content = chat_completion(messages)
    if not content.strip():
        raise SystemExit("Empty response from Gemini runner; session was not updated.")
    messages.append({"role": "assistant", "content": content})
    if not args.isolated:
        save_messages(messages)
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
