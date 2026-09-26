r"""A derivada com índice: ∂_μ A^ν, ∇_μ T_{αβ}.

O parser do SymPy lê `\partial_\mu A^\nu` como o símbolo `partial_{mu}`
multiplicando A — e a ponte recusava, desde o começo, porque derivada com
índice "não é um fator multiplicando outro, é um objeto próprio". Este arquivo
é esse objeto.

## Como é representada

Uma cabeça nova, com o índice da derivada no primeiro slot: ∂_μ A^ν é
`d_A(-mu, nu)`, ∇_μ A^ν é `D_A(-mu, nu)`, ∂_μ∂_ν φ é `dd_phi(-mu, -nu)`.
Assim a derivada entra na contração, na soma e na canonicalização como
qualquer tensor — ∂_μ A^μ é a divergência sem nada especial.

Os nomes não colidem com o que a pessoa declara: nome de várias letras sem
barra é recusado na declaração, justamente porque em LaTeX seria produto.

## O que se sabe dela sem hipótese

- ∂ e ∇ são lineares e seguem Leibniz: ∂_μ(A^ν B_ν) = (∂_μ A^ν)B_ν +
  A^ν ∂_μ B_ν. Escalar também: ∂_μ(φψ) = ψ∂_μφ + φ∂_μψ.
- Derivadas PARCIAIS comutam: dd_A é simétrica nos slots das derivadas, e
  ∂_μ∂_ν φ − ∂_ν∂_μ φ simplifica a zero.
- ∇ NÃO comuta — ∇_μ∇_ν − ∇_ν∇_μ é a curvatura —, e nada se supõe.
- Num escalar, ∇_μ φ = ∂_μ φ: é a definição, em qualquer conexão.
- A simetria do tensor derivado se mantém: ∂_λ g_{μν} é simétrico em μν.

O que NÃO se supõe: ∇g = 0 (é Levi-Civita, não qualquer conexão), e que ∇
comute em escalares (é torção nula).

## Alcance

A derivada age no fator imediatamente à direita — `\partial_\mu A^\nu B_\nu`
é (∂_μ A^ν) B_ν, como se lê em qualquer livro. Produto pede parênteses:
`\partial_\mu (A^\nu B_\nu)`.
"""

from __future__ import annotations

import functools
import operator
import re

import sympy as sp
from sympy.printing.latex import LatexPrinter
from sympy.tensor.tensor import (TensAdd, TensExpr, Tensor, TensMul,
                                 TensorHead, TensorSymmetry)

from .tensores import _RE_FATOR, indices_de

REGISTRO = {}
"""nome da cabeça derivada -> (operações de fora para dentro, nome da base)."""

_MACRO = {"d": r"\partial", "D": r"\nabla"}
_RE_OPERADOR = re.compile(
    r"\\(partial|nabla)(?![a-zA-Z])\s*([_^])\s*(\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z])")
_RE_SIMBOLO = re.compile(r"\\[a-zA-Z]+|[A-Za-z]|\d+(?:\.\d+)?")


class DerivadaMalEscrita(ValueError):
    """Derivada com índice cujo alcance ou índice não se lê de um jeito só."""


# --------------------------------------------------------------- no texto

class Derivada:
    """Um `\\partial_\\mu …` ou `\\nabla^\\mu …` no texto."""

    def __init__(self, ini, fim_cabeca, fim, operacao, indice, cima,
                 operando, problema=None):
        self.ini = ini
        self.fim_cabeca = fim_cabeca
        self.fim = fim
        self.operacao = operacao        # 'd' (∂) ou 'D' (∇)
        self.indice = indice            # 'mu', sem a barra
        self.cima = cima
        self.operando = operando        # o LaTeX sobre o qual age
        self.problema = problema


def _grupo(texto, i, abre, fecha):
    fundo = 0
    for j in range(i, len(texto)):
        if texto[j] == abre:
            fundo += 1
        elif texto[j] == fecha:
            fundo -= 1
            if fundo == 0:
                return j + 1
    return None


