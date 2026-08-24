# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.2.4] — 2026-08-23

**The two things 1.2.3 left open, closed on real hardware.** 1.2.3's audit filed
D-1 (`mihi_cpu_model` returns null on aarch64 Linux) as needing arm64 hardware,
and shipped A-5's AGNOS `mem_free` arm compile-verified only. Both are now
verified by running, not by reading.

### Added

- **aarch64 Linux CPU-model source — D-1 closed.** `mihi_cpu_model` gains a third
  arm: on arm64 Linux it reads `/sys/firmware/devicetree/base/cpus/cpu@0/compatible`
  and returns the device tree's own statement of CPU 0's model. Not a fallback —
  a separate arch-native source, the same shape as the AGNOS→CPUID split, and it
  anchors to `cpu@0` for the same big.LITTLE reason `"\nmodel name"` anchors the
  x86 path. This is the source the *original*, wrong citation named before D-1
  corrected it; it turns out to have been right about where to look and wrong
  about the kernel printing it into `/proc/cpuinfo`.

  **Verified on iron** — agnosarm, Raspberry Pi 4 Model B, Ubuntu 24.04.4,
  kernel 6.8.0-1053-raspi:

  ```
  arch:    aarch64
  model:   arm,cortex-a72        ← was: probe returned 0, smoke exited 1
  cpus:    4
  distro:  Ubuntu 24.04.4 LTS
  mihi smoke ok
  ```

  ⚠ Device-tree only. An arm64 machine booted via ACPI (most server hardware)
  has no `/sys/firmware/devicetree`, so the probe still returns 0 there — D-1's
  honest null, narrowed from "all of aarch64" to "ACPI-booted aarch64". Also
  note the two Linux arms return different *flavours* of string: x86 gives a
  marketing brand (`AMD Ryzen 7 5800H with Radeon Graphics`), the device tree
  gives a compatible tuple (`arm,cortex-a72`). mihi returns each raw, vendor
  prefix included; prettifying is the consumer's job.
- **`mihi_parse_dt_string(buf, len)`** — pure parser for a device-tree string
  property. A DT blob *is* the value and carries its own NUL (15 bytes for
  `"arm,cortex-a72\0"`, no trailing newline), and `compatible` may hold a
  NUL-separated list, most specific first — so returning the first entry is the
  DT convention, not a shortcut. A blob with no terminator is malformed and
  returns 0 rather than being repaired in place.
- **`programs/agnos_probe.cyr`** — the AGNOS-clean probe subset (five modules;
  no `gpu.cyr`, therefore no ai-hwaccel). Prints every fact as a raw integer or
  string with **no early return on a failed probe**, so one boot shows the whole
  surface and an older binary can be compared against it line for line.
- **`scripts/mihi-agnos-verify.py`** — QEMU harness that boots the real agnos
  kernel over gnoboot+OVMF, drives agnsh via HMP `sendkey`, and runs the probe
  **with a control arm in the same boot**. Per the agnos harness README's rule
  that a test which would also pass when broken is worthless, PASS *requires*
  the control to fail; a green control is reported as INCONCLUSIVE, not a pass.
- **Cross-target build gate in CI** — `--agnos` and `--aarch64` now compile on
  every run. The arch arms are the part of mihi that rots silently, because they
  are compiled out on the runner: D-1 sat undetected since 0.2.0 for exactly
  that reason.
- **Test coverage**: `mihi_parse_dt_string` blob shapes (terminated, list,
  unterminated, empty, zero-length) run on every target; an aarch64-only group
  asserts the DT tuple shape, that CPUID yields nothing there, and — the D-1
  claim itself — that `/proc/cpuinfo` carries no model-name line. The
  x86-only CPUID-vs-`/proc` group is now arch-guarded so the suite runs on both.
  **143 on x86, 144 on aarch64** (the arm64 build drops 5 CPUID assertions and
  adds 6 device-tree ones).

### Verified

- **A-5 on the real sovereign kernel.** `scripts/mihi-agnos-verify.py`, one boot,
  both binaries:

  | | control (pre-A-5, `188a7d3`) | this tree |
  |---|---|---|
  | `free B:` | **-1** | **489295872** |

  with `total B: 535580672`, `cpus: 1`, `uptime: 43`, `kernel: AGNOS`,
  `distro: AGNOS` — free ≤ total, figures internally consistent. The control
  failing at the same call in the same boot is what makes this a measurement
  rather than an assertion.
- **The full suite on arm64 hardware**: 144 passed, 0 failed on agnosarm.
- Host: 143 passed / 0 failed, smoke clean with empty stderr, whole CI workflow
  replayed locally.

### Notes

- **`programs/smoke.cyr` cannot run on AGNOS, and that is not new.** Built
  `--agnos` it faults before its first println — `run: exit 142`, measured in
  QEMU for the pre-A-5 binary and this tree's alike — because it links
  `src/gpu.cyr` and therefore the ai-hwaccel bundle, mihi's standing agnos
  blocker (ai-hwaccel → thread → atomic → Linux `CLONE_VM`). Every previous
  agnos claim in this repo went through `iam`, which links mihi without the gpu
  module. `agnos_probe.cyr` exists so mihi can answer for itself.
- **The control arm earned its keep on its first run.** The first attempt built
  the "1.2.2 control" from `HEAD`, which had moved on to 1.2.3 and already
  carried the A-5 fix — so the control passed, and the harness correctly refused
  to call the run a pass. Rebuilt from `188a7d3` (the last commit with a
  `mihi_mem_free` that had no AGNOS arm), it printed `-1` as predicted.

## [1.2.3] — 2026-08-23

**P(-1) audit / hardening sweep.** Second full audit of the probe surface (the
first was 2026-05-19, pre-0.6.0). Six code fixes, four documentation corrections,
one new `[lib]` module with an ADR behind it, and 21 new regression assertions —
**116 → 137**. Probe API unchanged; every signature, return shape and error
sentinel is the same as 1.0.0. Full write-up, including the CVE research and the
before/after benchmark, in [`docs/audit/2026-08-23-audit.md`](docs/audit/2026-08-23-audit.md).

Two things in here are worth a consumer's attention. **A-4** is the only finding
across both audits whose failure mode was a memory-safety event rather than a
wrong number. And **`mihi_cpu_model` got 126% slower** — deliberately; it was
reading 3288 bytes of the 8192 its caller asked for, and now reads all of it.

### Added

- **`src/io.cyr`** — a sixth `[lib]` module holding `_mihi_read_probe_file`, the
  one `/proc` + `/sys` read path. The same `open / one read / close` block had
  been pasted into six probes, carrying the same three defects in each copy, so
  the fix is a module rather than six edits. Module-shape changes need an ADR per
  CLAUDE.md: [ADR 0003](docs/adr/0003-shared-probe-read.md), which also records
  why `types.cyr` and `cpu.cyr` were the wrong homes and why the stdlib's reader
  was not used. `[lib].modules` order now carries a real dependency edge —
  `io.cyr` precedes `cpu`/`mem`/`host`.
