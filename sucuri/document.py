"""O documento: declarações, anotações e a recusa de adivinhar.

Um `Document` guarda as convenções em vigor — qual é a variável independente,
quais nomes são funções, se linha significa derivada — e, com elas, resolve
sozinho a maior parte dos sítios ambíguos. O que sobrar fica pendente, e a
expressão RECUSA-SE a virar SymPy enquanto houver pendência.

É esse o ponto do programa. Um parser entrega expressão errada em silêncio; o
Sucuri entrega uma pergunta.
"""

from __future__ import annotations

import sympy as sp

from .ambiguity import find


class Resolution:
    """Como um sítio ambíguo foi resolvido — e não apenas se foi.

    A distinção importa e veio da identidade visual, que reserva o âmbar para
    "ambiguidade resolvida por inferência". Uma convenção de documento pode
    acertar nove sítios e errar o décimo em silêncio: quem declarou que linha é
    derivada não olhou cada linha. Marcar esses sítios permite à interface
    pedir conferência sem bloquear o trabalho.

    Os três estados, na ordem de confiança:

      EXPLICIT  anotação feita para este sítio        (verde)
      INFERRED  convenção do documento aplicada aqui  (âmbar)
      PENDING   sem leitura definida                  (bloqueia)
    """

    EXPLICIT = "explícita"
    INFERRED = "inferida"
    PENDING = "pendente"

    def __init__(self, ambiguity, reading, how):
        self.ambiguity = ambiguity
        self.reading = reading
        self.how = how

    @property
    def needs_review(self):
        """Verdadeiro para o que foi inferido: correto até prova em contrário."""
        return self.how == Resolution.INFERRED

    def __repr__(self):
        alvo = self.reading or "—"
        return f"<{self.ambiguity.fragment!r} -> {alvo} [{self.how}]>"


class Unresolved(Exception):
    """Há sítio ambíguo sem anotação. Carrega a lista."""

    def __init__(self, pendentes):
        self.pending = list(pendentes)
        corpo = "\n".join(
            f"  {a.fragment!r}: " + " ou ".join(r.key for r in a.readings)
            for a in self.pending)
        super().__init__(
            f"{len(self.pending)} sítio(s) ambíguo(s) sem anotação:\n{corpo}\n"
            "Anote com .annotate(...) ou declare a convenção no documento.")


class Document:
    """Contexto de trabalho: convenções, símbolos e anotações."""

    def __init__(self, independent_variable=None):
        self.independent = (sp.Symbol(independent_variable)
                            if independent_variable else None)
        self._functions = set()
        self._variables = set()
        self._primes_are_derivatives = None      # None = sem convenção
        self._annotations = {}

    # ------------------------------------------------------- declarações

    def function(self, *names):
        """Declara nomes como funções: `f(x)` é aplicação."""
        self._functions.update(names)
        return self

    def variable(self, *names):
        """Declara nomes como variáveis: `f(x)` é produto."""
        self._variables.update(names)
        return self

    def primes_are_derivatives(self, yes=True, wrt=None):
        """Convenção de documento para a linha.

        Exigir a variável independente é deliberado: 'derivada' sem dizer em
        relação a quê continua sendo uma ambiguidade, só que escondida.
        """
        if yes and wrt is None and self.independent is None:
            raise ValueError(
                "para ler linha como derivada é preciso uma variável "
                "independente: passe wrt= ou crie o documento com "
                "independent_variable=")
        if wrt is not None:
            self.independent = sp.Symbol(wrt)
        self._primes_are_derivatives = bool(yes)
        return self

    def annotate(self, kind, base, reading, **detail):
        """Resolve um sítio específico, uma vez e para sempre."""
        self._annotations[(kind, base, tuple(sorted(detail.items())))] = reading
        return self

    # ------------------------------------------------------------ leitura

    def read(self, latex):
        """Lê a entrada e devolve uma Expression — resolvida ou pendente."""
        return Expression(latex, self)

    def resolve(self, amb):
        """A leitura em vigor para este sítio, ou None se pendente."""
        return self.resolution(amb).reading

    def resolution(self, amb):
        """A leitura E como se chegou a ela.

        Anotação feita para o sítio é EXPLICIT. Convenção de documento aplicada
        a ele é INFERRED — a interface a mostra em âmbar, pedindo conferência.
        """
        if amb.key in self._annotations:
            return Resolution(amb, self._annotations[amb.key], Resolution.EXPLICIT)

        inferida = None
        if amb.kind == "prime" and self._primes_are_derivatives is not None:
            inferida = "derivative" if self._primes_are_derivatives else "symbol"
        elif amb.kind == "juxtaposition":
            if amb.base in self._functions:
                inferida = "application"
            elif amb.base in self._variables:
                inferida = "product"
        elif amb.kind == "leibniz" and self._primes_are_derivatives is not False:
            inferida = "derivative"

        if inferida is None:
            return Resolution(amb, None, Resolution.PENDING)
        return Resolution(amb, inferida, Resolution.INFERRED)


