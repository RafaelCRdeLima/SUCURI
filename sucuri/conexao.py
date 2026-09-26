r"""A conexão sem índice: ∇_U X, [U,X] e R(U,X)W.

O parser do SymPy lê `\nabla_U X` como `X*nabla_{U}` — um símbolo chamado
"nabla_{U}" multiplicando X. Bem formado e falso, e falso do pior jeito: o
produto comuta, então ∇_U∇_X Y e ∇_X∇_U Y saem iguais, e a curvatura, que é
exatamente a diferença entre os dois, some sem aviso. `[U,X]` ele recusa, e
`R(U,X)W` vira a pergunta de sempre: R aplicada, ou R vezes o parêntese?

## O que decide a leitura

Nada na tipografia. `\nabla_U X` e `\nabla_\mu X^\nu` se escrevem igual — ∇ com
um subscrito —, e no Wald a letra latina do subscrito É índice. `[a,b]` é
colchete de Lie, comutador, intervalo ou par. Quem decide é a DECLARAÇÃO, como
em todo o resto:

    U, X = tensor(1,0)   (uma declaração por nome)
    R = curvatura

    \nabla_U X        →  ∇_U X, a derivada na direção de U
    [U, X]            →  o colchete de Lie de dois vetores
    R(U,X)W           →  o operador de curvatura aplicado a W

Um vetor escrito sem índice só pode ser o objeto abstrato. Entre dois vetores,
o colchete só pode ser o de Lie. E R declarada curvatura não multiplica
parêntese nenhum.

Onde a declaração não licencia — subscrito sem declaração, colchete de coisas
que não são vetores, curvatura agindo sobre um não-vetor —, recusa: montar o
objeto mesmo assim seria o erro silencioso de sempre.

## O que a leitura NÃO fixa

O sinal e a ordem dos argumentos de R. `R(U,X) = ∇_U∇_X − ∇_X∇_U − ∇_[U,X]` é
a convenção do MTW; há livros com o sinal trocado e com os argumentos na outra
ordem. Para LER `R(U,X)W` isso não importa — é o mesmo objeto escrito. Importa
para CALCULAR, e aí a definição terá de ser declarada, não suposta.

## O operando

É o que vem logo depois: uma letra, um grupo entre parênteses ou chaves, um
colchete, ou outro operador — `\nabla_U \nabla_U X` é ∇_U(∇_U X). Onde o
alcance não é evidente (`\nabla_U X^\mu`, `\nabla_U X_1`), recusa: escolher
até onde o operador alcança seria decidir por quem escreveu.
"""

from __future__ import annotations

import re

import sympy as sp

VETOR = (1, 0)
"""O tipo do Schutz de um vetor: recebe uma 1-forma, nenhum vetor."""

_RE_NABLA = re.compile(
    r"(?:\\(?P<acento>tilde|hat|bar|widetilde|widehat|overline)\s*"
    r"(?:\{\s*\\nabla\s*\}|\\nabla(?![a-zA-Z]))|\\nabla(?![a-zA-Z]))\s*_\s*")
_ACENTOS = {"widetilde": "tilde", "widehat": "hat", "overline": "bar"}
_RE_MACRO = re.compile(r"\\([a-zA-Z]+)")
_RE_LETRA = re.compile(r"[A-Za-z]")
_RE_NOME = re.compile(r"^\\?[A-Za-z]+$")


# ----------------------------------------------------------- os objetos

class DerivadaCovariante(sp.Function):
    """∇_U X — a derivada de X na direção do campo U.

    Função de dois argumentos, e não produto: a ordem de aplicação fica na
    ESTRUTURA da árvore, que é onde o SymPy não pode reordená-la.

    Um terceiro argumento, o acento, distingue outra conexão: ∇̃ = \tilde\nabla
    é uma conexão qualquer, que só compartilha com ∇ as regras que valem para
    toda conexão.
    """

    nargs = (2, 3)

    @property
    def direcao(self):
        return self.args[0]

    @property
    def operando(self):
        return self.args[1]

    @property
    def acento(self):
        return self.args[2].name if len(self.args) == 3 else None

    def com(self, direcao, operando):
        """A mesma conexão, noutros argumentos."""
        return type(self)(direcao, operando, *self.args[2:])

    def _latex(self, printer):
        direcao = printer._print(self.direcao)
        nabla = rf"\{self.acento}{{\nabla}}" if self.acento else r"\nabla"
        return rf"{nabla}_{{{direcao}}} {_envolto(printer, self.operando)}"

    def _sympystr(self, printer):
        nabla = f"{self.acento}_nabla" if self.acento else "nabla"
        return (f"{nabla}_{_str_direcao(printer, self.direcao)}"
                f"({printer._print(self.operando)})")


