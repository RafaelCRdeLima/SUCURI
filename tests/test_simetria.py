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


# ------------------------------------------------------------------ Riemann

def caderno_riemann(*fontes):
    c = Caderno()
    for f in (r"a, b, c, d = índices", "g = métrica",
              "R = tensor(0, 4, riemann)", "X = tensor(1,0)", "Y = tensor(1,0)",
              "Z = tensor(1,0)", "W = tensor(1,0)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


@pytest.mark.parametrize("latex", [
    r"R_{abcd} + R_{bacd}",                  # antissimétrico no primeiro par
    r"R_{abcd} + R_{abdc}",                  # e no segundo
    r"R_{abcd} - R_{cdab}",                  # simétrico na troca dos pares
    r"R_{abcd} g^{ab}",                      # traço sobre um par: zero
])
def test_riemann_com_indice(latex):
    c = caderno_riemann(latex)
    assert c.executar("simplificar(eq1)").to_dict()["exato"] == "0"


def test_a_identidade_ciclica_nao_e_simetria():
    """R_{a[bcd]} = 0 é teorema — pede torção nula —, não troca de slots."""
    c = caderno_riemann(r"R_{abcd} + R_{bcad} + R_{cabd}")
    assert c.executar("simplificar(eq1)").to_dict()["exato"] != "0"
    c = caderno_riemann(r"R(X,Y,Z,W) + R(Y,Z,X,W) + R(Z,X,Y,W) = 0")
    assert "Não achar" in c.executar("provar(eq1)").to_dict()["erro"]


@pytest.mark.parametrize("latex", [
    r"R(X, X, Y, Z) = 0",
    r"R(X, Y, Z, W) = R(Z, W, X, Y)",
    r"R(X, Y, Z, W) = -R(X, Y, W, Z)",
    r"R(X, Y, Z, W) = R(Y, X, W, Z)",
])
def test_riemann_sem_indice(latex):
    d = caderno_riemann(latex).executar("provar(eq1)").to_dict()
    assert not d.get("erro"), d.get("erro")


def test_riemann_com_a_ciclica_como_hipotese():
    c = caderno_riemann(
        r"\forall A, B, C, D: R(A,B,C,D) + R(B,C,A,D) + R(C,A,B,D) = 0",
        r"R(X,Y,Z,W) + R(Y,Z,X,W) + R(Z,X,Y,W) = 0")
    d = c.executar("provar(eq2, eq1)").to_dict()
    assert not d.get("erro"), d.get("erro")


@pytest.mark.parametrize("fonte, trecho", [
    ("P = tensor(1, 3, riemann)", "o Riemann com as simetrias é o (0,4)"),
    ("Q = tensor(0, 3, riemann)", "quatro slots"),
])
def test_riemann_recusa(fonte, trecho):
    assert trecho in Caderno().executar(fonte).to_dict()["erro"]


# ------------------------------------------------- nome de várias letras

def test_nome_de_varias_letras_e_recusado():
    r"""Rm_{abcd} em LaTeX é R vezes m_{abcd}: a declaração existiria e nunca
    seria usada, e o SymPy leria R*m(-a,-b,-c,-d) sem reclamar."""
    d = Caderno().executar("Rm = tensor(0, 4, riemann)").to_dict()
    assert "R vezes m" in d["erro"]


def test_comando_serve_de_nome():
    c = Caderno()
    for f in (r"a, b, c, d = índices", r"\Rm = tensor(0, 4, riemann)",
              r"\Rm_{abcd} + \Rm_{bacd}"):
        c.executar(f)
    assert c.executar("simplificar(eq1)").to_dict()["exato"] == "0"
