r"""Formas diferenciais: d, ∧, ι_X e ℒ_X, sem índice.

    \omega = forma(2)             uma 2-forma — um (0,2) antissimétrico
    \mathrm{d}\omega              a derivada exterior
    \omega \wedge \eta            o produto exterior
    \iota_X \omega                o produto interior
    \mathcal{L}_X \omega          a derivada de Lie

## O que decide a leitura

`d\omega` é d vezes ω, ou a derivada exterior? `\wedge` o parser nem lê.
Como em todo o resto, decide a declaração: `d` só é operador quando age numa
forma declarada; `\mathrm{d}` é sempre. `df` com f função continua sendo d
vezes f — para a diferencial de f, `\mathrm{d}f`. `\iota_X` e `\mathcal{L}_X`
pedem X declarado vetor.

## O que se sabe sem hipótese

O que vale em qualquer livro:

- d² = 0, e d(α∧β) = dα∧β + (−1)^p α∧dβ;
- α∧β = (−1)^{pq} β∧α, e α∧α = 0 para α de grau ímpar;
- ι_X é antiderivação de grau −1: ι_X(α∧β) = ι_Xα∧β + (−1)^p α∧ι_Xβ;
  ι_X df = X(f), ι_X ι_X = 0, linear sobre funções em X;
- ℒ_X = ι_X d + d ι_X — a fórmula de Cartan, que é teorema, não convenção;
  num escalar, ℒ_X f = X(f).

## A convenção que entra

ι_Y ι_X ω = ω(X, Y): a do determinante (Lee, Spivak), em que
(α∧β)(X,Y) = α(X)β(Y) − α(Y)β(X). É ela que liga o produto interior à
avaliação da forma nos vetores. A fórmula dω(X,Y) = X(ω(Y)) − Y(ω(X)) −
ω([X,Y]) muda de fator com a normalização, e por isso entra como hipótese.
"""

from __future__ import annotations

import re

import sympy as sp
from sympy.core.sorting import default_sort_key

from .conexao import (VETOR, Avaliado, AvaliadoAntissimetrico, Direcional,
                      exigir_vetor)

CHAVE = "__formas__"
"""Onde, no dicionário de tensores, vão os graus das formas declaradas."""

CHAVE_HODGE = "__hodge__"
"""E, com ⋆ declarado, (n, s): a dimensão e os sinais negativos."""


def graus(tensores):
    return dict(tensores.get(CHAVE, ()))


def hodge_de(tensores):
    return tensores.get(CHAVE_HODGE)


def com_graus(tensores, formas, hodge=None):
    """O dicionário de tensores levando também os graus das formas."""
    extra = {CHAVE_HODGE: hodge} if hodge else {}
    return {**tensores, CHAVE: tuple(sorted(formas.items())), **extra}


# ------------------------------------------------------------- os objetos

class Cunha(sp.Function):
    """α ∧ β ∧ … — na ordem escrita; a forma normal é que ordena."""

    def _latex(self, printer):
        return r" \wedge ".join(_parenteses(printer, a) for a in self.args)

    def _sympystr(self, printer):
        return " ^ ".join(_str_par(printer, a) for a in self.args)


class DerivadaExterior(sp.Function):
    """d(α), escrito — ainda não aberto por Leibniz."""

    nargs = 1

    def _latex(self, printer):
        return rf"\mathrm{{d}}{_parenteses(printer, self.args[0])}"

    def _sympystr(self, printer):
        return f"d({printer._print(self.args[0])})"


class Interior(sp.Function):
    """ι_X α, escrito."""

    nargs = 2

    def _latex(self, printer):
        return (rf"\iota_{{{printer._print(self.args[0])}}}"
                f"{_parenteses(printer, self.args[1])}")

    def _sympystr(self, printer):
        return f"iota_{printer._print(self.args[0])}({printer._print(self.args[1])})"


class DerivadaDeLie(sp.Function):
    """ℒ_X α, escrito."""

    nargs = 2

    def _latex(self, printer):
        return (rf"\mathcal{{L}}_{{{printer._print(self.args[0])}}}"
                f"{_parenteses(printer, self.args[1])}")

    def _sympystr(self, printer):
        return f"L_{printer._print(self.args[0])}({printer._print(self.args[1])})"


