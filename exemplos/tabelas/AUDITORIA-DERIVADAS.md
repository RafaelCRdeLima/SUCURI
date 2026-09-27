*[English version](AUDIT-DERIVATIVES.md)*

# Uma tabela de derivadas contra o Sucuri

**Fonte.** `en.wikipedia.org/wiki/Differentiation_rules`, via a API de
wikitexto — o LaTeX como o autor escreveu, não o HTML renderizado, que já é
interpretação. 66 alegações, extraídas por `derivadas.py --baixar` e gravadas em
`derivadas.json`. Auditadas por `derivadas.py`.

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

|                             | antes | depois |     |
|-----------------------------|------:|-------:|-----|
| provada                     |    17 | **27** | lida e verificada |
| provada fora de pontos isolados | — |      1 | vale salvo onde a tabela subentende (x ≠ 0) |
| **lida errado**             |    11 |  **2** | o desfecho inaceitável |
| recusada (pergunta)         |     6 |      4 | o Sucuri perguntou em vez de adivinhar |
| não lida                    |     9 |     17 | recusa honesta: notação fora do parser |
| não fechada                 |     3 |     11 | remete a definição dada na prosa |
| refutada                    |    20 |      4 | leitura boa, igualdade não fecha |

A coluna "depois" já inclui o que a **tabela de integrais** cobrou em seguida —
`\left|`, `{a \over b}`, o `e` de Euler e a lista de funções conhecidas. Ver
`AUDITORIA-INTEGRAIS.md`.

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

Este é o achado mais desconfortável: **das 27 entradas provadas, as 20 escritas
com `\frac{d}{dx}` passaram por uma leitura que o Sucuri nunca declarou** (as outras
7 usam linhas). `\frac{d}{dx}\sin x` funciona porque a
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

### Funções que o parser não conhece continuam só recusadas

Das entradas "não lidas", a maioria é uma família só:
`\operatorname{arsinh}`, `\coth`, `\operatorname{sech}` — funções que o SymPy
**tem** (`asinh`, `coth`, `sech`) e que o parser de LaTeX não conhece.

Traduzir não seria adivinhar; `arsinh` é o seno hiperbólico inverso e ponto.
Mas, ao contrário de `\over`, a tradução não é de LaTeX para LaTeX: exige o
mecanismo de marcador, a captura do argumento e o cuidado com `\coth^2 x`, que
é `(\coth x)^2`. Fica para quando houver uso.

### `\arctan(y,x)` é lido como `arctan(y)`

```
\frac{\partial \arctan(y,x)}{\partial y} = \frac{x}{x^2 + y^2}     → refutada
```

A entrada está certa: é o `atan2` de dois argumentos. O parser do SymPy leu só
o primeiro e jogou fora o segundo, sem dizer nada — mais um silêncio dele, e um
que a barreira de macro degradada não pega, porque nenhum símbolo estranho
aparece na saída. Seria preciso conferir a aridade contra o que foi escrito.

### Duas entradas não fecham porque falta o que a página diz em volta

`\frac{dx}{dy} = 1/\frac{dy}{dx}` pede o teorema da função inversa, e
`\frac{d}{dx}W(x)` pede a relação que define a função W. Nenhuma das duas é
legível fora da página, e nenhuma é defeito do leitor.

## As quatro recusas, que estão certas

O Sucuri perguntou em vez de adivinhar em quatro entradas, e as quatro perguntas
são boas:

- `\frac{d(af+bg)}{dx}` e `\frac{d(fg)}{dx}` — `d(` é `d` aplicado ao parêntese,
  ou `d` multiplicando-o?
- `\frac{d\left(\frac{1}{f}\right)}{dx}` — a mesma pergunta para `d\left(`;
- `\frac{d}{dx}\left(x^x\right) = x^x(1+\ln x)` — `x(` é aplicação ou produto?

Nos quatro casos a tipografia não decide. É exatamente o caso de uso.

## Reproduzir

```bash
python derivadas.py --baixar     # rede; regrava derivadas.json
python derivadas.py              # offline; usa o derivadas.json versionado
python derivadas.py --verboso
```

A contagem está travada em `tests/test_tabela_de_derivadas.py`: melhorar é
livre, piorar tem de doer.