- **Slice F of `tests/mihi.tcyr`** — 21 assertions across 8 groups, one per
  finding that produced a code change, each written to fail against the 1.2.2
  source. Includes the previously untested key-prefix case (`VERSION_ID=` must
  not satisfy a search for `ID=`).
- **`cyrius fmt --check` and required-files coverage for ADR 0003** in CI.

### Fixed

- **A-1 — silent truncation, short reads, and `-EINTR`, in six places.** A
  `sys_read` that filled the buffer was indistinguishable from EOF, so an
  undersized buffer produced *a plausible wrong value rather than an error*:
  `mihi_uptime_secs(&buf, 4)` against a 20-byte `/proc/uptime` returned the first
  four digits as a whole uptime. The short-read half was **not theoretical** —
  measured on the test host, a single `read(fd, buf, 8192)` on `/proc/cpuinfo`
  returns **3288 bytes** and it takes three reads to fill 8192, so
  `mihi_cpu_model` had been parsing 3288 bytes of its caller's 8192 on every call
  since 0.2.0. It worked only because `model name` sits ~1.6 kB in. Now: looped
  reads, `-EINTR` retried (bounded at 8), and truncation detected with one extra
  single-byte read when the buffer fills. Truncation is fatal for
  `/proc/meminfo`, `/proc/uptime`, `/etc/os-release` and
  `/sys/devices/system/cpu/online` (`MIHI_IO_WHOLE`) and expected for
  `/proc/cpuinfo` (`MIHI_IO_PREFIX`), which is one block per logical CPU — 26 kB
  on a 16-thread box — and whose parser deliberately wants only CPU 0's block.
  `/sys/devices/system/cpu/online`'s scratch grew 64 → 1024 bytes at the same
  time: it is a `%*pbl` *range list*, so a machine with many offline CPUs
  produces a long value that 64 bytes cut mid-range.
- **A-1 (cont.) — `O_NONBLOCK` + `O_CLOEXEC` on the probe open.** os-release(5)
  says `/etc/os-release` *should* be a symlink, so `O_NOFOLLOW` is not available
  to mihi; a symlink repointed at a FIFO would otherwise hang the caller on
  `open(2)`, and mihi's first consumer renders the **login MOTD**, where a hang
  is a login denial. `O_NONBLOCK` turns that into an immediate `-EAGAIN` and an
  honest probe error. Inert on regular/procfs/sysfs files.
- **A-2 — `mihi_parse_cpu_range` accumulated `total` without a bound.** 0.6.0's
  C-2 capped each range bound at 18 digits, bounding every *addend* below 10^18,
  but not the running total; ten such ranges wrap i64 negative. Previously
  unreachable by arithmetic (the 64-byte buffer could not hold enough ranges) —
  A-1's larger buffer is what made it live. Now capped at `MIHI_CPU_MAX` (2^20,
  two orders of magnitude past Linux's 8192-CPU `CONFIG_NR_CPUS` ceiling), over
  which the input is reported malformed.
- **A-3 — the `kB → bytes` scale could return a NEGATIVE byte count.** 0.6.0's
  M-1 capped `mihi_parse_meminfo_kb`'s accumulator at 18 digits; nobody re-checked
  the `* 1024` that consumes its result, and 10^18 × 1024 is four times i64 max.
  Measured: `MemTotal: 999999999999999999 kB` returned **-9017668127734891520**.
  Now rejected above `MIHI_MEM_KB_MAX` (2^53 - 1 = floor(i64max / 1024), ~9 EiB
  of RAM) rather than saturated — a value that large is a corrupt fact, not a
  truncated one.
- **A-4 — `mihi_uname` left the caller's buffer uninitialised on failure.** The
  four field accessors are pure pointer math and, per the ADR 0001 contract,
  deliberately do not check that the fill succeeded. So a caller that ignored the
  `Result` — the easiest mistake to make against this API — got a "cstring"
  pointing into uninitialised stack **with no NUL in it**, and the consumer's
  `println()` walked off the buffer. The only place in mihi where a caller
  mistake became an out-of-bounds read rather than a wrong value, and reachable
  on any target where `sys_uname` is unwired (`lib/sys.cyr` returns `-ENOSYS` for
  Windows). Now zeroes `UTS_SIZE` bytes first; worst case becomes an empty
  string, which the existing zero-init test already covers.
- **A-5 — `mihi_mem_free` had no AGNOS arm.** Alone among the file-reading
  probes it fell through to a Linux `open("/proc/meminfo")` the sovereign kernel
  cannot satisfy, so it returned `0 - 1` permanently. The 1.1.2 note justified
  that as "no sysinfo equivalent", which stopped being true when `lib/sys.cyr`
  grew the AGNOS §4.4 layout — `freeram` sits at `SI_FREERAM`. ⚠ The semantics
  differ and are documented rather than hidden: Linux reports `MemAvailable`
  (free + reclaimable), AGNOS reports plain free.
- **D-3 — single-quoted `os-release` values were returned with their quotes.**
  os-release(5) permits single *or* double quotes; `mihi_parse_osrelease_value`
  tested only `"`, so `PRETTY_NAME='Some Linux'` fell through to the bare branch
  and came back as `'Some Linux'`. Survived two audits because every mainstream
  distro uses double quotes. Backslash escaping remains deliberately
  unimplemented and is now documented as a known limit rather than silently
  absent.

### Changed

- **Documentation corrections (D-1, D-2, D-4).** CLAUDE.md requires a source
  citation on every probe; three were wrong or misleading, which matters more
  than usual here because the citation *is* what a consumer reasons about.
  **D-1**: `mihi_cpu_model` cited a device-tree source for aarch64 that the
  kernel does not print — arm64's `c_show()` emits no `model name` line at all,
  so the probe returns 0 on every aarch64 Linux box. Corrected; closing the gap
  needs arm64 hardware and is filed in `roadmap.md`. **D-2**: the `mihi_distro`
  fallback was justified on `ID` being "the mandatory minimum every distro must
  ship" — os-release(5) makes **both** `ID` and `PRETTY_NAME` optional, with
  documented defaults. The fallback stands, on the weaker true reason. **D-4**:
  "recommend 8192" for `/proc/cpuinfo` read as "the file fits"; it is "CPU 0's
  block fits", and leaving that implicit broke `mihi_cpu_model` during this very
  sweep when the first cut of A-1's fix treated truncation as fatal everywhere.