# Os átomos da forma normal — o que não se abre mais.

class Hodge(sp.Function):
    """⋆α. Escrito, ⋆ de qualquer coisa; na forma normal, ⋆ de um monômio —
    linear sobre funções, e ⋆⋆ = (−1)^{p(n−p)+s}."""

    nargs = 1

    def _latex(self, printer):
        return rf"\star {_parenteses(printer, self.args[0])}"

    def _sympystr(self, printer):
        # ⋆, e não *: `**omega` se leria potência.
        return f"⋆{_str_par(printer, self.args[0])}"


class Exterior(sp.Function):
    """dω com ω átomo: irredutível, e d(dω) = 0."""

    nargs = 1

    def _latex(self, printer):
        return rf"\mathrm{{d}}{printer._print(self.args[0])}"

    def _sympystr(self, printer):
        return f"d{printer._print(self.args[0])}"


class Diferencial(sp.Function):
    """df, com f escalar átomo — a 1-forma que dá ι_X df = X(f)."""

    nargs = 1

    def _latex(self, printer):
        return rf"\mathrm{{d}}{_parenteses(printer, self.args[0])}"

    def _sympystr(self, printer):
        return f"d({printer._print(self.args[0])})"


class Contraido(sp.Function):
    """ι_{X_k}…ι_{X_1} ω, com menos vetores que o grau: ainda uma forma.

    Antissimétrica nos vetores, como ω: a ordem canônica leva o sinal.
    """

    def _latex(self, printer):
        base = printer._print(self.args[0])
        vetores = "".join(rf"\iota_{{{printer._print(v)}}}"
                          for v in reversed(self.args[1:]))
        return f"{vetores}{base}"

    def _sympystr(self, printer):
        vetores = ", ".join(printer._print(v) for v in self.args[1:])
        return f"{printer._print(self.args[0])}({vetores}, ·)"


class FormaAvaliada(AvaliadoAntissimetrico):
    """dω(X, Y), com a base não sendo um nome declarado: um escalar."""


def _parenteses(printer, a):
    """Entre parênteses tudo o que não é um nome: d ω(X) se leria (dω)(X)."""
    texto = printer._print(a)
    return texto if isinstance(a, (sp.Symbol, Exterior)) \
        else rf"\left({texto}\right)"


def _str_par(printer, a):
    texto = printer._print(a)
    return f"({texto})" if isinstance(a, (sp.Add, sp.Mul)) else texto


ESCRITOS = (Cunha, DerivadaExterior, Interior, DerivadaDeLie)
ATOMOS = (Exterior, Diferencial, Contraido, Hodge)


def tem_forma(expr, tensores):
    """Há forma em `expr` — fora de uma avaliação, que é escalar?"""
    expr = sp.sympify(expr)
    if isinstance(expr, sp.Equality):
        return tem_forma(expr.lhs, tensores) or tem_forma(expr.rhs, tensores)
    if isinstance(expr, ESCRITOS + ATOMOS):
        return True
    if isinstance(expr, (Avaliado, Direcional)):
        return False
    if isinstance(expr, sp.Symbol):
        return expr.name in graus(tensores)
    return any(tem_forma(a, tensores) for a in expr.args)


# ------------------------------------------------------ a forma normal

def grau(a, tensores):
    if isinstance(a, sp.Symbol):
        return graus(tensores).get(a.name, 0)
    if isinstance(a, Exterior):
        return grau(a.args[0], tensores) + 1
    if isinstance(a, Diferencial):
        return 1
    if isinstance(a, Contraido):
        return grau(a.args[0], tensores) - (len(a.args) - 1)
    if isinstance(a, Hodge):
        n, _ = hodge_de(tensores)
        return n - sum(grau(x, tensores) for x in _atomos_de(a.args[0]))
    return 0


