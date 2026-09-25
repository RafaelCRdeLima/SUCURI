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
import itertools
import operator
import re

import sympy as sp
from sympy.tensor.tensor import (TensAdd, TensExpr, TensorHead, TensorIndexType,
                                 TensorSymmetry, tensor_indices)

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
        self.escrita = {}           # 'mu' -> '\\mu', como o usuário escreveu
        self._indices = {}
        self._cabecas = {}
        self._tipos = {}            # nome -> (formas, vetores), tipo do Schutz
        self._simetrias = {}        # nome -> 'simetrico' | 'antissimetrico'
        self.metrica = None         # o nome declarado como A métrica

    def indice(self, nome):
        if nome not in self._indices:
            # tensor_indices devolve o índice sozinho quando o nome é um só, e
            # uma lista quando são vários. Aceita os dois.
            achado = tensor_indices(nome, self.tipo)
            self._indices[nome] = achado[0] if isinstance(achado, list) else achado
        return self._indices[nome]

    def declarar(self, nome, formas, vetores, simetria=None):
        """O tipo do Schutz: (M, N) recebe M formas e N vetores.

        Um tensor do tipo (M/N) é uma função de M 1-formas e N vetores, o que
        em índices dá M em cima e N embaixo. g_{\u03bc\u03bd} é (0,2);
        g^{\u03bc\u03bd} é (2,0); a delta de Kronecker é (1,1).

        Declarar isso diz duas coisas que o uso não diz: o POSTO antes da
        primeira aparição, e a valência CANÔNICA — a partir da qual as outras
        se obtêm levantando ou baixando com a métrica.
        """
        self._tipos[nome] = (formas, vetores)
        if simetria:
            self._simetrias[nome] = simetria
        return self.cabeca(nome, formas + vetores)

    def definir_metrica(self, nome):
        r"""Diz qual das cabeças é A métrica do espaço — não uma (0,2) qualquer.

        Baixar índice é `A_\mu \equiv g_{\mu\nu}A^\nu`: uma CONVENÇÃO, e que só
        vale para a métrica. Aplicá-la a um tensor (0,2) qualquer produziria
        uma expressão bem formada e falsa, que é a pior classe de erro que este
        programa conhece. Por isso é declaração, e não adivinhação pelo nome.
        """
        # Simétrica sem precisar dizer: é o que se chama de métrica.
        cabeca = self.declarar(nome, 0, 2, "simetrico")
        self.tipo.set_metric(cabeca)
        self.metrica = nome
        return cabeca

    def cabeca_metrica(self):
        return self._cabecas[self.metrica][0] if self.metrica else None

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
        cabeca = TensorHead(nome, [self.tipo] * posto,
                            _simetria(self._simetrias.get(nome), posto))
        self._cabecas[nome] = (cabeca, posto)
        return cabeca


SIMETRIAS = ("simetrico", "antissimetrico", "riemann")


def _simetria(qual, posto):
    """A simetria do SymPy — que é o que alimenta a canonicalização."""
    if qual == "simetrico":
        return TensorSymmetry.fully_symmetric(posto)
    if qual == "antissimetrico":
        return TensorSymmetry.fully_symmetric(-posto)
    if qual == "riemann":
        return TensorSymmetry.riemann()
    return TensorSymmetry.no_symmetry(posto)


def problema_de_simetria(formas, vetores, simetria):
    """Por que a simetria declarada não cabe no tipo — ou None.

    Trocar um índice de cima com um de baixo não é operação: para compará-los
    é preciso baixar um deles, e isso é a métrica, não o tensor. E um slot só
    não tem com quem trocar.
    """
    if not simetria:
        return None
    if formas and vetores:
        dica = (" — o Riemann com as simetrias é o (0,4), R_{abcd}"
                if simetria == "riemann" else "")
        return (f"simetria entre índice de cima e de baixo, num ({formas},"
                f"{vetores}), só existe depois de baixar um deles com a "
                f"métrica — e aí é outro tensor. Declare a simetria no tipo "
                f"com os índices todos do mesmo lado{dica}")
    if formas + vetores < 2:
        return "com um slot só não há o que trocar"
    if simetria == "riemann" and formas + vetores != 4:
        return (f"as simetrias do Riemann são de quatro slots — dois pares "
                f"antissimétricos que trocam entre si —, e aqui há "
                f"{formas + vetores}")
    return None


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
    # A métrica é a exceção, e não por conveniência: g^{\mu\nu} É a inversa e
    # g^\mu{}_\nu É a delta — notação corrente, não valência trocada. E agora
    # há `contrair`, que aplica a convenção de fato; avisar que "o Sucuri não a
    # aplica sozinho" seria mentir sobre o próprio programa.
    if base == espaco.metrica and len(posicoes) == 2:
        return None
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


