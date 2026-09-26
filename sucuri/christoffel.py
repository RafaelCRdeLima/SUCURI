r"""Os símbolos de Christoffel com índice: ∇ aberto em ∂ e Γ, e Γ em ∂g.

    \nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda     eq1
    \Gamma = christoffel(eq1)
    expandir(eq2)          ∇ vira ∂ mais um termo de Γ por índice
    expandir(eq2, g)       e Γ vira ½ g^{αδ}(∂g + ∂g − ∂g), com Levi-Civita

## A convenção vem da definição escrita

Carroll e MTW põem o índice da derivada em primeiro — Γ^ν_{μλ}V^λ em
∇_μV^ν —; Reall, por último. Para Levi-Civita, simétrico, não importa; para
uma conexão com torção, importa. Como com o Riemann, o Sucuri não escolhe: lê
de que slot é cada índice na definição que você escreveu.

## O que expandir faz

Num índice de cima, +Γ; num de baixo, −Γ; em cada um, o slot do índice
original, o da derivada e o do mudo, na convenção declarada. É a mesma regra
que todo livro deduz de Leibniz e da ação em funções — e por isso vale para
tensor de qualquer posto, e para ∇ dentro de ∇.

## A métrica inversa e o determinante

∂_λ g^{μν} = −g^{μα}g^{νβ}∂_λ g_{αβ}: de g^{μα}g_{αν} = δ^μ_ν, e ∂δ = 0. Não é
convenção nem hipótese — é o que "inversa" quer dizer —, e se aplica ao
derivar (derivadas._derivada_da_inversa).

    g = det(g)             g sem índice é det g_{μν}

∂_λ g = g g^{μν} ∂_λ g_{μν}, a fórmula de Jacobi, o simplificar aplica. O sinal
de det g vem da assinatura, se declarada: (−1)^s, e |g| = −g na lorentziana.
"""

from __future__ import annotations

import functools
import operator

import sympy as sp
from sympy.tensor.tensor import (TensAdd, TensExpr, Tensor, TensorIndex,
                                 TensorSymmetry, TensMul)

from .derivadas import REGISTRO, _mapear, cabeca_derivada, derivar, escalar_de


class ChristoffelMalDefinido(ValueError):
    pass


_MUDOS = [0]


def _mudo(espaco):
    _MUDOS[0] += 1
    return TensorIndex(f"c_{_MUDOS[0]}", espaco.tipo)


def _soma(termos):
    # Expandidos: Γ·(soma) com mudos de mesmo nome dos dois lados confunde a
    # conferência de índices livres do SymPy ao somar.
    termos = [t.expand() if isinstance(t, TensExpr) else t for t in termos]
    termos = [t for t in termos if t != 0]
    return functools.reduce(operator.add, termos) if termos else sp.S.Zero


# ------------------------------------------------------------ a convenção

def convencao_de(equacao, nome):
    r"""Da definição ∇_μ V^ν = ∂_μ V^ν + Γ^ν{}_{μλ} V^λ, onde fica cada slot.

    Devolve {'cima', 'derivada', 'outro'}: a posição, em Γ, do índice de cima
    (o ν), do índice da derivada (o μ) e do mudo contraído com V (o λ).
    """
    esperado = (r"a definição tem de ter a forma ∇_μ V^ν = ∂_μ V^ν + " + nome +
                r"(ν, μ, λ em alguma ordem) V^λ — ∇ num vetor de um lado; do "
                r"outro, a derivada parcial e " + nome + " contraído com o mesmo "
                r"vetor")
    if not isinstance(equacao, sp.Equality):
        raise ChristoffelMalDefinido(esperado)
    lados = [equacao.lhs, equacao.rhs]
    nabla = next((l for l in lados if isinstance(l, Tensor)
                  and REGISTRO.get(l.head.name, ((),))[0] == ("D",)), None)
    soma = next((l for l in lados if isinstance(l, TensAdd)), None)
    if nabla is None or soma is None or len(soma.args) != 2:
        raise ChristoffelMalDefinido(esperado)
    mu, nu = nabla.indices
    vetor = REGISTRO[nabla.head.name][1]
    if mu.is_up or not nu.is_up:
        raise ChristoffelMalDefinido(esperado)
    termo = next((a for a in soma.args if isinstance(a, TensMul)), None)
    if termo is None or escalar_de(termo) != 1:
        raise ChristoffelMalDefinido(esperado)
    fatores = [x for x in termo.args if isinstance(x, Tensor)]
    gamma = [f for f in fatores if f.head.name == nome]
    V = [f for f in fatores if f.head.name == vetor]
    if len(gamma) != 1 or len(V) != 1 or len(gamma[0].indices) != 3:
        raise ChristoffelMalDefinido(esperado)
    lam = V[0].indices[0]
    posicoes = {}
    for k, i in enumerate(gamma[0].indices):
        if i == nu:
            posicoes["cima"] = k
        elif i == mu:
            posicoes["derivada"] = k
        elif i.name == lam.name and i.is_up != lam.is_up:
            posicoes["outro"] = k
    if len(posicoes) != 3:
        raise ChristoffelMalDefinido(esperado)
    return posicoes


