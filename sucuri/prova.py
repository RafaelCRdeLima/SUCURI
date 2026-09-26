r"""Provar uma igualdade da conexão a partir de hipóteses declaradas.

    provar(eq5, eq1, eq2, eq3, eq4)

A primeira é o que se quer provar; as outras são as hipóteses — e SÓ elas.
Nada do que está no caderno entra por estar lá: escrever uma equação não é
afirmá-la, e uma prova que usasse a conta de rascunho da linha de cima seria
prova de coisa nenhuma.

## O que o motor sabe sozinho

Só o que vale para QUALQUER conexão, em qualquer livro:

- ∇_U X é linear em U sobre funções, ∇_{fU} X = f ∇_U X, e no operando segue
  Leibniz: ∇_U (fX) = U(f) X + f ∇_U X;
- o colchete de Lie é antissimétrico, e com funções também segue Leibniz:
  [fA, gB] = fg[A,B] + f A(g) B − g B(f) A;
- U(f) é linear em U sobre funções e segue a regra da cadeia em f, e o
  colchete age numa função como [A,B](f) = A(B(f)) − B(A(f));
- g(X,Y), a métrica, é linear sobre funções em cada slot e simétrica — como
  todo (0,n) aplicado, ω(U), T(U,X), é linear em cada slot;
- a curvatura R(U,X)W é linear sobre funções nos três argumentos — é um
  tensor, e isso não depende da convenção.

O resto — torção nula, a DEFINIÇÃO de R, que a curva é geodésica — tem de vir
das hipóteses. O sinal de R em particular: sem a definição declarada, nada se
prova sobre R, e é assim que a convenção é declarada em vez de suposta.

## Como a prova é achada

Tudo vira combinação linear de termos que não se decompõem mais. Cada hipótese
é uma relação linear entre eles, e das hipóteses saem outras aplicando os
contextos que aparecem no problema: se ∇_U X = ∇_X U, então também
∇_U∇_U X = ∇_U∇_X U. A prova é achar uma combinação dessas relações que dê o
objetivo — álgebra linear, e o resultado é um CERTIFICADO: cada passo diz de
que hipótese veio e o que se fez com ela, e a soma é conferida de novo, do
zero, antes de dizer "provado".

## Quando não acha

Não achar não é prova de que é falso. A busca vai até uma profundidade finita
de contextos, e pode faltar hipótese. O motor diz as duas coisas.
"""

from __future__ import annotations

import itertools

import sympy as sp
from sympy.core.sorting import default_sort_key

from .conexao import (VETOR, Avaliado, AvaliadoAntissimetrico,
                      AvaliadoRiemann, AvaliadoSimetrico, ColcheteDeLie,
                      Curvatura,
                      DerivadaCovariante, Direcional, ParaTodo, e_vetor,
                      tem_tensor)

LIMITE_RELACOES = 4000
"""Quantas relações derivadas a busca aceita antes de desistir."""

LIMITE_INSTANCIAS = 300
"""Quantas instâncias das hipóteses com ∀ a busca aceita."""

RODADAS = 3
"""Até quantas vezes as instâncias novas podem gerar instâncias de novo.

A busca tenta com uma rodada e só aprofunda se não achar: cada rodada
multiplica as relações, e a maioria das provas não precisa da segunda."""

_OPERADORES = (DerivadaCovariante, ColcheteDeLie, Curvatura)

ESCALAR = sp.S.One
"""A chave de uma relação ESCALAR: {1: c} diz c = 0, como {X: c} diz cX = 0."""


class NaoEVetorial(ValueError):
    """A equação não é entre campos vetoriais, e o motor só sabe desses."""


# ------------------------------------------------------------ forma linear

def _nulo(c):
    c = sp.sympify(c)
    # simplify é caro, e quase todo coeficiente aqui é número.
    return c == 0 if c.is_number else sp.simplify(c) == 0


def _limpo(c):
    c = sp.sympify(c)
    return c if c.is_number else sp.simplify(c)


def _soma(*dicts):
    total = {}
    for d in dicts:
        for t, c in d.items():
            total[t] = total.get(t, 0) + c
    return {t: c for t, c in total.items() if not _nulo(c)}


def _vezes(c, d):
    return {t: c * v for t, v in d.items()}


def _constante(c):
    return sp.sympify(c).is_number


_MEMORIA = {}


def linear(expr, tensores):
    """{termo: coeficiente} — a expressão como combinação linear.

    Os termos são os que não se decompõem mais: vetores declarados, e os
    operadores aplicados a termos. Os coeficientes são escalares.
    """
    expr = sp.sympify(expr)
    chave = (expr, frozenset(tensores.items()))
    if chave not in _MEMORIA:
        if len(_MEMORIA) > 50000:
            _MEMORIA.clear()
        _MEMORIA[chave] = _linear(expr, tensores)
    return dict(_MEMORIA[chave])


