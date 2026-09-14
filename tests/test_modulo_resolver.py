"""O módulo que resolve — e que diz QUE TIPO de resposta deu.

O `dsolve` responde "consigo achar uma solução?", nunca "existe uma?". Pior:
ele rebaixa a resposta sem avisar, devolvendo série truncada onde havia forma
fechada. Estes testes prendem as quatro respostas possíveis no lugar.
"""

import pytest
import sympy as sp

import sucuri
from sucuri import modules
from sucuri.modules import Provenance
from sucuri.modules import resolver as R

x = sp.Symbol("x")


def doc():
    d = sucuri.Document(independent_variable="x")
    d.function("y")
    d.primes_are_derivatives(True)
    d.e_is_euler(True)
    return d


def resolver(latex):
    return R.resolver(doc().read(latex))


def linha(resultado, chave):
    for k, v in resultado.rows:
        if k == chave:
            return v
    return None


# ------------------------------------------------------ o que atravessa

def test_funcao_indefinida_nao_atravessa_por_pickle():
    """O `y` de y(x) é uma classe criada em tempo de execução, e o pickle só a
    encontra se por acaso for atributo de um módulo — a nossa nunca é. O erro
    estourava na thread que alimenta a fila, o filho saía com código 0, e o pai
    esperava para sempre. Por isso vai srepr, não objeto."""
    import pickle
    alvo = sp.Eq(sp.Function("y")(x), sp.Symbol("C1") * sp.sin(x))
    with pytest.raises(Exception):
        pickle.loads(pickle.dumps(alvo))

    assert R._desempacotar(R._empacotar(alvo)) == alvo
    assert R._desempacotar(R._empacotar([(True, sp.Integer(0))])) == [(True, 0)]


def test_prazo_mata_o_processo():
    """O dsolve não oferece ponto de interrupção; thread pendurada queima CPU
    até o fim do programa. Processo se mata."""
    import time
    t = time.time()
    with pytest.raises(R.TempoEsgotado):
        R._no_prazo(time.sleep, 1, 30)
    assert time.time() - t < 10


# ------------------------------------------------- as quatro respostas

def test_forma_fechada_e_conferida_por_substituicao():
    r = resolver("y'' + y = 0")
    assert linha(r, "tipo") == R.FECHADA
    assert r.provenance == Provenance.ESTABLISHED
    assert r.presentable
    assert r.payload == sp.Eq(sp.Function("y")(x),
                              sp.Symbol("C1") * sp.sin(x)
                              + sp.Symbol("C2") * sp.cos(x))
    assert "resto 0" in linha(r, "conferência")


def test_airy_sai_em_funcoes_de_airy():
    r = resolver("y'' = x y")
    assert r.provenance == Provenance.ESTABLISHED
    assert r.payload.rhs.has(sp.airyai)


def test_serie_truncada_nao_e_solucao():
    """y'' + xy' + y = 0 é (y' + xy)' = 0 e TEM forma fechada, com erfi. O
    dsolve devolve série até ordem 5 e não diz que mudou de tipo de resposta.
    Este é o motivo de o módulo existir."""
    r = resolver("y'' + x y' + y = 0")
    assert "série" in r.label
    assert linha(r, "tipo").startswith(R.SERIE)
    assert "O(x**6)" in linha(r, "tipo")
    # não é conclusão: é aproximação até uma ordem
    assert r.provenance == Provenance.INAPPLICABLE
    assert r.payload.has(sp.Order)


def test_nao_achar_nao_e_provar_que_nao_ha(monkeypatch):
    monkeypatch.setattr(R, "PRAZO_RESOLVER", 3)
    r = resolver("y'' = 6 y^2")
    assert r.label == "sem solução encontrada"
    assert linha(r, "tipo") == R.NENHUMA
    assert r.payload is None
    assert any("korvin" in b for b in r.blocked_by)


