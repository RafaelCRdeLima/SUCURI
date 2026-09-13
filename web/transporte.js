/* Transporte online: postMessage para o motor no Web Worker.
 *
 * Faz três coisas que o transporte local não precisa fazer: mostrar o
 * carregamento (o Python leva alguns segundos para chegar), impor prazo, e
 * reerguer o motor quando o prazo estoura — porque matar o worker é a única
 * forma de interromper um `dsolve` que não volta.
 */
'use strict';

var PRAZO_PADRAO = 25000;
var PRAZO_MODULO = 60000;

var motor = null;
var pendentes = {};
var proximo = 0;
var pronto = null;

/* Prefixo no nome porque estas variáveis dividem o espaço global com o
 * `sucuri.js`, que tem uma FUNÇÃO chamada `convencoes`. Guardar o estado numa
 * variável de mesmo nome sobrescrevia a função na primeira leitura: a página
 * pintava o primeiro resultado e nenhum outro, calada. */
var memConvencoes = null;   // reenviadas ao motor novo
var memAnotacoes = [];

function erguer() {
  motor = new Worker('motor.js');
  pronto = new Promise(function (resolve, reject) {
    motor.onmessage = function (e) {
      var d = e.data;
      if (d.tipo === 'carregando') { SUCURI_CARREGANDO(d); return; }
      if (d.tipo === 'pronto') { SUCURI_CARREGADO(d.versoes); resolve(); return; }
      if (d.tipo === 'falha') { SUCURI_FALHOU(d.erro); reject(d.erro); return; }
      var p = pendentes[d.id];
      if (!p) { return; }
      delete pendentes[d.id];
      clearTimeout(p.relogio);
      if (d.ok) { p.resolve(d.dados); } else { p.reject(new Error(d.erro)); }
    };
  });
}

function reerguer() {
  motor.terminate();
  Object.keys(pendentes).forEach(function (id) {
    clearTimeout(pendentes[id].relogio);
    pendentes[id].reject(new Error('o motor foi reiniciado'));
  });
  pendentes = {};
  erguer();
  // Devolve ao motor novo o que o usuário já tinha decidido.
  pronto.then(function () {
      memAnotacoes.forEach(function (a) { enviar('/api/anotar', a, PRAZO_PADRAO); });
  });
}

function enviar(rota, corpo, prazo) {
  var id = ++proximo;
  return new Promise(function (resolve, reject) {
    pendentes[id] = {
      resolve: resolve, reject: reject,
      relogio: setTimeout(function () {
        delete pendentes[id];
        reerguer();
        reject(new Error('não terminou em ' + Math.round(prazo / 1000) + ' s'));
      }, prazo)
    };
    motor.postMessage({ id: id, rota: rota, corpo: corpo });
  });
}

function SUCURI_TRANSPORTE(rota, corpo) {
  if (corpo.convencoes) { memConvencoes = corpo.convencoes; }
  if (rota === '/api/anotar' && corpo.leitura !== null) { memAnotacoes.push(corpo); }
  var prazo = (rota === '/api/operar') ? PRAZO_MODULO : PRAZO_PADRAO;
  return pronto.then(function () { return enviar(rota, corpo, prazo); });
}

erguer();
