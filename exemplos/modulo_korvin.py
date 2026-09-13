"""Do LaTeX ao veredito, atravessando dois programas.

O usuário escreve a equação de Airy como a escreveria num caderno. O Sucuri
desambigua a linha. O KORVIN analisa. E o Sucuri recusa-se a apresentar o
veredito como conclusão — porque o critério do caso 2 não tem proveniência
declarada, e o módulo disse isso ao atravessar a fronteira.

O Sucuri não sabe o que é grupo de Galois. Não precisa.
"""

import sucuri
from sucuri.modules import load

doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
e = doc.read(r"y'' = x y")

print("escrito:", e.source)
print("lido   :", e.to_sympy())
print(f"inferido por convenção: {len(e.inferred)} sítio(s)\n")

korvin = load("korvin")
for nome in korvin.operations:
    print("=" * 70)
    print(korvin.operations[nome].run(e))
