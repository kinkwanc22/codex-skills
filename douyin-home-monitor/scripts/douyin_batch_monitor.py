import argparse
import base64
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from html import escape
from pathlib import Path


DEFAULT_SERVICE_DIR = Path("E:/\u975e\u4e28\u94fe\u63a5\u63d0\u53d6\u6587\u6848\uff08\u6296+bilibili\uff09/\u975e\u4e28\u94fe\u63a5\u63d0\u53d6\u6587\u6848\uff08\u6296+bilibili\uff09")
DEFAULT_EDGE_EXE = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")


class MonitorError(RuntimeError):
    pass


def http_json(url, method="GET", payload=None, timeout=10):
    data = None
    headers = {"User-Agent": "douyin-home-monitor/1.0"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_text(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "douyin-home-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_state(path):
    if not path.exists():
        return {"homes": {}, "runs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_filename(text, fallback):
    text = re.sub(r'[\\/:*?"<>|\r\n]+', "_", text or "").strip(" ._")
    return (text[:80] or fallback)


def canonical_home_key(url, page_href=None):
    value = page_href or url
    sec = re.search(r"/user/([^/?#]+)", value)
    if sec:
        return "user:" + urllib.parse.unquote(sec.group(1))
    return "url:" + value.rstrip("/")


def ensure_service(service_dir, timeout=30):
    try:
        http_text("http://127.0.0.1:8080/", timeout=2)
        return {"running": True, "started": False}
    except Exception:
        pass
    exe = service_dir / "\u975e\u4e28\u94fe\u63a5\u63d0\u53d6\u6587\u6848.exe"
    if not exe.exists():
        raise MonitorError(f"8080 service is not running and extractor exe was not found: {exe}")
    subprocess.Popen(
        [str(exe)],
        cwd=str(service_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            http_text("http://127.0.0.1:8080/", timeout=2)
            return {"running": True, "started": True}
        except Exception:
            time.sleep(2)
    raise MonitorError("Extractor service did not become reachable at http://127.0.0.1:8080/")


class WebSocket:
    def __init__(self, url):
        parsed = urllib.parse.urlparse(url)
        self.host = parsed.hostname
        self.port = parsed.port or 80
        self.path = parsed.path + (("?" + parsed.query) if parsed.query else "")
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = self.sock.recv(4096)
        if b" 101 " not in response:
            raise MonitorError("Could not connect to Edge remote debugging websocket")

    def send_text(self, text):
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        mask = os.urandom(4)
        header.extend(mask)
        masked = bytes(payload[i] ^ mask[i % 4] for i in range(length))
        self.sock.sendall(bytes(header) + masked)

    def recv_text(self):
        while True:
            first = self.sock.recv(2)
            if len(first) < 2:
                raise MonitorError("Edge remote debugging connection closed")
            opcode = first[0] & 0x0F
            length = first[1] & 0x7F
            masked = first[1] & 0x80
            if length == 126:
                length = struct.unpack("!H", self.sock.recv(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self.sock.recv(8))[0]
            mask = self.sock.recv(4) if masked else b""
            payload = b""
            while len(payload) < length:
                payload += self.sock.recv(length - len(payload))
            if masked:
                payload = bytes(payload[i] ^ mask[i % 4] for i in range(length))
            if opcode == 1:
                return payload.decode("utf-8", errors="replace")
            if opcode == 8:
                raise MonitorError("Edge remote debugging websocket closed")
            if opcode == 9:
                self.sock.sendall(bytes([0x8A, len(payload)]) + payload)

    def close(self):
        self.sock.close()


class CDPClient:
    def __init__(self, ws_url):
        self.ws = WebSocket(ws_url)
        self.next_id = 0

    def call(self, method, params=None, timeout=25):
        self.next_id += 1
        msg_id = self.next_id
        self.ws.send_text(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = json.loads(self.ws.recv_text())
            if message.get("id") == msg_id:
                if "error" in message:
                    raise MonitorError(f"CDP call failed {method}: {message['error']}")
                return message.get("result", {})
        raise MonitorError(f"CDP call timed out: {method}")

    def close(self):
        self.ws.close()


def ensure_edge(cdp_port, edge_exe):
    try:
        return http_json(f"http://127.0.0.1:{cdp_port}/json/version", timeout=2)
    except Exception:
        pass
    if not edge_exe.exists():
        raise MonitorError(f"Edge remote debugging is unavailable and Edge was not found: {edge_exe}")
    user_data = Path(os.environ.get("DOUYIN_EDGE_USER_DATA_DIR", Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Edge" / "User Data"))
    subprocess.Popen(
        [
            str(edge_exe),
            f"--remote-debugging-port={cdp_port}",
            f"--user-data-dir={user_data}",
            "--profile-directory=Default",
            "--no-first-run",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            return http_json(f"http://127.0.0.1:{cdp_port}/json/version", timeout=2)
        except Exception:
            time.sleep(1)
    raise MonitorError("Edge remote debugging is unavailable. Close ordinary Edge windows, start Edge with --remote-debugging-port=9222, then rerun.")


def new_cdp_tab(cdp_port, url):
    new_url = f"http://127.0.0.1:{cdp_port}/json/new?{urllib.parse.quote(url, safe='')}"
    try:
        target = http_json(new_url, timeout=5)
    except Exception as exc:
        if "405" not in str(exc):
            raise
        target = http_json(new_url, method="PUT", timeout=5)
    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        raise MonitorError("Edge did not return a debuggable tab")
    return CDPClient(ws_url)


def extract_home_links(home_url, cdp_port, wait_seconds):
    client = new_cdp_tab(cdp_port, home_url)
    try:
        client.call("Page.enable")
        client.call("Runtime.enable")
        client.call("Page.navigate", {"url": home_url})
        time.sleep(wait_seconds)
        expression = r"""
(() => {
  const anchors = Array.from(document.querySelectorAll('a[href*="/video/"]'))
    .filter(a => {
      const rect = a.getBoundingClientRect();
      const style = getComputedStyle(a);
      return rect.width > 40 && rect.height > 40 && style.visibility !== 'hidden' && style.display !== 'none';
    })
    .map(a => ({
      href: a.href,
      text: (a.textContent || '').trim().slice(0, 180),
      pinned: (a.textContent || '').includes('置顶'),
      top: Math.round(a.getBoundingClientRect().top)
    }))
    .sort((a, b) => a.top - b.top);
  const seen = new Set();
  const items = [];
  function add(rawUrl, text) {
    const m = String(rawUrl || '').match(/douyin\.com\/video\/(\d{10,30})/);
    if (!m || seen.has(m[1])) return;
    seen.add(m[1]);
    const anchor = anchors.find(a => String(a.href || '').includes(m[1]));
    items.push({ aweme_id: m[1], url: `https://www.douyin.com/video/${m[1]}`, text: text || '', pinned: !!(anchor && anchor.pinned) });
  }
  anchors.forEach(a => add(a.href, a.text));
  return { href: location.href, title: document.title, bodyText: document.body.innerText.slice(0, 1200), items };
})()
"""
        result = client.call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True}, timeout=25)
        value = result.get("result", {}).get("value")
        if not value:
            raise MonitorError("Homepage opened, but page content could not be read")
        if not value.get("items"):
            body = value.get("bodyText", "")
            if any(word in body for word in ["登录", "验证码", "验证"]):
                raise MonitorError("Douyin page appears to require login or verification")
            raise MonitorError(f"No standard video links found on rendered homepage; title={value.get('title')}")
        return value
    finally:
        try:
            client.call("Page.close", timeout=3)
        except Exception:
            pass
        client.close()


def extract_video(video_url):
    return http_json(
        "http://127.0.0.1:8080/api/extract_douyin_text",
        method="POST",
        payload={"url": video_url},
        timeout=600,
    )


def make_docx(path, video_url, result):
    info = result.get("video_info") or {}
    paragraphs = [
        info.get("title") or video_url,
        f"作品链接：{video_url}",
        f"作者：{info.get('uploader', '')}",
        f"平台：{result.get('platform', '')}",
        f"提取时间：{result.get('timestamp', datetime.now().isoformat())}",
        "",
        "文案",
        result.get("transcript_text") or "",
        "",
        "SRT",
        result.get("transcript_srt") or "",
    ]
    body = "".join(f'<w:p><w:r><w:t xml:space="preserve">{escape(line)}</w:t></w:r></w:p>' for para in paragraphs for line in str(para).splitlines())
    document_xml = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>'
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)


def read_home_urls(args):
    candidates = list(args.urls or [])
    if args.home_file:
        candidates.extend(line.strip() for line in Path(args.home_file).read_text(encoding="utf-8").splitlines())
    urls = []
    for candidate in candidates:
        candidate = candidate.strip().lstrip("\ufeff")
        if not candidate or candidate.lstrip().startswith("#"):
            continue
        found = re.findall(r"https?://[^\s，。；;）)]+", candidate)
        urls.extend(found or [candidate.strip()])
    if not urls:
        raise MonitorError("No Douyin homepage URLs were provided")
    return list(dict.fromkeys(urls))


def run(args):
    service_dir = Path(args.service_dir or os.environ.get("DOUYIN_EXTRACTOR_DIR") or DEFAULT_SERVICE_DIR)
    state_path = Path(args.state).resolve()
    output_dir = Path(args.outputs).resolve()
    home_urls = read_home_urls(args)
    state = load_state(state_path)
    ensure_edge(args.cdp_port, Path(args.edge_exe))
    now = datetime.now().isoformat(timespec="seconds")
    summary = {"status": "ok", "processed": [], "baselines": [], "blocked": [], "state_path": str(state_path)}

    for home_url in home_urls:
        try:
            page = extract_home_links(home_url, args.cdp_port, args.wait_seconds)
            home_key = canonical_home_key(home_url, page.get("href"))
            home_state = state.setdefault("homes", {}).setdefault(home_key, {"source_url": home_url, "seen_aweme_ids": [], "items": {}})
            seen = set(home_state.get("seen_aweme_ids", []))
            first_home_run = not seen
            visible_items = page["items"]
            if first_home_run and not args.process_current:
                for item in visible_items:
                    home_state["items"][item["aweme_id"]] = {**item, "first_seen_at": now, "processed": False}
                home_state["seen_aweme_ids"] = list(dict.fromkeys([*home_state.get("seen_aweme_ids", []), *[i["aweme_id"] for i in visible_items]]))
                summary["baselines"].append({"home": home_url, "resolved": page.get("href"), "count": len(visible_items)})
                continue
            new_items = []
            for item in visible_items:
                if item.get("pinned"):
                    continue
                if item["aweme_id"] in seen:
                    if new_items:
                        break
                    continue
                new_items.append(item)
            all_new_ids = {item["aweme_id"] for item in new_items}
            if args.max_new_per_home:
                new_items = new_items[: args.max_new_per_home]
            processed_ids = set()
            if new_items:
                ensure_service(service_dir)
            for item in new_items:
                result = extract_video(item["url"])
                if not result.get("success"):
                    raise MonitorError(f"Extraction failed for {item['url']}: {result.get('error') or result}")
                info = result.get("video_info") or {}
                title = info.get("title") or item.get("text") or item["aweme_id"]
                docx_path = output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{item['aweme_id']}_{safe_filename(title, item['aweme_id'])}.docx"
                make_docx(docx_path, item["url"], result)
                record = {
                    **item,
                    "first_seen_at": now,
                    "processed": True,
                    "processed_at": datetime.now().isoformat(timespec="seconds"),
                    "docx_path": str(docx_path),
                    "title": title,
                    "extract_result": {
                        "success": result.get("success"),
                        "platform": result.get("platform"),
                        "timestamp": result.get("timestamp"),
                        "video_info": info,
                        "transcript_text_chars": len(result.get("transcript_text") or ""),
                        "transcript_srt_chars": len(result.get("transcript_srt") or ""),
                    },
                }
                home_state["items"][item["aweme_id"]] = record
                processed_ids.add(item["aweme_id"])
                summary["processed"].append({"home": home_url, "resolved_home": page.get("href"), "url": item["url"], "docx_path": str(docx_path), "result": record["extract_result"]})
            if args.max_new_per_home and len(processed_ids) < len(all_new_ids):
                ids_to_mark = processed_ids
            else:
                ids_to_mark = {i["aweme_id"] for i in visible_items}
            home_state["seen_aweme_ids"] = list(dict.fromkeys([*home_state.get("seen_aweme_ids", []), *ids_to_mark]))
            if not new_items:
                summary.setdefault("no_new", []).append({"home": home_url, "resolved": page.get("href"), "visible_count": len(visible_items)})
        except Exception as exc:
            summary["blocked"].append({"home": home_url, "reason": str(exc)})

    state.setdefault("runs", []).append({"time": now, "processed_count": len(summary["processed"]), "baseline_count": len(summary["baselines"]), "blocked_count": len(summary["blocked"])})
    save_state(state_path, state)
    if summary["blocked"] and not summary["processed"] and not summary["baselines"]:
        summary["status"] = "blocked"
    elif summary["blocked"]:
        summary["status"] = "partial"
    elif summary["processed"]:
        summary["status"] = "processed"
    elif summary["baselines"]:
        summary["status"] = "baseline_initialized"
    else:
        summary["status"] = "no_new"
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--home-file")
    parser.add_argument("--state", default=str(Path.cwd() / "work" / "douyin_monitor_state.json"))
    parser.add_argument("--outputs", default=str(Path.cwd() / "outputs"))
    parser.add_argument("--process-current", action="store_true")
    parser.add_argument("--max-new-per-home", type=int, default=0)
    parser.add_argument("--wait-seconds", type=int, default=7)
    parser.add_argument("--service-dir")
    parser.add_argument("--cdp-port", type=int, default=int(os.environ.get("DOUYIN_CDP_PORT", "9222")))
    parser.add_argument("--edge-exe", default=str(DEFAULT_EDGE_EXE))
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
