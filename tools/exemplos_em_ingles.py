"""Os exemplos executados de uma página em português, na versão em inglês.

    python tools/exemplos_em_ingles.py apostila.html tutorial.html
    python tools/exemplos_em_ingles.py manual.html manual-en.html

A página em inglês é a tradução da prosa, com as entradas e as saídas ainda em
português. Este script reescreve cada entrada com os comandos em inglês, roda
no motor em inglês, e troca a saída anunciada pela mesma saída traduzida —
conferindo que ela aparece de fato no que o motor respondeu. O que não confere
é listado, e não escrito: uma saída anunciada que não sai é o que os testes
existem para impedir.
"""

import html
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from sucuri.caderno import Caderno  # noqa: E402
from sucuri.idioma import traduzir, traduzir_resposta  # noqa: E402
from test_manual import tudo_que_saiu  # noqa: E402

ESTATICO = RAIZ / "sucuri" / "interface" / "estatico"

# português → inglês, na posição de comando
VERBOS = {
    "provar": "prove", "resolver": "solve", "avaliar": "evaluate",
    "simplificar": "simplify", "exportar": "export", "separar": "separate",
    "conferir": "check", "verificar": "check", "contrair": "contract",
    "expandir": "expand", "independentes": "independent", "linearizar": "linearize",
    "geodesicas": "geodesics", "geodésicas": "geodesics", "série": "series",
    "serie": "series", "em_componentes": "in_components", "em_carta": "in_chart",
    "orbitas": "orbits", "órbitas": "orbits", "elemento": "element",
    "colchete": "bracket", "laplaciano": "laplacian", "restringir": "restrict",
    "cunha": "wedge", "estrela": "star", "iguais": "equal", "escalar": "scalar",
    "curvatura": "scalar", "tetrada": "tetrad", "tétrada": "tetrad",
    "métrica": "metric", "metrica": "metric", "coordenadas": "coordinates",
    "coordenada": "coordinates", "campo": "field", "covetor": "covector",
    "forma": "form", "induzida": "induced", "índices": "indices", "indexar": "indices",
}
ESPECIES = {"constante": "constant", "curvatura": "curvature", "símbolo": "symbol",
            "simbolo": "symbol", "índices": "indices", "índice": "indices",
            "coordenadas": "coordinates", "métrica": "metric", "metrica": "metric"}
SIMETRIAS = {"antissimétrico": "antisymmetric", "antissimetrico": "antisymmetric",
             "anti-simétrico": "antisymmetric", "simétrico": "symmetric",
             "simetrico": "symmetric"}

_RE_VERBO = re.compile(r"^(\s*(?:\\?[A-Za-z]\w*\s*=\s*)?)(" + "|".join(
    sorted(map(re.escape, VERBOS), key=len, reverse=True)) + r")(\s*\()")
_RE_ESPECIE = re.compile(r"^(\s*(?:\\?[A-Za-z]\w*)(?:\s*,\s*\\?[A-Za-z]\w*)*\s*=\s*)("
                         + "|".join(map(re.escape, ESPECIES)) + r")(\s*(?:\(\s*\w+\s*\))?\s*)$")
_RE_SIMETRIA = re.compile(r"(tensor\s*\([^)]*,\s*)(" + "|".join(map(re.escape, SIMETRIAS)) + r")(\s*\))")
_RE_LEVI = re.compile(r"levi-civita\(símbolo\)")


def para_ingles(fonte):
    """Uma linha de entrada com os comandos em inglês."""
    saida = []
    for linha in fonte.split("\n"):
        linha = _RE_SIMETRIA.sub(lambda m: m.group(1) + SIMETRIAS[m.group(2)] + m.group(3), linha)
        linha = _RE_LEVI.sub("levi-civita(symbol)", linha)
        m = _RE_ESPECIE.match(linha)
        if m:
            linha = m.group(1) + ESPECIES[m.group(2)] + m.group(3)
        else:
            m = _RE_VERBO.match(linha)
            if m:
                linha = m.group(1) + VERBOS[m.group(2)] + m.group(3) + linha[m.end():]
        saida.append(linha)
    return "\n".join(saida)


_RE_ENTRADA = re.compile(r'(<code class="entrada">)(.*?)(</code>)', re.S)
_RE_SAIDA = re.compile(r'(<samp class="(?:saida|erro-esperado|pergunta)">)(.*?)(</samp>)', re.S)
_RE_EXEMPLO = re.compile(r'<div class="exemplo">.*?</div>', re.S)


def converter(pt_nome, en_nome, escrever=True):
    en_caminho = ESTATICO / en_nome
    texto = en_caminho.read_text(encoding="utf-8")
    problemas = []

    def exemplo(m):
        bloco = m.group(0)
        entradas = [html.unescape(e) for _, e, _ in _RE_ENTRADA.findall(bloco)]
        saidas = _RE_SAIDA.findall(bloco)
        novas = [para_ingles(e) for e in entradas]
        c = Caderno()
        d = {}
        for f in novas:
            d = traduzir_resposta(c.executar(f).to_dict(), "en")
        tudo = tudo_que_saiu(d) + " " + str(d.get("exato")) + " " + str(d.get("sympy"))
        it = iter(novas)
        bloco = _RE_ENTRADA.sub(lambda e: e.group(1) + html.escape(next(it), quote=False) + e.group(3), bloco)
        for abre, anunciado, fecha in saidas:
            pt = html.unescape(anunciado)
            en = traduzir(pt, "en")
            if en not in tudo and pt in tudo:
                en = pt
            if en not in tudo:
                problemas.append((novas[-1], pt, en, tudo[:300]))
            bloco = bloco.replace(abre + anunciado + fecha, abre + html.escape(en, quote=False) + fecha, 1)
        return bloco

    novo = _RE_EXEMPLO.sub(exemplo, texto)
    if escrever:
        en_caminho.write_text(novo, encoding="utf-8")
    return problemas


def codigo_na_prosa(en_nome):
    """`<code>provar</code>` na prosa: o nome do comando em inglês."""
    caminho = ESTATICO / en_nome
    texto = caminho.read_text(encoding="utf-8")

    def troca(m):
        dentro = html.unescape(m.group(1))
        if not re.match(r"^\s*(?:\\?[A-Za-z]\w*\s*(?:,\s*\\?[A-Za-z]\w*\s*)*=\s*)?[^\W\d][\w-]*", dentro):
            return m.group(0)
        novo = para_ingles(dentro)
        palavra = re.fullmatch(r"([^\W\d]\w*)(\(.*\))?", novo.strip(), re.S)
        if palavra and palavra.group(1) in VERBOS:
            novo = VERBOS[palavra.group(1)] + (palavra.group(2) or "")
        return "<code>" + html.escape(novo, quote=False) + "</code>"

    texto = re.sub(r"<code>(.*?)</code>", troca, texto, flags=re.S)
    caminho.write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    pt_nome, en_nome = sys.argv[1:3]
    codigo_na_prosa(en_nome)
    problemas = converter(pt_nome, en_nome)
    for entrada, pt, en, saiu in problemas:
        print(f"--- {entrada[:70]!r}\n   anunciado: {pt[:120]!r}\n   em inglês: {en[:120]!r}\n   saiu: {saiu[:200]!r}")
    print(f"{len(problemas)} saídas a revisar")
