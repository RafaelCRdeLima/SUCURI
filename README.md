# SUCURI

*SymPy Unified Compiler for Unambiguous Rendered Input.*

A symbolic environment in which the equation the user writes **is** a
manipulable object — and in which no ambiguity is guessed.

*[Leia em português](README.pt-BR.md)*

> **Two languages.** The interface has a PT/EN switch in the header (or open
> `caderno.html?lang=en`), and the engine's messages follow it. Commands have
> English names that work in either language — `g = metric(…)`,
> `\mu, \nu = indices`, `prove(eq3, eq1)`, `solve(eq1)`, `in_chart(eq2)`.
> The manual is `manual-en.html` in English and `manual.html` in Portuguese;
> the exercise book is `tutorial.html` in English and `apostila.html` in
> Portuguese.

## The problem it exists to solve

LaTeX is typography, not semantics. Handing LaTeX to a parser produces silent
errors. Measured in SymPy, with real equations:

| written | understood |
|---|---|
| `\varphi'' + 3\varphi\varphi' + \varphi^3` | `\varphi^3 + (\varphi + 3\varphi\varphi)` |
| `\frac{d^2 y}{dx^2}` | `d²·y / dx²`, symbols `d` and `dx` |
| `E^2 - f(m^2 + \ldots)` | `f` **applied**, not multiplying |
| `y'' = r y` | `y''` as a **symbol**, not a derivative |
| `\dot{x}` | **`Symbol('dot') × x`** — the dot became a multiplication |

None of these raises an exception. The parser returns a valid, wrong expression.

The last one is the most serious for the domain: all of Hamiltonian mechanics is
written with Newton's dots, and the parser turns them into a product by a symbol
called "dot".

The first row is the Riccati equation of Kovacic's case 2. Misreading it has
already cost a real project a false theorem.

## The principle

> **Ambiguity is not guessed: it is annotated.**

Sucuri scans the input, **locates** the ambiguous sites, and **refuses to
produce an expression** while any of them is unannotated. Once resolved
— by a declaration in the document or by the user's choice — the node **keeps**
the decision, and the ambiguity does not come back.

It is the same principle as KORVIN's provenance layer, applied to the input
instead of the criterion: nothing concludes from what has not been established.
(KORVIN is a separate program, for criteria on differential equations; it is not
on PyPI and not a dependency — the adapter `sucuri/modules/korvin.py` activates
only if it is installed.)

## The three layers

```
    view (LaTeX / MathML)
            ↕
    semantic tree  ←— the truth; the annotations live here
            ↕
    SymPy (engine)  +  domain modules (resolver, KORVIN, ...)
```

The view is disposable; the tree is not. Editing the view is editing the tree.

## The three states of a reading

The visual identity reserves amber for *ambiguity resolved by inference*,
and that is a state of its own in the engine:

| State | How | Color |
|---|---|---|
| **explicit** | annotation made for that site | green |
| **inferred** | document convention applied there | **amber** |
| **pending** | no reading defined | blocks |

The distinction is not cosmetic. A general convention — "prime is a derivative" —
can get nine sites right and the tenth wrong, and whoever declared it did not look
at each one. Amber says: it works, but nobody checked this case.

## The tables

`exemplos/tabelas/` pits the reader against real tables, downloaded from Wikipedia —
notation written by other people, for another purpose, which is the only honest
test of a notation reader.

```bash
python exemplos/tabelas/derivadas.py
python exemplos/tabelas/integrais.py
```

The scripts print their summaries in Portuguese (`provada`, `LIDA ERRADO`,
`não lida`, …).

A table of derivatives is proved by differentiating; a table of integrals is proved
**in reverse**, differentiating the right-hand side and comparing it with the
integrand — the constant of integration dies in the derivative, which is its fate.

Between the two, six silent errors, two from Sucuri and four from SymPy's LaTeX
parser, which does not refuse what it does not understand — it degrades:

```python
>>> parse_latex("(f + g)' = a")          f + g          # drops the equation
>>> parse_latex(r"\coth x")               coth*x         # the name becomes a symbol
>>> parse_latex(r"\frac{1}{2}\sqrt\frac{\pi}{a}")   1/2   # drops the factor
>>> sp.diff(parse_latex(r"\log_a x"), x)  1/x            # ln(a) is missing
```

See `exemplos/tabelas/AUDIT-DERIVATIVES.md` and `AUDIT-INTEGRALS.md`.

## Declaring dissolves the doubt

```
u = u(t,x)
\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}
```

No question, no amber. And not because someone chose a reading: if
`u` is a function of `x` and `t`, then `\frac{\partial u}{\partial t}` **cannot**
be "a literal fraction of the symbols ∂, u and ∂t" — there is no symbol `u` to
multiply. The site stops being a question because it stopped having two answers.

It is stronger than a convention, and that is why the site turns green and not amber:
the reason is a declaration, not a rule applied without looking. The reading says
where it came from — *u was declared a function of x, t*.

Parentheses, as in a book: *let u = u(t,x)* is how one declares in prose. Written
with the same name on both sides it is a tautology — nobody writes that as an
equation —, and it is this repetition that distinguishes a declaration from mathematics:
`u(t,x)` alone is still an expression, and swallowing it would be deciding for whoever
wrote it. Square brackets stay reserved for n-tuples.

It applies in the cell (from there down) or in the **Functions** field (whole document).

## More than one independent variable

Not for the **prime**: `f'` with two variables would not say with respect to which,
and that is exactly the ambiguity the program refuses. One independent variable
per document is not a limitation — it is what prime notation can carry.

For the **partial derivative**, yes, and without declaring anything: each site
carries its own variable, written out.

```python
from sucuri.document import Document
doc = Document()
doc.read(r"\partial_t u = k \partial_x u").to_sympy()
# Eq(Derivative(u(t, x), t), k*Derivative(u(t, x), x))
doc.read(r"\frac{\partial u}{\partial t} = k \frac{\partial^2 u}{\partial x^2}").to_sympy()
# Eq(Derivative(u(t, x), t), k*Derivative(u(t, x), (x, 2)))
```

`read` returns an `Expression`; `.to_sympy()` is the SymPy object.

The `u` is **a single one**, a function of both. Before, each site promoted the symbol
to its own function, and the same `u` came out as `u(t)` on one side and `u(x)` on
the other — two functions with the same name in the same equation, silently.

## When the notation and the declaration contradict each other

Writing `∂` **declares that there are other variables** — that is what distinguishes ∂
from d. If the function was declared as a function of a single variable, the two
statements disagree, and neither is wrong on its own: either the declaration is
incomplete, or the ∂ was a d.

```
u = u(x)
\frac{\partial u}{\partial x} = A u
   →  d/dx u(x) = A u(x)         the reading is correct
   →  note: u was declared a function of x only, and for a function of one
      variable ∂u/∂x is du/dx — the same object.
```

It does not block, because it is not an error. But staying silent makes whoever wrote
`∂/∂x` see `d/dx` and conclude the program got it wrong.

## Tensor notation

```
\mu, \nu, \lambda = indices

g_{\mu\nu} A^\mu A^\nu      →  g(-L₀,-L₁)·A(L₀)·A(L₁)   all contracted
\Gamma^\lambda_{\mu\nu}     →  free indices: λ, -μ, -ν
A^\mu B_\mu + C^\nu        →  the terms of the sum have different free indices
```

The type is declarable in Schutz's notation — `(M, N)` takes M 1-forms and N
vectors, which in indices means M up and N down:

```
g = tensor(0,2)     g_{\mu\nu\lambda}  →  'g' was declared of type (0,2),
                                          which has 2 indices, and appears here with 3
                    g^{\mu\nu}         →  note: raising an index requires the metric,
                                          and Sucuri does not apply it on its own
```

The note goes away once someone says **which** one is the metric — and then the
index actually comes down (below).

Without it, the rank comes from usage — and it comes late, on the second line
instead of the first.

