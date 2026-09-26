r"""provar com índice: o objetivo como combinação das hipóteses.

    \nabla_a T^{ab} = 0                          eq1
    \nabla_a X_b + \nabla_b X_a = 0              eq2
    \nabla_a (T^a{}_b X^b) = 0                   eq3
    provar(eq3, eq1, eq2)

Como sem índice: cada hipótese é uma relação linear entre termos canônicos, e
a prova é uma combinação delas que dá o objetivo — um certificado, conferido
de novo antes de se dizer "provado". O que muda é de onde vêm as relações.

## De onde vêm as relações

De cada hipótese H = 0 valem também, com índice:

- H com os índices livres trocados por outros (e contraídos, com a métrica);
- H vezes qualquer tensor, contraído ou não;
- ∇_c H, e ∇_d ∇_c H.

A busca não tenta tudo: para cada termo do objetivo, procura um termo de uma
dessas formas de H cujos fatores estejam entre os do termo — módulo as
simetrias declaradas —, e disso tira a troca de índices e o que multiplica.
Os termos novos que aparecem viram alvos também, até duas rodadas.

## O que entra sem ser hipótese

O que a forma canônica já sabe (simetrias declaradas, ∇g = 0, o comutador
[∇,∇] como curvatura, o Ricci como contração) e, com Levi-Civita e o Riemann
declarados, a primeira identidade de Bianchi, R^ρ{}_{[σμν]} = 0 — teorema da
torção nula, que a prova cita quando usa.
"""

from __future__ import annotations

import functools
import itertools
import operator

import sympy as sp
from sympy.combinatorics import PermutationGroup
from sympy.tensor.tensor import TensAdd, TensExpr, Tensor, TensorIndex, TensMul

from .derivadas import REGISTRO, derivar, escalar_de

LIMITE_CANDIDATOS = 600
LIMITE_ALVOS = 150
"""Quantos termos a busca persegue. As provas da apostila usam até ~100; sem
teto, um objetivo falso gerava alvo sobre alvo até ∇∇ e levava minutos para
dizer que não achou."""
RODADAS = 3


class SemProvaIndices(ValueError):
    pass


# ------------------------------------------------------------ utilidades

def _termos(expr):
    if expr == 0:
        return []
    if isinstance(expr, TensAdd):
        return list(expr.args)
    return [expr]


def _fatores(termo):
    if isinstance(termo, Tensor):
        return [termo]
    if isinstance(termo, TensMul):
        return [a for a in termo.args if isinstance(a, Tensor)]
    return []


def _produto(fatores):
    return functools.reduce(operator.mul, fatores, sp.S.One)


def _monomio(termo):
    """(chave, coeficiente) de um termo canônico."""
    fatores = _fatores(termo)
    coef = escalar_de(termo) if isinstance(termo, TensMul) else (
        sp.S.One if isinstance(termo, Tensor) else termo)
    return (str(_produto(fatores)) if fatores else "1"), coef


def vetor(expr):
    v = {}
    for t in _termos(expr):
        k, c = _monomio(t)
        v[k] = v.get(k, 0) + c
    return {k: c for k, c in v.items() if sp.simplify(c) != 0}


_N = [0]


def _fresco(espaco, prefixo="pp"):
    _N[0] += 1
    return TensorIndex(f"{prefixo}_{_N[0]}", espaco.tipo)


def _renomear_mudos(expr, espaco):
    """Os mudos de cada termo com nomes novos, que não colidem com os do
    termo com que a relação vai ser contraída."""
    novos = []
    for t in _termos(expr):
        if not isinstance(t, TensExpr):
            novos.append(t)
            continue
        nomes = [i.name for i in t.get_indices()]
        mudos = sorted({n for n in nomes if nomes.count(n) == 2})
        if mudos:
            trocas = [(TensorIndex(n, espaco.tipo), _fresco(espaco, "pm"))
                      for n in mudos]
            t = t.substitute_indices(*trocas)
        novos.append(t)
    return functools.reduce(operator.add, novos) if novos else sp.S.Zero


def _formas(fator):
    """As listas de índices iguais a este fator pelas simetrias da cabeça."""
    indices = list(fator.indices)
    n = len(indices)
    geradores = fator.head.symmetry.generators
    if not geradores:
        return [indices]
    grupo = PermutationGroup(*geradores)
    vistas, saida = set(), []
    for p in grupo.generate():
        imagem = [p(i) for i in range(n)]
        chave = tuple(imagem)
        if chave in vistas:
            continue
        vistas.add(chave)
        saida.append([indices[imagem[k]] for k in range(n)])
    return saida


