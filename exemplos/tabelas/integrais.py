"""A tabela de integrais da Wikipédia, entrada por entrada.

Mesmo método da tabela de derivadas, com uma diferença de prova. Uma entrada de
tabela de integrais é da forma

    ∫ f(x) dx = F(x) + C

e o jeito certo de conferi-la não é integrar — é **derivar o lado direito** e
comparar com o integrando. É mais rápido, não depende do integrador acertar, e
a constante de integração some sozinha na derivada, que é o que ela merece.

    python integrais.py [--baixar] [--verboso]

Ver AUDITORIA-INTEGRAIS.md.
"""

import pathlib
import random
import signal
import sys

import sympy as sp

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import comum                                                    # noqa: E402
import sucuri                                                   # noqa: E402
from sucuri.document import Unresolved                          # noqa: E402

PAGINA = "Lists_of_integrals"
ARQUIVO = "integrais"

FUNCOES = ("f", "g", "u", "v")
VARIAVEIS = ("a", "b", "c", "n", "m", "C", "A", "B")


def documento():
    doc = sucuri.Document(independent_variable="x")
    doc.function(*FUNCOES)
    doc.variable(*VARIAVEIS)
    doc.primes_are_derivatives(True)
    doc.e_is_euler(True)     # numa tabela, e^{ax} é Euler
    return doc


def interessa(esquerda):
    return "\\int" in esquerda


# ------------------------------------------------------------- vereditos

PROVADA = comum.PROVADA
PROVADA_QUASE = comum.PROVADA_QUASE
CONFERE = "confere numericamente (não é prova)"
NAO_AVALIADA = "definida, não avaliada"
NAO_CONFIRMADA = "não confirmada (só numericamente)"

NAO_FECHADA = "não fechada"
REFUTADA = "refutada"
LIDA_ERRADO = "LIDA ERRADO"
RECUSADA = "recusada (pergunta)"
NAO_LIDA = "não lida"

ORDEM = [PROVADA, PROVADA_QUASE, CONFERE, LIDA_ERRADO, RECUSADA, NAO_LIDA,
         NAO_CONFIRMADA, NAO_AVALIADA, NAO_FECHADA, REFUTADA]


_funcoes = comum.funcoes_indefinidas
_reais = comum.reais
_anula = comum.anula


def _numericamente_zero(diferenca, variavel, tentativas=12):
    """Concordância numérica NÃO é prova — serve só para separar uma alegação
    que o SymPy não soube fechar de uma alegação que é falsa."""
    if _funcoes(diferenca):
        return False
    livres = [s for s in diferenca.free_symbols if s != variavel]
    aleatorio = random.Random(20260913)
    acertos = 0
    for _ in range(tentativas):
        valores = {s: sp.Rational(aleatorio.randint(2, 9), aleatorio.randint(2, 5))
                   for s in livres}
        valores[variavel] = sp.Rational(aleatorio.randint(1, 30), 17)
        try:
            v = complex(diferenca.subs(valores, simultaneous=True).evalf())
        except Exception:                                       # noqa: BLE001
            continue
        if abs(v) > 1e-8:
            return False
        acertos += 1
    return acertos >= tentativas // 2


class _Estouro(Exception):
    pass


def _limite_de_tempo(segundos):
    """Integral definida é conta aberta: algumas não terminam."""
    def estourou(*_):
        raise _Estouro()
    anterior = signal.signal(signal.SIGALRM, estourou)
    signal.setitimer(signal.ITIMER_REAL, segundos)
    return anterior


def _solta(anterior):
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.signal(signal.SIGALRM, anterior)


def _valores(livres, semente):
    aleatorio = random.Random(semente)
    return {s: sp.Rational(aleatorio.randint(2, 9), aleatorio.randint(2, 5))
            for s in livres}


