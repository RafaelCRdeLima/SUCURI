r"""Inglês: os comandos em inglês na entrada, e as mensagens em inglês na saída.

O motor fala português por dentro — as mensagens estão onde o erro acontece, e
é lá que devem ficar, perto do porquê. O inglês é uma camada nas duas pontas:

- na ENTRADA, `g = metric(…)`, `prove(eq3, eq1)`, `\alpha = form(dr)` viram as
  palavras do caderno antes da leitura. Valem sempre, em qualquer idioma: um
  comando não muda de sentido com a língua da tela;
- na SAÍDA, cada mensagem é casada com os moldes do código (as f-strings, com os
  valores no lugar das chaves) e trocada pelo molde em inglês de
  `mensagens_en.EN`, com os valores traduzidos também — uma mensagem montada de
  pedaços é traduzida pedaço a pedaço.

O que é matemática — `latex`, `sympy`, `exato`, a fonte — não passa pela tradução.
"""

from __future__ import annotations

import functools
import re

IDIOMAS = ("pt", "en")

# ------------------------------------------------------------ a entrada

# Verbos em posição de comando: `nome = verbo(` ou `verbo(` no começo da linha.
_VERBOS_EN = {
    "metric": "métrica", "coordinates": "coordenadas", "coordinate": "coordenadas",
    "field": "campo", "covector": "covetor", "form": "forma",
    "induced": "induzida", "wedge": "cunha", "star": "estrela", "equal": "iguais",
    "bracket": "colchete", "laplacian": "laplaciano", "restrict": "restringir",
    "in_chart": "em_carta", "in_components": "em_componentes",
    "orbits": "orbitas", "element": "elemento", "tetrad": "cartan",
    "scalar": "escalar", "indices": "índices", "index": "índices",
    "determinant": "det",
}
# Espécies: `nomes = espécie`, sem parêntese.
_ESPECIES_EN = {
    "constant": "constante", "curvature": "curvatura", "symbol": "símbolo",
    "indices": "índices", "index": "índices", "coordinates": "coordenadas",
    "metric": "métrica",
}
_SIMETRIAS_EN = {"antisymmetric": "antissimétrico", "anti-symmetric": "antissimétrico",
                 "symmetric": "simétrico"}

_RE_VERBO = re.compile(r"^(\s*(?:\\?[A-Za-z]\w*\s*=\s*)?)(" + "|".join(
    sorted(map(re.escape, _VERBOS_EN), key=len, reverse=True)) + r")(\s*\()", re.I)
_RE_ESPECIE = re.compile(r"^(\s*(?:\\?[A-Za-z]\w*)(?:\s*,\s*\\?[A-Za-z]\w*)*\s*=\s*)("
                         + "|".join(_ESPECIES_EN) + r")(\s*(?:\(\s*\w+\s*\))?\s*)$", re.I)
_RE_SIMETRIA = re.compile(r"^(\s*\\?[A-Za-z]\w*\s*=\s*tensor\s*\([^)]*,\s*)("
                          + "|".join(map(re.escape, _SIMETRIAS_EN)) + r")(\s*\)\s*)$", re.I)


def normalizar_entrada(fonte):
    """Os comandos em inglês com as palavras do caderno. Só na posição de
    comando: `form` dentro de uma equação continua sendo f·o·r·m."""
    if not isinstance(fonte, str):
        return fonte
    m = _RE_SIMETRIA.match(fonte)
    if m:
        return m.group(1) + _SIMETRIAS_EN[m.group(2).lower()] + m.group(3)
    m = _RE_ESPECIE.match(fonte)
    if m:
        return m.group(1) + _ESPECIES_EN[m.group(2).lower()] + m.group(3)
    m = _RE_VERBO.match(fonte)
    if m:
        return m.group(1) + _VERBOS_EN[m.group(2).lower()] + m.group(3) + fonte[m.end():]
    return fonte


# ------------------------------------------------------------- a saída

# Só estas chaves levam prosa. As outras são matemática (`latex`, `sympy`,
# `exato`) ou identificadores que a tela compara (`estado`, `kind`, `tipo`,
# `leitura`) — traduzir um identificador quebraria a lógica, calado.
PROSA = {"erro", "texto", "avisos", "notas", "descricao", "motivo", "rotulo",
         "campo", "proveniencia", "bloqueado_por"}


@functools.lru_cache(maxsize=1)
def _moldes():
    from .mensagens_en import EN
    saida = []
    for pt, en in EN.items():
        if pt == en:
            continue
        # placeholders colados — `{6}{7}` — não têm fronteira entre si: viram
        # um grupo só, desde que o molde em inglês os cole na mesma ordem
        for run in sorted(set(re.findall(r"(?:(?<!\{)\{(?:\d+|nome)\}(?!\})){2,}", pt)), key=len, reverse=True):
            if run not in en:
                continue
            nums = re.findall(r"\d+|nome", run)
            unido = "{" + "_".join(nums) + "}"
            pt, en = pt.replace(run, unido), en.replace(run, unido)
        partes = re.split(r"(?<!\{)\{(\d+(?:_\d+)*|nome)\}(?!\})", pt)
        literais = [p.replace("{{", "{").replace("}}", "}") for p in partes[0::2]]
        grupos = partes[1::2]
        if len("".join(literais).strip()) < 3:
            continue
        regex = ""
        for k, lit in enumerate(literais):
            regex += re.escape(lit)
            if k < len(grupos):
                ultimo = k == len(grupos) - 1 and not literais[k + 1]
                # vazio vale: `{onde}` e o sufixo `{1}` muitas vezes são ""
                regex += f"(?P<g{grupos[k]}>.*)" if ultimo else f"(?P<g{grupos[k]}>.*?)"
        peso = len("".join(literais))
        saida.append((peso, re.compile(regex, re.S), en))
    saida.sort(key=lambda t: -t[0])
    return saida


