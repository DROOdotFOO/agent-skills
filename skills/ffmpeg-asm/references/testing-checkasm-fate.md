---
title: Testing with checkasm and FATE
impact: HIGH
impactDescription: byte-exact verification and cycle-accurate benchmarking. A kernel without checkasm coverage doesn't ship; FATE keeps the whole codec pipeline honest.
tags: checkasm, fate, testing, byte-exact, benchmark, tdd, verification
---

# Testing: checkasm + FATE

ffmpeg has two complementary test harnesses:

- **checkasm** -- per-function byte-exact and benchmark harness, lives in `tests/checkasm/`
- **FATE** (Fast Audio Video Evaluation) -- end-to-end codec regression suite against reference output, lives in `tests/fate/`

A new asm kernel needs a checkasm test in the same patch. A new codec
or container feature needs a FATE entry. See `tdd` for the
red/green/refactor discipline that maps naturally onto checkasm.

## checkasm overview

```
tests/checkasm/
  checkasm.c         -- top-level harness
  checkasm.h         -- declare_func, check_func, report macros
  h264dsp.c          -- per-subsystem test file
  hevcdsp.c
  vp9dsp.c
  ...
```

Build and run:

```bash
./configure ...
make checkasm
tests/checkasm/checkasm                       # run all tests
tests/checkasm/checkasm h264dsp               # single subsystem
tests/checkasm/checkasm --test=h264dsp_idct4  # specific test
tests/checkasm/checkasm --bench=h264dsp_idct  # benchmark mode
```

## Writing a checkasm test

```c
/* tests/checkasm/mydsp.c */
#include "checkasm.h"
#include "libavcodec/mydsp.h"
#include "libavutil/mem_internal.h"

#define randomize_buffers(buf, len)            \
    do {                                       \
        for (int i = 0; i < (len); i++)        \
            (buf)[i] = rnd();                  \
    } while (0)

static void check_add_pixels16(void)
{
    LOCAL_ALIGNED_32(uint8_t, dst_c,   [16 * 16]);
    LOCAL_ALIGNED_32(uint8_t, dst_asm, [16 * 16]);
    LOCAL_ALIGNED_32(int16_t, src,     [16 * 16]);

    MyDSPContext ctx;
    ff_mydsp_init(&ctx);

    declare_func(void, uint8_t *, const int16_t *, ptrdiff_t);

    if (check_func(ctx.add_pixels16, "add_pixels16")) {
        randomize_buffers(src, 16 * 16);
        memset(dst_c,   0, 16 * 16);
        memset(dst_asm, 0, 16 * 16);

        call_ref(dst_c,   src, 16);
        call_new(dst_asm, src, 16);

        if (memcmp(dst_c, dst_asm, 16 * 16))
            fail();

        bench_new(dst_asm, src, 16);
    }
    report("add_pixels");
}

void checkasm_check_mydsp(void)
{
    check_add_pixels16();
    /* check more functions here */
}
```

Then register the entry point in `tests/checkasm/checkasm.c`:

```c
// add to the list_of_tests array
{ "mydsp",   checkasm_check_mydsp },
```

And add the file to `tests/checkasm/Makefile`:

```makefile
AVCODECOBJS-$(CONFIG_MYDSP) += mydsp.o
```

## checkasm macros explained

