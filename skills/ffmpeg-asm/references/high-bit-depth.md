---
title: High Bit Depth (HBD) Conventions
impact: HIGH
impactDescription: Modern codec work (HEVC, VVC, AV1, VP9 profile 2) is dominated by 10-bit and 12-bit pixel formats. HBD changes asm templating, dispatch, and clipping in ways that bite first-time contributors.
tags: hbd, bit-depth, hevc, vvc, av1, vp9, bpc, templating, pixel
---

# High Bit Depth (HBD)

Most modern codec work in ffmpeg deals with 10-bit and 12-bit pixel
data, not 8-bit. The conventions for templating asm across bit depths,
naming dispatched symbols, and clipping intermediate results have
established patterns that aren't obvious from reading 8-bit kernels.

## Bit-depth landscape per codec

| Codec   | 8-bit | 10-bit | 12-bit | 16-bit |
| ------- | ----- | ------ | ------ | ------ |
| H.264   | yes   | rare (Hi10P/Hi422/Hi444 profiles) | no | no |
| HEVC    | yes   | Main10 (broadcast standard) | Main12 (mastering) | no |
| VVC     | yes   | Main10 | Main12 | no |
| VP9     | yes   | Profile 2 | Profile 3 | no |
| AV1     | yes   | Main 10-bit | Professional 12-bit | no |
| ProRes  | no    | yes (10-bit 422/444) | yes | no (raw uses int16) |

For HEVC/VVC/AV1, the Main10 profile is the practical default in
streaming, so 10-bit asm kernels often see more production use than
8-bit. Don't treat HBD as the "advanced" case.

## The `BIT_DEPTH` / `BPC` macro pattern

ffmpeg's HBD asm uses **NASM macro templating** to instantiate the same
source body for multiple bit depths. The active macros:

- `BIT_DEPTH` -- numeric bit depth (8, 10, or 12)
- `BPC` -- bytes per component (1 for 8-bit, 2 for 10/12-bit)
- `pixel` -- C-side typedef (`uint8_t` for 8-bit, `uint16_t` for HBD)

In the `.asm`:

```asm
; libavcodec/x86/h2656_template.asm (or similar pattern)
; Compiled multiple times with different BIT_DEPTH values

%if BIT_DEPTH == 8
    %define pixel_size 1
    %define pixel_max  255
%else
    %define pixel_size 2
    %define pixel_max  ((1 << BIT_DEPTH) - 1)
%endif

cglobal hevc_put_pixels_%(BIT_DEPTH), 4, 5, 8
    ; ... body that uses pixel_size and pixel_max
    RET
```

The `_%(BIT_DEPTH)` suffix appends the bit depth to the symbol name,
producing `ff_hevc_put_pixels_8`, `ff_hevc_put_pixels_10`,
`ff_hevc_put_pixels_12` from one source. The dispatcher (see
`references/dispatcher-init.md`) keys on `bit_depth` from the
`HEVCContext` to pick the right symbol.

The companion `.c` file `#includes` the template multiple times with
different `BIT_DEPTH`:

```c
/* libavcodec/x86/hevcdsp_init.c */
#define BIT_DEPTH 8
#include "hevcdsp_template.c"
#undef BIT_DEPTH

#define BIT_DEPTH 10
#include "hevcdsp_template.c"
#undef BIT_DEPTH

#define BIT_DEPTH 12
#include "hevcdsp_template.c"
#undef BIT_DEPTH
```

Inside `hevcdsp_template.c`, the function name uses a `FUNC` macro
that concatenates the suffix:

```c
#define FUNC2(a, b)  a ## _ ## b
#define FUNC(a, b)   FUNC2(a, b)

void FUNC(ff_hevc_put_pixels, BIT_DEPTH)(...) { /* C reference */ }
```

## Symbol suffix conventions by codec family