def _monomio(atomos, tensores):
    """(sinal, tupla canônica) — ordenar com o sinal de Koszul; 0 se um átomo
    de grau ímpar repete."""
    atomos = list(atomos)
    sinal = 1
    for i in range(len(atomos)):
        for j in range(len(atomos) - 1 - i):
            a, b = atomos[j], atomos[j + 1]
            if default_sort_key(b) < default_sort_key(a):
                atomos[j], atomos[j + 1] = b, a
                if grau(a, tensores) * grau(b, tensores) % 2:
                    sinal = -sinal
    for a, b in zip(atomos, atomos[1:]):
        if a == b and grau(a, tensores) % 2:
            return 0, ()
    hodge = hodge_de(tensores)
    if hodge:
        if sum(grau(a, tensores) for a in atomos) > hodge[0]:
            return 0, ()                # grau maior que a dimensão
        troca = _simetria_hodge(atomos, tensores)
        if troca is not None:
            outro_sinal, atomos = _monomio(troca, tensores)
            return sinal * outro_sinal, atomos
    return sinal, tuple(atomos)


def _simetria_hodge(atomos, tensores):
    """α ∧ ⋆β = β ∧ ⋆α, com α e β do mesmo grau: fica o de α menor.

    Só num monômio de dois átomos, que é onde a igualdade vale — de grau n,
    sem mais nada. Trocar α por β e ⋆β por ⋆α mantém o grau de cada
    posição, e o sinal de Koszul refaz a ordem."""
    if len(atomos) != 2:
        return None
    for i, h in enumerate(atomos):
        a = atomos[1 - i]
        if isinstance(h, Hodge) and not isinstance(h.args[0], Cunha) \
                and h.args[0] != sp.S.One \
                and grau(a, tensores) == grau(h.args[0], tensores) \
                and default_sort_key(h.args[0]) < default_sort_key(a):
            novos = list(atomos)
            novos[1 - i], novos[i] = h.args[0], Hodge(a)
            return novos
    return None


def _chave(atomos):
    if not atomos:
        return sp.S.One
    return atomos[0] if len(atomos) == 1 else Cunha(*atomos)


def _atomos_de(chave):
    if chave == sp.S.One:
        return ()
    return tuple(chave.args) if isinstance(chave, Cunha) else (chave,)


def _soma(*dicts):
    total = {}
    for d in dicts:
        for t, c in d.items():
            total[t] = total.get(t, 0) + c
    return {t: c for t, c in total.items() if sp.expand(c) != 0}


def _vezes(c, d):
    return {t: c * v for t, v in d.items()}


def _cunha(a, b, tensores):
    """Produto exterior de duas formas normais."""
    total = {}
    for ta, ca in a.items():
        for tb, cb in b.items():
            sinal, atomos = _monomio(_atomos_de(ta) + _atomos_de(tb), tensores)
            if sinal:
                total = _soma(total, {_chave(atomos): sinal * ca * cb})
    return total


def normal(expr, tensores):
    """{monomio: coeficiente} — monomio é 1 (escalar), um átomo, ou Cunha."""
    from .prova import escalar_normal
    expr = sp.sympify(expr)
    if expr == 0:
        return {}
    if isinstance(expr, sp.Add):
        return _soma(*(normal(a, tensores) for a in expr.args))
    if isinstance(expr, sp.Mul):
        formas = [a for a in expr.args if tem_forma(a, tensores)]
        escalar = sp.Mul(*(a for a in expr.args if not tem_forma(a, tensores)))
        total = {sp.S.One: escalar_normal(escalar, tensores)}
        for f in formas:
            total = _cunha(total, normal(f, tensores), tensores)
        return total
    if isinstance(expr, sp.Pow) and tem_forma(expr, tensores):
        raise ValueError(f"potência de forma, '{expr}': escreva o produto "
                         f"exterior com \\wedge")
    if not tem_forma(expr, tensores):
        c = escalar_normal(expr, tensores)
        return {} if sp.expand(c) == 0 else {sp.S.One: c}
    if isinstance(expr, Hodge):
        # Antes dos átomos: ⋆ escrito é aberto — linear, e ⋆⋆ com o sinal.
        return estrela(normal(expr.args[0], tensores), tensores)
    if isinstance(expr, sp.Symbol) or isinstance(expr, ATOMOS):
        return {expr: sp.S.One}
    if isinstance(expr, Cunha):
        total = {sp.S.One: sp.S.One}
        for a in expr.args:
            total = _cunha(total, normal(a, tensores), tensores)
        return total
    if isinstance(expr, DerivadaExterior):
        return d(normal(expr.args[0], tensores), tensores)
    if isinstance(expr, Interior):
        return iota(expr.args[0], normal(expr.args[1], tensores), tensores)
    if isinstance(expr, DerivadaDeLie):
        n = normal(expr.args[1], tensores)
        return _soma(iota(expr.args[0], d(n, tensores), tensores),
                     d(iota(expr.args[0], n, tensores), tensores))
    raise ValueError(f"'{expr}' não é forma que eu saiba ler")


