r"""Uma segunda conexão, \tilde\nabla: só as regras de toda conexão (Reall §3.1)."""

import pytest

from sucuri.caderno import Caderno

V = ["X = tensor(1, 0)", "Y = tensor(1, 0)", "Z = tensor(1, 0)"]


def ultimo(*fontes):
    c = Caderno()
    d = {}
    for f in fontes:
        d = c.executar(f).to_dict()
    return d


def test_a_diferenca_e_tensor():
    d = ultimo(*V, r"\nabla_{f X + Z} (h Y) - \tilde\nabla_{f X + Z} (h Y) = "
               r"f h \cdot (\nabla_X Y - \tilde\nabla_X Y) + h \cdot (\nabla_Z Y - \tilde\nabla_Z Y)",
               "provar(eq1)")
    assert d["texto"].startswith("provado")


@pytest.mark.parametrize("acento", [r"\tilde", r"\hat", r"\bar", r"\widetilde"])
def test_as_duas_nao_se_confundem(acento):
    d = ultimo(*V, rf"\nabla_X Y = {acento}{{\nabla}}_X Y", "provar(eq1)")
    assert d.get("erro")


def test_cada_uma_tem_o_seu_leibniz():
    d = ultimo(*V, r"\tilde\nabla_X (h Y) = h \tilde\nabla_X Y + \nabla_X h \cdot Y", "provar(eq1)")
    assert d["texto"].startswith("provado")


def test_a_leitura_guarda_o_acento():
    assert ultimo(*V, r"\hat\nabla_X Y")["sympy"] == "hat_nabla_X(Y)"
