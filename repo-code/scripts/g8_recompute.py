#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recomputations for the v1.2 revision.

(a) D_eff with the corrected zero point (sum from k=2, so a lone target has zero).
(b) RTS-79 readout with features normalised as Section 3.3 says (min-max to [0,1]),
    reporting C, Delta K and R for every candidate set, so the table is reproducible.

Run: python g8_recompute.py
"""

import csv
import itertools
import math
import os
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

CF, C0, RHO, EPS = 1.0, 1.5, 0.6, 0.05
KMAX = math.log(EPS) / math.log(RHO)
TH = C0 / CF
PI_SAT = (CF + EPS * C0) / (CF + C0)


# ------------------------------------------------------------------ (a) D_eff
def d_eff(m, s, zero_from_k2=True):
    start = 1 if zero_from_k2 else 0
    tot = 0.0
    for k in range(start, m):
        kap = 0.0 if s <= 0 else min(KMAX, k * s)
        tot += RHO ** kap - EPS
    return tot * TH / (1 + TH)


def table_deff():
    rows = []
    for m in (2, 4, 8, 16, 32):
        row = {"m": m}
        for s in (0.1, 0.5, 0.9, 1.0):
            row["s=%.1f" % s] = round(d_eff(m, s), 3)
        row["dispersed (s=0)"] = round(d_eff(m, 0.0), 3)
        rows.append(row)
    with open(os.path.join(OUT, "g8_deff.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("  D_eff (zero when m=1), theta=1.5 rho=0.6 eps=0.05")
    print("   %3s %8s %8s %8s %8s %10s" % ("m", "s=0.1", "s=0.5", "s=0.9", "s=1.0", "dispersed"))
    for r in rows:
        print("   %3d %8.3f %8.3f %8.3f %8.3f %10.3f" % (r["m"], r["s=0.1"], r["s=0.5"],
                                                         r["s=0.9"], r["s=1.0"], r["dispersed (s=0)"]))
    return rows


# --------------------------------------------------------------- (b) RTS readout
N, SRC, SNK, NN, LOAD = 24, 24, 25, 26, 2850
BUS = [(1,2,108,138,1),(2,2,97,138,1),(3,1,180,138,1),(4,1,74,138,1),(5,1,71,138,1),
       (6,1,136,138,2),(7,2,125,138,2),(8,1,171,138,2),(9,1,175,138,1),(10,1,195,138,2),
       (11,1,0,230,3),(12,1,0,230,3),(13,3,265,230,3),(14,2,194,230,3),(15,2,317,230,4),
       (16,2,100,230,4),(17,1,0,230,4),(18,2,333,230,4),(19,1,181,230,3),(20,1,128,230,3),
       (21,2,0,230,4),(22,2,0,230,4),(23,2,0,230,3),(24,1,0,230,4)]
BRANCH = [(1,2,175),(1,3,175),(1,5,175),(2,4,175),(2,6,175),(3,9,175),(3,24,400),(4,9,175),
          (5,10,175),(6,10,175),(7,8,175),(8,9,175),(8,10,175),(9,11,400),(9,12,400),
          (10,11,400),(10,12,400),(11,13,500),(11,14,500),(12,13,500),(12,23,500),
          (13,23,500),(14,16,500),(15,16,500),(15,21,500),(15,21,500),(15,24,500),
          (16,17,500),(16,19,500),(17,18,500),(17,22,500),(18,21,500),(18,21,500),
          (19,20,500),(19,20,500),(20,23,500),(20,23,500),(21,22,500)]
GEN = [(1,20),(1,20),(1,76),(1,76),(2,20),(2,20),(2,76),(2,76),(7,100),(7,100),(7,100),
       (13,197),(13,197),(13,197),(14,0),(15,12),(15,12),(15,12),(15,12),(15,12),(15,155),
       (16,155),(18,400),(21,400),(22,50),(22,50),(22,50),(22,50),(22,50),(22,50),
       (23,155),(23,155),(23,350)]


def adjacency():
    adj = {i: {} for i in range(NN)}
    for u, v, cap in BRANCH:
        u, v = u - 1, v - 1
        adj[u][v] = adj[u].get(v, 0) + cap
        adj[v][u] = adj[v].get(u, 0) + cap
    gen = {}
    for b, p in GEN:
        if p > 0:
            gen[b - 1] = gen.get(b - 1, 0) + p
    for b, p in gen.items():
        adj[SRC][b] = adj[SRC].get(b, 0) + p
    for b, _, pd, _, _ in BUS:
        if pd > 0:
            adj[b - 1][SNK] = adj[b - 1].get(SNK, 0) + pd
    return adj


ADJ = adjacency()


def maxflow(alive):
    res = {}
    for u in alive:
        for v, c in ADJ[u].items():
            if v in alive:
                res[(u, v)] = c
    flow = 0
    while True:
        par = {SRC: None}
        dq = deque([SRC])
        while dq and SNK not in par:
            u = dq.popleft()
            for v in ADJ[u]:
                if v in alive and v not in par and res.get((u, v), 0) > 0:
                    par[v] = u
                    dq.append(v)
        if SNK not in par:
            return flow
        b, v = float("inf"), SNK
        while par[v] is not None:
            u = par[v]; b = min(b, res[(u, v)]); v = u
        v = SNK
        while par[v] is not None:
            u = par[v]; res[(u, v)] -= b
            res[(v, u)] = res.get((v, u), 0) + b; v = u
        flow += b


_C = {}


def damage(D):
    key = frozenset(D)
    if key not in _C:
        alive = set(range(NN)) - set(D)
        _C[key] = 1.0 - min(1.0, maxflow(alive) / LOAD)
    return _C[key]


def features():
    """Section 3.3: every feature min-max normalised to [0,1]."""
    X = []
    for _, typ, _, kv, area in BUS:
        X.append([(kv - 138.0) / (230.0 - 138.0), (area - 1.0) / 3.0])
    return X


X = features()


def sim(i, j, lam):
    d2 = sum((X[i][k] - X[j][k]) ** 2 for k in range(2))
    return math.exp(-d2 / (2 * lam * lam))


def seq_cost(D, lam):
    left, H, tot = list(D), [], 0.0
    while left:
        best, bc = None, None
        for v in left:
            kap = min(KMAX, sum(sim(v, u, lam) for u in H))
            c = CF + C0 * RHO ** kap
            if bc is None or c < bc:
                best, bc = v, c
        tot += bc; H.append(best); left.remove(best)
    return tot


def best_sets(max_m=5, width=200):
    """Damage-maximising set for each size (exhaustive up to 5, then beam)."""
    out = {}
    for m in range(1, min(max_m, 5) + 1):
        best, arg = 0.0, None
        for D in itertools.combinations(range(N), m):
            d = damage(D)
            if d > best:
                best, arg = d, D
        out[m] = (best, arg)
    frontier = [frozenset(out[5][1])] if 5 in out else [frozenset()]
    for m in range(6, max_m + 1):
        cand = {}
        for D in frontier:
            for v in range(N):
                if v not in D:
                    T = D | {v}
                    if T not in cand:
                        cand[T] = damage(T)
        items = sorted(cand.items(), key=lambda kv: -kv[1])
        frontier = [k for k, _ in items[:width]]
        out[m] = (items[0][1], tuple(sorted(items[0][0])))
    return out


def rts_table():
    sets = best_sets(7)
    print("\n  RTS-79, features min-max normalised (kv, area); damage-max sets")
    for m in sorted(sets):
        print("   m=%d  dK=%.4f  %s" % (m, sets[m][0], sorted(x + 1 for x in sets[m][1])))
    rows = []
    for delta in (0.3, 0.5):
        for lam in (0.05, 0.4, 3.0):
            best = None
            for m in sorted(sets):
                dk = sets[m][0]
                if dk >= delta - 1e-9:
                    D = sets[m][1]
                    C = seq_cost(D, lam)
                    r = C / dk
                    if best is None or r < best[0]:
                        best = (r, m, C, dk, sorted(x + 1 for x in D))
            rows.append({"delta": delta, "lambda": lam, "m": best[1],
                         "damage": round(best[3], 4), "cost": round(best[2], 4),
                         "R": round(best[0], 4), "set": " ".join(map(str, best[4]))})
            print("   delta=%.1f lam=%-5s m=%d  dK=%.4f  C=%7.3f  R=%7.3f  %s"
                  % (delta, lam, best[1], best[3], best[2], best[0], best[4]))
    with open(os.path.join(OUT, "g8_rts_readout.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    table_deff()
    rts_table()