- **[ADR 0002](docs/adr/0002-gpu-singleton-cache.md) amended** for finding A-6:
  1.2.2's `sakshi` log-level clamp put a second passenger in the first-call
  TOCTOU window the ADR already documents. Under the interleaving *A saves INFO
  → A clamps → B saves WARN → A restores INFO → B restores WARN*, the process is
  left at `SK_WARN` permanently. No exposure today (every consumer is
  single-threaded at first GPU probe, the same precondition the ADR already
  relies on) and no fix — a lock would put a threading dependency inside a probe.
  ADR 0002's alternative-3 now has a second reason to exist.
- **`mihi_cpu_brand_fill`'s capacity contract strengthened in place** (finding
  A-7). It stores 48 bytes through `buf` and takes no `cap`; only its in-tree
  caller checks. It carries no leading underscore, so it is on the bundle's
  public surface. Adding a `cap` parameter is a signature change against a frozen
  API — a v2.0 item; until then the comment is the contract.
- **`docs/sources.md`** gains a "shared read path" section and per-probe notes
  for every behavioural change above; **`docs/development/roadmap.md`** gains the
  arm64 CPU-brand item.

### Performance

Re-measured against the 1.2.2 source built in a scratch worktree on the same
host, kernel and toolchain, so the delta is the code and nothing else:

| Probe | 1.2.2 | 1.2.3 | Δ |
|---|---:|---:|---:|
| `mihi_uname` | 481 ns | 1.014 µs | +533 ns (A-4 zeroing, once per process) |
| `mihi_cpu_model` | 37.34 µs | 84.51 µs | **+126%** (reads all 8192 bytes, not 3288) |
| everything else | — | — | +3% … +16% (helper call + two open flags) |

Pure parsers (25–411 ns) and field accessors (2–3 ns) unchanged. Rejected the
obvious mitigation — a single-read `MIHI_IO_PREFIX` — because it restores the
defect: `/proc/cpuinfo`'s first read contains `model name` by where the kernel
happens to put the field, not by guarantee. 47 µs once per process on the login
path is not worth buying that fragility back.

### Verified

Whole CI workflow replayed locally step by step. `cyrius deps --verify` 109/0;
build clean; smoke exits 0 with empty stderr; `--agnos` cross-build compiles with
the CPUID path intact; fmt clean across all 14 hand-written sources; lint clean;
distlib byte-deterministic; DCE parity; security scan 0; benchmark baseline
appended to `docs/benchmarks/history.csv`. **`cyrius test tests/mihi.tcyr`: 137
passed, 0 failed.**

## [1.2.2] — 2026-08-23

Toolchain / dependency maintenance cut. Cyrius pin **6.2.37 → 6.5.35**, ai-hwaccel
**2.2.6 → 2.3.18**. Probe API unchanged (frozen since 1.0.0) — but the ai-hwaccel jump
crosses two of its deliberate symbol renames and introduces a `sakshi` logging
dependency, so this cut is not purely mechanical. Consumers repinning to mihi 1.2.2
must repin ai-hwaccel to 2.3.18 in lockstep and add `"sakshi"` to their `[deps] stdlib`
(the new `dist/mihi.deps` sidecar declares it for them).

### Changed

- **`cyrius.cyml`: pin `6.2.37` → `6.5.35`** — closes the wrapper/manifest drift
  (installed toolchain was already 6.5.35; `cyrius --version` had been reporting it).
  `cyrius lib sync --full` re-vendored the version-matched snapshot into `lib/`: **108
  `.cyr` files**, of which 7 are the new `lib/unicode/` sub-package (`casefold` /
  `categories` / `normalize` + their data folds). Also new to mihi's `lib/` since the
  6.2.22-era snapshot it was carrying: `async_macos`, `async_win`, `thread_macos`,
  `yantra`. mihi links none of them directly; DCE drops them from the binary.
- **`cyrius.cyml`: `[deps.ai-hwaccel] tag = "2.2.6"` → `"2.3.18"`.** Twelve upstream
  releases, three of them ecosystem-wide symbol de-collisions: 2.3.13 (`ERR_*` →
  `HWA_ERR_*`), 2.3.14 (`registry_new` → `hw_registry_new`, clearing a real collision
  with bote-core's 24-byte tool registry), and 2.3.18 (`BACKEND_COUNT` →
  `AIHW_BACKEND_COUNT`, `enum Backend` → `AiHwBackend`, `path_exists` →
  `aihw_path_exists`, clearing a bounds-check collision with kavach). Only 2.3.14's
  reaches mihi — and only the test suite, not the probe source (see below); mihi
  references no ai-hwaccel error constants and no backend enum members.
- **`cyrius.cyml`: `sakshi` added to `[deps] stdlib`.** ai-hwaccel 2.3.x routes its
  detect-path diagnostics through `sakshi`; the bundle is one concatenation, so the
  parser needs the module in scope even though mihi calls no logging of its own.
- **`src/gpu.cyr`: `_mihi_gpu_ensure()` clamps the log level across detection.**
  `sakshi`'s default level is `SK_INFO`, so a bare `registry_detect_no_exec()` writes
  `detect: profiles=N` to **the consumer's stderr** — a library scribbling on a caller's
  terminal, and for `iam` / `chakshu` that means a corrupted card/TUI frame. ai-hwaccel's
  own programs avoid this by calling `hwlog_init()` (which sets `SK_WARN`); mihi can't,
  because permanently resetting a level the consumer chose is just as rude. So mihi saves
  the caller's level, clamps to `SK_WARN` for the one detect call, and restores. Process-
  local state, saved and put back — the "probes are pure reads" rule (no file/system
  mutation, no subprocess) is untouched.
- **`tests/mihi.tcyr`: `registry_new()` → `hw_registry_new()`** at the four synthetic-
  registry construction sites. Without this the suite failed to compile against 2.3.18
  (`error: refusing to emit binary with 1 reachable undefined function(s)`) — upstream
  deliberately kept no back-compat alias, since an alias by that name would reintroduce
  the collision it was renamed to remove.
- **Stale vendored modules pruned from `lib/`** — ten files absent from the 6.5.35
  snapshot and undeclared in `[deps] stdlib`: `agnosys.cyr` + `agnosys-core.cyr` (the
  stdlib snapshot cyrius retired at 6.2.37; mihi rewired off the dep at 1.1.3),
  `base64` / `bigint` / `csv` / `cyml` / `toml` / `u128` (folded into the `bayan`
  distribution in the 6.2.x reorg — the same prune 1.1.1 did for `json`, finished here),
  and `linalg` / `matrix` (folded into `ganita`). Same class of orphan the 1.1.1 note
  flagged; `lib/` now matches the pinned snapshot exactly, 108 stdlib modules + the
  ai-hwaccel dep.
