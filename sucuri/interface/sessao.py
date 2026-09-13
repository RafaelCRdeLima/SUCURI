"""A sessão: o documento vivo por trás da interface.

A interface não guarda semântica. Ela mostra o que a sessão diz, e devolve à
sessão as decisões do usuário — que são exatamente duas: as CONVENÇÕES do
documento e as ANOTAÇÕES de sítio. Tudo o mais é consequência.

A sessão reconstrói o `Document` a cada leitura em vez de mutá-lo. Assim
desfazer uma convenção é apagar uma linha de estado, e não desfazer um efeito.
"""

from __future__ import annotations

import re
import time

import sympy as sp

from ..ambiguity import _COMANDOS, find
from ..document import Document, FaltaVariavel, Resolution, Unresolved
from ..prazo import TempoEsgotado, no_prazo


def _chave(kind, base, detail):
    return (kind, base, tuple(sorted((k, v) for k, v in detail.items())))


class Sessao:
    """Estado de uma janela do Sucuri."""

    def __init__(self):
        self.latex = ""
        self.independente = None
        self.temporal = None
        self.linhas = None          # None | 'derivative' | 'symbol'
        self.pontos = None          # None | 'derivative' | 'decoration'
        self.funcoes = []
        self.variaveis = []
        self.anotacoes = {}         # chave -> (kind, base, detail, reading)

    # ------------------------------------------------------------- estado

    def estado(self):
        return {
            "latex": self.latex,
            "independente": self.independente,
            "temporal": self.temporal,
            "linhas": self.linhas,
            "pontos": self.pontos,
            "funcoes": list(self.funcoes),
            "variaveis": list(self.variaveis),
            "anotacoes": [
                {"kind": k, "base": b, "detalhe": d, "leitura": r}
                for (k, b, d, r) in self.anotacoes.values()
            ],
        }

    def configurar(self, dados):
        """Aplica o que veio da interface, ignorando o que ela não mandou."""
        if "independente" in dados:
            self.independente = _nome(dados["independente"])
        if "temporal" in dados:
            self.temporal = _nome(dados["temporal"])
        if "linhas" in dados:
            self.linhas = _leitura(dados["linhas"], ("derivative", "symbol"))
        if "pontos" in dados:
            self.pontos = _leitura(dados["pontos"], ("derivative", "decoration"))
        if "funcoes" in dados:
            self.funcoes = _lista(dados["funcoes"])
        if "variaveis" in dados:
            self.variaveis = _lista(dados["variaveis"])
        return self

    def anotar(self, kind, base, detail, reading):
        """Resolve um sítio específico — a decisão que vence a convenção."""
        detail = {k: v for k, v in (detail or {}).items()}
        self.anotacoes[_chave(kind, base, detail)] = (kind, base, detail, reading)
        return self

    def esquecer(self, kind, base, detail):
        self.anotacoes.pop(_chave(kind, base, detail or {}), None)
        return self

    # ------------------------------------------------------------ leitura

    def documento(self):
        """Um `Document` novo, montado a partir do estado declarado.

        Devolve também os avisos: convenções que não puderam ser aplicadas —
        tipicamente 'linha é derivada' sem variável independente, que é o caso
        em que a convenção esconderia uma ambiguidade em vez de resolvê-la.
        """
        avisos, falta = [], None
        doc = Document(independent_variable=self.independente,
                       time_variable=self.temporal)
        if self.funcoes:
            doc.function(*self.funcoes)
        if self.variaveis:
            doc.variable(*self.variaveis)

        if self.linhas is not None:
            try:
                doc.primes_are_derivatives(self.linhas == "derivative")
            except FaltaVariavel as e:
                avisos.append(str(e))
                falta = falta or _faltando(e, self.latex)
            except ValueError as e:
                avisos.append(str(e))
        if self.pontos is not None:
            try:
                doc.dots_are_time_derivatives(self.pontos == "derivative")
            except FaltaVariavel as e:
                avisos.append(str(e))
                falta = falta or _faltando(e, self.latex)
            except ValueError as e:
                avisos.append(str(e))

        for kind, base, detail, reading in self.anotacoes.values():
            doc.annotate(kind, base, reading, **detail)
        return doc, avisos, falta

    def ler(self, latex=None):
        """A leitura completa, na forma que a interface consome."""
        if latex is not None:
            self.latex = latex
        inicio = time.perf_counter()

        doc, avisos, falta = self.documento()
        expr = doc.read(self.latex)

        saida = {
            "latex": self.latex,
            "avisos": avisos,
            "ambiguidades": [_ambiguidade(a, doc.resolution(a))
                             for a in expr.ambiguities],
            "pendentes": len(expr.pending),
            "inferidas": len(expr.inferred),
            "arvore": None,
            "faltando": falta,
            "diferencial": False,
            "sympy": None,
            "codigo": None,
            "latex_semantico": None,
            "erro": None,
        }

        if self.latex.strip() and not expr.pending:
            try:
                objeto = expr.to_sympy()
                saida["sympy"] = sp.sstr(objeto)
                saida["codigo"] = codigo_python(objeto)
                saida["latex_semantico"] = sp.latex(objeto)
                saida["arvore"] = expr.tree().to_dict()
                saida["diferencial"] = _e_diferencial(objeto)
            except Unresolved as e:
                saida["erro"] = str(e)
            except FaltaVariavel as e:
                saida["erro"] = str(e)
                saida["faltando"] = _faltando(e, self.latex)
            except Exception as e:                      # noqa: BLE001
                saida["erro"] = f"{type(e).__name__}: {e}"

        saida["ms"] = round((time.perf_counter() - inicio) * 1000, 1)
        saida["estado"] = self.estado()
        saida["versoes"] = versoes()
        return saida

    # ---------------------------------------------------------- avaliação

    def avaliar(self, latex=None):
        """Faz a conta que a leitura deixou parada — e diz o que ela é.

        O Sucuri lê; avaliar é outro ato, e por isso é um botão e não um efeito
        de digitar. A integral fica `Integral(x**2, (x, 0, 1))` até alguém
        pedir, e aí vira 1/3.

        Três respostas possíveis, e o rótulo distingue as três, porque tratá-las
        como a mesma coisa é o erro de sempre:

          exata          a conta fechou: 1/3
          não fechou     o SymPy devolveu o mesmo objeto, sem calcular
          não terminou   estourou o prazo

        Quando o resultado é um número, vai junto a aproximação decimal — como
        aproximação, rotulada, nunca no lugar do valor exato.
        """
        if latex is not None:
            self.latex = latex
        inicio = time.perf_counter()
        saida = {"latex": self.latex, "exato": None, "latex_exato": None,
                 "numerico": None, "fechou": False, "indefinida": False,
                 "erro": None}

        doc, _, _ = self.documento()
        expressao = doc.read(self.latex)
        if expressao.pending:
            saida["erro"] = "há sítios pendentes; resolva antes de avaliar"
            saida["pendentes"] = expressao.questions()
            saida["ms"] = round((time.perf_counter() - inicio) * 1000, 1)
            return saida

        try:
            objeto = expressao.to_sympy()
            valor = no_prazo(_avaliar, PRAZO_AVALIAR, objeto)
        except TempoEsgotado as e:
            saida["erro"] = str(e)
        except Exception as e:                                  # noqa: BLE001
            saida["erro"] = f"{type(e).__name__}: {e}"
        else:
            saida["exato"] = sp.sstr(valor)
            saida["latex_exato"] = sp.latex(valor)
            saida["fechou"] = not _parou(valor)
            saida["indefinida"] = saida["fechou"] and _indefinida(objeto)
            # Aproximação decimal só de conta que fechou: avaliar numericamente
            # o que ficou parado devolve ruído com cara de resposta.
            if saida["fechou"] and valor.is_number and not valor.is_Integer:
                try:
                    saida["numerico"] = str(sp.N(valor, 12))
                except Exception:                               # noqa: BLE001
                    pass

        saida["ms"] = round((time.perf_counter() - inicio) * 1000, 1)
        return saida

    def expressao_de(self, latex):
        """A Expression de um latex qualquer, sob as convenções desta sessão."""
        doc, _, _ = self.documento()
        return doc.read(latex)

    def expressao(self):
        """A Expression atual, para os módulos operarem sobre ela."""
        doc, _, _ = self.documento()
        return doc.read(self.latex)