def _linear(expr, tensores):
    if expr == 0:
        return {}
    if isinstance(expr, sp.Add):
        return _soma(*(linear(a, tensores) for a in expr.args))
    if isinstance(expr, sp.Mul):
        vetoriais = [a for a in expr.args if _vetorial(a, tensores)]
        if len(vetoriais) != 1:
            raise NaoEVetorial(
                f"'{expr}' não é escalar vezes vetor: tem "
                f"{len(vetoriais)} fatores vetoriais")
        escalar = sp.Mul(*(a for a in expr.args if a is not vetoriais[0]))
        return _vezes(escalar_normal(escalar, tensores),
                      linear(vetoriais[0], tensores))
    if isinstance(expr, sp.Symbol):
        if not e_vetor(expr, tensores):
            raise NaoEVetorial(f"'{expr}' não é vetor declarado")
        return {expr: sp.S.One}
    if isinstance(expr, DerivadaCovariante):
        return _nabla(expr, tensores)
    if isinstance(expr, ColcheteDeLie):
        return _lie(expr, tensores)
    if isinstance(expr, Curvatura):
        return _curvatura(expr, tensores)
    raise NaoEVetorial(f"'{expr}' não é campo vetorial")


def _vetorial(expr, tensores):
    return tem_tensor(expr, tensores)


# ------------------------------------------------------------------ escalares
#
# Todo símbolo que não é número é tratado como FUNÇÃO, e não constante. É o
# lado seguro: se c for constante, U(c) = 0 é só um caso particular, e a prova
# que precisar disso pede a hipótese — nunca sai uma prova errada por supor
# constante o que variava.

def escalar_normal(expr, tensores):
    """O escalar com cada U(f) e cada g(X,Y) em forma normal.

    U(fg) = U(f)g + fU(g), (U+X)(f) = U(f) + X(f); g(fX + Y, Z) =
    f g(X,Z) + g(Y,Z), e a métrica com os slots em ordem canônica, porque
    g(X,Y) = g(Y,X).
    """
    expr = sp.sympify(expr)
    achados = {}
    for a in expr.atoms(Direcional, Avaliado):
        if isinstance(a, Direcional):
            achados[a] = direcional(linear(a.direcao, tensores),
                                    escalar_normal(a.escalar, tensores),
                                    tensores)
        else:
            achados[a] = avaliado(a, tensores)
    return expr.xreplace(achados) if achados else expr


def avaliado(a, tensores):
    """T(Σ c U, …) = Σ c … T(U, …): um (0,n) é linear sobre funções em cada
    slot — é um tensor. Simétrico (a métrica, ou o declarado), os slots vão
    para a ordem canônica; antissimétrico, também, com o sinal da permutação,
    e slot repetido dá zero."""
    total = sp.S.Zero
    for combinacao in _produto([linear(s, tensores) for s in a.slots]):
        coef = sp.Mul(*(c for _, c in combinacao))
        slots = [t for t, _ in combinacao]
        if isinstance(a, (AvaliadoSimetrico, AvaliadoAntissimetrico)):
            ordem = sorted(range(len(slots)),
                           key=lambda i: default_sort_key(slots[i]))
            canonicos = [slots[i] for i in ordem]
            if isinstance(a, AvaliadoAntissimetrico):
                if len(set(slots)) < len(slots):
                    continue
                coef *= _sinal(ordem)
            slots = canonicos
        elif isinstance(a, AvaliadoRiemann):
            sinal, slots = _canonico_riemann(slots)
            if sinal == 0:
                continue
            coef *= sinal
        total += coef * type(a)(a.nome, *slots)
    return sp.expand(total)


def _grupo_riemann():
    """As 8 permutações dos slots que as simetrias do Riemann geram, com sinal.

    Geradores: trocar o primeiro par (−), trocar o segundo (−), trocar os
    pares (+). A identidade cíclica não é permutação — não entra aqui.
    """
    geradores = [((1, 0, 2, 3), -1), ((0, 1, 3, 2), -1), ((2, 3, 0, 1), 1)]
    grupo = {((0, 1, 2, 3), 1)}
    while True:
        novos = {(tuple(p[q[i]] for i in range(4)), s * t)
                 for p, s in grupo for q, t in geradores} - grupo
        if not novos:
            return sorted(grupo)
        grupo |= novos


GRUPO_RIEMANN = _grupo_riemann()


def _canonico_riemann(slots):
    """(sinal, slots) do representante canônico — sinal 0 se a expressão é
    zero, porque a órbita contém os mesmos slots com os dois sinais."""
    orbita = {}
    for perm, sinal in GRUPO_RIEMANN:
        imagem = tuple(slots[i] for i in perm)
        if orbita.get(imagem, sinal) != sinal:
            return 0, slots
        orbita[imagem] = sinal
    canonico = min(orbita, key=lambda s: tuple(default_sort_key(x) for x in s))
    return orbita[canonico], list(canonico)


def _sinal(permutacao):
    """+1 ou −1: a paridade, contando as inversões."""
    inversoes = sum(1 for i in range(len(permutacao))
                    for j in range(i + 1, len(permutacao))
                    if permutacao[i] > permutacao[j])
    return -1 if inversoes % 2 else 1


def _produto(listas):
    """Todas as escolhas de um (termo, coef) de cada dicionário."""
    if not listas:
        return [[]]
    return [[par] + resto for par in listas[0].items()
            for resto in _produto(listas[1:])]


