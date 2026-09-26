*[English version](AUDIT-INTEGRALS.md)*

# Uma tabela de integrais contra o Sucuri

**Fonte.** `en.wikipedia.org/wiki/Lists_of_integrals`, pela API de wikitexto.
118 alegações, extraídas por `integrais.py --baixar`. A tabela de derivadas já
tinha passado por aqui (`AUDITORIA-DERIVADAS.md`); esta é a segunda, e serve
para uma pergunta diferente: **o que o leitor aprendeu na primeira tabela vale
para a segunda, ou só valia para aquela?**

## Uma tabela de integrais prova-se ao contrário

A entrada é

    ∫ f(x) dx = F(x) + C

e o jeito certo de conferi-la não é integrar — é **derivar o lado direito** e
comparar com o integrando. Mais rápido, não depende de o integrador acertar, e
a constante de integração morre na derivada, que é o destino dela.

Para as definidas isso não serve: o lado direito é um número. Ali tenta-se
fechar simbolicamente e, falhando, compara-se numericamente em pontos
sorteados — com o veredito dizendo, no próprio nome, que **isso não é prova**.

## Resultado

| 118 alegações                         |     |                                          |
|---------------------------------------|----:|------------------------------------------|
| provada                               |  31 | derivada do lado direito bate com o integrando |
| provada fora de pontos isolados       |  12 | vale salvo onde a tabela subentende (x ≠ 0) |
| confere numericamente (não é prova)   |   4 | definida que fechou só no avaliador       |
| **lida errado**                       | **0** | o desfecho inaceitável                  |
| recusada (pergunta)                   |  17 | o Sucuri perguntou em vez de adivinhar    |
| não lida                              |  28 | recusa honesta: notação fora do parser    |
| não confirmada (só numericamente)     |  14 | o verificador não fechou; a leitura está de pé |
| não fechada                           |   5 | remete a definição dada na prosa          |
| refutada                              |   7 | leitura boa, igualdade não fecha          |

**Nenhuma entrada lida errado** — que é a coluna que importa, e a que a tabela
de derivadas tinha deixado em 11 antes dos consertos.

Das 28 não lidas, 19 são `\operatorname{...}`; das 7 refutadas,
2 são a forma de operador `\frac{d^n f}{dx^n}` com ordem simbólica, 2 são o
alcance de `\cos ax\,e^{bx}` (abaixo), 2 são antiderivadas com `\lfloor·\rfloor`,
cuja derivada é zero quase em toda parte, e 1 é `∫sec x dx = ln|tan(x/2+π/4)|`,
identidade clássica verdadeira que nem o `simplify` nem a amostragem fecharam —
falha do verificador, não da leitura.

## O que a tabela de integrais cobrou

### 1. `\left|x\right|` — a mesma barra, escrita do jeito que todo mundo escreve

```python
>>> parse_latex(r"\ln|x|")              log(Abs(x))
>>> parse_latex(r"\ln\left|x\right|")   LaTeXParsingError
```

O parser do SymPy lê a barra simples e recusa a barra com `\left`. Como toda
tabela escreve `\left|` (é o que dá o tamanho certo à barra), isso sozinho
alcançava **28 das 118 alegações**.

Corrigido com uma reescrita inofensiva, de LaTeX para LaTeX: `\left|`, `\right|`,
`\vert`, `\lvert` e `\rvert` viram `|`. Não é adivinhação — é a mesma barra.
`\Vert` e `\lVert` ficam de fora, e de propósito: aquelas são **norma**, e quem
trocar uma pela outra troca o significado. Há teste para isso.

### 2. `{a \over b}` — a fração primitiva do TeX

Já tinha aparecido na tabela de derivadas, e lá ficou registrada como pendência
porque valia para poucas entradas. Aqui alcança 8 alegações, e nas derivadas
alcançava outras tantas — juntas, passam a valer o conserto. É
o mesmo tipo de reescrita: `{1 \over x}` vira `\frac{1}{x}`, e o cuidado único
é não confundir `\over` com `\overline`.

Junto com a barra, isto é a camada de **reescritas que não mudam significado**,
que roda no fim da normalização — depois da localização dos sítios ambíguos,
porque reescrever antes deslocaria todas as posições.

### 3. O `e` de Euler é ambiguidade, e era lida por omissão

Este é o achado sério da tabela de integrais.

```
\int e^{ax}\,dx = \frac{1}{a}e^{ax} + C     → refutada
```

Refutação correta de uma leitura errada: o parser lê `e` como um símbolo
qualquer, e para um símbolo `e` a derivada de `e^{ax}` é `a·e^{ax}·ln(e)`, que
não é `a·e^{ax}`. Toda a família exponencial da tabela caía assim — e caía em
silêncio, porque um símbolo chamado `e` é uma leitura perfeitamente bem formada.

