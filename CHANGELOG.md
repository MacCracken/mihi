# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.4.0] — 2026-05-19

**M3 — GPU probe shipped via ai-hwaccel 2.2.5 no-exec API.** mihi now
covers the accelerator slice of the system-info surface. Five probes
(`mihi_gpu_count` + `mihi_gpu_{name,memory_bytes,family,type}(idx)`)
let consumers list local GPUs / NPUs / TPUs / ASICs without any
subprocess spawning. The eight subprocess-shelling backends in
ai-hwaccel (CUDA, Apple, Vulkan, Gaudi, Neuron, Intel oneAPI,
Cerebras, Graphcore) are masked off ai-hwaccel-side by
`builder_no_exec()` before any detector runs — so mihi's "probes are
pure reads" rule is preserved end-to-end, not via mihi-side
discipline. Eight sysfs/syscall backends remain reachable: ROCm,
Intel NPU, AMD XDNA, TPU, Qualcomm, Groq, Samsung NPU, MediaTek APU.

### Added
- **Slice E — accelerator identity probes** (new module `src/gpu.cyr`):
  - `mihi_gpu_count(): i64` — count of detected accelerators (the
    synthetic CPU profile ai-hwaccel always emits is excluded). Lazy-
    initializes the module-level registry singleton on first call.
  - `mihi_gpu_name(idx): cstring` — device name from
    `profile_device_name`. Returns 0 if idx is out of range OR if the
    backing detector didn't populate the name (known gap in
    ai-hwaccel 2.2.5 `detect_rocm` — file an issue for 2.2.6).
  - `mihi_gpu_memory_bytes(idx): i64` — total accelerator memory.
    Returns 0 - 1 if idx out of range.
  - `mihi_gpu_family(idx): i64` — `FAMILY_GPU` / `FAMILY_NPU` /
    `FAMILY_TPU` / `FAMILY_AI_ASIC`. Returns 0 - 1 on bad idx.
  - `mihi_gpu_type(idx): i64` — precise `ACCEL_*` constant (one of
    the 18 variants from ai-hwaccel's `AcceleratorType` enum, but
    only the eight no-exec types are reachable under the safe mask).
- **Tests** (`tests/mihi.tcyr`) — synthetic-registry happy paths
  (CPU-only → count 0; CPU + ROCm → count 1, all accessors resolve),
  out-of-range idx returns sentinels (null / -1), live
  `registry_detect_no_exec()` smoke. Suite grows 59 → 75 assertions.
- **Smoke binary** (`programs/smoke.cyr`) — prints `gpu cnt:` line
  plus one `gpu: <name>` + `gpu MiB: <mem>` pair per accelerator.
  On a Ryzen 5800H with Radeon iGPU: `gpu cnt: 1` / `gpu MiB: 3072`.

### Changed
- **`VERSION`**: 0.3.0 → 0.4.0.
- **`cyrius.cyml`**:
  - `[lib].modules` — `src/gpu.cyr` appended (last in include order).
  - `[deps]` stdlib — added `fs`, `tagged`, `process`, `fnptr`,
    `thread`, `freelist`, `hashmap`, `ct`, `json`. Required by
    bundled-but-unused modules inside `dist/ai-hwaccel.cyr`
    (cache.cyr, lazy.cyr, async_detect.cyr, detect/command.cyr).
    DCE drops the unused code from the linked binary.
  - `[deps.ai-hwaccel]` — new block pinning ai-hwaccel `tag = "2.2.5"`
    via `modules = ["dist/ai-hwaccel.cyr"]`. First non-stdlib mihi
    dependency beyond agnosys.

### Known Issues
- **One linker warning** — `undefined function 'registry_to_json'`
  is referenced from `cache.cyr`'s disk-write path in the ai-hwaccel
  2.2.5 bundle. The defining module (`src/json_out.cyr`) is excluded
  from `cyrius distlib` per ai-hwaccel's CLI/lib partition, leaving
  a dangling reference. DCE elides the call (mihi never reaches it),
  so the binary is correct, but the warning is noise. To be fixed
  on the ai-hwaccel side in 2.2.6 (either include `json_out.cyr` in
  the bundle or gate the disk-cache code on a feature flag).
- **ROCm device names empty** — `detect_rocm` in ai-hwaccel 2.2.5
  never calls `profile_set_device_name`, so `mihi_gpu_name(idx)`
  returns null for ROCm GPUs. mihi correctly reports null rather
  than fabricating a name; smoke output shows "(unnamed)". Fix
  belongs in ai-hwaccel 2.2.6 — read e.g. `/sys/class/drm/cardN/
  device/product_name` or similar.

## [0.3.0] — 2026-05-19

M2 complete. mihi closes the "tell me about this box" surface for the
login MOTD path — hostname rides the existing uts buffer from M1, and
two new `/proc` + `/etc` probes deliver uptime and distro name. No new
dependencies (stdlib + agnosys still cover everything). M3 is the GPU
probe via `ai-hwaccel`.

