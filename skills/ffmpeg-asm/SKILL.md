---
name: ffmpeg-asm
description: >
  ffmpeg upstream contributions (hand-written assembly in
  libavcodec/libavfilter/libswscale) and custom ffmpeg integration
  (building, embedding, calling libav* APIs). Covers x86_64
  (SSE/AVX/AVX2/AVX-512) and AArch64 (NEON/SVE/SVE2) idioms specific to
  ffmpeg's x86inc.asm and aarch64/asm.S macro frameworks, the checkasm
  and FATE test harnesses, and the ffmpeg upstream patch workflow.
  TRIGGER when: editing .asm files under libav*/x86/, .S files under
  libav*/aarch64/ or libav*/arm/, working with x86inc.asm, x86util.asm,
  or aarch64/asm.S macros, writing *_init.c SIMD dispatch tables,
  modifying tests under checkasm/, running FATE, configuring an ffmpeg
  build (./configure flags, --enable-*), linking libavcodec, libavformat,
  libavutil, libavfilter, libswscale, or libswresample from C, Rust,
  Elixir, or Go, preparing a patch for ffmpeg-devel or Patchwork, or
  comparing libav vs ffmpeg fork divergence. DO NOT TRIGGER when:
  general SIMD or intrinsics questions outside ffmpeg's macro framework
  (use droo-stack for C/Rust syntax, native-code for BEAM NIF SIMD),
  non-ffmpeg codec libraries like libvpx, dav1d, x264, x265, SVT-AV1
  unless explicitly bridging through ffmpeg, GStreamer pipelines,
  application-level video editing UX, or container/protocol parser bugs
  without an asm or SIMD angle.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: ffmpeg, libav, simd, asm, x86, avx, avx512, neon, sve, sve2, aarch64, codec, video, audio, dsp, hbd, bit-depth
---

# ffmpeg-asm

You are an ffmpeg DSP contributor. The C reference is the oracle. The
assembler is hostile. Every cycle is contested. The upstream reviewer
has been doing this since 2007.

Domain knowledge for hand-written SIMD assembly inside libav*, the
build/integration surface around it, and the upstream patch workflow.
For BEAM NIF wrappers around libavcodec see `native-code`. For general C
or Rust language patterns outside ffmpeg's macros see `droo-stack`. For
higher-level profiling workflow before reaching for asm see
`performance-profiler`.

## What You Get

- x86inc.asm macro framework reference (`cglobal`, register naming, AVX/SSE auto-switching)
- CPU dispatch and DSP-context init pattern (`ff_get_cpu_flags_*`, `EXTERNAL_*` gates)
- x86_64 SIMD idioms (SSE through AVX-512) tailored to ffmpeg conventions
- AArch64 NEON plus SVE/SVE2 idioms, with Apple M4 SME caveats and 32-bit ARM legacy notes
- High-bit-depth (10/12-bit) templating, symbol suffixes, and clipping idioms
- Codec hot-path catalog (DCT, motion compensation, deblock, entropy, scaler, colorspace)
- Build and integration recipes for embedding ffmpeg in C, Rust, Elixir, Go
- checkasm and FATE testing discipline, plus ffmpeg upstream patch workflow

## Philosophy

The C reference is truth. Asm exists only to make the same output faster.
Every kernel must be bit-exact against the C path under checkasm, every
new function must register in the dispatch table in the same patch, and
the patch goes to ffmpeg-devel, not GitHub.

## Key principles

1. **C reference first, asm second, byte-exact always** -- no "close enough" on pixel output
2. **Same-patch checkasm** -- a kernel without a checkasm test will be rejected on review
3. **`INIT_XMM`/`INIT_YMM`/`INIT_ZMM` is your ISA gate** -- never hand-duplicate SSE/AVX/AVX-512 kernels
4. **Dispatch registration is part of the patch** -- a perfect kernel that nobody calls runs zero times
5. **VZEROUPPER on AVX exit, mask-register hygiene on AVX-512** -- Skylake-class transition penalty is real
6. **Contribute via ffmpeg's canonical paths, not the GitHub mirror** -- `code.ffmpeg.org` or `git send-email` to ffmpeg-devel; see `references/upstream-workflow.md`
7. **Asm comments describe the computation, not the patch** -- drop AI-narration / authoring-meta (`// Args are bare reg names`, `// Chroma-preserving variant of X for...`); keep dataflow + register annotations even through param-rename refactors; cover letters report speedup, not "fewer cycles"; see `references/upstream-workflow.md` "Comment style"

## When to use

- Editing `.asm` under `libav*/x86/` or `.S` under `libav*/aarch64/` or `libav*/arm/`
- Working with `x86inc.asm`, `x86util.asm`, `aarch64/asm.S` macro frameworks
- Writing or modifying `*_init.c` SIMD dispatch tables
- Adding or fixing tests under `tests/checkasm/`
- Running FATE (`make fate-*`) and triaging failures
- Configuring an ffmpeg build (`./configure` flags, custom minimal builds)
- Linking libav* from C, Rust, Elixir (via NIF), or Go
- Preparing a patch for ffmpeg-devel or following up on Patchwork review
- Comparing libav vs ffmpeg fork divergence for a shared API surface

## When NOT to use

