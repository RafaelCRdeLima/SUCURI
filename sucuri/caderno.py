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
from sympy.tensor.tensor import TensExpr

from .interface.sessao import Sessao, codigo_python

# Um verbo e um nome; ou um verbo e dois, para os que comparam duas coisas.
# O nome pode vir com barra — `\eta`, `\Gamma` —, porque é assim que se
# escreve o nome da métrica. A barra é da escrita, não do objeto.
#
# E pode vir com índice: `A_{t}`, `\Gamma^{r}_{tt}` são os rótulos que as
# tabelas de componentes imprimem, e o que aparece na tela tem de poder ser
# digitado de volta. Sem isso, `avaliar(A_{t})` não casava aqui, caía no leitor
# de LaTeX e virava "avaliar vezes (A_t)" — uma pergunta sobre `r(`, que é o
# `r` de "contrair". Bem formada e absurda.
_GRUPO_CHAVES = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
_ROTULO = (r"\\?[A-Za-z_]\w*(?:[_^](?:" + _GRUPO_CHAVES + r"|\\[A-Za-z]+|\w))*")
_RE_COMANDO = re.compile(r"^\s*([A-Za-z_]\w*)\s*\(\s*(" + _ROTULO + r")\s*"
                         r"(?:,\s*(" + _ROTULO + r")\s*)?\)\s*$")
# `provar(eq5, eq1, eq2)`: o objetivo e as hipóteses, quantas forem. Forma
# própria porque os outros verbos recebem um ou dois rótulos, e a lista de
# hipóteses é justamente o que não pode ficar implícito.
_RE_PROVAR = re.compile(r"^\s*(?:provar|prove)\s*\(\s*(" + _ROTULO +
                        r"(?:\s*,\s*" + _ROTULO + r")*)\s*\)\s*$", re.I)
# Declaração na folha: `u = u(t,x)`, com o MESMO nome dos dois lados.
#
# A repetição é o que distingue declaração de matemática. `u(t,x)` sozinho é
# uma expressão legítima — aplicação, ou produto, que é justamente um sítio
# ambíguo — e engoli-la como declaração seria decidir por quem escreveu.
# `u = u(t,x)` é tautologia: ninguém escreve isso como equação.
_RE_DECLARA = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*\1\s*\([^)]*\)\s*$")

# `x = coordenadas(t, r, \theta, \phi)` e `g = métrica(...)`: as componentes.
# A métrica vai pela DIAGONAL porque o parser de LaTeX não lê matriz —
# \begin{pmatrix} levanta erro —, e porque é assim que os livros dão quase
# todas as métricas que importam.
_RE_COORDENADAS = re.compile(r"^\s*([A-Za-z]\w*)\s*=\s*coordenadas?\s*"
                             r"\((.*)\)\s*$", re.I | re.S)
_RE_METRICA = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*m[ée]trica\s*"
                         r"\((.*)\)\s*$", re.I | re.S)

# O tipo do Schutz: A = tensor(M, N) recebe M 1-formas e N vetores, o que em
# índices dá M em cima e N embaixo. Números literais, e não nomes: aceitar
# `A = tensor(m, n)` com m e n definidos antes faria do caderno uma linguagem
# de programação, que é a porta que os verbos fechados existem para não abrir.
_RE_TENSOR = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*tensor\s*\(\s*"
                        r"(\d+)\s*,\s*(\d+)\s*\)\s*$", re.I)

# A forma antiga, para dizer o que mudou em vez de falhar em LaTeX.
_RE_COLCHETE = re.compile(r"^\s*([A-Za-z]\w*)\s*(?:=\s*\1\s*)?\[[^\]]*\]\s*$")

# As outras duas coisas que um nome pode ser, além de função de alguma coisa.
# Ficam na mesma forma porque são a mesma pergunta: o que é este nome?
_RE_ESPECIE = re.compile(r"^\s*((?:\\?[A-Za-z]\w*)(?:\s*,\s*\\?[A-Za-z]\w*)*)"
                         r"\s*=\s*(euler|s[ií]mbolo|constante|m[ée]trica"
                         r"|curvatura"
                         r"|metric|[ií]ndices?(?:\s*\(\s*\d+\s*\))?)\s*$", re.I)

VERBOS_GEOMETRIA = {
    "christoffel": "christoffel", "cristoffel": "christoffel",
    "ricci": "ricci", "riemann": "riemann",
    "escalar": "escalar", "curvatura": "escalar",
}

