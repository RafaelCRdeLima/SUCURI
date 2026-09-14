r"""A ponte até os tensores do SymPy.

O parser de LaTeX não tem notação de índice, e o que ele faz com ela é o pior
possível: A^\mu vira A**mu, x^2_i perde o índice. Mas o SymPy TEM tensores, com
contração automática — o que faltava era a ponte, e quem a abre é a declaração:

    \mu = índice

Declarado o índice, A^\mu deixa de ser ambíguo: não há potência possível com um
índice no expoente.
"""

import pytest
import sympy as sp

import sucuri
from sucuri import NotacaoTensorial
from sucuri.caderno import Caderno
from sucuri.tensores import IndicesIncompativeis, livres


def doc():
    d = sucuri.Document()
    d.index(r"\mu", r"\nu", r"\lambda", r"\sigma", r"\rho")
    return d


def test_a_contracao_acontece():
    """g_{μν}A^μA^ν tem todos os índices contraídos: nenhum livre."""
    lido = doc().read(r"g_{\mu\nu} A^\mu A^\nu").to_sympy()
    from sympy.tensor.tensor import TensExpr
    assert isinstance(lido, TensExpr)
    assert livres(lido) == []


def test_a_valencia_do_que_sobra():
    lido = doc().read(r"\Gamma^\lambda_{\mu\nu}").to_sympy()
    assert livres(lido) == ["lambda", "-mu", "-nu"]


def test_o_marcador_precisa_de_reconstrucao_e_nao_de_subs():
    """`subs` devolveria um Mul comum, e a contração não aconteceria — os
    índices repetidos ficariam parados e a expressão sairia errada sem
    reclamar. Este teste prende o comportamento certo."""
    from sympy.tensor.tensor import TensMul
    lido = doc().read(r"A^\mu B_\mu").to_sympy()
    assert isinstance(lido, TensMul)
    assert livres(lido) == []


def test_igualdade_e_coeficiente():
    lido = doc().read(r"T^{\mu\nu} = 8\pi S^{\mu\nu}").to_sympy()
    assert isinstance(lido, sp.Equality)
    assert livres(lido.lhs) == ["mu", "nu"]


def test_soma_com_indices_livres_diferentes_e_erro():
    """A^μB_μ + C^ν não é equação incompleta: é equação errada, e o erro é de
    relatividade, não de digitação. A olho ninguém vê."""
    with pytest.raises(IndicesIncompativeis, match="mesma valência"):
        doc().read(r"A^\mu B_\mu + C^\nu").to_sympy()


def test_o_posto_vem_do_uso_e_tem_de_ser_um_so():
    d = doc()
    d.read(r"g_{\mu\nu}").to_sympy()
    with pytest.raises(ValueError, match="posto"):
        d.read(r"g^\mu").to_sympy()


def test_sem_declarar_indice_continua_recusando():
    """A recusa existe para o silêncio, e declarar acaba com o silêncio — mas
    quem não declarou continua protegido."""
    with pytest.raises(NotacaoTensorial):
        sucuri.Document().read(r"g_{\mu\nu} A^\mu A^\nu").to_sympy()


def test_derivada_com_indice_ainda_nao_atravessa():
    """∂_μ A^ν não é um fator multiplicando outro: é um objeto próprio. Montar
    um produto aqui pareceria certo, e é por isso que a recusa existe."""
    with pytest.raises(NotacaoTensorial, match="derivada com índice"):
        doc().read(r"\partial_\mu A^\mu").to_sympy()


def test_o_que_nao_e_indice_continua_expoente():
    d = doc()
    assert d.read("x^2").to_sympy() == sp.Symbol("x")**2


# ------------------------------------------------------------- no caderno

def test_declarar_indices_no_caderno():
    c = Caderno()
    d = c.executar(r"\mu, \nu = índices").to_dict()
    assert d["tipo"] == "declaracao"
    assert "dimensão 4" in d["texto"]

    lido = c.executar(r"g_{\mu\nu} A^\mu A^\nu").to_dict()
    assert lido["nome"] == "eq1"
    assert lido["indices_livres"] == []


def test_a_dimensao_e_declaravel():
    c = Caderno()
    assert "dimensão 3" in c.executar(r"\alpha = índice(3)").to_dict()["texto"]
