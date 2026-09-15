r"""Várias instruções numa célula só — Enter encadeia, Shift+Enter roda.

A regra tem um limite que é o ponto todo: só encadeia quando TODAS as linhas
são instrução reconhecida. Uma equação em LaTeX pode ocupar duas linhas, e
parti-la daria duas metades sem sentido no lugar de um erro — silêncio, que é
o que este programa existe para não produzir.
"""

import sympy as sp

from sucuri.caderno import Caderno

SCHWARZSCHILD = [
    r"x = coordenadas(t, r, \theta, \phi)",
    r"g = métrica(-(1 - \frac{2M}{r}), \frac{1}{1 - \frac{2M}{r}}, "
    r"r^2, r^2 \sin^2\theta)",
    r"\mu, \nu = índices",
    "A = tensor(1,0)",
    r"g_{\mu\nu} A^{\nu}",
]


def caderno(*linhas):
    c = Caderno()
    for fonte in linhas:
        c.executar(fonte)
    return c


def test_dois_comandos_na_mesma_celula():
    c = caderno(*SCHWARZSCHILD)
    d = c.executar("contrair(eq1)\navaliar(eq1)").to_dict()
    assert d["tipo"] == "encadeada"
    assert [p["fonte"] for p in d["partes"]] == ["contrair(eq1)", "avaliar(eq1)"]
    assert d["partes"][0]["exato"] == "A(-mu)"
    assert "4 componentes" in d["partes"][1]["rotulo"]


def test_declaracoes_encadeadas():
    d = Caderno().executar("a = símbolo\ne = euler").to_dict()
    assert len(d["partes"]) == 2
    assert "número de Euler" in d["partes"][1]["texto"]


def test_linhas_em_branco_no_meio_nao_atrapalham():
    d = Caderno().executar("a = símbolo\n\n\ne = euler").to_dict()
    assert len(d["partes"]) == 2


def test_uma_equacao_em_duas_linhas_continua_inteira():
    """O limite da regra: quebrar isto daria duas metades sem sentido."""
    d = Caderno().executar("x^2 +\n1").to_dict()
    assert d["tipo"] == "math"
    assert d["sympy"] == "x**2 + 1"


def test_o_erro_de_uma_linha_nao_esconde_as_outras():
    c = caderno(*SCHWARZSCHILD)
    d = c.executar("contrair(eq7)\ncontrair(eq1)").to_dict()
    assert "não conheço 'eq7'" in d["partes"][0]["erro"]
    assert d["partes"][1]["exato"] == "A(-mu)"


def test_uma_linha_so_continua_como_antes():
    d = Caderno().executar("x^2 + 1").to_dict()
    assert d["tipo"] == "math" and "partes" not in d


# ------------------------------------------------- o LaTeX que se copia

def test_a_tabela_leva_o_latex_junto():
    r"""`A__theta*r**2` é texto do SymPy; um documento precisa de `A^{\theta}`.

    Sem a barra, o TeX compõe t-h-e-t-a em romano no lugar de um teta.
    """
    c = caderno(*SCHWARZSCHILD)
    d = c.executar("avaliar(eq1)").to_dict()
    latex = dict((l[0], l[2]) for l in d["linhas"])
    assert latex[r"A_{\theta}"] == r"A^{\theta} r^{2}"
    assert r"\phi" in latex[r"A_{\phi}"]


def test_a_tabela_inteira_se_copia():
    c = caderno(*SCHWARZSCHILD)
    d = c.executar("avaliar(eq1)").to_dict()
    inteira = d["latex_tabela"]
    assert inteira.startswith(r"\begin{aligned}")
    assert inteira.count(r"\\") == 3          # quatro linhas, três quebras
    assert r"A_{\theta} &= A^{\theta} r^{2}" in inteira


def test_a_geometria_tambem():
    c = Caderno()
    c.executar(SCHWARZSCHILD[0])
    c.executar(SCHWARZSCHILD[1])
    d = c.executar("christoffel(g)").to_dict()
    assert r"\Gamma^{r}_{{\theta}{\theta}}" in d["latex_tabela"]
    # e a componente vai em LaTeX, não em texto de SymPy
    valores = dict((l[0], l[2]) for l in d["linhas"])
    assert "**" not in valores[r"\Gamma^{r}_{{\phi}{\phi}}"]
