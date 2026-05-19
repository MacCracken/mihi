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

## Pending (filled as M1/M2 land)

| Probe              | Planned source                                | Slice |
| ------------------ | --------------------------------------------- | ----- |
| `mihi_cpu_model`   | `/proc/cpuinfo` "model name" (first block)    | B     |
| `mihi_cpu_count`   | `/sys/devices/system/cpu/online`              | B     |
| `mihi_mem_total`   | `/proc/meminfo` `MemTotal:` (kB → bytes)      | C     |
| `mihi_mem_free`    | `/proc/meminfo` `MemAvailable:`               | C     |
| `mihi_hostname`    | `uname(2)` → `utsname.nodename`               | M2    |
| `mihi_uptime_secs` | `/proc/uptime` first field                    | M2    |
| `mihi_distro`      | `/etc/os-release` `PRETTY_NAME`, fallback `ID` | M2    |
| `mihi_gpu_*`       | via `ai-hwaccel` (single source)              | M3    |
