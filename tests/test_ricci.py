r"""O Ricci e o escalar, declarados como contrações do Riemann.

    R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}      eq2
    R = ricci(eq2)

E as simetrias do Riemann que são teorema com Levi-Civita e métrica: a troca
de pares e a antissimetria no primeiro par. Delas sai a simetria do Ricci,
sem ser suposta.
"""

import pytest

from sucuri.caderno import Caderno

DEF_RIEMANN = (r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
               r" = R^\rho{}_{\sigma\mu\nu} V^\sigma")
WEYL = (r"R_{\mu\nu\rho\sigma} - \frac{1}{d-2} (R_{\mu\rho} g_{\nu\sigma}"
        r" + R_{\nu\sigma} g_{\mu\rho} - R_{\mu\sigma} g_{\nu\rho} - R_{\nu\rho} g_{\mu\sigma})"
        r" + \frac{1}{(d-1)(d-2)} R (g_{\mu\rho} g_{\nu\sigma} - g_{\mu\sigma} g_{\nu\rho})")


def caderno(*fontes, dim="", metrica=True, ricci=r"R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}"):
    c = Caderno()
    base = [rf"\mu, \nu, \rho, \sigma, \alpha, \beta = índices{dim}",
            "V = tensor(1, 0)", r"\nabla = levi-civita"]
    base += ["g = métrica"] if metrica else []
    base += [DEF_RIEMANN, "R = riemann(eq1)"]
    base += [ricci, "R = ricci(eq2)"] if ricci else []
    for f in (*base, *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def simplificado(c, latex):
    nome = c.executar(latex).to_dict()["nome"]
    d = c.executar(f"simplificar({nome})").to_dict()
    assert not d.get("erro"), d.get("erro")
    return d["exato"]


@pytest.mark.parametrize("latex, esperado", [
    (r"R_{\mu\nu} - R_{\nu\mu}", "0"),
    (r"R^\rho{}_{\mu\rho\nu}", "Ric(-mu, -nu)"),
    (r"R^\rho{}_{\mu\nu\rho}", "-Ric(-mu, -nu)"),
    (r"g^{\mu\nu} R_{\mu\nu}", "R"),
    (r"R^{\mu\nu}{}_{\mu\nu}", "R"),
])
def test_contracoes_dobram_em_ricci_e_escalar(latex, esperado):
    assert simplificado(caderno(), latex) == esperado


def test_a_convencao_do_ricci_e_a_escrita():
    """Contraindo o 1º com o 4º, o Ricci é o oposto — e é o que vale."""
    c = caderno(ricci=r"R_{\mu\nu} = R^\rho{}_{\mu\nu\rho}")
    assert simplificado(c, r"R^\rho{}_{\mu\rho\nu}") == "-Ric(-mu, -nu)"


def test_ricci_pede_o_riemann():
    c = Caderno()
    for f in (r"\mu, \nu, \rho = índices", "R = tensor(0, 4)",
              r"R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}"):
        c.executar(f)
    assert c.executar("R = ricci(eq1)").to_dict().get("erro")


@pytest.mark.parametrize("latex", [
    r"R_{\alpha\beta\mu\nu} - R_{\mu\nu\alpha\beta}",
    r"R_{\alpha\beta\mu\nu} + R_{\beta\alpha\mu\nu}",
])
def test_simetrias_do_riemann_com_metrica(latex):
    assert simplificado(caderno(ricci=None), latex) == "0"


def test_sem_metrica_a_troca_de_pares_nao_se_supoe():
    c = caderno(ricci=None, metrica=False)
    assert simplificado(c, r"R_{\alpha\beta\mu\nu} - R_{\mu\nu\alpha\beta}") != "0"


def test_divergencia_dupla_comuta():
    """Evans 3 Q1(ii): ∇_α∇_β T^{αβ} = ∇_β∇_α T^{αβ} — do Ricci simétrico."""
    c = caderno("T = tensor(2, 0)", ricci=None)
    assert simplificado(c, r"\nabla_\alpha \nabla_\beta T^{\alpha\beta}"
                           r" - \nabla_\beta \nabla_\alpha T^{\alpha\beta}") == "0"


def test_o_traco_do_weyl_em_d_dimensoes():
    c = caderno(dim="(d)")
    assert simplificado(c, rf"g^{{\mu\rho}} ({WEYL})") == "0"


def test_o_traco_com_a_e_b():
    c = caderno("a, b = constante", dim="(d)")
    saida = simplificado(c, r"g^{\mu\rho} (R_{\mu\nu\rho\sigma} + a (R_{\mu\rho}"
                            r" g_{\nu\sigma} + R_{\nu\sigma} g_{\mu\rho} - R_{\mu\sigma}"
                            r" g_{\nu\rho} - R_{\nu\rho} g_{\mu\sigma}) + b R (g_{\mu\rho}"
                            r" g_{\nu\sigma} - g_{\mu\sigma} g_{\nu\rho}))")
    assert saida == ("(R*a + R*b*d - R*b)*g(-nu, -sigma)"
                     " + (a*d - 2*a + 1)*Ric(-nu, -sigma)")


def test_dimensao_letra_recusa_o_que_pede_numero():
    c = Caderno()
    c.executar(r"\mu = índices(d)")
    assert c.executar(r"\epsilon = levi-civita(tensor)").to_dict().get("erro")
    assert c.executar("g = métrica(euclidiana)").to_dict().get("erro")


def test_r_sem_indice_sem_ricci_e_recusado_ao_derivar():
    c = caderno(ricci=None)
    d = c.executar(r"\partial_\mu R").to_dict()
    assert "ricci" in d.get("erro", "")
