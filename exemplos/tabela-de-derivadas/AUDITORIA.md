# Uma tabela de derivadas contra o Sucuri

**Fonte.** `en.wikipedia.org/wiki/Differentiation_rules`, via a API de
wikitexto — o LaTeX como o autor escreveu, não o HTML renderizado, que já é
interpretação. 66 alegações, extraídas por `baixar.py` e gravadas em
`tabela.json`. Auditadas por `auditoria.py`.

A tabela é externa de propósito. Tabela escrita por quem escreve o leitor
testa o leitor contra si mesmo; foi escrita por outra gente, para outro fim, e
por isso usa notação que ninguém aqui teria lembrado de prever.

## O que se pergunta de cada entrada

Duas perguntas, nesta ordem, e a ordem importa:

1. o Sucuri **lê** a entrada? — é o que o Sucuri promete;
2. a entrada é **verdadeira**? — é o que o SymPy calcula.

E um terceiro desfecho, o único inaceitável: o Sucuri lê, lê **errado**, e não
avisa. É contra ele que o programa existe.

## Resultado

|                        | antes | depois |     |
|------------------------|------:|-------:|-----|
| provada                |    17 | **23** | lida e verificada |
| **lida errado**        |    11 |  **2** | o desfecho inaceitável |
| recusada (pergunta)    |     6 |      6 | o Sucuri perguntou em vez de adivinhar |
| não lida               |     9 |     22 | recusa honesta: notação fora do parser |
| não fechada            |     3 |     11 | remete a definição dada na prosa |
| refutada               |    20 |      2 | leitura boa, igualdade não fecha |

O crescimento de "não lida" é a melhora principal, não uma piora: entram ali as
entradas que antes viravam lixo em silêncio e hoje param com erro. A coluna que
tinha de encolher — "lida errado" — encolheu de 11 para 2.

## Os três defeitos que a tabela encontrou

### 1. O marcador interno vazava na saída — `f'(x)`

`f'(x)` saía como `Z_{0}(x)`. O marcador que o Sucuri insere no lugar de um
sítio ambíguo é um **símbolo**; escrito antes de um parêntese, ` Z_{0} (x)`, o
parser o lê como **função aplicada**, e a reposição, que procurava o símbolo,
não casava. O marcador seguia para a saída, e a conta prosseguia com ele.

`f'(x)` é a notação mais comum de toda a tabela. A suíte não a tinha: os testes
usavam `y''` e `\varphi''`, sempre sem argumento.

Corrigido: a linha engole o argumento, e a leitura distingue os dois casos que
a notação junta —

    f'(x)     derivada de f, avaliada em x        → Derivative(f(x), x)
    f'(u)     derivada de f, avaliada em u        → Subs(Derivative(f(z),z), z, u)

que **não** são a mesma coisa, e escrevê-las como se fossem seria o erro
silencioso de sempre. Com isso a regra da cadeia da tabela fecha.

### 2. A linha sobre um grupo levava a equação inteira embora — `(f+g)'`

A linha de `(f+g)'` não é da letra `g`: é do parêntese todo. O detector só
conhecia linha sobre símbolo, então não via o sítio — e o que acontece depois é
pior do que não ver:

```python
>>> parse_latex("(f + g)' = a")
f + g
```

O parser do SymPy engole a linha, o sinal de igual e o lado direito inteiro, e
devolve o pedaço que sobrou sem dizer nada. Metade da equação desaparece.

Corrigido: linha sobre grupo é sítio, com o interior lido recursivamente sob as
mesmas convenções. A regra do quociente da tabela, `\left(\frac f g\right)'`,
fecha.

### 3. Macro que o parser não entende vira símbolo, calado

O parser de LaTeX do SymPy não recusa o que não conhece — ele degrada:

```python
>>> parse_latex(r"\coth x")                      coth*x
>>> parse_latex(r"{1 \over x}")                  1*(over*x)
>>> parse_latex(r"\operatorname{arccsc} x")      operatorname*(x*(a*(r*(c*(c*(c*s))))))
```

