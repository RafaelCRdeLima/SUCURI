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

    def __init__(self, ambiguity, reading, how, motivo=None):
        self.ambiguity = ambiguity
        self.reading = reading
        self.how = how
        self.motivo = motivo

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


_RE_DECLARACAO = re.compile(r"^\s*([A-Za-z][\w]*)\s*(?:=\s*\1\s*)?"
                            r"\(\s*([^)]*)\s*\)\s*$")


def _declaracao(texto):
    """'u(x,t)' e 'u = u(x,t)' -> ('u', ('x', 't'));  'f' -> ('f', None).

    Parêntese, como em livro: "seja u = u(t,x)" é como se declara em prosa, e
    escrito com o mesmo nome dos dois lados é tautologia — ninguém escreve isso
    como equação, então não há colisão com matemática.

    O colchete fica livre, reservado a n-tupla.

    Nota: aqui, onde se DECLARA, 'u(x,t)' sozinho já é declaração, porque o
    campo existe para isso. Na folha do caderno não: lá u(x,t) sozinho é uma
    expressão, e só a forma com "=" declara.
    """
    m = _RE_DECLARACAO.match(texto)
    if not m:
        return texto.strip(), None
    args = tuple(v.strip() for v in m.group(2).split(",") if v.strip())
    return m.group(1), args


def declaracoes(texto):
    """As declarações de uma linha inteira, separadas por vírgula ou ponto e
    vírgula: 'u[x,t]; f' -> [('u', ('x','t')), ('f', None)]."""
    achadas = []
    for pedaco in re.split(r"[;\n]", texto or ""):
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        if "(" in pedaco:
            achadas.append(_declaracao(pedaco))
        else:
            achadas += [(n.strip(), None) for n in pedaco.split(",") if n.strip()]
    return achadas


def _limpo_indice(nome):
    nome = nome.strip()
    return nome[1:] if nome.startswith("\\") else nome


def _porque(nome, args):
    return f"{nome} foi declarada função de {', '.join(str(a) for a in args)}"


class FaltaVariavel(ValueError):
    """Falta dizer em relação a que a derivada é derivada.

    Exceção própria, e não ValueError solto, porque a interface precisa
    RECONHECER este caso para perguntar em vez de só reclamar: ela sabe quais
    letras aparecem na equação, e oferecê-las é o que o programa faz com toda
    ambiguidade. Reclamar de campo vazio é empurrar para o usuário uma pergunta
    que dava para fazer.
    """

    def __init__(self, mensagem, qual, campo):
        self.qual = qual
        self.campo = campo
        super().__init__(mensagem)


def _exige(variavel, sitio, qual, parametro, campo):
    """A variável tem de existir ANTES de virar derivada.

    A convenção do documento já cobrava isso; a anotação de um sítio, não —
    e por ali passava um `Derivative(q(None), (None, 1))`, que estoura lá
    adiante com uma mensagem que não diz nada a quem escreveu a equação. Ler
    "derivada" sem dizer em relação a quê continua sendo ambiguidade, só que
    escondida, e a recusa é a mesma dos dois caminhos.
    """
    if variavel is None:
        raise FaltaVariavel(
            f"para ler {sitio} como derivada é preciso uma variável {qual}: "
            f"preencha '{campo}' nas convenções do documento "
            f"(ou {parametro}= na biblioteca)", qual, campo)


def _nao_derive_a_propria_variavel(base, variavel, qual, escrita="{0}'"):
    """x' com x sendo a própria variável independente é quase sempre engano.

    Quem escreve x' = A e^x quer dizer dx/dt: o x é a função incógnita, e a
    variável é outra. Declarando x como independente, o leitor monta
    Subs(Derivative(x(x), x), x, x(x)) — bem formado, sem sentido, e o SymPy
    segue em frente com ele. Vale a recusa, porque a dúvida aqui não é de
    notação, é de qual letra é a variável.
    """
    if variavel is not None and base == variavel.name:
        raise ValueError(
            f"'{base}' é a variável {qual} do documento, e "
            f"'{escrita.format(base)}' seria a derivada dela em relação a si "
            f"mesma. Se {base} é a função incógnita, declare outra variável "
            f"{qual} — t, por exemplo")