What decides that `\mu` is an index, and not an exponent, is the **declaration** —
no power is possible with an index in the exponent. It is the same mechanism as
`u = u(t,x)`: declaring dissolves the doubt instead of choosing between readings.

The contraction is SymPy's (`sympy.tensor.tensor`), and consistency comes free
with it: adding terms of different valences raises an error. It is a relativity
error, not a typo, and nobody sees it by eye.

Two pitfalls along the way. `subs` does **not** work to replace a symbol with a
tensor: it returns a plain `Mul`, the repeated indices sit still, and the
expression comes out wrong without complaint — the tree is rebuilt by actually
multiplying. And the valence is shown on screen, because it is the first thing
one checks in a tensor.

### Lowering and raising an index

```
\mu, \nu = indices
g = metric               →  g is the metric of the space — of type (0,2)
A = tensor(1,0)
g_{\mu\nu} A^{\nu}         →  g(-μ,-L₀)·A(L₀)
contract(eq1)            →  A(-μ)            lowered
```

`A_\mu ≡ g_{\mu\nu}A^\nu` is a **convention**, and it holds only for the metric.
No inspection of the expression tells the metric apart from a (0,2) with an
unlucky name — applying it to an arbitrary tensor would give a well-formed, false
expression. That is why it is a declaration, and why `contract` without
`g = metric` refuses instead of guessing. The same holds in the other direction:
`g^{\mu\nu}A_\nu` → `A^\mu`.

### Derivative with an index

```
\partial_\mu A^\mu                →  d_A(-L_0, L_0)                 the divergence
\partial_\mu (A^\nu B_\nu)         →  (∂_μ A^ν) B_ν + A^ν ∂_μ B_ν     Leibniz
\partial_\mu \partial_\nu \phi - \partial_\nu \partial_\mu \phi   simplify →  0
\nabla_\mu \nabla_\nu \phi - \nabla_\nu \nabla_\mu \phi       simplify →  not zero
\partial_\lambda g_{\mu\nu} - \partial_\lambda g_{\nu\mu}    simplify →  0
g^{\mu\nu} \partial_\nu \phi      contract    →  ∂^μ φ
```

SymPy's parser reads `\partial_\mu A` as the symbol `partial_{mu}` times A. A
derivative with an index is not one factor multiplying another, it is an object
of its own, and so the bridge used to refuse it. Now it exists as a head with the
derivative's index in the first slot: ∂_μ A^ν is `d_A(-mu, nu)`, ∇_μ is `D_A`,
∂_μ∂_ν is `dd_…`. With that, it enters contraction, sums and canonicalization
like any tensor, and the LaTeX comes out with the derivative in front:
`\partial_{\mu} A^{\nu}`.

What holds with no hypothesis:

- ∂ and ∇ are linear and obey Leibniz, on scalars too;
- **partial** derivatives commute, so ∂_μ∂_ν is symmetric in those slots;
- on a scalar, ∇_μ φ = ∂_μ φ, by definition, for any connection;
- the symmetry of the differentiated tensor is kept: ∂_λ g_{μν} is symmetric in μν.

What is **not** assumed: that ∇ commutes (that is curvature and torsion), and
that ∇g = 0 (that is Levi-Civita, not an arbitrary connection).

The derivative acts on the factor immediately to its right:
`\partial_\mu A^\nu B_\nu` is (∂_μ A^ν)B_ν, as in any book. A product needs
parentheses. There are three refusals:

- `\partial_{\mu\nu}` without saying the order;
- a derivative with no operand;
- a repeated index in the same position, as in `\partial_\mu A_\mu`.

With no index declared, `\partial_p H` is still the partial derivative with
respect to p, as it always was.

### The connection with indices, and the Ricci identity

```
\nabla = levi-civita
\nabla_\lambda g_{\mu\nu}                          simplify →  0
\nabla_\mu \nabla_\nu \phi - \nabla_\nu \nabla_\mu \phi     simplify →  0      torsion-free

\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho = R^\rho{}_{\sigma\mu\nu} V^\sigma     eq1
R = riemann(eq1)

∇_μ∇_ν W_ρ − ∇_ν∇_μ W_ρ                 simplify →  −R^σ{}_{ρμν} W_σ
∇_μ∇_ν T^α{}_β − ∇_ν∇_μ T^α{}_β         simplify →  R^α{}_{σμν}T^σ{}_β − R^σ{}_{βμν}T^α{}_σ
```

`\nabla = levi-civita` states what sets Levi-Civita apart from an arbitrary
connection: ∇g = 0 and zero torsion. With it, ∇ε = 0 when ε is the tensor.
Without the declaration, none of this is assumed. ∂δ = ∇δ = 0 always holds.

The Riemann comes **from the definition you write**. Sign and slot order vary
from book to book: Carroll and MTW write `R^ρ{}_{σμν}`, Wald writes
`R_{μνσ}{}^ρ`, and some flip the sign. `R = riemann(eq1)` reads the identity and
extracts from it the sign and where each slot goes. From then on, `simplify`
replaces every ∇∇ commutator with curvature, one term per index: the upper index
with one sign, the lower with the other. A lone ∇∇T comes out as it went in. With
the opposite-sign definition, the opposite-sign curvature comes out. The
definition must have the form of the commutator on a vector; otherwise it
refuses, saying what the form is.

Along the way, two silent errors, now with tests:

- `R^\rho{}_{\sigma\mu\nu} V^\sigma` was read as `R(rho)`. The `{}` every book
  uses ended the factor, and three indices and the V vanished;
- `\nabla_\mu T^\alpha{}_\beta` with β undeclared differentiated `T**alpha` as
  a scalar. Now it refuses.

### ∇ expanded into Γ, and Γ into ∂g

```
\nabla_\mu V^\nu = \partial_\mu V^\nu + \Gamma^\nu{}_{\mu\lambda} V^\lambda     eq1
\Gamma = christoffel(eq1)

\nabla_\rho T^\mu{}_\nu = …                 expand(eq2)     →  ∂T + Γ T − Γ T
\partial_\lambda g_{\mu\nu} = g Γ + g Γ     expand(eq2, g)  →  True
g_{\mu\kappa} \partial_\lambda g^{\kappa\nu} = -g^{\kappa\nu} \partial_\lambda g_{\mu\kappa}
                                            simplify        →  True
```

The slot order of Γ varies like that of the Riemann: Carroll and MTW put the
derivative index first, Reall last. With torsion the difference matters, and so
`\Gamma = christoffel(eq1)` reads it from the written definition, which must be
∇ on a vector. `expand(eq)` replaces each ∇ — also ∇ inside ∇ — with ∂ plus one
Γ per index: + on the upper, − on the lower. `expand(eq, g)` further writes each
Γ (and each ∂Γ) as ½g(∂g + ∂g − ∂g), which holds only for Levi-Civita and is only
done with `\nabla = levi-civita` declared; with it, Γ is symmetric in the lower
slots. For an equation, the answer is `True` when both sides agree.

∂_λ g^{μν} = −g^{μα}g^{νβ}∂_λ g_{αβ} is not a hypothesis: it is what "inverse"
means, and `simplify` applies it whenever a metric is declared; g^μ{}_ν is δ,
and its derivative is zero.

With the name on the left, `christoffel(eq1)` is a declaration; the
`christoffel` verb for components in a chart stays the same.

### The Ricci and the scalar, and the dimension as a letter

```
\mu, \nu, \rho, \sigma = indices(d)
R_{\mu\nu} = R^\rho{}_{\mu\rho\nu}              eq2
R = ricci(eq2)

R^\rho{}_{\mu\nu\rho}              simplify →  −Ric(−μ, −ν)
g^{\mu\nu} R_{\mu\nu}               simplify →  R
R_{\mu\nu} - R_{\nu\mu}              simplify →  0
```