O nome da função vira um símbolo com o nome da macro, ou o produto das letras
do nome. A conta segue, o resultado é lixo, e nada na saída indica isso. Das 20 entradas
que a auditoria dava como "refutadas", 18 eram isto: nunca tinham sido lidas.

Corrigido com uma barreira geral: **macro que reaparece na saída como símbolo
do mesmo nome foi degradada** — exceto o alfabeto grego e um punhado de letras
especiais, que viram símbolo por direito. `NotacaoNaoReconhecida`, e para.

A mesma barreira pega o defeito 1 pelo outro lado: marcador do Sucuri na saída
também é erro, e diz de quem é a culpa.

## O que continua aberto

### A forma de operador, `\frac{d}{dx}`, não é sítio do Sucuri

Este é o achado mais desconfortável: **as 23 entradas provadas passaram por uma
leitura que o Sucuri nunca declarou.** `\frac{d}{dx}\sin x` funciona porque a
gramática do SymPy tem uma regra para essa forma — não porque alguém aqui a
tenha reconhecido. O detector de Leibniz exige função no numerador
(`\frac{df}{dx}`) e não vê `\frac{d}{dx}`.

Onde a gramática do SymPy não alcança, o silêncio volta:

```python
>>> parse_latex(r"\frac{d^n}{dx^n}[f(x)g(x)]")
(d**n/(dx**n))*(f(x)*g(x))
```

— a ordem simbólica `n` derrota a regra, e a derivada vira fração literal de
símbolos multiplicando o resto. São as duas únicas entradas que ainda saem
**lidas errado**.

Pela doutrina do projeto, uma leitura que ninguém declarou não devia passar,
mesmo estando certa. O conserto é um detector para a forma de operador, com as
mesmas duas leituras das outras.

### Notação que o parser não conhece podia ser traduzida, não só recusada

As 22 entradas "não lidas" têm duas causas, ambas notação corrente:

- `{a \over b}` — primitiva do TeX, tem exatamente um significado;
- `\operatorname{arsinh}`, `\coth`, `\operatorname{sech}` — funções que o SymPy
  **tem** (`asinh`, `coth`, `sech`), mas que o parser de LaTeX não conhece.

Traduzir não seria adivinhar: `\over` é fração, `arsinh` é o seno hiperbólico
inverso. Seria conhecimento declarado, do mesmo tipo que `\varphi` → `varphi`.
Custo: uma tabela de nomes e a captura do argumento (com o cuidado de
`\coth^2 x`, que é `(\coth x)^2`).

### `e` é lido como símbolo, não como número de Euler

```
\frac{d}{dx}\left(e^{ax}\right) = ae^{ax}     → refutada
```

Refutação correta da leitura: para um símbolo `e`, a derivada é
`a·e^{ax}·ln(e)`, que não é `a·e^{ax}`. Mas a leitura é que está errada — o
`e` da tabela é o de Euler. É ambiguidade genuína (`e` é excentricidade, carga,
índice) e devia ser sítio com duas leituras, como a linha e o ponto.

## As seis recusas, que estão certas

O Sucuri perguntou em vez de adivinhar em seis entradas, e as seis perguntas
são boas:

- `\frac{d(fg)}{dx}` — `d(` é `d` aplicado a `fg`, ou `d` multiplicando?
- `\frac{d}{dx}(x^x)` — `x(` é aplicação ou produto?
- `\frac{\partial \arctan(y,x)}{\partial y}` — `\arctan(` aplicado, ou produto?

Nos três casos a tipografia não decide. É exatamente o caso de uso.

## Reproduzir

```bash
python baixar.py       # rede; regrava tabela.json
python auditoria.py    # offline; usa o tabela.json versionado
python auditoria.py --verboso
```

A contagem está travada em `tests/test_tabela_de_derivadas.py`: melhorar é
livre, piorar tem de doer.
