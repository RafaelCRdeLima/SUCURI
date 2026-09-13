"""O documento: declarações, anotações e a recusa de adivinhar.

Um `Document` guarda as convenções em vigor — qual é a variável independente,
quais nomes são funções, se linha significa derivada — e, com elas, resolve
sozinho a maior parte dos sítios ambíguos. O que sobrar fica pendente, e a
expressão RECUSA-SE a virar SymPy enquanto houver pendência.

É esse o ponto do programa. Um parser entrega expressão errada em silêncio; o
Sucuri entrega uma pergunta.
"""

from __future__ import annotations

import re

import sympy as sp

from .ambiguity import contido, find


class Resolution:
    """Como um sítio ambíguo foi resolvido — e não apenas se foi.

    A distinção importa e veio da identidade visual, que reserva o âmbar para
    "ambiguidade resolvida por inferência". Uma convenção de documento pode
    acertar nove sítios e errar o décimo em silêncio: quem declarou que linha é
    derivada não olhou cada linha. Marcar esses sítios permite à interface
    pedir conferência sem bloquear o trabalho.

    Os três estados, na ordem de confiança:

      EXPLICIT  anotação feita para este sítio        (verde)
      INFERRED  convenção do documento aplicada aqui  (âmbar)
      PENDING   sem leitura definida                  (bloqueia)
    """

    EXPLICIT = "explícita"
    INFERRED = "inferida"
    PENDING = "pendente"

    def __init__(self, ambiguity, reading, how):
        self.ambiguity = ambiguity
        self.reading = reading
        self.how = how

    @property
    def needs_review(self):
        """Verdadeiro para o que foi inferido: correto até prova em contrário."""
        return self.how == Resolution.INFERRED

    def __repr__(self):
        alvo = self.reading or "—"
        return f"<{self.ambiguity.fragment!r} -> {alvo} [{self.how}]>"


class Unresolved(Exception):
    """Há sítio ambíguo sem anotação. Carrega a lista."""

    def __init__(self, pendentes):
        self.pending = list(pendentes)
        corpo = "\n".join(
            f"  {a.fragment!r}: " + " ou ".join(r.key for r in a.readings)
            for a in self.pending)
        super().__init__(
            f"{len(self.pending)} sítio(s) ambíguo(s) sem anotação:\n{corpo}\n"
            "Anote com .annotate(...) ou declare a convenção no documento.")


# Macros que VIRAM símbolo legitimamente: o alfabeto grego e um punhado de
# letras especiais. Fora desta lista, macro que reaparece como símbolo do mesmo
# nome foi degradada pelo parser — \coth virou o símbolo "coth" multiplicando x.
_MACROS_SIMBOLO = frozenset("""
    alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota
    kappa lambda mu nu xi omicron pi varpi rho varrho sigma varsigma tau
    upsilon phi varphi chi psi omega
    Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
    ell hbar imath jmath aleph
""".split())

_RE_MACRO = re.compile(r"\\([a-zA-Z]+)")
_RE_MARCADOR = re.compile(r"^Z_\{\d+\}$")


_RE_OVER = re.compile(r"\\over(?![a-zA-Z])")


def _inofensivas(texto):
    """Reescritas de LaTeX para LaTeX que não mudam significado nenhum.

    Não é adivinhação, é tradução: \\left| e \\right| são a mesma barra de |, e
    {a \\over b} é a forma primitiva do TeX para \\frac{a}{b}. O parser do SymPy
    não conhece nenhuma das duas, e as duas aparecem em qualquer tabela.

    Fica no fim do `_normalize` de propósito: os sítios ambíguos foram
    localizados por posição no texto original, e reescrever antes deslocaria
    todos eles.
    """
    # \vert, \lvert e \rvert são a mesma barra de |. \Vert e \lVert NÃO são:
    # aquelas são norma, e quem trocar uma pela outra troca o significado.
    for macro in ("\\lvert", "\\rvert", "\\vert"):
        texto = texto.replace(macro, "|")
    texto = texto.replace("\\left|", "|").replace("\\right|", "|")
    while True:
        m = _RE_OVER.search(texto)
        if m is None:
            return texto
        i = _grupo_esquerda(texto, m.start())
        j = _grupo_direita(texto, m.end())
        numerador = texto[i + 1:m.start()].strip()
        denominador = texto[m.end():j].strip()
        texto = (texto[:i + 1] + "\\frac{" + numerador + "}{" + denominador + "}"
                 + texto[j:])


