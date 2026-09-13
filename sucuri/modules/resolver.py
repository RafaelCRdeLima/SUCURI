"""Resolver a equação — e dizer que tipo de resposta é.

O `dsolve` responde "consigo achar uma solução?", nunca "existe uma?". Não
achar não prova nada, e é o próprio SymPy quem esconde isso: ele rebaixa a
resposta sem avisar. Medido na versão que o Sucuri fixa:

    y'' + y = 0          C1·sin(x) + C2·cos(x)          forma fechada
    y'' = x y            C1·airyai(x) + C2·airybi(x)    forma fechada
    y'' + x y' + y = 0   ... + O(x**6)                  SÉRIE TRUNCADA
    y'' = 6 y^2          (não termina)
    y' = y^2 + x         TypeError dentro do solver

A terceira é a perigosa: a equação tem forma fechada (ela é (y' + xy)' = 0, e o
próprio SymPy resolve isso com erfi), mas o que volta é uma série até ordem 5.
Quem não olhar o `O(x**6)` no fim não percebe que mudou de tipo de resposta.

Por isso este módulo faz três coisas que o `dsolve` sozinho não faz:

1. **classifica a resposta** — forma fechada, série truncada, relação
   implícita ou nada;
2. **confere por substituição**, com `checkodesol`: solução que não volta zero
   na equação não se apresenta como conclusão, por mais bonita que seja;
3. **põe prazo**. O `dsolve` não tem como ser interrompido de fora, e em
   y'' = 6y² ele não volta.

E quando não acha, diz a única coisa honesta: não achar não é prova de que não
existe. Quem responde a essa outra pergunta é o módulo `korvin`.
"""

from __future__ import annotations

import multiprocessing as mp
import queue

import sympy as sp
from sympy.core.function import AppliedUndef

from . import Module, Operation, Provenance, Result, register

PRAZO_RESOLVER = 20
PRAZO_CONFERIR = 10


# ------------------------------------------------------------------ prazo

class TempoEsgotado(Exception):
    def __init__(self, segundos):
        self.segundos = segundos
        super().__init__(f"não terminou em {segundos} s")


def _empacotar(o):
    """Objeto do SymPy não atravessa processo por pickle.

    A classe de uma função indefinida — o `y` de y(x) — só se despickla se por
    acaso for atributo de um módulo, e a nossa nunca é: ela nasce dentro do
    leitor. O erro estoura na thread que alimenta a fila, o filho sai com
    código 0, e o pai espera para sempre por uma resposta que já foi perdida.
    O srepr atravessa sempre.
    """
    if isinstance(o, sp.Basic):
        return ("expr", sp.srepr(o))
    if isinstance(o, (list, tuple)):
        return ("lista", [_empacotar(i) for i in o], isinstance(o, tuple))
    return ("cru", o)


def _desempacotar(p):
    if p[0] == "expr":
        return sp.sympify(p[1])
    if p[0] == "lista":
        itens = [_desempacotar(i) for i in p[1]]
        return tuple(itens) if p[2] else itens
    return p[1]


def _correr(fila, alvo, args):
    try:
        fila.put(("ok", _empacotar(alvo(*args))))
    except Exception as e:                                      # noqa: BLE001
        fila.put(("erro", f"{type(e).__name__}: {e}"))


def _no_prazo(alvo, segundos, *args):
    """Roda `alvo(*args)` em processo separado, com prazo.

    Processo e não thread de propósito: o `dsolve` não oferece ponto de
    interrupção, e uma thread pendurada continua queimando CPU até o fim do
    programa. Processo se mata.
    """
    try:
        ctx = mp.get_context("fork")
    except ValueError:                      # sistema sem fork
        ctx = mp.get_context("spawn")

    fila = ctx.Queue()
    processo = ctx.Process(target=_correr, args=(fila, alvo, args), daemon=True)
    processo.start()
    try:
        # Esperar NA FILA, não no processo: Queue.empty() logo depois do join
        # mente, porque o dado ainda está a caminho do cano. Esperar no
        # processo e perguntar à fila depois perde a resposta.
        estado, carga = fila.get(timeout=segundos)
    except queue.Empty:
        raise TempoEsgotado(segundos) from None
    finally:
        if processo.is_alive():
            processo.terminate()
        processo.join(5)

    if estado == "erro":
        raise RuntimeError(carga)
    return _desempacotar(carga)


