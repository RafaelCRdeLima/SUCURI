r"""Simetria declarada: `F = tensor(0, 2, antissimétrico)`.

Nas duas notações. Com índice, a simetria alimenta a canonicalização de
Butler-Portugal do SymPy — o `simplify` sozinho não a usa, e F_{μν} + F_{νμ}
ficava como estava. Sem índice, o motor põe os slots em ordem canônica, com o
sinal da permutação, e F(X,X) = 0 sai sem hipótese.

A métrica é simétrica sem precisar dizer — antes, nem g_{μν} − g_{νμ} zerava.
"""

import pytest

from sucuri.caderno import Caderno, _RE_TENSOR


def caderno(*fontes):
    c = Caderno()
    for f in (r"\mu, \nu, \alpha = índices", "g = métrica",
              "F = tensor(0, 2, antissimétrico)", "h = tensor(2, 0, simétrico)",
              "X = tensor(1,0)", "Y = tensor(1,0)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def simplificado(latex):
    c = caderno(latex)
    return c.executar("simplificar(eq1)").to_dict()["exato"]


@pytest.mark.parametrize("escrito, qual", [
    ("F = tensor(0,2, antissimétrico)", "antissimétrico"),
    ("F = tensor(0,2, anti-simétrico)", "anti-simétrico"),
    ("F = tensor(0,2, antisimetrico)", "antisimetrico"),
    ("h = tensor(2,0, simétrico)", "simétrico"),
    ("h = tensor(2,0, simetrico)", "simetrico"),
])
def test_as_grafias_da_declaracao(escrito, qual):
    assert _RE_TENSOR.match(escrito).group(4) == qual


# ------------------------------------------------------------- com índice

@pytest.mark.parametrize("latex", [
    r"g_{\mu\nu} - g_{\nu\mu}",               # a métrica, sem dizer nada
    r"F_{\mu\nu} + F_{\nu\mu}",
    r"h^{\mu\nu} - h^{\nu\mu}",
    r"F_{\mu\nu} h^{\mu\nu}",                 # antissimétrico com simétrico
    r"F_{\mu\nu} g^{\mu\nu}",                 # o traço de um antissimétrico
])
def test_simplificar_usa_a_simetria(latex):
    assert simplificado(latex) == "0"


def test_ler_nao_simplifica():
    """Ler e simplificar são atos diferentes: a leitura mostra o que foi
    escrito, com a valência; o zero é resposta do verbo."""
    d = caderno().executar(r"F_{\mu\nu} + F_{\nu\mu}").to_dict()
    assert d["sympy"] != "0"


def test_sem_simetria_nao_zera():
    c = caderno("T = tensor(0, 2)", r"T_{\mu\nu} - T_{\nu\mu}")
    assert c.executar("simplificar(eq1)").to_dict()["exato"] != "0"


@pytest.mark.parametrize("fonte, trecho", [
    ("A = tensor(1, 1, simétrico)", "baixar um deles com a métrica"),
    ("V = tensor(1, 0, simétrico)", "um slot só"),
])
def test_recusa(fonte, trecho):
    d = Caderno().executar(fonte).to_dict()
    assert trecho in d["erro"]


# ------------------------------------------------------------- sem índice

@pytest.mark.parametrize("latex", [
    r"F(X, X) = 0",
    r"F(X, Y) + F(Y, X) = 0",
    r"F(X + Y, X) = F(Y, X)",
    r"F(f X, Y) = -f F(Y, X)",
])
def test_provar_usa_a_simetria(latex):
    c = caderno(latex)
    d = c.executar("provar(eq1)").to_dict()
    assert not d.get("erro"), d.get("erro")


def test_sem_simetria_nao_prova():
    c = caderno("T = tensor(0, 2)", r"T(X, X) = 0")
    assert "Não achar" in c.executar("provar(eq1)").to_dict()["erro"]
