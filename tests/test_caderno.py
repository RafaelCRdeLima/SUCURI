"""O caderno: várias equações, nomes que duram, verbos que operam sobre elas.

A tentação, num caderno, é abrir um console de Python — e nesse instante a
ponte que este programa é deixa de ser obrigatória. Os verbos são poucos e
fechados de propósito, e cada um passa pelo mesmo motor, com as mesmas recusas.
"""

import pytest
import sympy as sp

from sucuri.caderno import Caderno


def caderno():
    return Caderno().configurar({"independente": "x", "linhas": "derivative",
                                 "funcoes": "f", "e": None})


def test_celula_de_matematica_ganha_nome():
    c = caderno()
    d = c.executar(r"f^{\prime} = x^2").to_dict()
    assert d["nome"] == "eq1"
    assert d["tipo"] == "math"
    assert d["sympy"] == "Eq(Derivative(f(x), x), x**2)"


def test_os_nomes_duram_e_seguem():
    c = caderno()
    assert c.executar("x^2").to_dict()["nome"] == "eq1"
    assert c.executar("x^3").to_dict()["nome"] == "eq2"


def test_resolver_equacao_diferencial_confere_por_substituicao():
    c = caderno()
    c.executar(r"f^{\prime} = x^2")
    d = c.executar("resolver(eq1)").to_dict()
    assert d["tipo"] == "comando"
    assert d["proveniencia"] == "estabelecida"
    assert ("conferência", "substituída na equação: resto 0") in [
        tuple(l) for l in d["linhas"]]


def test_resolver_serve_para_a_algebrica_tambem():
    """Obrigar o usuário a escolher entre solve e dsolve é pedir que ele
    classifique a própria equação para o programa — ao contrário."""
    c = caderno()
    c.executar("x^2 - 5x + 6 = 0")
    d = c.executar("solve(eq1)").to_dict()
    assert sorted(l[1] for l in d["linhas"]) == ["2", "3"]


def test_o_verbo_aceita_os_dois_idiomas():
    c = caderno()
    c.executar(r"\int_0^1 x^2")
    assert c.executar("avaliar(eq1)").to_dict()["exato"] == "1/3"
    assert c.executar("evaluate(eq1)").to_dict()["exato"] == "1/3"


def test_exportar_devolve_codigo_que_roda_sozinho():
    """O pedido mais honesto que um programa destes recebe — 'me dá o código
    que você usou' — e a prova de que não há mágica: o que sai roda sem o
    Sucuri."""
    c = caderno()
    c.executar(r"f^{\prime} = x^2")
    codigo = c.executar("exportar(eq1)").to_dict()["codigo"]
    assert "dsolve(eq1, f(x))" in codigo
    assert "checkodesol" in codigo

    escopo = {}
    exec(codigo, escopo)                                # noqa: S102
    x = sp.Symbol("x")
    assert escopo["solucao"] == sp.Eq(sp.Function("f")(x),
                                      sp.Symbol("C1") + x**3 / 3)


def test_nome_que_nao_existe_diz_os_que_existem():
    c = caderno()
    c.executar("x^2")
    erro = c.executar("resolver(eq7)").to_dict()["erro"]
    assert "eq7" in erro and "eq1" in erro


def test_celula_com_sitio_pendente_nao_ganha_nome():
    """A recusa do leitor atravessa o caderno: o que ninguém leu não vira
    nome, e portanto não vira conta."""
    c = Caderno().configurar({"independente": "x"})
    d = c.executar(r"\int e^{x}\,dx").to_dict()
    assert d["nome"] is None
    assert d["pendentes"] == 1


def test_o_que_nao_e_verbo_conhecido_e_matematica():
    """`sin(x)` não é comando: é uma expressão. A lista de verbos é fechada, e
    o que não está nela não vira execução de código nenhuma."""
    c = caderno()
    d = c.executar("sin(x)").to_dict()
    assert d["tipo"] == "math"


def test_verbo_sobre_nome_inexistente_nao_executa_python():
    c = caderno()
    d = c.executar("__import__('os')").to_dict()
    assert d["tipo"] == "math"          # não é verbo conhecido: é (tentativa de) math
    assert d["sympy"] is None or "os" not in str(d["sympy"])


def test_mudar_convencao_refaz_a_leitura():
    c = caderno()
    c.executar("y' + y = 0")
    c.configurar({"linhas": "symbol"})
    d = c.executar("y' + y = 0").to_dict()
    assert "Derivative" not in (d["sympy"] or "")


def test_latex_devolve_a_escrita_de_volta():
    c = caderno()
    c.executar("x^2 + 1")
    assert c.executar("latex(eq1)").to_dict()["latex_exato"] == "x^{2} + 1"


# ------------------------------------------------- declarar dissolve a dúvida