# ------------------------------------------------------------- a equação

def edo(expression):
    """(equação, função incógnita, variável) — ou uma recusa explicada.

    Deliberadamente estreito, como o adaptador do KORVIN: o módulo diz o que
    aceita em vez de adivinhar a intenção.
    """
    expr = expression.to_sympy()
    if isinstance(expr, sp.Equality):
        equacao = expr
    else:
        equacao = sp.Eq(expr, 0)

    derivadas = equacao.atoms(sp.Derivative)
    if not derivadas:
        raise ValueError("não há derivada nenhuma: isto não é equação diferencial")

    incognitas = {a.func for d in derivadas for a in d.atoms(AppliedUndef)}
    if not incognitas:
        raise ValueError(
            "a derivada não é de uma função incógnita. Declare a função — em "
            "y'' + y = 0, é preciso dizer que y é função de x")
    if len(incognitas) > 1:
        nomes = ", ".join(sorted(f.__name__ for f in incognitas))
        raise ValueError(
            f"há mais de uma função incógnita ({nomes}): isto é um sistema, e "
            f"este módulo resolve uma equação de cada vez")

    variaveis = {v for d in derivadas for v in d.variables}
    if len(variaveis) > 1:
        nomes = ", ".join(sorted(str(v) for v in variaveis))
        raise ValueError(
            f"há derivadas em mais de uma variável ({nomes}): isto é uma "
            f"equação a derivadas parciais, e o pdsolve do SymPy resolve muito "
            f"pouco delas")

    funcao = next(iter(incognitas))
    variavel = next(iter(variaveis))
    return equacao, funcao(variavel), variavel


def _ordem(equacao, funcao):
    return sp.ode_order(equacao, funcao.func)


# ----------------------------------------------------- tipo de resposta

FECHADA = "forma fechada"
SERIE = "série truncada"
IMPLICITA = "relação implícita"
NENHUMA = "nenhuma"


def tipo_da_resposta(solucao, funcao):
    """Que espécie de objeto o solver devolveu.

    A distinção que o `dsolve` não faz: uma série truncada não é uma solução,
    é uma aproximação até certa ordem, e tratá-la como solução é o erro que
    este módulo existe para impedir.
    """
    if solucao is None:
        return NENHUMA, None
    if isinstance(solucao, (list, tuple)):
        tipos = [tipo_da_resposta(s, funcao)[0] for s in solucao]
        return (SERIE if SERIE in tipos else tipos[0]), None

    ordem = solucao.rhs.getO() if hasattr(solucao.rhs, "getO") else None
    if ordem is not None or solucao.has(sp.Order):
        return SERIE, ordem
    if solucao.lhs != funcao:
        return IMPLICITA, None
    return FECHADA, None


# --------------------------------------------------------------- operações

def _dsolve(equacao, funcao):
    return sp.dsolve(equacao, funcao)


def _checkodesol(equacao, solucao):
    return sp.checkodesol(equacao, solucao)


def _confere(equacao, solucao):
    """A solução volta zero quando substituída? ('sim'/'não'/'não deu tempo')"""
    try:
        veredito = _no_prazo(_checkodesol, PRAZO_CONFERIR, equacao, solucao)
    except TempoEsgotado:
        return None, f"não deu tempo de conferir em {PRAZO_CONFERIR} s"
    except Exception as e:                                      # noqa: BLE001
        return None, f"a conferência falhou: {e}"

    if isinstance(veredito, list):
        oks = [v[0] for v in veredito]
        restos = [v[1] for v in veredito]
        if all(oks):
            return True, f"{len(oks)} soluções substituídas: resto 0 em todas"
        return False, f"resto não nulo em {oks.count(False)} de {len(oks)}: {restos}"

    ok, resto = veredito
    if ok:
        return True, "substituída na equação: resto 0"
    return False, f"substituída na equação: resto {sp.sstr(resto)[:60]}"


