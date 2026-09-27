*[English version](README.md)*

# A versão online

Esta pasta é o Sucuri inteiro rodando **dentro do navegador**. Não há servidor:
o Python e o SymPy vêm compilados para WebAssembly pelo Pyodide, e o pacote
`sucuri` é o mesmo — vai num zip que o navegador desempacota.

O que isso quer dizer na prática:

- **nada do que o usuário escreve sai da máquina dele.** Não há para onde ir;
- a primeira visita baixa ~15 MB (Python + SymPy, do CDN do Pyodide) e leva
  alguns segundos; depois fica em cache do navegador;
- o que se publica aqui são ~1,7 MB: a interface, o KaTeX, o motor e a roda do ANTLR.

Duas páginas carregam o motor: `index.html`, uma equação de cada vez, e
`caderno.html`, o caderno. As duas são geradas de `sucuri/interface/estatico/` por
`construir.py`, que injeta a tela de carregamento — gerar em vez de copiar à mão é o
que impede as duas versões de divergirem sem ninguém perceber, e há teste que refaz a
geração e compara. As páginas de texto — `manual.html`, `manual-en.html`,
`apostila.html` e `tutorial.html` — não carregam motor e são copiadas como estão.

## Publicar no Cloudflare Pages

**Direto, só o executável** — corresponde a publicar o programa, não o
código-fonte:

1. Workers & Pages → **Create** → **Pages** → **Upload assets**
2. nome do projeto: `sucuri` — vira `sucuri.pages.dev`
3. arraste a pasta `web/` inteira
4. **Deploy**

**Ligado ao GitHub** (publica sozinho a cada push):

1. Workers & Pages → **Create** → **Pages** → **Connect to Git**
2. repositório `RafaelCRdeLima/SUCURI`, branch `main`
3. Framework preset: **None**
4. Build command: deixe **vazio**
5. Build output directory: **`web`**

O campo de build fica vazio porque a pasta já vai pronta no repositório. Quem
muda o motor roda `python web/construir.py` antes de commitar — e `tests/test_web.py`
falha se a pasta publicada ficar para trás: confere que `sucuri-motor.zip` tem
exatamente os `.py` do pacote, byte a byte; que `sucuri.css`, `sucuri.js`, `tokens.css`
e `favicon.svg` são idênticos aos da interface local e que o KaTeX tem os mesmos
arquivos; e que regerar `index.html` e `caderno.html` não muda nada (além de conferir
que essas páginas e o `motor.js` só pedem arquivos que existem, e que a roda do ANTLR
está lá). Os demais arquivos copiados e as páginas de texto não são comparados.

## Publicar como Worker da Cloudflare

Além do Pages, o `wrangler.jsonc` na raiz do repositório publica a mesma pasta como
Worker de ativos estáticos (`assets.directory` é `./web`; não há código de Worker):

```bash
npx wrangler deploy
```

## Reconstruir

```bash
python web/construir.py
```

Gera `index.html` e `caderno.html`, copia as páginas de texto, `sucuri.css`,
`sucuri.js`, `sitios.js`, `idioma.js`, `caderno.css`, `caderno.js`, `manual.css`,
`tokens.css`, `favicon.svg` e o KaTeX da interface local,
empacota o pacote Python em `sucuri-motor.zip` e baixa a roda do ANTLR se
faltar. Não escreve código nenhum, de propósito: código copiado à mão diverge.

## O que muda em relação à versão de mesa

| | mesa | navegador |
|---|---|---|
| motor | Python local | Pyodide (WebAssembly) |
| SymPy | 1.12 (fixado) | 1.13.3 (o que o Pyodide traz) |
| transporte | HTTP | postMessage para um Web Worker |
| prazo do `resolver` | subprocesso que se mata | o worker, que a página mata |
| módulo `korvin` | disponível | indisponível, e fora da interface |

A suíte passa nas duas versões do SymPy, e os silêncios do parser de LaTeX que
as auditorias documentam são idênticos nas duas — foram conferidos.

O `korvin` é outro programa e não vai junto: online a interface não o mostra
(o `sucuri.js` filtra os módulos indisponíveis), e a API `/api/modulos` continua
informando que ele está indisponível, com o motivo. É a mesma regra de sempre — não
oferecer o que quebra ao ser usado.