def _cabeca(texto, i, indices):
    """(operação, índice, cima, fim) se em `i` começa ∂_μ ou ∇_μ com μ
    declarado; None se não é derivada com índice."""
    m = _RE_OPERADOR.match(texto, i)
    if not m:
        return None
    nomes = indices_de(m.group(3))
    if not nomes or not all(n in indices for n in nomes):
        return None
    return m, nomes


def localizar(texto, indices):
    """As derivadas com índice de primeiro nível — as de dentro são lidas pela
    recursão sobre o operando."""
    if not indices:
        return []
    achados, i = [], 0
    while i < len(texto):
        d = _uma(texto, i, indices)
        if d is None:
            i += 1
            continue
        achados.append(d)
        i = max(d.fim, i + 1)
    return achados


def cabecas(texto, indices):
    """As posições que são cabeça de derivada com índice, em qualquer nível."""
    posicoes = set()
    for i in range(len(texto)):
        d = _uma(texto, i, indices)
        if d is not None:
            posicoes |= set(range(d.ini, d.fim_cabeca))
    return posicoes


def _uma(texto, i, indices):
    achado = _cabeca(texto, i, indices)
    if achado is None:
        return None
    m, nomes = achado
    operacao = "d" if m.group(1) == "partial" else "D"
    cima = m.group(2) == "^"
    if len(nomes) != 1:
        macro = _MACRO[operacao]
        um, dois = (("\\" + n) if len(n) > 1 else n for n in nomes[:2])
        return Derivada(i, m.end(), m.end(), operacao, nomes[0], cima, None,
                        f"{m.group(0)}: um índice por derivada — escreva "
                        f"{macro}_{um}{macro}_{dois}, que diz em que ordem se "
                        f"deriva")
    operando, fim, problema = _operando(texto, m.end(), indices,
                                        m.group(0).strip())
    return Derivada(i, m.end(), fim, operacao, nomes[0], cima, operando,
                    problema)


def _operando(texto, i, indices, quem):
    """(latex, fim, problema) do fator imediatamente à direita."""
    while i < len(texto) and texto[i].isspace():
        i += 1
    if i >= len(texto) or texto[i] in "=+-)}],":
        return None, i, f"{quem} sem operando: falta o que derivar"
    interna = _uma(texto, i, indices)
    if interna is not None:
        return texto[i:interna.fim], interna.fim, None
    for abre, fecha in (("(", ")"), ("{", "}")):
        if texto[i] == abre:
            fim = _grupo(texto, i, abre, fecha)
            if fim is None:
                return None, len(texto), f"'{abre}' sem '{fecha}' depois de {quem}"
            return texto[i + 1:fim - 1], fim, None
    if texto.startswith(r"\left(", i):
        fim = texto.find(r"\right)", i)
        if fim < 0:
            return None, len(texto), rf"'\left(' sem '\right)' depois de {quem}"
        return texto[i + 6:fim], fim + 7, None
    fator = _RE_FATOR.match(texto, i)
    if fator:
        from .tensores import _RE_PEDACO
        nomes = [n for p in _RE_PEDACO.finditer(fator.group(2))
                 for n in indices_de(p.group(2))]
        soltos = [n for n in nomes if n not in indices]
        if soltos:
            # Com um índice que ninguém declarou, o operando não é tensor — e
            # derivá-lo como escalar seria inventar a conta.
            return None, fator.end(), (
                f"o operando {fator.group(0)} de {quem} tem índice não "
                f"declarado ({', '.join(soltos)}): declare-o, ou a derivada "
                f"não tem sobre o que agir")
        return fator.group(0), fator.end(), None
    simbolo = _RE_SIMBOLO.match(texto, i)
    if simbolo:
        resto = texto[simbolo.end():].lstrip()
        if resto[:1] in ("(", "'"):
            return None, simbolo.end(), (
                f"não está claro até onde {quem} alcança em "
                f"'{simbolo.group(0)}{resto[:1]}…': escreva o operando entre "
                f"parênteses, {quem} ( … )")
        return simbolo.group(0), simbolo.end(), None
    return None, i + 1, f"o que vem depois de {quem} não é um operando"


