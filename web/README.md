*[Versão em português](LEIAME.md)*

# The online version

This folder is the whole of Sucuri running **inside the browser**. There is no server:
Python and SymPy come compiled to WebAssembly by Pyodide, and the `sucuri`
package is the same one — it ships in a zip that the browser unpacks.

What this means in practice:

- **nothing the user writes leaves their machine.** There is nowhere for it to go;
- the first visit downloads ~15 MB (Python + SymPy, from the Pyodide CDN) and takes
  a few seconds; after that it stays in the browser cache;
- what gets published here is ~1.7 MB: the interface, KaTeX, the engine and the ANTLR wheel.

Two pages load the engine: `index.html`, one equation at a time, and `caderno.html`,
the notebook. Both are generated from `sucuri/interface/estatico/` by
`construir.py`, which injects the loading screen — generating instead of copying by hand
is what keeps the two versions from drifting apart unnoticed, and there is a test that
redoes the generation and compares. The text pages — `manual.html`, `manual-en.html`,
`apostila.html` and `tutorial.html` — load no engine and are copied as they are.

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
changes the engine runs `python web/construir.py` before committing — and `tests/test_web.py`
fails if the published folder falls behind: it checks that `sucuri-motor.zip` holds exactly
the package's `.py` files, byte for byte; that `sucuri.css`, `sucuri.js`, `tokens.css` and
`favicon.svg` are identical to the local interface's and that KaTeX has the same files; and
that regenerating `index.html` and `caderno.html` changes nothing (besides checking that
those pages and `motor.js` only ask for files that exist, and that the ANTLR wheel is there).
The other copied files and the text pages are not compared.

## Publishing as a Cloudflare Worker

Besides Pages, `wrangler.jsonc` at the repository root publishes the same folder as a
Worker with static assets (`assets.directory` is `./web`; there is no Worker code):

```bash
npx wrangler deploy
```

## Rebuilding

```bash
python web/construir.py
```

Generates `index.html` and `caderno.html`, copies the text pages, `sucuri.css`,
`sucuri.js`, `sitios.js`, `idioma.js`, `caderno.css`, `caderno.js`, `manual.css`,
`tokens.css`, `favicon.svg` and KaTeX from the local interface,
packs the Python package into `sucuri-motor.zip` and downloads the ANTLR wheel if
missing. It writes no code at all, on purpose: hand-copied code drifts.

## What changes compared to the desktop version

| | desktop | browser |
|---|---|---|
| engine | local Python | Pyodide (WebAssembly) |
| SymPy | 1.12 (pinned) | 1.13.3 (whatever Pyodide ships) |
| transport | HTTP | postMessage to a Web Worker |
| `solve` time limit | a subprocess that gets killed | the worker, which the page kills |
| `korvin` module | available | unavailable, and left out of the interface |

The suite passes on both SymPy versions, and the LaTeX parser silences that
the audits document are identical in both — this was checked.

`korvin` is another program and does not come along: online the interface does not show it
(`sucuri.js` filters out unavailable modules), and the `/api/modulos` API still reports it as
unavailable, with the reason. Same rule as always — don't offer something that breaks when
used.
