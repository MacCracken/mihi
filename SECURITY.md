# Security Policy

## Threat surface

mihi is a read-only probe library. Every public function is a
syscall-bounded read against `/proc`, `/sys`, or a uname-class
syscall. mihi does not:

- Spawn processes
- Open network sockets
- Write to the filesystem
- Hold privileged credentials

The realistic threat is **malformed input** from `/proc` or `/sys`
files (e.g., on a system where these are simulated, mounted from
untrusted sources, or subject to TOCTOU during the read). Every
probe must validate bounds and integer ranges before consumers see
the result.

## Reporting Vulnerabilities

Report vulnerabilities privately to **security@agnos.dev**. Do not
open public issues for security bugs.

We will acknowledge receipt within 48 hours and provide a timeline
for a fix.