class ColcheteDeLie(sp.Function):
    """[U, X] — o colchete de Lie de dois campos vetoriais.

    Não é comutador de números nem par ordenado: a leitura só existe entre
    vetores declarados, e é essa condição que a torna a única possível.
    """

    nargs = 2

    def _latex(self, printer):
        a, b = (printer._print(x) for x in self.args)
        return rf"\left[{a}, {b}\right]"

    def _sympystr(self, printer):
        a, b = (printer._print(x) for x in self.args)
        return f"[{a}, {b}]"


class Curvatura(sp.Function):
    """R(U,X)W — o operador de curvatura R(U,X) aplicado ao vetor W.

    O primeiro argumento é o NOME declarado (R, Ω, o que for): o objeto guarda
    quem é a curvatura, e não só que há uma.
    """

    nargs = 4

    @property
    def nome(self):
        return self.args[0]

    def _latex(self, printer):
        r, u, x = (printer._print(a) for a in self.args[:3])
        return rf"{r}\left({u}, {x}\right) {_envolto(printer, self.args[3])}"

    def _sympystr(self, printer):
        r, u, x, w = (printer._print(a) for a in self.args)
        return f"{r}({u}, {x})({w})"


class Direcional(sp.Function):
    """U(f) — a derivada da função escalar f na direção do campo U.

    É ∇_U f quando f é escalar, e é um ESCALAR: entra como coeficiente, não
    como termo. Imprime `U(f)` no texto e `\\nabla_{U} f` em LaTeX, porque a
    segunda relida é a mesma coisa e a primeira é uma pergunta — U aplicado a
    f, ou U vezes f?
    """

    nargs = 2

    @property
    def direcao(self):
        return self.args[0]

    @property
    def escalar(self):
        return self.args[1]

    def _latex(self, printer):
        direcao = printer._print(self.direcao)
        return rf"\nabla_{{{direcao}}} {_envolto(printer, self.escalar)}"

    def _sympystr(self, printer):
        return (f"{_str_direcao(printer, self.direcao)}"
                f"({printer._print(self.escalar)})")


class Avaliado(sp.Function):
    """ω(U), T(U, X) — um tensor do tipo (0,n) com os n slots preenchidos.

    É a notação do Schutz: um (0,n) é uma função de n vetores, e com todos
    eles dados o resultado é um número em cada ponto — um ESCALAR. O primeiro
    argumento é o nome do tensor.
    """

    @property
    def nome(self):
        return self.args[0]

    @property
    def slots(self):
        return self.args[1:]

    def _latex(self, printer):
        slots = ", ".join(printer._print(a) for a in self.slots)
        return rf"{printer._print(self.nome)}\left({slots}\right)"

    def _sympystr(self, printer):
        slots = ", ".join(printer._print(a) for a in self.slots)
        return f"{printer._print(self.nome)}({slots})"


class AvaliadoSimetrico(Avaliado):
    """T(X, Y) com T declarado simétrico: T(X,Y) = T(Y,X)."""


class AvaliadoAntissimetrico(Avaliado):
    """F(X, Y) com F declarado antissimétrico: F(X,Y) = −F(Y,X), F(X,X) = 0."""


class AvaliadoRiemann(Avaliado):
    """R(X, Y, Z, W) com as simetrias do Riemann (0,4): antissimétrico em
    (X,Y) e em (Z,W), simétrico na troca dos pares."""


class Metrica(AvaliadoSimetrico):
    """g(X, Y) — a métrica: um (0,2) que é SIMÉTRICO.

    A simetria não é convenção de livro: é o que se chama de métrica. Por
    isso é do objeto, e o motor a usa sem hipótese.
    """


def _envolto(printer, operando):
    dentro = printer._print(operando)
    if isinstance(operando, (sp.Add, sp.Mul)):
        return rf"\left({dentro}\right)"
    return dentro


