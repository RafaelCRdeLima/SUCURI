r"""A derivada covariante sem índice: ∇_U X.

O parser lê `\nabla_U X` como `X*nabla_{U}` — produto, que comuta. Com isso
∇_U∇_X e ∇_X∇_U saem iguais e a curvatura some sem aviso. A declaração
`U = tensor(1,0)` é o que decide que o subscrito é direção, e não índice.
"""

import pytest
import sympy as sp

import sucuri
from sucuri import DerivadaCovariante as D
from sucuri import DerivadaCovarianteNaoLida, NotacaoNaoReconhecida
from sucuri.caderno import Caderno

U, X, Y = sp.symbols("U X Y")


def documento():
    doc = sucuri.Document()
    doc.tensor("U", 1, 0)
    doc.tensor("X", 1, 0)
    doc.tensor("Y", 1, 0)
    doc.tensor(r"\omega", 0, 1)
    doc.index(r"\mu")
    return doc


def ler(latex):
    return documento().read(latex).to_sympy()


def test_o_parser_realmente_le_produto():
    """O que a leitura evita, medido — se um dia mudar, o teste avisa."""
    from sympy.parsing.latex import parse_latex
    lido = parse_latex(r"\nabla_U X")
    assert isinstance(lido, sp.Mul)                     # produto, que comuta
    assert {s.name for s in lido.free_symbols} == {"nabla_{U}", "X"}


def test_sem_declaracao_a_macro_degradada_e_recusada():
    with pytest.raises((NotacaoNaoReconhecida, DerivadaCovarianteNaoLida)):
        sucuri.Document().read(r"\nabla_U X").to_sympy()


def test_macro_com_subscrito_nao_passa_mais_calada():
    r"""\coth_x virava o símbolo coth_{x}, e a conferência só via o nome inteiro."""
    with pytest.raises(NotacaoNaoReconhecida):
        sucuri.Document().read(r"\coth_x y").to_sympy()


def test_grego_com_subscrito_continua_sendo_simbolo():
    assert sucuri.Document().read(r"\alpha_{1} + x").to_sympy() == (
        sp.Symbol("alpha_{1}") + sp.Symbol("x"))


@pytest.mark.parametrize("latex, esperado", [
    (r"\nabla_U X", D(U, X)),
    (r"\nabla_{U} X", D(U, X)),
    (r"\nabla_U \nabla_U X", D(U, D(U, X))),
    (r"\nabla_U (X + Y)", D(U, X + Y)),
    (r"\nabla_U \left(X + Y\right)", D(U, X + Y)),
    (r"2\nabla_U X + Y", 2 * D(U, X) + Y),
    (r"\nabla_U X = 0", sp.Eq(D(U, X), 0)),
])
def test_leitura_direcional(latex, esperado):
    assert ler(latex) == esperado


def test_a_ordem_de_aplicacao_nao_comuta():
    """O ponto de tudo: ∇_U∇_X ≠ ∇_X∇_U, e a diferença não pode sumir."""
    e = ler(r"\nabla_U \nabla_X Y - \nabla_X \nabla_U Y")
    assert sp.simplify(e) != 0


def test_o_subscrito_nao_vira_pergunta_de_justaposicao():
    """Em \\nabla_U (X+Y) o U não é função nem fator — é o subscrito."""
    assert documento().read(r"\nabla_U (X + Y)").pending == []


@pytest.mark.parametrize("latex, trecho", [
    (r"\nabla_V X", "'V' não foi declarado"),
    (r"\nabla_\omega X", r"do tipo \(0,1\)"),
    (r"\nabla_U X^\mu", "até onde ∇ alcança"),
    (r"\nabla_U X_1", "até onde ∇ alcança"),
    (r"\nabla_U", "sem operando"),
    (r"\nabla_U \nabla_V X", "'V' não foi declarado"),
])
def test_recusa_com_o_motivo(latex, trecho):
    with pytest.raises(DerivadaCovarianteNaoLida, match=trecho):
        ler(latex)


def test_derivada_com_indice_continua_recusada():
    with pytest.raises(sucuri.NotacaoTensorial):
        documento().read(r"\nabla_\mu A^\mu").to_sympy()


def test_volta_ao_latex():
    assert sp.latex(ler(r"\nabla_U \nabla_U X")) == r"\nabla_{U} \nabla_{U} X"
    assert sp.latex(ler(r"\nabla_U (X + Y)")) == r"\nabla_{U} \left(X + Y\right)"


def test_a_arvore_diz_o_que_e():
    arvore = documento().read(r"\nabla_U X").tree()
    assert arvore.label == "derivada covariante na direção de U"


def test_no_caderno():
    c = Caderno()
    c.executar("U = tensor(1,0)")
    c.executar("X = tensor(1,0)")
    d = c.executar(r"\nabla_U \nabla_U X").to_dict()
    assert d["sympy"] == "nabla_U(nabla_U(X))"
