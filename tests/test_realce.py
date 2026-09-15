"""A lista de verbos da tela e a do programa são a mesma lista.

Duas listas iguais escritas em dois lugares divergem — é questão de tempo. Se
a tela pintar de verde um verbo que o Python não conhece, ela promete uma ação
que não acontece; se deixar de pintar um que existe, esconde o que age. Os dois
enganos são do mesmo tipo: a cor dizendo do programa uma coisa que não é.
"""

import pathlib
import re

from sucuri.caderno import VERBOS

TELA = (pathlib.Path(__file__).parents[1] / "sucuri" / "interface"
        / "estatico" / "caderno.js")


def da_tela():
    texto = TELA.read_text(encoding="utf-8")
    bloco = re.search(r"var VERBOS = \[(.*?)\];", texto, re.S)
    assert bloco, "a lista de verbos sumiu do caderno.js"
    return {n for n in re.findall(r"'([^']+)'", bloco.group(1))}


def test_a_tela_conhece_os_mesmos_verbos():
    assert da_tela() == set(VERBOS)


def test_o_realce_so_pinta_na_posicao_de_comando():
    r"""`resolver(eq1)` age; `r` vezes o resto de uma equação não.

    A regex da tela exige o parêntese e o começo da célula — pintar a palavra
    onde quer que ela apareça diria que ela age onde não age.
    """
    texto = TELA.read_text(encoding="utf-8")
    achado = re.search(r"var RE_VERBO = new RegExp\((.*?)\);", texto, re.S)
    assert achado, "a regra do realce sumiu"
    regra = achado.group(1)
    assert regra.lstrip().startswith("'^"), "o realce não está ancorado no começo"
    assert "\\\\(" in regra, "o realce não exige o parêntese do comando"


def test_a_camada_de_realce_tem_a_metrica_do_campo():
    """Medidas diferentes quebram a linha em lugar diferente, e o texto dobra."""
    css = (TELA.parent / "caderno.css").read_text(encoding="utf-8")
    regra = re.search(r"\.editor \.realce,\.celula \.editor textarea\{([^}]*)\}",
                      css)
    assert regra, "a regra compartilhada das duas camadas sumiu"
    for medida in ("padding", "font-family", "font-size", "line-height",
                   "border", "white-space"):
        assert medida in regra.group(1), f"{medida} não é compartilhada"