def test_o_bug_do_riccati_vira_motivo_e_nao_silencio():
    """classify_ode anuncia '1st_rational_riccati' para y' = y² + x, e o solver
    quebra com TypeError quando NÃO há solução racional. A equação é a forma de
    Riccati de Airy (y = -u'/u dá u'' + xu = 0), que não tem solução
    liouvilliana: não há o que achar, e o SymPy cai em vez de dizer isso."""
    r = resolver("y' = y^2 + x")
    assert r.label == "sem solução encontrada"
    assert "TypeError" in linha(r, "motivo")


def test_solucao_nao_conferida_nao_se_apresenta():
    """O caso que importa: o solver devolveu algo e a substituição não
    confirmou. A resposta existe, e não vale como conclusão."""
    r = resolver(r"y' = \frac{1}{x + y^2}")
    assert r.provenance == Provenance.UNSOURCED
    assert r.presentable is False
    assert r.payload is not None
    assert r.blocked_by


# ------------------------------------------------------------- recusas

def test_recusa_o_que_nao_e_equacao_diferencial():
    with pytest.raises(ValueError, match="não é equação diferencial"):
        resolver("x^2 + 1 = 0")


def test_recusa_sistema():
    d = doc()
    d.function("z")
    with pytest.raises(ValueError, match="sistema"):
        R.resolver(d.read("y' + z' = 0"))


def test_nao_recusa_mais_derivadas_parciais():
    """Recusava com "o pdsolve do SymPy resolve muito pouco delas" — verdade
    que não justificava a recusa: resolver pouco não é resolver nada, e quem
    decide se o pouco serve é quem escreveu a equação."""
    d = sucuri.Document()
    d.function("u(t,x)")
    r = R.resolver(d.read(r"\partial_t u = \partial_x u"))
    assert linha(r, "espécie") == "parcial"


# ------------------------------------------------------------- padrões

def test_padroes_mostram_a_maquina_por_dentro():
    """classify_ode devolve uma LISTA DE PADRÕES, não um procedimento de
    decisão — e ter padrão não garante resposta: y'' = 6y² tem padrão e não
    termina."""
    r = R.classificar(doc().read("y'' = x y"))
    padroes = [v for k, v in r.rows if k == "padrão"]
    assert "2nd_linear_airy" in padroes
    assert r.provenance == Provenance.INAPPLICABLE

    r2 = R.classificar(doc().read("y'' = 6 y^2"))
    assert [v for k, v in r2.rows if k == "padrão"]


# ------------------------------------------------------------ registro

def test_o_modulo_carrega_pelo_nome():
    m = modules.load("resolver")
    assert set(m.operations) == {"resolver", "padrões", "separar", "conferir"}
    assert "resolver" in modules.CONHECIDOS


# ----------------------------------------------------- equações a derivadas parciais

def docp():
    d = sucuri.Document()
    d.function("u(t,x)", "A(t)")
    return d


def test_a_incognita_de_varias_variaveis_vai_para_o_pdsolve():
    """Uma variável ou várias não é diferença de recusa, é de SOLVER.

    ∂u/∂t = A(t)u sai como F(x)·exp(∫A dt): a "constante" de integração é uma
    função arbitrária de x, que é o que ela é numa EDP. O dsolve recusava com
    "only work with functions of one variable" — e o módulo dava isso como
    "sem solução encontrada", que era falso.
    """
    r = R.resolver(docp().read(r"\frac{\partial u}{\partial t} = A u"))
    assert linha(r, "espécie") == "parcial"
    assert linha(r, "tipo") == R.FECHADA
    assert r.provenance == Provenance.ESTABLISHED
    assert "resto 0" in linha(r, "conferência")
    assert r.payload.rhs.has(sp.Function("F")(sp.Symbol("x")))


def test_a_ordinaria_continua_no_dsolve():
    r = resolver("y'' + y = 0")
    assert linha(r, "espécie") == "ordinária"
    assert r.provenance == Provenance.ESTABLISHED


def test_a_edp_que_o_pdsolve_nao_resolve_falha_honestamente():
    """O pdsolve resolve bem menos do que o dsolve. A equação da onda ele não
    resolve — e dizer isso é a resposta, não um defeito."""
    d = sucuri.Document()
    d.function("u(t,x)")
    r = R.resolver(d.read(
        r"\frac{\partial^2 u}{\partial t^2} = \frac{\partial^2 u}{\partial x^2}"))
    assert r.label == "sem solução encontrada"
    assert any("korvin" in b for b in r.blocked_by)


