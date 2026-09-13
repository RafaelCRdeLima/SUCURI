"""Localização e anotação dos sítios ambíguos da entrada.

O coração do Sucuri. LaTeX descreve como um símbolo é DESENHADO, não o que ele
SIGNIFICA, e por isso há construções que um parser não tem como resolver
sozinho. As três que aparecem sempre em física:

  y''            derivada segunda, ou símbolo chamado "y-duas-linhas"?
  f'(x)          derivada de f, avaliada em x — a linha engole o argumento
  (f+g)'         a linha recai sobre o grupo inteiro, não sobre a última letra
  f(x+1)         f aplicada ao argumento, ou f multiplicando o parêntese?
  d^2 y / dx^2   derivada de Leibniz, ou fração de símbolos d, y, dx?
  \\dot{x}        derivada temporal de Newton, ou decoração sobre x?
  \\partial_x f   derivada parcial, ou produto de f por um símbolo?
  e^{ax}         número de Euler, ou um símbolo chamado e?

O ponto de Newton é o caso mais grave medido: o SymPy lê \\dot{x} como o produto
do símbolo "dot" pelo símbolo x. Toda a mecânica hamiltoniana se escreve assim.

Um parser adivinha, e erra em silêncio. O Sucuri localiza, e recusa-se a
prosseguir sem anotação.
"""

from __future__ import annotations

import re


class Reading:
    """Uma leitura possível de um sítio ambíguo."""

    def __init__(self, key, description):
        self.key = key
        self.description = description

    def __repr__(self):
        return f"{self.key}: {self.description}"


class Ambiguity:
    """Um sítio da entrada cuja leitura não se decide pela tipografia.

    Atributos
    ---------
    kind : str
        'prime', 'juxtaposition' ou 'leibniz'.
    fragment : str
        O trecho de LaTeX, como escrito.
    span : (int, int)
        Onde ele está na entrada, para a interface destacar.
    base : str
        O símbolo envolvido.
    readings : list de Reading
        As leituras possíveis, sem ordem de preferência: sugerir uma delas
        como padrão seria adivinhar de novo.
    detail : dict
        Dados extras da detecção (ordem da derivada, variável, etc.).
    """

    def __init__(self, kind, fragment, span, base, readings, **detail):
        self.kind = kind
        self.fragment = fragment
        self.span = span
        self.base = base
        self.readings = list(readings)
        self.detail = detail

    @property
    def key(self):
        """Identidade estável do sítio, para casar com anotações."""
        return (self.kind, self.base, tuple(sorted(self.detail.items())))

    def __repr__(self):
        op = " | ".join(r.key for r in self.readings)
        return f"<{self.kind} {self.fragment!r} em {self.span}: {op}>"


# --------------------------------------------------------------- detectores

_SIMBOLO = r"(?:\\[a-zA-Z]+|[a-zA-Z])"

# A linha se escreve de vários jeitos, e a segunda derivada de mais ainda:
#     y''      y'' (x)      y^{\prime\prime}      y^\prime\prime      y\prime\prime
# O grupo em chaves precisa aceitar MAIS DE UMA linha dentro: escrito para uma
# só, ^{\prime\prime} casava metade e deixava um "}" solto, que fazia o parser
# do SymPy engolir o resto da equação sem dizer nada.
_LINHAS = (r"(?:'"
           r"|\^\s*\{\s*(?:\\prime\s*)+\}\s*"
           r"|\^\s*\\prime\s*"
           r"|\\prime\s*)")
_RE_PRIME = re.compile(rf"({_SIMBOLO})((?:{_LINHAS})+)")
_RE_LINHA_GRUPO = re.compile(rf"\)((?:{_LINHAS})+)")
# d e ∂ na mesma regra: a forma é a mesma, e o que muda é só o que a escolha
# do símbolo declara — que há outras variáveis além daquela.
_RE_LEIBNIZ = re.compile(
    r"\\frac\s*\{\s*(d|\\partial)(?:\^\{?(\d+)\}?)?\s*(" + _SIMBOLO + r")\s*\}"
    r"\s*\{\s*(?:d|\\partial)\s*(" + _SIMBOLO + r")(?:\^\{?(\d+)\}?)?\s*\}")
