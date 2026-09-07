# mihi — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

**1.2.6** — released 2026-09-07. **Toolchain cut that carries a real
API break.** Cyrius pin **6.5.35 → 6.6.0** (39 releases); ai-hwaccel
**2.3.19 → 2.3.22**. 6.6.0 makes `Result` / `Option` / `Either` the
**value form** — `enum Result<T, E>: stack` returns `(tag, payload)` in
a register pair instead of a 16-byte box from the global bump
allocator, whose only reclaim invalidates every pointer it ever handed
out. That changes the **arity** of every Result in the ecosystem.

mihi has exactly one Result-returning probe, `mihi_uname`, so the break
is narrow but real: consumers must write `var t, v = mihi_uname(&uts);`
and check `is_err_result(t)`. The old single-variable bind is a **hard
compile error naming the fix**, not a silent miscompile — cyrius
refuses it rather than dropping the payload — so every stale consumer
site fails at its own line. `is_ok` / `is_err_result` themselves are
unchanged. The other twelve probes return plain `i64` / `cstring` and
are untouched. Migrated at five in-tree sites; contract documented on
`mihi_uname` itself.

`lib/` re-vendored from the 6.6.0 snapshot (**40 modules changed**,
including the `lib/result.cyr` that decides the arity), plus the
transitive **`lib/hashseed.cyr`** — new at 6.5.39, required by the
declared `hashmap` leaf. `lib sync --full` alone no longer yields a
complete tree; `cyrius deps` finishes it.

ai-hwaccel 2.3.20 made `[deps.bayan]` optional and feature-gated, which
**removed a commit pin from mihi's lock** (2 → 1) and orphaned
`lib/bayan-json.cyr` — 100 KB of 1.5.2-era third-party source, not in
the 6.6.0 snapshot, pinned by nothing, referenced by nothing. Pruned;
`build/mihi-smoke` stayed **byte-identical at 379,872 B**, proving it
was never linked. Its visible residue is seven new `undefined function
'bayan_json_v_*'` warnings — verified unreachable (all five enclosing
functions have zero callers inside ai-hwaccel; the disk cache's read
path is still a `TODO`), eliminated by `CYRIUS_DCE=1`, and named by
ai-hwaccel 2.3.20 as the expected state for mihi. Probe facts, parsers
and values unchanged: **143/143**.

**1.2.5** — released 2026-08-24. Dropped `bayan` from `[deps].stdlib`
(21 → 20 modules) — it was cover for a dependency's dependency, and
mihi's own source references zero json/bayan symbols. Because those
back-compat aliases ship only in the monolithic `dist/bayan.cyr`, the
entry forced every consumer to link all 641 KB of it; measured in
chakshu, **861,536 → 571,496 B (−33.7%)**. ai-hwaccel pinned
`2.3.18 → 2.3.19` as a hard requirement, not a refresh: 2.3.19 is what
moves those call sites onto the canonical `bayan_json_v_*` names. API
unchanged.

**1.2.4** — released 2026-08-23. **The two things 1.2.3 left open,
closed on real hardware.** D-1 (`mihi_cpu_model` returns null on every
aarch64 Linux box) was filed as needing arm64 hardware; A-5's AGNOS
`mem_free` arm shipped compile-verified only. Both now verified by
running.

`mihi_cpu_model` gains a third arm: aarch64 Linux reads
`/sys/firmware/devicetree/base/cpus/cpu@0/compatible` — the device
tree's own statement of CPU 0's model, a separate arch-native source
rather than a fallback. Verified on **agnosarm** (Raspberry Pi 4 Model
B, Ubuntu 24.04.4, kernel 6.8.0-1053-raspi): `model: arm,cortex-a72`,
suite **144 passed / 0 failed on the hardware**. Residual: ACPI-booted
arm64 has no device tree, so the probe still returns null there —
narrowed, not eliminated.

A-5 verified on the sovereign kernel via the new
`scripts/mihi-agnos-verify.py`, which boots agnos in QEMU and runs
`programs/agnos_probe.cyr` twice in one boot: the pre-A-5 control
(`188a7d3`) prints `free B: -1`, this tree prints `free B: 489295872`
against `total B: 535580672`. A control that fails is what makes it a
measurement — and it earned its keep immediately, refusing to call the
first run a pass when the "control" turned out to have been built from
a HEAD that already carried the fix.

