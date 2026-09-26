/* O idioma da tela: português ou inglês.
 *
 * O motor responde no idioma que o pedido diz (`idioma` no corpo — a tradução
 * das mensagens é do Python, sucuri/idioma.py). Aqui fica o resto: os textos
 * da página e os que o JavaScript escreve, por T(). A escolha fica no
 * navegador, e o botão no cabeçalho troca sem recarregar: os textos fixos
 * trocam no lugar, e a página refaz o que já tinha mostrado (evento
 * `sucuri-idioma`).
 *
 * Os comandos em inglês — `g = metric(…)`, `prove(eq3, eq1)` — valem sempre,
 * nos dois idiomas: a língua da tela não muda o sentido de um comando. */
'use strict';

var SUCURI_IDIOMA = (function () {
  var q = /[?&]lang=(pt|en)\b/.exec(location.search);
  if (q) {
    try { localStorage.setItem('sucuri-idioma', q[1]); } catch (e) { /* segue */ }
    return q[1];
  }
  try {
    var salvo = localStorage.getItem('sucuri-idioma');
    if (salvo === 'pt' || salvo === 'en') { return salvo; }
  } catch (e) { /* armazenamento bloqueado: segue o navegador */ }
  var nav = (navigator.language || 'pt').toLowerCase();
  return nav.indexOf('pt') === 0 ? 'pt' : 'en';
})();