def simetria(conv, levi_civita):
    """Levi-Civita é sem torção: Γ simétrico nos dois slots de baixo. Só se
    exprime se forem vizinhos; noutro lugar, fica sem — incompleto, não falso."""
    if not levi_civita:
        return TensorSymmetry.no_symmetry(3)
    baixo = sorted((conv["derivada"], conv["outro"]))
    if baixo == [1, 2]:
        return TensorSymmetry.direct_product(1, 2)
    if baixo == [0, 1]:
        return TensorSymmetry.direct_product(2, 1)
    return TensorSymmetry.no_symmetry(3)


def _gamma(espaco, cima, derivada, outro):
    nome, conv = espaco.christoffel
    slots = [None] * 3
    slots[conv["cima"]], slots[conv["derivada"]], slots[conv["outro"]] = \
        cima, derivada, outro
    return espaco.cabeca(nome, 3)(*slots)


# ------------------------------------------------------------ ∇ → ∂ + Γ

def _objeto(espaco, operacoes, base, indices):
    """O tensor de base com as derivadas `operacoes`, nos `indices`."""
    if operacoes:
        posto = len(indices) - len(operacoes)
        return cabeca_derivada(espaco, operacoes, base, posto)(*indices)
    if not indices:
        return sp.Symbol(base)
    return espaco.cabeca(base, len(indices))(*indices)


def _abrir(t, espaco):
    operacoes, base = REGISTRO.get(t.head.name, ((), None))
    if "D" not in operacoes:
        return t
    indices = list(t.indices)
    mu, dentro = indices[0], indices[1:]
    interno = _objeto(espaco, operacoes[1:], base, dentro)
    aberto = (_abrir(interno, espaco) if isinstance(interno, Tensor)
              else interno)
    total = [derivar(aberto, "d", mu, espaco)]
    if operacoes[0] == "D":
        # Um Γ por índice LIVRE do operando: em ∇_δ(∇_α V^α) o operando é
        # escalar, e o par α contraído dentro dele não leva Γ.
        nomes = [i.name for i in dentro]
        for i in dentro:
            if nomes.count(i.name) > 1:
                continue
            s = _mudo(espaco)
            if i.is_up:
                trocado = _trocar_indice(aberto, i, s)
                total.append(_gamma(espaco, i, mu, -s) * trocado)
            else:
                trocado = _trocar_indice(aberto, i, -s)
                total.append(-_gamma(espaco, s, mu, i) * trocado)
    return _soma(total)


def _trocar_indice(expr, velho, novo):
    if not isinstance(expr, TensExpr):
        return expr
    return expr.substitute_indices((velho, novo))


def expandir(expr, espaco):
    """Cada ∇ em ∂ e Γ, na convenção declarada, até não sobrar ∇."""
    if espaco is None or not espaco.christoffel:
        raise ChristoffelMalDefinido(
            "para abrir ∇ é preciso dizer o que Γ é: escreva a definição "
            "∇_μ V^ν = ∂_μ V^ν + Γ^ν{}_{μλ} V^λ e declare "
            "\\Gamma = christoffel(eq)")
    if isinstance(expr, sp.Equality):
        return sp.Eq(expandir(expr.lhs, espaco), expandir(expr.rhs, espaco),
                     evaluate=False)
    return _mapear(expr, lambda t: _abrir(t, espaco))


# ------------------------------------------------------------ Γ → ∂g

def _metrico(espaco, cima, derivada, outro):
    """Γ de Levi-Civita pela métrica. Com o índice de cima já baixado,
    Γ_{a b c} = ½(∂_b g_{ac} + ∂_c g_{ab} − ∂_a g_{bc})."""
    g = espaco.cabeca(espaco.metrica, 2)

    def dg(d, a, b):
        return derivar(g(a, b), "d", d, espaco)

    if cima.is_up:
        a = _mudo(espaco)
        return sp.Rational(1, 2) * g(cima, a) * (
            dg(derivada, -a, outro) + dg(outro, -a, derivada)
            - dg(-a, derivada, outro))
    return sp.Rational(1, 2) * (dg(derivada, cima, outro) + dg(outro, cima, derivada)
                                - dg(cima, derivada, outro))


def metrizar(expr, espaco):
    """Cada Γ — e cada derivada de Γ — escrito pela métrica."""
    if espaco.conexao != "levi-civita" or not espaco.metrica:
        raise ChristoffelMalDefinido(
            "Γ só se escreve pela métrica para a conexão de Levi-Civita, e com "
            "a métrica declarada: \\nabla = levi-civita e g = métrica")
    nome, conv = espaco.christoffel
    if isinstance(expr, sp.Equality):
        return sp.Eq(metrizar(expr.lhs, espaco), metrizar(expr.rhs, espaco),
                     evaluate=False)

    def trocar(t):
        operacoes, base = REGISTRO.get(t.head.name, ((), t.head.name))
        if base != nome or any(o != "d" for o in operacoes):
            return t
        indices = list(t.indices)
        k = len(operacoes)
        dentro = indices[k:]
        if any(dentro[conv[s]].is_up for s in ("derivada", "outro")):
            return t                    # slots de baixo levantados: fica
        valor = _metrico(espaco, dentro[conv["cima"]], dentro[conv["derivada"]],
                         dentro[conv["outro"]])
        for op, i in zip(reversed(operacoes), reversed(indices[:k])):
            valor = derivar(valor, op, i, espaco)
        return valor

    return _mapear(expr, trocar)


