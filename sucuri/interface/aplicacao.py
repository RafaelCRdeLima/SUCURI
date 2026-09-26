"""As rotas, sem transporte nenhum.

O que a interface pede e o que o motor responde — em dicionários, não em HTTP.
Fica separado do servidor porque há dois hospedeiros: o servidor local, que
fala HTTP, e o navegador com Pyodide, que fala postMessage. Os dois chamam
exatamente estas funções, e é por isso que a versão online não é uma segunda
implementação do programa.
"""

from __future__ import annotations

import threading

from .sessao import Sessao


class Aplicacao:
    """As sessões abertas e o que se pode fazer com elas."""

    def __init__(self):
        self.sessoes = {}
        self.cadernos = {}
        self.trava = threading.Lock()

    def sessao(self, ident):
        with self.trava:
            return self.sessoes.setdefault(ident or "local", Sessao())

    def caderno(self, ident, novo=False):
        with self.trava:
            chave = ident or "local"
            if novo or chave not in self.cadernos:
                # Importado aqui, e não no topo: o caderno usa a Sessao, que
                # mora sob `interface`, e o ciclo fecharia na carga.
                from ..caderno import Caderno
                self.cadernos[chave] = Caderno()
            return self.cadernos[chave]

    # ------------------------------------------------------------- rotas

    def ler(self, corpo):
        s = self.sessao(corpo.get("sessao"))
        if "convencoes" in corpo:
            s.configurar(corpo["convencoes"])
        return s.ler(corpo.get("latex"))

    def anotar(self, corpo):
        s = self.sessao(corpo.get("sessao"))
        if corpo.get("leitura") is None:
            s.esquecer(corpo["kind"], corpo["base"], corpo.get("detalhe"))
        else:
            s.anotar(corpo["kind"], corpo["base"],
                     corpo.get("detalhe"), corpo["leitura"])
        return s.ler(corpo.get("latex"))

    def avaliar(self, corpo):
        s = self.sessao(corpo.get("sessao"))
        if "convencoes" in corpo:
            s.configurar(corpo["convencoes"])
        return s.avaliar(corpo.get("latex"))

    # ------------------------------------------------------------ caderno

    def executar(self, corpo):
        """Uma célula nova, sob as convenções e decisões que já valem."""
        c = self.caderno(corpo.get("sessao"))
        if "convencoes" in corpo:
            c.configurar(corpo["convencoes"])
        # As anotações vão em toda chamada, e não só no refazer: depois de
        # reiniciar o motor, a próxima célula precisa das decisões de volta —
        # decisão do usuário é fonte, não estado acumulado.
        for a in corpo.get("anotacoes") or []:
            c.anotar(a["kind"], a["base"], a.get("detalhe"), a["leitura"])
        return c.executar(corpo.get("fonte", "")).to_dict()

    def reiniciar(self, corpo):
        """Joga fora o que foi acumulado — nomes, declarações, contador.

        O que está ESCRITO não é problema desta rota: fica no navegador, e
        continua lá. Some o que o motor guardou por ter executado, que é o que
        faz eq1 existir. É o "reiniciar o kernel" de sempre, e a distinção
        entre as duas coisas é a razão de ele existir.
        """
        self.caderno(corpo.get("sessao"), novo=True)
        return {"reiniciado": True}

    def refazer(self, corpo):
        """Tudo de novo, na ordem.

        Mudar uma convenção muda o SIGNIFICADO do que já está escrito, e
        deixar células velhas na tela com a leitura antiga seria mostrar duas
        matemáticas diferentes ao mesmo tempo. Um caderno se refaz.
        """
        c = self.caderno(corpo.get("sessao"), novo=True)
        c.configurar(corpo.get("convencoes") or {})
        for a in corpo.get("anotacoes") or []:
            c.anotar(a["kind"], a["base"], a.get("detalhe"), a["leitura"])
        return {"celulas": [c.executar(f).to_dict()
                            for f in corpo.get("fontes") or []]}

    def anotar_caderno(self, corpo):
        """Decidir um sítio vale para o caderno inteiro, e refaz tudo."""
        return self.refazer(corpo)

    def modulos(self, corpo):
        from .. import modules

        nomes = corpo.get("nomes") or list(modules.CONHECIDOS)
        saida = []
        for nome in nomes:
            try:
                m = modules.load(nome)
            except Exception as e:                      # noqa: BLE001
                saida.append({"nome": nome, "disponivel": False,
                              "motivo": f"{type(e).__name__}: {e}"})
                continue
            saida.append({
                "nome": m.name,
                "descricao": m.description,
                "disponivel": True,
                "operacoes": [{"nome": op.name, "descricao": op.description}
                              for op in m.operations.values()],
            })
        return {"modulos": saida}

    def operar(self, corpo):
        from .. import modules

        s = self.sessao(corpo.get("sessao"))
        if corpo.get("latex") is not None:
            s.latex = corpo["latex"]
        modulo = modules.load(corpo["modulo"])
        operacao = modulo.operations.get(corpo["operacao"])
        if operacao is None:
            raise KeyError(f"operação desconhecida: {corpo['operacao']}")

        expressao = s.expressao()
        if expressao.pending:
            return {"erro": "há sítios pendentes; resolva antes de operar",
                    "pendentes": expressao.questions()}
        resultado = operacao.run(expressao)
        saida = resultado.to_dict()
        saida["modulo"] = modulo.name
        saida["operacao"] = operacao.name
        return saida

    ROTAS = {"/api/ler": ler, "/api/anotar": anotar, "/api/avaliar": avaliar,
             "/api/modulos": modulos, "/api/operar": operar,
             "/api/caderno/executar": executar,
             "/api/caderno/refazer": refazer,
             "/api/caderno/reiniciar": reiniciar}


def _no_idioma(rota):
    """A resposta no idioma que a interface pediu: `"idioma": "en"` no corpo.
    O motor responde em português; a tradução é a última coisa que acontece."""
    def atender(app, corpo):
        from ..idioma import traduzir_resposta
        return traduzir_resposta(rota(app, corpo), (corpo or {}).get("idioma", "pt"))
    atender.__name__ = rota.__name__
    return atender


Aplicacao.ROTAS = {k: _no_idioma(f) for k, f in Aplicacao.ROTAS.items()}
