---
title: AArch64 NEON and SVE/SVE2 Patterns
impact: HIGH
impactDescription: AArch64 idioms for libav*/aarch64. Apple Silicon and server Arm are growing ffmpeg targets; NEON and SVE2 patterns differ enough from x86 SIMD to need their own reference.
tags: aarch64, arm64, neon, sve, sve2, apple-silicon, ld1, tbl, asm
---

# AArch64 NEON and SVE/SVE2 Patterns

Working idioms for `libav*/aarch64/`. The macro framework lives in
`libavutil/aarch64/asm.S`. Apple Silicon (M1/M2/M3), Neoverse N1/V1/V2
(AWS Graviton, Ampere Altra), and Snapdragon X are the dominant
in-the-wild targets.

## Macro framework: `libavutil/aarch64/asm.S`

```asm
#include "libavutil/aarch64/asm.S"

function ff_pixel_avg_w16_neon, export=1
    // r0 = dst, r1 = src1, r2 = src2, r3 = stride
    ld1     {v0.16b}, [x1]
    ld1     {v1.16b}, [x2]
    urhadd  v0.16b, v0.16b, v1.16b
    st1     {v0.16b}, [x0]
    ret
endfunc

const some_table, align=4
    .byte 0x01, 0x02, 0x04, 0x08
endconst
```

Key macros:

- `function NAME, export=1` -- function prologue with global symbol
- `endfunc` -- function epilogue
- `const NAME, align=N` ... `endconst` -- read-only constant table

The `function` macro handles `.text` section setup, BTI landing pads
on hardware that requires them, and symbol versioning.

## Register naming

AArch64 has 32 vector registers, each addressable at multiple widths:

| Form     | Meaning                                     |
| -------- | ------------------------------------------- |
| `v0.16b` | 16 x 8-bit                                  |
| `v0.8h`  | 8 x 16-bit (half)                           |
| `v0.4s`  | 4 x 32-bit (single)                         |
| `v0.2d`  | 2 x 64-bit (double)                         |
| `v0.8b`  | 8 x 8-bit (low 64 bits only)                |
| `v0.4h`  | 4 x 16-bit (low 64 bits)                    |
| `v0.2s`  | 2 x 32-bit (low 64 bits)                    |
| `v0.d[1]` | high 64 bits of v0 as a scalar             |
| `v0.s[2]` | 3rd lane as a scalar                       |

Half-register forms (`.8b`, `.4h`, `.2s`) operate on only the low 64
bits and zero the upper 64. Useful for narrow data without wasting
register file pressure.

## Interleaved loads: `ld1` / `ld2` / `ld3` / `ld4`

The killer feature for codec work. A single instruction can
deinterleave planar from packed pixel layouts:

```asm
// Packed BGRA32 -> planar B, G, R, A in v0..v3
ld4     {v0.16b, v1.16b, v2.16b, v3.16b}, [x0]
// After: v0 = 16 x B, v1 = 16 x G, v2 = 16 x R, v3 = 16 x A

// Packed YUYV422 -> Y in v0, U+V interleaved in v1
ld2     {v0.16b, v1.16b}, [x0]

// Plain 16-byte load
ld1     {v0.16b}, [x0]

// Two consecutive 16-byte loads
ld1     {v0.16b, v1.16b}, [x0]

// Post-indexed load (stride update)
ld1     {v0.16b}, [x0], #16        // load, then x0 += 16
ld1     {v0.16b}, [x0], x1         // load, then x0 += stride (x1)
```

`st1`..`st4` mirror the load forms. This eliminates entire pshufb
chains that x86 needs for the same effect.

## `tbl` / `tbx` -- arbitrary permutations

NEON's answer to `pshufb`. `tbl` is the AArch64 equivalent of x86's
shuffle-by-table:

```asm
// Build an arbitrary permutation of bytes from v1, indexed by v0
tbl     v2.16b, {v1.16b}, v0.16b
// Each byte of v0 selects a byte from v1; out-of-range indices give 0

// Multi-register table (lookup across multiple vector registers)
tbl     v2.16b, {v1.16b, v3.16b}, v0.16b      // index 0..31 across v1+v3
tbl     v2.16b, {v1.16b, v3.16b, v4.16b, v5.16b}, v0.16b  // index 0..63

// tbx is the same but keeps the destination's old value on out-of-range
tbx     v2.16b, {v1.16b}, v0.16b
```

Multi-register `tbl` requires the source registers to be consecutive
(`v1, v2, v3, v4`) -- the assembler enforces this. Helpful for codec
table lookups (e.g. intra-prediction angles in HEVC).

## Multiply-accumulate

