r"""A ponte até os tensores do SymPy.

O parser de LaTeX do SymPy não tem notação de índice, e o que ele faz com ela é
o pior possível — `A^\mu` vira `A**mu`, `x^2_i` perde o índice, `g_{\mu\nu}`
vira um símbolo cujo nome tem um `*` dentro. Tudo bem formado, tudo falso.

Mas o SymPy TEM tensores, em `sympy.tensor.tensor`: índices com valência,
contração automática, canonicalização de Butler-Portugal. O que falta é a
ponte, e ela é este arquivo.

## O que decide se é índice

Nada na tipografia. `A^\mu` é "A elevado a μ" ou "A com índice contravariante
μ", e as duas se escrevem igual — foi por isso que o programa passou a recusar
em vez de adivinhar. Quem decide é a DECLARAÇÃO:

    \mu = índice

Declarado o índice, `A^\mu` deixa de ser ambíguo: não há potência possível com
um índice no expoente. É a mesma mecânica de `u = u(t,x)`, que dissolve a
dúvida do ∂ em vez de escolher entre as leituras.

## O que o SymPy cobra em troca

Consistência de índices, e cobra na hora. Somar termos com índices livres
diferentes levanta erro — `A^\mu B_\mu + C^\nu` não passa —, e isso é um erro
de relatividade que ninguém pega a olho.
"""

from __future__ import annotations

import functools
import operator
import re

import sympy as sp
from sympy.tensor.tensor import (TensAdd, TensExpr, TensorHead, TensorIndexType,
                                 tensor_indices)

DIMENSAO_PADRAO = 4
"""Quatro, porque quem escreve índice grego quase sempre escreve relatividade.
Declarável: `\\mu = índice(3)`."""

_SIMBOLO = r"(?:\\[a-zA-Z]+|[A-Za-z])"
_GRUPO = r"(?:\{[^{}]*\}|" + _SIMBOLO + r"|[0-9])"
_RE_FATOR = re.compile(rf"({_SIMBOLO})((?:\s*[_^]\s*{_GRUPO})+)")
_RE_PEDACO = re.compile(rf"\s*([_^])\s*({_GRUPO})")


def limpo(nome):
    return nome[1:] if nome.startswith("\\") else nome


class Espaco:
    """O tipo de índice do documento — um só, por ora.

    Um documento de relatividade tem um espaço-tempo, não vários. Quando
    precisar de mais de um (índices de grupo interno, por exemplo), a
    declaração é que vai dizer qual.
    """

    def __init__(self, dimensao=DIMENSAO_PADRAO, nome="L"):
        self.dimensao = dimensao
        self.tipo = TensorIndexType(nome, dim=dimensao)
        self._indices = {}
        self._cabecas = {}
        self._tipos = {}            # nome -> (formas, vetores), tipo do Schutz

    def indice(self, nome):
        if nome not in self._indices:
            # tensor_indices devolve o índice sozinho quando o nome é um só, e
            # uma lista quando são vários. Aceita os dois.
            achado = tensor_indices(nome, self.tipo)
            self._indices[nome] = achado[0] if isinstance(achado, list) else achado
        return self._indices[nome]

    def declarar(self, nome, formas, vetores):
        """O tipo do Schutz: (M, N) recebe M formas e N vetores.

        Um tensor do tipo (M/N) é uma função de M 1-formas e N vetores, o que
        em índices dá M em cima e N embaixo. g_{\u03bc\u03bd} é (0,2);
        g^{\u03bc\u03bd} é (2,0); a delta de Kronecker é (1,1).

        Declarar isso diz duas coisas que o uso não diz: o POSTO antes da
        primeira aparição, e a valência CANÔNICA — a partir da qual as outras
        se obtêm levantando ou baixando com a métrica.
        """
        self._tipos[nome] = (formas, vetores)
        return self.cabeca(nome, formas + vetores)

    def tipo_de(self, nome):
        return self._tipos.get(nome)

    def cabeca(self, nome, posto):
        """O TensorHead de `nome`, com o posto declarado ou o que o uso mostrou.

        Sem declaração, o posto vem do uso: quem escreve g_{\u03bc\u03bd} já
        disse que g tem dois índices. Com declaração, o posto vem de lá — e a
        diferença aparece na primeira linha, e não na segunda.
        """
        declarado = self._tipos.get(nome)
        if declarado and sum(declarado) != posto and nome in self._cabecas:
            formas, vetores = declarado
            raise ValueError(
                f"'{nome}' foi declarado do tipo ({formas},{vetores}), que tem "
                f"{formas + vetores} índice(s), e aqui aparece com {posto}")
        if nome in self._cabecas:
            cabeca, primeiro = self._cabecas[nome]
            if primeiro != posto:
                qual = (f"foi declarado com {primeiro}" if declarado
                        else f"apareceu com {primeiro}")
                raise ValueError(
                    f"'{nome}' {qual} índice(s) e agora com {posto}: "
                    f"um tensor tem um posto só")
            return cabeca
        cabeca = TensorHead(nome, [self.tipo] * posto)
        self._cabecas[nome] = (cabeca, posto)
        return cabeca


