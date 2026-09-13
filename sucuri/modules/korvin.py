"""Adaptador do KORVIN — não-integrabilidade por Galois diferencial.

O KORVIN não sabe o que é o Sucuri, e o Sucuri não sabe o que é grupo de Galois.
Este arquivo é a única peça que conhece os dois, e por isso mora aqui: assim o
KORVIN continua utilizável sozinho e o Sucuri não ganha dependência obrigatória.

## A ponte de proveniência

Os dois programas já declaravam a origem do que afirmam, cada um à sua maneira.
O KORVIN marca cada critério como primário, derivado ou sem fonte; o Sucuri
marca cada leitura como explícita, inferida ou pendente. Aqui as duas se
encontram: um veredito cujo critério não tem autoridade chega ao Sucuri como
resultado NÃO APRESENTÁVEL, e o hospedeiro o mostra como dado, nunca como
conclusão — sem precisar entender uma linha de teoria de Galois.
"""

from __future__ import annotations

import sympy as sp

import korvin as _korvin          # noqa: F401  — falha cedo se não houver

from . import Module, Operation, Provenance, Result, register

# O import acima é o contrato: este adaptador só existe se o KORVIN existir.
# Falhar aqui, na carga, faz o hospedeiro anunciar o módulo como indisponível
# em vez de oferecer operações que quebram ao serem usadas — é o que acontece
# na versão online, onde o KORVIN não vai junto.


def _traduz_proveniencia(criterio):
    """Da proveniência do KORVIN para a do Sucuri."""
    from korvin import provenance as kp
    if criterio is None:
        return Provenance.INAPPLICABLE
    if criterio.can_conclude:
        return Provenance.ESTABLISHED
    return Provenance.UNSOURCED


def _reduzida(expression):
    """Extrai r(x) de uma expressão lida como y'' = r y.

    Aceita a igualdade escrita na forma natural. É deliberadamente estreito: o
    módulo diz o que aceita, em vez de tentar adivinhar a intenção.
    """
    expr = expression.to_sympy()
    if not isinstance(expr, sp.Equality):
        raise ValueError(
            "esperava uma igualdade na forma y'' = r y; "
            f"recebi {type(expr).__name__}")

    derivadas = expr.lhs.atoms(sp.Derivative)
    if len(derivadas) != 1:
        raise ValueError("esperava exatamente uma derivada no lado esquerdo")
    d = next(iter(derivadas))
    variavel, ordem = d.variable_count[0]
    if ordem != 2:
        raise ValueError(f"esperava derivada de ordem 2; achei ordem {ordem}")

    funcao = d.expr
    r = sp.simplify(expr.rhs / funcao)
    if r.has(funcao):
        raise ValueError("o lado direito não é da forma r(x) y")
    return sp.cancel(sp.together(r)), variavel


# ------------------------------------------------------------- operações

def esquema_de_riemann(expression):
    from korvin import RiemannScheme
    r, x = _reduzida(expression)
    esq = RiemannScheme(r, x)

    linhas = [("ponto", "ordem", "expoentes")]
    for loc, ordem, exps in esq.table():
        e = f"{exps[0]}, {exps[1]}" if exps else "—"
        linhas.append((sp.sstr(loc), ordem, e))
    linhas.append(("∞", sp.sstr(esq.order_at_infinity), "—"))

    return Result(
        "esquema de Riemann", esq,
        latex=r"y'' = \left(" + sp.latex(r) + r"\right) y",
        rows=linhas,
        provenance=Provenance.INAPPLICABLE)   # é dado, não conclusão


def condicoes_de_kovacic(expression):
    from korvin import RiemannScheme
    from korvin import provenance as kp
    r, x = _reduzida(expression)
    veredito = RiemannScheme(r, x).kovacic_necessary_conditions()

    linhas = [("caso", "situação", "motivo")]
    for n in (1, 2, 3):
        c = veredito.cases[n]
        linhas.append((n, "satisfeita" if c.passes else "falha", c.reason))

    return Result(
        "condições necessárias de Kovacic", veredito, rows=linhas,
        provenance=_traduz_proveniencia(kp.CONDICOES_NECESSARIAS))


def nao_integrabilidade(expression):
    """O veredito — e o lugar onde a recusa do KORVIN atravessa a fronteira."""
    from korvin import RiemannScheme, decide
    r, x = _reduzida(expression)
    d = decide(RiemannScheme(r, x), include_case1=True)

    bloqueios = [c.refusal_reason() for c in d.blocking_criteria]
    prov = (Provenance.ESTABLISHED if not bloqueios else Provenance.UNSOURCED)

    linhas = [("caso", "resultado")]
    for rotulo, caso in (("1", d.case1), ("2", d.case2), ("3", d.case3)):
        if caso is not None:
            linhas.append((rotulo, repr(caso)))

    return Result(
        "não-integrabilidade", d, rows=linhas,
        provenance=prov, blocked_by=bloqueios)


MODULE = register(Module(
    name="korvin",
    description="não-integrabilidade hamiltoniana por Galois diferencial",
    operations=[
        Operation("esquema de Riemann",
                  "singularidades, ordens e expoentes de y'' = r y",
                  esquema_de_riemann),
        Operation("condições de Kovacic",
                  "as condições necessárias dos três casos",
                  condicoes_de_kovacic),
        Operation("não-integrabilidade",
                  "veredito combinado, com a proveniência de cada critério",
                  nao_integrabilidade),
    ]))
