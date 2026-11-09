"""Run every script in dependency order and report timings.

Usage:
    python run_all.py            # full pipeline, a few minutes
    python run_all.py --skip-fit # only the figure step (uses the committed CSVs)
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")

# (script, what it produces)
PIPELINE = [
    ("g8_recompute.py", "Table 2, Table 5, Fig. 4 data"),
    ("g2_rts79_v2.py", "Table 4 damage ladder"),
    ("e3_design.py", "Table 6 design rule"),
    ("g7_voi.py", "Table 7 value of information"),
    ("g1b_flip_uncertainty.py", "Fig. 3 data, Section 5.5 probability"),
    ("g6_replication.py", "Fig. 5 mean-field error"),
]
FIGURES = [
    ("figs_vector.py", "Figs. 1-5"),
    ("fig_ga.py", "graphical abstract"),
]


def run(script, label):
    path = os.path.join(SCRIPTS, script)
    if not os.path.exists(path):
        print("  missing: %s" % script)
        return False
    t0 = time.time()
    print("  %-28s %s ..." % (script, label), end="", flush=True)
    r = subprocess.run([sys.executable, path], cwd=SCRIPTS,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    dt = time.time() - t0
    if r.returncode != 0:
        print(" FAILED (%.1fs)" % dt)
        sys.stderr.write(r.stderr.decode("utf-8", "replace")[-800:])
        return False
    print(" ok (%.1fs)" % dt)
    return True


def main():
    skip_fit = "--skip-fit" in sys.argv
    ok = True
    if not skip_fit:
        print("computing results")
        for s, lab in PIPELINE:
            ok = run(s, lab) and ok
    print("drawing figures")
    for s, lab in FIGURES:
        ok = run(s, lab) and ok
    print("\ndone" if ok else "\nsome steps failed")
    print("CSV   -> scripts/out/")
    print("figures -> scripts/figures_pdf/")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
