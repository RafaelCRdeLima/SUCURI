"""Módulos de domínio.

O Sucuri lê e desambigua; ele não sabe teoria de Galois, nem geometria
diferencial, nem nada além de notação. O que dá utilidade a uma expressão é o
que se faz com ela, e isso vem de módulos.

Um módulo oferece OPERAÇÕES sobre expressões e devolve RESULTADOS que não são
expressões — tabelas, vereditos, certificados. É essa a diferença entre
hospedar calculadoras e hospedar áreas da matemática.

## O contrato

Toda conclusão de módulo carrega proveniência, e o hospedeiro **recusa-se a
apresentar como conclusão** o que vier de critério sem autoridade. O Sucuri não
precisa entender a matemática do módulo para aplicar essa regra — basta o
módulo declarar de onde vem o que afirma.

É a mesma regra que o Sucuri já aplica à leitura: nada se apresenta com mais
confiança do que a sua origem sustenta.
"""

from __future__ import annotations


class Provenance:
    """De onde vem a autoridade de um resultado."""

    ESTABLISHED = "estabelecida"
    """Critério com fonte primária ou derivação verificada."""

    UNSOURCED = "sem fonte"
    """Critério sem origem declarada. NÃO se apresenta como conclusão."""

    INAPPLICABLE = "não aplicável"
    """O resultado não é uma conclusão — é dado intermediário."""


class Result:
    """Um objeto de domínio devolvido por um módulo.

    Não é expressão. É tabela, veredito, certificado — coisa que tem estrutura
    própria e precisa de renderização própria.
    """

    def __init__(self, label, payload, *, latex=None, rows=None,
                 provenance=Provenance.INAPPLICABLE, blocked_by=()):
        self.label = label
        self.payload = payload
        self._latex = latex
        self.rows = list(rows) if rows else []
        self.provenance = provenance
        self.blocked_by = list(blocked_by)

    @property
    def is_conclusion(self):
        return self.provenance is not Provenance.INAPPLICABLE

    @property
    def presentable(self):
        """Se o hospedeiro pode apresentar isto como conclusão."""
        return (not self.is_conclusion
                or self.provenance == Provenance.ESTABLISHED)

    def to_dict(self):
        return {
            "rotulo": self.label,
            "latex": self._latex,
            "linhas": self.rows,
            "proveniencia": self.provenance,
            "apresentavel": self.presentable,
            "bloqueado_por": self.blocked_by,
        }

    def __repr__(self):
        cab = f"{self.label}  [{self.provenance}]"
        if not self.presentable:
            cab += "  — NÃO APRESENTÁVEL COMO CONCLUSÃO"
        linhas = [cab]
        if self._latex:
            linhas.append(f"  {self._latex}")
        for r in self.rows:
            linhas.append("  " + " | ".join(str(c) for c in r))
        for b in self.blocked_by:
            linhas.append(f"  bloqueio: {b}")
        return "\n".join(linhas)


class Operation:
    """Uma coisa que um módulo sabe fazer."""

    def __init__(self, name, description, run, accepts="expression"):
        self.name = name
        self.description = description
        self.run = run
        self.accepts = accepts

    def __repr__(self):
        return f"{self.name}: {self.description}"


class Module:
    """Um domínio carregado no Sucuri."""

    def __init__(self, name, description, operations=()):
        self.name = name
        self.description = description
        self.operations = {op.name: op for op in operations}

    def __repr__(self):
        linhas = [f"módulo {self.name} — {self.description}"]
        linhas += [f"  {op}" for op in self.operations.values()]
        return "\n".join(linhas)


REGISTRY = {}


def register(module):
    REGISTRY[module.name] = module
    return module


def available():
    return dict(REGISTRY)


CONHECIDOS = ("korvin", "resolver")
"""Os que acompanham o Sucuri. Outros podem registrar-se sozinhos."""


def load(name):
    """Carrega um módulo pelo nome, se as dependências estiverem presentes."""
    if name in REGISTRY:
        return REGISTRY[name]
    if name in CONHECIDOS:
        import importlib
        return importlib.import_module(f".{name}", __package__).MODULE
    raise KeyError(f"módulo desconhecido: {name}")
