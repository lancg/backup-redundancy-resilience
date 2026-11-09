# Learning-adjusted redundancy: reproduction code

Code and results for the manuscript

> **When a backup stops being a backup: learning-adjusted identification cost and the limits of
> redundancy**
> Lancong Guo, Xiadong Lyu, Gan Yu, Weidong Zhang, Wei Xie

This repository contains only the code that produces the numbers and figures. It does not contain
the manuscript.

## What the code does

The model prices a sequence of removals against a defender's redundant components. Each removal costs
an execution term plus an identification term that decays as the attacker accumulates similarity-
weighted knowledge about the components already hit:

```
c(i | D) = c_f + c_0 * rho ** kappa(i, D)      kappa(i, D) = min(kmax, sum_{j in D} s(i, j))
s(i, j)  = exp(-d(i, j)**2 / (2 * lam**2))
```

The readout is `R = min{ C(a) / dK(a) : dK(a) >= delta, C(a) <= Cbar }`, a price per unit of
capability. The repository computes that price, the saturation of effective redundancy, the design
threshold between adding a backup and moving a signature, and the value of information about the
attacker's parameters.

## Quick start

```bash
pip install -r requirements.txt
python run_all.py            # everything, about 10 seconds
```

`run_all.py` runs each script in dependency order and prints a timing line per step (the whole pipeline
takes about ten seconds on a laptop). It leaves the CSVs in
`scripts/out/` and the figures in `scripts/figures_pdf/`.

To reproduce one result, run its script directly, e.g.

```bash
python scripts/g8_recompute.py
```

## What reproduces what

| Paper item | Script | Output |
|---|---|---|
| Table 2 (effective redundancy), Fig. 1(b) | `g8_recompute.py` | `scripts/out/g8_deff.csv` |
| Table 4 (RTS-79 damage ladder) | `g2_rts79_v2.py` | `scripts/out/g2_rts79.csv` |
| Table 5 (RTS-79 readout) | `g8_recompute.py` | `scripts/out/g8_rts_readout.csv` |
| Table 6 (design rule vs enumeration) | `e3_design.py` | `scripts/out/e3_design.csv` |
| Table 7 (value of information) | `g7_voi.py` | `scripts/out/g7_voi.csv` |
| Fig. 3 (design reversal) | `g1b_flip_uncertainty.py` | `scripts/out/g1b_flip.csv` |
| Fig. 5 (mean-field error) | `g6_replication.py` | `scripts/out/g6_replication.csv` |
| Figs. 1, 2, 4 | `figs_vector.py` | `scripts/figures_pdf/*.pdf` |
| Graphical abstract | `fig_ga.py` | `scripts/figures_pdf/graphical_abstract.pdf` |

The CSVs produced by one full run are committed under `scripts/out/`, so the figures can be redrawn
without repeating the searches:

```bash
cd scripts && python figs_vector.py && python fig_ga.py
```

## Requirements

Python 3.9 or later, plus

```
numpy
Pillow
```

`numpy` is used by `g7_voi.py` and `g1b_flip_uncertainty.py`; `Pillow` provides font metrics for the
figures and is imported by `e3_design.py`. No plotting library is used: the figures are written as
vector PDF by `pdfvec.py`, so the output does not depend on a matplotlib version.

## Parameters

Shared constants, identical in every script:

```
c_f   = 1.0     execution cost of one action
theta = 1.5     c_0 / c_f
rho   = 0.6     learning rate
eps_c = 0.05    residual confirmation constant
kmax  = ln(eps_c) / ln(rho) = 5.864
```

The IEEE RTS-79 data in `g8_recompute.py` and `g2_rts79_v2.py` are transcribed from a public
implementation of the test system; load (2850 MW) and installed capacity (3405 MW) are checked when
the script starts.

## How exact is each result

- **Table 2, Table 5** — closed form plus finite search; these reproduce exactly.
- **Table 4** — exhaustive for `m <= 4`; beam search of width 200 for `m = 5..7`. The beam is a
  heuristic, and a full enumeration at `m = 5..7` (about 35 s) returns the same sets for this network,
  so the reported values are exact in practice even though the search is not.
- **Table 6** — 108 design instances (three values of `theta`, two of `rho`, six cost ratios, three
  budgets). 94 of 108 match the optimal objective and 84 of 108 are the identical design; the
  difference is a tie set in which another design reaches the same objective.
- **Table 7, Fig. 3** — Monte Carlo with fixed seeds; identical output for the same numpy version.

## A note on the history

Earlier working versions of this code had two defects, both corrected before publication: an
effective redundancy measured against `pi_inf` instead of `pi_sat`, and a knowledge stock that counted
removals not yet made. The scripts here implement the corrected definitions. If you have an old copy
of the code, it is not the version that produced the results in the paper.

## License

MIT. See `LICENSE`.

## Citing

If you use this code, please cite the manuscript. `CITATION.cff` is provided for GitHub's citation
widget.
