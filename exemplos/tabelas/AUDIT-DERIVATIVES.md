*[Versão em português](AUDITORIA-DERIVADAS.md)*

# A table of derivatives against Sucuri

**Source.** `en.wikipedia.org/wiki/Differentiation_rules`, via the wikitext
API — the LaTeX as the author wrote it, not the rendered HTML, which is already
interpretation. 66 claims, extracted by `baixar.py` and saved to
`tabela.json`. Audited by `auditoria.py`.

The table is external on purpose. A table written by whoever writes the reader
tests the reader against itself; this one was written by other people, for another purpose, and
so it uses notation nobody here would have thought to anticipate.

## What is asked of each entry

Two questions, in this order, and the order matters:

1. does Sucuri **read** the entry? — that is what Sucuri promises;
2. is the entry **true**? — that is what SymPy computes.

And a third outcome, the only unacceptable one: Sucuri reads it, reads it **wrong**, and does not
say so. That is what the program exists against.

## Result

|                             | before | after |     |
|-----------------------------|------:|-------:|-----|
| proved                      |    17 | **27** | read and verified |
| proved except at isolated points | — |      1 | holds except where the table implies it (x ≠ 0) |
| **misread**                 |    11 |  **2** | the unacceptable outcome |
| refused (question)          |     6 |      4 | Sucuri asked instead of guessing |
| not read                    |     9 |     17 | honest refusal: notation outside the parser |
| not closed                  |     3 |     11 | refers to a definition given in the prose |
| refuted                     |    20 |      4 | good reading, equality does not close |

The "after" column already includes what the **table of integrals** demanded next —
`\left|`, `{a \over b}`, Euler's `e` and the list of known functions. See
`AUDIT-INTEGRALS.md`.

The growth of "not read" is the main improvement, not a regression: it now holds the
entries that used to silently turn into garbage and now stop with an error. The column that
had to shrink — "misread" — shrank from 11 to 2.

## The three defects the table found

### 1. The internal marker leaked into the output — `f'(x)`

`f'(x)` came out as `Z_{0}(x)`. The marker Sucuri inserts in place of an
ambiguous site is a **symbol**; written before a parenthesis, ` Z_{0} (x)`, the
parser reads it as an **applied function**, and the substitution back, which looked for the symbol,
did not match. The marker went on to the output, and the computation carried on with it.

`f'(x)` is the most common notation in the whole table. The suite did not have it: the tests
used `y''` and `\varphi''`, always without an argument.

Fixed: the prime swallows the argument, and the reading distinguishes the two cases the
notation lumps together —

    f'(x)     derivative of f, evaluated at x      → Derivative(f(x), x)
    f'(u)     derivative of f, evaluated at u      → Subs(Derivative(f(z),z), z, u)

which are **not** the same thing, and writing them as if they were would be the usual
silent error. With this, the table's chain rule closes.

### 2. A prime over a group took the whole equation with it — `(f+g)'`

The prime in `(f+g)'` does not belong to the letter `g`: it belongs to the whole parenthesis. The detector only
knew primes over a symbol, so it did not see the site — and what happens next is
worse than not seeing it:

```python
>>> parse_latex("(f + g)' = a")
f + g
```

SymPy's parser swallows the prime, the equals sign and the whole right-hand side, and
returns the leftover piece without saying anything. Half the equation disappears.

Fixed: a prime over a group is a site, with the inside read recursively under the
same conventions. The table's quotient rule, `\left(\frac f g\right)'`,
closes.

### 3. A macro the parser does not understand becomes a symbol, silently

SymPy's LaTeX parser does not refuse what it does not know — it degrades:

```python
>>> parse_latex(r"\coth x")                      coth*x
>>> parse_latex(r"{1 \over x}")                  1*(over*x)
>>> parse_latex(r"\operatorname{arccsc} x")      operatorname*(x*(a*(r*(c*(c*(c*s))))))
```

The function name becomes a symbol named after the macro, or the product of the letters
of the name. The computation goes on, the result is garbage, and nothing in the output says so. Of the 20 entries
the audit reported as "refuted", 18 were this: they had never been read.

Fixed with a general barrier: **a macro that reappears in the output as a symbol
of the same name was degraded** — except the Greek alphabet and a handful of special
letters, which become symbols by right. `NotacaoNaoReconhecida`, and it stops.

The same barrier catches defect 1 from the other side: a Sucuri marker in the output
is also an error, and says whose fault it is.

## What remains open

### The operator form, `\frac{d}{dx}`, is not a Sucuri site

This is the most uncomfortable finding: **the 23 proved entries went through a
reading Sucuri never declared.** `\frac{d}{dx}\sin x` works because SymPy's
grammar has a rule for that form — not because anyone here
recognized it. The Leibniz detector requires a function in the numerator
(`\frac{df}{dx}`) and does not see `\frac{d}{dx}`.

Where SymPy's grammar does not reach, the silence returns:

```python
>>> parse_latex(r"\frac{d^n}{dx^n}[f(x)g(x)]")
(d**n/(dx**n))*(f(x)*g(x))
```

— the symbolic order `n` defeats the rule, and the derivative becomes a literal fraction of
symbols multiplying the rest. These are the only two entries still coming out
**misread**.

By the project's doctrine, a reading nobody declared should not pass,
even when it is right. The fix is a detector for the operator form, with the
same two readings as the others.

### Functions the parser does not know are still only refused

Of the "not read" entries, most are a single family:
`\operatorname{arsinh}`, `\coth`, `\operatorname{sech}` — functions SymPy
**has** (`asinh`, `coth`, `sech`) and the LaTeX parser does not know.

Translating would not be guessing; `arsinh` is the inverse hyperbolic sine, period.
But, unlike `\over`, the translation is not from LaTeX to LaTeX: it needs the
marker mechanism, capturing the argument and care with `\coth^2 x`, which
is `(\coth x)^2`. Left for when there is demand.

### `\arctan(y,x)` is read as `arctan(y)`

```
\frac{\partial \arctan(y,x)}{\partial y} = \frac{x}{x^2 + y^2}     → refuted
```

The entry is right: it is the two-argument `atan2`. SymPy's parser read only
the first and threw away the second, without saying anything — one more of its silences, and one
the degraded-macro barrier does not catch, because no strange symbol
appears in the output. It would take checking the arity against what was written.

### Two entries do not close because what the page says around them is missing

`\frac{dx}{dy} = 1/\frac{dy}{dx}` calls for the inverse function theorem, and
`\frac{d}{dx}W(x)` calls for the relation that defines the W function. Neither is
readable outside the page, and neither is a defect of the reader.

## The six refusals, which are right

Sucuri asked instead of guessing on six entries, and the six questions
are good:

- `\frac{d(fg)}{dx}` — is `d(` `d` applied to `fg`, or `d` multiplying?
- `\frac{d}{dx}(x^x)` — is `x(` application or product?
- `\frac{\partial \arctan(y,x)}{\partial y}` — `\arctan(` applied, or product?

In all three cases typography does not decide. That is exactly the use case.

## Reproducing

```bash
python derivadas.py --baixar     # network; rewrites derivadas.json
python derivadas.py              # offline; uses the versioned derivadas.json
python derivadas.py --verboso
```

The count is locked in `tests/test_tabela_de_derivadas.py`: improving is
free, getting worse has to hurt.