| Subsystem                      | Suffix style       | Example                              |
| ------------------------------ | ------------------ | ------------------------------------ |
| HEVC, VVC                      | `_8`, `_10`, `_12` | `ff_hevc_put_pixels_10_sse4`         |
| VP9                            | `_8`, `_10`, `_12` | `ff_vp9_mc_8tap_smooth_10_avx2`      |
| AV1 (dav1d-derived)            | `_8bpc`, `_16bpc`  | `dav1d_put_8tap_smooth_16bpc_avx2`   |
| H.264 (Hi10P)                  | `_8`, `_10`        | `ff_h264_idct_add_10_sse2`           |

The dav1d-imported AV1 code keeps dav1d's `_8bpc` / `_16bpc` (the
"16bpc" path handles both 10 and 12 -- intermediate values use int16
either way). When you write fresh AV1 asm in libavcodec, match the
surrounding files' convention.

## Pixel typedef and dispatch keying

The C side keys dispatch on `bit_depth`:

```c
av_cold void ff_hevc_dsp_init_x86(HEVCDSPContext *c, int bit_depth)
{
    int cpu_flags = av_get_cpu_flags();

    if (bit_depth == 8) {
        if (EXTERNAL_SSE2(cpu_flags))     c->put_hevc_qpel = ff_hevc_put_qpel_8_sse2;
        if (EXTERNAL_AVX2(cpu_flags))     c->put_hevc_qpel = ff_hevc_put_qpel_8_avx2;
    } else if (bit_depth == 10) {
        if (EXTERNAL_SSE2(cpu_flags))     c->put_hevc_qpel = ff_hevc_put_qpel_10_sse2;
        if (EXTERNAL_AVX2(cpu_flags))     c->put_hevc_qpel = ff_hevc_put_qpel_10_avx2;
    } else if (bit_depth == 12) {
        if (EXTERNAL_SSE2(cpu_flags))     c->put_hevc_qpel = ff_hevc_put_qpel_12_sse2;
        if (EXTERNAL_AVX2(cpu_flags))     c->put_hevc_qpel = ff_hevc_put_qpel_12_avx2;
    }
}
```

The `bit_depth` argument comes from the codec parser (HEVC SPS, VVC
SPS, etc.). It's set once at codec open. The dispatch table is per
`HEVCDSPContext`, so a single decode session sees only one bit depth.

## Width changes in SIMD code

The fundamental shift from 8-bit to HBD is that pixel data no longer
fits in a single byte lane:

| Operation                  | 8-bit (BPC=1)              | HBD (BPC=2)                          |
| -------------------------- | -------------------------- | ------------------------------------ |
| Single vector load (XMM)   | 16 pixels                  | 8 pixels                             |
| Single vector load (YMM)   | 32 pixels                  | 16 pixels                            |
| Filter accumulator         | int16                      | int32                                |
| Saturating pack to pixel   | `packuswb` (16->8)         | `packusdw` (32->16, SSE4.1)          |
| AArch64 clip               | `sqxtun v0.8b, v0.8h`      | `sqxtun v0.4h, v0.4s`                |
| Mul-high rounding (filter) | `pmulhrsw`                 | `pmulhrsw` (still int16, careful)    |

Practical consequences:

- A "16-pixel-wide" kernel for 8-bit becomes an "8-pixel-wide" kernel
  for HBD at the same SIMD register width. Plan loop counts and
  unroll accordingly.
- Accumulators promote from int16 to int32. `pmaddwd` (int16 x int16 ->
  int32, horizontal add) is your friend on x86. On AArch64, `smlal2`
  / `umlal2` accumulate into the wider lane.
- `packuswb` (SSE2) only handles 16->8. For HBD clipping you need
  `packusdw` (SSE4.1, signed 32 -> unsigned 16 with saturation). Gate
  the corresponding kernel with `EXTERNAL_SSE4`.

### x86: HBD clipping with `packusdw`

