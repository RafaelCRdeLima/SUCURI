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