_RE_JUSTAPOSICAO = re.compile(rf"({_SIMBOLO})\s*(?:\\left)?\(")
_RE_NEWTON = re.compile(r"\\(d+)ot\s*(?:\{\s*(" + _SIMBOLO + r")\s*\}|(" + _SIMBOLO + r"))")
# Só a base de potência: é onde o 'e' quase sempre é Euler e onde ler errado
# muda a matemática calado (d/dx e^{ax} = a·e^{ax}·ln e, se e for símbolo). Um
# 'e' solto em outro lugar não é sítio — seria pergunta demais para achado de
# menos, e um 'e' em subscrito quebraria a substituição.
_RE_EULER = re.compile(r"e(?=\s*\^)")
_RE_PARCIAL = re.compile(
    r"\\partial\s*_\s*(?:\{\s*(" + _SIMBOLO + r")\s*\}|(" + _SIMBOLO + r"))"
    r"\s*(" + _SIMBOLO + r")")

# Nomes que nunca são símbolo do usuário: comandos de estrutura do LaTeX e as
# funções que o parser já conhece. Perguntar se \arctan( é "arctan multiplicando
# o parêntese" não é rigor, é ruído — e pergunta que não é pergunta gasta a
# credibilidade das que são.
_COMANDOS = {
    "frac", "dfrac", "tfrac", "sqrt", "left", "right", "sum", "int", "prod",
    "lim", "cdot", "times", "partial", "mathrm", "text", "begin", "end",
    "quad", "qquad", "prime", "infty", "over", "operatorname",
    "sin", "cos", "tan", "sec", "csc", "cot",
    "arcsin", "arccos", "arctan", "arcsec", "arccsc", "arccot",
    "sinh", "cosh", "tanh", "coth", "sech", "csch",
    "exp", "log", "ln", "lg", "min", "max", "det", "gcd", "deg",
}


def _limpo(simbolo):
    return simbolo[1:] if simbolo.startswith("\\") else simbolo


def _dentro_de_nome(latex, i):
    r"""O 'e' em `i` é letra de outro nome, e não um 'e' sozinho?

    Duas formas de sê-lo: letra de uma macro (\sec) ou índice de um símbolo
    (v_e^2). Note que em 'ae^{ax}' o 'e' NÃO está dentro de nome — justaposição
    em LaTeX é produto, e ali há um 'a' vezes um 'e'.
    """
    j = i
    while j > 0 and latex[j - 1].isalpha():
        j -= 1
    if j > 0 and latex[j - 1] == "\\":
        return True
    anterior = latex[:i].rstrip()
    return anterior.endswith("_")


def _fecha(latex, i):
    """Índice logo após o ')' que fecha o '(' em `i`, ou None."""
    fundo = 0
    while i < len(latex):
        if latex[i] == "(":
            fundo += 1
        elif latex[i] == ")":
            fundo -= 1
            if fundo == 0:
                return i + 1
        i += 1
    return None


def _abre(latex, j):
    """Índice do '(' que casa com o ')' em `j`, ou None."""
    fundo = 0
    while j >= 0:
        if latex[j] == ")":
            fundo += 1
        elif latex[j] == "(":
            fundo -= 1
            if fundo == 0:
                return j
        j -= 1
    return None


def _sem_right(texto):
    texto = texto.strip()
    return texto[:-6].strip() if texto.endswith("\\right") else texto


_RE_ARG = re.compile(r"\s*(?:\\left)?\(")


def _argumento(latex, pos):
    """O argumento que começa em `pos`, se houver: ('x', índice_final).

    É o que distingue f' de f'(x). O segundo diz em que ponto a derivada é
    avaliada, e ignorar isso foi o defeito que a tabela de derivadas revelou:
    o marcador interno colava no parêntese e vazava para a saída.
    """
    m = _RE_ARG.match(latex, pos)
    if not m:
        return None
    abre = latex.index("(", m.start())
    fim = _fecha(latex, abre)
    if fim is None:
        return None
    return _sem_right(latex[abre + 1:fim - 1]), fim


