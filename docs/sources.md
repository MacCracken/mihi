# mihi — probe source citations

> Required-by-v1.0 index. Every probe gets a row before API freeze.
> Authority is **Linux**: man pages, kernel docs, kernel source. AGNOS-native
> entries land separately when boot-info handoff stabilises.

## Convention

- **Path / syscall**: the canonical Linux source. Single source per fact.
- **Authority**: man-page section + kernel-doc / kernel-source pointer.
- **Notes**: caveats, layout pins, error-path behaviour.

## Slice A — uname-backed probes (M1, v0.2.0)

All three share one `uname(2)` call into a caller-supplied 390-byte
buffer; see [ADR 0001](adr/0001-shared-uts-buffer.md) for the shared
buffer convention.

| Probe                  | Source                              | Authority                                                                          | Notes |
| ---------------------- | ----------------------------------- | ---------------------------------------------------------------------------------- | ----- |
| `mihi_kernel_name`     | `uname(2)` → `utsname.sysname`      | man 2 uname; `<asm-generic/utsname.h>`; kernel `arch/*/kernel/sys.c::sys_newuname` | Always "Linux" on Linux. Field is a 65-byte null-terminated buffer at offset 0. |
| `mihi_kernel_version`  | `uname(2)` → `utsname.release`      | man 2 uname; kernel `include/generated/utsrelease.h`                               | The `uname -r` string; baked at kernel build time. 65-byte buffer at offset 130. |
| `mihi_cpu_arch`        | `uname(2)` → `utsname.machine`      | man 2 uname                                                                        | Arch identifier (`x86_64`, `aarch64`, …). 65-byte buffer at offset 260. |

## Slice B — /proc + /sys parsers (M1, v0.2.0)

Each probe opens, reads, and closes its source per call — no caching,
no module-private state. `mihi_cpu_model` mutates the caller-supplied
read buffer (writes one NUL byte to terminate the value).

| Probe             | Source                                      | Authority                                                                                                                                 | Notes |
| ----------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| `mihi_cpu_count`  | `/sys/devices/system/cpu/online`            | `Documentation/admin-guide/cputopology.rst`; kernel `kernel/cpu.c::cpu_online_mask` printed via `%*pbl` format                            | Parses comma-separated ranges (`"0-15"`, `"0-3,5-7"`, `"0"`). Bare `N` treated as `N-N`. 64-byte stack scratch is plenty (max range string is short). |
| `mihi_cpu_model`  | `/proc/cpuinfo` first `model name` value    | man 5 proc; kernel `fs/proc/cpuinfo.c` → arch `show_cpuinfo()` (e.g. `arch/x86/kernel/cpu/proc.c`)                                        | Line-anchored search for `"\nmodel name"` pins us to CPU 0's block — first-block-only honours "one source per fact" on big.LITTLE. Caller supplies 8 kB scratch. |

## Slice C — /proc/meminfo (M1, v0.2.0)

Both probes share the field-finder + kB-parser helpers
(`mihi_find_meminfo_field`, `mihi_parse_meminfo_kb`,
`mihi_extract_meminfo_bytes`); each is exposed for unit testing.
Field anchor accepts file-start (MemTotal is the first line) and
`'\n'`-prefixed mid-buffer matches. Values returned as bytes
(kB × 1024).

| Probe             | Source                                | Authority                                                                                  | Notes |
| ----------------- | ------------------------------------- | ------------------------------------------------------------------------------------------ | ----- |
| `mihi_mem_total`  | `/proc/meminfo` `MemTotal:`           | man 5 proc; kernel `fs/proc/meminfo.c::meminfo_proc_show()`                                 | Always present on Linux; file-start anchored. Caller supplies 4 kB scratch (meminfo ≈ 1.5 kB). |
| `mihi_mem_free`   | `/proc/meminfo` `MemAvailable:`       | kernel commit 34e431b0ae39 (3.14+); `fs/proc/meminfo.c`                                     | Picked over `MemFree:` because MemAvailable counts reclaimable cache/slab — the kernel's own "actually usable" estimate that monitoring tools surface as "free". |

## Pending (filled as M2/M3 land)

| Probe              | Planned source                                | Slice |
| ------------------ | --------------------------------------------- | ----- |
| `mihi_hostname`    | `uname(2)` → `utsname.nodename`               | M2    |
| `mihi_uptime_secs` | `/proc/uptime` first field                    | M2    |
| `mihi_distro`      | `/etc/os-release` `PRETTY_NAME`, fallback `ID` | M2    |
| `mihi_gpu_*`       | via `ai-hwaccel` (single source)              | M3    |
