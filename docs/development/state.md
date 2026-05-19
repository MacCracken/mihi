# mihi — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

**0.2.0** — released 2026-05-19. M1 complete: kernel + CPU + memory
probe surface against Linux `uname(2)` / `/sys` / `/proc/cpuinfo` /
`/proc/meminfo`. Scaffolded as 0.1.0 via `cyrius init mihi` and
reshaped into the `[lib]` modules pattern parallel to
[darshana](https://github.com/MacCracken/darshana) on the same day.

## Toolchain

- **Cyrius pin**: `6.0.0` (in `cyrius.cyml [package].cyrius`)

## Shape

Library, not a binary. `[lib].modules` in `cyrius.cyml` declares the
bundle order; `cyrius distlib` concatenates them into
`dist/mihi.cyr` for consumer `include "lib/mihi.cyr"` after
`cyrius deps`.

## Source

M1 complete — 7 probes across kernel / cpu / mem. M2 (host-identity)
is next.

- `src/types.cyr` — shared types (empty; `MihiInfo` deferred per ADR 0001)
- `src/cpu.cyr` — `mihi_cpu_arch` ✅ + `mihi_cpu_count` ✅ + `mihi_cpu_model` ✅ (+ `mihi_parse_cpu_range` / `mihi_parse_cpu_model` pure-function helpers)
- `src/mem.cyr` — `mihi_mem_total` ✅ + `mihi_mem_free` ✅ (+ `mihi_find_meminfo_field` / `mihi_parse_meminfo_kb` / `mihi_extract_meminfo_bytes` helpers)
- `src/kernel.cyr` — `mihi_uname` wrapper + `mihi_kernel_name` ✅ + `mihi_kernel_version` ✅
- `src/host.cyr` — `mihi_hostname` / `mihi_uptime_secs` / `mihi_distro` stubs (M2)
- `src/main.cyr` — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/smoke.cyr` — smoke binary; prints `kernel / release / arch / model / cpus / mem MiB / free MiB`

## Tests

- `tests/mihi.tcyr` — primary suite: 37 assertions across 17 test
  groups. Slice A: real-uname happy path + zero-init buffer +
  synthetic-uts offset round-trip. Slice B: range-parser unit tests,
  cpuinfo-parser synthetic tests (happy + missing-field + line-anchor
  rejection), real `/proc/cpuinfo` + `/sys` reads. Slice C: meminfo
  field-anchor unit tests (file-start + mid-buffer + mid-line
  rejection), digit parser, kB→bytes extractor, real `/proc/meminfo`
  reads with sanity floors.
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

M2 adds `/proc/uptime`, `/etc/os-release`, and the second uname-backed
probe (`mihi_hostname` via `utsname.nodename`).

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke      # prints kernel / release / arch / model / cpus / mem MiB / free MiB + "mihi smoke ok", exit 0
cyrius test             # 37/37 pass
```

## Dependencies

Direct (declared in `cyrius.cyml`):

- stdlib — string, fmt, alloc, io, vec, str, syscalls, assert
- **agnosys** — Result-based wrapper over `uname(2)` / `sysinfo(2)`. mihi's uname-backed probes (kernel_name / kernel_version / cpu_arch / hostname) share one syscall through `agnosys_uname` rather than each re-implementing `SYS_UNAME`. See [ADR 0001](../adr/0001-shared-uts-buffer.md).

M3 will add `ai-hwaccel` for GPU probes.

## Consumers

_None yet._ Planned at v1.0:

- [`iam`](https://github.com/MacCracken/iam) — first consumer (M4)
- [`chakshu`](https://github.com/MacCracken/chakshu) — second consumer (M6)
- [`hapi`](https://github.com/MacCracken/hapi) — target-box info on link/sync
- [`BannerManor`](https://github.com/MacCracken/bannermanor) — hostname for banner auto-detect

## Next

See [`roadmap.md`](roadmap.md) for the v1.0 plan. **M1 shipped as
v0.2.0.** Next is M2 (v0.3.0): `mihi_hostname` (`utsname.nodename`
— slots into the existing uts buffer), `mihi_uptime_secs`
(`/proc/uptime` first field), `mihi_distro` (`/etc/os-release`
`PRETTY_NAME`). M3 wires `ai-hwaccel` for GPU probes.
