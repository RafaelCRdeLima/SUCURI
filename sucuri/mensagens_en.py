"""As mensagens do motor em inglês: {molde em português: molde em inglês}.

Gerado de `tools/extrair_mensagens.py` e traduzido; `tests/test_idioma.py` quebra
se aparecer mensagem nova sem tradução. `{0}`, `{1}`… são os valores
interpolados, na ordem em que aparecem no molde em português."""

EN = {
    # sucuri/__init__.py:39
    "primes deve ser 'derivative', 'symbol' ou None":
        "primes must be 'derivative', 'symbol' or None",
    # sucuri/ambiguity.py:215
    'derivada {0}de ordem {1} de {2} em relação a {3}':
        '{0}derivative of order {1} of {2} with respect to {3}',
    # sucuri/ambiguity.py:221
    'fração literal dos símbolos d, {0} e d{1}':
        'literal fraction of the symbols d, {0} and d{1}',
    # sucuri/ambiguity.py:236
    'derivada temporal de ordem {0} de {1}':
        'time derivative of order {0} of {1}',
    # sucuri/ambiguity.py:238
    'apenas um acento sobre {0}; o símbolo é {1}':
        'just an accent on {0}; the symbol is {1}',
    # sucuri/ambiguity.py:246
    'derivada parcial de {0} em relação a {1}':
        'partial derivative of {0} with respect to {1}',
    # sucuri/ambiguity.py:271
    'derivada de ordem {0} de ({1}){2}':
        'derivative of order {0} of ({1}){2}',
    # sucuri/ambiguity.py:273
    'as linhas são decoração; o grupo é ({0})':
        'the primes are decoration; the group is ({0})',
    # sucuri/ambiguity.py:296
    'derivada de ordem {0} de {1}{2}':
        'derivative of order {0} of {1}{2}',
    # sucuri/ambiguity.py:298
    'símbolo chamado {0}{1}{2}':
        'symbol named {0}{1}{2}',
    # sucuri/ambiguity.py:308
    '{0} multiplicando o parêntese':
        '{0} multiplying the parenthesis',
    # sucuri/ambiguity.py:315
    'o número de Euler, 2,71828…':
        "Euler's number, 2.71828…",
    # sucuri/ambiguity.py:316
    'um símbolo chamado e':
        'a symbol named e',
    # sucuri/caderno.py:1013
    'o Ricci é uma contração do Riemann, com a mesma letra: declare antes {0} = riemann(eq)':
        'Ricci is a contraction of Riemann, with the same letter: declare {0} = riemann(eq) first',
    # sucuri/caderno.py:1027
    '; e {0}, sem índice, é g^{{μν}}{1}_{{μν}}':
        '; and {0}, with no index, is g^{{μν}}{1}_{{μν}}',
    # sucuri/caderno.py:1029
    '; {0} sem índice, o escalar, pede a métrica declarada':
        '; {0} with no index, the scalar, requires the declared metric',
    # sucuri/caderno.py:1032
    '{0}_{{μν}} = {1}{2}({3}), contraído como em {4}':
        '{0}_{{μν}} = {1}{2}({3}), contracted as in {4}',
    # sucuri/caderno.py:1034
    '. Ao simplificar, os dois viram contrações do Riemann, e voltam':
        '. On simplifying, both become contractions of Riemann, and come back',
    # sucuri/caderno.py:1049
    'a identidade sem termo de torção pede ∇ sem torção: declare \\nabla = levi-civita antes':
        'the identity without a torsion term requires a torsion-free ∇: declare \\nabla = levi-civita first',
    # sucuri/caderno.py:1061
    '{0} é o Riemann de ∇, na convenção de {1}: [∇_μ, ∇_ν]V^ρ = {2}{3}({4}) V^σ. Ao simplificar, todo comutador ∇∇ vira curvatura':
        '{0} is the Riemann of ∇, in the convention of {1}: [∇_μ, ∇_ν]V^ρ = {2}{3}({4}) V^σ. On simplifying, every ∇∇ commutator becomes curvature',
    # sucuri/caderno.py:1090
    'as coordenadas declaram um espaço de dimensão {0}, e aqui os índices são de dimensão {1}':
        'the coordinates declare a space of dimension {0}, and here the indices are of dimension {1}',
    # sucuri/caderno.py:1099
    ' de um espaço de dimensão {0}':
        ' of a space of dimension {0}',
    # sucuri/caderno.py:1103
    'um espaço tem uma métrica: declare um nome só':
        'a space has one metric: declare a single name',
    # sucuri/caderno.py:1107
    '{0} é a métrica do espaço — do tipo (0,2), e é ela que baixa e levanta índice':
        '{0} is the metric of the space — of type (0,2), and it is what lowers and raises indices',
    # sucuri/caderno.py:1112
    '⋆⋆ = (−1)^{p(n−p)+s}: o sinal pede a assinatura. Declare antes g = métrica(-,+,+,+), ou a que for':
        '⋆⋆ = (−1)^{p(n−p)+s}: the sign requires the signature. Declare g = metric(-,+,+,+) first, or whichever it is',
    # sucuri/caderno.py:1117
    '{0} é o dual de Hodge, em dimensão {1} com {2} sinal(is) negativo(s): ⋆⋆ = (−1)^(p({3}−p)+{4}) numa p-forma, α∧⋆β = β∧⋆α, e a orientação não precisa ser dita — ela troca o sinal de ⋆, e não o de ⋆⋆':
        '{0} is the Hodge dual, in dimension {1} with {2} negative sign(s): ⋆⋆ = (−1)^(p({3}−p)+{4}) on a p-form, α∧⋆β = β∧⋆α, and the orientation need not be given — it flips the sign of ⋆, not that of ⋆⋆',
    # sucuri/caderno.py:1124
    'a delta é uma só: declare um nome':
        'there is only one delta: declare one name',
    # sucuri/caderno.py:1126
    '{0}^μ_ν é a delta de Kronecker — a identidade: {1}^μ_ν A^ν vira A^μ ao simplificar, e {2}^μ_μ vira a dimensão':
        '{0}^μ_ν is the Kronecker delta — the identity: {1}^μ_ν A^ν becomes A^μ on simplifying, and {2}^μ_μ becomes the dimension',
    # sucuri/caderno.py:1131
    '∇ é a conexão de Levi-Civita: ∇g = 0, e sem torção — ∇_μ∇_ν φ = ∇_ν∇_μ φ num escalar. Ao simplificar, ∇g e ∇ε (tensor) viram zero':
        '∇ is the Levi-Civita connection: ∇g = 0, and torsion-free — ∇_μ∇_ν φ = ∇_ν∇_μ φ on a scalar. On simplifying, ∇g and ∇ε (tensor) become zero',
    # sucuri/caderno.py:1142
    'levi-civita(símbolo) ou levi-civita(tensor)? Os livros não fazem igual. O símbolo vale ±1 em toda carta e é uma densidade: não sobe nem desce com g. O tensor é √|g| vezes o símbolo, e sobe e desce com g. As duas leituras dão contas diferentes em contrair, e escolher seria adivinhar':
        'levi-civita(symbol) or levi-civita(tensor)? Books differ. The symbol is ±1 in every chart and is a density: it is not raised or lowered with g. The tensor is √|g| times the symbol, and is raised and lowered with g. The two readings give different results under contract, and choosing would be guessing',
    # sucuri/caderno.py:1151
    'ε tem um índice por dimensão, e a dimensão é {0}, uma letra':
        'ε has one index per dimension, and the dimension is {0}, a letter',
    # sucuri/caderno.py:1156
    '{0}: Levi-Civita como {1}; {2} índices, totalmente antissimétrico':
        '{0}: Levi-Civita as {1}; {2} indices, totally antisymmetric',
    # sucuri/caderno.py:1157
    'tensor — sobe e desce com g':
        'tensor — raised and lowered with g',
    # sucuri/caderno.py:1157
    'símbolo — ±1 em toda carta, não sobe nem desce com g':
        'symbol — ±1 in every chart, not raised or lowered with g',
    # sucuri/caderno.py:1164
    'det(g) é o determinante da métrica declarada: declare antes g = métrica, e um nome só para o determinante':
        'det(g) is the determinant of the declared metric: declare g = metric first, and a single name for the determinant',
    # sucuri/caderno.py:1176
    '{0}, sem índice, é det {1}_{{μν}}: ∂_λ {2} = {3} {4}^{{μν}} ∂_λ {5}_{{μν}} ao simplificar':
        '{0}, with no index, is det {1}_{{μν}}: ∂_λ {2} = {3} {4}^{{μν}} ∂_λ {5}_{{μν}} on simplifying',
    # sucuri/caderno.py:1181
    'as coordenadas são um nome só, com índice: x = coordenadas, e x^i é a i-ésima':
        'the coordinates are a single name, with an index: x = coordinates, and x^i is the i-th',
    # sucuri/caderno.py:1186
    '{0}^i são as coordenadas: ∂_j {1}^i = δ^i_j, e as derivadas segundas são zero. ∇ não se aplica — {2}^i não é campo vetorial':
        '{0}^i are the coordinates: ∂_j {1}^i = δ^i_j, and the second derivatives are zero. ∇ does not apply — {2}^i is not a vector field',
    # sucuri/caderno.py:1194
    '{0}(U,X)W é o operador de curvatura aplicado a W, e não produto — a leitura não fixa o sinal nem a ordem dos argumentos, que variam de livro para livro':
        '{0}(U,X)W is the curvature operator applied to W, not a product — the reading fixes neither the sign nor the order of the arguments, which vary from book to book',
    # sucuri/caderno.py:1201
    '{0} é o número de Euler':
        "{0} is Euler's number",
    # sucuri/caderno.py:1205
    '{0}: símbolo, não função — {1}(…) é produto':
        '{0}: a symbol, not a function — {1}(…) is a product',
    # sucuri/caderno.py:1239
    'daqui para baixo, {0} é função de {1}':
        'from here on, {0} is a function of {1}',
    # sucuri/caderno.py:1273
    'os rótulos da última tabela: ':
        'the labels of the last table: ',
    # sucuri/caderno.py:1277
    "não conheço '{0}' (tenho: {1})":
        "unknown '{0}' (I have: {1})",
    # sucuri/caderno.py:1281
    "'{0}' tem sítio ambíguo sem decisão; resolva antes de operar":
        "'{0}' has an undecided ambiguous site; resolve it before operating",
    # sucuri/caderno.py:1311
    'os dois lados coincidem, componente por componente':
        'the two sides agree, component by component',
    # sucuri/caderno.py:1316
    'componentes da diferença dos lados, não nulas':
        'components of the difference of the sides, nonzero',
    # sucuri/caderno.py:1317
    'componentes não nulas':
        'nonzero components',
    # sucuri/caderno.py:1325
    'base ortonormal de {0}':
        'orthonormal basis of {0}',
    # sucuri/caderno.py:1328
    'tétrada e^a = √|g_aa| dx^a; ω^a_b de de^a = −ω^a_b∧e^b, com ω_ab = −ω_ba — as duas conferidas —; Θ^a_b = dω^a_b + ω^a_c∧ω^c_b = ½R^a_bcd e^c∧e^d':
        'tetrad e^a = √|g_aa| dx^a; ω^a_b from de^a = −ω^a_b∧e^b, with ω_ab = −ω_ba — both checked —; Θ^a_b = dω^a_b + ω^a_c∧ω^c_b = ½R^a_bcd e^c∧e^d',
    # sucuri/caderno.py:1348
    '{0} precisa de duas: {1}(equação, candidata)':
        '{0} needs two: {1}(equation, candidate)',
    # sucuri/caderno.py:1432
    "'{0}' está entre as próprias hipóteses: isso não prova nada":
        "'{0}' is among the hypotheses themselves: that proves nothing",
    # sucuri/caderno.py:1454
    '; não precisou de {0}':
        '; {0} was not needed',
    # sucuri/caderno.py:1457
    'provado a partir de {0}, e do que vale para qualquer conexão e métrica — linearidade, Leibniz, simetria de g{1}':
        'proved from {0}, and from what holds for any connection and metric — linearity, Leibniz, symmetry of g{1}',
    # sucuri/caderno.py:1476
    'em dimensão {0}, com a métrica e cada tensor os mais gerais que as declarações permitem':
        'in dimension {0}, with the metric and each tensor as general as the declarations allow',
    # sucuri/caderno.py:1478
    ' (o Riemann com a primeira identidade de Bianchi)':
        ' (Riemann with the first Bianchi identity)',
    # sucuri/caderno.py:1480
    ': vale, componente por componente':
        ': holds, component by component',
    # sucuri/caderno.py:1481
    ': não vale — há um tensor e uma métrica em que falha':
        ': does not hold — there is a tensor and a metric for which it fails',
    # sucuri/caderno.py:1496
    'declare os índices, com a dimensão':
        'declare the indices, with the dimension',
    # sucuri/caderno.py:1501
    'em dimensão {0}: {1} componentes; as simetrias de {2} deixam {3}':
        'in dimension {0}: {1} components; the symmetries of {2} leave {3}',
    # sucuri/caderno.py:1504
    '; com ':
        '; with ',
    # sucuri/caderno.py:1505
    '. Nenhuma: só o tensor nulo tem essas propriedades':
        '. None: only the zero tensor has these properties',
    # sucuri/caderno.py:1522
    '{0} não tem índice, e o objetivo tem: as duas notações não se misturam numa prova — traduza com indices(eq)':
        '{0} has no index, and the goal does: the two notations do not mix in a proof — translate with indices(eq)',
    # sucuri/caderno.py:1535
    'provado a partir de ':
        'proved from ',
    # sucuri/caderno.py:1536
    ', e de {0} (teorema, da torção nula)':
        ', and from {0} (a theorem, from zero torsion)',
    # sucuri/caderno.py:1538
    ' — com ∇ delas, trocas de índice e produtos; e do que a forma canônica sabe: simetrias declaradas, [∇,∇] como curvatura, ∇g = 0':
        ' — with their ∇, index swaps and products; and from what the canonical form knows: declared symmetries, [∇,∇] as curvature, ∇g = 0',
    # sucuri/caderno.py:1542
    '; vale se ':
        '; holds if ',
    # sucuri/caderno.py:1543
    ' — a combinação divide por isso':
        ' — the combination divides by this',
    # sucuri/caderno.py:1571
    'declare {0} = tensor(0, 2, simétrico): é a perturbação da métrica':
        'declare {0} = tensor(0, 2, symmetric): it is the metric perturbation',
    # sucuri/caderno.py:1581
    "'{0}' não é a métrica declarada":
        "'{0}' is not the declared metric",
    # sucuri/caderno.py:1606
    'declare os índices antes (\\mu, \\nu, … = índices): é com eles que a tradução se escreve':
        'declare the indices first (\\mu, \\nu, … = indices): the translation is written with them',
    # sucuri/caderno.py:1639
    "'{0}' não é expressão tensorial: contrair baixa índice com a métrica, e aqui não há índice":
        "'{0}' is not a tensor expression: contract lowers indices with the metric, and there is no index here",
    # sucuri/caderno.py:1648
    'não há índice para baixar ou levantar: a métrica não aparece contraída com nada aqui':
        'there is no index to lower or raise: the metric is not contracted with anything here',
    # sucuri/caderno.py:1671
    'avaliar componentes precisa da métrica com componentes: declare `g = métrica(...)` com uma entrada por coordenada':
        'evaluating components needs the metric with components: declare `g = metric(...)` with one entry per coordinate',
    # sucuri/caderno.py:1741
    "'{0}' não aparece nas componentes de {1}":
        "'{0}' does not appear in the components of {1}",
    # sucuri/caderno.py:1763
    'escalar de Ricci de {0}':
        'Ricci scalar of {0}',
    # sucuri/caderno.py:177
    'nenhum índice {0}':
        'no index {0}',
    # sucuri/caderno.py:1777
    'todas as componentes são nulas':
        'all components are zero',
    # sucuri/caderno.py:1778
    '{0} de {1}: {2} componente(s) não nula(s)':
        '{0} of {1}: {2} nonzero component(s)',
    # sucuri/caderno.py:1812
    "'{0}' não é uma igualdade: não há o que resolver":
        "'{0}' is not an equation: there is nothing to solve",
    # sucuri/caderno.py:1817
    "'{0}' não tem incógnita":
        "'{0}' has no unknown",
    # sucuri/caderno.py:1821
    'raízes em {0}':
        'roots in {0}',
    # sucuri/caderno.py:1850
    '{0}({1}, solucao)   # confere por substituição':
        '{0}({1}, solucao)   # checks by substitution',
    # sucuri/caderno.py:361
    'uma 0-forma é uma função: não precisa declarar — todo símbolo que não é tensor já é escalar':
        'a 0-form is a function: no need to declare it — every symbol that is not a tensor is already a scalar',
    # sucuri/caderno.py:367
    '{0} é uma {1}-forma — um (0,{2}) {3}':
        '{0} is a {1}-form — a (0,{2}) {3}',
    # sucuri/caderno.py:369
    '. d, ∧, ι_X e ℒ_X agem nela; ι_Y ι_X ω = ω(X, Y), na convenção do determinante':
        '. d, ∧, ι_X and ℒ_X act on it; ι_Y ι_X ω = ω(X, Y), in the determinant convention',
    # sucuri/caderno.py:394
    'a declaração agora se escreve com parênteses: {0} = {1}({2}). O colchete ficou reservado a n-tupla.':
        'the declaration is now written with parentheses: {0} = {1}({2}). Square brackets are reserved for n-tuples.',
    # sucuri/caderno.py:454
    "'{0}' não é um símbolo: coordenada é um nome, não uma conta":
        "'{0}' is not a symbol: a coordinate is a name, not a computation",
    # sucuri/caderno.py:465
    'as coordenadas são {0} — variedade de dimensão {1}':
        'the coordinates are {0} — manifold of dimension {1}',
    # sucuri/caderno.py:478
    'declare as coordenadas antes da métrica: componente sem coordenada não diz de quê é componente':
        'declare the coordinates before the metric: a component without coordinates does not say what it is a component of',
    # sucuri/caderno.py:507
    '{0} é a métrica em ({1}), diagonal, com {2} componentes':
        '{0} is the metric in ({1}), diagonal, with {2} components',
    # sucuri/caderno.py:519
    '{0} é a métrica em ({1}), ':
        '{0} is the metric in ({1}), ',
    # sucuri/caderno.py:557
    'o elemento de linha tem de ser quadrático nos d das coordenadas ({0}); sobrou {1}':
        'the line element must be quadratic in the d of the coordinates ({0}); {1} is left over',
    # sucuri/caderno.py:567
    'dada pelo elemento de linha':
        'given by the line element',
    # sucuri/caderno.py:578
    "induzida(g, …) começa pela métrica de onde se puxa — '{0}' não é métrica com componentes":
        "induced(g, …) starts with the metric being pulled back — '{0}' is not a metric with components",
    # sucuri/caderno.py:583
    'declare as coordenadas novas antes — x = coordenadas(u, v): a métrica induzida vive nelas':
        'declare the new coordinates first — x = coordinates(u, v): the induced metric lives in them',
    # sucuri/caderno.py:599
    'o pull-back de {0} por ({1})':
        'the pull-back of {0} by ({1})',
    # sucuri/caderno.py:609
    'declare as coordenadas antes: as componentes são numa carta':
        'declare the coordinates first: components are in a chart',
    # sucuri/caderno.py:653
    '{0} = {1} — uma {2}-forma na carta ({3})':
        '{0} = {1} — a {2}-form in the chart ({3})',
    # sucuri/caderno.py:664
    "não conheço a forma '{0}' (tenho: {1})":
        "unknown form '{0}' (I have: {1})",
    # sucuri/caderno.py:685
    "não conheço o campo '{0}'":
        "unknown field '{0}'",
    # sucuri/caderno.py:696
    ') — uma {0}-forma':
        ') — a {0}-form',
    # sucuri/caderno.py:703
    "não conheço o campo '{0}' (tenho: {1})":
        "unknown field '{0}' (I have: {1})",
    # sucuri/caderno.py:717
    '{0} restrito, na carta de {1} — e registrado com o mesmo nome':
        '{0} restricted, in the chart of {1} — and registered under the same name',
    # sucuri/caderno.py:723
    '{0} campos de Killing independentes com componentes polinomiais de grau ≤ {1} na carta ({2})':
        '{0} independent Killing fields with polynomial components of degree ≤ {1} in the chart ({2})',
    # sucuri/caderno.py:730
    'ℒ_{0} g = 0: {1} é de Killing':
        'ℒ_{0} g = 0: {1} is Killing',
    # sucuri/caderno.py:731
    'ℒ_{0} g ≠ 0: {1} não é de Killing':
        'ℒ_{0} g ≠ 0: {1} is not Killing',
    # sucuri/caderno.py:746
    'as primeiras e as segundas derivadas covariantes, na base coordenada':
        'the first and second covariant derivatives, in the coordinate basis',
    # sucuri/caderno.py:769
    "não conheço a métrica '{0}' (tenho: {1})":
        "unknown metric '{0}' (I have: {1})",
    # sucuri/caderno.py:788
    'as equações de Euler–Lagrange de ∫ g(ẋ,ẋ) dλ são −2g_ab vezes estas: conferido':
        'the Euler–Lagrange equations of ∫ g(ẋ,ẋ) dλ are −2g_ab times these: checked',
    # sucuri/caderno.py:790
    'geodésicas de {0}, com parâmetro afim λ':
        'geodesics of {0}, with affine parameter λ',
    # sucuri/caderno.py:793
    'as equações das geodésicas, uma por coordenada, e o que se conserva ao longo delas: g(ẋ, ẋ), pelo parâmetro ser afim, e g(∂_k, ẋ) para cada coordenada de que a métrica não depende':
        'the geodesic equations, one per coordinate, and what is conserved along them: g(ẋ, ẋ), since the parameter is affine, and g(∂_k, ẋ) for each coordinate the metric does not depend on',
    # sucuri/caderno.py:807
    'L = g_φφ φ̇ e κ = g(ẋ,ẋ): κ = −1, 0, 1 para tipo tempo, nula, tipo espaço (na assinatura da métrica)':
        "L = g_φφ φ̇ and κ = g(ẋ,ẋ): κ = −1, 0, 1 for timelike, null, spacelike (in the metric's signature)",
    # sucuri/caderno.py:821
    'órbitas geodésicas de {0}':
        'geodesic orbits of {0}',
    # sucuri/caderno.py:822
    'por quadratura: as duas quantidades conservadas dão dφ/dr, e a substituição dv = √|g_rr|/g_φφ dr reduz a integral a uma forma elementar':
        'by quadrature: the two conserved quantities give dφ/dr, and the substitution dv = √|g_rr|/g_φφ dr reduces the integral to an elementary form',
    # sucuri/caderno.py:852
    'elemento de volume':
        'volume element',
    # sucuri/caderno.py:855
    '∫ √|det g| nos limites dados; o elemento sem módulo foi conferido positivo no domínio':
        '∫ √|det g| over the given limits; the element without absolute value was checked positive on the domain',
    # sucuri/caderno.py:871
    'a ordem é um número inteiro':
        'the order is an integer',
    # sucuri/caderno.py:897
    'lorentziana, mas qual? (−,+,+,+) e (+,−,−,−) são as duas em uso, e contas como εε e g(U,U) mudam de sinal entre elas. Escreva os sinais: g = métrica(-,+,+,+)':
        'Lorentzian, but which? (−,+,+,+) and (+,−,−,−) are both in use, and computations like εε and g(U,U) change sign between them. Write the signs: g = metric(-,+,+,+)',
    # sucuri/caderno.py:902
    'a assinatura tem um sinal por dimensão, e a dimensão é {0}, uma letra':
        'the signature has one sign per dimension, and the dimension is {0}, a letter',
    # sucuri/caderno.py:912
    'a assinatura tem {0} sinais, e os índices são de um espaço de dimensão {1}':
        'the signature has {0} signs, and the indices are of a space of dimension {1}',
    # sucuri/caderno.py:924
    '{0} é a métrica do espaço, de assinatura ({1}) — {2} sinal(is) negativo(s), e é isso que decide o sinal de εε':
        '{0} is the metric of the space, of signature ({1}) — {2} negative sign(s), and that is what decides the sign of εε',
    # sucuri/caderno.py:927
    '; e constante — carta cartesiana, ou inercial: ∂g = 0':
        '; and constant — Cartesian, or inertial, chart: ∂g = 0',
    # sucuri/caderno.py:944
    'em LaTeX, {0} são {1} letras multiplicadas ({2}), e nunca seria lido como um tensor só. Use uma letra ({3}) ou um comando (\\{4})':
        'in LaTeX, {0} is {1} multiplied letters ({2}), and would never be read as a single tensor. Use one letter ({3}) or a command (\\{4})',
    # sucuri/caderno.py:961
    '; simétrico — trocar dois slots não muda nada':
        '; symmetric — swapping two slots changes nothing',
    # sucuri/caderno.py:963
    '; antissimétrico — trocar dois slots troca o sinal, e slot repetido dá zero':
        '; antisymmetric — swapping two slots flips the sign, and a repeated slot gives zero',
    # sucuri/caderno.py:966
    '; com as simetrias do Riemann — antissimétrico em cada par, simétrico na troca dos pares. A identidade cíclica não entra: é teorema, e pede torção nula':
        '; with the symmetries of Riemann — antisymmetric in each pair, symmetric under exchange of the pairs. The cyclic identity is not included: it is a theorem, and requires zero torsion',
    # sucuri/caderno.py:974
    '{0} é tensor do tipo ({1},{2}): recebe {3} e {4} — {5}, {6}{7}':
        '{0} is a tensor of type ({1},{2}): it takes {3} and {4} — {5}, {6}{7}',
    # sucuri/caderno.py:999
    '{0} são os símbolos de Christoffel de ∇, na convenção de {1}: ∇_μ V^ν = ∂_μ V^ν + {2}({3}) V^λ. expandir(eq) abre ∇ em ∂ e {4}; expandir(eq, g), com Levi-Civita, escreve {5} pela métrica':
        '{0} are the Christoffel symbols of ∇, in the convention of {1}: ∇_μ V^ν = ∂_μ V^ν + {2}({3}) V^λ. expand(eq) opens ∇ into ∂ and {4}; expand(eq, g), with Levi-Civita, writes {5} in terms of the metric',
    # sucuri/campos.py:143
    '{0} não é induzida: restringir pede a métrica de induzida(g, …)':
        '{0} is not induced: restrict requires the metric from induced(g, …)',
    # sucuri/campos.py:147
    '{0} tem de estar na carta de {1}':
        '{0} must be in the chart of {1}',
    # sucuri/campos.py:162
    '{0} não é tangente à subvariedade: tem componente normal':
        '{0} is not tangent to the submanifold: it has a normal component',
    # sucuri/campos.py:30
    '{0} tem {1} componentes e a carta tem {2} coordenadas':
        '{0} has {1} components and the chart has {2} coordinates',
    # sucuri/campos.py:49
    '{0} está na carta ({1}) e a métrica em ({2}): as duas têm de ser a mesma':
        '{0} is in the chart ({1}) and the metric in ({2}): the two must be the same',
    # sucuri/campos.py:55
    'os dois campos têm de estar na mesma carta':
        'the two fields must be in the same chart',
    # sucuri/cartan.py:172
    'todas as componentes nulas':
        'all components zero',
    # sucuri/cartan.py:53
    'a base ortonormal automática é para métrica diagonal: e^a = √|g_aa| dx^a':
        'the automatic orthonormal basis is for a diagonal metric: e^a = √|g_aa| dx^a',
    # sucuri/cartan.py:93
    'a primeira equação de estrutura não fechou — defeito do motor, e não resposta':
        'the first structure equation did not close — an engine defect, not an answer',
    # sucuri/cartan.py:98
    'ω_ab não saiu antissimétrica — defeito do motor':
        'ω_ab did not come out antisymmetric — an engine defect',
    # sucuri/christoffel.py:182
    'para abrir ∇ é preciso dizer o que Γ é: escreva a definição ∇_μ V^ν = ∂_μ V^ν + Γ^ν{}_{μλ} V^λ e declare \\Gamma = christoffel(eq)':
        'to open ∇ you must say what Γ is: write the definition ∇_μ V^ν = ∂_μ V^ν + Γ^ν{}_{μλ} V^λ and declare \\Gamma = christoffel(eq)',
    # sucuri/christoffel.py:214
    'Γ só se escreve pela métrica para a conexão de Levi-Civita, e com a métrica declarada: \\nabla = levi-civita e g = métrica':
        'Γ is written in terms of the metric only for the Levi-Civita connection, and with the metric declared: \\nabla = levi-civita and g = metric',
    # sucuri/christoffel.py:74
    'a definição tem de ter a forma ∇_μ V^ν = ∂_μ V^ν + ':
        'the definition must have the form ∇_μ V^ν = ∂_μ V^ν + ',
    # sucuri/christoffel.py:75
    '(ν, μ, λ em alguma ordem) V^λ — ∇ num vetor de um lado; do outro, a derivada parcial e ':
        '(ν, μ, λ in some order) V^λ — ∇ on a vector on one side; on the other, the partial derivative and ',
    # sucuri/christoffel.py:76
    ' contraído com o mesmo vetor':
        ' contracted with the same vector',
    # sucuri/conexao.py:343
    "{0}: '{1}' não foi declarado. Se é um vetor, declare {2} = tensor(1,0){3}":
        "{0}: '{1}' was not declared. If it is a vector, declare {2} = tensor(1,0){3}",
    # sucuri/conexao.py:346
    "{0}: '{1}' foi declarado do tipo ({2},{3}), e aqui é preciso um VETOR, do tipo (1,0)":
        "{0}: '{1}' was declared of type ({2},{3}), and a VECTOR, of type (1,0), is needed here",
    # sucuri/conexao.py:349
    "{0}: '{1}' não é vetor pelo que foi declarado":
        "{0}: '{1}' is not a vector by what was declared",
    # sucuri/conexao.py:449
    '∇ com subscrito vazio':
        '∇ with empty subscript',
    # sucuri/conexao.py:464
    'colchete com {0} entradas: o de Lie tem duas, [U, X]':
        'bracket with {0} entries: the Lie bracket has two, [U, X]',
    # sucuri/conexao.py:473
    "'{0}(' sem ')'":
        "'{0}(' without ')'",
    # sucuri/conexao.py:477
    '{0} foi declarada curvatura, e R(U,X) recebe dois vetores; aqui há {1}':
        '{0} was declared curvature, and R(U,X) takes two vectors; here there are {1}',
    # sucuri/conexao.py:480
    '{0}({1}) sem o vetor sobre o qual age: R(U,X) é um operador, e sozinho não é vetor':
        '{0}({1}) without the vector it acts on: R(U,X) is an operator, and alone is not a vector',
    # sucuri/conexao.py:495
    'do tipo (0,{0})':
        'of type (0,{0})',
    # sucuri/conexao.py:496
    '{0} é {1}, e recebe {2} vetor(es); aqui recebe {3}':
        '{0} is {1}, and takes {2} vector(s); here it gets {3}',
    # sucuri/conexao.py:524
    '{0} sem operando: falta sobre o que age':
        '{0} without operand: nothing for it to act on',
    # sucuri/conexao.py:534
    "'{0}' sem '{1}' depois de {2}":
        "'{0}' without '{1}' after {2}",
    # sucuri/conexao.py:539
    "'\\left(' sem '\\right)' depois de {0}":
        "'\\left(' without '\\right)' after {0}",
    # sucuri/conexao.py:544
    'o que vem depois de {0} não é um operando reconhecível':
        'what follows {0} is not a recognizable operand',
    # sucuri/conexao.py:550
    "não está claro até onde {0} alcança em '{1}{2}…': escreva o operando entre parênteses, {3} ( … )":
        "it is unclear how far {0} reaches in '{1}{2}…': write the operand in parentheses, {3} ( … )",
    # sucuri/conexao.py:601
    '; se é índice, declare {nome} = índice. A tipografia é a mesma, e escolher entre as duas seria adivinhar':
        '; if it is an index, declare {nome} = indices. The typography is the same, and choosing between the two would be guessing',
    # sucuri/conexao.py:627
    '. Entre outras coisas o colchete é comutador, intervalo ou par, e escolher seria adivinhar':
        '. Among other things a bracket is a commutator, an interval or a pair, and choosing would be guessing',
    # sucuri/contagem.py:101
    'contar pede a dimensão em número, e ela é {0}: declare os índices com índices(4), por exemplo':
        'counting requires the dimension as a number, and it is {0}: declare the indices with indices(4), for example',
    # sucuri/contagem.py:131
    'a primeira identidade de Bianchi, R^ρ{}_{[σμν]} = 0 — teorema da torção nula':
        'the first Bianchi identity, R^ρ{}_{[σμν]} = 0 — a theorem of zero torsion',
    # sucuri/contagem.py:158
    "a equação tem '{0}', e a contagem é das componentes de {1}: as equações podem ter só {2}, a métrica, δ e ε":
        "the equation has '{0}', and the count is over the components of {1}: the equations may contain only {2}, the metric, δ and ε",
    # sucuri/contagem.py:163
    'cada termo tem de ser linear em {0}':
        'each term must be linear in {0}',
    # sucuri/contagem.py:194
    'em componentes, a dimensão tem de ser um número, e ela é {0}: declare índices(2), por exemplo':
        'in components, the dimension must be a number, and it is {0}: declare indices(2), for example',
    # sucuri/contagem.py:197
    'em componentes, a métrica tem de estar declarada':
        'in components, the metric must be declared',
    # sucuri/contagem.py:218
    'em componentes não há derivada: as componentes são números num ponto':
        'in components there is no derivative: components are numbers at a point',
    # sucuri/contagem.py:43
    "'{0}' não é tensor declarado: declare com {1} = tensor(M, N)":
        "'{0}' is not a declared tensor: declare it with {1} = tensor(M, N)",
    # sucuri/derivadas.py:142
    '{0}: um índice por derivada — escreva {1}_{2}{3}_{4}, que diz em que ordem se deriva':
        '{0}: one index per derivative — write {1}_{2}{3}_{4}, which says in what order to differentiate',
    # sucuri/derivadas.py:156
    '{0} sem operando: falta o que derivar':
        '{0} without operand: nothing to differentiate',
    # sucuri/derivadas.py:181
    'o operando {0} de {1} tem índice não declarado ({2}): declare-o, ou a derivada não tem sobre o que agir':
        'the operand {0} of {1} has an undeclared index ({2}): declare it, or the derivative has nothing to act on',
    # sucuri/derivadas.py:194
    'o que vem depois de {0} não é um operando':
        'what follows {0} is not an operand',
    # sucuri/derivadas.py:331
    'o índice da derivada aparece de novo no operando, na mesma posição — contrair é um em cima e um embaixo, como em ∂_μ A^μ':
        "the derivative's index appears again in the operand, in the same position — contracting means one up and one down, as in ∂_μ A^μ",
    # sucuri/derivadas.py:440
    "'{0}' sem índice, e {1} é o Riemann: se é o escalar de curvatura, defina o Ricci — {2}_{{μν}} = {3}^ρ{{}}_{{μρν}} — e declare {4} = ricci(eq)":
        "'{0}' without index, and {1} is the Riemann: if it is the scalar curvature, define the Ricci — {2}_{{μν}} = {3}^ρ{{}}_{{μρν}} — and declare {4} = ricci(eq)",
    # sucuri/derivadas.py:444
    "'{0}' sem índice, e {1} é tensor: se é o determinante da métrica, declare {2} = det({3})":
        "'{0}' without index, and {1} is a tensor: if it is the determinant of the metric, declare {2} = det({3})",
    # sucuri/derivadas.py:541
    '∇ de {0}^i: as coordenadas não são campo vetorial, e ∇ delas não tem sentido — escreva com ∂':
        '∇ of {0}^i: the coordinates are not a vector field, and their ∇ makes no sense — write it with ∂',
    # sucuri/derivadas.py:552
    '∂_j {0}^i = δ^i_j pede a delta ou a métrica declarada':
        '∂_j {0}^i = δ^i_j needs the delta or the metric declared',
    # sucuri/derivadas.py:696
    'a definição tem de ter a forma ∇_μ∇_ν V^ρ − ∇_ν∇_μ V^ρ = ± ':
        'the definition must have the form ∇_μ∇_ν V^ρ − ∇_ν∇_μ V^ρ = ± ',
    # sucuri/derivadas.py:698
    '(ρ, σ, μ, ν em alguma ordem) V^σ — o comutador num vetor de um lado, o Riemann contraído com o mesmo vetor do outro':
        '(ρ, σ, μ, ν in some order) V^σ — the commutator on a vector on one side, the Riemann contracted with the same vector on the other',
    # sucuri/document.py:1052
    '{0}(…): um vetor aplicado age sobre UMA função escalar, U(f); aqui recebe {1}':
        '{0}(…): an applied vector acts on ONE scalar function, U(f); here it receives {1}',
    # sucuri/document.py:1082
    'marcador interno do Sucuri vazou para a saída ({0}); isto é defeito do Sucuri, não da entrada':
        'an internal Sucuri marker leaked into the output ({0}); this is a Sucuri bug, not an input error',
    # sucuri/document.py:1287
    'derivada com índice (∂_μ, ∇_μ) ainda não atravessa a ponte: ela não é um fator multiplicando outro, é um objeto próprio, e montar um produto aqui pareceria certo':
        'an indexed derivative (∂_μ, ∇_μ) does not cross the bridge yet: it is not a factor multiplying another, it is an object of its own, and building a product here would look right',
    # sucuri/document.py:1408
    'Expression({0}) [{1} pendência(s)]\n':
        'Expression({0}) [{1} pending]\n',
    # sucuri/document.py:209
    '{0} foi declarada função de {1}':
        '{0} was declared a function of {1}',
    # sucuri/document.py:239
    "para ler {0} como derivada é preciso uma variável {1}: preencha '{2}' nas convenções do documento (ou {3}= na biblioteca)":
        "reading {0} as a derivative needs a {1} variable: fill in '{2}' in the document's conventions (or {3}= in the library)",
    # sucuri/document.py:255
    "'{0}' é a variável {1} do documento, e '{2}' seria a derivada dela em relação a si mesma. Se {3} é a função incógnita, declare outra variável {4} — t, por exemplo":
        "'{0}' is the document's {1} variable, and '{2}' would be its derivative with respect to itself. If {3} is the unknown function, declare another {4} variable — t, for instance",
    # sucuri/document.py:336
    'notação tensorial não é lida: ':
        'tensor notation is not read: ',
    # sucuri/document.py:337
    '. O parser trataria o índice de cima como EXPOENTE e descartaria o de baixo, devolvendo uma conta bem formada e errada. O SymPy tem tensores em sympy.tensor.tensor, mas o Sucuri ainda não faz essa ponte.':
        '. The parser would treat the upper index as an EXPONENT and drop the lower one, returning a well-formed, wrong computation. SymPy has tensors in sympy.tensor.tensor, but Sucuri does not bridge to them yet.',
    # sucuri/document.py:381
    '(…) e […] nos índices simetrizam com o fator 1/n!, como em Wald, MTW e Carroll: T_{(\\mu\\nu)} = ½(T_{\\mu\\nu} + T_{\\nu\\mu})':
        '(…) and […] on indices symmetrize with the factor 1/n!, as in Wald, MTW and Carroll: T_{(\\mu\\nu)} = ½(T_{\\mu\\nu} + T_{\\nu\\mu})',
    # sucuri/document.py:401
    "'{0}': a simetrização atravessa grupos de índice — de cima para baixo, ou com {{}} no meio. Trocar índice de cima com de baixo pede a métrica, e aí é outro tensor; escreva os índices simetrizados num grupo só":
        "'{0}': the symmetrization crosses index groups — from upper to lower, or with {{}} in between. Swapping an upper index with a lower one needs the metric, and then it is another tensor; write the symmetrized indices in a single group",
    # sucuri/document.py:408
    "'{0}' simetriza índices que não foram declarados — o parser descarta os parênteses, e T_{{(\\mu\\nu)}} vira T_{{\\mu\\nu}}. Declare os índices ({1} = índices)":
        "'{0}' symmetrizes undeclared indices — the parser drops the parentheses, and T_{{(\\mu\\nu)}} becomes T_{{\\mu\\nu}}. Declare the indices ({1} = indices)",
    # sucuri/document.py:418
    "'{0}' tem sobrescrito e subscrito nessa ordem, e o parser descarta o de baixo":
        "'{0}' has a superscript and a subscript in that order, and the parser drops the lower one",
    # sucuri/document.py:424
    'o índice \\{0} aparece em cima e embaixo (soma de Einstein)':
        'the index \\{0} appears up and down (Einstein summation)',
    # sucuri/document.py:430
    'há letra grega no expoente (':
        'there is a Greek letter in the exponent (',
    # sucuri/document.py:431
    '): se for índice contravariante, a leitura está errada — o parser trata como POTÊNCIA, e notação tensorial ainda não é lida':
        '): if it is a contravariant index, the reading is wrong — the parser treats it as a POWER, and tensor notation is not read yet',
    # sucuri/document.py:435
    'há índice grego em subscrito: ele vira parte do NOME do símbolo, então T_{\\mu\\nu} e T_{\\nu\\mu} são o mesmo símbolo para o SymPy':
        "there is a Greek index in a subscript: it becomes part of the symbol's NAME, so T_{\\mu\\nu} and T_{\\nu\\mu} are the same symbol to SymPy",
    # sucuri/document.py:458
    'notação não reconhecida pelo parser, degradada a símbolo: {0}. Reescreva em notação que o SymPy entenda, ou trate o nome como símbolo declarando-o.':
        'notation not recognized by the parser, degraded to a symbol: {0}. Rewrite it in notation SymPy understands, or treat the name as a symbol by declaring it.',
    # sucuri/document.py:523
    "para ler a linha como derivada é preciso uma variável independente: preencha 'Variável independente' nas convenções do documento (ou independent_variable= na biblioteca)":
        "reading the prime as a derivative needs an independent variable: fill in 'Independent variable' in the document's conventions (or independent_variable= in the library)",
    # sucuri/document.py:541
    'para ler o ponto como derivada é preciso uma variável temporal: passe wrt= ou crie o documento com time_variable=':
        'reading the dot as a derivative needs a time variable: pass wrt= or create the document with time_variable=',
    # sucuri/document.py:571
    'o documento já tem índices de dimensão {0}; não dá para misturar com {1}':
        'the document already has indices of dimension {0}; they cannot be mixed with {1}',
    # sucuri/document.py:63
    ' ou ':
        ' or ',
    # sucuri/document.py:66
    '{0} sítio(s) ambíguo(s) sem anotação:\n{1}\nAnote com .annotate(...) ou declare a convenção no documento.':
        '{0} ambiguous site(s) without annotation:\n{1}\nAnnotate with .annotate(...) or declare the convention in the document.',
    # sucuri/document.py:664
    "∀{0}: '{1}' foi declarado índice, e o ∀ aqui quantifica campos vetoriais":
        "∀{0}: '{1}' was declared an index, and the ∀ here quantifies over vector fields",
    # sucuri/document.py:669
    "∀{0}: '{1}' foi declarado do tipo ({2},{3}), e o ∀ aqui quantifica campos vetoriais":
        "∀{0}: '{1}' was declared of type ({2},{3}), and the ∀ here quantifies over vector fields",
    # sucuri/document.py:759
    'levi-civita é (tensor) ou (símbolo)':
        'levi-civita is (tensor) or (symbol)',
    # sucuri/document.py:820
    '∂ é derivada parcial':
        '∂ is a partial derivative',
    # sucuri/document.py:889
    '∀ sem separador depois da lista: escreva \\forall A, B: … (ou \\colon, \\quad, \\;). Sem ele não se sabe onde a lista acaba — em \\forall W, R(U,X)W a vírgula separa nome ou encerra a lista?':
        '∀ without a separator after the list: write \\forall A, B: … (or \\colon, \\quad, \\;). Without it one cannot tell where the list ends — in \\forall W, R(U,X)W does the comma separate a name or close the list?',
    # sucuri/em_carta.py:115
    "'{0}' não tem componentes nesta carta: declare-o com campo(…), covetor(…) ou forma(…)":
        "'{0}' has no components in this chart: declare it with field(…), covector(…) or form(…)",
    # sucuri/em_carta.py:65
    'a métrica tem {0} coordenadas e os índices, dimensão {1}: declare índices({2})':
        'the metric has {0} coordinates and the indices dimension {1}: declare indices({2})',
    # sucuri/formas.py:322
    "potência de forma, '{0}': escreva o produto exterior com \\wedge":
        "power of a form, '{0}': write the exterior product with \\wedge",
    # sucuri/formas.py:345
    "'{0}' não é forma que eu saiba ler":
        "'{0}' is not a form I know how to read",
    # sucuri/formas.py:582
    '∧ sem forma à direita':
        '∧ without a form on the right',
    # sucuri/formas_carta.py:118
    'os termos têm graus diferentes: uma forma tem um grau só':
        'the terms have different degrees: a form has a single degree',
    # sucuri/formas_carta.py:133
    'sobrou um termo sem d das coordenadas: {0}':
        'a term without a coordinate differential is left over: {0}',
    # sucuri/formas_carta.py:212
    'o cobase ortonormal automático é para métrica diagonal':
        'the automatic orthonormal coframe is for a diagonal metric',
    # sucuri/geometria.py:260
    'não sei qual é a métrica: declare `g = métrica(componentes)` antes de avaliar componentes':
        'I do not know the metric: declare `g = metric(components)` before evaluating components',
    # sucuri/geometria.py:264
    'a métrica tem {0} coordenada(s) e os índices são de dimensão {1}: declare `índices({2})` para os dois falarem do mesmo espaço':
        'the metric has {0} coordinate(s) and the indices have dimension {1}: declare `indices({2})` so both speak of the same space',
    # sucuri/geometria.py:280
    "'{0}' tem {1} índices: por ora só sei dar componentes de vetor e da métrica":
        "'{0}' has {1} indices: for now I can only give components of a vector and of the metric",
    # sucuri/geometria.py:301
    'sei dar componentes de expressão com um índice livre; esta tem {0}':
        'I can give components of an expression with one free index; this one has {0}',
    # sucuri/geometria.py:377
    'as equações da ação e as dos Christoffel não coincidiram — defeito do motor':
        'the equations from the action and those from the Christoffels did not agree — an engine bug',
    # sucuri/geometria.py:383
    '∂/∂{0} é de Killing':
        '∂/∂{0} is Killing',
    # sucuri/geometria.py:406
    'faltam os limites de ':
        'missing the limits of ',
    # sucuri/geometria.py:417
    'o integrando √|det g| sem módulo fica negativo em parte do domínio: divida o domínio':
        'the integrand √|det g| without the absolute value becomes negative on part of the domain: split the domain',
    # sucuri/geometria.py:435
    'a métrica {0} tem {1} coordenadas ({2}), e foram dadas {3} expressões':
        'the metric {0} has {1} coordinates ({2}), and {3} expressions were given',
    # sucuri/geometria.py:459
    'órbitas pede uma métrica 2D diagonal':
        'orbits needs a diagonal 2D metric',
    # sucuri/geometria.py:462
    'nenhuma coordenada cíclica: a métrica depende das duas, e a quadratura pede uma de que ela não dependa':
        'no cyclic coordinate: the metric depends on both, and the quadrature needs one it does not depend on',
    # sucuri/geometria.py:65
    'a matriz da métrica tem de ser quadrada, simétrica, uma linha por coordenada':
        'the metric matrix must be square, symmetric, one row per coordinate',
    # sucuri/geometria.py:70
    '{0} coordenada(s) e {1} componente(s): a diagonal tem de ter uma entrada por coordenada':
        '{0} coordinate(s) and {1} component(s): the diagonal must have one entry per coordinate',
    # sucuri/interface/__main__.py:13
    'não abrir o navegador automaticamente':
        'do not open the browser automatically',
    # sucuri/interface/aplicacao.py:135
    'operação desconhecida: {0}':
        'unknown operation: {0}',
    # sucuri/interface/aplicacao.py:139
    'há sítios pendentes; resolva antes de operar':
        'there are pending sites; resolve them before operating',
    # sucuri/interface/servidor.py:114
    'Ctrl-C para encerrar.':
        'Ctrl-C to quit.',
    # sucuri/interface/sessao.py:278
    'há sítios pendentes; resolva antes de avaliar':
        'there are pending sites; resolve them before evaluating',
    # sucuri/interface/sessao.py:416
    '{0} foi declarada função de {1} só, e para função de uma variável ∂{2}/∂{3} é d{4}/d{5} — o mesmo objeto. Se {6} depende de mais variáveis, declare {7} = {8}(…) com todas.':
        '{0} was declared a function of {1} only, and for a function of one variable ∂{2}/∂{3} is d{4}/d{5} — the same object. If {6} depends on more variables, declare {7} = {8}(…) with all of them.',
    # sucuri/interface/sessao.py:539
    'leitura inválida: {0}':
        'invalid reading: {0}',
    # sucuri/modules/__init__.py:115
    'módulo {0} — {1}':
        'module {0} — {1}',
    # sucuri/modules/__init__.py:143
    'módulo desconhecido: {0}':
        'unknown module: {0}',
    # sucuri/modules/__init__.py:82
    '  — NÃO APRESENTÁVEL COMO CONCLUSÃO':
        '  — NOT PRESENTABLE AS A CONCLUSION',
    # sucuri/modules/korvin.py:100
    'condições necessárias de Kovacic':
        "Kovacic's necessary conditions",
    # sucuri/modules/korvin.py:125
    'não-integrabilidade hamiltoniana por Galois diferencial':
        'Hamiltonian non-integrability via differential Galois theory',
    # sucuri/modules/korvin.py:128
    "singularidades, ordens e expoentes de y'' = r y":
        "singularities, orders and exponents of y'' = r y",
    # sucuri/modules/korvin.py:130
    'condições de Kovacic':
        'Kovacic conditions',
    # sucuri/modules/korvin.py:131
    'as condições necessárias dos três casos':
        'the necessary conditions of the three cases',
    # sucuri/modules/korvin.py:134
    'veredito combinado, com a proveniência de cada critério':
        'combined verdict, with the provenance of each criterion',
    # sucuri/modules/korvin.py:50
    "esperava uma igualdade na forma y'' = r y; recebi {0}":
        "expected an equality of the form y'' = r y; got {0}",
    # sucuri/modules/korvin.py:55
    'esperava exatamente uma derivada no lado esquerdo':
        'expected exactly one derivative on the left-hand side',
    # sucuri/modules/korvin.py:59
    'esperava derivada de ordem 2; achei ordem {0}':
        'expected a derivative of order 2; found order {0}',
    # sucuri/modules/korvin.py:64
    'o lado direito não é da forma r(x) y':
        'the right-hand side is not of the form r(x) y',
    # sucuri/modules/korvin.py:82
    'esquema de Riemann':
        'Riemann scheme',
    # sucuri/modules/resolver.py:156
    'não deu tempo de conferir em {0} s':
        'no time to check within {0} s',
    # sucuri/modules/resolver.py:158
    'a conferência falhou: {0}':
        'the check failed: {0}',
    # sucuri/modules/resolver.py:164
    '{0} soluções substituídas: resto 0 em todas':
        '{0} solutions substituted: remainder 0 in all',
    # sucuri/modules/resolver.py:165
    'resto não nulo em {0} de {1}: {2}':
        'nonzero remainder in {0} of {1}: {2}',
    # sucuri/modules/resolver.py:169
    'substituída na equação: resto 0':
        'substituted into the equation: remainder 0',
    # sucuri/modules/resolver.py:170
    'substituída na equação: resto {0}':
        'substituted into the equation: remainder {0}',
    # sucuri/modules/resolver.py:173
    'não achar solução não é prova de que não existe; para essa outra pergunta, o módulo korvin':
        'not finding a solution is no proof that none exists; for that other question, the korvin module',
    # sucuri/modules/resolver.py:197
    'nenhum: o SymPy não tem por onde começar':
        'none: SymPy has nowhere to start',
    # sucuri/modules/resolver.py:199
    'sem solução encontrada':
        'no solution found',
    # sucuri/modules/resolver.py:227
    'série (não é solução fechada)':
        'series (not a closed-form solution)',
    # sucuri/modules/resolver.py:241
    'solução não confirmada':
        'solution not confirmed',
    # sucuri/modules/resolver.py:243
    'a substituição não devolveu zero; o que o solver achou não foi verificado':
        'the substitution did not return zero; what the solver found was not verified',
    # sucuri/modules/resolver.py:290
    'separar é para equação a derivadas parciais; {0} depende de uma variável só':
        'separate is for partial differential equations; {0} depends on a single variable',
    # sucuri/modules/resolver.py:302
    'o produto não separa esta equação; separar não é um método geral':
        'the product does not separate this equation; separation is not a general method',
    # sucuri/modules/resolver.py:315
    'equação em {0}':
        'equation in {0}',
    # sucuri/modules/resolver.py:317
    'solução em {0}':
        'solution in {0}',
    # sucuri/modules/resolver.py:321
    'não saiu: {0}':
        'did not come out: {0}',
    # sucuri/modules/resolver.py:323
    'separação de variáveis':
        'separation of variables',
    # sucuri/modules/resolver.py:326
    'isto não resolve a equação: separar SUPÕE que a solução é um produto. O que sai são os modos, e a solução geral é a superposição deles — que a separação não prova ser completa':
        'this does not solve the equation: separation ASSUMES the solution is a product. What comes out are the modes, and the general solution is their superposition — which separation does not prove complete',
    # sucuri/modules/resolver.py:342
    'a candidata precisa ser uma igualdade, como u = F(x - c t) + G(x + c t)':
        'the candidate must be an equality, such as u = F(x - c t) + G(x + c t)',
    # sucuri/modules/resolver.py:358
    'não deu para conferir':
        'could not check',
    # sucuri/modules/resolver.py:361
    'a conferência não pôde ser feita; isto não diz nada sobre a candidata, só sobre o conferidor':
        'the check could not be done; this says nothing about the candidate, only about the checker',
    # sucuri/modules/resolver.py:364
    'candidata NÃO verificada':
        'candidate NOT verified',
    # sucuri/modules/resolver.py:367
    'a substituição não devolveu zero: a candidata não satisfaz a equação':
        'the substitution did not return zero: the candidate does not satisfy the equation',
    # sucuri/modules/resolver.py:373
    'resolve a equação diferencial e diz que tipo de resposta é':
        'solves the differential equation and says what kind of answer it is',
    # sucuri/modules/resolver.py:376
    'dsolve com prazo, classificado e conferido por substituição':
        'dsolve with a time limit, classified and checked by substitution',
    # sucuri/modules/resolver.py:379
    'os métodos que o SymPy tentaria, antes de tentar':
        'the methods SymPy would try, before trying',
    # sucuri/modules/resolver.py:382
    'reduz uma EDP a ordinárias sob o ansatz de produto':
        'reduces a PDE to ODEs under the product ansatz',
    # sucuri/modules/resolver.py:385
    'a candidata satisfaz a equação? substitui e diz':
        'does the candidate satisfy the equation? substitutes and says',
    # sucuri/modules/resolver.py:62
    'não há derivada nenhuma: isto não é equação diferencial':
        'there is no derivative at all: this is not a differential equation',
    # sucuri/modules/resolver.py:67
    "a derivada não é de uma função incógnita. Declare a função — em y'' + y = 0, é preciso dizer que y é função de x":
        "the derivative is not of an unknown function. Declare the function — in y'' + y = 0, one must say that y is a function of x",
    # sucuri/modules/resolver.py:72
    'há mais de uma função incógnita ({0}): isto é um sistema, e este módulo resolve uma equação de cada vez':
        'there is more than one unknown function ({0}): this is a system, and this module solves one equation at a time',
    # sucuri/prazo.py:26
    'não terminou em {0} s':
        'did not finish within {0} s',
    # sucuri/prova.py:136
    "'{0}' não é escalar vezes vetor: tem {1} fatores vetoriais":
        "'{0}' is not a scalar times a vector: it has {1} vector factors",
    # sucuri/prova.py:143
    "'{0}' não é vetor declarado":
        "'{0}' is not a declared vector",
    # sucuri/prova.py:151
    "'{0}' não é campo vetorial":
        "'{0}' is not a vector field",
    # sucuri/prova.py:638
    'a igualdade já é falsa na leitura — os dois lados são diferentes e nada neles varia':
        'the equality is already false as read — the two sides differ and nothing in them varies',
    # sucuri/prova.py:766
    'a busca passou de {0} relações sem achar; não achar não é prova de que é falso':
        'the search went past {0} relations without finding one; not finding is no proof that it is false',
    # sucuri/prova.py:772
    ' Nenhuma hipótese fala de {0}.':
        ' No hypothesis mentions {0}.',
    # sucuri/prova.py:775
    'não achei combinação das hipóteses que dê isto.':
        'I found no combination of the hypotheses that gives this.',
    # sucuri/prova.py:776
    ' Não achar não é prova de que é falso: pode faltar hipótese, ou a prova pedir mais do que a linearidade e as hipóteses dão.':
        ' Not finding one is no proof that it is false: a hypothesis may be missing, or the proof may need more than linearity and the hypotheses give.',
    # sucuri/prova.py:932
    'as hipóteses com ∀ passaram de {0} instâncias sem achar; não achar não é prova de que é falso':
        'the ∀ hypotheses went past {0} instances without finding one; not finding is no proof that it is false',
    # sucuri/prova.py:955
    'defeito do Sucuri: coeficiente de combinação que não é número':
        'Sucuri bug: a combination coefficient that is not a number',
    # sucuri/prova.py:960
    'defeito do Sucuri: a combinação achada não confere (sobra {0})':
        'Sucuri bug: the combination found does not check out ({0} is left over)',
    # sucuri/prova_indices.py:481
    'não achei combinação das hipóteses que dê o objetivo — o que não prova que seja falso: a busca vai até ∇∇ das hipóteses e casa termo a termo, e pode faltar hipótese':
        'I found no combination of the hypotheses that gives the goal — which does not prove it false: the search goes up to ∇∇ of the hypotheses and matches term by term, and a hypothesis may be missing',
    # sucuri/prova_indices.py:546
    'a combinação achada não fecha ao conferir — defeito do motor, e não prova':
        'the combination found does not close when checked — an engine bug, and not a proof',
    # sucuri/prova_indices.py:569
    '{0} com {1} contraídos':
        '{0} with {1} contracted',
    # sucuri/ricci.py:56
    'a definição tem de ter a forma R_{μν} = ± R^ρ{}_{μρν} — o Ricci de um lado; do outro, o Riemann (declarado antes, com riemann(eq)) com um par de índices contraído':
        'the definition must have the form R_{μν} = ± R^ρ{}_{μρν} — the Ricci on one side; on the other, the Riemann (declared first, with riemann(eq)) with one pair of indices contracted',
    # sucuri/ricci.py:60
    'o Ricci é uma contração do Riemann: declare antes R = riemann(eq)':
        'the Ricci is a contraction of the Riemann: declare R = riemann(eq) first',
    # sucuri/tensores.py:165
    "'{0}' foi declarado do tipo ({1},{2}), que tem {3} índice(s), e aqui aparece com {4}":
        "'{0}' was declared of type ({1},{2}), which has {3} index(es), and appears here with {4}",
    # sucuri/tensores.py:170
    'foi declarado com {0}':
        'was declared with {0}',
    # sucuri/tensores.py:171
    'apareceu com {0}':
        'appeared with {0}',
    # sucuri/tensores.py:173
    "'{0}' {1} índice(s) e agora com {2}: um tensor tem um posto só":
        "'{0}' {1} index(es) and now with {2}: a tensor has a single rank",
    # sucuri/tensores.py:215
    ' — o Riemann com as simetrias é o (0,4), R_{abcd}':
        ' — the Riemann with these symmetries is the (0,4), R_{abcd}',
    # sucuri/tensores.py:217
    'simetria entre índice de cima e de baixo, num ({0},{1}), só existe depois de baixar um deles com a métrica — e aí é outro tensor. Declare a simetria no tipo com os índices todos do mesmo lado{2}':
        'a symmetry between an upper and a lower index, in a ({0},{1}), only exists after lowering one of them with the metric — and then it is another tensor. Declare the symmetry on the type with all indices on the same side{2}',
    # sucuri/tensores.py:222
    'com um slot só não há o que trocar':
        'with a single slot there is nothing to swap',
    # sucuri/tensores.py:224
    'as simetrias do Riemann são de quatro slots — dois pares antissimétricos que trocam entre si —, e aqui há {0}':
        'the Riemann symmetries are for four slots — two antisymmetric pairs that swap with each other — and here there are {0}',
    # sucuri/tensores.py:280
    '{0} foi declarado do tipo ({1},{2}) e aqui aparece como ({3},{4}): levantar ou baixar índice exige a métrica, e o Sucuri não a aplica sozinho':
        '{0} was declared of type ({1},{2}) and appears here as ({3},{4}): raising or lowering an index requires the metric, and Sucuri does not apply it on its own',
    # sucuri/tensores.py:291
    'a delta de Kronecker é δ^μ_ν, com um índice em cima e um embaixo; aqui tem {0} em cima e {1} embaixo. δ_{{μν}} só é tensor com a métrica — e aí é g_{{μν}}':
        'the Kronecker delta is δ^μ_ν, with one index up and one down; here it has {0} up and {1} down. δ_{{μν}} is a tensor only with the metric — and then it is g_{{μν}}',
    # sucuri/tensores.py:297
    'ε num espaço de dimensão {0} tem {1} índices; aqui tem {2}':
        'ε in a space of dimension {0} has {1} indices; here it has {2}',
    # sucuri/tensores.py:335
    "'{0}' dentro de '{1}' nos índices de {2}: simetrização aninhada não se lê de um jeito só":
        "'{0}' inside '{1}' in the indices of {2}: nested symmetrization has no single reading",
    # sucuri/tensores.py:343
    "'{0}' sem o '{1}' correspondente nos índices de {2}":
        "'{0}' without the matching '{1}' in the indices of {2}",
    # sucuri/tensores.py:347
    "barra aberta antes de '{0}' em {1}":
        "bar left open before '{0}' in {1}",
    # sucuri/tensores.py:353
    "'|' fora de (…) ou […] em {0}: a barra só exclui índice de uma simetrização":
        "'|' outside (…) or […] in {0}: the bar only excludes an index from a symmetrization",
    # sucuri/tensores.py:360
    'a simetrização em {0} junta índice de cima com de baixo — trocá-los pede a métrica, e aí é outro tensor':
        'the symmetrization in {0} mixes upper and lower indices — swapping them needs the metric, and then it is another tensor',
    # sucuri/tensores.py:367
    "'{0}' sem fechar nos índices de {1}":
        "unclosed '{0}' in the indices of {1}",
    # sucuri/tensores.py:371
    '{0}…{1} com {2} índice em {3}: não há o que trocar':
        '{0}…{1} with {2} index in {3}: there is nothing to swap',
    # sucuri/tensores.py:419
    'não sei qual é a métrica: declare `g = métrica` (ou `g = métrica(componentes)`) antes de contrair. Baixar índice é convenção da métrica, e não de um (0,2) qualquer':
        'I do not know the metric: declare `g = metric` (or `g = metric(components)`) before contracting. Lowering an index is a convention of the metric, not of an arbitrary (0,2)',
    # sucuri/tensores.py:438
    'o símbolo de Levi-Civita não sobe nem desce com a métrica: é ±1 em toda carta, uma densidade, e g_{μα}ε^{α…} não é ε_{μ…}. Para subir e descer com g, declare levi-civita(tensor)':
        'the Levi-Civita symbol is not raised or lowered with the metric: it is ±1 in every chart, a density, and g_{μα}ε^{α…} is not ε_{μ…}. To raise and lower with g, declare levi-civita(tensor)',
    # sucuri/tensores.py:655
    'os termos da soma têm índices livres diferentes. Some tensores de mesma valência: se um termo sobra com μ livre e o outro não, a igualdade não é uma igualdade de tensores':
        'the terms of the sum have different free indices. Add tensors of the same valence: if one term is left with μ free and the other is not, the equality is not an equality of tensors',
    # sucuri/traducao.py:105
    '{0}(U,X)W só se traduz com {1} também definido com índice — {2} = riemann(eq) —, que é de onde vêm o sinal e a ordem dos slots':
        '{0}(U,X)W translates only with {1} also defined with indices — {2} = riemann(eq) — which is where the sign and the slot order come from',
    # sucuri/traducao.py:116
    '{0}(U,X)W traduzido supondo {1}(U,X) = ∇_U∇_X − ∇_X∇_U − ∇_[U,X], sem torção — que é como a definição com índice o lê':
        '{0}(U,X)W translated assuming {1}(U,X) = ∇_U∇_X − ∇_X∇_U − ∇_[U,X], torsion-free — which is how the indexed definition reads it',
    # sucuri/traducao.py:158
    '∀ não se traduz: com índice, a identidade vale para todo vetor sem precisar dizer — traduza uma instância':
        '∀ does not translate: with indices, the identity holds for every vector without saying so — translate one instance',
    # sucuri/traducao.py:163
    'formas ainda não têm tradução para índices':
        'forms have no translation to indices yet',
    # sucuri/traducao.py:70
    "'{0}' não é escalar vezes vetor":
        "'{0}' is not a scalar times a vector",
    # sucuri/traducao.py:79
    'a ponte para índices conhece uma ∇ só: \\{0}{{\\nabla}} fica sem índice':
        'the bridge to indices knows a single ∇: \\{0}{{\\nabla}} stays without index',
    # sucuri/traducao.py:90
    '[X,Y] foi escrito com ∂: sem ∇ declarado sem torção, é a forma que vale em qualquer carta':
        '[X,Y] was written with ∂: without a declared torsion-free ∇, this is the form valid in any chart',
    # sucuri/traducao.py:98
    "'{0}' ainda não tem tradução para índices":
        "'{0}' has no translation to indices yet",
    # sucuri/tree.py:39
    'derivada de ordem {0} de {1} em {2}':
        'derivative of order {0} of {1} with respect to {2}',
    # sucuri/tree.py:42
    'derivada covariante na direção de {0}':
        'covariant derivative in the direction of {0}',
    # sucuri/tree.py:44
    'colchete de Lie':
        'Lie bracket',
    # sucuri/tree.py:49
    'função {0} aplicada a ({1})':
        'function {0} applied to ({1})',
    # pedaços curtos e rótulos
    '{0} = métrica({1})':
        '{0} = metric({1})',
    '{0} = forma({1})':
        '{0} = form({1})',
    'nenhuma hipótese':
        'no hypothesis',
    'pela ação':
        'from the action',
    'série(eq, variável, ordem)':
        'series(eq, variable, order)',
    'vale se':
        'holds if',
    'é índice':
        'is an index',
    'são índices':
        'are indices',
    'a métrica':
        'the metric',
    'sem operando':
        'without operand',
    'Variável independente':
        'Independent variable',
    'Variável temporal':
        'Time variable',
    'não encontrado':
        'not found',
    'sem fonte':
        'no source',
    'não aplicável':
        'not applicable',
    'forma fechada':
        'closed form',
    'série truncada':
        'truncated series',
    'relação implícita':
        'implicit relation',
    'padrões aplicáveis':
        'applicable patterns',
    'não separou':
        'did not separate',
    'padrão tentado':
        'pattern tried',
    'duas expressões':
        'two expressions',
    'símbolo {0}':
        'symbol {0}',
    'número {0}':
        'number {0}',
    '<{0} {1} em {2}: {3}>':
        '<{0} {1} at {2}: {3}>',
    ' avaliada em {0}':
        ' evaluated at {0}',
    ', avaliada em {0}':
        ', evaluated at {0}',
    '{0} aplicada ao argumento':
        '{0} applied to the argument',
    '{0} em componentes: {1}':
        '{0} in components: {1}',
    '{0}, na base coordenada':
        '{0}, in the coordinate basis',
    'nenhuma ainda':
        'none yet',
    ' — {0}, na base coordenada':
        ' — {0}, in the coordinate basis',
    'g^{ik}∇_i∇_k, componente por componente':
        'g^{ik}∇_i∇_k, component by component',
    'conserva-se ({0})':
        'conserved ({0})',
    "'{0}': escreva o limite como x = a .. b":
        "'{0}': write the limit as x = a .. b",
    ', na carta ({0})':
        ', in the chart ({0})',
    'em cima':
        'up',
    'nenhum ainda':
        'none yet',
    'Ricci na base':
        'Ricci in the basis',
    '{0} agindo sobre {1}':
        '{0} acting on {1}',
    'Sucuri em {0}':
        'Sucuri at {0}',
    '{0} em {1}':
        '{0} in {1}',
    '; depois ':
        '; then ',
    'curvatura {0} aplicada':
        'curvature {0} applied',
    '{0} é uma {1}-forma — um (0,{2})':
        '{0} is a {1}-form — a (0,{2})',
}
