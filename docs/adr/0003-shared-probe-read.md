# 0003 — a sixth `[lib]` module for the shared probe read

**Status**: Accepted
**Date**: 2026-08-23

## Context

CLAUDE.md says the module shape is part of the v1.0 contract, and that
adding to it needs an ADR. This is that ADR. It exists because the
2026-08-23 P(-1) audit found a defect that lived in five places at
once, and fixing it five times would have guaranteed a sixth copy
later.

Every file-reading probe — `mihi_cpu_count`, `mihi_cpu_model`,
`mihi_mem_total`, `mihi_mem_free`, `mihi_uptime_secs`, `mihi_distro` —
carried its own copy of:

```cyrius
var fd = sys_open(PATH, O_RDONLY, 0);
if (fd < 0) { return ERR; }
var n = sys_read(fd, buf, cap);
sys_close(fd);
if (n <= 0) { return ERR; }
return parse(buf, n);
```

Six copies, one shape, and the shape is wrong in three ways (audit
findings A-1, and the two sub-cases folded into it):

1. **A filled buffer is indistinguishable from EOF.** `sys_read`
   returning exactly `cap` could mean "that was the whole file" or
   "there is more". The parsers then ran over a truncated buffer and —
   this is the part that matters — returned a *plausible value*, not an
   error. `MemTotal:  61192260 kB` cut after `611` parses as 611 kB.
   For a library whose entire product is facts about the box, a
   confidently wrong fact is a worse outcome than an error, and
   CLAUDE.md already says so in different words: *one source per fact …
   if it's not present, return error.*
2. **A short read was treated as EOF.** `read(2)` may return fewer
   bytes than asked for. seq_file-backed `/proc` and kernfs-backed
   `/sys` files do not do this in practice when the count is large
   enough, but "in practice" is not a contract, and the failure mode is
   again a silently short parse rather than an error.
3. **`-EINTR` was a hard failure.** A signal landing mid-read made the
   probe report the fact as missing. mihi's first consumer renders the
   login MOTD; a spurious blank field there is exactly the kind of
   flake nobody ever reproduces.

Two further hardening measures also belong at this layer, and would
otherwise have to be pasted six times: `O_NONBLOCK` (so a repointed
`/etc/os-release` symlink landing on a FIFO cannot hang a login) and
`O_CLOEXEC`.

## Decision

Add `src/io.cyr` as the second entry in `[lib].modules`, after
`types.cyr` and before every probe module that calls into it. It
exports one internal function:

```cyrius
fn _mihi_read_probe_file(path, buf, cap, mode): i64
```

returning a byte count, `0 - MIHI_IO_FAIL`, or `0 - MIHI_IO_TRUNC`.

`mode` is the part worth arguing about. Truncation is fatal for five of
the six call sites and *expected* for the sixth:

- `MIHI_IO_WHOLE` — `/proc/meminfo`, `/proc/uptime`, `/etc/os-release`,
  `/sys/devices/system/cpu/online`. Each parser extracts a value that a
  cut could silently shorten, so a file larger than `cap` is an error.
- `MIHI_IO_PREFIX` — `/proc/cpuinfo`, and only `/proc/cpuinfo`. That
  file is one block per logical CPU: 26 kB on the 16-thread box this
  was measured on, and it grows with core count, so no fixed
  recommendation could ever mean "the whole file fits". The probe
  deliberately wants CPU 0's block (see `mihi_parse_cpu_model` on why
  it anchors there), and its parser returns null rather than a partial
  value when the buffer ends mid-line. Truncation is the normal case.

Making the mode explicit at each call site — rather than inferring it,
or defaulting it — is the point. It was the first thing the change got
wrong: a uniformly strict helper turned `mihi_cpu_model` into a
permanent failure on any machine with more than about five cores,
which the smoke binary caught immediately.

## Consequences

- **Positive** — the three defects are fixed once. New probes that read
  a file get the hardened path by construction rather than by whoever
  writes them remembering.
- **Positive** — the hardened path is testable in isolation. Slice F of
  `tests/mihi.tcyr` asserts the truncation split, the failure sentinel,
  and the degenerate-`cap` guard directly against the helper, rather
  than only through whichever probe happens to exercise it.
- **Positive** — `O_NONBLOCK` / `O_CLOEXEC` are stated once, so they
  cannot drift apart between probes.
- **Negative** — the bundle grows a module, and consumers re-including
  `dist/mihi.cyr` pick up one more symbol (`_mihi_read_probe_file`,
  plus the `MihiIoMode` / `MihiIoStatus` enum members). Cyrius has one
  flat symbol table and last-definition-wins, which is exactly how
  ai-hwaccel's `BACKEND_COUNT` collided with kavach's; every name here
  is therefore `_mihi_`- or `MIHI_IO_`-prefixed.
- **Negative** — `[lib].modules` order now carries a real dependency
  edge (`io.cyr` must precede `cpu`/`mem`/`host`), where before the
  order was only conventional. Recorded in the `cyrius.cyml` comment
  next to the list.
- **Neutral** — the module is inert on AGNOS. Every probe takes a
  `sysinfo(2)` / CPUID / constant path there, so the body is
  `#ifndef CYRIUS_TARGET_AGNOS`. That is load-bearing, not tidiness:
  `O_CLOEXEC` and `O_NONBLOCK` are not defined on the AGNOS target, so
  the flags must be removed by the preprocessor rather than merely left
  unreached.

## Alternatives considered

- **Fix the five copies in place.** Rejected: it is the same edit five
  times with five chances to get one wrong, and it leaves the next
  probe to reinvent it. The audit found this defect precisely because
  duplicated code drifts.
- **Put the helper in `types.cyr`.** Rejected: `types.cyr` is the
  shared-types module (empty today, `MihiInfo` deferred per ADR 0001).
  Putting an I/O function there is a module-shape change wearing a
  disguise — it would still need this ADR, and it would leave the
  library with no honest home for the next non-type shared helper.
- **Put the helper at the top of `cpu.cyr`.** Rejected for the same
  reason plus a worse one: `mem`/`host` would then depend on a *probe*
  module for their I/O, making the bundle order load-bearing in a way
  no comment would survive.
- **Take the read from the cyrius stdlib (`lib/fs.cyr`).** Rejected:
  mihi's probe internals must not grow a dependency they do not
  control, and none of the stdlib readers implement the
  truncation-detection contract this needs. `fs.cyr` is also not in the
  set the AGNOS build can rely on. The whole helper is 30 lines of
  syscalls.
- **Return a status out-param instead of encoding it in the return.**
  Rejected: every other function in mihi signals failure with a
  negative return, and a caller-supplied status pointer is a second
  buffer the caller has to own — against ADR 0001's grain.

## References

- [`docs/audit/2026-08-23-audit.md`](../audit/2026-08-23-audit.md) — findings A-1 … A-4, D-1 … D-3
- [ADR 0001](0001-shared-uts-buffer.md) — caller-supplies-buffer convention
- [ADR 0002](0002-gpu-singleton-cache.md) — the other place mihi departs from the plain-probe shape