def _distancia(a, b):
    """Quantos erros de digitação separam duas palavras.

    Conta TROCA DE LETRAS VIZINHAS como um erro só, e não dois — \\alpah por
    \\alpha é um dedo fora de ordem, não duas letras erradas. A distinção é o
    que permite exigir distância 1 e ainda assim pegar o engano mais comum,
    sem sugerir \\mathrm para quem escreveu \\mathbb.
    """
    m, n = len(a), len(b)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            custo = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                          d[i - 1][j - 1] + custo)
            if (i > 1 and j > 1 and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]):
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[m][n]


def _com_palpite(nome):
    """O nome, e — se for quase um nome conhecido — o palpite.

    \\partia por \\partial é erro de digitação, não de notação, e a diferença
    importa: uma palavra de conserto vale mais do que a explicação certa do
    problema errado. O leitor conhece o próprio vocabulário, então pode dizer.
    """
    from .ambiguity import _COMANDOS
    vocabulario = set(_COMANDOS) | set(_MACROS_SIMBOLO)
    if nome in vocabulario:
        return nome
    perto = [(d, c) for c in vocabulario if (d := _distancia(nome, c)) <= 1]
    if not perto:
        return nome
    return f"{nome} (quis dizer \\{min(perto)[1]}?)"


_GRUPO = r"(?:\{[^{}]*\}|\\[a-zA-Z]+|[A-Za-z0-9])"
_RE_BASE = r"(?:\\[a-zA-Z]+|[A-Za-z])"
_RE_SUPER = re.compile(rf"({_RE_BASE})\s*\^\s*({_GRUPO})")
_RE_SUB = re.compile(rf"({_RE_BASE})\s*_\s*({_GRUPO})")
# Só esta ordem: o parser do SymPy lê x_i^2 direito (Symbol('x_{i}')**2) e
# estraga x^2_i (devolve x**2, sem o índice). Recusar a ordem que funciona
# seria recusar matemática legítima.
_RE_PERDE = re.compile(rf"({_RE_BASE})\s*\^\s*{_GRUPO}\s*_")


class NotacaoTensorial(Exception):
    r"""Índice não é expoente, e o parser não sabe a diferença.

    Medido no SymPy 1.12 e 1.13:

        A^\mu                    ->  A**mu            (A elevado a μ)
        x^2_i                    ->  x**2             (o índice some)
        \Gamma^\lambda_{\mu\nu}  ->  Gamma**lambda_{mu*nu}
        g_{\mu\nu}               ->  Symbol('g_{mu*nu}')

    Nada disso levanta erro, e nada disso tem símbolo estranho na saída: são
    expressões bem formadas e falsas, que é a pior classe de erro que este
    programa conhece.

    A recusa é estreita de propósito, e cobre só onde o parser COMPROVADAMENTE
    perde informação. A suspeita — um grego no expoente, índices no subscrito —
    vira nota, não recusa: distinguir índice de expoente pela tipografia é
    impossível, e A^\mu é mesmo "A elevado a μ" em algum texto.
    """

    def __init__(self, motivos):
        self.motivos = list(motivos)
        super().__init__(
            "notação tensorial não é lida: " + "; ".join(self.motivos)
            + ". O parser trataria o índice de cima como EXPOENTE e descartaria "
            "o de baixo, devolvendo uma conta bem formada e errada. O SymPy tem "
            "tensores em sympy.tensor.tensor, mas o Sucuri ainda não faz essa "
            "ponte.")


def _gregos_em(padrao, texto):
    achados = set()
    for m in padrao.finditer(texto):
        if _limpo_macro(m.group(1)) in _COMANDOS_ESTRUTURA:
            continue
        for nome in re.findall(r"\\([a-zA-Z]+)", m.group(2)):
            if nome in _MACROS_SIMBOLO:
                achados.add(nome)
    return achados


def _limpo_macro(t):
    return t[1:] if t.startswith("\\") else t


_COMANDOS_ESTRUTURA = {"sum", "int", "prod", "oint", "lim", "bigcup", "bigcap",
                       "iint", "iiint", "coprod", "max", "min", "sup", "inf"}


