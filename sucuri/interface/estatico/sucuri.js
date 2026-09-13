/* SUCURI — a interface.
 *
 * Ela não decide nada de matemática. Manda o LaTeX ao motor, mostra o que
 * voltou e devolve ao motor as duas únicas decisões que são do usuário: as
 * convenções do documento e a leitura de cada sítio ambíguo.
 */
'use strict';

var $ = function (id) { return document.getElementById(id); };
var SESSAO = 'local';
var sequencia = 0;
var ultimo = null;      // última leitura recebida

/* O transporte vem de fora: `SUCURI_TRANSPORTE(rota, corpo)` devolve uma
 * promessa com a resposta do motor. Local é fetch para o servidor; online é
 * postMessage para o Pyodide. A interface não sabe a diferença, e é por isso
 * que existe uma só. */

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

function ler() {
  var meu = ++sequencia;
  pedir('/api/ler', { latex: $('entrada').value, convencoes: convencoes() })
    .then(function (d) { if (meu === sequencia) mostrar(d); })
    .catch(function (e) { mostrarFalha(e); });
}

var espera = null;
function lerDepois() {
  clearTimeout(espera);
  espera = setTimeout(ler, 220);
}

/* ---------------------------------------------------------------- estados */

var ICONE_OK = '<svg width="13" height="13" viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10.5l4 4 8-9" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
var ICONE_AVISO = '<svg width="13" height="13" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3l8 14H2z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M10 8v4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="10" cy="15" r="1" fill="currentColor"/></svg>';
var ICONE_ERRO = '<svg width="13" height="13" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 7l6 6M13 7l-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

function pastilha(classe, icone, texto) {
  var s = document.createElement('span');
  s.className = 'pill ' + classe;
  s.innerHTML = icone + ' ' + escapar(texto);
  return s;
}

function plural(n, um, muitos) { return n + ' ' + (n === 1 ? um : muitos); }

function estados(d) {
  var caixa = $('estados');
  caixa.textContent = '';
  if (!d.latex.trim()) { return; }

  if (d.pendentes) {
    caixa.appendChild(pastilha('aviso', ICONE_AVISO,
      plural(d.pendentes, 'sítio pendente', 'sítios pendentes')));
  } else if (d.erro) {
    caixa.appendChild(pastilha('erro', ICONE_ERRO, 'não foi possível converter'));
  } else {
    caixa.appendChild(pastilha('ok', ICONE_OK, 'árvore válida'));
  }
  if (d.inferidas) {
    caixa.appendChild(pastilha('aviso', ICONE_AVISO,
      plural(d.inferidas, 'leitura por convenção', 'leituras por convenção')));
  }
  (d.avisos || []).forEach(function (a) {
    caixa.appendChild(pastilha('erro', ICONE_ERRO, a));
  });
  if (d.erro && !d.pendentes) {
    caixa.appendChild(pastilha('neutro', '', d.erro));
  }
}

/* -------------------------------------------------------------- perguntas */

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
    b.addEventListener('click', function () { decidir(a, r.chave); });
    opcoes.appendChild(b);
  });
  if (a.estado === 'explicita') {
    var limpar = document.createElement('button');
    limpar.className = 'opcao';
    limpar.textContent = 'voltar à convenção';
    limpar.addEventListener('click', function () { decidir(a, null); });
    opcoes.appendChild(limpar);
  }
  div.appendChild(opcoes);
  return div;
}

function decidir(a, leitura) {
  var meu = ++sequencia;
  pedir('/api/anotar', {
    latex: $('entrada').value, kind: a.kind, base: a.base,
    detalhe: a.detalhe, leitura: leitura
  }).then(function (d) { if (meu === sequencia) mostrar(d); });
}

function perguntas(d) {
  var caixa = $('perguntas');
  caixa.textContent = '';
  var lista = d.ambiguidades || [];
  $('bloco-perguntas').hidden = lista.length === 0;
  lista.forEach(function (a) { caixa.appendChild(sitio(a)); });
}

/* ----------------------------------------------------------------- árvore */

