r"""Uma expressão com índice, avaliada componente por componente numa carta.

    x = coordenadas(t, r, \theta, \phi)
    g = métrica(-f, 1/f, r^2, r^2 \sin^2\theta)
    F = forma(\frac{Q}{r^2} dt \wedge dr)
    \alpha, \beta, \gamma, \delta = índices
    F_{\alpha\gamma} F_\beta{}^\gamma - \frac{1}{4} g_{\alpha\beta} F_{\gamma\delta} F^{\gamma\delta}
    em_carta(eq1)

Cada tensor vira o array das suas componentes: a métrica declarada, os campos
(campo, covetor), as formas numa carta, e o Riemann, o Ricci e o escalar — os
três pelos Christoffel, na convenção que riemann(eq) e ricci(eq) leram. As
derivadas ∂ e ∇ deles, também. Os arrays entram sempre com os índices de
baixo: subir com a inversa o SymPy faz certo, descer não.
"""

from __future__ import annotations

import itertools

import sympy as sp
from sympy.tensor.tensor import Tensor, TensorIndex

from .derivadas import BASE_ESCALAR, REGISTRO, RICCI
from .geometria import gamma


class SemComponentes(ValueError):
    pass


def _riemann_carroll(metrica):
    """C^ρ_{σμν} = ∂_μΓ^ρ_{νσ} − ∂_νΓ^ρ_{μσ} + Γ^ρ_{μλ}Γ^λ_{νσ} − Γ^ρ_{νλ}Γ^λ_{μσ}."""
    x, n = metrica.simbolos, len(metrica.simbolos)
    Gm = gamma(metrica)
    C = {}
    for r_, s, m, v in itertools.product(range(n), repeat=4):
        C[r_, s, m, v] = sp.simplify(
            sp.diff(Gm[r_][v][s], x[m]) - sp.diff(Gm[r_][m][s], x[v])
            + sum(Gm[r_][m][l] * Gm[l][v][s] - Gm[r_][v][l] * Gm[l][m][s] for l in range(n)))
    return C


def _arr(n, posto, f):
    return sp.MutableDenseNDimArray([f(t) for t in itertools.product(range(n), repeat=posto)],
                                    (n,) * posto if posto else ())


def _derivar(A, posto, op, metrica, Gm):
    """∂ ou ∇ de um array de índices de baixo: o índice novo primeiro."""
    x, n = metrica.simbolos, len(metrica.simbolos)
    def comp(t):
        a, resto = t[0], t[1:]
        v = sp.diff(A[resto] if posto else A[()], x[a])
        if op == "D":
            for k in range(posto):
                v -= sum(Gm[c][a][resto[k]] * A[resto[:k] + (c,) + resto[k + 1:]] for c in range(n))
        return sp.simplify(v)
    return _arr(n, posto + 1, comp)