def _atomos_escalares(expr, tensores):
    """Do que o escalar depende: os U(f), os g(X,Y), e os símbolos soltos.

    O que está DENTRO de U(f) ou de g(X,Y) não entra: o g e o X de g(X,Y) não
    são funções de que o escalar dependa, são o nome e o slot.
    """
    compostos = set(expr.atoms(Direcional, Avaliado))
    solto = expr.xreplace({a: sp.Dummy() for a in compostos})
    return compostos | {s for s in solto.free_symbols
                        if not isinstance(s, sp.Dummy) and s.name not in tensores}


def direcional(direcao, escalar, tensores):
    """Σ_d c_d · d(escalar), pela regra da cadeia, com `direcao` já linear.

    Na direção é linear sobre funções: (fU)(g) = f U(g). No argumento, a regra
    da cadeia sobre os átomos: U(φ(f, g)) = φ_f U(f) + φ_g U(g).
    """
    escalar = sp.sympify(escalar)
    if escalar.is_number:
        return sp.S.Zero
    atomos = sorted(_atomos_escalares(escalar, tensores), key=default_sort_key)
    total = sp.S.Zero
    mudos = {a: sp.Dummy() for a in atomos}
    aberto = escalar.xreplace(mudos)
    for a, m in mudos.items():
        parcial = sp.diff(aberto, m).xreplace({v: k for k, v in mudos.items()})
        if parcial == 0:
            continue
        for td, cd in direcao.items():
            if isinstance(td, ColcheteDeLie):
                # [A,B](f) = A(B(f)) − B(A(f)): é o que o colchete É, agindo
                # numa função — a definição, não uma convenção.
                p, q = td.args
                um = {p: sp.S.One}
                outro = {q: sp.S.One}
                total += cd * parcial * (
                    direcional(um, direcional(outro, a, tensores), tensores)
                    - direcional(outro, direcional(um, a, tensores), tensores))
            else:
                total += cd * parcial * Direcional(td, a)
    return sp.expand(total)


def _nabla(expr, tensores):
    direcao = linear(expr.direcao, tensores)
    operando = linear(expr.operando, tensores)
    total = {}
    for td, cd in direcao.items():
        # Na direção, linear sobre funções: qualquer coeficiente sai.
        for to, co in operando.items():
            parcela = {DerivadaCovariante(td, to): cd * co}
            if not _constante(co):
                # Leibniz: ∇_U(fX) = U(f)X + f∇_U X.
                parcela = _soma(parcela, {to: cd * direcional(
                    {td: sp.S.One}, co, tensores)})
            total = _soma(total, parcela)
    return total


def _lie(expr, tensores):
    a, b = (linear(x, tensores) for x in expr.args)
    total = {}
    for ta, ca in a.items():
        for tb, cb in b.items():
            if ta == tb:
                parcela = {}                            # [U, U] = 0
            elif default_sort_key(tb) < default_sort_key(ta):
                parcela = {ColcheteDeLie(tb, ta): -ca * cb}   # antissimetria
            else:
                parcela = {ColcheteDeLie(ta, tb): ca * cb}
            # [fA, gB] = fg[A,B] + f A(g) B − g B(f) A
            if not _constante(cb):
                parcela = _soma(parcela, {tb: ca * direcional(
                    {ta: sp.S.One}, cb, tensores)})
            if not _constante(ca):
                parcela = _soma(parcela, {ta: -cb * direcional(
                    {tb: sp.S.One}, ca, tensores)})
            total = _soma(total, parcela)
    return total


def _curvatura(expr, tensores):
    nome = expr.nome
    u, x, w = (linear(a, tensores) for a in expr.args[1:])
    total = {}
    for tu, cu in u.items():
        for tx, cx in x.items():
            for tw, cw in w.items():
                total = _soma(total, {Curvatura(nome, tu, tx, tw): cu * cx * cw})
    return total


def relacao(equacao, tensores):
    """A equação como relação `{termo: coef} = 0` — ou `{1: c}`, se escalar."""
    from .formas import normal, tem_forma
    if tem_forma(equacao, tensores):
        # Formas: os termos são monômios exteriores (ω, dω, ω∧η…), e o escalar
        # é o monômio vazio — a mesma chave 1 das relações escalares.
        lhs, rhs = ((equacao.lhs, equacao.rhs)
                    if isinstance(equacao, sp.Equality) else (equacao, 0))
        return {t: c for t, c in normal(lhs - rhs, tensores).items()
                if not _nulo(c)}
    if _e_escalar(equacao, tensores):
        lhs, rhs = ((equacao.lhs, equacao.rhs)
                    if isinstance(equacao, sp.Equality) else (equacao, 0))
        c = sp.expand(escalar_normal(lhs - rhs, tensores))
        return {} if _nulo(c) else {ESCALAR: c}
    if isinstance(equacao, sp.Equality):
        return _soma(linear(equacao.lhs, tensores),
                     _vezes(-1, linear(equacao.rhs, tensores)))
    return linear(equacao, tensores)


# ----------------------------------------------------------------- contextos

