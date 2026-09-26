r"""Γ com índice: a convenção lida da definição, ∇ aberto em ∂ e Γ, Γ em ∂g.

    \nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda
    \Gamma = christoffel(eq1)
    expandir(eq2)        ∇ → ∂ + Γ
    expandir(eq2, g)     e Γ → ½ g(∂g + ∂g − ∂g), com Levi-Civita
"""

import pytest

from sucuri.caderno import Caderno

IDX = r"\mu, \nu, \rho, \sigma, \lambda, \kappa, \alpha, \beta, \gamma, \delta = índices"
REALL = r"\nabla_\rho V^\mu = \partial_\rho V^\mu + \Gamma^\mu{}_{\sigma\rho} V^\sigma"
CARROLL = r"\nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda"
LC = (r"\nabla = levi-civita", "g = métrica")


def caderno(*fontes):
    c = Caderno()
    for f in (IDX, "V = tensor(1,0)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def resposta(c, fonte):
    d = c.executar(fonte).to_dict()
    assert not d.get("erro"), (fonte, d.get("erro"))
    return d["exato"]


def expandido(fontes, eq, comando):
    c = caderno(*fontes, eq)
    return resposta(c, comando)


# ------------------------------------------------------------- a convenção

def test_convencao_de_reall_num_tensor_1_1():
    fontes = ("T = tensor(1,1)", REALL, r"\Gamma = christoffel(eq1)")
    certo = (r"\nabla_\rho T^\mu{}_\nu = \partial_\rho T^\mu{}_\nu"
             r" + \Gamma^\mu{}_{\sigma\rho} T^\sigma{}_\nu"
             r" - \Gamma^\sigma{}_{\nu\rho} T^\mu{}_\sigma")
    errado = (r"\nabla_\rho T^\mu{}_\nu = \partial_\rho T^\mu{}_\nu"
              r" + \Gamma^\mu{}_{\sigma\rho} T^\sigma{}_\nu")
    assert expandido(fontes, certo, "expandir(eq2)") == "True"
    assert expandido(fontes, errado, "expandir(eq2)") != "True"


def test_com_torcao_a_ordem_dos_slots_importa():
    """Sem Levi-Civita, Γ não é simétrico: a forma de Carroll não é a de Reall."""
    fontes = ("T = tensor(0,1)", CARROLL, r"\Gamma = christoffel(eq1)")
    carroll = r"\nabla_\mu T_\nu = \partial_\mu T_\nu - \Gamma^\lambda{}_{\mu\nu} T_\lambda"
    reall = r"\nabla_\mu T_\nu = \partial_\mu T_\nu - \Gamma^\lambda{}_{\nu\mu} T_\lambda"
    assert expandido(fontes, carroll, "expandir(eq2)") == "True"
    assert expandido(fontes, reall, "expandir(eq2)") != "True"


def test_definicao_mal_escrita_e_recusada():
    c = caderno(r"\nabla_\mu V^\nu = \partial_\mu V^\nu")
    d = c.executar(r"\Gamma = christoffel(eq1)").to_dict()
    assert d.get("erro")


def test_expandir_sem_gamma_declarado_e_recusado():
    c = caderno(r"\nabla_\mu V^\nu")
    d = c.executar("expandir(eq1)").to_dict()
    assert "christoffel" in d.get("erro", "")


# --------------------------------------------------- Γ pela métrica (Carroll)

@pytest.mark.parametrize("eq, comando", [
    # Carroll 3.?: ∂g pelos Γ de índice baixado
    (r"\partial_\lambda g_{\mu\nu} = g_{\mu\sigma} \Gamma^\sigma{}_{\nu\lambda}"
     r" + g_{\nu\sigma} \Gamma^\sigma{}_{\mu\lambda}", "expandir(eq2, g)"),
    # a derivada da inversa
    (r"\partial_\lambda g^{\mu\nu} = -\Gamma^\mu{}_{\lambda\kappa} g^{\kappa\nu}"
     r" - \Gamma^\nu{}_{\lambda\kappa} g^{\kappa\mu}", "expandir(eq2, g)"),
])
def test_derivadas_da_metrica(eq, comando):
    assert expandido((*LC, CARROLL, r"\Gamma = christoffel(eq1)"), eq,
                     comando) == "True"


def test_inversa_ao_simplificar():
    c = caderno(*LC, r"g_{\mu\kappa} \partial_\lambda g^{\kappa\nu}"
                     r" = -g^{\kappa\nu} \partial_\lambda g_{\mu\kappa}")
    assert resposta(c, "simplificar(eq1)") == "True"


def test_lie_de_forma_coordenada_e_covariante_sem_torcao():
    eq = (r"X^\nu \partial_\nu W_\mu + W_\nu \partial_\mu X^\nu"
          r" = X^\nu \nabla_\nu W_\mu + W_\nu \nabla_\mu X^\nu")
    comum = ("X = tensor(1,0)", "W = tensor(0,1)", CARROLL,
             r"\Gamma = christoffel(eq1)")
    assert expandido((r"\nabla = levi-civita", *comum), eq,
                     "expandir(eq2)") == "True"
    assert expandido(comum, eq, "expandir(eq2)") != "True"


def test_lie_da_metrica():
    eq = (r"X^\rho \partial_\rho g_{\mu\nu} + g_{\mu\rho} \partial_\nu X^\rho"
          r" + g_{\rho\nu} \partial_\mu X^\rho"
          r" = g_{\nu\rho} \nabla_\mu X^\rho + g_{\mu\rho} \nabla_\nu X^\rho")
    assert expandido((*LC, "X = tensor(1,0)", CARROLL,
                      r"\Gamma = christoffel(eq1)"), eq,
                     "expandir(eq2, g)") == "True"


@pytest.mark.parametrize("sinal, esperado", [("-", True), ("+", False)])
def test_christoffel_conformes(sinal, esperado):
    """ĝ = Ω²g: Γ̂ = Γ + Ω⁻¹(δ∂Ω + δ∂Ω − g g ∂Ω)."""
    CARROLL_A = (r"\nabla_\beta V^\alpha = \partial_\beta V^\alpha"
                 r" + \Gamma^\alpha{}_{\beta\lambda} V^\lambda")
    eq = (r"\frac{1}{2} \Omega^{-2} g^{\alpha\delta} (\partial_\beta (\Omega^2 g_{\delta\gamma})"
          r" + \partial_\gamma (\Omega^2 g_{\delta\beta}) - \partial_\delta (\Omega^2 g_{\beta\gamma}))"
          r" = \Gamma^\alpha{}_{\beta\gamma} + \Omega^{-1} (g^\alpha{}_\beta \partial_\gamma \Omega"
          r" + g^\alpha{}_\gamma \partial_\beta \Omega " + sinal +
          r" g^{\alpha\delta} g_{\beta\gamma} \partial_\delta \Omega)")
    r = expandido((*LC, CARROLL_A, r"\Gamma = christoffel(eq1)"), eq,
                  "expandir(eq2, g)")
    assert (r == "True") is esperado
