r"""A delta de Kronecker e o Levi-Civita, declarados.

δ é também variação, número pequeno, índice: `\delta = kronecker` é
declaração. E Levi-Civita não se declara sem escolher — símbolo (±1 em toda
carta, uma densidade, que g não move) ou tensor (√|g| vezes o símbolo, que
sobe e desce com g) —, porque as duas leituras dão contas diferentes.
"""

import pytest

from sucuri.caderno import Caderno


def caderno(*fontes, dim=""):
    c = Caderno()
    for f in (rf"\mu, \nu, \rho, \sigma, \alpha = índices{dim}", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def simplificado(c, latex):
    c.executar(latex)
    ultimo = f"eq{len(c.nomes)}"
    return c.executar(f"simplificar({ultimo})").to_dict()["exato"]


# ------------------------------------------------------------------- δ

@pytest.mark.parametrize("latex, esperado", [
    (r"\delta^\mu_\nu A^\nu", "A(mu)"),
    (r"\delta^\mu_\mu", "4"),
    (r"\delta^\mu_\nu T_{\mu\rho}", "T(-nu, -rho)"),
    (r"\delta^\mu_\nu \delta^\nu_\rho", "delta(mu, -rho)"),
])
def test_delta_contrai_ao_simplificar(latex, esperado):
    c = caderno(r"\delta = kronecker", "A = tensor(1,0)", "T = tensor(0,2)")
    assert simplificado(c, latex) == esperado


def test_o_traco_da_delta_e_a_dimensao():
    c = caderno(r"\delta = kronecker", dim="(3)")
    assert simplificado(c, r"\delta^\mu_\mu") == "3"


def test_sem_declarar_delta_e_um_tensor_qualquer():
    """Sem a declaração, δ^μ_ν A^ν não vira A^μ: pode ser outra coisa."""
    c = caderno("A = tensor(1,0)")
    assert simplificado(c, r"\delta^\mu_\nu A^\nu") != "A(mu)"


@pytest.mark.parametrize("latex", [r"\delta_{\mu\nu}", r"\delta^{\mu\nu}"])
def test_delta_com_dois_indices_do_mesmo_lado_recusa(latex):
    d = caderno(r"\delta = kronecker").executar(latex).to_dict()
    assert "um índice em cima e um embaixo" in d["erro"]


# ------------------------------------------------------------------- ε

def test_levi_civita_sem_escolher_recusa():
    d = Caderno().executar(r"\epsilon = levi-civita").to_dict()
    assert "símbolo" in d["erro"] and "tensor" in d["erro"]


@pytest.mark.parametrize("qual", ["tensor", "símbolo"])
@pytest.mark.parametrize("latex", [
    r"\epsilon_{\mu\nu\rho\sigma} + \epsilon_{\nu\mu\rho\sigma}",
    r"\epsilon_{\mu\nu\rho\sigma} S^{\mu\nu}",
])
def test_levi_civita_e_antissimetrico(qual, latex):
    c = caderno(rf"\epsilon = levi-civita({qual})", "S = tensor(2,0, simétrico)")
    assert simplificado(c, latex) == "0"


def test_levi_civita_tem_tantos_indices_quanto_a_dimensao():
    c = caderno(r"\epsilon = levi-civita(tensor)", dim="(3)")
    assert c.executar(r"\epsilon_{\mu\nu\rho}").to_dict()["sympy"]
    d = c.executar(r"\epsilon_{\mu\nu\rho\sigma}").to_dict()
    assert "dimensão 3 tem 3 índices" in d["erro"]


def test_o_tensor_sobe_e_desce_com_g():
    c = caderno(r"\epsilon = levi-civita(tensor)", "g = métrica",
                r"g_{\alpha\mu} \epsilon^{\mu\nu\rho\sigma}")
    assert c.executar("contrair(eq1)").to_dict()["exato"] == \
        "epsilon(-alpha, nu, rho, sigma)"


def test_o_simbolo_nao_sobe_nem_desce():
    c = caderno(r"\epsilon = levi-civita(símbolo)", "g = métrica",
                r"g_{\alpha\mu} \epsilon^{\mu\nu\rho\sigma}")
    assert "não sobe nem desce com a métrica" in \
        c.executar("contrair(eq1)").to_dict()["erro"]


def test_o_simbolo_em_cima_nao_gera_nota_de_valencia():
    c = caderno(r"\epsilon = levi-civita(símbolo)")
    notas = c.executar(r"\epsilon^{\mu\nu\rho\sigma}").to_dict()["notas"]
    assert not any("levantar" in n for n in notas)
