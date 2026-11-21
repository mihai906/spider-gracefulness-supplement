# Computer-assisted part of the proof

| Path | Contents |
| --- | --- |
| `seven/inputs/P.smt2`, `seven/proofs/P.cpc` | The 128 seven-arm failure formulas (Article eq. (4.2)), one per parity word `P`, and their CPC refutations |
| `seven/formulas.py` | Definition of those formulas (needs the `z3-solver` Python package) |
| `eight_odd/` | Odd eight-arm failure formula (Article eq. (5.5)) and its refutation |
| `eight_even_min/` | Even-minimum failure formula (Article eq. (5.6)): the fourteen original assertions, their conjunction `input.smt2`, and its refutation |
| `binder.py` | Premise binder: proves that a CPC proof's global assumption is literally the saved formula |
| `checker/` | Logos CPC checker executable and its source |
| `finite/` | Builders for the finite tables of the supplement and their data |
| `verify.py` | Runs all checks |

Use Python 3 without `-O`. No other packages or network access are
needed:

```sh
python3 verify.py --finite
python3 verify.py --arithmetic
```

`--finite` rebuilds the finite tables. It checks every printed labeling
by exact label and color inventories, the exact profile sets and the
311 seven-arm decompositions. It then confirms that the tables are
identical to those printed in the supplement.

`--arithmetic` binds each of the 130 proofs to its formula with
`binder.py`, then requires the checker to return `correct`. It also
checks that the even-minimum input is exactly the conjunction of the
fourteen original assertions. The full run takes about 15 minutes on one core. Use
`--family seven`, `--family eight-odd` or `--family eight-even-min` to
check one group.
