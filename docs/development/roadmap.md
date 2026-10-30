# mihi — Roadmap

> Open work only, grouped into releases. Shipped work lives in
> [`../../CHANGELOG.md`](../../CHANGELOG.md), live state in
> [`state.md`](state.md). An item leaves this file when it ships; one that
> slips moves to a later release rather than being marked done here.

Every 1.x release keeps the 1.0 contract. Probe signatures, return shapes
and error semantics stay frozen, and anything that would break them waits
in [v2.0](#v20--breaking-parked). The rules for probes (pure reads, one
source per fact, cited sources, caller-owned buffers) are in
[`CLAUDE.md`](../../CLAUDE.md).

## 1.4.x — Verification on real targets

Several facts in `state.md` are true by reading, not by running, on the
current pins. This release runs them.

- **AGNOS.** Run `scripts/mihi-agnos-verify.py` in QEMU on the current
  pins. It last ran at 1.2.4 (cyrius 6.5.35). Its prerequisites are an agnos
  build, `agnsh` and gnoboot's `BOOTX64.EFI`. This also covers the 1.3.2
  AGNOS fixes, which are compile-verified only: B-8 (CPUID max leaf), B-9
  (sysinfo bounds; a 0 CPU count is now -1), B-10 (the uname seal) and
  B-13 (`mihi_distro` into `buf`).
- **arm64 hardware.** Run the suite and the fuzz harness on agnosarm
  (Raspberry Pi 4). They last ran at 1.2.4, when the suite was 144
  assertions there. CI only compiles `--aarch64`; decide whether a
  `qemu-aarch64` run can be a gate, given that the device-tree assertions
  read the host's `/sys`.
- **Accelerator hosts.** ai-hwaccel 2.5.5's `/sys/class/accel` driver
  routing (the phantom-TPU fix), the Intel NPU path and the Vulkan sysfs
  scan have been read from source but never seen on hardware. Wanted: a
  Core Ultra or Ryzen AI host, plus an NVIDIA or Intel GPU host. Also a
  hybrid-graphics laptop, to measure whether `mihi_gpu_count()` wakes a
  runtime-suspended dGPU (audit U-1: `power/runtime_status` before and
  after).
- **Consumers.** `iam` and `chakshu` both pin mihi 1.2.1. Build each one
  against mihi HEAD in a scratch copy, confirm the 1.2.6 `mihi_uname`
  bind and the 1.2.8 sidecar change are the only edits they need, and
  leave a note in each repo. Do not edit them from here.
- **Acceptance**: each run recorded in `state.md` with date, host and pins.

## 1.5.x — Documentation and consumer guidance

- **`docs/examples/` is empty.** Add runnable examples: the smallest
  consumer (kernel / CPU / memory), and a GPU listing.
- **Guides.** Write a toolchain-bump guide (the pin-move recipe now lives
  only in `state.md`), and a consumer-integration guide. The integration
  guide should cover:
  - include order and repin rules;
  - the expected `bayan_json_v_*` warnings;
  - null handling (`mihi_cpu_model` on ACPI arm64, `mihi_gpu_name`);
  - sanitizing before rendering (mihi returns raw bytes, and a hostname,
    PRETTY_NAME or CPUID brand can carry control characters, audit L-3);
  - the LXCFS hang (U-3).
- Refresh `README.md` and `docs/guides/getting-started.md` against the
  current pins and the published sidecar.

## 1.6.x — Upstream follow-through

- **The bayan-json workaround.** File the cyrius issue: distlib's sidecar
  verify credits a name that only a named dep's module leaves undefined
  to the bundle being published. That is still true on 6.7.18. Once a
  fixed cyrius is pinned, drop `[deps.bayan]` and `[features]` and confirm
  the sidecar stays `sys syscalls`.
- **The sakshi log-level clamp** in `_mihi_gpu_ensure()`. Since ai-hwaccel
  2.5.5 keeps its own WARN threshold, the clamp changes nothing by
  default. It still caps a consumer that raised ai-hwaccel's level for
  mihi's one detect call. Decide whether to keep it; the 1.2.2 tests pin
  the save / restore.
- **ai-hwaccel's no-exec PCIe pass wakes suspended devices** (audit U-1).
  `enrich_pcie` reads `max_link_{width,speed}`, which the kernel serves
  through `pci_config_pm_runtime_get()`. File the issue upstream, asking
  for a no-wake path: skip a device whose `power/runtime_status` is
  `suspended`; reading that attribute does not resume the device. Take
  the fix when it ships.
