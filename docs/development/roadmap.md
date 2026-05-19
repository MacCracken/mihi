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
- ✅ Single source per the *one source per fact* principle — sysfs
  reads via ai-hwaccel; no fallback chain to `lspci` / nvidia-smi /
  etc.
- ✅ **Dep gate cleared 2026-05-19**: ai-hwaccel 2.2.4 added the
  `[lib].modules` surface + `dist/ai-hwaccel.cyr` bundle; 2.2.5 added
  the `registry_detect_no_exec()` entry point that masks off the
  eight subprocess-shelling backends (CUDA, Apple, Vulkan, Gaudi,
  Neuron, Intel oneAPI, Cerebras, Graphcore) and skips
  `detect_interconnects`. Mihi pins `[deps.ai-hwaccel] tag = "2.2.5"`
  and calls only `registry_detect_no_exec()` — the no-exec contract
  is enforced on the ai-hwaccel side.
- ✅ **Safe backends mihi sees**: ROCm, Intel NPU, AMD XDNA, TPU,
  Qualcomm, Groq, Samsung NPU, MediaTek APU — plus the sysfs
  post-passes (`enrich_bandwidth/pcie/numa`, `detect_storage`,
  `detect_environment`).
- ✅ **Acceptance**: smoke prints `gpu cnt: 1 / gpu: (unnamed) /
  gpu MiB: 3072` on archaemenid (Ryzen 5800H + Radeon iGPU).
- **Open follow-ups (ai-hwaccel 2.2.6)**:
  - `detect_rocm` doesn't populate `profile_device_name` — name comes
    back null; mihi correctly reports null, smoke prints "(unnamed)".
  - `cache.cyr`'s disk-write path references `registry_to_json` from
    the excluded `json_out.cyr` — one persistent linker warning. DCE
    elides the call. Fix: include `json_out.cyr` in the bundle or
    feature-gate the disk-cache code.

### M4 — First consumer integration (v0.5.0)

`iam` consumes mihi end-to-end. The library has to be **shape-stable**
through this milestone; any signature changes are still breaking
pre-v1.0 but should be ADR'd before landing.

- `iam` repo's `[deps.mihi]` block pinned to mihi v0.5.0.
- Both repos build green in CI.
- `iam` produces a real output line for every mihi probe.
- **Dep gate**: iam v0.x reaches a state that exercises every mihi
  probe.
- **Acceptance**: `iam` on archaemenid prints a complete system-info
  report sourced entirely from mihi.

### M5 — distlib hardening + benchmarks (v0.9.0)

The pre-v1.0 polish pass. Lock determinism, file the hot-path
benchmark baseline, run the P(-1) hardening checklist from CLAUDE.md.

- `dist/mihi.cyr` bundle stable — `cyrius distlib` output is
  byte-deterministic across runs.
- Benchmarks for CPU detect, mem total, hostname (the login-hot
  path) with a 3-point trend in `docs/benchmarks.md`.
- P(-1) hardening pass complete — security audit doc filed under
  `docs/audit/YYYY-MM-DD-audit.md`.

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
