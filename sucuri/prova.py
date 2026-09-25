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

from .conexao import (VETOR, ColcheteDeLie, Curvatura, DerivadaCovariante,
                      ParaTodo, e_vetor)

LIMITE_RELACOES = 4000
"""Quantas relações derivadas a busca aceita antes de desistir."""

LIMITE_INSTANCIAS = 300
"""Quantas instâncias das hipóteses com ∀ a busca aceita."""

RODADAS = 3
"""Até quantas vezes as instâncias novas podem gerar instâncias de novo.

A busca tenta com uma rodada e só aprofunda se não achar: cada rodada
multiplica as relações, e a maioria das provas não precisa da segunda."""

_OPERADORES = (DerivadaCovariante, ColcheteDeLie, Curvatura)


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


def _aplicar(contexto, derivada, tensores):
    rel = derivada.relacao
    if not contexto.sobre_funcoes and not all(_constante(c) for c in rel.values()):
        return None
    expressao = sp.Add(*(c * contexto.preencher(t) for t, c in rel.items()))
    nova = linear(expressao, tensores)
    if not nova:
        return None
    return Derivada(nova, derivada.hipotese,
                    derivada.contextos + (contexto,), derivada.instancia)


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
    corpo = objetivo
    if isinstance(objetivo, ParaTodo):
        # Provar para todo W é provar para um W qualquer, sobre o qual nada se
        # sabe além de ser vetor — e nenhuma hipótese fala dele.
        tensores = {**tensores, **{v.name: VETOR for v in objetivo.variaveis}}
        corpo = objetivo.corpo
    alvo = relacao(corpo, tensores)
    if not alvo:
        return Prova(objetivo, [], [])

    base, gerais = [], []
    for rotulo, eq in hipoteses.items():
        if isinstance(eq, ParaTodo):
            gerais.append((rotulo, eq))
        else:
            base.append(Derivada(relacao(eq, tensores), rotulo))
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


def _buscar(objetivo, alvo, hipoteses, base, tensores):
    """A busca, com as hipóteses já instanciadas.

    Cada relação que aparece entra numa base escalonada, e o objetivo é
    testado logo em seguida: a busca para assim que a prova existe, em vez de
    gerar todas as relações para só então resolver um sistema com todas elas.
    """
    todos = [alvo] + [d.relacao for d in base]
    lugares = contextos(todos)
    profundidade = max((_profundidade(t) for r in todos for t in r), default=0)

    # O universo: os termos que o problema tem, e os que estão a UM contexto
    # deles. Relação derivada que sai disso não serve para nada que a prova
    # precise — e sem esta poda as instâncias trazem termos, os termos trazem
    # contextos, e a busca não acaba.
    presentes = _chao(todos, tensores)
    universo = presentes | {c.preencher(t) for c in lugares for t in presentes}
    universo = {t for u in universo for t in linear(u, tensores)} | presentes

    escalonada = _Escalonada()
    derivadas = []

    def entra(d):
        derivadas.append(d)
        escalonada.juntar(d.relacao, len(derivadas) - 1)
        return escalonada.combinacao(alvo)

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
                if not all(u in universo for t in d.relacao
                           for u in linear(c.preencher(t), tensores)):
                    continue
                n = _aplicar(c, d, tensores)
                if n is None or n.chave() in conhecidas:
                    continue
                if not all(t in universo for t in n.relacao):
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

    faltam = sorted({sp.sstr(t) for t in alvo}
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
    """Os termos vetoriais concretos do problema — onde um ∀ pode pousar."""
    achados = set()
    for rel in relacoes:
        for termo in rel:
            for sub in sp.preorder_traversal(termo):
                if _e_termo(sub, tensores):
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
            for p in padrao:
                if not (isinstance(p, _OPERADORES) and p.has(*variaveis)):
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
