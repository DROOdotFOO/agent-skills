---
name: local-browser-inspector
description: >
  Inspect a user's already-open local browser session without losing tab context.
  TRIGGER when: user asks to look at their Chrome, Brave, Safari, or already-open
  browser tab; mentions /chrome, browser relay, CDP, AppleScript, authenticated
  pages, Claude artifacts, or says a page is open in their browser.
  DO NOT TRIGGER when: static public content can be fetched with read, writing
  Playwright end-to-end tests (use playwright), auditing frontend quality (use
  frontend-slop-audit), or taking consequential account actions without explicit
  user instruction.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: browser, chrome, brave, applescript, relay, artifacts
---

# Local Browser Inspector

Use this when the useful state is in the user's existing browser: authenticated tabs, locally focused pages, extension-backed sessions, or Claude artifact frames that do not resolve from a cold fetch.

## Workflow

1. **Prefer non-invasive reads first.** Fetch static URLs directly with `read`. Use a managed browser only when JavaScript, authentication, or rendered state matters.
2. **Target the exact browser and tab.** Enumerate windows/tabs by browser application before copying or driving anything. Match on URL and title; do not assume the front tab is the requested page.
3. **Use browser relay or CDP when available.** Adopt a named target tab instead of navigating the user's visible tab. If relay times out or attaches to a test browser, fall back to local browser automation.
4. **For Chromium-family browsers on macOS, use app scripting as a read-only fallback.** Brave and Chrome expose tabs and `execute ... javascript` through AppleScript when enabled.
5. **For Claude artifacts, inspect the outer shell's iframe.** The visible artifact content usually lives under `*.frame.claudeusercontent.com/_f/...`; read that iframe URL directly once extracted.
6. **Only use clipboard copy as the last fallback.** First focus the target tab and click page body; save and restore clipboard; never trust copied text unless the selected tab was verified immediately before copying.

## Safety rules

- Do not navigate, submit, delete, purchase, sign, or approve anything in the user's real browser unless the user explicitly asked for that exact action.
- Do not close user-owned tabs. Release managed tool sessions only.
- Do not read unrelated tabs beyond URL/title enumeration needed to find the target.
- Treat extension pages and wallet pages as sensitive; collect only the minimum metadata needed to identify the target.

## Common pitfalls

| Mistake | Fix |
| --- | --- |
| Copying the front tab and assuming it is the target | Enumerate tabs and select the matching URL/title first |
| Reading `document.body.innerText` from the Claude artifact shell | Extract `iframe#frame-content.src`, then read that frame URL |
| Using Chrome automation when the user said Brave | Address `Brave Browser` explicitly; Chrome and Chrome for Testing can be separate apps |
| Retrying browser relay after repeated timeouts | Switch to CDP or app scripting; repeated relay opens add no evidence |

## What You Get

- A safe decision tree for inspecting already-open local browser sessions.
- Brave and Chrome tab-targeting guidance that avoids copying the wrong page.
- A Claude artifact iframe recipe for recovering rendered artifact content when the shell URL is insufficient.

## Reading guide

| Topic | File |
| --- | --- |
| Claude artifact and Brave/Chrome inspection recipes | `artifact-tabs.md` |

## See also

- `playwright`
- `frontend-slop-audit`
