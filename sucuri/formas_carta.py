r"""Formas diferenciais numa carta: dx ∧ dy com coeficientes.

    x = coordenadas(r, \theta, \phi)
    g = métrica(1, r^2, r^2 \sin^2\theta)
    \alpha = forma(a dr + b d\theta + c d\phi)
    \beta = estrela(\alpha, g)                  ⋆α
    H = forma(H_x dy \wedge dz + H_y dz \wedge dx + H_z dx \wedge dy)
    exterior(H)                                  dH
    lie(X, \mu)                                  ℒ_X μ = dι_Xμ + ι_Xdμ

## A orientação

⋆ pede uma orientação, e a desta carta é a da ordem das coordenadas: a forma
de volume é √|g| dx¹∧…∧dxⁿ. Trocar a ordem de duas coordenadas troca a
orientação, e o sinal de ⋆ — é assim que se declara a outra.

## ⋆

Com a forma de volume ε = √|g| dx¹∧…∧dxⁿ, (⋆α)_{j…} = (1/p!) α^{i…} ε_{i…j…}:
α ∧ ⋆β = ⟨α, β⟩ ε, que é a de Dray e de Reall (8.55).
"""

from __future__ import annotations

import itertools
import re

import sympy as sp
from sympy.combinatorics.permutations import Permutation


class FormaMalEscrita(ValueError):
    pass


class FormaC:
    """{(i₁ < … < i_p): coeficiente}, nas coordenadas `simbolos`."""

    def __init__(self, simbolos, termos, grau):
        self.simbolos = list(simbolos)
        self.grau = grau
        self.termos = {k: sp.simplify(v) for k, v in termos.items() if sp.simplify(v) != 0}

    def __add__(self, outra):
        t = dict(self.termos)
        for k, v in outra.termos.items():
            t[k] = t.get(k, 0) + v
        return FormaC(self.simbolos, t, self.grau)

    def escalar(self, c):
        return FormaC(self.simbolos, {k: c * v for k, v in self.termos.items()}, self.grau)

    def nula(self):
        return not self.termos

    def texto(self, escrita=None):
        escrita = escrita or {}
        if not self.termos:
            return "0", "0"
        nome = lambda i: escrita.get(str(self.simbolos[i]), str(self.simbolos[i]))
        partes, latex = [], []
        for k in sorted(self.termos):
            v = self.termos[k]
            base = "∧".join("d" + nome(i).lstrip("\\") for i in k)
            base_l = r" \wedge ".join(r"\mathrm{d}" + nome(i) for i in k)
            vs = sp.sstr(v)
            if isinstance(v, sp.Add):
                vs = f"({vs})"
            vl = sp.latex(v)
            if isinstance(v, sp.Add):
                vl = rf"\left({vl}\right)"
            if k and v == 1:
                partes.append(base); latex.append(base_l)
            elif k and v == -1:
                partes.append("-" + base); latex.append("-" + base_l)
            else:
                partes.append(f"{vs}*{base}" if k else vs)
                latex.append(f"{vl}\\,{base_l}" if k else vl)
        return " + ".join(partes).replace("+ -", "- "), " + ".join(latex)


def _ordenar(indices):
    """(sinal, tupla ordenada), ou (0, None) se houver repetição."""
    if len(set(indices)) != len(indices):
        return 0, None
    ordem = sorted(range(len(indices)), key=lambda k: indices[k])
    sinal = Permutation(ordem).signature() if len(indices) > 1 else 1
    return sinal, tuple(sorted(indices))


def ler(texto, simbolos, escrita, ler_expressao):
    r"""`a dr + b d\theta`, `H_x dy \wedge dz + …`: cada cadeia de d's vira uma
    incógnita W_{ijk}, com o sinal da permutação que a ordena; o que sobra é
    linear nelas, e os coeficientes são as componentes."""
    corpo = re.sub(r"\\mathrm\{d\}", "d", texto)
    nomes = [escrita.get(str(s), str(s)) for s in simbolos]
    padrao_d = r"d\s*(" + "|".join(sorted((re.escape(n) for n in nomes), key=len, reverse=True)) + r")(?![A-Za-z])"
    cadeia = re.compile(r"(?<![A-Za-z\\])" + padrao_d + r"(?:\s*\\wedge\s*" + padrao_d + r")*")
    marcas = {}                     # número -> tupla ordenada de índices
    ids = {}

    def trocar(m):
        achados = re.findall(padrao_d, m.group(0))
        indices = [nomes.index(a) for a in achados]
        sinal, chave = _ordenar(indices)
        antes = corpo_atual[0][:m.start()].rstrip()
        junta = "" if (not antes or antes[-1] in "+-(") else r" \cdot "
        if sinal == 0:
            return junta + " 0 "
        k = ids.setdefault(chave, len(ids) + 1)
        marcas[k] = chave
        return junta + (r" (-1) \cdot " if sinal < 0 else " ") + r"\Xi_{" + str(k) + "} "

    corpo_atual = [corpo]
    corpo = cadeia.sub(trocar, corpo)
    graus = {len(k) for k in marcas.values()}
    if len(graus) > 1:
        raise FormaMalEscrita("os termos têm graus diferentes: uma forma tem um grau só")
    grau = graus.pop() if graus else 0
    expr = sp.expand(ler_expressao(corpo))
    termos = {}
    por_nome = {}
    for k, chave in marcas.items():
        for n in (f"Xi_{{{k}}}", f"Xi_{k}", f"\\Xi_{{{k}}}"):
            por_nome[n] = chave
    resto = expr
    for s_ in list(expr.free_symbols):
        if str(s_) in por_nome:
            c = expr.coeff(s_)
            termos[por_nome[str(s_)]] = termos.get(por_nome[str(s_)], 0) + c
            resto = sp.expand(resto - c * s_)
    if marcas and sp.simplify(resto) != 0:
        raise FormaMalEscrita(f"sobrou um termo sem d das coordenadas: {sp.sstr(resto)}")
    if not marcas:
        termos = {(): expr}
    return FormaC(simbolos, termos, grau)


