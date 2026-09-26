r"""Quantas componentes independentes — contando, e não de cabeça.

    \mu, \nu, \rho, \sigma = índices(4)
    F = tensor(0, 2, antissimétrico)
    independentes(F)                         6
    independentes(R)                         20   (o Riemann: simetrias e Bianchi)
    independentes(C, eq3, eq4)               10   (e as equações dadas: traço nulo…)

Cada componente T_{i j …}, com os índices de 0 a n−1, é uma incógnita. As
simetrias declaradas identificam componentes (T_{ij} = −T_{ji}) ou as zeram
(T_{ii} = 0); cada equação dada — linear em T, com g, δ ou ε — vira uma
equação por valor dos índices livres. O que sobra é a dimensão do espaço de
soluções: n^r menos o posto. Zero quer dizer que só o tensor nulo tem aquelas
propriedades naquela dimensão.

## A métrica na contagem

Traço e contração pedem uma métrica. A contagem usa a euclidiana: com
qualquer outra de mesma dimensão o espaço de soluções tem a mesma dimensão
(troca de base), e contar não depende da assinatura.
"""

from __future__ import annotations

import itertools

import sympy as sp
from sympy.combinatorics import PermutationGroup
from sympy.tensor.tensor import TensAdd, TensExpr, Tensor, TensMul


class SemContagem(ValueError):
    pass


def _posto(nome, espaco):
    if nome in espaco._tipos:
        return sum(espaco._tipos[nome])
    if espaco.riemann and nome == espaco.riemann[0]:
        return 4
    if nome in espaco._cabecas:
        return espaco._cabecas[nome][1]
    raise SemContagem(f"'{nome}' não é tensor declarado: declare com "
                      f"{nome} = tensor(M, N)")


def _orbitas(cabeca, n, posto):
    """{tupla: (símbolo, sinal)} — e as tuplas que as simetrias zeram."""
    geradores = cabeca.symmetry.generators
    elementos = list(PermutationGroup(*geradores).generate()) if geradores else []
    valores, simbolos = {}, []
    for t in itertools.product(range(n), repeat=posto):
        if t in valores:
            continue
        orbita = {t: 1}
        nula = False
        for p in elementos:
            imagem = tuple(t[p(i)] for i in range(posto))
            sinal = -1 if p(posto) == posto + 1 else 1
            if imagem in orbita and orbita[imagem] != sinal:
                nula = True
            orbita.setdefault(imagem, sinal)
        if nula:
            for u in orbita:
                valores[u] = sp.S.Zero
            continue
        s = sp.Symbol("c_" + "".join(map(str, t)))
        simbolos.append(s)
        for u, sinal in orbita.items():
            valores[u] = sinal * s
    return valores, simbolos


def _array(valores, n, posto):
    return sp.MutableDenseNDimArray(
        [valores[t] for t in itertools.product(range(n), repeat=posto)],
        (n,) * posto)


def _bianchi(cabeca, espaco):
    """R^ρ{}_{[σμν]} = 0, na posição dos slots da convenção."""
    from .prova_indices import _bianchi as bianchi
    return bianchi(espaco)


def _equacoes(expr, repl, espaco):
    """As componentes de expr (= 0), para cada valor dos índices livres."""
    if expr == 0:
        return []
    livres = list(expr.get_free_indices())
    arr = expr.replace_with_arrays(repl, livres)
    if not isinstance(arr, sp.NDimArray):
        return [sp.expand(arr)]
    return [sp.expand(x) for x in sp.flatten(arr.tolist())]


def contar(nome, equacoes, espaco):
    """(componentes independentes, total, depois das simetrias, notas)."""
    n = espaco.dimensao
    if not isinstance(n, int):
        raise SemContagem(f"contar pede a dimensão em número, e ela é {n}: "
                          f"declare os índices com índices(4), por exemplo")
    posto = _posto(nome, espaco)
    cabeca = espaco.cabeca(nome, posto)
    valores, simbolos = _orbitas(cabeca, n, posto)
    depois_simetrias = len(simbolos)
    notas = []

    # Chave com índices de baixo: subir com a inversa o SymPy faz certo; descer a
    # partir de uma chave de cima, não.
    repl = {cabeca(*_indices(espaco, posto, cima=False)): _array(valores, n, posto),
            espaco.tipo: sp.eye(n)}
    if espaco.metrica:
        g = espaco.cabeca(espaco.metrica, 2)
        repl[g(*_indices(espaco, 2, cima=False))] = sp.eye(n)
    if espaco.kronecker:
        d = espaco.cabeca(espaco.kronecker, 2)
        a, b = _indices(espaco, 2)
        repl[d(a, -b)] = sp.eye(n)
    for e_nome, qual in espaco.levi.items():
        if len(_indices(espaco, n)) == n:
            eps = espaco.cabeca(e_nome, n)
            repl[eps(*_indices(espaco, n, cima=False))] = sp.Array(
                [sp.LeviCivita(*t) for t in itertools.product(range(n), repeat=n)],
                (n,) * n)

    exprs = list(equacoes)
    if (espaco.riemann and nome == espaco.riemann[0]
            and espaco.conexao == "levi-civita"):
        exprs.append(_bianchi(cabeca, espaco))
        notas.append("a primeira identidade de Bianchi, R^ρ{}_{[σμν]} = 0 — "
                     "teorema da torção nula")
    linhas = []
    for e in exprs:
        _conferir(e, cabeca, espaco)
        linhas += _equacoes(e, repl, espaco)
    linhas = [l for l in linhas if l != 0]
    posto_sistema = (sp.Matrix([[l.coeff(s) for s in simbolos] for l in linhas]).rank()
                     if linhas and simbolos else 0)
    return len(simbolos) - posto_sistema, n ** posto, depois_simetrias, notas