VERBOS = {
    "resolver": "resolver", "solve": "resolver", "dsolve": "resolver",
    "avaliar": "avaliar", "evaluate": "avaliar", "doit": "avaliar",
    "simplificar": "simplificar", "simplify": "simplificar",
    "exportar": "exportar", "export": "exportar",
    "latex": "latex",
    "separar": "separar", "separate": "separar",
    "conferir": "conferir", "check": "conferir", "verificar": "conferir",
    "contrair": "contrair", "contract": "contrair",
    **VERBOS_GEOMETRIA,
}

# Os que operam sobre DUAS equações: a conta e a candidata.
DE_DOIS = {"conferir"}


def _tabela_latex(linhas):
    r"""A tabela inteira em LaTeX, para caber num documento de verdade.

    O que a tela mostra é tipografado; o que se copia tem de ser copiável —
    `\theta` com a barra, e não `theta`, que o TeX compõe como três letras
    romanas. O SymPy já faz a tradução; o que faltava era oferecer o resultado.
    """
    if not linhas:
        return None
    corpo = " \\\\\n".join(f"{rot} &= {sp.latex(valor)}" for rot, valor in linhas)
    return "\\begin{aligned}\n" + corpo + "\n\\end{aligned}"


def fonte_metrica(nome, texto):
    return f"{nome} = métrica({texto.strip()})"


def _conta(n, um, muitos):
    return f"{n} {um if n == 1 else muitos}"


def _indices_em(n, onde):
    if n == 0:
        return f"nenhum índice {onde}"
    return f"{_conta(n, 'índice', 'índices')} {onde}"


class Pronta:
    """Um objeto que já é SymPy — veio de um verbo, não de leitura.

    Cumpre o contrato mínimo que os módulos pedem de uma expressão (`pending` e
    `to_sympy`), e com isso o que uma operação PRODUZ entra no caderno com
    nome, do mesmo jeito que o que foi escrito. É o que faz separar(eq1) deixar
    de ser um beco: as duas EDOs viram eq2 e eq3, e resolver(eq2) funciona.
    """

    pending = ()

    def __init__(self, objeto):
        self._objeto = objeto

    def to_sympy(self):
        return self._objeto


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


def _e_instrucao(linha):
    """A linha é comando ou declaração — coisa que se encadeia?

    Pergunta feita pelas MESMAS regras que despacham a célula, e não por uma
    segunda lista: duas listas divergem, e divergir aqui significa partir uma
    equação ao meio.
    """
    texto = linha or ""
    comando = _RE_COMANDO.match(texto)
    if comando and comando.group(1).lower() in VERBOS:
        return True
    return any(regra.match(texto) for regra in
               (_RE_COORDENADAS, _RE_METRICA, _RE_TENSOR, _RE_ESPECIE,
                _RE_DECLARA, _RE_COLCHETE, _RE_PROVAR))


def _chave(rotulo):
    r"""`A_{t}`, `A_t` e `A_ {t}` são o mesmo rótulo.

    Chave e espaço são tipografia do TeX, não identidade do objeto. Exigir a
    forma exata que a tabela imprimiu — `\Gamma^{r}_{{t}{t}}`, com as chaves
    duplas que existem só para o KaTeX não colar as macros — seria cobrar do
    usuário um detalhe de impressão.
    """
    return "".join(c for c in (rotulo or "") if c not in "{} \t")


def _sem_barra(nome):
    """`\\eta` e `eta` nomeiam a mesma coisa; a barra é de escrita."""
    if nome and nome.startswith("\\"):
        return nome[1:]
    return nome


