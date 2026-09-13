/* SUCURI — o caderno.
 *
 * Uma célula é matemática ou é um verbo. A página não decide qual: manda a
 * fonte ao motor e mostra o que voltou. Os verbos são poucos de propósito — se
 * aqui se pudesse escrever Python, a ponte que este programa é deixaria de ser
 * obrigatória, e sobraria um Jupyter com passos a mais.
 */
'use strict';

var $ = function (id) { return document.getElementById(id); };
var SESSAO = 'caderno';
var fontes = [];            // a fonte de cada célula, na ordem
var anotacoes = [];

function pedir(rota, corpo) {
  corpo.sessao = SESSAO;
  return SUCURI_TRANSPORTE(rota, corpo);
}

function convencoes() {
  return {
    independente: $('c-independente').value,
    temporal: $('c-temporal').value,
    linhas: $('c-linhas').value,
    pontos: $('c-pontos').value,
    funcoes: $('c-funcoes').value,
    variaveis: $('c-variaveis').value
  };
}

function escapar(t) {
  return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ------------------------------------------------------------- as células */

function criarCelula(fonte, indice) {
  var div = document.createElement('div');
  div.className = 'celula';

  var cabeca = document.createElement('div');
  cabeca.className = 'celula-cabeca';
  var nome = document.createElement('span');
  nome.className = 'celula-nome';
  nome.textContent = '';
  cabeca.appendChild(nome);
  var dica = document.createElement('span');
  dica.className = 'celula-dica';
  dica.textContent = 'Shift+Enter';
  cabeca.appendChild(dica);
  div.appendChild(cabeca);

  var area = document.createElement('textarea');
  area.rows = 1;
  area.spellcheck = false;
  area.value = fonte || '';
  area.addEventListener('input', function () {
    area.style.height = 'auto';
    area.style.height = (area.scrollHeight + 2) + 'px';
    fontes[indice] = area.value;
  });
  area.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      executar(indice);
    }
  });
  div.appendChild(area);

  var saida = document.createElement('div');
  saida.className = 'saida';
  div.appendChild(saida);

  div._nome = nome;
  div._area = area;
  div._saida = saida;
  return div;
}

function acrescentar(fonte) {
  var indice = fontes.length;
  fontes.push(fonte || '');
  var celula = criarCelula(fonte, indice);
  $('folha').appendChild(celula);
  celula._area.focus();
  return celula;
}

function celulaDe(indice) {
  return $('folha').children[indice];
}

/* --------------------------------------------------------------- executar */

function executar(indice) {
  var celula = celulaDe(indice);
  fontes[indice] = celula._area.value;
  celula._saida.innerHTML = '<p class="modulo-desc">…</p>';

  var ultima = indice === fontes.length - 1;
  pedir('/api/caderno/executar',
        { fonte: fontes[indice], convencoes: convencoes() })
    .then(function (d) {
      pintar(celula, d);
      if (ultima && fontes[indice].trim()) { acrescentar(''); }
      else { celulaDe(indice + 1)._area.focus(); }
    })
    .catch(function (e) {
      celula._saida.innerHTML = '<div class="bloqueio">' + escapar(e) + '</div>';
    });
}

function refazer() {
  /* Convenção mudou: o que já está escrito passa a significar outra coisa. */
  pedir('/api/caderno/refazer', { fontes: fontes.filter(function (f) {
    return f.trim();
  }), convencoes: convencoes(), anotacoes: anotacoes })
    .then(function (d) {
      var folha = $('folha');
      folha.textContent = '';
      var vivas = fontes.filter(function (f) { return f.trim(); });
      fontes = [];
      vivas.forEach(function (f, i) {
        var c = acrescentar(f);
        if (d.celulas[i]) { pintar(c, d.celulas[i]); }
      });
      acrescentar('');
    });
}

/* ----------------------------------------------------------------- pintar */

function pintar(celula, d) {
  var saida = celula._saida;
  saida.textContent = '';
  celula.className = 'celula' + (d.tipo === 'comando' ? ' comando' : '');
  celula._nome.textContent = d.nome || '';
  if (d.ms !== undefined) { $('tempo').textContent = d.ms + ' ms'; }

  if (d.erro || (d.pendentes && d.pendentes.length)) {
    celula.className += ' erro';
    if (d.erro) {
      saida.innerHTML = '<div class="bloqueio">' + escapar(d.erro) + '</div>';
    }
  }
  (d.avisos || []).forEach(function (a) {
    var p = document.createElement('div');
    p.className = 'bloqueio';
    p.textContent = a;
    saida.appendChild(p);
  });

  if (d.tipo === 'math') { pintarMath(saida, d); } else { pintarComando(saida, d); }
}