# ----------------------------------------------------------- as famílias

class Relacao:
    """Uma relação E = 0, com a história de onde veio."""

    def __init__(self, expr, origem, derivadas=(), latex_origem=None, bruto=None):
        self.expr = expr
        # A forma escrita, de onde se deriva: a identidade de Ricci simplifica
        # a zero — a forma canônica já a sabe —, mas ∇ dela não.
        self.bruto = bruto
        self.origem = origem
        self.derivadas = tuple(derivadas)
        self.latex_origem = latex_origem or origem
        self.livres = list(expr.get_free_indices()) if isinstance(
            expr, TensExpr) and expr != 0 else []

    def termos_para_casar(self, espaco):
        """Os termos, e também desdobrados: ∇_ν R, com R o escalar, só casa
        com o traço de ∇R_{αβ} escrito como contração do Riemann."""
        if not hasattr(self, "_termos"):
            from .ricci import desdobrar
            termos = {str(t): t for t in _termos(self.expr)}
            for t in list(termos.values()):
                a = desdobrar(t, espaco)
                if isinstance(a, TensExpr):
                    for x in _termos(a.canon_bp()):
                        termos.setdefault(str(x), x)
            self._termos = list(termos.values())
        return self._termos

    def rotulo(self):
        return "".join(f"∇_{d.name} " for d in reversed(self.derivadas)) + self.origem


def _bianchi(espaco):
    nome, conv = espaco.riemann
    R = espaco.cabeca(nome, 4)
    rho = _fresco(espaco, "pb")
    s, m, n = (_fresco(espaco, "pb") for _ in range(3))
    termos = []
    for a, b, c in ((s, m, n), (m, n, s), (n, s, m)):
        slots = [None] * 4
        slots[conv["rho"]], slots[conv["sigma"]] = rho, -a
        slots[conv["mu"]], slots[conv["nu"]] = -b, -c
        termos.append(R(*slots))
    return functools.reduce(operator.add, termos)


def familias(hipoteses, espaco, simplificar, profundidade=2):
    """Cada hipótese, e ∇ dela até `profundidade` vezes."""
    niveis = [nivel_zero(hipoteses, espaco, simplificar)]
    for _ in range(profundidade):
        niveis.append(proximo_nivel(niveis[-1], espaco, simplificar))
    return [r for n in niveis for r in n]


def nivel_zero(hipoteses, espaco, simplificar):
    base = []
    for nome, expr in hipoteses.items():
        e = simplificar(expr)
        if isinstance(e, TensExpr) and e != 0:
            base.append(Relacao(e, nome, bruto=expr))
        elif isinstance(expr, TensExpr):
            # Zero na forma canônica: não casa com nada, mas as suas
            # derivadas podem não ser zero.
            base.append(Relacao(sp.S.Zero, nome, bruto=expr))
    if (espaco.riemann and espaco.conexao == "levi-civita"):
        base.append(Relacao(simplificar(_bianchi(espaco)), "Bianchi",
                            latex_origem=r"\text{Bianchi}"))
    for r in base:
        if r.expr != 0:
            r.expr = _renomear_mudos(r.expr, espaco)
    return base


def proximo_nivel(atual, espaco, simplificar):
    """∇_c de cada relação do nível anterior."""
    proxima = []
    for r in atual:
        c = _fresco(espaco, "pc")
        base = r.bruto if r.bruto is not None else r.expr
        if base == 0:
            continue
        try:
            bruto = derivar(base, "D", -c, espaco)
            d = simplificar(bruto)
        except RecursionError:
            continue                    # ∇ de uma hipótese grande demais: fica sem
        if isinstance(d, TensExpr) and d != 0:
            proxima.append(Relacao(_renomear_mudos(d, espaco), r.origem,
                                   r.derivadas + (c,), r.latex_origem, bruto=bruto))
        elif isinstance(bruto, TensExpr):
            proxima.append(Relacao(sp.S.Zero, r.origem, r.derivadas + (c,),
                                   r.latex_origem, bruto=bruto))
    return proxima


# ------------------------------------------------------------- o casamento

def _casar(fator_h, forma_t, mapa):
    """Estende `mapa` (nome em h → índice de cima em t) com um fator; None se
    não casa."""
    novo = dict(mapa)
    for hi, ti in zip(fator_h.indices, forma_t):
        alvo = ti if hi.is_up else -ti
        if hi.name in novo and novo[hi.name] != alvo:
            return None
        novo[hi.name] = alvo
    return novo


