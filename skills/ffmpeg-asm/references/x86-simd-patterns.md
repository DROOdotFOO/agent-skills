---
title: x86_64 SIMD Patterns (SSE through AVX-512)
impact: HIGH
impactDescription: Working idioms for hot-path pixel and bitstream code on x86_64. Covers alignment, transposes, reductions, AVX-512 mask discipline, and the AVX-to-SSE transition penalty.
tags: x86, simd, sse, avx, avx2, avx512, vzeroupper, transpose, pixel-ops
---

# x86_64 SIMD Patterns

Working idioms for kernels in `libav*/x86/`. Assumes the reader knows
`x86inc.asm` macros (`mova`, `m0`, `INIT_XMM/YMM/ZMM`, etc.) -- see
`references/x86inc-macros.md`.

## Aligned vs unaligned loads

```asm
mova    m0, [r0]          ; aligned, faster on older CPUs, segfaults if r0 not aligned to reg width
movu    m0, [r0]          ; unaligned, always safe, equal-perf on Skylake+
```

Pixel data is typically aligned to row stride. Common ffmpeg strides
are multiples of 16 or 32 -- so XMM `mova` is usually safe, YMM `mova`
may not be unless the buffer was allocated with `av_malloc` (which
guarantees `AV_INPUT_BUFFER_PADDING_SIZE`-byte alignment, currently 64).
Bitstream reads are typically unaligned -- always `movu`.

Rule of thumb: prove alignment from the calling C code, or use `movu`.
Reviewer will ask you to prove it.

## Transpose patterns

### 4x4 16-bit transpose (SSE2)

Building block for DCT/IDCT row->column passes.

```asm
; Input:  m0 = a0 a1 a2 a3, m1 = b0 b1 b2 b3, m2 = c0 c1 c2 c3, m3 = d0 d1 d2 d3
;         (each register holds 4 x int16 + 4 x garbage, or 8 x int16 if packed)
; Output: m0 = a0 b0 c0 d0, m1 = a1 b1 c1 d1, m2 = a2 b2 c2 d2, m3 = a3 b3 c3 d3

punpcklwd   m4, m0, m1     ; a0 b0 a1 b1 a2 b2 a3 b3 (low quartet of each merged)
punpckhwd   m5, m0, m1     ; a4 b4 a5 b5 a6 b6 a7 b7  (high quartet)
punpcklwd   m6, m2, m3
punpckhwd   m7, m2, m3
punpckldq   m0, m4, m6
punpckhdq   m1, m4, m6
punpckldq   m2, m5, m7
punpckhdq   m3, m5, m7
```

For 8x8 16-bit transpose, do 4x4 on each quadrant then merge with
`punpcklqdq`/`punpckhqdq`. `x86util.asm` provides `TRANSPOSE4x4W` and
`TRANSPOSE8x8W` macros -- prefer those.

### AVX2 lane-crossing gotcha

AVX2 256-bit shuffles operate on two independent 128-bit lanes:

```asm
INIT_YMM avx2
vpshufb  m0, m0, m1       ; shuffles lanes [0:127] and [128:255] INDEPENDENTLY
                          ; cannot move bytes between lanes!
```

To cross lanes you need `vperm2i128`, `vpermq`, `vpermd`, or `vpermps`:

```asm
vperm2i128  m0, m0, m1, 0x20    ; pick low lane of m0 and low lane of m1
vpermq      m0, m0, q3120        ; reorder 64-bit chunks across both lanes
```

This is the #1 silent-wrong-output bug when porting SSE kernels to AVX2.
Re-derive the shuffle masks; don't assume the SSE2 pattern doubles.

## Horizontal reductions

For sums-of-absolute-differences, dot products, SAD/SATD:

```asm
; Sum 8 int32 lanes in m0 down to scalar in r0d
; (works for XMM = 4 lanes, YMM = 8 lanes; for YMM, fold high to low first)
%if mmsize == 32
    vextracti128  xm1, m0, 1
    paddd         xm0, xm1
%endif
pshufd        xm1, xm0, q3232       ; bring high 64 to low 64
paddd         xm0, xm1
pshufd        xm1, xm0, q0001       ; bring high 32 of remaining low 64
paddd         xm0, xm1
movd          r0d, xm0
```

The `phadd*` family looks attractive but has terrible latency (~6 cycles
each). The explicit shuffle-add chain above is faster on every modern
microarchitecture.

## Gather / scatter -- avoid in hot paths

`vpgatherdd`, `vgatherdps`, etc. are correct but slow even on
Skylake-class CPUs (~20 cycles per gather, no real speedup vs a manual
loop). Prefer:

```asm
; Equivalent of gather with constant stride: just do strided loads
movd        xm0, [r0]
pinsrd      xm0, [r0 + r1], 1
pinsrd      xm0, [r0 + r1*2], 2
pinsrd      xm0, [r0 + r2], 3       ; r2 = stride*3 precomputed
```

For truly arbitrary indices, the manual unrolled loop is usually faster
than `vpgatherdd`. AVX-512 `vpgatherdd` is somewhat better but still
rarely a win.

## AVX-512: mask registers and embedded broadcast

AVX-512 adds 8 mask registers (`k0..k7`) used for predicated
operations. `k0` is special -- writing to it has no effect, reading
returns "all ones".

