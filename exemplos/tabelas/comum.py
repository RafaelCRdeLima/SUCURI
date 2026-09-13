"""O que as duas auditorias de tabela compartilham: a fonte e o relato.

A tabela é sempre externa. Tabela escrita por quem escreve o leitor testa o
leitor contra si mesmo; a da Wikipédia foi escrita por outra gente, para outro
fim, e por isso usa notação que ninguém aqui teria lembrado de prever.

Baixa-se o **wikitexto**, não o HTML renderizado: o LaTeX como o autor
escreveu. HTML já é interpretação.
"""

import json
import pathlib
import re
import urllib.request

import sympy as sp

AQUI = pathlib.Path(__file__).parent
API = ("https://en.wikipedia.org/w/api.php?action=parse"
       "&page={pagina}&prop=wikitext&format=json")

# A Wikipédia recusa o agente padrão do urllib; a política dela pede que o
# agente identifique quem chama.
AGENTE = "sucuri-teste/0.1 (https://github.com/RafaelCRdeLima; leitor de notação)"

# Condições de domínio e prosa que acompanham as entradas. Retiro-as porque não
# são matéria do leitor de notação — mas o campo 'origem' guarda o texto inteiro.
_APARAS = [
    r",?\s*\\q?quad\s*\\text\{[^}]*\}.*$",       # \qquad\text{(for } n\neq -1
    r",?\s*\\q?quad\s+.*$",                       # \qquad c > 0
    r",?\s*\\text\{[^}]*\}.*$",
    r"\s*[,.]\s*$",
]


def baixar(pagina):
    pedido = urllib.request.Request(API.format(pagina=pagina),
                                    headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=60) as r:
        return json.load(r)["parse"]["wikitext"]["*"]


def blocos(wikitexto):
    return [b.strip() for b in
            re.findall(r"<math[^>]*>(.*?)</math>", wikitexto, re.S)]


def aparar(latex):
    for padrao in _APARAS:
        latex = re.sub(padrao, "", latex).strip()
    return latex


def _partir(latex):
    """Parte no '=' de primeiro nível.

    Partir no '=' sem olhar a profundidade quebraria \\sum_{k=0}^{n} ao meio — e
    uma alegação partida ao meio vira uma alegação falsa, que é pior do que uma
    alegação não lida.
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


def alegacoes(bloco):
    """Uma entrada de tabela pode conter várias alegações encadeadas.

        \\int \\tan x\\,dx = \\ln|\\sec x| + C = -\\ln|\\cos x| + C

    são duas alegações sobre a mesma integral, e conto as duas.
    """
    if r"\begin{align}" in bloco or "=" not in bloco:
        return []
    partes = [aparar(p) for p in _partir(bloco)]
    if any(not p for p in partes):
        return []
    return [(partes[0], d) for d in partes[1:]]


def recolher(pagina, arquivo, interessa):
    """Baixa a página, extrai as alegações que `interessa` aceita, grava."""
    wikitexto = baixar(pagina)
    (AQUI / f"wikitexto-{arquivo}.txt").write_text(wikitexto, encoding="utf-8")

    tabela = []
    for bloco in blocos(wikitexto):
        for esquerda, direita in alegacoes(bloco):
            if interessa(esquerda):
                tabela.append({"origem": bloco.replace("\n", " "),
                               "esquerda": esquerda, "direita": direita})

    destino = AQUI / f"{arquivo}.json"
    destino.write_text(json.dumps(
        {"fonte": API.format(pagina=pagina), "entradas": tabela},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(tabela)} alegações gravadas em {destino.name}")
    return tabela


def carregar(arquivo):
    caminho = AQUI / f"{arquivo}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))["entradas"]


# ------------------------------------------------------- prova e veredito

PROVADA = "provada"
PROVADA_QUASE = "provada fora de pontos isolados"


def funcoes_indefinidas(e):
    return {a.func for a in e.atoms(sp.core.function.AppliedUndef)}


def reais(expr):
    """A tabela fala de variável real; sem isso |x| não deriva.

    É suposição, e fica declarada aqui em vez de implícita — regra da casa.

    Aplica-se só à DIFERENÇA, nunca à equação inteira: trocar uma variável
    LIGADA dentro de uma integral não troca símbolo nenhum. O SymPy entende a
    troca como limite novo, e Integral(f(x), (x,)) vira Integral(f(x), (x, x)).
    """
    troca = {s: sp.Symbol(s.name, real=True)
             for s in expr.free_symbols if not s.assumptions0.get("real")}
    return expr.subs(troca, simultaneous=True) if troca else expr


def anula(diferenca):
    """A diferença é zero? E se não é em toda parte, onde deixa de ser?

    Uma tabela diz "∫dx/x = ln|x| + C" sem repetir "para x ≠ 0" — a condição
    está no ar da página. O veredito separado registra isso em vez de fingir
    que a identidade vale em toda parte ou que a entrada está errada.
    """
    if diferenca == 0:
        return PROVADA, "0"
    if isinstance(diferenca, sp.Piecewise):
        padrao = [e for e, cond in diferenca.args if cond == sp.true]
        if padrao and all(e == 0 for e in padrao):
            excecoes = [str(cond) for e, cond in diferenca.args if cond != sp.true]
            return PROVADA_QUASE, "exceto onde " + ", ".join(excecoes)
    return None, sp.sstr(diferenca)


def relatar(linhas, ordem, sempre_com_motivo=()):
    """O relatório, agrupado por veredito."""
    contagem = {}
    for veredito, _, _ in linhas:
        contagem[veredito] = contagem.get(veredito, 0) + 1

    verboso = "--verboso" in __import__("sys").argv
    for veredito in ordem:
        do_grupo = [l for l in linhas if l[0] == veredito]
        if not do_grupo:
            continue
        print(f"\n### {veredito}  ({len(do_grupo)})")
        for _, entrada, motivo in do_grupo:
            print(f"  {(entrada['esquerda'] + ' = ' + entrada['direita'])[:78]}")
            if verboso or veredito in sempre_com_motivo:
                print(f"      {motivo[:120]}")

    print(f"\n{'-' * 62}\n{len(linhas)} alegações da tabela")
    for veredito in ordem:
        if veredito in contagem:
            print(f"  {contagem[veredito]:3}  {veredito}")
    return contagem
