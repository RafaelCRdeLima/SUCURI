r"""A equação do desvio geodésico, deduzida sem um único índice.

    ∇_U ∇_U X = R(U,X)U

U é tangente a uma família de geodésicas, X liga geodésicas vizinhas. A
dedução usa só campos vetoriais, a derivada covariante, o colchete de Lie e o
operador de curvatura — e é por isso que ela serve de teste: o parser de LaTeX
do SymPy erra cada uma dessas notações sem avisar.

    python exemplos/desvio_geodesico.py
"""

import sympy as sp
from sympy.parsing.latex import parse_latex

from sucuri.caderno import Caderno

print("--- SymPy sozinho ---")
lido = parse_latex(r"\nabla_U \nabla_X U - \nabla_X \nabla_U U")
print(r"\nabla_U \nabla_X U - \nabla_X \nabla_U U  ->", lido,
      " =", sp.simplify(lido))
print("  ∇ virou um símbolo que multiplica e comuta; a curvatura sumiu")


def mostrar(caderno, fonte):
    d = caderno.executar(fonte).to_dict()
    nome = d.get("nome") or "    "
    if d.get("erro"):
        print(f"  {fonte}\n      recusa: {d['erro']}")
    elif d.get("linhas"):
        print(f"  {fonte}")
        for linha in d["linhas"]:
            print(f"      {linha[0]:<28} {linha[1]}")
    elif d.get("sympy"):
        print(f"  {nome}  {d['sympy']}")
    return d


print("\n--- Sucuri: as hipóteses sobre U e X dadas uma a uma ---")
c = Caderno()
for fonte in ("U = tensor(1,0)", "X = tensor(1,0)", "R = curvatura",
              r"[U,X] = 0",                                   # eq1
              r"\nabla_U U = 0",                              # eq2
              r"\nabla_U X - \nabla_X U = [U,X]",             # eq3
              r"R(U,X)U = \nabla_U \nabla_X U - \nabla_X \nabla_U U"
              r" - \nabla_{[U,X]} U",                         # eq4
              r"\nabla_U \nabla_U X = R(U,X)U"):              # eq5
    mostrar(c, fonte)
mostrar(c, "provar(eq5, eq1, eq2, eq3, eq4)")

print("\n  sem a definição de R, nada se prova sobre R:")
mostrar(c, "provar(eq5, eq1, eq2, eq3)")

print("\n--- Sucuri: a definição de R e a torção nula ditas uma vez ---")
c = Caderno()
for fonte in ("U = tensor(1,0)", "X = tensor(1,0)", "Y = tensor(1,0)",
              "R = curvatura",
              r"\forall A, B, W: R(A,B)W = \nabla_A \nabla_B W"
              r" - \nabla_B \nabla_A W - \nabla_{[A,B]} W",   # eq1
              r"\forall A, B: \nabla_A B - \nabla_B A = [A,B]",  # eq2
              r"[U,X] = 0",                                   # eq3
              r"\nabla_U U = 0",                              # eq4
              r"\nabla_U \nabla_U X = R(U,X)U"):              # eq5
    mostrar(c, fonte)
mostrar(c, "provar(eq5, eq1, eq2, eq3, eq4)")

print("\n  e o que sai da mesma definição:")
mostrar(c, r"\forall A, B, W: R(A,B)W = -R(B,A)W")            # eq6
mostrar(c, "provar(eq6, eq1)")
mostrar(c, r"\forall A, B, C: [A,[B,C]] + [B,[C,A]] + [C,[A,B]] = 0")  # eq7
mostrar(c, r"R(U,X)Y + R(X,Y)U + R(Y,U)X = 0")                # eq8
mostrar(c, "provar(eq8, eq1, eq2, eq7)")

print("\n--- A convenção de sinal é declarada, não suposta ---")
c = Caderno()
for fonte in ("U = tensor(1,0)", "X = tensor(1,0)", "R = curvatura",
              r"\forall A, B, W: R(A,B)W = \nabla_B \nabla_A W"
              r" - \nabla_A \nabla_B W + \nabla_{[A,B]} W",   # eq1, sinal oposto
              r"\forall A, B: \nabla_A B - \nabla_B A = [A,B]",
              r"[U,X] = 0", r"\nabla_U U = 0",
              r"\nabla_U \nabla_U X = R(U,X)U",               # eq5
              r"\nabla_U \nabla_U X = -R(U,X)U"):             # eq6
    mostrar(c, fonte)
print("  com a definição de sinal oposto, a forma do MTW não sai:")
mostrar(c, "provar(eq5, eq1, eq2, eq3, eq4)")
print("  e a com sinal trocado, sim:")
mostrar(c, "provar(eq6, eq1, eq2, eq3, eq4)")

print("\n--- E com índice, como no livro de física ---")
c = Caderno()
for fonte in (r"\mu, \alpha, \beta, \sigma, \rho, \nu = índices",
              "U = tensor(1,0)", "X = tensor(1,0)", "V = tensor(1,0)",
              r"\nabla = levi-civita",
              r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
              r" = R^\rho{}_{\sigma\mu\nu} V^\sigma",           # eq1
              "R = riemann(eq1)", "R = curvatura",
              r"\nabla_U \nabla_U X = R(U,X)U"):               # eq2
    mostrar(c, fonte)
d = c.executar("indices(eq2)").to_dict()
print(f"  indices(eq2)\n      {d['latex_exato']}")
for nota in d.get("notas") or []:
    print(f"      nota: {nota}")
