---
title: Building ffmpeg and Embedding libav*
impact: HIGH
impactDescription: ./configure and the libav* C API are the surface where your asm work meets the outside world. Custom minimal builds and language-binding pitfalls live here.
tags: configure, build, embedding, libavcodec, pkg-config, rust, elixir, go, gpl, lgpl
---

# Building ffmpeg and Embedding libav*

ffmpeg's `./configure` is a single 7000-line shell script. It's not
autoconf -- it's hand-rolled and behaves slightly differently. This
file covers the flags you'll actually use and the surface for
embedding libav* into your own application.

## Configure essentials

```bash
./configure \
    --prefix=/opt/ffmpeg \
    --enable-shared \
    --disable-static \
    --enable-pic \
    --enable-gpl \
    --enable-libx264 \
    --enable-libx265 \
    --enable-libvpx \
    --enable-libopus \
    --extra-cflags="-O3 -march=native" \
    --extra-ldflags="-Wl,-rpath,/opt/ffmpeg/lib"
make -j$(nproc)
make install
```

Common flags:

| Flag                          | Purpose                                              |
| ----------------------------- | ---------------------------------------------------- |
| `--prefix=PATH`               | Install root                                         |
| `--enable-shared`             | Build `.so`/`.dylib`/`.dll` libraries                |
| `--disable-static`            | Skip `.a` static archives                            |
| `--enable-pic`                | Position-independent code (required for shared lib)  |
| `--enable-gpl`                | Allow GPL components (x264, x265, etc.)              |
| `--enable-version3`           | Allow LGPLv3 / GPLv3 components                      |
| `--enable-nonfree`            | Allow non-redistributable components (FDK-AAC etc.)  |
| `--enable-lib*`               | Enable external library (e.g. `--enable-libx264`)    |
| `--disable-doc`               | Skip docs build                                      |
| `--disable-debug`             | Strip debug symbols                                  |
| `--cross-prefix=PFX`          | Cross-compile toolchain prefix (`aarch64-linux-gnu-`)|
| `--target-os=OS`              | Target OS (linux, darwin, mingw32, android, ios)     |
| `--arch=ARCH`                 | Target arch (x86_64, aarch64, arm, riscv64)          |
| `--cpu=CPU`                   | Target microarchitecture (`generic`, `znver3`)       |
| `--enable-lto`                | Link-time optimization                               |
| `--x86asmexe=PATH`            | Use specific assembler (nasm or yasm)                |

License gotcha: `--enable-gpl` is **sticky**. Once enabled, the
resulting binary is GPL, and any application that links it dynamically
or statically inherits GPL distribution obligations. For LGPL
distribution (closed-source apps embedding ffmpeg), leave `--enable-gpl`
off and pick LGPL-compatible codecs only.

## Minimal builds

For an app that needs only H.264 decode + MP4 demux:

```bash
./configure \
    --prefix=/opt/ffmpeg-minimal \
    --disable-everything \
    --enable-shared --disable-static --enable-pic \
    --enable-decoder=h264 \
    --enable-demuxer=mov \
    --enable-protocol=file \
    --enable-parser=h264 \
    --disable-doc --disable-programs
```

`--disable-everything` disables every codec/demuxer/muxer/protocol;
re-enable only the ones you need. Result: ~5MB libav* instead of ~50MB.

To see what's enabled:

```bash
./configure --list-decoders | grep h264
./configure --list-demuxers | grep mov
./configure --list-protocols
```

## pkg-config

After install, libraries register with `pkg-config`:

```bash
pkg-config --cflags libavcodec libavformat libavutil libswscale libswresample
# -> -I/opt/ffmpeg/include

pkg-config --libs libavcodec libavformat libavutil libswscale libswresample
# -> -L/opt/ffmpeg/lib -lavcodec -lavformat -lavutil -lswscale -lswresample
```

Set `PKG_CONFIG_PATH=/opt/ffmpeg/lib/pkgconfig` if not in default
search.

## Calling libav* from C

