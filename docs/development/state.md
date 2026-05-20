# mihi — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

**0.8.0** — released 2026-05-19. M5 acknowledgment cut. `iam`
integrated against mihi 0.7.0 (sitting as iam-0.9.0 RC), no
transitive fixes surfaced — the v0.8.x slot the 0.7.0 cut reserved
for them closes empty. No source changes; `dist/mihi.cyr` unchanged.
Roadmap M5 flipped ✅ at v0.8.0 (instead of the planned v0.9.0 —
iam pinned the current bundle rather than waiting for a renamed
cut). v1.0 remains gated on M6 (chakshu).

**0.7.0** — released 2026-05-19. Distlib hardening / CI gate cut.
Adds the determinism gate next to the existing drift check (SHA-256
compare across two `cyrius distlib` invocations), bench-files-build
gate, expanded required-files list (ADR 0002, audit doc, bench
infrastructure all CI-enforced). No source changes. Leaves 0.8.x
patch slots reserved for transitive fixes from `iam` / `chakshu`
consumer integration.

**0.6.0** — released 2026-05-19. Security audit cut. Three defensive
parser fixes (C-1 cpu_range descending, M-1 meminfo_kb overflow cap,
C-2 same for cpu_range + uptime), four new regression tests, two
transitive AMD GPU CVEs documented (CVE-2025-40288, CVE-2025-40289).
Full audit in `docs/audit/2026-05-19-audit.md`. Probe API unchanged.

**0.5.0** — released 2026-05-19. Pre-consumer hardening: 100+ test
assertions (104/104 across 38 groups), three-tier benchmark suite
under `benches/` + `docs/benchmarks/` (archaemenid baseline captured),
ADR 0002 for the gpu singleton cache, `docs/sources.md` Slice E.
Roadmap M4↔M5 reordered: this cut is the "library ready for
consumers" milestone; iam consumer integration shifts to v0.9.0.

**0.4.1** — released 2026-05-19. Dep-pin refresh: ai-hwaccel 2.2.5 →
2.2.6. Closes both Known Issues from 0.4.0 — ROCm device name now
populates (`AMD Radeon (PCI 0x1002:0x1638)` on archaemenid) and the
`registry_to_json` linker warning is gone. No mihi source changes.

**0.4.0** — released 2026-05-19. M3 complete: accelerator-identity
probes via ai-hwaccel 2.2.5's no-exec API. mihi now covers kernel /
CPU / memory / host-identity / accelerators — the full v1.0 probe
surface except `iam`'s consumer integration (M4). M2 shipped earlier
the same day (host identity); M1 covered kernel + CPU + memory.

## Toolchain

- **Cyrius pin**: `6.0.0` (in `cyrius.cyml [package].cyrius`)

## Shape

Library, not a binary. `[lib].modules` in `cyrius.cyml` declares the
bundle order; `cyrius distlib` concatenates them into
`dist/mihi.cyr` for consumer `include "lib/mihi.cyr"` after
`cyrius deps`.

## Source

M3 complete — 15 probes across kernel / cpu / mem / host / gpu.
M4 (hardening) + M4.5 (distlib CI gate) + M5 (iam consumer) all
shipped. M6 (chakshu) is the only milestone remaining before v1.0.

