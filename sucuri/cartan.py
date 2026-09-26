r"""A base ortonormal e as formas de Cartan, numa carta.

    x = coordenadas(t, r, \theta, \phi)
    g = métrica(-(1 - 2m/r), 1/(1 - 2m/r), r^2, r^2 \sin^2\theta)
    cartan(g)

Para uma métrica diagonal, a tétrada é e^a = √|g_aa| dx^a (sem soma), e as
contas são as dos livros:

    de^a = −ω^a_b ∧ e^b,        ω_ab = −ω_ba        (sem torção, métrica)
    Θ^a_b = dω^a_b + ω^a_c ∧ ω^c_b = ½ R^a_{bcd} e^c ∧ e^d

A conexão de spin sai dos Christoffel, ω^a_{bμ} = e^a_ν(∂_μ E_b^ν +
Γ^ν_{μλ} E_b^λ), e as duas equações de estrutura são CONFERIDAS antes de a
resposta sair — não supostas.

## Os índices e o sinal

a, b são índices da base ortonormal, que sobem e descem com η = diag(±1); os
nomes e^0, e^1, … seguem a ordem das coordenadas. R_{abcd} é o Riemann na
convenção R^ρ_{σμν} = ∂_μΓ^ρ_{νσ} − …, a de Carroll e de Reall.
"""

from __future__ import annotations

import sympy as sp

from .geometria import gamma


class SemBase(ValueError):
    pass


def _d(forma, x):
    """d de uma 1-forma dada por componentes ω_μ: (dω)_{μν} = ∂_μω_ν − ∂_νω_μ."""
    n = len(x)
    return [[sp.simplify(sp.diff(forma[v], x[m]) - sp.diff(forma[m], x[v]))
             for v in range(n)] for m in range(n)]


def _cunha(a, b):
    """(α ∧ β)_{μν} = α_μβ_ν − α_νβ_μ, para 1-formas."""
    n = len(a)
    return [[a[m] * b[v] - a[v] * b[m] for v in range(n)] for m in range(n)]


def cartan(metrica):
    G = metrica.matriz()
    x = metrica.simbolos
    n = len(x)
    if not G.is_diagonal():
        raise SemBase("a base ortonormal automática é para métrica diagonal: "
                      "e^a = √|g_aa| dx^a")
    # O sinal de cada direção, num ponto genérico: as coordenadas valendo 2,9 e
    # os parâmetros 0,31 — fora do horizonte, r > 2m, e com sen θ > 0.
    ponto = {c: sp.Rational(29, 10) for c in x}
    def sinal(c):
        c = c.subs(ponto)
        c = c.subs({f: sp.Rational(31, 100) for f in c.free_symbols})
        return -1 if sp.N(c) < 0 else 1
    eta = [sinal(G[i, i]) for i in range(n)]
    def raiz(c):
        c = sp.powdenest(sp.sqrt(sp.factor(sp.simplify(c))), force=True)
        return sp.simplify(c.replace(lambda u: isinstance(u, sp.Abs), lambda u: u.args[0]))
    fator = [raiz(eta[i] * G[i, i]) for i in range(n)]
    e = sp.diag(*fator)                     # e^a_μ
    E = sp.diag(*[1 / f for f in fator])    # E_a^μ
    Gam = gamma(metrica)
    # ω^a_{bμ}
    omega = [[[sp.simplify(sum(e[a, v] * (sp.diff(E[b, v], x[m])
                                         + sum(Gam[v][m][l] * E[b, l] for l in range(n)))
                               for v in range(n)))
               for m in range(n)] for b in range(n)] for a in range(n)]
    # Confere: de^a + ω^a_b ∧ e^b = 0, e ω_ab = −ω_ba.
    for a in range(n):
        de = _d([e[a, m] for m in range(n)], x)
        for b in range(n):
            w = _cunha(omega[a][b], [e[b, m] for m in range(n)])
            de = [[de[i][j] + w[i][j] for j in range(n)] for i in range(n)]
        if any(sp.simplify(de[i][j]) != 0 for i in range(n) for j in range(n)):
            raise SemBase("a primeira equação de estrutura não fechou — defeito "
                          "do motor, e não resposta")
        for b in range(n):
            if any(sp.simplify(eta[a] * omega[a][b][m] + eta[b] * omega[b][a][m]) != 0
                   for m in range(n)):
                raise SemBase("ω_ab não saiu antissimétrica — defeito do motor")
    # Θ^a_b = dω^a_b + ω^a_c ∧ ω^c_b, e R^a_{bcd} na base.
    theta = {}
    R = {}
    for a in range(n):
        for b in range(n):
            T = _d(omega[a][b], x)
            for c in range(n):
                w = _cunha(omega[a][c], omega[c][b])
                T = [[T[i][j] + w[i][j] for j in range(n)] for i in range(n)]
            T = [[sp.simplify(T[i][j]) for j in range(n)] for i in range(n)]
            theta[a, b] = T
            for c in range(n):
                for d in range(n):
                    R[a, b, c, d] = sp.simplify(T[c][d] * E[c, c] * E[d, d])
    return {"eta": eta, "e": [fator[a] for a in range(n)], "omega": omega,
            "theta": theta, "R": R, "x": x}


def _nome(i):
    return f"e^{i}"


def em_formas(res):
    """As formas como texto: ω^a_b em dx, Θ^a_b em e^c ∧ e^d."""
    x, n = res["x"], len(res["x"])
    linhas = []
    for a in range(n):
        linhas.append((f"e^{a}", res["e"][a] * sp.Symbol("d" + str(x[a]))))
    for a in range(n):
        for b in range(a + 1, n):
            w = sum(res["omega"][a][b][m] * sp.Symbol("d" + str(x[m])) for m in range(n))
            w = sp.simplify(w)
            if w != 0:
                linhas.append((f"ω^{a}_{b}", w))
    for a in range(n):
        for b in range(a + 1, n):
            t = sum(res["R"][a, b, c, d] * sp.Symbol(f"e{c}e{d}")
                    for c in range(n) for d in range(c + 1, n))
            t = sp.simplify(t)
            if t != 0:
                linhas.append((f"Θ^{a}_{b}", t))
    return linhas


def riemann_ortonormal(res):
    """R_{abcd} = η_aa R^a_{bcd}, não nulas e a menos das simetrias: a < b, c < d, (ab) ≤ (cd)."""
    n = len(res["x"])
    saida = []
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(n):
                for d in range(c + 1, n):
                    if (a, b) > (c, d):
                        continue
                    v = sp.simplify(res["eta"][a] * res["R"][a, b, c, d])
                    if v != 0:
                        saida.append((f"R_{{{a}{b}{c}{d}}}", v))
    return saida
