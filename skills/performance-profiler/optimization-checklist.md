---
title: Optimization Checklist
impact: HIGH
impactDescription: systematic checklist prevents missing common performance wins
tags: optimization, n-plus-one, caching, compression, memory-leaks, load-testing
---

# Optimization Checklist

## Quick wins by category

### Database

- [ ] **N+1 queries** -- Use eager loading or batch queries (see database-designer)
- [ ] **Missing indexes** -- Run EXPLAIN on slow queries, add targeted indexes
- [ ] **Connection pooling** -- Use PgBouncer/HikariCP/DBConnection, not per-request connections
- [ ] **Query result caching** -- Cache expensive aggregations with TTL
- [ ] **Pagination** -- Cursor-based for large result sets, never OFFSET on large tables

### API

- [ ] **Pagination** -- Return bounded result sets, provide next cursor
- [ ] **Caching headers** -- Set `Cache-Control`, `ETag`, `Last-Modified` appropriately
- [ ] **Compression** -- Enable gzip/brotli for responses over 1KB
- [ ] **Payload size** -- Return only requested fields (sparse fieldsets, GraphQL)
- [ ] **Connection reuse** -- HTTP/2, keep-alive, connection pooling for upstream calls

### Bundle (frontend / CLI)

- [ ] **Tree shaking** -- Remove unused exports (ESM required)
- [ ] **Code splitting** -- Lazy-load routes and heavy components
- [ ] **Lazy loading** -- Defer below-fold images, non-critical scripts
- [ ] **Asset optimization** -- Compress images (WebP/AVIF), minify CSS/JS
- [ ] **Bundle analysis** -- Use webpack-bundle-analyzer or equivalent to find bloat

### Memory

- [ ] **Leak detection** -- Profile heap over time; look for monotonic growth
- [ ] **Allocation reduction** -- Reuse buffers, avoid allocating in hot loops
- [ ] **Stream processing** -- Process large files/datasets as streams, not in-memory
- [ ] **Reference cleanup** -- Close connections, unsubscribe listeners, clear timers
- [ ] **GC tuning** -- Last resort; prefer reducing allocations over tuning GC

## Load testing tools

| Tool      | Language   | Strengths                                       |
| --------- | ---------- | ----------------------------------------------- |
| k6        | JavaScript | Scriptable, CLI-first, good for CI pipelines    |
| Artillery | JavaScript | YAML scenarios, protocol support (HTTP, WS)     |
| vegeta    | Go         | Constant-rate HTTP load, great for pipelining   |
| wrk       | C/Lua      | High-throughput HTTP benchmarking                |
| locust    | Python     | Python scripts, distributed, web UI             |

### k6 example

```javascript
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 50 },   // ramp up
    { duration: "1m", target: 50 },    // sustain
    { duration: "10s", target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],   // 95th percentile under 500ms
  },
};

export default function () {
  const res = http.get("http://localhost:3000/api/health");
  check(res, { "status is 200": (r) => r.status === 200 });
  sleep(1);
}
```

## When NOT to optimize

- Premature optimization without a measured bottleneck
- Micro-optimizing code that runs once at startup
- Optimizing code paths that account for less than 5% of total time
- Trading readability for negligible performance gains
