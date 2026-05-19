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

Pre-1.0 scaffold (0.1.0). Module shape pinned (`types` / `cpu` / `mem`
/ `kernel` / `host`); function signatures stubbed; bodies return 0. Not
yet usable.

## Build

```sh
cyrius deps                                          # resolve stdlib
cyrius build programs/smoke.cyr build/mihi-smoke    # smoke binary
./build/mihi-smoke                                   # prints "mihi smoke ok"
cyrius test                                          # run tests/*.tcyr
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
