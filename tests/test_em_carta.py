r"""em_carta: uma expressão com índice, componente por componente — o Ricci de
f(r), Reissner–Nordström (Carroll 4.5) e a holonomia da esfera."""

from sucuri.caderno import Caderno


def ultimo(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c.executar(fontes[-1]).to_dict()


CARTA = [r"\alpha, \beta, \gamma, \delta, \mu, \nu, \rho, \sigma = índices", "V = tensor(1, 0)",
         r"\nabla = levi-civita", r"x = coordenadas(t, r, \theta, \phi)"]
RIC = [r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho = R^\rho{}_{\sigma\mu\nu} V^\sigma",
       "R = riemann(eq1)", r"R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}", "R = ricci(eq2)"]
TMAX = r"F_{\alpha\gamma} F_\beta{}^\gamma - \frac{1}{4} g_{\alpha\beta} F_{\gamma\delta} F^{\gamma\delta}"
F_RN = r"1 - \frac{2m}{r} + \frac{\kappa Q^2}{2 r^2}"


def test_ricci_theta_theta():
    d = ultimo(*CARTA, "f = f(r)", r"g = métrica(-f, \frac{1}{f}, r^2, r^2 \sin^2\theta)", *RIC,
               r"R_{\mu\nu}", "em_carta(eq3)")
    assert "-r*Derivative(f(r), r) - f(r) + 1" in d["exato"]


def test_reissner_nordstrom():
    d = ultimo(*CARTA, rf"g = métrica(-({F_RN}), \frac{{1}}{{{F_RN}}}, r^2, r^2 \sin^2\theta)", *RIC,
               r"F = forma(\frac{Q}{r^2} dt \wedge dr)", r"\kappa = constante",
               rf"R_{{\alpha\beta}} = \kappa \cdot ({TMAX})", "em_carta(eq3)")
    assert d["exato"] == "True"


def test_a_metrica_errada_nao_confere():
    d = ultimo(*CARTA, r"g = métrica(-(1 - \frac{2m}{r}), \frac{1}{1 - \frac{2m}{r}}, r^2, r^2 \sin^2\theta)", *RIC,
               r"F = forma(\frac{Q}{r^2} dt \wedge dr)", r"\kappa = constante",
               rf"R_{{\alpha\beta}} = \kappa \cdot ({TMAX})", "em_carta(eq3)")
    assert d["exato"] != "True"


ESF = [r"a, b, c, d, e, f, h, k = índices(2)", "V = tensor(1, 0)", r"\nabla = levi-civita",
       r"x = coordenadas(\theta, \phi)", r"g = métrica(1, \sin^2\theta)",
       r"\nabla_a \nabla_b V^c - \nabla_b \nabla_a V^c = R^c{}_{dab} V^d", "R = riemann(eq1)", "A = campo()"]


def test_holonomia_ortogonal():
    assert ultimo(*ESF, r"g_{ab} A^a R^b{}_{cef} A^c", "em_carta(eq2)")["exato"] == "0"


def test_holonomia_rotacao_de_d_omega():
    d = ultimo(*ESF, r"g_{ab} R^a{}_{cef} A^c R^b{}_{dhk} A^d - (g_{eh} g_{fk} - g_{ek} g_{fh}) g_{cd} A^c A^d",
               "em_carta(eq2)")
    assert d["exato"] == "0"


def test_sem_componentes_recusa():
    d = ultimo(*ESF, "B = tensor(1, 0)", r"B^a R^b{}_{acd}", "em_carta(eq2)")
    assert d.get("erro")