```asm
// Signed/unsigned multiply-accumulate long: int16 * int16 -> int32 accum
smlal       v0.4s, v1.4h, v2.4h            // v0 += sign-extend(v1) * sign-extend(v2), low 4 lanes
smlal2      v0.4s, v1.8h, v2.8h            // same, but operates on HIGH 4 lanes (2 means "high")

umlal       v0.4s, v1.4h, v2.4h            // unsigned variant

// Saturating multiply-accumulate (used in fixed-point DSP)
sqdmlal     v0.4s, v1.4h, v2.4h            // saturating doubling multiply-accumulate
```

The `2`-suffixed variants (`smlal2`, `umlal2`, `addhn2`) operate on
the high half of the source register. Combined with the non-`2`
variant they let you process a full 128-bit register in two
instructions without explicit lane extraction.

## Saturating arithmetic

```asm
sqadd       v0.16b, v1.16b, v2.16b         // signed saturating add
uqadd       v0.16b, v1.16b, v2.16b         // unsigned saturating add
sqsub       v0.16b, v1.16b, v2.16b         // signed saturating subtract
uqxtn       v0.8b,  v1.8h                  // unsigned saturating narrow (16->8)
sqxtn       v0.8b,  v1.8h                  // signed saturating narrow
sqxtun      v0.8b,  v1.8h                  // signed source, unsigned saturated narrow (pixel clip)
```

`sqxtun` is the AArch64 equivalent of x86's `packuswb` for clipping
signed int16 into uint8 pixel data. Use it after IDCT, after horizontal
filter accumulation, etc.

## Pairwise / reduction ops

```asm
addp        v0.16b, v1.16b, v2.16b         // pairwise add: out[0] = in[0]+in[1], out[1] = in[2]+in[3], ...
saddlp      v0.8h,  v1.16b                 // pairwise add long: int8 pairs -> int16
uaddlp      v0.8h,  v1.16b                 // unsigned variant
addv        b0,     v1.16b                 // ACROSS lanes: sum all bytes of v1 to scalar b0
uaddlv      h0,     v1.16b                 // sum all uint8 lanes to uint16 scalar
saddlv      h0,     v1.16b                 // signed variant
```

`addv`/`uaddlv`/`saddlv` are single-instruction horizontal reductions --
unlike x86 where you need a shuffle-add chain. Use them for SAD-style
operations.

## SVE and SVE2 basics

SVE (Scalable Vector Extension) is vector-length-agnostic: code works
on any implementation width from 128 to 2048 bits. SVE2 adds
codec-friendly ops on top (`tbl` with arbitrary tables, more saturating
forms, integer multiply-high).

```asm
// SVE: declare a predicate for "all true up to 16 elements"
ptrue   p0.b, vl16

// Or runtime: predicate true for lanes [0, n)
whilelo p0.b, x0, x1          // p0 lane i = (x0 + i) < x1

// Predicated load (only loads where predicate is true)
ld1b    {z0.b}, p0/z, [x2]    // /z = zero inactive lanes; /m = merge

// SVE2-specific: arbitrary table lookup spanning multiple registers
tbl     z0.b, {z1.b, z2.b}, z3.b

// SVE2-specific: saturating multiply-high (codec dot product)
sqrdmulh z0.h, z1.h, z2.h
```

Predicates `p0..p15` replace masks. `p0` is conventionally "all true".
Inactive lanes either zero (`/z`) or keep their previous value (`/m`).

### SVE2 in ffmpeg: framework ready, kernels not yet upstream

