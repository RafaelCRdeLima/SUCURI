r"""A métrica com componentes, e o que se calcula dela.

A notação de índice diz a ESTRUTURA — que g tem dois índices embaixo. Não diz o
que g VALE. Para Christoffel, Ricci e Riemann é preciso o outro lado:
componentes num sistema de coordenadas.

O teste de sanidade de toda relatividade: Schwarzschild tem Ricci nulo.
"""

import pytest
import sympy as sp

from sucuri.caderno import Caderno

SCHWARZSCHILD = [
    r"x = coordenadas(t, r, \theta, \phi)",
    r"g = métrica(-(1 - \frac{2M}{r}), \frac{1}{1 - \frac{2M}{r}}, "
    r"r^2, r^2 \sin^2\theta)",
]


def caderno_schwarzschild():
    c = Caderno()
    for fonte in SCHWARZSCHILD:
        d = c.executar(fonte).to_dict()
        assert not d.get("erro"), d.get("erro")
    return c


def test_declarar_coordenadas_e_metrica():
    c = Caderno()
    d = c.executar(SCHWARZSCHILD[0]).to_dict()
    assert "dimensão 4" in d["texto"]
    d = c.executar(SCHWARZSCHILD[1]).to_dict()
    assert "diagonal" in d["texto"]
    # as coordenadas saem como foram ESCRITAS
    assert r"\theta" in d["texto"]


def test_a_metrica_precisa_das_coordenadas_antes():
    """Componente sem coordenada não diz de quê é componente."""
    c = Caderno()
    d = c.executar(r"g = métrica(-1, 1, 1, 1)").to_dict()
    assert "declare as coordenadas antes" in d["erro"]


def test_uma_componente_por_coordenada():
    c = Caderno()
    c.executar(SCHWARZSCHILD[0])
    d = c.executar(r"g = métrica(-1, 1)").to_dict()
    assert "uma entrada por coordenada" in d["erro"]


def test_christoffel_de_schwarzschild():
    c = caderno_schwarzschild()
    d = c.executar("christoffel(g)").to_dict()
    assert "13 componente" in d["rotulo"]
    rotulos = {l[0] for l in d["linhas"]}
    assert r"\Gamma^{r}_{{t}{t}}" in rotulos
    valor = dict((l[0], l[1]) for l in d["linhas"])[r"\Gamma^{r}_{{t}{t}}"]
    assert sp.simplify(sp.sympify(valor)
                       - sp.Symbol("M") * (sp.Symbol("r") - 2 * sp.Symbol("M"))
                       / sp.Symbol("r")**3) == 0


def test_schwarzschild_tem_ricci_nulo():
    """O teste de sanidade de toda relatividade — e a razão de a solução de
    Schwarzschild ser solução do vácuo."""
    c = caderno_schwarzschild()
    d = c.executar("ricci(g)").to_dict()
    assert "0 componente" in d["rotulo"]
    assert any("todas as componentes são nulas" in str(l[1])
               for l in d["linhas"])
    assert d["proveniencia"] == "estabelecida"


def test_o_escalar_de_curvatura_tambem():
    c = caderno_schwarzschild()
    assert c.executar("escalar(g)").to_dict()["exato"] == "0"


def test_o_resultado_diz_em_que_coordenadas_esta():
    """Componente é de uma carta: trocar de coordenadas troca todas elas."""
    c = caderno_schwarzschild()
    d = c.executar("christoffel(g)").to_dict()
    assert [l[:2] for l in d["linhas"]][0] == ["coordenadas", r"t, r, \theta, \phi"]


def test_metrica_que_nao_existe():
    c = Caderno()
    assert "não conheço a métrica" in c.executar("ricci(h)").to_dict()["erro"]


def test_minkowski_e_plana():
    c = Caderno()
    c.executar(r"x = coordenadas(t, x, y, z)")
    c.executar(r"\eta = métrica(-1, 1, 1, 1)")
    d = c.executar(r"christoffel(\eta)").to_dict()
    assert "0 componente" in d["rotulo"]