def _d_escalar(c, tensores):
    """dc = Σ ∂c/∂s ds, sobre os átomos escalares de c."""
    from .prova import _atomos_escalares
    c = sp.sympify(c)
    if c.is_number:
        return {}
    atomos = sorted(_atomos_escalares(c, tensores), key=default_sort_key)
    mudos = {a: sp.Dummy() for a in atomos}
    aberto = c.xreplace(mudos)
    total = {}
    for a, m in mudos.items():
        parcial = sp.diff(aberto, m).xreplace({v: k for k, v in mudos.items()})
        if parcial != 0:
            total = _soma(total, {Diferencial(a): parcial})
    return total


def _d_atomo(a, tensores):
    if isinstance(a, (Exterior, Diferencial)):
        return {}                                   # d² = 0
    return {Exterior(a): sp.S.One}


def d(forma, tensores):
    """A derivada exterior de uma forma normal — Leibniz graduado."""
    total = {}
    for chave, c in forma.items():
        atomos = _atomos_de(chave)
        total = _soma(total, _cunha(_d_escalar(c, tensores),
                                    {chave: sp.S.One}, tensores))
        antes = 0
        for i, a in enumerate(atomos):
            da = _d_atomo(a, tensores)
            if da:
                pedaco = {_chave(atomos[:i]): c * (-1) ** antes}
                pedaco = _cunha(pedaco, da, tensores)
                pedaco = _cunha(pedaco, {_chave(atomos[i + 1:]): sp.S.One},
                                tensores)
                total = _soma(total, pedaco)
            antes += grau(a, tensores)
    return total


def _iota_atomo(X, a, tensores):
    """ι_X de um átomo, com X termo vetorial: escalar ou forma."""
    from .prova import direcional
    if isinstance(a, Diferencial):
        return {sp.S.One: direcional({X: sp.S.One}, a.args[0], tensores)}
    if isinstance(a, Contraido):
        base, vetores = a.args[0], a.args[1:] + (X,)
    else:
        base, vetores = a, (X,)
    return _contraido(base, vetores, tensores)


def _contraido(base, vetores, tensores):
    """ω(v₁, …, v_k, ·): antissimétrico nos v, e escalar quando completo."""
    ordem = sorted(range(len(vetores)), key=lambda i: default_sort_key(vetores[i]))
    canonicos = tuple(vetores[i] for i in ordem)
    if len(set(canonicos)) < len(canonicos):
        return {}
    inversoes = sum(1 for i in range(len(ordem)) for j in range(i + 1, len(ordem))
                    if ordem[i] > ordem[j])
    sinal = -1 if inversoes % 2 else 1
    g = grau(base, tensores)
    if len(canonicos) < g:
        return {Contraido(base, *canonicos): sp.S(sinal)}
    if isinstance(base, sp.Symbol):
        classe = Avaliado if g == 1 else AvaliadoAntissimetrico
        return {sp.S.One: sinal * classe(base, *canonicos)}
    return {sp.S.One: sinal * FormaAvaliada(base, *canonicos)}