class SimetrizacaoMalFormada(ValueError):
    """Um (…) ou […] nos índices que não fecha, aninha, ou mistura cima e
    baixo — onde a leitura não teria como ser uma só."""


_RE_TOKEN = re.compile(r"\\[a-zA-Z]+|[A-Za-z]|[()\[\]|]")


def simetrizacoes(fator):
    r"""[(tipo, [posições])] — os (…) e […] nos índices de um fator.

    `T_{(\mu
u)}` dá [('(', [0, 1])]; `T_{[\mu|ho|
u]}` dá
    [('[', [0, 2])], porque o que está entre barras fica de fora. As posições
    são dos slots, na ordem escrita — as mesmas de `construir`.
    """
    m = _RE_FATOR.match(fator.strip())
    if m is None:
        return []
    grupos, aberto, excluindo, slot = [], None, False, 0
    for pedaco in _RE_PEDACO.finditer(m.group(2)):
        cima = pedaco.group(1) == "^"
        grupo = pedaco.group(2)
        dentro = grupo[1:-1] if grupo.startswith("{") else grupo
        for tok in _RE_TOKEN.findall(dentro):
            if tok in "([":
                if aberto:
                    raise SimetrizacaoMalFormada(
                        f"'{tok}' dentro de '{aberto[0]}' nos índices de "
                        f"{fator.strip()}: simetrização aninhada não se lê "
                        f"de um jeito só")
                aberto = (tok, [], cima)
            elif tok in ")]":
                par = {")": "(", "]": "["}[tok]
                if not aberto or aberto[0] != par:
                    raise SimetrizacaoMalFormada(
                        f"'{tok}' sem o '{par}' correspondente nos índices de "
                        f"{fator.strip()}")
                if excluindo:
                    raise SimetrizacaoMalFormada(
                        f"barra aberta antes de '{tok}' em {fator.strip()}")
                grupos.append((aberto[0], aberto[1]))
                aberto = None
            elif tok == "|":
                if not aberto:
                    raise SimetrizacaoMalFormada(
                        f"'|' fora de (…) ou […] em {fator.strip()}: a barra "
                        f"só exclui índice de uma simetrização")
                excluindo = not excluindo
            else:
                if aberto and not excluindo:
                    if aberto[2] != cima:
                        raise SimetrizacaoMalFormada(
                            f"a simetrização em {fator.strip()} junta índice "
                            f"de cima com de baixo — trocá-los pede a métrica, "
                            f"e aí é outro tensor")
                    aberto[1].append(slot)
                slot += 1
    if aberto:
        raise SimetrizacaoMalFormada(
            f"'{aberto[0]}' sem fechar nos índices de {fator.strip()}")
    for tipo, slots in grupos:
        if len(slots) < 2:
            raise SimetrizacaoMalFormada(
                f"{tipo}…{')' if tipo == '(' else ']'} com {len(slots)} "
                f"índice em {fator.strip()}: não há o que trocar")
    return grupos