def _str_direcao(printer, direcao):
    texto = printer._print(direcao)
    return texto if isinstance(direcao, sp.Symbol) else "{" + texto + "}"


class ParaTodo(sp.Basic):
    """∀A, B: corpo — a equação vale para quaisquer campos vetoriais A, B.

    A diferença para a mesma equação sem ∀ é o que a prova pode fazer com ela:
    sem ∀, `R(U,X)W = …` fala daqueles U, X, W; com ∀, de todos, e a prova a
    instancia onde precisar.
    """

    @property
    def variaveis(self):
        return tuple(self.args[0])

    @property
    def corpo(self):
        return self.args[1]

    def _latex(self, printer):
        nomes = ", ".join(printer._print(v) for v in self.variaveis)
        return rf"\forall {nomes}:\; {printer._print(self.corpo)}"

    def _sympystr(self, printer):
        nomes = ", ".join(printer._print(v) for v in self.variaveis)
        return f"para_todo({nomes}: {printer._print(self.corpo)})"


_RE_FORALL = re.compile(
    r"^\s*\\forall(?![a-zA-Z])\s*"
    r"((?:\\?[A-Za-z]+)(?:\s*,\s*\\?[A-Za-z]+)*)"
    r"\s*(?::|\\colon(?![a-zA-Z])|\\quad(?![a-zA-Z])|\\;|\\,)")


def quantificador(latex):
    """(nomes ligados, texto com o prefixo trocado por espaços).

    `\\forall A, B, W: …`. O separador é obrigatório — dois-pontos, `\\colon`,
    `\\quad`, `\\;` ou `\\,` —, porque sem ele não se sabe onde acaba a lista:
    em `\\forall W, R(U,X)W = …` a vírgula separa nome ou encerra a lista?
    """
    m = _RE_FORALL.match(latex or "")
    if not m:
        return [], latex
    nomes = [_limpo(n.strip()) for n in m.group(1).split(",")]
    return nomes, " " * m.end() + latex[m.end():]


class ConexaoNaoLida(Exception):
    """∇, colchete ou curvatura que a declaração não licencia.

    Sem esta recusa, o parser devolve um símbolo "nabla_{U}" que comuta com
    tudo — e a conta segue.
    """

    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


# ------------------------------------------------------------ o que é vetor

def e_vetor(expr, tensores):
    """O objeto é um campo vetorial, pelo que foi declarado?

    Soma de vetores é vetor; escalar vezes vetor é vetor; ∇_U de um vetor é
    vetor; colchete e curvatura aplicada são vetores por construção.
    """
    if isinstance(expr, sp.Symbol):
        return tensores.get(expr.name) == VETOR
    if isinstance(expr, DerivadaCovariante):
        return e_vetor(expr.operando, tensores)
    if isinstance(expr, (ColcheteDeLie, Curvatura)):
        return True
    if isinstance(expr, sp.Add):
        return all(e_vetor(a, tensores) for a in expr.args)
    if isinstance(expr, sp.Mul):
        vetores = [a for a in expr.args if e_vetor(a, tensores)]
        escalares = [a for a in expr.args if a not in vetores]
        return len(vetores) == 1 and not any(
            _tem_tensor(a, tensores) for a in escalares)
    return False


def tem_tensor(expr, tensores):
    """Há algo tensorial em `expr` — fora de uma derivada direcional?

    U(f) tem U dentro e é escalar: o U ali é a direção, não um fator.
    """
    if isinstance(expr, (Direcional, Avaliado)):
        return False
    if isinstance(expr, (DerivadaCovariante, ColcheteDeLie, Curvatura)):
        return True
    if isinstance(expr, sp.Symbol):
        return expr.name in tensores
    return any(tem_tensor(a, tensores) for a in expr.args)


_tem_tensor = tem_tensor


