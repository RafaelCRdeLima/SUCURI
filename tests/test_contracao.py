r"""Baixar e levantar índice — a convenção da métrica, aplicada de fato.

`A_\mu \equiv g_{\mu\nu}A^\nu` é uma CONVENÇÃO, e vale só para a métrica.
Nenhuma inspeção de `g_{\mu\nu}A^\nu` distingue a métrica de um tensor (0,2)
com nome infeliz — por isso a declaração, e por isso a recusa sem ela.

E há dois pedidos diferentes aqui, que o programa mantém separados:
`contrair` dá a ESTRUTURA (A_\mu), `avaliar` dá o VALOR (as componentes).
"""

import pytest
import sympy as sp

from sucuri.caderno import Caderno

SCHWARZSCHILD = [
    r"x = coordenadas(t, r, \theta, \phi)",
    r"g = métrica(-(1 - \frac{2M}{r}), \frac{1}{1 - \frac{2M}{r}}, "
    r"r^2, r^2 \sin^2\theta)",
]


def caderno(*linhas):
    c = Caderno()
    for fonte in linhas:
        c.executar(fonte)
    return c


def test_declarar_a_metrica_abstrata():
    d = caderno(r"\mu, \nu = índices").executar("g = métrica").to_dict()
    assert "é a métrica do espaço" in d["texto"]
    assert "(0,2)" in d["texto"]


def test_baixar_indice():
    c = caderno(r"\mu, \nu = índices", "g = métrica", "A = tensor(1,0)",
                r"g_{\mu\nu} A^{\nu}")
    d = c.executar("contrair(eq1)").to_dict()
    assert d["exato"] == "A(-mu)"
    assert d["indices_livres"] == [r"_\mu"]


def test_levantar_indice():
    """g^{\\mu\\nu} é a métrica inversa — a mesma convenção, na outra direção."""
    c = caderno(r"\mu, \nu = índices", "g = métrica", "A = tensor(0,1)",
                r"g^{\mu\nu} A_{\nu}")
    d = c.executar("contrair(eq1)").to_dict()
    assert d["exato"] == "A(mu)"
    assert d["indices_livres"] == [r"^\mu"]


def test_sem_declarar_a_metrica_ele_recusa():
    """A informação que falta não é calculável: só a declaração a tem."""
    c = caderno(r"\mu, \nu = índices", "A = tensor(1,0)", r"g_{\mu\nu} A^{\nu}")
    assert "não sei qual é a métrica" in c.executar("contrair(eq1)").to_dict()["erro"]


def test_contrair_o_que_nao_tem_metrica_contraida():
    c = caderno(r"\mu, \nu = índices", "g = métrica", "A = tensor(1,0)",
                r"A^{\mu} B_{\mu}")
    assert "não há índice para baixar" in c.executar("contrair(eq1)").to_dict()["erro"]


def test_contrair_o_que_nao_e_tensor():
    c = caderno("x^2 + 1")
    assert "não é expressão tensorial" in c.executar("contrair(eq1)").to_dict()["erro"]


def test_a_metrica_com_indice_em_cima_nao_gera_nota():
    """g^{\\mu\\nu} é notação corrente, e não valência trocada.

    A nota antiga dizia que o Sucuri não aplica a métrica sozinho. Agora
    aplica, quando mandam — mantê-la seria mentir sobre o próprio programa.
    """
    c = caderno(r"\mu, \nu = índices", "g = métrica", "A = tensor(0,1)")
    assert c.executar(r"g^{\mu\nu} A_{\nu}").to_dict()["notas"] == []


def test_a_metrica_ainda_tem_dois_indices():
    c = caderno(r"\mu, \nu, \lambda = índices", "g = métrica")
    d = c.executar(r"g_{\mu\nu\lambda}").to_dict()
    assert "aparece com 3" in d["erro"]


# ------------------------------------------------- do índice às componentes

def test_avaliar_da_as_componentes():
    """A estrutura vem dos índices; o valor vem das componentes."""
    c = caderno(*SCHWARZSCHILD, r"\mu, \nu = índices", "A = tensor(1,0)",
                r"g_{\mu\nu} A^{\nu}")
    d = c.executar("avaliar(eq1)").to_dict()
    assert d["proveniencia"] == "estabelecida"
    valores = dict((l[0], l[1]) for l in d["linhas"])
    assert valores["coordenadas"] == r"t, r, \theta, \phi"

    # A_t = g_tt A^t = -(1 - 2M/r) A^t
    M, r = sp.symbols("M r")
    esperado = -(1 - 2 * M / r) * sp.Symbol("A__t")
    assert sp.simplify(sp.sympify(valores[r"A_{t}"]) - esperado) == 0
    # e o índice escrito com barra continua com barra no rótulo
    assert r"A_{\theta}" in valores


def test_a_componente_que_sai_volta_para_dentro():
    """`A^t` na tela reentra como potência. O nome tem de sobreviver à volta."""
    c = caderno(*SCHWARZSCHILD, r"\mu, \nu = índices", "A = tensor(1,0)",
                r"g_{\mu\nu} A^{\nu}")
    d = c.executar("avaliar(eq1)").to_dict()
    for linha in d["linhas"][1:]:
        assert sp.sympify(linha[1]) is not None


def test_avaliar_sem_componentes_recusa():
    """Métrica abstrata diz a estrutura e não o valor — e o programa diz isso."""
    c = caderno(r"\mu, \nu = índices", "g = métrica", "A = tensor(1,0)",
                r"g_{\mu\nu} A^{\nu}")
    d = c.executar("avaliar(eq1)").to_dict()
    assert "precisa da métrica com componentes" in d["erro"]


def test_a_dimensao_vem_das_coordenadas():
    """Quatro coordenadas declaram um espaço de dimensão 4; pedir de novo é
    pedir a mesma informação duas vezes."""
    c = caderno(*SCHWARZSCHILD)
    assert "dimensão 4" in c.executar(r"\mu, \nu = índices").to_dict()["texto"]


def test_coordenadas_e_indices_que_se_contradizem():
    c = caderno(r"x = coordenadas(t, r, \theta)")
    d = c.executar(r"\alpha, \beta = índices(7)").to_dict()
    assert "dimensão 3" in d["erro"] and "dimensão 7" in d["erro"]


def test_um_nome_um_objeto():
    """`g = métrica(...)` já diz que g é A métrica: não se declara duas vezes."""
    c = caderno(*SCHWARZSCHILD, r"\mu, \nu = índices", "A = tensor(1,0)",
                r"g_{\mu\nu} A^{\nu}")
    assert c.executar("contrair(eq1)").to_dict()["exato"] == "A(-mu)"