Also learned: **`programs/smoke.cyr` has never run on AGNOS.** Built
`--agnos` it faults before its first println (`run: exit 142`) because
it links `src/gpu.cyr` and hence the ai-hwaccel bundle — the standing
agnos blocker. Every prior agnos claim went through `iam`.
`programs/agnos_probe.cyr` (five modules, no gpu) exists so mihi can
answer for itself. CI gained a cross-target build gate: `--agnos` and
`--aarch64` compile on every run, because the arch arms are the part of
mihi that rots silently — D-1 sat undetected since 0.2.0 for exactly
that reason.

**1.2.3** — released 2026-08-23. **P(-1) audit / hardening sweep** —
the second full audit of the probe surface (first was 2026-05-19,
pre-0.6.0). Six code fixes, four documentation corrections, one new
`[lib]` module, 116 → 137 assertions. Probe API unchanged.

The headline finding is **A-1**: every file-reading probe carried its
own `open / one read / close`, six copies, and a read that filled the
buffer was indistinguishable from EOF — so an undersized buffer
returned a *plausible wrong value rather than an error*. The
short-read half was not theoretical: a single `read(fd, buf, 8192)` on
`/proc/cpuinfo` returns 3288 bytes on this host, so `mihi_cpu_model`
had been parsing 3288 of its caller's 8192 since 0.2.0. Fixed once, in
a new `src/io.cyr` ([ADR 0003](../adr/0003-shared-probe-read.md)),
which also brought `O_NONBLOCK` (a repointed `/etc/os-release` symlink
landing on a FIFO must not hang a login) and `O_CLOEXEC`.

**A-4** is the one to read twice — the only finding across both audits
whose failure mode was a memory-safety event rather than a wrong
number: `mihi_uname` left the caller's buffer uninitialised on failure,
and the field accessors do not check the `Result` by contract, so a
caller who ignored it got an unterminated cstring into stack garbage.
**A-2** and **A-3** are both descendants of the 0.6.0 audit — places
where that sweep bounded one step of an arithmetic chain and left the
next unbounded; A-3 could return a *negative* byte count
(-9017668127734891520, measured). **A-5** gave `mihi_mem_free` the AGNOS
arm it never had. **D-1 … D-4** corrected citations that asserted false
things about the arm64 kernel and the os-release spec.

Cost, measured against the 1.2.2 source on the same host: `mihi_uname`
+533 ns (the zeroing), `mihi_cpu_model` **+126%** (it now reads all
8192 bytes it asks for), everything else +3–16%. Full write-up:
[`docs/audit/2026-08-23-audit.md`](../audit/2026-08-23-audit.md).

**1.2.2** — released 2026-08-23. Toolchain / dependency maintenance
cut. Cyrius pin **6.2.37 → 6.5.35** (closes the wrapper/manifest
drift; `cyrius lib sync --full` re-vendored the version-matched
108-module snapshot, including the new `lib/unicode/` sub-package and
`yantra`). ai-hwaccel **2.2.6 → 2.3.18** — twelve upstream releases,
of which only 2.3.14's `registry_new` → `hw_registry_new` rename
reaches mihi, and only in the test suite. Two consequences that are
not mechanical: `sakshi` joins `[deps] stdlib` (ai-hwaccel 2.3.x logs
through it), and `_mihi_gpu_ensure()` now clamps the log level to
`SK_WARN` across the one `registry_detect_no_exec()` call and restores
it, so mihi stops writing `detect: profiles=N` to a consumer's stderr.
Ten stale vendored modules pruned from `lib/` (`agnosys` ×2, the six
bayan-absorbed data-format modules, `linalg` / `matrix`). New
`dist/mihi.deps` sidecar checked in and CI-gated. Probe API unchanged.
CI reworked in the same cut: the toolchain now comes from the upstream
installer (the hand-rolled tarball copy could fail silently and skipped
signature verification), plus two new gates — `cyrius deps --verify`
against the 109-entry lock, and a `cyrius fmt --check` sweep over every
hand-written source, with `tests/mihi.tcyr` reformatted to match.
Verified green: 116/116 tests, clean smoke with empty stderr, `--agnos`
cross-build compiles with the CPUID path intact, whole workflow replayed
locally step-by-step.

