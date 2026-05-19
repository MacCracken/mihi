# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `mihi_uname(uts)` — wraps `agnosys_uname(2)` into a caller-supplied
  390-byte buffer. Sole syscall for slice-A field accessors.
- `mihi_kernel_name(uts)` — pointer to `utsname.sysname` (offset 0).
- `mihi_kernel_version(uts)` — pointer to `utsname.release` (offset 130).
- `mihi_cpu_arch(uts)` — pointer to `utsname.machine` (offset 260).
- `agnosys` and `slice` added to `[deps].stdlib`.
- ADR 0001 — shared uts buffer pattern for uname-backed probes.
- `docs/sources.md` — probe source-citation index.
- Test suite filled: 12 assertions across the three slice-A probes
  (real-uname happy path + synthetic-buffer offset round-trip + error
  contract on zero-init uts).

### Changed
- Probe signatures take a caller-supplied buffer as documented in
  ADR 0001. Roadmap M1 sketch was zero-arg; current shape is
  `fn mihi_kernel_name(uts): cstring` etc.

## [0.1.0]

### Added
- Initial project scaffold
