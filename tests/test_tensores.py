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


# --------------------------------------------- o tipo do Schutz: (M, N)

def test_declarar_o_tipo_diz_o_posto_antes_do_uso():
    """Um tensor do tipo (M/N) é uma função de M 1-formas e N vetores, o que em
    índices dá M em cima e N embaixo. Declarar isso diz o posto ANTES da
    primeira aparição — o uso sozinho dizia depois."""
    d = doc()
    d.tensor("g", 0, 2)
    with pytest.raises(ValueError, match=r"tipo \(0,2\)"):
        d.read(r"g_{\mu\nu\lambda}").to_sympy()


def test_a_valencia_certa_nao_gera_nota():
    from sucuri.tensores import desacordo_de_tipo

    d = doc()
    d.tensor("T", 1, 1)
    d.read(r"T^\mu_\nu").to_sympy()
    assert desacordo_de_tipo(d.espaco, "T", [("mu", True), ("nu", False)]) is None


def test_valencia_diferente_da_declarada_e_nota_e_nao_erro():
    """g^{μν} tendo declarado g do tipo (0,2) é a métrica INVERSA: não é erro,
    é outro tensor. Mas levantar índice exige métrica, e o Sucuri não a aplica
    sozinho — então vale dizer."""
    from sucuri.tensores import desacordo_de_tipo

    d = doc()
    d.tensor("g", 0, 2)
    d.read(r"g^{\mu\nu}").to_sympy()            # não levanta erro
    aviso = desacordo_de_tipo(d.espaco, "g", [("mu", True), ("nu", True)])
    assert "levantar ou baixar índice exige a métrica" in aviso


def test_o_tipo_no_caderno():
    c = Caderno()
    c.executar(r"\mu, \nu = índices")
    d = c.executar("g = tensor(0, 2)").to_dict()
    assert d["tipo"] == "declaracao"
    assert d["declarado"][0]["tipo"] == [0, 2]
    assert "recebe 0 1-formas e 2 vetores" in d["texto"]

    lido = c.executar(r"g_{\mu\nu}").to_dict()
    assert lido["indices_livres"] == ["-mu", "-nu"]
    assert lido["notas"] == []

    trocado = c.executar(r"g^{\mu\nu}").to_dict()
    assert any("tipo (0,2)" in n for n in trocado["notas"])


def test_so_numero_literal_no_tipo():
    """`A = tensor(m, n)` com m e n definidos antes faria do caderno uma
    linguagem de programação — a porta que os verbos fechados existem para não
    abrir. Quem escrever isso recebe a leitura normal, não uma declaração."""
    c = Caderno()
    assert c.executar("A = tensor(m, n)").to_dict()["tipo"] != "declaracao"
