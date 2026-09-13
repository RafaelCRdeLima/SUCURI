"""A tabela de integrais: o que ela cobrou do leitor.

Uma tabela de integrais prova-se ao contrário: não se integra o lado esquerdo,
deriva-se o direito e compara-se com o integrando. Mais rápido, não depende do
integrador acertar, e a constante de integração morre na derivada.

A tabela cobrou três notações que a de derivadas não tinha cobrado — |x| com
\\left, a fração primitiva do TeX, e o 'e' de Euler — e uma pergunta que não
era pergunta. Ver exemplos/tabelas/AUDITORIA-INTEGRAIS.md.
"""

import json
import pathlib
import sys

import pytest
import sympy as sp

import sucuri
from sucuri import NotacaoNaoReconhecida

TABELA = pathlib.Path(__file__).parents[1] / "exemplos" / "tabelas"
x = sp.Symbol("x")


def doc():
    d = sucuri.Document(independent_variable="x")
    d.function("f", "g", "u", "v")
    d.variable("a", "b", "c", "n", "m", "C", "A", "B")
    d.primes_are_derivatives(True)
    d.e_is_euler(True)
    return d


def derivando(latex):
    """Confere a entrada pelo método da tabela: derivar o lado direito."""
    igualdade = doc().read(latex).to_sympy()
    integral = igualdade.lhs
    assert isinstance(integral, sp.Integral), sp.sstr(integral)
    (variavel,) = integral.limits[0]
    real = {s: sp.Symbol(s.name, real=True)
            for s in (sp.diff(igualdade.rhs, variavel)).free_symbols}
    return sp.simplify(
        (sp.diff(igualdade.rhs, variavel) - integral.function).subs(real))


# ----------------------------------------------- o 'e' de Euler é sítio

def test_e_sem_convencao_e_pergunta_e_nao_palpite():
    """Lido como símbolo, d/dx e^{ax} = a·e^{ax}·ln(e): a tabela inteira de
    exponenciais passa a ser refutada, em silêncio. É ambiguidade de verdade —
    'e' também é excentricidade e carga — e por isso vira pergunta."""
    e = sucuri.Document(independent_variable="x").read(r"\int e^{ax}\,dx")
    assert e.pending
    assert "Euler" in e.questions()[0]


def test_e_declarado_como_euler_fecha_a_exponencial():
    assert derivando(r"\int e^{ax}\,dx = \frac{1}{a}e^{ax} + C") == 0


def test_e_justaposto_tambem_e_sitio():
    """Em 'ae^{ax}' há um 'a' vezes um 'e' — justaposição em LaTeX é produto.
    O primeiro detector só pegava o 'e' isolado e deixava metade da equação
    com um símbolo onde a outra metade tinha o número."""
    lido = doc().read(r"e^{ax} = ae^{ax}").to_sympy()
    assert not lido.free_symbols & {sp.Symbol("e")}


def test_e_dentro_de_nome_nao_e_sitio():
    """\\sec tem um 'e', e v_e^2 também: nenhum dos dois é o 'e' de Euler."""
    assert doc().read(r"v_e^2 + \sec^2 x").to_sympy() == (
        sp.Symbol("v_{e}")**2 + sp.sec(x)**2)


# ------------------------------- notação que o parser do SymPy não conhece

def test_barras_com_left_e_right():
    """parse_latex lê |x| e recusa \\left|x\\right| — a mesma barra, escrita do
    jeito que toda tabela escreve."""
    from sympy.parsing.latex import parse_latex
    with pytest.raises(Exception):
        parse_latex(r"\ln\left|x\right|")
    # parse_latex devolve log(·, E), que vale log(·) mas não é o mesmo objeto
    assert sp.simplify(doc().read(r"\ln\left|x\right|").to_sympy()
                       - sp.log(sp.Abs(x))) == 0


def test_fracao_primitiva_do_tex():
    """{a \\over b} é \\frac{a}{b} desde o TeX; o parser do SymPy lia 'over'
    como um símbolo e seguia a conta com ele."""
    assert doc().read(r"{1 \over x}").to_sympy() == 1 / x
    diferenca = derivando(r"\int {1 \over x}\,dx = \ln \left|x \right| + C")
    # zero fora de x = 0, que é a condição que a tabela subentende
    assert diferenca.subs(sp.Symbol("x", real=True), sp.Rational(3, 2)) == 0


