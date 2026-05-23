---
title: ffmpeg Upstream Patch Workflow
impact: MEDIUM
impactDescription: ffmpeg accepts contributions via two parallel paths as of July 2025 - code.ffmpeg.org and the traditional ffmpeg-devel mailing list with Patchwork. GitHub PRs are still ignored.
tags: ffmpeg-devel, ffmpeg-upstream, patchwork, send-email, code-review, license
---

# Upstream Patch Workflow

As of July 2025, ffmpeg accepts contributions via two parallel paths:

1. **Forgejo at `code.ffmpeg.org`** -- self-hosted Forgejo with
   pull-request workflow. Recommended path for new contributors who
   aren't already set up for email-based review.
2. **`ffmpeg-devel@ffmpeg.org` mailing list** -- the long-standing
   path, tracked via Patchwork at `patchwork.ffmpeg.org`. Still fully
   supported; many maintainers prefer it.

Both paths land in the same canonical repository. Pick whichever fits
your workflow; reviewers operate on both.

The **GitHub mirror** at `FFmpeg/FFmpeg` is read-only -- pull requests
opened there are closed without review.

## Path A: Forgejo pull requests

```bash
# Create an account at https://code.ffmpeg.org
# Add SSH key under user settings

# Fork via the Forgejo UI, then clone your fork
git clone git@code.ffmpeg.org:<your-user>/ffmpeg.git
cd ffmpeg
git remote add upstream https://code.ffmpeg.org/FFmpeg/FFmpeg.git
git fetch upstream

git checkout -b mydsp-h264-idct-avx2 upstream/master
# ... make changes, commit ...
git push origin mydsp-h264-idct-avx2
# Open PR via the Forgejo web UI
```

Forgejo PRs accept the same commit-message style as mailing-list patches
(see below). Reviewers leave inline comments on the PR; iterate by
force-pushing the branch with updated commits.

## Path B: Mailing list (Patchwork)

The traditional flow, fully supported in parallel with Forgejo.

### One-time setup: `git send-email`

```bash
# Install if not present (Debian/Ubuntu)
sudo apt install git-email

# macOS via Homebrew
brew install git-send-email

# Configure SMTP (Gmail with app password example)
git config --global sendemail.smtpserver smtp.gmail.com
git config --global sendemail.smtpserverport 587
git config --global sendemail.smtpencryption tls
git config --global sendemail.smtpuser your.address@gmail.com
# Use an app-specific password, not your account password
git config --global sendemail.smtppass "<app-password>"

# Always confirm before sending
git config --global sendemail.confirm always
```

For 1Password / pass / secret managers, replace `smtppass` with a
`sendemail.smtppass.cmd` shell snippet that resolves the password at
send-time.

## Patch hygiene

```bash
# Create a feature branch off master
git checkout master
git pull
git checkout -b mydsp-h264-idct-avx2

# Make changes, commit in logical units
git add libavcodec/x86/h264dsp.asm libavcodec/x86/h264dsp_init.c
git commit -m "avcodec/x86/h264dsp: add AVX2 IDCT 4x4"

git add tests/checkasm/h264dsp.c
git commit -m "checkasm/h264dsp: cover AVX2 IDCT 4x4"
```

Commit message format:

```
<subsystem>/<file>: <short imperative summary, ~50 chars>

<longer body, wrapped at 72 chars, explaining the why. Cite
spec sections, reference benchmark numbers, mention any
correctness considerations. Mention which CPU you benchmarked
on. Patchwork shows the body.>

Signed-off-by: Your Name <your@email>     <-- optional but conventional
```

Subject prefix convention: `<lib>/<sub>: <desc>` or just `<sub>: <desc>`
for top-level files. Examples:

- `avcodec/x86/h264dsp: add AVX2 IDCT 4x4`
- `avformat/mov: fix integer overflow in stsd box parser`
- `checkasm/hevc_pel: cover SVE2 implementation`
- `configure: enable AVX-512 by default on supported CPUs`

## Sending the patch series

