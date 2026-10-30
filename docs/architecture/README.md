# Architecture notes

Non-obvious constraints, quirks, and invariants that a reader cannot derive from the code alone. Numbered chronologically — never renumber.

Not decisions (those live in [`../adr/`](../adr/)) and not guides (those live in [`../guides/`](../guides/)). An item here describes *how the world is*, not *what we chose* or *how to do something*.

## Items

- [001 — Bundle order, the published sidecar, and bayan](001-bundle-and-dependency-shape.md): why `[lib].modules` is ordered as it is, why `[deps] stdlib` is mihi's own build only, why four modules include `lib/sys.cyr`, and why bayan is an optional thin-module dep and never the monolith.
