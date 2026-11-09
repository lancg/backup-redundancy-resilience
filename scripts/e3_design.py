#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E3: design budget split between adding homogeneous backups (A) and
decorrelating existing nodes (B); compare the true optimum with the
one-step rule  Theta = theta (1-rho^k) / (1 + theta rho^k).

Model (single cluster, one task, delta = 1 so the whole cluster must die):
    m homogeneous-or-decorrelated nodes, u decorrelated
    cost to kill everything = m*c_f + c_0 * [ (1-rho^k)/(1-rho) + u ],  k = m - u
    A: m -> m+1, unit design cost kappa_A
    B: u -> u+1 (that node no longer benefits from learning), unit cost kappa_B

The adversary seizes the discount on the homogeneous nodes first; decorrelated
nodes never become cheaper, so their price stays c_f + c_0.

Outputs: out/e3_design.csv, out/fig_e3.png
Run: python e3_design.py
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

CF, M0 = 1.0, 4


def kill_cost(m, u, c0, rho):
    k = m - u
    return m * CF + c0 * ((1.0 - rho ** k) / (1.0 - rho) + u)


def theta_rule(k, c0, rho):
    return c0 * (1.0 - rho ** k) / (CF + c0 * rho ** k)


def optimum(c0, rho, kA, kB, budget):
    best = None
    for nA in range(0, int(budget // kA) + 1):
        for nB in range(0, int(budget // kB) + 1):
            if nA * kA + nB * kB > budget + 1e-9:
                continue
            m, u = M0 + nA, nB
            if m - u < 0:
                continue
            r = kill_cost(m, u, c0, rho)
            if best is None or r > best[0] + 1e-12:
                best = (r, nA, nB)
    return best


def greedy(c0, rho, kA, kB, budget):
    """Repeatedly buy whichever action gives more cost-to-adversary per unit budget."""
    m, u, spent = M0, 0, 0.0
    while True:
        k = m - u
        gainA = (CF + c0 * rho ** k) / kA
        gainB = (c0 * (1.0 - rho ** k)) / kB
        canA = spent + kA <= budget + 1e-9
        canB = (u < m) and spent + kB <= budget + 1e-9   # cannot decorrelate more nodes than exist
        if canA and (not canB or gainA >= gainB):
            m += 1
            spent += kA
        elif canB:
            u += 1
            spent += kB
        else:
            return kill_cost(m, u, c0, rho), m - M0, u


def run():
    rows = []
    for theta in (0.5, 1.5, 3.0):
        c0 = theta
        for rho in (0.6, 0.95):
            for ratio in (0.1, 0.3, 0.6, 1.0, 2.0, 4.0):
                kB = ratio
                kA = 1.0
                for budget in (2.0, 4.0, 8.0):
                    opt = optimum(c0, rho, kA, kB, budget)
                    grd = greedy(c0, rho, kA, kB, budget)
                    k_here = M0
                    th = theta_rule(k_here, c0, rho)
                    rows.append({
                        "theta": theta, "rho": rho, "kB_over_kA": ratio,
                        "budget": budget,
                        "opt_nA": opt[1], "opt_nB": opt[2], "opt_R": round(opt[0], 4),
                        "greedy_nA": grd[1], "greedy_nB": grd[2],
                        "greedy_R": round(grd[0], 4),
                        "regret_pct": round(100 * (opt[0] - grd[0]) / opt[0], 3),
                        "Theta_at_k4": round(th, 4),
                        "rule_says_B": ratio <= th,
                        "opt_says_B": opt[2] * kB > opt[1] * kA,
                    })
    with open(os.path.join(OUT, "e3_design.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def summarize(rows):
    print("  theta  rho   kB/kA  budget | opt(A,B)  greedy(A,B)  regret%  Theta@k4  agree")
    for r in rows:
        if r["budget"] != 4.0:
            continue
        print(f"  {r['theta']:<5} {r['rho']:<5} {r['kB_over_kA']:<6} {r['budget']:<6} | "
              f"({r['opt_nA']},{r['opt_nB']})      ({r['greedy_nA']},{r['greedy_nB']})       "
              f"{r['regret_pct']:<7}  {r['Theta_at_k4']:<8}  {r['rule_says_B']==r['opt_says_B']}")
    worst = max(rows, key=lambda r: r["regret_pct"])
    print(f"\n  max greedy regret: {worst['regret_pct']}% "
          f"(theta={worst['theta']}, rho={worst['rho']}, kB/kA={worst['kB_over_kA']}, B={worst['budget']})")
    agree = sum(1 for r in rows if r["rule_says_B"] == r["opt_says_B"]) / len(rows)
    print(f"  Theta rule agrees with the optimum direction on {100*agree:.1f}% of cells")


def figure(rows):
    from PIL import Image, ImageDraw, ImageFont
    PW, PH = 740, 500
    LX, RX, TY, BY = 95, 30, 58, 72

    def font(sz, bold=False):
        for c in (["C:/Windows/Fonts/arialbd.ttf"] if bold else []) + \
                 ["C:/Windows/Fonts/arial.ttf"]:
            try:
                return ImageFont.truetype(c, sz)
            except Exception:
                pass
        return ImageFont.load_default()

    FT, FA, FK = font(22, True), font(18), font(16)
    CO = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"]

    def panel(xlim, ylim, xt, yt, xl, yl, ti, curves, items, itempos):
        im = Image.new("RGB", (PW, PH), "white")
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = LX, TY, PW - RX, PH - BY

        def tx(x):
            return x0 + (x - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0)

        def ty(y):
            return y1 - (y - ylim[0]) / (ylim[1] - ylim[0]) * (y1 - y0)

        def bb(s, f):
            b = d.textbbox((0, 0), s, font=f)
            return b[2] - b[0], b[3] - b[1]

        for yv in yt:
            d.line([x0, ty(yv), x1, ty(yv)], fill="#e4e4e4")
            w, _ = bb("%g" % yv, FK)
            d.text((x0 - 10 - w, ty(yv) - 9), "%g" % yv, font=FK, fill="#333")
        for xv in xt:
            d.line([tx(xv), y0, tx(xv), y1], fill="#f2f2f2")
            w, _ = bb("%g" % xv, FK)
            d.text((tx(xv) - w / 2, y1 + 7), "%g" % xv, font=FK, fill="#333")
        d.rectangle([x0, y0, x1, y1], outline="#333", width=2)
        for pts, c, mk in curves:
            pp = [(int(tx(a)), int(ty(b))) for a, b in pts]
            if len(pp) > 1:
                d.line(pp, fill=c, width=3, joint="curve")
            for px, py in pp:
                if mk == "o":
                    d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=c)
                elif mk == "s":
                    d.rectangle([px - 4, py - 4, px + 4, py + 4], fill=c)
        w, _ = bb(ti, FT)
        d.text(((PW - w) / 2, 8), ti, font=FT, fill="#111")
        w, _ = bb(xl, FA)
        d.text(((PW - w) / 2, PH - 40), xl, font=FA, fill="#222")
        d.text((14, y0 - 34), yl, font=FA, fill="#222")
        lx = x0 + itempos[0] * (x1 - x0)
        ly = y0 + itempos[1] * (y1 - y0)
        lw = max(bb(s, FK)[0] for s, _ in items) + 56
        d.rectangle([lx, ly, lx + lw, ly + 24 * len(items) + 8], fill="white", outline="#bbb")
        for i, (s, c) in enumerate(items):
            yy = ly + 12 + 24 * i
            d.line([lx + 8, yy, lx + 36, yy], fill=c, width=4)
            d.text((lx + 44, yy - 9), s, font=FK, fill="#222")
        return im

    # (a) share of budget spent on B vs kB/kA, for three theta (budget=8)
    curves, items = [], []
    for i, theta in enumerate((0.5, 1.5, 3.0)):
        pts = []
        for ratio in (0.1, 0.3, 0.6, 1.0, 2.0, 4.0):
            r = next(x for x in rows if x["theta"] == theta and x["rho"] == 0.6
                     and x["kB_over_kA"] == ratio and x["budget"] == 8.0)
            share = r["opt_nB"] * ratio / 8.0
            pts.append((ratio, share))
        curves.append((pts, CO[i], "o"))
        items.append(("theta=%.1f" % theta, CO[i]))
    pa = panel((0.05, 4.2), (0, 1.05), [0.1, 0.5, 1, 2, 4], [0, 0.25, 0.5, 0.75, 1.0],
               "kB / kA  (unit cost of decorrelation)", "budget share on B",
               "(a)  optimal split, rho=0.6, budget=8", curves, items, (0.55, 0.72))

    # (b) rule threshold Theta vs k for three theta
    curves, items = [], []
    ks = [1, 2, 3, 4, 5, 6, 7, 8]
    for i, theta in enumerate((0.5, 1.5, 3.0)):
        pts = [(k, theta_rule(k, theta, 0.6)) for k in ks]
        curves.append((pts, CO[i], "o"))
        items.append(("theta=%.1f" % theta, CO[i]))
    pb = panel((0.5, 8.5), (0, 3.2), [1, 2, 3, 4, 5, 6, 7, 8], [0, 1, 2, 3],
               "k (homogeneous strikes already made)", "Theta = kB / kA",
               "(b)  switch threshold, rho=0.6", curves, items, (0.05, 0.72))

    canvas = Image.new("RGB", (2 * PW + 20, PH + 40), "white")
    canvas.paste(pa, (5, 20))
    canvas.paste(pb, (PW + 10, 20))
    canvas.save(os.path.join(OUT, "fig_e3.png"))
    print("  figure -> out/fig_e3.png")


if __name__ == "__main__":
    rows = run()
    summarize(rows)
    figure(rows)
