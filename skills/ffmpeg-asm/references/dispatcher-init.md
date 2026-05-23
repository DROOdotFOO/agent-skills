---
title: CPU Dispatch and DSP Context Initialization
impact: CRITICAL
impactDescription: An asm kernel that isn't wired into the dispatch table runs zero times in production. Dispatch correctness is as load-bearing as kernel correctness.
tags: dispatch, cpu-flags, dsp-context, init, avx512, runtime-detection
---

# CPU Dispatch and DSP Context Init

ffmpeg discovers CPU features at runtime, then populates per-codec
"DSP contexts" (structs of function pointers) with the best available
implementation. A kernel ships dead code unless it's registered in
the corresponding `*_init.c`.

## Architecture overview

```
runtime:
  ff_get_cpu_flags_x86()     -> returns AV_CPU_FLAG_AVX2 | AV_CPU_FLAG_SSE2 | ...

per-codec init (called once at codec open):
  ff_<codec>dsp_init(ctx)         -> sets C fallbacks
  if (ARCH_X86)
    ff_<codec>dsp_init_x86(ctx)   -> overrides with SIMD where flags allow
  if (ARCH_AARCH64)
    ff_<codec>dsp_init_aarch64(ctx)

hot path:
  ctx->some_kernel(args)     -> indirect call into the chosen SIMD impl
```

## CPU flag detection

`libavutil/cpu.c` and arch-specific `libavutil/x86/cpu.c` /
`libavutil/aarch64/cpu.c` probe `cpuid` (x86) or `getauxval` /
`sysctl` (AArch64).

```c
int ff_get_cpu_flags_x86(void);
int ff_get_cpu_flags_aarch64(void);
```

Common flags:

| Flag                          | Meaning                                          |
| ----------------------------- | ------------------------------------------------ |
| `AV_CPU_FLAG_SSE2`            | SSE2 baseline (assumed on x86_64)                |
| `AV_CPU_FLAG_SSSE3`           | SSSE3 (`pshufb` etc.)                            |
| `AV_CPU_FLAG_SSE4`            | SSE4.1                                           |
| `AV_CPU_FLAG_AVX`             | AVX (3-operand, `vex` encoding)                  |
| `AV_CPU_FLAG_XOP`             | AMD XOP (rare, mostly avoid)                    |
| `AV_CPU_FLAG_AVX2`            | AVX2 (256-bit integer, `vpermd`)                 |
| `AV_CPU_FLAG_BMI2`            | `pdep`, `pext`                                   |
| `AV_CPU_FLAG_AVXSLOW`         | CPU has AVX but it's slow (e.g. AMD Bulldozer)   |
| `AV_CPU_FLAG_AVX512`          | AVX-512F + BW + DQ + VL baseline                 |
| `AV_CPU_FLAG_AVX512ICL`       | AVX-512 Ice Lake (VBMI2, VPOPCNTDQ, etc.)        |
| `AV_CPU_FLAG_NEON` (aarch64)  | NEON (assumed on AArch64)                        |
| `AV_CPU_FLAG_SVE`             | SVE                                              |
| `AV_CPU_FLAG_SVE2`            | SVE2                                             |

## `EXTERNAL_*` gating macros

In `libavutil/x86/cpu.h`:

```c
#define EXTERNAL_SSE2(flags)      ((flags) & AV_CPU_FLAG_SSE2)
#define EXTERNAL_SSSE3(flags)     ((flags) & AV_CPU_FLAG_SSSE3)
#define EXTERNAL_SSE4(flags)      ((flags) & AV_CPU_FLAG_SSE4)
#define EXTERNAL_AVX(flags)       (((flags) & AV_CPU_FLAG_AVX) && !((flags) & AV_CPU_FLAG_AVXSLOW))
#define EXTERNAL_AVX2(flags)      ((flags) & AV_CPU_FLAG_AVX2)
#define EXTERNAL_AVX2_FAST(flags) (EXTERNAL_AVX2(flags) && !((flags) & AV_CPU_FLAG_AVXSLOW))
#define EXTERNAL_AVX512(flags)    ((flags) & AV_CPU_FLAG_AVX512)
#define EXTERNAL_AVX512ICL(flags) ((flags) & AV_CPU_FLAG_AVX512ICL)
```

