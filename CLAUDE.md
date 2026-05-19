# mihi — Claude Code Instructions

> **Core rule**: this file is **preferences, process, and procedures** —
> durable rules that change rarely. Volatile state (current version,
> module line counts, supported backends, test counts, dep-gap status,
> consumers) lives in [`docs/development/state.md`](docs/development/state.md).
> Do not inline state here.

## Project Identity

**mihi** (Maori: मिही — *the formal self-introduction ceremony in te reo, stating mountain, river, ancestors, name*) — shared system-info probe library for AGNOS first-party tools.

- **Type**: Shared library (Cyrius `[lib]` modules → `cyrius distlib` → `dist/mihi.cyr`)
- **License**: GPL-3.0-only
- **Language**: Cyrius (toolchain pinned in `cyrius.cyml [package].cyrius`)
- **Version**: `VERSION` at the project root is the source of truth — do not inline the number here
- **Genesis repo**: [agnosticos](https://github.com/MacCracken/agnosticos)
- **Standards**: [First-Party Standards](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-standards.md) · [First-Party Documentation](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md)
- **Shared crates registry**: [shared-crates.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/shared-crates.md)

## Goal

Own the system-fact probe surface for AGNOS userland — CPU / RAM / GPU / kernel / uptime / distro / hostname. One small, well-cited library that consumers (`iam`, `chakshu`, `hapi`, `BannerManor`) include for "tell me about this box." A system performing `mihi` is exactly what this library enables: the box telling whoever asks who it is.

## Current State

> Volatile state lives in [`docs/development/state.md`](docs/development/state.md) —
> current version, module sizes, supported probe backends, consumer
> integrations. Refreshed every release.

This file (`CLAUDE.md`) is durable rules.

## Scaffolding

Project was scaffolded with `cyrius init mihi` then re-shaped into the `[lib]` modules pattern (parallel to [`darshana`](https://github.com/MacCracken/darshana)). **Do not manually create project structure** — use the tools. If a tool is missing something, fix the tool.

## Quick Start

```sh
cyrius deps                                           # resolve stdlib
cyrius build programs/smoke.cyr build/mihi-smoke     # build smoke binary
./build/mihi-smoke                                    # exit 0 = clean
cyrius test                                           # run tests/*.tcyr
```

To produce the consumable bundle:

```sh
cyrius distlib                                        # concatenates [lib].modules → dist/mihi.cyr
```

Consumers include via:

```cyrius
include "lib/mihi.cyr"   // after `cyrius deps` resolves the [deps.mihi] entry
```

## Key Principles

- **Probes are pure reads.** Never touch state. Never mutate a file. Never spawn a process. Every probe is a `syscall(open/read/close)` over `/proc`, `/sys`, or a uname-class syscall.
- **One source per fact.** Don't fall back from `/proc/cpuinfo` to `lscpu` to env vars to dmidecode — pick the canonical Linux source; if it's not present, return error. Fallback chains create non-determinism and consumers can't pin behavior.
- **Cite every source.** Per first-party-standards (this is a domain/data crate), every fact has a `/proc` / `/sys` / syscall citation in the declaring function's comment. No magic field offsets.
- **AGNOS-native is a separate code path, not a fallback.** On AGNOS-native, kernel facts come from the boot-info struct at handoff, not by faking Linux paths. The interpretive compat layer is permanently separate from the native path.
- **No allocator dependency from probe internals.** Probes write into caller-supplied buffers; consumers control lifetime. The `alloc_init()` in smoke/tests is for the smoke binary, not the library surface.
- **No string interpolation for output formatting.** mihi returns raw bytes / pointers + lengths. Pretty-printing lives in `iam` / `chakshu` / consumers.
- **Test domain logic extensively** — every probe gets a happy path + at least one error path (file missing, malformed content).

## Rules (Hard Constraints)

- **Read the genesis repo's CLAUDE.md first** — [agnosticos/CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/CLAUDE.md)
- **Do not commit or push** — the user handles all git operations
- **Never use `gh` CLI** — use `curl` to the GitHub API only
- Do not skip tests before claiming changes work
- Do not use `sys_system()` or `exec_*` from inside probe functions — probes are read-only
- Do not trust external data (`/proc` content, kernel boot-info) without bounds + range validation
- Do not modify `lib/` files (vendored stdlib / dep symlinks managed by `cyrius deps`)
- Do not add a `fn main()` body to library modules — the library entry is `src/main.cyr`'s include-only re-export shape
- Do not hardcode toolchain versions in CI YAML — `cyrius = "X.Y.Z"` in `cyrius.cyml` is the source of truth
- Do not add probes outside the planned module set without an ADR — the module shape is part of the v1.0 contract

## Process

### P(-1): Hardening (before v0.2.0 first feature cut, and before v1.0)

1. **Cleanliness** — `cyrius build` clean, `cyrius lint` clean, all tests pass
2. **Benchmark baseline** — `cyrius bench`, save CSV (when probes have real bodies)
3. **Internal review** — every probe's `/proc` parser audited for malformed input, bounds, integer overflow
4. **External research** — Linux source-of-truth doc for each probe (man procfs, kernel docs)
5. **Security audit** — bounds, buffer safety, syscall returns; file findings in `docs/audit/YYYY-MM-DD-audit.md`
6. **Documentation audit** — source citations on every probe; `docs/sources.md` complete; ADRs for any module-shape decisions

### Work Loop (continuous)

1. **Work phase** — new probe, bug fix, doc improvement
2. **Build check** — `cyrius build programs/smoke.cyr build/mihi-smoke`
3. **Test additions** — happy + error path per probe in `tests/mihi.tcyr`
4. **Internal review** — buffer bounds, syscall returns, citation present
5. **Documentation** — update CHANGELOG, `docs/development/state.md`, source citation
6. **Version sync** — `VERSION`, `cyrius.cyml`, CHANGELOG header in sync before tag

### Task Sizing

- **Low/Medium effort**: batch freely — multiple probes per cycle
- **Large effort**: small bites only — break into sub-tasks, verify each
- **If unsure**: treat it as large

## Cyrius Conventions

- All struct fields are 8 bytes (`i64`), accessed via `load64`/`store64` with offset
- Heap allocation via `fl_alloc()`/`fl_free()` for individual-lifetime data
- Bump allocation via `alloc()` for long-lived data (vec, str internals)
- Enum values for constants — don't consume `gvar_toks` slots (256 limit)
- `break` in while loops with `var` declarations is unreliable — use flag + `continue`
- No negative literals — write `(0 - N)` not `-N`
- `match`, `return;` (without value), and block-scoped `var` are all reserved/invalid — see [cyrius CLAUDE.md](https://github.com/MacCracken/cyrius/blob/main/CLAUDE.md)

## Docs

- [`docs/adr/`](docs/adr/) — Architecture Decision Records (*why X over Y?*)
- [`docs/architecture/`](docs/architecture/) — Non-obvious constraints (*what's true about the code?*)
- [`docs/guides/`](docs/guides/) — Task-oriented how-tos
- [`docs/examples/`](docs/examples/) — Runnable examples
- [`docs/development/state.md`](docs/development/state.md) — Live state snapshot
- [`docs/development/roadmap.md`](docs/development/roadmap.md) — Milestones through v1.0
- [`docs/sources.md`](docs/sources.md) — Per-probe `/proc`/`/sys`/syscall citation index (required before v1.0)

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md).

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/). Probe additions go under `Added` with the source citation. Probe-output format changes are `Breaking` until v1.0, after which the API is frozen.
