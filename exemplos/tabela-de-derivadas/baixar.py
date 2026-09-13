"""Baixa uma tabela de derivadas real e a põe em forma de lista de alegações.

A fonte é externa de propósito: uma tabela escrita por outra pessoa, para
outro fim, é o único teste honesto de um leitor de notação. Tabela escrita
por quem escreve o leitor testa o leitor contra si mesmo.

    python baixar.py        # grava wikitexto.txt e tabela.json

Fonte: en.wikipedia.org/wiki/Differentiation_rules (CC BY-SA 4.0), via a API
de wikitexto, que devolve o LaTeX como o autor o escreveu — não o HTML
renderizado, que já é interpretação.
"""

import json
import pathlib
import re
import urllib.request

AQUI = pathlib.Path(__file__).parent
FONTE = ("https://en.wikipedia.org/w/api.php?action=parse"
         "&page=Differentiation_rules&prop=wikitext&format=json")

# Condições de domínio e prosa que acompanham as entradas. Retiro-as porque
# não são matéria do leitor de notação — mas registro o que foi retirado.
_APARAS = [
    r",?\s*\\q?quad\s*\\text\{[^}]*\}.*$",      # \qquad\text{and}\qquad ...
    r",?\s*\\q?quad\s+.*$",                      # \qquad c > 0
    r"\s*[,.]\s*$",
]


# A Wikipédia recusa o agente padrão do urllib; a política dela pede que o
# agente identifique quem chama.
AGENTE = "sucuri-teste/0.1 (https://github.com/RafaelCRdeLima; leitor de notação)"


def baixar():
    pedido = urllib.request.Request(FONTE, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=60) as r:
        return json.load(r)["parse"]["wikitext"]["*"]


def blocos(wikitexto):
    return [b.strip() for b in
            re.findall(r"<math[^>]*>(.*?)</math>", wikitexto, re.S)]


def aparar(latex):
    for padrao in _APARAS:
        latex = re.sub(padrao, "", latex).strip()
    return latex


def alegacoes(bloco):
    """Uma entrada de tabela pode conter várias alegações encadeadas.

        d/dx tan x = sec^2 x = 1/cos^2 x = 1 + tan^2 x

    são três alegações sobre a mesma derivada, e conto as três.
    """
    if r"\begin{align}" in bloco or "=" not in bloco:
        return []
    partes = [aparar(p) for p in _partir(bloco)]
    if any(not p for p in partes):
        return []
    esquerda = partes[0]
    return [(esquerda, d) for d in partes[1:]]


def _partir(latex):
    """Parte no '=' de primeiro nível.

    Partir no '=' sem olhar a profundidade quebraria \\sum_{k=0}^{n} ao meio —
    e uma alegação partida ao meio vira uma alegação falsa, que é pior do que
    uma alegação não lida.
    """
    partes, atual, fundo = [], [], 0
    for c in latex:
        if c in "{[":
            fundo += 1
        elif c in "}]":
            fundo -= 1
        if c == "=" and fundo == 0:
            partes.append("".join(atual))
            atual = []
        else:
            atual.append(c)
    partes.append("".join(atual))
    return partes


def derivada(latex):
    """A entrada fala de uma derivada?"""
    return bool(re.search(r"\\frac\s*\{\s*d|\\partial|'", latex))


def main():
    wikitexto = baixar()
    (AQUI / "wikitexto.txt").write_text(wikitexto, encoding="utf-8")

    tabela = []
    for bloco in blocos(wikitexto):
        for esquerda, direita in alegacoes(bloco):
            if derivada(esquerda):
                tabela.append({"origem": bloco.replace("\n", " "),
                               "esquerda": esquerda, "direita": direita})

    (AQUI / "tabela.json").write_text(
        json.dumps({"fonte": FONTE, "entradas": tabela},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(tabela)} alegações gravadas em tabela.json")


if __name__ == "__main__":
    main()
