#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vector (PDF) versions of the five figures, designed at print size (540 pt wide)."""

import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfvec import PDF

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
VEC = os.path.join(HERE, "figures_pdf")
os.makedirs(VEC, exist_ok=True)

CF, C0, RHO, EPS = 1.0, 1.5, 0.6, 0.05
KMAX = math.log(EPS) / math.log(RHO)
TH = C0 / CF
CO = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"]
GRID, INK = "#e8e8e8", "#111111"

W2, H = 540, 250            # two-panel canvas
W1 = 330                    # single-panel canvas
T_TITLE, T_AXIS, T_TICK, T_NOTE = 8.6, 8.0, 7.0, 6.6


class Ax:
    def __init__(self, pdf, box, xlim, ylim, logx=False):
        self.d, self.box, self.xlim, self.ylim, self.logx = pdf, box, xlim, ylim, logx

    def _t(self, v):
        return math.log10(v) if self.logx else v

    def X(self, v):
        x0, _, x1, _ = self.box
        a, b = self._t(self.xlim[0]), self._t(self.xlim[1])
        return x0 + (self._t(v) - a) / (b - a) * (x1 - x0)

    def Y(self, v):
        _, y0, _, y1 = self.box
        a, b = self.ylim
        return y1 - (v - a) / (b - a) * (y1 - y0)

    def frame(self, xt, yt, xlabel, ylabel):
        d = self.d
        x0, y0, x1, y1 = self.box
        for v in yt:
            d.line([(x0, self.Y(v)), (x1, self.Y(v))], GRID, 0.4)
            d.text(x0 - 3, self.Y(v) - 2.4, "%g" % v, T_TICK, anchor="right")
        for v in xt:
            d.text(self.X(v), y1 + 9, "%g" % v, T_TICK, anchor="center")
        d.rect(x0, y0, x1, y1, "#333333", None, 0.7)
        d.text((x0 + x1) / 2, y1 + 17, xlabel, T_AXIS, anchor="center")
        # rotated y label
        d.text_vertical(x0 - 26, (y0 + y1) / 2, ylabel, T_AXIS)

    def line(self, pts, color, mk=False, width=1.0, dash=None):
        d = self.d
        pp = [(self.X(a), self.Y(b)) for a, b in pts]
        d.line(pp, color, width, dash)
        if mk:
            for a, b in pp:
                d.circle(a, b, 1.1, color)

    def hline(self, v, color="#555555", label=None):
        x0, _, x1, _ = self.box
        self.line([(x0, v), (x1, v)], color, width=0.6)
        if label:
            self.d.text(x1 - 2, self.Y(v) - 2.6, label, T_TICK, color, anchor="right")

    def vline(self, v, color="#555555"):
        _, y0, _, y1 = self.box
        self.d.line([(self.X(v), y0), (self.X(v), y1)], color, 0.6)


def title(d, cx, s):
    d.text(cx, 9, s, T_TITLE, INK, bold=True, anchor="center")


def legend_row(d, x, y, items, gap=14):
    for lab, c in items:
        d.rect(x, y - 5.4, x + 9, y + 0.6, c, "white", 0.6)
        d.line([(x + 2, y - 2.4), (x + 7, y - 2.4)], c, 1.2)
        d.text(x + 12, y, lab, T_TICK)
        x += 12 + d.width(lab, T_TICK) + gap
    return x


def note(d, x, y, s):
    d.text(x, y, s, T_NOTE, "#555555")


def pi_k(k, theta):
    return (CF + theta * RHO ** min(KMAX, k - 1)) / (CF + theta)


def pi_sat(theta):
    return (CF + EPS * theta) / (CF + theta)


def d_eff(m, s):
    if s <= 0:
        return (m - 1) * TH * (1 - EPS) / (1 + TH)
    return TH / (1 + TH) * sum(RHO ** min(KMAX, j * s) - EPS for j in range(1, m))


def theta_k(k, sr):
    return TH * (RHO ** (k * sr) - RHO ** k) / (1 + TH * RHO ** k)


Y0, Y1 = 40, 186


