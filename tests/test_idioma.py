"""O Sucuri em inglês: os comandos na entrada, as mensagens na saída.

A tradução é uma camada — o motor pensa em português —, e uma camada só presta
se cobre tudo: mensagem nova sem tradução apareceria em português no meio da
tela em inglês. O primeiro teste é o que impede isso.
"""

import pathlib
import sys

import pytest

from sucuri.caderno import Caderno
from sucuri.idioma import normalizar_entrada, traduzir, traduzir_resposta
from sucuri.interface.aplicacao import Aplicacao
from sucuri.mensagens_en import EN

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "tools"))
import extrair_mensagens  # noqa: E402


def test_toda_mensagem_do_codigo_tem_traducao():
    faltam = [f"{m!r} ({onde[0]})" for m, onde in extrair_mensagens.moldes().items()
              if m not in EN]
    assert not faltam, ("mensagens sem tradução em sucuri/mensagens_en.py:\n"
                        + "\n".join(faltam[:20]))


@pytest.mark.parametrize("en, pt", [
    ("g = metric(1, r^2)", "g = métrica(1, r^2)"),
    (r"x = coordinates(t, r)", r"x = coordenadas(t, r)"),
    (r"\mu, \nu = indices", r"\mu, \nu = índices"),
    ("a, b = indices(2)", "a, b = índices(2)"),
    ("k = constant", "k = constante"),
    ("F = tensor(0, 2, antisymmetric)", "F = tensor(0, 2, antissimétrico)"),
    (r"\alpha = form(dr)", r"\alpha = forma(dr)"),
    ("A = field()", "A = campo()"),
    (r"S = star(\beta, g)", r"S = estrela(\beta, g)"),
    ("in_chart(eq3)", "em_carta(eq3)"),
    ("h = induced(g, u)", "h = induzida(g, u)"),
])
def test_os_comandos_em_ingles(en, pt):
    assert normalizar_entrada(en) == pt


def test_so_na_posicao_de_comando():
    # `form` dentro de uma equação é f·o·r·m, e continua sendo
    assert normalizar_entrada("y = form + 1") == "y = form + 1"
    assert normalizar_entrada(r"\frac{form(x)}{2} = 0") == r"\frac{form(x)}{2} = 0"


def test_o_mesmo_resultado_nos_dois_idiomas():
    def rodar(fontes):
        c = Caderno()
        return [c.executar(f).to_dict().get("exato") for f in fontes]
    pt = rodar([r"x = coordenadas(\theta, \phi)", r"g = métrica(1, \sin^2\theta)", "escalar(g)"])
    en = rodar([r"x = coordinates(\theta, \phi)", r"g = metric(1, \sin^2\theta)", "scalar(g)"])
    assert pt == en and pt[-1] == "2"


def test_a_mensagem_traduzida_guarda_os_valores():
    assert traduzir("não conheço 'eq9' (tenho: eq1, eq2)") == "unknown 'eq9' (I have: eq1, eq2)"


def test_a_traducao_nao_toca_identificador_nem_matematica():
    d = {"estado": "pendente", "kind": "juxtaposition", "leitura": "product",
         "latex": r"\text{não}", "sympy": "Eq(x, 0)", "erro": "não achei combinação das hipóteses que dê isto."}
    t = traduzir_resposta(d, "en")
    assert t["estado"] == "pendente" and t["latex"] == r"\text{não}"
    assert t["erro"].startswith("I found no combination")


def test_em_portugues_nada_muda():
    d = {"erro": "não conheço 'eq9' (tenho: nenhum ainda)"}
    assert traduzir_resposta(d, "pt") == d


def test_a_rota_responde_no_idioma_pedido():
    app = Aplicacao()
    rota = Aplicacao.ROTAS["/api/caderno/executar"]
    en = rota(app, {"sessao": "i", "fonte": "provar(eq9)", "idioma": "en"})
    pt = rota(app, {"sessao": "j", "fonte": "provar(eq9)"})
    assert "unknown" in en["erro"] and "não conheço" in pt["erro"]


def test_a_tela_manda_o_idioma_em_todo_pedido():
    js = (pathlib.Path(__file__).parents[1] / "sucuri" / "interface" / "estatico"
          / "idioma.js").read_text(encoding="utf-8")
    assert "c.idioma = SUCURI_IDIOMA" in js
    for pagina in ("caderno.html", "index.html"):
        html = (pathlib.Path(__file__).parents[1] / "sucuri" / "interface" / "estatico"
                / pagina).read_text(encoding="utf-8")
        assert html.index('src="transporte.js"') < html.index('src="idioma.js"'), pagina


def test_levi_civita_em_ingles():
    c = Caderno()
    d = c.executar(r"\epsilon = levi-civita(symbol)").to_dict()
    assert not d.get("erro") and "símbolo" in d["texto"]


def test_as_tabelas_dos_modulos_em_ingles():
    """As linhas do resolver chegam como tuplas: também são traduzidas."""
    c = Caderno()
    for f in ("f = f(x)", r"f^{\prime} = x^2"):
        c.executar(f)
    d = traduzir_resposta(c.executar("solve(eq1)").to_dict(), "en")
    rotulos = [l[0] for l in d["linhas"]]
    assert "order" in rotulos and "check" in rotulos and d["proveniencia"] == "established"
