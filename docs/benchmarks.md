# mihi — benchmarks

Narrative companion to the auto-generated
[`docs/benchmarks/results.md`](benchmarks/results.md). The three-tier
layout matches the yukti / ai-hwaccel sibling convention:

| Tier | File | Purpose |
|---|---|---|
| 1 | [`benches/*.bcyr`](../benches/) | Bench definitions in Cyrius (group/name) |
| 2 | [`docs/benchmarks/history.csv`](benchmarks/history.csv) | Append-only per-run history; columns: timestamp, commit, branch, benchmark, avg_ns, min_ns, max_ns, iters |
| 3 | [`docs/benchmarks/results.md`](benchmarks/results.md) | Auto-regenerated table of the 3 most recent runs with Δ first→last per benchmark |

Re-run any time: `./scripts/bench-history.sh` — builds every
`benches/*.bcyr`, runs the binary, parses the `bench_report` lines,
appends to `history.csv`, regenerates `results.md`.

## Bench groups

### `probe/*` — public API with real I/O

These are the calls a login-MOTD consumer (`iam`, `BannerManor`)
makes once per shell. Each timing includes the underlying syscall(s)
plus the parser pass — open + read + close + parse. Costs are µs-scale
because every probe touches the kernel through `/proc` or `/sys`.

Hot-path expectations (archaemenid baseline, Ryzen 7 5800H):

- `probe/mihi_uname` — ~2 µs. One syscall, no parsing; the cheapest
  fact-extraction in mihi.
- `probe/mihi_cpu_count` — ~8 µs. `/sys/devices/system/cpu/online`
  open/read/close + range-string parse.
- `probe/mihi_mem_total` and `probe/mihi_mem_free` — ~13–14 µs each.
  Same `/proc/meminfo` read, different field lookups; consumers
  wanting both pay twice (mihi's "no caching layer" rule).
- `probe/mihi_uptime_secs` — ~24 µs. Higher variance because
  `/proc/uptime` is a small file the kernel re-computes on every read.
- `probe/mihi_cpu_model` — ~52 µs. The heaviest probe — 8 kB scratch,
  walks past the first-block model-name line, mutates the buffer to
  null-terminate. Login MOTD users hit this once; nothing else does.
- `probe/mihi_distro` — ~6 µs. `/etc/os-release` is small (~500 B)
  and lives in initramfs, so the read is faster than `/proc` cache
  lookups.

### `accessor/*` — uts field accessors (pure pointer arithmetic)

The four uname-backed probes (`mihi_kernel_name`, `mihi_kernel_version`,
`mihi_cpu_arch`, `mihi_hostname`) are zero-cost once `mihi_uname` has
filled the shared uts buffer (ADR 0001). Numbers should sit at 4–5 ns
— effectively a register move plus the bench harness's clock-read
overhead, which is amortised away by batching 100k iterations per
`bench_batch_start/stop` pair.

Regression watch: if any accessor drifts above ~10 ns the optimiser
has stopped inlining the pointer-add. Investigate before merging.

### `parser/*` — pure parsers (synthetic buffers)

The parse-only cost — what you'd pay if the data were already in
memory. AGNOS-native consumers (boot-info handoff) hit these without
the syscall overhead the `probe/*` group includes. Useful for two
reasons:

1. **Regression detection** — parser cost is independent of host
   `/proc` shape, so these numbers travel cleanly across boxes.
2. **Sizing the AGNOS-native fast path** — when boot-info handoff
   lands, `mihi_*` calls collapse from `probe/* `cost to
   `parser/*` cost. The ratio (typically 100×) is the AGNOS speedup
   bound.

Notable shapes:

- `parser/meminfo_MemAvailable` is ~4× slower than
  `parser/meminfo_MemTotal` because the field anchor must walk past
  `MemTotal` and `MemFree` before matching. Linear-search cost; not a
  bug.
- `parser/cpu_range_disjoint` is ~2× `cpu_range_simple` because the
  parser sums two range segments instead of one.

### `gpu/*` — accelerator probes (no-exec via ai-hwaccel)

This group exists to prove [ADR 0002](adr/0002-gpu-singleton-cache.md)
empirically. The module-level singleton makes the cost shape:

| Bench | What it measures | archaemenid baseline |
|---|---|---|
| `gpu/count_cold` | First call after `_mihi_gpu_registry = 0` — full `registry_detect_no_exec()` walk across `/sys/class/drm`, `/sys/class/accel`, `/sys/class/misc`, `/dev/*`, PCIe, NUMA | ~1.2 ms |
| `gpu/count_warm` | Subsequent calls — `vec_len + iteration over reg_profiles` | ~60 ns |
| `gpu/accessor_name_idx0` | Per-idx lookup once warm | ~70 ns |

The cold/warm ratio is **~20,000×** on archaemenid. That ratio is
the load-bearing claim of ADR 0002 — without the singleton, a
consumer iterating accelerators with the per-idx accessors would
trigger N+1 full `/sys` walks. On boxes with more discrete
accelerators (cloud / multi-GPU workstations) the cold cost grows
linearly with discovered devices while the warm cost stays
sub-microsecond. The ratio gets larger, not smaller.

## Regression protocol

Per CLAUDE.md P(-1): "Never skip benchmarks. Numbers don't lie."

Before any change that could affect hot-path code:

1. Run `./scripts/bench-history.sh` to capture a pre-change baseline.
2. Make the change.
3. Run again. `docs/benchmarks/results.md` now shows the Δ first→last
   per benchmark.
4. Investigate any group where a delta exceeds ±10% on a probe that
   wasn't deliberately changed.

For releases: re-run on the release commit so the CHANGELOG can
cite stable numbers. The CSV's per-run rows tie cleanly to git
short-hashes for blame.
