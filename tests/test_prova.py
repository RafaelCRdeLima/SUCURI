r"""O motor de prova: igualdades da conexão, a partir de hipóteses declaradas.

A prova é um certificado — cada passo diz de que hipótese veio e que contexto
se aplicou, e a soma é conferida de novo antes de dizer "provado". Só entra o
que foi nomeado na chamada: escrever uma equação no caderno não é afirmá-la.
"""

import pytest
import sympy as sp

import sucuri
from sucuri.caderno import Caderno
from sucuri.prova import NaoEVetorial, SemProva, linear, provar

U, X, Y, R = sp.symbols("U X Y R")
TENSORES = {"U": (1, 0), "X": (1, 0), "Y": (1, 0), "omega": (0, 1)}


def documento():
    doc = sucuri.Document()
    for n in ("U", "X", "Y"):
        doc.tensor(n, 1, 0)
    doc.tensor(r"\omega", 0, 1)
    doc.curvature("R")
    return doc


def ler(latex):
    return documento().read(latex).to_sympy()


def prova(objetivo, *hipoteses):
    return provar(ler(objetivo),
                  {f"h{i + 1}": ler(h) for i, h in enumerate(hipoteses)},
                  TENSORES)


# ------------------------------------------------------------ linearidade

@pytest.mark.parametrize("latex", [
    r"\nabla_U (X + Y) = \nabla_U X + \nabla_U Y",
    r"\nabla_{U + X} Y = \nabla_U Y + \nabla_X Y",
    r"\nabla_{2U} X = 2 \nabla_U X",
    r"\nabla_{f U} X = f \nabla_U X",          # linear sobre funções na direção
    r"[U, X] = -[X, U]",
    r"[U, U] = 0",
    r"[U, X + Y] = [U, X] + [U, Y]",
    r"R(U + X, Y)U = R(U, Y)U + R(X, Y)U",
    r"R(U, X)(f Y) = f R(U, X)Y",              # R é tensor
])
def test_o_que_vale_para_qualquer_conexao(latex):
    assert prova(latex).passos == []


@pytest.mark.parametrize("latex", [
    r"\nabla_U (f X) = f \nabla_U X",          # falta U(f) X: Leibniz
    r"[f U, X] = f [U, X]",                    # o colchete não é tensor
    r"R(U, X)Y = -R(X, U)Y",                   # antissimetria: depende de R
    r"\nabla_U X = \nabla_X U",                # torção nula não é de graça
])
def test_o_que_nao_vale_sem_hipotese(latex):
    with pytest.raises(SemProva):
        prova(latex)


def test_so_campos_vetoriais():
    with pytest.raises(NaoEVetorial):
        linear(sp.Symbol("omega"), TENSORES)


# ------------------------------------------------------------- com hipóteses

def test_congruencia_aplica_o_contexto():
    """De ∇_U X = ∇_X U sai ∇_Y∇_U X = ∇_Y∇_X U — aplicando ∇_Y aos dois lados."""
    p = prova(r"\nabla_Y \nabla_U X = \nabla_Y \nabla_X U",
              r"\nabla_U X = \nabla_X U")
    assert [d.rotulo() for _, d in p.passos] == ["nabla_Y(h1)"]


def test_hipotese_com_coeficiente_funcao_nao_passa_por_nabla():
    """∇_Y(fX) ≠ f∇_Y X: relação com coeficiente não constante não entra."""
    with pytest.raises(SemProva):
        prova(r"\nabla_Y (f X) = \nabla_Y (f U)", r"f X = f U")


DESVIO = [
    r"[U,X] = 0",
    r"\nabla_U U = 0",
    r"\nabla_U X - \nabla_X U = [U,X]",
    r"R(U,X)U = \nabla_U \nabla_X U - \nabla_X \nabla_U U - \nabla_{[U,X]} U",
]


def test_equacao_do_desvio_geodesico():
    p = prova(r"\nabla_U \nabla_U X = R(U,X)U", *DESVIO)
    rotulos = sorted(d.rotulo() for _, d in p.passos)
    assert rotulos == sorted(["h4", "nabla_U(h1)", "nabla_{h1}(U)",
                              "nabla_X(h2)", "nabla_U(h3)"])
    assert sorted(p.hipoteses_usadas) == ["h1", "h2", "h3", "h4"]


def test_sem_a_definicao_de_R_nao_prova():
    """O sinal de R é convenção: sem a definição declarada, nada sobre R."""
    with pytest.raises(SemProva, match="R\\(U, X\\)\\(U\\)"):
        prova(r"\nabla_U \nabla_U X = R(U,X)U", *DESVIO[:3])


def test_com_o_sinal_trocado_nao_prova():
    """Convenção oposta na definição: a igualdade vira falsa, e não passa."""
    oposta = r"R(U,X)U = \nabla_X \nabla_U U - \nabla_U \nabla_X U + \nabla_{[U,X]} U"
    with pytest.raises(SemProva):
        prova(r"\nabla_U \nabla_U X = R(U,X)U", *DESVIO[:3], oposta)
    p = prova(r"\nabla_U \nabla_U X = -R(U,X)U", *DESVIO[:3], oposta)
    assert "h4" in p.hipoteses_usadas


def test_sem_geodesica_nao_prova():
    with pytest.raises(SemProva):
        prova(r"\nabla_U \nabla_U X = R(U,X)U",
              DESVIO[0], DESVIO[2], DESVIO[3])


# ------------------------------------------------------------- no caderno

