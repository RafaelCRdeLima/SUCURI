"""Roda os exemplos do manual e da apostila em inglês e lista o português que
sobrou nas mensagens — o que o catálogo ainda não cobre."""
import collections, json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1])); sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "tests"))
from test_manual import Leitor
from sucuri.caderno import Caderno
from sucuri.idioma import traduzir_resposta, PROSA
PT = re.compile(r"\b(não|nao|de|da|dos|das|com|sem|que|para|pede|um|uma|os|é|está|tem|há|ou|foi|são|vale|ao|na|em|por|se|mas|já|só|cada|isto|aqui|recebe|índice|índices|vetor|campo|forma|métrica|equação|derivada|aplicada|multiplicando|sobre|entre|quando|como|mesmo|também|depois|antes|ainda|carta|nome|leitura|declare|declarado)\b|[ãõçáéíóúâêô]", re.I)
def prosa(obj, chave=None, out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            prosa(v, k, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if chave == "linhas" and isinstance(v, list):
                out += [c for j, c in enumerate(v) if isinstance(c, str) and (j == 0 or len(v) == 2)]
            else: prosa(v, chave, out)
    elif isinstance(obj, str) and chave in PROSA: out.append(obj)
    return out
paginas = sys.argv[1:] or ["manual.html", "apostila.html"]
restos = collections.Counter(); exemplos = {}
for pag in paginas:
    l = Leitor(); l.feed((pathlib.Path(__file__).parents[1] / "sucuri/interface/estatico" / pag).read_text()); 
    for e in l.exemplos:
        c = Caderno()
        for f in e["entradas"]:
            d = traduzir_resposta(c.executar(f).to_dict(), "en")
            for s in prosa(d):
                if PT.search(re.sub(r"\\[A-Za-z]+|`[^`]*`|'[^']*'", "", s)):
                    restos[s] += 1; exemplos.setdefault(s, f)
for s, n in restos.most_common():
    print(n, repr(s)[:230])
print(len(restos), "mensagens com português")
