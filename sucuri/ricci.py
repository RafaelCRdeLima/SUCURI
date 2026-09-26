r"""O Ricci e o escalar como contrações do Riemann — na convenção escrita.

    R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}      eq2
    R = ricci(eq2)

Os livros escrevem com a mesma letra o Riemann, o Ricci e o escalar, e o
posto os distingue: R^ρ{}_{σμν}, R_{μν}, R. Qual par se contrai varia —
Carroll contrai o primeiro com o terceiro, outros o primeiro com o quarto,
e o sinal muda —, e por isso o Sucuri lê a definição escrita, como com o
Riemann e com Γ. O escalar é g^{μν}R_{μν} em todo livro.

## Como simplificar usa isso

Desdobra: R_{μν} vira a contração do Riemann, R vira g^{μν} vezes ela. A
canonização vê então as simetrias do Riemann — e a simetria do Ricci, que é
teorema, sai sem ser suposta. Depois dobra de volta: um Riemann com um par
contraído que, canonizado, é ± a definição canonizada vira ±R_{μν}; com dois
pares, ±R.
"""

from __future__ import annotations

import functools
import operator

import sympy as sp
from sympy.tensor.tensor import TensAdd, TensExpr, Tensor, TensMul

from .derivadas import (BASE_ESCALAR, REGISTRO, RICCI, _mapear, derivar,
                        escalar_de)


class RicciMalDefinido(ValueError):
    pass


def _mudo(espaco):
    from .christoffel import _mudo as mudo
    return mudo(espaco)


def _termo(lado):
    """(coeficiente, Tensor) de ±T; None se não for isso."""
    if isinstance(lado, Tensor):
        return sp.S.One, lado
    if isinstance(lado, TensMul):
        fatores = [a for a in lado.args if isinstance(a, TensExpr)]
        if len(fatores) == 1 and isinstance(fatores[0], Tensor):
            return escalar_de(lado), fatores[0]
    return None


def convencao_de(equacao, espaco):
    r"""De R_{μν} = ±R^ρ{}_{μρν}: os slots contraídos, os livres, o sinal."""
    riemann = espaco.riemann[0] if espaco.riemann else None
    esperado = ("a definição tem de ter a forma R_{μν} = ± R^ρ{}_{μρν} — o "
                "Ricci de um lado; do outro, o Riemann (declarado antes, com "
                "riemann(eq)) com um par de índices contraído")
    if riemann is None:
        raise RicciMalDefinido("o Ricci é uma contração do Riemann: declare "
                               "antes R = riemann(eq)")
    if not isinstance(equacao, sp.Equality):
        raise RicciMalDefinido(esperado)
    lados = [_termo(equacao.lhs), _termo(equacao.rhs)]
    if None in lados:
        raise RicciMalDefinido(esperado)
    ric = next((l for l in lados if len(l[1].indices) == 2), None)
    rie = next((l for l in lados if len(l[1].indices) == 4
                and l[1].head.name == riemann), None)
    if ric is None or rie is None or ric[0] not in (1, -1) or rie[0] not in (1, -1):
        raise RicciMalDefinido(esperado)
    a, b = ric[1].indices
    indices = list(rie[1].indices)
    livres, par = {}, []
    for k, i in enumerate(indices):
        if i == a:
            livres["mu"] = k
        elif i == b:
            livres["nu"] = k
        else:
            par.append(k)
    if len(livres) != 2 or len(par) != 2 or \
            indices[par[0]].name != indices[par[1]].name:
        raise RicciMalDefinido(esperado)
    return {"sinal": int(rie[0] * ric[0]), "nome": ric[1].head.name,
            "par": tuple(par), **livres}


# ------------------------------------------------------------- desdobrar

def _riemann_de(espaco, conv, x, y):
    """±R^ρ{}_{xρy} na convenção: o Ricci em x, y, desdobrado."""
    s = _mudo(espaco)
    slots = [None] * 4
    slots[conv["mu"]], slots[conv["nu"]] = x, y
    slots[conv["par"][0]], slots[conv["par"][1]] = s, -s
    return conv["sinal"] * espaco.cabeca(espaco.riemann[0], 4)(*slots)


def _escalar_desdobrado(espaco, conv):
    g = espaco.cabeca(espaco.metrica, 2)
    a, b = _mudo(espaco), _mudo(espaco)
    return g(a, b) * _riemann_de(espaco, conv, -a, -b)


def _potencia(espaco, conv, n):
    return functools.reduce(operator.mul, [_escalar_desdobrado(espaco, conv)
                                           for _ in range(n)])