def find(latex):
    """Todos os sítios ambíguos da entrada, na ordem em que aparecem."""
    achados = []

    for m in _RE_LEIBNIZ.finditer(latex):
        simbolo, ordem_num, funcao, variavel, ordem_den = m.groups()
        ordem = int(ordem_num or ordem_den or 1)
        parcial = simbolo == "\\partial"
        letra = "∂" if parcial else "d"
        qualidade = "parcial " if parcial else ""
        achados.append(Ambiguity(
            "leibniz", m.group(0), m.span(), _limpo(funcao),
            [Reading("derivative",
                     f"derivada {qualidade}de ordem {ordem} de {_limpo(funcao)} "
                     f"em relação a {_limpo(variavel)}"),
             Reading("fraction",
                     f"fração literal dos símbolos {letra}, "
                     f"{_limpo(funcao)} e {letra}{_limpo(variavel)}")],
            order=ordem, wrt=_limpo(variavel), partial=parcial))

    for m in _RE_NEWTON.finditer(latex):
        ordem = len(m.group(1))
        base = _limpo(m.group(2) or m.group(3))
        if base in _COMANDOS:
            continue
        achados.append(Ambiguity(
            "newton", m.group(0), m.span(), base,
            [Reading("derivative",
                     f"derivada temporal de ordem {ordem} de {base}"),
             Reading("decoration",
                     f"apenas um acento sobre {base}; o símbolo é {base}")],
            order=ordem))

    for m in _RE_PARCIAL.finditer(latex):
        variavel, variavel2, alvo = m.groups()
        v, a = _limpo(variavel or variavel2), _limpo(alvo)
        achados.append(Ambiguity(
            "partial", m.group(0), m.span(), a,
            [Reading("derivative", f"derivada parcial de {a} em relação a {v}"),
             Reading("product", f"produto de {a} por um símbolo chamado d_{v}")],
            wrt=v))

    cobertos = {i for a in achados for i in range(*a.span)}

    # Linha sobre um grupo: (f+g)', \left(f/g\right)'. A linha não é da última
    # letra — é do parêntese inteiro. Sem isto o parser do SymPy engole a linha
    # E o resto da equação, em silêncio: parse_latex("(f+g)' = a") devolve f+g.
    for m in _RE_LINHA_GRUPO.finditer(latex):
        j = m.start()
        i = _abre(latex, j)
        if i is None:
            continue
        interno = _sem_right(latex[i + 1:j])
        ini = i - 5 if latex[max(0, i - 5):i] == "\\left" else i
        ordem = m.group(1).count("'") + m.group(1).count("\\prime")
        fim = m.end()
        detalhe = {"order": ordem, "group": True}
        arg = _argumento(latex, fim)
        if arg:
            detalhe["arg"], fim = arg
        onde = f" avaliada em {detalhe['arg']}" if "arg" in detalhe else ""
        achados.append(Ambiguity(
            "prime", latex[ini:fim], (ini, fim), interno,
            [Reading("derivative",
                     f"derivada de ordem {ordem} de ({interno}){onde}"),
             Reading("symbol",
                     f"as linhas são decoração; o grupo é ({interno})")],
            **detalhe))

    grupos = {i for a in achados if a.detail.get("group")
              for i in range(*a.span)}

    for m in _RE_PRIME.finditer(latex):
        if m.start() in cobertos or m.start() in grupos:
            continue
        base, linhas = m.groups()
        if _limpo(base) in _COMANDOS:
            continue
        ordem = linhas.count("'") + linhas.count("\\prime")
        detalhe = {"order": ordem}
        fim = m.end()
        arg = _argumento(latex, fim)
        if arg:
            detalhe["arg"], fim = arg
        onde = f", avaliada em {detalhe['arg']}" if "arg" in detalhe else ""
        aplicada = f"({detalhe['arg']})" if "arg" in detalhe else ""
        achados.append(Ambiguity(
            "prime", latex[m.start():fim], (m.start(), fim), _limpo(base),
            [Reading("derivative",
                     f"derivada de ordem {ordem} de {_limpo(base)}{onde}"),
             Reading("symbol",
                     f"símbolo chamado {_limpo(base)}{chr(39) * ordem}{aplicada}")],
            **detalhe))

    for m in _RE_JUSTAPOSICAO.finditer(latex):
        base = _limpo(m.group(1))
        if base in _COMANDOS or m.start() in cobertos:
            continue
        achados.append(Ambiguity(
            "juxtaposition", m.group(0), m.span(), base,
            [Reading("application", f"{base} aplicada ao argumento"),
             Reading("product", f"{base} multiplicando o parêntese")]))

    for m in _RE_EULER.finditer(latex):
        if m.start() in cobertos or _dentro_de_nome(latex, m.start()):
            continue
        achados.append(Ambiguity(
            "euler", m.group(0), m.span(), "e",
            [Reading("euler", "o número de Euler, 2,71828…"),
             Reading("symbol", "um símbolo chamado e")]))

    achados.sort(key=lambda a: a.span[0])
    return achados


def contido(sitio, outros):
    """O sítio está inteiramente dentro de outro?

    Acontece com f'(g(x)): o 'g(' é sítio de justaposição, mas mora dentro do
    argumento que a linha engoliu. O texto dele não se substitui aqui — quem o
    resolve é a leitura recursiva do fragmento.
    """
    ini, fim = sitio.span
    for o in outros:
        if o is sitio:
            continue
        if o.span[0] <= ini and fim <= o.span[1] and o.span != sitio.span:
            return True
    return False
