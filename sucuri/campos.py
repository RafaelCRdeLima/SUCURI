r"""Campos vetoriais dados por componentes numa carta.

    x = coordenadas(\theta, \phi)
    g = métrica(1, \sin^2\theta)
    Y = campo(\sin\phi, \cot\theta \cos\phi)
    killing(g, Y)              ℒ_Y g, componente por componente
    colchete(X, Y)             [X, Y]^i = X^k∂_k Y^i − Y^k∂_k X^i
    A = campo()                A^θ(θ, φ), A^φ(θ, φ): o campo genérico
    nabla(g, A)                A^j_{;i} e A^j_{;ik}
    laplaciano(g, A)           g^{ik} A^j_{;ik}
    killing(g, 1)              todos os campos de Killing de grau ≤ 1

As componentes são as da base coordenada, ∂_θ, ∂_φ — e não as de uma base
ortonormal: é o que distingue, na (7.44) de Cline, A^θ de A^θ̂ = r A^θ.
"""

from __future__ import annotations

import itertools

import sympy as sp

from .geometria import gamma


class Campo:
    def __init__(self, nome, coordenadas, componentes, escrita=None, cima=True):
        self.cima = cima                # vetor (A^i) ou covetor (A_i)
        if len(componentes) != len(coordenadas):
            raise ValueError(f"{nome} tem {len(componentes)} componentes e a carta "
                             f"tem {len(coordenadas)} coordenadas")
        self.nome = nome
        self.simbolos = list(coordenadas)
        self.componentes = [sp.sympify(c) for c in componentes]
        self.escrita = escrita or {}

    @classmethod
    def generico(cls, nome, coordenadas, escrita=None, cima=True):
        escrita = escrita or {}
        marca = "^" if cima else "_"
        comps = [sp.Function(f"{nome}{marca}{escrita.get(str(c), str(c)).lstrip(chr(92))}")(*coordenadas)
                 for c in coordenadas]
        return cls(nome, coordenadas, comps, escrita, cima)


def _mesma_carta(metrica, *campos):
    for c in campos:
        if list(c.simbolos) != list(metrica.simbolos):
            raise ValueError(f"{c.nome} está na carta ({', '.join(map(str, c.simbolos))}) "
                             f"e a métrica em ({metrica.coordenadas}): as duas têm de ser a mesma")


def colchete(X, Y):
    if list(X.simbolos) != list(Y.simbolos):
        raise ValueError("os dois campos têm de estar na mesma carta")
    x, n = X.simbolos, len(X.simbolos)
    return [sp.simplify(sum(X.componentes[k] * sp.diff(Y.componentes[i], x[k])
                            - Y.componentes[k] * sp.diff(X.componentes[i], x[k])
                            for k in range(n))) for i in range(n)]


def lie_metrica(metrica, K):
    """(ℒ_K g)_{ij} = K^k∂_k g_ij + g_kj ∂_i K^k + g_ik ∂_j K^k."""
    _mesma_carta(metrica, K)
    G, x, n, k_ = metrica.matriz(), metrica.simbolos, len(metrica.simbolos), K.componentes
    return sp.Matrix(n, n, lambda i, j: sp.simplify(
        sum(k_[k] * sp.diff(G[i, j], x[k]) + G[k, j] * sp.diff(k_[k], x[i])
            + G[i, k] * sp.diff(k_[k], x[j]) for k in range(n))))


def nabla(metrica, A):
    """A^j_{;i} = ∂_i A^j + Γ^j_{ik} A^k (vetor) ou A_{j;i} = ∂_i A_j − Γ^k_{ij} A_k
    (covetor), como matriz [i][j]."""
    _mesma_carta(metrica, A)
    x, n, a = metrica.simbolos, len(metrica.simbolos), A.componentes
    Gam = gamma(metrica)
    s = 1 if A.cima else -1
    if A.cima:
        return [[sp.simplify(sp.diff(a[j], x[i]) + sum(Gam[j][i][k] * a[k] for k in range(n)))
                 for j in range(n)] for i in range(n)]
    return [[sp.simplify(sp.diff(a[j], x[i]) - sum(Gam[k][i][j] * a[k] for k in range(n)))
             for j in range(n)] for i in range(n)]