function ramo(no) {
  var li = document.createElement('li');
  li.className = 'no' + (no.estado ? ' ' + no.estado : '');
  li.textContent = no.rotulo;
  var ul = document.createElement('ul');
  ul.appendChild(li);
  (no.filhos || []).forEach(function (f) { ul.appendChild(ramo(f)); });
  return ul;
}

function arvore(d) {
  var caixa = $('arvore');
  caixa.textContent = '';
  $('bloco-arvore').hidden = !d.arvore;
  if (d.arvore) { caixa.appendChild(ramo(d.arvore)); }
}

/* ---------------------------------------------------------------- leitura */

function leitura(d) {
  var caixa = $('leitura');
  caixa.textContent = '';
  caixa.classList.remove('cru');
  var alvo = d.latex_semantico;

  if (!d.latex.trim()) {
    caixa.innerHTML = '<span class="vazio">nada escrito ainda</span>';
    $('rotulo-leitura').textContent = 'Como o Sucuri lê';
    return;
  }
  if (!alvo) {
    caixa.classList.add('cru');
    alvo = d.latex;
    $('rotulo-leitura').textContent = 'Ainda não interpretado — só a sua escrita';
  } else {
    $('rotulo-leitura').textContent = 'Como o Sucuri lê';
  }
  try {
    katex.render(alvo, caixa, { displayMode: true, throwOnError: false });
  } catch (e) {
    caixa.textContent = alvo;
  }
}

/* ----------------------------------------------------------------- código */