class Contexto:
    """Um lugar com buraco: ∇_U □, ∇_□ W, [□, X], R(U,X)□…

    `sobre_funcoes` diz se é linear sobre funções, ou só sobre constantes.
    Os segundos (∇_U □, [U, □]) também recebem relação com coeficiente que
    varia: `_aplicar` os preenche com a combinação inteira, e a regra de
    Leibniz é aplicada ao expandir.

    `de` e `para` dizem o que entra e o que sai — vetor ou escalar. U(□) leva
    escalar em escalar; (□)(f), vetor em escalar; □·X, escalar em vetor.
    """

    def __init__(self, preencher, rotulo, latex, sobre_funcoes,
                 de="vetor", para="vetor"):
        self.preencher = preencher
        self.rotulo = rotulo            # com '{}' no lugar do buraco
        self.latex = latex
        self.sobre_funcoes = sobre_funcoes
        self.de = de                    # o que o buraco recebe
        self.para = para                # o que sai

    def chave(self):
        return self.rotulo


def _contextos_de(termo, achados):
    s = sp.sstr
    if isinstance(termo, DerivadaCovariante):
        u, x = termo.direcao, termo.operando
        achados.append(Contexto(lambda h, x=x: DerivadaCovariante(h, x),
                                f"nabla_{{{{}}}}({s(x)})",
                                rf"\nabla_{{{{{{}}}}}} {sp.latex(x)}", True))
        achados.append(Contexto(lambda h, u=u: DerivadaCovariante(u, h),
                                f"nabla_{s(u)}({{}})",
                                rf"\nabla_{{{sp.latex(u)}}}\left({{}}\right)",
                                False))
    elif isinstance(termo, ColcheteDeLie):
        a, b = termo.args
        achados.append(Contexto(lambda h, b=b: ColcheteDeLie(h, b),
                                f"[{{}}, {s(b)}]",
                                rf"\left[{{}}, {sp.latex(b)}\right]", False))
        achados.append(Contexto(lambda h, a=a: ColcheteDeLie(a, h),
                                f"[{s(a)}, {{}}]",
                                rf"\left[{sp.latex(a)}, {{}}\right]", False))
    elif isinstance(termo, Curvatura):
        r, u, x, w = termo.args
        n = s(r)
        achados.append(Contexto(lambda h, r=r, x=x, w=w: Curvatura(r, h, x, w),
                                f"{n}({{}}, {s(x)})({s(w)})",
                                rf"{n}\left({{}}, {sp.latex(x)}\right) {sp.latex(w)}",
                                True))
        achados.append(Contexto(lambda h, r=r, u=u, w=w: Curvatura(r, u, h, w),
                                f"{n}({s(u)}, {{}})({s(w)})",
                                rf"{n}\left({sp.latex(u)}, {{}}\right) {sp.latex(w)}",
                                True))
        achados.append(Contexto(lambda h, r=r, u=u, x=x: Curvatura(r, u, x, h),
                                f"{n}({s(u)}, {s(x)})({{}})",
                                rf"{n}\left({sp.latex(u)}, {sp.latex(x)}\right) {{}}",
                                True))
    else:
        return
    for arg in termo.args:
        for sub in sp.preorder_traversal(arg):
            if isinstance(sub, _OPERADORES):
                _contextos_de(sub, achados)


def contextos(relacoes, alvo=None, tensores=None):
    achados = []
    for rel in relacoes:
        for termo in rel:
            _contextos_de(termo, achados)
    s, L = sp.sstr, sp.latex
    for d in sorted({a for rel in relacoes for c in rel.values()
                     for a in sp.sympify(c).atoms(Direcional)},
                    key=default_sort_key):
        u, h = d.direcao, d.escalar
        achados.append(Contexto(lambda x, u=u: Direcional(u, x),
                                f"{s(u)}({{}})", rf"{L(u)}\left({{}}\right)",
                                False, "escalar", "escalar"))
        achados.append(Contexto(lambda v, h=h: Direcional(v, h),
                                f"({{}})({s(h)})", rf"\left({{}}\right)\left({L(h)}\right)",
                                True, "vetor", "escalar"))
    for a in sorted({a for rel in relacoes for c in rel.values()
                     for a in sp.sympify(c).atoms(Avaliado)}, key=default_sort_key):
        for i in range(len(a.slots)):
            def encher(v, a=a, i=i):
                slots = list(a.slots)
                slots[i] = v
                return type(a)(a.nome, *slots)
            marcas = [s(x) for x in a.slots]
            marcas[i] = "{}"
            marcas_l = [L(x) for x in a.slots]
            marcas_l[i] = "{}"
            achados.append(Contexto(
                encher, f"{s(a.nome)}({', '.join(marcas)})",
                rf"{L(a.nome)}\left({', '.join(marcas_l)}\right)",
                True, "vetor", "escalar"))
    if alvo:
        # Multiplicar por uma função, e levar um escalar a um vetor: só com o
        # que o objetivo tem, que é onde a multiplicação pode servir.
        atomos = set()
        for c in alvo.values():
            atomos |= _atomos_escalares(sp.sympify(c), tensores or {})
        atomos = {a for a in atomos
                  if not (isinstance(a, sp.Symbol) and a.name in (tensores or {}))}
        for a in sorted(atomos, key=default_sort_key):
            for tipo in ("vetor", "escalar"):
                c = Contexto(lambda x, a=a: a * x, f"{s(a)}·{{}}",
                             rf"{L(a)}\,{{}}", True, tipo, tipo)
                c.multiplica = True
                achados.append(c)
        for t in sorted((t for t in alvo if t != ESCALAR), key=default_sort_key):
            achados.append(Contexto(lambda x, t=t: x * t,
                                    f"{{}}·{s(t)}", rf"{{}}\,{L(t)}",
                                    True, "escalar", "vetor"))
    _contextos_de_formas(relacoes, alvo, tensores or {}, achados)
    unicos = {}
    for c in achados:
        unicos.setdefault(c.chave(), c)
    return list(unicos.values())


