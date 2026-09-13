"""Avaliar é outro ato, e a resposta tem três formas.

O Sucuri lê; a integral fica `Integral(x**2, (x, 0, 1))` parada até alguém
pedir a conta. Quando pedem, o que volta pode ser o valor, pode ser a conta
por fazer, e pode não voltar — e tratar as três como a mesma coisa é o erro
que este programa existe para não cometer.
"""

import pytest

from sucuri.interface.sessao import Sessao


def test_a_integral_definida_fecha():
    d = Sessao().avaliar(r"\int_0^1 x^2")
    assert d["fechou"] is True
    assert d["exato"] == "1/3"
    assert d["latex_exato"] == r"\frac{1}{3}"


def test_a_aproximacao_vem_rotulada_e_separada_do_valor():
    """O número decimal acompanha, nunca substitui: 0,333… não é 1/3."""
    d = Sessao().avaliar(r"\int_0^1 x^2")
    assert d["numerico"].startswith("0.3333")
    assert d["exato"] == "1/3"


def test_soma_infinita_tambem():
    d = Sessao().avaliar(r"\sum_{n=1}^\infty \frac{1}{n^2}")
    assert d["exato"] == "pi**2/6"


def test_a_conta_que_nao_fecha_diz_que_nao_fechou():
    """O SymPy devolve a própria integral quando não sabe integrar. Isso não é
    resposta, e o rótulo separa os dois casos."""
    d = Sessao().avaliar(r"\int_0^1 \frac{\sin x}{\ln x}\,dx")
    assert d["fechou"] is False
    assert "Integral" in d["exato"]


def test_sem_aproximacao_quando_a_conta_nao_fecha():
    """Avaliar numericamente o que ficou parado devolve ruído com cara de
    resposta — foi o que aconteceu na primeira versão: -0.e+2."""
    d = Sessao().avaliar(r"\int_0^1 \frac{\sin x}{\ln x}\,dx")
    assert d["numerico"] is None


def test_sitio_pendente_bloqueia_a_avaliacao():
    """A mesma recusa da leitura: nada se calcula sobre o que ninguém leu."""
    d = Sessao().avaliar(r"\int_0^\infty e^{-x}\,dx")
    assert d["exato"] is None
    assert "pendentes" in d["erro"]
    assert any("Euler" in p for p in d["pendentes"])


def test_avaliar_respeita_a_convencao_declarada():
    s = Sessao().configurar({"independente": "x"})
    s.avaliar(r"\int_0^\infty e^{-x}\,dx")
    s.anotar("euler", "e", {}, "euler")
    d = s.avaliar()
    assert d["exato"] == "1"


def test_o_prazo_existe():
    from sucuri.interface import sessao
    assert sessao.PRAZO_AVALIAR >= 5


def test_a_rota_esta_na_aplicacao():
    from sucuri.interface import Aplicacao
    a = Aplicacao()
    d = Aplicacao.ROTAS["/api/avaliar"](a, {"latex": r"\int_0^1 x^2", "sessao": "t"})
    assert d["exato"] == "1/3"
