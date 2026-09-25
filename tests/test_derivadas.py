r"""A derivada com índice: ∂_μ A^ν, ∇_μ T_{αβ}.

Era recusada desde o começo — "não é um fator multiplicando outro, é um
objeto próprio". Agora é: uma cabeça com o índice da derivada no primeiro
slot, que entra na contração, na soma e na canonicalização como qualquer
tensor. ∂ comuta, ∇ não; Leibniz vale para os dois; ∇ num escalar é ∂.
"""

import pytest
import sympy as sp

from sucuri.caderno import Caderno


def caderno(*fontes):
    c = Caderno()
    for f in (r"\mu, \nu, \rho, \lambda = índices", "A = tensor(1,0)",
              "B = tensor(0,1)", "g = métrica",
              "F = tensor(0,2, antissimétrico)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def lido(latex, *antes):
    return caderno(*antes).executar(latex).to_dict()


def simplificado(latex):
    c = caderno(latex)
    return c.executar("simplificar(eq1)").to_dict()["exato"]


def test_o_parser_le_produto():
    """O que a leitura evita, medido."""
    from sympy.parsing.latex import parse_latex
    lido_ = parse_latex(r"\partial_\mu A")
    assert isinstance(lido_, sp.Mul)


@pytest.mark.parametrize("latex, esperado", [
    (r"\partial_\mu A^\nu", "d_A(-mu, nu)"),
    (r"\partial_\mu A^\mu", "d_A(-L_0, L_0)"),              # a divergência
    (r"\partial^\mu \phi", "d_phi(mu)"),
    (r"\nabla_\mu \phi", "d_phi(-mu)"),                    # ∇ num escalar é ∂
    (r"\partial_\mu (\phi \psi)", "phi*d_psi(-mu) + psi*d_phi(-mu)"),
    (r"\partial_\mu (A^\nu B_\nu)",
     "A(L_0)*d_B(-mu, -L_0) + d_A(-mu, L_0)*B(-L_0)"),     # Leibniz
    (r"\partial_\mu 3", "0"),
])
def test_leitura(latex, esperado):
    assert lido(latex)["sympy"] == esperado


def test_age_so_no_fator_imediato():
    """∂_μ A^ν B_ν é (∂_μ A^ν) B_ν, como em qualquer livro."""
    assert lido(r"\partial_\mu A^\nu B_\nu")["sympy"] == "d_A(-mu, L_0)*B(-L_0)"


@pytest.mark.parametrize("latex, zero", [
    (r"\partial_\mu \partial_\nu \phi - \partial_\nu \partial_\mu \phi", True),
    (r"\nabla_\mu \nabla_\nu \phi - \nabla_\nu \nabla_\mu \phi", False),  # torção
    (r"\nabla_\mu \nabla_\nu A^\rho - \nabla_\nu \nabla_\mu A^\rho", False),
    (r"\partial_\lambda g_{\mu\nu} - \partial_\lambda g_{\nu\mu}", True),
    (r"\partial_\mu \partial_\nu F^{\mu\nu}", True),     # ∂∂ simétrico, F anti
    (r"\partial_\mu A_\nu - \partial_\nu A_\mu", False),
])
def test_simplificar(latex, zero):
    assert (simplificado(latex) == "0") == zero


def test_indices_livres():
    assert lido(r"\partial_\mu A^\nu")["indices_livres"] == [r"_\mu", r"^\nu"]


def test_latex_poe_a_derivada_na_frente():
    d = lido(r"\partial_\mu A^\nu")
    assert d["latex_semantico"].startswith(r"\partial_{\mu} A")


def test_contrair_sobe_o_indice_da_derivada():
    c = caderno(r"g^{\mu\nu} \partial_\nu \phi")
    assert c.executar("contrair(eq1)").to_dict()["exato"] == "d_phi(mu)"


def test_nao_e_a_derivada_parcial_do_sitio():
    r"""∂_μ com μ índice não pergunta "derivada em relação a μ ou produto?"."""
    assert lido(r"\partial_\mu A^\nu")["ambiguidades"] == []


@pytest.mark.parametrize("latex, trecho", [
    (r"\partial_{\mu\nu} A", "um índice por derivada"),
    (r"\partial_\mu", "sem operando"),
    (r"\partial_\mu A_\mu", "contrair é um em cima e um embaixo"),
    (r"\partial_\mu f(x)", "até onde"),
])
def test_recusa(latex, trecho):
    assert trecho in lido(latex)["erro"]


def test_sem_indice_declarado_continua_o_de_antes():
    r"""∂_p H, sem p índice, é a derivada parcial em relação a p, como sempre
    foi — ∂ está reservado à derivada, e não é pergunta."""
    d = Caderno().executar(r"\partial_p H").to_dict()
    assert d["sympy"] == "Derivative(H(p), p)"
