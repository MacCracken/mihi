# 001 — Bundle order, the published sidecar, and bayan

What `cyrius.cyml` declares and why, stated once here so the manifest can stay
a manifest. Each item is a constraint the code relies on that the manifest
cannot explain in a key.

## `[lib].modules` order is load-bearing

`cyrius distlib` concatenates the modules in the listed order into
`dist/mihi.cyr`, and cyrius resolves names in one pass:

- `src/types.cyr` comes first. It is empty today; `MihiInfo` lands there if it
  ever ships ([ADR 0001](../adr/0001-shared-uts-buffer.md)).
- `src/io.cyr` comes before every probe that reads a file. It is the one
  `/proc` + `/sys` read path that `cpu.cyr`, `mem.cyr` and `host.cyr` call
  ([ADR 0003](../adr/0003-shared-probe-read.md)).
- `src/gpu.cyr` comes last. It calls into ai-hwaccel (`registry_detect_no_exec`,
  `reg_profiles`, `profile_*`, `FAMILY_CPU`), which the bundle does not
  contain. A consumer includes `lib/ai-hwaccel.cyr` before `lib/mihi.cyr`.

`src/main.cyr` and `src/test.cyr` are not in the list. They are the include
hub for smoke and tests, and listing them would duplicate every module body.

## `[deps] stdlib` is mihi's own build, not the consumer's

Since cyrius 6.6.18, `dist/mihi.deps` (the sidecar consumers' `cyrius deps`
reads) is derived by `cyrius distlib`'s compile-verify. `[deps] stdlib` never
reaches it. The list is what mihi's own sources call directly: `src/`,
`programs/`, `tests/` (`assert`) and `benches/` (`bench`). A leaf that only a
dependency needs belongs to that dependency's sidecar, not here.

The verify seeds the sidecar with the `include "lib/<leaf>.cyr"` lines the
bundled modules carry, then compiles and adds owners for whatever is still
undefined. That is why `cpu.cyr`, `mem.cyr`, `kernel.cyr` and `host.cyr` each
include `lib/sys.cyr` even though mihi's own build prepends it. The include
states mihi's real dependency, and it makes `sys` the owner of `UTS_*` in the
verify. Without it, cyrius 6.6.20's verify took the first snapshot file
declaring `UTS_MACHINE`, in the publishing host's directory order, and that was
the sigil fold's copy of the enum. Since 6.7.7 the owner rule picks `sys`
either way (measured on 6.7.9). The include stays.

## bayan: the thin module, optional, never the monolith

bayan ships thin modules so a consumer can take only the part it uses. The
full `lib/bayan.cyr` (json, toml, cyml, csv, base64, bigint, u128, yaml, pdf)
is 641 KB; `dist/bayan-json.cyr` is the JSON part alone.

`dist/ai-hwaccel.cyr` references ten `bayan_json_v_*` functions (seven before
ai-hwaccel 2.5.5) and defines none. They sit in its `profile_from_json`
deserialize path, which nothing in ai-hwaccel calls, so they are unreachable.
ai-hwaccel declares bayan optional and leaves the names to a consumer that
wants that path. mihi never calls it.

So mihi declares `[deps.bayan]` on the thin JSON module, `optional = true`
with `[features] default = ["bayan"]`. distlib's compile-verify then resolves
the `bayan_json_v_*` names to that module, and mihi's sidecar stays `sys
syscalls`. With no bayan dep, the same names would resolve to the full
`lib/bayan.cyr` in the stdlib snapshot, and the sidecar would name `bayan`.
Measured on a minimal consumer at 6.6.20: 404,832 B as shipped, against
1,804,072 B (689,960 B with DCE) with `sigil` and `bayan` in the sidecar.

The rules that follow:

- **Never put `bayan` in `[deps] stdlib`.** That is the monolith, and through
  1.2.4 the sidecar copied `[deps] stdlib`, so every consumer linked 641 KB of
  it (chakshu: 861,536 → 571,496 B when 1.2.5 removed it).
- **Keep it optional.** Features resolve from the root manifest only, so a
  consumer never resolves mihi's `[deps.bayan]`. Its lock holds no bayan pin
  and its `lib/` has no bayan file. Measured: with `optional` removed, the same
  consumer's lock gains the bayan commit pin and its `lib/` gains
  `bayan-json.cyr`.
- **Move the tag with the toolchain.** Use the bayan release whose own
  `cyrius` pin is mihi's (1.5.14 for 6.7.9). If none pins it exactly, use the
  tag that cyrius folds into its stdlib (1.11.1 for 6.7.18, also the one
  ai-hwaccel 2.5.5 pins). `cyrius deps` notes when ai-hwaccel's
  optional bayan wants a different tag; mihi's root pin wins, and that is
  fine.

Expected warnings follow from this. mihi's own builds print no `undefined
function` lines. A consumer that does not supply bayan prints the
`bayan_json_v_*` warnings from `lib/ai-hwaccel.cyr` (ten at ai-hwaccel 2.5.5);
DCE removes them. A
consumer must not add the bayan monolith to silence them.

## Windows-only names in the distlib report

`cyrius distlib` compiles the bundle for six targets and reports `O_CLOEXEC`,
`O_NONBLOCK` and `EINTR` as undefined on `x86_64-windows`. `src/io.cyr` uses
them, and the Windows syscall table does not define them. mihi targets Linux and
AGNOS only (Windows is out of scope in [`roadmap.md`](../development/roadmap.md)),
so the warning is expected.