E `e` **é** ambíguo: excentricidade, carga elementar, índice. Virou sítio, com
as duas leituras e a convenção de documento correspondente:

```python
doc.e_is_euler(True)      # numa tabela, e^{ax} é Euler
```

Sem a convenção, `\int e^{ax}dx` fica **pendente** e o Sucuri pergunta.

O detector olha só o `e` que é base de potência (`e^`). É onde ele quase sempre
é Euler e onde a leitura errada muda a matemática calada; um `e` solto em outro
lugar seria pergunta demais para achado de menos. Duas armadilhas, as duas com
teste: em `ae^{ax}` há um `a` vezes um `e` — justaposição em LaTeX é produto, e
o primeiro detector deixava passar metade da equação com um símbolo onde a
outra metade tinha o número; e em `\sec` e `v_e^2` o `e` é letra de outro nome.

### 4. `\log_a x` deriva errado, e o objeto parece perfeito

```python
>>> cru = parse_latex(r"\log_a x")
>>> sp.diff(cru, x)
1/x                      # falta o ln(a)
>>> sp.diff(sp.log(x, a), x)
1/(x*log(a))             # o mesmo log, construído pelo SymPy
```

O parser monta um `log` de **dois argumentos por avaliar**, e esse objeto
deriva como se a base fosse `e`. Este é o pior dos silêncios encontrados até
aqui: não há símbolo estranho na saída, não há macro degradada, não há nada
para uma barreira pegar — o objeto parece perfeito e a conta sai falsa.

Corrigido reconstruindo os logs de dois argumentos, o que é identidade exata
(`log_b x = ln x / ln b`) e não escolha de leitura.

### 5. Pergunta que não era pergunta

```
'\arctan(' — application = arctan aplicada ao argumento;
             product     = arctan multiplicando o parêntese
```

Não existe leitura em que `\arctan` multiplique um parêntese. A lista de nomes
que nunca são símbolo do usuário tinha só `sin`, `cos`, `tan`, `exp`, `log`,
`ln` — faltavam as inversas, as hiperbólicas, as recíprocas e `\dfrac`.
Pergunta que não é pergunta gasta a credibilidade das que são.

## Dois silêncios que ficaram só registrados

Os dois vêm do parser do SymPy e nenhuma barreira atual os pega, porque em
ambos o que sai é uma expressão bem formada — só que não é a que foi escrita.

**Um fator inteiro desaparece.**

```python
>>> parse_latex(r"\frac{1}{2} \sqrt \frac{\pi}{a}")
1/2
```

O `\sqrt` sem chaves seguido de `\frac` é sumariamente descartado. Sozinho,
`\sqrt \frac{\pi}{a}` levanta erro; dentro de um produto, some calado. São as
gaussianas da tabela inteira.

**O alcance de uma função sem parênteses.**

```python
>>> parse_latex(r"\cos ax\, e^{bx}")
cos(a*x*exp(b*x))
```

A tabela quer `cos(ax)·e^{bx}`; o parser deu o produto todo de argumento ao
cosseno. E aqui não é só defeito do parser — **é ambiguidade de verdade**, do
mesmo tipo da linha e do ponto: `\sin 2x` é `sin(2x)` ou `sin(2)·x`? A
tipografia não decide, a convenção decide, e convenção é o que este programa
exige que se declare. É o próximo sítio a implementar.

Pegar o primeiro exigiria uma conferência que o Sucuri ainda não faz: **o
parser consumiu a entrada inteira?** É a mesma pergunta que pegaria
`(f+g)' = a` devolvendo `f+g`.

## O que a tabela confirmou da rodada anterior

Os consertos da tabela de derivadas seguraram aqui, e uma entrada os usa todos:

```
\int f'(x)e^{f(x)}\,dx = e^{f(x)} + C
```

A linha com argumento (`f'(x)`) é o defeito que vazava marcador; o `e` é o
desta rodada. A entrada fecha.

## O que continua aberto

- **`\operatorname{arsinh}` e família.** Segue recusada, com a mesma razão da
  rodada anterior: traduzir exige o mecanismo de marcador, não uma reescrita de
  texto. Aqui pesa mais, porque a tabela usa `\sgn` o tempo todo.
- **`\frac{d}{dx}` como operador** continua não sendo sítio do Sucuri.
- **`\begin{cases}`.** Várias entradas da tabela são definições por casos. O
  parser não as lê, e a recusa é honesta, mas uma tabela de integrais séria as
  tem.

## Reproduzir

```bash
python integrais.py --baixar     # rede; regrava integrais.json
python integrais.py              # offline; leva alguns minutos nas definidas
python integrais.py --verboso
```

A contagem das indefinidas está travada em
`tests/test_tabela_de_integrais.py`. As definidas ficam fora da suíte: dependem
de quadratura numérica e levam minutos.
