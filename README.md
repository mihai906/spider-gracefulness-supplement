# Graceful Labelings of Seven-Arm Spiders and Two Eight-Arm Families

Bogdan Dumitru and Mihai Nacu  
Faculty of Mathematics and Computer Science, University of Bucharest

Supporting material for the article.

## Results

- Every spider with at most seven nonunit arms, plus any number of unit
  arms, is graceful. In particular, every seven-arm spider is graceful.
- Every spider with at most eight nonunit arms, all of odd length, plus
  any number of unit arms, is graceful.
- A spider with one even shortest arm `a >= 2`, seven odd arms longer
  than `a`, and any number of unit arms is graceful.

## Contents

| Path | Contents |
| --- | --- |
| `spider_gracefulness_v2_supplement.pdf` | Technical supplement |
| `supplement_source/` | LaTeX source of the supplement |
| `data/affine/` | Affine construction data |
| `proof/` | Computer-assisted part of the proof |

## Checking the proof

From `proof/`, with Python 3:

```sh
python3 verify.py --finite
python3 verify.py --arithmetic
```
