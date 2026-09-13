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


# ------------------------------------------------- a constante de integração

def test_integral_indefinida_e_uma_familia():
    """∫sen x dx não é -cos(x): é -cos(x) + C. O SymPy devolve o
    representante e não diz que é um representante; qualquer tabela escreve a
    constante. Omiti-la é dar por resposta um pedaço da resposta."""
    d = Sessao().avaliar(r"\int \sin x\,dx")
    assert d["fechou"] is True
    assert d["indefinida"] is True
    assert d["exato"] == "-cos(x)"


def test_definida_nao_leva_constante():
    d = Sessao().avaliar(r"\int_0^1 x^2")
    assert d["indefinida"] is False


def test_indefinida_que_nao_fecha_nao_ganha_constante():
    """Sem primitiva não há família: pôr '+ C' numa conta por fazer seria
    enfeitar o que não foi respondido."""
    d = Sessao().avaliar(r"\int \frac{\sin x}{\ln x}\,dx")
    assert d["fechou"] is False
    assert d["indefinida"] is False


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


# ------------------------------------------------- o verbo segue o objeto

def test_equacao_diferencial_e_reconhecida_como_tal():
    """Avaliar uma equação diferencial não faz nada: `doit` deixa a derivada de
    uma função incógnita exatamente onde estava. A interface precisa saber
    disso para oferecer 'Resolver' em vez de 'Avaliar' — mandar o usuário
    descobrir sozinho que o botão certo é outro é fazê-lo adivinhar."""
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    assert s.ler(r"\frac{d^2 \phi}{dx^2} + x\phi = 0")["diferencial"] is True
    assert s.ler("y'' + y = 0")["diferencial"] is True


def test_o_que_nao_e_equacao_diferencial_nao_e_marcado():
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    for latex in [r"\int_0^1 x^2", "x^2 + 1 = 0", r"\int \sin x\,dx"]:
        assert s.ler(latex)["diferencial"] is False


def test_derivada_de_expressao_conhecida_nao_e_equacao_diferencial():
    """d/dx(sen x) = cos x tem derivada, mas de função CONHECIDA: isso se
    avalia, não se resolve."""
    s = Sessao().configurar({"independente": "x"})
    assert s.ler(r"\frac{d}{dx} \sin x = \cos x")["diferencial"] is False


# --------------------------------------------- a convenção que falta vira pergunta

def test_falta_de_variavel_vira_pergunta_com_o_que_se_pode_ver():
    """Reclamar de campo vazio é empurrar para o usuário uma pergunta que dava
    para fazer. O leitor sabe quais letras aparecem na equação; a interface
    pergunta ali mesmo, com elas à mão."""
    d = Sessao().configurar({"linhas": "derivative"}).ler(r"f^{\prime} = x^2")
    f = d["faltando"]
    assert f["qual"] == "independente"
    assert f["campo"] == "Variável independente"
    assert f["candidatos"] == ["x"]


def test_a_base_da_derivada_nao_entra_como_candidata():
    """y' com y independente seria a derivada de y em relação a si mesmo, e o
    leitor recusa isso — oferecer y seria oferecer um beco."""
    d = Sessao().configurar({"linhas": "derivative"}).ler("y'' + y = 0")
    assert d["faltando"]["candidatos"] == []


def test_lista_vazia_e_a_informacao():
    """Em y'' + y = 0 a variável não está escrita. A lista vazia diz isso, que é
    melhor do que uma lista errada."""
    d = Sessao().configurar({"linhas": "derivative"}).ler("y'' + y = 0")
    assert d["faltando"] is not None
    assert d["faltando"]["candidatos"] == []


def test_com_a_variavel_declarada_a_pergunta_some():
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    d = s.ler(r"f^{\prime} = x^2")
    assert d["faltando"] is None
    assert d["sympy"] == "Eq(Derivative(f(x), x), x**2)"
