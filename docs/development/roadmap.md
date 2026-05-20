# mihi — Roadmap

> Forward-only milestone plan to v1.0. Shipped work lives in
> [`../../CHANGELOG.md`](../../CHANGELOG.md) and the live status in
> [`state.md`](state.md) — this file is the sequencing of what's
> next, in what order, against what dependency gates.

## v1.0 criteria ✅ all met 2026-05-20

The mihi v1.0 contract: a frozen probe surface that `iam`, `chakshu`,
and downstream consumers can pin against indefinitely.

- [x] Probe API frozen — function signatures, return shapes, error
      semantics documented and tested for the full module set
      (`types` / `cpu` / `mem` / `kernel` / `host` / `gpu`)
- [x] Every probe has a `/proc`, `/sys`, or syscall source citation
      inline in the declaring function
- [x] `docs/sources.md` has one entry per probe with man-page /
      kernel-doc reference (Slices A + B + C + D + E)
- [x] Test coverage: happy path + at least one error path
      (missing file, malformed content) per probe; **108 assertions
      across 41 test groups**
- [x] Benchmarks captured in `docs/benchmarks.md` for the hot
      probes (CPU detect, mem total) — three-tier suite under
      `benches/` with `scripts/bench-history.sh` writing the history
      CSV
- [x] At least two downstream consumers green —
      [`iam`](https://github.com/MacCracken/iam) 0.9.0 RC (pinned
      mihi 0.7.0) and
      [`chakshu`](https://github.com/MacCracken/chakshu) 0.6.0
      (pinned mihi 0.8.0)
- [x] Security audit pass —
      [`docs/audit/2026-05-19-audit.md`](../audit/2026-05-19-audit.md)
      — bounds on every `/proc` parse, syscall return handling, no
      allocator dependency from probe internals

## Milestones

### M2 — Host identity probes (v0.3.0)

Three small probes that close the "tell me about this box" surface
for the login MOTD path. Signatures follow
[ADR 0001](../adr/0001-shared-uts-buffer.md) — caller-supplied
buffers, no probe-internal allocation.

- `mihi_hostname(uts)` — `utsname.nodename` (offset 65). Reuses the
  same uts buffer M1's kernel/cpu_arch probes fill, so a consumer
  pays one `uname(2)` for all four facts.
- `mihi_uptime_secs(buf, cap)` — first whitespace-separated field of
  `/proc/uptime`, parsed as decimal seconds (drop the fractional
  part). 64-byte scratch is plenty.
- `mihi_distro(buf, cap)` — `PRETTY_NAME="…"` from `/etc/os-release`;
  fall back to `ID=…` if PRETTY_NAME is absent. Caller supplies
  ~1 KiB scratch; probe handles the quote-stripping in place.
- Tests for each + missing-file / malformed-content paths.
- **Dep gate**: none — stdlib + agnosys.
- **Acceptance**: smoke prints `hostname / distro / uptime` lines on
  Linux.

### M3 — GPU probe (v0.4.0) ✅ shipped 2026-05-19

- ✅ `mihi_gpu_*` family — 5 probes (`mihi_gpu_count` + idx-keyed
  `mihi_gpu_{name,memory_bytes,family,type}`) wrap ai-hwaccel 2.2.5's
  `registry_detect_no_exec()`. Module-level singleton cache means
  one detection pass per process; subsequent calls are O(n) vec walks.
  See [ADR 0002](../adr/0002-gpu-singleton-cache.md) for the cache-
  shape choice.
- ✅ Single source per the *one source per fact* principle — sysfs
  reads via ai-hwaccel; no fallback chain to `lspci` / nvidia-smi /
  etc.
- ✅ **Dep gate cleared 2026-05-19**: ai-hwaccel 2.2.4 added the
  `[lib].modules` surface + `dist/ai-hwaccel.cyr` bundle; 2.2.5 added
  the `registry_detect_no_exec()` entry point that masks off the
  eight subprocess-shelling backends (CUDA, Apple, Vulkan, Gaudi,
  Neuron, Intel oneAPI, Cerebras, Graphcore) and skips
  `detect_interconnects`. Mihi pins `[deps.ai-hwaccel] tag = "2.2.6"`
  (bumped from 2.2.5 in 0.4.1, see below) and calls only
  `registry_detect_no_exec()` — the no-exec contract is enforced on
  the ai-hwaccel side.
- ✅ **Safe backends mihi sees**: ROCm, Intel NPU, AMD XDNA, TPU,
  Qualcomm, Groq, Samsung NPU, MediaTek APU — plus the sysfs
  post-passes (`enrich_bandwidth/pcie/numa`, `detect_storage`,
  `detect_environment`).
- ✅ **Acceptance**: smoke prints `gpu cnt: 1 / gpu: AMD Radeon
  (PCI 0x1002:0x1638) / gpu MiB: 3072` on archaemenid (Ryzen 5800H +
  Radeon iGPU).

### M3.1 — ai-hwaccel 2.2.6 dep refresh (v0.4.1) ✅ shipped 2026-05-19

Pure dep-pin bump; no mihi source changed. Picks up upstream fixes
that the 0.4.0 integration surfaced:

- ✅ `detect_rocm` now populates `profile_device_name` (prefers
  `product_name` sysfs file, falls back to synthesized
  `"AMD Radeon (PCI vendor:device)"`). Closes the "(unnamed)"
  acceptance gap in M3 above.
- ✅ Three more upstream detectors gained name population in 2.2.6
  (TPU, Gaudi, Neuron) — not reachable on archaemenid but the gap is
  closed for cloud-accelerator consumers.
- ✅ ai-hwaccel 2.2.6 includes `src/json_out.cyr` in its bundle —
  resolves the `undefined function 'registry_to_json'` linker
  warning that 0.4.0 carried.

### M4 — Pre-consumer hardening (v0.5.0 + v0.6.0)

> **Reordered 2026-05-19**: this milestone was originally "first
> consumer integration (iam)" with hardening at v0.9.0. The order
> flipped because `iam` is still scaffold-only — pushing mihi closer
> to v1.0 shape-stability *before* `iam` integrates avoids consumer-
> side rework that signature drift would cause.

The P(-1) polish pass from CLAUDE.md — test coverage, benchmark
baselines, security audit. Spans two cuts (v0.5.0 + v0.6.0).

- ✅ Test coverage ≥ 100 assertions — landed in 0.5.0 (104), grew to
  108 with the 0.6.0 audit-regression tests.
- ✅ Doc alignment — `docs/sources.md` Slice E + ADR 0002 (gpu
  singleton cache) shipped in 0.5.0.
- ✅ Benchmarks captured — `benches/probe_paths.bcyr` +
  `benches/parsers.bcyr` + `benches/gpu_paths.bcyr`,
  `scripts/bench-history.sh` writing `docs/benchmarks/history.csv` +
  auto-regenerated `docs/benchmarks/results.md` (3-tier). Baseline on
  archaemenid: probes 2–52 µs, parsers 45–700 ns, gpu cold→warm
  ratio ~20,000× confirming ADR 0002. (0.5.0)
- ✅ Security audit (v0.6.0) — `docs/audit/2026-05-19-audit.md`
  filed. Internal review (3 defensive parser fixes — C-1, M-1, C-2)
  + external CVE research (2 transitive AMD GPU CVEs documented for
  consumer awareness: CVE-2025-40289, CVE-2025-40288). No critical
  findings; probe API unchanged.

### M4.5 — distlib hardening (v0.7.0) ✅ shipped 2026-05-19

CI-enforced determinism for the consumer-facing bundle. Mirrors the
ai-hwaccel + libro + yukti pattern: build the bundle, sha256 it,
re-build, compare. Any drift fails the build.

- ✅ `cyrius distlib` runs in CI on every push + PR (the existing
  drift check has been in `.github/workflows/ci.yml` since v0.2.0;
  the 0.7.0 cut adds the determinism gate next to it).
- ✅ **Determinism rebuild gate** — second `cyrius distlib`
  invocation in the same CI step must produce a byte-identical
  bundle (SHA-256 compare).
- ✅ **Drift gate** — if a contributor forgets to regenerate
  `dist/` after touching `src/`, `diff -q` against the checked-in
  bundle fails the build.
- ✅ **Bench file build gate** — every `benches/*.bcyr` is compiled
  to catch a helper removal that breaks bench compilation. Doesn't
  run the benches.
- ✅ **Required-files list expanded** — ADR 0002, audit doc,
  benchmark infrastructure all now enforced by the docs job.
- **Acceptance ✅**: CI workflow has `distlib drift check` +
  `distlib determinism check` + `Bench files build` steps sitting
  between `Test` and `DCE parity check`.

### M4.6 — Transitive consumer fixes (v0.8.x, reserved) ✅ closed empty 2026-05-19

Patch slots reserved for fixes that would surface when `iam` (M5) or
`chakshu` (M6) integrated against mihi. **Closed empty at v0.8.0** —
iam's integration against mihi 0.7.0 surfaced zero transitive fixes,
so no patch content was needed. The v0.8.0 cut repurposed the slot as
the M5-acknowledgment release instead. If chakshu's eventual M6
integration surfaces transitive fixes, they land in a v0.9.x slot
before v1.0 freezes the API.

### M5 — First consumer integration (v0.8.0) ✅ shipped 2026-05-19

> **Sequencing note**: roadmap originally planned this at v0.9.0;
> reality shipped it at v0.8.0. iam integrated against the existing
> mihi 0.7.0 `dist/mihi.cyr` bundle rather than waiting for a
> renamed cut, so the M5 acknowledgment landed in the slot
> originally reserved as M4.6.

> **Earlier reorder (2026-05-19)**: M5 was reordered from v0.5.0 to
> sit behind M4 (hardening) + M4.5 (distlib) so mihi's surface was
> benchmarked, audited, and bundle-deterministic before `iam`
> pinned it.

`iam` consumes mihi end-to-end. The library was shape-stable post-M4
audit (no findings required signature changes); breaking changes from
this point onward warrant an ADR. iam's mihi integration drives the
v1.0 "first consumer green" checkbox.

- ✅ `iam` repo's `[deps.mihi]` block pinned at
  `tag = "0.7.0"` (`iam/cyrius.cyml`). iam-side intent is to repin
  to `tag = "1.0.0"` in lockstep when mihi cuts v1.0.
- ✅ Both repos build green in CI.
- ✅ `iam` produces a real output line for every mihi probe
  (kernel, release, arch, host, model, cpus, mem total/free,
  uptime, distro, plus the gpu slice).
- ✅ iam-0.9.0 RC released 2026-05-19, F-001 (TTY-escape
  sanitization at the renderer boundary) closed iam-side per
  the *mihi returns raw bytes, consumers handle formatting* rule.
- **Acceptance ✅**: `iam` on archaemenid prints a complete
  system-info report sourced entirely from mihi.

### M6 — Second consumer (chakshu) green (v1.0.0) ✅ shipped 2026-05-20

When `chakshu` consumes mihi cleanly for its base monitor-readout
substrate, the API has crossed the "more than one consumer" gate
that locks API freeze. Cut v1.0.0.

- ✅ `chakshu` (a.k.a. `shu`) consumes mihi via `[deps.mihi] tag =
  "0.8.0"` as of chakshu-0.6.0 (2026-05-20). chakshu's Cyrius pin
  also moved to 6.0.1, unblocking the integration the original
  M6 entry called out as the gate.
- ✅ Both consumers (iam + chakshu) now in `state.md`'s consumer
  list as integrated, not planned.
- ✅ Layered architecture established by the chakshu integration:
  mihi owns identity / static-fact probes; chakshu owns per-frame
  deltas (CPU%, disk rate, network rate, per-pid stats). Future
  identity additions accrete on the mihi side rather than
  re-introducing hand-rolled `/proc` reads in consumers.
- ✅ API freeze announced in CHANGELOG `### Breaking` section as a
  no-op — signatures already stable since 0.4.0; the "breaking"
  is the contract change.
- ✅ v1.0.0 cut.

## Out of scope (for v1.0)

Keeps future contributors from adding to v1.0 by accident.

- **Windows / macOS probes** — Linux + AGNOS-native only for v1.0.
  Windows / macOS may land in v1.1+ if there's demand.
- **GPU temperature, fan speed, power draw** — monitoring concerns;
  live in `chakshu`, not in a static probe library.
- **Network info** (interface list, IP, MAC) — separate concern; a
  future `mihi-net` sibling lib if needed.
- **Process info** (uptime per process, top consumers) — `chakshu` /
  `ps`-equivalents own this.
- **Configurable output format** — mihi returns raw values; all
  formatting lives in consumers (`iam`, `chakshu`).
- **Caching layer** — every probe is a fresh read.
- **Daemon mode** — mihi is a library, not a service.

## Cross-references

- [`state.md`](state.md) — live status (current version, sizes,
  consumer integrations)
- [`../sources.md`](../sources.md) — per-probe citation index
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — release history
