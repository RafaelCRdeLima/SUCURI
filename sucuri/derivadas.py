r"""A derivada com índice: ∂_μ A^ν, ∇_μ T_{αβ}.

O parser do SymPy lê `\partial_\mu A^\nu` como o símbolo `partial_{mu}`
multiplicando A — e a ponte recusava, desde o começo, porque derivada com
índice "não é um fator multiplicando outro, é um objeto próprio". Este arquivo
é esse objeto.

## Como é representada

Uma cabeça nova, com o índice da derivada no primeiro slot: ∂_μ A^ν é
`d_A(-mu, nu)`, ∇_μ A^ν é `D_A(-mu, nu)`, ∂_μ∂_ν φ é `dd_phi(-mu, -nu)`.
Assim a derivada entra na contração, na soma e na canonicalização como
qualquer tensor — ∂_μ A^μ é a divergência sem nada especial.

Os nomes não colidem com o que a pessoa declara: nome de várias letras sem
barra é recusado na declaração, justamente porque em LaTeX seria produto.

## O que se sabe dela sem hipótese

- ∂ e ∇ são lineares e seguem Leibniz: ∂_μ(A^ν B_ν) = (∂_μ A^ν)B_ν +
  A^ν ∂_μ B_ν. Escalar também: ∂_μ(φψ) = ψ∂_μφ + φ∂_μψ.
- Derivadas PARCIAIS comutam: dd_A é simétrica nos slots das derivadas, e
  ∂_μ∂_ν φ − ∂_ν∂_μ φ simplifica a zero.
- ∇ NÃO comuta — ∇_μ∇_ν − ∇_ν∇_μ é a curvatura —, e nada se supõe.
- Num escalar, ∇_μ φ = ∂_μ φ: é a definição, em qualquer conexão.
- A simetria do tensor derivado se mantém: ∂_λ g_{μν} é simétrico em μν.

O que NÃO se supõe: ∇g = 0 (é Levi-Civita, não qualquer conexão), e que ∇
comute em escalares (é torção nula).

## Alcance

A derivada age no fator imediatamente à direita — `\partial_\mu A^\nu B_\nu`
é (∂_μ A^ν) B_ν, como se lê em qualquer livro. Produto pede parênteses:
`\partial_\mu (A^\nu B_\nu)`.
"""

from __future__ import annotations

import functools
import operator
import re

import sympy as sp
from sympy.printing.latex import LatexPrinter
from sympy.tensor.tensor import (TensAdd, TensExpr, Tensor, TensMul,
                                 TensorHead, TensorSymmetry)

from .tensores import _RE_FATOR, indices_de

REGISTRO = {}
"""nome da cabeça derivada -> (operações de fora para dentro, nome da base)."""

_MACRO = {"d": r"\partial", "D": r"\nabla"}
_RE_OPERADOR = re.compile(
    r"\\(partial|nabla)(?![a-zA-Z])\s*([_^])\s*(\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z])")
_RE_SIMBOLO = re.compile(r"\\[a-zA-Z]+|[A-Za-z]|\d+(?:\.\d+)?")


class DerivadaMalEscrita(ValueError):
    """Derivada com índice cujo alcance ou índice não se lê de um jeito só."""


# --------------------------------------------------------------- no texto

class Derivada:
    """Um `\\partial_\\mu …` ou `\\nabla^\\mu …` no texto."""

    def __init__(self, ini, fim_cabeca, fim, operacao, indice, cima,
                 operando, problema=None):
        self.ini = ini
        self.fim_cabeca = fim_cabeca
        self.fim = fim
        self.operacao = operacao        # 'd' (∂) ou 'D' (∇)
        self.indice = indice            # 'mu', sem a barra
        self.cima = cima
        self.operando = operando        # o LaTeX sobre o qual age
        self.problema = problema


def _grupo(texto, i, abre, fecha):
    fundo = 0
    for j in range(i, len(texto)):
        if texto[j] == abre:
            fundo += 1
        elif texto[j] == fecha:
            fundo -= 1
            if fundo == 0:
                return j + 1
    return None