var SUCURI_EN = {
  /* cabeçalho, barras, rodapé */
  'manual': 'manual', 'caderno': 'notebook', 'uma equação': 'one equation',
  'apostila': 'tutorial',
  'Novo': 'New', 'Abrir': 'Open', 'Salvar': 'Save', 'Rodar tudo': 'Run all',
  'Reiniciar': 'Restart', 'executa': 'runs', 'nome do arquivo': 'file name',
  'sem título.tex': 'untitled.tex', 'LaTeX estrito': 'strict LaTeX',
  /* uma equação */
  'Entrada em LaTeX': 'LaTeX input', 'Falta uma convenção': 'A convention is missing',
  'Sítios ambíguos': 'Ambiguous sites', 'Convenções do documento': 'Document conventions',
  'Variável independente': 'Independent variable', 'Variável temporal': 'Time variable',
  'Linha': 'Prime', 'perguntar': 'ask', 'é derivada': 'is a derivative',
  'faz parte do nome': 'is part of the name', 'Ponto': 'Dot',
  'é derivada temporal': 'is a time derivative', 'é só um acento': 'is just an accent',
  'Funções': 'Functions', 'Variáveis': 'Variables',
  'Árvore reconhecida': 'Recognized tree', 'Como o Sucuri lê': 'How Sucuri reads it',
  'Saída em SymPy': 'SymPy output', '# escreva algo à esquerda': '# write something on the left',
  'Copiar código': 'Copy code', 'Módulos': 'Modules', 'Avaliar': 'Evaluate',
  'Valor': 'Value', 'Módulos carregados': 'Loaded modules',
  'Resolver': 'Solve', 'Solução': 'Solution', 'Código copiado': 'Code copied',
  'sítio pendente': 'pending site', 'sítios pendentes': 'pending sites',
  'não foi possível converter': 'could not convert', 'árvore válida': 'valid tree',
  'índices livres: ': 'free indices: ', 'todos os índices contraídos': 'all indices contracted',
  'leitura por convenção': 'reading by convention', 'leituras por convenção': 'readings by convention',
  'Derivada em relação a qual variável? Sem isso, ': 'Derivative with respect to which variable? Without it, ',
  '"derivada" não diz o bastante.': '"derivative" does not say enough.',
  'Usar': 'Use', 'letras que aparecem na equação:': 'letters that appear in the equation:',
  'nenhuma letra sobra na equação: a variável não está ': 'no letter is left in the equation: the variable is not ',
  'escrita ali, e é por isso que ninguém pode tirá-la de lá.': 'written there, and that is why nobody can take it from there.',
  'Ainda não interpretado — só a sua escrita': 'Not interpreted yet — only what you wrote',
  'nada escrito ainda': 'nothing written yet',
  'sítio ambíguo espera decisão': 'ambiguous site awaits a decision',
  'sítios ambíguos esperam decisão': 'ambiguous sites await a decision',
  'sem saída': 'no output', 'resolvendo…': 'solving…', 'calculando…': 'computing…',
  'integral indefinida: a resposta é a família inteira, ': 'indefinite integral: the answer is the whole family, ',
  'e o código abaixo traz uma primitiva dela.': 'and the code below gives one antiderivative.',
  '  (aproximação; o valor é o de cima)': '  (approximation; the value is the one above)',
  'não fechou: o SymPy devolveu a conta por fazer, ': 'did not close: SymPy returned the computation undone, ',
  'não o valor dela': 'not its value',
  'proveniência: ': 'provenance: ', ' — não apresentável como conclusão': ' — not presentable as a conclusion',
  'algo quebrou na página: ': 'something broke on the page: ',
  'um pedido não voltou: ': 'a request did not come back: ', 'motor fora do ar: ': 'engine is down: ',
  /* operações dos módulos */
  'esquema de Riemann': 'Riemann scheme', 'condições de Kovacic': 'Kovacic conditions',
  'não-integrabilidade': 'non-integrability', 'resolver': 'solve', 'padrões': 'patterns',
  'separar': 'separate', 'conferir': 'check',
  /* caderno */
  'apagar esta célula': 'delete this cell', 'inserir célula aqui': 'insert a cell here',
  'célula apagada — o que ela já tinha definido continua no motor até ':
    'cell deleted — what it had defined stays in the engine until ',
  '"Rodar tudo" ou "Reiniciar"': '"Run all" or "Restart"',
  'célula apagada': 'cell deleted', 'desfazer': 'undo',
  'não consegui refazer o caderno (': 'could not rerun the notebook (',
  '); o que está na tela ': '); what is on the screen ',
  'ainda é a leitura anterior': 'is still the previous reading',
  'Copiar LaTeX': 'Copy LaTeX', 'caderno novo': 'new notebook',
  'motor reiniciado: eq1, eq2 e as declarações não existem mais; ':
    'engine restarted: eq1, eq2 and the declarations no longer exist; ',
  'o que está escrito continua aí': 'what is written is still there',
  'esse arquivo não tem célula nenhuma': 'this file has no cells',
  /* sítios */
  'da convenção — ninguém olhou este caso': 'from the convention — nobody looked at this case',
  'decidido aqui': 'decided here', 'o Sucuri não escolhe por você': 'Sucuri does not choose for you',
  'voltar à convenção': 'back to the convention',
  /* carregamento (versão online) */
  'iniciando…': 'starting…', 'baixando o Python': 'downloading Python',
  'carregando o SymPy': 'loading SymPy', 'carregando o leitor de LaTeX': 'loading the LaTeX reader',
  'abrindo o Sucuri': 'opening Sucuri', 'aquecendo o leitor': 'warming up the reader',
  'recarregando o motor…': 'reloading the engine…', 'não deu: ': 'failed: ',
  '  ·  no navegador': '  ·  in the browser'
};

function T(s) {
  if (SUCURI_IDIOMA !== 'en' || s == null) { return s; }
  var en = SUCURI_EN[s];
  return en === undefined ? s : en;
}

/* Páginas com versão em inglês própria: o link segue o idioma. */
var SUCURI_PAGINAS_EN = { 'manual.html': 'manual-en.html', 'apostila.html': 'tutorial.html' };

var SUCURI_TEXTOS = [];   // [nó, português] — para voltar ao português sem recarregar