def exigir_vetor(expr, papel, tensores, senao=""):
    """Recusa, com o motivo, se `expr` não é vetor declarado.

    `senao` é a outra leitura que a declaração decidiria — índice, para o
    subscrito de ∇; comutador ou intervalo, para o colchete.
    """
    if e_vetor(expr, tensores):
        return
    if isinstance(expr, sp.Symbol):
        nome = expr.name
        tipo = tensores.get(nome)
        if tipo is None:
            raise ConexaoNaoLida(
                f"{papel}: '{nome}' não foi declarado. Se é um vetor, declare "
                f"{nome} = tensor(1,0){senao.format(nome=nome)}")
        raise ConexaoNaoLida(
            f"{papel}: '{nome}' foi declarado do tipo ({tipo[0]},{tipo[1]}), "
            f"e aqui é preciso um VETOR, do tipo (1,0)")
    raise ConexaoNaoLida(
        f"{papel}: '{expr}' não é vetor pelo que foi declarado")


# -------------------------------------------------------- onde estão no texto

class Ocorrencia:
    """Um operador no texto: de que espécie, onde está, e o que ele engole.

    `fim_cabeca` marca onde acaba a parte que não é argumento — o subscrito de
    ∇, o nome da curvatura. Um sítio de justaposição que comece ali é falso: em
    `\\nabla_U (X+Y)` o U não é função, e em `R(U,X)W` o R não multiplica.
    """

    def __init__(self, especie, ini, fim_cabeca, fim, partes, problema=None):
        self.especie = especie              # 'nabla', 'colchete', 'curvatura'
        self.ini = ini
        self.fim_cabeca = fim_cabeca
        self.fim = fim
        self.partes = partes                # LaTeX de cada argumento
        self.problema = problema            # None, ou o motivo da recusa

    @property
    def span(self):
        return self.ini, self.fim


def _grupo(texto, i, abre, fecha):
    """Fim (exclusivo) do grupo que abre em `i`, ou None se não fecha."""
    fundo = 0
    for j in range(i, len(texto)):
        if texto[j] == abre:
            fundo += 1
        elif texto[j] == fecha:
            fundo -= 1
            if fundo == 0:
                return j + 1
    return None


def _virgulas(texto):
    """Separa por vírgula de primeiro nível."""
    pedacos, atual, fundo = [], [], 0
    for c in texto:
        if c in "({[":
            fundo += 1
        elif c in ")}]":
            fundo -= 1
        if c == "," and fundo == 0:
            pedacos.append("".join(atual).strip())
            atual = []
        else:
            atual.append(c)
    pedacos.append("".join(atual).strip())
    return pedacos


def _limpo(nome):
    return nome[1:] if nome and nome.startswith("\\") else nome


def _cabeca_curvatura(nome):
    """A regex de `R(` para a curvatura declarada `nome`."""
    if len(nome) == 1:
        return re.compile(rf"(?<![A-Za-z\\]){re.escape(nome)}\s*\(")
    return re.compile(rf"\\{re.escape(nome)}(?![a-zA-Z])\s*\(")


