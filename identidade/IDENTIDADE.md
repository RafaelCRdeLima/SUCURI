*[English version](IDENTITY.md)*

# SUCURI — identidade visual

**SUCURI** — *SymPy Unified Compiler for Unambiguous Rendered Input*.
Conversor de equações em LaTeX para código SymPy.

O nome vem da *Eunectes murinus*, a sucuri-verde. A escolha resolve um problema
de forma: a curva serpentina é naturalmente um S, então a cobra não concorre com
a inicial do nome — ela **é** a inicial.

---

## Símbolo

A marca é uma sucuri enrolada formando a letra S. Três elementos a definem:

| Elemento | Onde | O que significa |
|---|---|---|
| Cabeça com olho | terminal superior | entrada: a notação matemática |
| Manchas ovais no corpo | ao longo do traço | a espécie; herdadas do padrão dorsal da *murinus* |
| Bloco quadrado | terminal inferior | saída: o cursor de bloco do terminal, o código |

A leitura é de cima para baixo: entra notação pela cabeça, sai código pela cauda.

Construção: traço de espessura 10 sobre grade de 100 × 100, ladrilho com raio de
canto de 23 %. O bloco da cauda é girado −31° para alinhar com a tangente do
traço — sem isso aparece um degrau visível no terminal.

## Variantes

| Arquivo | Uso |
|---|---|
| `marca/sucuri-marca-principal.svg` | padrão; verde Sucuri sobre Mata |
| `marca/sucuri-marca-invertida.svg` | documentos impressos, fundos claros |
| `marca/sucuri-marca-ambar.svg` | material de divulgação, capa de apostila |
| `marca/sucuri-marca-monocromatica.svg` | uma cor só; herda `currentColor` |
| `marca/sucuri-simbolo.svg` | sem ladrilho, fundo transparente, `currentColor` |
| `marca/sucuri-lockup-horizontal.svg` | cabeçalho de site, rodapé de slide |
| `marca/sucuri-lockup-vertical.svg` | capa, pôster, splash screen |
| `marca/folha-de-contato.svg` \| `.png` | referência rápida de todas as variantes |

## Paleta

| Nome | Hex | Função |
|---|---|---|
| Mata | `#14291C` | fundo do ladrilho, tema escuro |
| Sucuri | `#8FBE45` | marca sobre fundo escuro |
| Folha | `#6F9C33` | marca e wordmark sobre fundo claro |
| Âmbar | `#E3B23C` | aviso; hipótese assumida pelo parser |
| Areia | `#F1EDDF` | superfície clara |
| Argila | `#C0442F` | erro de parse |

Os tokens estão em `tokens/sucuri-tokens.css`, com as derivadas de interface
(elevação, texto secundário, fundos de estado).

Verde é identidade, não estado. O verde de sucesso da interface (`#E6F0D4` /
`#3D5A15`) é deliberadamente mais claro e dessaturado, para que ninguém confunda
"deu certo" com "é o SUCURI".

## Tipografia

| Papel | Família | Ajuste |
|---|---|---|
| Wordmark | Inter medium | tracking 0.18em, sempre em versalete |
| Interface | Inter regular | corpo 15 px, entrelinha 1.6 |
| LaTeX e código | JetBrains Mono | corpo 13–14 px, entrelinha 1.75 |

O nome é versalete no wordmark e minúsculo no código: `import sucuri`,
`sucuri.parse(...)`.

## Escala e degradação

| Tamanho | O que permanece |
|---|---|
| ≥ 64 px | tudo: manchas, olho, cabeça, bloco |
| 40 px | cabeça e bloco; manchas saem |
| 24 px | cabeça e bloco, traço engrossado; olho sai |
| 16 px | só o S e a abertura; traço em 18 unidades |

Tamanho mínimo absoluto: 16 px. Abaixo disso use o wordmark sozinho.

## Área de respiro

Margem livre ao redor do ladrilho igual à altura da cabeça — 15 % do lado.
No lockup horizontal, a distância entre ladrilho e wordmark é fixa em 26 % do
lado do ladrilho.

## O que não fazer

- Não usar a marca solta sobre fundo claro no verde Sucuri: sem contraste.
  Sobre claro, use Folha ou a variante invertida.
- Não mostrar manchas abaixo de 32 px — viram sujeira de um pixel.
- Não colocar Âmbar ou Argila no mesmo enquadramento que o verde da marca.
- Não distorcer a proporção do ladrilho nem girar a marca.
- Não recolorir o corpo: a sucuri é verde, âmbar ou mata, e nada mais.
- Não adicionar contorno, sombra ou gradiente ao símbolo.

## Ícones de aplicativo

`launcher/` traz os PNGs de 48 a 1024 px, já com a degradação de detalhe
aplicada em cada tamanho — não são reamostragens de um único arquivo.

- `favicon.ico` — multirresolução: 16, 24, 32, 48, 64
- `favicon.svg` — versão vetorial simplificada, sem manchas nem olho
- `sucuri-180.png` — Apple touch icon
- `sucuri-192.png`, `sucuri-512.png` — manifesto PWA
- `sucuri-maskable-512.png` — Android adaptativo, marca a 58 % dentro da zona segura

```html
<link rel="icon" href="/launcher/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/launcher/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/launcher/sucuri-180.png">
```

## Mockup

`mockup/mockup.html` é a interface de referência: página autocontida, responsiva,
que aplica todos os tokens. Abre direto no navegador. Mostra o fluxo completo —
entrada em LaTeX, árvore reconhecida, estados de parse, saída em SymPy.

## Estrutura

```
sucuri-identidade/
├── IDENTIDADE.md
├── marca/          símbolo, variantes, lockups, folha de contato
├── launcher/       favicon, PNGs de 48 a 1024, maskable
├── tokens/         sucuri-tokens.css
└── mockup/         mockup.html
```
