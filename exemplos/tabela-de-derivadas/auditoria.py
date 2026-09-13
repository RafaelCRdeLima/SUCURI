"""Passa a tabela inteira pelo Sucuri e diz o que acontece com cada entrada.

Duas perguntas, em ordem, e a ordem importa:

  1. o Sucuri LÊ a entrada?           (é o que o Sucuri promete)
  2. a entrada é VERDADEIRA?          (é o que o SymPy calcula)

A segunda só faz sentido depois da primeira. E há um terceiro desfecho, o
único inaceitável: o Sucuri lê a entrada e lê ERRADO, em silêncio. É contra
esse desfecho que o programa existe, e é ele que esta auditoria caça.

    python auditoria.py [--verboso]
"""

import json
import pathlib
import sys

import sympy as sp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import sucuri                                                   # noqa: E402
from sucuri.document import Unresolved                          # noqa: E402

AQUI = pathlib.Path(__file__).parent

# As convenções de uma tabela de derivadas, declaradas uma vez. É exatamente o
# que um leitor humano assume ao abrir a página — a diferença é que aqui está
# escrito.
FUNCOES = ("f", "g", "h", "W", "F", "a", "b")
VARIAVEIS = ("c", "r", "n", "k", "z")


def documento():
    doc = sucuri.Document(independent_variable="x")
    doc.function(*FUNCOES)
    doc.variable(*VARIAVEIS)
    doc.primes_are_derivatives(True)
    return doc


# ------------------------------------------------------------- veredito

LIDA_E_PROVADA = "provada"
LIDA_E_NAO_FECHADA = "não fechada"
LIDA_E_REFUTADA = "refutada"
LIDA_ERRADO = "LIDA ERRADO"
RECUSADA = "recusada (pergunta)"
NAO_LIDA = "não lida"


def _derivadas(e):
    return e.atoms(sp.Derivative)


def _funcoes(e):
    return {a.func for a in e.atoms(sp.core.function.AppliedUndef)}


def julgar(entrada):
    """O desfecho de uma entrada, com o motivo."""
    latex = entrada["esquerda"] + " = " + entrada["direita"]
    doc = documento()
    expressao = doc.read(latex)

    if expressao.pending:
        return RECUSADA, "; ".join(expressao.questions()), None

    try:
        objeto = expressao.to_sympy()
    except Unresolved as e:
        return RECUSADA, str(e), None
    except Exception as e:                                      # noqa: BLE001
        return NAO_LIDA, f"{type(e).__name__}: {e}", None

    if not isinstance(objeto, sp.Equality):
        return NAO_LIDA, f"não virou igualdade: {sp.sstr(objeto)}", objeto

    esquerda, direita = objeto.lhs, objeto.rhs

    # O desfecho que o Sucuri existe para impedir: a entrada FALA de uma
    # derivada e o objeto lido não tem derivada nenhuma.
    if not _derivadas(esquerda):
        return (LIDA_ERRADO,
                f"a entrada é uma derivada; o objeto lido não tem derivada: "
                f"{sp.sstr(esquerda)}", objeto)

    try:
        diferenca = sp.simplify(esquerda.doit() - direita.doit())
    except Exception as e:                                      # noqa: BLE001
        return LIDA_E_REFUTADA, f"não avaliou: {type(e).__name__}: {e}", objeto

    if diferenca == 0:
        return LIDA_E_PROVADA, sp.sstr(esquerda.doit()), objeto

    # A entrada pode remeter a uma definição dada na prosa em volta ("seja
    # h = fg"). Nesse caso ela não é falsa — é incompleta fora da página.
    if _funcoes(esquerda) != _funcoes(direita):
        return (LIDA_E_NAO_FECHADA,
                f"lados falam de funções diferentes: "
                f"{sorted(f.__name__ for f in _funcoes(esquerda))} contra "
                f"{sorted(f.__name__ for f in _funcoes(direita))}", objeto)

    return LIDA_E_REFUTADA, f"diferença não anulou: {sp.sstr(diferenca)}", objeto


def main():
    verboso = "--verboso" in sys.argv
    dados = json.loads((AQUI / "tabela.json").read_text(encoding="utf-8"))
    contagem = {}
    linhas = []

    for entrada in dados["entradas"]:
        veredito, motivo, _ = julgar(entrada)
        contagem[veredito] = contagem.get(veredito, 0) + 1
        linhas.append((veredito, entrada, motivo))

    ordem = [LIDA_E_PROVADA, LIDA_ERRADO, RECUSADA, NAO_LIDA,
             LIDA_E_NAO_FECHADA, LIDA_E_REFUTADA]
    for veredito in ordem:
        do_grupo = [l for l in linhas if l[0] == veredito]
        if not do_grupo:
            continue
        print(f"\n### {veredito}  ({len(do_grupo)})")
        for _, entrada, motivo in do_grupo:
            alegacao = entrada["esquerda"] + " = " + entrada["direita"]
            print(f"  {alegacao[:78]}")
            if verboso or veredito in (LIDA_ERRADO, NAO_LIDA, RECUSADA):
                print(f"      {motivo[:120]}")

    total = len(linhas)
    print(f"\n{'-' * 62}\n{total} alegações da tabela")
    for veredito in ordem:
        if veredito in contagem:
            print(f"  {contagem[veredito]:3}  {veredito}")


if __name__ == "__main__":
    main()