class _Leitor:
    def __init__(self, texto, indices, curvaturas, formas=None):
        self.texto = texto
        self.indices = set(indices)
        self.curvaturas = [(n, _cabeca_curvatura(n)) for n in curvaturas]
        # nome -> (quantos slots, é a métrica?, simetria)
        self.formas = [(n, _cabeca_curvatura(n), k, metrica, simetria)
                       for n, (k, metrica, simetria) in (formas or {}).items()]

    # O que começa em i, se for operador nosso.
    def em(self, i):
        t = self.texto
        if _RE_NABLA.match(t, i):
            return self.nabla(i)
        for nome, regra in self.curvaturas:
            m = regra.match(t, i)
            if m and (i == 0 or not re.match(r"[A-Za-z\\]", t[i - 1])):
                return self.curvatura(i, m, nome)
        for nome, regra, k, metrica, simetria in self.formas:
            m = regra.match(t, i)
            if m and (i == 0 or not re.match(r"[A-Za-z\\]", t[i - 1])):
                return self.avaliado(i, m, nome, k, metrica, simetria)
        if t.startswith("[", i):
            return self.colchete(i)
        return None

    def nabla(self, i):
        m = _RE_NABLA.match(self.texto, i)
        direcao, fim_direcao = self._direcao(m.end())
        if direcao is not None and _limpo(direcao) in self.indices:
            return None                     # ∇_μ: é da ponte tensorial
        operando, fim, problema = self._operando(fim_direcao)
        if direcao is None:
            problema = "∇ com subscrito vazio"
        acento = m.group("acento")
        return Ocorrencia("nabla", i, fim_direcao, fim,
                          {"direcao": direcao, "operando": operando,
                           "acento": _ACENTOS.get(acento, acento)}, problema)

    def colchete(self, i):
        fim = _grupo(self.texto, i, "[", "]")
        if fim is None:
            return None
        partes = _virgulas(self.texto[i + 1:fim - 1])
        if len(partes) == 1:
            return None                     # [x+1]^2: é agrupamento
        problema = None
        if len(partes) != 2 or not all(partes):
            problema = (f"colchete com {len(partes)} entradas: o de Lie tem "
                        f"duas, [U, X]")
        return Ocorrencia("colchete", i, i, fim, {"args": partes}, problema)

    def curvatura(self, i, m, nome):
        abre = m.end() - 1
        fecha = _grupo(self.texto, abre, "(", ")")
        if fecha is None:
            return Ocorrencia("curvatura", i, abre, len(self.texto), {},
                              f"'{nome}(' sem ')'")
        args = _virgulas(self.texto[abre + 1:fecha - 1])
        operando, fim, problema = self._operando(fecha, quem=f"{nome}(…)")
        if len(args) != 2 or not all(args):
            problema = (f"{nome} foi declarada curvatura, e R(U,X) recebe dois "
                        f"vetores; aqui há {len(args)}")
        elif operando is None and problema and "sem operando" in problema:
            problema = (f"{nome}({', '.join(args)}) sem o vetor sobre o qual "
                        f"age: R(U,X) é um operador, e sozinho não é vetor")
        return Ocorrencia("curvatura", i, abre, fim,
                          {"nome": nome, "args": args, "operando": operando},
                          problema)

    def avaliado(self, i, m, nome, k, metrica, simetria=None):
        abre = m.end() - 1
        fecha = _grupo(self.texto, abre, "(", ")")
        if fecha is None:
            return Ocorrencia("avaliado", i, abre, len(self.texto), {},
                              f"'{nome}(' sem ')'")
        args = _virgulas(self.texto[abre + 1:fecha - 1])
        problema = None
        if len(args) != k or not all(args):
            quem = "a métrica" if metrica else f"do tipo (0,{k})"
            problema = (f"{nome} é {quem}, e recebe {k} vetor(es); aqui "
                        f"recebe {len(args)}")
        return Ocorrencia("avaliado", i, abre, fecha,
                          {"nome": nome, "args": args, "metrica": metrica,
                           "simetria": simetria},
                          problema)

    def _direcao(self, i):
        """(latex, fim) do subscrito que começa em `i`."""
        t = self.texto
        if t.startswith("{", i):
            fim = _grupo(t, i, "{", "}")
            if fim is None:
                return None, len(t)
            return t[i + 1:fim - 1].strip() or None, fim
        m = _RE_MACRO.match(t, i)
        if m:
            return m.group(0), m.end()
        if i < len(t) and _RE_LETRA.match(t, i):
            return t[i], i + 1
        return None, i

    def _operando(self, i, quem="∇_U"):
        """(latex, fim, problema) do que o operador alcança a partir de `i`."""
        t = self.texto
        while i < len(t) and t[i].isspace():
            i += 1
        if i >= len(t) or t[i] in "=+-)}],":
            return None, i, f"{quem} sem operando: falta sobre o que age"

        interno = self.em(i)
        if interno is not None:
            return t[i:interno.fim], interno.fim, None

        for abre, fecha in (("(", ")"), ("{", "}")):
            if t[i] == abre:
                fim = _grupo(t, i, abre, fecha)
                if fim is None:
                    return None, len(t), f"'{abre}' sem '{fecha}' depois de {quem}"
                return t[i + 1:fim - 1], fim, None
        if t.startswith(r"\left(", i):
            fim = t.find(r"\right)", i)
            if fim < 0:
                return None, len(t), rf"'\left(' sem '\right)' depois de {quem}"
            return t[i + 6:fim], fim + 7, None

        m = _RE_MACRO.match(t, i) or _RE_LETRA.match(t, i)
        if not m:
            return None, i + 1, (f"o que vem depois de {quem} não é um operando "
                                 f"reconhecível")
        fim = m.end()
        resto = t[fim:].lstrip()
        if resto[:1] in ("_", "^", "(", "'"):
            return None, fim, (
                f"não está claro até onde {quem} alcança em "
                f"'{t[i:fim]}{resto[:1]}…': escreva o operando entre "
                f"parênteses, {quem} ( … )")
        return m.group(0), fim, None