def _mudos_frescos(fatores, espaco):
    """Os fatores de um termo com os mudos renomeados, um a um — multiplicados
    o SymPy os chamaria de L_0 de novo. Casar um livre da relação com o L_0
    do alvo, numa relação que tem o seu próprio L_0 por dentro, daria dois
    índices iguais, e a candidata se perderia calada."""
    nomes = [i.name for f in fatores for i in f.indices]
    mudos = {n for n in nomes if nomes.count(n) == 2}
    if not mudos:
        return fatores, {}
    novo = {n: _fresco(espaco, "pz") for n in sorted(mudos)}
    saida = []
    for f in fatores:
        trocas = [(i, novo[i.name] if i.is_up else -novo[i.name])
                  for i in f.indices if i.name in novo]
        saida.append(f.substitute_indices(*trocas) if trocas else f)
    # para o certificado: os nomes novos voltam a ser os do objetivo
    return saida, {v.name: TensorIndex(n, espaco.tipo) for n, v in novo.items()}


def _de_volta(indice, voltar):
    if indice.name not in voltar:
        return indice
    original = voltar[indice.name]
    return original if indice.is_up else -original


def _casamentos(termo_h, termo_t, metrica=None, ft=None):
    """Cada modo de pôr os fatores de h entre os de t: (mapa, índices de t
    usados). Um fator da métrica em h não precisa casar: a relação pode ser
    contraída com g^{..} que o cancela."""
    fh = _fatores(termo_h)
    ft = _fatores(termo_t) if ft is None else ft
    sem_g = [f for f in fh if f.head.name != metrica]
    if metrica and sem_g and len(sem_g) < len(fh):
        fh = sem_g
    if not fh or len(fh) > len(ft):
        return
    opcoes = [[j for j, f in enumerate(ft) if f.head == h.head] for h in fh]
    if any(not o for o in opcoes):
        return
    for escolha in itertools.product(*opcoes):
        if len(set(escolha)) != len(escolha):
            continue

        def estender(k, mapa):
            if k == len(fh):
                yield mapa
                return
            for forma in _formas(ft[escolha[k]]):
                m = _casar(fh[k], forma, mapa)
                if m is not None:
                    yield from estender(k + 1, m)

        for mapa in estender(0, {}):
            yield mapa, set(escolha)


def _variantes(c, livres_objetivo):
    """C com os índices livres permutados entre si — cada um na valência do
    objetivo. Uma relação vale com quaisquer nomes; é a permutação que leva
    ∇_μ(∇_σK_ρ + ∇_ρK_σ) a ∇_σ(∇_μK_ρ + ∇_ρK_μ)."""
    livres = list(c.get_free_indices())
    por_nome = {i.name: i for i in livres_objetivo}
    if sorted(i.name for i in livres) != sorted(por_nome) or len(livres) > 4:
        return []
    saida = []
    nomes = [i.name for i in livres]
    for perm in itertools.permutations(nomes):
        if list(perm) == nomes:
            continue
        trocas = [(i, por_nome[n]) for i, n in zip(livres, perm)]
        saida.append((c.substitute_indices(*trocas),
                      [(i.name, n) for i, n in zip(livres, perm) if i.name != n]))
    return saida


def _trocas(livres, mapa, espaco):
    """Os índices livres da relação pelos do alvo. Dois livres que caem no
    mesmo índice, um em cima e outro embaixo, são um traço: cada um ganha um
    nome novo e g os contrai — substituir direto criaria um mudo dentro de uma
    soma, que o SymPy recusa."""
    alvos = {i: (mapa[i.name] if i.is_up else -mapa[i.name]) for i in livres}
    por_nome = {}
    for i, a in alvos.items():
        por_nome.setdefault(a.name, []).append(i)
    trocas, metricas = [], []
    g = espaco.cabeca(espaco.metrica, 2) if espaco.metrica else None
    for nome, quem in por_nome.items():
        if len(quem) == 1:
            trocas.append((quem[0], alvos[quem[0]]))
        elif len(quem) == 2 and alvos[quem[0]] == -alvos[quem[1]] and g is not None:
            novos = []
            for i in quem:
                p = _fresco(espaco, "pt")
                novo = p if i.is_up else -p
                trocas.append((i, novo))
                novos.append(-novo)
            metricas.append(g(*novos))
        else:
            return None, None
    return trocas, metricas


