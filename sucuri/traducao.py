r"""De uma notação à outra: sem índice → com índice.

    indices(eq5)
        ∇_U ∇_U X = R(U,X)U
        →  U^α ∇_α (U^β ∇_β X^μ) = R^μ{}_{σαβ} U^σ U^α X^β

A prova sem índice é mais curta e não depende de carta; o livro de física
escreve com índice. Este arquivo é a ponte entre as duas, e as regras são as
que as declarações já fixaram:

    X            →  X^μ
    g(X, Y)      →  g_{αβ} X^α Y^β
    ω(X), T(X,Y) →  ω_α X^α, T_{αβ} X^α Y^β
    ∇_X Y        →  X^α ∇_α Y^μ              (Leibniz nos produtos)
    X(f)         →  X^α ∂_α f
    [X, Y]       →  X^α ∇_α Y^μ − Y^α ∇_α X^μ   (com Levi-Civita; sem, com ∂)
    R(U, X)W     →  na convenção de riemann(eq): o sinal e os slots da
                    definição escrita

## Onde entra uma suposição

R(U,X)W só se traduz se a mesma letra estiver declarada `curvatura` (sem
índice) e `riemann(eq)` (com índice). A ponte supõe então R(U,X) =
∇_U∇_X − ∇_X∇_U − ∇_{[U,X]}, que é como a definição com índice a lê — e diz
isso numa nota, em vez de supor calada.
"""

from __future__ import annotations

import functools
import operator

import sympy as sp
from sympy.tensor.tensor import TensExpr, TensorIndex

from .conexao import (VETOR, Avaliado, ColcheteDeLie, Curvatura,
                      DerivadaCovariante, Direcional, ParaTodo, e_vetor)
from .derivadas import derivar


class SemTraducao(ValueError):
    """O que ainda não tem tradução, ou não tem sem suposição que não se fez."""