**1.2.1** — released 2026-07-02. Fix cut: the CPUID CPU-model path was
compiled **out** on agnos in 1.2.0, because `cyrius build --agnos` does
not predefine `CYRIUS_ARCH_X86` — so `iam` still rendered
`CPU: (unknown)` on the sovereign kernel. `src/cpu.cyr` now `#define`s
`CYRIUS_ARCH_X86` when `CYRIUS_TARGET_AGNOS` is set (agnos *is* x86),
and `mihi_cpu_brand_fill` loads its buffer param via `param_load(rdi, 0)`
rather than assuming prologue register placement. Verified on iron in
QEMU/KVM: iam prints the real brand.

**1.2.0** — released 2026-07-02. **CPU probe made sovereign on AGNOS.**
`mihi_cpu_model` read `/proc/cpuinfo`, which agnos has no procfs for;
the brand is the same datum procfs prints from (CPUID leaves
0x80000002/3/4), so mihi reads it straight from the instruction. Adds
`mihi_cpu_model_cpuid` + `mihi_cpu_brand_fill`; `mihi_cpu_model`
dispatches AGNOS → CPUID, Linux → `/proc/cpuinfo`. `mihi_cpu_count` on
AGNOS stops returning a hardcoded `1` and reads the kernel's enumerated
count from `sysinfo`#35. Same `(buf, cap) → cstring` API — consumers
unaffected.

**1.1.3** — released 2026-06-22. **Rewired off `agnosys` onto the
native `sys` stdlib module.** cyrius retired the stale stdlib `agnosys`
snapshot at 6.2.37, so mihi dropped the `[deps.agnosys]` git dep
entirely and rewired the single `uname`#34 + `sysinfo`#35 path to
`lib/sys.cyr`'s `sys_uname` / `sys_sysinfo` (same plumbing, carved off
agnosys at cyrius 6.1.28, with per-target `UTS_*` / `SI_*` offsets for
Linux **and** AGNOS). `mihi_uname` wraps the raw `0/-errno` return as a
`Result` so consumers checking `is_err_result` are unaffected. Cyrius
pin `6.2.22` → `6.2.37`.

**1.1.2** — released 2026-06-19. AGNOS build-target support for the
probes, via `#ifdef CYRIUS_TARGET_AGNOS` branches on the four that read
Linux `/proc` + `/sys`: `mihi_mem_total` and `mihi_uptime_secs` → the
`sysinfo`#35 struct, `mihi_cpu_count` → `1` (the then-committed
single-core gate, since superseded at 1.2.0), `mihi_distro` → `"AGNOS"`.
Verified on real agnos (kernel 1.45.10) under QEMU via iam. Probe API
unchanged.

**1.1.1** — released 2026-06-18. Toolchain-pin / stdlib-reorg
maintenance cut. Cyrius pin **6.0.56 → 6.2.22** (ecosystem stdlib-pin
sweep); `cyrius lib sync` re-vendored the 6.2.22 snapshot. The 6.2.x
stdlib reorg carved the standalone `json` module out of the cyrius
stdlib into the bundled **`bayan`** distribution (json / toml / cyml /
csv / base64 / bigint / u128, folded back byte-identical via the
sandhi pattern), so `json` → `bayan` in `[deps] stdlib`; mihi's only
JSON use is the `registry_to_json` symbols inside `dist/ai-hwaccel.cyr`,
which resolve through bayan's back-compat aliases. Orphaned
`lib/json.cyr` pruned. No probe source changes; API still frozen.
`dist/mihi.cyr` regenerated for the version stamp (module content
byte-identical to 1.1.0). Verified green: deps resolve (109 locked),
build OK, smoke exits 0, `cyrius test` 108/108.