The same letter for the Riemann, the Ricci and the scalar, as in the books: the
rank tells them apart. Which pair the Ricci contracts (and with what sign) varies
from book to book, and `R = ricci(eq)` reads it from the written definition; the
scalar is g^{μν}R_{μν}. Internally, R with two indices is another head, `Ric` —
a tensor has only one rank. On simplifying, both become contractions of the
Riemann, canonicalization compares them, and whatever matches the definition
goes back to being R_{μν} or R.

With `\nabla = levi-civita` and the metric declared, the Riemann gains the
symmetries that are theorems: antisymmetry in the first pair and pair exchange.
The symmetry of the Ricci follows. Without the metric, only the antisymmetry that
comes from the commutator. And the output is written in the convention's order —
the upper index in ρ's slot — not in the one canonicalization prefers.

`indices(d)` leaves the dimension as a letter: g^μ{}_μ = d, and computations "in
d dimensions" come out with simplified coefficients. What needs a number —
ε, the signature — refuses.

### prove with indices

```
a, b = indices
T = tensor(2, 0, symmetric)
X = tensor(0, 1)

\nabla_a T^{ab} = 0                          eq1
\nabla_a X_b + \nabla_b X_a = 0              eq2
\nabla_a (T^{ab} X_b) = 0                    eq3
prove(eq3, eq1, eq2)
    eq1 [b→L_1] × X(-L_1)
    1/2 · eq2 [a→L_0, b→L_1] × T(L_0, L_1)
    summing   ∎
```

The symmetry of T is what closes it: with `T = tensor(2, 0)` the same call finds
no combination.

The same verb, and the same idea as without indices: the proof is a linear
combination of relations drawn from the hypotheses, checked again before the ∎.
From H = 0 also follow H with its free indices swapped or contracted (by the
metric), H times any tensor, ∇H and ∇∇H. The search matches each term of the goal
with a term of these forms, modulo the declared symmetries, and from that gets the
index relabeling and the factor; the new terms become targets, for a few rounds,
going deeper in ∇ only when needed.

With `\nabla = levi-civita` and the Riemann declared, `R^ρ{}_{[σμν]} = 0` — the
first Bianchi identity, a theorem of zero torsion — enters without being a
hypothesis, and the certificate says when it was used. This way one gets the
conservation of `T^{ab}X_b` with X Killing, `∇_μ∇_νK^ρ = R^ρ{}_{νμσ}K^σ`, the
contracted Bianchi from the second Bianchi identity, and |∇φ|² + R constant when
∇∇φ = Ric (with the contracted Bianchi as a lemma). Each has a false twin that
does not go through.

### Counting, checking in components, linearizing

```
\mu, \nu, \rho, \sigma = indices(4)
independent(R)                       20      the Riemann, with Bianchi (see below)
independent(C, eq1, eq2)             10      the Weyl: also cyclic and traceless
in_components(eq3)                   True    in indices(2): R_{μν} = ½ R g_{μν}
linearize(eq2, h)                    True    g = η + εh, to order ε
x = coordinates                              ∂_j x^i = δ^i_j
```

`independent(T, eq…)` counts: each component is an unknown, the declared
symmetries identify or zero them, and each given equation — linear in T, with g,
δ, ε — becomes one equation per index value. Zero means only the zero tensor has
those properties in that dimension: that is how the Weyl vanishes in d = 2, 3.
The metric of the count is Euclidean; the dimension of the solution space does
not depend on the signature.

The 20 needs the first Bianchi identity, and that needs `\nabla = levi-civita`,
`g = metric` and the Riemann declared from its definition, `R = riemann(eq1)`.
With `R = tensor(0,4,riemann)` only the slot symmetries enter, and the count is
21.

`in_components(eq)` checks an identity with the most general tensor the
declarations allow (the Riemann with its symmetries and Bianchi) and an arbitrary
symmetric metric, component by component. If it holds for the most general, it
holds for all.

`linearize(eq, h)` expands ∇ into Γ and Γ into ∂g, replaces g_{ab} with
η_{ab} + εh_{ab}, the inverse with η^{ab} − εh^{ab}, ∂g with ε∂h, and truncates
at order ε. η keeps the metric's name, and it is η that raises and lowers the
indices of h.

`x = coordinates`, with no arguments, are the coordinates with an index:
`\partial_j x^i` simplifies to `δ^i_j` once `\delta = kronecker` (or the metric)
is declared — without either, `simplify` says so. `\nabla_\nu x^\mu` is read,
but `simplify` refuses it: x^i is not a vector field, write it with ∂.

### The determinant, and the Cartesian chart

```
g = metric(-,+,+,+)
g = det(g)                     g without indices is det g_{μν}

\nabla_\mu V^\mu = \frac{1}{\sqrt{-g}} \partial_\mu (\sqrt{-g} V^\mu)      expand(eq, g) → True
\Gamma^\beta{}_{\alpha\beta} = \partial_\alpha (\ln \sqrt{-g})              expand(eq, g) → True
```

Books write g, without indices, for the determinant; Sucuri only reads it that
way with `g = det(g)` declared (the name can be another), and without it refuses:
g without indices, g being a tensor, is ambiguous. Once declared,
∂_λ g = g g^{μν} ∂_λ g_{μν} — Jacobi's formula — on simplifying, and the sign of
g comes from the signature: in Lorentzian, g < 0 and |g| = −g.

∂ does not commute with raising an index: ∂_μ(∂^μ φ) is ∂_μ(g^{μν}∂_ν φ), with
∂g. Sucuri differentiates each tensor in its **declared** valence —
`tensor(1,0)` is up, the index of a derivative is down — and puts g explicitly in
the rest. In a Cartesian chart ∂g = 0 and the difference vanishes, but the chart
is a declaration: `g = metric(cartesian)`, or `g = metric(-,+,+,+, constant)` for
an inertial chart. `metric(euclidean)` states only the signature.

The derivative **without** indices, ∇_U X, is the next section.

### Declared symmetry

```
F = tensor(0, 2, antisymmetric)
h = tensor(2, 0, symmetric)

F_{\mu\nu} + F_{\nu\mu}     simplify →  0
F_{\mu\nu} h^{\mu\nu}        simplify →  0      antisymmetric with symmetric
F_{\mu\nu} g^{\mu\nu}        simplify →  0      the trace of an antisymmetric
g_{\mu\nu} - g_{\nu\mu}      simplify →  0      the metric, without saying anything
F(X, X) = 0                  prove    →  ∎      no indices, no hypothesis
```

Symmetry belongs to the slots, and the same declaration serves both notations.
With indices, it feeds SymPy's Butler-Portugal canonicalization, because
`simplify` alone does not use it. Without indices, the engine puts the slots in
canonical order, with the sign of the permutation, and a repeated slot in an
antisymmetric tensor gives zero.

The metric is symmetric without having to say so. Before this declaration
existed, not even `g_{\mu\nu} - g_{\nu\mu}` vanished. It was not wrong, but it
was incomplete.

Reading does not simplify: `F_{\mu\nu} + F_{\nu\mu}` shows up as written, with
its valence, and the zero is the verb's answer. There are two refusals:

- symmetry on a (1,1): swapping an upper index with a lower one requires lowering
  one of them, and that is the metric, not the tensor;
- symmetry on a (1,0) or (0,1): a single slot has nothing to swap with.

The Riemann has its own declaration, because its symmetries are not total:

```
R = tensor(0, 4, riemann)

R_{abcd} + R_{bacd}      simplify →  0      antisymmetric in the first pair
R_{abcd} + R_{abdc}      simplify →  0      and in the second
R_{abcd} - R_{cdab}      simplify →  0      symmetric under pair exchange
R_{abcd} g^{ab}          simplify →  0
R(X,X,Y,Z) = 0           prove    →  ∎
```

These symmetries of the (0,4) are the same in every book. What changes between
conventions is the overall sign and the index order in the (1,3), and none of
that touches slot exchanges. The (1,3), R^a_{bcd}, mixes upper and lower indices
and is refused by the rule above. The cyclic identity, R_{a[bcd]} = 0, does
**not** enter: it is not a slot exchange, it is a theorem, and it needs zero
torsion. It comes as a hypothesis.