def _contextos_de_formas(relacoes, alvo, tensores, achados):
    """d □, ι_X □ e α ∧ □ — quando o problema tem forma."""
    from .formas import (CHAVE, Cunha, DerivadaExterior, Interior, _atomos_de,
                         tem_forma)
    if not any(tem_forma(t, tensores) for r in relacoes for t in r
               if t != ESCALAR):
        return
    L = sp.latex
    achados.append(Contexto(lambda x: DerivadaExterior(x), "d({})",
                            r"\mathrm{d}\left({}\right)", True,
                            "qualquer", "forma"))
    vetores = sorted((sp.Symbol(n) for n, t in tensores.items()
                      if n != CHAVE and t == VETOR), key=default_sort_key)
    for X in vetores:
        achados.append(Contexto(lambda x, X=X: Interior(X, x),
                                f"iota_{X}({{}})",
                                rf"\iota_{{{L(X)}}}\left({{}}\right)", True,
                                "qualquer", "forma"))
    for t in (alvo or {}):
        for a in _atomos_de(t) if t != ESCALAR else ():
            achados.append(Contexto(lambda x, a=a: Cunha(a, x),
                                    f"{sp.sstr(a)} ^ {{}}",
                                    rf"{L(a)} \wedge {{}}", True,
                                    "qualquer", "forma"))


def _profundidade(termo):
    if not isinstance(termo, _OPERADORES + (Direcional, Avaliado)):
        return 0
    return 1 + max(_profundidade(a) for a in termo.args)


def _profundidade_rel(rel):
    termos = [t for t in rel if t != ESCALAR]
    termos += [a for c in rel.values()
               for a in sp.sympify(c).atoms(Direcional, Avaliado)]
    return max((_profundidade(t) for t in termos), default=0)


# -------------------------------------------------------------- a busca

class Derivada:
    """Uma relação e de onde ela veio: a hipótese e os contextos aplicados."""

    def __init__(self, relacao, hipotese, contextos=(), instancia=None):
        self.relacao = relacao
        self.hipotese = hipotese        # o rótulo: 'eq3'
        self.contextos = tuple(contextos)
        self.instancia = instancia      # [(variável, termo)], se veio de ∀

    def _trocas(self):
        """Só as que mudam algo: eq1[A→A, B→B] é eq1, e dizer mais é ruído."""
        return [(v, t) for v, t in (self.instancia or []) if v != t]

    def chave(self):
        return frozenset((t, _limpo(c)) for t, c in self.relacao.items())

    def rotulo(self):
        texto = self.hipotese
        if self._trocas():
            texto += "[" + ", ".join(f"{v}→{sp.sstr(t)}"
                                     for v, t in self._trocas()) + "]"
        for c in self.contextos:
            texto = c.rotulo.replace("{}", texto)
        return texto

    def rotulo_latex(self):
        texto = rf"\text{{{self.hipotese}}}"
        if self._trocas():
            texto += (r"\left[" + r",\ ".join(
                rf"{sp.latex(v)} \mapsto {sp.latex(t)}"
                for v, t in self._trocas()) + r"\right]")
        for c in self.contextos:
            texto = c.latex.replace("{}", texto)
        return texto


def _e_rel_escalar(rel):
    return set(rel) == {ESCALAR}


def _aplicar(contexto, derivada, tensores):
    rel = derivada.relacao
    if contexto.de != "qualquer" and \
            (contexto.de == "escalar") != _e_rel_escalar(rel):
        return None
    # O contexto recebe a combinação INTEIRA, e não termo a termo: ∇_U(fX) não
    # é f∇_U X, e é `linear` — com Leibniz — quem sabe expandir.
    if _e_rel_escalar(rel):
        expressao = contexto.preencher(rel[ESCALAR])
    else:
        expressao = contexto.preencher(sp.Add(*(c * t for t, c in rel.items())))
    from .formas import normal, tem_forma
    de_formas = any(tem_forma(t, tensores) for t in rel if t != ESCALAR)
    if de_formas and contexto.de == "vetor" and \
            not getattr(contexto, "multiplica", False):
        return None             # ∇_□ X, (□)(f): o buraco pede vetor, não forma
    if contexto.para == "forma" or de_formas or tem_forma(expressao, tensores):
        # Multiplicar uma relação de formas por f, ou pô-la num contexto de
        # formas: quem expande é a forma normal, não `linear`, que só sabe de
        # campos vetoriais.
        nova = {t: c for t, c in normal(expressao, tensores).items()
                if not _nulo(c)}
    elif contexto.para == "escalar":
        c = sp.expand(escalar_normal(expressao, tensores))
        nova = {} if _nulo(c) else {ESCALAR: c}
    else:
        nova = linear(expressao, tensores)
    if not nova:
        return None
    return Derivada(nova, derivada.hipotese,
                    derivada.contextos + (contexto,), derivada.instancia)