# ------------------------------------------------------- o determinante

def simbolo_det(espaco):
    """det g como símbolo, com o sinal que a assinatura dá: (−1)^s. Sem
    assinatura, só real e não nulo — e |g| fica |g|."""
    nome = espaco.determinante
    if espaco.assinatura:
        s = sum(1 for x in espaco.assinatura if x < 0)
        return sp.Symbol(nome, negative=True) if s % 2 else sp.Symbol(nome, positive=True)
    return sp.Symbol(nome, real=True, nonzero=True)


def _nos_coeficientes(expr, f):
    if isinstance(expr, TensAdd):
        return _soma([_nos_coeficientes(a, f) for a in expr.args])
    if isinstance(expr, TensMul):
        fatores = [a for a in expr.args if isinstance(a, TensExpr)]
        return f(escalar_de(expr)) * functools.reduce(operator.mul, fatores)
    if isinstance(expr, TensExpr):
        return expr
    return f(sp.sympify(expr))


def jacobi(expr, espaco):
    """∂_λ det g = det g · g^{μν} ∂_λ g_{μν} — a fórmula de Jacobi, que é o
    que "determinante" quer dizer. E o sinal de det g, se a assinatura o dá."""
    from .derivadas import base_escalar
    if espaco is None or not espaco.determinante or not espaco.metrica:
        return expr
    nome = espaco.determinante
    h = simbolo_det(espaco)
    com_sinal = lambda c: c.subs(sp.Symbol(nome), h)
    expr = _nos_coeficientes(expr, com_sinal)
    if not isinstance(expr, TensExpr):
        return expr
    base_det = base_escalar(nome, espaco)
    g = espaco.cabeca(espaco.metrica, 2)

    def trocar(t):
        operacoes, base = REGISTRO.get(t.head.name, ((), None))
        if base != base_det:
            return t
        indices = list(t.indices)
        a, b = _mudo(espaco), _mudo(espaco)
        valor = h * g(a, b) * derivar(g(-a, -b), "d", indices[-1], espaco)
        for op, i in zip(reversed(operacoes[:-1]), reversed(indices[:-1])):
            valor = derivar(valor, op, i, espaco)
        return valor

    for _ in range(4):
        novo = _nos_coeficientes(_mapear(expr, trocar), com_sinal)
        if novo == expr or not isinstance(novo, TensExpr):
            return novo
        expr = novo
    return expr


# ------------------------------------------------------------ linearizar

EPSILON = sp.Symbol("epsilon")


def linearizar(expr, espaco, h):
    """g = η + εh, até a primeira ordem em ε.

    Depois de `metrizar`, a métrica só aparece como g explícito e como ∂g. A
    troca é: g_{ab} → g_{ab} + εh_{ab}; g^{ab} → g^{ab} − εh^{ab} (a inversa,
    até primeira ordem); g^a{}_b é δ, e fica; ∂g → ε∂h. Daí em diante g é o
    fundo η, constante, e sobe e desce os índices de h — como na teoria
    linearizada. Os termos de ordem ε² ou mais saem.
    """
    if isinstance(expr, sp.Equality):
        return sp.Eq(linearizar(expr.lhs, espaco, h),
                     linearizar(expr.rhs, espaco, h), evaluate=False)
    if not isinstance(expr, TensExpr):
        return expr
    g = espaco.metrica
    H = espaco.cabeca(h, 2)

    def trocar(t):
        operacoes, base = REGISTRO.get(t.head.name, ((), t.head.name))
        if base != g:
            return t
        indices = list(t.indices)
        if not operacoes:
            a, b = indices
            if a.is_up != b.is_up:
                return t
            return t + (EPSILON if not a.is_up else -EPSILON) * H(a, b)
        if any(o != "d" for o in operacoes):
            return t
        k = len(operacoes)
        valor = H(*indices[k:])
        for op, i in zip(reversed(operacoes), reversed(indices[:k])):
            valor = derivar(valor, op, i, espaco)
        return EPSILON * valor

    expr = _mapear(expr, trocar)
    if isinstance(expr, TensExpr):
        expr = expr.expand()
    return _truncar(expr)


def _truncar(expr, ordem=1):
    def corta(c):
        c = sp.expand(c)
        return sum((c.coeff(EPSILON, k) * EPSILON ** k for k in range(ordem + 1)),
                   sp.S.Zero)
    return _nos_coeficientes(expr, corta)