def test_over_nao_confunde_overline():
    from sucuri.document import _inofensivas
    assert _inofensivas(r"\overline{z}") == r"\overline{z}"


def test_log_com_base_deriva_certo():
    """parse_latex monta \\log_a x como um log de dois argumentos POR AVALIAR, e
    esse objeto deriva errado: d/dx log(x, a) devolve 1/x, sem o ln(a). A conta
    segue e o resultado é falso — mais um silêncio, e dos piores, porque o
    objeto parece perfeito."""
    from sympy.parsing.latex import parse_latex
    cru = parse_latex(r"\log_a x")
    assert sp.diff(cru, x) == 1 / x                     # errado, e calado

    lido = doc().read(r"\log_a x").to_sympy()
    a = sp.Symbol("a")
    assert sp.diff(lido, x) == 1 / (x * sp.log(a))      # certo
    assert derivando(r"\int \log_a x\,dx = x\log_a x - \frac{x}{\ln a} + C") == 0


# ------------------------------- pergunta que não era pergunta

def test_funcao_conhecida_nao_vira_pergunta():
    """'\\arctan(' não é 'arctan multiplicando o parêntese'. Pergunta que não é
    pergunta gasta a credibilidade das que são."""
    e = doc().read(r"\int \operatorname{sech} x \, dx = \arctan(\sinh x) + C")
    assert not [p for p in e.pending if p.base == "arctan"]


# ------------------------------------------------ entradas de verdade

@pytest.mark.parametrize("latex", [
    r"\int \sin x \, dx = -\cos x + C",
    r"\int \cos x\, dx = \sin x + C",
    r"\int x^n\,dx = \frac{x^{n+1}}{n+1} + C",
    r"\int a\,dx = ax + C",
    r"\int (ax + b)^n \, dx= \frac{(ax + b)^{n+1}}{a(n + 1)} + C",
    r"\int \sec^2 x \, dx = \tan x + C",
    r"\int \ln x\,dx = x \ln x - x + C",
    r"\int a^x\,dx = \frac{a^x}{\ln a} + C",
    r"\int \tan^2 x \, dx = \tan x - x + C",
])
def test_entradas_da_tabela(latex):
    assert derivando(latex) == 0


def test_entrada_com_linha_no_integrando():
    """∫f'(x)e^{f(x)}dx = e^{f(x)} + C junta os dois consertos: a linha com
    argumento, que vazava marcador, e o 'e' de Euler."""
    assert derivando(r"\int f'(x)e^{f(x)}\,dx = e^{f(x)} + C") == 0


# --------------------------------------------- a tabela inteira (indefinidas)

def _indefinidas():
    sys.path.insert(0, str(TABELA))
    import integrais
    dados = json.loads((TABELA / "integrais.json").read_text(encoding="utf-8"))
    entradas = [e for e in dados["entradas"] if r"\int_" not in e["esquerda"]]
    return [(integrais.julgar(e)[0], e) for e in entradas], integrais


def test_as_indefinidas_continuam_no_mesmo_lugar():
    """Trava a contagem: melhorar é livre, piorar tem de doer.

    Só as indefinidas — as definidas dependem de quadratura numérica e levam
    minutos, o que não cabe numa suíte.
    """
    vereditos, integrais = _indefinidas()
    conta = {}
    for v, _ in vereditos:
        conta[v] = conta.get(v, 0) + 1
    provadas = (conta.get(integrais.PROVADA, 0)
                + conta.get(integrais.PROVADA_QUASE, 0))
    assert provadas >= 33
    assert conta.get(integrais.LIDA_ERRADO, 0) == 0


def test_nenhuma_integral_vaza_marcador():
    vereditos, integrais = _indefinidas()
    for _, entrada in vereditos:
        _, motivo, objeto = integrais.julgar(entrada)
        assert "Z_{" not in (motivo or "")
        if objeto is not None:
            assert "Z_{" not in sp.sstr(objeto)