- **`tests/mihi.tcyr` normalized to canonical cyrfmt layout.** Twenty-five continuation
  lines used aligned-to-open-paren indentation; canonical style is 2 spaces per open
  paren. Whitespace-only — `git diff -w` is empty, 116 passed / 0 failed before and
  after, and `cyrius fmt` is idempotent on the result. The drift predated this cut; the
  new gate above is what stops it recurring. No `[lib].modules` file was touched, so
  `dist/` is unaffected.

### Added

- **cyrfmt gate in `.github/workflows/ci.yml`** — every hand-written Cyrius source
  (`src/*.cyr`, `programs/*.cyr`, `tests/*.tcyr`, `benches/*.bcyr`) is checked with
  `cyrius fmt <file> --check`; drift fails the build. Sits next to the lint step, since
  both are static checks. Mirrors the ai-hwaccel 2.3.18 gate with two deliberate
  differences: the offending-line diagnostic is left on stdout rather than sent to
  `/dev/null` (the line number is the actionable part), and the loop reports *every*
  offender before exiting instead of stopping at the first. `dist/mihi.cyr` is
  intentionally out of scope — it is `cyrius distlib` output, so its layout is the
  generator's contract, already covered by the drift + determinism gates.
- **`cyrius deps --verify` gate in CI.** mihi is unusual among the siblings in having a
  real `cyrius.lock` (109 entries — the vendored stdlib snapshot plus the commit-pinned
  ai-hwaccel dep) *and* a committed `lib/` rather than a gitignored one, so `--verify`
  hashes what's checked in against what the lock claims. It catches a hand-edited
  vendored file (which CLAUDE.md forbids) or a `lib/` snapshot that has drifted from the
  pinned toolchain. For the same reason the workflow deliberately does **not** gain a
  `cyrius lib sync` step: siblings that gitignore `lib/` need one, but here it would
  overwrite 109 tracked files and mask the very drift this gate exists to surface.
- **`dist/mihi.deps`** — the stdlib-leaf sidecar `cyrius distlib` emits alongside the
  bundle as of cyrius 6.5.x, listing the 21 stdlib modules mihi's fold needs in scope.
  Consumers' `cyrius deps` reads it, so it has to be checked in next to `dist/mihi.cyr`.
  Wired into all three places the bundle already was: the CI drift check (a stale sidecar
  breaks consumers exactly the way a stale bundle does), the required-files gate, and the
  release tarball.
- **Test group `gpu.cyr — detect restores the caller's sakshi level`** (3 assertions).
  Asserts both halves of the clamp: a verbose caller (`SK_DEBUG`) gets its level back
  after a cold detect, and an already-quiet caller (`SK_ERROR`) is never raised. **113 →
  116 assertions.**

### Fixed

