# mihi — Roadmap

> Milestone plan through v1.0. State lives in [`state.md`](state.md);
> this file is the sequencing — what ships, in what order, against
> what dependency gates.

## v1.0 criteria

The mihi v1.0 contract: a frozen probe surface that `iam`, `chakshu`,
and downstream consumers can pin against indefinitely.

- [ ] Probe API frozen — function signatures, return shapes, error
      semantics documented and tested for the full module set
      (`types` / `cpu` / `mem` / `kernel` / `host`)
- [ ] Every probe has a `/proc`, `/sys`, or syscall source citation
      inline in the declaring function
- [ ] `docs/sources.md` complete — one entry per probe with man-page
      / kernel-doc reference
- [ ] Test coverage: happy path + at least one error path
      (missing file, malformed content) per probe; 100+ assertions
- [ ] Benchmarks captured in `docs/benchmarks.md` for the hot
      probes (CPU detect, mem total) — these run on every shell login
- [ ] At least two downstream consumers green
      ([`iam`](https://github.com/MacCracken/iam) +
      [`chakshu`](https://github.com/MacCracken/chakshu))
- [ ] CHANGELOG complete from v0.1.0 onward
- [ ] Security audit pass (`docs/audit/YYYY-MM-DD-audit.md`) — bounds
      on every `/proc` parse, syscall return handling, no allocator
      dependency from probe internals

## Milestones

### M0 — Scaffold (v0.1.0) — ✅ shipped 2026-05-19

- `cyrius init` scaffold reshaped into `[lib]` modules pattern (parallels darshana)
- Module skeleton: `src/types.cyr`, `src/cpu.cyr`, `src/mem.cyr`, `src/kernel.cyr`, `src/host.cyr`
- `programs/smoke.cyr` builds clean and exits 0
- Doc-tree per [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md)
- All probe bodies return 0; ready for real implementations

### M1 — Linux probes: CPU + memory + kernel (v0.2.0)

The first batch of working probes — the facts every `iam` invocation
needs on Linux. uname-backed probes route through `agnosys_uname`
and share a single UTS buffer (one syscall, multiple field reads).

- `mihi_cpu_model()` — parse `model name` field from `/proc/cpuinfo` (first occurrence)
- `mihi_cpu_count()` — count logical CPUs from `/sys/devices/system/cpu/online`
- `mihi_cpu_arch()` — `uname.machine` (via shared agnosys_uname UTS buffer)
- `mihi_mem_total()` — parse `MemTotal:` from `/proc/meminfo` (kB → bytes)
- `mihi_mem_free()` — parse `MemAvailable:` from `/proc/meminfo`
- `mihi_kernel_name()` — `uname.sysname` (shared UTS)
- `mihi_kernel_version()` — `uname.release` (shared UTS)
- ADR: `docs/adr/0001-shared-uts-buffer.md` — rationale for one-syscall-many-fields via agnosys
- Each probe: source citation in declaring function + tests/mihi.tcyr happy + missing-file path
- **Dep gate**: agnosys (already in `cyrius.cyml`)
- **Acceptance**: smoke binary calls each probe, prints non-zero result on Linux.

### M2 — Host identity probes (v0.3.0)

- `mihi_hostname()` — `gethostname(2)` into static buffer
- `mihi_uptime_secs()` — parse first field of `/proc/uptime`
- `mihi_distro()` — parse `PRETTY_NAME` from `/etc/os-release`, fall back to `ID`
- Tests for each + missing-file paths
- **Dep gate**: none.
- **Acceptance**: smoke prints `hostname / distro / uptime` line.

### M3 — GPU probe (v0.4.0)

- `mihi_gpu_*` family — consume [`ai-hwaccel`](https://github.com/MacCracken/ai-hwaccel) for the canonical GPU detection surface
- Single source (per the *one source per fact* principle)
- **Dep gate**: `ai-hwaccel` ≥ 2.2.2 (currently pinned to cyrius 5.11.8 — verify compatibility before pin)
- **Acceptance**: smoke prints GPU vendor + model on a NUC AMD system.

### M4 — First consumer integration (v0.5.0)

`iam` consumes mihi end-to-end. The library has to be **shape-stable**
through this milestone; any signature changes are breaking pre-v1.0
but should still be ADR'd and recorded.

- `iam` repo's `[deps.mihi]` block pinned to mihi v0.5.0
- Both repos build green
- `iam` produces a real output line for every mihi probe
- **Dep gate**: iam v0.x reaches a state that exercises every mihi probe.
- **Acceptance**: `iam` on archaemenid prints a complete system-info report sourced entirely from mihi.

### M5 — distlib hardening + benchmarks (v0.9.0)

- `dist/mihi.cyr` bundle stable — `cyrius distlib` output is byte-deterministic across runs
- Benchmarks for CPU detect, mem total, hostname (the login-hot path)
- 3-point bench trend captured in `docs/benchmarks.md`
- P(-1) hardening pass complete — security audit doc filed
- `docs/sources.md` complete

### M6 — Second consumer (chakshu) green (v1.0.0)

When `chakshu` consumes mihi cleanly for its base monitor-readout
substrate, the API has crossed the "more than one consumer" gate that
locks API freeze. Cut v1.0.0.

- `chakshu` consumes mihi via `[deps.mihi]`
- Both consumers (iam + chakshu) tracked in `state.md` consumer list
- API freeze announced in CHANGELOG `Breaking` section as a
  no-op (signature already stable; the freeze is the contract change)
- v1.0.0 cut

## Out of scope (for v1.0)

The list keeps future contributors from adding to v1.0 by accident.

- **Windows / macOS probes** — Linux + AGNOS-native only for v1.0.
  Windows / macOS may land in v1.1+ if there's demand.
- **GPU temperature, fan speed, power draw** — not in scope; these
  are monitoring concerns and live in `chakshu`, not in a static
  probe library.
- **Network info** (interface list, IP, MAC) — separate concern; a
  future `mihi-net` sibling lib if needed, not v1.0 scope.
- **Process info** (uptime per process, top consumers) — `chakshu` /
  `ps`-equivalents own this.
- **Configurable output format** — mihi returns raw values. All
  formatting concerns live in consumers (`iam`, `chakshu`).
- **Caching layer** — every probe is a fresh read. Caching is a
  consumer concern.
- **Daemon mode** — mihi is a library, not a service.

## Cross-references

- [`state.md`](state.md) — live status (versions, sizes, consumer integrations)
- [`../sources.md`](../sources.md) — per-probe citation index (created at M1)
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — release history
