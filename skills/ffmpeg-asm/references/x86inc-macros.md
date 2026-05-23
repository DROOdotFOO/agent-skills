---
title: x86inc.asm Macro Framework
impact: CRITICAL
impactDescription: Every x86 .asm file in libav* sits on top of x86inc.asm. Misusing these macros is the most common reviewer rejection reason and the most common source of cross-ABI bugs.
tags: x86inc, nasm, yasm, cglobal, abi, simd, macros, x86_64
---

# x86inc.asm Macro Framework

`libavutil/x86/x86inc.asm` is the shared macro layer for all ffmpeg x86
assembly. It handles ABI differences (System V vs Win64), register
allocation, AVX/SSE source sharing, and aligned memory section setup.
Companion file `libavutil/x86/x86util.asm` adds higher-level pixel and
arithmetic helpers (transposes, packed math).

## Function prologue: `cglobal`

```asm
; cglobal name, nargs, nregs [, scratch_regs]
;   nargs       -- number of incoming function arguments
;   nregs       -- number of named GPRs you'll use (r0..r{nregs-1})
;   scratch_regs (optional) -- additional named GPR names you want bound

INIT_XMM sse2
cglobal pixel_avg_w16, 4, 5, 8
    ; Arguments are now in r0..r3 regardless of ABI:
    ;   r0 = dst, r1 = src1, r2 = src2, r3 = stride
    ; r4 is a free scratch GPR
    ; m0..m7 are XMM registers (because INIT_XMM)
    ...
    RET
```

What `cglobal` actually does:

- Emits a global label with the correct symbol mangling (`ff_` prefix is conventional, often added via macros)
- Saves callee-saved registers required by the active ABI
- Reserves stack space for shadow store on Win64 (32 bytes) when needed
- Sets up `r0..r{nregs-1}` aliases so the source is ABI-agnostic

Use `RET` (not `ret`) to exit. `RET` restores callee-saved registers and,
inside an AVX `INIT_YMM`/`INIT_ZMM` block, emits `vzeroupper` to avoid
the AVX-to-SSE transition penalty.

## ISA gates: `INIT_XMM` / `INIT_YMM` / `INIT_ZMM`

These macros declare which vector ISA the following block compiles to,
and which register set the `m0..mN` aliases bind to.

```asm
INIT_XMM sse2     ; m0..m7 = xmm0..xmm7,  mnemonics emitted as SSE2
INIT_XMM ssse3    ; same regs, SSSE3 instructions available
INIT_XMM sse4     ; SSE4.1 instructions available
INIT_XMM avx      ; m0..m7 = xmm0..xmm7,  3-operand AVX encoding
INIT_YMM avx2     ; m0..m7 = ymm0..ymm7,  AVX2 instructions
INIT_ZMM avx512   ; m0..m7 = zmm0..zmm7,  AVX-512F+ instructions
```

The same source body can compile under multiple `INIT_*` blocks. This is
the entire point of x86inc -- you write the kernel once and instantiate
it for each ISA tier:

```asm
%macro AVG_W16_FN 0
cglobal pixel_avg_w16, 4, 5, 8
    mova    m0, [r1]
    pavgb   m0, [r2]
    mova    [r0], m0
    ...
    RET
%endmacro

INIT_XMM sse2
AVG_W16_FN
INIT_YMM avx2
AVG_W16_FN
```

You now have `ff_pixel_avg_w16_sse2` and `ff_pixel_avg_w16_avx2` from
one body.

## Register naming

- **GPRs**: `r0, r1, r2, ..., r6` -- ABI-mapped argument and scratch registers. Never write `rax`, `rdi`, `rsi` directly in cross-ABI code.
- **Vector regs**: `m0..m15` -- map to xmm/ymm/zmm based on the active `INIT_*`.
- **Explicit widths**: `xm0` always means `xmm0`, `ym0` always means `ymm0`, `zm0` always means `zmm0`. Use these when you need to mix widths (e.g. zero-extend from xmm to ymm).
- **High registers**: `m8..m15` only available with 64-bit ABIs. Gate with `%if num_mmregs >= 16` if a kernel needs to compile under x86-32 too.

## AVX/SSE 2-to-3 operand auto-rewrite

Under `INIT_XMM avx`, SSE-style 2-operand mnemonics are rewritten to
AVX 3-operand form automatically:

```asm
INIT_XMM avx
paddw   m0, m1          ; emitted as: vpaddw xmm0, xmm0, xmm1
pshufb  m0, m1          ; emitted as: vpshufb xmm0, xmm0, xmm1
```