def _grupo_esquerda(texto, k):
    """Índice da chave que abre o grupo onde `k` está, ou -1."""
    fundo = 0
    for i in range(k - 1, -1, -1):
        if texto[i] == "}":
            fundo += 1
        elif texto[i] == "{":
            if fundo == 0:
                return i
            fundo -= 1
    return -1


def _grupo_direita(texto, k):
    """Índice da chave que fecha o grupo onde `k` está, ou len(texto)."""
    fundo = 0
    for j in range(k, len(texto)):
        if texto[j] == "{":
            fundo += 1
        elif texto[j] == "}":
            if fundo == 0:
                return j
            fundo -= 1
    return len(texto)


def _canonizar(expr):
    r"""Conserta objetos que o parser monta sem avaliar.

    \log_a x vira um log de DOIS argumentos que o SymPy deixa por avaliar — e
    esse objeto deriva errado: d/dx log(x, a) devolve 1/x, sem o ln(a). O mesmo
    log construído por sp.log(x, a) vira log(x)/log(a) e deriva certo.

    Reconstruí-lo é identidade exata (log_b x = ln x / ln b), não é escolha de
    leitura. Fica aqui porque o silêncio é do mesmo tipo dos outros: a conta
    segue, o resultado é errado, e nada avisa.
    """
    return expr.replace(
        lambda e: isinstance(e, sp.log) and len(e.args) == 2,
        lambda e: sp.log(e.args[0], e.args[1]))


def _exige(variavel, sitio, qual, parametro):
    """A variável tem de existir ANTES de virar derivada.

    A convenção do documento já cobrava isso; a anotação de um sítio, não —
    e por ali passava um `Derivative(q(None), (None, 1))`, que estoura lá
    adiante com uma mensagem que não diz nada a quem escreveu a equação. Ler
    "derivada" sem dizer em relação a quê continua sendo ambiguidade, só que
    escondida, e a recusa é a mesma dos dois caminhos.
    """
    if variavel is None:
        raise ValueError(
            f"para ler {sitio} como derivada é preciso uma variável "
            f"{qual}: crie o documento com {parametro}=")


class NotacaoNaoReconhecida(Exception):
    """O parser degradou uma notação em vez de recusá-la.

    O parser de LaTeX do SymPy não avisa quando não entende: \\coth x vira o
    símbolo "coth" multiplicado por x, {1 \\over x} vira 1*(over*x), e
    \\operatorname{arccsc} x vira o produto das letras do nome. A conta segue,
    o resultado é lixo, e nada na saída diz isso.

    Esta é a recusa correspondente: o Sucuri confere se alguma macro reapareceu
    como símbolo do mesmo nome e, se reapareceu, para.
    """

    def __init__(self, nomes, motivo=None):
        self.nomes = list(nomes)
        self.motivo = motivo
        lista = ", ".join("\\" + n for n in self.nomes)
        super().__init__(
            motivo or
            f"notação não reconhecida pelo parser, degradada a símbolo: {lista}. "
            f"Reescreva em notação que o SymPy entenda, ou trate o nome como "
            f"símbolo declarando-o.")


