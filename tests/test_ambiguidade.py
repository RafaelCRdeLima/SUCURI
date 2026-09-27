"""Os sítios ambíguos são localizados, não adivinhados.

Cada caso aqui é uma falha silenciosa medida no parser de LaTeX do SymPy, com
equações de trabalho real. O Sucuri não pode repetir nenhuma.
"""

import sympy as sp
import pytest

from sucuri import Document, Unresolved, find

RICCATI = r"\varphi'' + 3\varphi\varphi' + \varphi^3 = 4r\varphi + 2r'"


# ------------------------------------------------------------- detecção

def test_localiza_todas_as_linhas_da_riccati():
    """O SymPy apaga estas três linhas em silêncio."""
    a = find(RICCATI)
    assert [x.kind for x in a] == ["prime"] * 3
    assert [x.base for x in a] == ["varphi", "varphi", "r"]
    assert [x.detail["order"] for x in a] == [2, 1, 1]


def test_localiza_derivada_de_leibniz():
    a = find(r"\frac{d^2 y}{dx^2}")
    assert len(a) == 1 and a[0].kind == "leibniz"
    assert a[0].base == "y"
    # `partial` distingue d de ∂: a forma é a mesma, e o que o símbolo declara
    # é que há outras variáveis além daquela.
    assert a[0].detail == {"order": 2, "wrt": "x", "partial": False}


def test_localiza_justaposicao():
    a = find(r"E^2 - f\left(m^2 + 1\right)")
    assert len(a) == 1 and a[0].kind == "juxtaposition" and a[0].base == "f"


def test_nao_inventa_ambiguidade():
    """Expressão sem ambiguidade não pode gerar pergunta."""
    assert find(r"\frac{x^2+1}{x-1}") == []
    assert find(r"\sqrt{1+4\alpha}") == []


def test_ignora_comandos_do_latex():
    """\\frac e \\left não são símbolos do usuário."""
    assert not any(x.base in ("frac", "left", "right")
                   for x in find(r"\frac{a}{b}\left(c\right)"))


# ---------------------------------------------------------- a recusa

def test_recusa_sem_anotacao():
    """O comportamento central: pendência bloqueia a conversão."""
    e = Document().read(RICCATI)
    assert len(e.pending) == 3
    assert not e.resolved
    with pytest.raises(Unresolved) as exc:
        e.to_sympy()
    assert len(exc.value.pending) == 3


def test_a_recusa_vira_pergunta():
    """Em vez de expressão errada, o programa entrega perguntas."""
    q = Document().read(RICCATI).questions()
    assert len(q) == 3
    assert all("derivative" in s and "symbol" in s for s in q)


def test_derivada_exige_variavel_independente():
    """'Derivada' sem dizer em relação a quê é ambiguidade escondida."""
    with pytest.raises(ValueError):
        Document().primes_are_derivatives()


# ------------------------------------------------- leitura correta

def test_le_a_riccati_de_kovacic_corretamente():
    """O teste que define o programa.

    Esta é a equação do caso 2 de Kovacic, cuja leitura errada já custou um
    teorema falso. O SymPy devolve
        varphi^3 + (varphi + 3 varphi varphi) = 4 r varphi + 2 r'
    apagando as três linhas. O Sucuri tem de devolver a equação certa.
    """
    doc = Document(independent_variable='x').primes_are_derivatives()
    obtido = doc.read(RICCATI).to_sympy()

    x = sp.Symbol('x')
    phi, r = sp.Function('varphi')(x), sp.Function('r')(x)
    esperado = sp.Eq(sp.Derivative(phi, (x, 2)) + 3 * phi * sp.Derivative(phi, x)
                     + phi**3,
                     4 * r * phi + 2 * sp.Derivative(r, x))
    assert sp.simplify((obtido.lhs - obtido.rhs)
                       - (esperado.lhs - esperado.rhs)) == 0


def test_o_sympy_sozinho_erra_a_mesma_equacao():
    """Registra a falha que motiva o programa, para que não se esqueça dela."""
    from sympy.parsing.latex import parse_latex
    cru = parse_latex(RICCATI)
    assert not cru.atoms(sp.Derivative), "o SymPy não vê derivada nenhuma aqui"


def test_linha_como_simbolo_quando_assim_declarado():
    """A outra leitura também tem de estar disponível."""
    doc = Document().primes_are_derivatives(False)
    expr = doc.read(r"y' + 1").to_sympy()
    assert sp.Symbol("y'") in expr.free_symbols
    assert not expr.atoms(sp.Derivative)