A multi-letter name is refused in the declaration: `Rm_{abcd}` in LaTeX is R
times `m_{abcd}`, and that is how the parser reads it. Without the refusal, the
declaration would exist and never be used, with no warning. Use one letter or a
command (`\Rm`).

And the symmetrization notation:

```
T_{(\mu\nu)}                    →  ½ T_{μν} + ½ T_{νμ}
T_{[\mu\nu]}                    →  ½ T_{μν} − ½ T_{νμ}
S_{(\mu|\rho|\nu)}              →  ½ S_{μρν} + ½ S_{νρμ}       ρ is left out
S_{[\mu\nu\rho]}                →  six terms, with 1/6
T_{(\mu\nu)} + T_{[\mu\nu]} - T_{\mu\nu}   simplify →  0
F_{(\mu\nu)}                    simplify →  0            F antisymmetric
```

Before this, with the indices declared, `T_{(\mu\nu)}` was read as
`T_{\mu\nu}`: the parentheses vanished, and `T_{(\mu\nu)} - T_{\mu\nu}` gave
**zero**, which is false for T with no symmetry. With no indices declared,
SymPy's parser does the same, and it is now refused.

The factor is 1/n!, that of Wald, MTW and Carroll, and the reading says so in a
note. Refused:

- a bracket that does not close, or is nested;
- symmetrization of a single index;
- a bar outside a bracket;
- symmetrization mixing an upper index with a lower one (swapping them needs the
  metric).

### Kronecker and Levi-Civita

```
\delta = kronecker
\delta^\mu_\nu A^\nu        simplify →  A^μ
\delta^\mu_\mu             simplify →  4          the dimension
\delta_{\mu\nu}            refused: with the metric, this is g_{μν}

\epsilon = levi-civita(tensor)      or  levi-civita(symbol)
\epsilon_{\mu\nu\rho\sigma} S^{\mu\nu}    simplify →  0     S symmetric
g_{\alpha\mu}\epsilon^{\mu\nu\rho\sigma}      contract →  ε_α^{νρσ}      only the tensor
```

δ is a declaration because `\delta` is also a variation, a small number and an
index. It requires one index up and one down. δ_{μν} outside Euclidean space is
not a tensor; with the metric, it is g_{μν}.

Levi-Civita cannot be declared without choosing, because books do not agree:

- the **symbol** is ±1 in every chart, is a density, and g does not move it:
  `contract` refuses to lower one of its indices;
- the **tensor** is √|g| times the symbol, and is raised and lowered with g.

In both cases, ε has as many indices as the dimension and is totally
antisymmetric.

Contracting two ε needs the signature, and the signature is declared with the
signs; the result is written with δ, so δ must be declared too:

```
g = metric(-,+,+,+)
\delta = kronecker
\epsilon = levi-civita(tensor)
\epsilon^{\mu\nu\rho\sigma} \epsilon_{\mu\nu\rho\sigma}     simplify →  −24
\epsilon^{\mu\nu\rho\sigma} \epsilon_{\mu\nu\rho\alpha}     simplify →  −6 δ^σ_α
\epsilon^{ijk} \epsilon_{imn}                  simplify →  δ^j_m δ^k_n − δ^j_n δ^k_m   (Euclidean, 3D)
```

In general, ε^{a₁…a_k b…}ε_{a₁…a_k c…} = σ k! δ^{[b…}_{c…]}, with the sign of
the permutation that aligns the contracted indices. For the **tensor**,
σ = (−1)^s, where s is the number of minus signs. For the **symbol**, σ = 1,
because it is ±1 in both positions and the metric does not enter. The tensor with
no declared signature stays as it is, because the sign is unknown.

`lorentzian` alone is refused: (−,+,+,+) and (+,−,−,−) are both in use, and εε
and g(U,U) change sign between them. `riemannian` and `euclidean` mean all +. A
signature declared after indices with a dimension must match it:
`i, j = indices(3)` then `g = metric(-,+,+,+)` is refused. Declared before, it
gives its dimension to indices declared without one — `\mu, \nu = indices` are
then of dimension 4 —, while `indices(3)` states its own and is accepted.

### The connection without indices: ∇_U X, [U,X] and R(U,X)W

```
U = tensor(1,0)
X = tensor(1,0)
R = curvature

\nabla_U \nabla_X U - \nabla_X \nabla_U U   →  nabla_U(nabla_X(U)) - nabla_X(nabla_U(U))
[U, X] = 0                                 →  Eq([U, X], 0)
\nabla_U \nabla_U X = R(U,X)U              →  Eq(nabla_U(nabla_U(X)), R(U, X)(U))
```

Without this the parser read `\nabla_U X` as `X*nabla_{U}`: an oddly named
symbol multiplying X. The product commutes, so ∇_U∇_X and ∇_X∇_U came out equal,
and the curvature, which is precisely the difference between the two, vanished
without warning. `[U,X]` it refused, and `R(U,X)U` became the question "R
applied, or R times the parenthesis?".

Typography resolves none of the three. `\nabla_U` and `\nabla_\mu` are written
the same way, and in Wald the Latin letter in the subscript **is** an index.
`[a,b]` can be a Lie bracket, a commutator, an interval or a pair. The
declaration decides:

- **∇_U**: a vector written without an index can only be the abstract object.
  Then ∇_U becomes an application, with the order kept in the structure. The
  direction can be composite, as in `\nabla_{[U,X]}` or `\nabla_{U+X}`.
- **[U,X]**: between two declared vectors, it can only be the Lie bracket. A
  bracket with no comma is still grouping, as in `[x+1]^2`.
- **R(U,X)W**: with `R = curvature`, R does not multiply the parenthesis. It
  requires two vectors and the vector it acts on, and `R(U,X)` alone refuses.

When what was declared does not license the reading, it refuses. That holds for a
subscript with no declaration, a bracket of things that are not vectors, and
curvature acting on a 1-form. It also refuses where it is unclear how far the
operator reaches (`\nabla_U X^\mu`, `\nabla_U X_1`): in that case use
parentheses.

`R = curvature` declares the **role** of R, not the convention. The sign and the
argument order vary from book to book. For *reading* `R(U,X)W` that does not
matter, because it is the same written object. For *computing* it matters, and
then the definition will have to be declared, not assumed.

### Proving

```
[U,X] = 0                                                     eq1
\nabla_U U = 0                                                eq2
\nabla_U X - \nabla_X U = [U,X]                               eq3
R(U,X)U = \nabla_U\nabla_X U - \nabla_X\nabla_U U - \nabla_{[U,X]} U   eq4
\nabla_U \nabla_U X = R(U,X)U                                 eq5

prove(eq5, eq1, eq2, eq3, eq4)
    − eq4            R(U, X)(U) - nabla_U(nabla_X(U)) + … = 0
    nabla_U(eq1)     nabla_U([U, X]) = 0
    nabla_{eq1}(U)   nabla_{[U, X]}(U) = 0
    nabla_X(eq2)     nabla_X(nabla_U(U)) = 0
    nabla_U(eq3)     -nabla_U([U, X]) + nabla_U(nabla_U(X)) - nabla_U(nabla_X(U)) = 0
    summing          ∇_U∇_U X = R(U,X)U  ∎
```

That is the geodesic deviation equation, derived without indices.
`nabla_U(eq3)` is eq3 with ∇_U applied to both sides, and `nabla_{eq1}(U)` is eq1
put in the direction of ∇ acting on U.

Only the hypotheses **named** in the call enter. Writing an equation in the
notebook is not asserting it, and a proof that used the scratch computation on
the line above would prove nothing.

On its own, the engine knows only what holds for **any** connection, in any
book:

- ∇_U X is linear in U over functions, and obeys Leibniz in the operand:
  ∇_U(fX) = U(f)X + f∇_U X;
- the bracket is antisymmetric and obeys Leibniz:
  [fA, gB] = fg[A,B] + f A(g) B − g B(f) A;