def indices_de(grupo):
    """Os índices escritos num grupo: '{\\mu\\nu}' -> ['mu', 'nu']."""
    dentro = grupo[1:-1] if grupo.startswith("{") else grupo
    return [limpo(t) for t in re.findall(_SIMBOLO, dentro)]


def localizar(latex, declarados):
    """Os fatores tensoriais do texto: (início, fim, base, [(nome, cima)]).

    Um fator é um nome seguido de índices, e só conta se TODOS os índices
    estiverem declarados. `x^2` não é fator — 2 não é índice; `A^\\mu` só é
    fator depois de alguém declarar `\\mu = índice`.
    """
    achados = []
    for m in _RE_FATOR.finditer(latex):
        posicoes = []
        for pedaco in _RE_PEDACO.finditer(m.group(2)):
            for nome in indices_de(pedaco.group(2)):
                posicoes.append((nome, pedaco.group(1) == "^"))
        if not posicoes or any(n not in declarados for n, _ in posicoes):
            continue
        achados.append((m.start(), m.end(), limpo(m.group(1)), posicoes))
    return achados


def desacordo_de_tipo(espaco, base, posicoes):
    """A valência escrita bate com a declarada?

    Não é erro escrever g^{\u03bc\u03bd} tendo declarado g do tipo (0,2): é a
    métrica inversa, obtida levantando os índices. Mas levantar exige métrica,
    e o Sucuri não a aplica sozinho — então o objeto que sai é OUTRO tensor com
    o mesmo nome, e vale dizer.
    """
    tipo = espaco.tipo_de(base)
    if not tipo:
        return None
    cima = sum(1 for _, c in posicoes if c)
    baixo = len(posicoes) - cima
    if (cima, baixo) == tipo:
        return None
    return (f"{base} foi declarado do tipo ({tipo[0]},{tipo[1]}) e aqui aparece "
            f"como ({cima},{baixo}): levantar ou baixar índice exige a métrica, "
            f"e o Sucuri não a aplica sozinho")


def construir(espaco, base, posicoes):
    """O objeto do SymPy: a cabeça aplicada aos índices, com valência."""
    cabeca = espaco.cabeca(base, len(posicoes))
    argumentos = [espaco.indice(n) if cima else -espaco.indice(n)
                  for n, cima in posicoes]
    return cabeca(*argumentos)


class IndicesIncompativeis(ValueError):
    """Termos somados com índices livres diferentes.

    A^\\mu B_\\mu + C^\\nu não é equação incompleta: é equação errada, e o erro
    é de relatividade, não de digitação. O SymPy recusa a soma, e a recusa é
    uma das coisas boas de atravessar a ponte — a olho ninguém vê.
    """

    def __init__(self):
        super().__init__(
            "os termos da soma têm índices livres diferentes. Some tensores de "
            "mesma valência: se um termo sobra com \u03bc livre e o outro não, "
            "a igualdade não é uma igualdade de tensores")


def reconstruir(expr, tensores):
    """Refaz a árvore multiplicando de verdade, em vez de substituir.

    `subs` não serve: trocar um símbolo por um tensor dentro de um Mul devolve
    um Mul comum, e a contração não acontece — os índices repetidos ficam lá,
    parados, e a expressão fica errada sem reclamar. Multiplicar de novo faz o
    SymPy montar o TensMul e contrair.
    """
    if not tensores:
        return expr

    def andar(e):
        if e in tensores:
            return tensores[e]
        if e.is_Mul:
            return functools.reduce(operator.mul, [andar(a) for a in e.args])
        if e.is_Add:
            return functools.reduce(operator.add, [andar(a) for a in e.args])
        if isinstance(e, sp.Equality):
            return sp.Eq(andar(e.lhs), andar(e.rhs))
        return e

    return andar(expr)


def livres(expr):
    """Os índices que sobraram sem par — a valência do que foi escrito."""
    if isinstance(expr, TensExpr):
        return [str(i) for i in expr.get_free_indices()]
    return []