def _cabeca(texto, i, indices):
    """(operação, índice, cima, fim) se em `i` começa ∂_μ ou ∇_μ com μ
    declarado; None se não é derivada com índice."""
    m = _RE_OPERADOR.match(texto, i)
    if not m:
        return None
    nomes = indices_de(m.group(3))
    if not nomes or not all(n in indices for n in nomes):
        return None
    return m, nomes


def localizar(texto, indices):
    """As derivadas com índice de primeiro nível — as de dentro são lidas pela
    recursão sobre o operando."""
    if not indices:
        return []
    achados, i = [], 0
    while i < len(texto):
        d = _uma(texto, i, indices)
        if d is None:
            i += 1
            continue
        achados.append(d)
        i = max(d.fim, i + 1)
    return achados


def cabecas(texto, indices):
    """As posições que são cabeça de derivada com índice, em qualquer nível."""
    posicoes = set()
    for i in range(len(texto)):
        d = _uma(texto, i, indices)
        if d is not None:
            posicoes |= set(range(d.ini, d.fim_cabeca))
    return posicoes


def _uma(texto, i, indices):
    achado = _cabeca(texto, i, indices)
    if achado is None:
        return None
    m, nomes = achado
    operacao = "d" if m.group(1) == "partial" else "D"
    cima = m.group(2) == "^"
    if len(nomes) != 1:
        macro = _MACRO[operacao]
        um, dois = (("\\" + n) if len(n) > 1 else n for n in nomes[:2])
        return Derivada(i, m.end(), m.end(), operacao, nomes[0], cima, None,
                        f"{m.group(0)}: um índice por derivada — escreva "
                        f"{macro}_{um}{macro}_{dois}, que diz em que ordem se "
                        f"deriva")
    operando, fim, problema = _operando(texto, m.end(), indices,
                                        m.group(0).strip())
    return Derivada(i, m.end(), fim, operacao, nomes[0], cima, operando,
                    problema)


def _operando(texto, i, indices, quem):
    """(latex, fim, problema) do fator imediatamente à direita."""
    while i < len(texto) and texto[i].isspace():
        i += 1
    if i >= len(texto) or texto[i] in "=+-)}],":
        return None, i, f"{quem} sem operando: falta o que derivar"
    interna = _uma(texto, i, indices)
    if interna is not None:
        return texto[i:interna.fim], interna.fim, None
    for abre, fecha in (("(", ")"), ("{", "}")):
        if texto[i] == abre:
            fim = _grupo(texto, i, abre, fecha)
            if fim is None:
                return None, len(texto), f"'{abre}' sem '{fecha}' depois de {quem}"
            return texto[i + 1:fim - 1], fim, None
    if texto.startswith(r"\left(", i):
        fim = texto.find(r"\right)", i)
        if fim < 0:
            return None, len(texto), rf"'\left(' sem '\right)' depois de {quem}"
        return texto[i + 6:fim], fim + 7, None
    fator = _RE_FATOR.match(texto, i)
    if fator:
        return fator.group(0), fator.end(), None
    simbolo = _RE_SIMBOLO.match(texto, i)
    if simbolo:
        resto = texto[simbolo.end():].lstrip()
        if resto[:1] in ("(", "'"):
            return None, simbolo.end(), (
                f"não está claro até onde {quem} alcança em "
                f"'{simbolo.group(0)}{resto[:1]}…': escreva o operando entre "
                f"parênteses, {quem} ( … )")
        return simbolo.group(0), simbolo.end(), None
    return None, i + 1, f"o que vem depois de {quem} não é um operando"


# ---------------------------------------------------------------- a conta

def _simetria_base(espaco, base):
    if base == espaco.metrica:
        return "simetrico"
    return espaco._simetrias.get(base)


