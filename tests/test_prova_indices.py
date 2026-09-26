r"""provar com índice: o objetivo como combinação das hipóteses.

Cada prova tem o seu par que não sai — sem uma hipótese, ou com um sinal
trocado. Uma prova que sai também quando o enunciado é falso não prova nada.
"""

import pytest

from sucuri.caderno import Caderno

RIEMANN = [r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
           r" = R^\rho{}_{\sigma\mu\nu} V^\sigma", "R = riemann(eq1)"]
RICCI = [r"R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}", "R = ricci(eq2)"]
BIANCHI = (r"\nabla_\lambda R^\rho{}_{\sigma\mu\nu} + \nabla_\mu R^\rho{}_{\sigma\nu\lambda}"
           r" + \nabla_\nu R^\rho{}_{\sigma\lambda\mu} = 0")


def prova(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c.executar(fontes[-1]).to_dict()


def base(*extra):
    return [r"\alpha, \beta, \gamma, \mu, \nu, \rho, \sigma, \lambda = índices",
            "V = tensor(1, 0)", r"\nabla = levi-civita", "g = métrica", *extra]


@pytest.mark.parametrize("hipoteses, sai", [("eq1, eq2", True), ("eq1", False)])
def test_corrente_de_killing(hipoteses, sai):
    """Reall §5.3: J^a = T^{ab}X_b conservada."""
    d = prova("a, b = índices", "T = tensor(2, 0, simétrico)", "X = tensor(0, 1)",
              r"\nabla = levi-civita", "g = métrica",
              r"\nabla_a T^{ab} = 0", r"\nabla_a X_b + \nabla_b X_a = 0",
              r"\nabla_a (T^{ab} X_b) = 0", f"provar(eq3, {hipoteses})")
    assert bool(d.get("linhas")) is sai, d.get("erro")


@pytest.mark.parametrize("sinal, sai", [("", True), ("-", False)])
def test_killing_de_segunda_ordem(sinal, sai):
    """Carroll (3.174): ∇_μ∇_σ K^ρ = R^ρ{}_{σμν} K^ν — com Bianchi, citado."""
    d = prova(*base("K = tensor(1, 0)", *RIEMANN,
                    r"\nabla_\mu K_\nu + \nabla_\nu K_\mu = 0",
                    rf"\nabla_\mu \nabla_\sigma K^\rho = {sinal}R^\rho{{}}_{{\sigma\mu\nu}} K^\nu",
                    "provar(eq3, eq2)"))
    assert bool(d.get("linhas")) is sai, d.get("erro")
    if sai:
        assert "Bianchi" in d["texto"]


@pytest.mark.parametrize("objetivo, sai", [
    (r"\nabla^\mu R_{\mu\nu} = \frac{1}{2} \nabla_\nu R", True),
    (r"\nabla^\mu R_{\mu\nu} = \nabla_\nu R", False),
    (r"\nabla^\mu (R_{\mu\nu} - \frac{1}{2} g_{\mu\nu} R) = 0", True),
])
def test_bianchi_contraida(objetivo, sai):
    d = prova(*base(*RIEMANN, *RICCI, BIANCHI, objetivo, "provar(eq4, eq3)"))
    assert bool(d.get("linhas")) is sai, d.get("erro")


@pytest.mark.parametrize("sinal, sai", [("+", True), ("-", False)])
def test_gradiente_mais_escalar_constante(sinal, sai):
    """Evans 3 Q4: ∇∇φ = Ric ⇒ |∇φ|² + R constante."""
    d = prova(*base(*RIEMANN, *RICCI,
                    r"\nabla^\mu R_{\mu\nu} = \frac{1}{2} \nabla_\nu R",
                    r"\nabla_\alpha \nabla_\beta \phi = R_{\alpha\beta}",
                    rf"\nabla_\gamma (\nabla^\alpha \phi \nabla_\alpha \phi {sinal} R) = 0",
                    "provar(eq5, eq3, eq4)"))
    assert bool(d.get("linhas")) is sai, d.get("erro")


def test_notacoes_nao_se_misturam():
    d = prova(*base("U = tensor(1,0)", r"\nabla_\mu V^\mu = 0", "[U,V] = 0",
                    "provar(eq1, eq2)"))
    assert "não tem índice" in d.get("erro", "")


def test_o_certificado_fecha():
    """A soma dos passos, com os coeficientes, é o objetivo."""
    d = prova("a, b = índices", "T = tensor(2, 0, simétrico)", "X = tensor(0, 1)",
              r"\nabla = levi-civita", "g = métrica",
              r"\nabla_a T^{ab} = 0", r"\nabla_a X_b + \nabla_b X_a = 0",
              r"\nabla_a (T^{ab} X_b) = 0", "provar(eq3, eq1, eq2)")
    rotulos = [l[0] for l in d["linhas"]]
    assert rotulos[0].startswith("eq1") and rotulos[1].startswith("1/2 · eq2")


SCHUR = [r"\mu, \nu, \rho, \sigma, \lambda = índices(d)", "V = tensor(1, 0)", r"\nabla = levi-civita", "g = métrica",
         *RIEMANN, *RICCI, r"\nabla^\mu R_{\mu\nu} = \frac{1}{2} \nabla_\nu R", r"R_{\mu\nu} = f g_{\mu\nu}"]


def test_schur_diz_que_divide_por_d_menos_2():
    """Ric = fg ⇒ ∇f = 0: pelo traço da hipótese, e dividindo por d − 2 —
    o que a prova tem de dizer, e não supor calada."""
    d = prova(*SCHUR, r"\nabla_\nu f = 0", "provar(eq5, eq3, eq4)")
    assert "d - 2 ≠ 0" in d["texto"]


def test_bianchi_segunda_da_identidade_de_ricci():
    """A identidade de Ricci simplifica a zero — a forma canônica a sabe —,
    mas ∇ dela não: é daí que sai a segunda identidade de Bianchi."""
    base = [r"\mu, \nu, \rho, \sigma, \lambda = índices", "V = tensor(1, 0)", r"\nabla = levi-civita", "g = métrica", *RIEMANN]
    certo = prova(*base, r"(\nabla_\lambda R^\rho{}_{\sigma\mu\nu} + \nabla_\mu R^\rho{}_{\sigma\nu\lambda}"
                         r" + \nabla_\nu R^\rho{}_{\sigma\lambda\mu}) V^\sigma = 0", "provar(eq2, eq1)")
    assert "provado" in certo["texto"]


BASE_DUAL = [r"a, b, c, i, j, k, l = índices", r"\delta = kronecker", r"\omega = tensor(1, 1)",
             r"X = tensor(1, 1)", "V = tensor(0, 1)", r"\omega^i{}_a X^a{}_j = \delta^i_j"]


def test_o_mudo_da_hipotese_nao_colide_com_o_do_objetivo():
    # ω X = δ tem um mudo por dentro; casado com o mudo de ω X V, os dois
    # tinham o mesmo nome e a candidata se perdia calada.
    d = prova(*BASE_DUAL, r"\omega^i{}_a X^a{}_l V_i = V_l", "provar(eq2, eq1)")
    assert d["texto"].startswith("provado"), d.get("erro")


def test_e_o_falso_continua_falso():
    d = prova(*BASE_DUAL, r"\omega^i{}_a X^a{}_l V_i = 2 V_l", "provar(eq2, eq1)")
    assert d.get("erro")


def test_maurer_cartan():
    d = prova(r"a, b, c, i, j, k, l = índices", r"\delta = kronecker", r"D = tensor(1, 2)", r"C = tensor(1, 2)",
              r"\omega = tensor(1, 1)", r"X = tensor(1, 1)",
              r"D^k{}_{ab} X^a{}_i X^b{}_j = -C^k{}_{ij}", r"X^a{}_i \omega^i{}_b = \delta^a_b",
              r"C^k{}_{ij} + C^k{}_{ji} = 0",
              r"D^k{}_{ab} = -\frac{1}{2} C^k{}_{ij} (\omega^i{}_a \omega^j{}_b - \omega^i{}_b \omega^j{}_a)",
              "provar(eq4, eq1, eq2, eq3)")
    assert d["texto"].startswith("provado"), d.get("erro")


def test_derivada_covariante_transforma_como_tensor():
    d = prova(r"\alpha, \beta, \gamma, \lambda, \mu, \nu, \rho, \sigma, \tau = índices", r"\delta = kronecker",
              r"J = tensor(1, 1)", r"K = tensor(1, 1)", r"H = tensor(1, 2)", r"L = tensor(1, 2)",
              r"S = tensor(1, 2)", r"G = tensor(1, 2)", r"A = tensor(1, 0)", r"U = tensor(1, 1)", r"T = tensor(1, 1)",
              r"L^\mu{}_{\nu\alpha} J^\alpha{}_\rho + K^\mu{}_\alpha H^\alpha{}_{\nu\rho} = 0",
              r"S^\mu{}_{\nu\rho} = K^\mu{}_\tau J^\lambda{}_\nu J^\sigma{}_\rho G^\tau{}_{\lambda\sigma} + K^\mu{}_\alpha H^\alpha{}_{\nu\rho}",
              r"T^\mu{}_\nu = L^\mu{}_{\nu\alpha} A^\alpha + K^\mu{}_\alpha J^\beta{}_\nu U^\alpha{}_\beta",
              r"J^\alpha{}_\mu K^\mu{}_\beta = \delta^\alpha_\beta",
              r"T^\mu{}_\nu + S^\mu{}_{\nu\rho} K^\rho{}_\gamma A^\gamma = K^\mu{}_\alpha J^\beta{}_\nu (U^\alpha{}_\beta + G^\alpha{}_{\beta\gamma} A^\gamma)",
              "provar(eq5, eq1, eq2, eq3, eq4)")
    assert d["texto"].startswith("provado"), d.get("erro")
