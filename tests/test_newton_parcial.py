"""Ponto de Newton e derivada parcial — a notação da mecânica hamiltoniana.

O ponto é o caso mais grave medido no parser do SymPy: `\\dot{x}` vira o produto
do símbolo "dot" pelo símbolo x. Como toda a mecânica hamiltoniana se escreve
com pontos, isso inviabilizaria o domínio inteiro do programa.
"""

import sympy as sp
import pytest

import sucuri
from sucuri import Document, Unresolved, Resolution, find


# ------------------------------------------------------------- detecção

def test_localiza_ponto_simples_e_duplo():
    assert [(a.kind, a.base, a.detail["order"]) for a in find(r"\dot{x}")] \
        == [("newton", "x", 1)]
    assert [(a.kind, a.base, a.detail["order"]) for a in find(r"\ddot{q}")] \
        == [("newton", "q", 2)]


def test_localiza_ponto_sobre_grego_e_sem_chaves():
    assert find(r"\dot{\varphi}")[0].base == "varphi"
    assert find(r"\dot x")[0].base == "x"


def test_localiza_dois_pontos_seguidos():
    """O SymPy lê isto como dot*q*dot*p."""
    a = find(r"\dot{q}\dot{p}")
    assert [x.base for x in a] == ["q", "p"]


def test_localiza_parcial_com_indice():
    a = find(r"\partial_p H")
    assert len(a) == 1
    assert a[0].kind == "partial" and a[0].base == "H"
    assert a[0].detail["wrt"] == "p"


# ------------------------------------------------------ a falha do SymPy

def test_o_sympy_transforma_o_ponto_em_produto():
    """Registra a falha, para que ela não seja esquecida."""
    from sympy.parsing.latex import parse_latex
    e = parse_latex(r"\dot{x}")
    assert sp.Symbol('dot') in e.free_symbols, "o 'dot' virou símbolo"
    assert not e.atoms(sp.Derivative)


# ------------------------------------------------------------- leitura

def test_recusa_ponto_sem_convencao():
    e = Document().read(r"\ddot{q} + \omega^2 q = 0")
    assert len(e.pending) == 1
    with pytest.raises(Unresolved):
        e.to_sympy()


def test_ponto_exige_variavel_temporal():
    """Pelo mesmo motivo que a linha exige a independente."""
    with pytest.raises(ValueError):
        Document().dots_are_time_derivatives()


def test_le_o_oscilador_corretamente():
    doc = Document(time_variable='t').dots_are_time_derivatives()
    obtido = doc.read(r"\ddot{q} + \omega^2 q = 0").to_sympy()

    t = sp.Symbol('t')
    q, w = sp.Function('q')(t), sp.Symbol('omega')
    esperado = sp.Eq(sp.Derivative(q, (t, 2)) + w**2 * q, 0)
    assert sp.simplify((obtido.lhs - obtido.rhs)
                       - (esperado.lhs - esperado.rhs)) == 0


def test_le_as_equacoes_de_hamilton():
    """O par que define o domínio do programa."""
    doc = Document(time_variable='t').dots_are_time_derivatives()
    t, p, q = sp.symbols('t p q')

    e1 = doc.read(r"\dot{q} = \partial_p H").to_sympy()
    assert e1.lhs == sp.Derivative(sp.Function('q')(t), t)
    assert e1.rhs == sp.Derivative(sp.Function('H')(p), p)

    e2 = doc.read(r"\dot{p} = -\partial_q H").to_sympy()
    assert e2.rhs == -sp.Derivative(sp.Function('H')(q), q)


def test_ponto_como_decoracao_quando_declarado():
    doc = Document().dots_are_time_derivatives(False)
    e = doc.read(r"\dot{x} + 1").to_sympy()
    assert e == sp.Symbol('x') + 1
    assert not e.atoms(sp.Derivative)


def test_tempo_e_independente_sao_separados():
    """d/dt do ponto não se confunde com d/dx da linha.

    Em mecânica a variável independente da linha raramente é o tempo, e tratar
    as duas como uma só produziria equação errada em silêncio.
    """
    doc = (Document(independent_variable='x', time_variable='t')
           .primes_are_derivatives().dots_are_time_derivatives())
    e = doc.read(r"\dot{q} + y'").to_sympy()
    variaveis = {v for d in e.atoms(sp.Derivative) for v, _ in d.variable_count}
    assert variaveis == {sp.Symbol('t'), sp.Symbol('x')}


def test_ponto_aparece_como_inferido_na_arvore():
    doc = Document(time_variable='t').dots_are_time_derivatives()
    t = doc.read(r"\ddot{q} + \omega^2 q = 0").tree()
    marcados = [n for n in t.walk() if n.needs_review]
    assert len(marcados) == 1
    assert "derivada de ordem 2 de q em t" == marcados[0].label


