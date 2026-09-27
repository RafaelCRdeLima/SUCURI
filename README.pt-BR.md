# SUCURI

*SymPy Unified Compiler for Unambiguous Rendered Input.*

Um ambiente simbólico em que a equação escrita pelo usuário **é** um objeto
manipulável — e em que nenhuma ambiguidade é adivinhada.

*[Read in English](README.md)*

> **Dois idiomas.** A interface tem um botão PT/EN no cabeçalho (ou abra
> `caderno.html?lang=en`), e as mensagens do motor seguem a escolha. Os
> comandos têm nomes em inglês que valem nos dois idiomas — `g = metric(…)`,
> `\mu, \nu = indices`, `prove(eq3, eq1)`, `solve(eq1)`, `in_chart(eq2)`.
> O manual é `manual.html` em português e `manual-en.html` em inglês; a
> apostila é `apostila.html` em português e `tutorial.html` em inglês.

## O problema que ele existe para resolver

LaTeX é tipografia, não semântica. Entregar LaTeX a um parser produz erro
silencioso. Medido no SymPy, com equações reais:

| escrito | entendido |
|---|---|
| `\varphi'' + 3\varphi\varphi' + \varphi^3` | `\varphi^3 + (\varphi + 3\varphi\varphi)` |
| `\frac{d^2 y}{dx^2}` | `d²·y / dx²`, símbolos `d` e `dx` |
| `E^2 - f(m^2 + \ldots)` | `f` **aplicada**, não multiplicando |
| `y'' = r y` | `y''` como **símbolo**, não derivada |
| `\dot{x}` | **`Symbol('dot') × x`** — o ponto virou multiplicação |

Nenhum desses levanta exceção. O parser devolve expressão válida e errada.

A última é a mais grave para o domínio: toda a mecânica hamiltoniana se escreve
com pontos de Newton, e o parser os transforma em produto por um símbolo
chamado "dot".

A primeira linha é a equação de Riccati do caso 2 de Kovacic. A leitura errada
dela já custou um teorema falso a um projeto real.

## O princípio

> **Ambiguidade não se adivinha: anota-se.**

O Sucuri varre a entrada, **localiza** os sítios ambíguos, e **recusa-se a
produzir uma expressão** enquanto algum estiver sem anotação. Resolvido uma vez
— por declaração do documento ou por escolha do usuário — o nó **guarda** a
decisão, e a ambiguidade não volta.

É o mesmo princípio da camada de proveniência do KORVIN, aplicado à entrada em
vez do critério: nada conclui a partir do que não foi estabelecido. (O KORVIN é
um programa à parte, de critérios para equações diferenciais; não está no PyPI
e não é dependência do Sucuri — o adaptador `sucuri/modules/korvin.py` só se
ativa se ele estiver instalado.)

## As três camadas

```
    vista (LaTeX / MathML)
            ↕
    árvore semântica  ←— a verdade; aqui moram as anotações
            ↕
    SymPy (motor)  +  módulos de domínio (resolver, KORVIN, ...)
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

## As tabelas

`exemplos/tabelas/` põe o leitor contra tabelas reais, baixadas da Wikipédia —
notação escrita por outra gente, para outro fim, que é o único teste honesto de
um leitor de notação.

```bash
python exemplos/tabelas/derivadas.py
python exemplos/tabelas/integrais.py
```

Os dois scripts imprimem o resumo em português.

Uma tabela de derivadas prova-se derivando; uma de integrais prova-se **ao
contrário**, derivando o lado direito e comparando com o integrando — a
constante de integração morre na derivada, que é o destino dela.

Entre as duas, seis erros silenciosos, dois do Sucuri e quatro do parser de
LaTeX do SymPy, que não recusa o que não entende — ele degrada:

```python
>>> parse_latex("(f + g)' = a")          f + g          # some com a equação
>>> parse_latex(r"\coth x")               coth*x         # o nome vira símbolo
>>> parse_latex(r"\frac{1}{2}\sqrt\frac{\pi}{a}")   1/2   # some com o fator
>>> sp.diff(parse_latex(r"\log_a x"), x)  1/x            # falta o ln(a)
```

Ver `exemplos/tabelas/AUDITORIA-DERIVADAS.md` e `AUDITORIA-INTEGRAIS.md`.

## Declarar dissolve a dúvida

```
u = u(t,x)
\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}
```

Nenhuma pergunta, nenhum âmbar. E não porque alguém escolheu uma leitura: se
`u` é função de `x` e `t`, então `\frac{\partial u}{\partial t}` **não pode**
ser "fração literal dos símbolos ∂, u e ∂t" — não há símbolo `u` para
multiplicar. O sítio para de ser pergunta porque parou de ter duas respostas.

É mais forte do que uma convenção, e por isso o sítio fica verde e não âmbar: o
motivo é uma declaração, não uma regra aplicada sem olhar. A leitura diz de
onde veio — *u foi declarada função de x, t*.

Parêntese, como em livro: *seja u = u(t,x)* é como se declara em prosa. Escrito
com o mesmo nome dos dois lados é tautologia — ninguém escreve isso como
equação —, e é essa repetição que distingue declaração de matemática: `u(t,x)`
sozinho continua sendo uma expressão, e engoli-la seria decidir por quem
escreveu. O colchete fica reservado a n-tupla.

Vale na célula (daqui para baixo) ou no campo **Funções** (documento inteiro).

## Mais de uma variável independente

Para a **linha** não: `f'` com duas variáveis não diria em relação a qual, e é
justamente essa ambiguidade que o programa recusa. Uma variável independente
por documento não é limitação — é o que a notação da linha comporta.

Para a **derivada parcial**, sim, e sem declarar nada: cada sítio traz a sua
variável escrita.

```python
from sucuri.document import Document
doc = Document()
doc.read(r"\partial_t u = k \partial_x u").to_sympy()
# Eq(Derivative(u(t, x), t), k*Derivative(u(t, x), x))
doc.read(r"\frac{\partial u}{\partial t} = k \frac{\partial^2 u}{\partial x^2}").to_sympy()
# Eq(Derivative(u(t, x), t), k*Derivative(u(t, x), (x, 2)))
```

`read` devolve uma `Expression`; `.to_sympy()` dá o objeto do SymPy.

O `u` é **um só**, função das duas. Antes cada sítio promovia o símbolo à sua
própria função e o mesmo `u` saía como `u(t)` de um lado e `u(x)` do outro —
duas funções com o mesmo nome na mesma equação, em silêncio.

## Quando a notação e a declaração se contradizem

Escrever `∂` **declara que existem outras variáveis** — é isso que distingue ∂
de d. Se a função foi declarada de uma variável só, as duas afirmações estão em
desacordo, e nenhuma está errada sozinha: ou a declaração está incompleta, ou o
∂ era d.

```
u = u(x)
\frac{\partial u}{\partial x} = A u
   →  d/dx u(x) = A u(x)         a leitura está certa
   →  nota: u foi declarada função de x só, e para função de uma variável
      ∂u/∂x é du/dx — o mesmo objeto.
```

Não bloqueia, porque não é erro. Mas ficar calado faz quem escreveu `∂/∂x` ver
`d/dx` e concluir que o programa errou.

## Notação tensorial

```
\mu, \nu, \lambda = índices

g_{\mu\nu} A^\mu A^\nu      →  g(-L₀,-L₁)·A(L₀)·A(L₁)   todos contraídos
\Gamma^\lambda_{\mu\nu}     →  índices livres: λ, -μ, -ν
A^\mu B_\mu + C^\nu        →  os termos da soma têm índices livres diferentes
```

O tipo é declarável na notação do Schutz — `(M, N)` recebe M 1-formas e N
vetores, o que em índices dá M em cima e N embaixo:

```
g = tensor(0,2)     g_{\mu\nu\lambda}  →  'g' foi declarado do tipo (0,2),
                                          que tem 2 índices, e aqui aparece com 3
                    g^{\mu\nu}         →  nota: levantar índice exige a métrica,
                                          e o Sucuri não a aplica sozinho
```

A nota some quando alguém diz **qual** é a métrica — e aí o índice desce de
fato (abaixo).

Sem isso o posto vem do uso — e vem tarde, na segunda linha em vez da primeira.

Quem decide que `\mu` é índice, e não expoente, é a **declaração** — não há
potência possível com um índice no expoente. É a mesma mecânica de
`u = u(t,x)`: declarar dissolve a dúvida em vez de escolher entre as leituras.

A contração é do SymPy (`sympy.tensor.tensor`), e vem de graça junto com a
consistência: somar termos de valências diferentes levanta erro. É erro de
relatividade, não de digitação, e a olho ninguém vê.

