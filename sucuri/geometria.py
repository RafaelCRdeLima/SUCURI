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


_CARTAS = 0


def _isolado(calculo):
    """Cada cálculo com o cache do SymPy limpo.

    Com o cache cheio, o cálculo de uma métrica recebia objetos feitos no
    cálculo de outra: o R de FRW em (t, x, y, z) saía com um Subs cujo ponto
    era o t de uma carta (t, r, θ, φ) usada antes — nem os nomes únicos das
    cartas impediam. Limpar custa pouco, e um resultado deixa de poder
    depender do que se calculou antes dele.
    """
    import functools
    from sympy.core.cache import clear_cache

    @functools.wraps(calculo)
    def envolto(*args, **kwargs):
        clear_cache()
        return calculo(*args, **kwargs)
    return envolto


class Metrica:
    """Uma métrica com as suas coordenadas — pela diagonal ou pela matriz."""

    def __init__(self, nome, coordenadas, componentes, escrita=None):
        # Com o cache cheio, uma derivada f′(ϖ) das componentes voltava com o
        # ponto de Subs no campo de outra carta — a métrica de onde esta foi
        # induzida, com o mesmo ϖ —, e o diffgeom recusava a mistura.
        from sympy.core.cache import clear_cache
        clear_cache()
        if isinstance(componentes, sp.MatrixBase):
            G = sp.Matrix(componentes)
            if G.shape != (len(coordenadas),) * 2 or G != G.T:
                raise ValueError("a matriz da métrica tem de ser quadrada, "
                                 "simétrica, uma linha por coordenada")
        else:
            if len(coordenadas) != len(componentes):
                raise ValueError(
                    f"{len(coordenadas)} coordenada(s) e {len(componentes)} "
                    f"componente(s): a diagonal tem de ter uma entrada por "
                    f"coordenada")
            G = sp.diag(*componentes)
        self.G = G
        self.nome = nome
        self.escrito = nome             # com a barra, se foi escrito `\\eta`
        self.escrita = escrita or {}    # 'theta' -> '\\theta', como foi escrito
        self.simbolos = list(coordenadas)
        self.componentes = [G[i, i] for i in range(G.shape[0])]

        # Um sistema de coordenadas por métrica, com nome único. O SymPy
        # compara sistemas pelo nome, e não pelos símbolos: duas métricas
        # chamadas g, em cartas diferentes, davam campos "iguais", e o cache
        # devolvia, no cálculo de uma, objetos feitos com as coordenadas da
        # outra — o ponto de um Subs era o t de (t, r, θ, φ) dentro de uma
        # conta em (t, x, y, z).
        global _CARTAS
        _CARTAS += 1
        self.variedade = Manifold(f"M_{nome}_{_CARTAS}", len(coordenadas))
        self.carta = Patch(f"P_{nome}_{_CARTAS}", self.variedade)
        self.sistema = CoordSystem(f"x_{_CARTAS}", self.carta, self.simbolos)

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
        n = len(formas)
        self.tensor = sum(
            (G[i, j].subs(troca, simultaneous=True) * TensorProduct(formas[i], formas[j])
             for i in range(n) for j in range(n) if G[i, j] != 0),
            sp.S.Zero)

    @property
    def coordenadas(self):
        """Como foram escritas, e não como o SymPy as chama."""
        return ", ".join(self.escrita.get(str(s), str(s))
                         for s in self.simbolos)

    def matriz(self):
        return self.G

    @property
    def diagonal(self):
        return self.G.is_diagonal()


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
            valor = _sem_subs(sp.simplify(valor.subs(de_volta, simultaneous=True)),
                              de_volta)
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


@_isolado
def christoffel(metrica):
    return nao_nulas(metric_to_Christoffel_2nd(metrica.tensor),
                     metrica.simbolos, 3, escrita=metrica.escrita,
                     de_volta=metrica.de_volta)


@_isolado
def ricci(metrica):
    return nao_nulas(metric_to_Ricci_components(metrica.tensor),
                     metrica.simbolos, 2, cima=0, escrita=metrica.escrita,
                     de_volta=metrica.de_volta)