def _definida(objeto, segundos=8):
    """Integral definida não se prova derivando: o lado direito é um número.

    Tenta-se primeiro fechar simbolicamente. Falhando, compara-se numericamente
    em pontos sorteados — e o veredito diz, no nome, que isso NÃO é prova.
    """
    esquerda, direita = objeto.lhs, objeto.rhs
    if _funcoes(objeto):
        return NAO_FECHADA, "integrando com função indefinida", objeto

    anterior = _limite_de_tempo(segundos)
    try:
        fechada = esquerda.doit()
        if not fechada.atoms(sp.Integral):
            diferenca = sp.simplify(fechada - direita)
            if diferenca == 0:
                return PROVADA, "fechou simbolicamente", objeto
            if not diferenca.free_symbols:
                return (REFUTADA, f"fechou em {sp.sstr(fechada)}, "
                        f"que difere de {sp.sstr(direita)}", objeto)
    except (_Estouro, Exception):                               # noqa: BLE001
        pass
    finally:
        _solta(anterior)

    livres = sorted((esquerda.free_symbols | direita.free_symbols),
                    key=str)
    for tentativa in range(3):
        anterior = _limite_de_tempo(segundos)
        try:
            valores = _valores(livres, 20260913 + tentativa)
            a = complex(sp.N(esquerda.subs(valores, simultaneous=True)))
            b = complex(sp.N(direita.subs(valores, simultaneous=True)))
        except (_Estouro, Exception):                           # noqa: BLE001
            continue
        finally:
            _solta(anterior)
        if not (a == a and b == b):          # NaN
            continue
        escala = max(1.0, abs(a), abs(b))
        if abs(a - b) < 1e-6 * escala:
            return CONFERE, f"{a:.6g} contra {b:.6g}", objeto
        # Discordância numérica NÃO refuta: a quadratura de integral imprópria
        # ou oscilante erra sozinha. ∫₀^∞ sen(x)/x dx, que vale π/2, sai -4 no
        # avaliador. Refutar com isso seria trocar um silêncio por uma mentira.
        return (NAO_CONFIRMADA,
                f"quadratura discorda, e quadratura não refuta: "
                f"{a:.6g} contra {b:.6g}", objeto)
    return NAO_AVALIADA, "não fechou nem avaliou dentro do tempo", objeto


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
    # integral e o objeto lido não tem integral nenhuma.
    if not esquerda.atoms(sp.Integral):
        return (LIDA_ERRADO,
                f"a entrada é uma integral; o objeto lido não tem integral: "
                f"{sp.sstr(esquerda)}", objeto)
    if not isinstance(esquerda, sp.Integral):
        return (LIDA_ERRADO,
                f"a integral não é o lado esquerdo inteiro: {sp.sstr(esquerda)}",
                objeto)

    (limite,) = esquerda.limits
    if len(limite) > 1:
        return _definida(objeto)
    variavel = limite[0]
    integrando = esquerda.function

    # A prova: derivar o lado direito e comparar com o integrando. A constante
    # de integração morre na derivada, que é o destino dela.
    try:
        diferenca = sp.simplify(_reais(sp.diff(direita, variavel) - integrando))
    except Exception as e:                                      # noqa: BLE001
        return REFUTADA, f"não avaliou: {type(e).__name__}: {e}", objeto

    veredito, motivo = _anula(diferenca)
    if veredito:
        return veredito, motivo, objeto

    if _funcoes(esquerda) != _funcoes(direita):
        return (NAO_FECHADA,
                f"lados falam de funções diferentes: "
                f"{sorted(f.__name__ for f in _funcoes(esquerda))} contra "
                f"{sorted(f.__name__ for f in _funcoes(direita))}", objeto)

    if _numericamente_zero(diferenca, variavel):
        return NAO_CONFIRMADA, f"nula em todos os pontos testados: {motivo}", objeto

    return REFUTADA, f"diferença não anulou: {motivo}", objeto


def main():
    if "--baixar" in sys.argv:
        comum.recolher(PAGINA, ARQUIVO, interessa)
    linhas = []
    for entrada in comum.carregar(ARQUIVO):
        veredito, motivo, _ = julgar(entrada)
        linhas.append((veredito, entrada, motivo))
    comum.relatar(linhas, ORDEM,
                  sempre_com_motivo=(LIDA_ERRADO, NAO_LIDA, RECUSADA))


if __name__ == "__main__":
    main()