def nabla2(metrica, A):
    """A^j_{;ik} = ∂_k(A^j_{;i}) + Γ^j_{kl} A^l_{;i} − Γ^l_{ki} A^j_{;l} (vetor), e
    A_{j;ik} = ∂_k(A_{j;i}) − Γ^l_{kj} A_{l;i} − Γ^l_{ki} A_{j;l} (covetor): [i][k][j]."""
    x, n = metrica.simbolos, len(metrica.simbolos)
    Gam = gamma(metrica)
    D = nabla(metrica, A)
    if A.cima:
        return [[[sp.simplify(sp.diff(D[i][j], x[k]) + sum(Gam[j][k][l] * D[i][l] for l in range(n))
                              - sum(Gam[l][k][i] * D[l][j] for l in range(n)))
                  for j in range(n)] for k in range(n)] for i in range(n)]
    return [[[sp.simplify(sp.diff(D[i][j], x[k]) - sum(Gam[l][k][j] * D[i][l] for l in range(n))
                          - sum(Gam[l][k][i] * D[l][j] for l in range(n)))
              for j in range(n)] for k in range(n)] for i in range(n)]


def laplaciano(metrica, A):
    """(∇²A)^j = g^{ik} A^j_{;ik}."""
    inv = metrica.matriz().inv()
    n = len(metrica.simbolos)
    D2 = nabla2(metrica, A)
    return [sp.expand(sp.simplify(sum(inv[i, k] * D2[i][k][j] for i in range(n) for k in range(n))))
            for j in range(n)]


def killings(metrica, grau=1):
    """Os campos de Killing com componentes polinomiais de grau ≤ `grau` nas
    coordenadas: a equação de Killing num ansatz, e o espaço de soluções."""
    x, n = metrica.simbolos, len(metrica.simbolos)
    monomios = [sp.Mul(*m) for d in range(grau + 1)
                for m in itertools.combinations_with_replacement(x, d)]
    coefs = []
    comps = []
    for i in range(n):
        cs = [sp.Symbol(f"c_{i}_{k}") for k in range(len(monomios))]
        coefs += cs
        comps.append(sum(c * m for c, m in zip(cs, monomios)))
    K = Campo("K", x, comps)
    L = lie_metrica(metrica, K)
    equacoes = []
    for i in range(n):
        for j in range(i, n):
            e = sp.numer(sp.together(L[i, j]))
            equacoes += sp.Poly(sp.expand(e), *x).coeffs()
    sol = sp.solve(equacoes, coefs, dict=True)
    sol = sol[0] if sol else {}
    geral = [sp.expand(c.subs(sol)) for c in comps]
    livres = sorted(set().union(*(g.free_symbols for g in geral)) & set(coefs), key=str)
    base = []
    for p in livres:
        base.append([sp.expand(g.subs({q: (1 if q == p else 0) for q in livres})) for g in geral])
    return base


def restringir(K, metrica):
    """Um campo do espaço ambiente, restrito à subvariedade de onde `metrica`
    foi induzida: V^i = (h⁻¹ Jᵀ G K)^i em X(u). Recusa se K não for tangente —
    senão a "restrição" seria a projeção, e mudaria o campo."""
    if not hasattr(metrica, "ambiente"):
        raise ValueError(f"{metrica.nome} não é induzida: restringir pede a "
                         f"métrica de induzida(g, …)")
    amb = metrica.ambiente
    if list(K.simbolos) != list(amb.simbolos):
        raise ValueError(f"{K.nome} tem de estar na carta de {amb.nome}")
    troca = dict(zip(amb.simbolos, metrica.imagens))
    k = sp.Matrix([c.subs(troca, simultaneous=True) for c in K.componentes])
    G = amb.matriz().subs(troca, simultaneous=True)
    J = metrica.jacobiana
    V = (metrica.matriz().inv() * J.T * G * k).applyfunc(lambda e: sp.simplify(e))
    def nulo(e):
        if sp.simplify(e) == 0 or sp.simplify(e.rewrite(sp.exp)) == 0:
            return True
        # identidade hiperbólica que o simplify não fecha: confere em pontos
        pontos = [{u: sp.Rational(7 + 3 * i + j, 10) for j, u in enumerate(sorted(e.free_symbols, key=str))}
                  for i in range(3)]
        return all(abs(complex(sp.N(e.subs(p_)))) < 1e-9 for p_ in pontos)
    resto = J * V - k
    if not all(nulo(e) for e in resto):
        raise ValueError(f"{K.nome} não é tangente à subvariedade: tem componente normal")
    return Campo(K.nome, metrica.simbolos, [sp.simplify(e) for e in V], metrica.escrita)