```c
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>

int main(int argc, char **argv) {
    AVFormatContext *fmt_ctx = NULL;
    if (avformat_open_input(&fmt_ctx, argv[1], NULL, NULL) < 0) return 1;
    if (avformat_find_stream_info(fmt_ctx, NULL) < 0) return 1;

    int vid_stream = av_find_best_stream(fmt_ctx, AVMEDIA_TYPE_VIDEO, -1, -1, NULL, 0);
    AVCodecParameters *par = fmt_ctx->streams[vid_stream]->codecpar;
    const AVCodec *codec = avcodec_find_decoder(par->codec_id);
    AVCodecContext *ctx = avcodec_alloc_context3(codec);
    avcodec_parameters_to_context(ctx, par);
    avcodec_open2(ctx, codec, NULL);

    AVPacket *pkt = av_packet_alloc();
    AVFrame *frame = av_frame_alloc();

    while (av_read_frame(fmt_ctx, pkt) >= 0) {
        if (pkt->stream_index == vid_stream) {
            avcodec_send_packet(ctx, pkt);
            while (avcodec_receive_frame(ctx, frame) == 0) {
                // frame->data[0..3], frame->linesize[0..3]
                av_frame_unref(frame);
            }
        }
        av_packet_unref(pkt);
    }

    av_frame_free(&frame);
    av_packet_free(&pkt);
    avcodec_free_context(&ctx);
    avformat_close_input(&fmt_ctx);
    return 0;
}
```

Critical lifecycle rules:

- Every `av_*_alloc()` needs a matching `av_*_free()`
- `av_frame_unref` / `av_packet_unref` resets but keeps the allocation
- `av_frame_free` / `av_packet_free` releases the allocation
- `avcodec_send_packet` may return `AVERROR(EAGAIN)` -- means "drain receive_frame first"
- Reference counting via `av_buffer_ref` / `av_buffer_unref` for zero-copy frame sharing

## Rust: `rsmpeg` (active) or `ffmpeg-next` (maintenance)

Two main options:

- **`rsmpeg`** (`larksuite/rsmpeg`) -- actively developed, supports
  ffmpeg 6.x and 7.x, MSRV 1.81. Preferred for new projects.
- **`ffmpeg-next`** -- mature, broad version support (ffmpeg 3.4 through
  8.0), now in **maintenance mode**. Pick if you need legacy ffmpeg
  version support or already have code on it.

```toml
# Cargo.toml -- rsmpeg
[dependencies]
rsmpeg = { version = "0.15", features = ["link_system_ffmpeg"] }
```

```rust
use rsmpeg::avformat::AVFormatContextInput;
use rsmpeg::avcodec::AVCodecContext;
use rsmpeg::error::RsmpegError;

fn main() -> Result<(), RsmpegError> {
    let mut ictx = AVFormatContextInput::open(c"input.mp4", None, &mut None)?;
    let (video_stream_index, decoder) = {
        let (idx, stream) = ictx
            .streams()
            .iter()
            .enumerate()
            .find(|(_, s)| s.codecpar().codec_type == rsmpeg::ffi::AVMEDIA_TYPE_VIDEO)
            .unwrap();
        let decoder = AVCodecContext::find_decoder(stream.codecpar().codec_id).unwrap();
        (idx, decoder)
    };
    // ... send_packet / receive_frame loop similar to C
    Ok(())
}
```

```toml
# Cargo.toml -- ffmpeg-next (if you need the older API)
[dependencies]
ffmpeg-next = "8"
```

Both crates require the system ffmpeg dev headers + libs. Set
`PKG_CONFIG_PATH` if using a non-system install. `ffmpeg-sys-next` is
the lower-level raw FFI crate underneath `ffmpeg-next`; `rsmpeg-sys`
plays the same role for `rsmpeg`.

build.rs pitfall: cross-compiling needs `PKG_CONFIG_SYSROOT_DIR` and a
matching cross-pkg-config. Easier path is to vendor the libs in a
known directory and use `--extra-link-arg` via `RUSTFLAGS`.

## Elixir: NIF wrapper

For BEAM integration, write a thin C or Rust NIF that holds an
`AVCodecContext` in a resource:

