# mihi — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

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

- **Cyrius pin**: `6.5.35` (in `cyrius.cyml [package].cyrius`). Bumped
  6.2.37 → 6.5.35 at the 1.2.2 cut, closing the drift against the
  installed wrapper. `cyrius lib sync --full` re-vendored the
  version-matched snapshot: **108 stdlib modules**, `lib/` now matching
  the pin exactly (plus `lib/ai-hwaccel.cyr`, the one git dep).
- **`[deps] stdlib`** (21 modules): `string`, `fmt`, `alloc`, `io`,
  `vec`, `str`, `slice`, `syscalls`, `sys`, `assert`, `fs`, `tagged`,
  `process`, `fnptr`, `thread`, `freelist`, `hashmap`, `sakshi`, `ct`,
  `bayan`, `bench`. Most are there for the ai-hwaccel bundle, not for
  mihi's own probes — the bundle is one concatenation, so the parser
  needs the full set in scope and DCE drops what the binary doesn't
  reach. `sakshi` joined at 1.2.2 (ai-hwaccel 2.3.x logging); `bayan`
  replaced the standalone `json` at 1.1.1 (6.2.x data-format reorg).
- **Pruned orphans**: `lib/` carried ten modules the 6.5.35 snapshot no
  longer ships — `agnosys` + `agnosys-core` (retired at cyrius 6.2.37;
  mihi rewired off the dep at 1.1.3), `base64` / `bigint` / `csv` /
  `cyml` / `toml` / `u128` (absorbed into `bayan`), `linalg` / `matrix`
  (absorbed into `ganita`). Removed at 1.2.2, finishing the prune 1.1.1
  started with `json`.

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
- `src/cpu.cyr` (263) — `mihi_cpu_arch` ✅ + `mihi_cpu_count` ✅ + `mihi_cpu_model` ✅ (+ `mihi_parse_cpu_range` / `mihi_parse_cpu_model` pure-function helpers, and `mihi_cpu_model_cpuid` / `mihi_cpu_brand_fill` — the x86 CPUID brand-string path the AGNOS build dispatches to)
- `src/mem.cyr` (113) — `mihi_mem_total` ✅ + `mihi_mem_free` ✅ (+ `mihi_find_meminfo_field` / `mihi_parse_meminfo_kb` / `mihi_extract_meminfo_bytes` helpers)
- `src/kernel.cyr` (44) — `mihi_uname` wrapper over `sys_uname` (`Result`-wrapped since 1.1.3) + `mihi_kernel_name` ✅ + `mihi_kernel_version` ✅
- `src/host.cyr` (172) — `mihi_hostname` ✅ + `mihi_uptime_secs` ✅ + `mihi_distro` ✅ (+ `mihi_parse_uptime_secs` / `mihi_find_osrelease_key` / `mihi_parse_osrelease_value` helpers)
- `src/gpu.cyr` (168) — `mihi_gpu_count` ✅ + `mihi_gpu_name` ✅ + `mihi_gpu_memory_bytes` ✅ + `mihi_gpu_family` ✅ + `mihi_gpu_type` ✅ (module-level singleton cache via `_mihi_gpu_ensure`; first call runs `registry_detect_no_exec()` under a save/clamp/restore of the caller's `sakshi` log level)
- `src/main.cyr` (22) — convenience re-export (consumed by smoke + tests; not in distlib bundle)
- `programs/smoke.cyr` (120) — smoke binary; prints `kernel / release / arch / host / model / cpus / mem MiB / free MiB / uptime / distro / gpu cnt / gpu / gpu MiB`
- `dist/mihi.cyr` (786 lines; 764 by `cyrius distlib`'s non-blank count) — the consumable bundle; `dist/mihi.deps` is the stdlib-leaf sidecar beside it (cyrius 6.5.x), both CI-gated against drift

## Tests

- `tests/mihi.tcyr` — primary suite: **116 assertions across 45 test
  groups** (104 from the 0.5.0 hardening push, 4 from the 0.6.0 audit
  regressions, 5 from the 1.2.0 CPUID work, 3 from the 1.2.2 log-level
  clamp). Slice A: real-uname happy path + zero-init buffer +
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
- `tests/mihi.bcyr` — benchmark stub
- `tests/mihi.fcyr` — fuzz stub

## Build

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
./build/mihi-smoke            # 11+ lines incl. gpu cnt / gpu / gpu MiB + "mihi smoke ok", exit 0, empty stderr
cyrius test tests/mihi.tcyr   # 116/116 pass
cyrius build --agnos programs/smoke.cyr build/mihi-smoke-agnos   # sovereign-target cross-build
```

Build is clean as of 1.2.2 / cyrius 6.5.35 / ai-hwaccel 2.3.18 —
manifest pin and installed wrapper agree, `lib/` matches the pinned
snapshot exactly, and smoke's stderr is empty (ai-hwaccel's detect
logging is clamped for the duration of the one detect call; see the
1.2.2 note above).

## Dependencies

Direct (declared in `cyrius.cyml`):

- **stdlib** — mihi's own probes need string, fmt, alloc, io, vec, str, slice, syscalls, `sys`, assert (+ ct, bench). The rest — fs, tagged, process, fnptr, thread, freelist, hashmap, `sakshi`, bayan — are there for the ai-hwaccel bundle: it is one concatenation, so the parser needs every module its modules reference in scope, and DCE drops unused code from the linked binary. `bayan` is the 6.2.x data-format bundle that absorbed the standalone `json` module (ai-hwaccel's `registry_to_json` symbols resolve through its back-compat aliases); `sakshi` joined at 1.2.2 for ai-hwaccel 2.3.x's detect-path logging.
- **`sys` (stdlib)** — the `uname(2)` / `sysinfo(2)` plumbing, with per-target `UTS_*` / `SI_*` offsets for Linux **and** AGNOS. mihi's four identity probes (kernel name / kernel version / cpu arch / hostname) share one `sys_uname` call. This replaced the `[deps.agnosys]` git dep at 1.1.3, when cyrius retired the stale stdlib agnosys snapshot at 6.2.37. See [ADR 0001](../adr/0001-shared-uts-buffer.md).
- **ai-hwaccel 2.3.18** (git dep) — accelerator detection. 2.2.5 was the first release with the no-exec contract (`registry_detect_no_exec()` masks off the subprocess-shelling backends — 9 of 18 as of 2.3.18, after `BACKEND_WINDOWS` joined the exec set); without it mihi couldn't honor the "probes are pure reads" rule. 2.2.6 closed the device-name + bundling gaps mihi's 0.4.0 integration surfaced. The 2.3.x line brought three ecosystem symbol de-collisions (`HWA_ERR_*`, `hw_registry_new`, `AIHW_BACKEND_COUNT` / `AiHwBackend` / `aihw_path_exists`), of which only `hw_registry_new` reaches mihi — in the test suite's synthetic-registry construction, not the probe source. 2.3.x also reserves `BACKEND_AGNOS_GPU` in the no-exec mask with **no detector dispatch wired yet**, so it is inert for mihi today.

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

**Repinning to 1.2.2 is a three-part change for both**, because the
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
upstream ai-hwaccel for dep bumps (current pin: 2.3.18) and cyrius for
toolchain pins (current: 6.5.35), (c) absorbing additions that fit the
"tell me about this box" surface without breaking signatures
(additive-only).

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
