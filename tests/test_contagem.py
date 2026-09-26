r"""Contar componentes, conferir em componentes, coordenadas com índice e a
teoria linearizada — o que a notação indicial pede além da álgebra.

Cada verbo tem o seu controle: uma resposta que sai a mesma com o enunciado
errado não confere nada.
"""

import pytest

from sucuri.caderno import Caderno

RIEMANN = [r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
           r" = R^\rho{}_{\sigma\mu\nu} V^\sigma", "R = riemann(eq1)"]
RICCI = [r"R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}", "R = ricci(eq2)"]


def ultimo(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    d = c.executar(fontes[-1]).to_dict()
    assert not d.get("erro"), d.get("erro")
    return d["exato"]


def riemann(n, *extra):
    return [rf"\mu, \nu, \rho, \sigma = índices({n})", "V = tensor(1, 0)",
            r"\nabla = levi-civita", "g = métrica", *RIEMANN, *extra]


# ------------------------------------------------------------ contar

@pytest.mark.parametrize("n, esperado", [(2, "1"), (3, "6"), (4, "20")])
def test_componentes_do_riemann(n, esperado):
    assert ultimo(*riemann(n), "independentes(R)") == esperado


@pytest.mark.parametrize("declaracao, n, esperado", [
    ("tensor(0, 2, antissimétrico)", 4, "6"),
    ("tensor(0, 2, simétrico)", 4, "10"),
    ("tensor(0, 3, antissimétrico)", 4, "4"),
    ("tensor(0, 3, antissimétrico)", 2, "0"),
])
def test_componentes_com_simetria(declaracao, n, esperado):
    assert ultimo(rf"\mu, \nu = índices({n})", f"T = {declaracao}",
                  "independentes(T)") == esperado


@pytest.mark.parametrize("n, esperado", [(2, "0"), (3, "0"), (4, "10")])
def test_o_weyl_em_cada_dimensao(n, esperado):
    assert ultimo(rf"\mu, \nu, \rho, \sigma = índices({n})", "g = métrica",
                  "C = tensor(0, 4, riemann)",
                  r"C_{\mu\nu\rho\sigma} + C_{\mu\rho\sigma\nu} + C_{\mu\sigma\nu\rho} = 0",
                  r"C^\mu{}_{\nu\mu\sigma} = 0",
                  "independentes(C, eq1, eq2)") == esperado


def test_contar_pede_dimensao_em_numero():
    c = Caderno()
    for f in (r"\mu, \nu = índices(d)", "T = tensor(0, 2)"):
        c.executar(f)
    assert c.executar("independentes(T)").to_dict().get("erro")


# ------------------------------------------------------- em componentes

@pytest.mark.parametrize("n, eq, esperado", [
    (2, r"R_{\mu\nu\rho\sigma} = \frac{1}{2} R (g_{\mu\rho} g_{\nu\sigma} - g_{\mu\sigma} g_{\nu\rho})", "True"),
    (2, r"R_{\mu\nu\rho\sigma} = R (g_{\mu\rho} g_{\nu\sigma} - g_{\mu\sigma} g_{\nu\rho})", "False"),
    (3, r"R_{\mu\nu\rho\sigma} = \frac{1}{2} R (g_{\mu\rho} g_{\nu\sigma} - g_{\mu\sigma} g_{\nu\rho})", "False"),
    (2, r"R_{\mu\nu} = \frac{1}{2} R g_{\mu\nu}", "True"),
])
def test_identidades_por_dimensao(n, eq, esperado):
    assert ultimo(*riemann(n, *RICCI), eq, "em_componentes(eq3)") == esperado


# ------------------------------------------------ coordenadas com índice

BASE_R3 = ["i, j, k, l, m, n = índices(3)", r"\delta = kronecker",
           "g = métrica(cartesiana)", r"\epsilon = levi-civita(tensor)",
           "x = coordenadas"]


@pytest.mark.parametrize("sinal, esperado", [("+", "0"), ("-", "2*epsilon(-i, -k, -l)")])
def test_killing_das_rotacoes(sinal, esperado):
    assert ultimo(*BASE_R3, rf"\partial_k (\epsilon_{{ijl}} x^j) {sinal} "
                            r"\partial_l (\epsilon_{ijk} x^j)",
                  "simplificar(eq1)") == esperado


def test_algebra_das_rotacoes():
    assert ultimo(*BASE_R3,
                  r"\epsilon_{i m l} x^m \partial^l (\epsilon_{j n k} x^n)"
                  r" - \epsilon_{j m l} x^m \partial^l (\epsilon_{i n k} x^n)"
                  r" = -\epsilon_{i j m} \epsilon^m{}_{n k} x^n",
                  "simplificar(eq1)") == "True"


def test_nabla_das_coordenadas_e_recusado():
    c = Caderno()
    for f in BASE_R3 + [r"\nabla = levi-civita", r"\nabla_j x^i"]:
        c.executar(f)
    assert c.executar("simplificar(eq1)").to_dict().get("erro")


# ------------------------------------------------------------ linearizar

LIN = [r"\alpha, \beta, \gamma, \delta, \rho, \lambda, \kappa = índices(4)",
       "V = tensor(1, 0)", "h = tensor(0, 2, simétrico)", r"\nabla = levi-civita",
       "g = métrica",
       r"\nabla_\alpha V^\beta = \partial_\alpha V^\beta + \Gamma^\beta{}_{\alpha\lambda} V^\lambda",
       r"\Gamma = christoffel(eq1)"]


@pytest.mark.parametrize("sinal, esperado", [("-", "True"), ("+", None)])
def test_riemann_linearizado(sinal, esperado):
    eq = (r"g_{\alpha\rho} (\nabla_\gamma \nabla_\delta V^\rho - \nabla_\delta \nabla_\gamma V^\rho)"
          r" = \frac{\epsilon}{2} (\partial_\beta \partial_\gamma h_{\alpha\delta}"
          r" + \partial_\alpha \partial_\delta h_{\beta\gamma} "
          + sinal + r" \partial_\beta \partial_\delta h_{\alpha\gamma}"
          r" - \partial_\alpha \partial_\gamma h_{\beta\delta}) V^\beta")
    r = ultimo(*LIN, eq, "linearizar(eq2, h)")
    assert (r == "True") is (esperado == "True")


def test_ricci_linearizado_com_h_barra():
    def hb(a, b):
        return (rf"(h_{{{a}{b}}} - \frac{{1}}{{2}} g_{{{a}{b}}}"
                r" g^{\kappa\lambda} h_{\kappa\lambda})")
    eq = (r"\nabla_\alpha \nabla_\delta V^\alpha - \nabla_\delta \nabla_\alpha V^\alpha"
          r" = \frac{\epsilon}{2} (- g^{\gamma\rho} \partial_\gamma \partial_\rho "
          + hb(r"\beta", r"\delta") + r" + g^{\gamma\rho} \partial_\gamma \partial_\delta "
          + hb(r"\beta", r"\rho") + r" + g^{\gamma\rho} \partial_\gamma \partial_\beta "
          + hb(r"\delta", r"\rho") + r" - \frac{1}{2} g_{\beta\delta} g^{\gamma\rho}"
          r" g^{\kappa\lambda} \partial_\gamma \partial_\rho h_{\kappa\lambda}) V^\beta")
    assert ultimo(*LIN, eq, "linearizar(eq2, h)") == "True"


def test_expandir_divergencia_dentro_de_nabla():
    """∇_δ(∇_α V^α): o operando é escalar, e o par α não leva Γ."""
    r = ultimo(*LIN, r"\nabla_\delta \nabla_\alpha V^\alpha", "expandir(eq2)")
    assert "Gamma" in r


def test_torcao_de_uma_conexao_qualquer():
    assert ultimo(r"\mu, \nu, \rho, \lambda = índices", "V = tensor(1, 0)",
                  r"\nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda",
                  r"\Gamma = christoffel(eq1)",
                  r"\nabla_\mu \nabla_\nu f - \nabla_\nu \nabla_\mu f"
                  r" = -(\Gamma^\rho{}_{\mu\nu} - \Gamma^\rho{}_{\nu\mu}) \nabla_\rho f",
                  "expandir(eq2)") == "True"
