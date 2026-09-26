r"""A conexão com índice: `\nabla = levi-civita` e `R = riemann(eq1)`.

∇g = 0 e torção nula são o que distingue Levi-Civita de uma conexão qualquer
— declaração, e não suposição. E o Riemann vem na convenção que a definição
escrita diz: o sinal e a ordem dos slots variam de livro para livro, e o
Sucuri lê a identidade em vez de escolher uma.
"""

import pytest

from sucuri.caderno import Caderno

CARROLL = (r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
           r" = R^\rho{}_{\sigma\mu\nu} V^\sigma")


def caderno(*fontes):
    c = Caderno()
    for f in (r"\mu, \nu, \rho, \sigma, \lambda, \alpha, \beta = índices",
              "g = métrica", r"\delta = kronecker", "V = tensor(1,0)",
              "W = tensor(0,1)", "T = tensor(1,1)", *fontes):
        d = c.executar(f).to_dict()
        assert not d.get("erro"), (f, d.get("erro"))
    return c


def simplificado(c, latex):
    nome = c.executar(latex).to_dict()["nome"]
    return c.executar(f"simplificar({nome})").to_dict()["exato"]


def com_riemann(definicao=CARROLL):
    c = caderno(r"\nabla = levi-civita", definicao)
    d = c.executar("R = riemann(eq1)").to_dict()
    assert not d.get("erro"), d.get("erro")
    return c


# ------------------------------------------------------ o {} entre índices

def test_o_vazio_entre_indices_nao_come_o_resto():
    r"""R^\rho{}_{\sigma\mu\nu} V^\sigma era lido como R(rho): três índices e o
    V sumiam, sem aviso."""
    d = caderno().executar(r"R^\rho{}_{\sigma\mu\nu} V^\sigma").to_dict()
    assert d["sympy"] == "R(rho, -L_0, -mu, -nu)*V(L_0)"


# ------------------------------------------------------------ Levi-Civita

def test_nabla_g_so_zera_com_levi_civita():
    c = caderno()
    assert simplificado(c, r"\nabla_\lambda g_{\mu\nu}") != "0"
    c = caderno(r"\nabla = levi-civita")
    assert simplificado(c, r"\nabla_\lambda g_{\mu\nu}") == "0"
    assert simplificado(c, r"\nabla_\lambda g^{\mu\nu}") == "0"
    assert simplificado(c, r"\partial_\lambda g_{\mu\nu}") != "0"   # ∂g não


def test_derivada_da_delta_e_zero_sempre():
    c = caderno()
    assert simplificado(c, r"\nabla_\mu \delta^\nu_\rho") == "0"
    assert simplificado(c, r"\partial_\mu \delta^\nu_\rho") == "0"


def test_torcao_nula_num_escalar():
    latex = r"\nabla_\mu \nabla_\nu \phi - \nabla_\nu \nabla_\mu \phi"
    assert simplificado(caderno(), latex) != "0"
    assert simplificado(caderno(r"\nabla = levi-civita"), latex) == "0"


def test_nabla_epsilon_tensor_zera():
    c = caderno(r"\nabla = levi-civita", r"\epsilon = levi-civita(tensor)")
    assert simplificado(c, r"\nabla_\lambda \epsilon_{\mu\nu\rho\sigma}") == "0"


# ------------------------------------------------------------------ Ricci

@pytest.mark.parametrize("latex, esperado", [
    (r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho",
     "R(rho, L_0, -mu, -nu)*V(-L_0)"),
    (r"\nabla_\mu \nabla_\nu W_\rho - \nabla_\nu \nabla_\mu W_\rho",
     "-R(L_0, -rho, -mu, -nu)*W(-L_0)"),
    (r"\nabla_\mu \nabla_\nu T^\alpha{}_\beta - \nabla_\nu \nabla_\mu T^\alpha{}_\beta",
     "R(alpha, L_0, -mu, -nu)*T(-L_0, -beta) - R(L_0, -beta, -mu, -nu)*T(alpha, -L_0)"),
    (r"\nabla_\mu \nabla_\nu V^\rho", "DD_V(-mu, -nu, rho)"),     # sai como entrou
])
def test_identidade_de_ricci(latex, esperado):
    assert simplificado(com_riemann(), latex) == esperado


def test_com_o_sinal_trocado_a_curvatura_troca():
    menos = CARROLL.replace("= R", "= -R")
    c = com_riemann(menos)
    assert simplificado(
        c, r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho") == \
        "-R(rho, L_0, -mu, -nu)*V(-L_0)"


def test_na_ordem_de_wald():
    wald = (r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho"
            r" = R_{\mu\nu\sigma}{}^\rho V^\sigma")
    c = com_riemann(wald)
    assert simplificado(
        c, r"\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho") == \
        "R(-mu, -nu, L_0, rho)*V(-L_0)"


def test_riemann_pede_levi_civita():
    c = caderno(CARROLL)
    assert "levi-civita" in c.executar("R = riemann(eq1)").to_dict()["erro"]


def test_definicao_mal_formada():
    c = caderno(r"\nabla = levi-civita", r"R^\rho{}_{\sigma\mu\nu} V^\sigma = 0")
    assert "a definição tem de ter a forma" in \
        c.executar("R = riemann(eq1)").to_dict()["erro"]


def test_operando_com_indice_nao_declarado_recusa():
    c = Caderno()
    for f in (r"\mu, \nu, \alpha = índices", "T = tensor(1,1)"):
        c.executar(f)
    assert c.executar(r"\nabla_\mu \nabla_\nu T^\alpha{}_\beta").to_dict()["erro"]