PRAZO_AVALIAR = 20


def _avaliar(objeto):
    """`doit` faz a conta; `simplify` arruma o que sobrou dela."""
    return sp.simplify(objeto.doit())


_RE_LETRA = re.compile(r"\\[a-zA-Z]+|[a-zA-Z]")


def _faltando(erro, latex):
    """A pergunta que o erro devia ter sido, com os candidatos que dá para ver.

    As letras que sobram fora dos sítios de derivada vão como ATALHO, não como
    resposta: em f' = x^2 sobra o x, que é mesmo a variável, mas em x' = A e^x
    sobra o A, que é constante — a variável ali é o t, que não está escrito.
    Oferecer a lista como se fosse a resposta seria adivinhar de novo, só que
    com cara de ajuda.

    Quando não sobra nenhuma — y'' + y = 0 —, a lista vazia é a informação: a
    variável REALMENTE não aparece na equação, e é por isso que ninguém pode
    tirá-la de lá.
    """
    return {"qual": erro.qual, "campo": erro.campo,
            "candidatos": _candidatas(latex)}


def _candidatas(latex):
    sitios = find(latex)
    cobertos = {i for a in sitios for i in range(*a.span)}
    # A base de uma derivada NÃO pode ser a variável: y' com y independente
    # seria a derivada de y em relação a si mesmo, e isso o leitor recusa.
    derivadas = {a.base for a in sitios if a.kind in ("prime", "newton")}
    achadas = []
    for m in _RE_LETRA.finditer(latex):
        if m.start() in cobertos:
            continue
        nome = m.group(0)
        nome = nome[1:] if nome.startswith("\\") else nome
        if nome in _COMANDOS or nome in derivadas or nome in achadas:
            continue
        achadas.append(nome)
    return achadas