def _com_tracos(mapa, livres, espaco):
    """Os livres da relação que o casamento não alcançou, contraídos dois a
    dois — o traço da relação, que é também relação. Até quatro."""
    soltos = [i for i in livres if i.name not in mapa]
    if not soltos:
        yield mapa
        return
    if len(soltos) % 2 or len(soltos) > 4 or not espaco.metrica:
        return
    def pareamentos(xs):
        if not xs:
            yield []
            return
        a = xs[0]
        for k in range(1, len(xs)):
            for resto in pareamentos(xs[1:k] + xs[k + 1:]):
                yield [(a, xs[k])] + resto
    for pares in pareamentos(soltos):
        novo = dict(mapa)
        for a, b in pares:
            t = _fresco(espaco, "pq")
            novo[a.name] = t if a.is_up else -t
            novo[b.name] = -t if b.is_up else t
        yield novo


def candidatos(alvo, relacoes, espaco, simplificar, vistos, livres=None):
    saida = []

    def entra(c, r, trocas, cofator):
        chave = str(c)
        if chave in vistos:
            return
        vistos.add(chave)
        saida.append((c, r, trocas, cofator))

    for termo in _termos(alvo):
        originais = _fatores(termo)
        ft, voltar = _mudos_frescos(originais, espaco)
        for r in relacoes:
            if r.expr == 0:
                continue
            for th in r.termos_para_casar(espaco):
                pares = [(m, u) for m0, u in _casamentos(th, termo, espaco.metrica, ft)
                         for m in _com_tracos(m0, r.livres, espaco)]
                for mapa, usados in pares:
                    trocas, metricas = _trocas(r.livres, mapa, espaco)
                    if trocas is None:
                        continue
                    try:
                        instancia = _produto(metricas) * \
                            r.expr.substitute_indices(*trocas)
                        cofator = _produto([f for j, f in enumerate(ft)
                                            if j not in usados])
                        c = simplificar(cofator * instancia)
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(c, TensExpr) or c == 0 or str(c) in vistos:
                        continue
                    exibidas = [(a, _de_volta(b, voltar)) for a, b in trocas]
                    exibido = _produto([f for j, f in enumerate(originais)
                                        if j not in usados])
                    entra(c, r, exibidas, exibido)
                    for v, perm in _variantes(c, livres or []):
                        v = simplificar(v)
                        if isinstance(v, TensExpr) and v != 0:
                            entra(v, r, exibidas + [("perm", perm)], exibido)
                    if len(vistos) > LIMITE_CANDIDATOS:
                        return saida
    return saida


# -------------------------------------------------------- a álgebra linear

def _resolver(objetivo, lista):
    """x com objetivo = Σ x_i C_i, ou None."""
    vo = vetor(objetivo)
    vs = [vetor(c) for c, *_ in lista]
    chaves = sorted(set(vo).union(*vs)) if vs else sorted(vo)
    xs = sp.symbols(f"x0:{len(lista)}")
    equacoes = [sum(v.get(k, 0) * x for v, x in zip(vs, xs)) - vo.get(k, 0)
                for k in chaves]
    solucao = sp.linsolve(equacoes, xs)
    if not solucao:
        return None
    sol = next(iter(solucao))
    livres = set().union(*(s.free_symbols for s in sol)) & set(xs)
    return [sp.simplify(s.subs({x: 0 for x in livres})) for s in sol]


class ProvaIndices:
    def __init__(self, objetivo, passos, usadas, condicoes=()):
        self.objetivo = objetivo
        self.passos = passos            # [(coef, relação, trocas, cofator, expr)]
        self.hipoteses_usadas = usadas
        # Os denominadores dos coeficientes: dividir por d − 2 é supor d ≠ 2,
        # e a prova só vale onde eles não se anulam — dito, e não calado.
        self.condicoes = list(condicoes)


def provar(objetivo, hipoteses, espaco, simplificar):
    """O objetivo (expressão = 0) a partir das hipóteses {nome: expressão}."""
    alvo = simplificar(objetivo)
    if alvo == 0:
        return ProvaIndices(objetivo, [], [])
    livres = alvo.get_free_indices() if isinstance(alvo, TensExpr) else []
    # A mesma conta aparece muitas vezes: guardada pela escrita.
    memoria = {}

    def simp(e):
        k = str(e)
        if k not in memoria:
            memoria[k] = simplificar(e)
        return memoria[k]

    # Aprofundando aos poucos: ∇∇ de uma hipótese grande custa caro, e a
    # maioria das provas não precisa. O que já se fez não se refaz.
    estado = _Estado(alvo)
    niveis = [nivel_zero(hipoteses, espaco, simp)]
    for profundidade in range(3):
        if profundidade:
            niveis.append(proximo_nivel(niveis[-1], espaco, simp))
        relacoes = [r for n in niveis for r in n]
        achada = _buscar(objetivo, alvo, relacoes, espaco, simp, livres, estado)
        if achada is not None:
            return achada
    raise SemProvaIndices(
        "não achei combinação das hipóteses que dê o objetivo — o que não "
        "prova que seja falso: a busca vai até ∇∇ das hipóteses e casa termo "
        "a termo, e pode faltar hipótese")


