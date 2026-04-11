---
title: Per-Language Profiling Tools
impact: HIGH
impactDescription: correct tool selection determines whether you find the real bottleneck
tags: flamegraph, pprof, py-spy, fprof, criterion, clinic, telemetry
---

# Per-Language Profiling Tools

## Node.js / TypeScript

| Tool         | What it measures          | When to use                          |
| ------------ | ------------------------- | ------------------------------------ |
| `--prof`     | V8 CPU ticks              | Quick CPU profiling                  |
| clinic.js    | CPU, memory, event loop   | Comprehensive Node diagnostics       |
| 0x           | Flamegraphs               | Visual CPU hotspot identification    |
| `--inspect`  | Chrome DevTools profiler  | Interactive debugging                |

```bash
# Generate flamegraph with 0x
npx 0x -- node server.js
# Clinic.js doctor (event loop, GC, CPU)
npx clinic doctor -- node server.js
```

## Python

| Tool         | What it measures          | When to use                          |
| ------------ | ------------------------- | ------------------------------------ |
| py-spy       | CPU sampling (no overhead)| Production-safe profiling            |
| cProfile     | Function call counts/time | Development profiling                |
| memray       | Memory allocations        | Memory leak detection                |
| scalene      | CPU + memory + GPU        | Multi-dimensional profiling          |

```bash
# py-spy flamegraph (attach to running process)
py-spy record -o profile.svg --pid $PID
# cProfile with sorting
python -m cProfile -s cumtime app.py
```

## Go

| Tool         | What it measures          | When to use                          |
| ------------ | ------------------------- | ------------------------------------ |
| pprof (CPU)  | CPU time by function      | Always the first tool to reach for   |
| pprof (heap) | Memory allocations        | Suspected memory issues              |
| pprof (block)| Goroutine blocking        | Concurrency bottlenecks              |
| trace        | Execution trace           | Scheduler and GC analysis            |

```go
import _ "net/http/pprof"
// Visit http://localhost:6060/debug/pprof/
```

```bash
go tool pprof -http=:8080 http://localhost:6060/debug/pprof/profile?seconds=30
```

## Elixir

| Tool         | What it measures          | When to use                          |
| ------------ | ------------------------- | ------------------------------------ |
| :fprof       | Function call time        | Detailed per-function analysis       |
| :eprof       | Time per process          | Finding hot processes                |
| :observer    | System overview (GUI)     | Live system inspection               |
| Telemetry    | Custom metrics            | Production instrumentation           |
| Recon        | Production-safe sampling  | Live production debugging            |

```elixir
# fprof a specific function call
:fprof.apply(&MyModule.slow_function/1, [arg], [{:procs, :all}])
:fprof.profile()
:fprof.analyse(dest: :stdout)

# Telemetry event
:telemetry.span([:my_app, :query], %{}, fn ->
  result = execute_query()
  {result, %{row_count: length(result)}}
end)
```

## Rust

| Tool            | What it measures          | When to use                       |
| --------------- | ------------------------- | --------------------------------- |
| cargo-flamegraph| CPU flamegraphs           | Visual CPU hotspot identification |
| perf            | Hardware counters, CPU    | Low-level Linux profiling         |
| criterion       | Statistical benchmarks    | Regression-aware microbenchmarks  |
| DHAT            | Heap profiling            | Allocation patterns               |

```bash
# Flamegraph (requires perf on Linux, DTrace on macOS)
cargo flamegraph --bin my_app
# Criterion benchmark
cargo bench
```

```rust
// criterion benchmark example
use criterion::{criterion_group, criterion_main, Criterion};

fn bench_parse(c: &mut Criterion) {
    c.bench_function("parse_input", |b| {
        b.iter(|| parse(std::hint::black_box(INPUT)))
    });
}

criterion_group!(benches, bench_parse);
criterion_main!(benches);
```

## Before/after measurement template

Record this for every optimization:

```
## Performance change: [description]

| Metric          | Before    | After     | Change   |
| --------------- | --------- | --------- | -------- |
| p50 latency     |           |           |          |
| p95 latency     |           |           |          |
| p99 latency     |           |           |          |
| Throughput (rps)|           |           |          |
| Memory (RSS)    |           |           |          |
| CPU utilization  |           |           |          |

Environment: [production / staging / local]
Load profile: [concurrent users, request pattern]
Duration: [measurement window]
```
