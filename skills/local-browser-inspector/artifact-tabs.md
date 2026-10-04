---
title: Claude Artifact and Local Browser Recipes
impact: HIGH
impactDescription: Authenticated browser state and Claude artifact frames are easy to misread from the wrong tab or shell page
tags: claude-artifacts, brave, chrome, applescript, browser-relay
---

# Claude Artifact and Local Browser Recipes

## Brave tab enumeration on macOS

INCORRECT -- copying the visible page without proving it is the requested tab:

```bash
osascript -e 'tell application "System Events" to keystroke "a" using command down' \
  -e 'tell application "System Events" to keystroke "c" using command down' \
  -e 'return the clipboard'
```

This can silently capture an unrelated focused tab.

CORRECT -- enumerate Brave tabs and identify the target first:

```bash
osascript \
  -e 'tell application "Brave Browser" to set out to ""' \
  -e 'tell application "Brave Browser" to repeat with wi from 1 to count of windows' \
  -e 'set w to window wi' \
  -e 'repeat with ti from 1 to count of tabs of w' \
  -e 'set t to tab ti of w' \
  -e 'set out to out & wi & ":" & ti & " selected=" & (ti = active tab index of w) & " | " & (URL of t) & " | " & (title of t) & linefeed' \
  -e 'end repeat' \
  -e 'end repeat' \
  -e 'return out'
```

Then address the exact window/tab in later commands.

## Claude artifact iframe extraction

INCORRECT -- reading the artifact URL alone and stopping at the shell:

```text
https://claude.ai/code/artifact/<uuid>
```

The shell may show only the Claude chrome, `Page not found`, or a minimal title even while the authenticated browser has the artifact loaded.

CORRECT -- inspect iframes in the already-open tab:

```bash
osascript -e 'tell application "Brave Browser" to execute tab 2 of window 1 javascript "JSON.stringify({url:location.href,title:document.title,iframes:[...document.querySelectorAll(\\"iframe\\")].map(f=>({src:f.src,id:f.id,title:f.title,className:f.className}))})"'
```

Read the returned `frame.claudeusercontent.com/_f/...` URL directly. That URL usually contains the full artifact HTML.

## Chrome-family caveats

- `Google Chrome`, `Google Chrome for Testing`, and `Brave Browser` are separate AppleScript targets. Confirm the process and tab list instead of addressing `Google Chrome` by habit.
- Chrome may reject `execute ... javascript` until the user enables **View > Developer > Allow JavaScript from Apple Events**.
- A browser relay timeout is evidence to change approach, not evidence that the tab is unavailable.
- If copying is unavoidable, save the current clipboard, focus the verified tab, click the page body, copy, read the clipboard, then restore the original clipboard.