Dois cuidados no caminho. `subs` **não** serve para trocar um símbolo por um
tensor: devolve um `Mul` comum, os índices repetidos ficam parados e a
expressão sai errada sem reclamar — a árvore é reconstruída multiplicando de
verdade. E a valência aparece na tela, porque é a primeira coisa que se confere
num tensor.

### Baixar e levantar índice

```
\mu, \nu = índices
g = métrica              →  g é a métrica do espaço — do tipo (0,2)
A = tensor(1,0)
g_{\mu\nu} A^{\nu}         →  g(-μ,-L₀)·A(L₀)
contrair(eq1)            →  A(-μ)            baixou
```

`A_\mu ≡ g_{\mu\nu}A^\nu` é uma **convenção**, e vale só para a métrica.
Nenhuma inspeção da expressão distingue a métrica de um (0,2) com nome
infeliz — aplicá-la a um tensor qualquer daria expressão bem formada e falsa.
Por isso é declaração, e por isso `contrair` sem `g = métrica` recusa em vez de
chutar. Na outra direção vale o mesmo: `g^{\mu\nu}A_\nu` → `A^\mu`.

### Derivada com índice

```
\partial_\mu A^\mu                →  d_A(-L_0, L_0)                 a divergência
\partial_\mu (A^\nu B_\nu)         →  (∂_μ A^ν) B_ν + A^ν ∂_μ B_ν     Leibniz
\partial_\mu \partial_\nu \phi - \partial_\nu \partial_\mu \phi   simplificar →  0
\nabla_\mu \nabla_\nu \phi - \nabla_\nu \nabla_\mu \phi       simplificar →  não zera
\partial_\lambda g_{\mu\nu} - \partial_\lambda g_{\nu\mu}    simplificar →  0
g^{\mu\nu} \partial_\nu \phi      contrair    →  ∂^μ φ
```

O parser do SymPy lê `\partial_\mu A` como o símbolo `partial_{mu}` vezes A. A
derivada com índice não é um fator multiplicando outro, é um objeto próprio, e
por isso a ponte a recusava. Agora ela existe como uma cabeça com o índice da
derivada no primeiro slot: `∂_μ A^ν` é `d_A(-mu, nu)`, `∇_μ` é `D_A`, `∂_μ∂_ν` é
`dd_…`. Com isso, entra na contração, na soma e na canonicalização como
qualquer tensor, e o LaTeX sai com a derivada na frente: `\partial_{\mu} A^{\nu}`.

O que vale sem hipótese:

- ∂ e ∇ são lineares e seguem Leibniz, também em escalar;
- derivadas **parciais** comutam, então `∂_μ∂_ν` é simétrica nesses slots;
- num escalar, `∇_μ φ = ∂_μ φ`, por definição, em qualquer conexão;
- a simetria do tensor derivado se mantém: `∂_λ g_{μν}` é simétrica em μν.

O que **não** se supõe: que ∇ comute (é curvatura e torção), e que ∇g = 0 (é
Levi-Civita, não uma conexão qualquer).

A derivada age no fator imediatamente à direita: `\partial_\mu A^\nu B_\nu` é
`(∂_μ A^ν) B_ν`, como em qualquer livro. Um produto pede parênteses. Há três
recusas:

- `\partial_{\mu\nu}` sem dizer a ordem;
- derivada sem operando;
- índice repetido na mesma posição, como `\partial_\mu A_\mu`.

Sem índice declarado, `\partial_p H` continua sendo a derivada parcial em
relação a p, como sempre foi.

### A conexão com índice, e a identidade de Ricci

```
\nabla = levi-civita
\nabla_\lambda g_{\mu\nu}                          simplificar →  0
\nabla_\mu \nabla_\nu \phi - \nabla_\nu \nabla_\mu \phi     simplificar →  0      sem torção

\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho = R^\rho{}_{\sigma\mu\nu} V^\sigma     eq1
R = riemann(eq1)

∇_μ∇_ν W_ρ − ∇_ν∇_μ W_ρ                 simplificar →  −R^σ{}_{ρμν} W_σ
∇_μ∇_ν T^α{}_β − ∇_ν∇_μ T^α{}_β         simplificar →  R^α{}_{σμν}T^σ{}_β − R^σ{}_{βμν}T^α{}_σ
```

`\nabla = levi-civita` diz o que distingue Levi-Civita de uma conexão
qualquer: ∇g = 0 e torção nula. Com ela, ∇ε = 0 quando ε é o tensor. Sem a
declaração, nada disso se supõe. ∂δ = ∇δ = 0 vale sempre.

O Riemann vem **da definição que você escreve**. Sinal e ordem dos slots variam
de livro para livro: Carroll e MTW escrevem `R^ρ{}_{σμν}`, o Wald escreve
`R_{μνσ}{}^ρ`, e há quem troque o sinal. `R = riemann(eq1)` lê a identidade e
extrai dela o sinal e onde fica cada slot. Daí em diante, `simplificar` troca
todo comutador ∇∇ por curvatura, com um termo por índice: o índice de cima com
um sinal, o de baixo com o outro. Um ∇∇T sozinho sai como entrou. Com a
definição de sinal trocado, sai a curvatura de sinal trocado. A definição tem
de ter a forma do comutador num vetor, e senão recusa, dizendo qual é a forma.

No caminho, dois silêncios, agora com teste:

- `R^\rho{}_{\sigma\mu\nu} V^\sigma` era lido como `R(rho)`. O `{}` que todo
  livro usa acabava o fator, e três índices e o V sumiam;
- `\nabla_\mu T^\alpha{}_\beta` com β não declarado derivava `T**alpha` como
  escalar. Agora recusa.

### ∇ aberto em Γ, e Γ em ∂g

```
\nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda     eq1
\Gamma = christoffel(eq1)

\nabla_\rho T^\mu{}_\nu = …                 expandir(eq2)     →  ∂T + Γ T − Γ T
\partial_\lambda g_{\mu\nu} = g Γ + g Γ     expandir(eq2, g)  →  True
g_{\mu\kappa} \partial_\lambda g^{\kappa\nu} = -g^{\kappa\nu} \partial_\lambda g_{\mu\kappa}
                                            simplificar       →  True
```

A ordem dos slots de Γ varia como a do Riemann: Carroll e MTW põem o índice da
derivada primeiro, Reall por último. Com torção a diferença importa, e por isso
`\Gamma = christoffel(eq1)` a lê da definição escrita, que tem de ser ∇ num
vetor. `expandir(eq)` troca cada ∇ — também ∇ dentro de ∇ — por ∂ mais um Γ
por índice: + no de cima, − no de baixo. `expandir(eq, g)` escreve ainda cada Γ
(e cada ∂Γ) por ½g(∂g + ∂g − ∂g), o que só vale para Levi-Civita e só se faz
com `\nabla = levi-civita` declarada; com ela, Γ é simétrico nos slots de
baixo. Numa equação, a resposta é `True` quando os lados coincidem.

`∂_λ g^{μν} = −g^{μα}g^{νβ}∂_λ g_{αβ}` não é hipótese: é o que "inversa" quer
dizer, e o `simplificar` a aplica sempre que há métrica declarada; `g^μ{}_ν` é δ,
e sua derivada é zero.

Com o nome à esquerda, `christoffel(eq1)` é declaração; o verbo
`christoffel` das componentes numa carta continua o mesmo.

### O Ricci e o escalar, e a dimensão como letra

```
\mu, \nu, \rho, \sigma = índices(d)
R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}              eq2
R = ricci(eq2)

R^\rho{}_{\mu\nu\rho}              simplificar →  −Ric(−μ, −ν)
g^{\mu\nu} R_{\mu\nu}               simplificar →  R
R_{\mu\nu} - R_{\nu\mu}              simplificar →  0
```

A mesma letra para o Riemann, o Ricci e o escalar, como nos livros: o posto
distingue. Qual par o Ricci contrai (e com que sinal) varia de livro para
livro, e `R = ricci(eq)` lê da definição escrita; o escalar é `g^{μν}R_{μν}`.
Por dentro, R com dois índices é outra cabeça, `Ric` — um tensor tem um posto
só. Ao simplificar, os dois viram contrações do Riemann, a canonização as
compara, e o que coincide com a definição volta a ser `R_{μν}` ou R.

Com `\nabla = levi-civita` e a métrica declaradas, o Riemann ganha as
simetrias que são teorema: antissimetria no primeiro par e troca de pares. Daí
sai a simetria do Ricci. Sem a métrica, só a antissimetria que vem do
comutador. E a saída é escrita na ordem da convenção — o índice de cima no
slot de ρ —, e não na que a canonização prefere.

`índices(d)` deixa a dimensão como letra: `g^μ{}_μ = d`, e as contas "em d
dimensões" saem com os coeficientes simplificados. O que pede um número —
ε, a assinatura — recusa.

### provar com índice