The "external" naming convention means "use the externally-implemented
(asm) kernel". The macros bake in CPU-quality heuristics (`AVXSLOW`).

## DSP context init pattern

Each subsystem has a `*_init.c` plus arch-specific `*_init_x86.c`,
`*_init_aarch64.c`, `*_init_arm.c`. Example for a hypothetical
`mydsp.c`:

```c
/* libavcodec/mydsp.c */
av_cold void ff_mydsp_init(MyDSPContext *c)
{
    c->add_pixels16 = mydsp_add_pixels16_c;
    c->avg_pixels16 = mydsp_avg_pixels16_c;
    c->idct_put     = mydsp_idct_put_c;

#if ARCH_X86
    ff_mydsp_init_x86(c);
#elif ARCH_AARCH64
    ff_mydsp_init_aarch64(c);
#elif ARCH_ARM
    ff_mydsp_init_arm(c);
#endif
}
```

```c
/* libavcodec/x86/mydsp_init.c */
#include "libavutil/x86/cpu.h"
#include "libavcodec/mydsp.h"

void ff_add_pixels16_sse2(uint8_t *dst, const int16_t *src, ptrdiff_t stride);
void ff_add_pixels16_avx2(uint8_t *dst, const int16_t *src, ptrdiff_t stride);
void ff_idct_put_sse2   (uint8_t *dst, ptrdiff_t stride, int16_t *block);
void ff_idct_put_avx2   (uint8_t *dst, ptrdiff_t stride, int16_t *block);

av_cold void ff_mydsp_init_x86(MyDSPContext *c)
{
    int cpu_flags = av_get_cpu_flags();

    if (EXTERNAL_SSE2(cpu_flags)) {
        c->add_pixels16 = ff_add_pixels16_sse2;
        c->idct_put     = ff_idct_put_sse2;
    }
    if (EXTERNAL_AVX2_FAST(cpu_flags)) {
        c->add_pixels16 = ff_add_pixels16_avx2;
        c->idct_put     = ff_idct_put_avx2;
    }
}
```

Pattern notes:

- **C fallback first** -- always assign the C implementation before
  testing flags. Then SIMD assignments overwrite with progressively
  better tiers (SSE2 -> SSSE3 -> SSE4 -> AVX -> AVX2 -> AVX-512).
- **Last-write-wins ordering** -- check tiers in ascending order so the
  highest available tier ends up assigned. Don't use `else if`; you
  want the table walked top-to-bottom.
- **`av_cold` attribute** -- init runs once per codec open, marks as
  cold for the optimizer.
- **`av_get_cpu_flags()` is cached** -- read it once into a local;
  it's a function call but the result is memoized.

## AArch64 dispatch

```c
/* libavcodec/aarch64/mydsp_init.c */
#include "libavutil/aarch64/cpu.h"
#include "libavcodec/mydsp.h"

void ff_add_pixels16_neon(uint8_t *dst, const int16_t *src, ptrdiff_t stride);
void ff_idct_put_neon   (uint8_t *dst, ptrdiff_t stride, int16_t *block);
void ff_idct_put_sve2   (uint8_t *dst, ptrdiff_t stride, int16_t *block);

av_cold void ff_mydsp_init_aarch64(MyDSPContext *c)
{
    int cpu_flags = av_get_cpu_flags();

    if (have_neon(cpu_flags)) {
        c->add_pixels16 = ff_add_pixels16_neon;
        c->idct_put     = ff_idct_put_neon;
    }
    if (have_sve2(cpu_flags)) {
        c->idct_put = ff_idct_put_sve2;
    }
}
```

`have_neon()`, `have_sve()`, `have_sve2()` are the AArch64 equivalents
of the x86 `EXTERNAL_*` macros, defined in `libavutil/aarch64/cpu.h`.