# ---------------------------------------------------------------- a conta

def _simetria_base(espaco, base):
    if base == espaco.metrica:
        return "simetrico"
    return espaco._simetrias.get(base)


def cabeca_derivada(espaco, operacoes, base, posto_base):
    """A cabeça de `operacoes` aplicadas à base — criada uma vez só."""
    nome = "".join(operacoes) + "_" + base
    if nome in espaco._cabecas:
        return espaco._cabecas[nome][0]
    k = len(operacoes)
    blocos = [k] if all(o == "d" for o in operacoes) else [1] * k
    if (operacoes == ("D", "d") and posto_base == 0
            and espaco.conexao == "levi-civita"):
        blocos = [2]        # ∇_μ∇_ν φ = ∇_ν∇_μ φ: torção nula, num escalar
    simetria = _simetria_base(espaco, base)
    if posto_base > 1 and simetria == "simetrico":
        blocos.append(posto_base)
    elif posto_base > 1 and simetria == "antissimetrico":
        blocos.append(-posto_base)
    else:
        blocos += [1] * posto_base
    cabeca = TensorHead(nome, [espaco.tipo] * (k + posto_base),
                        TensorSymmetry.direct_product(*blocos))
    espaco._cabecas[nome] = (cabeca, k + posto_base)
    REGISTRO[nome] = (tuple(operacoes), base)
    return cabeca


def _produto(fatores):
    return functools.reduce(operator.mul, fatores, sp.S.One)


def _soma(termos):
    termos = [t for t in termos if t != 0]
    return functools.reduce(operator.add, termos) if termos else sp.S.Zero


def derivar(expr, operacao, indice, espaco):
    """∂ ou ∇ com o índice `indice` (já com a valência) aplicado a `expr`."""
    if isinstance(expr, TensAdd):
        return _soma([derivar(a, operacao, indice, espaco) for a in expr.args])
    if isinstance(expr, TensMul):
        coef = expr.coeff
        fatores = [a for a in expr.args if isinstance(a, TensExpr)]
        termos = [_escalar(coef, operacao, indice, espaco) * _produto(fatores)]
        for k, f in enumerate(fatores):
            outros = fatores[:k] + [derivar(f, operacao, indice, espaco)] + \
                fatores[k + 1:]
            termos.append(coef * _produto(outros))
        return _soma(termos)
    if isinstance(expr, Tensor):
        cabeca = expr.head
        indices = list(expr.indices)
        operacoes, base = REGISTRO.get(cabeca.name, ((), cabeca.name))
        posto_base = len(indices) - len(operacoes)
        nova = cabeca_derivada(espaco, (operacao,) + operacoes, base, posto_base)
        try:
            return nova(indice, *indices)
        except ValueError:
            raise DerivadaMalEscrita(
                "o índice da derivada aparece de novo no operando, na mesma "
                "posição — contrair é um em cima e um embaixo, como em "
                "∂_μ A^μ") from None
    return _escalar(expr, operacao, indice, espaco)


def _escalar(expr, operacao, indice, espaco):
    """∂_μ de um escalar — que é também ∇_μ dele: regra da cadeia sobre os
    símbolos, cada um uma função."""
    expr = sp.sympify(expr)
    if expr.is_number:
        return sp.S.Zero
    termos = []
    for s in sorted(expr.free_symbols, key=lambda s: s.name):
        parcial = sp.diff(expr, s)
        if parcial != 0:
            # ∇_μ φ = ∂_μ φ num escalar: a mesma cabeça.
            cabeca = cabeca_derivada(espaco, ("d",), s.name, 0)
            termos.append(parcial * cabeca(indice))
    return _soma(termos)