- **CI installed the toolchain by hand instead of using the upstream installer.** Both
  workflows `curl`'d `cyrius-<v>-x86_64-linux.tar.gz` from the GitHub release and `cp`'d
  it into `$HOME/.cyrius/{bin,lib}` — with `2>/dev/null || true` on every copy, so a
  fetch failure or an upstream layout change left the step **green with nothing
  installed**. It also produced a flat `lib/` with no `versions/<v>/` and no `current`,
  which is the layout `cyrius lib sync` and the wrapper's own drift detector read, and it
  skipped the installer's Ed25519 release-signature verification entirely. Both
  `ci.yml` and `release.yml` now read the `[package].cyrius` pin (anchored `^cyrius = `,
  so it can't match `language = "cyrius"`) and pipe it to
  `cyrius/scripts/install.sh` — the same block patra and libro use. `set -e` plus an
  empty-pin guard replace the swallowed errors.
- **Stale CI comments** — the "Resolve dependencies" step still described mihi as pulling
  `agnosys` (dropped at 1.1.3; uname/sysinfo come from `lib/sys.cyr`), and the DCE parity
  step attributed its ~1600 unreachable fns to agnosys rather than the ai-hwaccel bundle.
- **Stale doc references** — `docs/sources.md` cited ai-hwaccel 2.2.6 and an "8 exec / 8
  sysfs" backend split; 2.3.18 has 18 backends, 9 exec / 9 no-exec (`BACKEND_WINDOWS`
  joined the exec set, `BACKEND_AGNOS_GPU` the no-exec one — the latter is reserved
  upstream with **no detector dispatch wired yet**, so mihi's behavior is unchanged).
  `README.md`'s Status section still read "Pre-1.0 scaffold (0.1.0) … bodies return 0.
  Not yet usable" — three minor versions past the API freeze.
  `docs/development/state.md` was stranded at 1.1.1 and is refreshed through 1.2.2;
  `roadmap.md`'s "Pending upstream — agnosys → agnodrm" item closed at 1.1.3 but was
  never checked off.

### Verified

- `cyrius deps` resolves (109 locked, ai-hwaccel commit-pinned at 2.3.18); build clean;
  smoke exits 0 **with empty stderr** (the regression this cut fixes); `--agnos`
  cross-build compiles, and the 1.2.1 CPUID brand path is still in the agnos binary
  (`cpuid` instruction count matches the native build). Lint clean under the CI policy,
  and the new fmt gate passes across all 13 hand-written sources; all three
  `benches/*.bcyr` compile; DCE parity holds; `cyrius distlib` byte-deterministic across
  two runs. **`cyrius test tests/mihi.tcyr`: 116 passed, 0 failed.**

## [1.2.1] — 2026-07-02

**Fix: the CPUID CPU-model path was compiled OUT on agnos in 1.2.0.** 1.2.0 added
`mihi_cpu_model_cpuid` under `#ifdef CYRIUS_ARCH_X86`, but `cyrius build --agnos` does
**not** predefine `CYRIUS_ARCH_X86` (only a native x86 build does) — so the `cpuid` asm
was stripped from the agnos build and `iam` still rendered `CPU: (unknown)`. Verified
in QEMU (agnos, KVM): iam now prints the real brand (`AMD Ryzen 7 5800H …`).

### Changed

- **`src/cpu.cyr`: `#define CYRIUS_ARCH_X86` when `CYRIUS_TARGET_AGNOS` is set** — agnos
  *is* x86, so map it, and the existing `#ifdef CYRIUS_ARCH_X86` brand-string asm now
  compiles into the agnos build (0 → 3 `cpuid` instructions in the agnos binary). A
  future aarch64-agnos would set `CYRIUS_ARCH_AARCH64` and skip this.
- **`mihi_cpu_brand_fill` uses `param_load(rdi, 0)`** (sigil `_sha_ni_cpuid_probe` idiom)
  to load the buffer param — prologue-drift-proof, vs the 1.2.0 hand-assumption that
  `buf` stayed in `rdi`. (Belt-and-suspenders; the real 1.2.0 agnos miss was the guard.)

### Verified

- Native Linux test suite green (CPUID-brand-vs-/proc prefix check). **agnos (QEMU/KVM):**
  `iam` renders the full card with the real CPU brand — `scripts/iam-agnos-verify.py` PASS.

## [1.2.0] — 2026-07-02

**CPU probe made sovereign on AGNOS.** `iam` rendered `CPU: (unknown)` on agnos because
`mihi_cpu_model` read `/proc/cpuinfo`, which agnos has no procfs for. The CPU *brand* is
the same datum `/proc/cpuinfo`'s "model name" is printed from — CPUID leaves
0x80000002/3/4 — so this reads it straight from the instruction, which works bare-metal on
any x86 target. (The uname-backed probes — arch / kernel / hostname — were already
agnos-correct via cyrius's per-target `UTS_*` offsets, `sys.cyr` 6.1.28+; no change there.)

### Added

- **`mihi_cpu_model_cpuid(buf, cap)` + `mihi_cpu_brand_fill(buf)`** (`src/cpu.cyr`): read the
  48-byte CPUID processor brand string (leaves 0x80000002/3/4, EAX/EBX/ECX/EDX each) and
  trim it (AMD NUL-pads / Intel space-pads, plus Intel's leading-space left-pad). The fill
  is a hand-asm block whose first statement keeps arg1 (`buf`) live in `rdi` — `cpuid`
  clobbers rax/rbx/rcx/rdx (rbx push/pop'd per leaf) but not rdi. x86-only (`CYRIUS_ARCH_X86`).

### Changed

- **`mihi_cpu_model`** now dispatches: **AGNOS → CPUID brand** (no `/proc`), **Linux → `/proc/cpuinfo`**
  (unchanged). Same `(buf, cap) → cstring` API — consumers (iam, chakshu) are unaffected.
- **`mihi_cpu_count`** on AGNOS: was a hardcoded `return 1` (stale — the `smp_wake_enabled=0`
  single-core gate was lifted; the kernel wakes APs, iron-confirmed `cpus online: 4` on
  archaemenid). Now reads the kernel's enumerated count from `sysinfo`#35 (§4.4 `cpus` field,
  `SI_CPUS`). Linux path (`/sys/devices/system/cpu/online`) unchanged.

### Verified

- **CPUID hand-asm validated on the x86 Linux host** (the whole point of doing it CPUID-side):
  new test `mihi_cpu_model_cpuid matches /proc (x86 host)` asserts the brand string is a
  prefix of `/proc/cpuinfo`'s "model name" — **113 passed, 0 failed**. Smoke prints the real
  brand (`AMD Ryzen 7 5800H with Radeon Graphics`). The identical CPUID instruction on agnos
  makes this the pre-iron proof; iam-on-agnos is the runtime confirmation (next burn).

## [1.1.3] — 2026-06-22

### Changed

- **Rewired off `agnosys` onto the native `sys` stdlib module.** The identity probes'
  single `uname`#34 + `sysinfo`#35 path went through the `[deps.agnosys]` git dep
  (`agnosys_uname` / `query_sysinfo`). cyrius retired the stale stdlib `agnosys`
  snapshot at **6.2.37**, so this **drops the agnosys git dependency entirely** and
  rewires to `lib/sys.cyr`'s `sys_uname` / `sys_sysinfo` (the same uname/sysinfo
  plumbing carved off agnosys at cyrius 6.1.28, with per-target `UTS_*` / `SI_*`
  offsets for Linux **and** AGNOS — agnos reads the sovereign 64-byte uname struct,
  release@32). `mihi_uname` now wraps the raw `0/-errno` return as a `Result` so
  consumers checking `is_err_result` (iam) are unaffected; **no probe-API change**.
  cyrius pin `6.2.22` → `6.2.37`; `dist/mihi.cyr` regenerated; host + `--agnos`
  builds verified. This is the mihi half of the agnosys-retirement consumer rewire —
  chakshu can now drop its stdlib `"agnosys"` entry.

## [1.1.2] — 2026-06-19

AGNOS build-target support for the probes. Probe API unchanged.

### Added

- **`#ifdef CYRIUS_TARGET_AGNOS` branches** for the probes that read Linux `/proc`+`/sys` (absent on the sovereign kernel):
  - `mihi_mem_total` → `query_sysinfo` / `sysinfo_total_memory` (sysinfo#35, bytes).
  - `mihi_uptime_secs` → `sysinfo_uptime` (sysinfo#35, seconds).
  - `mihi_cpu_count` → `1` (committed single-core gate, agnos 1.44.24; revisit when SMP unlocks).
  - `mihi_distro` → `"AGNOS"` (no `/etc/os-release` on the native target).
  The uname-based probes (`kernel_name`/`kernel_version`/`cpu_arch`/`hostname`) were already agnos-portable via `agnosys_uname` (#34). `mem_free`/`cpu_model`/`gpu` degrade gracefully to unknown on agnos (no sysinfo equivalent).

### Verified

- **On real agnos (kernel 1.45.10) under QEMU** via iam: the card renders `Distro: AGNOS`, `Kernel: AGNOS`, `Uptime: <1m`, `Memory: 128 MiB` (the real PMM size, via sysinfo#35). Host tests **108/108** (Linux paths intact). Harness: `agnos/scripts/iam-agnos-verify.py`.

## [1.1.1] — 2026-06-18

Toolchain-pin / stdlib-reorg maintenance cut. No probe source changes;
probe API unchanged (still frozen since 1.0.0).

### Changed

- **`cyrius.cyml`** — `cyrius` pin bumped **6.0.56 → 6.2.22** (ecosystem
  stdlib-pin sweep onto the current toolchain). `cyrius lib sync`
  re-vendored the 6.2.22 stdlib snapshot into `lib/`.
- **`json` → `bayan` in the `[deps] stdlib` list.** In the 6.2.x stdlib
  reorg the standalone `json` module was carved out of the cyrius stdlib
  into the bundled **`bayan`** distribution (json / toml / cyml / csv /
  base64 / bigint / u128) and folded back byte-identical via the sandhi
  pattern. mihi calls no JSON directly — the `registry_to_json` symbols
  inside `dist/ai-hwaccel.cyr` now resolve through bayan's back-compat
  aliases. The orphaned `lib/json.cyr` (absent from the 6.2.22 snapshot)
  was pruned.
- **`VERSION`**: 1.1.0 → 1.1.1.
- **`dist/mihi.cyr`** — regenerated via `cyrius distlib` for the v1.1.1
  version stamp. Module content byte-identical to 1.1.0.

### Notes

- Verified green on 6.2.22: `cyrius deps` resolves cleanly (109 deps
  locked), `cyrius build programs/smoke.cyr` OK, smoke binary prints the
  full probe surface and exits 0, `cyrius test` 108/108.

## [1.1.0] — 2026-06-06 (cycle-open: AGNOS as a build target — PREP done, full build deferred to 1.43.x)

### Added (prep — full agnos build blocked, see below)

- **AGNOS platform prep** (VERSION → 1.1.0; cyrius pin 6.0.1 → 6.0.56, lib re-vendored). The kernel-interface dep is rewired from the toolchain-bundled `agnosys` stdlib entry to a proper **`[deps.agnosys]` git dep at 1.4.0** (`dist/agnosys-core.cyr`) — the agnos-aware build that resolves `uname`#34 / `sysinfo`#35 (no Linux `/proc`). That blocker is cleared.

### Deferred to 1.43.x (graphics arc)

- **mihi's full `--agnos` build is blocked by its GPU probe**, not by mihi's own probes. `src/gpu.cyr` pulls `ai-hwaccel` → `thread` → `atomic` → Linux `CLONE_VM`; cyrius `atomic`/`thread` are **stdlib (hands-off)** and can't target agnos until agnos *has* threads (the future multi-threading / SMP arc). GPU detection is itself a graphics concern, so it revisits **with 1.43.x graphics** — at which point the GPU probe is separated to a Linux-only profile (or built back in for agnos alongside the GPU surface), and the core probes (cpu/mem/kernel/uptime/hostname via `agnosys-core` + `sysinfo`#35) finish. The inline `#ifdef CYRIUS_TARGET_AGNOS` probe branches land then.

## [1.0.0] — 2026-05-20

**API freeze.** mihi's full probe surface — `types` / `cpu` / `mem` /
`kernel` / `host` / `gpu`, 15 probes — is now contract. Both planned
v1.0 consumers are integrated and green: **iam-0.9.0 RC** (pinned to
mihi 0.7.0, will repin to 1.0.0 in lockstep) and **chakshu-0.6.0**
(released 2026-05-20, pinned to mihi 0.8.0; closed mihi's M6 gate).
Every v1.0 criterion from the roadmap checks: full module set
shape-stable since 0.4.0, citations in declaring functions, complete
`docs/sources.md`, 108 test assertions across happy + error paths,
three-tier benchmark suite, security audit pass.

From here, any signature / return-shape / error-semantics change is
a real `Breaking` and requires a major-version bump.

### Breaking
- **API freeze** — no signatures, return shapes, or error semantics
  changed in this cut. The "breaking" is the contract change: the
  surface mihi-0.8.0 froze in shape, mihi-1.0.0 freezes in contract.
  Pre-v1.0 churn ended at 0.4.0; the four cuts since (0.5.0, 0.6.0,
  0.7.0, 0.8.0) added tests / docs / CI / consumer-acknowledgment
  with zero probe-API drift. Anything that would have been a
  pre-v1.0 `Breaking` becomes a major-version bump from here.

### Changed
- **`VERSION`**: 0.8.0 → 1.0.0.
- **`cyrius.cyml`** — `cyrius` pin bumped 6.0.0 → 6.0.1 to match the
  ecosystem (iam and chakshu both moved to 6.0.1 in their M5 / M2.5
  integration cuts; the local wrapper has been 6.0.1 for the last
  several mihi releases and `state.md` called the drift "cosmetic").
  No source / bundle effect — distlib output is identical apart from
  the version stamp.
- **`dist/mihi.cyr`** — regenerated via `cyrius distlib` for the
  v1.0.0 version stamp in the bundle header. Single-line diff;
  module content byte-identical to 0.8.0 (which was itself
  byte-identical to 0.7.0 — see chakshu-0.6.0 CHANGELOG for the
  symmetric callout on the consumer side).
- **`docs/development/roadmap.md`** — M6 ✅; every v1.0 criterion box
  ticked.
- **`docs/development/state.md`** — chakshu promoted to integrated
  consumer; toolchain pin row updated to 6.0.1; `## Next` shifts to
  post-v1.0 stewardship mode.

### Notes
- v1.0 is a *shape-and-contract* freeze, not a feature freeze. The
  "Out of scope (for v1.0)" list in `roadmap.md` (Windows / macOS
  probes, network info, monitoring concerns) remains the scope bar.
  Additions that fit "tell me about this box" for the AGNOS userland
  accrete here; anything outside the surface spins out into a
  sibling lib (e.g. `mihi-net`).
- iam will cut iam-1.0.0 in lockstep — see iam-0.9.0 CHANGELOG
  *"mihi 1.0 ship is the only external gate."*
- chakshu's per-frame delta loop remains chakshu-local; mihi owns
  identity probes only. The layered split established in
  chakshu-0.6.0 is the architectural contract going forward.

## [0.8.0] — 2026-05-19

**M5 acknowledgment cut.** `iam` integrated against mihi 0.7.0 and is
sitting as iam-0.9.0 RC pending mihi v1.0 — no transitive fixes
surfaced from the integration, so the v0.8.x slot the 0.7.0 cut
reserved for them closes empty. This release recognizes M5 as shipped
in the roadmap and refreshes `state.md` to reflect iam as mihi's first
consumer. v1.0 remains gated on M6 (chakshu, blocked on its own
Cyrius language update).

No source changes. `dist/mihi.cyr` regenerated for the v0.8.0
version stamp in its header comment (single-line diff: the bundle
header includes `# Version: <VERSION>`, so any VERSION bump
triggers the distlib drift check).

### Changed
- **`VERSION`**: 0.7.0 → 0.8.0.
- **`dist/mihi.cyr`**: regenerated via `cyrius distlib` for the
  header version stamp. One-line diff; no module content changed.
- **`docs/development/roadmap.md`** — M5 flipped ✅, sequenced at
  v0.8.0 (instead of the previously planned v0.9.0; iam integrated
  against the current `dist/mihi.cyr` bundle rather than waiting for
  a renamed cut). M4.6 noted as closed empty. M6 still v1.0.0,
  blocked on chakshu.
- **`docs/development/state.md`** — `## Consumers` updated: iam is
  the first consumer, pinned at `[deps.mihi] tag = "0.7.0"`,
  sitting as iam-0.9.0 RC per its CHANGELOG. `## Next` section
  refreshed (was two releases stale, still pointed at M4).

### Open (post-0.8.0)
- **v1.0.0 (M6)** — `chakshu` second consumer + API freeze. Blocked
  on chakshu's Cyrius language update; no internal ETA. iam-side
  has declared *"mihi 1.0 ship is the only external gate"* (iam
  0.9.0 CHANGELOG); the v1.0 cut becomes a lockstep release when
  chakshu unblocks.

## [0.7.0] — 2026-05-19

**Distlib determinism + CI gate hardening.** Closes M4.5 from the
reordered roadmap. The drift check has been in CI since v0.2.0;
this cut adds the determinism gate next to it so non-reproducible
bundle output fails the build, mirrors the ai-hwaccel / libro /
yukti convention, and expands the required-files list to enforce
every v1.0 hardening artifact landed in 0.5.0–0.6.0. No source
changes; CI-only.

Leaves the 0.8.x patch slots free for transitive fixes that surface
when `iam` (M5) or `chakshu` (M6) start consuming mihi.

### Added (CI)
- **distlib determinism gate** in `.github/workflows/ci.yml` — runs
  `cyrius distlib` twice and SHA-256-compares the two outputs. Any
  byte drift (timestamps, ordering, formatting noise) fails the build.
  Sits next to the existing drift check; drift = stale, determinism
  = non-reproducible.
- **Bench files build gate** — every `benches/*.bcyr` is compiled in
  CI to catch contributors removing a helper that a bench file
  references. Doesn't run the benches (hot-path numbers come from
  local `scripts/bench-history.sh` runs that write to
  `docs/benchmarks/history.csv`).
- **Required-files list expanded** in the docs job:
  - `docs/adr/0002-gpu-singleton-cache.md`
  - `docs/benchmarks.md`
  - `benches/{probe_paths,parsers,gpu_paths}.bcyr`
  - `scripts/bench-history.sh`
  - `docs/audit/*-audit.md` (glob — at least one audit doc must
    exist; date rotates per cut)

### Changed
- **`VERSION`**: 0.6.0 → 0.7.0.
- **`docs/development/roadmap.md`** — M4.5 checkbox flipped ✅;
  intermediate-version notes updated (0.8.x reserved for
  transitive consumer-side patches).
- **`docs/development/state.md`** — refreshed for 0.7.0; CI gate
  status documented.

### Open (post-0.7.0)
- **0.8.x** (reserved) — transitive fixes that surface when `iam` /
  `chakshu` begin consuming mihi. No planned content; placeholder
  for the consumer-integration discovery cycle.
- **v0.9.0** (M5) — `iam` first consumer integration.
- **v1.0.0** (M6) — `chakshu` second consumer + API freeze.

## [0.6.0] — 2026-05-19

**Security audit + defensive parser fixes.** Per-CLAUDE.md P(-1)
checklist item, with the
[`feedback-security-audit-web-research`](memory)-memory guidance
applied: every audit pass must combine internal review with external
CVE/0day research, never just one. Full findings in
[`docs/audit/2026-05-19-audit.md`](docs/audit/2026-05-19-audit.md).

No critical findings — three defensive parser hardenings landed
(C-1, M-1, C-2) and two transitive AMD GPU CVEs are documented for
consumer awareness. The probe API is unchanged.

### Fixed (audit findings)
- **C-1** — `mihi_parse_cpu_range` (`src/cpu.cyr`) now coerces
  descending ranges (`"10-5"`) to single-CPU ranges instead of
  producing a negative addend. Real kernel output never emits
  descending ranges; this defends against corrupted `/sys` content.
- **M-1** — `mihi_parse_meminfo_kb` (`src/mem.cyr`) caps digit
  accumulation at 18 to prevent i64 overflow on adversarial input.
  Real `/proc/meminfo` values are bounded by physical RAM (~10
  digits in kB); 18 leaves headroom.
- **C-2** — Same overflow defense applied to the lo/hi
  accumulators in `mihi_parse_cpu_range` and to
  `mihi_parse_uptime_secs` (`src/host.cyr`). All three digit-parsing
  parsers now share the same cap.
- Regression tests added: `audit C-1 — cpu_range coerces
  descending`, `audit M-1 — meminfo_kb caps digits`, `audit C-2 —
  uptime_secs caps digits`. Suite grows 104 → 108 assertions.

### Known Environmental Issues (kernel CVEs, no mihi-side fix)

These are upstream Linux kernel bugs that mihi cannot avoid; the
audit documents them so consumers running on affected kernels know
to upgrade. Both are AMD-GPU-specific and reach mihi only via the
`mihi_gpu_*` family (ai-hwaccel's `detect_rocm` sysfs path).

- **[CVE-2025-40289](https://nvd.nist.gov/vuln/detail/CVE-2025-40289)** —
  Reading `/sys/class/drm/cardN/device/mem_info_vram_total` (or
  `_used`) crashes the kernel on some AMD GPUs without dedicated
  VRAM. The fix hides the sysfs attribute on those GPUs.
  Recommend mainline Linux 6.15+ or a distro kernel with the
  backport. archaemenid's `7.0.5-arch1-1` is not affected.
- **[CVE-2025-40288](https://nvd.nist.gov/vuln/detail/CVE-2025-40288)** —
  NULL pointer deref in `ttm_resource_manager_usage()` on APU
  platforms where the VRAM manager isn't initialized. Same
  hardware exposure class as 40289. Same recommendation.

### Changed
- **`VERSION`**: 0.5.0 → 0.6.0.
- **`docs/development/roadmap.md`** — M4 audit checkbox flipped ✅;
  added M4.5 entry for the v0.7.0 distlib hardening (per the user's
  sequencing); M5 (iam consumer) still v0.9.0.
- **`docs/development/state.md`** — refreshed for 0.6.0; test count
  104 → 108; audit doc referenced.

### Open (post-0.6.0)
- v0.7.0 — distlib determinism CI gate (per ai-hwaccel's pattern).
- v0.9.0 (M5) — `iam` consumer integration, blocked on iam
  itself catching up.
- v1.0.0 (M6) — `chakshu` second consumer, blocked on chakshu's
  language update.

## [0.5.0] — 2026-05-19

**Pre-consumer hardening — mihi's v1.0 shape, validated.** Roadmap
M4↔M5 reordered: this milestone is now the hardening pass (test
coverage, doc alignment, benchmarks) and the iam consumer integration
moves to v0.9.0. The flip avoids consumer-side rework — `iam` is still
scaffold-only, and pinning it against a mihi that's still settling
would force a second pass later. Better to land iam against a
benchmarked, audited, shape-stable mihi.

No probe-surface changes; all 15 public probes (5 gpu probes added
in 0.4.0) retain their 0.4.x signatures. This is the
"library ready for consumers" cut.

### Added
- **Doc-alignment batch** — [`docs/sources.md`](docs/sources.md)
  Slice E with one citation row per `mihi_gpu_*` probe;
  [ADR 0002](docs/adr/0002-gpu-singleton-cache.md) justifying the
  module-level singleton cache in `src/gpu.cyr` against ADR 0001's
  caller-buffer rule; roadmap M3 follow-ups flipped to ✅; new
  M3.1 entry for the 0.4.1 dep refresh.
- **Test coverage push 75 → 104 assertions** across 10 new test
  groups — closes the v1.0 "100+ assertions" criterion. Targets the
  error paths the happy-path suite didn't reach: `mihi_parse_cpu_range`
  (multi-digit / alphabetic / whitespace-only),
  `mihi_parse_cpu_model` (empty buffer / EOF-no-newline),
  `mihi_find_meminfo_field` (empty / key-longer-than-buffer),
  `mihi_parse_meminfo_kb` (start-past-end / ws-only / 64-GiB-no-overflow),
  `mihi_parse_uptime_secs` (year-long / ws-only / bare-no-separator),
  `mihi_find_osrelease_key` (empty / key-longer),
  `mihi_parse_osrelease_value` (unterminated quote / bare-no-newline),
  `gpu.cyr` (multi-accelerator registry / mixed family types /
  singleton cache stability).
- **Benchmark suite** — three-tier convention matching yukti / ai-hwaccel:
  - [`benches/probe_paths.bcyr`](benches/probe_paths.bcyr) — public
    API with real I/O. archaemenid baseline: `probe/mihi_uname` 2 µs,
    `probe/mihi_cpu_count` 8 µs, `probe/mihi_mem_total` 13 µs,
    `probe/mihi_cpu_model` 52 µs (the heaviest probe),
    `accessor/mihi_*` 4-5 ns (pure pointer arithmetic).
  - [`benches/parsers.bcyr`](benches/parsers.bcyr) — pure parsers,
    synthetic buffers. archaemenid baseline: `parser/cpu_range_simple`
    48 ns, `parser/cpu_model` 311 ns, `parser/meminfo_MemAvailable`
    691 ns (4× MemTotal because the field anchor walks past
    MemTotal+MemFree).
  - [`benches/gpu_paths.bcyr`](benches/gpu_paths.bcyr) — proves
    [ADR 0002](docs/adr/0002-gpu-singleton-cache.md) empirically.
    archaemenid: `gpu/count_cold` 1.2 ms, `gpu/count_warm` 56 ns —
    **~22,000× ratio**, the load-bearing claim of ADR 0002.
  - [`scripts/bench-history.sh`](scripts/bench-history.sh) — builds
    every bench, parses `bench_report` output, appends to
    [`docs/benchmarks/history.csv`](docs/benchmarks/history.csv),
    auto-regenerates [`docs/benchmarks/results.md`](docs/benchmarks/results.md)
    with the 3 most recent runs side-by-side and Δ first→last per
    benchmark. Narrative companion at
    [`docs/benchmarks.md`](docs/benchmarks.md).
- **Roadmap reorder** — M4 is now "pre-consumer hardening" (v0.5.0,
  this release); M5 is "first consumer integration (iam)" (v0.9.0).
  See [`docs/development/roadmap.md`](docs/development/roadmap.md).

### Changed
- **`VERSION`**: 0.4.1 → 0.5.0.
- **`cyrius.cyml`**: stdlib gains `bench` (required by `benches/*.bcyr`
  builds; DCE removes it from `programs/smoke.cyr`).
- **`docs/adr/README.md`** indexes both ADRs.
- **`src/gpu.cyr`** header references ADR 0002 instead of inlining
  the full cache-shape rationale.
- **`docs/development/state.md`** — refreshed test count (104) and
  bench reference.

### Removed
- **`tests/mihi.bcyr`** — obsolete stub. The `cyrius bench` runner
  looks in `benches/` (per the sibling convention) so the old stub
  was never discoverable anyway. `benches/probe_paths.bcyr` +
  `benches/parsers.bcyr` + `benches/gpu_paths.bcyr` supersede it.

### Open (v1.0 checklist remaining)
- ☐ Security audit — `docs/audit/2026-05-19-audit.md`. Per the
  `feedback-security-audit-web-research` memory note: must include
  external CVE/0day research for every `/proc`, `/sys`, and syscall
  surface mihi (or its ai-hwaccel transitive deps) touches. Targeted
  for the next patch (0.5.1).
- ☐ `dist/mihi.cyr` distlib determinism CI gate — mirror the
  ai-hwaccel pattern (build, sha256, rebuild, compare). The bundle
  is already deterministic; the gate just enforces it.
- ☐ M5 / v0.9.0 — `iam` consumer integration, once iam itself
  catches up.

## [0.4.1] — 2026-05-19

**ai-hwaccel pin bump: 2.2.5 → 2.2.6 — closes both Known Issues from
0.4.0.** No mihi-side code changed; this is purely a dependency
refresh that picks up upstream fixes for the two gaps mihi 0.4.0
flagged in its CHANGELOG. After bumping, `mihi_gpu_name` returns a
populated string on ROCm devices instead of null, and the persistent
linker warning is gone.

### Changed
- **`cyrius.cyml`**: `[deps.ai-hwaccel] tag = "2.2.5"` → `"2.2.6"`.
- **`dist/mihi.cyr`**: regenerated. No mihi source changes — only the
  pinned dep version moves.

### Fixed (via ai-hwaccel 2.2.6)
- `mihi_gpu_name(idx)` now returns the device name for ROCm GPUs
  (ai-hwaccel's `detect_rocm` populates `profile_device_name` from
  `/sys/class/drm/cardN/device/product_name`, falling back to a
  synthesized `AMD Radeon (PCI vendor:device)` string). On
  archaemenid the smoke binary now prints
  `gpu: AMD Radeon (PCI 0x1002:0x1638)` instead of `gpu: (unnamed)`.
- The `undefined function 'registry_to_json'` linker warning is gone —
  ai-hwaccel 2.2.6 includes `src/json_out.cyr` in its bundle so the
  symbol resolves. DCE still elides the call (mihi doesn't use the
  serializer); binary output is unchanged.
- Same upstream fix populates `device_name` for three other
  detectors (TPU, Gaudi, Neuron) — mihi doesn't reach these on
  archaemenid but the gap is closed for any consumer running on
  cloud accelerators.

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

### Known Issues (resolved in 0.4.1 via ai-hwaccel 2.2.6)
- ~~**One linker warning** — `undefined function 'registry_to_json'`
  is referenced from `cache.cyr`'s disk-write path in the ai-hwaccel
  2.2.5 bundle. The defining module (`src/json_out.cyr`) is excluded
  from `cyrius distlib` per ai-hwaccel's CLI/lib partition, leaving
  a dangling reference. DCE elides the call (mihi never reaches it),
  so the binary is correct, but the warning is noise.~~ → Fixed
  upstream in 2.2.6 by including `json_out.cyr` in the bundle.
- ~~**ROCm device names empty** — `detect_rocm` in ai-hwaccel 2.2.5
  never calls `profile_set_device_name`, so `mihi_gpu_name(idx)`
  returns null for ROCm GPUs. mihi correctly reports null rather
  than fabricating a name; smoke output shows "(unnamed)".~~ → Fixed
  upstream in 2.2.6: prefers `product_name` sysfs file, falls back
  to a synthesized `AMD Radeon (PCI vendor:device)` string.

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
