r"""Provar uma igualdade da conexão a partir de hipóteses declaradas.

    provar(eq5, eq1, eq2, eq3, eq4)

A primeira é o que se quer provar; as outras são as hipóteses — e SÓ elas.
Nada do que está no caderno entra por estar lá: escrever uma equação não é
afirmá-la, e uma prova que usasse a conta de rascunho da linha de cima seria
prova de coisa nenhuma.

## O que o motor sabe sozinho

Só o que vale para QUALQUER conexão, em qualquer livro:

- ∇_U X é linear em X sobre constantes, e linear em U sobre funções:
  ∇_{fU} X = f ∇_U X, mas ∇_U (fX) = U(f) X + f ∇_U X — e esta segunda o
  motor não expande, deixa como está;
- o colchete de Lie é bilinear sobre constantes e antissimétrico;
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

import sympy as sp
from sympy.core.sorting import default_sort_key

from .conexao import ColcheteDeLie, Curvatura, DerivadaCovariante, e_vetor

LIMITE_RELACOES = 4000
"""Quantas relações derivadas a busca aceita antes de desistir."""

_OPERADORES = (DerivadaCovariante, ColcheteDeLie, Curvatura)


class NaoEVetorial(ValueError):
    """A equação não é entre campos vetoriais, e o motor só sabe desses."""


# ------------------------------------------------------------ forma linear

def _soma(*dicts):
    total = {}
    for d in dicts:
        for t, c in d.items():
            total[t] = total.get(t, 0) + c
    return {t: c for t, c in total.items() if sp.simplify(c) != 0}


def _vezes(c, d):
    return {t: c * v for t, v in d.items()}


def _constante(c):
    return sp.sympify(c).is_number


def linear(expr, tensores):
    """{termo: coeficiente} — a expressão como combinação linear.

    Os termos são os que não se decompõem mais: vetores declarados, e os
    operadores aplicados a termos. Os coeficientes são escalares.
    """
    expr = sp.sympify(expr)
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
        return _vezes(escalar, linear(vetoriais[0], tensores))
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
    return (isinstance(expr, _OPERADORES)
            or any(s.name in tensores for s in expr.free_symbols))


def _nabla(expr, tensores):
    direcao = linear(expr.direcao, tensores)
    operando = linear(expr.operando, tensores)
    total = {}
    for td, cd in direcao.items():
        # Na direção, linear sobre funções: qualquer coeficiente sai.
        for to, co in operando.items():
            if _constante(co):
                parcela = {DerivadaCovariante(td, to): cd * co}
            else:
                # ∇_U(fX) = U(f)X + f∇_U X: a regra de Leibniz pede U(f), que
                # não é objeto daqui. Fica inteiro, sem expandir.
                parcela = {DerivadaCovariante(td, co * to): cd}
            total = _soma(total, parcela)
    return total


def _lie(expr, tensores):
    a, b = (linear(x, tensores) for x in expr.args)
    total = {}
    for ta, ca in a.items():
        for tb, cb in b.items():
            if not (_constante(ca) and _constante(cb)):
                parcela = {ColcheteDeLie(ca * ta, cb * tb): sp.S.One}
            elif ta == tb:
                parcela = {}                            # [U, U] = 0
            elif default_sort_key(tb) < default_sort_key(ta):
                parcela = {ColcheteDeLie(tb, ta): -ca * cb}   # antissimetria
            else:
                parcela = {ColcheteDeLie(ta, tb): ca * cb}
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
    """A equação como relação `{termo: coef} = 0`."""
    if isinstance(equacao, sp.Equality):
        return _soma(linear(equacao.lhs, tensores),
                     _vezes(-1, linear(equacao.rhs, tensores)))
    return linear(equacao, tensores)


# ----------------------------------------------------------------- contextos

class Contexto:
    """Um lugar com buraco: ∇_U □, ∇_□ W, [□, X], R(U,X)□…

    `sobre_funcoes` diz se é linear sobre funções, ou só sobre constantes. Só
    os primeiros podem receber relação com coeficiente que não é número:
    ∇_U(fX) não é f∇_U X.
    """

    def __init__(self, preencher, rotulo, latex, sobre_funcoes):
        self.preencher = preencher
        self.rotulo = rotulo            # com '{}' no lugar do buraco
        self.latex = latex
        self.sobre_funcoes = sobre_funcoes

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


def contextos(relacoes):
    achados = []
    for rel in relacoes:
        for termo in rel:
            _contextos_de(termo, achados)
    unicos = {}
    for c in achados:
        unicos.setdefault(c.chave(), c)
    return list(unicos.values())


def _profundidade(termo):
    if not isinstance(termo, _OPERADORES):
        return 0
    return 1 + max(_profundidade(a) for a in termo.args)


# -------------------------------------------------------------- a busca

class Derivada:
    """Uma relação e de onde ela veio: a hipótese e os contextos aplicados."""

    def __init__(self, relacao, hipotese, contextos=()):
        self.relacao = relacao
        self.hipotese = hipotese        # o rótulo: 'eq3'
        self.contextos = tuple(contextos)

    def chave(self):
        return frozenset((t, sp.simplify(c)) for t, c in self.relacao.items())

    def rotulo(self):
        texto = self.hipotese
        for c in self.contextos:
            texto = c.rotulo.replace("{}", texto)
        return texto

    def rotulo_latex(self):
        texto = rf"\text{{{self.hipotese}}}"
        for c in self.contextos:
            texto = c.latex.replace("{}", texto)
        return texto


def _aplicar(contexto, derivada, tensores):
    rel = derivada.relacao
    if not contexto.sobre_funcoes and not all(_constante(c) for c in rel.values()):
        return None
    expressao = sp.Add(*(c * contexto.preencher(t) for t, c in rel.items()))
    nova = linear(expressao, tensores)
    if not nova:
        return None
    return Derivada(nova, derivada.hipotese,
                    derivada.contextos + (contexto,))


class Prova:
    """O certificado: cada passo, o coeficiente, e a soma conferida."""

    def __init__(self, objetivo, passos, hipoteses_usadas):
        self.objetivo = objetivo        # a equação, como foi lida
        self.passos = passos            # [(coeficiente, Derivada)]
        self.hipoteses_usadas = hipoteses_usadas


class SemProva(Exception):
    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


def provar(objetivo, hipoteses, tensores):
    """Uma `Prova` de `objetivo` a partir de `hipoteses` ({rótulo: equação}).

    Levanta `SemProva` quando não acha — dizendo que não achar não é refutar.
    """
    alvo = relacao(objetivo, tensores)
    if not alvo:
        return Prova(objetivo, [], [])

    base = [Derivada(relacao(eq, tensores), rotulo)
            for rotulo, eq in hipoteses.items()]
    base = [d for d in base if d.relacao]
    todos = [alvo] + [d.relacao for d in base]
    lugares = contextos(todos)
    profundidade = max((_profundidade(t) for r in todos for t in r), default=0)

    conhecidas = {d.chave(): d for d in base}
    fronteira = list(base)
    for _ in range(profundidade):
        nova_fronteira = []
        for d in fronteira:
            for c in lugares:
                n = _aplicar(c, d, tensores)
                if n is None or n.chave() in conhecidas:
                    continue
                conhecidas[n.chave()] = n
                nova_fronteira.append(n)
                if len(conhecidas) > LIMITE_RELACOES:
                    raise SemProva(
                        f"a busca passou de {LIMITE_RELACOES} relações sem "
                        f"achar; não achar não é prova de que é falso")
        fronteira = nova_fronteira

    derivadas = list(conhecidas.values())
    passos = _combinacao(alvo, derivadas)
    if passos is None:
        faltam = sorted({sp.sstr(t) for t in alvo}
                        - {sp.sstr(t) for d in derivadas for t in d.relacao})
        dica = (f" Nenhuma hipótese fala de {', '.join(faltam)}."
                if faltam else "")
        raise SemProva(
            "não achei combinação das hipóteses que dê isto." + dica +
            " Não achar não é prova de que é falso: pode faltar hipótese, ou "
            "a prova pedir mais do que a linearidade e as hipóteses dão.")

    _conferir(alvo, passos)
    # Na ordem em que foram dadas, e não na da busca: quem lê confere a
    # lista contra a chamada que escreveu.
    tocadas = {d.hipotese for _, d in passos}
    usadas = [h for h in hipoteses if h in tocadas]
    return Prova(objetivo, passos, usadas)


def _combinacao(alvo, derivadas):
    """[(λ, derivada)] com Σ λ·relação = alvo, ou None."""
    if not derivadas:
        return None
    termos = sorted({t for t in alvo} | {t for d in derivadas for t in d.relacao},
                    key=default_sort_key)
    lambdas = sp.symbols(f"lambda0:{len(derivadas)}")
    equacoes = [sp.Add(*(l * d.relacao.get(t, 0)
                         for l, d in zip(lambdas, derivadas))) - alvo.get(t, 0)
                for t in termos]
    solucao = sp.linsolve(equacoes, lambdas)
    if not solucao:
        return None
    particular = next(iter(solucao))
    livres = set().union(*(sp.sympify(v).free_symbols for v in particular)) \
        & set(lambdas)
    particular = [sp.simplify(sp.sympify(v).subs({l: 0 for l in livres}))
                  for v in particular]
    return [(v, d) for v, d in zip(particular, derivadas) if v != 0]


def _conferir(alvo, passos):
    """A soma é conferida de novo, do zero: o certificado não é de confiança."""
    soma = _soma(*(_vezes(v, d.relacao) for v, d in passos))
    resto = _soma(soma, _vezes(-1, alvo))
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
