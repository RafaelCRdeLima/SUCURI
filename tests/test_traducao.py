r"""De uma notação à outra: `indices(eq)`.

A prova sem índice é mais curta; o livro de física escreve com índice. A
tradução usa o que as declarações fixaram — e onde precisa supor algo (o que
R(U,X) é, sem índice), diz numa nota.
"""

import pytest

from sucuri.caderno import Caderno

DEFINICAO = (r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
             r" = R^\rho{}_{\sigma\mu\nu} V^\sigma")


def caderno(*fontes):
    c = Caderno()
    for f in (r"\mu, \alpha, \beta, \sigma, \rho, \nu = índices",
              "U = tensor(1,0)", "X = tensor(1,0)", "Y = tensor(1,0)",
              "V = tensor(1,0)", "g = métrica", r"\omega = forma(1)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def traduzido(c, latex):
    nome = c.executar(latex).to_dict()["nome"]
    return c.executar(f"indices({nome})").to_dict()


@pytest.mark.parametrize("latex, latex_esperado", [
    (r"g(X, Y)", r"g{}_{\alpha\beta}X{}^{\alpha}Y{}^{\beta}"),
    (r"\omega(X)", r"\omega{}_{\alpha}X{}^{\alpha}"),
    (r"\nabla_U X", r"U{}^{\alpha}\nabla_{\alpha} X{}^{\mu}"),
])
def test_traducoes_simples(latex, latex_esperado):
    assert traduzido(caderno(), latex)["latex_exato"] == latex_esperado


def test_desvio_geodesico_em_indices():
    c = caderno(r"\nabla = levi-civita", DEFINICAO, "R = riemann(eq1)",
                "R = curvatura")
    d = traduzido(c, r"\nabla_U \nabla_U X = R(U,X)U")
    assert d["latex_exato"].endswith(
        r"= R{}^{\mu}{}_{\alpha\beta\sigma}U{}^{\alpha}U{}^{\beta}X{}^{\sigma}")
    assert any("supondo R(U,X)" in n for n in d["notas"])


def test_curvatura_sem_riemann_com_indice_recusa():
    c = caderno("R = curvatura")
    d = traduzido(c, r"\nabla_U \nabla_U X = R(U,X)U")
    assert "riemann(eq)" in d["erro"]


def test_compatibilidade_traduzida_simplifica_a_verdade():
    """Sem índice e com índice falam da mesma coisa: a compatibilidade,
    traduzida, fecha com ∇g = 0."""
    c = caderno(r"\nabla = levi-civita")
    nome = c.executar(
        r"\nabla_U g(X,Y) = g(\nabla_U X, Y) + g(X, \nabla_U Y)").to_dict()["nome"]
    traducao = c.executar(f"indices({nome})").to_dict()["nomeados"][0]["nome"]
    assert c.executar(f"simplificar({traducao})").to_dict()["exato"] == "True"


def test_igualdade_errada_traduzida_nao_fecha():
    c = caderno(r"\nabla = levi-civita")
    nome = c.executar(r"\nabla_U g(X,Y) = g(\nabla_U X, Y)").to_dict()["nome"]
    traducao = c.executar(f"indices({nome})").to_dict()["nomeados"][0]["nome"]
    assert c.executar(f"simplificar({traducao})").to_dict()["exato"] != "True"


def test_colchete_sem_levi_civita_usa_parcial():
    d = traduzido(caderno(), r"[U, X]")
    assert r"\partial" in d["latex_exato"] and d["notas"]


@pytest.mark.parametrize("latex, trecho", [
    (r"\forall A: \nabla_A A = 0", "traduza uma instância"),
    (r"\mathrm{d}\omega", "formas ainda não"),
])
def test_recusas(latex, trecho):
    assert trecho in traduzido(caderno(), latex)["erro"]


def test_sem_indices_declarados_recusa():
    c = Caderno()
    c.executar("X = tensor(1,0)")
    c.executar("g = métrica")
    nome = c.executar(r"g(X, X)").to_dict()["nome"]
    assert "declare os índices" in c.executar(f"indices({nome})").to_dict()["erro"]
