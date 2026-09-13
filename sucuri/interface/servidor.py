"""O servidor local.

Escolha de arquitetura: HTTP na máquina do usuário, página no navegador. O
programa é de Linux hoje e fica online amanhã sem reescrita — o mesmo motor,
a mesma página, outro endereço. Um aplicativo de área de trabalho em Qt ou GTK
teria de ser refeito por inteiro para essa segunda vida.

Só biblioteca padrão: quem instalar o Sucuri já tem o SymPy para instalar;
não deve precisar de um servidor web por cima.
"""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .aplicacao import Aplicacao

ESTATICO = Path(__file__).parent / "estatico"

mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")


class Manipulador(BaseHTTPRequestHandler):
    server_version = "Sucuri"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, aplicacao=None, **kwargs):
        self.aplicacao = aplicacao
        super().__init__(*args, **kwargs)

    def log_message(self, formato, *args):          # silêncio no terminal
        pass

    # -------------------------------------------------------------- GET

    def do_GET(self):
        caminho = self.path.split("?", 1)[0]
        if caminho == "/":
            caminho = "/index.html"
        alvo = (ESTATICO / caminho.lstrip("/")).resolve()
        if not str(alvo).startswith(str(ESTATICO.resolve())) or not alvo.is_file():
            return self._erro(404, "não encontrado")
        tipo = mimetypes.guess_type(alvo.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo.endswith("javascript"):
            tipo += "; charset=utf-8"
        self._responder(200, alvo.read_bytes(), tipo)

    # ------------------------------------------------------------- POST

    def do_POST(self):
        caminho = self.path.split("?", 1)[0]
        rota = Aplicacao.ROTAS.get(caminho)
        if rota is None:
            return self._erro(404, "rota desconhecida")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            corpo = json.loads(self.rfile.read(n) or b"{}")
            resposta = rota(self.aplicacao, corpo)
        except Exception as e:                          # noqa: BLE001
            return self._erro(400, f"{type(e).__name__}: {e}")
        bruto = json.dumps(resposta, ensure_ascii=False).encode("utf-8")
        self._responder(200, bruto, "application/json; charset=utf-8")

    # ------------------------------------------------------------ saída

    def _responder(self, codigo, corpo, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, codigo, mensagem):
        corpo = json.dumps({"erro": mensagem}, ensure_ascii=False).encode("utf-8")
        self._responder(codigo, corpo, "application/json; charset=utf-8")


def _aquecer():
    """Carrega o ANTLR antes do usuário digitar.

    A primeira chamada a `parse_latex` monta o parser gerado e custa mais de um
    segundo; as seguintes custam milissegundos. Pagar isso na partida é a
    diferença entre uma interface que responde enquanto se escreve e uma que
    trava na primeira tecla.
    """
    try:
        from sympy.parsing.latex import parse_latex
        parse_latex("x")
    except Exception:                                   # noqa: BLE001
        pass


def criar(host="127.0.0.1", porta=8765):
    """O servidor, pronto mas parado — é o que os testes usam."""
    threading.Thread(target=_aquecer, daemon=True).start()
    aplicacao = Aplicacao()
    servidor = ThreadingHTTPServer(
        (host, porta), partial(Manipulador, aplicacao=aplicacao))
    servidor.aplicacao = aplicacao
    return servidor


def servir(host="127.0.0.1", porta=8765, abrir=True):
    servidor = criar(host, porta)
    endereco = f"http://{host}:{servidor.server_address[1]}/"
    print(f"Sucuri em {endereco}")
    print("Ctrl-C para encerrar.")
    if abrir:
        threading.Timer(0.5, webbrowser.open, [endereco]).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nencerrado.")
    finally:
        servidor.server_close()
