r"""A conexão sem índice: ∇_U X, [U,X] e R(U,X)W.

O parser lê `\nabla_U X` como `X*nabla_{U}` — produto, que comuta. Com isso
∇_U∇_X e ∇_X∇_U saem iguais e a curvatura some sem aviso. A declaração
`U = tensor(1,0)` é o que decide que o subscrito é direção, e não índice; entre
vetores, `[U,X]` só pode ser o colchete de Lie; e `R = curvatura` tira de R(U,X)W
a pergunta "R vezes o parêntese?".
"""

import pytest
import sympy as sp

import sucuri
from sucuri import ColcheteDeLie as L
from sucuri import Curvatura
from sucuri import DerivadaCovariante as D
from sucuri import ConexaoNaoLida, NotacaoNaoReconhecida
from sucuri.caderno import Caderno

U, X, Y, R = sp.symbols("U X Y R")


def documento():
    doc = sucuri.Document()
    doc.tensor("U", 1, 0)
    doc.tensor("X", 1, 0)
    doc.tensor("Y", 1, 0)
    doc.tensor(r"\omega", 0, 1)
    doc.index(r"\mu")
    doc.curvature("R")
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
    with pytest.raises((NotacaoNaoReconhecida, ConexaoNaoLida)):
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
    (r"\nabla_U X^\mu", "até onde ∇_U alcança"),
    (r"\nabla_U X_1", "até onde ∇_U alcança"),
    (r"\nabla_U", "sem operando"),
    (r"\nabla_U = 0", "sem operando"),
    (r"\nabla_U \nabla_V X", "'V' não foi declarado"),
])
def test_recusa_com_o_motivo(latex, trecho):
    with pytest.raises(ConexaoNaoLida, match=trecho):
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


# ------------------------------------------------------ o colchete de Lie

def test_o_parser_recusa_o_colchete():
    from sympy.parsing.latex import LaTeXParsingError, parse_latex
    with pytest.raises(LaTeXParsingError):
        parse_latex(r"[U,X]")


@pytest.mark.parametrize("latex, esperado", [
    (r"[U,X]", L(U, X)),
    (r"[U, X] = 0", sp.Eq(L(U, X), 0)),
    (r"[U, X + Y]", L(U, X + Y)),
    (r"[U, \nabla_U X]", L(U, D(U, X))),
    (r"\nabla_{[U,X]} Y", D(L(U, X), Y)),
    (r"\nabla_{U+X} Y", D(U + X, Y)),
])
def test_colchete_entre_vetores(latex, esperado):
    assert ler(latex) == esperado


def test_colchete_sem_virgula_continua_agrupamento():
    assert sp.expand(ler(r"[x+1]^2") - (sp.Symbol("x") + 1)**2) == 0


@pytest.mark.parametrize("latex, trecho", [
    (r"[a, b]", "'a' não foi declarado"),
    (r"[U, \omega]", r"do tipo \(0,1\)"),
    (r"[U, X, Y]", "3 entradas"),
    (r"\nabla_{[U,\omega]} X", r"do tipo \(0,1\)"),
])
def test_colchete_recusa(latex, trecho):
    with pytest.raises(ConexaoNaoLida, match=trecho):
        ler(latex)


# ---------------------------------------------------------- a curvatura

@pytest.mark.parametrize("latex, esperado", [
    (r"R(U,X)Y", Curvatura(R, U, X, Y)),
    (r"R(U, X)(Y + 2U)", Curvatura(R, U, X, Y + 2 * U)),
    (r"R(U,X)\nabla_U Y", Curvatura(R, U, X, D(U, Y))),
    (r"R(U,X)[U,Y]", Curvatura(R, U, X, L(U, Y))),
])
def test_curvatura_aplicada(latex, esperado):
    assert ler(latex) == esperado


def test_curvatura_declarada_nao_vira_pergunta():
    assert documento().read(r"R(U,X)Y").pending == []


def test_sem_declarar_continua_pergunta():
    doc = documento()
    doc._curvaturas.clear()
    assert [a.fragment for a in doc.read(r"R(U,X)Y").pending] == ["R("]


@pytest.mark.parametrize("latex, trecho", [
    (r"R(U,X)", "sem o vetor sobre o qual age"),
    (r"R(U,X) = 0", "sem o vetor sobre o qual age"),
    (r"R(U,X,Y)U", "aqui há 3"),
    (r"R(U,\omega)X", r"do tipo \(0,1\)"),
    (r"R(U,X)\omega", r"do tipo \(0,1\)"),
])
def test_curvatura_recusa(latex, trecho):
    with pytest.raises(ConexaoNaoLida, match=trecho):
        ler(latex)


def test_a_letra_dentro_de_macro_nao_e_curvatura():
    r"""O R de \Rightarrow não é a curvatura declarada."""
    from sucuri.conexao import localizar
    assert localizar(r"a \Rightarrow (b)", curvaturas=["R"]) == []


# ------------------------------------------- a dedução do desvio geodésico

DEDUCAO = [
    (r"[U,X] = 0", sp.Eq(L(U, X), 0)),
    (r"\nabla_U U = 0", sp.Eq(D(U, U), 0)),
    (r"\nabla_U X - \nabla_X U = [U,X]", sp.Eq(D(U, X) - D(X, U), L(U, X))),
    (r"R(U,X)U = \nabla_U \nabla_X U - \nabla_X \nabla_U U - \nabla_{[U,X]} U",
     sp.Eq(Curvatura(R, U, X, U),
           D(U, D(X, U)) - D(X, D(U, U)) - D(L(U, X), U))),
    (r"\nabla_U \nabla_U X = R(U,X)U", sp.Eq(D(U, D(U, X)), Curvatura(R, U, X, U))),
]


@pytest.mark.parametrize("latex, esperado", DEDUCAO, ids=[d[0][:30] for d in DEDUCAO])
def test_cada_linha_da_deducao_e_lida(latex, esperado):
    """A dedução inteira, linha a linha — ler é o que vem antes de provar."""
    assert ler(latex) == esperado


def test_volta_ao_latex_da_curvatura_e_do_colchete():
    assert sp.latex(ler(r"R(U,X)U")) == r"R\left(U, X\right) U"
    assert sp.latex(ler(r"[U,X]")) == r"\left[U, X\right]"


def test_a_arvore_do_colchete_e_da_curvatura():
    assert documento().read(r"[U,X]").tree().label == "colchete de Lie"
    assert documento().read(r"R(U,X)U").tree().label == "curvatura R aplicada"


def test_curvatura_no_caderno():
    c = Caderno()
    for fonte in ("U = tensor(1,0)", "X = tensor(1,0)", "R = curvatura"):
        c.executar(fonte)
    d = c.executar(r"\nabla_U \nabla_U X = R(U,X)U").to_dict()
    assert d["sympy"] == "Eq(nabla_U(nabla_U(X)), R(U, X)(U))"
