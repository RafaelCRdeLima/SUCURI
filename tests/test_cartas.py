r"""Métricas por elemento de linha e por pull-back; geodésicas, órbitas,
volume e série — o que os exercícios de componentes pediam além da curvatura.
"""

import pytest

from sucuri.caderno import Caderno


def ultimo(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    d = c.executar(fontes[-1]).to_dict()
    assert not d.get("erro"), d.get("erro")
    return d


R4 = ["X = coordenadas(w, x, y, z)", "E = métrica(1, 1, 1, 1)",
      r"u = coordenadas(\psi, \theta, \phi)",
      r"h = induzida(E, \cos\psi, \sin\psi \sin\theta \cos\phi, \sin\psi \sin\theta \sin\phi, \sin\psi \cos\theta)"]


def test_a_3_esfera_induzida():
    assert ultimo(*R4, "elemento(h)")["exato"] == (
        "dphi**2*sin(psi)**2*sin(theta)**2 + dpsi**2 + dtheta**2*sin(psi)**2")
    assert ultimo(*R4, "escalar(h)")["exato"] == "6"


def test_o_volume_e_o_elemento():
    d = ultimo(*R4, r"volume(h, \psi = 0 .. \pi, \theta = 0 .. \pi, \phi = 0 .. 2\pi)")
    assert d["exato"] == "2*pi**2"
    assert d["linhas"][0][1] == "sin(psi)**2*sin(theta)"


def test_volume_sem_limite_de_uma_coordenada_e_recusado():
    c = Caderno()
    for f in R4:
        c.executar(f)
    assert c.executar(r"volume(h, \psi = 0 .. \pi)").to_dict().get("erro")


def test_serie():
    assert ultimo(r"\frac{2 \pi \cdot (\epsilon - \sin\epsilon \cos\epsilon)}{\frac{4}{3} \pi \epsilon^3}",
                  r"série(eq1, \epsilon, 4)")["exato"] == "1 - epsilon**2/5 + O(epsilon**4)"


def test_elemento_de_linha_com_termo_cruzado():
    d = ultimo(r"x = coordenadas(t, \phi)", r"g = métrica(ds^2 = -dt^2 + 2 a dt d\phi + r^2 d\phi^2)",
               "elemento(g)")
    assert d["exato"] == "2*a*dphi*dt + dphi**2*r**2 - dt**2"


def test_elemento_de_linha_que_nao_e_quadratico_e_recusado():
    c = Caderno()
    c.executar("x = coordenadas(t, r)")
    assert c.executar("g = métrica(ds^2 = -dt^2 + dr)").to_dict().get("erro")


def test_mudanca_de_coordenadas_e_pull_back():
    d = ultimo("X = coordenadas(x, y)", "E = métrica(1, 1)", r"u = coordenadas(r, \phi)",
               r"g = induzida(E, r \cos\phi, r \sin\phi)", "elemento(g)")
    assert d["exato"] == "dphi**2*r**2 + dr**2"


@pytest.mark.parametrize("coords, metrica, esperado", [
    (r"x, y", r"\frac{1}{y^2}, \frac{1}{y^2}", "Eq(x - x_0, -sqrt(-L**2*y**2 + kappa)/L)"),
    (r"u, \phi", r"-1, \cosh^2 u", "Eq(tanh(u), sqrt(L**2 - kappa)*sin(phi - phi_0)/L)"),
    (r"\theta, \phi", r"1, \sin^2\theta", "Eq(-1/tan(theta), sqrt(-L**2 + kappa)*sin(phi - phi_0)/L)"),
])
def test_orbitas_por_quadratura(coords, metrica, esperado):
    assert ultimo(f"x = coordenadas({coords})", f"g = métrica({metrica})",
                  "órbitas(g)")["exato"] == esperado


def test_geodesicas_do_plano_hiperbolico():
    d = ultimo("x = coordenadas(x, y)", r"g = métrica(\frac{1}{y^2}, \frac{1}{y^2})", "geodésicas(g)")
    assert "2*Derivative(x(lambda), lambda)*Derivative(y(lambda), lambda)/y(lambda)" in d["exato"]
    assert any("Killing" in l[0] for l in d["linhas"])


def test_superficie_de_revolucao_com_funcao():
    d = ultimo(r"X = coordenadas(z, \varpi, \phi)", r"E = métrica(1, 1, \varpi^2)", r"f = f(\varpi)",
               r"u = coordenadas(\varpi, \phi)", r"h = induzida(E, f(\varpi), \varpi, \phi)", "escalar(h)")
    assert d["exato"] == ("2*Derivative(f(varpi), varpi)*Derivative(f(varpi), (varpi, 2))"
                          "/(varpi*(Derivative(f(varpi), varpi)**2 + 1)**2)")