class Prova:
    """O certificado: cada passo, o coeficiente, e a soma conferida."""

    def __init__(self, objetivo, passos, hipoteses_usadas):
        self.objetivo = objetivo        # a equação, como foi lida
        self.passos = passos            # [(número, Derivada)]
        self.hipoteses_usadas = hipoteses_usadas


class SemProva(Exception):
    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


def provar(objetivo, hipoteses, tensores):
    """Uma `Prova` de `objetivo` a partir de `hipoteses` ({rótulo: equação}).

    Levanta `SemProva` quando não acha — dizendo que não achar não é refutar.
    """
    if objetivo is sp.true:
        # `A = A`: o SymPy já decidiu na leitura, e não há o que provar.
        return Prova(objetivo, [], [])
    if objetivo is sp.false:
        raise SemProva("a igualdade já é falsa na leitura — os dois lados "
                       "são diferentes e nada neles varia")
    corpo = objetivo
    if isinstance(objetivo, ParaTodo):
        # Provar para todo W é provar para um W qualquer, sobre o qual nada se
        # sabe além de ser vetor — e nenhuma hipótese fala dele.
        tensores = {**tensores, **{v.name: VETOR for v in objetivo.variaveis}}
        corpo = objetivo.corpo

    base, gerais = [], []
    for rotulo, eq in hipoteses.items():
        if isinstance(eq, ParaTodo):
            gerais.append((rotulo, eq))
        else:
            base.append(Derivada(relacao(eq, tensores), rotulo))

    alvo = relacao(corpo, tensores)
    if not alvo:
        return Prova(objetivo, [], [])

    base = [d for d in base if d.relacao]
    if not gerais:
        return _buscar(objetivo, alvo, hipoteses, base, tensores)
    for rodadas in range(1, RODADAS + 1):
        try:
            return _buscar(objetivo, alvo, hipoteses, base + _instancias(
                gerais, [alvo] + [d.relacao for d in base], tensores, rodadas),
                tensores)
        except SemProva as e:
            ultima = e
    raise ultima


def _e_escalar(eq, tensores):
    from .formas import CHAVE
    tensores = {k: v for k, v in tensores.items() if k != CHAVE}
    if isinstance(eq, sp.Equality):
        return not (tem_tensor(eq.lhs, tensores) or tem_tensor(eq.rhs, tensores))
    return not tem_tensor(eq, tensores)


def _coordenadas(rel):
    """A relação em coordenadas NUMÉRICAS: {(monômio, termo): número}.

    É isto que impede a divisão por função. Combinar relações com
    coeficientes que são funções seria dividir por elas quando preciso — e de
    fX = fU sairia X = U, que é falso onde f se anula. Com monômios como
    coordenadas, a combinação é só com números; multiplicar por uma função é
    um contexto explícito (f·□), que aparece na prova.
    """
    coord = {}
    for t, c in rel.items():
        for m, q in sp.expand(c).as_coefficients_dict().items():
            chave = (m, t)
            coord[chave] = coord.get(chave, 0) + q
    return {k: q for k, q in coord.items() if q != 0}


def _buscar(objetivo, alvo, hipoteses, base, tensores):
    """A busca, com as hipóteses já instanciadas.

    Cada relação que aparece entra numa base escalonada, e o objetivo é
    testado logo em seguida: a busca para assim que a prova existe, em vez de
    gerar todas as relações para só então resolver um sistema com todas elas.
    """
    todos = [alvo] + [d.relacao for d in base]
    lugares = contextos(todos, alvo, tensores)
    profundidade = max(1, max(_profundidade_rel(r) for r in todos))
    from .formas import tem_forma
    com_formas = any(tem_forma(t, tensores) for r in todos for t in r
                     if t != ESCALAR)
    if com_formas:
        profundidade = max(profundidade, 2)

    # O universo: os termos que o problema tem, e os que estão a UM contexto
    # deles. Relação derivada que sai disso não serve para nada que a prova
    # precise — e sem esta poda as instâncias trazem termos, os termos trazem
    # contextos, e a busca não acaba.
    presentes = {t for t in _chao(todos, tensores) if _e_termo(t, tensores)}
    universo = presentes | {c.preencher(t) for c in lugares for t in presentes
                            if c.de == c.para == "vetor"}
    universo = ({t for u in universo for t in linear(u, tensores)} | presentes
                | {ESCALAR})

    escalonada = _Escalonada()
    derivadas = []
    alvo_coord = _coordenadas(alvo)

    def entra(d):
        derivadas.append(d)
        escalonada.juntar(_coordenadas(d.relacao), len(derivadas) - 1)
        return escalonada.combinacao(alvo_coord)

    conhecidas = {}
    for d in base:
        if d.chave() in conhecidas:
            continue
        conhecidas[d.chave()] = d
        achou = entra(d)
        if achou is not None:
            return _pronta(objetivo, alvo, hipoteses, derivadas, achou)

    fronteira = list(conhecidas.values())
    for _ in range(profundidade):
        nova_fronteira = []
        for d in fronteira:
            for c in lugares:
                # Termo a termo primeiro, que a memória de `linear` faz barato:
                # a maioria dos contextos leva para fora do universo, e montar
                # a relação inteira para depois jogá-la fora era o grosso do
                # tempo.
                if (c.de == c.para == "vetor" and not com_formas
                        and not _e_rel_escalar(d.relacao)
                        and not all(u in universo for t in d.relacao
                                    for u in linear(c.preencher(t), tensores))):
                    continue
                n = _aplicar(c, d, tensores)
                if n is None or n.chave() in conhecidas:
                    continue
                if not com_formas and not all(t in universo for t in n.relacao):
                    continue
                conhecidas[n.chave()] = n
                nova_fronteira.append(n)
                achou = entra(n)
                if achou is not None:
                    return _pronta(objetivo, alvo, hipoteses, derivadas, achou)
                if len(conhecidas) > LIMITE_RELACOES:
                    raise SemProva(
                        f"a busca passou de {LIMITE_RELACOES} relações sem "
                        f"achar; não achar não é prova de que é falso")
        fronteira = nova_fronteira

    faltam = sorted({sp.sstr(t) for t in alvo if t != ESCALAR}
                    - {sp.sstr(t) for d in derivadas for t in d.relacao})
    dica = (f" Nenhuma hipótese fala de {', '.join(faltam)}."
            if faltam else "")
    raise SemProva(
        "não achei combinação das hipóteses que dê isto." + dica +
        " Não achar não é prova de que é falso: pode faltar hipótese, ou "
        "a prova pedir mais do que a linearidade e as hipóteses dão.")


