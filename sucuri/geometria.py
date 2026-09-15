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
        # E o caminho de volta. O que sai do diffgeom vem em CAMPOS ESCALARES,
        # não em símbolos: `sstr` imprime `r` e engana, mas `latex` imprime
        # `\mathbf{r}` e `free_symbols` não vê coordenada nenhuma. Quem lê a
        # componente quer o r que escreveu.
        self.de_volta = {f: x for x, f in troca.items()}
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


def nao_nulas(arranjo, simbolos, posto, cima=1, escrita=None, de_volta=None):
    r"""As componentes que não são zero, com o índice escrito por extenso.

    Mostrar as 64 componentes de Christoffel, das quais 55 são zero, é esconder
    as nove que importam. Um livro mostra as nove.

    E devolve SÍMBOLOS: o campo escalar do diffgeom imprime como `r` em texto e
    como `\mathbf{r}` em LaTeX, então a componente parecia certa na tela e saía
    errada no que se copiava.
    """
    n = len(simbolos)
    saida, todas = [], {}
    for indices in _combinacoes(n, posto):
        valor = sp.simplify(arranjo[indices])
        if de_volta:
            valor = sp.simplify(valor.subs(de_volta, simultaneous=True))
        rotulo = _rotulo(simbolos, indices, cima, escrita)
        todas[rotulo] = valor
        if valor != 0:
            saida.append((rotulo, valor))
    # As nulas vão juntas, mas à parte: não entram na tabela (55 zeros escondem
    # as nove que importam) e mesmo assim se procuram pelo rótulo. Responder
    # "não conheço" a uma componente que existe e vale zero seria mentir.
    return saida, todas


def _combinacoes(n, posto):
    if posto == 0:
        yield ()
        return
    for i in range(n):
        for resto in _combinacoes(n, posto - 1):
            yield (i,) + resto


def christoffel(metrica):
    return nao_nulas(metric_to_Christoffel_2nd(metrica.tensor),
                     metrica.simbolos, 3, escrita=metrica.escrita,
                     de_volta=metrica.de_volta)


def ricci(metrica):
    return nao_nulas(metric_to_Ricci_components(metrica.tensor),
                     metrica.simbolos, 2, cima=0, escrita=metrica.escrita,
                     de_volta=metrica.de_volta)


def riemann(metrica):
    return nao_nulas(metric_to_Riemann_components(metrica.tensor),
                     metrica.simbolos, 4, escrita=metrica.escrita,
                     de_volta=metrica.de_volta)


def escalar(metrica):
    """O escalar de Ricci: R = g^{\\mu\\nu} R_{\\mu\\nu}."""
    R = metric_to_Ricci_components(metrica.tensor)
    inversa = metrica.matriz().inv()
    n = len(metrica.simbolos)
    bruto = sum(inversa[i, j] * R[i, j] for i in range(n) for j in range(n))
    return sp.simplify(sp.sympify(bruto).subs(metrica.de_volta,
                                              simultaneous=True))


def _simbolo_componente(base, coordenada, cima):
    """`A^t`, `A_theta` — a componente que ninguém declarou, com um nome.

    Sem componentes de A, a única coisa honesta a fazer é chamá-las pelo nome:
    A^t, A^r, … Assim o que sai é a RELAÇÃO — A_t em função de A^t —, que é o
    que um livro escreve quando baixa um índice de um vetor qualquer.

    O nome vai na convenção do próprio SymPy — `A__t` em cima, `A_t` embaixo —,
    e não em `A^t`, que reentra como "A elevado a t". O que sai da tela tem de
    poder voltar para dentro do programa sem mudar de sentido.
    """
    return sp.Symbol(f"{base}{'__' if cima else '_'}{coordenada}")


def componentes(expr, espaco, metrica):
    r"""As componentes de uma expressão tensorial, na carta da métrica.

    `g_{\mu\nu}A^\nu` com Schwarzschild devolve as quatro componentes de
    A_\mu — cada uma em função das de A^\mu, que ninguém declarou e por isso
    entram como nomes.

    Só funciona onde há componentes: a métrica precisa ter sido declarada com
    elas. A notação de índice sozinha diz a estrutura, não o valor.
    """
    from .tensores import livres

    if espaco is None or espaco.metrica is None:
        raise ValueError(
            "não sei qual é a métrica: declare `g = métrica(componentes)` "
            "antes de avaliar componentes")
    if len(metrica.simbolos) != espaco.dimensao:
        raise ValueError(
            f"a métrica tem {len(metrica.simbolos)} coordenada(s) e os índices "
            f"são de dimensão {espaco.dimensao}: declare `índices"
            f"({len(metrica.simbolos)})` para os dois falarem do mesmo espaço")

    troca = {}
    cabeca_g = espaco.cabeca_metrica()
    i, j = espaco.indice("_c0"), espaco.indice("_c1")
    troca[cabeca_g(-i, -j)] = metrica.matriz()

    escritas = [metrica.escrita.get(str(s), str(s)) for s in metrica.simbolos]
    nomes = [str(s) for s in metrica.simbolos]
    for nome, (cabeca, posto) in espaco._cabecas.items():
        if nome == espaco.metrica:
            continue
        if posto != 1:
            raise ValueError(
                f"'{nome}' tem {posto} índices: por ora só sei dar componentes "
                f"de vetor e da métrica")
        tipo = espaco.tipo_de(nome) or (1, 0)
        canonico = bool(tipo[0])
        # A valência ESCRITA pode não ser a canônica: `A_\mu` já contraído é o
        # mesmo A, com o índice descido. Quem desce é a métrica, e aqui ela
        # está em componentes — então descemos nós, em vez de devolver o
        # "No metric provided to lower index" do SymPy na cara de quem pediu.
        escrito = _posicao_escrita(expr, cabeca, canonico)
        valores = [_simbolo_componente(nome, c, canonico) for c in nomes]
        if escrito != canonico:
            matriz = (metrica.matriz() if canonico else metrica.matriz().inv())
            valores = [sp.simplify(sum(matriz[i, j] * valores[j]
                                       for j in range(len(nomes))))
                       for i in range(len(nomes))]
        indice = espaco.indice("_c2")
        troca[cabeca(indice if escrito else -indice)] = valores

    soltos = livres(expr, espaco) or []
    if len(soltos) != 1:
        raise ValueError(
            "sei dar componentes de expressão com um índice livre; esta tem "
            f"{len(soltos)}")
    ordem = [espaco.indice("_s0") if soltos[0].startswith("^")
             else -espaco.indice("_s0")]
    bruto = expr.replace_with_arrays(troca, ordem)

    alto = soltos[0].startswith("^")
    return [(f"{_base_de(expr, espaco)}{'^' if alto else '_'}{{{escrito}}}",
             sp.simplify(valor))
            for escrito, valor in zip(escritas, bruto)]


def _posicao_escrita(expr, cabeca, padrao):
    """O índice daquela cabeça aparece em cima ou embaixo, no que foi escrito?"""
    from sympy.tensor.tensor import Tensor

    for arg in sp.preorder_traversal(expr):
        if isinstance(arg, Tensor) and arg.head == cabeca:
            return arg.get_indices()[0].is_up
    return padrao


def _base_de(expr, espaco):
    """O nome que sobra depois da contração — o que a linha está descrevendo."""
    from sympy.tensor.tensor import Tensor

    for arg in sp.preorder_traversal(expr):
        if isinstance(arg, Tensor) and arg.head.name != espaco.metrica:
            return arg.head.name
    return "T"
