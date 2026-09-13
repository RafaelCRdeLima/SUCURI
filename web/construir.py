"""Monta a pasta que vai para o ar.

A versão online não é uma segunda implementação: é o mesmo pacote Python,
empacotado num zip que o Pyodide desempacota dentro do navegador, e a mesma
folha e o mesmo `sucuri.js` da interface local. Este script copia e empacota —
não escreve código nenhum, de propósito, porque código copiado à mão diverge.

    python web/construir.py

Depois, `web/` é uma pasta estática: dá para servir de qualquer lugar, e é o
que se publica no Cloudflare Pages.
"""

import hashlib
import pathlib
import shutil
import urllib.request
import zipfile

AQUI = pathlib.Path(__file__).parent
RAIZ = AQUI.parent
PACOTE = RAIZ / "sucuri"
ESTATICO = PACOTE / "interface" / "estatico"

ANTLR = "antlr4_python3_runtime-4.11.1-py3-none-any.whl"
ANTLR_URL = ("https://files.pythonhosted.org/packages/py3/a/"
             "antlr4-python3-runtime/" + ANTLR)

# O que a interface local e a online compartilham, byte a byte.
COMPARTILHADO = ["sucuri.css", "sucuri.js", "caderno.css", "caderno.js",
                 "tokens.css", "favicon.svg"]

# As páginas: as mesmas da interface local, com a tela de carregamento
# injetada. Gerar em vez de copiar à mão é o que impede as duas versões de
# divergirem sem ninguém perceber.
PAGINAS = ["index.html", "caderno.html"]


def motor_zip():
    """O pacote `sucuri`, só o Python, para o Pyodide desempacotar.

    Fora: os estáticos da interface local (o navegador já tem os seus) e os
    caches. O zip é determinístico — mesma data para todos os membros — para
    que reconstruir sem mudar fonte não gere arquivo diferente.
    """
    destino = AQUI / "sucuri-motor.zip"
    arquivos = sorted(p for p in PACOTE.rglob("*.py")
                      if "__pycache__" not in p.parts)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for p in arquivos:
            info = zipfile.ZipInfo(str(p.relative_to(RAIZ)), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return destino, arquivos


def _pedaco(texto, nome):
    """Recorte por marcador, nunca por busca de tag.

    Procurar o primeiro "</div>" para achar o fim de um bloco funciona até o
    bloco ter divs dentro — e aí o recorte corta no meio, o HTML sai
    desbalanceado, e o estrago aparece longe da causa.
    """
    ini = texto.index(f"<!-- SUCURI:{nome} -->") + len(f"<!-- SUCURI:{nome} -->")
    fim = texto.index(f"<!-- /SUCURI:{nome} -->")
    return texto[ini:fim].strip()


def paginas():
    """Cada página local vira a página online, com a tela de carregamento."""
    partes = (AQUI / "_carregando.html").read_text(encoding="utf-8")
    estilo = _pedaco(partes, "estilo")
    overlay = _pedaco(partes, "overlay")
    ganchos = _pedaco(partes, "ganchos")

    for nome in PAGINAS:
        html = (ESTATICO / nome).read_text(encoding="utf-8")
        html = html.replace("</head>", estilo + "\n</head>", 1)
        html = html.replace("<body>", "<body>\n\n" + overlay, 1)
        html = html.replace('<script src="vendor/katex/katex.min.js"></script>',
                            ganchos + '\n<script src="vendor/katex/katex.min.js"></script>',
                            1)
        (AQUI / nome).write_text(html, encoding="utf-8")
    print(f"páginas geradas: {', '.join(PAGINAS)}")


def impressao(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()[:16]


def main():
    destino, arquivos = motor_zip()
    print(f"{destino.name}: {len(arquivos)} arquivos, "
          f"{destino.stat().st_size // 1024} kB, {impressao(destino)}")

    paginas()

    for nome in COMPARTILHADO:
        shutil.copy2(ESTATICO / nome, AQUI / nome)
    print(f"copiados da interface local: {', '.join(COMPARTILHADO)}")

    katex = AQUI / "vendor" / "katex"
    if katex.exists():
        shutil.rmtree(katex)
    shutil.copytree(ESTATICO / "vendor" / "katex", katex)
    print("KaTeX copiado")

    roda = AQUI / "vendor" / ANTLR
    if not roda.exists():
        print(f"baixando {ANTLR}…")
        urllib.request.urlretrieve(ANTLR_URL, roda)
    print(f"{ANTLR}: {roda.stat().st_size // 1024} kB")

    total = sum(p.stat().st_size for p in AQUI.rglob("*") if p.is_file())
    print(f"\nweb/ pronta: {total // 1024} kB no total")


if __name__ == "__main__":
    main()
