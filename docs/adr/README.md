# Architecture Decision Records

Decisions about mihi — what we chose, the context, and the consequences we accept. Use these when a future reader would reasonably ask *"why did we do it this way?"*

## Conventions

- **Filename**: `NNNN-kebab-case-title.md`, zero-padded to four digits. Never renumber.
- **One decision per ADR.** If a decision supersedes a prior one, add a new ADR and set the old one's status to `Superseded by NNNN`.
- **Status lifecycle**: `Proposed` → `Accepted` → (optionally) `Superseded` or `Deprecated`.
- Use [`template.md`](template.md) as the starting point.

## ADR vs. architecture note vs. guide

| Kind | Lives in | Answers |
|---|---|---|
| ADR | `docs/adr/` | *Why did we choose X over Y?* |
| Architecture note | `docs/architecture/` | *What non-obvious constraint is true about the code?* |
| Guide | `docs/guides/` | *How do I do X?* |

## Index

- [0001 — Shared uts buffer for uname-backed probes](0001-shared-uts-buffer.md) — caller-supplied 390-byte buffer; one `uname(2)` serves four facts.
- [0002 — gpu.cyr module-level singleton cache](0002-gpu-singleton-cache.md) — lazy process-lifetime registry from `ai-hwaccel::registry_detect_no_exec()`; departs from ADR 0001's caller-buffer rule because the accelerator registry isn't a flat buffer.
