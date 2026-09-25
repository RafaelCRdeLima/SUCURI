"""O exemplo do desvio geodésico, executado.

Pelo mesmo motivo que o manual é executado: exemplo que ninguém roda apodrece
em silêncio. Este é o que mostra a conexão sem índice de ponta a ponta — a
leitura, as duas formas da prova, e a convenção de sinal fazendo diferença.
"""

import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).parents[1]


def test_o_exemplo_do_desvio_geodesico_roda_e_prova():
    saida = subprocess.run(
        [sys.executable, "-W", "ignore",
         str(RAIZ / "exemplos" / "desvio_geodesico.py")],
        capture_output=True, text=True, cwd=RAIZ, timeout=300,
        env={"PYTHONPATH": str(RAIZ)}, check=True).stdout
    # o SymPy sozinho perde a curvatura
    assert "->" in saida and " = 0\n" in saida
    # as cinco provas saem, e as duas recusas também
    assert saida.count("somando") == 5
    assert saida.count("recusa:") == 2
    assert "eq1[A→U, B→X, W→U]" in saida
    assert "Eq(nabla_U(nabla_U(X)), -R(U, X)(U))" in saida
