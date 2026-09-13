"""Localização e anotação dos sítios ambíguos da entrada.

O coração do CADMUS. LaTeX descreve como um símbolo é DESENHADO, não o que ele
SIGNIFICA, e por isso há construções que um parser não tem como resolver
sozinho. As três que aparecem sempre em física:

  y''            derivada segunda, ou símbolo chamado "y-duas-linhas"?
  f(x+1)         f aplicada ao argumento, ou f multiplicando o parêntese?
  d^2 y / dx^2   derivada de Leibniz, ou fração de símbolos d, y, dx?

Um parser adivinha, e erra em silêncio. O CADMUS localiza, e recusa-se a
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

_RE_PRIME = re.compile(rf"({_SIMBOLO})((?:'|\\prime\s*)+)")
_RE_LEIBNIZ = re.compile(
    r"\\frac\s*\{\s*d(?:\^\{?(\d+)\}?)?\s*(" + _SIMBOLO + r")\s*\}"
    r"\s*\{\s*d\s*(" + _SIMBOLO + r")(?:\^\{?(\d+)\}?)?\s*\}")
_RE_JUSTAPOSICAO = re.compile(rf"({_SIMBOLO})\s*(?:\\left)?\(")

# Nomes que nunca são símbolo do usuário: comandos de estrutura do LaTeX.
_COMANDOS = {
    "frac", "sqrt", "left", "right", "sum", "int", "prod", "lim", "cdot",
    "times", "partial", "mathrm", "text", "begin", "end", "quad", "qquad",
    "sin", "cos", "tan", "exp", "log", "ln", "prime", "infty",
}


def _limpo(simbolo):
    return simbolo[1:] if simbolo.startswith("\\") else simbolo


def find(latex):
    """Todos os sítios ambíguos da entrada, na ordem em que aparecem."""
    achados = []

    for m in _RE_LEIBNIZ.finditer(latex):
        ordem_num, funcao, variavel, ordem_den = m.groups()
        ordem = int(ordem_num or ordem_den or 1)
        achados.append(Ambiguity(
            "leibniz", m.group(0), m.span(), _limpo(funcao),
            [Reading("derivative",
                     f"derivada de ordem {ordem} de {_limpo(funcao)} "
                     f"em relação a {_limpo(variavel)}"),
             Reading("fraction",
                     "fração literal dos símbolos d, "
                     f"{_limpo(funcao)} e d{_limpo(variavel)}")],
            order=ordem, wrt=_limpo(variavel)))

    cobertos = {i for a in achados for i in range(*a.span)}

    for m in _RE_PRIME.finditer(latex):
        if m.start() in cobertos:
            continue
        base, linhas = m.groups()
        if _limpo(base) in _COMANDOS:
            continue
        ordem = linhas.count("'") + linhas.count("\\prime")
        achados.append(Ambiguity(
            "prime", m.group(0), m.span(), _limpo(base),
            [Reading("derivative",
                     f"derivada de ordem {ordem} de {_limpo(base)}"),
             Reading("symbol",
                     f"símbolo chamado {_limpo(base)}{chr(39) * ordem}")],
            order=ordem))

    for m in _RE_JUSTAPOSICAO.finditer(latex):
        base = _limpo(m.group(1))
        if base in _COMANDOS or m.start() in cobertos:
            continue
        achados.append(Ambiguity(
            "juxtaposition", m.group(0), m.span(), base,
            [Reading("application", f"{base} aplicada ao argumento"),
             Reading("product", f"{base} multiplicando o parêntese")]))

    achados.sort(key=lambda a: a.span[0])
    return achados
