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
var anotacoes = [];

function pedir(rota, corpo) {
  corpo.sessao = SESSAO;
  return SUCURI_TRANSPORTE(rota, corpo);
}

/* O caderno não tem convenções: tem declarações, que são células como as
 * outras. Seis campos de formulário diziam o que um punhado de linhas na folha
 * diz melhor — e a declaração DISSOLVE a ambiguidade em vez de escolher uma
 * leitura, então o que ela resolve fica verde, e não âmbar. */

function escapar(t) {
  return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ------------------------------------------------------------- as células */

/* A ORDEM DO DOM é a identidade de uma célula, e não um índice guardado.
 *
 * Guardar o número numa closure funcionava enquanto só se acrescentava no fim.
 * Inserir no meio desloca todas as seguintes, e cada uma continuaria escrevendo
 * na posição antiga do vetor — a folha e o vetor sairiam de sincronia sem que
 * nada avisasse. Com a ordem do DOM mandando, não há segunda cópia para
 * divergir: as fontes se leem da folha quando são precisas.
 */

function celulas() {
  return Array.prototype.filter.call($('folha').children, function (n) {
    return n.classList.contains('celula');
  });
}

function fontesAtuais() {
  return celulas().map(function (c) { return c._area.value; });
}

function criarCelula(fonte) {
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

  var apagar = document.createElement('button');
  apagar.type = 'button';
  apagar.className = 'apagar';
  apagar.setAttribute('aria-label', 'apagar esta célula');
  apagar.title = 'apagar esta célula';
  apagar.textContent = '×';
  apagar.addEventListener('click', function () { apagarCelula(div); });
  cabeca.appendChild(apagar);
  div.appendChild(cabeca);

  var area = document.createElement('textarea');
  area.rows = 1;
  area.spellcheck = false;
  area.value = fonte || '';
  function ajustar() {
    area.style.height = 'auto';
    area.style.height = (area.scrollHeight + 2) + 'px';
  }
  setTimeout(ajustar, 0);
  area.addEventListener('input', ajustar);
  area.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      executar(div);
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

/* O lugar entre duas células, que só existe para ser clicado. Discreto até o
 * ponteiro chegar: um traço e um "+". */
function criarInseridor() {
  var div = document.createElement('div');
  div.className = 'inserir';
  var b = document.createElement('button');
  b.type = 'button';
  b.setAttribute('aria-label', 'inserir célula aqui');
  b.title = 'inserir célula aqui';
  b.textContent = '+';
  b.addEventListener('click', function () {
    var nova = criarCelula('');
    $('folha').insertBefore(nova, div.nextSibling);
    $('folha').insertBefore(criarInseridor(), nova.nextSibling);
    nova._area.focus();
  });
  div.appendChild(b);
  return div;
}

/* Apagar é a única ação da folha que perde trabalho, e não tem diálogo de
 * confirmação: diálogo interrompe todo mundo para proteger o engano de um. A
 * proteção é poder desfazer — e a faixa de aviso já é o lugar onde a página
 * diz o que fez. */
function apagarCelula(celula) {
  var folha = $('folha');
  var antes = celula.previousSibling;          // o inseridor de cima
  var depois = celula.nextSibling;             // o de baixo, que vai junto
  var fonte = celula._area.value;
  var tinhaNome = !!celula._nome.textContent;

  folha.removeChild(celula);
  if (depois && depois.classList && depois.classList.contains('inserir')) {
    folha.removeChild(depois);
  }
  if (!celulas().length) { acrescentar(''); }

  function desfazer() {
    var volta = criarCelula(fonte);
    folha.insertBefore(volta, antes ? antes.nextSibling : folha.firstChild);
    folha.insertBefore(criarInseridor(), volta.nextSibling);
    volta._area.focus();
  }

  if (!fonte.trim()) { return; }               // célula vazia não merece aviso
  avisar(tinhaNome
    ? 'célula apagada — o que ela já tinha definido continua no motor até '
      + '"Rodar tudo" ou "Reiniciar"'
    : 'célula apagada', { rotulo: 'desfazer', fn: desfazer });
}

function acrescentar(fonte) {
  var folha = $('folha');
  var celula = criarCelula(fonte);
  if (!folha.children.length) { folha.appendChild(criarInseridor()); }
  folha.appendChild(celula);
  folha.appendChild(criarInseridor());
  celula._area.focus();
  return celula;
}

/* --------------------------------------------------------------- executar */

function executar(celula) {
  var fonte = celula._area.value;
  celula._saida.innerHTML = '<p class="modulo-desc">…</p>';

  var lista = celulas();
  var ultima = lista[lista.length - 1] === celula;
  pedir('/api/caderno/executar', { fonte: fonte, anotacoes: anotacoes })
    .then(function (d) {
      pintar(celula, d);
      if (ultima && fonte.trim()) { acrescentar(''); return; }
      var depois = celulas()[celulas().indexOf(celula) + 1];
      if (depois) { depois._area.focus(); }
    })
    .catch(function (e) {
      celula._saida.innerHTML = '<div class="bloqueio">' + escapar(e) + '</div>';
    });
}

function refazer() {
  /* Convenção mudou: o que já está escrito passa a significar outra coisa.
   *
   * A folha só se apaga DEPOIS que a resposta chegou e as células novas foram
   * montadas. A primeira versão apagava antes e reconstruía dentro do `then`:
   * qualquer erro no meio — ou uma resposta que não veio — deixava a página em
   * branco, sem uma palavra. Apagar o que está na tela antes de ter o que pôr
   * no lugar é apostar que nada dá errado. */
  var vivas = fontesAtuais().filter(function (f) { return f.trim(); });
  if (!vivas.length) { return; }

  pedir('/api/caderno/refazer',
        { fontes: vivas, anotacoes: anotacoes })
    .then(function (d) {
      var novas = document.createDocumentFragment();
      novas.appendChild(criarInseridor());
      vivas.forEach(function (f, i) {
        var c = criarCelula(f);
        novas.appendChild(c);
        novas.appendChild(criarInseridor());
        if (d.celulas && d.celulas[i]) { pintar(c, d.celulas[i]); }
      });
      var folha = $('folha');
      folha.textContent = '';
      folha.appendChild(novas);
      acrescentar('');
    })
    .catch(function (e) {
      /* Mantém o que está na tela: leitura velha é melhor do que tela vazia,
       * desde que o aviso diga que ela é velha. */
      avisar('não consegui refazer o caderno (' + e + '); o que está na tela '
             + 'ainda é a leitura anterior');
    });
}

function avisar(texto, acao) {
  var faixa = $('faixa');
  faixa.textContent = texto;
  faixa.hidden = false;
  if (acao) {
    var b = document.createElement('button');
    b.className = 'desfazer';
    b.textContent = acao.rotulo;
    b.addEventListener('click', function () {
      faixa.hidden = true;
      acao.fn();
    });
    faixa.appendChild(b);
  }
  clearTimeout(avisar._relogio);
  avisar._relogio = setTimeout(function () { faixa.hidden = true; }, 12000);
}

/* ----------------------------------------------------------------- pintar */

function pintar(celula, d) {
  var saida = celula._saida;
  saida.textContent = '';
  celula.className = 'celula'
    + (d.tipo === 'comando' ? ' comando' : '')
    + (d.tipo === 'declaracao' ? ' declaracao' : '');
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
  /* Nota não é erro: a leitura saiu certa, o que está em desacordo são duas
   * coisas que o usuário afirmou. Âmbar, e não vermelho. */
  (d.notas || []).forEach(function (n) {
    var p = document.createElement('div');
    p.className = 'nao-apresentavel';
    p.textContent = n;
    saida.appendChild(p);
  });

  if (d.tipo === 'declaracao') { pintarDeclaracao(saida, d); }
  else if (d.tipo === 'math') { pintarMath(saida, d); }
  else { pintarComando(saida, d); }
}

function pintarDeclaracao(saida, d) {
  var p = document.createElement('p');
  p.className = 'declarado';
  p.textContent = d.texto;
  saida.appendChild(p);
}

function pintarMath(saida, d) {
  if (d.indices_livres) {
    var val = document.createElement('p');
    val.className = 'valencia';
    val.textContent = d.indices_livres.length
      ? 'índices livres: ' + d.indices_livres.join(', ')
      : 'todos os índices contraídos';
    saida.appendChild(val);
  }
  (d.ambiguidades || []).forEach(function (a) {
    saida.appendChild(SUCURI_SITIO(a, decidir));
  });
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
  /* O que a conta produziu, com nome: é o que permite continuar. Sem isso,
   * ler duas EDOs numa tabela e ter de redigitá-las para seguir. */
  if ((d.nomeados || []).length) {
    var lista = document.createElement('div');
    lista.className = 'nomeados';
    d.nomeados.forEach(function (o) {
      var linha = document.createElement('div');
      linha.className = 'nomeado';
      var nome = document.createElement('span');
      nome.className = 'celula-nome';
      nome.textContent = o.nome;
      linha.appendChild(nome);
      var corpo = document.createElement('div');
      try { katex.render(o.latex, corpo, { throwOnError: false }); }
      catch (e) { corpo.textContent = o.sympy; }
      linha.appendChild(corpo);
      lista.appendChild(linha);
    });
    saida.appendChild(lista);
  }

  /* A cor segue a natureza do recado, e não o campo onde ele veio: barreira
   * (o resultado não se apresenta) é vermelha; nota de alcance (a conta está
   * certa, e o limite dela precisa ser dito) é verde. Os dois chegam em
   * `bloqueado_por`, e era isso que apagava a diferença. */
  var barreira = d.apresentavel === false;
  (d.bloqueado_por || []).forEach(function (b) {
    var p = document.createElement('div');
    p.className = barreira ? 'bloqueio' : 'nota-escopo';
    p.textContent = b;
    saida.appendChild(p);
  });
  if (barreira) {
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

/* Decidir um sítio vale para o caderno inteiro: refaz tudo. */
function decidir(a, leitura) {
  anotacoes = anotacoes.filter(function (o) {
    return !(o.kind === a.kind && o.base === a.base);
  });
  if (leitura !== null) {
    anotacoes.push({ kind: a.kind, base: a.base, detalhe: a.detalhe,
                     leitura: leitura });
  }
  refazer();
}

/* Erro solto não pode terminar em silêncio. */
window.addEventListener('error', function (e) {
  avisar('algo quebrou na página: ' + (e.message || e.error));
});
window.addEventListener('unhandledrejection', function (e) {
  avisar('um pedido não voltou: ' + (e.reason && e.reason.message || e.reason));
});

/* ------------------------------------------------------------------ ligar */

acrescentar('');
pedir('/api/ler', { latex: 'x' }).then(function (d) {
  if (d.versoes) {
    $('motor').textContent = 'SymPy ' + d.versoes.sympy
      + '  ·  Sucuri ' + d.versoes.sucuri;
  }
});

/* ------------------------------------------------------- o caderno inteiro
 *
 * Cinco ações, e cada uma mexe numa camada diferente — a distinção entre elas
 * é a razão de existirem cinco e não duas:
 *
 *   Novo         apaga o escrito E o acumulado
 *   Abrir        troca o escrito, refaz o acumulado
 *   Salvar       leva o escrito (e as decisões) para um arquivo
 *   Rodar tudo   refaz o acumulado a partir do escrito, na ordem
 *   Reiniciar    joga fora só o acumulado: o que está escrito fica
 *
 * "Reiniciar" é o que apaga eq1, eq2 e as declarações sem tocar numa linha do
 * que você escreveu — depois dele, `resolver(eq1)` deixa de achar eq1, que é
 * exatamente o ponto.
 */

var MARCA = '% sucuri caderno v1';
var SEPARADOR = '%%';

function serializar() {
  var linhas = [MARCA];
  if (anotacoes.length) {
    /* As decisões de sítio vão junto: são do usuário, não do motor, e sem elas
     * o caderno reaberto voltaria a perguntar o que já foi respondido. */
    linhas.push('% decisoes: ' + JSON.stringify(anotacoes));
  }
  linhas.push('');
  return linhas.join('\n')
    + fontesAtuais().filter(function (f) { return f.trim(); })
        .join('\n' + SEPARADOR + '\n')
    + '\n';
}

function desserializar(texto) {
  var linhas = texto.split('\n');
  var decisoes = [];
  while (linhas.length && linhas[0].indexOf('%') === 0) {
    var m = linhas[0].match(/^% decisoes:\s*(.*)$/);
    if (m) { try { decisoes = JSON.parse(m[1]); } catch (e) { decisoes = []; } }
    linhas.shift();
  }
  var celulas = linhas.join('\n').split('\n' + SEPARADOR + '\n');
  return {
    fontes: celulas.map(function (c) { return c.trim(); })
      .filter(function (c) { return c; }),
    anotacoes: decisoes
  };
}

function limpar() {
  $('folha').textContent = '';
}

function novo() {
  anotacoes = [];
  limpar();
  acrescentar('');
  $('arquivo').value = 'caderno.tex';
  pedir('/api/caderno/reiniciar', {}).then(function () {
    avisar('caderno novo');
  });
}

function reiniciar() {
  /* Só o acumulado. As células ficam onde estão, com o texto intacto — some o
   * que o motor guardou por ter executado. */
  pedir('/api/caderno/reiniciar', {}).then(function () {
    celulas().forEach(function (c) {
      c._saida.textContent = '';
      c._nome.textContent = '';
      c.className = 'celula';
    });
    avisar('motor reiniciado: eq1, eq2 e as declarações não existem mais; '
           + 'o que está escrito continua aí');
  });
}

function salvar() {
  var nome = ($('arquivo').value || 'caderno.tex').trim();
  var blob = new Blob([serializar()], { type: 'text/plain;charset=utf-8' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = nome;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
}

function abrir(arquivo) {
  var leitor = new FileReader();
  leitor.onload = function () {
    var lido = desserializar(String(leitor.result));
    if (!lido.fontes.length) {
      avisar('esse arquivo não tem célula nenhuma');
      return;
    }
    anotacoes = lido.anotacoes;
    $('arquivo').value = arquivo.name;
    limpar();
    lido.fontes.forEach(function (f) { acrescentar(f); });
    acrescentar('');
    pedir('/api/caderno/reiniciar', {}).then(refazer);
  };
  leitor.readAsText(arquivo);
}

$('b-novo').addEventListener('click', novo);
$('b-salvar').addEventListener('click', salvar);
$('b-rodar').addEventListener('click', refazer);
$('b-reiniciar').addEventListener('click', reiniciar);
$('b-abrir').addEventListener('click', function () {
  $('entrada-arquivo').click();
});
$('entrada-arquivo').addEventListener('change', function (e) {
  if (e.target.files && e.target.files[0]) { abrir(e.target.files[0]); }
  e.target.value = '';
});
