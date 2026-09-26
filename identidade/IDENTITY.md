*[Versão em português](IDENTIDADE.md)*

# SUCURI — visual identity

**SUCURI** — *SymPy Unified Compiler for Unambiguous Rendered Input*.
Converter from LaTeX equations to SymPy code.

The name comes from *Eunectes murinus*, the green anaconda (*sucuri* in Portuguese). The choice solves a
shape problem: the serpentine curve is naturally an S, so the snake does not compete with
the name's initial — it **is** the initial.

---

## Symbol

The mark is an anaconda coiled into the letter S. Three elements define it:

| Element | Where | What it means |
|---|---|---|
| Head with eye | upper end | input: the mathematical notation |
| Oval spots on the body | along the stroke | the species; inherited from the dorsal pattern of *murinus* |
| Square block | lower end | output: the terminal's block cursor, the code |

It reads top to bottom: notation goes in through the head, code comes out through the tail.

Construction: stroke width 10 on a 100 × 100 grid, tile with a corner
radius of 23 %. The tail block is rotated −31° to align with the stroke's
tangent — without it a visible step appears at the end.

## Variants

| File | Use |
|---|---|
| `marca/sucuri-marca-principal.svg` | default; Sucuri green on Mata |
| `marca/sucuri-marca-invertida.svg` | printed documents, light backgrounds |
| `marca/sucuri-marca-ambar.svg` | promotional material, tutorial cover |
| `marca/sucuri-marca-monocromatica.svg` | single color; inherits `currentColor` |
| `marca/sucuri-simbolo.svg` | no tile, transparent background, `currentColor` |
| `marca/sucuri-lockup-horizontal.svg` | site header, slide footer |
| `marca/sucuri-lockup-vertical.svg` | cover, poster, splash screen |
| `marca/folha-de-contato.svg` \| `.png` | quick reference of all variants |

## Palette

| Name | Hex | Role |
|---|---|---|
| Mata | `#14291C` | tile background, dark theme |
| Sucuri | `#8FBE45` | mark on dark background |
| Folha | `#6F9C33` | mark and wordmark on light background |
| Âmbar | `#E3B23C` | warning; assumption made by the parser |
| Areia | `#F1EDDF` | light surface |
| Argila | `#C0442F` | parse error |

The tokens are in `tokens/sucuri-tokens.css`, together with the interface derivatives
(elevation, secondary text, state backgrounds).

Green is identity, not state. The interface's success green (`#E6F0D4` /
`#3D5A15`) is deliberately lighter and desaturated, so that nobody confuses
"it worked" with "it's SUCURI".

## Typography

| Role | Family | Setting |
|---|---|---|
| Wordmark | Inter medium | tracking 0.18em, always in small caps |
| Interface | Inter regular | size 15 px, line height 1.6 |
| LaTeX and code | JetBrains Mono | size 13–14 px, line height 1.75 |

The name is small caps in the wordmark and lowercase in code: `import sucuri`,
`sucuri.parse(...)`.

## Scale and degradation

| Size | What remains |
|---|---|
| ≥ 64 px | everything: spots, eye, head, block |
| 40 px | head and block; spots go |
| 24 px | head and block, thicker stroke; eye goes |
| 16 px | only the S and the opening; stroke at 18 units |

Absolute minimum size: 16 px. Below that, use the wordmark alone.

## Clear space

Free margin around the tile equal to the height of the head — 15 % of the side.
In the horizontal lockup, the distance between tile and wordmark is fixed at 26 % of
the tile's side.

## What not to do

- Do not use the bare mark on a light background in Sucuri green: no contrast.
  On light, use Folha or the inverted variant.
- Do not show spots below 32 px — they turn into one-pixel dirt.
- Do not put Âmbar or Argila in the same frame as the mark's green.
- Do not distort the tile's proportions or rotate the mark.
- Do not recolor the body: the anaconda is green, amber or mata, and nothing else.
- Do not add outline, shadow or gradient to the symbol.

## App icons

`launcher/` holds the PNGs from 48 to 1024 px, each with its size's detail
degradation already applied — they are not resamplings of a single file.

- `favicon.ico` — multi-resolution: 16, 24, 32, 48, 64
- `favicon.svg` — simplified vector version, no spots or eye
- `sucuri-180.png` — Apple touch icon
- `sucuri-192.png`, `sucuri-512.png` — PWA manifest
- `sucuri-maskable-512.png` — Android adaptive, mark at 58 % inside the safe zone

```html
<link rel="icon" href="/launcher/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/launcher/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/launcher/sucuri-180.png">
```

## Mockup

`mockup/mockup.html` is the reference interface: a self-contained, responsive page
that applies every token. Opens directly in the browser. Shows the full flow —
LaTeX input, recognized tree, parse states, SymPy output.

## Structure

```
sucuri-identidade/
├── IDENTIDADE.md
├── marca/          symbol, variants, lockups, contact sheet
├── launcher/       favicon, PNGs from 48 to 1024, maskable
├── tokens/         sucuri-tokens.css
└── mockup/         mockup.html
```
