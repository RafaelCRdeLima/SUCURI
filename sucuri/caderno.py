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
_RE_COMANDO = re.compile(r"^\s*([^\W\d]\w*)\s*\(\s*(" + _ROTULO + r")\s*"
                         r"(?:,\s*(" + _ROTULO + r")\s*)?\)\s*$")
# `provar(eq5, eq1, eq2)`: o objetivo e as hipóteses, quantas forem. Forma
# própria porque os outros verbos recebem um ou dois rótulos, e a lista de
# hipóteses é justamente o que não pode ficar implícito.
_RE_PROVAR = re.compile(r"^\s*(?:provar|prove)\s*\(\s*(" + _ROTULO +
                        r"(?:\s*,\s*" + _ROTULO + r")*)\s*\)\s*$", re.I)
# `h = induzida(g, X^1(u), …)`: o pull-back de g pela parametrização — um
# mergulho, ou uma mudança de coordenadas.
_RE_INDUZIDA = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*induzida\s*\((.*)\)\s*$", re.I | re.S)
# `volume(g, \psi = 0 .. \pi, …)` e `série(eq3, \epsilon, 5)`: argumentos que
# não são só rótulos.
_RE_VOLUME = re.compile(r"^\s*volume\s*\((.*)\)\s*$", re.I | re.S)
_RE_SERIE = re.compile(r"^\s*(?:s[ée]rie|series)\s*\((.*)\)\s*$", re.I | re.S)
# `A = campo(A^r, A^θ)`, `W = covetor(…)`: campos por componentes na carta.
_RE_CAMPO = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*(campo|covetor)\s*\((.*)\)\s*$", re.I | re.S)
# `\alpha = forma(a dr + b d\theta)`: forma numa carta, com d das coordenadas.
# `\beta = estrela(\alpha, g)`, `cunha(α, β)`, `exterior(α)`, `interior(X, α)`,
# `lie(X, α)`: operações, com ou sem nome à esquerda.
_RE_FORMA_C = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*forma\s*\((.*[^0-9\s].*)\)\s*$", re.I | re.S)
_RE_OP_FORMA = re.compile(r"^\s*(?:(\\?[A-Za-z]\w*)\s*=\s*)?(cunha|exterior|estrela|interior|lie|iguais|ortonormal)\s*\((.*)\)\s*$", re.I | re.S)
# `killing(g, X)`, `killing(g, 1)`, `colchete(X, Y)`, `nabla(g, A)`,
# `laplaciano(g, A)`, `restringir(K, h)`: verbos de campos por componentes.
_RE_VERBO_CAMPO = re.compile(r"^\s*(killing|colchete|nabla|laplaciano|restringir)\s*\((.*)\)\s*$", re.I | re.S)
# `independentes(C, eq3, eq4)`: um tensor e as equações que ele satisfaz.
_RE_INDEPENDENTES = re.compile(r"^\s*(?:independentes|independent)\s*\(\s*(" +
                               _ROTULO + r"(?:\s*,\s*" + _ROTULO +
                               r")*)\s*\)\s*$", re.I)
# `\omega = forma(2)`: uma 2-forma — um (0,2) antissimétrico.
_RE_FORMA = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*forma\s*\(\s*(\d+)\s*\)\s*$",
                       re.I)
# `R = riemann(eq1)`: R é o Riemann de ∇, na convenção que eq1 escreve.
_RE_RIEMANN = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*(riemann|christoffel|ricci)\s*"
                         r"\(\s*(" + _ROTULO + r")\s*\)\s*$", re.I)
# Declaração na folha: `u = u(t,x)`, com o MESMO nome dos dois lados.
#
# A repetição é o que distingue declaração de matemática. `u(t,x)` sozinho é
# uma expressão legítima — aplicação, ou produto, que é justamente um sítio
# ambíguo — e engoli-la como declaração seria decidir por quem escreveu.
# `u = u(t,x)` é tautologia: ninguém escreve isso como equação.
_RE_DECLARA = re.compile(r"^\s*(\\?[A-Za-z]\w*)\s*=\s*\1\s*\([^)]*\)\s*$")

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
                        r"(\d+)\s*,\s*(\d+)\s*"
                        r"(?:,\s*((?:anti-?s?)?sim[ée]tric[oa]|riemann)\s*)?\)\s*$",
                        re.I)

# A forma antiga, para dizer o que mudou em vez de falhar em LaTeX.
_RE_COLCHETE = re.compile(r"^\s*([A-Za-z]\w*)\s*(?:=\s*\1\s*)?\[[^\]]*\]\s*$")

# As outras duas coisas que um nome pode ser, além de função de alguma coisa.
# Ficam na mesma forma porque são a mesma pergunta: o que é este nome?
_RE_ESPECIE = re.compile(r"^\s*((?:\\?[A-Za-z]\w*)(?:\s*,\s*\\?[A-Za-z]\w*)*)"
                         r"\s*=\s*(euler|s[ií]mbolo|constante|m[ée]trica"
                         r"|curvatura|kronecker|hodge|coordenadas?"
                         r"|det(?:erminante)?\s*\(\s*\\?[A-Za-z]\w*\s*\)"
                         r"|levi-?civita(?:\s*\(\s*[^)]*\))?"
                         r"|metric|[ií]ndices?(?:\s*\(\s*(?:\d+|[A-Za-z]\w*)\s*\))?)\s*$", re.I)

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
    "indices": "indices", "índices": "indices", "indexar": "indices",
    "expandir": "expandir", "expand": "expandir",
    "independentes": "independentes", "independent": "independentes",
    "em_componentes": "em_componentes",
    "linearizar": "linearizar", "linearize": "linearizar",
    "geodesicas": "geodesicas", "geodésicas": "geodesicas", "geodesics": "geodesicas",
    "volume": "volume", "serie": "serie", "série": "serie",
    "orbitas": "orbitas", "órbitas": "orbitas",
    "elemento": "elemento", "em_carta": "em_carta",
    "cartan": "cartan", "tetrada": "cartan", "tétrada": "cartan",
    "killing": "killing", "colchete": "colchete", "nabla": "nabla",
    "cunha": "cunha", "exterior": "exterior", "estrela": "estrela",
    "interior": "interior", "lie": "lie", "iguais": "iguais", "ortonormal": "ortonormal",
    "laplaciano": "laplaciano", "restringir": "restringir",
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


def _latex_de(objeto):
    """LaTeX com o impressor que sabe escrever ∂_μ A^ν."""
    from .derivadas import latex
    return latex(objeto)


def _qual_simetria(escrito):
    if not escrito:
        return None
    if escrito.lower() == "riemann":
        return "riemann"
    return "antissimetrico" if escrito.lower().startswith("anti") else "simetrico"


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
               (_RE_COORDENADAS, _RE_METRICA, _RE_TENSOR, _RE_ESPECIE, _RE_INDUZIDA, _RE_CAMPO,
                _RE_DECLARA, _RE_COLCHETE, _RE_PROVAR, _RE_RIEMANN, _RE_FORMA))


def _chave(rotulo):
    r"""`A_{t}`, `A_t` e `A_ {t}` são o mesmo rótulo.

    Chave e espaço são tipografia do TeX, não identidade do objeto. Exigir a
    forma exata que a tabela imprimiu — `\Gamma^{r}_{{t}{t}}`, com as chaves
    duplas que existem só para o KaTeX não colar as macros — seria cobrar do
    usuário um detalhe de impressão.
    """
    return "".join(c for c in (rotulo or "") if c not in "{} \t")


