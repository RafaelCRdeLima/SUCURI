r"""Componentes numa carta, de exercícios de listas reais.

Achados resolvendo-os: a declaração de função não aceitava nome grego
(`\phi = \phi(x)`), e φ ficava constante — a métrica 1+1 do MIT 8.962 PS5 #6
saía plana; e a derivada de uma função da coordenada saía como Subs com o
campo escalar do diffgeom no ponto, que a troca de volta não alcançava.
"""

import sympy as sp

from sucuri.caderno import Caderno


def ultimo(*fontes):
    c = Caderno()
    for f in fontes:
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return d


def test_funcao_de_nome_grego():
    d = ultimo("x = coordenadas(t, x)", "e = euler", r"\phi = \phi(x)",
               r"\psi = \psi(x)", r"g = métrica(-e^{2\phi}, e^{-2\psi})",
               "escalar(g)")
    phi, psi = sp.Function("phi"), sp.Function("psi")
    x = sp.Symbol("x")
    esperado = -2 * sp.exp(2 * psi(x)) * (phi(x).diff(x, 2) + phi(x).diff(x)**2
                                          + phi(x).diff(x) * psi(x).diff(x))
    assert sp.simplify(sp.sympify(d["exato"], locals={"phi": phi, "psi": psi})
                       - esperado) == 0


def test_sem_subs_e_sem_campo_do_diffgeom():
    d = ultimo("x = coordenadas(t, x, y, z)", "a = a(t)",
               "g = métrica(-1, a^2, a^2, a^2)", "escalar(g)")
    assert "Subs" not in d["exato"] and "mathbf" not in d["latex_exato"]
    assert d["exato"] == "6*(a(t)*Derivative(a(t), (t, 2)) + Derivative(a(t), t)**2)/a(t)**2"


def test_uma_metrica_nao_contamina_a_seguinte():
    r"""FRW com k em (t, r, θ, φ), depois FRW plano em (t, x, y, z): o cache do
    SymPy devolvia, na segunda conta, um Subs com o t da primeira carta."""
    ultimo("x = coordenadas(t, r, \\theta, \\phi)", "a = a(t)",
           r"g = métrica(-1, \frac{a^2}{1 - k r^2}, a^2 r^2, a^2 r^2 \sin^2\theta)",
           "escalar(g)")
    d = ultimo("x = coordenadas(t, x, y, z)", "a = a(t)",
               "g = métrica(-1, a^2, a^2, a^2)", "escalar(g)")
    assert "Subs" not in d["exato"]


def test_argumento_de_nome_grego():
    r"""Hirata, Ph236 HW4 #1: F = F(\varpi) guardava a variável como '\varpi',
    um símbolo diferente da coordenada varpi, e a superfície saía plana."""
    d = ultimo(r"x = coordenadas(\varpi, \phi)", r"F = F(\varpi)",
               r"g = métrica(F, \varpi^2)", "escalar(g)")
    assert d["exato"] == "Derivative(F(varpi), varpi)/(varpi*F(varpi)**2)"