- `src/types.cyr` — shared types (empty; `MihiInfo` deferred per ADR 0001)
- `src/cpu.cyr` — `mihi_cpu_arch` ✅ + `mihi_cpu_count` ✅ + `mihi_cpu_model` ✅ (+ `mihi_parse_cpu_range` / `mihi_parse_cpu_model` pure-function helpers)
- `src/mem.cyr` — `mihi_mem_total` ✅ + `mihi_mem_free` ✅ (+ `mihi_find_meminfo_field` / `mihi_parse_meminfo_kb` / `mihi_extract_meminfo_bytes` helpers)
- `src/kernel.cyr` — `mihi_uname` wrapper + `mihi_kernel_name` ✅ + `mihi_kernel_version` ✅
- `src/host.cyr` — `mihi_hostname` ✅ + `mihi_uptime_secs` ✅ + `mihi_distro` ✅ (+ `mihi_parse_uptime_secs` / `mihi_find_osrelease_key` / `mihi_parse_osrelease_value` helpers)
- `src/gpu.cyr` — `mihi_gpu_count` ✅ + `mihi_gpu_name` ✅ + `mihi_gpu_memory_bytes` ✅ + `mihi_gpu_family` ✅ + `mihi_gpu_type` ✅ (module-level singleton cache via `_mihi_gpu_ensure`; first call runs `registry_detect_no_exec()`)
- `src/main.cyr` — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/smoke.cyr` — smoke binary; prints `kernel / release / arch / host / model / cpus / mem MiB / free MiB / uptime / distro / gpu cnt / gpu / gpu MiB`

## Tests

- `tests/mihi.tcyr` — primary suite: 108 assertions across 41 test
  groups (104 from 0.5.0 hardening push + 4 from the 0.6.0 audit
  regression tests). Slice A: real-uname happy path + zero-init buffer +
  synthetic-uts offset round-trip. Slice B: range-parser unit tests,
  cpuinfo-parser synthetic tests (happy + missing-field + line-anchor
  rejection), real `/proc/cpuinfo` + `/sys` reads. Slice C: meminfo
  field-anchor unit tests (file-start + mid-buffer + mid-line
  rejection), digit parser, kB→bytes extractor, real `/proc/meminfo`
  reads with sanity floors. Slice D: nodename offset round-trip,
  uptime parser (happy / freshly-booted / empty / non-digit),
  os-release key anchors (file-start + mid-buffer + mid-line + missing),
  value parser (quoted + bare + empty), ID-fallback composition, real
  `/proc/uptime` + `/etc/os-release` reads. Slice E (M3): synthetic
  registry CPU-only count + accessors, synthetic CPU+ROCm registry
  with name/memory/family/type assertions, out-of-range idx sentinel
  returns, live `registry_detect_no_exec()` smoke.
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke      # prints all 11+ lines including gpu cnt / gpu / gpu MiB + "mihi smoke ok", exit 0
cyrius test             # 108/108 pass
```

Build is clean as of 0.4.1 / ai-hwaccel 2.2.6 — only the cyrius
toolchain-pin-drift note remains (cosmetic; 6.0.0 pin matches 6.0.0
cycc, snapshot just predates the warning suppression).

## Dependencies

Direct (declared in `cyrius.cyml`):

- **stdlib** — string, fmt, alloc, io, vec, str, slice, syscalls, assert, agnosys, plus (added for the ai-hwaccel bundle) fs, tagged, process, fnptr, thread, freelist, hashmap, ct, json. DCE drops unused code from the linked binary.
- **agnosys** — Result-based wrapper over `uname(2)` / `sysinfo(2)`. mihi's uname-backed probes share one syscall through `agnosys_uname`. See [ADR 0001](../adr/0001-shared-uts-buffer.md).
- **ai-hwaccel 2.2.6** — accelerator detection. 2.2.5 was the first release with the no-exec contract (`registry_detect_no_exec()` masks off the eight subprocess-shelling backends); 2.2.6 closed the device-name + bundling gaps mihi's 0.4.0 integration surfaced. Without the no-exec contract mihi couldn't honor the "probes are pure reads" rule.

## Consumers

- [`iam`](https://github.com/MacCracken/iam) ✅ — **first consumer
  integrated** as of iam-0.9.0 (2026-05-19), pinned at
  `[deps.mihi] tag = "0.7.0"`. iam consumes the full mihi probe
  surface (kernel / cpu / mem / host / gpu) end-to-end; the M6 RC
  release notes confirm *"mihi 1.0 ship is the only external gate"*
  on iam's side. iam will repin to mihi v1.0 in lockstep when the
  freeze cuts.

Planned but not yet integrated:

- [`chakshu`](https://github.com/MacCracken/chakshu) — second consumer
  (M6 / v1.0). Blocked on chakshu's own Cyrius language update.
- [`hapi`](https://github.com/MacCracken/hapi) — target-box info on
  link/sync (post-v1.0).
- [`BannerManor`](https://github.com/MacCracken/bannermanor) —
  hostname for banner auto-detect (post-v1.0).

## Next

See [`roadmap.md`](roadmap.md) for the v1.0 plan. **M5 shipped as
v0.8.0** (iam integrated against mihi 0.7.0; v0.8.0 was the
acknowledgment cut). Only **M6 (chakshu)** remains before v1.0, and
it's blocked externally on chakshu's Cyrius language update. The
mihi side is feature-complete and shape-stable; no internal work is
planned between now and the v1.0 cut. If a transitive fix surfaces
from chakshu's eventual integration, it lands in a v0.9.x slot
before v1.0 freezes the API.
