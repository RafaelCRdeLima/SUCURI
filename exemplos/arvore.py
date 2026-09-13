"""A árvore reconhecida, com a proveniência de cada nó.

O painel central da interface. Dois dos três nós de derivada vieram de uma
convenção do documento — e aparecem marcados para conferência. O terceiro foi
anotado sítio a sítio, e não aparece.
"""

import json

import sucuri

RICCATI = r"\varphi'' + 3\varphi\varphi' + \varphi^3 = 4r\varphi + 2r'"

doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
doc.annotate("prime", "r", "derivative", order=1)   # este foi decidido olhando

e = doc.read(RICCATI)
print("entrada:", RICCATI, "\n")
print(e.tree())

print(f"\nnós a conferir: {len([n for n in e.tree().walk() if n.needs_review])}")
print("\n--- para a interface ---")
print(json.dumps(e.tree().to_dict(), ensure_ascii=False)[:180] + " ...")