@_isolado
def riemann(metrica):
    return nao_nulas(metric_to_Riemann_components(metrica.tensor),
                     metrica.simbolos, 4, escrita=metrica.escrita,
                     de_volta=metrica.de_volta)


@_isolado
def escalar(metrica):
    """O escalar de Ricci: R = g^{\\mu\\nu} R_{\\mu\\nu}."""
    R = metric_to_Ricci_components(metrica.tensor)
    inversa = metrica.matriz().inv()
    n = len(metrica.simbolos)
    bruto = sum(inversa[i, j] * R[i, j] for i in range(n) for j in range(n))
    valor = _sem_subs(sp.simplify(sp.sympify(bruto).subs(metrica.de_volta,
                                                         simultaneous=True)),
                      metrica.de_volta)
    # Fatorado: (2f′² + 2)f′f″/(ϖ(f′² + 1)³) é 2f′f″/(ϖ(1 + f′²)²).
    fatorado = sp.factor(sp.cancel(valor))
    return fatorado if sp.count_ops(fatorado) <= sp.count_ops(valor) else valor


def _sem_subs(valor, de_volta=None):
    """Subs(Derivative(f(ξ), ξ), ξ, r) é f'(r): o diffgeom deixa a derivada
    avaliada por substituição, que está certa e é ilegível.

    E o ponto da substituição é o campo escalar do diffgeom, não o símbolo r:
    a troca de volta não entra no ponto de um Subs, e o campo vazava para a
    saída. O ponto é trocado aqui, junto com a avaliação."""
    valor = sp.sympify(valor)
    if not valor.has(sp.Subs):
        return valor
    de_volta = de_volta or {}

    def avaliar(e):
        pontos = [de_volta.get(p, p) for p in e.point]
        return e.expr.subs(dict(zip(e.variables, pontos)))

    # Sem simplify depois: ele reescreve a derivada de volta como Subs.
    return valor.replace(lambda e: isinstance(e, sp.Subs), avaliar)


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


@_isolado
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


# ------------------------------------------------ Γ direto da matriz

def gamma(metrica):
    """Γ^a_{bc} = ½ g^{ad}(∂_b g_{dc} + ∂_c g_{db} − ∂_d g_{bc}), das componentes.

    Direto da matriz, sem o diffgeom: para geodésicas e transporte, onde as
    componentes entram numa equação e não numa tabela."""
    G, x = metrica.matriz(), metrica.simbolos
    n = len(x)
    inv = G.inv()
    return [[[sp.simplify(sum(inv[a, d] * (sp.diff(G[d, c], x[b]) + sp.diff(G[d, b], x[c])
                                           - sp.diff(G[b, c], x[d])) for d in range(n)) / 2)
              for c in range(n)] for b in range(n)] for a in range(n)]


def geodesicas(metrica, parametro=None):
    """As equações das geodésicas, e o que se conserva ao longo delas.

    ẍ^a + Γ^a_{bc} ẋ^b ẋ^c = 0, com x^a(λ). Conserva-se g_{ab}ẋ^a ẋ^b sempre
    (λ afim), e g_{kb}ẋ^b para cada coordenada x^k de que a métrica não
    depende — o vetor ∂_k é de Killing.
    """
    lam = parametro or sp.Symbol("lambda")
    x = metrica.simbolos
    n = len(x)
    curva = [sp.Function(str(c))(lam) for c in x]
    na_curva = dict(zip(x, curva))
    v = [sp.diff(c, lam) for c in curva]
    G = metrica.matriz().subs(na_curva, simultaneous=True)
    Gam = gamma(metrica)
    equacoes = []
    for a in range(n):
        termo = sum(Gam[a][b][c].subs(na_curva, simultaneous=True) * v[b] * v[c]
                    for b in range(n) for c in range(n))
        equacoes.append(sp.Eq(sp.diff(curva[a], lam, 2) + sp.simplify(termo), 0))
    conservadas = [("normalização", sp.simplify(sum(G[a, b] * v[a] * v[b]
                                                    for a in range(n) for b in range(n))))]
    for k in range(n):
        if all(sp.diff(metrica.matriz()[i, j], x[k]) == 0 for i in range(n) for j in range(n)):
            conservadas.append((f"∂/∂{metrica.escrita.get(str(x[k]), str(x[k]))} é de Killing",
                                sp.simplify(sum(G[k, b] * v[b] for b in range(n)))))
    return equacoes, conservadas, curva, lam