def iota(X, forma, tensores):
    """ι_X de uma forma normal — antiderivação de grau −1, linear sobre
    funções em X."""
    from .prova import escalar_normal, linear
    exigir_vetor(X, "ι", {k: v for k, v in tensores.items() if k != CHAVE})
    total = {}
    for tx, cx in linear(X, tensores).items():
        for chave, c in forma.items():
            atomos = _atomos_de(chave)
            antes = 0
            for i, a in enumerate(atomos):
                ia = _iota_atomo(tx, a, tensores)
                if ia:
                    pedaco = {_chave(atomos[:i]): cx * c * (-1) ** antes}
                    pedaco = _cunha(pedaco, ia, tensores)
                    pedaco = _cunha(pedaco, {_chave(atomos[i + 1:]): sp.S.One},
                                    tensores)
                    total = _soma(total, pedaco)
                antes += grau(a, tensores)
    return {k: escalar_normal(v, tensores) for k, v in total.items()}


def estrela(forma, tensores):
    """⋆ de uma forma normal: linear sobre funções, e ⋆⋆ com o sinal."""
    hodge = hodge_de(tensores)
    if not hodge:
        raise ValueError("⋆ sem declaração: \\star = hodge, depois da "
                         "assinatura")
    n, s = hodge
    total = {}
    for chave, c in forma.items():
        if isinstance(chave, Hodge):
            interna = chave.args[0]
            p = sum(grau(a, tensores) for a in _atomos_de(interna))
            total = _soma(total, {interna: c * (-1) ** (p * (n - p) + s)})
        else:
            sinal, atomos = _monomio((Hodge(chave),), tensores)
            total = _soma(total, {_chave(atomos): sinal * c})
    return total


def expressao(forma):
    """A forma normal de volta como expressão."""
    return sp.Add(*(c * t for t, c in forma.items()))


# ------------------------------------------------------------ no texto

_RE_D = re.compile(r"\\mathrm\s*\{\s*d\s*\}|(?<![A-Za-z\\])d(?![a-zA-Z])")
_RE_IOTA = re.compile(r"\\iota(?![a-zA-Z])\s*_\s*(\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z])")
_RE_LIE = re.compile(r"\\mathcal\s*\{\s*L\s*\}\s*_\s*(\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z])")
_RE_CUNHA = re.compile(r"\s*\\(?:wedge|land)(?![a-zA-Z])\s*")
_RE_NOME = re.compile(r"\\[a-zA-Z]+|[A-Za-z]")


class Ocorrencia:
    def __init__(self, ini, fim, cadeia, problema=None):
        self.ini, self.fim = ini, fim
        self.cadeia = cadeia            # [(prefixos, base_latex)]
        self.problema = problema


_RE_ESTRELA = re.compile(r"\\(?:star|ast)(?![a-zA-Z])")


