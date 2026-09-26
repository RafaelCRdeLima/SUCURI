r"""A base ortonormal e as formas de Cartan: conferidas contra Reall (8.50)–(8.51)
e Carroll, e as equações de estrutura conferidas pelo próprio motor."""

import sympy as sp

from sucuri.caderno import Caderno
from sucuri.cartan import cartan
from sucuri.geometria import Metrica


def linhas(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    d = c.executar(fontes[-1]).to_dict()
    assert not d.get("erro"), d.get("erro")
    return {l[0]: l[1] for l in d["linhas"]}


def test_schwarzschild_na_base():
    t, r, th, ph, m = sp.symbols("t r theta phi m")
    res = cartan(Metrica("g", [t, r, th, ph],
                         [-(1 - 2 * m / r), 1 / (1 - 2 * m / r), r**2, r**2 * sp.sin(th)**2]))
    R = lambda a, b, c, d: sp.simplify(res["eta"][a] * res["R"][a, b, c, d])
    assert R(0, 1, 0, 1) == -2 * m / r**3          # Carroll (7.33); Reall (8.51)
    assert R(2, 3, 2, 3) == 2 * m / r**3
    assert R(0, 2, 0, 2) == m / r**3
    assert res["eta"] == [-1, 1, 1, 1]


def test_ricci_nulo_de_schwarzschild():
    l = linhas(r"x = coordenadas(t, r, \theta, \phi)",
               r"g = métrica(-(1 - \frac{2m}{r}), \frac{1}{1 - \frac{2m}{r}}, r^2, r^2 \sin^2\theta)",
               "cartan(g)")
    assert l["Ricci na base"] == "todas as componentes nulas"
    assert l["ω^0_1"] == "m/r**2*dt"


def test_esfera_de_dray():
    l = linhas(r"x = coordenadas(\theta, \phi)", r"g = métrica(r^2, r^2 \sin^2\theta)", "cartan(g)")
    assert l["ω^0_1"] == "-cos(theta)*dphi"
    assert l["Θ^0_1"] == "r**(-2)*e^0∧e^1  =  sin(theta)*dtheta∧dphi"


def test_familia_f_de_tong_e_reall():
    l = linhas(r"x = coordenadas(t, r, \theta, \phi)", "f = f(r)",
               r"g = métrica(-f^2, f^{-2}, r^2, r^2 \sin^2\theta)", "cartan(g)")
    assert l["R_0101"] == "f(r)*Derivative(f(r), (r, 2)) + Derivative(f(r), r)**2"


def test_metrica_nao_diagonal_e_recusada():
    c = Caderno()
    c.executar(r"x = coordenadas(t, \phi)")
    c.executar(r"g = métrica(ds^2 = -dt^2 + 2 a dt d\phi + d\phi^2)")
    assert "diagonal" in c.executar("cartan(g)").to_dict().get("erro", "")


def test_geodesicas_conferidas_pela_acao():
    l = linhas(r"x = coordenadas(u, \phi)", r"g = métrica(-1, \cosh^2 u)", "geodésicas(g)")
    assert "conferido" in l["pela ação"]
