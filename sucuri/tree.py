"""A árvore reconhecida.

O painel central do mockup. Mostra o que o programa entendeu, nó a nó, e —
esta é a parte que importa — carrega de volta a proveniência: cada nó que
nasceu de um sítio ambíguo sabe COMO aquele sítio foi resolvido, para a
interface pintá-lo de âmbar quando a leitura veio de convenção e não de decisão.

Sem isso a árvore seria decoração. Com isso ela é o lugar onde o usuário vê,
de relance, quais pedaços da sua equação o programa supôs.
"""

from __future__ import annotations

import sympy as sp


_ROTULOS = {
    sp.Add: "soma",
    sp.Mul: "produto",
    sp.Pow: "potência",
    sp.Derivative: "derivada",
    sp.Integral: "integral",
    sp.Equality: "igualdade",
    sp.Symbol: "símbolo",
}


def _rotulo(expr):
    """Nome legível do nó, em português."""
    if isinstance(expr, sp.Symbol):
        return f"símbolo {expr.name}"
    if isinstance(expr, (sp.Integer, sp.Rational, sp.Float)):
        return f"número {expr}"
    if isinstance(expr, sp.Derivative):
        alvo = expr.expr
        nome = alvo.func.__name__ if hasattr(alvo, "func") else str(alvo)
        ordem = sum(n for _, n in expr.variable_count)
        var = ", ".join(str(v) for v, _ in expr.variable_count)
        return f"derivada de ordem {ordem} de {nome} em {var}"
    if isinstance(expr, sp.core.function.AppliedUndef):
        args = ", ".join(str(a) for a in expr.args)
        return f"função {expr.func.__name__} aplicada a ({args})"
    for tipo, nome in _ROTULOS.items():
        if isinstance(expr, tipo):
            return nome
    return type(expr).__name__.lower()


class Node:
    """Um nó da árvore reconhecida."""

    def __init__(self, expr, resolution=None):
        self.sympy = expr
        self.label = _rotulo(expr)
        self.resolution = resolution
        self.children = []

    @property
    def latex(self):
        return sp.latex(self.sympy)

    @property
    def state(self):
        """'explícita', 'inferida' ou None — o que decide a cor na interface."""
        return self.resolution.how if self.resolution else None

    @property
    def needs_review(self):
        return bool(self.resolution and self.resolution.needs_review)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def to_dict(self):
        """Forma serializável, para a interface web consumir."""
        return {
            "rotulo": self.label,
            "latex": self.latex,
            "estado": self.state,
            "conferir": self.needs_review,
            "filhos": [c.to_dict() for c in self.children],
        }

    def __repr__(self):
        return self._render(0)

    def _render(self, nivel):
        marca = ""
        if self.state:
            marca = f"  [{self.state}]" + ("  <- conferir" if self.needs_review else "")
        linhas = ["  " * nivel + self.label + marca]
        for c in self.children:
            linhas.append(c._render(nivel + 1))
        return "\n".join(linhas)


def build(expr, origins=None):
    """Constrói a árvore, ligando cada nó à sua origem ambígua quando houver.

    `origins` mapeia a subexpressão que substituiu um marcador para a Resolution
    daquele sítio. O casamento é por igualdade estrutural, que basta porque as
    substituições foram feitas com objetos distintos.
    """
    origins = origins or {}

    def recursao(e):
        no = Node(e, origins.get(e))
        # Nós que vieram de um sítio ambíguo são folhas na leitura do usuário:
        # ele quer ver "derivada segunda de phi", não a árvore interna dela.
        if no.resolution is None:
            for arg in e.args:
                no.children.append(recursao(arg))
        return no

    return recursao(expr)