class _Leitor:
    """Uma cadeia `op… base (∧ op… base)*` que tenha operador ou ∧."""

    def __init__(self, texto, formas, vetores, hodge=False):
        self.t = texto
        self.formas = formas
        self.vetores = vetores
        self.hodge = hodge

    def _espacos(self, i):
        while i < len(self.t) and self.t[i].isspace():
            i += 1
        return i

    def _nome(self, grupo):
        g = grupo.strip()
        return g[1:-1].strip() if g.startswith("{") else g

    def operando(self, i):
        """(prefixos, base, fim) ou None."""
        prefixos = []
        j = self._espacos(i)
        explicito = False
        while True:
            m = _RE_D.match(self.t, j)
            if m and self.t.startswith(r"\mathrm", j):
                prefixos.append(("d", None))
                explicito = True
                j = self._espacos(m.end())
                continue
            if m and m.start() == j:
                prefixos.append(("d?", None))
                j = self._espacos(m.end())
                continue
            m = _RE_IOTA.match(self.t, j)
            if m and _limpo(self._nome(m.group(1))) in self.vetores:
                prefixos.append(("i", self._nome(m.group(1))))
                j = self._espacos(m.end())
                continue
            m = _RE_LIE.match(self.t, j)
            if m:
                prefixos.append(("L", self._nome(m.group(1))))
                j = self._espacos(m.end())
                continue
            m = _RE_ESTRELA.match(self.t, j)
            if m and self.hodge:
                prefixos.append(("h", None))
                j = self._espacos(m.end())
                continue
            break
        if j < len(self.t) and self.t[j] == "(":
            fim = _fecha(self.t, j)
            if fim is None:
                return None
            base = self.t[j + 1:fim - 1]
            e_forma = self._tem_forma_texto(base)
        else:
            m = _RE_NOME.match(self.t, j) or (
                re.compile(r"\d+").match(self.t, j)
                if any(op == "h" for op, _ in prefixos) else None)
            if not m:
                return None
            base, fim = m.group(0), m.end()
            resto = self.t[fim:].lstrip()
            if resto[:1] in ("(", "_", "^"):
                return None                     # ω(X): avaliação, não operando
            e_forma = _limpo(base) in self.formas
        # `d` sem \mathrm só é operador sobre forma: df continua d vezes f.
        prefixos = [("d", None) if (op == "d?" and (e_forma or explicito
                                                    or any(p[0] != "d?" for p in prefixos)))
                    else (op, v) for op, v in prefixos]
        if any(op == "d?" for op, _ in prefixos):
            return None
        if not prefixos and not e_forma:
            return None
        return prefixos, base, fim

    def _tem_forma_texto(self, texto):
        return any(_limpo(n) in self.formas for n in _RE_NOME.findall(texto)) \
            or bool(_RE_CUNHA.search(texto)) or r"\mathrm" in texto

    def em(self, i):
        if i > 0 and (self.t[i - 1].isalpha() or self.t[i - 1] == "\\"):
            return None
        primeiro = self.operando(i)
        if primeiro is None:
            return None
        cadeia = [primeiro[:2]]
        fim = primeiro[2]
        while True:
            m = _RE_CUNHA.match(self.t, fim)
            if not m:
                break
            proximo = self.operando(m.end())
            if proximo is None:
                return Ocorrencia(i, m.end(), cadeia,
                                  "∧ sem forma à direita")
            cadeia.append(proximo[:2])
            fim = proximo[2]
        if len(cadeia) == 1 and not cadeia[0][0]:
            return None                         # uma forma sozinha: é símbolo
        return Ocorrencia(i, fim, cadeia)


def _fecha(t, i):
    fundo = 0
    for j in range(i, len(t)):
        if t[j] == "(":
            fundo += 1
        elif t[j] == ")":
            fundo -= 1
            if fundo == 0:
                return j + 1
    return None


def _limpo(nome):
    return nome[1:] if nome.startswith("\\") else nome


def localizar(texto, formas, vetores, hodge=False):
    if not formas and not hodge:
        return []
    leitor = _Leitor(texto, formas, vetores, hodge)
    achados, i = [], 0
    while i < len(texto):
        oc = leitor.em(i)
        if oc is None:
            i += 1
            continue
        achados.append(oc)
        i = max(oc.fim, i + 1)
    return achados


def cabecas(texto, formas, vetores, hodge=False):
    """Tudo o que uma cadeia de formas engole — para não virar pergunta."""
    posicoes = set()
    for oc in localizar(texto, formas, vetores, hodge):
        posicoes |= set(range(oc.ini, oc.fim))
    return posicoes


def construir(oc, ler, tensores):
    """O objeto escrito: Cunha de operadores aplicados às bases."""
    fatores = []
    for prefixos, base in oc.cadeia:
        objeto = ler(base)
        for op, v in reversed(prefixos):
            if op == "d":
                objeto = DerivadaExterior(objeto)
            elif op == "h":
                objeto = Hodge(objeto)
            else:
                X = ler(v)
                exigir_vetor(X, rf"\iota_{v}" if op == "i" else rf"\mathcal{{L}}_{v}",
                             {k: t for k, t in tensores.items() if k != CHAVE})
                objeto = (Interior if op == "i" else DerivadaDeLie)(X, objeto)
        fatores.append(objeto)
    return fatores[0] if len(fatores) == 1 else Cunha(*fatores)
