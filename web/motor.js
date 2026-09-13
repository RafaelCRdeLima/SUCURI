/* O motor, dentro de um Web Worker.
 *
 * Aqui roda o Sucuri de verdade — o mesmo Python, o mesmo SymPy — compilado
 * para WebAssembly pelo Pyodide. Não é uma segunda implementação em JavaScript:
 * é o pacote `sucuri` importado e a classe `Aplicacao` chamada rota por rota,
 * exatamente como o servidor local faz.
 *
 * Worker e não thread principal por dois motivos. A página continua respondendo
 * enquanto o motor pensa; e, quando o `dsolve` não volta — em y'' = 6y² ele não
 * volta —, quem hospeda mata o worker. É o papel que o subprocesso faz na
 * versão de mesa.
 */
'use strict';

importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js');

var pyodide = null;
var atender = null;

async function desempacotar(caminho) {
  const resposta = await fetch(caminho);
  if (!resposta.ok) {
    throw new Error('não achei ' + caminho + ' (' + resposta.status + ')');
  }
  pyodide.unpackArchive(await resposta.arrayBuffer(), 'zip');
}

function aviso(texto, etapa, total) {
  postMessage({ tipo: 'carregando', texto: texto, etapa: etapa, total: total });
}

async function iniciar() {
  aviso('baixando o Python', 1, 5);
  pyodide = await loadPyodide({
    indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/',
  });

  aviso('carregando o SymPy', 2, 5);
  await pyodide.loadPackage(['sympy']);

  aviso('carregando o leitor de LaTeX', 3, 5);
  // A roda do ANTLR entra como zip, e não pelo micropip: micropip trata
  // caminho relativo como arquivo do sistema, e uma roda É um zip — o pacote
  // vai direto para o diretório de trabalho, que já está no sys.path.
  await desempacotar('vendor/antlr4_python3_runtime-4.11.1-py3-none-any.whl');

  aviso('abrindo o Sucuri', 4, 5);
  await desempacotar('sucuri-motor.zip');

  atender = pyodide.runPython(`
import json
from sucuri.interface.aplicacao import Aplicacao

_app = Aplicacao()

def _atender(rota, corpo_json):
    corpo = json.loads(corpo_json)
    rota_f = Aplicacao.ROTAS.get(rota)
    if rota_f is None:
        raise KeyError("rota desconhecida: " + rota)
    return json.dumps(rota_f(_app, corpo), ensure_ascii=False)

_atender
`);

  aviso('aquecendo o leitor', 5, 5);
  // A primeira leitura monta o parser do ANTLR e custa caro; pagar aqui é a
  // diferença entre uma interface que responde enquanto se escreve e uma que
  // trava na primeira tecla.
  atender('/api/ler', JSON.stringify({ latex: 'x', sessao: 'aquecimento' }));

  postMessage({ tipo: 'pronto', versoes: pyodide.runPython(
    'import sympy, sucuri; sympy.__version__ + "|" + sucuri.__version__') });
}

const inicializacao = iniciar().catch(function (e) {
  postMessage({ tipo: 'falha', erro: String(e) });
});

onmessage = async function (evento) {
  const { id, rota, corpo } = evento.data;
  await inicializacao;
  try {
    const resposta = atender(rota, JSON.stringify(corpo));
    postMessage({ id: id, ok: true, dados: JSON.parse(resposta) });
  } catch (e) {
    postMessage({ id: id, ok: false, erro: String(e) });
  }
};