- U(f) obeys the chain rule;
- R is a tensor.

Everything else must come from the hypotheses: zero torsion, that the curve is a
geodesic and, above all, the **definition** of R. That is how the sign convention
is declared instead of assumed. With the opposite-sign definition, the same call
refuses `R(U,X)U` and proves `-R(U,X)U`. Things that look true and are not also
fail: `\nabla_U(fX) = f\nabla_U X` (U(f)X is missing), `[fU, X] = f[U,X]` and
`R(U,X) = -R(X,U)` without the definition.

Underneath, everything becomes a linear combination. Other relations are derived
from the hypotheses by applying the contexts that appear in the problem
(∇_U □, ∇_□ U, [□, X], …). The proof is a combination of these relations that
gives the goal, and the sum is checked again, from scratch, before the ∎.

When the engine does not find one, it says what is usually missing ("No
hypothesis mentions R(U, X)(U)") and also says that not finding a proof is not a
proof that it is false.

### For all

A definition holds for any vector, and this is how it is written:

```
\forall A, B, W: R(A,B)W = \nabla_A \nabla_B W - \nabla_B \nabla_A W - \nabla_{[A,B]} W   eq1
\forall A, B: \nabla_A B - \nabla_B A = [A,B]                                           eq2
[U,X] = 0                                                                                eq3
\nabla_U U = 0                                                                           eq4
\nabla_U \nabla_U X = R(U,X)U                                                            eq5

prove(eq5, eq1, eq2, eq3, eq4)
    − eq1[A→U, B→X, W→U]
    nabla_U(eq2[A→U, B→X])
    nabla_U(eq3) · nabla_{eq3}(U) · nabla_X(eq4)
    summing          ∇_U∇_U X = R(U,X)U  ∎
```

The definition of R and zero torsion are stated **once**. The proof instantiates
each where the problem calls for it, and says which instance:
`eq1[A→U, B→X, W→U]`.

The separator after the list is mandatory: a colon, `\colon`, `\quad`, `\;` or
`\,`. Without it there is no telling where the list ends: in
`\forall W, R(U,X)W = …`, does the comma separate names or close the list? The
bound variables are vectors only **inside** the equation and do not leak into the
lines below.

Instantiation does not try every vector. It matches each term of the hypothesis
with the terms of the problem: `R(A,B)W` with `R(U,X)U` gives A=U, B=X, W=U. It is
what one does when reading a definition: apply it to the case at hand. With the
general definition, things come out that did not before: the antisymmetry
`R(A,B)W = -R(B,A)W` and, with the Jacobi identity as a hypothesis, the algebraic
Bianchi identity.

### Scalar functions

A scalar is anything not declared a tensor, and `\nabla_U f` with f a scalar is
the directional derivative U(f):

```
\nabla_U (f X) = \nabla_U f \, X + f \nabla_U X        prove: ∎, no hypothesis
[f U, X] = f [U, X] - \nabla_X f \, U                 prove: ∎, no hypothesis
\nabla_U (f X) = f \nabla_U X                         fails: U(f)X is missing
\nabla_U f = 0                                        eq1
prove(eq_above, eq1)                                  ∎ — the step is "eq1·X"
```

Every symbol that is not a number is treated as a **function**, not as a
constant. That is the safe side: if c is constant, U(c) = 0 is just a special
case, and a proof that needs it asks for the hypothesis. A wrong proof never
comes out of treating as constant something that varied.

A scalar hypothesis, like `\nabla_U f = 0`, is a relation like the others:
multiplied by a vector of the problem (`eq1·X`), differentiated in a direction
(`U(eq1)`), or by a function (`f·eq1`). Each of these operations shows up as a
step in the table.

**No division by a function.** The combination that closes the proof uses
numbers only. Dividing by f would conclude X = U from fX = fU, which is false
where f vanishes. Elimination is done in numeric coordinates, one per monomial,
and multiplying by a function is an explicit context (`f·eq1`). An earlier
version of the engine did divide, and concluded X = U from fX = fU. Today there
is a test for that.

`U(f)` is also read as a directional derivative, but it is still a question: U
applied to f, or U times f? Both readings are well typed, because (a+b)U is also
a vector. Once application is chosen, what comes out is U(f), not a function
called U. `\nabla_U f` leaves no doubt.

### The metric

With `g = metric`, `g(X,Y)` is the inner product. With `\omega = tensor(0,1)`,
`\omega(U)` is ω applied to U. In general, a (0,n) applied to n vectors is a
scalar: it is Schutz's slot notation, the same as in the declarations. No doubt
is left: with a comma, `g(X,Y)` cannot be a product, and with the type declared
the slots are vectors.

```
\forall A, B, C: \nabla_A g(B,C) = g(\nabla_A B, C) + g(B, \nabla_A C)    eq1
\forall A, B: \nabla_A B - \nabla_B A = [A,B]                               eq2
2 g(\nabla_X Y, Z) = \nabla_X g(Y,Z) + \nabla_Y g(X,Z) - \nabla_Z g(X,Y)
                    + g([X,Y],Z) - g([X,Z],Y) - g([Y,Z],X)                   eq3

prove(eq3, eq1, eq2)
    − eq1[A→X, B→Y, C→Z] · − eq1[A→Y, B→X, C→Z] · eq1[A→Z, B→X, C→Y]
    g(eq2[A→X, B→Y], Z) · − g(eq2[A→X, B→Z], Y) · − g(X, eq2[A→Y, B→Z])
    summing   the Koszul formula  ∎
```

The Koszul formula follows from the two conditions that make ∇ the Levi-Civita
connection: compatibility with the metric and zero torsion. Without zero torsion,
it does not follow. `g(eq2[…], Z)` is zero torsion put in the first slot of g: a
relation between vectors carried into a relation between scalars.

On its own, the engine knows that g is linear over functions in each slot and
symmetric. Symmetry is not a book convention, it is what is meant by a metric. It
also knows that the bracket acts on a function as `[A,B](f) = A(B(f)) − B(A(f))`,
because that is the definition of the bracket. Compatibility does not enter on
its own: it is what sets Levi-Civita apart from an arbitrary connection, and it
comes as a hypothesis, with ∀ or without.

Limits: only linear equalities, with scalar coefficients. Proofs that need an
idea, and not just chaining hypotheses, do not come out. One example is
g(R(U,X)Y, W) = −g(Y, R(U,X)W): that proof needs to introduce h = g(Y,W) and
compare `[U,X](h)` with `U(X(h)) − X(U(h))`. None of that appears in the statement,
and the search only instantiates what appears.

### From one notation to the other

```
\nabla = levi-civita
\nabla_\mu \nabla_\nu V^\rho - \nabla_\nu \nabla_\mu V^\rho = R^\rho{}_{\sigma\mu\nu} V^\sigma      eq1
R = riemann(eq1)
R = curvature
\nabla_U \nabla_U X = R(U,X)U                                                    eq2
indices(eq2)
    U^α(U^β ∇_α∇_β X^μ + ∇_α U^β ∇_β X^μ) = R^μ{}_{αβσ} U^α U^β X^σ
```

The index-free proof is shorter and chart-independent, and physics books write
with indices. `indices(eq)` translates with the rules the declarations have
already fixed:

- X becomes X^μ;
- g(X,Y) becomes g_{αβ}X^αY^β, and ω(X) becomes ω_αX^α;
- ∇_X Y becomes X^α∇_αY^μ, with Leibniz on products;
- X(f) becomes X^α∇_α f;
- [X,Y] becomes X^α∇_αY^μ − Y^α∇_αX^μ with Levi-Civita, and with ∂ without it;
- R(U,X)W follows the convention of `riemann(eq)`.

To translate R(U,X)W, the same letter must be declared `curvature` and
`riemann(eq)`. The translation then assumes R(U,X) = ∇_U∇_X − ∇_X∇_U − ∇_{[U,X]},
which is how the index definition reads it, and says so in a note.

Both notations talk about the same thing, and that can be checked. Compatibility
with the metric, written without indices and translated, gives `True` in
`simplify` with Levi-Civita, because ∇g = 0. A wrong version shows the leftover
difference.

The output is not canonicalized. With the metric, the canonical form raises and
lowers the dummies, and R^μ{}_{σαβ}U^σ would come out as R^{μαβσ}U_σ, which is
equal and unreadable. Not yet: the way back, from indices to index-free; and ∀
and forms are not translated.

### Differential forms

```
\omega = form(1)
\eta = form(2)                        a 2-form: an antisymmetric (0,2)

\mathrm{d}(\omega \wedge \eta) = \mathrm{d}\omega \wedge \eta - \omega \wedge \mathrm{d}\eta   prove → ∎
\mathcal{L}_X \mathrm{d}\omega = \mathrm{d} \mathcal{L}_X \omega                          prove → ∎
\iota_Y \iota_X \eta = \eta(X, Y)                                                 prove → ∎
\eta \wedge \eta = 0                                        fails: even degree
\mathrm{d}(f \omega) = \mathrm{d} f \wedge \omega              only with \mathrm{d}\omega = 0
```

d, ∧, ι_X and ℒ_X without indices. In reading, the declaration decides, as
everywhere else:

- `\mathrm{d}` is always the operator;
- a bare `d` is an operator only when it acts on a declared form, and `df` with f
  a function is still d times f;
- `\wedge` (or `\land`) is only valid between forms;
- `\iota_X` and `\mathcal{L}_X` require X declared a vector.

A p-form is an antisymmetric (0,p), and so ω(X,Y) is read with what already
existed.

With no hypothesis, the engine knows what holds in any book: d² = 0, graded
Leibniz, α∧β = (−1)^{pq}β∧α, ι_X as an antiderivation (with ι_X df = X(f) and
ι_Xι_X = 0), and Cartan's formula, ℒ_X = ι_X d + d ι_X, which is a theorem and
not a convention.

The convention that enters is ι_Y ι_X ω = ω(X,Y), the determinant one (Lee,
Spivak). The formula dω(X,Y) = X(ω(Y)) − Y(ω(X)) − ω([X,Y]) changes by a factor
with the normalization, and so it comes as a hypothesis, with ∀:

```
\forall A, B: \iota_B \iota_A \mathrm{d}\omega = \nabla_A (\omega(B)) - \nabla_B (\omega(A)) - \omega([A,B])   eq1
\mathrm{d}\omega = 0                                                                              eq2
\nabla_X (\omega(Y)) - \nabla_Y (\omega(X)) = \omega([X,Y])                                         eq3
prove(eq3, eq1, eq2)       − eq1[A→X, B→Y] · iota_Y(iota_X(eq2))   ∎
```

Relations between forms enter the same engine as the others. The terms are
exterior monomials, the scalar is the empty monomial, and the contexts are d □,
ι_X □, α ∧ □ and f·□.

The Hodge dual is declared after the signature, which is where the dimension n
and the number of minus signs s come from:

```
g = metric(-,+,+,+)
\star = hodge
\star \star F = -F                                    prove → ∎      2-form, Lorentz
\star \star \omega = \omega                              prove → ∎      1-form, Lorentz
\omega \wedge \star \alpha = \alpha \wedge \star \omega          prove → ∎
\omega \wedge \star \omega \wedge \alpha = 0                  prove → ∎      degree 5 > 4
```

⋆ is linear over functions, ⋆⋆ = (−1)^{p(n−p)+s} on a p-form, α∧⋆β = β∧⋆α, and
every product of degree greater than n is zero. The orientation need not be
stated: flipping it flips the sign of ⋆, but not that of ⋆⋆ nor the symmetry of
α∧⋆β. The codifferential δ = ±⋆d⋆ has a convention-dependent sign, and so it is
not built in; write ⋆d⋆. Without `\star = hodge`, `\star` is not an operator.

### Without declaring, the refusal stays

An index is not an exponent, and SymPy's parser does not know the difference.
Measured:

```python
>>> parse_latex(r"A^\mu")                    A**mu          # A raised to μ
>>> parse_latex(r"x^2_i")                    x**2           # the index vanishes
>>> parse_latex(r"\Gamma^\lambda_{\mu\nu}")  Gamma**lambda_{mu*nu}
>>> parse_latex(r"g_{\mu\nu}")               Symbol('g_{mu*nu}')
```

None of this raises an error and none of it has a strange symbol in the output:
they are **well-formed, false** expressions, the worst class of error this
program knows. Anyone writing relativity would get silently wrong computations.

With no index declared, Sucuri refuses where the parser **demonstrably loses** — superscript before
subscript, and the same Greek index up and down (Einstein summation) — and
**warns** where there is only suspicion, because `A^\mu` really is "A raised to
μ" in some text, and telling an index from an exponent by typography is
impossible.

Declaring the index is what opens the bridge, and then none of this happens.

## Metric and curvature

Index notation states the **structure**: that `g` has two lower indices, that
`A^\mu B_\mu` is contracted. It does not state what `g` **is**. Christoffel, Ricci and
Riemann need the other side: components in a chart.

```
x = coordinates(t, r, \theta, \phi)
g = metric(-(1 - \frac{2M}{r}), \frac{1}{1 - \frac{2M}{r}}, r^2, r^2 \sin^2\theta)

christoffel(g)  →  13 nonzero components, Γ^t_{tr} = M/((-2M + r)r), …
ricci(g)        →  result: all components are zero
scalar(g)       →  0
```

All of Schwarzschild, and the vanishing Ricci that is the sanity check of all
relativity. The computation is `sympy.diffgeom`'s; what was missing was **stating the
metric in LaTeX**.

It goes in as a **diagonal**, because that is how textbooks give almost every
metric that matters, or as a **line element**, which takes cross terms:

```
x = coordinates(t, r, \theta, \phi)
g = metric(ds^2 = -dt^2 + 2 a\, dt\, d\phi + dr^2 + r^2 d\theta^2 + r^2 \sin^2(\theta) d\phi^2)

christoffel(g)  →  13 nonzero components, Γ^t_{rφ} = ar sin²θ/(a² + r² sin²θ), …
```

A matrix is not: `metric(\begin{pmatrix}…)` is refused ("A LaTeX matrix is not
read").

With declared components, `evaluate` carries the notation all the way to numbers:

```
\mu, \nu = indices
A = tensor(1,0)
g_{\mu\nu} A^{\nu}
evaluate(eq1)  →  A_{t} = A__t·(2M − r)/r        A_{\theta} = A__theta·r²
                  A_{r} = A__r·r/(r − 2M)        A_{\phi}   = A__phi·r²sin²θ
```

Nobody declared the components of A, so they come in as names, in SymPy's
convention (`A__t` is A^t). What round-trips is precise: the SymPy name goes back into
SymPy — the exported script, the SymPy output — as that symbol, not a power; and the
labels of the last table (`A_{t}`, `\Gamma^{r}_{tt}`) go back into the notebook as
verb targets. The typeset `A^{t}`, typed back into a cell, is read as A to the power t:
that is what the notation says without a declaration.

`contract` gives the **structure**; `evaluate` gives the **value**. They are two different
requests, and the program keeps them apart.

The printed label is a valid verb target (`evaluate(A_{t})`, `latex(\Gamma^{r}_{tt})`)
without requiring the double braces the screen uses, because braces are TeX typography,
not the object's identity. A **zero** component is left out of the table, and still
answers when asked: hiding the 51 zeros is showing the 13 that
matter, but saying "I don't know it" to someone who asks for one of them would be lying.

What comes back are **components**, not the tensor: changing chart changes all of
them. That is why the answer always says which coordinates it is in. What does not change
are the invariant statements: vanishing Ricci is vanishing Ricci in any chart.

## What is NOT ambiguity

`∂` is reserved for the partial derivative. Nobody has ever written
`\frac{\partial u}{\partial t}` meaning a fraction of the symbols ∂, u and ∂t;
with `d` the doubt is real, because `d` is a letter people use for
distance, diameter, whatever.

The site is still **located**, because SymPy's parser degrades
`\frac{\partial^2 u}{\partial x^2}` into `(partial**2*u)/(partial*x**2)` and
someone has to rewrite it. What changes is that nobody needs to be asked. That is
why `\partial_p H` appears in the table below: it is located, and never asked.

A question that is not a question spends the credibility of the ones that are; the same reason
`\arctan(` does not open a juxtaposition site.

## Recognized ambiguities

| Kind | Example | Readings |
|---|---|---|
| prime | `y''` | derivative / symbol |
| Leibniz | `\frac{d^2y}{dx^2}` | derivative / fraction of symbols |
| juxtaposition | `f(x+1)` | application / product |
| **Newton** | `\ddot{q}` | time derivative / decoration |
| **partial** | `\partial_p H` | partial derivative / product |

Time and the independent variable are declared **separately**: in mechanics the
prime's variable is rarely the dot's, and treating them as one would silently produce
a wrong equation.

```python
doc = (sucuri.Document(independent_variable='x', time_variable='t')
       .primes_are_derivatives().dots_are_time_derivatives())
doc.read(r"\dot{q} = \partial_p H")     # d/dt on one side, d/dp on the other
```

## The recognized tree

`Expression.tree()` returns what the program understood, node by node, and every node
born from an ambiguous site carries **how** that site was resolved. That is
what lets the interface paint in amber whatever came from a convention.
`exemplos/arvore.py` reads Kovacic's Riccati equation,
`\varphi'' + 3\varphi\varphi' + \varphi^3 = 4r\varphi + 2r'`, with primes as
derivatives by convention and `r'` annotated by hand. The Python API prints the
tree in Portuguese (the interface shows it in the chosen language):

```
igualdade
  soma
    potência
      função varphi aplicada a (x)
        símbolo x
      número 3
    produto
      número 3
      derivada de ordem 1 de varphi em x  [inferida]  <- conferir
      função varphi aplicada a (x)
        símbolo x
    derivada de ordem 2 de varphi em x  [inferida]  <- conferir
  soma
    produto
      número 2
      derivada de ordem 1 de r em x  [explícita]
    ...
```

Two derivatives came from the convention and are marked for checking (*conferir*,
"check"); the third was annotated site by site (*explícita*, "explicit").

Derivatives are leaves in the user's reading: the reader wants to see "second derivative
of φ", not its internal tree. `to_dict()` serializes for the web interface.

## Usage

```python
import sucuri

# one-off case: no convention, it REFUSES, which is the default
e = sucuri.parse(r"\varphi'' + \varphi' = r")
e.questions()                      # the questions, instead of a guess
e.to_sympy()                       # raises Unresolved, listing the pending sites

# with the convention declared
e = sucuri.parse(r"\varphi'' + \varphi' = r",
                 independent_variable='x', primes='derivative')
e.to_sympy()
e.inferred                         # what came from a convention and asks to be checked

# ongoing work: the document keeps conventions and annotations
doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
doc.annotate("prime", "r", "derivative", order=1)
doc.read(...).tree()

# the index-free connection, and a proof
from sucuri.prova import provar, linhas
doc = sucuri.Document()
doc.tensor("U", 1, 0); doc.tensor("X", 1, 0); doc.curvature("R")
eq = lambda s: doc.read(s).to_sympy()
p = provar(eq(r"\nabla_U \nabla_U X = R(U,X)U"),
           {"def": eq(r"\forall A, B, W: R(A,B)W = \nabla_A \nabla_B W"
                      r" - \nabla_B \nabla_A W - \nabla_{[A,B]} W"),
            "tor": eq(r"\forall A, B: \nabla_A B - \nabla_B A = [A,B]"),
            "fam": eq(r"[U,X] = 0"), "geo": eq(r"\nabla_U U = 0")},
           {"U": (1, 0), "X": (1, 0)})
linhas(p)                          # the steps: label, text, LaTeX
```

The Python API speaks Portuguese: `e.questions()`, the `Unresolved` message and
the tree come out as `derivative = derivada de ordem 2 de varphi`,
`2 sítio(s) ambíguo(s) sem anotação`, and so on. The English translation is the
interface's.

The full example, with the refusals and the sign flip, is in
`exemplos/desvio_geodesico.py`, and the suite runs it.

## Manual

`sucuri/interface/estatico/manual-en.html`, served at `/manual-en.html` in both
versions. Writing, declaring, the verbs, what each answer means, and what
the program does not do yet.

**The manual's examples are run by the suite on every change.** A manual whose
examples nobody runs rots, and rots silently, which is the failure mode this
project hunts. When an example breaks, either the program changed and the manual
lies, or the manual is right and the program regressed; both deserve to stop the
suite.

## Installation

Python ≥ 3.10. From the repository:

```bash
pip install .                 # or, to run the tests:  pip install -e ".[dev]"
python -m sucuri.interface    # or just:  sucuri
pytest                        # the suite, manual examples included
```

## The interface

```bash
python -m sucuri.interface        # opens at http://127.0.0.1:8765/
```

And **online**, with nothing to install: `web/` is the same interface with the engine running
inside the browser: Python and SymPy compiled to WebAssembly by Pyodide,
the `sucuri` package in a zip the page unpacks. It is not a second
implementation: they are the same files, and a test fails if the published copy
diverges from the repository. Nothing the user writes leaves their machine,
because there is nowhere for it to go. See `web/README.md`.

Local server and a page in the browser. The choice is deliberate: the program is
Linux today and goes online tomorrow without a rewrite: the same engine, the same page,
another address. Only the standard library on the Python side; KaTeX comes
bundled, and the interface works offline.

What the page shows, left to right:

- **the LaTeX input**, re-read on every keystroke (220 ms window);
- **the ambiguous sites**, one by one, with the possible readings as buttons: clicking
  is annotating, and the annotation beats the convention;
- **the document's conventions**, which apply to everything and show in amber;
- **the recognized tree**, with each node's provenance;
- **the reading**, typeset: what the program understood, in textbook
  math, not what you wrote;
- **the SymPy output**, pasteable into a script;
- **the modules**, with the provenance barrier intact: a conclusion without a source
  reaches the page marked as not presentable.

The interface decides nothing mathematical. Between it and the engine passes JSON
(`/api/ler`, `/api/anotar`, `/api/avaliar`, `/api/modulos`, `/api/operar`,
`/api/caderno/executar`, `/api/caderno/refazer`, `/api/caderno/reiniciar`), and the only two
decisions it carries are the user's: convention and annotation.

## The notebook

```bash
python -m sucuri.interface        # and click "notebook" in the header
```

One equation per page is enough to inspect notation; work is writing one
thing, looking at it, writing another that uses the first.

```
        f = f(x)                               →  from here on, f is a function of x
        f^{\prime} = x^2          Shift+Enter   →  eq1,  df/dx = x²
        solve(eq1)                             →  f(x) = C₁ + x³/3
                                                  check: remainder 0
        export(eq1)                            →  the script that runs without Sucuri
```

Five actions, and each touches a different layer of state; the distinction
between them is why there are five and not two:

| | |
|---|---|
| **New** | erases what is written **and** what is accumulated |
| **Open** | replaces what is written, rebuilds what is accumulated |
| **Save** | takes what is written and the decisions to a file |
| **Run all** | rebuilds the accumulated state from what is written, in order |
| **Restart** | throws away only the accumulated state: what is written stays |

"Restart" erases `eq1`, `eq2` and the declarations without touching a line of what
you wrote; after it, `solve(eq1)` no longer finds `eq1`, which is
exactly the point.

The saved file is text, readable, with cells separated by `%%`; `%` is a
comment in LaTeX, so it opens in any editor. The site decisions
go in a comment line at the top: they belong to the user, not the engine, and without them
the reopened notebook would ask again what was already answered.

**The notebook has no conventions**: it has declarations, which are cells like the
others. Six form fields said what three lines on the sheet say
better, and say it more strongly: a convention *chooses* a reading, a
declaration *dissolves* the doubt.

```
u = u(t,x)        u is a function of t and x
e = euler         e is Euler's number
c = symbol        c is a symbol, not a function: c(…) is a product
```

That alone decides `'`, `\dot`, `∂`, Leibniz and juxtaposition for the declared
names. And what the notation does not say is still a question: `u'` with `u` a
function of two variables does not say with respect to which, and declaring does not invent.

### The wave equation, and what "SymPy doesn't solve it" means

```
u = u(t,x)
c = symbol
\frac{\partial^2 u}{\partial t^2} = c^2 \frac{\partial^2 u}{\partial x^2}

solve(eq1)         →  no solution found
                      NotImplementedError: psolve: Cannot solve …
separate(eq1)      →  eq2   T'' = k T,   eq3   c² X'' = k X,   both solved

F = F(x)
G = G(x)
u = F(x - c t) + G(x + c t)                                          eq4
check(eq1, eq4)    →  candidate verified: substituted into the equation: remainder 0
```

`pdsolve` does not solve the wave equation, and it is only one of SymPy's paths.
`pde_separate_mul` separates, `dsolve` solves each piece, and `checkpdesol`
checks d'Alembert.

What a computation **produces** gets a name, and that is what makes the notebook compose:

```
separate(eq1)    →  eq2   T″(t) = k T(t)
                    eq3   c² X″(x) = k X(x)
solve(eq2)       →  eq5   T(t) = C₁e^(−√k t) + C₂e^(√k t)     (after the block above)
```

An operation that returns unnamed equations returns dead ends: whoever reads two ODEs in a
table has no way to ask for the next computation on them except by retyping.

`separate` **does not present itself as a solution**: separating ASSUMES the solution is a
product, and the assumption is a restriction. What comes out are the modes; the general solution
is their superposition, and separation does not prove it is complete.

The verbs are a fixed, closed list **on purpose** — a few dozen today, from
`solve`, `evaluate`, `simplify`, `export` and `latex` to `prove`, `contract`,
`separate`, `check` and `christoffel`; the manual lists them all.
If Python could be written here, the bridge this program is would stop being
mandatory: whoever writes `sympy.solve(...)` talks straight to SymPy, with no
sites, no declared convention, no provenance, and what is left is a Jupyter with
extra steps.

`solve` is a single verb, and the object decides the computation; **three** computations now:

| the unknown | the solver |
|---|---|
| `y(x)` | `dsolve`, checked with `checkodesol` |
| `u(t,x)` | `pdsolve`, checked with `checkpdesol` |
| no derivative | `solve` |

`∂u/∂t = A u`, with `u = u(t,x)` and `A = A(t)` declared, comes out as
`F(x)·exp(∫A(t) dt)`: in a PDE, the "constant" of
integration is an arbitrary function of the other variable. `pdsolve` solves far
less than `dsolve` (it does not solve the wave equation), but solving
little is not solving nothing, and whoever wrote the equation decides whether the little
is enough.

A differential equation goes to the module that checks the solution by
substitution; an algebraic one goes to `solve`. Forcing the user to choose between `solve` and `dsolve` is asking them to
classify their own equation for the program; backwards.

Conventions apply to the whole notebook, and changing one **redoes everything**: what
was already written comes to mean something else, and showing both readings at
once would be showing two mathematics.

### More than one instruction per cell

`Enter` breaks the line, `Shift+Enter` runs. A cell accepts several instructions,
one per line:

```
contract(eq1)
evaluate(eq1)
```

It only chains when **every** line is a recognized instruction: a command or a
declaration. A LaTeX equation can legitimately span two lines, and
splitting it would give two meaningless halves instead of an error, which is the kind of
silence this program exists not to produce.

## The verb follows the object

A differential equation is **solved**; an expression is **evaluated**. They are different
computations, and the page's main button changes its name according to what is
written; offering the wrong verb makes the user conclude the program cannot
do what it can.

## Reading and evaluating are different acts

`\int_0^1 x^2` is read as `Integral(x**2, (x, 0, 1))` and stays that way: at rest.
Sucuri reads; computing is another act, and so it is a button (**Evaluate**), not a
side effect of typing.

The answer comes with the name of what it is:

| | |
|---|---|
| closed | `1/3`, with the approximation `≈ 0.333…` **beside** it, never in its place |
| indefinite | `-\cos(x) + C`: the answer is the family, not one representative of it |
| did not close | SymPy returned the computation undone, and the label says so |
| did not finish | the time limit ran out |

Treating these as the same thing is the usual mistake. And a pending site blocks
evaluation just as it blocks reading: nothing is computed on what nobody has read.

## Domain modules

Sucuri reads and disambiguates; it knows neither Galois theory nor differential
geometry. What makes an expression useful comes from modules, which offer
operations and return **results that are not expressions**: tables, verdicts,
certificates. It is the difference between hosting calculators and hosting areas of
mathematics.

```python
import sucuri
import sucuri.modules

doc = sucuri.Document(independent_variable='x').primes_are_derivatives()
e = doc.read(r"y'' = x y")            # Airy
resolver = sucuri.modules.load("resolver")
resolver.operations["resolver"].run(e)
# solução  [estabelecida]
#   y{\left(x \right)} = C_{1} Ai\left(x\right) + C_{2} Bi\left(x\right) …
korvin = sucuri.modules.load("korvin")          # only with KORVIN installed
korvin.operations["não-integrabilidade"].run(e)
```

As the rest of the Python API, the modules answer in Portuguese.

`resolver` ships with Sucuri; `korvin` is an adapter, and needs the external
KORVIN package (without it, `load("korvin")` raises `ModuleNotFoundError`). The
two answer different questions:

| | question |
|---|---|
| `resolver` | can I find a solution? |
| `korvin` | does one exist? |

`resolver` wraps `dsolve` to say what it does not say: **what kind of
answer it is**. A closed form checked by substitution, a truncated series (which is not
a solution, it is an approximation up to some order), an implicit relation, or nothing; and when
it is nothing, that not finding does not prove there is none.

```
y'' + y = 0          solution                              [established]
y'' = x y            solution                              [established]
y'' + x y' + y = 0   series (not a closed-form solution)   [not applicable]
y'' = 6 y^2          no solution found                     [not applicable]
y' = 1/(x + y^2)     solution not confirmed                [no source]
```

The third line is why the module exists: that equation is `(y' + xy)' = 0`
and **has** a closed form, with `erfi`; `dsolve` returns a series up to order 5 and
does not warn that it changed the kind of answer.

### The provenance bridge

Every module conclusion carries the origin of the criterion that produced it, and the
host **refuses to present as a conclusion** anything that comes from a criterion without
authority:

```
Riemann scheme                  [not applicable]    → it is data, it asserts nothing
necessary conditions            [established]       → primary source (Kovacic §2)
non-integrability               [no source]         → NOT PRESENTABLE
  blocked: the criterion 'symmetric power with a rational solution' has no
           declared provenance and therefore issues no verdict
```

Sucuri does not understand a line of Galois theory. It does not need to: it is enough for the module
to declare where what it asserts comes from. It is the same rule Sucuri already applies to
reading: nothing is presented with more confidence than its origin supports.

## Visual identity

In `identidade/`: logo and variants, icons from 48 to 1024 px, CSS tokens and the
reference mockup. See `identidade/IDENTITY.md`.

The logo is the anaconda (sucuri) coiled into the letter S: notation goes in at the head,
code comes out through the tail block.

## Status

Engine and interface under construction. See `sucuri/`, `sucuri/interface/` and the suite
in `tests/`.

## License

MIT — see [LICENSE](LICENSE).

## Citing

If you use Sucuri, cite it as described in [CITATION.cff](CITATION.cff). A DOI will be added.