class Caderno:
    """As convenções de um documento, e as equações que se acumulam sob elas.

    As convenções são as da `Sessao` — mesmas anotações, mesmas perguntas —,
    porque um caderno é um documento, não uma coleção de documentos avulsos.
    """

    def __init__(self):
        self.sessao = Sessao()
        self.nomes = {}             # nome -> latex escrito
        self.prontos = {}           # nome -> objeto produzido por um verbo
        self.metricas = {}          # nome -> Metrica, com componentes
        self.rotulos = {}           # 'A_t' -> valor, o que as tabelas imprimem
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
        """Uma célula: uma coisa, ou várias em sequência.

        Enter dentro da célula encadeia; Shift+Enter roda tudo. Mas só quando
        TODAS as linhas são coisa reconhecida — comando ou declaração. Uma
        equação em LaTeX pode legitimamente ocupar duas linhas, e quebrá-la em
        duas leituras daria duas metades sem sentido em vez de um erro.
        """
        linhas = [l for l in (fonte or "").split("\n") if l.strip()]
        if len(linhas) > 1 and all(_e_instrucao(l) for l in linhas):
            return self._encadeadas(fonte, linhas)
        return self._uma(fonte)

    def _encadeadas(self, fonte, linhas):
        """Cada linha por sua vez, e o que cada uma produziu, na ordem."""
        partes = [self._uma(l).to_dict() for l in linhas]
        nomes = [d["nome"] for d in partes if d.get("nome")]
        tipo = "erro" if any(d.get("erro") for d in partes) else "encadeada"
        return Celula(" ".join(nomes) or None, fonte, "encadeada",
                      {"partes": partes, "estado_geral": tipo})

    def _uma(self, fonte):
        """Uma célula: declaração, verbo, ou matemática."""
        coord = _RE_COORDENADAS.match(fonte or "")
        if coord:
            return self._coordenadas(coord.group(1), coord.group(2))

        metrica = _RE_METRICA.match(fonte or "")
        if metrica:
            return self._metrica(metrica.group(1), metrica.group(2))

        tensorial = _RE_TENSOR.match(fonte or "")
        if tensorial:
            return self._tensor(tensorial.group(1), int(tensorial.group(2)),
                                int(tensorial.group(3)))

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

        prova = _RE_PROVAR.match(fonte or "")
        if prova:
            rotulos = [_sem_barra(r.strip()) for r in prova.group(1).split(",")]
            return Celula(None, fonte, "comando",
                          self._provar(rotulos[0], rotulos[1:]))

        comando = _RE_COMANDO.match(fonte or "")
        if comando and comando.group(1).lower() in VERBOS:
            verbo = VERBOS[comando.group(1).lower()]
            alvo, segundo = (_sem_barra(comando.group(2)),
                             _sem_barra(comando.group(3)))
            return Celula(None, fonte, "comando",
                          self._comando(verbo, alvo, segundo))
        return self._matematica(fonte)

    def _argumentos(self, texto):
        """Separa por vírgula de primeiro nível, e lê cada pedaço em LaTeX."""
        pedacos, atual, fundo = [], [], 0
        for c in texto:
            if c in "({[":
                fundo += 1
            elif c in ")}]":
                fundo -= 1
            if c == "," and fundo == 0:
                pedacos.append("".join(atual))
                atual = []
            else:
                atual.append(c)
        pedacos.append("".join(atual))
        return [p.strip() for p in pedacos if p.strip()]

    def _coordenadas(self, nome, texto):
        r"""`x = coordenadas(t, r, \theta, \phi)`."""
        escritos = self._argumentos(texto)
        simbolos = []
        for escrito in escritos:
            lido = self.sessao.expressao_de(escrito).to_sympy()
            if not isinstance(lido, sp.Symbol):
                return Celula(None, f"{nome} = coordenadas(...)", "declaracao",
                              {"erro": f"'{escrito}' não é um símbolo: "
                                       f"coordenada é um nome, não uma conta"})
            simbolos.append(lido)
        self.sessao.coordenadas = simbolos
        self.sessao.escrita_coord = {str(s): e for s, e in zip(simbolos, escritos)}
        # Quem declarou quatro coordenadas declarou um espaço de dimensão 4, e
        # pedir `índices(4)` depois seria pedir a mesma informação duas vezes.
        self.sessao.dimensao = len(simbolos)
        return Celula(None, f"{nome} = coordenadas({texto.strip()})",
                      "declaracao",
                      {"declarado": [{"nome": str(s)} for s in simbolos],
                       "texto": f"as coordenadas são {', '.join(escritos)} — "
                                f"variedade de dimensão {len(simbolos)}"})

    def _metrica(self, nome, texto):
        r"""`g = métrica(-(1-2M/r), 1/(1-2M/r), r^2, r^2\sin^2\theta)`."""
        from .geometria import Metrica

        limpo = _sem_barra(nome)
        if not self.sessao.coordenadas:
            return Celula(None, fonte_metrica(nome, texto), "declaracao",
                          {"erro": "declare as coordenadas antes da métrica: "
                                   "componente sem coordenada não diz de quê "
                                   "é componente"})
        componentes = []
        for escrito in self._argumentos(texto):
            expressao = self.sessao.expressao_de(escrito)
            if expressao.pending:
                return Celula(None, fonte_metrica(nome, texto), "declaracao",
                              {"erro": f"'{escrito}': "
                                       + "; ".join(expressao.questions())})
            componentes.append(expressao.to_sympy())
        try:
            metrica = Metrica(limpo, self.sessao.coordenadas, componentes,
                              self.sessao.escrita_coord)
        except ValueError as e:
            return Celula(None, fonte_metrica(nome, texto), "declaracao",
                          {"erro": str(e)})

        metrica.escrito = nome
        self.metricas[limpo] = metrica
        # Um nome, um objeto: o `g` das componentes é o mesmo `g` dos índices.
        # Ter dois seria pedir que a pessoa declarasse a mesma coisa duas vezes
        # — e deixaria `avaliar` sem as componentes que ela já deu.
        self.sessao.metrica_abstrata = limpo
        self.sessao.tensores.pop(limpo, None)
        return Celula(None, fonte_metrica(nome, texto), "declaracao",
                      {"declarado": [{"nome": limpo, "metrica": True}],
                       "texto": f"{nome} é a métrica em ({metrica.coordenadas}), "
                                f"diagonal, com {len(componentes)} componentes",
                       "latex_exato": sp.latex(metrica.matriz())})

    def _tensor(self, nome, formas, vetores):
        """`A = tensor(0, 2)` — o tipo do Schutz.

        Diz o posto ANTES da primeira aparição, e diz a valência canônica. O
        uso sozinho dizia só o posto, e dizia tarde.
        """
        limpo = nome[1:] if nome.startswith("\\") else nome
        self.sessao.tensores[limpo] = (formas, vetores)
        return Celula(None, f"{nome} = tensor({formas}, {vetores})",
                      "declaracao",
                      {"declarado": [{"nome": limpo,
                                      "tipo": [formas, vetores]}],
                       "texto": (f"{limpo} é tensor do tipo ({formas},{vetores}): "
                                 f"recebe {_conta(formas, '1-forma', '1-formas')}"
                                 f" e {_conta(vetores, 'vetor', 'vetores')}"
                                 f" — {_indices_em(formas, 'em cima')},"
                                 f" {_indices_em(vetores, 'embaixo')}")})

    def _especie(self, nomes, especie):
        r"""`e = euler`, `a = símbolo`, `\mu = índice`.

        A mesma pergunta das outras declarações — o que é este nome? — com as
        outras respostas possíveis. Vira anotação de sítio ou lista do
        documento, e não convenção cega: é uma decisão sobre AQUELES nomes.
        """
        lista = [n.strip() for n in nomes.split(",") if n.strip()]

        if especie.startswith("índice") or especie.startswith("indice"):
            import re as _re
            achou = _re.search(r"\((\s*\d+\s*)\)", especie)
            dimensao = int(achou.group(1)) if achou else None
            self.sessao.indices.extend(n for n in lista
                                       if n not in self.sessao.indices)
            if dimensao and self.sessao.coordenadas and \
                    dimensao != len(self.sessao.coordenadas):
                return Celula(None, f"{nomes} = {especie}", "declaracao",
                              {"erro": f"as coordenadas declaram um espaço de "
                                       f"dimensão {len(self.sessao.coordenadas)}, "
                                       f"e aqui os índices são de dimensão "
                                       f"{dimensao}"})
            if dimensao:
                self.sessao.dimensao = dimensao
            dim = self.sessao.dimensao
            texto = (f"{', '.join(lista)} " +
                     ("é índice" if len(lista) == 1 else "são índices") +
                     f" de um espaço de dimensão {dim}")
        elif especie.lower() in ("métrica", "metrica", "metric"):
            if len(lista) != 1:
                return Celula(None, f"{nomes} = {especie}", "declaracao",
                              {"erro": "um espaço tem uma métrica: declare um "
                                       "nome só"})
            self.sessao.metrica_abstrata = _sem_barra(lista[0])
            self.sessao.tensores.pop(_sem_barra(lista[0]), None)
            texto = (f"{lista[0]} é a métrica do espaço — do tipo (0,2), e "
                     f"é ela que baixa e levanta índice")
        elif especie == "curvatura":
            for n in lista:
                limpo = _sem_barra(n)
                if limpo not in self.sessao.curvaturas:
                    self.sessao.curvaturas.append(limpo)
            texto = (f"{', '.join(lista)}(U,X)W é o operador de curvatura "
                     f"aplicado a W, e não produto — a leitura não fixa o "
                     f"sinal nem a ordem dos argumentos, que variam de livro "
                     f"para livro")
        elif especie == "euler":
            for n in lista:
                self.sessao.anotar("euler", n, {}, "euler")
            texto = f"{', '.join(lista)} é o número de Euler"
        else:
            for n in lista:
                self.sessao.anotar("juxtaposition", n, {}, "product")
            texto = (f"{', '.join(lista)}: símbolo, não função — "
                     f"{lista[0]}(…) é produto")

        return Celula(None, f"{nomes} = {especie}", "declaracao",
                      {"declarado": [{"nome": n, "especie": especie}
                                     for n in lista],
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

    def _registrar(self, objeto):
        """Dá nome a uma equação que saiu de uma conta, e não da folha."""
        nome = self._proximo_nome()
        self.prontos[nome] = Pronta(objeto)
        return nome

    def _objeto(self, nome):
        if nome in self.prontos:
            return self.prontos[nome]
        # O que a tabela imprimiu também é objeto: `A_{t}` está na tela com
        # nome e valor, e não poder pedi-lo de volta é pedir que se redigite o
        # que o programa acabou de calcular.
        # Das duas formas: o despacho tira a barra de `\eta` (que é escrita), e
        # `\Gamma^{r}_{tt}` precisa dela de volta para casar com o que a tabela
        # imprimiu.
        for tentativa in (_chave(nome), _chave("\\" + (nome or ""))):
            if tentativa in self.rotulos:
                return Pronta(self.rotulos[tentativa])
        if nome not in self.nomes:
            conhecidos = ", ".join(sorted(
                list(self.nomes) + list(self.prontos),
                key=lambda n: int(n[2:]) if n[2:].isdigit() else 0))
            if self.rotulos:
                tabela = ("os rótulos da última tabela: "
                          + ", ".join(list(self.rotulos)[:6])
                          + ("…" if len(self.rotulos) > 6 else ""))
                conhecidos = f"{conhecidos}; e {tabela}" if conhecidos else tabela
            raise KeyError(f"não conheço '{nome}' (tenho: {conhecidos or 'nenhum ainda'})")
        expressao = self.sessao.expressao_de(self.nomes[nome])
        if expressao.pending:
            raise ValueError(
                f"'{nome}' tem sítio ambíguo sem decisão; resolva antes de operar")
        return expressao

    def _comando(self, verbo, alvo, segundo=None):
        if verbo in VERBOS_GEOMETRIA.values():
            return self._geometria(verbo, alvo)
        try:
            expressao = self._objeto(alvo)
            if verbo in DE_DOIS:
                if segundo is None:
                    return {"erro": f"{verbo} precisa de duas: "
                                    f"{verbo}(equação, candidata)"}
                candidata = self._objeto(segundo)
        except (KeyError, ValueError) as e:
            return {"erro": str(e)}

        if verbo in ("separar", "conferir"):
            from .modules import load
            operacao = load("resolver").operations[verbo]
            argumentos = ((expressao, candidata) if verbo in DE_DOIS
                          else (expressao,))
            try:
                resultado = operacao.run(*argumentos)
            except ValueError as e:
                return {"erro": str(e), "alvo": alvo}
            saida = self._nomear(resultado)
            saida["alvo"] = alvo
            return saida

        if verbo == "latex":
            return {"latex_exato": sp.latex(expressao.to_sympy()),
                    "exato": sp.sstr(expressao.to_sympy()), "alvo": alvo}
        if verbo == "exportar":
            return {"codigo": self.exportar(alvo), "alvo": alvo}
        if verbo == "contrair":
            return self._contrair(alvo, expressao)
        if verbo == "avaliar":
            if isinstance(expressao.to_sympy(), TensExpr):
                return self._componentes(alvo, expressao)
            if isinstance(expressao, Pronta):
                # O que um verbo produziu não tem fonte em LaTeX para reler.
                d = self.sessao.avaliar_objeto(expressao.to_sympy())
            else:
                d = Sessao.avaliar(self._sessao_de(alvo))
            d["alvo"] = alvo
            return d
        if verbo == "simplificar":
            objeto = sp.simplify(expressao.to_sympy())
            return {"alvo": alvo, "exato": sp.sstr(objeto),
                    "latex_exato": sp.latex(objeto),
                    "nomeados": [self._nome_de(objeto)]}
        return self._resolver(alvo, expressao)

    def _provar(self, alvo, hipoteses):
        """O objetivo, a partir das hipóteses nomeadas — e de nada mais."""
        from .prova import NaoEVetorial, SemProva, linhas, provar

        if alvo in hipoteses:
            return {"erro": f"'{alvo}' está entre as próprias hipóteses: "
                            f"isso não prova nada", "alvo": alvo}
        try:
            objetivo = self._objeto(alvo).to_sympy()
            dadas = {h: self._objeto(h).to_sympy() for h in hipoteses}
        except (KeyError, ValueError) as e:
            return {"erro": str(e), "alvo": alvo}

        try:
            prova = provar(objetivo, dadas, self.sessao.tensores)
        except (SemProva, NaoEVetorial) as e:
            return {"erro": str(e), "alvo": alvo}

        tabela = linhas(prova)
        usadas = ", ".join(prova.hipoteses_usadas) or "nenhuma hipótese"
        sobrou = [h for h in hipoteses if h not in prova.hipoteses_usadas]
        nota = f"; não precisou de {', '.join(sobrou)}" if sobrou else ""
        tabela.append(["somando", sp.sstr(objetivo),
                       sp.latex(objetivo) + r"\quad\blacksquare"])
        texto = (f"provado a partir de {usadas}, e da linearidade de ∇, "
                 f"do colchete e de R{nota}")
        tabela.append(["usou", texto])
        return {"alvo": alvo, "latex_exato": sp.latex(objetivo),
                "exato": sp.sstr(objetivo), "linhas": tabela, "texto": texto}

    def _contrair(self, alvo, expressao):
        r"""`g_{\mu\nu}A^\nu` vira `A_\mu`: baixar o índice, de fato.

        Não é simplificação nem cosmética — é a convenção da métrica aplicada,
        e por isso exige que alguém tenha dito qual é a métrica.
        """
        from .tensores import SemMetrica, contrair, latex_de, livres

        objeto = expressao.to_sympy()
        if not isinstance(objeto, TensExpr):
            return {"erro": f"'{alvo}' não é expressão tensorial: contrair "
                            f"baixa índice com a métrica, e aqui não há índice",
                    "alvo": alvo}
        espaco = expressao.document.espaco
        try:
            saida = contrair(objeto, espaco)
        except SemMetrica as e:
            return {"erro": str(e), "alvo": alvo}
        if saida == objeto:
            return {"erro": "não há índice para baixar ou levantar: a métrica "
                            "não aparece contraída com nada aqui",
                    "alvo": alvo}
        nome = self._registrar(saida)
        return {"alvo": alvo, "exato": sp.sstr(saida),
                "latex_exato": latex_de(saida, espaco),
                "indices_livres": livres(saida, espaco),
                "nomeados": [{"nome": nome, "sympy": sp.sstr(saida),
                              "latex": latex_de(saida, espaco)}]}

    def _componentes(self, alvo, expressao):
        """As componentes, que é o que a métrica declarada com números dá.

        A estrutura vem dos índices; o valor vem das componentes. Avaliar uma
        expressão tensorial é pedir o segundo, e por isso exige o segundo.
        """
        from . import geometria

        # Da SESSÃO, e não da expressão: o que veio de um verbo é objeto puro,
        # sem documento atrás. O espaço é do caderno de qualquer modo.
        espaco = self.sessao.documento()[0].espaco
        nome = espaco.metrica if espaco else None
        if nome not in self.metricas:
            return {"erro": "avaliar componentes precisa da métrica com "
                            "componentes: declare `g = métrica(...)` com uma "
                            "entrada por coordenada",
                    "alvo": alvo}
        metrica = self.metricas[nome]
        # SEM contrair antes: é a métrica escrita que carrega as componentes
        # com que se baixa o índice. Contraí-la primeiro deixa `A_\mu` sozinho
        # e sem por onde descer.
        objeto = expressao.to_sympy()
        try:
            linhas = geometria.componentes(objeto, espaco, metrica)
        except ValueError as e:
            return {"erro": str(e), "alvo": alvo}
        self._guardar_rotulos(linhas)
        return {"alvo": alvo, "proveniencia": "estabelecida",
                "apresentavel": True,
                "rotulo": f"{alvo} em componentes: {_conta(len(linhas), 'componente', 'componentes')}",
                "linhas": ([["coordenadas", metrica.coordenadas,
                             metrica.coordenadas]]
                           + [[r, sp.sstr(v), sp.latex(v)] for r, v in linhas]),
                "latex_tabela": _tabela_latex(linhas)}

    def _guardar_rotulos(self, linhas):
        r"""O que a tabela imprimiu passa a ser procurável pelo rótulo.

        A tabela ANTERIOR sai de cena: dois `christoffel` de métricas
        diferentes dariam `\Gamma^{r}_{tt}` para as duas, e devolver a de antes
        seria devolver a resposta de outra pergunta.
        """
        self.rotulos = {_chave(rot): valor for rot, valor in linhas}

    def _nome_de(self, objeto):
        nome = self._registrar(objeto)
        return {"nome": nome, "sympy": sp.sstr(objeto),
                "latex": sp.latex(objeto)}

    def _nomear(self, resultado):
        """Batiza o que a operação produziu, e devolve os nomes junto.

        Uma operação que devolve equações sem nome devolve becos: o usuário lê
        duas EDOs numa tabela e não tem como pedir a próxima conta sobre elas
        senão redigitando.
        """
        saida = resultado.to_dict()
        saida["nomeados"] = [self._nome_de(o) for o in resultado.produz]
        return saida

    def _geometria(self, verbo, alvo):
        """Christoffel, Ricci, Riemann, escalar — a partir das componentes.

        O que sai são COMPONENTES num sistema de coordenadas, e não o tensor:
        trocar de carta troca todas elas. O que não muda são as afirmações
        invariantes — Ricci nulo é Ricci nulo em qualquer carta —, e por isso o
        resultado diz em que coordenadas está.
        """
        from . import geometria

        if alvo not in self.metricas:
            conhecidas = ", ".join(self.metricas) or "nenhuma ainda"
            return {"erro": f"não conheço a métrica '{alvo}' "
                            f"(tenho: {conhecidas})"}
        metrica = self.metricas[alvo]
        calculo = getattr(geometria, verbo)
        resultado = calculo(metrica)

        base = {"alvo": alvo, "proveniencia": "estabelecida",
                "apresentavel": True,
                "coordenadas": metrica.coordenadas}
        if verbo == "escalar":
            base.update({"rotulo": f"escalar de Ricci de {alvo}",
                         "exato": sp.sstr(resultado),
                         "latex_exato": sp.latex(resultado),
                         "linhas": [["coordenadas", metrica.coordenadas]]})
            return base

        simbolo = {"christoffel": "\\Gamma", "ricci": "R", "riemann": "R"}[verbo]
        resultado, todas = resultado
        self._guardar_rotulos([(simbolo + rot, valor)
                               for rot, valor in todas.items()])
        linhas = [["coordenadas", metrica.coordenadas, metrica.coordenadas]]
        linhas += [[simbolo + rot, sp.sstr(valor), sp.latex(valor)]
                   for rot, valor in resultado]
        if not resultado:
            linhas.append(["resultado", "todas as componentes são nulas"])
        base.update({"rotulo": f"{verbo} de {alvo}: "
                               f"{len(resultado)} componente(s) não nula(s)",
                     "linhas": linhas,
                     "latex_tabela": _tabela_latex(
                         [(simbolo + rot, valor) for rot, valor in resultado])})
        return base

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
            saida = self._nomear(resultado)
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
            aplicadas = [a for d in objeto.atoms(sp.Derivative)
                         for a in d.expr.atoms(sp.core.function.AppliedUndef)]
            incognita = sorted(aplicadas, key=lambda a: a.func.__name__)[0]
            argumento = sp.sstr(incognita)
            # Solver por espécie: a incógnita de várias variáveis é EDP.
            verbo = "pdsolve" if len(incognita.args) > 1 else "dsolve"
            confere = "checkpdesol" if len(incognita.args) > 1 else "checkodesol"
            linhas += ["", f"solucao = {verbo}({nome}, {argumento})",
                       f"{confere}({nome}, solucao)   # confere por substituição"]
        elif isinstance(objeto, sp.Equality):
            livres = sorted(objeto.free_symbols, key=str)
            if livres:
                linhas += ["", f"solucao = solve({nome}, {livres[0]})"]
        else:
            linhas += ["", f"valor = simplify({nome}.doit())"]
        return "\n".join(linhas)
