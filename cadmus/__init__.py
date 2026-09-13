"""CADMUS — Converting Annotated Differential Mathematics Using SymPy.

Ambiguidade não se adivinha: anota-se. Ver README.md.
"""

__version__ = "0.1.0"

from .ambiguity import Ambiguity, Reading, find
from .document import Document, Expression, Unresolved

__all__ = ["Document", "Expression", "Unresolved", "Ambiguity", "Reading", "find"]