**1.1.0** — released 2026-06-06. Cycle-open: AGNOS as a build target
(PREP done, full build deferred to 1.43.x graphics arc). Cyrius pin
6.0.1 → 6.0.56, lib re-vendored. The kernel-interface dep rewired from
the toolchain-bundled `agnosys` stdlib entry to a proper
`[deps.agnosys]` git dep at 1.4.0 (`dist/agnosys-core.cyr`) — the
agnos-aware build resolving `uname`#34 / `sysinfo`#35. mihi's full
`--agnos` build remains blocked by its GPU probe (ai-hwaccel → thread →
atomic → Linux `CLONE_VM`), revisited with 1.43.x graphics.

**1.0.0** — released 2026-05-20. **API freeze.** Both M5 (iam) and
M6 (chakshu) consumer gates closed; all seven v1.0 criteria from
`roadmap.md` met. From here, signature / return-shape / error-
semantics changes are real `Breaking` and require a major-version
bump. v1.0 is shape-and-contract freeze, not feature freeze: the
"Out of scope (for v1.0)" list in `roadmap.md` still bounds what
mihi takes on. Cyrius toolchain pin bumped 6.0.0 → 6.0.1 (matches
iam + chakshu; closes the cosmetic drift). `dist/mihi.cyr`
regenerated for the version stamp; module content byte-identical
to 0.8.0 / 0.7.0.

**0.8.0** — released 2026-05-19. M5 acknowledgment cut. `iam`
integrated against mihi 0.7.0 (sitting as iam-0.9.0 RC), no
transitive fixes surfaced — the v0.8.x slot the 0.7.0 cut reserved
for them closes empty. No source changes; `dist/mihi.cyr` unchanged.
Roadmap M5 flipped ✅ at v0.8.0 (instead of the planned v0.9.0 —
iam pinned the current bundle rather than waiting for a renamed
cut). v1.0 remains gated on M6 (chakshu).

**0.7.0** — released 2026-05-19. Distlib hardening / CI gate cut.
Adds the determinism gate next to the existing drift check (SHA-256
compare across two `cyrius distlib` invocations), bench-files-build
gate, expanded required-files list (ADR 0002, audit doc, bench
infrastructure all CI-enforced). No source changes. Leaves 0.8.x
patch slots reserved for transitive fixes from `iam` / `chakshu`
consumer integration.

**0.6.0** — released 2026-05-19. Security audit cut. Three defensive
parser fixes (C-1 cpu_range descending, M-1 meminfo_kb overflow cap,
C-2 same for cpu_range + uptime), four new regression tests, two
transitive AMD GPU CVEs documented (CVE-2025-40288, CVE-2025-40289).
Full audit in `docs/audit/2026-05-19-audit.md`. Probe API unchanged.

**0.5.0** — released 2026-05-19. Pre-consumer hardening: 100+ test
assertions (104/104 across 38 groups), three-tier benchmark suite
under `benches/` + `docs/benchmarks/` (archaemenid baseline captured),
ADR 0002 for the gpu singleton cache, `docs/sources.md` Slice E.
Roadmap M4↔M5 reordered: this cut is the "library ready for
consumers" milestone; iam consumer integration shifts to v0.9.0.

**0.4.1** — released 2026-05-19. Dep-pin refresh: ai-hwaccel 2.2.5 →
2.2.6. Closes both Known Issues from 0.4.0 — ROCm device name now
populates (`AMD Radeon (PCI 0x1002:0x1638)` on archaemenid) and the
`registry_to_json` linker warning is gone. No mihi source changes.

**0.4.0** — released 2026-05-19. M3 complete: accelerator-identity
probes via ai-hwaccel 2.2.5's no-exec API. mihi now covers kernel /
CPU / memory / host-identity / accelerators — the full v1.0 probe
surface except `iam`'s consumer integration (M4). M2 shipped earlier
the same day (host identity); M1 covered kernel + CPU + memory.

## Toolchain

- **Cyrius pin**: `6.6.0` (in `cyrius.cyml [package].cyrius`). Bumped
  6.5.35 → 6.6.0 at the 1.2.6 cut (39 releases), which also clears the
  wrapper's standing `6.5.36 enum Critical` warning (enum constants
  ≥ 2^62 read back as `-1`) that the 6.5.35 pin had carried since 1.2.2.
  `cyrius lib sync --full` re-vendors the version-matched snapshot:
  **109 stdlib modules** (40 changed at this cut), and `cyrius deps`
  then adds the transitive `lib/hashseed.cyr` — new at 6.5.39, pulled
  by the declared `hashmap` leaf. **`lib sync` alone no longer yields a
  complete `lib/`**; the deps pass finishes it. Plus
  `lib/ai-hwaccel.cyr`, the one git dep — 110 hashed lock entries and
  **one** commit pin.
