"""Sucuri — matemática diferencial anotada sobre SymPy.

Ambiguidade não se adivinha: anota-se. Ver README.md.
"""

__version__ = "0.1.0"

from .ambiguity import Ambiguity, Reading, find
from .document import (Document, Expression, NotacaoNaoReconhecida,
                       Resolution, Unresolved)
from .tree import Node


def parse(latex, *, independent_variable=None, primes=None,
          functions=(), variables=()):
    """Lê uma equação avulsa, com as convenções passadas na chamada.

    Atalho para o caso de uma expressão só. Trabalho continuado deve usar um
    `Document`, que guarda as convenções e as anotações entre expressões — a
    anotação só vale a pena se persistir.

    Parâmetros
    ----------
    primes : 'derivative', 'symbol' ou None
        None deixa as linhas PENDENTES, e a expressão recusa-se a converter.
        É o padrão de propósito: adivinhar é o que este programa não faz.
    """
    doc = Document(independent_variable=independent_variable)
    doc.function(*functions)
    doc.variable(*variables)
    if primes == "derivative":
        doc.primes_are_derivatives(True)
    elif primes == "symbol":
        doc.primes_are_derivatives(False)
    elif primes is not None:
        raise ValueError("primes deve ser 'derivative', 'symbol' ou None")
    return doc.read(latex)


__all__ = ["parse", "Document", "Expression", "Resolution", "Unresolved",
           "NotacaoNaoReconhecida", "Ambiguity", "Reading", "Node", "find"]