As of mid-2026, ffmpeg has only **build-system plumbing** for SVE/SVE2
(Martin Storsjö's series, Sept 2024): `--disable-sve` / `--disable-sve2`
configure flags, `HAVE_SVE` / `HAVE_SVE2` defines, and `.arch_extension`
helpers in `aarch64/asm.S`. A direct check of `libavcodec/aarch64/`
finds zero `*_sve.S` or `*_sve2.S` files.

Real production SVE2 codec code lives in **dav1d 1.5 "Sonic"** (Jan 2025),
which added SVE2 implementations of HBD subpel filters and used the
6-tap `usmmla` instruction. If you're writing SVE2 for ffmpeg, look at
dav1d's `src/arm/64/` directory for prior art -- the macro framework
and predicate-discipline patterns there are battle-tested.

Gate via `have_sve(cpu_flags)` / `have_sve2(cpu_flags)` in
`*_init_aarch64.c`. Expect a higher review bar for the first SVE2
kernels in any ffmpeg subsystem.

## Apple Silicon vs Neoverse vs Snapdragon

The big practical splits:

| Target              | NEON throughput    | SVE/SVE2  | SME       | Notes                                                     |
| ------------------- | ------------------ | --------- | --------- | --------------------------------------------------------- |
| Apple M1/M2/M3      | excellent, wide ROB| no SVE    | no        | NEON only; very forgiving of dep chains                   |
| Apple M4 / M4 Pro   | excellent          | streaming-only | yes (512-bit tile, Streaming SVE2) | Non-streaming SVE2 traps; SVE2 only inside `smstart`/`smstop` |
| Neoverse N1         | NEON only          | no        | no        | Graviton2, older Ampere                                   |
| Neoverse V1         | SVE 256-bit        | yes       | no        | Graviton3                                                 |
| Neoverse V2         | SVE2 128-bit       | yes       | no        | Graviton4                                                 |
| Cortex-X / X2 / X3  | NEON               | SVE2 some | no        | Mobile flagship                                           |
| Snapdragon 8cx/X    | NEON               | SVE2 some | no        | Windows on ARM                                            |

Profile on the target. M-series and Neoverse have very different
in-order vs out-of-order behavior; what's optimal on one can be a
regression on another. If you must pick one, optimize for Neoverse V1+
(SVE-capable server) and provide a NEON-only fallback for Apple
Silicon parity.

### Apple SME caveat

M4 onward ship Armv9.2-A's **SME (Scalable Matrix Extension)** with
**Streaming SVE2** at 512-bit tile width. Subtleties for ffmpeg work:

- SVE2 instructions only execute inside an `smstart`/`smstop` region
  on Apple parts. Calling SVE2 from a normal NEON kernel traps with
  `EXC_BAD_INSTRUCTION`.
- Apple's official compute path is `Accelerate.framework`, which now
  backends to SME on M4+. ffmpeg has no Accelerate dependency.
- **Apple AMX** (the older matrix coprocessor on M1-M3) is undocumented
  and unstable across OS updates -- don't write to it directly.
  Apple has signaled they will remove it in a future SoC.

Practical advice: don't write Apple-SME-only kernels for ffmpeg. If you
write SVE2, gate it through ffmpeg's existing `have_sve2()` flag and
expect it to run on Neoverse V2 and Cortex-X4+, not Apple.

## 32-bit ARM legacy (`libav*/arm/`)

ffmpeg still maintains a 32-bit ARM (ARMv7 + NEON) port for embedded
targets. Different macro framework (`libavutil/arm/asm.S`), different
register set (`q0..q15` for 128-bit, `d0..d31` for 64-bit), and
different ABI (more callee-save registers).

For a new kernel, ask first whether the 32-bit version is required.
The answer is usually "no" unless the codec specifically targets
embedded -- but H.264 baseline, libopus, and a few mobile-flavored
codecs do still get 32-bit ARM contributions.

## Worked example: NEON yuv-to-rgb16 fast paths

A real merged patch in `libswscale/aarch64/yuv2rgb_neon.S` (May 2026,
3.3-4.7x speedup vs C on Apple M1) demonstrates several patterns at
once. Excerpted:

```asm
// Conditional callee-save: d8-d15 are AAPCS-64 callee-saved.
// Only spill if the output format actually needs them.
.if rgb16
    stp     d8, d9, [sp, #-0x10]!
.endif

// Macro-based format dispatch: the same kernel body services
// yuv420p / yuv422p / nv12 / nv21 / yuva420p by gating loads on .ifc.
.macro load_args_nv12 ofmt
    ldr     x8, [sp]                    // table pointer (stack arg)
    load_yoff_ycoeff 8, 16              // y_offset, y_coeff
.ifc \ofmt,rgb16
    sub     w3, w3, w0, lsl #1          // linesize - width*2 for 16bpp
.endif
.endm

// 16-bit RGB565 packing: shift-right + zero-extend + shift-left-insert
// chain, no scalar ops, all in vector registers.
.macro pack_rgb16 dst, low_ch, mid_ch, high_ch, g_shr, high_shl
    ushr    v20.8b,  \high_ch\().8b,  #3       // top 5 bits of high
    uxtl    \dst\().8h, v22.8b                 // zero-extend low channel
    sli     \dst\().8h, v23.8h, #5             // insert mid channel
    sli     \dst\().8h, v23.8h, #\high_shl     // insert high channel
.endm
```

Three transferable lessons:

1. **Conditional spills via `.if`/`.endif`** -- avoid paying stack-traffic
   cost for callee-saves in code paths that don't need them.
2. **Macro arg `.ifc` for format dispatch** -- one kernel source can
   service N input/output layouts. Cleaner than N near-identical
   functions, and the dispatch table can register all variants under
   their suffixed symbol names.
3. **`sli` (shift-left-insert) for bit-packing** -- folds the "shift the
   new field into place AND or-it-in" pair into one instruction. The
   AArch64 equivalent of x86's missing-piece for cheap field merging.

## Reviewer hot-buttons specific to AArch64

- Missing `endfunc` after `function` -- breaks symbol table
- Hand-written `ldr q0, ...` instead of `ld1 {v0.16b}, [...]` (less idiomatic)
- Use of `addv`/`uaddlv` on wider data than supported (check the manual)
- `tbl` source registers not consecutive (assembler will error)
- Predicate `/z` vs `/m` confusion in SVE code (zeroes vs preserves inactive lanes)
- New kernel without `have_sve2()` gate in `*_init_aarch64.c` for SVE2 code
- 32-bit ARM port missing for codecs that conventionally require it (ask first)