# -------------------------------------------------------------- impressão

class Impressor(LatexPrinter):
    """∂_μ A^ν, e não A com todos os índices juntos — `\\partial A{}_{\\mu}{}^{\\nu}`
    leria como a derivada de A_μ^ν."""

    def _print_Tensor(self, expr):
        nome = expr.head.name
        if nome not in REGISTRO:
            return super()._print_Tensor(expr)
        operacoes, base = REGISTRO[nome]
        indices = list(expr.indices)
        partes = []
        for op, i in zip(operacoes, indices):
            lado = "^" if i.is_up else "_"
            partes.append(f"{_MACRO[op]}{lado}{{{self._print(sp.Symbol(i.name))}}}")
        corpo = self._print(sp.Symbol(base))
        for i in indices[len(operacoes):]:
            lado = "^" if i.is_up else "_"
            corpo += f"{{}}{lado}{{{self._print(sp.Symbol(i.name))}}}"
        return " ".join(partes) + " " + corpo


def latex(expr):
    return Impressor().doprint(expr)


# ------------------------------------------ a conexão declarada, e Ricci

def _mapear(expr, trocar):
    """Refaz a expressão tensorial trocando cada Tensor por `trocar(t)`.

    Multiplicando de novo, e não substituindo: os índices mudos são objetos
    compartilhados entre fatores, e refazer o produto refaz a contração.
    """
    if isinstance(expr, TensAdd):
        return _soma([_mapear(a, trocar) for a in expr.args])
    if isinstance(expr, TensMul):
        fatores = [a for a in expr.args if isinstance(a, TensExpr)]
        return expr.coeff * _produto([_mapear(f, trocar) for f in fatores])
    if isinstance(expr, Tensor):
        return trocar(expr)
    return expr


def _nulo(t, espaco):
    """A derivada que é zero pela declaração — ou por ser a delta.

    ∂δ = ∇δ = 0 sempre: componentes constantes, e δ é a identidade em
    qualquer conexão. ∇g = 0 e ∇ε = 0 só com a conexão de Levi-Civita
    declarada — é o que a distingue de uma conexão qualquer.
    """
    operacoes, base = REGISTRO.get(t.head.name, ((), None))
    if not operacoes:
        return False
    if base == espaco.kronecker:
        return True
    levi = espaco.conexao == "levi-civita"
    if operacoes[-1] == "D" and levi:
        if base == espaco.metrica or espaco.levi.get(base) == "tensor":
            return True
    return False


def _comutavel(t, espaco):
    """∇_μ∇_ν aplicado a alguma coisa — onde o comutador vira curvatura."""
    operacoes, base = REGISTRO.get(t.head.name, ((), None))
    if len(operacoes) < 2 or operacoes[0] != "D":
        return False
    if operacoes[1] == "D":
        return True
    # ∇_μ ∂_ν φ é ∇_μ ∇_ν φ num escalar.
    return operacoes[1] == "d" and len(operacoes) == 2 and \
        len(t.indices) == 2


_MUDOS = [0]


def _mudo(espaco):
    from sympy.tensor.tensor import TensorIndex
    _MUDOS[0] += 1
    return TensorIndex(f"s_{_MUDOS[0]}", espaco.tipo)


def _operando_de(t, espaco):
    """A cabeça e os índices do que está SOB as duas primeiras derivadas."""
    operacoes, base = REGISTRO[t.head.name]
    indices = list(t.indices)
    resto = operacoes[2:]
    if resto:
        cabeca = cabeca_derivada(espaco, resto, base, len(indices) - len(operacoes))
    elif len(indices) == 2:
        return None, []                       # um escalar: não há termo
    else:
        cabeca = espaco.cabeca(base, len(indices) - 2)
    return cabeca, indices[2:]


