#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value of information for the design choice.

Question: if the defender cannot observe (theta, rho, lambda), how much does it cost to
commit to a design?  We compute, over the parameter box:

  R_d(M)   readout of design d under parameters M
  d*(M)    the design maximising R_d(M)
  regret(d) = E[ (R_{d*}(M) - R_d(M)) / R_{d*}(M) ]

and the value of information: the expected improvement from learning M before choosing.
Also reports the two degenerate policies (always backups, always 3+3) and the best
*unconditional* design (the one minimising expected regret).

Run: python g7_voi.py
"""

import csv
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

CF, C0, RHO, EPS = 1.0, 1.5, 0.6, 0.05
KMAX = math.log(EPS) / math.log(RHO)
TH = C0 / CF
M0, BUDGET, DMAX = 4, 6, 0.6


def kill_cost(m, u, sr):
    kh = m - u
    total = 0.0
    for j in range(kh):
        total += CF + C0 * RHO ** min(KMAX, j + u * sr)
    for j in range(u):
        total += CF + C0 * RHO ** min(KMAX, (kh + j) * sr)
    return total


def designs():
    out = []
    for nA in range(BUDGET + 1):
        for nB in range(BUDGET - nA + 1):
            if nB <= M0 + nA:
                out.append((nA, nB))
    return out


DS = designs()


def readouts(theta, rho, lam):
    sr = math.exp(-(DMAX ** 2) / (2 * lam * lam))
    kmax = math.log(0.05) / math.log(rho) if rho < 1 else 1e9
    vals = []
    for nA, nB in DS:
        m, u = M0 + nA, nB
        kh = m - u
        tot = 0.0
        # knowledge comes only from strikes already made
        for j in range(kh):
            tot += CF + theta * rho ** min(kmax, j)
        for j in range(u):
            tot += CF + theta * rho ** min(kmax, (kh + j) * sr)
        vals.append(tot)          # damage = 1, so R = total cost
    return vals


def main():
    rng = np.random.default_rng(11)
    N = 6000
    thetas = rng.uniform(0.2, 2.0, N)
    rhos = rng.uniform(0.5, 0.95, N)
    lams = np.exp(rng.uniform(math.log(0.05), math.log(1.5), N))

    R = np.array([readouts(thetas[i], rhos[i], lams[i]) for i in range(N)])   # N x D
    best = R.max(axis=1)
    idx_best = R.argmax(axis=1)

    regret = (best[:, None] - R) / best[:, None]          # N x D
    mean_regret = regret.mean(axis=0)

    # policies
    names = {"always backups": (BUDGET, 0), "always 3+3": (3, 3), "always 2+4": (2, 4)}
    rows = []
    for lab, d in names.items():
        if d not in DS:
            continue
        j = DS.index(d)
        rows.append((lab, 100 * mean_regret[j]))
    jstar = int(mean_regret.argmin())
    rows.append(("best unconditional (%d,%d)" % DS[jstar], 100 * mean_regret[jstar]))
    rows.append(("perfect information (VOI ceiling)", 0.0))

    print("  design            expected regret (%)")
    for lab, v in rows:
        print("   %-32s %6.2f" % (lab, v))

    print("\n  value of information: choosing after seeing (theta,rho,lambda)")
    print("   best unconditional regret      : %.2f%%" % (100 * mean_regret[jstar]))
    jb = DS.index((BUDGET, 0))
    j33 = DS.index((3, 3))
    print("   VOI vs always-backups          : %.2f points" % (100 * (mean_regret[jb] - mean_regret[jstar])))
    print("   VOI vs always-3+3              : %.2f points" % (100 * (mean_regret[j33] - mean_regret[jstar])))

    print("\n  how often is each policy optimal")
    for lab, d in list(names.items()) + [("best unconditional", DS[jstar])]:
        if d in DS:
            print("   %-32s %5.1f%%" % (lab, 100 * (idx_best == DS.index(d)).mean()))

    print("\n  regret by direction (worst case over draws)")
    for lab, d in names.items():
        if d in DS:
            j = DS.index(d)
            print("   %-32s mean %5.2f%%  p95 %5.2f%%  max %5.2f%%"
                  % (lab, 100 * mean_regret[j], 100 * np.quantile(regret[:, j], 0.95),
                     100 * regret[:, j].max()))

    with open(os.path.join(OUT, "g7_voi.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["design", "expected_regret_pct"])
        for lab, v in rows:
            w.writerow([lab, round(v, 3)])


if __name__ == "__main__":
    main()