def fig1():
    d = PDF(W2, H)
    title(d, W2 / 2, "price schedule and effective redundancy")
    a = Ax(d, (62, Y0, 258, Y1), (1, 14), (0.24, 1.03))
    for i, th in enumerate((0.5, 1.5, 3.0)):
        a.line([(k, pi_k(k, th)) for k in range(1, 15)], CO[i], mk=True)
        a.line([(1, pi_sat(th)), (14, pi_sat(th))], CO[i], width=0.8, dash="2 2")
    a.frame([1, 3, 5, 7, 9, 11, 13], [0.3, 0.5, 0.7, 0.9],
            "k (actions on one signature)", "price / first price")
    legend_row(d, 62, 20, [("θ=0.5", CO[0]), ("θ=1.5", CO[1]), ("θ=3", CO[2])], gap=10)
    d.text(250, Y0 + 11, "(a)", T_AXIS)

    b = Ax(d, (346, Y0, 520, Y1), (1, 32), (0, 9.5))
    for i, s in enumerate((0.1, 0.5, 0.9, 1.0)):
        b.line([(m, d_eff(m, s)) for m in range(1, 33)], CO[i])
    b.frame([1, 8, 16, 24, 32], [0, 2, 4, 6, 8], "m (units in the group)", "D_{eff}(rounds)")
    legend_row(d, 346, 20, [("s=0.1", CO[0]), ("s=0.5", CO[1]), ("s=0.9", CO[2]), ("s=1.0", CO[3])], gap=8)
    d.text(506, Y0 + 11, "(b)", T_AXIS)
    note(d, 62, 224, "dotted: the stopping point π_{sat} of Proposition 2, one per θ.")
    note(d, 346, 224, "θ=1.5, ρ=0.6, ε_{c}=0.05.")
    d.save(os.path.join(VEC, "fig1_price_saturation.pdf"))


def fig2():
    d = PDF(W1, H)
    title(d, W1 / 2, "design threshold")
    a = Ax(d, (66, Y0, 318, Y1), (0.001, 1.0), (0, 1.6), logx=True)
    srs = [0.001 * (1000 ** (j / 60)) for j in range(61)]
    for i, k in enumerate((1, 2, 4, 8)):
        a.line([(s, theta_k(k, s)) for s in srs], CO[i])
    a.hline(1.0, "#444444", "Θ = 1")
    a.frame([0.001, 0.01, 0.1, 1.0], [0, 0.4, 0.8, 1.2, 1.6],
            "residual similarity s_{r}", "Θ(k, s_{r})")
    legend_row(d, 66, 20, [("k=1", CO[0]), ("k=2", CO[1]), ("k=4", CO[2]), ("k=8", CO[3])], gap=10)
    note(d, 66, 220, "θ=1.5, ρ=0.6; decorrelate where a curve lies above 1.")
    note(d, 66, 230, "for k=4 the crossing is s_{r} = 0.038.")
    d.save(os.path.join(VEC, "fig2_threshold.pdf"))


def fig3():
    rows = [{"lam": float(r["lambda"]), "nA": float(r["nA"]), "nB": float(r["nB"])}
            for r in csv.DictReader(open(os.path.join(OUT, "g1b_flip.csv"), encoding="utf-8"))]
    d = PDF(W1, H)
    title(d, W1 / 2, "design reversal")
    a = Ax(d, (66, Y0, 318, Y1), (0.02, 2.0), (0, 6.5), logx=True)
    a.line([(r["lam"], r["nA"]) for r in rows], CO[0])
    a.line([(r["lam"], r["nB"]) for r in rows], CO[1])
    a.vline(0.271)
    a.frame([0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0], [0, 2, 4, 6],
            "attacker resolution λ", "optimal count")
    legend_row(d, 66, 20, [("backups added", CO[0]), ("decorrelated", CO[1])], gap=10)
    d.text(a.X(0.234) + 3, a.Y(5.2), "λ* = 0.271", T_TICK, "#444444")
    note(d, 66, 220, "θ=1.5, ρ=0.6, design budget 6, d_{max}=0.6.")
    note(d, 66, 230, "above λ*: moving signatures is wasted; below: half the budget goes to it.")
    d.save(os.path.join(VEC, "fig3_flip.pdf"))


