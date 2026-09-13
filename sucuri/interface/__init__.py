"""A interface do Sucuri: servidor local e página.

    python -m sucuri.interface

O motor não sabe que existe interface, e a interface não sabe matemática.
Entre os dois passa JSON: entrada em LaTeX de um lado, leitura anotada do
outro — e, quando a leitura está completa, o objeto SymPy.
"""

from .aplicacao import Aplicacao
from .sessao import Sessao
from .servidor import criar, servir

__all__ = ["Aplicacao", "Sessao", "criar", "servir"]