- **`[deps] stdlib`** (20 modules): `string`, `fmt`, `alloc`, `io`,
  `vec`, `str`, `slice`, `syscalls`, `sys`, `assert`, `fs`, `tagged`,
  `process`, `fnptr`, `thread`, `freelist`, `hashmap`, `sakshi`, `ct`,
  `bench`. Most are there for the ai-hwaccel bundle, not for
  mihi's own probes — the bundle is one concatenation, so the parser
  needs the full set in scope and DCE drops what the binary doesn't
  reach. `sakshi` joined at 1.2.2 (ai-hwaccel 2.3.x logging); `bayan`
  was **removed at 1.2.5** — it was cover for a dependency's dependency
  and cost every consumer a 641 KB link. Do not re-add it; if mihi ever
  genuinely needs JSON, take `dist/bayan-json.cyr` as a git dep.
- **Pruned orphans**: `lib/` carried ten modules the 6.5.35 snapshot no
  longer ships — `agnosys` + `agnosys-core` (retired at cyrius 6.2.37;
  mihi rewired off the dep at 1.1.3), `base64` / `bigint` / `csv` /
  `cyml` / `toml` / `u128` (absorbed into `bayan`), `linalg` / `matrix`
  (absorbed into `ganita`). Removed at 1.2.2, finishing the prune 1.1.1
  started with `json`. **`bayan-json` joined them at 1.2.6**: it had
  arrived through ai-hwaccel 2.3.19's transitive `[deps.bayan]`, and
  when 2.3.20 made that dep optional and feature-gated it was left
  pinned by no commit line, absent from the 6.6.0 snapshot, and
  referenced by nothing — while `cyrius deps` kept hashing it into the
  lock. The recurring shape here is a vendored file whose owner has
  gone away; the lock is what surfaces it.

## Shape

Library, not a binary. `[lib].modules` in `cyrius.cyml` declares the
bundle order; `cyrius distlib` concatenates them into
`dist/mihi.cyr` for consumer `include "lib/mihi.cyr"` after
`cyrius deps`.

## Source

**v1.0 — API frozen.** 15 probes across kernel / cpu / mem / host /
gpu. All milestones shipped: M1 (kernel/cpu/mem), M2 (host identity),
M3 (gpu via ai-hwaccel no-exec), M4 (hardening), M4.5 (distlib CI
gate), M5 (iam consumer), M6 (chakshu consumer). Signatures, return
shapes, and error semantics are now contract. Post-freeze work has all
been additive or internal: AGNOS build-target branches (1.1.2), the
`sys.cyr` rewire (1.1.3), the CPUID CPU-model path (1.2.0 / 1.2.1), and
the log-level clamp (1.2.2).