def indices_tensoriais(texto, declarados=()):
    r"""(recusas, notas) — o que é perda comprovada e o que é suspeita.

    Distinguir índice de expoente pela tipografia é impossível: A^\mu é "A
    elevado a μ" ou "A com índice contravariante μ", e as duas se escrevem
    igual. Então não se adivinha. Recusa-se onde o parser PERDE — e onde há a
    marca que só a soma de Einstein deixa —, e avisa-se onde há suspeita.
    """
    recusas, notas = [], []

    # Onde o índice foi DECLARADO não há dúvida nem perda: o fator vira tensor
    # de verdade antes de o parser ver. A recusa existe para o silêncio, e
    # declarar acaba com o silêncio.
    if declarados:
        from .tensores import localizar
        cobertos = {i for ini, fim, _, _ in localizar(texto, set(declarados))
                    for i in range(ini, fim)}
        if cobertos:
            texto = "".join(" " if i in cobertos else c
                            for i, c in enumerate(texto))

    for m in _RE_PERDE.finditer(texto):
        base = m.group(1)
        if _limpo_macro(base) in _COMANDOS_ESTRUTURA:
            continue
        recusas.append(f"'{base}' tem sobrescrito e subscrito nessa ordem, e o "
                       f"parser descarta o de baixo")

    em_cima = _gregos_em(_RE_SUPER, texto)
    embaixo = _gregos_em(_RE_SUB, texto)
    for nome in sorted(em_cima & embaixo):
        recusas.append(f"o índice \\{nome} aparece em cima e embaixo "
                       f"(soma de Einstein)")

    soltos = sorted(em_cima - embaixo)
    if soltos and not recusas:
        notas.append(
            "há letra grega no expoente (" + ", ".join("\\" + n for n in soltos)
            + "): se for índice contravariante, a leitura está errada — o "
              "parser trata como POTÊNCIA, e notação tensorial ainda não é lida")
    if embaixo and not recusas:
        notas.append(
            "há índice grego em subscrito: ele vira parte do NOME do símbolo, "
            "então T_{\\mu\\nu} e T_{\\nu\\mu} são o mesmo símbolo para o SymPy")
    return recusas, notas


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
        lista = ", ".join("\\" + _com_palpite(n) for n in self.nomes)
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
        self._function_args = {}        # u(x,t) -> ('x', 't')
        self._indices = set()           # nomes declarados como índice
        self._tensores = {}             # nome -> (formas, vetores)
        self._espaco = None             # o tipo de índice, criado quando precisa
        self._variables = set()
        self._primes_are_derivatives = None      # None = sem convenção
        self._dots_are_derivatives = None
        self._e_is_euler = None
        self._annotations = {}

    # ------------------------------------------------------- declarações

    def function(self, *names):
        """Declara funções, e opcionalmente de que variáveis elas são.

            doc.function("f")            # f é função
            doc.function("u(x,t)")       # u é função de x e t

        A segunda forma é mais forte do que qualquer convenção, e por um
        motivo que vale dizer: declarar que u é função DISSOLVE ambiguidades em
        vez de escolher entre elas. Se u é função de x e t, então
        \\frac{\\partial u}{\\partial t} não pode ser "fração literal dos
        símbolos ∂, u e ∂t" — não há símbolo u para multiplicar. O sítio deixa
        de ser pergunta porque deixou de ter duas leituras, não porque alguém
        escolheu uma.
        """
        for n in names:
            nome, args = _declaracao(n)
            self._functions.add(nome)
            if args is not None:
                self._function_args[nome] = args
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
            raise FaltaVariavel(
                "para ler a linha como derivada é preciso uma variável "
                "independente: preencha 'Variável independente' nas convenções "
                "do documento (ou independent_variable= na biblioteca)",
                "independente", "Variável independente")
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

    def index(self, *nomes, dimensao=None):
        r"""Declara nomes como ÍNDICES: \mu, \nu, ...

        Declarar o índice é o que torna A^\mu não-ambíguo: não há potência
        possível com um índice no expoente. É a mesma mecânica de u = u(t,x),
        que dissolve a dúvida do ∂ em vez de escolher entre as leituras.
        """
        from .tensores import DIMENSAO_PADRAO, Espaco

        if self._espaco is None:
            self._espaco = Espaco(dimensao or DIMENSAO_PADRAO)
        elif dimensao and dimensao != self._espaco.dimensao:
            raise ValueError(
                f"o documento já tem índices de dimensão "
                f"{self._espaco.dimensao}; não dá para misturar com {dimensao}")

        for n in nomes:
            limpo = _limpo_indice(n)
            self._indices.add(limpo)
            # Guarda como foi ESCRITO: é isso que volta para a tela no lugar do
            # índice mudo que o SymPy inventa.
            self._espaco.escrita[limpo] = n.strip()
        return self

    def tensor(self, nome, formas, vetores):
        """Declara o TIPO do Schutz: (M, N) recebe M formas e N vetores.

        Em índices, M em cima e N embaixo. Diz o posto antes da primeira
        aparição — e a valência canônica, a partir da qual as outras se obtêm
        levantando ou baixando.
        """
        from .tensores import DIMENSAO_PADRAO, Espaco

        if self._espaco is None:
            self._espaco = Espaco(DIMENSAO_PADRAO)
        self._tensores[_limpo_indice(nome)] = (formas, vetores)
        self._espaco.declarar(_limpo_indice(nome), formas, vetores)
        return self

    def metric(self, nome):
        r"""Diz qual nome é A métrica — o que licencia baixar e levantar índice.

        `A_\mu \equiv g_{\mu\nu}A^\nu` é convenção da métrica, e não de um
        (0,2) qualquer. Nenhuma inspeção da expressão distingue os dois casos;
        só a declaração distingue.
        """
        from .tensores import DIMENSAO_PADRAO, Espaco

        if self._espaco is None:
            self._espaco = Espaco(DIMENSAO_PADRAO)
        limpo = _limpo_indice(nome)
        self._tensores[limpo] = (0, 2)
        self._espaco.definir_metrica(limpo)
        return self

    @property
    def espaco(self):
        return self._espaco

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
        # Sítio de leitura única não se pergunta e não se anota: ele é.
        if amb.certa:
            return Resolution(amb, amb.readings[0].key, Resolution.EXPLICIT,
                              motivo="∂ é derivada parcial")

        if amb.key in self._annotations:
            return Resolution(amb, self._annotations[amb.key], Resolution.EXPLICIT)

        # Declarar que u é função de x e t não escolhe entre as leituras: tira
        # uma delas do mundo. \frac{\partial u}{\partial t} não pode ser
        # "fração literal dos símbolos ∂, u e ∂t" se não existe símbolo u para
        # multiplicar. Vale onde a variável está ESCRITA na notação — ∂ e
        # Leibniz —; a linha continua precisando da convenção, porque f' com
        # duas variáveis não diz em relação a qual.
        declaradas = self._function_args.get(amb.base)
        if declaradas and amb.kind in ("leibniz", "partial"):
            return Resolution(amb, "derivative", Resolution.EXPLICIT,
                              motivo=_porque(amb.base, declaradas))

        # A linha e o ponto não trazem a variável escrita, então a declaração
        # só os resolve quando não há dúvida de QUAL: uma variável só. Com duas,
        # f' continua não dizendo em relação a qual, e o programa continua
        # perguntando — declarar não inventa o que a notação não diz.
        if declaradas and len(declaradas) == 1 and amb.kind in ("prime", "newton"):
            return Resolution(amb, "derivative", Resolution.EXPLICIT,
                              motivo=_porque(amb.base, declaradas))

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

        recusas, _ = indices_tensoriais(self.source, self.document._indices)
        if recusas:
            raise NotacaoTensorial(recusas)

        texto, reposicoes, derivadas, _, tensores = self._normalize()
        from sympy.parsing.latex import parse_latex
        expr = parse_latex(texto)
        if reposicoes:
            expr = expr.subs(reposicoes, simultaneous=True)

        # Coerência: se um símbolo aparece derivado, ele É função da variável
        # independente, e as suas ocorrências SEM linha também. Sem isto a
        # mesma letra viraria dois objetos distintos na mesma equação — erro
        # silencioso do tipo que este programa existe para impedir.
        # Funções declaradas são promovidas mesmo sem aparecer derivadas.
        promovidas = dict(derivadas)
        for nome, vs in self.document._function_args.items():
            promovidas.setdefault(nome, tuple(sp.Symbol(v) for v in vs))
        if promovidas:
            promocao = {sp.Symbol(nome): sp.Function(nome)(*args)
                        for nome, args in promovidas.items()}
            expr = expr.subs(promocao, simultaneous=True)

        expr = _canonizar(expr)

        # Reconstruir ANTES de conferir: o marcador de um fator tensorial ainda
        # é símbolo neste ponto, e a barreira de marcador vazado — que existe
        # para pegar defeito nosso — acusaria o funcionamento normal.
        #
        # Reconstruir, e não substituir: trocar um símbolo por um tensor dentro
        # de um Mul devolve um Mul comum, e a contração não acontece.
        from .tensores import IndicesIncompativeis, reconstruir
        try:
            expr = reconstruir(expr, tensores)
        except IndicesIncompativeis:
            raise
        except ValueError as e:
            if "same indices" in str(e):
                raise IndicesIncompativeis() from None
            raise

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
        derivadas = {}
        tensores = {}
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

        # Primeiro passo: quem é função de quê, olhando a expressão INTEIRA.
        #
        # Sem isto, cada sítio promovia o símbolo à sua própria função e o
        # mesmo u saía como u(t) de um lado e u(x) do outro — duas funções
        # diferentes com o mesmo nome na mesma equação, em silêncio. É a
        # mesma falha que a linha teve um dia, agora com várias variáveis.
        argumentos = self._argumentos()

        # Sítios e fatores tensoriais no MESMO passo, de trás para frente.
        # Dois passos separados invalidariam as posições um do outro: quem
        # reescreve na frente desloca tudo o que vem depois.
        fatores = self._fatores_tensoriais()
        itens = ([(a.span[0], "sitio", a) for a in self.ambiguities]
                 + [(ini, "tensor", (ini, fim, base, pos))
                    for ini, fim, base, pos in fatores])

        for _, especie, item in sorted(itens, key=lambda i: -i[0]):
            if especie == "tensor":
                ini, fim, base, posicoes = item
                nome, simbolo = marcador()
                from .tensores import construir
                tensores[simbolo] = construir(doc.espaco, base, posicoes)
                texto = texto[:ini] + nome + texto[fim:]
                continue
            a = item
            # Sítio dentro de outro sítio não se substitui aqui: o texto dele já
            # foi engolido, e quem o resolve é a leitura recursiva do fragmento.
            if contido(a, self.ambiguities):
                continue
            resolucao = doc.resolution(a)
            leitura = resolucao.reading
            ini, fim = a.span

            if a.kind == "prime":
                ordem = a.detail["order"]
                declarada = self._variavel_declarada(a.base)
                if declarada is not None:
                    x = declarada
                if leitura == "derivative":
                    _exige(x, "a linha", "independente", "independent_variable",
                           "Variável independente")
                nome, simbolo = marcador()
                alvo = self._linha(a, leitura, ordem, x, derivadas)
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "newton":
                nome, simbolo = marcador()
                ordem = a.detail["order"]
                tempo = self._variavel_declarada(a.base) or self.document.time
                if leitura == "derivative":
                    _exige(tempo, "o ponto", "temporal",
                           "time_variable", "Variável temporal")
                    _nao_derive_a_propria_variavel(a.base, tempo,
                                                   "temporal", r"\dot{{{0}}}")
                    funcao, args = self._funcao(a.base, tempo, argumentos)
                    derivadas[a.base] = args
                    alvo = sp.Derivative(funcao, (tempo, ordem))
                else:
                    alvo = sp.Symbol(a.base)
                reposicoes[simbolo] = alvo
                origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "partial":
                nome, simbolo = marcador()
                v = sp.Symbol(a.detail["wrt"])
                if leitura == "derivative":
                    funcao, args = self._funcao(a.base, v, argumentos)
                    derivadas[a.base] = args
                    alvo = sp.Derivative(funcao, v)
                else:
                    alvo = sp.Symbol(a.base) * sp.Symbol("d_" + a.detail["wrt"])
                reposicoes[simbolo] = alvo
                if not a.certa:
                    origens[alvo] = resolucao
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "leibniz":
                nome, simbolo = marcador()
                if leitura == "derivative":
                    v = sp.Symbol(a.detail["wrt"])
                    funcao, args = self._funcao(a.base, v, argumentos)
                    derivadas[a.base] = args
                    alvo = sp.Derivative(funcao, (v, a.detail["order"]))
                else:
                    alvo = (sp.Symbol("d")**a.detail["order"] * sp.Symbol(a.base)
                            / sp.Symbol("d" + a.detail["wrt"])**a.detail["order"])
                reposicoes[simbolo] = alvo
                if not a.certa:
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

        return _inofensivas(texto), reposicoes, derivadas, origens, tensores

    def _fatores_tensoriais(self):
        """Os fatores tensoriais, e a recusa onde eles esbarram numa derivada.

        ∂_μ A^ν é derivada COM índice, e isso não é multiplicação de um fator
        por outro — é um objeto próprio, que o SymPy trata em outro lugar. A
        ponte ainda não vai até lá, e dizer isso é melhor do que montar um
        produto que parece certo.
        """
        from .tensores import localizar

        doc = self.document
        if not doc._indices:
            return []
        fatores = localizar(self.source, doc._indices)
        ocupados = {i for a in self.ambiguities for i in range(*a.span)}
        for ini, fim, base, _ in fatores:
            if base in ("partial", "nabla") or any(
                    i in ocupados for i in range(ini, fim)):
                raise NotacaoTensorial([
                    "derivada com índice (∂_μ, ∇_μ) ainda não atravessa a "
                    "ponte: ela não é um fator multiplicando outro, é um "
                    "objeto próprio, e montar um produto aqui pareceria certo"])
        return fatores

    def _argumentos(self):
        """De que variáveis cada função incógnita depende, na entrada inteira.

        A ordem é a da primeira aparição no texto: u(t, x) para
        ∂u/∂t = k ∂u/∂x. Qualquer ordem serve à matemática — Derivative(u, x) é
        a mesma coisa —, mas uma ordem FIXA importa, senão a mesma equação lida
        duas vezes daria objetos diferentes.
        """
        doc = self.document
        # O que foi DECLARADO vale mesmo onde não há derivada: um u solto numa
        # equação continua sendo a mesma função, e não um símbolo homônimo.
        args = {nome: [sp.Symbol(v) for v in vs]
                for nome, vs in doc._function_args.items()}
        for a in sorted(self.ambiguities, key=lambda a: a.span[0]):
            leitura = doc.resolve(a)
            if leitura != "derivative" or a.detail.get("group"):
                continue
            if a.kind in ("prime", "leibniz") and a.kind == "prime":
                var = doc.independent
            elif a.kind == "leibniz":
                var = sp.Symbol(a.detail["wrt"])
            elif a.kind == "newton":
                var = doc.time
            elif a.kind == "partial":
                var = sp.Symbol(a.detail["wrt"])
            else:
                continue
            if var is None:
                continue
            lista = args.setdefault(a.base, [])
            if var not in lista:
                lista.append(var)
        return {nome: tuple(vs) for nome, vs in args.items()}

    def _funcao(self, nome, padrao, argumentos):
        """A função incógnita `nome`, com TODOS os argumentos que ela tem."""
        args = argumentos.get(nome) or (padrao,)
        return sp.Function(nome)(*args), args

    def _variavel_declarada(self, base):
        """A variável de uma função declarada de UMA variável, se houver."""
        args = self.document._function_args.get(base)
        return sp.Symbol(args[0]) if args and len(args) == 1 else None

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

        if not grupo:
            _nao_derive_a_propria_variavel(a.base, x, "independente")

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

        funcao, args = self._funcao(a.base, x, self._argumentos())
        if arg is None:
            derivadas[a.base] = args
            return sp.Derivative(funcao, (x, ordem))

        onde = self._fragmento(arg)
        if onde == x:
            derivadas[a.base] = args
            return sp.Derivative(funcao, (x, ordem))
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
        _, _, _, origens, _ = self._normalize()
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