def cabeca_derivada(espaco, operacoes, base, posto_base):
    """A cabeça de `operacoes` aplicadas à base — criada uma vez só."""
    nome = "".join(operacoes) + "_" + base
    if nome in espaco._cabecas:
        return espaco._cabecas[nome][0]
    k = len(operacoes)
    blocos = [k] if all(o == "d" for o in operacoes) else [1] * k
    simetria = _simetria_base(espaco, base)
    if posto_base > 1 and simetria == "simetrico":
        blocos.append(posto_base)
    elif posto_base > 1 and simetria == "antissimetrico":
        blocos.append(-posto_base)
    else:
        blocos += [1] * posto_base
    cabeca = TensorHead(nome, [espaco.tipo] * (k + posto_base),
                        TensorSymmetry.direct_product(*blocos))
    espaco._cabecas[nome] = (cabeca, k + posto_base)
    REGISTRO[nome] = (tuple(operacoes), base)
    return cabeca


def _produto(fatores):
    return functools.reduce(operator.mul, fatores, sp.S.One)


def _soma(termos):
    termos = [t for t in termos if t != 0]
    return functools.reduce(operator.add, termos) if termos else sp.S.Zero


def derivar(expr, operacao, indice, espaco):
    """∂ ou ∇ com o índice `indice` (já com a valência) aplicado a `expr`."""
    if isinstance(expr, TensAdd):
        return _soma([derivar(a, operacao, indice, espaco) for a in expr.args])
    if isinstance(expr, TensMul):
        coef = expr.coeff
        fatores = [a for a in expr.args if isinstance(a, TensExpr)]
        termos = [_escalar(coef, operacao, indice, espaco) * _produto(fatores)]
        for k, f in enumerate(fatores):
            outros = fatores[:k] + [derivar(f, operacao, indice, espaco)] + \
                fatores[k + 1:]
            termos.append(coef * _produto(outros))
        return _soma(termos)
    if isinstance(expr, Tensor):
        cabeca = expr.head
        indices = list(expr.indices)
        operacoes, base = REGISTRO.get(cabeca.name, ((), cabeca.name))
        posto_base = len(indices) - len(operacoes)
        nova = cabeca_derivada(espaco, (operacao,) + operacoes, base, posto_base)
        try:
            return nova(indice, *indices)
        except ValueError:
            raise DerivadaMalEscrita(
                "o índice da derivada aparece de novo no operando, na mesma "
                "posição — contrair é um em cima e um embaixo, como em "
                "∂_μ A^μ") from None
    return _escalar(expr, operacao, indice, espaco)


def _escalar(expr, operacao, indice, espaco):
    """∂_μ de um escalar — que é também ∇_μ dele: regra da cadeia sobre os
    símbolos, cada um uma função."""
    expr = sp.sympify(expr)
    if expr.is_number:
        return sp.S.Zero
    termos = []
    for s in sorted(expr.free_symbols, key=lambda s: s.name):
        parcial = sp.diff(expr, s)
        if parcial != 0:
            # ∇_μ φ = ∂_μ φ num escalar: a mesma cabeça.
            cabeca = cabeca_derivada(espaco, ("d",), s.name, 0)
            termos.append(parcial * cabeca(indice))
    return _soma(termos)


# -------------------------------------------------------------- impressão

class Impressor(LatexPrinter):
    """∂_μ A^ν, e não A com todos os índices juntos — `\\partial A{}_{\\mu}{}^{\\nu}`
    leria como a derivada de A_μ^ν."""

    def _print_Tensor(self, expr):
        nome = expr.head.name
        if nome not in REGISTRO:
            return super()._print_Tensor(expr)
        operacoes, base = REGISTRO[nome]
        indices = list(expr.indices)
        partes = []
        for op, i in zip(operacoes, indices):
            lado = "^" if i.is_up else "_"
            partes.append(f"{_MACRO[op]}{lado}{{{self._print(sp.Symbol(i.name))}}}")
        corpo = self._print(sp.Symbol(base))
        for i in indices[len(operacoes):]:
            lado = "^" if i.is_up else "_"
            corpo += f"{{}}{lado}{{{self._print(sp.Symbol(i.name))}}}"
        return " ".join(partes) + " " + corpo


def latex(expr):
    return Impressor().doprint(expr)
