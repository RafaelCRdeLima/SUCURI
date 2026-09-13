"""O caderno: várias equações, nomes que duram, verbos que operam sobre elas.

A página de uma equação só serve para inspecionar notação. Trabalho de verdade
é escrever uma coisa, olhar, escrever outra que usa a primeira. É o que um
caderno faz, e é o que falta aqui.

## Por que os verbos são poucos e fechados

A tentação é abrir um console de Python: aí `solve(eq)` seria `sympy.solve(eq)`
e pronto. Mas nesse instante a ponte que este programa é deixa de ser
obrigatória — quem escreve Python fala direto com o SymPy, sem sítios, sem
convenção declarada, sem proveniência. Sobra um Jupyter com passos a mais.

Então os comandos são um punhado, e cada um é uma operação que o motor já faz,
com as mesmas recusas:

    resolver(eq)      solve(eq)       equação diferencial ou algébrica
    avaliar(eq)       evaluate(eq)    faz a conta parada
    simplificar(eq)   simplify(eq)
    exportar(eq)      export(eq)      o código SymPy que produz e resolve
    latex(eq)                         a escrita de volta, para copiar

Célula com sítio pendente não vira nada: o caderno recusa como a leitura recusa.
"""

from __future__ import annotations

import re

import sympy as sp

from .interface.sessao import Sessao, codigo_python

_RE_COMANDO = re.compile(r"^\s*([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)\s*$")
# Declaração na folha: `u = u(t,x)`, com o MESMO nome dos dois lados.
#
# A repetição é o que distingue declaração de matemática. `u(t,x)` sozinho é
# uma expressão legítima — aplicação, ou produto, que é justamente um sítio
# ambíguo — e engoli-la como declaração seria decidir por quem escreveu.
# `u = u(t,x)` é tautologia: ninguém escreve isso como equação.
_RE_DECLARA = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*\1\s*\([^)]*\)\s*$")

# A forma antiga, para dizer o que mudou em vez de falhar em LaTeX.
_RE_COLCHETE = re.compile(r"^\s*([A-Za-z]\w*)\s*(?:=\s*\1\s*)?\[[^\]]*\]\s*$")

# As outras duas coisas que um nome pode ser, além de função de alguma coisa.
# Ficam na mesma forma porque são a mesma pergunta: o que é este nome?
_RE_ESPECIE = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*"
                         r"(euler|s[ií]mbolo|constante)\s*$", re.I)

VERBOS = {
    "resolver": "resolver", "solve": "resolver", "dsolve": "resolver",
    "avaliar": "avaliar", "evaluate": "avaliar", "doit": "avaliar",
    "simplificar": "simplificar", "simplify": "simplificar",
    "exportar": "exportar", "export": "exportar",
    "latex": "latex",
}


class Celula:
    """Uma entrada do caderno e o que ela produziu."""

    def __init__(self, nome, fonte, tipo, dados):
        self.nome = nome
        self.fonte = fonte
        self.tipo = tipo            # 'math' ou 'comando'
        self.dados = dados

    def to_dict(self):
        return {"nome": self.nome, "fonte": self.fonte, "tipo": self.tipo,
                **self.dados}


