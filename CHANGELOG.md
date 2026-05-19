# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `mihi_uname(uts)` — wraps `agnosys_uname(2)` into a caller-supplied
  390-byte buffer. Sole syscall for slice-A field accessors.
- `mihi_kernel_name(uts)` — pointer to `utsname.sysname` (offset 0).
- `mihi_kernel_version(uts)` — pointer to `utsname.release` (offset 130).
- `mihi_cpu_arch(uts)` — pointer to `utsname.machine` (offset 260).
- `mihi_cpu_count()` — logical CPU count from
  `/sys/devices/system/cpu/online`. Returns `0 - 1` on read failure.
- `mihi_parse_cpu_range(buf, len)` — pure parser for the `%*pbl`
  range-list format ("0-15", "0-3,5-7"); exposed for unit tests.
- `mihi_cpu_model(buf, cap)` — first `model name` value from
  `/proc/cpuinfo`. Caller supplies an 8kB scratch buffer; probe
  null-terminates the value in place and returns a cstring ptr.
- `mihi_parse_cpu_model(buf, len)` — pure parser; line-anchored on
  `"\nmodel name"` so the first-block / one-source-per-fact rule
  holds even on heterogeneous big.LITTLE parts.
- `agnosys` and `slice` added to `[deps].stdlib`.
- ADR 0001 — shared uts buffer pattern for uname-backed probes.
- `docs/sources.md` — probe source-citation index (slice A + B rows).
- Test suite: 24 assertions across 12 groups — synthetic-buffer
  parser unit tests + real `/proc` / `/sys` / `uname(2)` happy paths.

### Changed
- Probe signatures take a caller-supplied buffer as documented in
  ADR 0001. Roadmap M1 sketch was zero-arg; current shape is
  `fn mihi_kernel_name(uts): cstring` etc.

## [0.1.0]

### Added
- Initial project scaffold