class Expression:
    """Uma equação do documento: a vista em LaTeX e a semântica, juntas."""

    def __init__(self, latex, document):
        self.source = latex
        self.document = document
        self.ambiguities = find(latex)

    # ------------------------------------------------------------- estado

    @property
    def pending(self):
        """Sítios ainda sem leitura definida."""
        return [a for a in self.ambiguities if self.document.resolve(a) is None]

    @property
    def resolved(self):
        return not self.pending

    @property
    def resolutions(self):
        """Como cada sítio foi resolvido, na ordem da entrada."""
        return [self.document.resolution(a) for a in self.ambiguities]

    @property
    def inferred(self):
        """Sítios resolvidos por convenção, não por anotação do sítio.

        São os que a interface pinta de âmbar: a expressão funciona, mas a
        leitura veio de uma regra geral e ninguém olhou este caso.
        """
        return [r for r in self.resolutions if r.needs_review]

    def questions(self):
        """As perguntas que o programa faria ao usuário, em vez de adivinhar."""
        saida = []
        for a in self.pending:
            opcoes = "; ".join(f"{r.key} = {r.description}" for r in a.readings)
            saida.append(f"{a.fragment!r} — {opcoes}")
        return saida

    # ---------------------------------------------------------- conversão

    def to_sympy(self):
        """A expressão SymPy. Levanta Unresolved se houver pendência.

        A recusa é o comportamento central: nenhuma leitura é escolhida por
        omissão, porque escolher por omissão é exatamente o que produz o erro
        silencioso.
        """
        if self.pending:
            raise Unresolved(self.pending)

        texto, reposicoes, derivadas = self._normalize()
        from sympy.parsing.latex import parse_latex
        expr = parse_latex(texto)
        if reposicoes:
            expr = expr.subs(reposicoes, simultaneous=True)

        # Coerência: se um símbolo aparece derivado, ele É função da variável
        # independente, e as suas ocorrências SEM linha também. Sem isto a
        # mesma letra viraria dois objetos distintos na mesma equação — erro
        # silencioso do tipo que este programa existe para impedir.
        if derivadas:
            x = self.document.independent
            promocao = {sp.Symbol(nome): sp.Function(nome)(x) for nome in derivadas}
            expr = expr.subs(promocao, simultaneous=True)
        return expr

    def _normalize(self):
        """Reescreve a entrada em forma sem ambiguidade, guardando as trocas."""
        doc = self.document
        x = doc.independent
        texto = self.source
        reposicoes = {}
        derivadas = set()
        contador = 0

        # O marcador precisa sobreviver ao parser de LaTeX como UM símbolo.
        # Nomes alfabéticos não servem: em LaTeX, letras justapostas são
        # multiplicação, e "cadvar0" vira c*a*d*v*a*r*0. Índice subscrito
        # resolve — Z_{0} é lido como um símbolo só.
        def marcador():
            nonlocal contador
            nome = f"Z_{{{contador}}}"
            contador += 1
            # Espaços em volta: sem eles o marcador cola no macro anterior e
            # "3\\varphi" + "Z_{1}" vira o macro inexistente "\\varphiZ".
            return f" {nome} ", sp.Symbol(nome)

        # De trás para frente: preserva os deslocamentos dos sítios anteriores.
        for a in sorted(self.ambiguities, key=lambda a: -a.span[0]):
            leitura = doc.resolve(a)
            ini, fim = a.span

            if a.kind == "prime":
                ordem = a.detail["order"]
                nome, simbolo = marcador()
                if leitura == "derivative":
                    derivadas.add(a.base)
                    reposicoes[simbolo] = sp.Derivative(
                        sp.Function(a.base)(x), (x, ordem))
                else:
                    reposicoes[simbolo] = sp.Symbol(a.base + "'" * ordem)
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "leibniz":
                nome, simbolo = marcador()
                if leitura == "derivative":
                    derivadas.add(a.base)
                    v = sp.Symbol(a.detail["wrt"])
                    alvo = sp.Derivative(sp.Function(a.base)(v),
                                         (v, a.detail["order"]))
                else:
                    alvo = (sp.Symbol("d")**a.detail["order"] * sp.Symbol(a.base)
                            / sp.Symbol("d" + a.detail["wrt"])**a.detail["order"])
                reposicoes[simbolo] = alvo
                texto = texto[:ini] + nome + texto[fim:]

            elif a.kind == "juxtaposition" and leitura == "product":
                # insere a multiplicação explícita antes do parêntese
                abre = texto.find("(", ini)
                texto = texto[:abre] + r" \cdot " + texto[abre:]

        return texto, reposicoes, derivadas

    def to_latex(self):
        """Volta ao LaTeX a partir da semântica — o round-trip de conferência."""
        return sp.latex(self.to_sympy())

    def __repr__(self):
        if self.resolved:
            return f"Expression({self.source!r}) [resolvida]"
        return (f"Expression({self.source!r}) [{len(self.pending)} pendência(s)]\n"
                + "\n".join("  ? " + q for q in self.questions()))

    def _repr_latex_(self):
        return "$$" + self.source + "$$"
