"""Os exemplos do manual, executados.

Manual cujos exemplos ninguém roda apodrece — e apodrece em silêncio, que é a
forma que este projeto persegue. Cada `.exemplo` da página é lido daqui,
executado célula a célula, e a saída anunciada tem de aparecer na saída real.

Quando um exemplo quebrar, ou o programa mudou e o manual mente, ou o manual
está certo e o programa regrediu. Os dois merecem parar a suíte.
"""

import pathlib
import re
from html.parser import HTMLParser

import pytest

from sucuri.caderno import Caderno

MANUAL = (pathlib.Path(__file__).parents[1] / "sucuri" / "interface"
          / "estatico" / "manual.html")


class Leitor(HTMLParser):
    """Tira da página os exemplos: as entradas e a saída anunciada."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.exemplos = []
        self._atual = None
        self._campo = None
        self._texto = []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if "exemplo" in classes:
            self._atual = {"entradas": [], "saida": None, "especie": None}
        elif self._atual is not None:
            for c in ("entrada", "saida", "pergunta", "erro-esperado"):
                if c in classes:
                    self._campo, self._texto = c, []

    def handle_data(self, dados):
        if self._campo:
            self._texto.append(dados)

    def handle_endtag(self, tag):
        if self._campo:
            texto = "".join(self._texto).strip()
            if self._campo == "entrada":
                self._atual["entradas"].append(texto)
            else:
                self._atual["saida"] = texto
                self._atual["especie"] = self._campo
            self._campo = None
        elif tag == "div" and self._atual and self._atual["saida"] is not None:
            self.exemplos.append(self._atual)
            self._atual = None


def exemplos():
    leitor = Leitor()
    leitor.feed(MANUAL.read_text(encoding="utf-8"))
    assert leitor.exemplos, "nenhum exemplo encontrado no manual"
    return leitor.exemplos


def tudo_que_saiu(d):
    """Tudo o que uma célula mostrou, num texto só."""
    pedacos = [str(d.get(k) or "") for k in
               ("sympy", "texto", "erro", "codigo", "exato", "rotulo")]
    for chave, valor in (d.get("linhas") or []):
        pedacos.append(f"{chave}={valor}")
    for o in (d.get("nomeados") or []):
        pedacos.append(str(o.get("sympy")))
    for a in (d.get("ambiguidades") or []):
        pedacos.append(a["fragmento"])
        pedacos += [r["descricao"] for r in a["leituras"]]
    return " | ".join(p for p in pedacos if p)


@pytest.mark.parametrize("exemplo", exemplos(),
                         ids=lambda e: e["entradas"][-1][:40])
def test_o_exemplo_do_manual_faz_o_que_diz(exemplo, monkeypatch):
    caderno = Caderno()
    if any("6 y^2" in e for e in exemplo["entradas"]):
        # monkeypatch, e não atribuição: baixar o prazo e não repor contamina
        # os testes seguintes, e um teste que estraga o vizinho é pior do que
        # um teste a menos.
        import sucuri.modules.resolver as R
        monkeypatch.setattr(R, "PRAZO_RESOLVER", 4)

    saida = ""
    for fonte in exemplo["entradas"]:
        saida = tudo_que_saiu(caderno.executar(fonte).to_dict())

    esperado = exemplo["saida"]
    if exemplo["especie"] == "pergunta":
        # A pergunta é mostrada ao leitor numa linha só, com setas e barras que
        # são tipografia, não saída. O que tem de bater são os pedaços.
        for pedaco in re.split(r"\s*[→|]\s*", esperado):
            if pedaco.strip():
                assert pedaco.strip() in saida, (
                    f"o manual anuncia {pedaco.strip()!r}\n"
                    f"mas a saída foi {saida[:300]!r}")
        return
    assert esperado in saida, (
        f"o manual anuncia {esperado!r}\nmas a saída foi {saida[:300]!r}")


def test_todos_os_exemplos_tem_entrada_e_saida():
    for e in exemplos():
        assert e["entradas"] and e["saida"]


def test_o_manual_esta_publicado():
    web = pathlib.Path(__file__).parents[1] / "web" / "manual.html"
    assert web.exists()
    assert web.read_text(encoding="utf-8") == MANUAL.read_text(encoding="utf-8")
