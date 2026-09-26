"""Os moldes de mensagem em português do código: literais e f-strings, sem docstrings.

    python tools/extrair_mensagens.py saida.json

Cada f-string vira um molde com {0}, {1}… no lugar dos valores. É daqui que sai
a lista que `sucuri/mensagens_en.py` traduz, e `tests/test_idioma.py` usa
`moldes()` para exigir que toda mensagem nova tenha tradução.
"""
import ast, json, pathlib, re, sys
RAIZ = pathlib.Path(__file__).parents[1] / "sucuri"
PT = re.compile(r"[áàâãéêíóôõúçÁÉÍÓÚÇ]|\b(não|nao|de|do|da|dos|das|com|sem|que|para|pede|declare|declarado|declarada|um|uma|os|as|é|está|tem|há|ou|foi|são|vale|provado|achei|conheço|índice|vetor|campo|forma|métrica|equação|ao|aos|na|nas|nos|em|por|se|mas|já|só|cada|isto|aqui|recebe|derivada|aplicada|multiplicando|sobre|entre|quando|como|mesmo|também|depois|antes|ainda|carta|nome|leitura|qualquer|conexão|linearidade|simetria|solução|componentes|ordem|relação|variável|chamado|chamada)\b", re.I)
def molde(no):
    if isinstance(no, ast.Constant) and isinstance(no.value, str):
        return no.value
    if isinstance(no, ast.JoinedStr):
        partes, k = [], 0
        for v in no.values:
            if isinstance(v, ast.Constant):
                partes.append(v.value.replace("{", "{{").replace("}", "}}"))
            else:
                partes.append("{%d}" % k); k += 1
        return "".join(partes)
    return None
def docstrings(arvore):
    ids = set()
    for n in ast.walk(arvore):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body:
            p = n.body[0]
            if isinstance(p, ast.Expr) and isinstance(p.value, ast.Constant):
                ids.add(id(p.value))
    return ids
def moldes():
    """{molde: ["arquivo:linha", …]}."""
    saida = {}
    for arq in sorted(RAIZ.rglob("*.py")):
        if "__pycache__" in arq.parts or arq.name in ("mensagens_en.py", "idioma.py"): continue
        arv = ast.parse(arq.read_text())
        ds = docstrings(arv)
        dentro = set()
        for n in ast.walk(arv):
            if isinstance(n, ast.Expr) and isinstance(n.value, (ast.Constant, ast.JoinedStr)):
                dentro.add(id(n.value))          # string solta: comentário, não mensagem
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in ("compile", "match", "search", "sub", "fullmatch", "findall", "finditer", "split"):
                for a in n.args[:1]: dentro.add(id(a))
        for n in ast.walk(arv):
            if isinstance(n, ast.JoinedStr):
                for v in n.values: dentro.add(id(v))
        for n in ast.walk(arv):
            if id(n) in ds or id(n) in dentro: continue
            # uma expressão solta (comentário em string) não é mensagem
            m = molde(n)
            if m and (m.lstrip().startswith("^") or "\\s" in m or "(?" in m): continue
            if not m or len(re.sub(r"\{\d+\}", "", m)) < 3: continue
            if not PT.search(re.sub(r"\{\d+\}", "", m)): continue
            if " " not in m.strip(): continue
            saida.setdefault(m, []).append(f"{arq.relative_to(RAIZ.parent)}:{n.lineno}")
    return saida


if __name__ == "__main__":
    m = moldes()
    json.dump(m, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    print(len(m))