class Document:
    """Contexto de trabalho: convenções, símbolos e anotações."""

    def __init__(self, independent_variable=None, time_variable=None):
        self.independent = (sp.Symbol(independent_variable)
                            if independent_variable else None)
        # O ponto de Newton significa derivada NO TEMPO por convenção, e a
        # linha em relação à variável independente — que em mecânica raramente
        # é a mesma. Guardá-las separadas evita confundir d/dt com d/dx.
        self.time = sp.Symbol(time_variable) if time_variable else None
        self._functions = set()
        self._variables = set()
        self._primes_are_derivatives = None      # None = sem convenção
        self._dots_are_derivatives = None
        self._e_is_euler = None
        self._annotations = {}

    # ------------------------------------------------------- declarações

    def function(self, *names):
        """Declara nomes como funções: `f(x)` é aplicação."""
        self._functions.update(names)
        return self

    def variable(self, *names):
        """Declara nomes como variáveis: `f(x)` é produto."""
        self._variables.update(names)
        return self

    def primes_are_derivatives(self, yes=True, wrt=None):
        """Convenção de documento para a linha.

        Exigir a variável independente é deliberado: 'derivada' sem dizer em
        relação a quê continua sendo uma ambiguidade, só que escondida.
        """
        if yes and wrt is None and self.independent is None:
            raise ValueError(
                "para ler linha como derivada é preciso uma variável "
                "independente: passe wrt= ou crie o documento com "
                "independent_variable=")
        if wrt is not None:
            self.independent = sp.Symbol(wrt)
        self._primes_are_derivatives = bool(yes)
        return self

    def dots_are_time_derivatives(self, yes=True, wrt=None):
        """Convenção para o ponto de Newton.

        Exige a variável temporal pelo mesmo motivo que a linha exige a
        independente: 'derivada' sem dizer em relação a quê é ambiguidade
        escondida.
        """
        if yes and wrt is None and self.time is None:
            raise ValueError(
                "para ler o ponto como derivada é preciso uma variável "
                "temporal: passe wrt= ou crie o documento com time_variable=")
        if wrt is not None:
            self.time = sp.Symbol(wrt)
        self._dots_are_derivatives = bool(yes)
        return self

    def e_is_euler(self, yes=True):
        """Convenção para o 'e' como base de potência.

        Sem ela, e^{ax} fica PENDENTE. Não é preciosismo: lido como símbolo, a
        derivada de e^{ax} é a·e^{ax}·ln(e), e a tabela inteira de exponenciais
        passa a ser refutada — silenciosamente, porque a leitura não avisa.
        """
        self._e_is_euler = bool(yes)
        return self

    def annotate(self, kind, base, reading, **detail):
        """Resolve um sítio específico, uma vez e para sempre."""
        self._annotations[(kind, base, tuple(sorted(detail.items())))] = reading
        return self

    # ------------------------------------------------------------ leitura

    def read(self, latex):
        """Lê a entrada e devolve uma Expression — resolvida ou pendente."""
        return Expression(latex, self)

    def resolve(self, amb):
        """A leitura em vigor para este sítio, ou None se pendente."""
        return self.resolution(amb).reading

    def resolution(self, amb):
        """A leitura E como se chegou a ela.

        Anotação feita para o sítio é EXPLICIT. Convenção de documento aplicada
        a ele é INFERRED — a interface a mostra em âmbar, pedindo conferência.
        """
        if amb.key in self._annotations:
            return Resolution(amb, self._annotations[amb.key], Resolution.EXPLICIT)

        inferida = None
        if amb.kind == "prime" and self._primes_are_derivatives is not None:
            inferida = "derivative" if self._primes_are_derivatives else "symbol"
        elif amb.kind == "juxtaposition":
            if amb.base in self._functions:
                inferida = "application"
            elif amb.base in self._variables:
                inferida = "product"
        elif amb.kind == "newton" and self._dots_are_derivatives is not None:
            inferida = "derivative" if self._dots_are_derivatives else "decoration"
        elif amb.kind == "euler" and self._e_is_euler is not None:
            inferida = "euler" if self._e_is_euler else "symbol"
        elif amb.kind == "partial":
            inferida = "derivative"     # \partial_x só tem uma leitura razoável
        elif amb.kind == "leibniz" and self._primes_are_derivatives is not False:
            inferida = "derivative"

        if inferida is None:
            return Resolution(amb, None, Resolution.PENDING)
        return Resolution(amb, inferida, Resolution.INFERRED)