def simetrizar(tensor, grupos):
    r"""T_{(\mu
u)} = ½(T_{\mu
u} + T_{
u\mu}); T_{[\mu
u]} com o sinal.

    O fator é 1/n! — o de Wald, MTW e Carroll, com que T_{(\mu
u)} = T_{\mu
u}
    quando T já é simétrico.
    """
    cabeca = tensor.head
    termos = [(sp.S.One, list(tensor.get_indices()))]
    for tipo, slots in grupos:
        n = len(slots)
        novos = []
        for coef, indices in termos:
            for perm in itertools.permutations(range(n)):
                sinal = 1
                if tipo == "[":
                    inversoes = sum(1 for i in range(n) for j in range(i + 1, n)
                                    if perm[i] > perm[j])
                    sinal = -1 if inversoes % 2 else 1
                novo = list(indices)
                for k, p in enumerate(perm):
                    novo[slots[k]] = indices[slots[p]]
                novos.append((coef * sinal / sp.factorial(n), novo))
        termos = novos
    return functools.reduce(operator.add,
                            [c * cabeca(*indices) for c, indices in termos])


class SemMetrica(ValueError):
    r"""Pedir para contrair sem ter dito qual é a métrica.

    A informação que falta não é calculável: nenhuma inspeção de
    `g_{\mu\nu}A^\nu` diz se aquele `g` é a métrica do espaço ou um tensor
    (0,2) com o nome infeliz. Só a declaração diz.
    """

    def __init__(self):
        super().__init__(
            "não sei qual é a métrica: declare `g = métrica` (ou "
            "`g = métrica(componentes)`) antes de contrair. Baixar índice é "
            "convenção da métrica, e não de um (0,2) qualquer")


def contrair(expr, espaco):
    r"""`g_{\mu\nu}A^\nu` vira `A_\mu` — baixar o índice, de fato.

    O SymPy faz o colapso em `contract_metric`, mas só reconhece como métrica a
    cabeça que o espaço registrou. Sem `g = métrica`, recusa.
    """
    if espaco is None or espaco.metrica is None:
        raise SemMetrica()
    if not isinstance(expr, TensExpr):
        return expr
    return expr.contract_metric(espaco.cabeca_metrica())


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


def mudos_na_ordem(texto, declarados):
    """Os índices contraídos, na ordem em que aparecem no que foi escrito.

    Contraído é o que aparece em cima E embaixo. A ordem importa porque é ela
    que casa com a numeração dos índices mudos do SymPy.
    """
    cima, baixo, ordem = set(), set(), []
    for _, _, _, posicoes in localizar(texto, set(declarados)):
        for nome, eh_cima in posicoes:
            (cima if eh_cima else baixo).add(nome)
            if nome not in ordem:
                ordem.append(nome)
    return [n for n in ordem if n in cima and n in baixo]


def latex_de(expr, espaco=None, mudos=()):
    r"""O LaTeX do tensor, com os índices que a pessoa escreveu.

    O SymPy renomeia todo índice contraído para L_0, L_1 — e faz certo: índice
    mudo é nome ligado, e qualquer letra serve. Mas quem escreveu 
u quer ver
    
u, e não L_0.

    E há um estrago junto: o impressor emite os índices colados, então
    g{}_{\mu L_{0}} sai como "\muL_{0}" — a macro \mu engole o L e vira \muL,
    que não existe. O KaTeX pinta de vermelho, e a equação parece errada
    quando o que está errado é a impressão dela. Devolver as letras originais
    conserta os dois, porque letra grega é macro e macro não cola em macro.
    """
    texto = sp.latex(expr)
    if espaco is None or not isinstance(expr, TensExpr):
        return texto
    for k, nome in enumerate(mudos):
        escrito = espaco.escrita.get(nome, nome)
        texto = texto.replace(f"{espaco.tipo.dummy_name}_{{{k}}}", escrito)
    return texto


def livres(expr, espaco=None):
    r"""Os índices que sobraram sem par — a valência do que foi escrito.

    Devolvidos como se escrevem: ^\mu para contravariante, _\mu para
    covariante. O SymPy diz 'mu' e '-mu', que é nome interno — e mostrar nome
    interno faz o usuário procurar o que ele mesmo escreveu.
    """
    if not isinstance(expr, TensExpr):
        return []
    saida = []
    for i in expr.get_free_indices():
        nome = str(i)
        baixo = nome.startswith("-")
        nome = nome[1:] if baixo else nome
        if espaco is not None:
            nome = espaco.escrita.get(nome, nome)
        saida.append(("_" if baixo else "^") + nome)
    return saida