def localizar(texto, indices=(), curvaturas=(), formas=None):
    """Os operadores de primeiro nível do texto, na ordem em que aparecem.

    Os que estão DENTRO de outro — o ∇ interno de ∇_U∇_U X, o colchete em
    ∇_{[U,X]} — ficam para a leitura recursiva do pedaço que os contém.
    `\\nabla_\\mu` fica de fora: é da ponte tensorial, com a sua própria recusa.
    """
    leitor = _Leitor(texto, indices, curvaturas, formas)
    achados, i = [], 0
    while i < len(texto):
        oc = leitor.em(i)
        if oc is None:
            i += 1
            continue
        achados.append(oc)
        i = max(oc.fim, i + 1)
    return achados


def cabecas(texto, indices=(), curvaturas=(), formas=None):
    """As posições que são cabeça de operador — em QUALQUER nível.

    `localizar` devolve só os de primeiro nível, porque os de dentro são lidos
    pela recursão. Mas a pergunta de justaposição é feita sobre o texto
    inteiro: o `g(` de `\\nabla_U (g(X,Y))` também não é pergunta.
    """
    leitor = _Leitor(texto, indices, curvaturas, formas)
    posicoes = set()
    for i in range(len(texto)):
        oc = leitor.em(i)
        if oc is not None:
            posicoes |= set(range(oc.ini, max(oc.fim_cabeca, oc.ini + 1)))
    return posicoes


def construir(oc, ler, tensores):
    """O objeto SymPy da ocorrência; `ler` lê um pedaço de LaTeX.

    A exigência de vetor vem DEPOIS da leitura, porque só lido se sabe o que um
    pedaço é: `U + X` é vetor, `f` não, `\\nabla_U X` é se X for.
    """
    p = oc.partes
    if oc.especie == "nabla":
        direcao = ler(p["direcao"])
        exigir_vetor(direcao, f"∇_{p['direcao']}", tensores,
                     "; se é índice, declare {nome} = índice. A tipografia é "
                     "a mesma, e escolher entre as duas seria adivinhar")
        operando = ler(p["operando"])
        if p.get("acento"):
            if not tem_tensor(operando, tensores):
                return Direcional(direcao, operando)     # toda conexão: ∇̃_U f = U(f)
            return DerivadaCovariante(direcao, operando, sp.Symbol(p["acento"]))
        if not tem_tensor(operando, tensores):
            # ∇_U f com f escalar é a derivada direcional U(f): um escalar, e
            # não um campo — o motor precisa saber a diferença.
            return Direcional(direcao, operando)
        return DerivadaCovariante(direcao, operando)
    if oc.especie == "avaliado":
        nome = p["nome"]
        slots = [ler(a) for a in p["args"]]
        for a, escrito in zip(slots, p["args"]):
            exigir_vetor(a, f"{nome}({', '.join(p['args'])})", tensores)
        classe = (Metrica if p["metrica"]
                  else AvaliadoSimetrico if p.get("simetria") == "simetrico"
                  else AvaliadoAntissimetrico if p.get("simetria") == "antissimetrico"
                  else AvaliadoRiemann if p.get("simetria") == "riemann"
                  else Avaliado)
        return classe(sp.Symbol(nome), *slots)
    if oc.especie == "colchete":
        a, b = (ler(x) for x in p["args"])
        papel = f"[{p['args'][0]}, {p['args'][1]}]"
        senao = (". Entre outras coisas o colchete é comutador, intervalo ou "
                 "par, e escolher seria adivinhar")
        exigir_vetor(a, papel, tensores, senao)
        exigir_vetor(b, papel, tensores, senao)
        return ColcheteDeLie(a, b)
    nome = p["nome"]
    u, x = (ler(a) for a in p["args"])
    w = ler(p["operando"])
    papel = f"{nome}({p['args'][0]}, {p['args'][1]})"
    exigir_vetor(u, papel, tensores)
    exigir_vetor(x, papel, tensores)
    exigir_vetor(w, f"{papel} agindo sobre {p['operando']}", tensores)
    return Curvatura(sp.Symbol(nome), u, x, w)
