*[Versão em português](AUDITORIA-INTEGRAIS.md)*

# A table of integrals against Sucuri

**Source.** `en.wikipedia.org/wiki/Lists_of_integrals`, through the wikitext API.
118 claims, extracted by `integrais.py --baixar`. The table of derivatives had
already been through here (`AUDIT-DERIVATIVES.md`); this is the second, and it serves
a different question: **does what the reader learned from the first table hold
for the second, or did it only hold for that one?**

## A table of integrals is proved backwards

The entry is

    ∫ f(x) dx = F(x) + C

and the right way to check it is not to integrate — it is to **differentiate the right-hand side** and
compare with the integrand. Faster, it does not depend on the integrator getting it right, and
the constant of integration dies in the derivative, which is its fate.

For definite integrals this does not work: the right-hand side is a number. There we try to
close it symbolically and, failing that, compare numerically at randomly drawn
points — with the verdict saying, in its very name, that **this is not a proof**.

## Result

| 118 claims                            |     |                                          |
|---------------------------------------|----:|------------------------------------------|
| proved                                |  31 | derivative of the right-hand side matches the integrand |
| proved except at isolated points      |  12 | holds except where the table implies it (x ≠ 0) |
| checks numerically (not a proof)      |   4 | definite integral that closed only in the evaluator |
| **misread**                           | **0** | the unacceptable outcome                |
| refused (question)                    |  17 | Sucuri asked instead of guessing          |
| not read                              |  28 | honest refusal: notation outside the parser |
| not confirmed (numerically only)      |  14 | the verifier did not close; the reading stands |
| not closed                            |   5 | refers to a definition given in the prose |
| refuted                               |   7 | good reading, equality does not close     |

**No entry misread** — which is the column that matters, and the one the table
of derivatives had left at 11 before the fixes.

Of the 28 not read, 19 are `\operatorname{...}`; of the 7 refuted,
2 are the operator form `\frac{d^n f}{dx^n}` with symbolic order, 2 are the
scope of `\cos ax\,e^{bx}` (below), 2 are antiderivatives with `\lfloor·\rfloor`,
whose derivative is zero almost everywhere, and 1 is `∫sec x dx = ln|tan(x/2+π/4)|`,
a true classical identity that neither `simplify` nor sampling closed —
a failure of the verifier, not of the reading.

## What the table of integrals demanded

### 1. `\left|x\right|` — the same bar, written the way everybody writes it

```python
>>> parse_latex(r"\ln|x|")              log(Abs(x))
>>> parse_latex(r"\ln\left|x\right|")   LaTeXParsingError
```

SymPy's parser reads the plain bar and refuses the bar with `\left`. Since every
table writes `\left|` (it is what gives the bar the right size), this alone
reached **28 of the 118 claims**.

Fixed with a harmless rewrite, from LaTeX to LaTeX: `\left|`, `\right|`,
`\vert`, `\lvert` and `\rvert` become `|`. It is not guessing — it is the same bar.
`\Vert` and `\lVert` are left out, on purpose: those are a **norm**, and whoever
swaps one for the other swaps the meaning. There is a test for that.

### 2. `{a \over b}` — TeX's primitive fraction

It had already shown up in the table of derivatives, and was recorded there as pending
because it affected few entries. Here it reaches 8 claims, and in the derivatives it
reached about as many — together, they make the fix worth it. It is
the same kind of rewrite: `{1 \over x}` becomes `\frac{1}{x}`, and the only care
is not to confuse `\over` with `\overline`.

Together with the bar, this is the layer of **rewrites that do not change meaning**,
which runs at the end of normalization — after locating the ambiguous sites,
because rewriting earlier would shift every position.

### 3. Euler's `e` is an ambiguity, and was being read by default

This is the serious finding of the table of integrals.

```
\int e^{ax}\,dx = \frac{1}{a}e^{ax} + C     → refuted
```

A correct refutation of a wrong reading: the parser reads `e` as an ordinary
symbol, and for a symbol `e` the derivative of `e^{ax}` is `a·e^{ax}·ln(e)`, which
is not `a·e^{ax}`. The table's whole exponential family fell this way — and fell
silently, because a symbol named `e` is a perfectly well-formed reading.