def _curvatura_de(t, espaco, mu, nu):
    """[∇_μ, ∇_ν] T — um termo por índice de T, na convenção declarada.

    Índice de cima entra no slot ρ do Riemann, e o de T vira mudo no σ; índice
    de baixo entra no σ, com o sinal trocado, e o mudo vai para o ρ.
    """
    nome, conv = espaco.riemann
    cabeca, indices = _operando_de(t, espaco)
    if cabeca is None:
        return sp.S.Zero
    R = espaco.cabeca(nome, 4)
    termos = []
    for k, i in enumerate(indices):
        s = _mudo(espaco)
        slots = [None] * 4
        slots[conv["mu"]], slots[conv["nu"]] = mu, nu
        novos = list(indices)
        if i.is_up:
            slots[conv["rho"]], slots[conv["sigma"]] = i, -s
            novos[k] = s
            sinal = conv["sinal"]
        else:
            slots[conv["rho"]], slots[conv["sigma"]] = s, i
            novos[k] = -s
            sinal = -conv["sinal"]
        termos.append(sinal * R(*slots) * cabeca(*novos))
    return _soma(termos)


def _simetrica(t, espaco):
    """A cabeça da parte simétrica ∇_(μ∇_ν) — criada ao lado da derivada."""
    operacoes, base = REGISTRO[t.head.name]
    nome = "S" + t.head.name
    if nome not in espaco._cabecas:
        posto_base = len(t.indices) - len(operacoes)
        blocos = [2] + [1] * (len(operacoes) - 2)
        simetria = _simetria_base(espaco, base)
        if posto_base > 1 and simetria == "simetrico":
            blocos.append(posto_base)
        elif posto_base > 1 and simetria == "antissimetrico":
            blocos.append(-posto_base)
        else:
            blocos += [1] * posto_base
        cabeca = TensorHead(nome, [espaco.tipo] * len(t.indices),
                            TensorSymmetry.direct_product(*blocos))
        espaco._cabecas[nome] = (cabeca, len(t.indices))
    return espaco._cabecas[nome][0]


def normalizar(expr, espaco):
    """O que a conexão declarada permite dizer, antes da forma canônica.

    Zeros: ∂δ, ∇δ; e com Levi-Civita, ∇g e ∇ε. Comutadores: com Levi-Civita e
    o Riemann definido, cada ∇_μ∇_ν T vira ∇_(μ∇_ν)T + ½[∇_μ,∇_ν]T; a forma
    canônica cancela as partes simétricas que se cancelam, e depois a parte
    simétrica volta a ser escrita como ∇∇T − ½[…]. Um ∇∇T sozinho sai como
    entrou; ∇_μ∇_ν T − ∇_ν∇_μ T sai como curvatura.
    """
    if not isinstance(expr, TensExpr) or espaco is None:
        return expr
    expr = _mapear(expr, lambda t: sp.S.Zero if _nulo(t, espaco) else t)
    if not isinstance(expr, TensExpr):
        return expr
    if espaco.conexao != "levi-civita" or not espaco.riemann:
        return expr

    partes = {}

    def abrir(t):
        if not _comutavel(t, espaco):
            return t
        mu, nu = t.indices[0], t.indices[1]
        S = _simetrica(t, espaco)
        partes[S.name] = t.head
        return S(*t.indices) + sp.Rational(1, 2) * _curvatura_de(t, espaco, mu, nu)

    aberto = _mapear(expr, abrir)
    if not isinstance(aberto, TensExpr):
        return aberto
    aberto = aberto.canon_bp()
    if not isinstance(aberto, TensExpr):
        return aberto

    def fechar(t):
        if t.head.name not in partes:
            return t
        original = partes[t.head.name](*t.indices)
        mu, nu = t.indices[0], t.indices[1]
        return original - sp.Rational(1, 2) * _curvatura_de(original, espaco, mu, nu)

    return _mapear(aberto, fechar)


