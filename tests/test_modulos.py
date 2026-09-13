"""Módulos de domínio, e a ponte de proveniência entre eles.

O Sucuri lê e desambigua; o KORVIN decide não-integrabilidade. Nenhum sabe o
que o outro faz. O que atravessa a fronteira é a PROVENIÊNCIA: um veredito cujo
critério não tem autoridade chega ao Sucuri como não apresentável, e o
hospedeiro o mostra como dado em vez de conclusão — sem entender de Galois.
"""

import pytest

import sucuri
from sucuri.modules import Provenance, load, available

korvin = pytest.importorskip("korvin")


def airy():
    """A equação de Airy, escrita como um físico escreveria."""
    doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
    return doc.read(r"y'' = x y")


def modulo():
    return load("korvin")


# ------------------------------------------------------------ carga

def test_carrega_o_modulo():
    m = modulo()
    assert m.name == "korvin"
    assert set(m.operations) == {"esquema de Riemann", "condições de Kovacic",
                                 "não-integrabilidade"}
    assert "korvin" in available()


# ------------------------------------------------------- as operações

def test_esquema_de_riemann_e_dado_nao_conclusao():
    """Uma tabela de singularidades não afirma nada; é insumo."""
    r = modulo().operations["esquema de Riemann"].run(airy())
    assert r.provenance == Provenance.INAPPLICABLE
    assert not r.is_conclusion and r.presentable
    assert r.rows[0] == ("ponto", "ordem", "expoentes")
    assert ("∞", "-1", "—") in r.rows, "Airy: sem polos, o(inf) = -1"


def test_condicoes_de_kovacic_sao_conclusao_estabelecida():
    """Critério com fonte primária atravessa como conclusão."""
    r = modulo().operations["condições de Kovacic"].run(airy())
    assert r.provenance == Provenance.ESTABLISHED
    assert r.is_conclusion and r.presentable
    situacoes = {linha[0]: linha[1] for linha in r.rows[1:]}
    assert set(situacoes.values()) == {"falha"}, "as três falham no Airy"


def test_veredito_nao_atravessa_como_conclusao():
    """O TESTE QUE DEFINE A ARQUITETURA.

    O critério do caso 2 do KORVIN não tem proveniência declarada. O Sucuri,
    que não sabe o que é grupo de Galois, recusa-se a apresentar o veredito
    como conclusão — porque o módulo declarou de onde vem o que afirma.
    """
    r = modulo().operations["não-integrabilidade"].run(airy())
    assert r.provenance == Provenance.UNSOURCED
    assert r.is_conclusion
    assert not r.presentable, "não pode ser apresentado como conclusão"
    assert r.blocked_by, "e diz por quê"
    assert "proveniência" in r.blocked_by[0]


def test_resultado_serializa_para_a_interface():
    d = modulo().operations["não-integrabilidade"].run(airy()).to_dict()
    assert d["apresentavel"] is False
    assert d["proveniencia"] == Provenance.UNSOURCED
    assert d["bloqueado_por"]


# -------------------------------------------------- o módulo diz o que aceita

def test_recusa_entrada_fora_da_forma_esperada():
    """O módulo declara o que aceita, em vez de adivinhar a intenção."""
    doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
    op = modulo().operations["esquema de Riemann"]

    with pytest.raises(ValueError, match="igualdade"):
        op.run(doc.read(r"y' + x"))
    with pytest.raises(ValueError, match="ordem 2"):
        op.run(doc.read(r"y' = x y"))


def test_a_ambiguidade_bloqueia_antes_do_modulo():
    """Sem convenção, a expressão nem chega ao KORVIN."""
    e = sucuri.Document().read(r"y'' = x y")
    with pytest.raises(sucuri.Unresolved):
        modulo().operations["esquema de Riemann"].run(e)