function pintarMath(saida, d) {
  (d.ambiguidades || []).forEach(function (a) { saida.appendChild(sitio(a)); });
  if (d.latex_semantico) {
    saida.appendChild(livro(d.latex_semantico));
    saida.appendChild(rodape([
      ['Copiar LaTeX', d.latex_semantico],
      ['Copiar código', d.codigo]
    ]));
  }
}

function pintarComando(saida, d) {
  if (d.codigo && !d.latex_exato) {          // exportar
    var pre = document.createElement('pre');
    pre.textContent = d.codigo;
    saida.appendChild(pre);
    saida.appendChild(rodape([['Copiar código', d.codigo]]));
    return;
  }
  var escrito = d.latex_exato || d.latex;
  if (escrito) { saida.appendChild(livro(escrito)); }
  if (d.numerico) {
    var n = document.createElement('p');
    n.className = 'modulo-desc';
    n.textContent = '≈ ' + d.numerico + '  (aproximação; o valor é o de cima)';
    saida.appendChild(n);
  }
  if ((d.linhas || []).length) {
    var t = document.createElement('table');
    d.linhas.forEach(function (linha) {
      var tr = document.createElement('tr');
      linha.forEach(function (c) {
        var td = document.createElement('td');
        td.textContent = c;
        tr.appendChild(td);
      });
      t.appendChild(tr);
    });
    var caixa = document.createElement('div');
    caixa.className = 'resultado';
    caixa.appendChild(t);
    saida.appendChild(caixa);
  }
  (d.bloqueado_por || []).forEach(function (b) {
    var p = document.createElement('div');
    p.className = 'bloqueio';
    p.textContent = b;
    saida.appendChild(p);
  });
  if (d.apresentavel === false) {
    var aviso = document.createElement('div');
    aviso.className = 'nao-apresentavel';
    aviso.textContent = 'proveniência: ' + d.proveniencia
      + ' — não apresentável como conclusão';
    saida.appendChild(aviso);
  }
  if (escrito) { saida.appendChild(rodape([['Copiar LaTeX', escrito]])); }
}

function livro(latex) {
  var div = document.createElement('div');
  div.className = 'livro';
  try { katex.render(latex, div, { displayMode: true, throwOnError: false }); }
  catch (e) { div.textContent = latex; }
  return div;
}

function rodape(botoes) {
  var div = document.createElement('div');
  div.className = 'rodape';
  botoes.forEach(function (par) {
    if (!par[1]) { return; }
    var b = document.createElement('button');
    b.textContent = par[0];
    b.addEventListener('click', function () {
      navigator.clipboard.writeText(par[1]).then(function () {
        var antes = b.textContent;
        b.textContent = 'copiado';
        setTimeout(function () { b.textContent = antes; }, 1400);
      });
    });
    div.appendChild(b);
  });
  return div;
}

/* ------------------------------------------------------ sítios ambíguos */

function sitio(a) {
  var div = document.createElement('div');
  div.className = 'sitio ' + a.estado;
  var cabeca = document.createElement('div');
  cabeca.className = 'sitio-cabeca';
  var frag = document.createElement('span');
  frag.className = 'fragmento';
  frag.textContent = a.fragmento;
  cabeca.appendChild(frag);
  var nota = document.createElement('span');
  nota.className = 'sitio-nota';
  nota.textContent = a.estado === 'pendente' ? 'o Sucuri não escolhe por você'
                   : a.estado === 'inferida' ? 'veio da convenção — confira'
                   : 'decidido aqui';
  cabeca.appendChild(nota);
  div.appendChild(cabeca);

  var opcoes = document.createElement('div');
  opcoes.className = 'opcoes';
  a.leituras.forEach(function (r) {
    var b = document.createElement('button');
    b.className = 'opcao';
    if (a.leitura === r.chave) {
      b.className += a.estado === 'explicita' ? ' escolhida' : ' herdada';
    }
    b.textContent = r.descricao;
    b.addEventListener('click', function () {
      /* Decidir um sítio vale para o caderno inteiro: refaz tudo. */
      anotacoes.push({ kind: a.kind, base: a.base, detalhe: a.detalhe,
                       leitura: r.chave });
      refazer();
    });
    opcoes.appendChild(b);
  });
  div.appendChild(opcoes);
  return div;
}

/* ------------------------------------------------------------------ ligar */

['c-independente', 'c-temporal', 'c-funcoes', 'c-variaveis'].forEach(function (id) {
  $(id).addEventListener('change', refazer);
});
['c-linhas', 'c-pontos'].forEach(function (id) {
  $(id).addEventListener('change', refazer);
});

acrescentar('');
pedir('/api/ler', { latex: 'x' }).then(function (d) {
  if (d.versoes) {
    $('motor').textContent = 'SymPy ' + d.versoes.sympy
      + '  ·  Sucuri ' + d.versoes.sucuri;
  }
});
