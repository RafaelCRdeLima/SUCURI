/* Transporte local: HTTP para o servidor que serve esta página. */
'use strict';

function SUCURI_TRANSPORTE(rota, corpo) {
  return fetch(rota, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(corpo)
  }).then(function (r) { return r.json(); });
}
