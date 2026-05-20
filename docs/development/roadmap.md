# mihi — Roadmap

> Forward-only milestone plan to v1.0. Shipped work lives in
> [`../../CHANGELOG.md`](../../CHANGELOG.md) and the live status in
> [`state.md`](state.md) — this file is the sequencing of what's
> next, in what order, against what dependency gates.

## v1.0 criteria

The mihi v1.0 contract: a frozen probe surface that `iam`, `chakshu`,
and downstream consumers can pin against indefinitely.

- [ ] Probe API frozen — function signatures, return shapes, error
      semantics documented and tested for the full module set
      (`types` / `cpu` / `mem` / `kernel` / `host`)
- [ ] Every probe has a `/proc`, `/sys`, or syscall source citation
      inline in the declaring function
- [ ] `docs/sources.md` has one entry per probe with man-page /
      kernel-doc reference
- [ ] Test coverage: happy path + at least one error path
      (missing file, malformed content) per probe; 100+ assertions
- [ ] Benchmarks captured in `docs/benchmarks.md` for the hot
      probes (CPU detect, mem total) — these run on every shell login
- [ ] At least two downstream consumers green
      ([`iam`](https://github.com/MacCracken/iam) +
      [`chakshu`](https://github.com/MacCracken/chakshu))
- [ ] Security audit pass (`docs/audit/YYYY-MM-DD-audit.md`) — bounds
      on every `/proc` parse, syscall return handling, no allocator
      dependency from probe internals

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

### M4 — Pre-consumer hardening (v0.5.0)

> **Reordered 2026-05-19**: this milestone was originally "first
> consumer integration (iam)" with hardening at v0.9.0. The order
> flipped because `iam` is still scaffold-only — pushing mihi closer
> to v1.0 shape-stability *before* `iam` integrates avoids consumer-
> side rework that signature drift would cause. M5 below now holds
> the iam slot.

The P(-1) polish pass from CLAUDE.md — lock determinism, capture
benchmark baselines, run the security audit.

- ✅ Test coverage ≥ 100 assertions (104 across 38 groups, hit in the
  0.5.0 lead-up — see CHANGELOG).
- ✅ Doc alignment — `docs/sources.md` Slice E + ADR 0002 (gpu
  singleton cache) shipped pre-cut.
- ✅ Benchmarks captured — `benches/probe_paths.bcyr` +
  `benches/parsers.bcyr` + `benches/gpu_paths.bcyr`,
  `scripts/bench-history.sh` writing `docs/benchmarks/history.csv` +
  auto-regenerated `docs/benchmarks/results.md` (3-tier). Baseline on
  archaemenid: probes 2–52 µs, parsers 45–700 ns, gpu cold→warm
  ratio ~20,000× confirming ADR 0002.
- ☐ Security audit — `docs/audit/2026-05-19-audit.md`. Per the
  `feedback-security-audit-web-research` memory: internal review of
  bounds / syscall returns / overflow + external CVE/0day research
  for every `/proc` and `/sys` path mihi touches plus ai-hwaccel's
  transitive surfaces.
- ☐ `dist/mihi.cyr` distlib determinism CI gate (mirror of the
  ai-hwaccel pattern — `cyrius distlib` twice + sha256 compare).

### M5 — First consumer integration (v0.9.0)

> **Reordered 2026-05-19**: was v0.5.0; now blocked behind M4 so
> mihi's surface is benchmarked and audited before `iam` pins it.

`iam` consumes mihi end-to-end. The library is now shape-stable
(post-M4 audit); any breaking changes from this point onward warrant
an ADR. iam's mihi integration drives the v1.0 "first consumer green"
checkbox.

- `iam` repo's `[deps.mihi]` block pinned to mihi v0.9.0.
- Both repos build green in CI.
- `iam` produces a real output line for every mihi probe (kernel,
  release, arch, host, model, cpus, mem total/free, uptime, distro,
  plus the gpu slice).
- **Dep gate**: iam v0.x reaches a state that exercises every mihi
  probe. (As of 2026-05-19 iam is scaffold-only — the gate is open
  pending iam itself.)
- **Acceptance**: `iam` on archaemenid prints a complete system-info
  report sourced entirely from mihi.

### M6 — Second consumer (chakshu) green (v1.0.0)

When `chakshu` consumes mihi cleanly for its base monitor-readout
substrate, the API has crossed the "more than one consumer" gate
that locks API freeze. Cut v1.0.0.

- `chakshu` consumes mihi via `[deps.mihi]`.
- Both consumers (iam + chakshu) tracked in `state.md` consumer
  list.
- API freeze announced in CHANGELOG `Breaking` section as a no-op
  (signature already stable; the freeze is the contract change).
- v1.0.0 cut.

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
