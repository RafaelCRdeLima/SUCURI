"""Os exercícios da apostila, executados.

Pelo mesmo motivo do manual, e com mais razão: a apostila diz, exercício por
exercício, o que o Sucuri resolve. Se isso deixar de ser verdade, a suíte
para — e a apostila é corrigida, ou o programa.

Aqui a saída anunciada é conferida com mais rigor que no manual: quando ela é
a resposta inteira de um verbo (`0`, `-24`, `2/a**2`), tem de ser a resposta
exata, e não um pedaço qualquer do que saiu.
"""

import pathlib

import pytest

from sucuri.caderno import Caderno
from test_manual import Leitor, tudo_que_saiu

APOSTILA = (pathlib.Path(__file__).parents[1] / "sucuri" / "interface"
            / "estatico" / "apostila.html")


TUTORIAL = APOSTILA.with_name("tutorial.html")


def exercicios(pagina=None):
    leitor = Leitor()
    leitor.feed((pagina or APOSTILA).read_text(encoding="utf-8"))
    assert leitor.exemplos, "nenhum exercício encontrado na apostila"
    return leitor.exemplos


def _pares():
    """Cada exercício da apostila com o seu gêmeo do tutorial, em inglês."""
    pt, en = exercicios(), exercicios(TUTORIAL)
    assert len(pt) == len(en), "a apostila e o tutorial têm exercícios diferentes"
    return list(zip(pt, en))


def _confere(exemplo, d, pagina):
    esperado = exemplo["saida"]
    exatos = [d.get("exato"), d.get("sympy")]
    if esperado in exatos:
        return
    saida = tudo_que_saiu(d)
    assert not d.get("erro") or exemplo["especie"] == "erro-esperado", d.get("erro")
    # Resposta curta só vale inteira: "0" dentro de "10" não é resposta.
    assert len(esperado) > 3, (
        f"{pagina} anuncia {esperado!r} e a resposta foi {exatos!r}")
    assert esperado in saida, (
        f"{pagina} anuncia {esperado!r}\nmas a saída foi {saida[:400]!r}")


@pytest.mark.parametrize("par", _pares(),
                         ids=lambda p: p[0]["entradas"][-2][:40])
def test_o_exercicio_da_apostila_sai(par):
    """Uma conta só, conferida nas duas línguas: o tutorial roda as entradas
    em inglês — que o motor lê como as da apostila — e a mesma resposta tem
    de trazer a saída da apostila e, traduzida, a do tutorial."""
    from sucuri.idioma import traduzir_resposta
    pt, en = par
    assert len(pt["entradas"]) == len(en["entradas"])
    caderno = Caderno()
    d = {}
    for fonte in en["entradas"]:
        d = caderno.executar(fonte).to_dict()
    _confere(pt, d, "a apostila")
    _confere(en, traduzir_resposta(d, "en"), "o tutorial")


@pytest.mark.parametrize("pagina", [APOSTILA, TUTORIAL], ids=lambda p: p.name)
def test_a_apostila_esta_publicada(pagina):
    web = pathlib.Path(__file__).parents[1] / "web" / pagina.name
    assert web.read_text(encoding="utf-8") == pagina.read_text(encoding="utf-8")


@pytest.mark.parametrize("pagina", [APOSTILA, TUTORIAL], ids=lambda p: p.name)
def test_o_placar_confere_com_os_titulos(pagina):
    """Os totais da tabela são os das marcações dos exercícios — contados, e
    não escritos à mão. Um placar que diverge dos títulos engana quem lê."""
    import re
    s = pagina.read_text(encoding="utf-8")
    corpo = s[s.index('<h2 id="indicial">'):s.index('<h2 id="nao-sai">')]
    status = {}
    for h in re.findall(r"<h3>(.*?)</h3>", corpo):
        cab = h.split(".")[0]
        if "–" in cab:
            a, b = map(int, cab.split("–"))
            nums = list(range(a, b + 1))
        else:
            nums = [int(x) for x in re.findall(r"\d+", cab)]
        pills = re.findall(r'pill (ok|aviso)">[^<]*</span>(?:\s*\(([^)]*)\))?', h)
        if len(pills) == 1 and not pills[0][1]:
            for n in nums:
                status.setdefault(n, pills[0][0])
        else:
            for p, lista in pills:
                for n in re.findall(r"\d+", lista):
                    status.setdefault(int(n), p)
    v = s[s.index('<h2 id="nao-sai">'):s.index('<h2 id="achados">')]
    nao = set()
    for li in re.findall(r"<li><strong>([^<]*)</strong>", v):
        if "em parte" not in li and "partly" not in li:
            nao |= {int(x) for x in re.findall(r"\d+", li.split("(")[0])}
    assert not (nao & set(status)), "exercício com resolução e também em 'não sai'"
    assert set(range(1, 86)) == set(status) | nao, "exercício sem marcação"
    resolve = sum(1 for p in status.values() if p == "ok")
    parte = sum(1 for p in status.values() if p == "aviso")
    total = re.search(r"total \(85\)</strong></td><td><strong>(\d+)</strong></td>"
                      r"<td><strong>(\d+)</strong></td><td><strong>(\d+)</strong>", s)
    assert tuple(map(int, total.groups())) == (resolve, parte, len(nao))
