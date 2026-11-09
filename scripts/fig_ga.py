#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Graphical abstract: the two results that survive review, drawn as data.

Elsevier asks for a wide strip (about 1328 x 531 px, ratio 2.5:1); we emit vector PDF.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfvec import PDF

HERE = os.path.dirname(os.path.abspath(__file__))
VEC = os.path.join(HERE, "figures_pdf")
os.makedirs(VEC, exist_ok=True)

CF, C0, RHO, EPS = 1.0, 1.5, 0.6, 0.05
KMAX = math.log(EPS) / math.log(RHO)
TH = C0 / CF
BLUE, RED, GREY = "#1f77b4", "#d62728", "#555555"
GRID, INK = "#ececec", "#111111"

W, H = 540.0, 216.0
Y0, Y1 = 58, 176


def pi_k(k):
    return (CF + C0 * RHO ** min(KMAX, k - 1)) / (CF + C0)


def d_eff(m, s):
    if s <= 0:
        return (m - 1) * TH * (1 - EPS) / (1 + TH)
    return TH / (1 + TH) * sum(RHO ** min(KMAX, j * s) - EPS for j in range(1, m))


def panel(d, box, ylim, xt, yt, xlabel, ylabel, tag, note):
    x0, y0, x1, y1 = box

    def X(v, xlim):
        return x0 + (v - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0)

    def Y(v):
        return y1 - (v - ylim[0]) / (ylim[1] - ylim[0]) * (y1 - y0)

    return X, Y


def build():
    d = PDF(W, H)
    d.text(W / 2, 16, "learning reprices redundancy, and its value saturates", 11.5, INK, bold=True,
           anchor="center")

    # ---------------- panel A: the price schedule
    ax0, ay0, ax1, ay1 = 52, Y0, 248, Y1
    xlim, ylim = (1, 14), (0.24, 1.02)

    def AX(v):
        return ax0 + (v - xlim[0]) / (xlim[1] - xlim[0]) * (ax1 - ax0)

    def AY(v):
        return ay1 - (v - ylim[0]) / (ylim[1] - ylim[0]) * (ay1 - ay0)

    for v in (0.3, 0.5, 0.7, 0.9):
        d.line([(ax0, AY(v)), (ax1, AY(v))], GRID, 0.4)
        d.text(ax0 - 3, AY(v) - 2.3, "%.1f" % v, 7.0, anchor="right")
    floor = pi_k(99)
    d.line([(ax0, AY(floor)), (ax1, AY(floor))], GREY, 0.7, dash="2 2")
    pts = [(AX(k), AY(pi_k(k))) for k in range(1, 15)]
    d.line(pts, BLUE, 1.4)
    for x, y in pts[::3]:
        d.circle(x, y, 1.2, BLUE)
    d.rect(ax0, ay0, ax1, ay1, "#333333", None, 0.7)
    for v in (1, 3, 5, 7, 9, 11, 13):
        d.text(AX(v), ay1 + 8, "%d" % v, 7.0, anchor="center")
    d.text((ax0 + ax1) / 2, ay1 + 17, "k-th strike on the same signature", 7.6, anchor="center")
    d.text_vertical(ax0 - 26, (ay0 + ay1) / 2, "price / first price", 7.6)
    d.text(ax1 - 4, AY(floor) - 4, "floor", 6.8, GREY, anchor="right")

    # ---------------- panel B: effective redundancy
    bx0, by0, bx1, by1 = 336, Y0, 528, Y1
    xlim2, ylim2 = (1, 32), (0, 18.5)

    def BX(v):
        return bx0 + (v - xlim2[0]) / (xlim2[1] - xlim2[0]) * (bx1 - bx0)

    def BY(v):
        return by1 - (v - ylim2[0]) / (ylim2[1] - ylim2[0]) * (by1 - by0)

    for v in (0, 6, 12, 18):
        d.line([(bx0, BY(v)), (bx1, BY(v))], GRID, 0.4)
        d.text(bx0 - 3, BY(v) - 2.3, "%d" % v, 7.0, anchor="right")
    for s, col in ((0.0, RED), (1.0, BLUE)):
        pts = [(BX(m), BY(d_eff(m, s))) for m in range(1, 33)]
        d.line(pts, col, 1.4)
    d.line([(bx0, BY(0.68)), (bx1, BY(0.68))], BLUE, 0.6, dash="2 2")
    d.text(bx1 - 4, BY(0.68) - 4, "0.68", 6.8, BLUE, anchor="right")
    d.rect(bx0, by0, bx1, by1, "#333333", None, 0.7)
    for v in (1, 8, 16, 24, 32):
        d.text(BX(v), by1 + 8, "%d" % v, 7.0, anchor="center")
    d.text((bx0 + bx1) / 2, by1 + 17, "m units in the group", 7.6, anchor="center")
    d.text_vertical(bx0 - 26, (by0 + by1) / 2, "effective redundancy (rounds)", 7.6)

    d.line([(bx0 + 8, by0 + 18), (bx0 + 22, by0 + 18)], RED, 1.4)
    d.text(bx0 + 26, by0 + 20, "dispersed: no ceiling", 6.8)
    d.line([(bx0 + 8, by0 + 30), (bx0 + 22, by0 + 30)], BLUE, 1.4)
    d.text(bx0 + 26, by0 + 32, "identical: saturates", 6.8)

    d.text(ax0, 34, "(a) the unit price stops at a floor.", 7.8)
    d.text(bx0, 34, "(b) its value stops at a level set by similarity.", 7.8)

    out = os.path.join(VEC, "graphical_abstract.pdf")
    d.save(out)
    print("wrote", out)


if __name__ == "__main__":
    build()
