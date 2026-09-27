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
    assert livres(lido) == ["^lambda", "_mu", "_nu"]


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
    assert livres(lido.lhs) == ["^mu", "^nu"]


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


def test_derivada_com_indice_atravessa_como_objeto_proprio():
    """∂_μ A^ν não é um fator multiplicando outro: é um objeto próprio — e
    agora existe (derivadas.py). A divergência contrai como qualquer tensor."""
    e = doc().read(r"\partial_\mu A^\mu").to_sympy()
    assert sp.sstr(e) == "d_A(-L_0, L_0)"


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


def test_com_a_metrica_declarada_a_nota_some():
    """Declarada a métrica, A_ν é A com o índice baixado por ela: não há o que
    avisar."""
    c = Caderno()
    for f in (r"\mu, \nu = índices", "g = métrica", "A = tensor(1, 0)"):
        c.executar(f)
    assert not c.executar(r"A_\nu").to_dict().get("notas")


def test_sem_metrica_simplificar_nao_sobe_nem_desce_indice():
    """A^ν B_ν = A_ν B^ν só vale com métrica; sem ela, a canonização não pode
    trocar as posições dos mudos."""
    for decl, zera in (([], False), (["g = métrica"], True)):
        c = Caderno()
        for f in (r"\mu, \nu = índices", *decl, "A = tensor(1,0)", "B = tensor(0,1)",
                  r"A^\nu B_\nu - A_\nu B^\nu"):
            c.executar(f)
        assert (c.executar("simplificar(eq1)").to_dict().get("exato") == "0") is zera


def test_o_tipo_no_caderno():
    c = Caderno()
    c.executar(r"\mu, \nu = índices")
    d = c.executar("g = tensor(0, 2)").to_dict()
    assert d["tipo"] == "declaracao"
    assert d["declarado"][0]["tipo"] == [0, 2]
    assert "recebe 0 1-formas e 2 vetores" in d["texto"]

    lido = c.executar(r"g_{\mu\nu}").to_dict()
    assert lido["indices_livres"] == [r"_\mu", r"_\nu"]
    assert lido["notas"] == []

    trocado = c.executar(r"g^{\mu\nu}").to_dict()
    assert any("tipo (0,2)" in n for n in trocado["notas"])


def test_so_numero_literal_no_tipo():
    """`A = tensor(m, n)` com m e n definidos antes faria do caderno uma
    linguagem de programação — a porta que os verbos fechados existem para não
    abrir. Quem escrever isso recebe a leitura normal, não uma declaração."""
    c = Caderno()
    assert c.executar("A = tensor(m, n)").to_dict()["tipo"] != "declaracao"


# ---------------------------------------------- o que a tela mostra

def test_o_indice_mudo_volta_a_ser_o_que_a_pessoa_escreveu():
    r"""O SymPy renomeia todo índice contraído para L_0 — e faz certo: índice
    mudo é nome ligado. Mas quem escreveu \nu quer ver \nu.

    E há um estrago junto: o impressor emite os índices colados, então
    g{}_{\mu L_{0}} sai "\muL_{0}" — a macro \mu engole o L e vira \muL, que
    não existe. O KaTeX pinta de vermelho, e a equação PARECE errada quando o
    que está errado é a impressão dela.
    """
    from sucuri.interface.sessao import Sessao

    s = Sessao()
    s.indices = [r"\mu", r"\nu"]
    s.tensores = {"g": (0, 2)}
    d = s.ler(r"g_{\mu \nu} A^{\nu}")

    assert d["latex_semantico"] == r"g{}_{\mu\nu}A{}^{\nu}"
    assert "L_" not in d["latex_semantico"]
    assert r"\muL" not in d["latex_semantico"]


def test_a_valencia_sai_como_se_escreve():
    """'-mu' é nome interno, e mostrar nome interno faz o usuário procurar o
    que ele mesmo escreveu."""
    from sucuri.interface.sessao import Sessao

    s = Sessao()
    s.indices = [r"\mu", r"\nu", r"\lambda"]
    assert s.ler(r"T^{\mu\nu}_{\lambda}")["indices_livres"] == [
        r"^\mu", r"^\nu", r"_\lambda"]


def test_contrair_o_resultado_de_contrair():
    c = Caderno()
    for f in (r"\mu, \nu = índices", "g = métrica", "A = tensor(1,0)", r"g_{\mu\nu} A^\nu", "contrair(eq1)"):
        c.executar(f)
    d = c.executar("contrair(eq2)").to_dict()
    assert "não há índice para baixar" in d["erro"]
