"""A árvore reconhecida e a API avulsa.

A árvore é o painel central da interface. Ela só tem valor se carregar de volta
a proveniência: um nó que nasceu de convenção do documento precisa aparecer em
âmbar, para o usuário ver de relance o que o programa supôs.
"""

import json

import sympy as sp
import pytest

import sucuri
from sucuri import Document, Unresolved, Resolution

RICCATI = r"\varphi'' + 3\varphi\varphi' + \varphi^3 = 4r\varphi + 2r'"


def documento():
    d = Document(independent_variable='x').primes_are_derivatives()
    d.annotate("prime", "r", "derivative", order=1)
    return d


# ------------------------------------------------------------- estrutura

def test_arvore_tem_a_forma_da_equacao():
    t = documento().read(RICCATI).tree()
    assert t.label == "igualdade"
    assert len(t.children) == 2, "lado esquerdo e direito"


def test_derivada_e_folha_na_leitura_do_usuario():
    """Quem lê quer ver 'derivada segunda de phi', não a árvore interna dela."""
    t = documento().read(RICCATI).tree()
    derivadas = [n for n in t.walk() if "derivada" in n.label]
    assert derivadas
    assert all(n.children == [] for n in derivadas)


# --------------------------------------------------------- proveniência

def test_no_carrega_como_foi_resolvido():
    """O que decide a cor: inferida vira âmbar, explícita não."""
    t = documento().read(RICCATI).tree()
    estados = {n.label: n.state for n in t.walk() if n.state}

    assert estados["derivada de ordem 2 de varphi em x"] == Resolution.INFERRED
    assert estados["derivada de ordem 1 de varphi em x"] == Resolution.INFERRED
    assert estados["derivada de ordem 1 de r em x"] == Resolution.EXPLICIT

    conferir = [n for n in t.walk() if n.needs_review]
    assert len(conferir) == 2


def test_no_sem_origem_ambigua_nao_tem_estado():
    """Soma, produto e potência não vieram de ambiguidade nenhuma."""
    t = documento().read(RICCATI).tree()
    assert all(n.state is None
               for n in t.walk() if n.label in ("soma", "produto", "potência"))


def test_arvore_serializa_para_a_interface():
    d = documento().read(RICCATI).tree().to_dict()
    texto = json.dumps(d)                       # tem de ser serializável
    assert '"conferir": true' in texto
    assert d["rotulo"] == "igualdade"
    assert "latex" in d and "filhos" in d


def test_arvore_recusa_com_pendencia():
    with pytest.raises(Unresolved):
        Document().read(RICCATI).tree()


# ------------------------------------------------------- API avulsa

def test_parse_sem_convencao_recusa():
    """O padrão é recusar. Adivinhar é o que este programa não faz."""
    e = sucuri.parse(RICCATI)
    assert len(e.pending) == 3
    with pytest.raises(Unresolved):
        e.to_sympy()


def test_parse_com_convencao_le_certo():
    e = sucuri.parse(RICCATI, independent_variable='x', primes='derivative')
    assert e.resolved
    assert len(e.to_sympy().atoms(sp.Derivative)) == 3


def test_parse_marca_tudo_como_inferido():
    """Convenção passada na chamada é inferência, não decisão por sítio."""
    e = sucuri.parse(RICCATI, independent_variable='x', primes='derivative')
    assert len(e.inferred) == 3


def test_parse_funcao_versus_variavel():
    src = r"f\left(x + 1\right)"
    assert sucuri.parse(src, functions=['f']).to_sympy().atoms(sp.Function)
    assert sp.Symbol('f') in sucuri.parse(src, variables=['f']).to_sympy().free_symbols


def test_parse_recusa_opcao_invalida():
    with pytest.raises(ValueError):
        sucuri.parse(r"y'", primes='talvez')
