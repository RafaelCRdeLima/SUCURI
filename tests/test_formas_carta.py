r"""Formas numa carta: ∧, d, ⋆, ι, ℒ — conferidas contra Dray (as tabelas de ⋆)
e Wendl (o divergente)."""

import pytest

from sucuri.caderno import Caderno


def ultimo(*fontes):
    c = Caderno()
    for f in fontes[:-1]:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c.executar(fontes[-1]).to_dict()


ESF = [r"x = coordenadas(r, \theta, \phi)", r"g = métrica(1, r^2, r^2 \sin^2\theta)"]


@pytest.mark.parametrize("forma, estrela", [
    ("dr", "r**2*sin(theta)*dtheta∧dphi"),
    (r"d\phi", "1/sin(theta)*dr∧dtheta"),
    (r"dr \wedge d\theta", "sin(theta)*dphi"),
    (r"d\theta \wedge d\phi", "1/(r**2*sin(theta))*dr"),
])
def test_estrela_esferica(forma, estrela):
    assert ultimo(*ESF, rf"\alpha = forma({forma})", r"estrela(\alpha, g)")["exato"] == estrela


def test_estrela_de_um():
    assert ultimo(*ESF, "estrela(1, g)")["exato"] == "r**2*sin(theta)*dr∧dtheta∧dphi"


@pytest.mark.parametrize("ordem, metrica, esperado", [
    ("x, y, z, t", "1, 1, 1, -1", "dx∧dy∧dz"),
    ("t, x, y, z", "-1, 1, 1, 1", "-dx∧dy∧dz"),
])
def test_a_orientacao_e_a_ordem_das_coordenadas(ordem, metrica, esperado):
    assert ultimo(f"x = coordenadas({ordem})", f"g = métrica({metrica})",
                  r"\alpha = forma(dt)", r"estrela(\alpha, g)")["exato"] == esperado


def test_d_ao_quadrado_e_zero():
    assert ultimo(r"x = coordenadas(u, v, w)", r"f = f(u, v, w)", "F = forma(f)",
                  "D = exterior(F)", "E = exterior(D)", "iguais(E, 0)")["exato"] == "True"


def test_divergente_pela_derivada_de_lie():
    assert ultimo("x = coordenadas(x, y, z)", "X = campo()", r"\mu = forma(dx \wedge dy \wedge dz)",
                  r"lie(X, \mu)")["exato"] == (
        "(Derivative(X^x(x, y, z), x) + Derivative(X^y(x, y, z), y)"
        " + Derivative(X^z(x, y, z), z))*dx∧dy∧dz")


def test_decomposicao_em_r3():
    assert ultimo("x = coordenadas(x, y, z)", r"H = forma(H_x dy \wedge dz + H_y dz \wedge dx + H_z dx \wedge dy)",
                  r"\alpha = forma(H_x dy - H_y dx)", r"\beta = forma(\frac{1}{H_x} (H_x dz - H_z dx))",
                  r"P = cunha(\alpha, \beta)", "iguais(P, H)")["exato"] == "True"


def test_forma_com_graus_misturados_e_recusada():
    c = Caderno()
    c.executar("x = coordenadas(x, y)")
    assert c.executar(r"\alpha = forma(dx + dx \wedge dy)").to_dict().get("erro")


def test_operacao_com_argumentos_a_menos_diz_a_forma_de_uso():
    d = ultimo(*ESF, r"\alpha = forma(dr)", r"estrela(\alpha)")
    assert d["erro"] == "estrela recebe 2 argumento(s): estrela(α, g)"


@pytest.mark.parametrize("fonte", [r"O = ortonormal(\alpha, g)", r"P = iguais(\alpha, \alpha)"])
def test_o_que_nao_e_forma_nao_recebe_nome(fonte):
    d = ultimo(*ESF, r"\alpha = forma(dr)", fonte)
    assert "não recebe nome" in d["erro"]