function escapar(t) {
  return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

var TOKENS = /(#[^\n]*)|('[^'\n]*')|\b(from|import|True|False|None|lambda)\b/g;

function pintar(codigo) {
  return escapar(codigo).replace(TOKENS, function (m, cm, str, kw) {
    if (cm) { return '<span class="cm">' + cm + '</span>'; }
    if (str) { return '<span class="str">' + str + '</span>'; }
    return '<span class="kw">' + kw + '</span>';
  });
}

function codigo(d) {
  var pre = $('codigo');
  if (d.codigo) { pre.innerHTML = pintar(d.codigo); return; }
  if (!d.latex.trim()) {
    pre.innerHTML = '<span class="cm"># escreva algo à esquerda</span>';
  } else if (d.pendentes) {
    pre.innerHTML = '<span class="cm"># ' + escapar(plural(d.pendentes,
      'sítio ambíguo espera decisão', 'sítios ambíguos esperam decisão'))
      + '</span>';
  } else {
    pre.innerHTML = '<span class="cm"># ' + escapar(d.erro || 'sem saída') + '</span>';
  }
}

/* --------------------------------------------------------------- avaliação */

/* Ler e avaliar são atos diferentes, e é por isso que avaliar é um botão e não
 * um efeito de digitar: a integral fica parada até alguém pedir a conta. */

/* O verbo segue o objeto: equação diferencial se resolve, expressão se avalia.
 * São contas diferentes, e oferecer a errada faz o usuário concluir que o
 * programa não sabe fazer o que ele sabe fazer. */

function acaoPrincipal() {
  return (ultimo && ultimo.diferencial) ? resolverEdo : avaliar;
}

function resolverEdo() {
  var caixa = abrirValor('resolvendo…');
  pedir('/api/operar', { latex: $('entrada').value, modulo: 'resolver',
                         operacao: 'resolver' })
    .then(function (r) { caixa.textContent = ''; caixa.appendChild(resultado(r)); })
    .catch(function (e) {
      caixa.innerHTML = '<div class="bloqueio">' + escapar(e) + '</div>';
    });
}

function abrirValor(aviso) {
  var caixa = $('avaliacao');
  $('bloco-avaliacao').hidden = false;
  caixa.innerHTML = '<p class="modulo-desc">' + aviso + '</p>';
  return caixa;
}

function avaliar() {
  var caixa = abrirValor('calculando…');
  pedir('/api/avaliar', { latex: $('entrada').value, convencoes: convencoes() })
    .then(function (d) { caixa.textContent = ''; caixa.appendChild(valor(d)); })
    .catch(function (e) {
      caixa.innerHTML = '<div class="bloqueio">' + escapar(e) + '</div>';
    });
}

function valor(d) {
  var div = document.createElement('div');
  div.className = 'resultado';

  if (d.erro) {
    div.innerHTML = '<div class="bloqueio">' + escapar(d.erro) + '</div>';
    (d.pendentes || []).forEach(function (p) {
      var q = document.createElement('p');
      q.className = 'modulo-desc';
      q.textContent = p;
      div.appendChild(q);
    });
    return div;
  }

  var m = document.createElement('div');
  /* A constante entra na conta que se mostra, não numa nota de rodapé: o
   * resultado de uma integral indefinida É a família, e escrever só um
   * representante dela seria dar o representante por resposta. */
  var escrita = d.latex_exato + (d.indefinida ? ' + C' : '');
  try { katex.render(escrita, m, { displayMode: true, throwOnError: false }); }
  catch (e) { m.textContent = d.exato + (d.indefinida ? ' + C' : ''); }
  div.appendChild(m);

  if (d.indefinida) {
    var fam = document.createElement('p');
    fam.className = 'modulo-desc';
    fam.textContent = 'integral indefinida: a resposta é a família inteira, '
      + 'e o código abaixo traz uma primitiva dela.';
    div.appendChild(fam);
  }

  if (d.numerico) {
    var n = document.createElement('p');
    n.className = 'modulo-desc';
    n.textContent = '≈ ' + d.numerico + '  (aproximação; o valor é o de cima)';
    div.appendChild(n);
  }
  if (!d.fechou) {
    var aviso = document.createElement('div');
    aviso.className = 'nao-apresentavel';
    aviso.textContent = 'não fechou: o SymPy devolveu a conta por fazer, '
      + 'não o valor dela';
    div.appendChild(aviso);
  }
  $('tempo').textContent = d.ms + ' ms';
  return div;
}

/* ---------------------------------------------------------------- módulos */

/* Operações que a página já oferece por outro caminho. Repeti-las num painel
 * faz o usuário procurar diferença onde não há, e um botão que só mostra o
 * que já está à mão não paga o espaço que ocupa. */
var JA_OFERECIDO = { resolver: ['resolver', 'padrões'] };

function sobra(m) {
  var cobertas = JA_OFERECIDO[m.nome] || [];
  return (m.operacoes || []).filter(function (op) {
    return cobertas.indexOf(op.nome) === -1;
  });
}

/* Módulo indisponível não vai para a tela. Dizer "korvin: ModuleNotFoundError"
 * a quem nunca ouviu falar do KORVIN não é honestidade, é ruído; a API
 * continua reportando, com motivo, para quem for olhar. */
function decidirModulos() {
  pedir('/api/modulos', {}).then(function (d) {
    var uteis = (d.modulos || []).filter(function (m) {
      return m.disponivel && sobra(m).length;
    });
    if (!uteis.length) { $('abrir-modulos').hidden = true; }
  }).catch(function () { $('abrir-modulos').hidden = true; });
}

function modulos() {
  var bloco = $('bloco-modulos');
  if (!bloco.hidden) { bloco.hidden = true; return; }
  bloco.hidden = false;
  pedir('/api/modulos', {}).then(function (d) {
    var caixa = $('modulos');
    caixa.textContent = '';
    (d.modulos || []).filter(function (m) {
      return m.disponivel && sobra(m).length;
    }).forEach(function (m) {
      var cab = document.createElement('p');
      cab.className = 'modulo-cabeca';
      cab.innerHTML = '<b>' + escapar(m.nome) + '</b>';
      caixa.appendChild(cab);
      var desc = document.createElement('p');
      desc.className = 'modulo-desc';
      desc.textContent = m.descricao;
      caixa.appendChild(desc);
      var ops = document.createElement('div');
      ops.className = 'operacoes';
      sobra(m).forEach(function (op) {
        var b = document.createElement('button');
        b.textContent = op.nome;
        b.title = op.descricao;
        b.addEventListener('click', function () { operar(m.nome, op.nome); });
        ops.appendChild(b);
      });
      caixa.appendChild(ops);
    });
  });
}

function operar(modulo, operacao) {
  var caixa = $('resultado');
  caixa.innerHTML = '<p class="modulo-desc">calculando…</p>';
  pedir('/api/operar', {
    latex: $('entrada').value, modulo: modulo, operacao: operacao
  }).then(function (r) { caixa.textContent = ''; caixa.appendChild(resultado(r)); });
}

function resultado(r) {
  var div = document.createElement('div');
  div.className = 'resultado';
  if (r.erro) {
    div.innerHTML = '<div class="bloqueio">' + escapar(r.erro) + '</div>';
    (r.pendentes || []).forEach(function (p) {
      var q = document.createElement('p');
      q.className = 'modulo-desc';
      q.textContent = p;
      div.appendChild(q);
    });
    return div;
  }

  var h = document.createElement('h3');
  h.textContent = r.rotulo;
  div.appendChild(h);

  if (r.latex) {
    var m = document.createElement('div');
    try { katex.render(r.latex, m, { displayMode: true, throwOnError: false }); }
    catch (e) { m.textContent = r.latex; }
    div.appendChild(m);
  }
  if ((r.linhas || []).length) {
    var t = document.createElement('table');
    r.linhas.forEach(function (linha) {
      var tr = document.createElement('tr');
      linha.forEach(function (c) {
        var td = document.createElement('td');
        td.textContent = c;
        tr.appendChild(td);
      });
      t.appendChild(tr);
    });
    div.appendChild(t);
  }
  (r.bloqueado_por || []).forEach(function (b) {
    var p = document.createElement('div');
    p.className = 'bloqueio';
    p.textContent = b;
    div.appendChild(p);
  });
  var prov = document.createElement('div');
  prov.className = 'proveniencia' + (r.apresentavel ? '' : ' nao-apresentavel');
  prov.textContent = r.apresentavel
    ? 'proveniência: ' + r.proveniencia
    : 'proveniência: ' + r.proveniencia + ' — não apresentável como conclusão';
  div.appendChild(prov);
  return div;
}

/* ------------------------------------------------------------------ pinta */

function mostrar(d) {
  ultimo = d;
  $('bloco-avaliacao').hidden = true;      // o valor era de outra equação
  $('avaliar').textContent = d.diferencial ? 'Resolver' : 'Avaliar';
  $('rotulo-valor').textContent = d.diferencial ? 'Solução' : 'Valor';
  estados(d);
  perguntas(d);
  arvore(d);
  leitura(d);
  codigo(d);
  $('tempo').textContent = d.ms + ' ms';
  if (d.versoes) {
    $('motor').textContent = 'SymPy ' + d.versoes.sympy
      + '  ·  Sucuri ' + d.versoes.sucuri;
  }
  if (d.pendentes && !$('bloco-convencoes').open) {
    $('bloco-convencoes').open = true;
  }
}

function mostrarFalha(e) {
  $('estados').textContent = '';
  $('estados').appendChild(pastilha('erro', ICONE_ERRO, 'motor fora do ar: ' + e));
}

/* ------------------------------------------------------------------ ligar */

$('entrada').addEventListener('input', lerDepois);
['c-independente', 'c-temporal', 'c-funcoes', 'c-variaveis'].forEach(function (id) {
  $(id).addEventListener('input', lerDepois);
});
['c-linhas', 'c-pontos'].forEach(function (id) {
  $(id).addEventListener('change', ler);
});

$('copiar').addEventListener('click', function (e) {
  navigator.clipboard.writeText($('codigo').innerText).then(function () {
    e.target.textContent = 'Código copiado';
    setTimeout(function () { e.target.textContent = 'Copiar código'; }, 1600);
  });
});
$('abrir-modulos').addEventListener('click', modulos);
$('avaliar').addEventListener('click', function () { acaoPrincipal()(); });

$('entrada').focus();
ler();
decidirModulos();