And `e` **is** ambiguous: eccentricity, elementary charge, index. It became a site, with
the two readings and the corresponding document convention:

```python
doc.e_is_euler(True)      # in a table, e^{ax} is Euler
```

Without the convention, `\int e^{ax}dx` stays **pending** and Sucuri asks.

The detector only looks at an `e` that is the base of a power (`e^`). That is where it is almost always
Euler and where the wrong reading silently changes the mathematics; a loose `e` elsewhere
would be too much asking for too little finding. Two traps, both with
tests: in `ae^{ax}` there is an `a` times an `e` — juxtaposition in LaTeX is a product, and
the first detector let half the equation through with a symbol where the
other half had the number; and in `\sec` and `v_e^2` the `e` is a letter of another name.

### 4. `\log_a x` differentiates wrong, and the object looks perfect

```python
>>> cru = parse_latex(r"\log_a x")
>>> sp.diff(cru, x)
1/x                      # the ln(a) is missing
>>> sp.diff(sp.log(x, a), x)
1/(x*log(a))             # the same log, built by SymPy
```

The parser builds an **unevaluated two-argument** `log`, and that object
differentiates as if the base were `e`. This is the worst of the silences found so
far: there is no strange symbol in the output, no degraded macro, nothing
for a barrier to catch — the object looks perfect and the computation comes out false.

Fixed by rebuilding two-argument logs, which is an exact identity
(`log_b x = ln x / ln b`) and not a choice of reading.

### 5. A question that was not a question

```
'\arctan(' — application = arctan applied to the argument;
             product     = arctan multiplying the parenthesis
```

There is no reading in which `\arctan` multiplies a parenthesis. The list of names
that are never a user symbol had only `sin`, `cos`, `tan`, `exp`, `log`,
`ln` — missing the inverses, the hyperbolics, the reciprocals and `\dfrac`.
A question that is not a question spends the credibility of the ones that are.

## Two silences that were only recorded

Both come from SymPy's parser and no current barrier catches them, because in
both what comes out is a well-formed expression — just not the one that was written.

**A whole factor disappears.**

```python
>>> parse_latex(r"\frac{1}{2} \sqrt \frac{\pi}{a}")
1/2
```

A `\sqrt` without braces followed by `\frac` is summarily dropped. On its own,
`\sqrt \frac{\pi}{a}` raises an error; inside a product, it vanishes silently. These are
the Gaussians of the entire table.

**The scope of a function without parentheses.**

```python
>>> parse_latex(r"\cos ax\, e^{bx}")
cos(a*x*exp(b*x))
```

The table means `cos(ax)·e^{bx}`; the parser gave the whole product to the cosine as its
argument. And here it is not just a parser defect — **it is a genuine ambiguity**, of the
same kind as the prime and the dot: is `\sin 2x` `sin(2x)` or `sin(2)·x`? The
typography does not decide, convention decides, and convention is what this program
requires to be declared. It is the next site to implement.

Catching the first would require a check Sucuri does not do yet: **did the
parser consume the whole input?** It is the same question that would catch
`(f+g)' = a` returning `f+g`.

## What the table confirmed from the previous round

The fixes from the table of derivatives held here, and one entry uses them all:

```
\int f'(x)e^{f(x)}\,dx = e^{f(x)} + C
```

The prime with an argument (`f'(x)`) is the defect that leaked the marker; the `e` is the one
from this round. The entry closes.

## What remains open

- **`\operatorname{arsinh}` and family.** Still refused, for the same reason as in the
  previous round: translating needs the marker mechanism, not a text
  rewrite. Here it weighs more, because the table uses `\sgn` all the time.
- **`\frac{d}{dx}` as an operator** is still not a Sucuri site.
- **`\begin{cases}`.** Several entries in the table are definitions by cases. The
  parser does not read them, and the refusal is honest, but a serious table of integrals
  has them.

## Reproducing

```bash
python integrais.py --baixar     # network; rewrites integrais.json
python integrais.py              # offline; takes a few minutes on the definite ones
python integrais.py --verboso
```

The count of the indefinite integrals is locked in
`tests/test_tabela_de_integrais.py`. The definite ones are left out of the suite: they depend
on numerical quadrature and take minutes.
