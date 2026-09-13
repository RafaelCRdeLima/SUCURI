"""Sucuri — matemática diferencial anotada sobre SymPy.

Ambiguidade não se adivinha: anota-se. Ver README.md.
"""

__version__ = "0.1.0"

from .ambiguity import Ambiguity, Reading, find
from .document import Document, Expression, Resolution, Unresolved

__all__ = ["Document", "Expression", "Resolution", "Unresolved", "Ambiguity", "Reading", "find"]
