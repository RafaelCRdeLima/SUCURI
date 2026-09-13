/* Os sítios ambíguos, desenhados conforme o estado — e não todos iguais.
 *
 * Perguntar o que já foi respondido é o erro oposto ao de adivinhar, e custa a
 * mesma coisa: faz o usuário desconfiar de uma decisão que ele já tomou. Quem
 * declarou "linha é derivada" nas convenções não deve ver a pergunta de novo
 * em cada célula.
 *
 * Mas o sítio resolvido ainda tem o que dizer, e é diferente da pergunta:
 *
 *   pendente    ninguém decidiu     -> a pergunta inteira, com as leituras
 *   inferida    veio da convenção   -> uma linha em âmbar: funcionou, e
 *                                      ninguém olhou ESTE caso
 *   explícita   decidida aqui       -> uma linha em verde, discreta
 *
 * A linha abre nas opções quando clicada: mudar de ideia continua a um toque,
 * só não ocupa a tela enquanto ninguém quer mudar.
 */
'use strict';

function SUCURI_SITIO(a, aoDecidir) {
  var div = document.createElement('div');
  div.className = 'sitio ' + a.estado;

  if (a.estado === 'pendente') {
    div.appendChild(cabecaDoSitio(a));
    div.appendChild(opcoesDoSitio(a, aoDecidir));
    return div;
  }

  div.className += ' resolvido';
  var linha = document.createElement('button');
  linha.className = 'sitio-linha';
  linha.setAttribute('aria-expanded', 'false');

  var frag = document.createElement('span');
  frag.className = 'fragmento';
  frag.textContent = a.fragmento;
  linha.appendChild(frag);

  var leitura = document.createElement('span');
  leitura.className = 'sitio-leitura';
  leitura.textContent = descricaoDe(a);
  linha.appendChild(leitura);

  var origem = document.createElement('span');
  origem.className = 'sitio-origem';
  /* Quando a leitura veio de uma DECLARAÇÃO, o motivo é melhor do que
   * "decidido aqui": diz o que foi declarado, e portanto por que não há mais
   * o que perguntar. */
  origem.textContent = a.motivo ? a.motivo
    : a.estado === 'inferida' ? 'da convenção — ninguém olhou este caso'
    : 'decidido aqui';
  linha.appendChild(origem);

  var opcoes = opcoesDoSitio(a, aoDecidir);
  opcoes.hidden = true;
  linha.addEventListener('click', function () {
    opcoes.hidden = !opcoes.hidden;
    linha.setAttribute('aria-expanded', String(!opcoes.hidden));
  });

  div.appendChild(linha);
  div.appendChild(opcoes);
  return div;
}

function descricaoDe(a) {
  for (var i = 0; i < a.leituras.length; i++) {
    if (a.leituras[i].chave === a.leitura) { return a.leituras[i].descricao; }
  }
  return a.leitura || '';
}

function cabecaDoSitio(a) {
  var cabeca = document.createElement('div');
  cabeca.className = 'sitio-cabeca';
  var frag = document.createElement('span');
  frag.className = 'fragmento';
  frag.textContent = a.fragmento;
  cabeca.appendChild(frag);
  var nota = document.createElement('span');
  nota.className = 'sitio-nota';
  nota.textContent = 'o Sucuri não escolhe por você';
  cabeca.appendChild(nota);
  return cabeca;
}

function opcoesDoSitio(a, aoDecidir) {
  var opcoes = document.createElement('div');
  opcoes.className = 'opcoes';
  a.leituras.forEach(function (r) {
    var b = document.createElement('button');
    b.className = 'opcao';
    if (a.leitura === r.chave) {
      b.className += a.estado === 'explicita' ? ' escolhida' : ' herdada';
    }
    b.textContent = r.descricao;
    b.addEventListener('click', function (e) {
      e.stopPropagation();
      aoDecidir(a, r.chave);
    });
    opcoes.appendChild(b);
  });
  if (a.estado === 'explicita') {
    var limpar = document.createElement('button');
    limpar.className = 'opcao';
    limpar.textContent = 'voltar à convenção';
    limpar.addEventListener('click', function (e) {
      e.stopPropagation();
      aoDecidir(a, null);
    });
    opcoes.appendChild(limpar);
  }
  return opcoes;
}
