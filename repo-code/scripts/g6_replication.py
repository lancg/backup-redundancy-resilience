#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G6: replication of the mean-field approximation behind Proposition 3.

Proposition 3 replaces the full similarity matrix by its mean s. This script checks how
much that costs: for each (lambda, m) it draws N random feature sets, computes D_eff with
the full matrix, and compares with the mean-field value.

This is a verification experiment, not a new result: it quantifies the "within 1.4%"
claim of Section 5.1 and shows whether the error depends on the regime.

Run: python g6_replication.py
"""

import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

CF, C0, RHO, EPS = 1.0, 1.5, 0.6, 0.05
KMAX = math.log(EPS) / math.log(RHO)
TH = C0 / CF
SIGMA = 0.35
N_DRAW = 40


class LCG:
    def __init__(self, seed):
        self.s = seed

    def r(self):
        self.s = (1103515245 * self.s + 12345) % (2 ** 31)
        return self.s / 2 ** 31


def d_eff_full(pts, lam, m):
    """D_eff using the full pairwise similarity matrix, kill order 0..m-1."""
    total = 0.0
    for k in range(1, m):
        kappa = 0.0
        for j in range(k):
            d2 = sum((pts[k][t] - pts[j][t]) ** 2 for t in range(4))
            kappa += math.exp(-d2 / (2 * lam * lam))
        total += RHO ** min(KMAX, kappa) - EPS
    return total * TH / (1 + TH)


def d_eff_mean(sbar, m):
    return sum(RHO ** min(KMAX, j * sbar) - EPS for j in range(1, m)) * TH / (1 + TH)


def main():
    rows = []
    for lam in (0.08, 0.15, 0.30, 0.60, 1.20):
        for m in (4, 8):
            for draw in range(N_DRAW):
                rng = LCG(1000 * draw + 7)
                pts = [[0.5 + SIGMA * (rng.r() - 0.5) for _ in range(4)] for _ in range(m)]
                full = d_eff_full(pts, lam, m)
                sbar = 0.0
                cnt = 0
                for i in range(m):
                    for j in range(i):
                        d2 = sum((pts[i][t] - pts[j][t]) ** 2 for t in range(4))
                        sbar += math.exp(-d2 / (2 * lam * lam))
                        cnt += 1
                sbar /= cnt
                approx = d_eff_mean(sbar, m)
                rows.append({"lambda": lam, "m": m, "draw": draw,
                             "sbar": round(sbar, 5),
                             "D_full": round(full, 5), "D_mean": round(approx, 5),
                             "rel_err_pct": round(100 * (approx - full) / full, 3)})
    with open(os.path.join(OUT, "g6_replication.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"  {N_DRAW} draws per cell")
    print(f"  {'lambda':>7} {'m':>2} {'mean err%':>9} {'sd err%':>8} {'max |err|%':>10}")
    for lam in (0.08, 0.15, 0.30, 0.60, 1.20):
        for m in (4, 8):
            sel = [r["rel_err_pct"] for r in rows if r["lambda"] == lam and r["m"] == m]
            mu = sum(sel) / len(sel)
            sd = (sum((x - mu) ** 2 for x in sel) / (len(sel) - 1)) ** 0.5
            print(f"  {lam:>7} {m:>2} {mu:>9.2f} {sd:>8.2f} {max(abs(x) for x in sel):>10.2f}")


if __name__ == "__main__":
    main()
