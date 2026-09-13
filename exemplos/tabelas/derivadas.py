"""A tabela de derivadas da Wikipédia, entrada por entrada.

Duas perguntas, nesta ordem, e a ordem importa:

  1. o Sucuri LÊ a entrada?           (é o que o Sucuri promete)
  2. a entrada é VERDADEIRA?          (é o que o SymPy calcula)

E um terceiro desfecho, o único inaceitável: o Sucuri lê a entrada e lê ERRADO,
em silêncio. É contra ele que o programa existe, e é ele que esta auditoria
caça.

    python derivadas.py [--baixar] [--verboso]

Ver AUDITORIA-DERIVADAS.md.
"""

import pathlib
import re
import sys

import sympy as sp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import comum                                                    # noqa: E402
import sucuri                                                   # noqa: E402
from sucuri.document import Unresolved                          # noqa: E402

PAGINA = "Differentiation_rules"
ARQUIVO = "derivadas"

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
    doc.e_is_euler(True)     # numa tabela, e^{ax} é Euler
    return doc


def interessa(esquerda):
    return bool(re.search(r"\\frac\s*\{\s*d|\\partial|'", esquerda))


# ------------------------------------------------------------- vereditos

LIDA_E_PROVADA = comum.PROVADA
PROVADA_QUASE = comum.PROVADA_QUASE
LIDA_E_NAO_FECHADA = "não fechada"
LIDA_E_REFUTADA = "refutada"
LIDA_ERRADO = "LIDA ERRADO"
RECUSADA = "recusada (pergunta)"
NAO_LIDA = "não lida"

ORDEM = [LIDA_E_PROVADA, PROVADA_QUASE, LIDA_ERRADO, RECUSADA, NAO_LIDA,
         LIDA_E_NAO_FECHADA, LIDA_E_REFUTADA]


_funcoes = comum.funcoes_indefinidas


def julgar(entrada):
    """O desfecho de uma entrada, com o motivo."""
    latex = entrada["esquerda"] + " = " + entrada["direita"]
    expressao = documento().read(latex)

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
    if not esquerda.atoms(sp.Derivative):
        return (LIDA_ERRADO,
                f"a entrada é uma derivada; o objeto lido não tem derivada: "
                f"{sp.sstr(esquerda)}", objeto)

    try:
        diferenca = sp.simplify(comum.reais(esquerda.doit() - direita.doit()))
    except Exception as e:                                      # noqa: BLE001
        return LIDA_E_REFUTADA, f"não avaliou: {type(e).__name__}: {e}", objeto

    veredito, motivo = comum.anula(diferenca)
    if veredito:
        return veredito, motivo, objeto

    # A entrada pode remeter a uma definição dada na prosa em volta ("seja
    # h = fg"). Nesse caso ela não é falsa — é incompleta fora da página.
    if _funcoes(esquerda) != _funcoes(direita):
        return (LIDA_E_NAO_FECHADA,
                f"lados falam de funções diferentes: "
                f"{sorted(f.__name__ for f in _funcoes(esquerda))} contra "
                f"{sorted(f.__name__ for f in _funcoes(direita))}", objeto)

    return LIDA_E_REFUTADA, f"diferença não anulou: {sp.sstr(diferenca)}", objeto


def main():
    if "--baixar" in sys.argv:
        comum.recolher(PAGINA, ARQUIVO, interessa)
    linhas = []
    for entrada in comum.carregar(ARQUIVO):
        veredito, motivo, _ = julgar(entrada)
        linhas.append((veredito, entrada, motivo))
    comum.relatar(linhas, ORDEM, sempre_com_motivo=(LIDA_ERRADO, NAO_LIDA, RECUSADA))


if __name__ == "__main__":
    main()
