r"""O que a tabela imprime, o caderno sabe procurar.

`A_{t}` aparece na tela com nome e valor. Não poder pedi-lo de volta é pedir
que se redigite o que o programa acabou de calcular — e, pior, a versão antiga
não recusava: `avaliar(A_{t})` caía no leitor de LaTeX e virava "avaliar vezes
(A_t)", com uma pergunta sobre `r(` — o `r` de "contrair". Bem formada e
absurda, que é a pior classe de resposta que este programa pode dar.
"""

import sympy as sp

from sucuri.caderno import Caderno

SCHWARZSCHILD = [
    r"x = coordenadas(t, r, \theta, \phi)",
    r"g = métrica(-(1 - \frac{2M}{r}), \frac{1}{1 - \frac{2M}{r}}, "
    r"r^2, r^2 \sin^2\theta)",
]
COM_VETOR = SCHWARZSCHILD + [
    r"\mu, \nu = índices", "A = tensor(1,0)", r"g_{\mu\nu} A^{\nu}",
    "avaliar(eq1)",
]


def caderno(*linhas):
    c = Caderno()
    for fonte in linhas:
        c.executar(fonte)
    return c


def test_o_rotulo_da_tabela_e_um_alvo():
    c = caderno(*COM_VETOR)
    d = c.executar(r"avaliar(A_{t})").to_dict()
    M, r = sp.symbols("M r")
    esperado = -(1 - 2 * M / r) * sp.Symbol("A__t")
    assert sp.simplify(sp.sympify(d["exato"]) - esperado) == 0


def test_a_chave_ignora_o_que_e_tipografia():
    """`A_{t}` e `A_t` são o mesmo rótulo: chave é do TeX, não do objeto."""
    c = caderno(*COM_VETOR)
    assert (c.executar(r"avaliar(A_t)").to_dict()["exato"]
            == c.executar(r"avaliar(A_{t})").to_dict()["exato"])


def test_rotulo_com_barra():
    r"""`\Gamma^{r}_{tt}` — e sem exigir as chaves duplas que a tela usa."""
    c = caderno(*SCHWARZSCHILD, "christoffel(g)")
    d = c.executar(r"avaliar(\Gamma^{r}_{tt})").to_dict()
    M, r = sp.symbols("M r")
    assert sp.simplify(sp.sympify(d["exato"])
                       - M * (r - 2 * M) / r**3) == 0


def test_a_componente_nula_existe_e_vale_zero():
    """Ela não entra na tabela — 55 zeros escondem as nove que importam —,
    mas responder 'não conheço' a quem a pede seria mentir."""
    c = caderno(*SCHWARZSCHILD, "christoffel(g)")
    assert c.executar(r"avaliar(\Gamma^{t}_{rr})").to_dict()["exato"] == "0"


def test_rotulo_que_nao_existe_recusa_e_diz_o_que_tem():
    c = caderno(*SCHWARZSCHILD, "christoffel(g)")
    erro = c.executar(r"avaliar(\Gamma^{q}_{tt})").to_dict()["erro"]
    assert "não conheço" in erro and "rótulos da última tabela" in erro


def test_a_tabela_anterior_sai_de_cena():
    """Dois christoffel de métricas diferentes dariam o mesmo rótulo, e
    devolver o de antes seria responder a outra pergunta.

    Trocada a carta, `\\Gamma^{r}_{tt}` deixa de existir — não há coordenada r
    em (t,x,y,z) —, e a recusa é a forma certa de dizer isso."""
    c = caderno(*SCHWARZSCHILD, "christoffel(g)")
    assert c.executar(r"avaliar(\Gamma^{r}_{tt})").to_dict()["exato"]
    c.executar(r"x = coordenadas(t, x, y, z)")
    c.executar(r"\eta = métrica(-1, 1, 1, 1)")
    c.executar(r"christoffel(\eta)")
    assert "não conheço" in c.executar(r"avaliar(\Gamma^{r}_{tt})").to_dict()["erro"]
    assert c.executar(r"avaliar(\Gamma^{x}_{tt})").to_dict()["exato"] == "0"


# --------------------------------------------- o que quebrava antes disto

def test_avaliar_o_que_um_verbo_produziu():
    """`eq2` vindo de separar é objeto, não texto: não há LaTeX para reler.

    A versão que tentava reler estourava KeyError na cara de quem pedisse.
    """
    c = caderno(r"u = u(t,x)",
                r"\frac{\partial u}{\partial t} = \frac{\partial^2 u}{\partial x^2}",
                "separar(eq1)")
    d = c.executar("avaliar(eq2)").to_dict()
    assert not d.get("erro")
    assert "Derivative" in d["exato"]


def test_avaliar_um_tensor_ja_contraido():
    r"""`A_\mu` contraído é o mesmo A com o índice descido — e quem desce é a
    métrica, que aqui está em componentes."""
    c = caderno(*SCHWARZSCHILD, r"\mu, \nu = índices", "A = tensor(1,0)",
                r"g_{\mu\nu} A^{\nu}", "contrair(eq1)")
    escrita = c.executar("avaliar(eq1)").to_dict()["linhas"]
    contraida = c.executar("avaliar(eq2)").to_dict()
    assert not contraida.get("erro")
    assert contraida["linhas"] == escrita


def test_a_componente_de_christoffel_e_simbolo_de_verdade():
    r"""O campo escalar do diffgeom imprime `r` em texto e `\mathbf{r}` em
    LaTeX: a componente parecia certa na tela e saía errada no que se copiava.
    """
    c = caderno(*SCHWARZSCHILD)
    d = c.executar("christoffel(g)").to_dict()
    assert "mathbf" not in d["latex_tabela"]
    valor = sp.sympify(dict((l[0], l[1]) for l in d["linhas"])[
        r"\Gamma^{r}_{{\theta}{\theta}}"])
    assert valor.free_symbols == {sp.Symbol("M"), sp.Symbol("r")}