def convencao_de(equacao, nome):
    r"""Da definição escrita, a convenção: o sinal e onde fica cada slot.

        \nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho
            = R^\rho{}_{\sigma\mu\nu} V^\sigma

    dá sinal +1, ρ no slot 0, σ no 1, μ no 2, ν no 3. Com o sinal trocado, ou
    os slots em outra ordem, sai outra convenção — e é a que vale.
    """
    esperado = (r"a definição tem de ter a forma "
                r"∇_μ∇_ν V^ρ − ∇_ν∇_μ V^ρ = ± " + nome +
                r"(ρ, σ, μ, ν em alguma ordem) V^σ — o comutador num vetor de "
                r"um lado, o Riemann contraído com o mesmo vetor do outro")
    if not isinstance(equacao, sp.Equality):
        raise ValueError(esperado)
    lados = [equacao.lhs, equacao.rhs]
    comutador = next((l for l in lados if isinstance(l, TensAdd)), None)
    curvatura = next((l for l in lados if l is not comutador), None)
    if comutador is None or not isinstance(curvatura, (TensMul, Tensor)):
        raise ValueError(esperado)

    termos = []
    for a in comutador.args:
        coef = a.coeff if isinstance(a, TensMul) else sp.S.One
        tensores = ([x for x in a.args if isinstance(x, Tensor)]
                    if isinstance(a, TensMul) else [a])
        if len(tensores) != 1:
            raise ValueError(esperado)
        termos.append((coef, tensores[0]))
    if len(termos) != 2 or {c for c, _ in termos} != {1, -1}:
        raise ValueError(esperado)
    positivo = next(t for c, t in termos if c == 1)
    negativo = next(t for c, t in termos if c == -1)
    for t in (positivo, negativo):
        operacoes, _ = REGISTRO.get(t.head.name, ((), None))
        if operacoes != ("D", "D") or len(t.indices) != 3 or not t.indices[2].is_up:
            raise ValueError(esperado)
    mu, nu, rho = positivo.indices
    if list(negativo.indices) != [nu, mu, rho] or mu.is_up or nu.is_up:
        raise ValueError(esperado)
    vetor = REGISTRO[positivo.head.name][1]

    coef = curvatura.coeff if isinstance(curvatura, TensMul) else sp.S.One
    fatores = ([x for x in curvatura.args if isinstance(x, Tensor)]
               if isinstance(curvatura, TensMul) else [curvatura])
    R = [f for f in fatores if f.head.name == nome]
    V = [f for f in fatores if f.head.name == vetor]
    if coef not in (1, -1) or len(R) != 1 or len(V) != 1 or len(fatores) != 2:
        raise ValueError(esperado)
    R, V = R[0], V[0]
    if len(R.indices) != 4 or len(V.indices) != 1:
        raise ValueError(esperado)
    sigma = V.indices[0]
    posicoes = {}
    for k, i in enumerate(R.indices):
        if i == rho:
            posicoes["rho"] = k
        elif i == mu:
            posicoes["mu"] = k
        elif i == nu:
            posicoes["nu"] = k
        elif i.name == sigma.name and i.is_up != sigma.is_up:
            posicoes["sigma"] = k
    if len(posicoes) != 4:
        raise ValueError(esperado)
    return {"sinal": int(coef), **posicoes}


def simetria_do_riemann(conv):
    """Antissimétrico nos slots de μ e ν — em qualquer convenção, porque vem
    do comutador. Só se exprime se os dois slots forem vizinhos no começo ou
    no fim; noutro lugar, fica sem, o que não é falso, só incompleto."""
    par = sorted((conv["mu"], conv["nu"]))
    if par == [2, 3]:
        return TensorSymmetry.direct_product(1, 1, -2)
    if par == [0, 1]:
        return TensorSymmetry.direct_product(-2, 1, 1)
    return TensorSymmetry.no_symmetry(4)
