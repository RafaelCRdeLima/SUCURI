"""A equação que define o CADMUS.

A Riccati do caso 2 de Kovacic. Lida pelo parser do SymPy, ela perde as três
linhas em silêncio e vira outra equação — leitura errada que já custou um
teorema falso a um projeto real.
"""

import sympy as sp
from sympy.parsing.latex import parse_latex

from cadmus import Document, Unresolved

RICCATI = r"\varphi'' + 3\varphi\varphi' + \varphi^3 = 4r\varphi + 2r'"

print("escrito:", RICCATI, "\n")

print("--- SymPy sozinho ---")
print(sp.latex(parse_latex(RICCATI)))
print("derivadas reconhecidas:", len(parse_latex(RICCATI).atoms(sp.Derivative)))

print("\n--- CADMUS, sem anotação ---")
e = Document().read(RICCATI)
try:
    e.to_sympy()
except Unresolved:
    for q in e.questions():
        print("  ?", q)

print("\n--- CADMUS, com a convenção declarada ---")
doc = Document(independent_variable='x').primes_are_derivatives()
expr = doc.read(RICCATI).to_sympy()
print(sp.latex(expr))
print("derivadas reconhecidas:", len(expr.atoms(sp.Derivative)))