```c
// my_decoder.c (Rustler equivalent works similarly)
#include <erl_nif.h>
#include <libavcodec/avcodec.h>

static ErlNifResourceType *decoder_type;

typedef struct {
    AVCodecContext *ctx;
} Decoder;

static void decoder_dtor(ErlNifEnv *env, void *obj) {
    Decoder *d = obj;
    if (d->ctx) avcodec_free_context(&d->ctx);
}

// decode_packet/2 NIF -- send packet, return frame or :again
static ERL_NIF_TERM decode_packet(ErlNifEnv *env, int argc, const ERL_NIF_TERM argv[]) {
    Decoder *d;
    if (!enif_get_resource(env, argv[0], decoder_type, (void**)&d)) {
        return enif_make_badarg(env);
    }
    // ... binary -> AVPacket, avcodec_send_packet, avcodec_receive_frame
    // Use dirty NIF: decoding 1080p H.264 frame is well over 1ms
}
```

Critical: decode steps frequently exceed the BEAM 1ms scheduler budget.
Mark the NIF as `ERL_NIF_DIRTY_JOB_CPU_BOUND` or scheduler starvation
follows. See `native-code` for the BEAM boundary discipline (resource
types, dirty schedulers, panic safety, memory ownership).

## Go: `goav` / cgo

```go
// #cgo pkg-config: libavcodec libavformat libavutil
// #include <libavcodec/avcodec.h>
// #include <libavformat/avformat.h>
import "C"
```

cgo bridges have a per-call overhead (~50-200ns). For tight inner
loops, batch many libav* calls in one cgo trip rather than crossing
the boundary per frame. Static linking on Go is fiddly -- set
`CGO_LDFLAGS=-static -lavcodec ...` and confirm with `ldd`.

`goav` (the popular wrapper) is somewhat dormant; the lower-level
direct cgo approach is more common for fresh code.

## libav fork: archived

ffmpeg forked from libav in 2011, then libav declined and is now
**fully archived** -- the `libav.org` domain no longer resolves and the
mailing list is closed. Modern advice to "build against libav" is
stale; everything you'd want lives in ffmpeg today. Use ffmpeg
exclusively.

Headers like `<libavcodec/avcodec.h>` are the ffmpeg paths -- they
happened to match libav's during the shared-API era, which is why
old build instructions sometimes still mention libav. Treat any libav
reference in 2026 documentation as historical.

## License accounting

| Component        | License                                              |
| ---------------- | ---------------------------------------------------- |
| libavutil        | LGPLv2.1+                                            |
| libavcodec       | LGPLv2.1+ (parts GPL if `--enable-gpl`)              |
| libavformat      | LGPLv2.1+                                            |
| libavfilter      | LGPLv2.1+ (parts GPL)                                |
| libswscale       | LGPLv2.1+                                            |
| libswresample    | LGPLv2.1+                                            |
| libavdevice      | LGPLv2.1+                                            |
| libpostproc      | GPLv2+ (always GPL, gated on `--enable-gpl`)         |
| x264, x265       | GPLv2+ (requires `--enable-gpl --enable-libx264`)    |
| FDK-AAC          | non-free (requires `--enable-nonfree`)               |
| OpenH264         | BSD                                                  |

For closed-source distribution: don't pass `--enable-gpl` or
`--enable-nonfree`. Inspect `./configure` output near the end -- it
prints "License: LGPL", "License: GPL", or "License: non-free" based
on what got enabled.

## Common pitfalls specific to build/integration

- `--enable-gpl` enabled "by default" because someone copy-pasted, then app needs LGPL distribution
- Missing `--enable-pic` on a shared-lib build -> link failure
- pkg-config not finding the build because `PKG_CONFIG_PATH` not set
- Mixing system libav* headers with custom-build libraries (ABI skew)
- cgo Go binaries hitting unexpected runtime symbol lookups -- check `LD_LIBRARY_PATH`
- Rust `ffmpeg-next` version mismatch with system ffmpeg (e.g. crate v7 expects ffmpeg 7.x)
- Forgetting `av_*_unref` between frames -> memory growth proportional to frames decoded
- Static linking on Go without `CGO_LDFLAGS` properly setting `-static` and full lib list
