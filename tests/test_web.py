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


@pytest.mark.parametrize("pagina", ["index.html", "caderno.html"])
def test_a_pagina_so_pede_arquivos_que_existem(pagina):
    html = (WEB / pagina).read_text(encoding="utf-8")
    pedidos = re.findall(r'(?:src|href)="([^"]+)"', html)
    locais = [p for p in pedidos if not p.startswith(("http:", "https:", "data:"))]
    assert locais
    faltando = [p for p in locais if not (WEB / p).exists()]
    assert not faltando, f"{pagina} pede o que não está lá: {faltando}"


def test_as_paginas_publicadas_sao_geradas_das_locais():
    """Gerar em vez de copiar à mão é o que impede as duas versões de
    divergirem sem ninguém perceber. Este teste refaz a geração e compara.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("construir", WEB / "construir.py")
    construir = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(construir)

    antes = {n: (WEB / n).read_text(encoding="utf-8") for n in construir.PAGINAS}
    construir.paginas()
    for nome, conteudo in antes.items():
        assert (WEB / nome).read_text(encoding="utf-8") == conteudo, nome


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


def test_o_botao_de_modulos_so_aparece_se_tiver_o_que_mostrar():
    """Um botão que abre um painel com um módulo indisponível e uma operação
    que já está no botão ao lado não paga o espaço que ocupa. A regra fica
    explícita no JavaScript, e este teste guarda as duas metades dela:
    esconder quando não sobra nada, e não anunciar o que não está instalado.
    """
    js = (ESTATICO / "sucuri.js").read_text(encoding="utf-8")
    assert "JA_OFERECIDO" in js
    assert "resolver: ['resolver', 'padrões']" in js
    assert "$('abrir-modulos').hidden = true" in js
    # o painel filtra por disponibilidade antes de listar
    assert js.count("m.disponivel && sobra(m).length") == 2


@pytest.mark.parametrize("pagina", ["index.html", "caderno.html"])
def test_a_tela_de_carregamento_fecha_antes_da_pagina(pagina):
    """O defeito que virou "a página some do nada".

    A tela de carregamento era recortada procurando o primeiro "</div>" — e ela
    tem divs dentro. O recorte cortava no meio; o navegador fechava a div
    sozinho; a página inteira virava FILHA de #carregando; e no instante em que
    o motor ficava pronto, a regra .pronto{display:none} sumia com tudo.

    O sintoma aparecia longe da causa, que é o que torna esse tipo de erro
    caro: não havia nada de errado com a página, só com o recorte dela.
    """
    html = (WEB / pagina).read_text(encoding="utf-8")
    assert 'id="passo"' in html and 'id="barra"' in html

    trecho = html[html.index('<div id="carregando">'):html.index('<div class="app">')]
    assert trecho.count("<div") == trecho.count("</div>"), (
        f"{pagina}: a tela de carregamento não fecha antes da página")


@pytest.mark.parametrize("pagina", ["index.html", "caderno.html"])
def test_as_paginas_publicadas_tem_as_divs_balanceadas(pagina):
    html = (WEB / pagina).read_text(encoding="utf-8")
    assert html.count("<div") == html.count("</div>"), pagina
