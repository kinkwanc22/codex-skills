---
name: douyin-home-monitor
description: Monitor one or many Douyin creator home pages for new works by opening logged-in rendered web pages and extracting standard card links such as Douyin video URLs with aweme IDs. Use when the user asks to monitor Douyin home/profile links, batch watch creators, avoid duplicate processing, extract new Douyin video text/SRT, or generate Word .docx files from new Douyin works via the local 8080 extractor service.
---

# Douyin Home Monitor

## Required Preflight

Before running the monitor, confirm Edge remote debugging is available at `http://127.0.0.1:9222/json/version`.

Use this check:

```powershell
try { Invoke-RestMethod http://127.0.0.1:9222/json/version -TimeoutSec 2 } catch { "Edge remote debugging is not available" }
```

If it is unavailable, close ordinary Edge windows and start Edge with remote debugging:

```powershell
& 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' --remote-debugging-port=9222 --user-data-dir="$env:LOCALAPPDATA\Microsoft\Edge\User Data" --profile-directory=Default
```

Then open or log in to Douyin in that Edge profile if needed, and rerun the monitor. This preflight is mandatory because the script reads rendered logged-in homepage cards; it does not use Douyin's blocked background works-list API.

To reduce disruption, keep this Edge window minimized after login. The monitor script should close the temporary tabs it opens after each homepage check.

## Logged-In Account Check

Before processing new works, try to identify the visible logged-in Douyin account from the rendered page, such as the nickname shown in the left navigation/user panel. Report the visible account nickname when available.

If the user has provided an expected logged-in account nickname, compare it before extraction:

- If it matches, continue.
- If it does not match or the account cannot be confirmed, stop before extraction and notify the user.
- Do not read or expose private credentials, cookies, phone numbers, passwords, or tokens. Only use visible page text such as the public nickname shown by Douyin.

For this user's current browser session, the visible logged-in nickname observed previously was `Kin`. Treat this only as a sanity-check hint, not as a credential.

## Run

Use the bundled script for deterministic batch monitoring:

```powershell
& '<extractor-python>' '<skill-dir>\scripts\douyin_batch_monitor.py' --home-file '<links.txt>' --state '<state.json>' --outputs '<output-dir>'
```

Prefer the Python runtime bundled with the local extractor app. If `DOUYIN_EXTRACTOR_DIR` is set:

```powershell
$extractorPython = Join-Path $env:DOUYIN_EXTRACTOR_DIR 'feige\python.exe'
```

If `DOUYIN_EXTRACTOR_DIR` is not set, locate the extractor app directory first or ask the user for the path. The script can start/check the app's `http://127.0.0.1:8080` service if `DOUYIN_EXTRACTOR_DIR` is set or the default local path exists.

## Workflow

1. Run the `Required Preflight` check. Start Edge with remote debugging if needed.
2. Put the user's Douyin homepage/profile links into a UTF-8 text file, one URL per line. Short links such as `https://v.douyin.com/.../` are allowed.
3. Run `scripts/douyin_batch_monitor.py` with:
   - `--home-file`: file containing homepage links, or pass links as positional args.
   - `--state`: persistent JSON state file. Default to the current workspace `work/douyin_monitor_state.json`.
   - `--outputs`: docx output directory. Default to the current workspace `outputs`.
4. On a first run for each home, initialize that home's baseline by default and do not process all old visible works.
5. On later runs, process only unseen `aweme_id`s per homepage.
6. When new works are processed, report each work URL, Word path, title/uploader/duration, transcript length, and SRT length.
7. If login is invalid, the account cannot be confirmed when required, the page cannot load, Edge debugging is unavailable, or no latest works can be confirmed, follow `Login Or Verification Problems` and tell the user the exact blocking reason.

## Browser Requirement

The script reads the rendered Douyin homepage through Edge remote debugging on `127.0.0.1:9222`. It intentionally does not use Douyin's blocked background works-list API.

If the script reports that Edge remote debugging is unavailable, follow `Required Preflight` and rerun the monitor.

## Login Or Verification Problems

If the rendered homepage shows login prompts, QR login, SMS verification, slider/captcha, security verification, or no visible works because the session is invalid:

1. Do not retry Douyin's background works-list API.
2. Do not mark any new works as seen or processed for that blocked homepage.
3. Preserve the existing state file unchanged except for a run/block log if the script records one.
4. Tell the user that manual browser login or verification is required.
5. Ask the user to use the Edge window started by `Required Preflight`, open `https://www.douyin.com/`, complete login/verification, then open one target homepage and confirm works cards are visible.
6. After the user confirms login is restored, rerun the monitor with the same state file and outputs directory.

Common blocker messages and meanings:

- `Edge remote debugging is unavailable`: Edge was not started with `--remote-debugging-port=9222`, or ordinary Edge is already occupying the profile.
- `requires login or verification`: the rendered page is reachable but Douyin is asking for login, QR scan, captcha, slider, SMS, or security verification.
- `No standard video links found`: the page loaded but no `douyin.com/video/...` card links were visible; possible causes include incomplete rendering, private/empty homepage, blocked content, or a tab that is not logged in.

When reporting a login blocker, include:

- the affected homepage URL,
- the blocker message,
- the Edge remote debugging preflight command,
- the instruction to log in manually in that Edge profile,
- confirmation that no extraction or duplicate-state update was performed for that homepage.

## Useful Options

- `--process-current`: process currently visible works even when there is no prior state.
- `--max-new-per-home N`: cap new works processed per home per run.
- `--wait-seconds N`: wait longer for slow Douyin homepage rendering.
- `--service-dir PATH`: override extractor app directory.
- `--cdp-port PORT`: override Edge remote debugging port.