def elemento_de_volume(metrica):
    """√|det g| sem o módulo: |sin²ψ sin θ| escrito sin²ψ sin θ. Quem integra
    confere o sinal no domínio (volume); aqui é a forma que o livro escreve."""
    det = sp.factor(sp.simplify(metrica.matriz().det()))
    raiz = sp.powdenest(sp.sqrt(sp.Abs(det)), force=True)
    raiz = raiz.replace(lambda e: isinstance(e, sp.Abs), lambda e: e.args[0])
    return det, sp.simplify(raiz)


def volume(metrica, limites):
    """∫ √|det g| dⁿx nos limites dados, [(símbolo, a, b)] na ordem de fora
    para dentro. Confere, em pontos do domínio, que o integrando escrito sem
    módulo é positivo — senão recusa, em vez de devolver um volume com sinal."""
    import random
    _, raiz = elemento_de_volume(metrica)
    usados = {s for s, _, _ in limites}
    livres = [x for x in metrica.simbolos if x not in usados]
    if livres:
        raise ValueError("faltam os limites de " + ", ".join(map(str, livres)))
    rnd = random.Random(0)
    for _ in range(12):
        ponto = {}
        for s_, a, b in limites:
            ponto[s_] = a + (b - a) * sp.Rational(rnd.randint(1, 99), 100)
        valor = raiz.subs(ponto)
        outros = valor.free_symbols
        valor = valor.subs({f: sp.Rational(7, 10) for f in outros})
        try:
            if float(sp.N(valor)) < 0:
                raise ValueError("o integrando √|det g| sem módulo fica negativo "
                                 "em parte do domínio: divida o domínio")
        except TypeError:
            pass
    integral = raiz
    for s_, a, b in reversed(limites):
        integral = sp.integrate(integral, (s_, a, b))
    return raiz, sp.simplify(integral)


def induzida(ambiente, coordenadas, imagens, escrita=None, nome="h"):
    """O pull-back de uma métrica: h_{ij} = ∂_i X^a ∂_j X^b g_{ab}(X(u)).

    Serve ao mergulho — a superfície x² + y² + z² + w² = 1 parametrizada — e à
    mudança de coordenadas, que é o mesmo cálculo com tantas coordenadas novas
    quanto antigas."""
    if len(imagens) != len(ambiente.simbolos):
        raise ValueError(
            f"a métrica {ambiente.nome} tem {len(ambiente.simbolos)} coordenadas "
            f"({ambiente.coordenadas}), e foram dadas {len(imagens)} expressões")
    X = sp.Matrix(imagens)
    J = X.jacobian(sp.Matrix(coordenadas))
    G = ambiente.matriz().subs(dict(zip(ambiente.simbolos, imagens)), simultaneous=True)
    H = (J.T * G * J).applyfunc(lambda e: sp.trigsimp(sp.simplify(e)))
    return Metrica(nome, coordenadas, H, escrita)


