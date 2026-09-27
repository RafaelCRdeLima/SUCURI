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


MANUAL_EN = MANUAL.with_name("manual-en.html")


def exemplos(pagina=None):
    leitor = Leitor()
    leitor.feed((pagina or MANUAL).read_text(encoding="utf-8"))
    assert leitor.exemplos, "nenhum exemplo encontrado no manual"
    return leitor.exemplos


def executar(caderno, fonte, idioma="pt"):
    """A célula, no idioma da página: em inglês, a resposta traduzida como a
    rota a devolve à tela."""
    from sucuri.idioma import traduzir_resposta
    return traduzir_resposta(caderno.executar(fonte).to_dict(), idioma)


def _casos():
    return ([(e, "pt") for e in exemplos()]
            + [(e, "en") for e in exemplos(MANUAL_EN)])


def tudo_que_saiu(d):
    """Tudo o que uma célula mostrou, num texto só.

    Inclusive quando a célula tem várias linhas: desde que Enter encadeia, uma
    célula pode responder mais de uma vez, e o manual anuncia o conjunto.
    """
    if d.get("partes"):
        return " | ".join(tudo_que_saiu(p) for p in d["partes"])
    pedacos = [str(d.get(k) or "") for k in
               ("sympy", "texto", "erro", "codigo", "exato", "rotulo",
                "latex_tabela")]
    for linha in (d.get("linhas") or []):
        pedacos.append("=".join(str(c) for c in linha))
    for o in (d.get("nomeados") or []):
        pedacos.append(str(o.get("sympy")))
    for a in (d.get("ambiguidades") or []):
        pedacos.append(a["fragmento"])
        pedacos += [r["descricao"] for r in a["leituras"]]
    return " | ".join(p for p in pedacos if p)


@pytest.mark.parametrize("exemplo, idioma", _casos(),
                         ids=lambda x: x if isinstance(x, str) else x["entradas"][-1][:40])
def test_o_exemplo_do_manual_faz_o_que_diz(exemplo, idioma, monkeypatch):
    caderno = Caderno()
    if any("6 y^2" in e for e in exemplo["entradas"]):
        # monkeypatch, e não atribuição: baixar o prazo e não repor contamina
        # os testes seguintes, e um teste que estraga o vizinho é pior do que
        # um teste a menos.
        import sucuri.modules.resolver as R
        monkeypatch.setattr(R, "PRAZO_RESOLVER", 4)

    saida = ""
    for fonte in exemplo["entradas"]:
        saida = tudo_que_saiu(executar(caderno, fonte, idioma))

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


@pytest.mark.parametrize("pagina", [MANUAL, MANUAL_EN], ids=lambda p: p.name)
def test_o_manual_esta_publicado(pagina):
    web = pathlib.Path(__file__).parents[1] / "web" / pagina.name
    assert web.exists()
    assert web.read_text(encoding="utf-8") == pagina.read_text(encoding="utf-8")


def test_as_duas_versoes_do_manual_tem_os_mesmos_exemplos():
    assert len(exemplos()) == len(exemplos(MANUAL_EN))


# ------------------------------------------------------- a lista de verbos

class _CodigosDaLista(HTMLParser):
    """Os `<code>` da primeira coluna da tabela `#lista-de-verbos` — a do
    idioma da página; a segunda é a do outro."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.codigos, self._dentro, self._code, self._coluna = [], False, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table" and dict(attrs).get("id") == "lista-de-verbos":
            self._dentro = True
        elif tag == "tr":
            self._coluna = 0
        elif tag == "td":
            self._coluna += 1
        elif tag == "code" and self._dentro and self._coluna == 1:
            self._code = []

    def handle_data(self, dados):
        if self._code is not None:
            self._code.append(dados)

    def handle_endtag(self, tag):
        if tag == "table":
            self._dentro = False
        elif tag == "code" and self._code is not None:
            self.codigos.append("".join(self._code).strip())
            self._code = None


def _verbos_listados(pagina):
    """O verbo de cada `<code>` da lista: `h = induzida(g, …)` dá `induzida`;
    sem acento, que `série` e `serie` são o mesmo verbo."""
    import unicodedata
    leitor = _CodigosDaLista()
    leitor.feed(pagina.read_text(encoding="utf-8"))
    assert leitor.codigos, f"{pagina.name}: sem a tabela #lista-de-verbos"
    verbos = set()
    for c in leitor.codigos:
        m = re.match(r"(?:\\?\w+\s*=\s*)?(\w+)\(", c)
        if m:
            verbos.add(unicodedata.normalize("NFKD", m.group(1))
                       .encode("ascii", "ignore").decode())
    return verbos


def _canonicos():
    from sucuri.caderno import VERBOS
    return set(VERBOS.values()) | {"provar", "induzida"}


# O nome em inglês de cada verbo; o que não tem nome próprio é o mesmo.
EM_INGLES = {
    "resolver": "solve", "avaliar": "evaluate", "simplificar": "simplify",
    "separar": "separate", "conferir": "check", "exportar": "export",
    "serie": "series", "contrair": "contract", "expandir": "expand",
    "independentes": "independent", "em_componentes": "in_components",
    "linearizar": "linearize", "provar": "prove", "escalar": "scalar",
    "geodesicas": "geodesics", "orbitas": "orbits", "elemento": "element",
    "cartan": "tetrad", "em_carta": "in_chart", "colchete": "bracket",
    "laplaciano": "laplacian", "restringir": "restrict", "induzida": "induced",
    "cunha": "wedge", "estrela": "star", "iguais": "equal",
}


def test_a_lista_de_verbos_tem_todos():
    faltam = _canonicos() - _verbos_listados(MANUAL)
    assert not faltam, f"verbos fora da lista do manual: {sorted(faltam)}"


def test_a_lista_de_verbos_em_ingles_tem_todos():
    from sucuri.caderno import VERBOS
    # os três que não passam por VERBOS: forma própria na leitura
    proprios = {"series": "serie", "prove": "provar", "induced": "induzida"}
    for pt, en in EM_INGLES.items():
        assert VERBOS.get(en, proprios.get(en)) == pt, (en, pt)
    esperados = {EM_INGLES.get(v, v) for v in _canonicos()}
    faltam = esperados - _verbos_listados(MANUAL_EN)
    assert not faltam, f"verbos fora da lista do manual em inglês: {sorted(faltam)}"
