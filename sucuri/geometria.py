r"""A métrica com componentes, e o que se calcula a partir dela.

A notação de índice diz a ESTRUTURA — que g tem dois índices embaixo, que
A^\mu B_\mu está contraído. Não diz o que g VALE. Para Christoffel, Ricci e
Riemann é preciso o outro lado: componentes num sistema de coordenadas.

O SymPy tem isso em `sympy.diffgeom`, e calcula Schwarzschild inteiro em
segundos. O que faltava era dizer a métrica em LaTeX, porque o parser não lê
matriz — `\begin{pmatrix}` levanta erro. Então se diz pela diagonal, que é
como os livros dão quase todas as métricas que importam:

    x = coordenadas(t, r, \theta, \phi)
    g = métrica(-(1 - 2M/r), 1/(1 - 2M/r), r^2, r^2\sin^2\theta)

## O que estes números são

Componentes num sistema de coordenadas, e não o tensor. Trocar de coordenadas
troca todos eles; o que não muda são as afirmações invariantes — Ricci nulo é
Ricci nulo em qualquer carta. Por isso o resultado diz em que coordenadas está.
"""

from __future__ import annotations

import sympy as sp
from sympy.diffgeom import (CoordSystem, Manifold, Patch, TensorProduct,
                            metric_to_Christoffel_2nd,
                            metric_to_Ricci_components,
                            metric_to_Riemann_components)


class Metrica:
    """Uma métrica diagonal, com as suas coordenadas."""

    def __init__(self, nome, coordenadas, componentes, escrita=None):
        if len(coordenadas) != len(componentes):
            raise ValueError(
                f"{len(coordenadas)} coordenada(s) e {len(componentes)} "
                f"componente(s): a diagonal tem de ter uma entrada por "
                f"coordenada")
        self.nome = nome
        self.escrito = nome             # com a barra, se foi escrito `\\eta`
        self.escrita = escrita or {}    # 'theta' -> '\\theta', como foi escrito
        self.simbolos = list(coordenadas)
        self.componentes = list(componentes)

        self.variedade = Manifold(f"M_{nome}", len(coordenadas))
        self.carta = Patch(f"P_{nome}", self.variedade)
        self.sistema = CoordSystem("x", self.carta, self.simbolos)

        # As componentes vêm escritas nos símbolos das coordenadas; o diffgeom
        # trabalha com as FUNÇÕES de coordenada. Trocar uma pela outra é o que
        # liga o que a pessoa escreveu ao que a biblioteca usa.
        troca = dict(zip(self.simbolos, self.sistema.coord_functions()))
        formas = self.sistema.base_oneforms()
        self.tensor = sum(
            (c.subs(troca, simultaneous=True) * TensorProduct(f, f)
             for c, f in zip(self.componentes, formas)),
            sp.S.Zero)

    @property
    def coordenadas(self):
        """Como foram escritas, e não como o SymPy as chama."""
        return ", ".join(self.escrita.get(str(s), str(s))
                         for s in self.simbolos)

    def matriz(self):
        return sp.diag(*self.componentes)


def _rotulo(simbolos, indices, cima=1, escrita=None):
    """Γ^r_{\\theta\\theta} em vez de Γ[1,2,2].

    O índice é a COORDENADA, não a posição no arranjo — e escrita como a pessoa
    escreveu, que é o que distingue \\theta de theta na hora de ler.
    """
    escrita = escrita or {}
    # Cada índice nas suas chaves: `\theta` colado em `r` vira o macro
    # inexistente `\thetar`, e o que aparece na tela é vermelho.
    nomes = ["{" + escrita.get(str(simbolos[i]), str(simbolos[i])) + "}"
             for i in indices]
    if cima:
        return "^" + nomes[0] + "_{" + "".join(nomes[1:]) + "}"
    return "_{" + "".join(nomes) + "}"


def nao_nulas(arranjo, simbolos, posto, cima=1, escrita=None):
    """As componentes que não são zero, com o índice escrito por extenso.

    Mostrar as 64 componentes de Christoffel, das quais 55 são zero, é esconder
    as nove que importam. Um livro mostra as nove.
    """
    n = len(simbolos)
    saida = []
    for indices in _combinacoes(n, posto):
        valor = sp.simplify(arranjo[indices])
        if valor != 0:
            saida.append((_rotulo(simbolos, indices, cima, escrita), valor))
    return saida


def _combinacoes(n, posto):
    if posto == 0:
        yield ()
        return
    for i in range(n):
        for resto in _combinacoes(n, posto - 1):
            yield (i,) + resto


def christoffel(metrica):
    return nao_nulas(metric_to_Christoffel_2nd(metrica.tensor),
                     metrica.simbolos, 3, escrita=metrica.escrita)


def ricci(metrica):
    return nao_nulas(metric_to_Ricci_components(metrica.tensor),
                     metrica.simbolos, 2, cima=0, escrita=metrica.escrita)


def riemann(metrica):
    return nao_nulas(metric_to_Riemann_components(metrica.tensor),
                     metrica.simbolos, 4, escrita=metrica.escrita)


def escalar(metrica):
    """O escalar de Ricci: R = g^{\\mu\\nu} R_{\\mu\\nu}."""
    R = metric_to_Ricci_components(metrica.tensor)
    inversa = metrica.matriz().inv()
    n = len(metrica.simbolos)
    return sp.simplify(sum(inversa[i, j] * R[i, j]
                           for i in range(n) for j in range(n)))