```
a, b = índices
T = tensor(2, 0, simétrico)
X = tensor(0, 1)
\nabla_a T^{ab} = 0                          eq1
\nabla_a X_b + \nabla_b X_a = 0              eq2
\nabla_a (T^{ab} X_b) = 0                    eq3
provar(eq3, eq1, eq2)
    eq1 [b→L_1] × X(-L_1)
    1/2 · eq2 [a→L_0, b→L_1] × T(L_0, L_1)
    somando
```

A prova só fecha porque T é simétrico: com `T = tensor(2, 0)` a busca não acha
a combinação, e diz isso.

O mesmo verbo, e a mesma ideia de sem índice: a prova é uma combinação linear
de relações tiradas das hipóteses, conferida de novo antes do ∎. De H = 0
valem também H com os índices livres trocados ou contraídos (pela métrica), H
vezes qualquer tensor, ∇H e ∇∇H. A busca casa cada termo do objetivo com um
termo dessas formas, módulo as simetrias declaradas, e disso tira a troca de
índices e o fator; os termos novos viram alvos, algumas rodadas, aprofundando
em ∇ só quando precisa.

Com `\nabla = levi-civita` e o Riemann declarados, `R^ρ{}_{[σμν]} = 0` — a
primeira identidade de Bianchi, teorema da torção nula — entra sem ser
hipótese, e o certificado diz quando a usou. Saem assim a conservação de
`T^{ab}X_b` com X de Killing, `∇_μ∇_νK^ρ = R^ρ{}_{νμσ}K^σ`, a Bianchi contraída a
partir da segunda identidade de Bianchi, e |∇φ|² + R constante quando
∇∇φ = Ric (com a Bianchi contraída como lema). Cada uma tem um par falso que
não sai.

### Contar, conferir em componentes, linearizar

```
\mu, \nu, \rho, \sigma = índices(4)
independentes(R)                     20      o Riemann, com Bianchi
independentes(C, eq1, eq2)           10      o Weyl: e cíclico e sem traço
em_componentes(eq3)                  True    em índices(2): R_{μν} = ½ R g_{μν}
linearizar(eq2, h)                   True    g = η + εh, até ordem ε
x = coordenadas                              ∂_j x^i = δ^i_j
```

O 20 do Riemann pede a conexão e a curvatura declaradas como acima —
`\nabla = levi-civita`, `g = métrica` e `R = riemann(eq1)` —, porque a
primeira identidade de Bianchi é teorema da torção nula. Com
`R = tensor(0,4,riemann)`, que diz só as simetrias dos slots, a resposta é 21.

`independentes(T, eq…)` conta: cada componente é uma incógnita, as simetrias
declaradas as identificam ou zeram, e cada equação dada — linear em T, com g,
δ, ε — vira uma equação por valor dos índices. Zero quer dizer que só o tensor
nulo tem aquelas propriedades naquela dimensão: é assim que o Weyl some em
d = 2, 3. A métrica da contagem é a euclidiana; a dimensão do espaço de
soluções não depende da assinatura.

`em_componentes(eq)` confere uma identidade com o tensor mais geral que as
declarações permitem (o Riemann com as suas simetrias e Bianchi) e uma
métrica simétrica qualquer, componente por componente. Se vale para o mais
geral, vale para todos.

`linearizar(eq, h)` abre ∇ em Γ e Γ em ∂g, troca `g_{ab}` por `η_{ab} + εh_{ab}`,
a inversa por `η^{ab} − εh^{ab}`, ∂g por ε∂h, e corta em ordem ε. O η fica com o
nome da métrica, e é ele que sobe e desce os índices de h.

`x = coordenadas`, sem argumentos, são as coordenadas com índice: ao
simplificar, `∂_j x^i` vira `δ^i_j` — o que pede `\delta = kronecker` (ou a
métrica) declarada, e sem isso recusa dizendo isso. `\nabla_j x^i` se lê, mas
`simplificar` o recusa: x^i não é campo vetorial, e ∇ dele não tem sentido.

### O determinante, e a carta cartesiana

```
g = métrica(-,+,+,+)
g = det(g)                     g sem índice é det g_{μν}

\nabla_\mu V^\mu = \frac{1}{\sqrt{-g}} \partial_\mu (\sqrt{-g} V^\mu)      expandir(eq, g) → True
\Gamma^\beta{}_{\alpha\beta} = \partial_\alpha (\ln \sqrt{-g})              expandir(eq, g) → True
```

Os livros escrevem g, sem índice, para o determinante; o Sucuri só lê assim
com `g = det(g)` declarado (o nome pode ser outro), e sem isso recusa: g sem
índice, sendo g tensor, é ambíguo. Declarado, `∂_λ g = g g^{μν} ∂_λ g_{μν}` — a
fórmula de Jacobi — ao simplificar, e o sinal de g vem da assinatura: na
lorentziana, g < 0 e |g| = −g.

∂ não comuta com levantar índice: `∂_μ(∂^μ φ)` é `∂_μ(g^{μν}∂_ν φ)`, com ∂g. O
Sucuri deriva cada tensor na valência **declarada** — `tensor(1,0)` é de cima,
o índice de uma derivada é de baixo — e põe g explícito no resto. Numa carta
cartesiana ∂g = 0 e a diferença some, mas a carta é declaração:
`g = métrica(cartesiana)`, ou `g = métrica(-,+,+,+, constante)` para uma carta
inercial. `métrica(euclidiana)` diz só a assinatura.

A derivada **sem** índice, `∇_U X`, é a seção seguinte.

### Simetria declarada

```
F = tensor(0, 2, antissimétrico)
h = tensor(2, 0, simétrico)

F_{\mu\nu} + F_{\nu\mu}     simplificar →  0
F_{\mu\nu} h^{\mu\nu}        simplificar →  0      antissimétrico com simétrico
F_{\mu\nu} g^{\mu\nu}        simplificar →  0      o traço de um antissimétrico
g_{\mu\nu} - g_{\nu\mu}      simplificar →  0      a métrica, sem dizer nada
F(X, X) = 0                  provar      →  ∎      sem índice, sem hipótese
```

A simetria é dos slots, e a mesma declaração serve às duas notações. Com
índice, ela alimenta a canonicalização de Butler-Portugal do SymPy, porque o
`simplify` sozinho não a usa. Sem índice, o motor põe os slots em ordem
canônica, com o sinal da permutação, e slot repetido num antissimétrico dá
zero.

A métrica é simétrica sem precisar dizer. Antes desta declaração existir, nem
`g_{\mu\nu} - g_{\nu\mu}` zerava. Não era errado, mas era incompleto.

Ler não simplifica: `F_{\mu\nu} + F_{\nu\mu}` aparece como foi escrito, com a
valência, e o zero é resposta do verbo. Há duas recusas:

- simetria num (1,1): trocar um índice de cima com um de baixo exige baixar
  um deles, e isso é a métrica, não o tensor;
- simetria num (1,0) ou (0,1): um slot só não tem com quem trocar.

O Riemann tem declaração própria, porque suas simetrias não são totais:

```
R = tensor(0, 4, riemann)

R_{abcd} + R_{bacd}      simplificar →  0      antissimétrico no primeiro par
R_{abcd} + R_{abdc}      simplificar →  0      e no segundo
R_{abcd} - R_{cdab}      simplificar →  0      simétrico na troca dos pares
R_{abcd} g^{ab}          simplificar →  0
R(X,X,Y,Z) = 0           provar      →  ∎
```

Essas simetrias do (0,4) são as mesmas em todos os livros. O que muda entre
convenções é o sinal geral e a ordem dos índices no (1,3), e nada disso toca
as trocas de slots. O (1,3), `R^a_{bcd}`, mistura índices de cima e de baixo e é
recusado pela regra acima. A identidade cíclica, `R_{a[bcd]} = 0`, **não** entra:
não é troca de slots, é teorema, e pede torção nula. Ela vem como hipótese.

Nome de várias letras é recusado na declaração: `Rm_{abcd}` em LaTeX é R vezes
`m_{abcd}`, e é assim que o parser lê. Sem a recusa, a declaração existiria e
nunca seria usada, sem aviso. Use uma letra ou um comando (`\Rm`).

E a notação de simetrização:

```
T_{(\mu\nu)}                    →  ½ T_{μν} + ½ T_{νμ}
T_{[\mu\nu]}                    →  ½ T_{μν} − ½ T_{νμ}
S_{(\mu|\rho|\nu)}              →  ½ S_{μρν} + ½ S_{νρμ}       ρ fica de fora
S_{[\mu\nu\rho]}                →  seis termos, com 1/6
T_{(\mu\nu)} + T_{[\mu\nu]} - T_{\mu\nu}   simplificar →  0
F_{(\mu\nu)}                    simplificar →  0            F antissimétrico
```

