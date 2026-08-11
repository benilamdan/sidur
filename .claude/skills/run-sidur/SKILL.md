---
name: run-sidur
description: Build, run, and drive the Sidur shift-schedule PWA (sidur_live.html). Use when asked to start sidur, preview the schedule site, test the admin panel, verify a schedule update before publish, or screenshot the app.
---

Sidur is a single-file static HTML PWA (`sidur_live.html`, ~2450 lines,
Hebrew RTL) — a weekly shift schedule for Wolfson textile employees,
served by GitHub Pages. No build step, no npm deps. Drive it with the
Browser pane MCP tools (`mcp__Claude_Browser__*`) against a local
static server — that's the `chromium-cli` equivalent in this
environment.

All paths below are relative to `sidur-repo/` (this skill's parent
repo root).

## Prerequisites

None beyond Python 3 (already on PATH — used for both the local
static server and the publish scripts).

## Run (agent path)

1. Start a static file server in this directory (background):

```bash
cd sidur-repo
python -m http.server 8791 > /tmp/sidur_http.log 2>&1 &
sleep 1
curl -sf http://localhost:8791/sidur_live.html -o /dev/null && echo OK
```

2. Open it in the Browser pane and drive it:

```
mcp__Claude_Browser__preview_start { url: "http://localhost:8791/sidur_live.html" }
mcp__Claude_Browser__read_page { filter: "interactive" }
```

Representative flow — verified this session, worked end to end:

```
# click the admin tab (ref from read_page, label "ניהול 🔒")
mcp__Claude_Browser__computer { action: "left_click", ref: "<admin-tab-ref>" }
mcp__Claude_Browser__read_page { filter: "interactive" }   # → password box + "כניסה" button appear

mcp__Claude_Browser__form_input { ref: "<password-ref>", value: "1221" }
mcp__Claude_Browser__computer { action: "left_click", ref: "<login-btn-ref>" }
mcp__Claude_Browser__read_page { filter: "interactive" }
# → admin panel confirmed: "🌐 שמור לכולם" (publish), "התנתק" (logout),
#   "💾 הורד HTML" (download) buttons present
```

Admin password is the hardcoded `ADMIN_PASSWORD` constant in the HTML
(`sidur_live.html:698`, currently `"1221"`).

Stop the server when done: kill the `http.server` process (find with
`netstat -ano | grep 8791` on Windows, or track the bash job).

## Direct invocation — testing a schedule update without pushing

The real weekly flow (`auto_publish.py`) rewrites the `scheduleData`
block in `sidur_live.html` from `schedules/YYYY-MM-DD.json` (next
Sunday's date) and bumps `version.json`. To test it without touching
the real repo, run it against a throwaway copy:

```bash
cp -r sidur-repo /tmp/sidur-test
cd /tmp/sidur-test
python auto_publish.py
```

Verified this session: with no `schedules/<next-sunday>.json` present
it prints `No schedule file: ... — skipping` and exits 0 (safe
no-op). When the file exists it rewrites `scheduleData` in place and
updates `version.json` — diff the copy's `sidur_live.html` against the
original to review before applying for real.

## Test / verify a real update

Real workflow lives in [project_sidur_system memory] — in short:
`python parse_schedule.py <excel> <sunday-date>` (or place the JSON
directly under `schedules/`) → commit → push. GitHub Actions
(`weekly-auto-publish.yml`, Saturdays 20:30 IL time) runs
`auto_publish.py` automatically for the upcoming Sunday.

## Gotchas

- **`fetch('version.json')` needs a real HTTP server** — opening
  `sidur_live.html` via `file://` fails the fetch (CORS blocks local
  file fetch), so always serve it (step 1) rather than opening the
  file directly in a browser tab.
- **OneSignal push errors in console are expected on localhost** — the
  SDK hardcodes `Can only be used on: https://benilamdan.github.io`
  and refuses to init off that origin. Harmless for UI testing; ignore
  it in `read_console_messages`.
- **`mcp__Claude_Browser__computer { action: "screenshot" }` can fail**
  with "the Browser pane is not displayed" in a headless/no-UI run —
  clicks and `form_input` still work fine via `ref`. Use
  `read_page { filter: "interactive" }` as your proof-of-state instead
  of a screenshot when this happens.
- **The real `sidur_live.html` (at repo root, one level up, outside
  `sidur-repo/`) holds the live OneSignal REST key** — never copy or
  push that one; `sidur-repo/sidur_live.html` is the stripped version
  that's safe to edit/test/push.
- **`parse_schedule.py` referenced in older notes doesn't exist in the
  current repo tree** — only `auto_publish.py` is present. Don't
  assume it's there without checking.