def test_o_codigo_exportado_de_uma_edp_usa_pdsolve():
    from sucuri.caderno import Caderno

    c = Caderno()
    c.executar("u = u(t,x)")
    c.executar("A = A(t)")
    c.executar(r"\frac{\partial u}{\partial t} = A u")
    codigo = c.executar("exportar(eq1)").to_dict()["codigo"]
    assert "pdsolve(eq1, u(t, x))" in codigo
    assert "checkpdesol" in codigo

    escopo = {}
    exec(codigo, escopo)                                # noqa: S102
    assert escopo["solucao"].rhs.has(sp.Function("F"))


# ------------------------------------------------- a equação da onda

def onda():
    d = sucuri.Document()
    d.function("u(t,x)", "F(z)", "G(z)")
    d.variable("c")
    return d


def test_o_pdsolve_nao_resolve_a_onda_mas_o_sympy_separa():
    """"O SymPy não resolve a equação da onda" é meia verdade: o pdsolve não
    resolve, e ele é só um dos caminhos. pde_separate_mul separa, e o dsolve
    resolve cada pedaço — é a via clássica, e ela está lá."""
    r = R.separar(onda().read(
        r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}"))
    chaves = {k for k, _ in r.rows}
    assert "equação em t" in chaves and "equação em x" in chaves
    assert linha(r, "ansatz") == "u(t, x) = T(t) · X(x)"


def test_separar_nao_se_apresenta_como_solucao():
    """Separar SUPÕE que a solução é um produto, e a suposição é uma restrição:
    o que sai são os modos, e a solução geral é a superposição deles — que a
    separação não prova ser completa."""
    r = R.separar(onda().read(
        r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}"))
    assert r.provenance == Provenance.INAPPLICABLE
    assert any("não resolve a equação" in b for b in r.blocked_by)


def test_separar_recusa_equacao_ordinaria():
    with pytest.raises(ValueError, match="uma variável só"):
        R.separar(doc().read("y'' + y = 0"))


def test_dalembert_se_confere():
    """O SymPy não resolve a onda, mas CONFERE a solução de d'Alembert — e
    conferir é meia matemática: a que separa uma resposta de um palpite."""
    d = onda()
    eq = d.read(r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}")
    candidata = d.read(r"u = F(x - c t) + G(x + c t)")
    r = R.conferir(eq, candidata)
    assert r.provenance == Provenance.ESTABLISHED
    assert "resto 0" in linha(r, "conferência")


def test_candidata_errada_nao_se_apresenta():
    d = onda()
    eq = d.read(r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}")
    errada = d.read(r"u = F(x - c t) + x^2 t")
    r = R.conferir(eq, errada)
    assert r.provenance == Provenance.UNSOURCED
    assert r.presentable is False


def test_nao_conferir_e_nao_poder_conferir_sao_desfechos_diferentes():
    """"Não conferiu" diz algo sobre a CANDIDATA; "não deu para conferir" diz
    algo sobre o CONFERIDOR. Chamar a segunda de primeira é acusar sem prova.
    """
    d = onda()
    eq = d.read(r"\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}")

    errada = R.conferir(eq, d.read(r"u = F(x - c t) + x^2 t"))
    assert errada.label == "candidata NÃO verificada"
    assert any("não satisfaz a equação" in b for b in errada.blocked_by)

    # uma candidata que o checkpdesol não sabe testar
    class Impossivel:
        pending = ()
        def to_sympy(self):
            import sympy as sp
            t, k = sp.symbols("t k")
            T = sp.Function("T")
            return sp.Eq(sp.Derivative(T(t), (t, 2)), k * T(t))

    indeciso = R.conferir(eq, Impossivel())
    assert indeciso.label == "não deu para conferir"
    assert any("só sobre o conferidor" in b for b in indeciso.blocked_by)
    # os dois seguem não apresentáveis: nenhum é conclusão
    assert errada.presentable is False and indeciso.presentable is False