Antes disto, com os índices declarados, `T_{(\mu\nu)}` era lido como
`T_{\mu\nu}`: os parênteses sumiam, e `T_{(\mu\nu)} - T_{\mu\nu}` dava **zero**,
o que é falso para T sem simetria. Sem índices declarados, o parser do SymPy
faz o mesmo, e agora é recusado.

O fator é 1/n!, o de Wald, MTW e Carroll, e a leitura diz isso numa nota. São
recusados:

- colchete que não fecha ou aninhado;
- simetrização de um índice só;
- barra fora de um colchete;
- simetrização que junta índice de cima com de baixo (trocá-los pede a métrica).

### Kronecker e Levi-Civita

```
\delta = kronecker
\delta^\mu_\nu A^\nu        simplificar →  A^μ
\delta^\mu_\mu             simplificar →  4          a dimensão
\delta_{\mu\nu}            recusa: com a métrica, isso é g_{μν}

\epsilon = levi-civita(tensor)      ou  levi-civita(símbolo)
\epsilon_{\mu\nu\rho\sigma} S^{\mu\nu}    simplificar →  0     S simétrico
g_{\alpha\mu}\epsilon^{\mu\nu\rho\sigma}      contrair →  ε_α^{νρσ}      só o tensor
```

δ é declaração porque `\delta` também é variação, número pequeno e índice.
Ela exige um índice em cima e um embaixo. `δ_{μν}` fora do espaço euclidiano não
é tensor; com a métrica, é `g_{μν}`.

Levi-Civita não se declara sem escolher, porque os livros não fazem igual:

- o **símbolo** vale ±1 em toda carta, é uma densidade, e g não o move:
  `contrair` recusa baixar-lhe um índice;
- o **tensor** é √|g| vezes o símbolo, e sobe e desce com g.

Nos dois casos, ε tem tantos índices quanto a dimensão e é totalmente
antissimétrico.

A contração de dois ε pede a assinatura, e a assinatura se declara com os
sinais:

```
g = métrica(-,+,+,+)
\delta = kronecker
\epsilon = levi-civita(tensor)
\epsilon^{\mu\nu\rho\sigma} \epsilon_{\mu\nu\rho\sigma}     simplificar →  −24
\epsilon^{\mu\nu\rho\sigma} \epsilon_{\mu\nu\rho\alpha}     simplificar →  −6 δ^σ_α
\epsilon^{ijk} \epsilon_{imn}                  simplificar →  δ^j_m δ^k_n − δ^j_n δ^k_m   (euclidiana, 3D)
```

Em geral, `ε^{a₁…a_k b…}ε_{a₁…a_k c…} = σ k! δ^{[b…}_{c…]}`, com o sinal da
permutação que alinha os índices contraídos. Para o **tensor**, σ = (−1)^s,
onde s é o número de sinais negativos. Para o **símbolo**, σ = 1, porque ele
vale ±1 nas duas posições e a métrica não entra. O tensor sem assinatura
declarada fica como está, porque o sinal é desconhecido — e sem
`\delta = kronecker` também, porque o resultado se escreve com δ.

`lorentziana` sozinha é recusada: (−,+,+,+) e (+,−,−,−) estão as duas em uso,
e εε e g(U,U) mudam de sinal entre elas. `riemanniana` e `euclidiana` dizem
todos +. Declarada depois dos índices, a assinatura tem de bater com a
dimensão deles — `i, j = índices(3)` e depois `g = métrica(-,+,+,+)` é
recusado. Declarada antes, ela dá a dimensão aos índices que vêm sem número
(`\mu, \nu = índices` sai de dimensão 4 com (−,+,+,+) e 3 com (+,+,+)); quem
diz o número, como `índices(3)`, é aceito com o número que disse.

### A conexão sem índice: ∇_U X, [U,X] e R(U,X)W

```
U = tensor(1,0)
X = tensor(1,0)
R = curvatura

\nabla_U \nabla_X U - \nabla_X \nabla_U U   →  nabla_U(nabla_X(U)) - nabla_X(nabla_U(U))
[U, X] = 0                                 →  Eq([U, X], 0)
\nabla_U \nabla_U X = R(U,X)U              →  Eq(nabla_U(nabla_U(X)), R(U, X)(U))
```

Sem isso o parser lia `\nabla_U X` como `X*nabla_{U}`: um símbolo de nome
esquisito multiplicando X. O produto comuta, então `∇_U∇_X` e `∇_X∇_U` saíam
iguais, e a curvatura, que é justamente a diferença entre os dois, sumia sem
aviso. `[U,X]` ele recusava, e `R(U,X)U` virava a pergunta "R aplicada, ou R
vezes o parêntese?".

A tipografia não resolve nenhum dos três. `\nabla_U` e `\nabla_\mu` se
escrevem igual, e no Wald a letra latina do subscrito **é** índice. `[a,b]`
pode ser colchete de Lie, comutador, intervalo ou par. Quem decide é a
declaração:

- **`∇_U`**: um vetor escrito sem índice só pode ser o objeto abstrato. Aí `∇_U`
  vira aplicação, com a ordem guardada na estrutura. A direção pode ser
  composta, como em `\nabla_{[U,X]}` ou `\nabla_{U+X}`.
- **[U,X]**: entre dois vetores declarados, só pode ser o colchete de Lie.
  Colchete sem vírgula continua sendo agrupamento, como em `[x+1]^2`.
- **R(U,X)W**: com `R = curvatura`, R não multiplica o parêntese. Exige dois
  vetores e o vetor sobre o qual age, e `R(U,X)` sozinho recusa.

Quando o que foi declarado não licencia a leitura, recusa. Isso vale para
subscrito sem declaração, colchete de coisas que não são vetores e curvatura
agindo sobre uma 1-forma. Também recusa onde não fica claro até onde o operador
alcança (`\nabla_U X^\mu`, `\nabla_U X_1`): nesse caso use parênteses.

`R = curvatura` declara o **papel** de R, e não a convenção. O sinal e a ordem
dos argumentos variam de livro para livro. Para *ler* `R(U,X)W` isso não
importa, porque é o mesmo objeto escrito. Para *calcular* importa, e aí a
definição terá de ser declarada, não suposta.

### Provar

```
[U,X] = 0                                                     eq1
\nabla_U U = 0                                                eq2
\nabla_U X - \nabla_X U = [U,X]                               eq3
R(U,X)U = \nabla_U\nabla_X U - \nabla_X\nabla_U U - \nabla_{[U,X]} U   eq4
\nabla_U \nabla_U X = R(U,X)U                                 eq5

provar(eq5, eq1, eq2, eq3, eq4)
    − eq4            R(U, X)(U) - nabla_U(nabla_X(U)) + … = 0
    nabla_U(eq1)     nabla_U([U, X]) = 0
    nabla_{eq1}(U)   nabla_{[U, X]}(U) = 0
    nabla_X(eq2)     nabla_X(nabla_U(U)) = 0
    nabla_U(eq3)     -nabla_U([U, X]) + nabla_U(nabla_U(X)) - nabla_U(nabla_X(U)) = 0
    somando          ∇_U∇_U X = R(U,X)U  ∎
```

Essa é a equação do desvio geodésico, deduzida sem índices. `nabla_U(eq3)` é
eq3 com `∇_U` aplicado aos dois lados, e `nabla_{eq1}(U)` é eq1 posta na direção
de ∇ agindo sobre U.

Só entram as hipóteses **nomeadas** na chamada. Escrever uma equação no caderno
não é afirmá-la, e uma prova que usasse a conta de rascunho da linha de cima não
provaria nada.

O motor sabe sozinho só o que vale para **qualquer** conexão, em qualquer livro:

- `∇_U X` é linear em U sobre funções, e no operando segue Leibniz:
  `∇_U(fX) = U(f)X + f∇_U X`;
- o colchete é antissimétrico e segue Leibniz:
  [fA, gB] = fg[A,B] + f A(g) B − g B(f) A;
- U(f) segue a regra da cadeia;
- R é tensor.

Tudo o mais tem de vir das hipóteses: torção nula, que a curva é geodésica e,
principalmente, a **definição** de R. Esse é o jeito de declarar a convenção de
sinal em vez de supor uma. Com a definição de sinal oposto, a mesma chamada
recusa `R(U,X)U` e prova `-R(U,X)U`. Também não passam as coisas que parecem
verdade e não são: `\nabla_U(fX) = f\nabla_U X` (falta U(f)X),
`[fU, X] = f[U,X]` e `R(U,X) = -R(X,U)` sem a definição.

Por baixo, tudo vira combinação linear. Das hipóteses saem outras relações,
aplicando os contextos que aparecem no problema (`∇_U □`, `∇_□ U`, `[□, X]`, …). A
prova é uma combinação dessas relações que dá o objetivo, e a soma é conferida
de novo, do zero, antes do ∎.

