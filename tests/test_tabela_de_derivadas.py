"""Os defeitos que uma tabela de derivadas de verdade revelou.

A tabela veio da Wikipédia, escrita por outra gente para outro fim — que é a
única forma honesta de testar um leitor de notação. Ela encontrou três erros
silenciosos em duas horas, dois deles do Sucuri. Cada um vira um teste aqui.

Ver exemplos/tabela-de-derivadas/AUDITORIA.md.
"""

import json
import pathlib
import sys

import pytest
import sympy as sp

import sucuri
from sucuri import NotacaoNaoReconhecida

TABELA = (pathlib.Path(__file__).parents[1] / "exemplos" / "tabela-de-derivadas")


def doc():
    d = sucuri.Document(independent_variable="x")
    d.function("f", "g", "h", "W", "F", "a", "b")
    d.variable("c", "r", "n", "k", "z")
    d.primes_are_derivatives(True)
    return d


x = sp.Symbol("x")
f, g, h = (sp.Function(n) for n in "fgh")


# ------------------------------------- defeito 1: o marcador vazava na saída

def test_linha_com_argumento_e_derivada_e_nao_marcador():
    """f'(x) saía como Z_{0}(x) — o marcador interno, na cara do usuário.

    O marcador é um símbolo; ' Z_{0} (x)' o parser lê como função aplicada, e
    a reposição, que procurava o símbolo, não casava. A notação mais comum de
    toda a tabela produzia lixo em silêncio.
    """
    assert doc().read("f'(x) = 1").to_sympy() == sp.Eq(sp.Derivative(f(x), x), 1)


def test_marcador_vazado_vira_erro_e_nao_resultado():
    """A rede de proteção: se algum dia vazar de novo, para."""
    e = doc().read("f'(x)")
    e._normalize = lambda: (" Z_{0} (x)", {}, set(), {})
    with pytest.raises(NotacaoNaoReconhecida, match="defeito do Sucuri"):
        e.to_sympy()


def test_linha_avaliada_em_outro_ponto_usa_subs():
    """f'(g(x)) é a derivada de f avaliada em g(x) — não é d/dx de f(g(x))."""
    lido = doc().read("f'(g(x))").to_sympy()
    assert lido.atoms(sp.Subs)
    assert lido != sp.Derivative(f(g(x)), x)
    # e a regra da cadeia, escrita com ela, fecha:
    cadeia = doc().read(r"h'(x) = f'(g(x))\cdot g'(x)").to_sympy()
    assert sp.simplify(cadeia.rhs - sp.Derivative(f(g(x)), x).doit()) == 0


# --------------------------- defeito 2: linha sobre grupo sumia com a equação

def test_linha_sobre_grupo_e_derivada_do_grupo():
    lido = doc().read("(f + g)' = f' + g'").to_sympy()
    assert lido.lhs == sp.Derivative(f(x) + g(x), x)
    assert sp.simplify(lido.lhs.doit() - lido.rhs) == 0


def test_linha_sobre_grupo_nao_perde_o_resto_da_equacao():
    """O SymPy sozinho devolve 'f + g' para "(f + g)' = a": engole a linha, o
    sinal de igual e o lado direito, sem dizer nada. É o pior desfecho possível
    e era o que o Sucuri repassava."""
    from sympy.parsing.latex import parse_latex
    assert parse_latex("(f + g)' = a") == sp.Symbol("f") + sp.Symbol("g")

    lido = doc().read("(f + g)' = a").to_sympy()
    assert isinstance(lido, sp.Equality)


def test_regra_do_quociente_com_left_right():
    lido = doc().read(r"\left(\frac{f}{g}\right)' = \frac{f'g - g'f}{g^2}").to_sympy()
    assert sp.simplify(lido.lhs.doit() - lido.rhs) == 0


def test_linha_escrita_como_expoente():
    assert (doc().read(r"h^{\prime}(x)").to_sympy()
            == doc().read("h'(x)").to_sympy())


# ----------------------- defeito 3: macro degradada a símbolo, sem aviso

@pytest.mark.parametrize("latex, macro", [
    (r"{1 \over x}", "over"),
    (r"\coth x", "coth"),
    (r"\operatorname{arccsc} x", "operatorname"),
])
def test_macro_degradada_e_recusada(latex, macro):
    """O parser do SymPy não avisa quando não entende: \\coth x vira o símbolo
    'coth' vezes x, e a conta segue com lixo. O Sucuri para."""
    with pytest.raises(NotacaoNaoReconhecida, match=macro):
        doc().read(latex).to_sympy()


def test_letra_grega_nao_e_degradacao():
    """A regra distingue macro degradada de macro que vira símbolo por direito."""
    lido = sucuri.parse(r"\varphi'' + \alpha\varphi = 0",
                        independent_variable="x", primes="derivative")
    assert lido.to_sympy() == sp.Eq(
        sp.Symbol("alpha") * sp.Function("varphi")(x)
        + sp.Derivative(sp.Function("varphi")(x), (x, 2)), 0)


# ------------------------------------------------- a tabela inteira, de novo

def _julgar():
    sys.path.insert(0, str(TABELA))
    import auditoria
    dados = json.loads((TABELA / "tabela.json").read_text(encoding="utf-8"))
    return [(auditoria.julgar(e)[0], e) for e in dados["entradas"]], auditoria


def test_a_tabela_inteira_continua_no_mesmo_lugar():
    """Trava a contagem da auditoria: melhorar é livre, piorar tem de doer."""
    vereditos, auditoria = _julgar()
    conta = {}
    for v, _ in vereditos:
        conta[v] = conta.get(v, 0) + 1

    assert conta.get(auditoria.LIDA_E_PROVADA, 0) >= 23
    assert conta.get(auditoria.LIDA_E_REFUTADA, 0) <= 2
    # as duas únicas leituras erradas restantes são a forma de OPERADOR
    # \frac{d^n}{dx^n}, que ainda não é sítio do Sucuri. Ver AUDITORIA.md.
    assert conta.get(auditoria.LIDA_ERRADO, 0) <= 2
    for veredito, entrada in vereditos:
        if veredito == auditoria.LIDA_ERRADO:
            assert r"\frac{d^n}" in entrada["esquerda"]


def test_nenhuma_entrada_da_tabela_vaza_marcador():
    """A garantia que interessa: nada do Sucuri aparece na saída do Sucuri."""
    vereditos, auditoria = _julgar()
    for _, entrada in vereditos:
        _, motivo, objeto = auditoria.julgar(entrada)
        assert "Z_{" not in (motivo or "")
        if objeto is not None:
            assert "Z_{" not in sp.sstr(objeto)
