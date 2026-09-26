r"""Ordem linear em componentes; a identidade de Ricci pela (4.6) de Reall;
Maxwell em espaço curvo."""

from sucuri.caderno import Caderno


def ultimo(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c.executar(fontes[-1]).to_dict()


CAMPO_FRACO = ["x = coordenadas(t, x, y, z)", r"\Phi = \Phi(x, y, z)",
               r"g = métrica(-(1 + 2\Phi), 1 - 2\Phi, 1 - 2\Phi, 1 - 2\Phi)"]


def test_ricci_em_primeira_ordem():
    d = ultimo(*CAMPO_FRACO, r"ricci(g, \Phi)")
    lap = ("Derivative(Phi(x, y, z), (x, 2)) + Derivative(Phi(x, y, z), (y, 2))"
           " + Derivative(Phi(x, y, z), (z, 2))")
    valores = {l[0]: l[1] for l in d["linhas"][1:]}
    assert set(valores) == {"R_{{t}{t}}", "R_{{x}{x}}", "R_{{y}{y}}", "R_{{z}{z}}"}
    assert all(v == lap for v in valores.values())


def test_escalar_em_primeira_ordem():
    assert ultimo(*CAMPO_FRACO, r"escalar(g, \Phi)")["exato"] == (
        "2*Derivative(Phi(x, y, z), (x, 2)) + 2*Derivative(Phi(x, y, z), (y, 2))"
        " + 2*Derivative(Phi(x, y, z), (z, 2))")


REALL = [r"\mu, \nu, \rho, \sigma, \tau = índices", "V = tensor(1, 0)", "Z = tensor(1, 0)",
         r"\nabla_\rho V^\mu = \partial_\rho V^\mu + \Gamma^\mu{}_{\nu\rho} V^\nu", r"\Gamma = christoffel(eq1)"]
RIEMANN_46 = (r"(\partial_\rho \Gamma^\mu{}_{\nu\sigma} - \partial_\sigma \Gamma^\mu{}_{\nu\rho}"
              r" + \Gamma^\tau{}_{\nu\sigma} \Gamma^\mu{}_{\tau\rho} - \Gamma^\tau{}_{\nu\rho} \Gamma^\mu{}_{\tau\sigma}) Z^\nu")
COMUTADOR = r"\nabla_\rho \nabla_\sigma Z^\mu - \nabla_\sigma \nabla_\rho Z^\mu = "


def test_identidade_de_ricci_pela_4_6():
    assert ultimo(*REALL[:3], r"\nabla = levi-civita", *REALL[3:], COMUTADOR + RIEMANN_46, "expandir(eq2)")["exato"] == "True"


def test_com_torcao_a_identidade_nao_vale():
    assert ultimo(*REALL, COMUTADOR + RIEMANN_46, "expandir(eq2)")["exato"] != "True"


MAXWELL = [r"\alpha, \beta, \gamma, \delta, \mu, \nu, \rho, \sigma = índices", "V = tensor(1, 0)", r"\nabla = levi-civita",
           "g = métrica", r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho = R^\rho{}_{\sigma\mu\nu} V^\sigma",
           "R = riemann(eq1)", "F = tensor(0, 2, antissimétrico)", r"\nabla_\beta F^{\alpha\beta} = 0",
           r"\nabla_\gamma F_{\alpha\beta} + \nabla_\alpha F_{\beta\gamma} + \nabla_\beta F_{\gamma\alpha} = 0",
           r"\nabla_\beta (F^\alpha{}_\gamma F^{\beta\gamma} - \frac{1}{4} g^{\alpha\beta} F_{\gamma\delta} F^{\gamma\delta}) = 0"]


def test_conservacao_do_tensor_de_maxwell():
    assert "provado" in ultimo(*MAXWELL, "provar(eq4, eq2, eq3)")["texto"]
    assert ultimo(*MAXWELL, "provar(eq4, eq2)").get("erro")


def test_a_corrente_de_t_hooft():
    assert ultimo(r"\mu, \nu = índices", "F = tensor(2, 0, antissimétrico)", "g = métrica", "g = det(g)",
                  r"\partial_\nu \partial_\mu (\sqrt{-g} F^{\mu\nu})", "simplificar(eq1)")["exato"] == "0"