def avaliar(expr, espaco, metrica, campos, formas):
    if len(metrica.simbolos) != espaco.dimensao:
        raise SemComponentes(
            f"a métrica tem {len(metrica.simbolos)} coordenadas e os índices, dimensão "
            f"{espaco.dimensao}: declare índices({len(metrica.simbolos)})")
    x, n = metrica.simbolos, len(metrica.simbolos)
    G = metrica.matriz()
    Gm = gamma(metrica)
    C = None

    def riemann_baixo():
        nonlocal C
        if C is None:
            C = _riemann_carroll(metrica)
        nome, conv = espaco.riemann
        def comp(t):
            # t nos slots da convenção do usuário; R do usuário = sinal·C, com o
            # ρ descido pela métrica
            ro, si, mu, nu = t[conv["rho"]], t[conv["sigma"]], t[conv["mu"]], t[conv["nu"]]
            return conv["sinal"] * sum(G[ro, a] * C[a, si, mu, nu] for a in range(n))
        return _arr(n, 4, comp)

    def base_array(base):
        if base == espaco.metrica:
            return _arr(n, 2, lambda t: G[t]), 2
        if base in campos:
            c = campos[base]
            v = [sum(G[i, j] * c.componentes[j] for j in range(n)) for i in range(n)] if c.cima else c.componentes
            return _arr(n, 1, lambda t: v[t[0]]), 1
        if base in formas:
            f = formas[base]
            from .formas_carta import _ordenar
            def comp(t):
                s_, k = _ordenar(list(t))
                return s_ * f.termos.get(k, 0) if s_ else 0
            return _arr(n, f.grau, comp), f.grau
        if espaco.riemann and base == espaco.riemann[0]:
            return riemann_baixo(), 4
        if base == RICCI and espaco.ricci:
            R = riemann_baixo()
            conv = espaco.ricci
            inv = G.inv()
            def comp(t):
                total = 0
                for a, b in itertools.product(range(n), repeat=2):
                    slots = [None] * 4
                    slots[conv["mu"]], slots[conv["nu"]] = t[0], t[1]
                    slots[conv["par"][0]], slots[conv["par"][1]] = a, b
                    total += inv[a, b] * R[tuple(slots)]
                return sp.simplify(conv["sinal"] * total)
            return _arr(n, 2, comp), 2
        if base.startswith(BASE_ESCALAR) or (espaco.ricci and base == espaco.riemann[0]):
            return _arr(n, 0, lambda t: escalar()), 0
        raise SemComponentes(f"'{base}' não tem componentes nesta carta: declare-o com "
                             f"campo(…), covetor(…) ou forma(…)")

    def escalar():
        Ric, _ = base_array(RICCI)
        inv = G.inv()
        return sp.simplify(sum(inv[a, b] * Ric[a, b] for a in range(n) for b in range(n)))

    repl = {espaco.tipo: G}
    vistos = set()
    for t in sp.preorder_traversal(expr):
        if not isinstance(t, Tensor) or t.head.name in vistos:
            continue
        vistos.add(t.head.name)
        operacoes, base = REGISTRO.get(t.head.name, ((), t.head.name))
        if base.startswith(BASE_ESCALAR):
            A, posto = _arr(n, 0, lambda _: escalar()), 0
        elif base in campos or base in formas or base == espaco.metrica or base == RICCI or \
                (espaco.riemann and base == espaco.riemann[0]):
            A, posto = base_array(base)
        else:
            # escalar: uma função das coordenadas, derivada
            A, posto = _arr(n, 0, lambda _: sp.Function(base)(*x) if base not in map(str, x) else sp.Symbol(base)), 0
        for op in reversed(operacoes):
            A = _derivar(A, posto, op, metrica, Gm)
            posto += 1
        idx = [-TensorIndex(f"z_{i}", espaco.tipo) for i in range(len(t.indices))]
        repl[t.head(*idx)] = A
    # o escalar de curvatura nos coeficientes
    if espaco.ricci and sp.Symbol(espaco.riemann[0]) in expr.free_symbols:
        expr = expr.subs(sp.Symbol(espaco.riemann[0]), escalar())
    livres = list(expr.get_free_indices())
    arr = expr.replace_with_arrays(repl, livres)
    nomes = [metrica.escrita.get(str(c), str(c)) for c in x]
    saida = []
    if not livres:
        return [("", sp.simplify(arr))]
    for t in itertools.product(range(n), repeat=len(livres)):
        v = sp.simplify(arr[t])
        if v.has(sp.sin, sp.cos, sp.tan, sp.cot):
            # sin 2θ/tan θ − 2 cos 2θ só vira 2sin²θ com os ângulos expandidos
            v = sp.simplify(sp.trigsimp(sp.expand_trig(v)))
        v = sp.factor(v)
        if v != 0:
            rotulo = "".join(("^" if i.is_up else "_") + "{" + nomes[k] + "}" for i, k in zip(livres, t))
            saida.append((rotulo, v))
    return saida
