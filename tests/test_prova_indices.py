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
