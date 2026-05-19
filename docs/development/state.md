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

Module skeleton — all bodies are stubs returning 0.

- `src/types.cyr` — shared types (empty placeholder; MihiInfo struct lands at M1)
- `src/cpu.cyr` — `mihi_cpu_model` / `mihi_cpu_count` / `mihi_cpu_arch`
- `src/mem.cyr` — `mihi_mem_total` / `mihi_mem_free`
- `src/kernel.cyr` — `mihi_kernel_name` / `mihi_kernel_version`
- `src/host.cyr` — `mihi_hostname` / `mihi_uptime_secs` / `mihi_distro`
- `src/main.cyr` — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/smoke.cyr` — smoke binary; build target

## Tests

- `tests/mihi.tcyr` — primary suite (currently empty per cyrius init defaults)
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

M1 onward fills real cases.

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke      # prints "mihi smoke ok", exit 0
```

`build/mihi-smoke` at M0 builds against vendored stdlib only; no
external deps.

## Dependencies

Direct (declared in `cyrius.cyml`):

- stdlib — string, fmt, alloc, io, vec, str, syscalls, assert

M3 will add `ai-hwaccel` for GPU probes.

## Consumers

_None yet._ Planned at v1.0:

- [`iam`](https://github.com/MacCracken/iam) — first consumer (M4)
- [`chakshu`](https://github.com/MacCracken/chakshu) — second consumer (M6)
- [`hapi`](https://github.com/MacCracken/hapi) — target-box info on link/sync
- [`BannerManor`](https://github.com/MacCracken/bannermanor) — hostname for banner auto-detect

## Next

See [`roadmap.md`](roadmap.md) for the M1 → v1.0 plan. Next ship is M1
(Linux probes: CPU + memory + kernel), targeting v0.2.0.