def caderno_do_desvio():
    c = Caderno()
    for fonte in ("U = tensor(1,0)", "X = tensor(1,0)", "R = curvatura",
                  *DESVIO, r"\nabla_U \nabla_U X = R(U,X)U"):
        c.executar(fonte)
    return c


def test_provar_no_caderno():
    d = caderno_do_desvio().executar("provar(eq5, eq1, eq2, eq3, eq4)").to_dict()
    assert "erro" not in d or not d["erro"]
    assert d["linhas"][-2][0] == "somando"
    assert "blacksquare" in d["linhas"][-2][2]
    assert "provado a partir de" in d["texto"]


def test_provar_diz_o_que_nao_usou():
    c = caderno_do_desvio()
    c.executar(r"\nabla_X X = 0")
    d = c.executar("provar(eq5, eq1, eq2, eq3, eq4, eq6)").to_dict()
    assert "não precisou de eq6" in d["texto"]


def test_provar_recusa_circulo():
    d = caderno_do_desvio().executar("provar(eq5, eq5)").to_dict()
    assert "próprias hipóteses" in d["erro"]


def test_provar_so_com_o_que_foi_nomeado():
    """eq1…eq4 estão no caderno, mas não foram nomeadas: não entram."""
    d = caderno_do_desvio().executar("provar(eq5)").to_dict()
    assert "Não achar não é prova de que é falso" in d["erro"]


def test_provar_encadeia_como_instrucao():
    from sucuri.caderno import _e_instrucao
    assert _e_instrucao("provar(eq5, eq1, eq2)")


# ---------------------------------------------------------------- para todo

DEFINICAO_R = (r"\forall A, B, W: R(A,B)W = \nabla_A \nabla_B W"
               r" - \nabla_B \nabla_A W - \nabla_{[A,B]} W")
TORCAO_NULA = r"\forall A, B: \nabla_A B - \nabla_B A = [A,B]"


def test_forall_e_lido_como_para_todo():
    e = ler(TORCAO_NULA)
    assert isinstance(e, sucuri.ParaTodo)
    assert e.variaveis == sp.symbols("A B")


def test_a_variavel_ligada_nao_vaza():
    doc = documento()
    doc.read(TORCAO_NULA).to_sympy()
    with pytest.raises(sucuri.ConexaoNaoLida, match="'A' não foi declarado"):
        doc.read(r"\nabla_A B").to_sympy()


@pytest.mark.parametrize("latex", [
    r"\forall A, B \quad \nabla_A B = \nabla_B A",
    r"\forall A, B \colon \nabla_A B = \nabla_B A",
    r"\forall A, B \; \nabla_A B = \nabla_B A",
])
def test_separadores_do_forall(latex):
    assert isinstance(ler(latex), sucuri.ParaTodo)


@pytest.mark.parametrize("latex, trecho", [
    (r"\forall A, \nabla_A U = 0", "sem separador"),
    (r"\forall \omega: \nabla_U \omega = 0", r"do tipo \(0,1\)"),
])
def test_forall_recusa(latex, trecho):
    with pytest.raises(sucuri.ConexaoNaoLida, match=trecho):
        ler(latex)


def test_forall_volta_ao_latex():
    assert sp.latex(ler(r"\forall A: \nabla_A A = 0")) == \
        r"\forall A:\; \nabla_{A} A = 0"


def test_desvio_geodesico_com_definicoes_gerais():
    """A definição de R e a torção nula ditas UMA vez, para todo vetor."""
    p = prova(r"\nabla_U \nabla_U X = R(U,X)U", DEFINICAO_R, TORCAO_NULA,
              r"[U,X] = 0", r"\nabla_U U = 0")
    rotulos = sorted(d.rotulo() for _, d in p.passos)
    assert rotulos == sorted(["h1[A→U, B→X, W→U]", "nabla_U(h2[A→U, B→X])",
                              "nabla_U(h3)", "nabla_{h3}(U)", "nabla_X(h4)"])
    assert p.hipoteses_usadas == ["h1", "h2", "h3", "h4"]


def test_antissimetria_de_R_sai_da_definicao():
    """Sem hipótese não passava; com a definição geral, sai."""
    p = prova(r"\forall A, B, W: R(A,B)W = -R(B,A)W", DEFINICAO_R)
    assert sorted(d.rotulo() for _, d in p.passos) == ["h1", "h1[A→B, B→A]"]


def test_objetivo_com_forall_sem_hipotese_sobre_ele():
    with pytest.raises(SemProva):
        prova(r"\forall A, B, W: R(A,B)W = -R(B,A)W")


def test_forall_nao_instancia_o_que_nao_aparece():
    """A torção nula geral não prova nada sobre R."""
    with pytest.raises(SemProva, match="R\\(U, X\\)\\(U\\)"):
        prova(r"\nabla_U \nabla_U X = R(U,X)U", TORCAO_NULA,
              r"[U,X] = 0", r"\nabla_U U = 0")


def test_identidade_de_bianchi_algebrica():
    r"""R(A,B)C + R(B,C)A + R(C,A)B = 0, da definição e da torção nula.

    Precisa também da identidade de Jacobi do colchete, que é hipótese: o
    motor não a sabe sozinho.
    """
    jacobi = r"\forall A, B, C: [A,[B,C]] + [B,[C,A]] + [C,[A,B]] = 0"
    p = prova(r"R(U,X)Y + R(X,Y)U + R(Y,U)X = 0",
              DEFINICAO_R, TORCAO_NULA, jacobi)
    assert "h1" in p.hipoteses_usadas and "h2" in p.hipoteses_usadas