def _preencher(en, valores):
    def troca(m):
        return valores.get(m.group(1), m.group(0))
    texto = re.sub(r"(?<!\{)\{(\d+(?:_\d+)*|nome)\}(?!\})", troca, en)
    return texto.replace("{{", "{").replace("}}", "}")


# Palavras que chegam soltas, como valor de um molde: o `onde` de "índice em
# cima", o singular e o plural de _conta.
PALAVRAS = {
    "1-forma": "1-form", "1-formas": "1-forms", "vetor": "vector", "vetores": "vectors",
    "índice": "index", "índices": "indices", "em cima": "up", "embaixo": "down",
    "nenhum": "no", "parcial ": "partial ", "parcial": "partial", "simétrico": "symmetric",
    "antissimétrico": "antisymmetric", "linha": "line", "linhas": "lines",
    "componente": "component", "componentes": "components", "forma": "form", "formas": "forms",
    "campo": "field", "campos": "fields", "equação": "equation", "equações": "equations",
    "solução": "solution", "solução geral": "general solution",
    "potência": "power", "soma": "sum", "produto": "product", "fração": "fraction",
    "função": "function", "igualdade": "equality", "derivada": "derivative",
    "integral": "integral", "número": "number", "símbolo": "symbol",
    "substituição": "substitution", "normalização": "normalization",
    "somando": "summing", "usou": "used", "contraídos": "contracted", "resultado": "result",
    # rótulos das tabelas dos módulos
    "ordem": "order", "espécie": "kind", "tipo": "type", "conferência": "check",
    "ordinária": "ordinary", "parcial": "partial", "estabelecida": "established",
    "padrão": "pattern", "candidata": "candidate",
    "constante": "constant", "motivo": "reason", "caso": "case", "ponto": "point",
    "falha": "fails", "satisfeita": "satisfied", "situação": "status",
    "expoentes": "exponents", "separação de variáveis": "separation of variables",
    "candidata verificada": "candidate verified", "sem solução encontrada": "no solution found",
    "solução não confirmada": "solution not confirmed", "não deu para conferir": "could not check",
    "condições necessárias de Kovacic": "Kovacic necessary conditions",
    "nenhuma": "none", "nenhum": "none",
    "coordenadas": "coordinates", "é de Killing": "is Killing",
    "vezes": "times",
}
_RE_PALAVRAS = re.compile(r"(?<![\w-])(" + "|".join(
    sorted(map(re.escape, PALAVRAS), key=len, reverse=True)) + r")(?![\w-])")


def _palavras(texto):
    """Um valor curto que nenhum molde casou: as palavras conhecidas."""
    return _RE_PALAVRAS.sub(lambda m: PALAVRAS[m.group(1)], texto)


def traduzir(texto, idioma="en", _prof=0):
    """Uma mensagem em português, no idioma pedido."""
    if idioma != "en" or not isinstance(texto, str) or not texto.strip() or _prof > 6:
        return texto
    guardados = []

    def marca(s):
        guardados.append(s)
        return f"\x00{len(guardados) - 1}\x00"

    atual = texto
    for _, regex, en in _moldes():
        if regex.pattern and regex.search(atual) is None:
            continue

        def troca(m, en=en):
            # um valor com trecho já traduzido volta a ser texto antes de
            # ser traduzido ele mesmo
            valores = {k[1:]: _palavras(traduzir(_devolver(v, guardados), idioma, _prof + 1))
                       for k, v in m.groupdict().items() if v is not None}
            return marca(_preencher(en, valores))

        atual = regex.sub(troca, atual)
    if _prof or len(atual) <= 30:
        # num valor — ou num rótulo curto —, o que sobrou entre os trechos traduzidos são palavras soltas
        atual = re.sub(r"[^\x00]+(?=\x00|$)|(?<=\x00)[^\x00]+",
                       lambda m: m.group(0) if re.fullmatch(r"\d+", m.group(0)) else _palavras(m.group(0)), atual)
    return _devolver(atual, guardados)


def _devolver(texto, guardados):
    while "\x00" in texto:
        novo = re.sub(r"\x00(\d+)\x00", lambda m: guardados[int(m.group(1))], texto)
        if novo == texto:
            break
        texto = novo
    return texto


def traduzir_resposta(obj, idioma="en", chave=None):
    """Uma resposta do motor inteira: a prosa traduzida, o resto intocado."""
    if idioma != "en":
        return obj
    if isinstance(obj, dict):
        return {k: traduzir_resposta(v, idioma, k) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        if chave == "linhas":
            # [rótulo, sympy, latex]: só o rótulo é prosa; ["usou", texto] é prosa
            # (as linhas chegam como lista ou como tupla: as dos módulos são tuplas)
            return [[traduzir(c, idioma) if isinstance(c, str) and (i == 0 or len(linha) == 2)
                     else c for i, c in enumerate(linha)] if isinstance(linha, (list, tuple))
                    else traduzir_resposta(linha, idioma) for linha in obj]
        return [traduzir_resposta(v, idioma, chave) for v in obj]
    if isinstance(obj, str) and chave in PROSA:
        return traduzir(obj, idioma)
    return obj
