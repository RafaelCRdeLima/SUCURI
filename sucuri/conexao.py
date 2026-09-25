r"""A derivada covariante sem índice: ∇_U X.

O parser do SymPy lê `\nabla_U X` como `X*nabla_{U}` — um símbolo chamado
"nabla_{U}" multiplicando X. Bem formado e falso, e falso do pior jeito: o
produto comuta, então ∇_U∇_X Y e ∇_X∇_U Y saem iguais, e a curvatura, que é
exatamente a diferença entre os dois, some sem aviso.

## O que decide a leitura

Nada na tipografia. `\nabla_U X` e `\nabla_\mu X^\nu` se escrevem igual — ∇ com
um subscrito —, e no Wald a letra latina do subscrito É índice. Quem decide é a
DECLARAÇÃO, como em todo o resto:

    U = tensor(1,0)
    \nabla_U X        →  ∇_U X, a derivada na direção de U

Um vetor escrito sem índice só pode ser o objeto abstrato, e não há derivada
"na direção" de um índice. Declarado, o subscrito deixa de ter duas leituras.

Sem declaração, recusa. Com o subscrito declarado de outro tipo — uma 1-forma,
um (0,2) —, recusa também: derivar na direção de algo que não é vetor não é
definido, e montar o objeto mesmo assim seria o erro silencioso de sempre.

## O operando

É o que vem logo depois: uma letra, um grupo entre parênteses ou chaves, ou
outra derivada covariante — `\nabla_U \nabla_U X` é ∇_U(∇_U X). Onde o alcance
não é evidente (`\nabla_U X^\mu`, `\nabla_U X_1`), recusa: escolher até onde
o operador alcança seria decidir por quem escreveu.
"""

from __future__ import annotations

import re

import sympy as sp

VETOR = (1, 0)
"""O tipo do Schutz de um vetor: recebe uma 1-forma, nenhum vetor."""

_RE_NABLA = re.compile(r"\\nabla(?![a-zA-Z])\s*_\s*")
_RE_MACRO = re.compile(r"\\([a-zA-Z]+)")
_RE_LETRA = re.compile(r"[A-Za-z]")


class DerivadaCovariante(sp.Function):
    """∇_U X — a derivada de X na direção do campo U.

    Função de dois argumentos, e não produto: a ordem de aplicação fica na
    ESTRUTURA da árvore, que é onde o SymPy não pode reordená-la.
    """

    nargs = 2

    @property
    def direcao(self):
        return self.args[0]

    @property
    def operando(self):
        return self.args[1]

    def _latex(self, printer):
        dentro = printer._print(self.operando)
        if isinstance(self.operando, (sp.Add, sp.Mul)):
            dentro = rf"\left({dentro}\right)"
        return rf"\nabla_{{{printer._print(self.direcao)}}} {dentro}"

    def _sympystr(self, printer):
        return f"nabla_{printer._print(self.direcao)}({printer._print(self.operando)})"


class DerivadaCovarianteNaoLida(Exception):
    """∇ com subscrito que a declaração não licencia.

    Sem esta recusa, o parser devolve um símbolo "nabla_{U}" que comuta com
    tudo — e a conta segue.
    """

    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


class Ocorrencia:
    """Um `\\nabla_U …` no texto: onde está, e se a declaração o licencia."""

    def __init__(self, ini, fim_direcao, fim, direcao, operando, problema):
        self.ini = ini
        self.fim_direcao = fim_direcao      # onde acaba o subscrito
        self.fim = fim
        self.direcao = direcao              # 'U', sem a barra
        self.operando = operando            # LaTeX do operando
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


def _direcao(texto, i):
    """(nome, fim) do subscrito que começa em `i`."""
    if texto.startswith("{", i):
        fim = _grupo(texto, i, "{", "}")
        if fim is None:
            return None, len(texto)
        return texto[i + 1:fim - 1].strip(), fim
    m = _RE_MACRO.match(texto, i)
    if m:
        return m.group(0), m.end()
    if i < len(texto):
        return texto[i], i + 1
    return None, i


def _operando(texto, i):
    """(latex, fim, problema) do que ∇_U alcança a partir de `i`."""
    while i < len(texto) and texto[i].isspace():
        i += 1
    if i >= len(texto):
        return None, i, "∇ sem operando: falta o que derivar"

    if _RE_NABLA.match(texto, i):
        interna = _uma(texto, i)
        return texto[i:interna.fim], interna.fim, None

    for abre, fecha in (("(", ")"), ("{", "}")):
        if texto[i] == abre:
            fim = _grupo(texto, i, abre, fecha)
            if fim is None:
                return None, len(texto), f"'{abre}' sem '{fecha}' no operando de ∇"
            return texto[i + 1:fim - 1], fim, None
    if texto.startswith(r"\left(", i):
        fim = texto.find(r"\right)", i)
        if fim < 0:
            return None, len(texto), r"'\left(' sem '\right)' no operando de ∇"
        return texto[i + 6:fim], fim + 7, None

    m = _RE_MACRO.match(texto, i) or _RE_LETRA.match(texto, i)
    if not m:
        return None, i + 1, "o que vem depois de ∇_U não é um operando reconhecível"
    fim = m.end()
    resto = texto[fim:].lstrip()
    if resto[:1] in ("_", "^", "(", "'"):
        return None, fim, (
            f"não está claro até onde ∇ alcança em '{texto[i:fim]}{resto[:1]}…': "
            f"escreva o operando entre parênteses, ∇_U ( … )")
    return m.group(0), fim, None


def _uma(texto, ini):
    m = _RE_NABLA.match(texto, ini)
    direcao, fim_direcao = _direcao(texto, m.end())
    operando, fim, problema = _operando(texto, fim_direcao)
    return Ocorrencia(ini, fim_direcao, fim, direcao, operando, problema)


def _limpo(nome):
    return nome[1:] if nome and nome.startswith("\\") else nome


def localizar(texto, tensores, indices=()):
    """As ocorrências de `\\nabla_U …` que NÃO são derivada com índice.

    `\\nabla_\\mu` fica de fora: é da ponte tensorial, que tem a sua própria
    recusa. As de fora da cadeia vêm primeiro; as internas são lidas pela
    recursão sobre o operando.
    """
    achados = []
    pos = 0
    while True:
        m = _RE_NABLA.search(texto, pos)
        if m is None:
            return achados
        oc = _uma(texto, m.start())
        nome = _limpo(oc.direcao)
        if nome in indices:
            pos = m.end()
            continue
        tipo = tensores.get(nome)
        if oc.direcao is None:
            oc.problema = "∇ com subscrito vazio"
        elif tipo is None:
            oc.problema = (
                f"∇_{oc.direcao}: '{nome}' não foi declarado. Se é a direção "
                f"da derivada, declare {nome} = tensor(1,0); se é índice, "
                f"declare {nome} = índice. A tipografia é a mesma, e escolher "
                f"entre as duas seria adivinhar")
        elif tipo != VETOR:
            oc.problema = (
                f"∇_{oc.direcao}: '{nome}' foi declarado do tipo "
                f"({tipo[0]},{tipo[1]}), e a derivada covariante é na direção "
                f"de um VETOR, do tipo (1,0)")
        achados.append(oc)
        pos = oc.fim if oc.fim > m.end() else m.end()