```asm
; 4 x int32 accumulator in m0, want 4 x uint10 clipped to [0, 1023]
INIT_XMM sse4
; Clip ceiling at pixel_max via min
pminsd      m0, [pixel_max_10]      ; pixel_max_10 = times 4 dd 1023
; packusdw saturates negative -> 0 implicitly
packusdw    m0, m0                  ; 4 x int32 -> 8 x uint16 (low 4 valid)
```

For 12-bit, swap the constant table. For 16-bit unsigned (ProRes-style
intermediates), `packusdw` still works because it clips to uint16
range natively.

### AArch64: HBD clipping with `sqxtun`

```asm
// 4 x int32 in v0.4s, want 4 x uint10
movi    v1.4s, #0xff, lsl #8     // upper bound for 10-bit (1023)
movi    v1.4s, #3, msl #8        // alternate: 0x3ff = 1023
smin    v0.4s, v0.4s, v1.4s      // clip ceiling
sqxtun  v0.4h, v0.4s             // signed -> unsigned narrow with saturation
                                  // (also clips negatives to 0)
```

`sqxtun` does the "saturate negative to 0" implicitly, matching x86's
`packusdw`. For 12-bit, change the ceiling constant.

## Rounding rules and bit-exact reference

HBD codec specs are explicit about rounding: typically
`(value + (1 << (shift - 1))) >> shift` (round-half-up), implemented
via `pmulhrsw` on x86 and `sqrshrn` / `srshr` on AArch64. The C
reference encodes the exact formula -- never simplify the rounding
constant; checkasm will catch the 1-LSB difference.

```asm
; x86 rounding shift right (signed)
pmulhrsw    m0, m1, [pw_rnd]        ; m0 = (m0 * m1 + 0x4000) >> 15

; AArch64 rounding shift right narrow
sqrshrn     v0.4h, v0.4s, #14       ; signed saturate, round-half-up shift narrow
```

## Choosing where to add HBD support

Some kernels only matter for 8-bit (legacy MPEG-2 IDCT, H.263 deblock).
Others are 10-bit-first (Main10 HEVC, VVC, AV1 streaming).
Recommendations:

- Adding asm to a codec without existing HBD asm: check whether the
  codec spec actually permits HBD. If yes, write both 8-bit and 10-bit
  variants in the same patch series (separate patches, same series).
- Adding asm to a codec with existing HBD asm: match all existing
  bit-depth variants. Don't ship 8-bit-only when the surrounding
  module has 10-bit and 12-bit too.
- The `--enable-small` build cuts HBD code when the user didn't request
  it -- guard expansive HBD tables with `#if CONFIG_<CODEC>_DECODER`.

## checkasm for HBD

checkasm typically tests each bit depth in a loop:

```c
static void check_put_pixels(void)
{
    for (int bit_depth = 8; bit_depth <= 12; bit_depth += 2) {
        HEVCDSPContext c;
        ff_hevc_dsp_init(&c, bit_depth);

        if (check_func(c.put_hevc_pixels, "put_hevc_pixels_%d", bit_depth)) {
            // ... randomize, call_ref, call_new, memcmp
        }
    }
}
```

Make sure your test exercises every bit depth your kernel claims to
support, not just 10-bit.

## Common pitfalls specific to HBD

- 8-bit-only kernel registered in HBD dispatch path -> integer overflow on first 10-bit frame
- `packuswb` left in HBD code path -> wrong saturation, silent bad output
- Loop count assumed to be "16 per XMM" when it's 8 in HBD
- Rounding constant simplified (e.g. `>> 14` instead of `pmulhrsw`) -> 1-LSB diff fails checkasm
- Missing 12-bit variant when the surrounding module supports 12-bit
- AV1-from-dav1d code given `_10` suffix instead of dav1d's `_16bpc`
- HBD checkasm test only covering one bit depth
- `bit_depth` argument missing from `*_dsp_init` call site after adding HBD support
