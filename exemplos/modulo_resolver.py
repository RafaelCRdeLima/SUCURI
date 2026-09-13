"""As quatro respostas que o `dsolve` dá — e só uma delas é solução.

    python exemplos/modulo_resolver.py
"""

import sucuri
from sucuri import modules


def documento():
    doc = sucuri.Document(independent_variable="x")
    doc.function("y")
    doc.primes_are_derivatives(True)
    doc.e_is_euler(True)
    return doc


EQUACOES = [
    ("forma fechada, conferida", r"y'' + y = 0"),
    ("forma fechada com nome", r"y'' = x y"),
    ("série truncada — NÃO é solução", r"y'' + x y' + y = 0"),
    ("o solver não volta", r"y'' = 6 y^2"),
    ("o solver quebra", r"y' = y^2 + x"),
    ("achou, mas não confere", r"y' = \frac{1}{x + y^2}"),
]


def main():
    resolver = modules.load("resolver")
    for rotulo, latex in EQUACOES:
        print("=" * 72)
        print(f"{rotulo}\n  {latex}\n")
        print(resolver.operations["resolver"].run(documento().read(latex)))
        print()


if __name__ == "__main__":
    main()