class _Estado:
    """O que a busca já fez, entre uma profundidade e a seguinte."""

    def __init__(self, alvo):
        self.vistos, self.lista = set(), []
        self.alvos = {}                 # escrita do termo -> termos a casar
        self.feitos = set()             # (termo, relação) já casados
        self._alvo(alvo)

    def _alvo(self, expr):
        novos = []
        for t in _termos(expr):
            k = str(t)
            if k in self.alvos:
                continue
            self.alvos[k] = [t]
            novos.append(k)
        return novos


def _buscar(objetivo, alvo, relacoes, espaco, simplificar, livres, estado):
    from .ricci import desdobrar
    pendentes = list(estado.alvos)
    for _ in range(RODADAS):
        novos = []
        for k in pendentes:
            (t,) = estado.alvos[k][:1]
            aberto = desdobrar(t, espaco)
            aberto = aberto.canon_bp() if isinstance(aberto, TensExpr) else aberto
            formas = list({str(x): x for x in [t, aberto]}.values())
            for r in relacoes:
                if (k, id(r)) in estado.feitos:
                    continue
                estado.feitos.add((k, id(r)))
                for alvo_t in formas:
                    novos += candidatos(alvo_t, [r], espaco, simplificar,
                                        estado.vistos, livres)
        estado.lista += novos
        if estado.lista:
            x = _resolver(alvo, estado.lista)
            if x is not None:
                return _certificado(objetivo, alvo, estado.lista, x, simplificar)
        if not novos:
            break
        pendentes = []
        for c, *_ in novos:
            if len(estado.alvos) >= LIMITE_ALVOS:
                break
            pendentes += estado._alvo(c)
        pendentes = list(estado.alvos) if not pendentes else pendentes
    return None


def _certificado(objetivo, alvo, lista, x, simplificar):
    passos = [(c, *item) for c, item in zip(x, lista) if c != 0]
    soma = functools.reduce(operator.add,
                            [c * item[0] for c, *item in passos], sp.S.Zero)
    resto = simplificar(alvo - soma) if isinstance(alvo - soma, TensExpr) \
        else sp.simplify(alvo - soma)
    if resto != 0:
        raise SemProvaIndices("a combinação achada não fecha ao conferir — "
                              "defeito do motor, e não prova")
    usadas = list(dict.fromkeys(r.origem for _, _, r, _, _ in passos))
    condicoes = []
    for c, *_ in passos:
        for fator in sp.factor_list(sp.denom(sp.together(c)))[1]:
            base = fator[0]
            if base.free_symbols and base not in condicoes:
                condicoes.append(base)
    return ProvaIndices(objetivo, [(c, r, trocas, cofator, expr)
                                   for c, expr, r, trocas, cofator in passos],
                        usadas, condicoes)


def linhas(prova, latex_de):
    saida = []
    for coef, r, trocas, cofator, expr in prova.passos:
        c = "" if coef == 1 else ("−" if coef == -1 else f"{coef} ·")
        simples = [(a, b) for a, b in trocas if a != "perm"]
        troca = ", ".join(f"{a.name}→{b.name}" for a, b in simples
                          if a.name != b.name and not b.name.startswith("pt_"))
        tracos = [a.name for a, b in simples if b.name.startswith("pt_")]
        for x, y in zip(tracos[::2], tracos[1::2]):
            troca += (", " if troca else "") + f"{x} com {y} contraídos"
        for a, perm in trocas:
            if a == "perm":
                troca += "; depois " + ", ".join(f"{x}→{y}" for x, y in perm)
        rotulo = r.rotulo() + (f" [{troca}]" if troca else "")
        if cofator != 1:
            rotulo += f" × {cofator}"
        saida.append([f"{c} {rotulo}".strip(), f"{sp.sstr(expr)} = 0",
                      latex_de(expr) + " = 0"])
    return saida
