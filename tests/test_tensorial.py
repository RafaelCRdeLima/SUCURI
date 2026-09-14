"""Índice não é expoente, e o parser do SymPy não sabe a diferença.

    A^\\mu                    ->  A**mu            (A elevado a μ)
    x^2_i                     ->  x**2             (o índice some)
    \\Gamma^\\lambda_{\\mu\\nu}  ->  Gamma**lambda_{mu*nu}
    g_{\\mu\\nu}                ->  Symbol('g_{mu*nu}')

Nada disso levanta erro e nada disso tem símbolo estranho na saída: são
expressões bem formadas e FALSAS, que é a pior classe de erro que este programa
conhece — quem escreve relatividade receberia contas silenciosamente erradas.
"""

import pytest
import sympy as sp

import sucuri
from sucuri import NotacaoTensorial
from sucuri.interface.sessao import Sessao


def ler(latex):
    return sucuri.Document().read(latex).to_sympy()


# ------------------------------------------------- o que o parser perde

def test_o_parser_realmente_perde():
    """O que a recusa evita, medido — se um dia isto mudar, o teste avisa."""
    from sympy.parsing.latex import parse_latex

    assert parse_latex(r"A^\mu") == sp.Symbol("A")**sp.Symbol("mu")
    assert parse_latex(r"x^2_i") == sp.Symbol("x")**2        # o índice sumiu
    assert parse_latex(r"x_i^2") == sp.Symbol("x_{i}")**2    # esta ordem vai bem


@pytest.mark.parametrize("latex", [
    r"\Gamma^\lambda_{\mu\nu}",          # sobrescrito antes do subscrito
    r"R^\rho_{\sigma\mu\nu}",
    r"x^2_i",
    r"g_{\mu\nu} A^\mu A^\nu",           # o mesmo índice em cima e embaixo
])
def test_recusa_onde_o_parser_perde(latex):
    with pytest.raises(NotacaoTensorial):
        ler(latex)


@pytest.mark.parametrize("latex", [
    "x^2", r"\alpha^2 + \beta^2", r"x_i^2", r"y^{\prime\prime}",
    r"\sum_{n=1}^\infty \frac{1}{n^2}", r"\int_0^1 x^2\,dx",
])
def test_nao_recusa_matematica_comum(latex):
    """A recusa é estreita de propósito: \\sum_{n=1}^\\infty tem sobrescrito e
    subscrito, e não é tensor; x_i^2 é legítimo e o parser lê direito."""
    d = sucuri.Document(independent_variable="x")
    d.primes_are_derivatives(True)
    d.read(latex).to_sympy()


# ------------------------------------------------------------- a suspeita

def test_grego_no_expoente_vira_nota_e_nao_recusa():
    """A^\\mu é mesmo "A elevado a μ" em algum texto. Distinguir índice de
    expoente pela tipografia é impossível, então a suspeita avisa e não
    bloqueia."""
    d = Sessao().ler(r"A^\mu")
    assert d["sympy"] == "A**mu"
    assert any("grega no expoente" in n for n in d["notas"])


def test_indice_em_subscrito_vira_nota():
    """T_{\\mu\\nu} e T_{\\nu\\mu} viram o MESMO símbolo, porque o índice entra
    no nome. Para um tensor simétrico dá certo por acaso; para os outros, não.
    """
    d = Sessao().ler(r"R_{\mu\nu} = 8\pi T_{\mu\nu}")
    assert d["sympy"] is not None
    assert any("parte do NOME" in n for n in d["notas"])


def test_a_mensagem_diz_onde_ha_tensor_no_sympy():
    with pytest.raises(NotacaoTensorial, match="sympy.tensor.tensor"):
        ler(r"g_{\mu\nu} A^\mu A^\nu")