def _indices(espaco, k, cima=True):
    from sympy.tensor.tensor import TensorIndex
    return [TensorIndex(f"z_{i}", espaco.tipo, cima) for i in range(k)]


def _conferir(expr, cabeca, espaco):
    """Só T, g, δ e ε: a contagem é das componentes de T."""
    permitidos = {cabeca.name, espaco.metrica, espaco.kronecker, *espaco.levi}
    termos = expr.args if isinstance(expr, TensAdd) else [expr]
    for t in termos:
        fatores = [t] if isinstance(t, Tensor) else [
            a for a in getattr(t, "args", []) if isinstance(a, Tensor)]
        for f in fatores:
            if f.head.name not in permitidos:
                raise SemContagem(
                    f"a equação tem '{f.head.name}', e a contagem é das "
                    f"componentes de {cabeca.name}: as equações podem ter só "
                    f"{cabeca.name}, a métrica, δ e ε")
        if isinstance(t, TensMul):
            if sum(1 for f in fatores if f.head == cabeca) != 1:
                raise SemContagem(f"cada termo tem de ser linear em {cabeca.name}")


# ------------------------------------------------ o tensor mais geral

def geral(nome, espaco, repl):
    """As componentes do T mais geral com as simetrias declaradas (e, para o
    Riemann com Levi-Civita, Bianchi): um array com parâmetros livres."""
    n = espaco.dimensao
    posto = _posto(nome, espaco)
    cabeca = espaco.cabeca(nome, posto)
    valores, simbolos = _orbitas(cabeca, n, posto)
    arr = _array(valores, n, posto)
    if (espaco.riemann and nome == espaco.riemann[0]
            and espaco.conexao == "levi-civita"):
        r = dict(repl)
        r[cabeca(*_indices(espaco, posto, cima=False))] = arr
        linhas = [l for l in _equacoes(_bianchi(cabeca, espaco), r, espaco) if l != 0]
        if linhas:
            sol = sp.solve(linhas, simbolos, dict=True)
            if sol:
                arr = arr.applyfunc(lambda x: x.subs(sol[0]))
    return cabeca, arr


def em_componentes(expr, espaco):
    """expr (= 0) vale para todo tensor com as propriedades declaradas, e toda
    métrica? Componente por componente, com o mais geral de cada um."""
    from .ricci import desdobrar
    n = espaco.dimensao
    if not isinstance(n, int):
        raise SemContagem(f"em componentes, a dimensão tem de ser um número, e "
                          f"ela é {n}: declare índices(2), por exemplo")
    if not espaco.metrica:
        raise SemContagem("em componentes, a métrica tem de estar declarada")
    G = sp.Matrix(n, n, lambda i, j: sp.Symbol(f"g_{min(i, j)}{max(i, j)}"))
    g = espaco.cabeca(espaco.metrica, 2)
    repl = {espaco.tipo: G, g(*_indices(espaco, 2, cima=False)): G}
    if espaco.kronecker:
        d = espaco.cabeca(espaco.kronecker, 2)
        a, b = _indices(espaco, 2)
        repl[d(a, -b)] = sp.eye(n)
    if isinstance(expr, TensExpr):
        expr = desdobrar(expr.expand(), espaco)
        expr = expr.expand() if isinstance(expr, TensExpr) else expr
    if not isinstance(expr, TensExpr):
        return sp.simplify(expr) == 0
    nomes = set()
    for t in (expr.args if isinstance(expr, TensAdd) else [expr]):
        for f in ([t] if isinstance(t, Tensor) else
                  [a for a in t.args if isinstance(a, Tensor)]):
            nomes.add(f.head.name)
    from .derivadas import REGISTRO
    for nome in nomes - {espaco.metrica, espaco.kronecker}:
        if nome in REGISTRO:
            raise SemContagem("em componentes não há derivada: as componentes "
                              "são números num ponto")
        cabeca, arr = geral(nome, espaco, repl)
        repl[cabeca(*_indices(espaco, len(arr.shape), cima=False))] = arr
    livres = list(expr.get_free_indices())
    arr = expr.replace_with_arrays(repl, livres)
    entradas = sp.flatten(arr.tolist()) if isinstance(arr, sp.NDimArray) else [arr]
    return all(sp.simplify(sp.together(x)) == 0 for x in entradas)
