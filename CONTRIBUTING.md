# Contributing to mihi

Contributions are welcome. All contributions must be licensed under
GPL-3.0-only.

## Development

Follow the conventions in [`CLAUDE.md`](CLAUDE.md) and the AGNOS
[first-party standards](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-standards.md).

Build and test before submitting:

```sh
cyrius deps
cyrius build programs/smoke.cyr build/mihi-smoke
cyrius test
```

## Probe additions

Every new probe needs:

1. A canonical source citation in an inline comment on the declaring
   function (`/proc/*`, `/sys/*`, or a syscall — pick one, no fallback chains).
2. A happy-path test + at least one error-path test (missing file,
   malformed content) in `tests/mihi.tcyr`.
3. An entry in `docs/sources.md` linking to the Linux man page or
   kernel documentation that defines the source.
4. A CHANGELOG entry under `Added` with the source citation.

## Reporting Issues

Open an issue at https://github.com/MacCracken/mihi/issues.

For security-sensitive issues, see [`SECURITY.md`](SECURITY.md)
instead.