def fig4():
    dam = [0.1168, 0.2442, 0.4358, 0.6432, 0.7600, 0.8653, 0.9326]
    d = PDF(W2, H)
    a = Ax(d, (62, Y0, 258, Y1), (0.5, 7.5), (0, 1.03))
    a.line([(i + 1, v) for i, v in enumerate(dam)], CO[0], mk=True)
    a.hline(0.5, "#666666", "δ = 0.5")
    a.frame([1, 2, 3, 4, 5, 6, 7], [0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "buses removed m", "damage ΔK")
    d.text(50, 11, "(a) RTS-79 damage curve", T_AXIS)

    b = Ax(d, (346, Y0, 520, Y1), (0.04, 3.5), (10.5, 14.0), logx=True)
    b.line([(0.05, 13.605), (0.40, 11.616), (3.0, 11.138)], CO[1], mk=True)
    b.frame([0.05, 0.2, 0.5, 1.0, 3.0], [11, 12, 13, 14],
            "attacker resolution λ", "readout R")
    d.text(334, 11, "(b) readout at δ = 0.5", T_AXIS)
    note(d, 62, 224, "exhaustive for m ≤ 4, beam search above.")
    note(d, 346, 224, "optimal set {13,15,16,18,23}, ΔK = 0.76; R falls 18%.")
    d.save(os.path.join(VEC, "fig4_rts79.pdf"))


def fig5():
    rows = list(csv.DictReader(open(os.path.join(OUT, "g6_replication.csv"), encoding="utf-8")))
    lams = [0.08, 0.15, 0.30, 0.60, 1.20]
    d = PDF(W1, H)
    title(d, W1 / 2, "mean-field error of Proposition 3")
    x0, y0, x1, y1 = 66, Y0, 318, Y1
    a = Ax(d, (x0, y0, x1, y1), (0, len(lams)), (-10.5, 6.5))

    lx = 66
    for key, lab, c in (("m4", "m = 4", CO[0]), ("m8", "m = 8", CO[1])):
        d.rect(lx, 14.6, lx + 9, 20.6, c, "white", 0.6)
        d.line([(lx + 2, 17.6), (lx + 7, 17.6)], c, 1.2)
        d.text(lx + 12, 20, "group size " + lab, T_TICK)
        lx += 12 + d.width("group size " + lab, T_TICK) + 12
    d.line([(lx, 17.6), (lx + 9, 17.6)], "#444444", 1.2)
    d.text(lx + 12, 20, "exact agreement", T_TICK)

    for v in (-10, -8, -6, -4, -2, 0, 2, 4, 6):
        d.line([(x0, a.Y(v)), (x1, a.Y(v))], GRID, 0.4)
        d.text(x0 - 3, a.Y(v) - 2.4, "%g" % v, T_TICK, anchor="right")
    d.line([(x0, a.Y(0)), (x1, a.Y(0))], "#444444", 0.6)
    d.rect(x0, y0, x1, y1, "#333333", None, 0.7)

    bw = (x1 - x0) / len(lams)
    for li, lam in enumerate(lams):
        if li:
            d.line([(x0 + bw * li, y0), (x0 + bw * li, y1)], "#f0f0f0", 0.4)
        for key, m, c in (("m4", 4, CO[0]), ("m8", 8, CO[1])):
            vals = sorted(float(r["rel_err_pct"]) for r in rows
                          if float(r["lambda"]) == lam and int(r["m"]) == m)
            n = len(vals)
            lo, q1, med, q3, hi = vals[0], vals[n // 4], (vals[(n - 1) // 2] + vals[n // 2]) / 2, \
                vals[3 * n // 4], vals[-1]
            cx = x0 + bw * (li + 0.5) + (-0.17 if key == "m4" else 0.17) * bw
            d.line([(cx, a.Y(lo)), (cx, a.Y(q1))], c, 0.7)
            d.line([(cx, a.Y(q3)), (cx, a.Y(hi))], c, 0.7)
            d.line([(cx - 3, a.Y(lo)), (cx + 3, a.Y(lo))], c, 0.7)
            d.line([(cx - 3, a.Y(hi)), (cx + 3, a.Y(hi))], c, 0.7)
            d.rect(cx - 4.5, a.Y(q3), cx + 4.5, a.Y(q1), c, "white", 0.7)
            d.line([(cx - 4.5, a.Y(med)), (cx + 4.5, a.Y(med))], c, 0.9)
        d.text(x0 + bw * (li + 0.5), y1 + 9, "%g" % lam, T_TICK, anchor="center")

    d.text((x0 + x1) / 2, y1 + 17, "attacker resolution λ", T_AXIS, anchor="center")
    d.text_vertical(x0 - 26, (y0 + y1) / 2, "relative error (%)", T_AXIS)
    note(d, 66, 218, "40 random feature draws per cell; negative means the mean-field")
    note(d, 66, 228, "form understates D_{eff}.")
    d.save(os.path.join(VEC, "fig5_replication.pdf"))


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5()
    print("wrote PDFs to", VEC)