- `src/types.cyr` (4 lines) — shared types (empty; `MihiInfo` deferred per ADR 0001)
- `src/io.cyr` (149) — `_mihi_read_probe_file`, the one `/proc` + `/sys` read path: looped reads, bounded `-EINTR` retry, truncation detection (`MIHI_IO_WHOLE` vs `MIHI_IO_PREFIX`), `O_NONBLOCK` + `O_CLOEXEC`. Added at 1.2.3 per [ADR 0003](../adr/0003-shared-probe-read.md); inert on AGNOS
- `src/cpu.cyr` (388) — `mihi_cpu_arch` ✅ + `mihi_cpu_count` ✅ + `mihi_cpu_model` ✅ (+ `mihi_parse_cpu_range` / `mihi_parse_cpu_model` pure-function helpers, and `mihi_cpu_model_cpuid` / `mihi_cpu_brand_fill` — the x86 CPUID brand-string path the AGNOS build dispatches to)
- `src/mem.cyr` (152) — `mihi_mem_total` ✅ + `mihi_mem_free` ✅ (+ `mihi_find_meminfo_field` / `mihi_parse_meminfo_kb` / `mihi_extract_meminfo_bytes` helpers)
- `src/kernel.cyr` (82) — `mihi_uname` wrapper over `sys_uname` (`Result`-wrapped since 1.1.3; **value-form pair since 1.2.6** — callers bind `var t, v =`, see the contract block on the function) + `mihi_kernel_name` ✅ + `mihi_kernel_version` ✅
- `src/host.cyr` (196) — `mihi_hostname` ✅ + `mihi_uptime_secs` ✅ + `mihi_distro` ✅ (+ `mihi_parse_uptime_secs` / `mihi_find_osrelease_key` / `mihi_parse_osrelease_value` helpers)
- `src/gpu.cyr` (168) — `mihi_gpu_count` ✅ + `mihi_gpu_name` ✅ + `mihi_gpu_memory_bytes` ✅ + `mihi_gpu_family` ✅ + `mihi_gpu_type` ✅ (module-level singleton cache via `_mihi_gpu_ensure`; first call runs `registry_detect_no_exec()` under a save/clamp/restore of the caller's `sakshi` log level)
- `src/main.cyr` (24) — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/agnos_probe.cyr` (65) — the AGNOS-clean probe subset (no `gpu.cyr`, so no ai-hwaccel); prints raw values with no early return so one QEMU boot shows the whole surface. Driven by `scripts/mihi-agnos-verify.py`
- `programs/smoke.cyr` (120) — smoke binary (Linux + aarch64 only — see the 1.2.4 note); prints `kernel / release / arch / host / model / cpus / mem MiB / free MiB / uptime / distro / gpu cnt / gpu / gpu MiB`
- `dist/mihi.cyr` (1164 lines; 1139 by `cyrius distlib`'s own count) — the consumable bundle; `dist/mihi.deps` is the stdlib-leaf sidecar beside it (cyrius 6.5.x), both CI-gated against drift

## Tests

- `tests/mihi.tcyr` — primary suite: **143 assertions on x86 / 144 on
  aarch64, across 56 test groups** (the arm64 build drops the 5
  CPUID-vs-`/proc` assertions and adds 6 device-tree ones) (104 from the 0.5.0 hardening push, 4 from the 0.6.0 audit
  regressions, 5 from the 1.2.0 CPUID work, 3 from the 1.2.2 log-level
  clamp, 21 from the 1.2.3 audit — Slice F, 6+ from the 1.2.4 arm64
  work). Slice A: real-uname happy path + zero-init buffer +
  synthetic-uts offset round-trip. Slice B: range-parser unit tests,
  cpuinfo-parser synthetic tests (happy + missing-field + line-anchor
  rejection), real `/proc/cpuinfo` + `/sys` reads. Slice C: meminfo
  field-anchor unit tests (file-start + mid-buffer + mid-line
  rejection), digit parser, kB→bytes extractor, real `/proc/meminfo`
  reads with sanity floors. Slice D: nodename offset round-trip,
  uptime parser (happy / freshly-booted / empty / non-digit),
  os-release key anchors (file-start + mid-buffer + mid-line + missing),
  value parser (quoted + bare + empty), ID-fallback composition, real
  `/proc/uptime` + `/etc/os-release` reads. Slice E (M3): synthetic
  registry CPU-only count + accessors, synthetic CPU+ROCm registry
  with name/memory/family/type assertions, out-of-range idx sentinel
  returns, live `registry_detect_no_exec()` smoke, and (1.2.2) the
  assertion that a live detect leaves the caller's `sakshi` level
  exactly as it found it — a verbose caller restored, a quiet caller
  never raised.
- **Slice F (1.2.3 audit regressions)**: `_mihi_read_probe_file`'s
  truncation split (WHOLE errors, PREFIX accepts a filled buffer),
  missing-path and zero-`cap` sentinels, probes returning an error
  rather than a truncated number on an undersized `cap`, the
  `mihi_parse_cpu_range` total cap at its boundary and past it, the
  `kB → bytes` scale rejection plus the largest value that still
  scales, `mihi_uname` leaving no poison byte behind, single-quoted
  os-release values (and an apostrophe inside a double-quoted one), and
  the previously untested `VERSION_ID=` / `ID=` prefix-shadowing case.
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke            # 11+ lines incl. gpu cnt / gpu / gpu MiB + "mihi smoke ok", exit 0, empty stderr
cyrius test tests/mihi.tcyr   # 143/143 pass (144/144 on aarch64)
cyrius build --agnos programs/smoke.cyr build/mihi-smoke-agnos   # sovereign-target cross-build
```

Build is clean as of 1.2.6 / cyrius 6.6.0 / ai-hwaccel 2.3.22 —
manifest pin and installed wrapper agree, `lib/` matches the pinned
snapshot exactly, and smoke's stderr is empty (ai-hwaccel's detect
logging is clamped for the duration of the one detect call; see the
1.2.2 note above).