def cunha(a, b):
    t = {}
    for ka, va in a.termos.items():
        for kb, vb in b.termos.items():
            sinal, chave = _ordenar(list(ka) + list(kb))
            if sinal:
                t[chave] = t.get(chave, 0) + sinal * va * vb
    return FormaC(a.simbolos, t, a.grau + b.grau)


def exterior(a):
    x = a.simbolos
    t = {}
    for k, v in a.termos.items():
        for i, xi in enumerate(x):
            dv = sp.diff(v, xi)
            if dv == 0:
                continue
            sinal, chave = _ordenar([i] + list(k))
            if sinal:
                t[chave] = t.get(chave, 0) + sinal * dv
    return FormaC(x, t, a.grau + 1)


def interior(campo, a):
    """ι_X α: o vetor no primeiro slot."""
    t = {}
    for k, v in a.termos.items():
        for pos, i in enumerate(k):
            resto = k[:pos] + k[pos + 1:]
            t[resto] = t.get(resto, 0) + (-1) ** pos * campo.componentes[i] * v
    return FormaC(a.simbolos, t, a.grau - 1)


def lie(campo, a):
    """ℒ_X α = dι_Xα + ι_Xdα (Cartan) — que em grau 0 é X(f)."""
    parte1 = exterior(interior(campo, a)) if a.grau > 0 else FormaC(a.simbolos, {}, a.grau)
    return parte1 + interior(campo, exterior(a))


def estrela(a, metrica):
    """⋆α com ε = √|g| dx¹∧…∧dxⁿ, na ordem das coordenadas."""
    x = a.simbolos
    n = len(x)
    G = metrica.matriz()
    inv = G.inv()
    from .geometria import elemento_de_volume
    _, raiz = elemento_de_volume(metrica)
    p = a.grau
    # componentes totalmente antissimétricas de α com índices de cima
    def comp_cima(idx):
        total = 0
        for k, v in a.termos.items():
            for perm in itertools.permutations(k):
                s, _ = _ordenar(list(perm))
                total += s * v * sp.Mul(*[inv[idx[m], perm[m]] for m in range(p)])
        return total
    t = {}
    for resto in itertools.combinations(range(n), n - p):
        valor = 0
        for idx in itertools.permutations([i for i in range(n) if i not in resto], p):
            s, _ = _ordenar(list(idx) + list(resto))
            if s:
                valor += s * comp_cima(idx) / sp.factorial(p)
        t[resto] = raiz * valor
    return FormaC(x, t, n - p)


def ortonormal(a, metrica):
    """As componentes de α no cobase ortonormal σ^i = h_i dx^i de uma métrica
    diagonal (h_i = √|g_ii|): o coeficiente de dx^I dividido pelos h."""
    G = metrica.matriz()
    if not G.is_diagonal():
        raise FormaMalEscrita("o cobase ortonormal automático é para métrica diagonal")
    from .cartan import cartan
    h = cartan(metrica)["e"]
    termos = {k: sp.simplify(v / sp.Mul(*[h[i] for i in k])) for k, v in a.termos.items()}
    return FormaC(a.simbolos, termos, a.grau)


def texto_ortonormal(f, escrita=None):
    """Como texto, com σ^coordenada no lugar de d coordenada."""
    escrita = escrita or {}
    if not f.termos:
        return "0", "0"
    nome = lambda i: escrita.get(str(f.simbolos[i]), str(f.simbolos[i]))
    partes, latex = [], []
    for k in sorted(f.termos):
        v = f.termos[k]
        base = "∧".join("σ^" + nome(i).lstrip("\\") for i in k)
        base_l = r" \wedge ".join(r"\sigma^{" + nome(i) + "}" for i in k)
        vs, vl = sp.sstr(v), sp.latex(v)
        if isinstance(v, sp.Add):
            vs, vl = f"({vs})", rf"\left({vl}\right)"
        partes.append(f"{vs}*{base}" if k else vs)
        latex.append(f"{vl}\\,{base_l}" if k else vl)
    return " + ".join(partes).replace("+ -", "- "), " + ".join(latex)
