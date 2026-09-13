"""A pasta que vai para o ar.

Publicar é a operação mais fácil de fazer errado em silêncio: basta o zip do
motor estar velho, ou um arquivo referenciado não subir junto, e o que o
usuário recebe não é o que foi revisado. Estes testes conferem que a pasta
`web/` é, byte a byte, o que está no repositório.
"""

import pathlib
import re
import zipfile

import pytest

RAIZ = pathlib.Path(__file__).parents[1]
WEB = RAIZ / "web"
PACOTE = RAIZ / "sucuri"
ESTATICO = PACOTE / "interface" / "estatico"

pytestmark = pytest.mark.skipif(not WEB.exists(), reason="sem pasta web/")


def test_o_zip_do_motor_e_o_pacote():
    """Zip velho é a forma mais silenciosa de publicar código que ninguém viu.

    Roda `python web/construir.py` quando este teste falhar.
    """
    fonte = {str(p.relative_to(RAIZ)): p.read_bytes()
             for p in PACOTE.rglob("*.py") if "__pycache__" not in p.parts}
    with zipfile.ZipFile(WEB / "sucuri-motor.zip") as z:
        publicado = {n: z.read(n) for n in z.namelist()}

    assert set(publicado) == set(fonte), "o zip não tem os mesmos arquivos"
    diferentes = [n for n in fonte if publicado[n] != fonte[n]]
    assert not diferentes, f"desatualizados no zip: {diferentes}"


def test_a_interface_publicada_e_a_interface_local():
    """A versão online não é uma segunda implementação: é a mesma folha, o
    mesmo JavaScript e o mesmo KaTeX."""
    for nome in ["sucuri.css", "sucuri.js", "tokens.css", "favicon.svg"]:
        assert (WEB / nome).read_bytes() == (ESTATICO / nome).read_bytes(), nome

    local = {p.name for p in (ESTATICO / "vendor" / "katex").rglob("*") if p.is_file()}
    publicado = {p.name for p in (WEB / "vendor" / "katex").rglob("*") if p.is_file()}
    assert local == publicado


def test_a_pagina_so_pede_arquivos_que_existem():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    pedidos = re.findall(r'(?:src|href)="([^"]+)"', html)
    locais = [p for p in pedidos if not p.startswith(("http:", "https:", "data:"))]
    assert locais
    faltando = [p for p in locais if not (WEB / p).exists()]
    assert not faltando, f"a página pede o que não está lá: {faltando}"


def test_o_motor_so_pede_arquivos_que_existem():
    js = (WEB / "motor.js").read_text(encoding="utf-8")
    for caminho in re.findall(r"(?:fetch|desempacotar)\(\s*'([^']+)'", js):
        assert (WEB / caminho).exists(), caminho


def test_o_transporte_nao_colide_com_a_interface():
    """O erro que custou uma depuração: `transporte.js` guardava estado numa
    variável chamada `convencoes`, e `sucuri.js` tem uma FUNÇÃO com esse nome.
    A primeira leitura sobrescrevia a função com um objeto — a página pintava o
    primeiro resultado e nenhum outro, sem uma palavra no console.

    Os dois arquivos dividem o espaço global, então nome repetido é colisão.
    """
    def globais(caminho):
        fonte = caminho.read_text(encoding="utf-8")
        return set(re.findall(r"^(?:var|function)\s+([A-Za-z_$][\w$]*)", fonte, re.M))

    interface = globais(ESTATICO / "sucuri.js")
    for transporte in [WEB / "transporte.js", ESTATICO / "transporte.js"]:
        colisoes = globais(transporte) & interface
        assert not colisoes, f"{transporte.name} colide em {sorted(colisoes)}"


def test_a_roda_do_antlr_vai_junto():
    """Sem ela o parse_latex não existe no navegador, e o programa inteiro é o
    parse_latex."""
    rodas = list((WEB / "vendor").glob("antlr4*.whl"))
    assert len(rodas) == 1
    assert rodas[0].stat().st_size > 100_000
