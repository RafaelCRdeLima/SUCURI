r"""det g declarado, e as derivadas da métrica que ∂ esconde.

    g = det(g)             g sem índice é det g_{μν}: ∂g = g g^{μν}∂g_{μν}
    g = métrica(cartesiana)   ∂g = 0 — e só então

∂ não comuta com levantar índice: ∂_μ(∂^μ φ) é ∂_μ(g^{μν}∂_ν φ). Até esta
suíte, o Sucuri empilhava ∂ na cabeça com o índice levantado, e o termo de ∂g
sumia calado.
"""

import pytest

from sucuri.caderno import Caderno

CARROLL = r"\nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda"


def caderno(*fontes, metrica="g = métrica(-,+,+,+)"):
    c = Caderno()
    for f in (r"\mu, \nu, \lambda, \alpha, \beta = índices", "V = tensor(1,0)",
              r"\nabla = levi-civita", metrica, *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def resposta(c, fonte):
    d = c.executar(fonte).to_dict()
    assert not d.get("erro"), (fonte, d.get("erro"))
    return d["exato"]


def expandido(eq, *fontes, **kw):
    c = caderno(*fontes, "g = det(g)", CARROLL, r"\Gamma = christoffel(eq1)",
                eq, **kw)
    return resposta(c, "expandir(eq2, g)")


def test_g_sem_indice_sem_declarar_e_recusado():
    c = caderno()
    d = c.executar(r"\partial_\mu (\sqrt{-g} V^\mu)").to_dict()
    assert "det(g)" in d.get("erro", "")


def test_det_pede_a_metrica_declarada():
    c = Caderno()
    d = c.executar("h = det(g)").to_dict()
    assert d.get("erro")


@pytest.mark.parametrize("eq, sai", [
    (r"\nabla_\mu V^\mu = \frac{1}{\sqrt{-g}} \partial_\mu (\sqrt{-g} V^\mu)", True),
    (r"\nabla_\mu V^\mu = \frac{1}{-g} \partial_\mu (-g V^\mu)", False),
    (r"\Gamma^\beta{}_{\alpha\beta} = \partial_\alpha (\ln \sqrt{-g})", True),
    (r"\Gamma^\beta{}_{\alpha\beta} = \partial_\alpha (\ln (-g))", False),
    (r"\nabla_\mu \nabla^\mu \phi = \frac{1}{\sqrt{-g}} \partial_\mu"
     r" (\sqrt{-g} g^{\mu\nu} \partial_\nu \phi)", True),
    (r"\nabla_\mu \nabla^\mu \phi = \frac{1}{\sqrt{-g}} \partial_\mu"
     r" (\sqrt{-g} \partial^\mu \phi)", True),
])
def test_divergencias_com_raiz_de_g(eq, sai):
    assert (expandido(eq) == "True") is sai


def test_modulo_de_g_sem_assinatura():
    eq = r"\nabla_\mu V^\mu = \frac{1}{\sqrt{|g|}} \partial_\mu (\sqrt{|g|} V^\mu)"
    assert expandido(eq, metrica="g = métrica") == "True"


@pytest.mark.parametrize("simetria, sai", [(", antissimétrico", True), ("", False)])
def test_divergencia_de_antissimetrico(simetria, sai):
    eq = (r"\nabla_\mu F^{\mu\nu} = (-g)^{-1/2} \partial_\mu"
          r" (\sqrt{-g} F^{\mu\nu})")
    assert (expandido(eq, f"F = tensor(2,0{simetria})") == "True") is sai


# ------------------------------------------ ∂ e o índice levantado

IDENTIDADE = (r"u^j \partial_j u^i = \frac{1}{2} \partial^i (u_j u^j)"
              r" - \epsilon^{ijk} u_j \epsilon_{klm} \partial^l u^m")


@pytest.mark.parametrize("metrica, sai", [
    ("g = métrica(cartesiana)", True),
    ("g = métrica(+,+,+, constante)", True),
    ("g = métrica(euclidiana)", False),     # ∂g sobra: a carta não foi dita
])
def test_a_carta_cartesiana_e_declarada(metrica, sai):
    c = Caderno()
    for f in ("i, j, k, l, m = índices(3)", r"\delta = kronecker", metrica,
              r"\epsilon = levi-civita(tensor)", "u = tensor(1, 0)", IDENTIDADE):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    assert (resposta(c, "simplificar(eq1)") == "True") is sai


def test_derivar_indice_levantado_deriva_a_metrica():
    """∂_λ V_μ, com V declarado (1,0), é ∂_λ(g_{μν}V^ν)."""
    c = caderno(metrica="g = métrica")
    c.executar(r"\partial_\lambda V_\mu - g_{\mu\nu} \partial_\lambda V^\nu")
    assert "d_g" in resposta(c, "simplificar(eq1)")