Two warnings are expected and neither is mihi's to fix: seven
`undefined function 'bayan_json_v_*'` (the visible half of ai-hwaccel
2.3.20's feature gate — verified unreachable, DCE-eliminated), and, on
`--aarch64` only, `lib/io.cyr:442: raw syscall 32 is x86_64 dup` — in
the **vendored stdlib**, not mihi's 149-line `src/io.cyr`, and
CLAUDE.md forbids hand-editing `lib/`.

## Dependencies

Direct (declared in `cyrius.cyml`):

- **stdlib** — mihi's own probes need string, fmt, alloc, io, vec, str, slice, syscalls, `sys`, assert (+ ct, bench). The rest — fs, tagged, process, fnptr, thread, freelist, hashmap, `sakshi` — are there for the ai-hwaccel bundle: it is one concatenation, so the parser needs every module its modules reference in scope, and DCE drops unused code from the linked binary. `sakshi` joined at 1.2.2 for ai-hwaccel 2.3.x's detect-path logging. `bayan` left at 1.2.5 and must not come back — see the Toolchain note above.
- **`sys` (stdlib)** — the `uname(2)` / `sysinfo(2)` plumbing, with per-target `UTS_*` / `SI_*` offsets for Linux **and** AGNOS. mihi's four identity probes (kernel name / kernel version / cpu arch / hostname) share one `sys_uname` call. This replaced the `[deps.agnosys]` git dep at 1.1.3, when cyrius retired the stale stdlib agnosys snapshot at 6.2.37. See [ADR 0001](../adr/0001-shared-uts-buffer.md).
- **ai-hwaccel 2.3.22** (git dep) — accelerator detection. 2.2.5 was the first release with the no-exec contract (`registry_detect_no_exec()` masks off the subprocess-shelling backends — 9 of 18 as of 2.3.18, after `BACKEND_WINDOWS` joined the exec set); without it mihi couldn't honor the "probes are pure reads" rule. 2.2.6 closed the device-name + bundling gaps mihi's 0.4.0 integration surfaced. The 2.3.x line brought three ecosystem symbol de-collisions (`HWA_ERR_*`, `hw_registry_new`, `AIHW_BACKEND_COUNT` / `AiHwBackend` / `aihw_path_exists`), of which only `hw_registry_new` reaches mihi — in the test suite's synthetic-registry construction, not the probe source. 2.3.x also reserves `BACKEND_AGNOS_GPU` in the no-exec mask with **no detector dispatch wired yet**, so it is inert for mihi today. **2.3.20 → 2.3.22** (taken at 1.2.6) changes no symbol mihi calls: 2.3.20 feature-gated `[deps.bayan]` so it stops resolving transitively into consumers (this is what orphaned `lib/bayan-json.cyr` here); 2.3.21 is ai-hwaccel's own 6.6.0 bump plus four portability fixes, of which only "detector threads no longer log through single-threaded `sakshi`" touches a path mihi could reach — and mihi calls the *non*-threaded `registry_detect_no_exec()`; 2.3.22 fixed `load_models` returning 1 of 26 models, which has no caller in the detection path at all.

## Consumers

- [`iam`](https://github.com/MacCracken/iam) ✅ — first consumer
  integrated as of iam-0.9.0 (2026-05-19); at iam-1.1.5 it pins
  `[deps.mihi] tag = "1.2.1"`. Consumes the full mihi probe surface
  (kernel / cpu / mem / host / gpu) end-to-end, and is the runtime
  proof for the AGNOS work (1.1.2 / 1.2.0 / 1.2.1 were all verified
  through iam under QEMU).
- [`chakshu`](https://github.com/MacCracken/chakshu) ✅ — second
  consumer integrated as of chakshu-0.6.0 (2026-05-20); at
  chakshu-0.7.11 it pins `[deps.mihi] tag = "1.2.1"`. Consumes mihi for
  all identity / static-fact reads (hostname, kernel, distro, CPU
  model, core count, total/available memory, uptime,
  GPU/accelerators); chakshu owns per-frame deltas (CPU%, disk rate,
  network rate, per-pid stats). This integration closed mihi's M6 gate.

**Repinning to 1.2.6 requires a source edit, not just a tag bump.**
cyrius 6.6.0's value-form `Result` changes `mihi_uname`'s arity, so
every consumer's call site must become:

```cyrius
var t, v = mihi_uname(&uts);
if (is_err_result(t) == 1) { ... }
```

The old single-variable bind is a hard compile error naming the fix, so
the migration is mechanical and cannot silently miscompile — but it
does mean the mihi bump, the ai-hwaccel bump (`2.3.22`) and the
consumer's own cyrius pin (`6.6.0`) have to land in **one commit**: the
arity gate is the vendored `lib/result.cyr`, not `cycc`, and ai-hwaccel
2.3.21 measured both wrong pairings — an old dep against a new `lib/`
is a hard compile error, and a new dep against an old `lib/` **builds
clean and destructures a box pointer into a register pair**. That
second one is the dangerous half. Nothing else in mihi's surface
returns a `Result`.

Historical, for the 1.2.2 hop: **repinning was a three-part change for both**, because the
concatenated `dist/mihi.cyr` + `dist/ai-hwaccel.cyr` bundle has to stay
symbol-consistent: (1) `[deps.mihi] tag = "1.2.2"`, (2)
`[deps.ai-hwaccel] tag = "2.3.18"` — chakshu's manifest currently
carries an explicit "do NOT bump ahead of mihi" note pinning it to
2.2.6, which 1.2.2 releases, (3) add `"sakshi"` to `[deps] stdlib`
(the `dist/mihi.deps` sidecar declares it, so `cyrius deps` can pull
it). A consumer that bumps ai-hwaccel without mihi hits
`registry_new` → `hw_registry_new` head-on.

Planned for post-v1.0:

- [`hapi`](https://github.com/MacCracken/hapi) — target-box info on
  link/sync.
- [`BannerManor`](https://github.com/MacCracken/bannermanor) —
  hostname for banner auto-detect.

## Next

**v1.0 shipped — stewardship mode.** mihi is now API-frozen; future
changes have to respect the contract or wait for v2.0. No internal
work planned; the loop becomes (a) responding to consumer-side
issues that surface in iam / chakshu / future consumers, (b) tracking
upstream ai-hwaccel for dep bumps (current pin: 2.3.22) and cyrius for
toolchain pins (current: 6.6.0), (c) absorbing additions that fit the
"tell me about this box" surface without breaking signatures
(additive-only).

The freeze held through 1.2.5 and broke at **1.2.6** — not by choice:
cyrius 6.6.0's value-form `Result` changes `mihi_uname`'s arity, and
the toolchain and its vendored stdlib snapshot cannot be split. The
break is one bind at one call site, it fails loudly at compile time,
and it is the only signature mihi has ever had to move post-1.0.

Open follow-up from 1.2.2: **`BACKEND_AGNOS_GPU`.** ai-hwaccel 2.3.x
reserves the backend id and gives it an `ACCEL_AGNOS_GPU` type, but
ships no detector for it — when upstream wires one, mihi's gpu probes
gain accelerator identity on the sovereign target for free (they
already run the no-exec mask that includes it). Worth a smoke pass on
agnos at that point; nothing to do until then.

Anything outside the v1.0 contract — Windows / macOS, network probes,
monitoring concerns — stays out of scope per `roadmap.md`. If a new
domain needs probes, it spins out as a sibling lib (e.g. `mihi-net`)
rather than expanding the mihi surface.
