"""Prazo para contas que podem não terminar.

Integrar e resolver são operações abertas: `Integral(sin(x)/x, (x, 0, oo))`
fecha, `y'' = 6y²` não volta nunca. O SymPy não oferece ponto de interrupção,
então quem chama tem de poder desistir.

Processo, e não thread, porque thread pendurada continua queimando CPU até o
fim do programa — processo se mata. No navegador não há processos: lá quem
hospeda mata o Web Worker inteiro, que é o mesmo desenho com outro mecanismo.
"""

from __future__ import annotations

import multiprocessing as mp
import queue
import sys

import sympy as sp

SEM_PROCESSOS = sys.platform == "emscripten"


class TempoEsgotado(Exception):
    def __init__(self, segundos):
        self.segundos = segundos
        super().__init__(f"não terminou em {segundos} s")


def empacotar(o):
    """Objeto do SymPy não atravessa processo por pickle.

    A classe de uma função indefinida — o `y` de y(x) — só se despickla se por
    acaso for atributo de um módulo, e a nossa nunca é: ela nasce dentro do
    leitor. O erro estoura na thread que alimenta a fila, o filho sai com
    código 0, e o pai espera para sempre por uma resposta já perdida. O srepr
    atravessa sempre.
    """
    if isinstance(o, sp.Basic):
        return ("expr", sp.srepr(o))
    if isinstance(o, (list, tuple)):
        return ("lista", [empacotar(i) for i in o], isinstance(o, tuple))
    return ("cru", o)


def desempacotar(p):
    if p[0] == "expr":
        return sp.sympify(p[1])
    if p[0] == "lista":
        itens = [desempacotar(i) for i in p[1]]
        return tuple(itens) if p[2] else itens
    return p[1]


def _correr(fila, alvo, args):
    try:
        fila.put(("ok", empacotar(alvo(*args))))
    except Exception as e:                                      # noqa: BLE001
        fila.put(("erro", f"{type(e).__name__}: {e}"))


def no_prazo(alvo, segundos, *args):
    """Roda `alvo(*args)` com prazo, e devolve o que ele devolveu."""
    if SEM_PROCESSOS:
        return alvo(*args)
    try:
        ctx = mp.get_context("fork")
    except ValueError:                      # sistema sem fork
        ctx = mp.get_context("spawn")

    fila = ctx.Queue()
    processo = ctx.Process(target=_correr, args=(fila, alvo, args), daemon=True)
    processo.start()
    try:
        # Esperar NA FILA, não no processo: Queue.empty() logo depois do join
        # mente, porque o dado ainda está a caminho do cano.
        estado, carga = fila.get(timeout=segundos)
    except queue.Empty:
        raise TempoEsgotado(segundos) from None
    finally:
        if processo.is_alive():
            processo.terminate()
        processo.join(5)

    if estado == "erro":
        raise RuntimeError(carga)
    return desempacotar(carga)