def orbitas(metrica):
    """As geodésicas de uma métrica 2D diagonal com uma coordenada cíclica,
    por quadratura — o método dos livros.

    Com φ cíclica, L = g_φφ φ̇ e κ = g_rr ṙ² + g_φφ φ̇² se conservam (κ = ±1 ou
    0, conforme a geodésica). Daí dφ/dr, e com v tal que dv = √|g_rr|/g_φφ dr
    a integral vira ∫ L dv/√(±(κ − L²/g_φφ)): a substituição de Binet, que na
    esfera é v = −cot θ e em de Sitter 2D é v = tanh u. Quando o radicando sai
    A + Bv² com B < 0, a órbita é v = √(A/−B) sen(√−B (φ − φ₀)/L).
    """
    x = metrica.simbolos
    G = metrica.matriz()
    if len(x) != 2 or not metrica.diagonal:
        raise ValueError("órbitas pede uma métrica 2D diagonal")
    ciclicas = [k for k in range(2) if all(sp.diff(G[i, i], x[k]) == 0 for i in range(2))]
    if not ciclicas:
        raise ValueError("nenhuma coordenada cíclica: a métrica depende das duas, "
                         "e a quadratura pede uma de que ela não dependa")
    kf = ciclicas[-1]
    kr = 1 - kf
    r, phi = x[kr], x[kf]
    rp = sp.Dummy("r", positive=True)
    grr, gff = G[kr, kr].subs(r, rp), G[kf, kf].subs(r, rp)
    L = sp.Symbol("L", positive=True)
    kappa, v = sp.symbols("kappa v")
    phi0 = sp.Symbol(f"{phi}_0")
    sinal = -1 if (grr.is_number and grr < 0) else 1
    dphi_dr = sp.simplify(L / gff / sp.sqrt((kappa - L**2 / gff) / grr)).subs(rp, r)
    v_de_r = sp.simplify(sp.integrate(sp.sqrt(sinal * grr) / gff, rp))
    saida = {"r": r, "phi": phi, "dphi_dr": dphi_dr, "v": v_de_r.subs(rp, r)}
    # O ramo da inversa que é real: v = tanh u tem duas, e uma é log de negativo.
    def _real(q):
        teste = q.subs(v, sp.Rational(3, 10))
        teste = teste.subs({f: sp.Rational(7, 10) for f in teste.free_symbols})
        return sp.N(teste).is_real
    reais = [q for q in sp.solve(sp.Eq(v, v_de_r), rp) if _real(q)]
    if not reais:
        return saida
    w = sp.simplify((1 / gff).subs(rp, reais[0]))
    if not w.is_polynomial(v):
        # 1/cosh²(log …) só vira 1 − v² escrito em exponenciais.
        w = sp.cancel(sp.expand(w.rewrite(sp.exp)))
    radicando = sp.expand(sinal * (kappa - L**2 * w))
    A, B, C = radicando.coeff(v, 0), radicando.coeff(v, 2), radicando.coeff(v, 1)
    if B == 0 and C != 0 and sp.expand(radicando - A - C * v) == 0:
        # Linear em v — o plano hiperbólico: ∫ L dv/√(A + Cv) = 2L√(A + Cv)/C.
        F = sp.simplify(2 * L * sp.sqrt(A + C * v) / C)
        saida.update({"radicando": radicando, "condicao": sp.simplify(radicando.subs(v, saida["v"])) > 0,
                      "integral": F,
                      "orbita": [sp.Eq(phi - phi0, sp.simplify(F.subs(v, saida["v"])))]})
        return saida
    if sp.expand(radicando - A - B * v**2) != 0 or not (B.subs(L, 1).is_negative):
        return saida
    # ∫ L dv/√(A + Bv²) = L/√−B · asen(v √(−B/A)), com A > 0.
    F = sp.simplify(L / sp.sqrt(-B) * sp.asin(v * sp.sqrt(-B / A)))
    orbita = sp.simplify(sp.sqrt(A / -B) * sp.sin(sp.sqrt(-B) * (phi - phi0) / L))
    saida.update({"radicando": radicando, "condicao": sp.simplify(A) > 0,
                  "integral": F, "orbita": [sp.Eq(saida["v"], orbita)]})
    return saida


def elemento_de_linha(metrica):
    """ds² = g_{ij} dx^i dx^j, com dx^i escritos como símbolos d<coordenada>."""
    x = metrica.simbolos
    d = [sp.Symbol("d" + metrica.escrita.get(str(c), str(c)).lstrip("\\")) for c in x]
    G = metrica.matriz()
    n = len(x)
    return sp.Add(*[sp.factor(G[i, j] if i == j else 2 * G[i, j]) * d[i] * d[j]
                    for i in range(n) for j in range(i, n) if G[i, j] != 0])