```asm
INIT_ZMM avx512
; Compare 64 bytes, build a mask
vpcmpb      k1, m0, m1, 0           ; k1 = bitmask where m0 == m1 (per-byte)
; Conditional store using mask
vmovdqu8    [r0]{k1}, m2            ; only store bytes where k1 bit is set
; Zero-masking variant: set masked-out lanes to zero
vmovdqa32   m3{k1}{z}, m4           ; m3 = m4 where k1 set, 0 elsewhere
```

Embedded broadcast lets you fold a scalar load into an arithmetic op:

```asm
vpaddd      m0, m1, [rip + scalar]{1to16}    ; broadcast 32-bit scalar to all 16 lanes
```

The `{1to16}` syntax means "broadcast one dword to 16 lanes". Saves a
separate broadcast load and stays in the same uop.

## VZEROUPPER discipline

The historical Sandy Bridge / Ivy Bridge / Haswell / Broadwell model
penalized AVX-to-SSE transitions with a ~70-cycle save/restore. **That
specific penalty is gone on Skylake and later.** What remains on
Skylake-class Intel:

- Non-VEX SSE instructions running while YMM/ZMM upper halves are
  "dirty" pay a per-instruction false dependency + blend uop (single
  digit cycles each, accumulates in loops).
- AVX-512 leaves ZMM upper halves dirty in the same way.

On AMD Zen through Zen5, upper halves are tracked per-register; no
Intel-style transition penalty exists, but a non-VEX SSE write into a
register with dirty upper bits creates a merge dependency.

Either way: emit `vzeroupper` at the function exit boundary of any
AVX/AVX-512 kernel. The `RET` macro inside an `INIT_YMM` / `INIT_ZMM`
block emits it automatically.

```asm
INIT_YMM avx2
cglobal mykernel, 3, 4, 8
    ...
    RET                ; -> emits vzeroupper; ret

; If you have multiple exit points, use RET at each one, not bare ret:
INIT_YMM avx2
cglobal mykernel2, 3, 4, 8
    test    r0, r0
    jz      .done
    ...
.done:
    RET                ; <-- correct, even for early exits
```

Never use bare `ret` inside an AVX block. Reviewer will catch it.

## VEX vs EVEX encoding

- VEX = AVX/AVX2 3-operand encoding, accesses XMM/YMM
- EVEX = AVX-512 encoding, accesses ZMM and mask regs

`INIT_YMM avx2` emits VEX. `INIT_ZMM avx512` emits EVEX. EVEX has a
slightly longer encoding (so larger code size) but no perf delta on
the same instruction.

Mixing matters only at the function exit boundary -- VZEROUPPER zeroes
the upper bits of all YMM/ZMM regs and clears the dirty-state tracking
so an SSE caller doesn't pay the penalty.

## Common pixel-op idioms

### Saturating pack to bytes (`packuswb` / `packusdw`)

```asm
; m0, m1 hold 8 x int16 each, signed. We want 16 x uint8 clipped to [0, 255].
packuswb    m0, m1          ; saturates negative -> 0, >255 -> 255
```

Saturation is implicit and free -- no need for explicit `min`/`max`
clamps before pack. The unsigned-saturating pack is the entire point.

### Unsigned arithmetic and the no-overflow trick

To average two unsigned bytes without carry leak:

```asm
pavgb       m0, m1          ; (m0 + m1 + 1) >> 1, all lanes, no overflow
```

Half a dozen pixel-format conversions rely on this.

### Multiply-add accumulate

```asm
; pmaddwd: multiply pairs of int16, accumulate horizontally to int32
;   m0 = a0 a1 a2 a3 a4 a5 a6 a7 (int16)
;   m1 = b0 b1 b2 b3 b4 b5 b6 b7 (int16)
;   result = (a0*b0 + a1*b1) (a2*b2 + a3*b3) (a4*b4 + a5*b5) (a6*b6 + a7*b7) -- 4 x int32
pmaddwd     m0, m1
```

Heavily used in IDCT and filtering kernels.

## Profiling individual kernels

Before reaching for AVX-512 or chasing micro-optimizations, profile.
See `performance-profiler` for the higher-level workflow. For asm
hot-path tuning specifically:

```bash
# checkasm --bench gives cycle counts per function
make checkasm
tests/checkasm/checkasm --bench=h264dsp_idct
```

`uica.uops.info` and `llvm-mca` let you analyze a code sequence for
front-end / port pressure without running it. Useful for choosing
between two equally-correct sequences.

## Reviewer hot-buttons specific to x86 SIMD

- `mova` on unaligned address (prove alignment or use `movu`)
- AVX2 lane-crossing assumed to work like SSE shuffle
- `phaddw`/`phaddd` chain in a hot loop (use shuffle-add)
- `vpgatherdd` in a hot loop (use unrolled strided loads)
- AVX-512 kernel gated on `EXTERNAL_AVX512` when `EXTERNAL_AVX512ICL` was needed for VBMI2 / cross-lane byte permutes / GFNI
- Missing `RET` (bare `ret`) inside `INIT_YMM` or `INIT_ZMM`
- Hand-typed `vpaddw m0, m0, m1` when the cross-ISA macro wanted `paddw m0, m1`