def test_anotar_o_ponto_sem_variavel_temporal_recusa_com_recado():
    """O caminho da convenção já cobrava a variável; o da anotação de sítio,
    não — e por ali saía um Derivative(q(None), (None, 1)), que estoura muito
    depois com uma mensagem que não diz nada a quem escreveu a equação. Achado
    clicando na interface, que é onde se anota sítio."""
    import pytest
    import sucuri

    doc = sucuri.Document()
    doc.annotate("newton", "q", "derivative", order=1)
    with pytest.raises(ValueError, match="variável temporal"):
        doc.read(r"\dot{q} + q = 0").to_sympy()

    doc = sucuri.Document()
    doc.annotate("prime", "y", "derivative", order=2)
    with pytest.raises(ValueError, match="variável independente"):
        doc.read("y'' = 0").to_sympy()


def test_derivar_a_propria_variavel_independente_recusa():
    """x' = A e^x com x declarado independente é quase sempre engano de quem
    escreve: o x ali é a função incógnita e a variável é outra, t. Sem a
    recusa, o leitor montava Subs(Derivative(x(x), x), x, x(x)) — bem formado,
    sem sentido — e o dsolve seguia em frente com aquilo.

    Achado por alguém usando o programa, não pela suíte.
    """
    import pytest
    import sucuri

    doc = sucuri.Document(independent_variable="x").primes_are_derivatives(True)
    doc.e_is_euler(True)
    with pytest.raises(ValueError, match="variável independente do documento"):
        doc.read(r"x^{\prime} = A e^{x}").to_sympy()

    # com a variável certa, lê sem reclamar
    import sympy as sp
    doc = sucuri.Document(independent_variable="t").primes_are_derivatives(True)
    doc.e_is_euler(True)
    t, A = sp.Symbol("t"), sp.Symbol("A")
    x = sp.Function("x")
    assert doc.read(r"x^{\prime} = A e^{x}").to_sympy() == sp.Eq(
        sp.Derivative(x(t), t), A * sp.exp(x(t)))


def test_derivar_a_propria_variavel_temporal_recusa():
    import pytest
    import sucuri

    doc = sucuri.Document(time_variable="t").dots_are_time_derivatives(True)
    with pytest.raises(ValueError, match="variável temporal do documento"):
        doc.read(r"\dot{t} = 1").to_sympy()


# ------------------------------------------- mais de uma variável independente

def test_a_mesma_funcao_nao_vira_duas_funcoes_diferentes():
    """∂u/∂t = k ∂u/∂x tem UM u, função de duas variáveis.

    Antes cada sítio promovia o símbolo à sua própria função, e o mesmo u saía
    como u(t) de um lado e u(x) do outro — duas funções com o mesmo nome na
    mesma equação, em silêncio. É a mesma falha que a linha teve um dia, agora
    com várias variáveis.
    """
    import sympy as sp
    import sucuri

    doc = sucuri.Document(independent_variable="x")
    doc.function("u")
    lido = doc.read(r"\partial_t u = k \partial_x u").to_sympy()

    u = sp.Function("u")(sp.Symbol("t"), sp.Symbol("x"))
    assert lido == sp.Eq(sp.Derivative(u, sp.Symbol("t")),
                         sp.Symbol("k") * sp.Derivative(u, sp.Symbol("x")))
    assert len({f.func for f in lido.atoms(sp.core.function.AppliedUndef)}) == 1


def test_a_notacao_de_leibniz_aceita_o_partial():
    """∂u/∂t é como se escreve toda equação a derivadas parciais, e o parser do
    SymPy degrada a segunda ordem dela: \\frac{\\partial^2 u}{\\partial x^2} vira
    (partial**2*u)/(partial*x**2), com 'partial' virando símbolo."""
    import sympy as sp
    import sucuri

    doc = sucuri.Document(independent_variable="x")
    doc.function("u")
    lido = doc.read(r"\frac{\partial u}{\partial t} = k \frac{\partial^2 u}{\partial x^2}").to_sympy()

    t, x, k = sp.symbols("t x k")
    u = sp.Function("u")(t, x)
    assert lido == sp.Eq(sp.Derivative(u, t), k * sp.Derivative(u, (x, 2)))


def test_o_sitio_de_partial_diz_que_e_parcial():
    from sucuri.ambiguity import find
    (sitio,) = find(r"\frac{\partial u}{\partial t}")
    assert sitio.detail["partial"] is True
    assert "parcial" in sitio.readings[0].description

    (sitio,) = find(r"\frac{dy}{dx}")
    assert sitio.detail["partial"] is False
    assert "parcial" not in sitio.readings[0].description


def test_a_linha_continua_admitindo_uma_variavel_so():
    """f' com duas variáveis não diria em relação a qual — e é justamente essa
    ambiguidade que o programa recusa. Uma variável independente por documento
    não é limitação: é o que a notação da linha comporta."""
    import sympy as sp
    import sucuri

    doc = sucuri.Document(independent_variable="x").primes_are_derivatives(True)
    y = sp.Function("y")(sp.Symbol("x"))
    assert doc.read("y'' + y = 0").to_sympy() == sp.Eq(
        y + sp.Derivative(y, (sp.Symbol("x"), 2)), 0)