This is what lets one macro body work as both `sse2` and `avx`. The
explicit AVX 3-operand form (`vpaddw m0, m1, m2`) is also valid but
breaks the cross-ISA sharing trick.

Hard rule: when writing for cross-ISA, use the SSE-style 2-operand
mnemonic. The macro takes care of AVX.

## `mova` / `movu` / `movh`

Width-agnostic move aliases:

| Macro  | Meaning                          | x86 mnemonic at INIT_XMM   | x86 mnemonic at INIT_YMM    |
| ------ | -------------------------------- | -------------------------- | --------------------------- |
| `mova` | aligned move, full width         | `movaps` / `movdqa`        | `vmovdqa` / `vmovaps`       |
| `movu` | unaligned move, full width       | `movups` / `movdqu`        | `vmovdqu`                   |
| `movh` | half-register (low 64 bits)      | `movq`                     | `vmovq`                     |
| `movd` | doubleword (low 32 bits)         | `movd`                     | `vmovd`                     |

Use `mova` when you can prove alignment (typically frame buffer rows
with known stride alignment). Use `movu` for unaligned loads (decoder
bitstreams, sub-pixel offset reads). Misuse of `mova` on an unaligned
address segfaults on older CPUs and is slower than `movu` on newer ones
without the safety.

## Read-only constants: `SECTION_RODATA`

```asm
SECTION_RODATA 32           ; 32-byte alignment for AVX2 loads

pw_1:      times 16 dw 1
pw_512:    times 16 dw 512
pd_0_4:    dd 0, 4, 0, 4, 0, 4, 0, 4
mask_lsb:  times 32 db 0x01

SECTION .text
```

The trailing number is the alignment in bytes. For AVX2 use 32, for
AVX-512 use 64. `SECTION .text` returns to code. The `times N` form
replicates the literal; `dw` / `dd` / `dq` are word, dword, qword.

Reference the table by label: `mova m4, [pw_1]`. Inside a function with
PIC, you may need `[rel pw_1]` (`x86inc` typically handles PIC; check
existing files in the same subsystem for convention).

## CPU feature gates inside macros

Branch on `cpuflag()` inside a macro to select between paths:

```asm
%macro PACK_DIFFS 0
%if cpuflag(ssse3)
    pshufb  m0, [shuf_mask]
%else
    pand    m0, [pb_0f]
    packuswb m0, m1
%endif
%endmacro
```

`cpuflag(ssse3)` is true only when the current `INIT_*` block is at
SSSE3 or higher. This avoids invalid instructions in older ISA
instantiations while sharing the macro body.

## Assembler portability

Source must build with both NASM and YASM. Avoid:

- NASM-only macros (`%substr`, `%strlen` post-NASM-2.x extensions if you target older YASM)
- `default rel` toggling mid-file
- Comments with `;;` followed by `%` (some YASM versions misparse)

Use `make` from a clean tree with `--cc=clang` and `--cc=gcc` and verify
the asm assembles in both NASM and YASM. The configure system tells you
which assembler is in use:

```bash
./configure --x86asmexe=nasm | grep "x86 assembler"
./configure --x86asmexe=yasm | grep "x86 assembler"
```

## Function name decoration

`cglobal foo` typically emits a symbol named `ff_foo_<suffix>` where
`<suffix>` is `sse2`, `avx2`, etc., derived from the active `INIT_*`.
The dispatch table in `*_init.c` references the C-visible name:

```c
extern void ff_pixel_avg_w16_sse2(uint8_t *dst, const uint8_t *src1,
                                  const uint8_t *src2, ptrdiff_t stride);
extern void ff_pixel_avg_w16_avx2(uint8_t *dst, const uint8_t *src1,
                                  const uint8_t *src2, ptrdiff_t stride);
```

See `references/dispatcher-init.md` for how these get wired into the DSP
context.

## Reviewer hot-buttons specific to x86inc

- 2-operand SSE-style mnemonic when AVX 3-operand explicit form was needed (or vice versa)
- Hand-typed `xmm0`/`ymm0` instead of `m0`/`xm0`/`ym0`
- Missing `RET` (using bare `ret` skips `vzeroupper` and callee-save restore)
- New constants in code section instead of `SECTION_RODATA`
- `mova` on possibly-unaligned address -- prove it or use `movu`
- Forgetting `INIT_*` reset between functions (state leaks across `cglobal` blocks)
