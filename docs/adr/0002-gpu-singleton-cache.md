# 0002 — gpu.cyr module-level singleton cache

**Status**: Accepted
**Date**: 2026-05-19

## Context

[ADR 0001](0001-shared-uts-buffer.md) locked the
caller-supplies-buffer convention for the entire library: every probe
is a pure read into stack memory the caller owns. cpu / mem / kernel /
host all follow it cleanly because their underlying sources are short
files or a single syscall (~32 bytes to ~1.5 kB), and the parse is
linear over the buffer.

`mihi_gpu_*` (M3, v0.4.0) is a different shape:

- The underlying source is **ai-hwaccel**'s registry — a heap-allocated
  graph of `profile` structs (one per detected accelerator), each
  ~160 bytes, with embedded `device_name` strings, memory bytes,
  family tags, accelerator-type enum, and sysfs-derived enrichments
  (PCIe lane width, NUMA node, bandwidth). The registry isn't a flat
  buffer; it's a `vec<profile*>` plus a warnings vec plus a system_io
  struct.
- `ai-hwaccel::registry_detect_no_exec()` walks `/sys/class/drm`,
  `/sys/class/accel`, `/sys/class/misc/*`, `/dev/*`, the PCIe tree,
  and the NUMA tree. Cost is "many sysfs reads", not "one file
  parse". Re-running per accessor call would be wasteful — a consumer
  iterating `mihi_gpu_count()` then `mihi_gpu_name(0..count)` would
  trigger N+1 full sysfs walks.
- The mihi probe surface for accelerators is `count + per-idx
  accessors`, which is a natural fit for "build once, query many
  times" — but that pattern requires the registry to outlive a single
  function call, which conflicts with the stateless caller-buffer
  rule in ADR 0001.

mihi's CLAUDE.md hard rules constrain the design space:

- **No allocator dependency from probe internals** — appears to rule
  out any module-owned heap state.
- **No caching layer** (roadmap out-of-scope list) — explicitly
  worded against memoization.
- **Probes are pure reads** — fine, every ai-hwaccel call is a sysfs
  read.

The "no allocator dependency" rule, read strictly, rules out *any*
allocation from inside `src/gpu.cyr`. But ai-hwaccel itself allocates
the registry — that's its API contract. The choice isn't "allocate or
not" (ai-hwaccel will allocate when we call it); the choice is
"where does the registry pointer live across mihi calls".

## Decision

`src/gpu.cyr` holds a module-level singleton:

```cyrius
var _mihi_gpu_registry = 0;

fn _mihi_gpu_ensure() {
    if (_mihi_gpu_registry == 0) {
        _mihi_gpu_registry = registry_detect_no_exec();
    }
    return _mihi_gpu_registry;
}
```

First call to any `mihi_gpu_*` probe lazy-initializes the singleton
via `registry_detect_no_exec()`. Subsequent calls — same probe or any
other in the family — reuse the cached registry. The registry is
never freed; its lifetime is process lifetime.

The five public probes (`mihi_gpu_count`, `mihi_gpu_name`,
`mihi_gpu_memory_bytes`, `mihi_gpu_family`, `mihi_gpu_type`) all
delegate through `_mihi_gpu_ensure()` + `_mihi_gpu_profile(idx)` — a
single point of access for the cache plus a single CPU-skipping
indexer.

## Why this doesn't violate the rules

- **"No allocator dependency from probe internals"** — read as "mihi's
  caller-supplied-buffer probes don't allocate themselves". The
  allocation is ai-hwaccel's; mihi just holds the pointer. The
  alternative — passing the registry handle in from the caller —
  pushes the same allocation onto the consumer's plate and leaks
  ai-hwaccel's type into mihi's public API. Holding the pointer
  inside the module is the *narrowest* place for the dependency.