function sucuriColetar(raiz) {
  var andar = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, null);
  var n;
  while ((n = andar.nextNode())) {
    var p = n.parentNode;
    if (!p || /^(SCRIPT|STYLE|TEXTAREA|CODE|KBD|PRE)$/.test(p.nodeName)) { continue; }
    if (p.closest && p.closest('[data-en], .folha, #leitura, #arvore, #perguntas, #resultado, #avaliacao, #estados, #faltando, #modulos')) { continue; }
    var chave = n.nodeValue.replace(/\s+/g, ' ').trim();
    if (chave && SUCURI_EN[chave] !== undefined) { SUCURI_TEXTOS.push([n, n.nodeValue, chave]); }
  }
  Array.prototype.forEach.call(raiz.querySelectorAll('[title],[aria-label],[placeholder]'), function (el) {
    ['title', 'aria-label', 'placeholder'].forEach(function (a) {
      var v = el.getAttribute(a);
      if (v && SUCURI_EN[v] !== undefined) { SUCURI_TEXTOS.push([el, v, v, a]); }
    });
  });
  Array.prototype.forEach.call(raiz.querySelectorAll('[data-en]'), function (el) {
    SUCURI_TEXTOS.push([el, el.innerHTML, null, 'html']);
  });
  Array.prototype.forEach.call(raiz.querySelectorAll('a[href]'), function (el) {
    var h = el.getAttribute('href');
    if (SUCURI_PAGINAS_EN[h]) { SUCURI_TEXTOS.push([el, h, null, 'href']); }
  });
}

function sucuriAplicar() {
  var en = SUCURI_IDIOMA === 'en';
  document.documentElement.lang = en ? 'en' : 'pt-BR';
  SUCURI_TEXTOS.forEach(function (t) {
    var no = t[0], pt = t[1], chave = t[2], modo = t[3];
    if (modo === 'html') { no.innerHTML = en ? no.getAttribute('data-en') : pt; }
    else if (modo === 'href') { no.setAttribute('href', en ? SUCURI_PAGINAS_EN[pt] : pt); }
    else if (modo) { no.setAttribute(modo, en ? SUCURI_EN[chave] : pt); }
    else {
      var fora = pt.match(/^\s*/)[0], dentro = pt.match(/\s*$/)[0];
      no.nodeValue = en ? fora + SUCURI_EN[chave] + dentro : pt;
    }
  });
  var b = document.getElementById('b-idioma');
  if (b) {
    b.textContent = en ? 'PT' : 'EN';
    b.title = en ? 'ver em português' : 'switch to English';
  }
}

function sucuriTrocarIdioma() {
  SUCURI_IDIOMA = SUCURI_IDIOMA === 'en' ? 'pt' : 'en';
  try { localStorage.setItem('sucuri-idioma', SUCURI_IDIOMA); } catch (e) { /* segue sem guardar */ }
  sucuriAplicar();
  window.dispatchEvent(new Event('sucuri-idioma'));
}

/* Todo pedido leva o idioma: o motor traduz a resposta. Vale para os dois
 * transportes — HTTP local e o Pyodide da versão online. */
if (typeof SUCURI_TRANSPORTE === 'function') {
  var sucuriTransporteOriginal = SUCURI_TRANSPORTE;
  SUCURI_TRANSPORTE = function (rota, corpo) {
    var c = {};
    Object.keys(corpo || {}).forEach(function (k) { c[k] = corpo[k]; });
    c.idioma = SUCURI_IDIOMA;
    return sucuriTransporteOriginal(rota, c);
  };
}

(function () {
  var cab = document.querySelector('header');
  if (cab && !document.getElementById('b-idioma')) {
    var b = document.createElement('button');
    b.type = 'button';
    b.id = 'b-idioma';
    b.className = 'modo idioma';
    b.addEventListener('click', sucuriTrocarIdioma);
    var arquivo = cab.querySelector('.arquivo');
    cab.insertBefore(b, arquivo);          // antes do nome do arquivo, com os outros modos
  }
  sucuriColetar(document.body);
  sucuriAplicar();
})();