class Tradutor:
    def __init__(self, espaco, tensores):
        self.espaco = espaco
        self.tensores = tensores
        self.notas = []
        self._n = 0

    def mudo(self):
        self._n += 1
        return TensorIndex(f"t_{self._n}", self.espaco.tipo)

    def _nabla(self, expr, indice):
        """∇_indice — o ∇ de ∇_X Y é o mesmo, com ou sem índice."""
        return derivar(expr, "D", indice, self.espaco)

    # ------------------------------------------------------- vetor → V^a

    def vetor(self, expr, a):
        """A expressão vetorial com o índice livre `a` (de cima)."""
        expr = sp.sympify(expr)
        if isinstance(expr, sp.Add):
            return _soma([self.vetor(t, a) for t in expr.args])
        if isinstance(expr, sp.Mul):
            vetoriais = [f for f in expr.args if e_vetor(f, self.tensores)]
            if len(vetoriais) != 1:
                raise SemTraducao(f"'{expr}' não é escalar vezes vetor")
            escalar = sp.Mul(*(f for f in expr.args if f is not vetoriais[0]))
            return self.escalar(escalar) * self.vetor(vetoriais[0], a)
        if isinstance(expr, sp.Symbol):
            if self.tensores.get(expr.name) != VETOR:
                raise SemTraducao(f"'{expr.name}' não é vetor declarado")
            return self.espaco.cabeca(expr.name, 1)(a)
        if isinstance(expr, DerivadaCovariante):
            if expr.acento:
                raise SemTraducao("a ponte para índices conhece uma ∇ só: "
                                  f"\\{expr.acento}{{\\nabla}} fica sem índice")
            b = self.mudo()
            return self.vetor(expr.direcao, b) * \
                self._nabla(self.vetor(expr.operando, a), -b)
        if isinstance(expr, ColcheteDeLie):
            A, B = expr.args
            b, c = self.mudo(), self.mudo()
            operacao = "D" if self.espaco.conexao == "levi-civita" else "d"
            if operacao == "d":
                self.notas.append(
                    "[X,Y] foi escrito com ∂: sem ∇ declarado sem torção, é "
                    "a forma que vale em qualquer carta")
            return (self.vetor(A, b) * derivar(self.vetor(B, a), operacao, -b,
                                               self.espaco)
                    - self.vetor(B, c) * derivar(self.vetor(A, a), operacao, -c,
                                                 self.espaco))
        if isinstance(expr, Curvatura):
            return self._curvatura(expr, a)
        raise SemTraducao(f"'{expr}' ainda não tem tradução para índices")

    def _curvatura(self, expr, a):
        nome = str(expr.nome)
        riemann = self.espaco.riemann
        if not riemann or riemann[0] != nome:
            raise SemTraducao(
                f"{nome}(U,X)W só se traduz com {nome} também definido com "
                f"índice — {nome} = riemann(eq) —, que é de onde vêm o sinal "
                f"e a ordem dos slots")
        conv = riemann[1]
        U, X, W = expr.args[1:]
        s, m, n = self.mudo(), self.mudo(), self.mudo()
        slots = [None] * 4
        slots[conv["rho"]], slots[conv["sigma"]] = a, -s
        slots[conv["mu"]], slots[conv["nu"]] = -m, -n
        R = self.espaco.cabeca(nome, 4)
        self.notas.append(
            f"{nome}(U,X)W traduzido supondo {nome}(U,X) = ∇_U∇_X − ∇_X∇_U − "
            f"∇_[U,X], sem torção — que é como a definição com índice o lê")
        return conv["sinal"] * R(*slots) * self.vetor(W, s) * \
            self.vetor(U, m) * self.vetor(X, n)

    # ------------------------------------------------------------ escalar

    def escalar(self, expr):
        expr = sp.sympify(expr)
        if expr.is_number or isinstance(expr, sp.Symbol):
            return expr
        if isinstance(expr, sp.Add):
            return _soma([self.escalar(t) for t in expr.args])
        if isinstance(expr, sp.Mul):
            return functools.reduce(operator.mul,
                                    [self.escalar(f) for f in expr.args])
        if isinstance(expr, sp.Pow) and expr.exp.is_number:
            return self.escalar(expr.base) ** expr.exp
        if isinstance(expr, Direcional):
            # X(f) = X^α ∇_α f: num escalar ∇ é ∂, e com ∇ o Leibniz nos
            # componentes fica covariante — ∇g some depois, com Levi-Civita.
            b = self.mudo()
            return self.vetor(expr.direcao, b) * \
                derivar(self.escalar(expr.escalar), "D", -b, self.espaco)
        if isinstance(expr, Avaliado):
            nome = str(expr.nome)
            indices = [self.mudo() for _ in expr.slots]
            T = self.espaco.cabeca(nome, len(indices))(*(-i for i in indices))
            return functools.reduce(operator.mul, [
                self.vetor(v, i) for v, i in zip(expr.slots, indices)], T)
        raise SemTraducao(f"'{expr}' ainda não tem tradução para índices")


def _soma(termos):
    termos = [t for t in termos if t != 0]
    return functools.reduce(operator.add, termos) if termos else sp.S.Zero


def traduzir(expr, espaco, tensores, livre):
    """(expressão com índice, notas). `livre` é o índice de cima que um
    resultado vetorial leva."""
    if isinstance(expr, ParaTodo):
        raise SemTraducao("∀ não se traduz: com índice, a identidade vale para "
                          "todo vetor sem precisar dizer — traduza uma "
                          "instância")
    from .formas import tem_forma
    if tem_forma(expr, tensores):
        raise SemTraducao("formas ainda não têm tradução para índices")
    t = Tradutor(espaco, tensores)
    lados = [expr.lhs, expr.rhs] if isinstance(expr, sp.Equality) else [expr]
    vetorial = any(e_vetor(l, tensores) or (
        isinstance(l, sp.Add) and any(e_vetor(x, tensores) for x in l.args))
        for l in lados)
    saida = []
    for l in lados:
        if l == 0:
            saida.append(sp.S.Zero)
        elif vetorial:
            saida.append(t.vetor(l, livre))
        else:
            saida.append(t.escalar(l))
    if isinstance(expr, sp.Equality):
        resultado = sp.Eq(saida[0], saida[1], evaluate=False)
    else:
        resultado = saida[0]
    return resultado, list(dict.fromkeys(t.notas))


def canonico(expr):
    """Expande e canonicaliza cada lado, sem simplificar a igualdade."""
    def um(e):
        return e.canon_bp() if isinstance(e, TensExpr) else e
    if isinstance(expr, sp.Equality):
        return sp.Eq(um(expr.lhs), um(expr.rhs), evaluate=False)
    return um(expr)
