r"""Formas diferenciais: d, ∧, ι_X e ℒ_X, sem índice.

A leitura segue a regra de sempre — decide a declaração: `d` só é operador
sobre forma declarada, `\mathrm{d}` sempre; `df` com f função continua d
vezes f. O motor sabe sem hipótese o que vale em qualquer livro (d² = 0,
Leibniz graduado, comutatividade graduada, ι antiderivação, Cartan); a
fórmula de dω nos vetores muda de fator com a normalização, e entra como
hipótese.
"""

import pytest
import sympy as sp

from sucuri.caderno import Caderno


def caderno(*fontes):
    c = Caderno()
    for f in (r"\omega = forma(1)", r"\alpha = forma(1)", r"\eta = forma(2)",
              "X = tensor(1,0)", "Y = tensor(1,0)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def lido(latex):
    return caderno().executar(latex).to_dict()


def provado(objetivo, *hipoteses):
    c = caderno()
    nome = c.executar(objetivo).to_dict()["nome"]
    nomes = [c.executar(h).to_dict()["nome"] for h in hipoteses]
    return c.executar(f"provar({', '.join([nome] + nomes)})").to_dict()


# ------------------------------------------------------------- a leitura

@pytest.mark.parametrize("latex, esperado", [
    (r"d\omega", "d(omega)"),
    (r"\mathrm{d}\omega", "d(omega)"),
    (r"\omega \wedge \alpha", "omega ^ alpha"),
    (r"\omega \land \alpha", "omega ^ alpha"),
    (r"\iota_X \eta", "iota_X(eta)"),
    (r"\mathcal{L}_X \omega", "L_X(omega)"),
    (r"\mathrm{d} f", "d(f)"),
])
def test_leitura(latex, esperado):
    assert lido(latex)["sympy"] == esperado


@pytest.mark.parametrize("latex", [r"d f", r"d x"])
def test_d_sem_forma_nao_e_operador(latex):
    """f e x não são formas: `d f` continua lido como antes, e não d(f)."""
    antes = Caderno().executar(latex).to_dict()["sympy"]
    assert lido(latex)["sympy"] == antes != "d(f)"


def test_d_de_uma_avaliacao_leva_parenteses():
    r"""d(ω(X)) impresso sem parênteses se leria (dω)(X)."""
    assert lido(r"\mathrm{d}(\omega(X))")["latex_semantico"] == \
        r"\mathrm{d}\left(\omega\left(X\right)\right)"


def test_zero_forma_nao_se_declara():
    assert "função" in Caderno().executar(r"f = forma(0)").to_dict()["erro"]


def test_iota_pede_vetor():
    """ι com subscrito que não é vetor declarado não é lido como ι."""
    assert lido(r"\iota_Z \omega")["sympy"] != "iota_Z(omega)"


# -------------------------------------------- o que vale sem hipótese

@pytest.mark.parametrize("latex", [
    r"\mathrm{d}\mathrm{d}\omega = 0",
    r"\omega \wedge \omega = 0",
    r"\omega \wedge \alpha = -\alpha \wedge \omega",
    r"\omega \wedge \eta = \eta \wedge \omega",
    r"\mathrm{d}(\omega \wedge \eta) = \mathrm{d}\omega \wedge \eta - \omega \wedge \mathrm{d}\eta",
    r"\iota_X (\omega \wedge \alpha) = \omega(X) \alpha - \alpha(X) \omega",
    r"\iota_X \mathrm{d} f = \nabla_X f",
    r"\iota_X \iota_X \eta = 0",
    r"\iota_Y \iota_X \eta = -\iota_X \iota_Y \eta",
    r"\iota_Y \iota_X \eta = \eta(X, Y)",
    r"\mathcal{L}_X \omega = \iota_X \mathrm{d}\omega + \mathrm{d}(\omega(X))",
    r"\mathcal{L}_X \mathrm{d}\omega = \mathrm{d} \mathcal{L}_X \omega",
    r"\mathcal{L}_X (\omega \wedge \alpha) = \mathcal{L}_X \omega \wedge \alpha + \omega \wedge \mathcal{L}_X \alpha",
    r"\mathcal{L}_X f = \nabla_X f",
    r"\mathrm{d}(f g) = g \mathrm{d} f + f \mathrm{d} g",
])
def test_vale_sem_hipotese(latex):
    d = provado(latex)
    assert not d.get("erro"), d.get("erro")


@pytest.mark.parametrize("latex", [
    r"\eta \wedge \eta = 0",                                   # grau par
    r"\mathrm{d}(f \omega) = \mathrm{d} f \wedge \omega",      # falta dω = 0
    r"\omega \wedge \alpha = \alpha \wedge \omega",
])
def test_o_que_nao_vale_nao_passa(latex):
    assert "Não achar" in provado(latex)["erro"]


# ------------------------------------------------------- com hipótese

def test_forma_fechada():
    d = provado(r"\mathrm{d}(f \omega) = \mathrm{d} f \wedge \omega",
                r"\mathrm{d}\omega = 0")
    assert [l[0] for l in d["linhas"]][0].startswith("f·")


def test_formula_de_d_nos_vetores_como_hipotese():
    formula = (r"\forall A, B: \iota_B \iota_A \mathrm{d}\omega = "
               r"\nabla_A (\omega(B)) - \nabla_B (\omega(A)) - \omega([A,B])")
    alvo = r"\nabla_X (\omega(Y)) - \nabla_Y (\omega(X)) = \omega([X,Y])"
    d = provado(alvo, formula, r"\mathrm{d}\omega = 0")
    rotulos = [l[0] for l in d["linhas"]]
    assert any("[A→X, B→Y]" in r for r in rotulos)
    assert any(r.startswith("iota_Y(iota_X(") for r in rotulos)
    assert "Não achar" in provado(alvo, formula)["erro"]


def test_simplificar_da_a_forma_normal():
    c = caderno()
    nome = c.executar(r"\omega \wedge \alpha + \alpha \wedge \omega").to_dict()["nome"]
    assert c.executar(f"simplificar({nome})").to_dict()["exato"] == "0"
