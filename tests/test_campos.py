r"""Campos vetoriais por componentes: Killing, colchete, ∇ e laplaciano,
restrição a uma subvariedade."""

import pytest

from sucuri.caderno import Caderno


def ultimo(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c.executar(fontes[-1]).to_dict()


ESFERA = [r"x = coordenadas(\theta, \phi)", r"g = métrica(1, \sin^2\theta)",
          "X = campo(0, 1)", r"Y = campo(\sin\phi, \cot\theta \cos\phi)"]


@pytest.mark.parametrize("campo, killing", [
    (r"\sin\phi, \cot\theta \cos\phi", True),
    (r"\cos\phi, -\cot\theta \sin\phi", True),
    (r"\sin\phi, \cos\phi", False),
])
def test_killing_na_esfera(campo, killing):
    d = ultimo(*ESFERA, f"Z = campo({campo})", "killing(g, Z)")
    assert (d["exato"] == "True") is killing


def test_so3():
    assert ultimo(*ESFERA, "colchete(X, Y)")["exato"] == r"(cos(phi))*∂_\theta + (-sin(phi)*cot(theta))*∂_\phi"
    assert ultimo(*ESFERA, r"Z = campo(\cos\phi, -\cot\theta \sin\phi)", "colchete(Y, Z)")["exato"] == r"(1)*∂_\phi"


@pytest.mark.parametrize("dim, sinais, n", [(4, "-1, 1, 1, 1", "10"), (3, "1, 1, 1", "6"), (2, "1, 1", "3")])
def test_os_campos_de_killing_do_espaco_plano(dim, sinais, n):
    coords = ", ".join("txyz"[:dim]) if dim == 4 else ", ".join("xyz"[:dim])
    assert ultimo(f"x = coordenadas({coords})", f"g = métrica({sinais})", "killing(g, 1)")["exato"] == n


def test_laplaciano_de_cline():
    d = ultimo(r"x = coordenadas(r, \theta)", "g = métrica(1, r^2)", "A = covetor()", "laplaciano(g, A)")
    assert d["linhas"][0][1] == ("Derivative(A_r(r, theta), (r, 2)) + Derivative(A_r(r, theta), r)/r"
                                 " - A_r(r, theta)/r**2 + Derivative(A_r(r, theta), (theta, 2))/r**2"
                                 " - 2*Derivative(A_theta(r, theta), theta)/r**3")


H3 = ["X = coordenadas(t, x, y, z)", "M = métrica(-1, 1, 1, 1)"]
EMB = [r"u = coordenadas(\chi, \theta, \phi)",
       r"h = induzida(M, \cosh\chi, \sinh\chi \sin\theta \cos\phi, \sinh\chi \sin\theta \sin\phi, \sinh\chi \cos\theta)"]


def test_boost_restrito_ao_hiperboloide_e_de_killing():
    assert ultimo(*H3, "B = campo(x, t, 0, 0)", *EMB, "restringir(B, h)", "killing(h, B)")["exato"] == "True"


def test_campo_nao_tangente_e_recusado():
    d = ultimo(*H3, "T = campo(1, 0, 0, 0)", *EMB, "restringir(T, h)")
    assert "tangente" in d.get("erro", "")