- **gpu.cyr on AGNOS.** `programs/smoke.cyr` faults on AGNOS before its
  first line because it links the ai-hwaccel bundle (thread / atomic,
  Linux `CLONE_VM`). Re-measure with ai-hwaccel 2.5.5. If it still
  faults, write an ADR on whether the gpu probes report an empty registry
  on AGNOS, or whether the blocker stays until upstream fixes it.

## 1.7.x — Coverage gaps (additive, inside the planned module set)

- **`mihi_cpu_model` on ACPI-booted arm64** still returns null, because
  there is no device tree; this is the residual from finding D-1.
  Candidates are the SMBIOS processor record
  (`/sys/firmware/dmi/entries/4-*/raw`) or a MIDR implementer / part
  table. Either must be argued as that boot path's own source, not a
  fallback chain, in an ADR before any code.
- **arm64: `cpu@0` is conventional, not guaranteed** (audit L-5). A cpu
  node's unit address is its MPIDR affinity. Settle it with the ACPI item
  above: the first cpu node, or the boot CPU's.
- **os-release conformance.** All four are documented limits in
  `docs/sources.md`. Implement each one or keep the limit, and say which:
  - backslash escapes (the D-3 tail) are left intact;
  - with duplicate keys the first wins, where a shell takes the last
    (audit L-1);
  - a CRLF bare value keeps its `\r` (L-2);
  - `/usr/lib/os-release` is not consulted when `/etc/os-release` is
    absent, although os-release(5) defines that lookup (L-4). This one
    is a second path, so it needs an ADR.
- **The AGNOS-native source of truth.** CLAUDE.md says kernel facts come
  from the boot-info struct at handoff. The shipped AGNOS arms use AGNOS's
  own `uname` / `sysinfo` syscalls. Decide which is the target and record
  it in an ADR.

## 1.x.x — Gated, no release assigned

- **`BACKEND_AGNOS_GPU` detector.** ai-hwaccel reserves the backend and
  `ACCEL_AGNOS_GPU` but ships no detector. When one lands, mihi's gpu
  probes should report accelerators on AGNOS with no mihi-side change;
  run an AGNOS smoke pass then. *Gate: upstream ai-hwaccel.*
- **Locking for the gpu singleton** (finding A-6). This is ADR 0002's
  alternative 3. *Gate: a multi-threaded consumer.*
- **The read path's last race** (audit U-3). A device node swapped in
  between `stat` and `open` is still opened. Closing that means an
  `O_PATH` open plus a re-open through `/proc/self/fd`, which breaks the
  distro probe where `/proc` is not mounted. *Gate: a consumer that needs
  it, weighed against chroot / minimal-container support.*
- **New consumers.** `hapi` (target-box info on link / sync) and
  `BannerManor` (hostname for banner auto-detect). mihi-side work only
  if they need a fact mihi lacks. *Gate: their integration.*

## v2.0 — breaking, parked

Not on the 1.x line. Each one changes a frozen signature.

- **`mihi_cpu_brand_fill(buf, cap)`** (finding A-7). The public helper
  stores 48 bytes with no capacity parameter. The comment on it is the
  contract until then.
- **A `MihiInfo` envelope / `mihi_collect(info)`**, deferred in ADR 0001.
  Only if a consumer needs one-call collection.

## Out of scope

Keeps the probe surface from growing by accident. Changing any of these
needs an ADR.

- **Windows / macOS probes** — Linux and AGNOS only.
- **GPU temperature, fan speed, power draw** — monitoring concerns that
  belong to `chakshu`, not a static probe library.
- **Network info** (interfaces, IPs, MACs) — a future `mihi-net` sibling
  if needed.
- **Process info** (per-process uptime, top consumers) — `chakshu` and
  `ps`-equivalents own it.
- **Configurable output format** — mihi returns raw values; formatting
  lives in consumers.
- **Caching layer** — every probe is a fresh read; the gpu singleton is
  the one documented exception ([ADR 0002](../adr/0002-gpu-singleton-cache.md)).
- **Daemon mode** — mihi is a library, not a service.

## Cross-references

- [`state.md`](state.md) — live status: version, pins, sizes, consumers
- [`../sources.md`](../sources.md) — per-probe citation index
- [`../audit/`](../audit/) — audit reports
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — release history
