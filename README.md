# SUCURI

*SymPy Unified Compiler for Unambiguous Rendered Input.*

Um ambiente simbólico em que a equação escrita pelo usuário **é** um objeto
manipulável — e em que nenhuma ambiguidade é adivinhada.

## O problema que ele existe para resolver

LaTeX é tipografia, não semântica. Entregar LaTeX a um parser produz erro
silencioso. Medido no SymPy, com equações reais:

| escrito | entendido |
|---|---|
| `\varphi'' + 3\varphi\varphi' + \varphi^3` | `\varphi^3 + (\varphi + 3\varphi\varphi)` |
| `\frac{d^2 y}{dx^2}` | `d²·y / dx²`, símbolos `d` e `dx` |
| `E^2 - f(m^2 + \ldots)` | `f` **aplicada**, não multiplicando |
| `y'' = r y` | `y''` como **símbolo**, não derivada |

Nenhum desses levanta exceção. O parser devolve expressão válida e errada.

A primeira linha é a equação de Riccati do caso 2 de Kovacic. A leitura errada
dela já custou um teorema falso a um projeto real.

## O princípio

> **Ambiguidade não se adivinha: anota-se.**

O Sucuri varre a entrada, **localiza** os sítios ambíguos, e **recusa-se a
produzir uma expressão** enquanto algum estiver sem anotação. Resolvido uma vez
— por declaração do documento ou por escolha do usuário — o nó **guarda** a
decisão, e a ambiguidade não volta.

É o mesmo princípio da camada de proveniência do KORVIN, aplicado à entrada em
vez do critério: nada conclui a partir do que não foi estabelecido.

## As três camadas

```
    vista (LaTeX / MathML)
            ↕
    árvore semântica  ←— a verdade; aqui moram as anotações
            ↕
    SymPy (motor)  +  módulos de domínio (KORVIN, ODEROM, ...)
```

A vista é descartável; a árvore, não. Editar a vista é editar a árvore.

## Os três estados de uma leitura

A identidade visual reserva o âmbar para *ambiguidade resolvida por inferência*,
e isso é um estado próprio no motor:

| Estado | Como | Cor |
|---|---|---|
| **explícita** | anotação feita para aquele sítio | verde |
| **inferida** | convenção do documento aplicada ali | **âmbar** |
| **pendente** | sem leitura definida | bloqueia |

A distinção não é cosmética. Uma convenção geral — "linha é derivada" — pode
acertar nove sítios e errar o décimo, e quem a declarou não olhou cada um. O
âmbar diz: funciona, mas ninguém conferiu este caso.

## Identidade visual

Em `identidade/`: marca e variantes, ícones de 48 a 1024 px, tokens em CSS e o
mockup de referência. Ver `identidade/IDENTIDADE.md`.

A marca é a sucuri enrolada formando a letra S — entra notação pela cabeça, sai
código pelo bloco da cauda.

## Estado

Motor em construção. Ver `sucuri/` e a suíte em `tests/`.