## DSP context split: encoder vs decoder

A common foot-gun is registering a kernel in the wrong DSP context. The
codec landscape has many contexts:

| Context                  | Purpose                                       |
| ------------------------ | --------------------------------------------- |
| `H264DSPContext`         | H.264 decoder DSP (IDCT, deblock, etc.)       |
| `H264QpelContext`        | H.264 quarter-pel motion compensation         |
| `H264ChromaContext`      | H.264 chroma MC                               |
| `H264PredContext`        | H.264 intra prediction                        |
| `HEVCDSPContext`         | HEVC decoder DSP                              |
| `HEVCPredContext`        | HEVC intra prediction                         |
| `VP9DSPContext`          | VP9 decoder DSP                               |
| `AV1DSPContext`          | AV1 decoder DSP                               |
| `MECmpContext`           | Motion estimation compare (encoder side)      |
| `PixblockDSPContext`     | Pixel block diff/sum/add helpers              |
| `BlockDSPContext`        | Generic block ops                             |
| `IDCTDSPContext`         | Generic IDCT (MPEG-2 era codecs)              |

Adding a HEVC kernel to `H264DSPContext` is the kind of mistake that
gets caught only when somebody decodes a real file. Match the codec.

## AVX-512: `EXTERNAL_AVX512` vs `EXTERNAL_AVX512ICL`

The two gating macros separate "any AVX-512" from "Ice Lake-class
AVX-512 with VBMI2, GFNI, VPCLMULQDQ, etc.". The split exists for
**feature availability**, not for dodging frequency throttling.

License-based downclock on AVX-512 was a real concern on Skylake-X and
Cascade Lake but is essentially gone on Ice Lake, Sapphire Rapids,
Emerald Rapids, Granite Rapids, and AMD Zen4 / Zen5. The narrow gate
remains the right call for a different reason:

1. **`EXTERNAL_AVX512ICL` unlocks cross-lane byte permutes (`vpermb`),
   VBMI2 shifts (`vpshrdw`), GFNI (`gf2p8affineqb`), VPCLMULQDQ.**
   These are the instructions that make AVX-512 win over AVX2 for
   codec kernels; without them the speedup is usually marginal.
2. **Pre-ICL AVX-512 parts (Skylake-X, Cannon Lake) lack the above
   instructions** -- gating on `EXTERNAL_AVX512` would crash on those
   parts if your kernel uses them.
3. **Allow users to `./configure --disable-avx512`** to opt out
   entirely, since some workloads on older AVX-512 hardware still
   benefit from sticking with AVX2.
4. **Test on the actual target hardware** before assuming a win, and
   document the result if AVX-512 is a regression somewhere.

## Validating dispatch

After `chmod +x configure && make`, run with `FFREPORT` or `-loglevel`
to see flag detection. To confirm a specific kernel is being called,
the cleanest method is to put a breakpoint in gdb on the asm label, or
to temporarily inject an `int3` (x86) / `brk #0` (aarch64) at the top
of the kernel and rerun -- if you hit it, dispatch is wired correctly.

Force-disable a tier for differential testing:

```bash
./configure --disable-avx2 --disable-avx512
make
./ffmpeg -cpuflags 0 -i input.mp4 ...      # disables runtime SIMD
./ffmpeg -cpuflags +sse2 -i input.mp4 ...  # forces specific tier
```

`-cpuflags` is great for byte-exact differential runs between C and a
specific SIMD tier.

## Reviewer hot-buttons specific to dispatch

- New `ff_*_<isa>` symbol declared but no corresponding assignment in `*_init.c`
- Assignment under wrong `EXTERNAL_*` macro (e.g. AVX2 kernel gated on `EXTERNAL_SSE2`)
- Missing C fallback before the SIMD overrides
- Wrong DSP context (e.g. HEVC kernel in H.264 init)
- AVX-512 gated on `EXTERNAL_AVX512` when `EXTERNAL_AVX512ICL` is what was tested
- Using `else if` between tiers (breaks last-write-wins)
