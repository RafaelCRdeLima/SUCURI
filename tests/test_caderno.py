"""O caderno: várias equações, nomes que duram, verbos que operam sobre elas.

A tentação, num caderno, é abrir um console de Python — e nesse instante a
ponte que este programa é deixa de ser obrigatória. Os verbos são poucos e
fechados de propósito, e cada um passa pelo mesmo motor, com as mesmas recusas.
"""

import pytest
import sympy as sp

from sucuri.caderno import Caderno


def caderno():
    return Caderno().configurar({"independente": "x", "linhas": "derivative",
                                 "funcoes": "f", "e": None})


def test_celula_de_matematica_ganha_nome():
    c = caderno()
    d = c.executar(r"f^{\prime} = x^2").to_dict()
    assert d["nome"] == "eq1"
    assert d["tipo"] == "math"
    assert d["sympy"] == "Eq(Derivative(f(x), x), x**2)"


def test_os_nomes_duram_e_seguem():
    c = caderno()
    assert c.executar("x^2").to_dict()["nome"] == "eq1"
    assert c.executar("x^3").to_dict()["nome"] == "eq2"


def test_resolver_equacao_diferencial_confere_por_substituicao():
    c = caderno()
    c.executar(r"f^{\prime} = x^2")
    d = c.executar("resolver(eq1)").to_dict()
    assert d["tipo"] == "comando"
    assert d["proveniencia"] == "estabelecida"
    assert ("conferência", "substituída na equação: resto 0") in [
        tuple(l) for l in d["linhas"]]


def test_resolver_serve_para_a_algebrica_tambem():
    """Obrigar o usuário a escolher entre solve e dsolve é pedir que ele
    classifique a própria equação para o programa — ao contrário."""
    c = caderno()
    c.executar("x^2 - 5x + 6 = 0")
    d = c.executar("solve(eq1)").to_dict()
    assert sorted(l[1] for l in d["linhas"]) == ["2", "3"]


def test_o_verbo_aceita_os_dois_idiomas():
    c = caderno()
    c.executar(r"\int_0^1 x^2")
    assert c.executar("avaliar(eq1)").to_dict()["exato"] == "1/3"
    assert c.executar("evaluate(eq1)").to_dict()["exato"] == "1/3"


def test_exportar_devolve_codigo_que_roda_sozinho():
    """O pedido mais honesto que um programa destes recebe — 'me dá o código
    que você usou' — e a prova de que não há mágica: o que sai roda sem o
    Sucuri."""
    c = caderno()
    c.executar(r"f^{\prime} = x^2")
    codigo = c.executar("exportar(eq1)").to_dict()["codigo"]
    assert "dsolve(eq1, f(x))" in codigo
    assert "checkodesol" in codigo

    escopo = {}
    exec(codigo, escopo)                                # noqa: S102
    x = sp.Symbol("x")
    assert escopo["solucao"] == sp.Eq(sp.Function("f")(x),
                                      sp.Symbol("C1") + x**3 / 3)


def test_nome_que_nao_existe_diz_os_que_existem():
    c = caderno()
    c.executar("x^2")
    erro = c.executar("resolver(eq7)").to_dict()["erro"]
    assert "eq7" in erro and "eq1" in erro


def test_celula_com_sitio_pendente_nao_ganha_nome():
    """A recusa do leitor atravessa o caderno: o que ninguém leu não vira
    nome, e portanto não vira conta."""
    c = Caderno().configurar({"independente": "x"})
    d = c.executar(r"\int e^{x}\,dx").to_dict()
    assert d["nome"] is None
    assert d["pendentes"] == 1


def test_o_que_nao_e_verbo_conhecido_e_matematica():
    """`sin(x)` não é comando: é uma expressão. A lista de verbos é fechada, e
    o que não está nela não vira execução de código nenhuma."""
    c = caderno()
    d = c.executar("sin(x)").to_dict()
    assert d["tipo"] == "math"


def test_verbo_sobre_nome_inexistente_nao_executa_python():
    c = caderno()
    d = c.executar("__import__('os')").to_dict()
    assert d["tipo"] == "math"          # não é verbo conhecido: é (tentativa de) math
    assert d["sympy"] is None or "os" not in str(d["sympy"])


def test_mudar_convencao_refaz_a_leitura():
    c = caderno()
    c.executar("y' + y = 0")
    c.configurar({"linhas": "symbol"})
    d = c.executar("y' + y = 0").to_dict()
    assert "Derivative" not in (d["sympy"] or "")


def test_latex_devolve_a_escrita_de_volta():
    c = caderno()
    c.executar("x^2 + 1")
    assert c.executar("latex(eq1)").to_dict()["latex_exato"] == "x^{2} + 1"