```bash
# Generate patch files (one per commit)
git format-patch -2 origin/master --subject-prefix='PATCH'
# Produces 0001-...patch, 0002-...patch

# Or as a series with cover letter
git format-patch -2 origin/master --subject-prefix='PATCH' --cover-letter
# Edit 0000-cover-letter.patch to add overall description

# Send to mailing list
git send-email --to=ffmpeg-devel@ffmpeg.org *.patch
```

Subject prefix conventions:

- `[PATCH]` -- single patch, ready for review
- `[PATCH 1/N]`, `[PATCH 2/N]` -- numbered series
- `[PATCH v2]`, `[PATCH v3 1/3]` -- subsequent revisions after review
- `[RFC]` -- request for comment, not ready to merge
- `[FFmpeg-devel] [PATCH ...]` -- list software prepends this prefix; don't add yourself

For revisions, increment `v` in the prefix:

```bash
git send-email --to=ffmpeg-devel@ffmpeg.org \
    --subject-prefix='PATCH v2' --in-reply-to='<msgid-of-v1>' \
    *.patch
```

`--in-reply-to` threads the new version under the original on
Patchwork. Get the message ID from the original cover letter (right
column in Patchwork).

## Cover letter content

When sending more than one patch as a related series, include a cover
letter:

```
Subject: [PATCH 0/3] avcodec: AVX2 acceleration for H.264 IDCT

This series adds AVX2 implementations of the four H.264 IDCT block
sizes (4x4, 8x8, idct8_dc, idct_dc), wires them into the existing
H264DSPContext dispatch, and adds checkasm coverage.

Benchmarks on Zen 4 (5950X), median cycles via checkasm --bench:
                    C       SSE2    AVX2
  h264_idct_add    160.5    42.1    28.3   (+33% over SSE2)
  h264_idct8_add   480.2   118.4    91.0   (+23% over SSE2)
  ...

FATE-h264 passes with and without --disable-avx2.

Patch 1: kernel + dispatch
Patch 2: checkasm coverage
Patch 3: minor comment cleanup
```

Reviewers grep the cover letter for benchmark numbers and FATE
status. Lead with that.

### Patchwork: finding and tracking your patch

`patchwork.ffmpeg.org` indexes everything sent to the list. Bookmark
the URL to your patch series -- you'll reference it when sending v2,
v3, etc.

States:

- **New** -- recently posted, awaiting review
- **Under Review** -- a reviewer commented
- **Changes Requested** -- send a v2 addressing comments
- **Accepted** -- merged to master
- **Rejected** -- closed without merge, see thread for reason
- **Superseded** -- replaced by a newer revision

Reply to review comments inline on the list -- don't open a new
thread. Use `mutt`, `mu`, `notmuch`, `aerc`, or webmail with proper
reply-quoting.

## Reviewer hot-buttons (the meta-list)

Drawing from `references/x86inc-macros.md`, `dispatcher-init.md`,
`testing-checkasm-fate.md`, the typical reasons a patch goes through
multiple revisions:

| Category         | Specific issue                                                       |
| ---------------- | -------------------------------------------------------------------- |
| Correctness      | No checkasm test in the same patch                                   |
| Correctness      | Test doesn't cover edge cases (zero block, saturation, misalignment) |
| Correctness      | FATE failure introduced (run `make fate-<codec>` before sending)     |
| Dispatch         | New `ff_*_<isa>` symbol but no assignment in `*_init.c`              |
| Dispatch         | Gated on wrong `EXTERNAL_*` macro                                    |
| x86inc           | Hand-typed `xmm0` instead of `m0` (breaks cross-ISA sharing)         |
| x86inc           | Bare `ret` instead of `RET` (skips vzeroupper)                       |
| x86inc           | `mova` on unaligned address                                          |
| AArch64          | Missing `endfunc`                                                    |
| AArch64          | SVE2 code without `have_sve2()` gate                                 |
| Build            | Configure flag added that defaults to enabled (breaks for someone)   |
| Style            | Tabs vs spaces inconsistent (ffmpeg uses 4-space indent in C)        |
| Style            | Line length >80 in C, >100 in asm (loose enforcement)                |
| Process          | GitHub PR opened instead of mailing list patch                       |
| Process          | Commit message subject >50-72 chars or missing subsystem prefix      |
| Performance      | "Optimization" that's slower on the contributor's claim machine      |
| Performance      | AVX-512 win not validated against AVX2 baseline on the same CPU      |