Quando o motor não acha, diz o que costuma faltar ("nenhuma hipótese fala de
R(U, X)(U)") e diz também que não achar não é prova de que é falso.

### Para todo

Uma definição vale para qualquer vetor, e é assim que se escreve:

```
\forall A, B, W: R(A,B)W = \nabla_A \nabla_B W - \nabla_B \nabla_A W - \nabla_{[A,B]} W   eq1
\forall A, B: \nabla_A B - \nabla_B A = [A,B]                                           eq2
[U,X] = 0                                                                                eq3
\nabla_U U = 0                                                                           eq4
\nabla_U \nabla_U X = R(U,X)U                                                            eq5

provar(eq5, eq1, eq2, eq3, eq4)
    − eq1[A→U, B→X, W→U]
    nabla_U(eq2[A→U, B→X])
    nabla_U(eq3) · nabla_{eq3}(U) · nabla_X(eq4)
    somando          ∇_U∇_U X = R(U,X)U  ∎
```

A definição de R e a torção nula são ditas **uma vez**. A prova instancia cada
uma onde o problema pede, e diz em qual instância: `eq1[A→U, B→X, W→U]`.

O separador depois da lista é obrigatório: dois-pontos, `\colon`, `\quad`,
`\;` ou `\,`. Sem ele não se sabe onde a lista acaba: em
`\forall W, R(U,X)W = …`, a vírgula separa nomes ou encerra a lista? As
variáveis ligadas são vetores só **dentro** da equação e não vazam para as
linhas de baixo.

A instanciação não tenta todos os vetores. Ela casa cada termo da hipótese com
os termos do problema: `R(A,B)W` com `R(U,X)U` dá A=U, B=X, W=U. É o que se faz
ao ler uma definição, aplicá-la ao caso que se tem na mão. Com a definição
geral saem coisas que antes não saíam: a antissimetria `R(A,B)W = -R(B,A)W` e,
com a identidade de Jacobi como hipótese, a identidade de Bianchi algébrica.

### Funções escalares

Escalar é tudo o que não foi declarado tensor, e `\nabla_U f` com f escalar é
a derivada direcional U(f):

```
\nabla_U (f X) = \nabla_U f \, X + f \nabla_U X        provar: ∎, sem hipótese
[f U, X] = f [U, X] - \nabla_X f \, U                 provar: ∎, sem hipótese
\nabla_U (f X) = f \nabla_U X                         não passa: falta U(f)X
\nabla_U f = 0                                        eq1
provar(eq_acima, eq1)                                 ∎ — o passo é "eq1·X"
```

Todo símbolo que não é número é tratado como **função**, e não como constante.
É o lado seguro: se c for constante, U(c) = 0 é só um caso particular, e a
prova que precisar disso pede a hipótese. Nunca sai uma prova errada por tratar
como constante o que variava.

Hipótese escalar, como `\nabla_U f = 0`, é relação como as outras: multiplicada
por um vetor do problema (`eq1·X`), derivada numa direção (`U(eq1)`), ou por
uma função (`f·eq1`). Cada uma dessas operações aparece como passo na tabela.

**Não se divide por função.** A combinação que fecha a prova é só com números.
Dividir por f seria concluir X = U de fX = fU, o que é falso onde f se anula. A
eliminação é feita em coordenadas numéricas, uma por monômio, e multiplicar por
função é contexto explícito (`f·eq1`). Uma versão anterior do motor dividia, e
de fX = fU concluía X = U. Hoje há teste para isso.

`U(f)` também se lê como derivada direcional, mas continua sendo pergunta: U
aplicado a f, ou U vezes f? As duas leituras são bem tipadas, porque (a+b)U
também é vetor. Escolhida a aplicação, o que sai é U(f), e não uma função
chamada U. `\nabla_U f` não tem dúvida.

### A métrica

Com `g = métrica`, `g(X,Y)` é o produto escalar. Com `\omega = tensor(0,1)`,
`\omega(U)` é ω aplicado a U. Em geral, um (0,n) aplicado a n vetores é
escalar: é a notação de slots do Schutz, a mesma das declarações. Não sobra
dúvida: com vírgula, `g(X,Y)` não pode ser produto, e com o tipo declarado os
slots são vetores.

```
\forall A, B, C: \nabla_A g(B,C) = g(\nabla_A B, C) + g(B, \nabla_A C)    eq1
\forall A, B: \nabla_A B - \nabla_B A = [A,B]                               eq2
2 g(\nabla_X Y, Z) = \nabla_X g(Y,Z) + \nabla_Y g(X,Z) - \nabla_Z g(X,Y)
                    + g([X,Y],Z) - g([X,Z],Y) - g([Y,Z],X)                   eq3

provar(eq3, eq1, eq2)
    − eq1[A→X, B→Y, C→Z] · − eq1[A→Y, B→X, C→Z] · eq1[A→Z, B→X, C→Y]
    g(eq2[A→X, B→Y], Z) · − g(eq2[A→X, B→Z], Y) · − g(X, eq2[A→Y, B→Z])
    somando   a fórmula de Koszul  ∎
```

A fórmula de Koszul sai das duas condições que fazem de ∇ a conexão de
Levi-Civita: compatibilidade com a métrica e torção nula. Sem a torção nula,
não sai. `g(eq2[…], Z)` é a torção nula posta no primeiro slot de g: uma
relação entre vetores levada a uma relação entre escalares.

O motor sabe sozinho que g é linear sobre funções em cada slot e simétrica.
Simetria não é convenção de livro, é o que se chama de métrica. Também sabe que
o colchete age numa função como `[A,B](f) = A(B(f)) − B(A(f))`, porque essa é a
definição do colchete. A compatibilidade não entra sozinha: ela é o que
distingue Levi-Civita de uma conexão qualquer, e vem como hipótese, com ∀ ou
sem.

Limites: só igualdades lineares, com coeficientes escalares. Provas que pedem
uma ideia, e não só encadear hipóteses, não saem. Um exemplo é
g(R(U,X)Y, W) = −g(Y, R(U,X)W): essa prova precisa introduzir h = g(Y,W) e
comparar `[U,X](h)` com `U(X(h)) − X(U(h))`. Nada disso aparece no enunciado, e a
busca só instancia o que aparece.

### De uma notação à outra

```
\nabla = levi-civita
\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho = R^\rho{}_{\sigma\mu\nu} V^\sigma      eq1
R = riemann(eq1)
R = curvatura
\nabla_U \nabla_U X = R(U,X)U                                                    eq2
índices(eq2)
    U^α(U^β ∇_α∇_β X^μ + ∇_α U^β ∇_β X^μ) = R^μ{}_{αβσ} U^α U^β X^σ
```

A prova sem índice é mais curta e não depende de carta, e o livro de física
escreve com índice. `índices(eq)` traduz com as regras que as declarações já
fixaram:

- X vira X^μ;
- g(X,Y) vira `g_{αβ}X^αY^β`, e ω(X) vira `ω_αX^α`;
- `∇_X Y` vira `X^α∇_αY^μ`, com Leibniz nos produtos;
- X(f) vira `X^α∇_α f`;
- [X,Y] vira `X^α∇_αY^μ − Y^α∇_αX^μ` com Levi-Civita, e com ∂ sem ela;
- R(U,X)W segue a convenção de `riemann(eq)`.

Para traduzir R(U,X)W, a mesma letra tem de estar declarada `curvatura` e
`riemann(eq)`. A tradução supõe então `R(U,X) = ∇_U∇_X − ∇_X∇_U − ∇_{[U,X]}`, que
é como a definição com índice a lê, e diz isso numa nota.

As duas notações falam da mesma coisa, e isso se confere. A compatibilidade
com a métrica, escrita sem índice e traduzida, dá `True` em `simplificar` com
Levi-Civita, porque ∇g = 0. Uma versão errada mostra a diferença que sobra.

A saída não é canonicalizada. Com a métrica, a forma canônica sobe e desce os
mudos, e `R^μ{}_{σαβ}U^σ` sairia `R^{μαβσ}U_σ`, que é igual e ilegível. Ainda não:
a volta, de índice para sem índice; e ∀ e formas não se traduzem.

### Formas diferenciais

```
\omega = forma(1)
\eta = forma(2)                       uma 2-forma: um (0,2) antissimétrico

\mathrm{d}(\omega \wedge \eta) = \mathrm{d}\omega \wedge \eta - \omega \wedge \mathrm{d}\eta   provar → ∎
\mathcal{L}_X \mathrm{d}\omega = \mathrm{d} \mathcal{L}_X \omega                          provar → ∎
\iota_Y \iota_X \eta = \eta(X, Y)                                                 provar → ∎
\eta \wedge \eta = 0                                        não passa: grau par
\mathrm{d}(f \omega) = \mathrm{d} f \wedge \omega              só com \mathrm{d}\omega = 0
```

d, ∧, `ι_X` e `ℒ_X` sem índice. Na leitura decide a declaração, como no resto:

- `\mathrm{d}` é sempre o operador;
- `d` sozinho só é operador quando age numa forma declarada, e `df` com f
  função continua d vezes f;
- `\wedge` (ou `\land`) só vale entre formas;
- `\iota_X` e `\mathcal{L}_X` pedem X declarado vetor.

Uma p-forma é um (0,p) antissimétrico, e por isso ω(X,Y) se lê com o que já
existia.

O motor sabe sem hipótese o que vale em qualquer livro: d² = 0, o Leibniz
graduado, `α∧β = (−1)^{pq}β∧α`, `ι_X` como antiderivação (com `ι_X df = X(f)` e
`ι_Xι_X = 0`), e a fórmula de Cartan, `ℒ_X = ι_X d + d ι_X`, que é teorema e não
convenção.

A convenção que entra é `ι_Y ι_X ω = ω(X,Y)`, a do determinante (Lee, Spivak).
A fórmula dω(X,Y) = X(ω(Y)) − Y(ω(X)) − ω([X,Y]) muda de fator com a
normalização, e por isso vem como hipótese, com ∀:

```
\forall A, B: \iota_B \iota_A \mathrm{d}\omega = \nabla_A (\omega(B)) - \nabla_B (\omega(A)) - \omega([A,B])   eq1
\mathrm{d}\omega = 0                                                                              eq2
\nabla_X (\omega(Y)) - \nabla_Y (\omega(X)) = \omega([X,Y])                                         eq3
provar(eq3, eq1, eq2)      − eq1[A→X, B→Y] · iota_Y(iota_X(eq2))   ∎
```

As relações entre formas entram no mesmo motor das outras. Os termos são
monômios exteriores, o escalar é o monômio vazio, e os contextos são `d □`,
`ι_X □`, `α ∧ □` e `f·□`.

O dual de Hodge se declara depois da assinatura, que é de onde saem a
dimensão n e os sinais negativos s:

```
g = métrica(-,+,+,+)
\star = hodge
\star \star F = -F                                    provar → ∎      2-forma, Lorentz
\star \star \omega = \omega                              provar → ∎      1-forma, Lorentz
\omega \wedge \star \alpha = \alpha \wedge \star \omega          provar → ∎
\omega \wedge \star \omega \wedge \alpha = 0                  provar → ∎      grau 5 > 4
```

⋆ é linear sobre funções, ⋆⋆ = (−1)^{p(n−p)+s} numa p-forma, α∧⋆β = β∧⋆α,
e todo produto de grau maior que n é zero. A orientação não precisa ser dita:
trocá-la troca o sinal de ⋆, mas não o de ⋆⋆ nem a simetria de α∧⋆β. O
codiferencial δ = ±⋆d⋆ tem sinal de convenção, e por isso não entra pronto;
escreve-se ⋆d⋆. Sem `\star = hodge`, `\star` não é operador.

### Sem declarar, a recusa continua

Índice não é expoente, e o parser do SymPy não sabe a diferença. Medido:

```python
>>> parse_latex(r"A^\mu")                    A**mu          # A elevado a μ
>>> parse_latex(r"x^2_i")                    x**2           # o índice some
>>> parse_latex(r"\Gamma^\lambda_{\mu\nu}")  Gamma**lambda_{mu*nu}
>>> parse_latex(r"g_{\mu\nu}")               Symbol('g_{mu*nu}')
```

Nada disso levanta erro e nada disso tem símbolo estranho na saída: são
expressões **bem formadas e falsas**, a pior classe de erro que este programa
conhece. Quem escrevesse relatividade receberia contas silenciosamente erradas.

Sem índice declarado, o Sucuri recusa onde o parser **comprovadamente perde** — sobrescrito antes de
subscrito, e o mesmo índice grego em cima e embaixo (soma de Einstein) — e
**avisa** onde há só suspeita, porque `A^\mu` é mesmo "A elevado a μ" em algum
texto, e distinguir índice de expoente pela tipografia é impossível.

Declarar o índice é o que abre a ponte, e aí nada disso acontece.

## Métrica e curvatura

A notação de índice diz a **estrutura** — que `g` tem dois índices embaixo, que
`A^\mu B_\mu` está contraído. Não diz o que `g` **vale**. Christoffel, Ricci e
Riemann precisam do outro lado: componentes numa carta.

```
x = coordenadas(t, r, \theta, \phi)
g = métrica(-(1 - \frac{2M}{r}), \frac{1}{1 - \frac{2M}{r}}, r^2, r^2 \sin^2\theta)

christoffel(g)  →  13 componentes não nulas, Γ^t_{tr} = M/((-2M + r)r), …
ricci(g)        →  resultado: todas as componentes são nulas
escalar(g)      →  0
```

Schwarzschild inteiro, e o Ricci nulo que é o teste de sanidade de toda
relatividade. O cálculo é do `sympy.diffgeom`; o que faltava era **dizer a
métrica em LaTeX**.

Ela vai pela **diagonal**, como acima, ou pelo **elemento de linha**, que é
como os livros dão as métricas com termo cruzado:

```
x = coordenadas(t, r, \theta, \phi)
g = métrica(ds^2 = -dt^2 + 2 a\, dt\, d\phi + dr^2 + r^2 d\theta^2 + r^2 \sin^2(\theta) d\phi^2)
    →  g é a métrica em (t, r, \theta, \phi), dada pelo elemento de linha
christoffel(g)  →  13 componentes não nulas, Γ^t_{rφ} = a r sin²θ/(a² + r² sin²θ), …
```

O termo `2a\, dt\, d\phi` vira `g_{tφ} = g_{φt} = a`. Matriz em LaTeX não
entra: `métrica(\begin{pmatrix}…)` é recusada, com uma mensagem que diz as duas
formas que valem.

Com componentes declaradas, `avaliar` leva a notação até os números:

```
\mu, \nu = índices
A = tensor(1,0)
g_{\mu\nu} A^{\nu}
avaliar(eq1)   →  A_{t} = A__t·(2M − r)/r        A_{\theta} = A__theta·r²
                  A_{r} = A__r·r/(r − 2M)        A_{\phi}   = A__phi·r²sin²θ
```

As componentes de A ninguém declarou, então entram como nomes — na convenção
do SymPy, `A__t`, que a tela tipografa como A^{t}. O que volta para dentro sem
mudar de sentido é preciso dizer: o nome `A__t` volta no Python (no SymPy e no
script exportado ele é o mesmo símbolo), e os **rótulos da tabela** voltam no
caderno. O A^{t} tipografado, relido como LaTeX, é uma potência — é o que a
notação diz sem índice declarado.

`contrair` dá a **estrutura**; `avaliar` dá o **valor**. São dois pedidos
diferentes, e o programa os mantém separados.

O rótulo impresso é um alvo de verbo — `avaliar(A_{t})` (ou `avaliar(A_t)`)
depois do `avaliar(eq1)`, `latex(\Gamma^{r}_{tt})` depois do `christoffel(g)` —
sem exigir as chaves duplas que a tela usa, porque chave é tipografia do TeX e
não identidade do objeto. Valem os rótulos da **última** tabela. A componente
**nula** não entra na tabela, e mesmo assim responde quando perguntada
(`avaliar(\Gamma^{t}_{tt})` → 0): esconder os 51 zeros é mostrar as 13 que
importam, mas dizer "não conheço" a quem pede um deles seria mentir.

O que volta são **componentes**, e não o tensor: trocar de carta troca todas
elas. Por isso a resposta diz sempre em que coordenadas está. O que não muda
são as afirmações invariantes — Ricci nulo é Ricci nulo em qualquer carta.

## O que NÃO é ambiguidade

`∂` está reservado à derivada parcial. Ninguém nunca escreveu
`\frac{\partial u}{\partial t}` querendo uma fração dos símbolos ∂, u e ∂t —
e com `d` a dúvida é real, porque `d` é uma letra que as pessoas usam para
distância, diâmetro, o que for.

O sítio continua sendo **localizado**, porque o parser do SymPy degrada
`\frac{\partial^2 u}{\partial x^2}` em `(partial**2*u)/(partial*x**2)` e
alguém tem de reescrever. O que muda é que ninguém precisa ser consultado.

Pergunta que não é pergunta gasta a credibilidade das que são — o mesmo motivo
pelo qual `\arctan(` não abre um sítio de justaposição.

## Ambiguidades reconhecidas

| Tipo | Exemplo | Leituras |
|---|---|---|
| linha | `y''` | derivada / símbolo |
| Leibniz | `\frac{d^2y}{dx^2}` | derivada / fração de símbolos |
| justaposição | `f(x+1)` | aplicação / produto |
| **Newton** | `\ddot{q}` | derivada temporal / decoração |
| **parcial** | `\partial_p H` | derivada parcial / produto |

A linha **parcial** é das que o Sucuri **localiza**, e nunca pergunta: pelo
motivo da seção anterior, `\partial_p H` sai como a derivada parcial de H em
relação a p sem abrir pergunta — o sítio existe porque o parser do SymPy o
degradaria em produto, e alguém tem de reescrevê-lo.

Tempo e variável independente são declarados **em separado**: em mecânica a
variável da linha raramente é a do ponto, e tratá-las como uma só produziria
equação errada em silêncio.

```python
doc = (sucuri.Document(independent_variable='x', time_variable='t')
       .primes_are_derivatives().dots_are_time_derivatives())
doc.read(r"\dot{q} = \partial_p H")     # d/dt de um lado, d/dp do outro
```

## A árvore reconhecida

`Expression.tree()` devolve o que o programa entendeu, nó a nó — e cada nó
nascido de um sítio ambíguo carrega **como** aquele sítio foi resolvido. É isso
que permite à interface pintar de âmbar o que veio de convenção. Para a
Riccati do início, `\varphi'' + 3\varphi\varphi' + \varphi^3 = 4r\varphi + 2r'`,
lida com "linha é derivada" como convenção e o `r'` anotado à mão
(`exemplos/arvore.py`):

```
igualdade
  soma
    potência
      função varphi aplicada a (x)
        símbolo x
      número 3
    produto
      número 3
      derivada de ordem 1 de varphi em x  [inferida]  <- conferir
      função varphi aplicada a (x)
        símbolo x
    derivada de ordem 2 de varphi em x  [inferida]  <- conferir
  soma
    produto
      número 2
      derivada de ordem 1 de r em x  [explícita]
    produto
      número 4
      …
```

Derivadas são folhas na leitura do usuário: quem lê quer ver "derivada segunda
de φ", não a árvore interna dela. `to_dict()` serializa para a interface web.
Pela API em Python, os rótulos da árvore saem em português, qualquer que seja
o idioma da interface.

## Uso

```python
import sucuri

# caso avulso — sem convenção, RECUSA, que é o padrão
e = sucuri.parse(r"\varphi'' + \varphi' = r")
e.questions()                      # as perguntas, em vez de um palpite
                                   # (em português, na API em Python)

# com a convenção declarada
e = sucuri.parse(r"\varphi'' + \varphi' = r",
                 independent_variable='x', primes='derivative')
e.to_sympy()
e.inferred                         # o que veio de convenção e pede conferência

# trabalho continuado: o documento guarda convenções e anotações
doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
doc.annotate("prime", "r", "derivative", order=1)
doc.read(...).tree()

# a conexão sem índice, e uma prova
from sucuri.prova import provar, linhas
doc = sucuri.Document()
doc.tensor("U", 1, 0); doc.tensor("X", 1, 0); doc.curvature("R")
eq = lambda s: doc.read(s).to_sympy()
p = provar(eq(r"\nabla_U \nabla_U X = R(U,X)U"),
           {"def": eq(r"\forall A, B, W: R(A,B)W = \nabla_A \nabla_B W"
                      r" - \nabla_B \nabla_A W - \nabla_{[A,B]} W"),
            "tor": eq(r"\forall A, B: \nabla_A B - \nabla_B A = [A,B]"),
            "fam": eq(r"[U,X] = 0"), "geo": eq(r"\nabla_U U = 0")},
           {"U": (1, 0), "X": (1, 0)})
linhas(p)                          # os passos: rótulo, texto, LaTeX
```

Na API em Python as mensagens são em português: as perguntas de
`e.questions()`, a exceção `Unresolved` que `e.to_sympy()` levanta enquanto
houver sítio pendente ("2 sítio(s) ambíguo(s) sem anotação: …") e os rótulos
de `tree()`. A troca PT/EN é da interface.

O exemplo inteiro, com as recusas e a troca de sinal, está em
`exemplos/desvio_geodesico.py` — e a suíte o executa.

## Manual

`sucuri/interface/estatico/manual.html` — servido em `/manual.html` nas duas
versões. Escrever, declarar, os verbos, o que cada resposta quer dizer, e o que
o programa ainda não faz.

**Os exemplos do manual são executados pela suíte a cada mudança.** Manual cujos
exemplos ninguém roda apodrece, e apodrece em silêncio — que é a forma que este
projeto persegue. Quando um exemplo quebra, ou o programa mudou e o manual
mente, ou o manual está certo e o programa regrediu; os dois merecem parar a
suíte.

## Instalação

Python ≥ 3.10. Na pasta do repositório:

```bash
pip install .                     # ou, para rodar a suíte: pip install -e ".[dev]"
python -m sucuri.interface        # ou o comando `sucuri`, que o pip instala
pytest                            # a suíte, em tests/
```

## A interface

```bash
python -m sucuri.interface        # abre em http://127.0.0.1:8765/
```

E **online**, sem instalar nada: `web/` é a mesma interface com o motor rodando
dentro do navegador — Python e SymPy compilados para WebAssembly pelo Pyodide,
o pacote `sucuri` num zip que a página desempacota. Não é uma segunda
implementação: são os mesmos arquivos, e há teste que falha se o publicado
divergir do repositório. Nada do que o usuário escreve sai da máquina dele,
porque não há para onde ir. Ver `web/LEIAME.md`.

Servidor local e página no navegador. A escolha é deliberada: o programa é de
Linux hoje e fica online amanhã sem reescrita — o mesmo motor, a mesma página,
outro endereço. Só biblioteca padrão do lado do Python; o KaTeX vem
empacotado, e a interface funciona sem rede.

O que a página mostra, da esquerda para a direita:

- **a entrada em LaTeX**, relida a cada tecla (janela de 220 ms);
- **os sítios ambíguos**, um a um, com as leituras possíveis em botões — clicar
  é anotar, e a anotação vence a convenção;
- **as convenções do documento**, que valem para tudo e aparecem em âmbar;
- **a árvore reconhecida**, com a proveniência de cada nó;
- **a leitura**, tipografada — o que o programa entendeu, em matemática de
  livro, e não o que você escreveu;
- **a saída em SymPy**, colável num script;
- **os módulos**, com a barreira de proveniência intacta: conclusão sem fonte
  chega à página marcada como não apresentável.

A interface não decide nada de matemática. Entre ela e o motor passa JSON
(`/api/ler`, `/api/anotar`, `/api/avaliar`, `/api/modulos`, `/api/operar`, e
as do caderno: `/api/caderno/executar`, `/api/caderno/refazer`,
`/api/caderno/reiniciar`), e as duas únicas
decisões que ela transporta são as do usuário: convenção e anotação.

## O caderno

```bash
python -m sucuri.interface        # e clique em "caderno" no cabeçalho
```

Uma equação por página serve para inspecionar notação; trabalho é escrever uma
coisa, olhar, escrever outra que usa a primeira.

```
        f = f(x)                               →  daqui para baixo, f é função de x
        f^{\prime} = x^2          Shift+Enter   →  eq1,  df/dx = x²
        resolver(eq1)                          →  eq2,  f(x) = C₁ + x³/3
                                                  conferência: substituída na equação: resto 0
        exportar(eq1)                          →  o script que roda sem o Sucuri
```

Sem o `f = f(x)`, a linha de `f^{\prime}` fica pendente: derivada ou símbolo
chamado f′ — e é pergunta.

Cinco ações, e cada uma mexe numa camada diferente do estado — a distinção
entre elas é a razão de existirem cinco e não duas:

| | |
|---|---|
| **Novo** | apaga o escrito **e** o acumulado |
| **Abrir** | troca o escrito, refaz o acumulado |
| **Salvar** | leva o escrito e as decisões para um arquivo |
| **Rodar tudo** | refaz o acumulado a partir do escrito, na ordem |
| **Reiniciar** | joga fora só o acumulado: o que está escrito fica |

"Reiniciar" apaga `eq1`, `eq2` e as declarações sem tocar numa linha do que
você escreveu — depois dele, `resolver(eq1)` deixa de achar `eq1`, que é
exatamente o ponto.

O arquivo salvo é texto, legível, com as células separadas por `%%` — `%` é
comentário em LaTeX, então ele abre em qualquer editor. As decisões de sítio
vão numa linha de comentário no alto: são do usuário, não do motor, e sem elas
o caderno reaberto voltaria a perguntar o que já foi respondido.

**O caderno não tem convenções** — tem declarações, que são células como as
outras. Seis campos de formulário diziam o que três linhas na folha dizem
melhor, e dizem de um jeito mais forte: a convenção *escolhe* uma leitura, a
declaração *dissolve* a dúvida.

```
u = u(t,x)        u é função de t e x
e = euler         e é o número de Euler
c = símbolo       c é símbolo, não função: c(…) é produto
```

Só isso decide `'`, `\dot`, `∂`, Leibniz e justaposição para os nomes
declarados. E o que a notação não diz continua sendo pergunta: `u'` com `u`
função de duas variáveis não diz em relação a qual, e declarar não inventa.

### A equação da onda, e o que "o SymPy não resolve" quer dizer

```
u = u(t,x)
c = símbolo
\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}

resolver(eq1)      →  sem solução encontrada
                      motivo: o solver falhou: NotImplementedError: psolve: Cannot solve
                      -c**2*Derivative(u(t, x), (x, 2)) + Derivative(u(t, x), (t, 2))
separar(eq1)       →  eq2   T″(t) = k T(t)
                      eq3   c² X″(x) = k X(x)       com as duas resolvidas na tabela
F = F(x)
G = G(x)
u = F(x - c t) + G(x + c t)                          eq4
conferir(eq1, eq4) →  candidata verificada: substituída na equação: resto 0
```

O `pdsolve` não resolve a onda — e ele é só um dos caminhos do SymPy. O
`pde_separate_mul` separa, o `dsolve` resolve cada pedaço, e o `checkpdesol`
confere d'Alembert.

O que uma conta **produz** ganha nome, e é isso que faz o caderno compor
(aqui, logo depois da eq1):

```
separar(eq1)     →  eq2   T″(t) = k T(t)
                    eq3   c² X″(x) = k X(x)
resolver(eq2)    →  eq4   T(t) = C₁e^(−√k t) + C₂e^(√k t)
```

Operação que devolve equações sem nome devolve becos: quem lê duas EDOs numa
tabela não tem como pedir a próxima conta sobre elas senão redigitando.

`separar` **não se apresenta como solução**: separar SUPÕE que a solução é um
produto, e a suposição é uma restrição. O que sai são os modos; a solução geral
é a superposição deles, e a separação não prova que ela seja completa.

Os verbos formam uma lista fechada **de propósito**: são uns 35 —
`resolver`/`solve`, `avaliar`/`evaluate`, `simplificar`/`simplify`,
`separar`/`separate`, `conferir`/`check`, `contrair`/`contract`,
`provar`/`prove`, `exportar`/`export`, `latex`, … —, e o manual traz todos.
Se aqui se pudesse escrever Python, a ponte que este programa é deixaria de ser
obrigatória — quem escreve `sympy.solve(...)` fala direto com o SymPy, sem
sítios, sem convenção declarada, sem proveniência, e sobra um Jupyter com
passos a mais.

`resolver` é um verbo só, e o objeto decide a conta — **três** contas agora:

| a incógnita | o solver |
|---|---|
| `y(x)` | `dsolve`, conferido com `checkodesol` |
| `u(t,x)` | `pdsolve`, conferido com `checkpdesol` |
| sem derivada | `solve` |

Com `u = u(t,x)` e `A = A(t)` declaradas, `∂u/∂t = A u` sai como
`F(x)·exp(∫A dt)`: numa EDP, a "constante" de
integração é uma função arbitrária da outra variável. O `pdsolve` resolve bem
menos do que o `dsolve` — a equação da onda ele não resolve —, mas resolver
pouco não é resolver nada, e quem decide se o pouco serve é quem escreveu a
equação.

Equação diferencial vai para o módulo que confere a solução por substituição,
algébrica vai para o `solve`. Obrigar o usuário a escolher entre `solve` e `dsolve` é pedir que ele
classifique a própria equação para o programa — ao contrário.

As convenções valem para o caderno inteiro, e mudar uma **refaz tudo**: o que
já estava escrito passa a significar outra coisa, e mostrar as duas leituras ao
mesmo tempo seria mostrar duas matemáticas.

### Mais de uma instrução por célula

`Enter` quebra linha, `Shift+Enter` roda. Uma célula aceita várias instruções,
uma por linha:

```
contrair(eq1)
avaliar(eq1)
```

Só encadeia quando **todas** as linhas são instrução reconhecida — comando ou
declaração. Uma equação em LaTeX pode legitimamente ocupar duas linhas, e
parti-la daria duas metades sem sentido no lugar de um erro, que é o tipo de
silêncio que este programa existe para não produzir.

## O verbo segue o objeto

Equação diferencial se **resolve**; expressão se **avalia**. São contas
diferentes, e o botão principal da página muda de nome conforme o que está
escrito — oferecer o verbo errado faz o usuário concluir que o programa não
sabe fazer o que ele sabe fazer.

## Ler e avaliar são atos diferentes

`\int_0^1 x^2` é lido como `Integral(x**2, (x, 0, 1))` e fica assim: parada. O
Sucuri lê; a conta é outro ato, e por isso é um botão — **Avaliar** — e não um
efeito de digitar.

A resposta vem com o nome do que ela é:

| | |
|---|---|
| fechou | `1/3`, e a aproximação `≈ 0,333…` **ao lado**, nunca no lugar |
| indefinida | `-\cos(x) + C` — a resposta é a família, não um representante dela |
| não fechou | o SymPy devolveu a conta por fazer, e o rótulo diz isso |
| não terminou | estourou o prazo |

Tratar as três como a mesma coisa é o erro de sempre. E sítio pendente bloqueia
a avaliação como bloqueia a leitura: nada se calcula sobre o que ninguém leu.

## Módulos de domínio

O Sucuri lê e desambigua; ele não sabe teoria de Galois nem geometria
diferencial. O que dá utilidade a uma expressão vem de módulos, que oferecem
operações e devolvem **resultados que não são expressões** — tabelas, vereditos,
certificados. É a diferença entre hospedar calculadoras e hospedar áreas da
matemática.

```python
import sucuri
import sucuri.modules

doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
e = doc.read(r"y'' = x y")            # Airy

resolver = sucuri.modules.load("resolver")
resolver.operations["resolver"].run(e)
# solução  [estabelecida]
#   y{\left(x \right)} = C_{1} Ai\left(x\right) + C_{2} Bi\left(x\right)
#   …
#   conferência | substituída na equação: resto 0

korvin = sucuri.modules.load("korvin")    # só com o KORVIN instalado
korvin.operations["não-integrabilidade"].run(e)
```

O `resolver` acompanha o Sucuri. O `korvin` é um adaptador: só se ativa com o
pacote KORVIN, que é externo e não vai junto (sem ele, `load("korvin")` falha
com `ModuleNotFoundError`, e a interface anuncia o módulo como indisponível).
Ver `exemplos/modulo_korvin.py`. Os dois respondem a perguntas diferentes:

| | pergunta |
|---|---|
| `resolver` | consigo achar uma solução? |
| `korvin` | existe uma? |

O `resolver` embrulha o `dsolve` para dizer o que ele não diz: **que tipo de
resposta é**. Forma fechada conferida por substituição, série truncada (que não
é solução, é aproximação até uma ordem), relação implícita, ou nada — e quando
é nada, que não achar não prova que não há.

```
y'' + y = 0          solução                        [estabelecida]
y'' = x y            solução                        [estabelecida]
y'' + x y' + y = 0   série (não é solução fechada)   [não aplicável]
y'' = 6 y^2          sem solução encontrada          [não aplicável]
y' = 1/(x + y^2)     solução não confirmada          [sem fonte]
```

A terceira linha é o motivo de o módulo existir: essa equação é `(y' + xy)' = 0`
e **tem** forma fechada, com `erfi` — o `dsolve` devolve uma série até ordem 5 e
não avisa que mudou de tipo de resposta.

### A ponte de proveniência

Toda conclusão de módulo carrega a origem do critério que a produziu, e o
hospedeiro **recusa-se a apresentar como conclusão** o que vier de critério sem
autoridade:

```
esquema de Riemann              [não aplicável]     → é dado, não afirma nada
condições necessárias           [estabelecida]      → fonte primária (Kovacic §2)
não-integrabilidade             [sem fonte]         → NÃO APRESENTÁVEL
  bloqueio: o critério 'potência simétrica com solução racional' não tem
            proveniência declarada e por isso não emite veredito
```

O Sucuri não entende uma linha de teoria de Galois. Não precisa: basta o módulo
declarar de onde vem o que afirma. É a mesma regra que o Sucuri já aplica à
leitura — nada se apresenta com mais confiança do que a sua origem sustenta.

## Identidade visual

Em `identidade/`: marca e variantes, ícones de 48 a 1024 px, tokens em CSS e o
mockup de referência. Ver `identidade/IDENTIDADE.md`.

A marca é a sucuri enrolada formando a letra S — entra notação pela cabeça, sai
código pelo bloco da cauda.

## Estado

Motor e interface em construção. Ver `sucuri/`, `sucuri/interface/` e a suíte
em `tests/`.

## Licença

MIT — ver `LICENSE`.

## Como citar

Ver `CITATION.cff`. Um DOI será acrescentado.