def desdobrar(expr, espaco):
    """R_{μν} e R em contrações do Riemann; ∂R e ∇R_{μν} também."""
    if espaco is None or not espaco.ricci or not isinstance(expr, TensExpr):
        return expr
    conv = espaco.ricci
    nome_ric = conv["nome"]
    escalar = sp.Symbol(espaco.riemann[0])
    base_escalar = BASE_ESCALAR + espaco.riemann[0]

    def trocar(t):
        operacoes, base = REGISTRO.get(t.head.name, ((), t.head.name))
        indices = list(t.indices)
        k = len(operacoes)
        if base == nome_ric:
            valor = _riemann_de(espaco, conv, *indices[k:])
        elif base == base_escalar and espaco.metrica:
            valor = _escalar_desdobrado(espaco, conv)
        else:
            return t
        for op, i in zip(reversed(operacoes), reversed(indices[:k])):
            valor = derivar(valor, op, i, espaco)
        return valor

    expr = _mapear(expr, trocar)
    if not espaco.metrica:
        return expr

    def coeficiente(termo):
        if not isinstance(termo, TensMul):
            return termo
        c = sp.expand(escalar_de(termo))
        if escalar not in c.free_symbols:
            return termo
        fatores = functools.reduce(
            operator.mul, [a for a in termo.args if isinstance(a, TensExpr)])
        try:
            p = sp.Poly(c, escalar)
        except sp.PolynomialError:
            return termo
        partes = []
        for (n,), cn in p.terms():
            partes.append(cn * fatores if n == 0
                          else cn * _potencia(espaco, conv, n) * fatores)
        return functools.reduce(operator.add, partes)

    if isinstance(expr, TensAdd):
        return functools.reduce(operator.add,
                                [coeficiente(a) for a in expr.args])
    return coeficiente(expr)


# ----------------------------------------------------------------- dobrar

def _canon(e):
    return e.canon_bp() if isinstance(e, TensExpr) else e


def dobrar(expr, espaco):
    """O Riemann contraído de volta em ±R_{μν} ou ±R."""
    if espaco is None or not espaco.ricci or not isinstance(expr, TensExpr):
        return expr
    conv = espaco.ricci
    riemann = espaco.riemann[0]
    ric = espaco.cabeca(conv["nome"], 2)

    def trocar(t):
        if t.head.name != riemann:
            return t
        indices = list(t.indices)
        nomes = [i.name for i in indices]
        pares = [n for n in set(nomes) if nomes.count(n) == 2]
        canonico = _canon(t)
        if len(pares) == 1:
            x, y = [i for i in indices if i.name not in pares]
            for u, v in ((x, y), (y, x)):
                alvo = _canon(_riemann_de(espaco, conv, u, v))
                if canonico == alvo:
                    return ric(u, v)
                if canonico == -alvo:
                    return -ric(u, v)
        elif len(pares) == 2 and espaco.metrica:
            alvo = _canon(_escalar_desdobrado(espaco, conv).contract_metric(
                espaco.cabeca(espaco.metrica, 2)))
            if canonico == alvo:
                return sp.Symbol(riemann)
            if canonico == -alvo:
                return -sp.Symbol(riemann)
        return t

    return _mapear(expr, trocar)


# ------------------------------------------------------------ apresentar

# As oito formas que as simetrias do Riemann dão: R_{abcd} = sinal·R_{perm}.
_FORMAS = [((0, 1, 2, 3), 1), ((1, 0, 2, 3), -1), ((0, 1, 3, 2), -1),
           ((1, 0, 3, 2), 1), ((2, 3, 0, 1), 1), ((3, 2, 0, 1), -1),
           ((2, 3, 1, 0), -1), ((3, 2, 1, 0), 1)]


def apresentar(expr, espaco):
    """Cada Riemann na forma da convenção: o índice de cima no slot de ρ.

    A canonização escolhe, entre as formas iguais pelas simetrias, a menor na
    ordem dela — R_{μν}{}^ρ{}_σ, por exemplo. É igual a R^ρ{}_{σμν}, mas não
    é como se lê; esta é a última passada, e só muda a escrita.
    """
    if (espaco is None or not espaco.riemann or not isinstance(expr, TensExpr)
            or espaco.conexao != "levi-civita" or not espaco.metrica):
        return expr
    nome, conv = espaco.riemann
    ideal = [k == conv["rho"] for k in range(4)]
    if sorted([sorted((conv["mu"], conv["nu"])),
               sorted((conv["rho"], conv["sigma"]))]) != [[0, 1], [2, 3]]:
        return expr

    # Um índice livre pesa mais que um mudo: a valência do mudo a métrica
    # troca, a do livre é a que o leitor escreveu.
    livres = set(expr.get_free_indices())

    def trocar(t):
        if t.head.name != nome or len(t.indices) != 4:
            return t
        indices = list(t.indices)

        def nota(forma):
            perm, _ = forma
            return sum((10 if indices[p] in livres else 1)
                       * (indices[p].is_up == ideal[k]) for k, p in enumerate(perm))

        perm, sinal = max(_FORMAS, key=nota)     # empate: a primeira, a atual
        if perm == (0, 1, 2, 3):
            return t
        return sinal * t.head(*(indices[p] for p in perm))

    return _mapear(expr, trocar)