def test_coerencia_entre_ocorrencias():
    """Se phi aparece derivada, todo phi da equação é a mesma função.

    Sem isto a mesma letra vira dois objetos distintos na mesma expressão —
    exatamente o erro silencioso que o programa existe para impedir.
    """
    doc = Document(independent_variable='x').primes_are_derivatives()
    expr = doc.read(r"\varphi' + \varphi").to_sympy()
    assert not any(s.name == 'varphi' for s in expr.free_symbols), \
        "não pode sobrar varphi como símbolo solto"


def test_justaposicao_como_produto_ou_aplicacao():
    src = r"f\left(x + 1\right)"
    prod = Document().variable('f').read(src).to_sympy()
    apl = Document().function('f').read(src).to_sympy()
    assert prod != apl
    assert sp.Symbol('f') in prod.free_symbols
    assert apl.atoms(sp.Function)


def test_leibniz_como_derivada():
    doc = Document(independent_variable='x').primes_are_derivatives()
    expr = doc.read(r"\frac{d^2 y}{dx^2}").to_sympy()
    assert expr.atoms(sp.Derivative), "não pode virar fração de símbolos d e dx"


# --------------------------------------------- estados de resolução

def test_distingue_anotacao_explicita_de_convencao():
    """Resolver por convenção não é o mesmo que resolver por anotação.

    A distinção veio da identidade visual, que reserva o âmbar para
    "ambiguidade resolvida por inferência". Uma convenção geral pode acertar
    nove sítios e errar o décimo: quem declarou que linha é derivada não olhou
    cada linha.
    """
    from sucuri import Resolution
    doc = Document(independent_variable='x').primes_are_derivatives()
    doc.annotate("prime", "r", "derivative", order=1)
    e = doc.read(RICCATI)

    como = {r.ambiguity.base + "'" * r.ambiguity.detail["order"]: r.how
            for r in e.resolutions}
    assert como["varphi''"] == Resolution.INFERRED
    assert como["varphi'"] == Resolution.INFERRED
    assert como["r'"] == Resolution.EXPLICIT

    assert len(e.inferred) == 2, "dois sítios pedem conferência"
    assert e.resolved, "mas a expressão funciona"


def test_pendente_nao_conta_como_inferido():
    """Sem convenção nenhuma, tudo é pendente e nada é âmbar."""
    from sucuri import Resolution
    e = Document().read(RICCATI)
    assert e.inferred == []
    assert all(r.how == Resolution.PENDING for r in e.resolutions)


def test_sem_ambiguidade_nao_gera_estado():
    e = Document().read(r"\frac{x^2+1}{x-1}")
    assert e.resolutions == [] and e.inferred == [] and e.resolved


# ------------------------------------------------------------- a barra

@pytest.mark.parametrize("latex, sitio", [
    (r"y = 1/2 (x+z)", "2"), (r"y = 1/2 x", "2"), (r"y = a/b (x+z)", "b"),
    (r"y = 1/(a+b) x", "(a+b)"), (r"y = x/\tau t", r"\tau"),
])
def test_a_barra_com_algo_colado_e_sitio(latex, sitio):
    """1/2 (x+z) o SymPy lê 1/(2(x+z)), calado: é pergunta."""
    assert [(a.kind, a.base) for a in find(latex)] == [("slash", sitio)]


@pytest.mark.parametrize("latex", [
    r"y = 1/2 \cdot (x+z)", r"y = \frac{1}{2} (x+z)", r"y = 3/4", r"y = 1/23",
    r"y = x^{1/2} z", r"y = e^{-t/\tau} x",
])
def test_a_barra_sem_duvida_nao_e_sitio(latex):
    assert not [a for a in find(latex) if a.kind == "slash"]


@pytest.mark.parametrize("leitura, esperado", [
    ("times", sp.Rational(1, 2) * (sp.Symbol("x") + sp.Symbol("z"))),
    ("denominator", 1 / (2 * (sp.Symbol("x") + sp.Symbol("z")))),
])
def test_as_duas_leituras_da_barra(leitura, esperado):
    doc = Document()
    doc.annotate("slash", "2", leitura)
    e = doc.read(r"y = 1/2 (x+z)")
    assert sp.simplify(e.to_sympy().rhs - esperado) == 0


def test_a_barra_sem_resposta_nao_vira_equacao():
    with pytest.raises(Unresolved):
        Document().read(r"y = 1/2 (x+z)").to_sympy()