_NAO_E_PROVA = ("não achar solução não é prova de que não existe; para essa "
                "outra pergunta, o módulo korvin")


def _sem_solucao(linhas, motivo):
    """O desfecho mais comum, e o que mais precisa de rótulo honesto.

    Rotular isto de "solução" seria a mentira do próprio `dsolve`: o que houve
    foi o solver não achar, e não achar não é achar que não há.
    """
    return Result("sem solução encontrada", None,
                  rows=linhas + [("tipo", NENHUMA), ("motivo", motivo)],
                  provenance=Provenance.INAPPLICABLE,
                  blocked_by=[_NAO_E_PROVA])


def resolver(expression):
    """Resolve, classifica a resposta e confere por substituição."""
    equacao, funcao, _ = edo(expression)
    ordem = _ordem(equacao, funcao)
    linhas = [("equação", sp.sstr(equacao)), ("ordem", str(ordem))]

    try:
        solucao = _no_prazo(_dsolve, PRAZO_RESOLVER, equacao, funcao)
    except TempoEsgotado as e:
        return _sem_solucao(linhas, str(e))
    except Exception as e:                                      # noqa: BLE001
        return _sem_solucao(linhas, f"o solver falhou: {e}")

    tipo, ordem_serie = tipo_da_resposta(solucao, funcao)
    linhas.append(("tipo", tipo if ordem_serie is None
                   else f"{tipo} em {sp.sstr(ordem_serie)}"))

    if tipo == SERIE:
        # Série truncada não é solução: é aproximação até uma ordem. Vai como
        # DADO, nunca como conclusão, e o rótulo diz isso.
        linhas.append(("solução", sp.sstr(solucao)))
        return Result("série (não é solução fechada)", solucao,
                      latex=sp.latex(solucao), rows=linhas,
                      provenance=Provenance.INAPPLICABLE)

    linhas.append(("solução", sp.sstr(solucao)))
    conferida, nota = _confere(equacao, solucao)
    linhas.append(("conferência", nota))

    if conferida:
        return Result("solução", solucao, latex=sp.latex(solucao), rows=linhas,
                      provenance=Provenance.ESTABLISHED)

    # O solver devolveu algo que a substituição não confirmou. É o caso em que
    # a resposta parece perfeita e não se sustenta — não se apresenta.
    return Result("solução não confirmada", solucao, latex=sp.latex(solucao),
                  rows=linhas, provenance=Provenance.UNSOURCED,
                  blocked_by=["a substituição não devolveu zero; o que o solver "
                              "achou não foi verificado"])


def classificar(expression):
    """Os padrões que o SymPy tentaria — a máquina por dentro.

    `classify_ode` devolve uma lista de PADRÕES, não um procedimento de
    decisão. Ver a lista vazia, ou só com 'power_series' e 'lie_group', já
    antecipa que não vem forma fechada.
    """
    equacao, funcao, _ = edo(expression)
    try:
        padroes = _no_prazo(sp.classify_ode, PRAZO_CONFERIR, equacao, funcao)
    except TempoEsgotado as e:
        padroes = ()
        nota = str(e)
    else:
        nota = None

    linhas = [("ordem", str(_ordem(equacao, funcao)))]
    linhas += [("padrão", p) for p in padroes]
    if not padroes:
        linhas.append(("padrão", nota or "nenhum: o SymPy não tem por onde começar"))

    return Result("padrões aplicáveis", list(padroes), rows=linhas,
                  provenance=Provenance.INAPPLICABLE)


MODULE = register(Module(
    name="resolver",
    description="resolve a equação diferencial e diz que tipo de resposta é",
    operations=[
        Operation("resolver",
                  "dsolve com prazo, classificado e conferido por substituição",
                  resolver),
        Operation("padrões",
                  "os métodos que o SymPy tentaria, antes de tentar",
                  classificar),
    ]))
