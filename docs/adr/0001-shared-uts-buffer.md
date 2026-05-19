# 0001 — Shared uts buffer for uname-backed probes

**Status**: Accepted
**Date**: 2026-05-19

## Context

`uname(2)` returns a 390-byte `utsname` struct containing six fields
mihi cares about: `sysname` (kernel name), `release` (kernel version),
`machine` (CPU arch), `nodename` (hostname). Four mihi probes —
`mihi_kernel_name`, `mihi_kernel_version`, `mihi_cpu_arch`,
`mihi_hostname` — all want fields out of this one struct.

The roadmap (pre-implementation) sketched these as zero-arg functions:
`mihi_cpu_arch()` etc. CLAUDE.md's hard rules constrain the
implementation:

- **Probes are pure reads** — fine, `uname(2)` is read-only.
- **No allocator dependency from probe internals** — rules out a
  module-private heap-allocated `uts` cache.
- **Probes write into caller-supplied buffers; consumers control
  lifetime** — rules out a module-private static `utsname` cell that
  consumers can't observe or invalidate.
- **No caching layer** (roadmap, out-of-scope list) — rules out
  "memoize the first uname call and serve subsequent probes from
  that."

The zero-arg signature can only be satisfied by something the rules
forbid. Each probe issuing its own `uname(2)` (four syscalls to read
one struct) is wasteful and contradicts "one source per fact" — the
fact is the struct, read once.

## Decision

uname-backed probes take a caller-supplied 390-byte `uts` buffer as
their sole argument. Signatures:

```cyrius
fn mihi_uname(uts): i64           # invokes uname(2); Ok(uts) or Err
fn mihi_kernel_name(uts): i64     # ptr to uts.sysname  (null-terminated)
fn mihi_kernel_version(uts): i64  # ptr to uts.release
fn mihi_cpu_arch(uts): i64        # ptr to uts.machine
fn mihi_hostname(uts): i64        # ptr to uts.nodename  (M2)
```

Consumers stack-allocate the buffer once per logical "tell me about
this box" invocation, call `mihi_uname` once, then read whichever
fields they want. The buffer's lifetime is the caller's stack frame;
mihi owns no state.

`/proc`-backed probes (`mihi_cpu_model`, `mihi_mem_total`,
`mihi_distro`, etc.) follow the same pattern — caller supplies a
read buffer; the probe parses out one fact and returns it. This ADR
locks the convention for the whole library, not just uname.

## Consequences

- **Positive** — one syscall serves four facts. No mihi-owned state,
  no allocator dependency. Field-extraction logic is trivially
  unit-testable: tests construct a synthetic uts buffer in stack
  memory and verify offsets without touching `uname(2)`. Mirrors the
  agnosys idiom (`uname_machine(uts)` etc.) consumers may already
  know.

- **Negative** — the signature deviates from the roadmap's zero-arg
  sketch; consumers must allocate the uts buffer and pass it around.
  Cannot write `println(mihi_cpu_arch())` — must be
  `var uts[390]; mihi_uname(&uts); println(mihi_cpu_arch(&uts))`.
  Roadmap section M1 / M2 signature lines need to be updated to
  match.

- **Neutral** — the caller-buffer convention will be reused for every
  `/proc` probe in slice B/C. Will likely justify a `MihiInfo`
  envelope struct at v0.5.0 (iam consumer) that bundles uts +
  meminfo + cpuinfo read buffers behind one `mihi_collect(info)`
  entry — but that's a *convenience wrapper around the same primitives*,
  not a state-owning cache, so it doesn't violate the rule.

## Alternatives considered

- **Zero-arg signatures with module-private static buffer** — rejected:
  violates "consumers control lifetime"; also racy under any future
  multi-threaded consumer.
- **Zero-arg signatures, fresh uname(2) per call** — rejected: four
  syscalls to read one struct; "one source per fact" reads the source
  once.
- **`MihiInfo` envelope as the only public API** — rejected for now:
  forces every consumer to allocate the full envelope even when they
  want one field; revisit at v0.5.0 if iam wants the convenience.