### Added
- **Slice D — host identity probes** (per
  [ADR 0001](docs/adr/0001-shared-uts-buffer.md) for the uname-backed
  one):
  - `mihi_hostname(uts)` — `utsname.nodename` (offset 65). Reuses the
    same uts buffer the kernel + CPU-arch probes fill, so a consumer
    pays one `uname(2)` for four facts.
  - `mihi_uptime_secs(buf, cap)` — integer seconds from
    `/proc/uptime` first whitespace-separated field. Fractional part
    dropped. Caller supplies 64-byte scratch.
  - `mihi_distro(buf, cap)` — `PRETTY_NAME` from `/etc/os-release`
    with `ID` fallback (the only fallback chain in mihi — justified
    by the os-release spec marking `PRETTY_NAME` as
    recommended-not-required and `ID` as mandatory). Caller supplies
    1 KiB scratch; probe handles quote-stripping in place.
  - `mihi_parse_uptime_secs(buf, len)` — pure parser for the integer
    prefix; exposed for unit tests.
  - `mihi_find_osrelease_key(buf, len, key, key_len)` — line-anchored
    key finder, twin of `mihi_find_meminfo_field`.
  - `mihi_parse_osrelease_value(buf, len, start)` — value parser
    handling both `KEY="quoted"` and `KEY=bare` shapes; mutates the
    buffer to null-terminate.
- Smoke binary now prints `host` / `uptime` / `distro` lines (9
  total facts).
- `docs/sources.md` gains a Slice D table covering the three M2
  probes.
- Test suite: 59 assertions across 24 groups (22 new in M2) —
  synthetic-buffer parser unit tests + real `/proc/uptime` /
  `/etc/os-release` / `uname(2)` happy paths + missing/malformed
  rejection.

## [0.2.0] — 2026-05-19

M1 complete. mihi ships its planned Linux-side CPU/kernel/memory
probe surface — `uname(2)` for kernel + CPU arch, `/sys` for CPU
count, `/proc/cpuinfo` for CPU model, `/proc/meminfo` for total +
available RAM. M2 (host-identity: hostname, uptime, distro) is the
next milestone.

### Added
- **Slice A — uname-backed probes** (share one syscall via a
  caller-supplied 390-byte uts buffer; see [ADR 0001](docs/adr/0001-shared-uts-buffer.md)):
  - `mihi_uname(uts)` — wraps `agnosys_uname(2)`.
  - `mihi_kernel_name(uts)` — `utsname.sysname` (offset 0).
  - `mihi_kernel_version(uts)` — `utsname.release` (offset 130).
  - `mihi_cpu_arch(uts)` — `utsname.machine` (offset 260).
- **Slice B — /proc + /sys parsers**:
  - `mihi_cpu_count()` — logical CPU count from
    `/sys/devices/system/cpu/online`. Returns `0 - 1` on read failure.
  - `mihi_parse_cpu_range(buf, len)` — pure parser for the `%*pbl`
    range-list format ("0-15", "0-3,5-7"); exposed for unit tests.
  - `mihi_cpu_model(buf, cap)` — first `model name` value from
    `/proc/cpuinfo`. Caller supplies an 8 kB scratch buffer; probe
    null-terminates the value in place and returns a cstring ptr.
  - `mihi_parse_cpu_model(buf, len)` — pure parser; line-anchored on
    `"\nmodel name"` so the first-block / one-source-per-fact rule
    holds even on heterogeneous big.LITTLE parts.
- **Slice C — /proc/meminfo**:
  - `mihi_mem_total(buf, cap)` — `MemTotal:` returned as bytes
    (kB × 1024). Caller supplies 4 kB scratch.
  - `mihi_mem_free(buf, cap)` — `MemAvailable:` (kernel's
    reclaimable-aware estimate; preferred over `MemFree:`).
  - `mihi_find_meminfo_field(buf, len, field, field_len)` —
    line-anchored field finder; accepts file-start or
    `'\n'`-prefixed matches.
  - `mihi_parse_meminfo_kb(buf, len, start)` — digit parser that
    skips leading whitespace.
  - `mihi_extract_meminfo_bytes(buf, len, field, field_len)` —
    convenience combining the above two; returns bytes or `0 - 1`.
- `agnosys` and `slice` added to `[deps].stdlib`.
- ADR 0001 — shared uts buffer pattern for uname-backed probes.
- `docs/sources.md` — probe source-citation index (slices A + B + C).
- Test suite: 37 assertions across 17 groups — synthetic-buffer
  parser unit tests + real `/proc` / `/sys` / `uname(2)` happy paths.

### Changed
- Probe signatures take a caller-supplied buffer as documented in
  ADR 0001. Roadmap M1 sketch was zero-arg; current shape is
  `fn mihi_kernel_name(uts): cstring` etc.

## [0.1.0]

### Added
- Initial project scaffold