def _tem_indice(expr):
    """Uma expressão (ou igualdade) com tensor de índice?"""
    from sympy.tensor.tensor import TensExpr
    if isinstance(expr, sp.Equality):
        return any(isinstance(l, TensExpr) for l in (expr.lhs, expr.rhs))
    return isinstance(expr, TensExpr)


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
        self.campos = {}            # nome -> Campo, por componentes numa carta
        self.formas_c = {}          # nome -> FormaC, forma numa carta
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

        induz = _RE_INDUZIDA.match(fonte or "")
        if induz:
            return self._induzida(induz.group(1), induz.group(2))

        fc = _RE_FORMA_C.match(fonte or "")
        if fc and self.sessao.coordenadas and not _RE_FORMA.match(fonte or ""):
            return self._forma_carta(fc.group(1), fc.group(2))

        opf = _RE_OP_FORMA.match(fonte or "")
        if opf:
            return Celula(None, fonte, "comando",
                          self._op_forma(opf.group(1), opf.group(2).lower(), opf.group(3)))

        campo = _RE_CAMPO.match(fonte or "")
        if campo:
            return self._campo(campo.group(1), campo.group(2).lower(), campo.group(3))

        tensorial = _RE_TENSOR.match(fonte or "")
        if tensorial:
            return self._tensor(tensorial.group(1), int(tensorial.group(2)),
                                int(tensorial.group(3)),
                                _qual_simetria(tensorial.group(4)))

        forma = _RE_FORMA.match(fonte or "")
        if forma:
            p = int(forma.group(2))
            if p == 0:
                return Celula(None, fonte, "declaracao", {"erro": (
                    "uma 0-forma é uma função: não precisa declarar — todo "
                    "símbolo que não é tensor já é escalar")})
            celula = self._tensor(forma.group(1), 0, p,
                                  "antissimetrico" if p >= 2 else None)
            if not celula.dados.get("erro"):
                celula.dados["texto"] = (
                    f"{forma.group(1)} é uma {p}-forma — um (0,{p}) "
                    f"{'antissimétrico' if p >= 2 else ''}".rstrip() +
                    ". d, ∧, ι_X e ℒ_X agem nela; ι_Y ι_X ω = ω(X, Y), na "
                    "convenção do determinante")
            return celula

        riemann = _RE_RIEMANN.match(fonte or "")
        if riemann and riemann.group(2).lower() == "christoffel":
            return self._christoffel(riemann.group(1), _sem_barra(riemann.group(3)))
        if riemann and riemann.group(2) == "ricci":
            return self._ricci(riemann.group(1), _sem_barra(riemann.group(3)))
        if riemann:
            return self._riemann(riemann.group(1), _sem_barra(riemann.group(3)))

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

        vc = _RE_VERBO_CAMPO.match(fonte or "")
        if vc:
            return Celula(None, fonte, "comando", self._verbo_campo(vc.group(1).lower(), vc.group(2)))

        vol = _RE_VOLUME.match(fonte or "")
        if vol:
            return Celula(None, fonte, "comando", self._volume(vol.group(1)))
        serie = _RE_SERIE.match(fonte or "")
        if serie:
            return Celula(None, fonte, "comando", self._serie(serie.group(1)))

        contagem = _RE_INDEPENDENTES.match(fonte or "")
        if contagem:
            rotulos = [_sem_barra(r.strip()) for r in contagem.group(1).split(",")]
            return Celula(None, fonte, "comando",
                          self._independentes(rotulos[0], rotulos[1:]))

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
        assinatura = self._assinatura(nome, texto)
        if assinatura is not None:
            return assinatura
        if not self.sessao.coordenadas:
            return Celula(None, fonte_metrica(nome, texto), "declaracao",
                          {"erro": "declare as coordenadas antes da métrica: "
                                   "componente sem coordenada não diz de quê "
                                   "é componente"})
        if re.match(r"^\s*ds\s*\^\s*\{?2\}?\s*=", texto):
            return self._elemento_de_linha(nome, texto)
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

    def _registrar_metrica(self, nome, fonte, metrica, como):
        metrica.escrito = nome
        limpo = _sem_barra(nome)
        self.metricas[limpo] = metrica
        self.sessao.metrica_abstrata = limpo
        self.sessao.tensores.pop(limpo, None)
        return Celula(None, fonte, "declaracao",
                      {"declarado": [{"nome": limpo, "metrica": True}],
                       "texto": f"{nome} é a métrica em ({metrica.coordenadas}), "
                                + como,
                       "latex_exato": sp.latex(metrica.matriz())})

    def _elemento_de_linha(self, nome, texto):
        r"""`g = métrica(ds^2 = -dt^2 + 2a\,dt\,d\phi + …)`: com termos cruzados.

        Cada d<coordenada> vira uma incógnita; o que se lê tem de ser uma forma
        quadrática nelas, e os coeficientes são a matriz — o termo cruzado
        dividido por dois, que é como ds² o escreve."""
        from .geometria import Metrica
        fonte = fonte_metrica(nome, texto)
        corpo = texto.split("=", 1)[1]
        corpo = re.sub(r"\\mathrm\{d\}", "d", corpo)
        marcas = []
        for k, s_ in enumerate(self.sessao.coordenadas):
            escrito = self.sessao.escrita_coord.get(str(s_), str(s_))
            marca = f"Q_{{{k}}}"
            padrao = r"(?<![A-Za-z\\])d\s*" + re.escape(escrito) + r"(?![A-Za-z])"
            corpo, n = re.subn(padrao, " " + marca + " ", corpo)
            marcas.append(sp.Symbol(f"Q_{{{k}}}"))
        expressao = self.sessao.expressao_de(corpo)
        if expressao.pending:
            return Celula(None, fonte, "declaracao",
                          {"erro": "; ".join(expressao.questions())})
        forma = sp.expand(expressao.to_sympy())
        n = len(marcas)
        G = sp.zeros(n, n)
        for i in range(n):
            for j in range(n):
                if i == j:
                    G[i, i] = forma.coeff(marcas[i], 2)
                else:
                    G[i, j] = forma.coeff(marcas[i], 1).coeff(marcas[j], 1) / 2
        resto = sp.expand(forma - sum(G[i, j] * marcas[i] * marcas[j]
                                      for i in range(n) for j in range(n)))
        if resto != 0 or any(G[i, j].has(*marcas) for i in range(n) for j in range(n)):
            return Celula(None, fonte, "declaracao", {"erro": (
                "o elemento de linha tem de ser quadrático nos d das coordenadas "
                f"({', '.join('d' + self.sessao.escrita_coord.get(str(c), str(c)) for c in self.sessao.coordenadas)}); "
                f"sobrou {sp.sstr(resto)}")})
        G = G.applyfunc(sp.simplify)
        try:
            metrica = Metrica(_sem_barra(nome), self.sessao.coordenadas, G,
                              self.sessao.escrita_coord)
        except ValueError as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        return self._registrar_metrica(nome, fonte, metrica,
                                       "dada pelo elemento de linha")

    def _induzida(self, nome, texto):
        r"""`h = induzida(g, X^1, …, X^n)`: o pull-back de g pela parametrização
        X^a(u), com u as coordenadas declaradas por último."""
        from .geometria import induzida
        fonte = f"{nome} = induzida({texto.strip()})"
        partes = self._argumentos(texto)
        amb = _sem_barra(partes[0]) if partes else ""
        if amb not in self.metricas:
            return Celula(None, fonte, "declaracao", {"erro": (
                f"induzida(g, …) começa pela métrica de onde se puxa — "
                f"'{partes[0] if partes else ''}' não é métrica com componentes")})
        ambiente = self.metricas[amb]
        if list(self.sessao.coordenadas) == list(ambiente.simbolos):
            return Celula(None, fonte, "declaracao", {"erro": (
                "declare as coordenadas novas antes — x = coordenadas(u, v): "
                "a métrica induzida vive nelas")})
        imagens = []
        for escrito in partes[1:]:
            e = self.sessao.expressao_de(escrito)
            if e.pending:
                return Celula(None, fonte, "declaracao",
                              {"erro": f"'{escrito}': " + "; ".join(e.questions())})
            imagens.append(e.to_sympy())
        try:
            metrica = induzida(ambiente, list(self.sessao.coordenadas), imagens,
                               self.sessao.escrita_coord, _sem_barra(nome))
        except ValueError as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        return self._registrar_metrica(
            nome, fonte, metrica,
            f"o pull-back de {partes[0]} por "
            f"({', '.join(partes[1:])})")

    def _campo(self, nome, especie, texto):
        r"""`X = campo(0, 1)`, `A = campo()`, `W = covetor(…)`: na carta atual."""
        from .campos import Campo
        limpo = _sem_barra(nome)
        fonte = f"{nome} = {especie}({texto.strip()})"
        if not self.sessao.coordenadas:
            return Celula(None, fonte, "declaracao",
                          {"erro": "declare as coordenadas antes: as componentes são numa carta"})
        cima = especie == "campo"
        partes = self._argumentos(texto)
        try:
            if not partes:
                c = Campo.generico(limpo, list(self.sessao.coordenadas),
                                   self.sessao.escrita_coord, cima)
            else:
                comps = []
                for p_ in partes:
                    e = self.sessao.expressao_de(p_)
                    if e.pending:
                        return Celula(None, fonte, "declaracao",
                                      {"erro": f"'{p_}': " + "; ".join(e.questions())})
                    comps.append(e.to_sympy())
                c = Campo(limpo, list(self.sessao.coordenadas), comps,
                          self.sessao.escrita_coord, cima)
        except ValueError as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        self.campos[limpo] = c
        base = [("∂_" if cima else "d") + self.sessao.escrita_coord.get(str(x), str(x))
                for x in self.sessao.coordenadas]
        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": limpo, "campo": True}],
            "texto": (f"{nome} = " + " + ".join(f"({sp.sstr(v)}) {b}" for v, b in zip(c.componentes, base))
                      + f" — {'vetor' if cima else 'covetor'}, na base coordenada")})

    def _forma_carta(self, nome, texto):
        from .formas_carta import FormaMalEscrita, ler
        limpo = _sem_barra(nome)
        fonte = f"{nome} = forma({texto.strip()})"
        def expr(t):
            e = self.sessao.expressao_de(t)
            if e.pending:
                raise FormaMalEscrita("; ".join(e.questions()))
            return e.to_sympy()
        try:
            f = ler(texto, list(self.sessao.coordenadas), self.sessao.escrita_coord, expr)
        except (FormaMalEscrita, ValueError) as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        self.formas_c[limpo] = f
        t, l = f.texto(self.sessao.escrita_coord)
        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": limpo, "forma": f.grau}],
            "texto": f"{nome} = {t} — uma {f.grau}-forma na carta ({', '.join(map(str, self.sessao.coordenadas))})",
            "latex_exato": l})

    def _op_forma(self, nome, verbo, texto):
        from . import formas_carta as F
        partes = [_sem_barra(p_) for p_ in self._argumentos(texto)]
        def forma(n):
            if n in self.formas_c:
                return self.formas_c[n]
            if re.fullmatch(r"-?\d+", n):          # ⋆1: a 0-forma constante
                return F.FormaC(list(self.sessao.coordenadas), {(): sp.Integer(n)}, 0)
            raise KeyError(f"não conheço a forma '{n}' (tenho: {', '.join(self.formas_c) or 'nenhuma'})")
        try:
            if verbo == "iguais":
                a, b = forma(partes[0]), forma(partes[1])
                dif = a + b.escalar(-1)
                return {"alvo": partes[0], "exato": "True" if dif.nula() else "False",
                        "texto": (f"{partes[0]} = {partes[1]}" if dif.nula() else
                                  f"{partes[0]} − {partes[1]} = {dif.texto(self.sessao.escrita_coord)[0]}")}
            if verbo == "ortonormal":
                o = F.ortonormal(forma(partes[0]), self._metrica_de(partes[1]))
                t, l = F.texto_ortonormal(o, self.sessao.escrita_coord)
                return {"alvo": partes[0], "exato": t, "latex_exato": l,
                        "texto": f"{partes[0]} no cobase ortonormal σ^i = √|g_ii| dx^i"}
            if verbo == "cunha":
                r = F.cunha(forma(partes[0]), forma(partes[1]))
            elif verbo == "exterior":
                r = F.exterior(forma(partes[0]))
            elif verbo == "estrela":
                r = F.estrela(forma(partes[0]), self._metrica_de(partes[1]))
            elif verbo in ("interior", "lie"):
                if partes[0] not in self.campos:
                    raise KeyError(f"não conheço o campo '{partes[0]}'")
                f = forma(partes[1])
                r = (F.interior if verbo == "interior" else F.lie)(self.campos[partes[0]], f)
        except (KeyError, IndexError, ValueError) as e:
            return {"erro": str(e.args[0]) if e.args else "argumentos a menos"}
        escrita = self.sessao.escrita_coord
        t, l = r.texto(escrita)
        rotulo = {"cunha": "∧", "exterior": "d", "estrela": "⋆", "interior": "ι", "lie": "ℒ"}[verbo]
        if nome:
            self.formas_c[_sem_barra(nome)] = r
        return {"alvo": partes[0], "exato": t, "latex_exato": l,
                "texto": (f"{nome + ' = ' if nome else ''}{rotulo}(" + ", ".join(partes) + f") — uma {r.grau}-forma")}

    def _verbo_campo(self, verbo, texto):
        from . import campos as C
        partes = [_sem_barra(p_) for p_ in self._argumentos(texto)]
        def campo(n):
            if n not in self.campos:
                raise KeyError(f"não conheço o campo '{n}' (tenho: {', '.join(self.campos) or 'nenhum'})")
            return self.campos[n]
        try:
            if verbo == "colchete":
                X, Y = campo(partes[0]), campo(partes[1])
                v = C.colchete(X, Y)
                nome = f"[{X.nome},{Y.nome}]"
                return self._saida_campo(nome, v, X)
            if verbo == "restringir":
                K = campo(partes[0])
                metrica = self._metrica_de(partes[1])
                c = C.restringir(K, metrica)
                self.campos[c.nome] = c
                return self._saida_campo(c.nome, c.componentes, c,
                                         f"{c.nome} restrito, na carta de {partes[1]} — e registrado com o mesmo nome")
            metrica = self._metrica_de(partes[0])
            if verbo == "killing" and len(partes) > 1 and partes[1].isdigit():
                base = C.killings(metrica, int(partes[1]))
                linhas = [[f"K_{i + 1}", sp.sstr(b), sp.latex(sp.Matrix(b).T)] for i, b in enumerate(base)]
                return {"alvo": partes[0], "exato": str(len(base)), "linhas": linhas,
                        "texto": (f"{len(base)} campos de Killing independentes com componentes "
                                  f"polinomiais de grau ≤ {partes[1]} na carta ({metrica.coordenadas})")}
            if verbo == "killing":
                L = C.lie_metrica(metrica, campo(partes[1]))
                nulo = all(e == 0 for e in L)
                return {"alvo": partes[1], "exato": "True" if nulo else sp.sstr(L),
                        "latex_exato": sp.latex(L),
                        "texto": (f"ℒ_{partes[1]} g = 0: {partes[1]} é de Killing" if nulo
                                  else f"ℒ_{partes[1]} g ≠ 0: {partes[1]} não é de Killing")}
            A = campo(partes[1])
            esc = lambda x: metrica.escrita.get(str(x), str(x))
            marca = "^" if A.cima else "_"
            if verbo == "nabla":
                D = C.nabla(metrica, A)
                D2 = C.nabla2(metrica, A)
                n = len(metrica.simbolos)
                linhas = [[f"{A.nome}{marca}{{{esc(metrica.simbolos[j])}}}_{{;{esc(metrica.simbolos[i])}}}",
                           sp.sstr(D[i][j]), sp.latex(D[i][j])] for i in range(n) for j in range(n)]
                linhas += [[f"{A.nome}{marca}{{{esc(metrica.simbolos[j])}}}_{{;{esc(metrica.simbolos[i])}{esc(metrica.simbolos[k])}}}",
                            sp.sstr(D2[i][k][j]), sp.latex(D2[i][k][j])]
                           for i in range(n) for k in range(n) for j in range(n)]
                return {"alvo": partes[1], "linhas": linhas,
                        "exato": "; ".join(f"{l[0]} = {l[1]}" for l in linhas),
                        "texto": "as primeiras e as segundas derivadas covariantes, na base coordenada"}
            if verbo == "laplaciano":
                L = C.laplaciano(metrica, A)
                n = len(metrica.simbolos)
                linhas = [[f"∇²{A.nome}{marca}{{{esc(metrica.simbolos[j])}}}", sp.sstr(L[j]), sp.latex(L[j])]
                          for j in range(n)]
                return {"alvo": partes[1], "linhas": linhas,
                        "exato": "; ".join(f"{l[0]} = {l[1]}" for l in linhas),
                        "texto": "g^{ik}∇_i∇_k, componente por componente"}
        except (KeyError, IndexError, ValueError) as e:
            return {"erro": str(e.args[0]) if e.args else "argumentos a menos"}
        return {"erro": f"{verbo}: argumentos inesperados"}

    def _saida_campo(self, nome, comps, ref, texto=None):
        base = ["∂_" + ref.escrita.get(str(x), str(x)) for x in ref.simbolos]
        exato = " + ".join(f"({sp.sstr(v)})*{b}" for v, b in zip(comps, base) if v != 0) or "0"
        return {"alvo": nome, "exato": exato,
                "linhas": [[f"{nome}^{b[2:]}", sp.sstr(v), sp.latex(v)] for v, b in zip(comps, base)],
                "texto": texto or f"{nome}, na base coordenada"}

    def _metrica_de(self, alvo):
        if _sem_barra(alvo) not in self.metricas:
            conhecidas = ", ".join(self.metricas) or "nenhuma ainda"
            raise KeyError(f"não conheço a métrica '{alvo}' (tenho: {conhecidas})")
        return self.metricas[_sem_barra(alvo)]

    def _geodesicas(self, alvo):
        """`geodesicas(g)`: ẍ^a + Γ^a_{bc}ẋ^bẋ^c = 0, e o que se conserva."""
        from . import geometria
        try:
            metrica = self._metrica_de(alvo)
        except KeyError as e:
            return {"erro": str(e.args[0]), "alvo": alvo}
        equacoes, conservadas, _, lam = geometria.geodesicas(metrica)
        linhas = [["coordenadas", metrica.coordenadas, metrica.coordenadas]]
        nomeados = []
        for eq in equacoes:
            nome = self._registrar(eq)
            nomeados.append({"nome": nome, "sympy": sp.sstr(eq), "latex": sp.latex(eq)})
            linhas.append([nome, sp.sstr(eq), sp.latex(eq)])
        for rotulo, q in conservadas:
            linhas.append([f"conserva-se ({rotulo})", sp.sstr(q), sp.latex(q)])
        linhas.append(["pela ação", "as equações de Euler–Lagrange de ∫ g(ẋ,ẋ) dλ "
                       "são −2g_ab vezes estas: conferido"])
        return {"alvo": alvo, "rotulo": f"geodésicas de {alvo}, com parâmetro afim λ",
                "linhas": linhas, "nomeados": nomeados,
                "exato": "; ".join(sp.sstr(e) for e in equacoes),
                "texto": ("as equações das geodésicas, uma por coordenada, e o "
                          "que se conserva ao longo delas: g(ẋ, ẋ), pelo "
                          "parâmetro ser afim, e g(∂_k, ẋ) para cada coordenada "
                          "de que a métrica não depende")}

    def _orbitas(self, alvo):
        """`órbitas(g)`: as geodésicas de uma métrica 2D por quadratura."""
        from . import geometria
        try:
            metrica = self._metrica_de(alvo)
            o = geometria.orbitas(metrica)
        except (KeyError, ValueError) as e:
            return {"erro": str(e.args[0]), "alvo": alvo}
        esc = lambda s_: metrica.escrita.get(str(s_), str(s_))
        linhas = [["conservadas", f"L = g_φφ φ̇ e κ = g(ẋ,ẋ): κ = −1, 0, 1 para tipo tempo, nula, tipo espaço (na assinatura da métrica)"],
                  [f"d{esc(o['phi'])}/d{esc(o['r'])}", sp.sstr(o["dphi_dr"]), sp.latex(o["dphi_dr"])]]
        nomeados = []
        if "v" in o:
            linhas.append(["substituição", f"v = {sp.sstr(o['v'])}", "v = " + sp.latex(o["v"])])
        if "integral" in o:
            linhas.append([f"{esc(o['phi'])} − φ₀", sp.sstr(o["integral"]), sp.latex(o["integral"])])
            linhas.append(["vale se", sp.sstr(o["condicao"]), sp.latex(o["condicao"])])
            for eq in o["orbita"]:
                nome = self._registrar(eq)
                nomeados.append({"nome": nome, "sympy": sp.sstr(eq), "latex": sp.latex(eq)})
                linhas.append([nome, sp.sstr(eq), sp.latex(eq)])
        exato = "; ".join(sp.sstr(e) for e in o.get("orbita", [])) or sp.sstr(o["dphi_dr"])
        return {"alvo": alvo, "exato": exato, "linhas": linhas, "nomeados": nomeados,
                "rotulo": f"órbitas geodésicas de {alvo}",
                "texto": ("por quadratura: as duas quantidades conservadas dão "
                          "dφ/dr, e a substituição dv = √|g_rr|/g_φφ dr reduz a "
                          "integral a uma forma elementar")}

    def _volume(self, texto):
        r"""`volume(g, \psi = 0 .. \pi, …)`: ∫√|det g|, com o elemento escrito."""
        from . import geometria
        partes = self._argumentos(texto)
        try:
            metrica = self._metrica_de(partes[0])
        except KeyError as e:
            return {"erro": str(e.args[0])}
        limites = []
        for p in partes[1:]:
            m = re.match(r"^(.*?)=(.*?)\.\.(.*)$", p)
            if not m:
                return {"erro": f"'{p}': escreva o limite como x = a .. b"}
            lidos = []
            for pedaco in m.groups():
                e = self.sessao.expressao_de(pedaco.strip())
                if e.pending:
                    return {"erro": f"'{pedaco}': " + "; ".join(e.questions())}
                lidos.append(e.to_sympy().subs(sp.Symbol("pi"), sp.pi))
            limites.append(tuple(lidos))
        try:
            raiz, valor = geometria.volume(metrica, limites)
        except ValueError as e:
            return {"erro": str(e)}
        nome = self._registrar(valor)
        return {"alvo": partes[0], "exato": sp.sstr(valor), "latex_exato": sp.latex(valor),
                "linhas": [["elemento de volume", sp.sstr(raiz), sp.latex(raiz)],
                           [nome, sp.sstr(valor), sp.latex(valor)]],
                "nomeados": [{"nome": nome, "sympy": sp.sstr(valor), "latex": sp.latex(valor)}],
                "texto": "∫ √|det g| nos limites dados; o elemento sem módulo foi "
                         "conferido positivo no domínio"}

    def _serie(self, texto):
        r"""`série(eq3, \epsilon, 5)`: a série até a ordem dada, com o O(·)."""
        partes = self._argumentos(texto)
        if len(partes) != 3:
            return {"erro": "série(eq, variável, ordem)"}
        try:
            obj = self._objeto(_sem_barra(partes[0])).to_sympy()
        except (KeyError, ValueError) as e:
            return {"erro": str(e)}
        var = self.sessao.expressao_de(partes[1]).to_sympy()
        try:
            ordem = int(partes[2])
        except ValueError:
            return {"erro": "a ordem é um número inteiro"}
        alvo = obj.lhs - obj.rhs if isinstance(obj, sp.Equality) else obj
        valor = sp.series(alvo, var, 0, ordem)
        nome = self._registrar(valor.removeO())
        return {"alvo": partes[0], "exato": sp.sstr(valor), "latex_exato": sp.latex(valor),
                "nomeados": [{"nome": nome, "sympy": sp.sstr(valor.removeO()),
                              "latex": sp.latex(valor.removeO())}]}

    def _assinatura(self, nome, texto):
        """`g = métrica(-,+,+,+)` — a assinatura, e não as componentes.

        Com os sinais escritos, porque "lorentziana" não diz qual: há
        (−,+,+,+) e (+,−,−,−), e os livros se dividem. Riemanniana e
        euclidiana dizem: todos +. Devolve None se o texto são componentes.
        """
        limpo = _sem_barra(nome)
        fonte = fonte_metrica(nome, texto)
        pedacos = [p.strip() for p in texto.split(",")]
        constante = False
        if len(pedacos) > 1 and pedacos[-1].lower() in ("constante", "constant"):
            constante, pedacos = True, pedacos[:-1]
        palavra = ",".join(pedacos).strip().lower()
        if palavra in ("cartesiana", "cartesian"):
            constante, palavra = True, "euclidiana"
        if palavra in ("lorentziana", "lorentzian", "minkowski"):
            return Celula(None, fonte, "declaracao", {"erro": (
                "lorentziana, mas qual? (−,+,+,+) e (+,−,−,−) são as duas "
                "em uso, e contas como εε e g(U,U) mudam de sinal entre elas. "
                "Escreva os sinais: g = métrica(-,+,+,+)")})
        if not isinstance(self.sessao.dimensao, int):
            return Celula(None, fonte, "declaracao", {"erro": (
                f"a assinatura tem um sinal por dimensão, e a dimensão é "
                f"{self.sessao.dimensao}, uma letra")})
        if palavra in ("riemanniana", "euclidiana", "riemannian", "euclidean"):
            sinais = (1,) * self.sessao.dimensao
        elif pedacos and all(p in ("+", "-", "−") for p in pedacos):
            sinais = tuple(-1 if p in ("-", "−") else 1 for p in pedacos)
        else:
            return None
        if self.sessao.indices and len(sinais) != self.sessao.dimensao:
            return Celula(None, fonte, "declaracao", {"erro": (
                f"a assinatura tem {len(sinais)} sinais, e os índices são de "
                f"um espaço de dimensão {self.sessao.dimensao}")})
        self.sessao.dimensao = len(sinais)
        self.sessao.assinatura = sinais
        self.sessao.metrica_constante = constante
        self.sessao.metrica_abstrata = limpo
        self.sessao.tensores.pop(limpo, None)
        escrita = ", ".join("−" if x < 0 else "+" for x in sinais)
        negativos = sum(1 for x in sinais if x < 0)
        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": limpo, "metrica": True,
                           "assinatura": list(sinais)}],
            "texto": (f"{nome} é a métrica do espaço, de assinatura "
                      f"({escrita}) — {negativos} sinal(is) negativo(s), e é "
                      f"isso que decide o sinal de εε" +
                      ("; e constante — carta cartesiana, ou inercial: ∂g = 0"
                       if constante else ""))})

    def _tensor(self, nome, formas, vetores, simetria=None):
        """`A = tensor(0, 2)` — o tipo do Schutz; `F = tensor(0, 2,
        antissimétrico)` — e a simetria dos slots.

        Diz o posto ANTES da primeira aparição, e diz a valência canônica. O
        uso sozinho dizia só o posto, e dizia tarde.
        """
        from .tensores import problema_de_simetria
        limpo = nome[1:] if nome.startswith("\\") else nome
        if not nome.startswith("\\") and len(nome) > 1:
            # Rm_{abcd} em LaTeX é R vezes m_{abcd}, e é assim que o parser o
            # lê: a declaração existiria e nunca seria usada, em silêncio.
            return Celula(None, f"{nome} = tensor({formas}, {vetores})",
                          "declaracao", {"erro": (
                f"em LaTeX, {nome} são {len(nome)} letras multiplicadas "
                f"({' vezes '.join(nome)}), e nunca seria lido como um tensor "
                f"só. Use uma letra ({nome[0]}) ou um comando "
                f"(\\{nome})")})
        grafia = {"antissimetrico": "antissimétrico", "simetrico": "simétrico",
                  "riemann": "riemann"}
        escrito = f"{nome} = tensor({formas}, {vetores}" + (
            f", {grafia[simetria]})" if simetria else ")")
        problema = problema_de_simetria(formas, vetores, simetria)
        if problema:
            return Celula(None, escrito, "declaracao", {"erro": problema})
        self.sessao.tensores[limpo] = (formas, vetores)
        self.sessao.simetrias.pop(limpo, None)
        if simetria:
            self.sessao.simetrias[limpo] = simetria
        nota = ""
        if simetria == "simetrico":
            nota = "; simétrico — trocar dois slots não muda nada"
        elif simetria == "antissimetrico":
            nota = ("; antissimétrico — trocar dois slots troca o sinal, e "
                    "slot repetido dá zero")
        elif simetria == "riemann":
            nota = ("; com as simetrias do Riemann — antissimétrico em cada "
                    "par, simétrico na troca dos pares. A identidade cíclica "
                    "não entra: é teorema, e pede torção nula")
        return Celula(None, escrito,
                      "declaracao",
                      {"declarado": [{"nome": limpo,
                                      "tipo": [formas, vetores],
                                      "simetria": simetria}],
                       "texto": (f"{limpo} é tensor do tipo ({formas},{vetores}): "
                                 f"recebe {_conta(formas, '1-forma', '1-formas')}"
                                 f" e {_conta(vetores, 'vetor', 'vetores')}"
                                 f" — {_indices_em(formas, 'em cima')},"
                                 f" {_indices_em(vetores, 'embaixo')}{nota}")})

    def _tem_forma(self, objeto):
        from .formas import tem_forma
        doc = self.sessao.documento()[0]
        return tem_forma(objeto, doc.tensores_com_graus())

    def _christoffel(self, nome, rotulo):
        """`\Gamma = christoffel(eq1)` — a convenção vem da definição de ∇."""
        from .christoffel import ChristoffelMalDefinido, convencao_de
        limpo = _sem_barra(nome)
        fonte = f"{nome} = christoffel({rotulo})"
        try:
            conv = convencao_de(self._objeto(rotulo).to_sympy(), limpo)
        except (KeyError, ValueError, ChristoffelMalDefinido) as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        self.sessao.christoffel = (limpo, conv)
        ordem = sorted(conv, key=conv.get)
        grego = {"cima": "ν", "derivada": "μ", "outro": "λ"}
        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": limpo, "christoffel": conv}],
            "texto": (f"{nome} são os símbolos de Christoffel de ∇, na convenção "
                      f"de {rotulo}: ∇_μ V^ν = ∂_μ V^ν + {nome}"
                      f"({', '.join(grego[k] for k in ordem)}) V^λ. expandir(eq) "
                      f"abre ∇ em ∂ e {nome}; expandir(eq, g), com Levi-Civita, "
                      f"escreve {nome} pela métrica")})

    def _ricci(self, nome, rotulo):
        """`R = ricci(eq2)` — de R_{μν} = R^ρ{}_{μρν}: que par se contrai, e
        o sinal. O escalar, sem índice, é g^{μν}R_{μν}."""
        from .ricci import RicciMalDefinido, convencao_de
        fonte = f"{nome} = ricci({rotulo})"
        limpo = _sem_barra(nome)
        if not self.sessao.riemann or self.sessao.riemann[0] != limpo:
            return Celula(None, fonte, "declaracao", {"erro": (
                f"o Ricci é uma contração do Riemann, com a mesma letra: "
                f"declare antes {nome} = riemann(eq)")})
        try:
            doc = self.sessao.documento()[0]
            conv = convencao_de(self._objeto(rotulo).to_sympy(), doc.espaco)
        except (KeyError, ValueError) as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        self.sessao.ricci = conv
        # R sem índice é o escalar: R(…) é produto, e não função.
        self.sessao.anotar("juxtaposition", nome, {}, "product")
        slots = ["·"] * 4
        slots[conv["mu"]], slots[conv["nu"]] = "μ", "ν"
        slots[conv["par"][0]], slots[conv["par"][1]] = "ρ", "ρ"
        sinal = "" if conv["sinal"] > 0 else "−"
        escalar = (f"; e {nome}, sem índice, é g^{{μν}}{nome}_{{μν}}"
                   if self.sessao.metrica_abstrata else
                   f"; {nome} sem índice, o escalar, pede a métrica declarada")
        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": limpo, "ricci": conv}],
            "texto": (f"{nome}_{{μν}} = {sinal}{nome}({', '.join(slots)}), "
                      f"contraído como em {rotulo}" + escalar +
                      ". Ao simplificar, os dois viram contrações do Riemann, "
                      "e voltam")})

    def _riemann(self, nome, rotulo):
        """`R = riemann(eq1)` — a convenção vem da definição escrita.

        O sinal e a ordem dos índices do Riemann variam de livro para livro; em
        vez de escolher um, o Sucuri lê a identidade que você escreveu e usa a
        convenção dela.
        """
        from .derivadas import convencao_de
        limpo = _sem_barra(nome)
        fonte = f"{nome} = riemann({rotulo})"
        if self.sessao.conexao != "levi-civita":
            return Celula(None, fonte, "declaracao", {"erro": (
                "a identidade sem termo de torção pede ∇ sem torção: declare "
                "\\nabla = levi-civita antes")})
        try:
            equacao = self._objeto(rotulo).to_sympy()
            conv = convencao_de(equacao, limpo)
        except (KeyError, ValueError) as e:
            return Celula(None, fonte, "declaracao", {"erro": str(e)})
        self.sessao.riemann = (limpo, conv)
        ordem = sorted(("rho", "sigma", "mu", "nu"), key=conv.get)
        grego = {"rho": "ρ", "sigma": "σ", "mu": "μ", "nu": "ν"}
        return Celula(None, fonte, "declaracao", {
            "declarado": [{"nome": limpo, "riemann": conv}],
            "texto": (f"{limpo} é o Riemann de ∇, na convenção de {rotulo}: "
                      f"[∇_μ, ∇_ν]V^ρ = "
                      f"{'' if conv['sinal'] == 1 else '−'}{limpo}"
                      f"({', '.join(grego[k] for k in ordem)}) V^σ. Ao "
                      f"simplificar, todo comutador ∇∇ vira curvatura")})

    def _especie(self, nomes, especie):
        r"""`e = euler`, `a = símbolo`, `\mu = índice`.

        A mesma pergunta das outras declarações — o que é este nome? — com as
        outras respostas possíveis. Vira anotação de sítio ou lista do
        documento, e não convenção cega: é uma decisão sobre AQUELES nomes.
        """
        lista = [n.strip() for n in nomes.split(",") if n.strip()]

        if especie.startswith("índice") or especie.startswith("indice"):
            import re as _re
            achou = _re.search(r"\(\s*(\d+|[A-Za-z]\w*)\s*\)", especie)
            dimensao = None
            if achou:
                # índices(d): a dimensão como letra, para as contas "em d
                # dimensões". O que pede número — ε, a assinatura — recusa.
                dimensao = (int(achou.group(1)) if achou.group(1).isdigit()
                            else sp.Symbol(achou.group(1)))
            self.sessao.indices.extend(n for n in lista
                                       if n not in self.sessao.indices)
            if dimensao and self.sessao.coordenadas and \
                    str(dimensao) != str(len(self.sessao.coordenadas)):
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
        elif especie == "hodge":
            if not self.sessao.assinatura:
                return Celula(None, f"{nomes} = {especie}", "declaracao", {
                    "erro": "⋆⋆ = (−1)^{p(n−p)+s}: o sinal pede a assinatura. "
                            "Declare antes g = métrica(-,+,+,+), ou a que for"})
            self.sessao.hodge = True
            n = len(self.sessao.assinatura)
            s = sum(1 for x in self.sessao.assinatura if x < 0)
            texto = (f"{', '.join(lista)} é o dual de Hodge, em dimensão {n} "
                     f"com {s} sinal(is) negativo(s): ⋆⋆ = (−1)^(p({n}−p)+{s}) "
                     f"numa p-forma, α∧⋆β = β∧⋆α, e a orientação não precisa "
                     f"ser dita — ela troca o sinal de ⋆, e não o de ⋆⋆")
        elif especie == "kronecker":
            if len(lista) != 1:
                return Celula(None, f"{nomes} = {especie}", "declaracao",
                              {"erro": "a delta é uma só: declare um nome"})
            self.sessao.kronecker = _sem_barra(lista[0])
            texto = (f"{lista[0]}^μ_ν é a delta de Kronecker — a identidade: "
                     f"{lista[0]}^μ_ν A^ν vira A^μ ao simplificar, e "
                     f"{lista[0]}^μ_μ vira a dimensão")
        elif especie.startswith("levi") and lista == ["\\nabla"]:
            self.sessao.conexao = "levi-civita"
            texto = ("∇ é a conexão de Levi-Civita: ∇g = 0, e sem torção — "
                     "∇_μ∇_ν φ = ∇_ν∇_μ φ num escalar. Ao simplificar, ∇g e "
                     "∇ε (tensor) viram zero")
        elif especie.startswith("levi"):
            import re as _re
            dentro = _re.search(r"\(\s*([^)]*?)\s*\)", especie)
            qual = (dentro.group(1).lower() if dentro else "")
            qual = {"tensor": "tensor", "símbolo": "simbolo",
                    "simbolo": "simbolo"}.get(qual)
            if qual is None:
                return Celula(None, f"{nomes} = {especie}", "declaracao", {
                    "erro": "levi-civita(símbolo) ou levi-civita(tensor)? Os "
                            "livros não fazem igual. O símbolo vale ±1 em "
                            "toda carta e é uma densidade: não sobe nem desce "
                            "com g. O tensor é √|g| vezes o símbolo, e sobe e "
                            "desce com g. As duas leituras dão contas "
                            "diferentes em contrair, e escolher seria "
                            "adivinhar"})
            if not isinstance(self.sessao.dimensao, int):
                return Celula(None, f"{nomes} = {especie}", "declaracao", {
                    "erro": f"ε tem um índice por dimensão, e a dimensão é "
                            f"{self.sessao.dimensao}, uma letra"})
            for n in lista:
                self.sessao.levi[_sem_barra(n)] = qual
            dim = self.sessao.dimensao
            texto = (f"{', '.join(lista)}: Levi-Civita como "
                     f"{'tensor — sobe e desce com g' if qual == 'tensor' else 'símbolo — ±1 em toda carta, não sobe nem desce com g'}"
                     f"; {dim} índices, totalmente antissimétrico")
        elif especie.startswith("det"):
            import re as _re
            de = _sem_barra(_re.search(r"\(\s*(\\?\w+)\s*\)", especie).group(1))
            if len(lista) != 1 or de != self.sessao.metrica_abstrata:
                return Celula(None, f"{nomes} = {especie}", "declaracao", {
                    "erro": "det(g) é o determinante da métrica declarada: "
                            "declare antes g = métrica, e um nome só para "
                            "o determinante"})
            self.sessao.determinante = _sem_barra(lista[0])
            self.sessao.anotar("juxtaposition", lista[0], {}, "product")
            h = lista[0]
            sinal = ""
            if self.sessao.assinatura:
                negativos = sum(1 for x in self.sessao.assinatura if x < 0)
                sinal = (f"; pela assinatura, {h} "
                         f"{'< 0' if negativos % 2 else '> 0'}, e |{h}| = "
                         f"{'−' if negativos % 2 else ''}{h}")
            texto = (f"{h}, sem índice, é det {de}_{{μν}}: ∂_λ {h} = {h} "
                     f"{de}^{{μν}} ∂_λ {de}_{{μν}} ao simplificar" + sinal)
        elif especie.startswith("coordenada"):
            if len(lista) != 1:
                return Celula(None, f"{nomes} = {especie}", "declaracao", {
                    "erro": "as coordenadas são um nome só, com índice: "
                            "x = coordenadas, e x^i é a i-ésima"})
            limpo = _sem_barra(lista[0])
            self.sessao.coordenada_indice = limpo
            self.sessao.tensores[limpo] = (1, 0)
            texto = (f"{lista[0]}^i são as coordenadas: ∂_j {lista[0]}^i = "
                     f"δ^i_j, e as derivadas segundas são zero. ∇ não se "
                     f"aplica — {lista[0]}^i não é campo vetorial")
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
            return self._geometria(verbo, alvo, segundo)
        if verbo == "expandir":
            return self._expandir(alvo, segundo)
        if verbo == "independentes":
            return self._independentes(alvo, [segundo] if segundo else [])
        if verbo == "em_componentes":
            return self._em_componentes(alvo)
        if verbo == "geodesicas":
            return self._geodesicas(alvo)
        if verbo == "orbitas":
            return self._orbitas(alvo)
        if verbo == "em_carta":
            from .em_carta import SemComponentes, avaliar
            try:
                objeto = self._objeto(alvo).to_sympy()
                expr = objeto.lhs - objeto.rhs if isinstance(objeto, sp.Equality) else objeto
                nome = self.sessao.metrica_abstrata
                metrica = self._metrica_de(nome or "")
                espaco = self.sessao.documento()[0].espaco
                comps = avaliar(expr, espaco, metrica, self.campos, self.formas_c)
            except (KeyError, SemComponentes, ValueError) as e:
                return {"erro": str(e.args[0]) if e.args else str(e), "alvo": alvo}
            eq = isinstance(objeto, sp.Equality)
            if not comps or (len(comps) == 1 and comps[0][0] == "" and comps[0][1] == 0):
                return {"alvo": alvo, "exato": "True" if eq else "0",
                        "texto": ("os dois lados coincidem, componente por componente" if eq
                                  else "todas as componentes são nulas") + f", na carta ({metrica.coordenadas})"}
            linhas = [[r or "valor", sp.sstr(v), sp.latex(v)] for r, v in comps]
            return {"alvo": alvo, "linhas": [["coordenadas", metrica.coordenadas, metrica.coordenadas]] + linhas,
                    "exato": "; ".join(f"{r}: {sp.sstr(v)}" if r else sp.sstr(v) for r, v in comps),
                    "texto": ("componentes da diferença dos lados, não nulas" if eq else
                              "componentes não nulas") + f", na carta ({metrica.coordenadas})"}
        if verbo == "cartan":
            from .cartan import SemBase, cartan, em_formas
            try:
                metrica = self._metrica_de(alvo)
                linhas = em_formas(cartan(metrica), metrica.escrita)
            except (KeyError, SemBase) as e:
                return {"erro": str(e.args[0]), "alvo": alvo}
            return {"alvo": alvo, "rotulo": f"base ortonormal de {alvo}",
                    "linhas": [list(l) for l in linhas],
                    "exato": "; ".join(f"{l[0]} = {l[1]}" for l in linhas),
                    "texto": ("tétrada e^a = √|g_aa| dx^a; ω^a_b de de^a = −ω^a_b∧e^b, "
                              "com ω_ab = −ω_ba — as duas conferidas —; Θ^a_b = "
                              "dω^a_b + ω^a_c∧ω^c_b = ½R^a_bcd e^c∧e^d")}
        if verbo == "elemento":
            from .geometria import elemento_de_linha
            try:
                metrica = self._metrica_de(alvo)
            except KeyError as e:
                return {"erro": str(e.args[0]), "alvo": alvo}
            ds2 = elemento_de_linha(metrica)
            return {"alvo": alvo, "exato": sp.sstr(ds2),
                    "latex_exato": "ds^2 = " + sp.latex(ds2),
                    "linhas": [["coordenadas", metrica.coordenadas, metrica.coordenadas],
                               ["ds²", sp.sstr(ds2), sp.latex(ds2)]]}
        if verbo == "linearizar":
            return self._expandir(alvo, None, linear=segundo)
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
            from .derivadas import latex as _latex
            return {"latex_exato": _latex(expressao.to_sympy()),
                    "exato": sp.sstr(expressao.to_sympy()), "alvo": alvo}
        if verbo == "exportar":
            return {"codigo": self.exportar(alvo), "alvo": alvo}
        if verbo == "contrair":
            return self._contrair(alvo, expressao)
        if verbo == "indices":
            return self._traduzir(alvo, expressao)
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
            objeto = expressao.to_sympy()
            if isinstance(objeto, sp.Equality) and any(
                    isinstance(l, TensExpr) for l in (objeto.lhs, objeto.rhs)):
                # Igualdade entre tensores: simplifica a diferença, e diz se
                # os dois lados coincidem.
                from .tensores import simplificar as _simplificar
                espaco = self.sessao.documento()[0].espaco
                # Cada lado primeiro, e depois a diferença do que sobrou:
                # simplificar a diferença crua misturava os termos dos dois
                # lados antes de cada um ter a sua forma, e identidades que
                # fechavam lado a lado não fechavam juntas.
                try:
                    lhs = _simplificar(objeto.lhs, espaco)
                    rhs = _simplificar(objeto.rhs, espaco)
                    diferenca = _simplificar(lhs - rhs, espaco)
                except ValueError as e:
                    return {"erro": str(e), "alvo": alvo}
                objeto = sp.true if diferenca == 0 else sp.Eq(
                    lhs, rhs, evaluate=False)
            elif isinstance(objeto, TensExpr):
                # O simplify do SymPy não usa a simetria de um tensor; a
                # canonicalização de Butler-Portugal usa — F_{μν} + F_{νμ}
                # só vira 0 por ela. E a delta declarada é contraída antes.
                from .tensores import simplificar as _simplificar
                try:
                    objeto = _simplificar(objeto, self.sessao.documento()[0].espaco)
                except ValueError as e:
                    return {"erro": str(e), "alvo": alvo}
            elif self._tem_forma(objeto):
                from .formas import expressao, normal
                doc = self.sessao.documento()[0]
                objeto = expressao(normal(objeto, doc.tensores_com_graus()))
            else:
                objeto = sp.simplify(objeto)
            return {"alvo": alvo, "exato": sp.sstr(objeto),
                    "latex_exato": _latex_de(objeto),
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

        if _tem_indice(objetivo):
            return self._provar_indices(alvo, objetivo, dadas)

        from .formas import com_graus
        try:
            doc = self.sessao.documento()[0]
            prova = provar(objetivo, dadas, com_graus(
                self.sessao.tensores, doc.graus(), doc.hodge_info()))
        except (SemProva, NaoEVetorial) as e:
            return {"erro": str(e), "alvo": alvo}

        tabela = linhas(prova)
        usadas = ", ".join(prova.hipoteses_usadas) or "nenhuma hipótese"
        sobrou = [h for h in hipoteses if h not in prova.hipoteses_usadas]
        nota = f"; não precisou de {', '.join(sobrou)}" if sobrou else ""
        tabela.append(["somando", sp.sstr(objetivo),
                       sp.latex(objetivo) + r"\quad\blacksquare"])
        texto = (f"provado a partir de {usadas}, e do que vale para "
                 f"qualquer conexão e métrica — linearidade, Leibniz, "
                 f"simetria de g{nota}")
        tabela.append(["usou", texto])
        return {"alvo": alvo, "latex_exato": sp.latex(objetivo),
                "exato": sp.sstr(objetivo), "linhas": tabela, "texto": texto}

    def _em_componentes(self, alvo):
        """`em_componentes(eq)`: a identidade vale para o tensor mais geral
        de cada tipo declarado, e para qualquer métrica, na dimensão dada?"""
        from .contagem import SemContagem, em_componentes
        espaco = self.sessao.documento()[0].espaco
        try:
            e = self._objeto(alvo).to_sympy()
            expr = e.lhs - e.rhs if isinstance(e, sp.Equality) else e
            vale = em_componentes(expr, espaco)
        except (KeyError, ValueError) as err:
            return {"erro": str(err), "alvo": alvo}
        n = espaco.dimensao
        texto = (f"em dimensão {n}, com a métrica e cada tensor os mais gerais "
                 f"que as declarações permitem" +
                 (" (o Riemann com a primeira identidade de Bianchi)"
                  if espaco.riemann and espaco.conexao == "levi-civita" else "") +
                 (": vale, componente por componente" if vale else
                  ": não vale — há um tensor e uma métrica em que falha"))
        return {"alvo": alvo, "exato": str(vale), "latex_exato": str(vale),
                "texto": texto}

    def _independentes(self, nome, rotulos):
        """`independentes(T, eq…)`: quantas componentes de T sobram, com as
        simetrias declaradas e as equações dadas, na dimensão declarada."""
        from .contagem import SemContagem, contar
        espaco = self.sessao.documento()[0].espaco
        try:
            eqs = []
            for r in rotulos:
                e = self._objeto(r).to_sympy()
                eqs.append(e.lhs - e.rhs if isinstance(e, sp.Equality) else e)
            if espaco is None:
                raise SemContagem("declare os índices, com a dimensão")
            k, total, simetrias, notas = contar(nome, eqs, espaco)
        except (KeyError, ValueError) as e:
            return {"erro": str(e), "alvo": nome}
        n = espaco.dimensao
        texto = (f"em dimensão {n}: {total} componentes; as simetrias de {nome} "
                 f"deixam {simetrias}")
        if rotulos or notas:
            texto += ("; com " + ", ".join(list(rotulos) + notas) + f", {k}")
        texto += (". Nenhuma: só o tensor nulo tem essas propriedades" if k == 0
                  else "")
        return {"alvo": nome, "exato": str(k), "latex_exato": str(k),
                "texto": texto}

    def _provar_indices(self, alvo, objetivo, dadas):
        """provar com índice: o objetivo como combinação das hipóteses, de
        seus ∇, e do que a forma canônica e a torção nula já sabem."""
        from .prova_indices import SemProvaIndices, linhas, provar
        from .tensores import latex_de, simplificar as _simplificar
        espaco = self.sessao.documento()[0].espaco

        def diferenca(e):
            return e.lhs - e.rhs if isinstance(e, sp.Equality) else e

        nao = [h for h, e in dadas.items() if not _tem_indice(e)]
        if nao:
            return {"erro": f"{', '.join(nao)} não tem índice, e o objetivo "
                            f"tem: as duas notações não se misturam numa "
                            f"prova — traduza com indices(eq)", "alvo": alvo}
        try:
            prova = provar(diferenca(objetivo),
                           {h: diferenca(e) for h, e in dadas.items()},
                           espaco, lambda e: _simplificar(e, espaco))
        except SemProvaIndices as e:
            return {"erro": str(e), "alvo": alvo}
        tabela = linhas(prova, lambda e: latex_de(e, espaco))
        usadas = [h for h in dadas if h in prova.hipoteses_usadas]
        teoremas = [h for h in prova.hipoteses_usadas if h not in dadas]
        sobrou = [h for h in dadas if h not in usadas]
        texto = ("provado a partir de " + (", ".join(usadas) or "nenhuma hipótese")
                 + (f", e de {', '.join(teoremas)} (teorema, da torção nula)"
                    if teoremas else "")
                 + " — com ∇ delas, trocas de índice e produtos; e do que a "
                   "forma canônica sabe: simetrias declaradas, [∇,∇] como "
                   "curvatura, ∇g = 0"
                 + (f"; não precisou de {', '.join(sobrou)}" if sobrou else "")
                 + ("; vale se " + ", ".join(f"{sp.sstr(c)} ≠ 0" for c in prova.condicoes)
                    + " — a combinação divide por isso" if prova.condicoes else ""))
        tabela.append(["somando", sp.sstr(objetivo),
                       latex_de(objetivo, espaco) + r"\quad\blacksquare"])
        tabela.append(["usou", texto])
        return {"alvo": alvo, "latex_exato": latex_de(objetivo, espaco),
                "exato": sp.sstr(objetivo), "linhas": tabela, "texto": texto}

    def _expandir(self, alvo, metrica=None, linear=None):
        """`expandir(eq)`: ∇ em ∂ e Γ; `expandir(eq, g)`: e Γ pela métrica.

        Uma igualdade sai `True` quando, expandida e simplificada, os dois
        lados coincidem — é assim que a fórmula de um livro se confere.
        """
        from .christoffel import ChristoffelMalDefinido, expandir, metrizar
        from .tensores import latex_de, simplificar as _simplificar
        try:
            objeto = self._objeto(alvo).to_sympy()
        except (KeyError, ValueError) as e:
            return {"erro": str(e), "alvo": alvo}
        doc = self.sessao.documento()[0]
        espaco = doc.espaco
        try:
            if espaco.christoffel or not linear:
                objeto = expandir(objeto, espaco)
            if linear:
                # linearizar(eq, h): g = η + εh — e Γ, se houver, pela métrica.
                from .christoffel import linearizar
                if _sem_barra(linear) not in self.sessao.tensores:
                    return {"erro": f"declare {linear} = tensor(0, 2, simétrico): "
                                    f"é a perturbação da métrica", "alvo": alvo}
                if espaco.christoffel:
                    objeto = metrizar(objeto, espaco)
                objeto = linearizar(objeto, espaco, _sem_barra(linear))
                # Daqui em diante g é o fundo η: constante. O espaço é
                # remontado a cada comando, e isto não vaza para o próximo.
                espaco.metrica_constante = True
            elif metrica:
                if _sem_barra(metrica) != espaco.metrica:
                    return {"erro": f"'{metrica}' não é a métrica declarada",
                            "alvo": alvo}
                objeto = metrizar(objeto, espaco)
        except (ChristoffelMalDefinido, ValueError) as e:
            return {"erro": str(e), "alvo": alvo}
        if isinstance(objeto, sp.Equality):
            lhs = _simplificar(objeto.lhs, espaco)
            rhs = _simplificar(objeto.rhs, espaco)
            resto = _simplificar(lhs - rhs, espaco) if isinstance(
                lhs - rhs, TensExpr) else sp.simplify(lhs - rhs)
            objeto = sp.true if resto == 0 else sp.Eq(lhs, rhs, evaluate=False)
        else:
            objeto = _simplificar(objeto, espaco)
        nome = self._registrar(objeto)
        latex = latex_de(objeto, espaco)
        return {"alvo": alvo, "exato": sp.sstr(objeto), "latex_exato": latex,
                "nomeados": [{"nome": nome, "sympy": sp.sstr(objeto),
                              "latex": latex}]}

    def _traduzir(self, alvo, expressao):
        """`indices(eq5)` — a mesma igualdade, escrita com índice."""
        from .tensores import latex_de
        from .traducao import SemTraducao, traduzir
        doc = self.sessao.documento()[0]
        if not self.sessao.indices:
            return {"erro": "declare os índices antes (\\mu, \\nu, … = "
                            "índices): é com eles que a tradução se escreve",
                    "alvo": alvo}
        espaco = doc.espaco
        primeiro = _sem_barra(self.sessao.indices[0])
        try:
            # Sem canonicalizar: com a métrica, a forma canônica sobe e desce
            # os mudos, e R^μ{}_{σαβ}U^σ sairia R^{μαβσ}U_σ — igual, e
            # ilegível. A tradução fica como foi montada.
            resultado, notas = traduzir(expressao.to_sympy(), espaco,
                                        doc.tensores_com_graus(),
                                        espaco.indice(primeiro))
        except (SemTraducao, ValueError) as e:
            return {"erro": str(e), "alvo": alvo}
        mudos = [_sem_barra(n) for n in self.sessao.indices[1:]]
        nome = self._registrar(resultado)
        latex = latex_de(resultado, espaco, mudos)
        return {"alvo": alvo, "exato": sp.sstr(resultado), "latex_exato": latex,
                "texto": "; ".join(notas) if notas else None,
                "notas": notas,
                "nomeados": [{"nome": nome, "sympy": sp.sstr(resultado),
                              "latex": latex}]}

    def _contrair(self, alvo, expressao):
        r"""`g_{\mu\nu}A^\nu` vira `A_\mu`: baixar o índice, de fato.

        Não é simplificação nem cosmética — é a convenção da métrica aplicada,
        e por isso exige que alguém tenha dito qual é a métrica.
        """
        from .tensores import contrair, latex_de, livres

        objeto = expressao.to_sympy()
        if not isinstance(objeto, TensExpr):
            return {"erro": f"'{alvo}' não é expressão tensorial: contrair "
                            f"baixa índice com a métrica, e aqui não há índice",
                    "alvo": alvo}
        espaco = expressao.document.espaco
        try:
            saida = contrair(objeto, espaco)
        except ValueError as e:                 # SemMetrica, e o símbolo ε
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
                "latex": _latex_de(objeto)}

    def _nomear(self, resultado):
        """Batiza o que a operação produziu, e devolve os nomes junto.

        Uma operação que devolve equações sem nome devolve becos: o usuário lê
        duas EDOs numa tabela e não tem como pedir a próxima conta sobre elas
        senão redigitando.
        """
        saida = resultado.to_dict()
        saida["nomeados"] = [self._nome_de(o) for o in resultado.produz]
        return saida

    def _geometria(self, verbo, alvo, linear=None):
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
        if linear:
            # `ricci(g, \Phi)`: em primeira ordem em Φ — Φ → εΦ, a conta, a
            # série em ε até a ordem 1, e ε = 1.
            eps = sp.Symbol("varepsilon_ordem")
            alvo_f = [f for f in metrica.matriz().atoms(sp.Function) if f.func.__name__ == linear]
            simbolo = sp.Symbol(linear)
            if not alvo_f and simbolo not in metrica.matriz().free_symbols:
                return {"erro": f"'{linear}' não aparece nas componentes de {alvo}"}
            troca = {f: eps * f for f in alvo_f}
            if simbolo in metrica.matriz().free_symbols:
                troca[simbolo] = eps * simbolo
            G = metrica.matriz().xreplace(troca)
            perturbada = geometria.Metrica(metrica.nome, metrica.simbolos, G, metrica.escrita)
            bruto = calculo(perturbada)
            def corta(v):
                return sp.simplify(sp.series(v, eps, 0, 2).removeO().subs(eps, 1))
            if verbo == "escalar":
                resultado = corta(bruto)
            else:
                lista, todas = bruto
                todas = {k: corta(v) for k, v in todas.items()}
                resultado = ([(k, v) for k, v in todas.items() if v != 0], todas)
        else:
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