class Caderno:
    """As convenções de um documento, e as equações que se acumulam sob elas.

    As convenções são as da `Sessao` — mesmas anotações, mesmas perguntas —,
    porque um caderno é um documento, não uma coleção de documentos avulsos.
    """

    def __init__(self):
        self.sessao = Sessao()
        self.nomes = {}             # nome -> latex
        self.contador = 0

    # ------------------------------------------------------------- estado

    def configurar(self, convencoes):
        self.sessao.configurar(convencoes)
        return self

    def anotar(self, kind, base, detail, reading):
        self.sessao.anotar(kind, base, detail, reading)
        return self

    def _proximo_nome(self):
        self.contador += 1
        return f"eq{self.contador}"

    # ------------------------------------------------------------ execução

    def executar(self, fonte):
        """Uma célula: declaração, verbo, ou matemática."""
        especie = _RE_ESPECIE.match(fonte or "")
        if especie:
            return self._especie(especie.group(1), especie.group(2).lower())

        declarada = _RE_DECLARA.match(fonte or "")
        if declarada:
            return self._declarar(fonte)

        colchete = _RE_COLCHETE.match(fonte or "")
        if colchete:
            nome = colchete.group(1)
            dentro = fonte[fonte.index("[") + 1:fonte.rindex("]")]
            return Celula(None, fonte, "declaracao", {
                "erro": f"a declaração agora se escreve com parênteses: "
                        f"{nome} = {nome}({dentro}). O colchete ficou reservado "
                        f"a n-tupla."})

        comando = _RE_COMANDO.match(fonte or "")
        if comando and comando.group(1).lower() in VERBOS:
            verbo, alvo = comando.group(1).lower(), comando.group(2)
            return Celula(None, fonte, "comando",
                          self._comando(VERBOS[verbo], alvo))
        return self._matematica(fonte)

    def _especie(self, nome, especie):
        """`e = euler`, `a = símbolo`.

        A mesma pergunta das outras declarações — o que é este nome? — com as
        outras duas respostas possíveis. Vira anotação de sítio, e não
        convenção, porque é uma decisão sobre AQUELE nome, não uma regra
        aplicada a tudo sem olhar.
        """
        if especie == "euler":
            self.sessao.anotar("euler", nome, {}, "euler")
            texto = f"{nome} é o número de Euler"
        else:
            self.sessao.anotar("juxtaposition", nome, {}, "product")
            texto = f"{nome} é símbolo, não função: {nome}(…) é produto"
        return Celula(None, f"{nome} = {especie}", "declaracao",
                      {"declarado": [{"nome": nome, "especie": especie}],
                       "texto": texto})

    def _declarar(self, fonte):
        """`u = u(t,x)` — e a ambiguidade some em vez de ser escolhida.

        Declarar que u é função de x e t não escolhe entre as leituras de
        ∂u/∂t: tira uma delas do mundo, porque não há símbolo u para
        multiplicar. Vale daqui para baixo, como em qualquer caderno; para o
        documento inteiro, o campo "Funções" no cabeçalho.
        """
        from .document import declaracoes

        novas = declaracoes(fonte.split("=", 1)[1])
        vistos = []
        for nome, args in novas:
            if not args:
                continue
            self.sessao.funcoes_declaradas = [
                f for f in self.sessao.funcoes_declaradas
                if not f.startswith(nome + "[")]
            self.sessao.funcoes_declaradas.append(f"{nome}({','.join(args)})")
            vistos.append((nome, args))
        if not vistos:
            return self._matematica(fonte)

        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": n, "variaveis": list(a)} for n, a in vistos],
            "texto": "; ".join(
                f"daqui para baixo, {n} é função de {', '.join(a)}"
                for n, a in vistos)})

    def _matematica(self, latex):
        leitura = self.sessao.ler(latex)
        nome = None
        if leitura["sympy"] is not None:
            nome = self._proximo_nome()
            self.nomes[nome] = latex
        return Celula(nome, latex, "math", leitura)

    def _objeto(self, nome):
        if nome not in self.nomes:
            conhecidos = ", ".join(self.nomes) or "nenhum ainda"
            raise KeyError(f"não conheço '{nome}' (tenho: {conhecidos})")
        expressao = self.sessao.expressao_de(self.nomes[nome])
        if expressao.pending:
            raise ValueError(
                f"'{nome}' tem sítio ambíguo sem decisão; resolva antes de operar")
        return expressao

    def _comando(self, verbo, alvo):
        try:
            expressao = self._objeto(alvo)
        except (KeyError, ValueError) as e:
            return {"erro": str(e)}

        if verbo == "latex":
            return {"latex_exato": sp.latex(expressao.to_sympy()),
                    "exato": sp.sstr(expressao.to_sympy()), "alvo": alvo}
        if verbo == "exportar":
            return {"codigo": self.exportar(alvo), "alvo": alvo}
        if verbo == "avaliar":
            d = Sessao.avaliar(self._sessao_de(alvo))
            d["alvo"] = alvo
            return d
        if verbo == "simplificar":
            objeto = sp.simplify(expressao.to_sympy())
            return {"alvo": alvo, "exato": sp.sstr(objeto),
                    "latex_exato": sp.latex(objeto)}
        return self._resolver(alvo, expressao)

    def _sessao_de(self, nome):
        """Uma sessão com as convenções do caderno e o latex da célula."""
        copia = Sessao()
        copia.__dict__.update(self.sessao.__dict__)
        copia.anotacoes = dict(self.sessao.anotacoes)
        copia.latex = self.nomes[nome]
        return copia

    def _resolver(self, alvo, expressao):
        """Resolver é um verbo só; qual conta fazer, o objeto decide.

        Equação diferencial vai para o módulo `resolver`, que confere a solução
        por substituição; equação algébrica vai para o solve do SymPy. Obrigar
        o usuário a escolher entre solve e dsolve é pedir que ele classifique a
        própria equação para o programa — ao contrário.
        """
        from .interface.sessao import _e_diferencial
        from .modules import load

        objeto = expressao.to_sympy()
        if _e_diferencial(objeto):
            resultado = load("resolver").operations["resolver"].run(expressao)
            saida = resultado.to_dict()
            saida["alvo"] = alvo
            return saida

        if not isinstance(objeto, sp.Equality):
            return {"erro": f"'{alvo}' não é uma igualdade: não há o que resolver",
                    "alvo": alvo}

        incognitas = sorted(objeto.free_symbols, key=str)
        if not incognitas:
            return {"erro": f"'{alvo}' não tem incógnita", "alvo": alvo}
        raizes = sp.solve(objeto, incognitas[0], dict=True)
        linhas = [(str(incognitas[0]), sp.sstr(r[incognitas[0]]))
                  for r in raizes if incognitas[0] in r]
        return {"alvo": alvo, "rotulo": f"raízes em {incognitas[0]}",
                "linhas": [list(l) for l in linhas],
                "latex_exato": sp.latex([r[incognitas[0]] for r in raizes
                                         if incognitas[0] in r]),
                "proveniencia": "estabelecida", "apresentavel": True}

    # ------------------------------------------------------------ exportar

    def exportar(self, nome):
        """O script que refaz tudo: declara, monta e resolve.

        É o pedido mais honesto que um programa destes recebe — "me dá o código
        que você usou" —, e é também a prova de que não há mágica aqui: o que
        sai roda sozinho, sem o Sucuri.
        """
        expressao = self._objeto(nome)
        objeto = expressao.to_sympy()
        linhas = [codigo_python(objeto).replace("expr = ", f"{nome} = ", 1)]

        from .interface.sessao import _e_diferencial
        if _e_diferencial(objeto):
            funcoes = {a.func for d in objeto.atoms(sp.Derivative)
                       for a in d.expr.atoms(sp.core.function.AppliedUndef)}
            f = sorted(funcoes, key=lambda c: c.__name__)[0]
            var = sorted(objeto.free_symbols, key=str)
            argumento = f"{f.__name__}({var[0]})" if var else f.__name__
            linhas += ["", f"solucao = dsolve({nome}, {argumento})",
                       f"checkodesol({nome}, solucao)   # confere por substituição"]
        elif isinstance(objeto, sp.Equality):
            livres = sorted(objeto.free_symbols, key=str)
            if livres:
                linhas += ["", f"solucao = solve({nome}, {livres[0]})"]
        else:
            linhas += ["", f"valor = simplify({nome}.doit())"]
        return "\n".join(linhas)