def _pronta(objetivo, alvo, hipoteses, derivadas, combinacao):
    passos = [(v, derivadas[k]) for k, v in sorted(combinacao.items())]
    _conferir(alvo, passos)
    # Na ordem em que foram dadas, e não na da busca: quem lê confere a
    # lista contra a chamada que escreveu.
    tocadas = {d.hipotese for _, d in passos}
    usadas = [h for h in hipoteses if h in tocadas]
    return Prova(objetivo, passos, usadas)


class _Escalonada:
    """Eliminação de Gauss esparsa e incremental, guardando de onde veio cada
    linha.

    Cada linha nova chega reduzida pelas anteriores, então não contém pivô de
    nenhuma delas; reduzir sempre pelo pivô da linha MAIS ANTIGA só introduz
    pivôs de linhas mais novas, e a redução termina.
    """

    def __init__(self):
        self.linhas = {}            # pivô -> (vetor, {índice: coeficiente})
        self.ordem = {}             # pivô -> quando entrou

    def reduzir(self, vetor, combo):
        vetor, combo = dict(vetor), dict(combo)
        while True:
            pivos = [t for t in vetor if t in self.linhas]
            if not pivos:
                return vetor, combo
            t = min(pivos, key=self.ordem.__getitem__)
            linha, origem = self.linhas[t]
            fator = vetor[t] / linha[t]
            vetor = _soma(vetor, _vezes(-fator, linha))
            combo = _soma(combo, _vezes(-fator, origem))

    def juntar(self, vetor, indice):
        vetor, combo = self.reduzir(vetor, {indice: sp.S.One})
        if not vetor:
            return
        pivo = max(vetor, key=default_sort_key)
        self.ordem[pivo] = len(self.ordem)
        self.linhas[pivo] = (vetor, combo)

    def combinacao(self, alvo):
        """{índice: λ} com Σ λ·relação = alvo, ou None se ainda não dá."""
        resto, combo = self.reduzir(alvo, {})
        if resto:
            return None
        # alvo − Σ f·linha = 0, e combo acumulou −f·origem: o sinal volta.
        return {k: -v for k, v in combo.items()}


# ---------------------------------------------------------------- instâncias

def _chao(relacoes, tensores):
    """Os termos concretos do problema — onde um ∀ pode pousar.

    Os vetoriais, e também os escalares compostos, U(f) e g(X,Y): é neles que
    pousa uma hipótese como a compatibilidade com a métrica.
    """
    achados = set()
    for rel in relacoes:
        raizes = [t for t in rel if t != ESCALAR]
        raizes += [a for c in rel.values()
                   for a in sp.sympify(c).atoms(Direcional, Avaliado)]
        for termo in raizes:
            for sub in sp.preorder_traversal(termo):
                if _e_termo(sub, tensores) or isinstance(sub, (Direcional,
                                                               Avaliado)):
                    achados.add(sub)
    return achados


def _e_termo(expr, tensores):
    return (isinstance(expr, _OPERADORES)
            or (isinstance(expr, sp.Symbol) and tensores.get(expr.name) == VETOR))


