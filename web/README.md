*[Versão em português](LEIAME.md)*

# The online version

This folder is the whole of Sucuri running **inside the browser**. There is no server:
Python and SymPy come compiled to WebAssembly by Pyodide, and the `sucuri`
package is the same one — it ships in a zip that the browser unpacks.

What this means in practice:

- **nothing the user writes leaves their machine.** There is nowhere for it to go;
- the first visit downloads ~15 MB (Python + SymPy, from the Pyodide CDN) and takes
  a few seconds; after that it stays in the browser cache;
- what gets published here is ~750 kB: the interface, KaTeX and the engine.

There are two pages: `index.html`, one equation at a time, and `caderno.html`, the
notebook. Both are generated from `sucuri/interface/estatico/` by
`construir.py` — generating instead of copying by hand is what keeps the two versions
from drifting apart unnoticed, and there is a test that redoes the generation and compares.

## Publishing on Cloudflare Pages

**Direct, executable only** — amounts to publishing the program, not the
source code:

1. Workers & Pages → **Create** → **Pages** → **Upload assets**
2. project name: `sucuri` — becomes `sucuri.pages.dev`
3. drag the whole `web/` folder
4. **Deploy**

**Connected to GitHub** (publishes by itself on every push):

1. Workers & Pages → **Create** → **Pages** → **Connect to Git**
2. repository `RafaelCRdeLima/SUCURI`, branch `main`
3. Framework preset: **None**
4. Build command: leave **empty**
5. Build output directory: **`web`**

The build field stays empty because the folder is already committed ready to serve. Whoever
changes the engine runs `python web/construir.py` before committing — and there is a test that
fails if what is published does not match the package.

## Rebuilding

```bash
python web/construir.py
```

Copies `sucuri.css`, `sucuri.js`, `tokens.css` and KaTeX from the local interface,
packs the Python package into `sucuri-motor.zip` and downloads the ANTLR wheel if
missing. It writes no code at all, on purpose: hand-copied code drifts.

## What changes compared to the desktop version

| | desktop | browser |
|---|---|---|
| engine | local Python | Pyodide (WebAssembly) |
| SymPy | 1.12 (pinned) | 1.13.3 (whatever Pyodide ships) |
| transport | HTTP | postMessage to a Web Worker |
| `solve` time limit | a subprocess that gets killed | the worker, which the page kills |
| `korvin` module | available | unavailable, and announced as such |

The suite passes on both SymPy versions, and the LaTeX parser silences that
the audits document are identical in both — this was checked.

`korvin` is another program and does not come along: online it shows up in the list as
unavailable, with the reason. Same rule as always — say what you don't have
instead of offering something that breaks when used.