class Expression:
    """Uma equação do documento: a vista em LaTeX e a semântica, juntas."""

    def __init__(self, latex, document):
        self.source = latex
        self.document = document
        self.ambiguities = find(latex)

    # ------------------------------------------------------------- estado

    @property
    def pending(self):
        """Sítios ainda sem leitura definida."""
        return [a for a in self.ambiguities if self.document.resolve(a) is None]

    @property
    def resolved(self):
        return not self.pending

    @property
    def resolutions(self):
        """Como cada sítio foi resolvido, na ordem da entrada."""
        return [self.document.resolution(a) for a in self.ambiguities]

    @property
    def inferred(self):
        """Sítios resolvidos por convenção, não por anotação do sítio.

        São os que a interface pinta de âmbar: a expressão funciona, mas a
        leitura veio de uma regra geral e ninguém olhou este caso.
        """
        return [r for r in self.resolutions if r.needs_review]

    def questions(self):
        """As perguntas que o programa faria ao usuário, em vez de adivinhar."""
        saida = []
        for a in self.pending:
            opcoes = "; ".join(f"{r.key} = {r.description}" for r in a.readings)
            saida.append(f"{a.fragment!r} — {opcoes}")
        return saida

    # ---------------------------------------------------------- conversão

    def to_sympy(self):
        """A expressão SymPy. Levanta Unresolved se houver pendência.

        A recusa é o comportamento central: nenhuma leitura é escolhida por
        omissão, porque escolher por omissão é exatamente o que produz o erro
        silencioso.
        """
        if self.pending:
            raise Unresolved(self.pending)

        texto, reposicoes, derivadas, _ = self._normalize()
        from sympy.parsing.latex import parse_latex
        expr = parse_latex(texto)
        if reposicoes:
            expr = expr.subs(reposicoes, simultaneous=True)

        # Coerência: se um símbolo aparece derivado, ele É função da variável
        # independente, e as suas ocorrências SEM linha também. Sem isto a
        # mesma letra viraria dois objetos distintos na mesma equação — erro
        # silencioso do tipo que este programa existe para impedir.
        if derivadas:
            promocao = {sp.Symbol(nome): sp.Function(nome)(var)
                        for nome, var in derivadas}
            expr = expr.subs(promocao, simultaneous=True)

        expr = _canonizar(expr)
        self._conferir(texto, expr)
        return expr

    def _conferir(self, texto, expr):
        """A saída é feita só de coisas que alguém leu de propósito?

        Duas perguntas. A primeira é sobre o Sucuri: sobrou marcador interno na
        saída? Se sobrou, é defeito daqui, e defeito silencioso — foi assim que
        f'(x) saía como Z_{0}(x). A segunda é sobre o parser: alguma macro
        reapareceu como símbolo do mesmo nome, isto é, foi degradada?
        """
        nomes = {s.name for s in expr.free_symbols}
        nomes |= {f.func.__name__
                  for f in expr.atoms(sp.core.function.AppliedUndef)}

        vazados = sorted(n for n in nomes if _RE_MARCADOR.match(n))
        if vazados:
            raise NotacaoNaoReconhecida(
                vazados,
                f"marcador interno do Sucuri vazou para a saída ({', '.join(vazados)}); "
                f"isto é defeito do Sucuri, não da entrada")

        degradadas = sorted((set(_RE_MACRO.findall(texto)) - _MACROS_SIMBOLO)
                            & nomes)
        if degradadas:
            raise NotacaoNaoReconhecida(degradadas)

    def _normalize(self):
        """Reescreve a entrada em forma sem ambiguidade, guardando as trocas."""
        doc = self.document
        x = doc.independent
        texto = self.source
        reposicoes = {}
        derivadas = set()
        origens = {}          # subexpressão -> Resolution do sítio que a gerou
        contador = 0

        # O marcador precisa sobreviver ao parser de LaTeX como UM símbolo.
        # Nomes alfabéticos não servem: em LaTeX, letras justapostas são
        # multiplicação, e "cadvar0" vira c*a*d*v*a*r*0. Índice subscrito
        # resolve — Z_{0} é lido como um símbolo só.
        def marcador():
            nonlocal contador
            nome = f"Z_{{{contador}}}"
            contador += 1
            # Espaços em volta: sem eles o marcador cola no macro anterior e
            # "3\\varphi" + "Z_{1}" vira o macro inexistente "\\varphiZ".
            return f" {nome} ", sp.Symbol(nome)

        # De trás para frente: preserva os deslocamentos dos sítios anteriores.
        for a in sorted(self.ambiguities, key=lambda a: -a.span[0]):
            # Sítio dentro de outro sítio não se substitui aqui: o texto dele já
            # foi engolido, e quem o resolve é a leitura recursiva do fragmento.
            if contido(a, self.ambiguities):
                continue
            resolucao = doc.resolution(a)
            leitura = resolucao.reading
            ini, fim = a.span

            if a.kind == "prime":
                ordem = a.detail["order"]
                if leitura == "derivative":
                    _exige(x, "a linha", "independente", "independent_variable")
                nome, simbolo = marcador()
                alvo = self._linha(a, leitura, ordem, x, derivadas)
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "newton":
                nome, simbolo = marcador()
                ordem = a.detail["order"]
                if leitura == "derivative":
                    _exige(self.document.time, "o ponto", "temporal", "time_variable")
                    derivadas.add((a.base, self.document.time))
                    alvo = sp.Derivative(sp.Function(a.base)(self.document.time),
                                         (self.document.time, ordem))
                else:
                    alvo = sp.Symbol(a.base)
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "partial":
                nome, simbolo = marcador()
                v = sp.Symbol(a.detail["wrt"])
                if leitura == "derivative":
                    derivadas.add((a.base, v))
                    alvo = sp.Derivative(sp.Function(a.base)(v), v)
                else:
                    alvo = sp.Symbol(a.base) * sp.Symbol("d_" + a.detail["wrt"])
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "leibniz":
                nome, simbolo = marcador()
                if leitura == "derivative":
                    v = sp.Symbol(a.detail["wrt"])
                    derivadas.add((a.base, v))
                    alvo = sp.Derivative(sp.Function(a.base)(v),
                                         (v, a.detail["order"]))
                else:
                    alvo = (sp.Symbol("d")**a.detail["order"] * sp.Symbol(a.base)
                            / sp.Symbol("d" + a.detail["wrt"])**a.detail["order"])
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "euler":
                nome, simbolo = marcador()
                alvo = sp.E if leitura == "euler" else sp.Symbol("e")
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "juxtaposition" and leitura == "product":
                # insere a multiplicação explícita antes do parêntese
                abre = texto.find("(", ini)
                texto = texto[:abre] + r" \cdot " + texto[abre:]

        return _inofensivas(texto), reposicoes, derivadas, origens

    def _linha(self, a, leitura, ordem, x, derivadas):
        """O objeto que a linha denota, nas quatro formas em que ela aparece.

            f'      derivada de f
            f'(x)   a mesma derivada, dita onde é avaliada
            f'(u)   derivada de f avaliada em u — que NÃO é d/dx f(u)
            (f+g)'  derivada do grupo inteiro

        A terceira é a que obriga ao Subs: derivar f e depois avaliar em u não
        é o mesmo que derivar f(u) em x, e escrever as duas como a mesma coisa
        seria o erro silencioso de sempre.
        """
        arg = a.detail.get("arg")
        grupo = a.detail.get("group")

        if grupo:
            interior = self._fragmento(a.base)
            if leitura != "derivative":
                return interior
            alvo = sp.Derivative(interior, (x, ordem))
            return sp.Subs(alvo, x, self._fragmento(arg)) if arg else alvo

        if leitura != "derivative":
            simbolo = sp.Symbol(a.base + "'" * ordem)
            if arg is None:
                return simbolo
            return sp.Function(a.base + "'" * ordem)(self._fragmento(arg))

        if arg is None:
            derivadas.add((a.base, x))
            return sp.Derivative(sp.Function(a.base)(x), (x, ordem))

        onde = self._fragmento(arg)
        if onde == x:
            derivadas.add((a.base, x))
            return sp.Derivative(sp.Function(a.base)(x), (x, ordem))
        muda = sp.Dummy(a.base + "_arg")
        return sp.Subs(sp.Derivative(sp.Function(a.base)(muda), (muda, ordem)),
                       muda, onde)

    def _fragmento(self, latex):
        """Lê um pedaço da entrada com as mesmas convenções do documento.

        Usado onde um sítio engole texto: o argumento de f'(x), o interior de
        (f+g)'. O pedaço é estritamente menor que a entrada, logo a recursão
        termina.
        """
        return Expression(latex, self.document).to_sympy()

    def tree(self):
        """A árvore reconhecida, com a proveniência de cada nó.

        É o painel central da interface: mostra o que o programa entendeu, e
        marca em âmbar o que ele entendeu por convenção em vez de por decisão.
        """
        from .tree import build
        if self.pending:
            raise Unresolved(self.pending)
        _, _, _, origens = self._normalize()
        return build(self.to_sympy(), origens)

    def to_latex(self):
        """Volta ao LaTeX a partir da semântica — o round-trip de conferência."""
        return sp.latex(self.to_sympy())

    def __repr__(self):
        if self.resolved:
            return f"Expression({self.source!r}) [resolvida]"
        return (f"Expression({self.source!r}) [{len(self.pending)} pendência(s)]\n"
                + "\n".join("  ? " + q for q in self.questions()))

    def _repr_latex_(self):
        return "$$" + self.source + "$$"