- General SIMD or intrinsics work outside ffmpeg's macros -- use `droo-stack` or `native-code`
- Non-ffmpeg codec libraries' internal asm (dav1d, libvpx, x264, x265, SVT-AV1)
- Hardware acceleration APIs (VAAPI, NVENC, VideoToolbox, QSV) -- these wrap vendor drivers
- Application-level ffmpeg CLI usage, filter graph composition, muxing recipes
- GStreamer, MLT, OBS, and adjacent application ecosystems
- Audio DSP theory (psychoacoustic models, perceptual coding math)
- Container or protocol parser security bugs without an asm/SIMD angle -- use `security-auditor`

## Reading guide

### Writing assembly

| Working on                                          | Read                                                                    |
| --------------------------------------------------- | ----------------------------------------------------------------------- |
| x86inc.asm macros, cglobal, AVX/SSE switching       | [references/x86inc-macros](references/x86inc-macros.md)                 |
| CPU feature detection and DSP dispatch tables       | [references/dispatcher-init](references/dispatcher-init.md)             |
| x86_64 SSE/AVX/AVX2/AVX-512 idioms                  | [references/x86-simd-patterns](references/x86-simd-patterns.md)         |
| AArch64 NEON/SVE/SVE2, Apple Silicon, ARMv7 legacy  | [references/aarch64-neon-sve](references/aarch64-neon-sve.md)           |
| 10/12-bit pixel asm, BPC templating, HBD dispatch   | [references/high-bit-depth](references/high-bit-depth.md)               |
| DCT/IDCT, motion comp, deblocking, entropy, scaler  | [references/codec-hot-paths](references/codec-hot-paths.md)             |

### Integration and process

| Working on                                          | Read                                                                    |
| --------------------------------------------------- | ----------------------------------------------------------------------- |
| `./configure` flags, embedding libav* in C/Rust/etc | [references/build-integration](references/build-integration.md)         |
| checkasm + FATE byte-exact verification             | [references/testing-checkasm-fate](references/testing-checkasm-fate.md) |
| ffmpeg upstream patch workflow (both canonical paths) | [references/upstream-workflow](references/upstream-workflow.md)       |

## Common pitfalls

| Mistake                                              | Impact                                              | Fix                                                                  |
| ---------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------- |
| Missing `VZEROUPPER` before SSE-style code path      | Per-instruction false-dep cost on Skylake+, merge dep on Zen | Add `RET` macro which emits `vzeroupper` for AVX `INIT_YMM` blocks   |
| Submitting kernel without checkasm test              | Reviewer rejects, byte-exactness unverified         | Add `tests/checkasm/<module>.c` entry in the same patch              |
| New function not registered in `*_init.c`            | Kernel ships but nothing calls it                   | Add function pointer assignment under correct `EXTERNAL_*` flag      |
| AVX-512 without `EXTERNAL_AVX512ICL` gate            | Crashes on pre-ICL AVX-512 parts (Skylake-X, Cannon Lake) using VBMI2/GFNI | Gate with the narrowest applicable flag; consider `--disable-avx512` |
| Hand-duplicated SSE/AVX kernels                      | Doubles maintenance, divergent bugs                 | Use `INIT_XMM sse2` / `INIT_YMM avx2` to share source                |
| AVX2 lane-crossing assumed to be SSE-style shuffle   | Silent wrong output on upper 128-bit lane           | Read AVX2 shuffle docs; use `vperm2i128` for cross-lane              |
| GitHub PR opened against ffmpeg mirror               | Ignored -- mirror is read-only                      | Use `code.ffmpeg.org` or `git send-email` to ffmpeg-devel             |
| AI-narration `//` comments left in asm               | Reviewer blocks PR for noise; reads as authoring-meta, not code semantics | Strip comments that explain the refactor or implementation choice; keep dataflow + register annotations only |
| `//` annotations stripped during param-rename refactor | Block: reviewer flags lost annotations one by one  | Carry original comment text verbatim through the rename; change the symbol, not the trailing prose |
| Cover letter framed as "fewer cycles" / every bench width dumped | Reviewer requests rewrite; speedup is the grep target | Frame as speedup (new/baseline); foreground the widest column; model after `f54841d375` |
| v(N)->v(N+1) diff edits lines unrelated to review comments | Forgejo `Compare` button useless; review history splinters | Constrain revisions to review comments; split structural changes into a separate prep commit |
| 8-bit-only kernel registered in HBD dispatch path    | Integer overflow on first 10-bit frame              | Add 10/12-bit variants (`_10`, `_12` suffix); see references/high-bit-depth |
| `SECTION_RODATA` constants without explicit align    | Misaligned `mova` traps                             | `SECTION_RODATA 32` (or 64 for AVX-512); use `ALIGN`                 |
| `--enable-gpl` toggled accidentally on LGPL target   | Downstream license obligations change               | Audit `./configure` output; keep LGPL builds clean of GPL components |

## See also

- `native-code` -- BEAM NIF wrappers calling into libavcodec from Elixir
- `droo-stack` -- general C, Rust, Zig language patterns
- `performance-profiler` -- higher-level perf workflow, flamegraphs, before reaching for asm
- `code-review` -- pre-submission self-review against ffmpeg-devel reviewer hot-buttons
- `tdd` -- red/green/refactor discipline applied to checkasm tests
- `focused-fix` -- 5-phase methodology for SIMD correctness regressions
