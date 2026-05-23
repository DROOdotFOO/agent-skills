---
title: Codec Hot Paths (DCT, MC, Deblock, Entropy, Scaler)
impact: HIGH
impactDescription: Catalog of where the cycles go inside libav* codecs. Knowing which kernels matter for which codecs is half the work of choosing what to optimize.
tags: codec, dct, idct, motion-compensation, deblocking, cabac, scaler, swscale, hevc, h264
---

# Codec Hot Paths

A working map of where SIMD effort pays off, organized by codec
subsystem. For each, the relevant DSP context and the kernels that
typically dominate the profile.

## Transform: DCT / IDCT

The forward DCT (encoder) and inverse DCT/transform (decoder) appear in
almost every codec, at varying block sizes.

| Codec    | Sizes              | Where                                              |
| -------- | ------------------ | -------------------------------------------------- |
| MPEG-2   | 8x8                | `IDCTDSPContext` (idct_put, idct_add)              |
| H.264    | 4x4, 8x8           | `H264DSPContext` (h264_idct_add, h264_idct8_add)   |
| HEVC     | 4x4, 8x8, 16x16, 32x32 | `HEVCDSPContext` (idct_4x4, ..., idct_32x32)   |
| VP9      | 4x4..32x32 + ADST  | `VP9DSPContext` (itxfm_add)                        |
| AV1      | 4x4..64x64 + variants | `AV1DSPContext` (inv_txfm_add)                  |

Implementation idiom: 2D transforms decompose into row pass + transpose
+ column pass + add to predictor. The transpose between passes is the
classic SIMD challenge -- see `references/x86-simd-patterns.md` for the
4x4/8x8 transpose recipe.

Bit-exactness matters because transforms are baked into the codec
spec. Even a 1-LSB rounding difference fails FATE.

## Motion compensation (MC)

Inter-predicted blocks get filtered samples from a reference frame at
sub-pixel precision. The filter tap counts and sub-pixel grids vary by
codec.

| Codec  | Sub-pel | Filter taps   | DSP context          | Function family               |
| ------ | ------- | ------------- | -------------------- | ----------------------------- |
| H.264  | quarter | 6-tap luma, bilinear chroma | `H264QpelContext` + `H264ChromaContext` | `put_h264_qpel*_mc*`, `put_h264_chroma_mc*` |
| HEVC   | quarter | 8-tap luma, 4-tap chroma  | `HEVCDSPContext`     | `put_hevc_qpel_*`, `put_hevc_epel_*` |
| VP9    | eighth  | 8-tap symmetric | `VP9DSPContext`     | `mc_8tap_*`                   |
| AV1    | eighth  | 8-tap + warp affine | `AV1DSPContext` | `put_8tap_*`, `warp_8x8`      |

MC kernels come in two flavors: `put` (write to output buffer) and
`avg` (bi-predict, average with existing buffer). Plus separable
horizontal-then-vertical decomposition for each.

Cycle-heavy because MC is run per-block at every output pixel. A 5%
speedup here moves the needle on overall decode throughput.

## In-loop deblocking

Post-decode filter that smooths block boundaries. Strength-driven
branching makes SIMD tricky -- pure SIMD has to compute all branches
and select.

| Codec | Filter            | DSP context     |
| ----- | ----------------- | --------------- |
| H.264 | edge-adaptive     | `H264DSPContext` (`h264_loop_filter_*`) |
| HEVC  | bilateral + SAO   | `HEVCDSPContext` (`hevc_loop_filter_*`, `hevc_sao_*`) |
| VP9   | per-edge strength | `VP9DSPContext` (`loop_filter_*`)       |
| AV1   | CDEF + loop restoration | `AV1DSPContext` (`cdef_*`, `loop_restore_*`) |

Idiom: compute deltas, generate per-lane mask using `cmpgt`/`pcmpgtb`,
then `pand`/`pblendvb` to apply the filter conditionally. NEON
`bsl` (bit-select) is the AArch64 equivalent.

## Entropy coding: CABAC

CABAC (Context-Adaptive Binary Arithmetic Coding) is the inner loop of
H.264 and HEVC decoders. Hot path is the bin decoder:

```c
// libavcodec/cabac.h - decode one bin
get_cabac(CABACContext *c, uint8_t *state);
```

This is mostly **scalar** code, not SIMD -- but heavy on branching,
table lookups, and bit-fiddling. Architecture-specific optimization
goes into:

| Path                          | What it does                                |
| ----------------------------- | ------------------------------------------- |
| `libavcodec/x86/cabac.h`      | `__asm__ goto` blocks, `bsr`-based renorm   |
| `libavcodec/aarch64/...`      | NEON helpers for residual-block reads       |

Don't try to vectorize the per-bin path. Focus on the renormalization
and residual-coefficient decode where SIMD does help.

VLC (Variable Length Coding) decoders (MPEG-2, VP9 boolean coder, AV1
symbol coder) have similar shape -- scalar inner loop with occasional
SIMD helpers for batch operations.

## Pixel comparison: SAD / SSE / SATD

Encoder motion estimation walks candidate motion vectors and compares
each candidate's predicted block against the original. SAD (sum of
absolute differences), SSE (sum of squared errors), and SATD
(sum of absolute Hadamard-transformed differences) are the metrics.

DSP context: `MECmpContext`. Functions like `sad8x8`, `sad16x16`,
`sse16`, `hadamard8_diff*`. These get called millions of times per
frame in an encoder -- highly worth optimizing.

x86 instruction notes:

- `psadbw` -- single-instruction SAD over 16 bytes, returns 2 x int16 sums
- `pmaddwd` followed by `paddd` for SSE on int16 data
- AVX-512 `vpdpbusd` (VNNI) fuses multiply-add for dot products

AArch64 instruction notes:

- `uabd` + `uadalp` chains for SAD
- `addv` for final reduction
- `udot` / `sdot` (Armv8.2-DotProd) for SSE-style accumulation

## Scaling and colorspace: libswscale

`libswscale/x86/` and `libswscale/aarch64/` hold conversions between
pixel formats and resizers.

| Subsystem    | Hot kernels                                            |
| ------------ | ------------------------------------------------------ |
| Format conv  | YUV<->RGB, YUYV<->YUV420P, NV12<->I420                 |
| Scaler       | bilinear, bicubic, lanczos hScale and vScale           |
| Bit depth    | 8<->10<->12 conversions, dithering                     |

Scaler kernels are particularly amenable to SIMD: long horizontal runs
of independent filter taps. The interleaved load (`ld2`/`ld3`/`ld4`
on AArch64, `pshufb`-based deinterleaving on x86) is the workhorse.

## Filter graphs: libavfilter

`libavfilter/x86/` and `libavfilter/aarch64/` hold SIMD for individual
filters. The big wins:

- `vf_yadif` (deinterlace) -- vector filter taps + adaptive blend
- `vf_bwdif` -- newer deinterlacer, similar shape
- `vf_overlay` -- alpha blend, pixel-saturated
- `vf_blend` -- many blend modes per-pixel
- `af_volume`, `af_loudnorm` -- audio gain with saturation

Filter graph compiles once, runs per-frame. Hot kernels typically
operate on full rows.

## Choosing what to optimize

The standard ffmpeg perf workflow:

```bash
# 1. Identify hot functions from a real workload
./ffmpeg -i typical.mp4 -f null - -benchmark
perf record -g ./ffmpeg -i typical.mp4 -f null -
perf report

# 2. Once you have a function name, check it has an asm impl
grep -r "ff_<funcname>_" libav*/x86 libav*/aarch64

# 3. If asm exists for some tiers but not the one your CPU has,
#    add the missing tier
# 4. If no asm exists at all, that's a candidate
```

Heuristic: if a C function takes >2% of total CPU and has no asm impl,
it's worth writing one. <1% is rarely worth the maintenance burden
unless it's on a critical path.

## What NOT to optimize

- **Init / open / setup paths** -- run once per stream, profile noise
- **Bitstream parsing** that's already scalar-optimal -- branch prediction wins
- **Audio resampling** beyond what `libswresample/aarch64` already has -- DSP is dominated by other stages
- **Error concealment paths** -- rare in practice, complexity not worth it
- **Anything called <0.5% of total time** -- maintenance cost exceeds gain

## Common pitfalls specific to codec hot paths

- Optimizing the wrong size (e.g. AVX2 32x32 IDCT when the test workload uses 8x8)
- Beating C for one block size but regressing another -- benchmark all sizes
- Bit-inexact "fast" path that fails FATE on edge-case inputs
- New transform without updating the dispatch in `*_init.c` for that block size
- Forgetting that encoder kernels use `MECmpContext`, not the decoder DSP context
- Spending cycles on `psadbw` when AVX-512 VPDPBUSD or AArch64 `udot` is available and faster