def test_declarar_a_funcao_e_suas_variaveis():
    """`u = u(t,x)` não escolhe entre as leituras de ∂u/∂t: tira uma delas do
    mundo. Não há símbolo u para multiplicar, então "fração literal dos
    símbolos ∂, u e ∂t" deixa de ser uma leitura possível — o sítio para de ser
    pergunta porque parou de ter duas respostas.
    """
    c = Caderno().configurar({"variaveis": "c"})
    d = c.executar("u = u(x,t)").to_dict()
    assert d["tipo"] == "declaracao"
    assert d["declarado"] == [{"nome": "u", "variaveis": ["x", "t"]}]

    onda = c.executar(
        r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}"
    ).to_dict()
    assert onda["pendentes"] == 0
    assert onda["inferidas"] == 0          # nada ficou por conferir
    assert onda["sympy"] == (
        "Eq(Derivative(u(x, t), (t, 2)), c**2*Derivative(u(x, t), (x, 2)))")
    assert all(a["estado"] == "explicita" for a in onda["ambiguidades"])
    assert all("declarada função de x, t" in a["motivo"]
               for a in onda["ambiguidades"])


def test_so_a_forma_com_igual_declara():
    """`u(t,x)` sozinho é expressão legítima — aplicação, ou produto, que é
    justamente um sítio ambíguo. Engoli-la como declaração seria decidir por
    quem escreveu. A repetição do nome é o que distingue: `u = u(t,x)` é
    tautologia, e ninguém escreve isso como equação."""
    c = Caderno()
    assert c.executar("u = u(t,x)").to_dict()["tipo"] == "declaracao"
    assert c.executar("u(t,x)").to_dict()["tipo"] == "math"
    assert c.executar("u = v(t,x)").to_dict()["tipo"] == "math"


def test_a_forma_antiga_diz_o_que_mudou():
    """Falhar em LaTeX não ajudaria quem aprendeu a sintaxe de ontem."""
    c = Caderno()
    d = c.executar("u[x,t]").to_dict()
    assert "parênteses" in d["erro"] and "u = u(x,t)" in d["erro"]


def test_funcao_declarada_vale_tambem_onde_nao_ha_derivada():
    """Um u solto continua sendo a mesma função, e não um símbolo homônimo."""
    c = Caderno()
    c.executar("u = u(x,t)")
    assert c.executar("u + 1").to_dict()["sympy"] == "u(x, t) + 1"


def test_o_campo_de_funcoes_aceita_a_mesma_notacao():
    """Vírgula dentro de colchete não separa: 'u(x,t), f' são duas
    declarações, não três."""
    from sucuri.interface.sessao import _lista
    assert _lista("u(x,t), f") == ["u(x,t)", "f"]

    c = Caderno().configurar({"funcoes": "u(x,t)", "variaveis": "c"})
    assert c.executar(r"\partial_t u").to_dict()["sympy"] == \
        "Derivative(u(x, t), t)"


def test_a_linha_continua_precisando_da_convencao():
    """Declarar u(x,t) não resolve f': com duas variáveis, a linha não diz em
    relação a qual. A declaração dissolve o que a notação já nomeia — ∂ e
    Leibniz —, e não o que ela deixa em aberto."""
    c = Caderno()
    c.executar("u = u(x,t)")
    assert c.executar("u' = 0").to_dict()["pendentes"] == 1


def test_o_cabecalho_vazio_nao_apaga_a_declaracao_da_celula():
    """A interface manda as convenções do cabeçalho a CADA execução, e o campo
    'Funções' vazio reescrevia a lista — apagando em silêncio o que a célula
    tinha declarado. Declaração de célula e campo de cabeçalho são duas
    origens, e só uma delas é reescrita pelo formulário.
    """
    from sucuri.interface import Aplicacao

    app = Aplicacao()
    conv = {"variaveis": "c", "funcoes": ""}        # cabeçalho vazio
    app.executar({"sessao": "t", "fonte": "u = u(x,t)", "convencoes": conv})
    d = app.executar({"sessao": "t", "convencoes": conv,
                      "fonte": r"\partial_t u = 0"})
    assert d["pendentes"] == 0 and d["inferidas"] == 0
    assert d["sympy"] == "Eq(Derivative(u(x, t), t), 0)"


# ------------------------------- as convenções cabem todas em declarações

def test_a_declaracao_resolve_a_linha_quando_ha_uma_variavel_so():
    """f = f[x] torna a convenção "linha é derivada" desnecessária: se f é
    função de x, f' só pode ser df/dx. Não há regra a aplicar — há um fato
    declarado, e por isso o sítio fica verde e não âmbar."""
    c = Caderno()
    c.executar("y = y(x)")
    d = c.executar("y'' + y = 0").to_dict()
    assert d["pendentes"] == 0 and d["inferidas"] == 0
    assert d["sympy"] == "Eq(y(x) + Derivative(y(x), (x, 2)), 0)"
    assert all(a["estado"] == "explicita" for a in d["ambiguidades"])