def _casar(padrao, termo, variaveis, sub, tensores):
    """A substituição que faz `padrao` virar `termo`, ou None."""
    if padrao in variaveis:
        if padrao in sub:
            return sub if sub[padrao] == termo else None
        return {**sub, padrao: termo} if _e_termo(termo, tensores) else None
    if not padrao.has(*variaveis):
        return sub if padrao == termo else None
    if type(padrao) is not type(termo) or len(padrao.args) != len(termo.args):
        return None
    ordens = [termo.args]
    if isinstance(termo, (AvaliadoSimetrico, AvaliadoAntissimetrico)):
        # g(X,Y) = g(Y,X), F(X,Y) = −F(Y,X): o casamento só acha a
        # substituição, e a instância é normalizada de novo, com o sinal.
        ordens = [(termo.args[0],) + p
                  for p in itertools.permutations(termo.args[1:])]
    elif isinstance(termo, AvaliadoRiemann):
        slots = termo.args[1:]
        ordens = [(termo.args[0],) + tuple(slots[i] for i in perm)
                  for perm, _ in GRUPO_RIEMANN]
    if isinstance(termo, ColcheteDeLie):
        # O colchete foi posto em ordem canônica pela antissimetria, e a ordem
        # depende dos NOMES: [A,[B,C]] pode ter virado −[[B,C],A] no padrão e
        # não no problema. O casamento só acha a substituição; a instância é
        # montada da equação original e normalizada de novo, com o sinal certo.
        ordens.append(termo.args[::-1])
    for args in ordens:
        tentativa = sub
        for p, t in zip(padrao.args, args):
            tentativa = _casar(p, t, variaveis, tentativa, tensores)
            if tentativa is None:
                break
        else:
            return tentativa
    return None


def _instancias(gerais, relacoes, tensores, rodadas=1):
    """As hipóteses com ∀, instanciadas onde o problema as toca.

    Não se instancia com tudo: casa-se cada termo da hipótese com os termos
    que aparecem no problema — `R(A,B)W` com `R(U,X)U` dá A=U, B=X, W=U. É o
    que um matemático faz ao ler a definição: aplica ao caso que tem na mão.
    Casamento que não fixa todas as variáveis não vira instância: completar
    com todos os vetores à mão multiplicava a busca por nada.
    """
    chao = _chao(relacoes, tensores)
    feitas, novas = set(), []
    for _ in range(rodadas):
        rodada = []
        for rotulo, eq in gerais:
            variaveis = eq.variaveis
            locais = {**tensores, **{v.name: VETOR for v in variaveis}}
            padrao = relacao(eq.corpo, locais)
            achadas = set()
            candidatos = [p for p in padrao if p != ESCALAR]
            candidatos += [a for c in padrao.values()
                           for a in sp.sympify(c).atoms(Direcional, Avaliado)]
            for p in candidatos:
                if not (isinstance(p, _OPERADORES + (Direcional, Avaliado))
                        and p.has(*variaveis)):
                    continue
                for t in chao:
                    s = _casar(p, t, variaveis, {}, tensores)
                    if s and len(s) == len(variaveis):
                        achadas.add(frozenset(s.items()))
            for achada in sorted(achadas, key=lambda s: sp.sstr(sorted(s, key=str))):
                for sub in (dict(achada),):
                    chave = (rotulo, frozenset(sub.items()))
                    if chave in feitas:
                        continue
                    feitas.add(chave)
                    if len(feitas) > LIMITE_INSTANCIAS:
                        raise SemProva(
                            f"as hipóteses com ∀ passaram de "
                            f"{LIMITE_INSTANCIAS} instâncias sem achar; não "
                            f"achar não é prova de que é falso")
                    rel = relacao(eq.corpo.xreplace(sub), tensores)
                    if rel:
                        rodada.append(Derivada(
                            rel, rotulo,
                            instancia=[(v, sub[v]) for v in variaveis]))
        if not rodada:
            break
        novas += rodada
        chao |= _chao([d.relacao for d in rodada], tensores)
    return novas


def _conferir(alvo, passos):
    """A soma é conferida de novo, do zero: o certificado não é de confiança.

    E os coeficientes da combinação têm de ser NÚMEROS — multiplicar por
    função só por contexto explícito, nunca escondido num coeficiente.
    """
    if not all(sp.sympify(v).is_number for v, _ in passos):
        raise AssertionError(
            "defeito do Sucuri: coeficiente de combinação que não é número")
    soma = _soma(*(_vezes(v, d.relacao) for v, d in passos))
    resto = _coordenadas(_soma(soma, _vezes(-1, alvo)))
    if resto:
        raise AssertionError(
            f"defeito do Sucuri: a combinação achada não confere (sobra {resto})")


def _latex_relacao(rel):
    if not rel:
        return "0 = 0"
    return sp.latex(sp.Add(*(c * t for t, c in rel.items()))) + " = 0"


def linhas(prova):
    """A prova como tabela: [rótulo, texto, latex] por passo."""
    saida = []
    for v, d in prova.passos:
        coef = "" if v == 1 else ("−" if v == -1 else f"{v} ·")
        expressao = sp.Add(*(c * t for t, c in d.relacao.items()))
        saida.append([f"{coef} {d.rotulo()}".strip(),
                      f"{sp.sstr(expressao)} = 0",
                      (("-" if v == -1 else "" if v == 1 else sp.latex(v) + r"\,\cdot\,")
                       + d.rotulo_latex() + r":\quad " + _latex_relacao(d.relacao))])
    return saida
