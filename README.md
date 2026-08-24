# mihi

मिही — system-info probe library. CPU, RAM, GPU, kernel, uptime,
distro, hostname. Substrate for [iam](https://github.com/MacCracken/iam)
(login MOTD / screenshot flex) and [chakshu](https://github.com/MacCracken/chakshu)
(AI-augmented system monitor); designed for any tool that needs to ask
"tell me about this box."

**Maori:** *the formal self-introduction ceremony in te reo* — stating
mountain, river, ancestors, name. A system performing mihi is exactly
what this library enables: the box telling whoever asks who it is.

Pairs linguistically with [hapi](https://github.com/MacCracken/hapi) —
both Polynesian-family. hapi (Hawaiian) for the experiential layer,
mihi (Maori) for the substrate.

## Status

**Stable — API frozen since 1.0.0.** 15 probes across five modules
(`cpu` / `mem` / `kernel` / `host` / `gpu`, plus a `types` placeholder):
CPU arch / count / model, total + free memory, kernel name + version,
hostname / uptime / distro, and accelerator count / name / memory /
family / type. Signatures, return shapes, and error semantics are
contract; changes to them wait for a major bump.

Every probe is a pure read — an `open`/`read`/`close` over `/proc` or
`/sys`, a `uname`/`sysinfo` syscall, or (on x86) the `cpuid`
instruction. No process is ever spawned and no file is ever written.
Probes fill buffers you supply, so you own the lifetime — the one
exception is the accelerator registry behind the `gpu` probes, a
process-lifetime singleton mihi owns and never frees (see
[ADR 0002](docs/adr/0002-gpu-singleton-cache.md)). Formatting is the
consumer's job; mihi returns raw values.

Both Linux and AGNOS are supported targets — on AGNOS the probes that
would need procfs read the kernel's `sysinfo` struct or CPUID instead,
which is a separate code path rather than a fallback chain.

## Build

```sh
cyrius deps                                        # resolve stdlib + deps
cyrius build programs/smoke.cyr build/mihi-smoke   # smoke binary
./build/mihi-smoke                                 # prints the full fact set, exit 0
cyrius test tests/mihi.tcyr                        # 143 assertions
```

## Consume

```cyrius
include "lib/mihi.cyr"   // after `cyrius deps` resolves mihi
```

`lib/mihi.cyr` is the `cyrius distlib` bundle — `[lib].modules` from
`cyrius.cyml` concatenated in dependency order. In-tree development
goes through `src/main.cyr`, which re-exports the same module set.

## License

GPL-3.0-only
