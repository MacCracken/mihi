# mihi — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

**0.3.0** — released 2026-05-19. M2 complete: host-identity probes
(hostname / uptime / distro) close the "tell me about this box"
surface for the login MOTD path. M1 shipped earlier the same day
covering kernel + CPU + memory.

## Toolchain

- **Cyrius pin**: `6.0.0` (in `cyrius.cyml [package].cyrius`)

## Shape

Library, not a binary. `[lib].modules` in `cyrius.cyml` declares the
bundle order; `cyrius distlib` concatenates them into
`dist/mihi.cyr` for consumer `include "lib/mihi.cyr"` after
`cyrius deps`.

## Source

M2 complete — 10 probes across kernel / cpu / mem / host. M3 (GPU
via `ai-hwaccel`) is next.

- `src/types.cyr` — shared types (empty; `MihiInfo` deferred per ADR 0001)
- `src/cpu.cyr` — `mihi_cpu_arch` ✅ + `mihi_cpu_count` ✅ + `mihi_cpu_model` ✅ (+ `mihi_parse_cpu_range` / `mihi_parse_cpu_model` pure-function helpers)
- `src/mem.cyr` — `mihi_mem_total` ✅ + `mihi_mem_free` ✅ (+ `mihi_find_meminfo_field` / `mihi_parse_meminfo_kb` / `mihi_extract_meminfo_bytes` helpers)
- `src/kernel.cyr` — `mihi_uname` wrapper + `mihi_kernel_name` ✅ + `mihi_kernel_version` ✅
- `src/host.cyr` — `mihi_hostname` ✅ + `mihi_uptime_secs` ✅ + `mihi_distro` ✅ (+ `mihi_parse_uptime_secs` / `mihi_find_osrelease_key` / `mihi_parse_osrelease_value` helpers)
- `src/main.cyr` — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/smoke.cyr` — smoke binary; prints `kernel / release / arch / host / model / cpus / mem MiB / free MiB / uptime / distro`

## Tests

- `tests/mihi.tcyr` — primary suite: 59 assertions across 24 test
  groups. Slice A: real-uname happy path + zero-init buffer +
  synthetic-uts offset round-trip. Slice B: range-parser unit tests,
  cpuinfo-parser synthetic tests (happy + missing-field + line-anchor
  rejection), real `/proc/cpuinfo` + `/sys` reads. Slice C: meminfo
  field-anchor unit tests (file-start + mid-buffer + mid-line
  rejection), digit parser, kB→bytes extractor, real `/proc/meminfo`
  reads with sanity floors. Slice D: nodename offset round-trip,
  uptime parser (happy / freshly-booted / empty / non-digit),
  os-release key anchors (file-start + mid-buffer + mid-line + missing),
  value parser (quoted + bare + empty), ID-fallback composition, real
  `/proc/uptime` + `/etc/os-release` reads.
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

M3 will add `ai-hwaccel`-backed GPU probes.

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke      # prints kernel / release / arch / host / model / cpus / mem MiB / free MiB / uptime / distro + "mihi smoke ok", exit 0
cyrius test             # 59/59 pass
```

## Dependencies

Direct (declared in `cyrius.cyml`):

- stdlib — string, fmt, alloc, io, vec, str, slice, syscalls, assert
- **agnosys** — Result-based wrapper over `uname(2)` / `sysinfo(2)`. mihi's uname-backed probes (kernel_name / kernel_version / cpu_arch / hostname) share one syscall through `agnosys_uname` rather than each re-implementing `SYS_UNAME`. See [ADR 0001](../adr/0001-shared-uts-buffer.md).

M3 will add `ai-hwaccel` for GPU probes.

## Consumers

_None yet._ Planned at v1.0:

- [`iam`](https://github.com/MacCracken/iam) — first consumer (M4)
- [`chakshu`](https://github.com/MacCracken/chakshu) — second consumer (M6)
- [`hapi`](https://github.com/MacCracken/hapi) — target-box info on link/sync
- [`BannerManor`](https://github.com/MacCracken/bannermanor) — hostname for banner auto-detect

## Next

See [`roadmap.md`](roadmap.md) for the v1.0 plan. **M2 shipped as
v0.3.0.** Next is M3 (v0.4.0): GPU probes via
[`ai-hwaccel`](https://github.com/MacCracken/ai-hwaccel) — adds a new
declared dep + a cyrius-version pin compatible with `cyrius.cyml`.
After that M4 (v0.5.0) integrates `iam` as the first consumer.
