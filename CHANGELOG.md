# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
