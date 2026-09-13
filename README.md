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

## Identidade visual

Em `identidade/`: marca e variantes, ícones de 48 a 1024 px, tokens em CSS e o
mockup de referência. Ver `identidade/IDENTIDADE.md`.

A marca é a sucuri enrolada formando a letra S — entra notação pela cabeça, sai
código pelo bloco da cauda.

## Estado

Motor em construção. Ver `sucuri/` e a suíte em `tests/`.