When in doubt, look at recently-merged patches in the same subsystem
via `git log libavcodec/x86/h264dsp.asm` and mimic their structure.

## License headers

New files need an LGPL or GPL header. The convention:

```
/*
 * <file purpose> for H.264 decoder
 * Copyright (c) <year> <author>
 *
 * This file is part of FFmpeg.
 *
 * FFmpeg is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * FFmpeg is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without any implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with FFmpeg; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
```

For GPL files (libpostproc, some encoders), substitute "Lesser General
Public" with "General Public" and adjust version.

`.asm` files use `;` line comments and otherwise the same body:

```asm
;******************************************************************************
;* <file purpose>
;* Copyright (c) <year> <author>
;*
;* This file is part of FFmpeg.
;*
;* FFmpeg is free software; you can redistribute it and/or
;* modify it under the terms of the GNU Lesser General Public...
;******************************************************************************
```

Don't invent a new format -- copy verbatim from a similar existing
file in the same subsystem.

## IRC and other channels

- **`#ffmpeg-devel` on Libera Chat** -- async discussion, design questions before sending an RFC
- **`#ffmpeg` on Libera Chat** -- end-user help, not for dev questions
- **`ffmpeg-cvslog`** -- mailing list that mirrors commits, useful to subscribe for awareness
- **Trac at `trac.ffmpeg.org`** -- bug tracker, file bugs here, but don't propose features there (use the list)

Don't ping reviewers directly on IRC about pending patches. Wait at
least a week before resending or asking on the list. Maintainers are
volunteers.

## libav fork: archived

libav forked from ffmpeg in 2011 and went into a long decline; the
project is now archived. The `libav.org` domain no longer resolves and
the mailing list is closed. Modern ffmpeg-compatible APIs that
originated in libav still ship under ffmpeg. If you encounter advice to
"send the patch to libav-devel", it's stale.

Contribute exclusively to ffmpeg.

## Before submitting: pre-send checklist

Run through this list before `git send-email` or "Create Pull Request":

- [ ] `make checkasm && tests/checkasm/checkasm <module>` passes for the touched module
- [ ] checkasm test for the new kernel is in the same patch series
- [ ] Edge cases covered: zero block, saturated extremes, misaligned source
- [ ] Dispatch table entry added in `*_init.c` under the correct `EXTERNAL_*` / `have_*()` gate
- [ ] `make fate-<codec>` passes for any codec touched
- [ ] Build clean with `--disable-asm`, `--cpu=generic`, and your target CPU
- [ ] No bare `ret` inside `INIT_YMM` / `INIT_ZMM` blocks (use `RET`)
- [ ] No hand-typed `xmm0`/`ymm0` where `m0`/`xm0`/`ym0` was expected
- [ ] AArch64: `endfunc` after every `function`
- [ ] Commit message: `<subsystem>/<file>: <imperative summary>` under ~50 chars
- [ ] Commit body includes benchmark numbers and the CPU you tested on
- [ ] License header on new files matches the directory (LGPL vs GPL)
- [ ] No GPL-only code under an LGPL-licensed build path

## Common pitfalls specific to upstream workflow

- Opening a GitHub PR -- silently ignored; use Forgejo or mailing list
- Sending a patch via `git format-patch | mail` instead of `git send-email` (often mangles encoding)
- Forgetting `--in-reply-to` on v2/v3, so Patchwork doesn't thread
- Mixing the two paths mid-series (Forgejo PR for v1, mailing list for v2) -- reviewers lose history
- Subject line missing `<subsystem>:` prefix
- Commit message body missing the "why" (benchmark numbers, spec citation)
- Replying to review comments by quoting the whole patch (use inline quotes)
- Sending v2 without first reading the v1 review feedback carefully
- Squashing what should be multiple commits into one giant patch
- Splitting what should be one logical change into many micro-commits
