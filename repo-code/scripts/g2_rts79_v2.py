#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2v2: RTS-79 with a CORRECT search.

The v1 beam sorted candidates by -capability, i.e. it kept the least-damaged
sets and expanded those. This version:
  * enumerates exhaustively for m <= 4 (C(24,4) = 10626),
  * runs a beam that sorts by damage for m = 5..7,
  * reports damage_max(m) so that the damage curve can be checked directly.

Run: python g2_rts79_v2.py
"""

import csv
import itertools
import math
import os
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

N = 24
SRC, SNK, NN = 24, 25, 26
LOAD = 2850

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
            u = par[v]
            b = min(b, res[(u, v)])
            v = u
        v = SNK
        while par[v] is not None:
            u = par[v]
            res[(u, v)] -= b
            res[(v, u)] = res.get((v, u), 0) + b
            v = u
        flow += b


CACHE = {}


def damage(D):
    key = frozenset(D)
    if key in CACHE:
        return CACHE[key]
    alive = set(range(NN)) - set(D)
    d = 1.0 - min(1.0, maxflow(alive) / LOAD)
    CACHE[key] = d
    return d


def exhaustive(m):
    best, arg = 0.0, None
    for D in itertools.combinations(range(N), m):
        d = damage(D)
        if d > best:
            best, arg = d, D
    return best, arg


def beam(m_max, width=200):
    out = {}
    frontier = [frozenset()]
    for m in range(1, m_max + 1):
        cand = {}
        for D in frontier:
            for v in range(N):
                if v not in D:
                    T = D | {v}
                    if T not in cand:
                        cand[T] = damage(T)
        items = sorted(cand.items(), key=lambda kv: -kv[1])   # DAMAGE, descending
        frontier = [k for k, _ in items[:width]]
        out[m] = (items[0][1], items[0][0])
    return out


def main():
    print("  exhaustive m<=4")
    ex = {}
    for m in range(1, 5):
        d, arg = exhaustive(m)
        ex[m] = d
        print(f"   m={m}  damage_max={d:.4f}  set={sorted(x+1 for x in arg)}")
    print("\n  beam (damage-sorted) m=5..7")
    bm = beam(7, width=250)
    for m in range(5, 8):
        print(f"   m={m}  damage_max={bm[m][0]:.4f}  set={sorted(x+1 for x in bm[m][1])}")
    print("\n  damage curve:", {m: round(ex.get(m, bm.get(m, (0,))[0]), 4)
                                 for m in range(1, 8)})


if __name__ == "__main__":
    main()
