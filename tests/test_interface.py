"""A interface por dentro: sessão e servidor.

Testa-se o que a página consome — o JSON —, não a página. O que importa é que
a regra do motor atravesse a fronteira intacta: sítio pendente não vira SymPy,
leitura por convenção chega marcada, e conclusão sem fonte chega barrada.
"""

import json
import threading
import urllib.request

import pytest

from sucuri.interface import criar
from sucuri.interface.sessao import Sessao, codigo_python


# ------------------------------------------------------------------ sessão

def test_sitio_pendente_nao_vira_sympy():
    s = Sessao()
    d = s.ler("y'' + y = 0")
    assert d["pendentes"] == 1
    assert d["sympy"] is None
    assert d["arvore"] is None
    assert d["ambiguidades"][0]["estado"] == "pendente"
    assert d["ambiguidades"][0]["leitura"] is None


def test_convencao_resolve_e_chega_marcada_como_inferida():
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    d = s.ler("y'' + y = 0")
    assert d["pendentes"] == 0
    assert d["inferidas"] == 1
    assert d["ambiguidades"][0]["estado"] == "inferida"
    assert "Derivative" in d["codigo"]


def test_anotacao_de_sitio_vence_a_convencao_e_e_explicita():
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    a = s.ler("y' + y = 0")["ambiguidades"][0]
    s.anotar(a["kind"], a["base"], a["detalhe"], "symbol")
    d = s.ler()
    assert d["ambiguidades"][0]["estado"] == "explicita"
    assert d["inferidas"] == 0
    assert "Derivative" not in d["codigo"]


def test_esquecer_devolve_o_sitio_a_convencao():
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    a = s.ler("y' + y = 0")["ambiguidades"][0]
    s.anotar(a["kind"], a["base"], a["detalhe"], "symbol")
    s.esquecer(a["kind"], a["base"], a["detalhe"])
    assert s.ler()["ambiguidades"][0]["estado"] == "inferida"


def test_convencao_impossivel_vira_aviso_e_nao_excecao():
    # linha como derivada sem variável independente: a convenção esconderia a
    # ambiguidade em vez de resolvê-la, e o motor recusa.
    d = Sessao().configurar({"linhas": "derivative"}).ler("y' = 0")
    assert d["avisos"]
    assert d["pendentes"] == 1


def test_detalhe_atravessa_o_json_com_o_tipo_certo():
    # a chave da anotação inclui detail; se a ordem virasse string, a anotação
    # feita pela página não casaria com o sítio.
    s = Sessao().configurar({"independente": "x"})
    a = s.ler("y'' = 0")["ambiguidades"][0]
    viagem = json.loads(json.dumps(a))
    s.anotar(viagem["kind"], viagem["base"], viagem["detalhe"], "derivative")
    assert s.ler()["ambiguidades"][0]["estado"] == "explicita"


def test_arvore_carrega_a_proveniencia_ate_a_pagina():
    s = Sessao().configurar({"independente": "x", "linhas": "derivative"})
    d = s.ler("y'' + y = 0")
    estados = {n["estado"] for n in _nos(d["arvore"])}
    assert "inferida" in estados


def test_erro_de_leitura_nao_derruba_a_sessao():
    d = Sessao().ler(r"\frac{")
    assert d["sympy"] is None
    assert d["erro"] or d["pendentes"] == 0


def test_codigo_python_e_colavel():
    import sympy as sp
    x = sp.Symbol("x")
    codigo = codigo_python(sp.Eq(sp.Derivative(sp.Function("phi")(x), x, 2), 0))
    escopo = {}
    exec(codigo, escopo)                                # noqa: S102
    assert escopo["expr"] == sp.Eq(sp.Derivative(sp.Function("phi")(x), x, 2), 0)


def _nos(no):
    yield no
    for f in no["filhos"]:
        yield from _nos(f)


# ---------------------------------------------------------------- servidor

@pytest.fixture
def servidor():
    s = criar("127.0.0.1", 0)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()
    s.server_close()


def _post(base, rota, corpo):
    pedido = urllib.request.Request(
        base + rota, data=json.dumps(corpo).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=10) as r:
        return json.loads(r.read())


def _get(base, rota):
    with urllib.request.urlopen(base + rota, timeout=10) as r:
        return r.status, r.read()


def test_pagina_e_servida(servidor):
    codigo, corpo = _get(servidor, "/")
    assert codigo == 200
    assert b"SUCURI" in corpo


def test_katex_vendorizado_esta_presente(servidor):
    # a renderização precisa funcionar sem rede: é um programa de mesa.
    for caminho in ("/vendor/katex/katex.min.js", "/vendor/katex/katex.min.css"):
        assert _get(servidor, caminho)[0] == 200


def test_nao_serve_fora_do_diretorio(servidor):
    with pytest.raises(urllib.error.HTTPError) as e:
        _get(servidor, "/../sessao.py")
    assert e.value.code == 404


def test_rota_ler_devolve_a_leitura(servidor):
    d = _post(servidor, "/api/ler", {"latex": r"x^2 + 1"})
    assert d["sympy"] == "x**2 + 1"
    assert d["pendentes"] == 0
    assert d["versoes"]["sympy"]


def test_a_sessao_guarda_as_decisoes_entre_pedidos(servidor):
    corpo = {"sessao": "t", "latex": "y' = 0",
             "convencoes": {"independente": "x", "linhas": "derivative"}}
    assert _post(servidor, "/api/ler", corpo)["inferidas"] == 1
    a = _post(servidor, "/api/ler", corpo)["ambiguidades"][0]
    d = _post(servidor, "/api/anotar",
              {"sessao": "t", "latex": "y' = 0", "kind": a["kind"],
               "base": a["base"], "detalhe": a["detalhe"], "leitura": "symbol"})
    assert d["ambiguidades"][0]["estado"] == "explicita"
    # e a decisão sobrevive à próxima leitura, que não a menciona
    assert _post(servidor, "/api/ler", corpo)["ambiguidades"][0]["estado"] == "explicita"


def test_sessoes_sao_independentes(servidor):
    _post(servidor, "/api/ler", {"sessao": "a", "latex": "x",
                                 "convencoes": {"independente": "x"}})
    d = _post(servidor, "/api/ler", {"sessao": "b", "latex": "x"})
    assert d["estado"]["independente"] is None


def test_operacao_de_modulo_recusa_expressao_pendente(servidor):
    _post(servidor, "/api/ler", {"sessao": "m", "latex": "y'' + y = 0"})
    d = _post(servidor, "/api/operar",
              {"sessao": "m", "latex": "y'' + y = 0", "modulo": "korvin",
               "operacao": "esquema de Riemann"})
    assert "pendente" in d["erro"]


def test_conclusao_sem_fonte_chega_barrada(servidor):
    # a regra do KORVIN atravessa a fronteira: o que não tem origem declarada
    # não se apresenta como conclusão, nem na página.
    corpo = {"sessao": "k", "latex": r"y'' = x y",
             "convencoes": {"independente": "x", "linhas": "derivative"}}
    _post(servidor, "/api/ler", corpo)
    d = _post(servidor, "/api/operar",
              {"sessao": "k", "latex": corpo["latex"],
               "modulo": "korvin", "operacao": "não-integrabilidade"})
    assert d["apresentavel"] is False
    assert d["proveniencia"] == "sem fonte"


def test_rota_desconhecida_devolve_404(servidor):
    with pytest.raises(urllib.error.HTTPError) as e:
        _post(servidor, "/api/inexistente", {})
    assert e.value.code == 404