def test_a_declaracao_resolve_o_ponto_tambem():
    c = Caderno()
    c.executar("q = q(t)")
    d = c.executar(r"\dot{q}^2 + q = 0").to_dict()
    assert d["pendentes"] == 0
    assert d["sympy"] == "Eq(q(t) + Derivative(q(t), t)**2, 0)"


def test_com_duas_variaveis_a_linha_continua_perguntando():
    """Declarar não inventa o que a notação não diz: u' com u função de x e t
    não diz em relação a qual."""
    c = Caderno()
    c.executar("u = u(x,t)")
    assert c.executar("u' = 0").to_dict()["pendentes"] == 1


def test_euler_e_simbolo_sao_declaracoes_como_as_outras():
    """A mesma pergunta — o que é este nome? — com as outras duas respostas."""
    c = Caderno()
    assert "Euler" in c.executar("e = euler").to_dict()["texto"]
    assert c.executar(r"\int e^{-x}\,dx").to_dict()["sympy"] == \
        "Integral(exp(-x), x)"

    assert "produto" in c.executar("a = símbolo").to_dict()["texto"]
    assert c.executar("a(x+1)").to_dict()["sympy"] == "a*(x + 1)"


def test_o_caderno_nao_precisa_de_convencao_nenhuma():
    """A folha inteira, sem um campo de formulário: só declarações e
    matemática."""
    c = Caderno()
    for fonte in ["u = u(x,t)", "c = símbolo"]:
        assert c.executar(fonte).to_dict()["tipo"] == "declaracao"
    d = c.executar(
        r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}"
    ).to_dict()
    assert d["pendentes"] == 0 and d["inferidas"] == 0
    assert d["sympy"] == (
        "Eq(Derivative(u(x, t), (t, 2)), c**2*Derivative(u(x, t), (x, 2)))")


# ------------------------------------------- reiniciar: só o que foi acumulado

def test_reiniciar_apaga_o_acumulado_e_nao_o_escrito():
    """"Reiniciar o kernel" é a distinção entre duas coisas que parecem uma: o
    que você ESCREVEU e o que o motor GUARDOU por ter executado. Depois dele,
    eq1 deixa de existir — e é exatamente esse o ponto.

    O escrito não é problema desta rota: fica no navegador, e continua lá.
    """
    from sucuri.interface import Aplicacao

    app = Aplicacao()
    assert app.executar({"sessao": "k", "fonte": "x^2"})["nome"] == "eq1"
    assert app.executar({"sessao": "k", "fonte": "x^3"})["nome"] == "eq2"

    assert app.reiniciar({"sessao": "k"}) == {"reiniciado": True}
    assert app.executar({"sessao": "k", "fonte": "x^4"})["nome"] == "eq1"


def test_reiniciar_apaga_tambem_as_declaracoes():
    from sucuri.interface import Aplicacao

    app = Aplicacao()
    app.executar({"sessao": "d", "fonte": "u = u(t,x)"})
    assert app.executar({"sessao": "d", "fonte": "u"})["sympy"] == "u(t, x)"

    app.reiniciar({"sessao": "d"})
    assert app.executar({"sessao": "d", "fonte": "u"})["sympy"] == "u"


def test_as_decisoes_voltam_com_a_celula_e_nao_so_no_refazer():
    """Decisão de sítio é FONTE, não estado acumulado: depois de reiniciar, a
    próxima célula precisa dela de volta. Por isso vai em toda chamada."""
    from sucuri.interface import Aplicacao

    app = Aplicacao()
    decisao = [{"kind": "prime", "base": "y", "detalhe": {"order": 2},
                "leitura": "derivative"}]
    app.reiniciar({"sessao": "a"})
    d = app.executar({"sessao": "a", "fonte": "y'' + y = 0",
                      "convencoes": {"independente": "x"},
                      "anotacoes": decisao})
    assert d["pendentes"] == 0
    assert d["sympy"] == "Eq(y(x) + Derivative(y(x), (x, 2)), 0)"


def test_o_verbo_de_dois_argumentos():
    """`conferir(equação, candidata)` — o primeiro verbo que compara duas
    coisas, e por isso a gramática ganhou a vírgula."""
    c = Caderno()
    for f in ["u = u(t,x)", "c = símbolo", "F = F(z)", "G = G(z)"]:
        c.executar(f)
    c.executar(r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}")
    c.executar(r"u = F(x - c t) + G(x + c t)")

    d = c.executar("conferir(eq1, eq2)").to_dict()
    assert d["proveniencia"] == "estabelecida"
    assert d["rotulo"] == "candidata verificada"

    faltando = c.executar("conferir(eq1)").to_dict()
    assert "duas" in faltando["erro"]
