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

## As tabelas

`exemplos/tabelas/` põe o leitor contra tabelas reais, baixadas da Wikipédia —
notação escrita por outra gente, para outro fim, que é o único teste honesto de
um leitor de notação.

```bash
python exemplos/tabelas/derivadas.py
python exemplos/tabelas/integrais.py
```

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
doc.read(r"\partial_t u = k \partial_x u")
doc.read(r"\frac{\partial u}{\partial t} = k \frac{\partial^2 u}{\partial x^2}")
# Eq(Derivative(u(t, x), t), k*Derivative(u(t, x), (x, 2)))
```

O `u` é **um só**, função das duas. Antes cada sítio promovia o símbolo à sua
própria função e o mesmo `u` saía como `u(t)` de um lado e `u(x)` do outro —
duas funções com o mesmo nome na mesma equação, em silêncio.

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
que permite à interface pintar de âmbar o que veio de convenção:

```
igualdade
  soma
    potência
      função varphi aplicada a (x)
    produto
      número 3
      derivada de ordem 1 de varphi em x  [inferida]  <- conferir
      função varphi aplicada a (x)
    derivada de ordem 2 de varphi em x    [inferida]  <- conferir
  soma
    produto
      número 2
      derivada de ordem 1 de r em x       [explícita]
    ...
```

Derivadas são folhas na leitura do usuário: quem lê quer ver "derivada segunda
de φ", não a árvore interna dela. `to_dict()` serializa para a interface web.

## Uso

```python
import sucuri

# caso avulso — sem convenção, RECUSA, que é o padrão
e = sucuri.parse(r"\varphi'' + \varphi' = r")
e.questions()                      # as perguntas, em vez de um palpite

# com a convenção declarada
e = sucuri.parse(r"\varphi'' + \varphi' = r",
                 independent_variable='x', primes='derivative')
e.to_sympy()
e.inferred                         # o que veio de convenção e pede conferência

# trabalho continuado: o documento guarda convenções e anotações
doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
doc.annotate("prime", "r", "derivative", order=1)
doc.read(...).tree()
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
(`/api/ler`, `/api/anotar`, `/api/modulos`, `/api/operar`), e as duas únicas
decisões que ela transporta são as do usuário: convenção e anotação.

## O caderno

```bash
python -m sucuri.interface        # e clique em "caderno" no cabeçalho
```

Uma equação por página serve para inspecionar notação; trabalho é escrever uma
coisa, olhar, escrever outra que usa a primeira.

```
        f^{\prime} = x^2          Shift+Enter   →  eq1,  df/dx = x²
        resolver(eq1)                          →  f(x) = C₁ + x³/3
                                                  conferência: resto 0
        exportar(eq1)                          →  o script que roda sem o Sucuri
```

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

Os verbos são poucos e fechados **de propósito**: `resolver`/`solve`,
`avaliar`/`evaluate`, `simplificar`/`simplify`, `exportar`/`export`, `latex`.
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

`∂u/∂t = A(t)u` sai como `F(x)·exp(∫A dt)`: numa EDP, a "constante" de
integração é uma função arbitrária da outra variável. O `pdsolve` resolve bem
menos do que o `dsolve` — a equação da onda ele não resolve —, mas resolver
pouco não é resolver nada, e quem decide se o pouco serve é quem escreveu a
equação.

Antes: equação diferencial vai
para o módulo que confere a solução por substituição, algébrica vai para o
`solve`. Obrigar o usuário a escolher entre `solve` e `dsolve` é pedir que ele
classifique a própria equação para o programa — ao contrário.

As convenções valem para o caderno inteiro, e mudar uma **refaz tudo**: o que
já estava escrito passa a significar outra coisa, e mostrar as duas leituras ao
mesmo tempo seria mostrar duas matemáticas.

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
e = doc.read(r"y'' = x y")            # Airy
korvin = sucuri.modules.load("korvin")
korvin.operations["não-integrabilidade"].run(e)
```

Dois módulos acompanham o Sucuri, e respondem a perguntas diferentes:

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