- **"No caching layer"** — read in context: the original "no caching"
  bullet is about not memoizing `/proc` reads (mem_total, cpu_count)
  where the fact can change between calls. Accelerator topology is
  effectively static for the process lifetime — accelerators don't
  appear/disappear on a running box. Caching here is "construct
  once" rather than "remember a value that can change".
- **"Probes are pure reads"** — the cache lookup is a pure read; the
  initial `registry_detect_no_exec()` is itself a composition of pure
  sysfs reads (the no-exec contract enforced ai-hwaccel-side, see
  ADR 0001 follow-on in `docs/sources.md` Slice E). No subprocess,
  no mutation of system state.

The singleton also matches the AGNOS-native handoff shape: on AGNOS,
accelerator topology comes from the boot-info struct at handoff
(populated once by the bootloader; immutable to userland). The
process-lifetime singleton is the natural mihi-side mirror.

## Consequences

- **Positive** — N+1 sysfs walks collapse to one. Consumer code is
  natural: `var n = mihi_gpu_count(); var i = 0; while (i < n) {
  println(mihi_gpu_name(i)); i = i + 1; }` without registry-handle
  threading. Tests can reach into `_mihi_gpu_registry` directly to
  inject a synthetic registry (CPU-only, CPU+ROCm, etc.) and exercise
  the accessors against known inputs without touching `/sys`.

- **Negative** — `src/gpu.cyr` has a mutable module-level var, which
  the cpu / mem / kernel / host modules don't. Anyone reading mihi
  src has to absorb that the gpu probe family has hidden state. The
  ADR is here so future readers don't have to derive the reasoning.
  The state is also non-resettable in normal usage — once detected,
  the cache lives until process exit. (Tests reset it explicitly.)

- **Negative** — under any future multi-threaded consumer, the
  first-call init has a TOCTOU window (two threads simultaneously
  pass the `_mihi_gpu_registry == 0` check, both call
  `registry_detect_no_exec()`, the second clobbers the first). Mihi
  consumers today (`iam` at M4, smoke binary) are single-threaded.
  When the first multi-threaded consumer appears, this ADR's
  alternative-3 ("explicit `mihi_gpu_init` entry point") becomes the
  forward path.

- **Neutral** — the singleton is allocated via ai-hwaccel's `alloc()`,
  which routes through cyrius's bump allocator. The bump allocator
  has no `free` — every byte allocated during detection lives until
  process exit anyway. "Never freed" is the only correct thing to do
  here.

## Alternatives considered

- **Caller-managed registry handle** — `mihi_gpu_detect() -> i64`
  returns the registry pointer; every accessor takes it as a first
  arg. Rejected: leaks ai-hwaccel's type into mihi's public API
  (the returned `i64` is opaque to consumers but is in fact a
  `reg*`); puts handle-threading onto every consumer; defeats the
  goal of mihi being a "facts about this box" library rather than a
  "registry library".

- **Opaque mihi handle wrapping the registry** — `mihi_gpu_init() ->
  MihiGpuCtx*`; accessors take the ctx. Same shape as above but with
  a mihi-owned wrapper type. Rejected for the same reason — adds a
  type without buying anything the singleton doesn't provide. Could
  be the future answer if multi-threading forces the issue (see
  Negative-2 above).

- **Stateless re-detection on every call** — call
  `registry_detect_no_exec()` inside each `mihi_gpu_*` probe.
  Rejected: N+1 sysfs walks, plus the registry would be allocated
  N times (bump allocator never frees → process-lifetime memory
  bloat per call).

- **`MihiInfo` envelope** (per ADR 0001 future-work note) — bundle
  uts + meminfo + cpuinfo + gpu registry into one
  `mihi_collect(info)` entry point. Deferred to v0.5.0 / M4 if `iam`
  wants the convenience; doesn't conflict with this ADR since the
  envelope would be a wrapper around the same primitives, and the
  gpu portion of the envelope is exactly this singleton-pointer
  rehomed onto a struct field.
