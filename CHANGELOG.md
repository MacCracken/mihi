# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