def _e_diferencial(objeto):
    """Isto é equação diferencial?

    A pergunta decide qual verbo a interface oferece. Avaliar uma equação
    diferencial não faz nada — `doit` deixa a derivada de uma função incógnita
    exatamente onde estava —, e mandar o usuário descobrir sozinho que o botão
    certo é outro é fazê-lo adivinhar, que é o que este programa não faz.
    """
    if not isinstance(objeto, sp.Equality):
        return False
    return any(d.expr.atoms(sp.core.function.AppliedUndef)
               for d in objeto.atoms(sp.Derivative))


def _indefinida(objeto):
    """A entrada tinha integral sem limites?

    Se tinha, o que sai não é UMA função: é uma família, e todas diferem por
    uma constante. O SymPy devolve -cos(x) para ∫sen x dx e não diz mais nada;
    qualquer tabela escreve -cos(x) + C. Omitir a constante é dar por resposta
    um representante da resposta.
    """
    return any(len(limite) == 1
               for integral in objeto.atoms(sp.Integral)
               for limite in integral.limits)


def _parou(valor):
    """A conta ficou parada onde estava?

    Integral, Sum ou Derivative sobrando no resultado querem dizer que o SymPy
    não soube fazer — e devolver isso como se fosse resposta seria fingir.
    """
    return bool(valor.atoms(sp.Integral, sp.Sum, sp.Product, sp.Derivative))


# ------------------------------------------------------------- auxiliares

_ESTADOS = {Resolution.EXPLICIT: "explicita",
            Resolution.INFERRED: "inferida",
            Resolution.PENDING: "pendente"}


def _ambiguidade(amb, resolucao):
    return {
        "kind": amb.kind,
        "fragmento": amb.fragment,
        "inicio": amb.span[0],
        "fim": amb.span[1],
        "base": amb.base,
        "detalhe": dict(amb.detail),
        "leituras": [{"chave": r.key, "descricao": r.description}
                     for r in amb.readings],
        "estado": _ESTADOS[resolucao.how],
        "leitura": resolucao.reading,
    }


def codigo_python(expr):
    """O mesmo objeto, escrito como programa — o que se cola num script."""
    from sympy.printing.python import python
    corpo = python(expr).strip().splitlines()
    declaracoes = [l for l in corpo if not l.startswith("e = ")]
    final = [l for l in corpo if l.startswith("e = ")]
    linhas = ["from sympy import *", ""]
    linhas += declaracoes
    if declaracoes:
        linhas.append("")
    linhas += [l.replace("e = ", "expr = ", 1) for l in final]
    return "\n".join(linhas)


def versoes():
    from .. import __version__
    return {"sympy": sp.__version__, "sucuri": __version__}


def _nome(v):
    v = (v or "").strip()
    return v or None


def _lista(v):
    if isinstance(v, str):
        v = v.replace(",", " ").split()
    return [str(x).strip() for x in (v or []) if str(x).strip()]


def _leitura(v, permitidas):
    if v in (None, "", "nenhuma"):
        return None
    if v not in permitidas:
        raise ValueError(f"leitura inválida: {v!r}")
    return v
