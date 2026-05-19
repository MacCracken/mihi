# mihi — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

**0.1.0** — scaffolded 2026-05-19 via `cyrius init mihi`, then reshaped
into the `[lib]` modules pattern parallel to
[darshana](https://github.com/MacCracken/darshana). No releases yet.

## Toolchain

- **Cyrius pin**: `6.0.0` (in `cyrius.cyml [package].cyrius`)

## Shape

Library, not a binary. `[lib].modules` in `cyrius.cyml` declares the
bundle order; `cyrius distlib` concatenates them into
`dist/mihi.cyr` for consumer `include "lib/mihi.cyr"` after
`cyrius deps`.

## Source

Slices A + B landed (5 probes: 3 uname-backed + cpu_count + cpu_model).
Slice C and M2/M3 still stubs.

- `src/types.cyr` — shared types (empty; `MihiInfo` deferred per ADR 0001)
- `src/cpu.cyr` — `mihi_cpu_arch` ✅ + `mihi_cpu_count` ✅ + `mihi_cpu_model` ✅ (+ `mihi_parse_cpu_range` / `mihi_parse_cpu_model` pure-function helpers)
- `src/mem.cyr` — `mihi_mem_total` / `mihi_mem_free` stubs (slice C)
- `src/kernel.cyr` — `mihi_uname` wrapper + `mihi_kernel_name` ✅ + `mihi_kernel_version` ✅
- `src/host.cyr` — `mihi_hostname` / `mihi_uptime_secs` / `mihi_distro` stubs (M2)
- `src/main.cyr` — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/smoke.cyr` — smoke binary; prints `kernel / release / arch / model / cpus`

## Tests

- `tests/mihi.tcyr` — primary suite: 25 assertions across 12 test
  groups. Slice A: real-uname happy path + zero-init buffer +
  synthetic-uts offset round-trip. Slice B: range-parser unit tests
  (`"0-15"` / `"0"` / `"0-3,5-7"` / empty), real `/sys` read,
  cpuinfo-parser synthetic tests (happy + missing-field + line-anchor
  rejection of file-start match), real `/proc/cpuinfo` read.
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

Slice C and M2 add `/proc/meminfo`, `/proc/uptime`, `/etc/os-release`
parser coverage.

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke      # prints kernel / release / arch / model / cpus + "mihi smoke ok", exit 0
cyrius test             # 25/25 pass
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

See [`roadmap.md`](roadmap.md) for the M1 → v1.0 plan. Slices A + B
of M1 (kernel + cpu_arch via uname; cpu_count + cpu_model via /sys
and /proc/cpuinfo) are in `Unreleased`. Slice C
(`mihi_mem_total` / `mihi_mem_free` from `/proc/meminfo`) closes
M1. v0.2.0 cuts when slice C ships.
