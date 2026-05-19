# Getting started with mihi

mihi is a **library**, not a binary. You don't run `mihi`; consumers
include it.

## Build the smoke binary

The smoke binary proves the library compiles end-to-end. CI builds
this on every push.

```sh
cyrius deps                                           # resolve stdlib
cyrius build programs/smoke.cyr build/mihi-smoke     # compile
./build/mihi-smoke                                    # prints "mihi smoke ok"
cyrius test                                           # run tests/*.tcyr
```

## Layout

- `src/types.cyr` — shared types
- `src/cpu.cyr` — CPU probes (`mihi_cpu_*`)
- `src/mem.cyr` — memory probes (`mihi_mem_*`)
- `src/kernel.cyr` — kernel-identity probes (`mihi_kernel_*`)
- `src/host.cyr` — host-identity probes (`mihi_hostname`, `mihi_uptime_secs`, `mihi_distro`)
- `src/main.cyr` — in-tree convenience entry (re-exports the modules). **Not** part of the `cyrius distlib` bundle — that's intentional; the dist bundle would otherwise duplicate the module bodies.
- `programs/smoke.cyr` — smoke binary entry. Builds via `cyrius build`.
- `tests/mihi.{tcyr,bcyr,fcyr}` — tests / benchmarks / fuzz.

## Build the consumable bundle

For consumers that include mihi via `[deps.mihi]`:

```sh
cyrius distlib                # concatenates [lib].modules → dist/mihi.cyr
```

After a consumer runs `cyrius deps`, they include via:

```cyrius
include "lib/mihi.cyr"        # resolved by cyrius deps from [deps.mihi]
```

## Adding a probe

1. Identify the canonical Linux source (`/proc/*`, `/sys/*`, or a uname-class syscall). One source per fact — no fallback chains.
2. Add the function to the appropriate module (`src/cpu.cyr`, `src/mem.cyr`, etc.).
3. Include the source citation as an inline comment on the declaring function (see existing stubs for shape).
4. Add a happy-path test + a missing-file error-path test to `tests/mihi.tcyr`.
5. Run `cyrius test`.
6. If the function changes the public surface, add an entry to `docs/sources.md`.
7. Bump `VERSION` and add a CHANGELOG entry before tagging.

See [`../adr/template.md`](../adr/template.md) when a non-trivial
design choice (e.g., adding a non-standard probe, breaking a public
signature) deserves an ADR.

## What mihi does NOT do

- No formatting (consumers do that)
- No caching (every probe is a fresh read)
- No daemon mode (mihi is a library)
- No Windows / macOS (Linux + AGNOS-native only for v1.0)

See `docs/development/roadmap.md` § "Out of scope" for the full list.
