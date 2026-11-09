#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G1b + G4: locate the design flip lambda*, and propagate uncertainty in (theta, rho, lambda)
to the recommended design.

Model (single redundant group, delta = 1 so every node must be removed):
  m nodes, of which u are decorrelated with residual similarity s_r = exp(-d_max^2/2 lambda^2)
  attacker removes homogeneous nodes first, then decorrelated ones
  defender budget B_d, unit costs kappa_A = kappa_B = 1

Outputs: out/g1b_flip.csv (lambda sweep), out/g4_uncertainty.csv (Monte Carlo draws),
         out/g4_summary.csv
Run: python g1b_flip_uncertainty.py
"""

import csv
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

CF, DMAX, BUDGET, M0 = 1.0, 0.6, 6, 4


def kill_cost(m, u, sr, theta, rho):
    kmax = math.log(0.05) / math.log(rho) if rho < 1 else 1e9
    c0 = theta
    kh = m - u
    total = 0.0
    for j in range(kh):
        total += CF + c0 * rho ** min(kmax, j)          # knowledge from earlier strikes only
    for j in range(u):
        total += CF + c0 * rho ** min(kmax, (kh + j) * sr)
    return total


def best_design(theta, rho, lam):
    sr = math.exp(-(DMAX ** 2) / (2 * lam * lam))
    best = None
    for nA in range(BUDGET + 1):
        for nB in range(BUDGET - nA + 1):
            if nB > M0 + nA:
                continue
            c = kill_cost(M0 + nA, nB, sr, theta, rho)
            if best is None or c > best[0] + 1e-12:
                best = (c, nA, nB)
    return best, sr


def sweep():
    rows = []
    theta, rho = 1.5, 0.6
    for i in range(41):
        lam = 0.02 * (100 ** (i / 40))          # 0.02 -> 2
        (c, nA, nB), sr = best_design(theta, rho, lam)
        rows.append({"lambda": round(lam, 4), "s_residual": round(sr, 4),
                     "nA": nA, "nB": nB, "R": round(c, 4)})
    with open(os.path.join(OUT, "g1b_flip.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # first lambda at which the design becomes A-only
    lam_star = None
    for r in rows:
        if r["nB"] == 0:
            lam_star = r["lambda"]
            break
    print(f"  flip: B disappears at lambda* = {lam_star}")
    print(f"  design at lambda=0.05: A={rows[0]['nA']} B={rows[0]['nB']}")
    print(f"  design at lambda=2.00: A={rows[-1]['nA']} B={rows[-1]['nB']}")
    return lam_star


def uncertainty(n=4000, seed=17):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0.2, 2.0, n)
    rho = rng.uniform(0.5, 0.95, n)
    lam = np.exp(rng.uniform(math.log(0.05), math.log(1.5), n))
    rows = []
    for i in range(n):
        (c, nA, nB), sr = best_design(float(theta[i]), float(rho[i]), float(lam[i]))
        rows.append({"theta": round(float(theta[i]), 4), "rho": round(float(rho[i]), 4),
                     "lambda": round(float(lam[i]), 4),
                     "nA": nA, "nB": nB, "R": round(c, 4)})
    with open(os.path.join(OUT, "g4_uncertainty.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    nb = np.array([r["nB"] for r in rows])
    R = np.array([r["R"] for r in rows])
    summ = [
        ("P(decorrelation used at all)", round(float((nb > 0).mean()), 3)),
        ("P(decorrelation is the majority of the budget)", round(float((nb >= 4).mean()), 3)),
        ("mean nB", round(float(nb.mean()), 2)),
        ("R quantile 10%", round(float(np.quantile(R, 0.10)), 3)),
        ("R median", round(float(np.median(R)), 3)),
        ("R quantile 90%", round(float(np.quantile(R, 0.90)), 3)),
    ]
    with open(os.path.join(OUT, "g4_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["quantity", "value"])
        w.writerows(summ)
    for k, v in summ:
        print(f"  {k}: {v}")


if __name__ == "__main__":
    print("[G1b] locating the flip")
    sweep()
    print("\n[G4] uncertainty propagation, n=4000")
    uncertainty()