- `declare_func(ret_type, arg_types...)` -- declares `call_ref` and `call_new` function pointers with the given signature
- `check_func(impl, "name")` -- returns true if the implementation differs from the C reference (i.e. there's an asm version to test). The string is the test label.
- `call_ref(args...)` -- invokes the C reference implementation
- `call_new(args...)` -- invokes the implementation chosen by dispatch (your asm)
- `fail()` -- mark the current test as failed
- `bench_new(args...)` -- run the asm impl in a loop for cycle measurement
- `report(label)` -- emit results for the current group; call after each `check_func` block

## Byte-exact discipline

The C reference is the oracle. Your asm output must be **identical**
byte-for-byte for all valid inputs. "Close enough" fails review.

```c
// WRONG -- floating-point fuzz tolerance has no place in pixel data
if (abs(dst_c[i] - dst_asm[i]) > 1) fail();

// RIGHT -- byte-exact memcmp
if (memcmp(dst_c, dst_asm, size)) fail();
```

If a kernel uses floating-point intermediate values (rare in codec DSP,
common in audio), use the codec spec's rounding rules to derive the
expected output, not an `abs() < epsilon` check.

## Edge case coverage

Random input is necessary but not sufficient. Add explicit edge-case
inputs:

```c
// Zero block (lots of codec paths special-case this)
memset(src, 0, sizeof src);
call_ref(dst_c, src, stride);
call_new(dst_asm, src, stride);
if (memcmp(dst_c, dst_asm, dst_size)) fail();

// Saturated extremes
for (int i = 0; i < src_count; i++) src[i] = INT16_MAX;
call_ref(...); call_new(...); ...

for (int i = 0; i < src_count; i++) src[i] = INT16_MIN;
call_ref(...); call_new(...); ...

// Misaligned source (stride boundary cases)
randomize_buffers(src, src_count);
call_ref(dst_c   + 1, src + 1, stride);
call_new(dst_asm + 1, src + 1, stride);
if (memcmp(dst_c + 1, dst_asm + 1, dst_size - 1)) fail();
```

Random input misses saturating boundaries and zero-block fast paths.
Cover them explicitly.

## Benchmarking with `--bench`

```bash
tests/checkasm/checkasm --bench=h264dsp_idct
```

Output:

```
checkasm: using random seed 12345678
h264dsp.idct_add_c:           160.5
h264dsp.idct_add_sse2:         42.1
h264dsp.idct_add_avx:          39.8
h264dsp.idct_add_avx2:         28.3
```

Numbers are cycles per call (median across many runs). The harness
takes care of:

- Pinning to a core, disabling frequency scaling
- Warming up icache and dcache
- Median-of-N to reject outliers

Caveat: cycle counts are reproducible on the same machine, not
portable. Compare improvements on the same CPU.

## Differential build for regression hunting

When a checkasm failure appears, narrow the suspect tier:

```bash
# Build with all asm enabled
./configure ...
make checkasm
tests/checkasm/checkasm           # fails on h264dsp_idct_avx2

# Build with AVX2 disabled
./configure --disable-avx2 ...
make checkasm
tests/checkasm/checkasm           # passes -> bug is in AVX2 kernel

# Or use runtime flags without rebuilding
tests/checkasm/checkasm -cpuflags +sse2     # force baseline
tests/checkasm/checkasm -cpuflags +avx      # add AVX
tests/checkasm/checkasm -cpuflags +avx2     # add AVX2
```

`--disable-asm` builds the pure-C reference for comparison
ground-truth. Combine with `make fate-h264` to confirm a real-world
file decodes correctly with no asm at all.

## FATE: end-to-end suite

```bash
make fate-rsync                       # download sample files (~3GB)
make fate                             # run full suite (~hour)
make fate-h264                        # codec-specific subset
make fate-list                        # list every test target
make THREADS=8 fate                   # parallel run
```

FATE tests:

- Decode a known input, compare output md5 to expected reference
- Run a filter graph, compare to reference
- Run an encoder, decode the result, verify

A FATE failure means somebody's asm or C path produced different bytes
than expected for a real codec stream. Bisect with `git bisect run
make fate-h264`.

## Adding a FATE entry

For a new codec test:

```makefile
# tests/fate/<codec>.mak

FATE_<CODEC> += fate-<codec>-myfile
fate-<codec>-myfile: CMD = framecrc -i $(TARGET_SAMPLES)/<codec>/myfile.bin
```

Then add the expected reference output under `tests/ref/fate/<codec>-myfile`
(generate with `make fate-<codec>-myfile GEN=1`).

Sample files go in the `fate-suite` repository (separate from main
ffmpeg repo). Upload via maintainer or attach to the patch email.

## checkasm vs FATE: when to use each

| Need                                       | Harness          |
| ------------------------------------------ | ---------------- |
| Test a single DSP kernel in isolation      | checkasm         |
| Byte-exact match against C reference       | checkasm         |
| Cycle benchmark a single function          | checkasm `--bench` |
| End-to-end codec on a real stream          | FATE             |
| Catch regressions across the whole pipeline| FATE             |
| Bisect a "video looks corrupted" bug       | FATE then checkasm to localize |

A new asm kernel needs **both**: checkasm to prove the kernel itself
is correct, FATE (existing tests are usually sufficient) to prove
nothing broke at the codec level.

## Common pitfalls specific to testing

- New kernel without a checkasm test (reviewer rejection guaranteed)
- checkasm test missing edge cases (zero block, saturation, misalignment)
- "Close enough" tolerance instead of `memcmp`
- `bench_new` outside `check_func` block (timing without correctness check)
- Forgetting to register new `checkasm_check_*` in `checkasm.c` list
- Forgetting to add the `.c` file to `tests/checkasm/Makefile`
- FATE failure ignored as "flaky" -- it's deterministic, dig in
- Using `--bench` to compare improvements across different machines
