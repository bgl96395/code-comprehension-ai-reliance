#!/usr/bin/env python3
"""
assemble_table17.py -- builds Table 17 (robustness results) from the three
analysis.py result folders, so no number is copied by hand.

Usage:
    python assemble_table17.py results_main results_no_help results_se_only table17_robustness.csv

A subgroup with fewer than 10 analysed participants is marked "n<10: not interpreted".
"""
import os
import sys
import pandas as pd

OUTCOMES = ["Code-reading", "Bug-finding"]
MIN_INTERPRET = 10


def fmt(est, p, label="rho"):
    if pd.isna(est):
        return "not computed"
    return f"{label} = {est:.2f}, p = {p:.3f}"


def corr_cell(folder, outcome):
    path = os.path.join(folder, "correlations.csv")
    if not os.path.exists(path):
        return "folder missing", None
    c = pd.read_csv(path)
    r = c[c["outcome"] == outcome].iloc[0]
    n = int(r["n"])
    txt = fmt(r["spearman_rho"], r["p_value"])
    if n < MIN_INTERPRET:
        txt += f" (n<{MIN_INTERPRET}: not interpreted)"
    return txt, n


def sens_cell(folder, check_prefix, outcome, label):
    path = os.path.join(folder, "sensitivity_checks.csv")
    if not os.path.exists(path):
        return "folder missing", None
    s = pd.read_csv(path)
    r = s[(s["check"].str.startswith(check_prefix)) & (s["outcome"] == outcome)].iloc[0]
    return fmt(r["estimate"], r["p_value"], label), int(r["n"])


def main(main_dir, nohelp_dir, seonly_dir, out):
    rows = []
    n_main = corr_cell(main_dir, OUTCOMES[0])[1]
    rows.append({"check": f"Main: Spearman, composite of three items (n = {n_main})",
                 **{o: corr_cell(main_dir, o)[0] for o in OUTCOMES}})
    rows.append({"check": "Composite without ai_explain",
                 **{o: sens_cell(main_dir, "Spearman", o, "rho")[0] for o in OUTCOMES}})
    rows.append({"check": "Median split, Mann-Whitney, rank-biserial r",
                 **{o: sens_cell(main_dir, "Median split", o, "r")[0] for o in OUTCOMES}})
    n_nh = corr_cell(nohelp_dir, OUTCOMES[0])[1]
    rows.append({"check": f"Excluding reported outside help (n = {n_nh})",
                 **{o: corr_cell(nohelp_dir, o)[0] for o in OUTCOMES}})
    n_se = corr_cell(seonly_dir, OUTCOMES[0])[1]
    rows.append({"check": f"Software Engineering only (n = {n_se})",
                 **{o: corr_cell(seonly_dir, o)[0] for o in OUTCOMES}})
    t = pd.DataFrame(rows)
    t.to_csv(out, index=False)
    print(t.to_string(index=False))
    print(f"\nWritten to: {out}")
    print("Fill the 'Changed or stable?' column yourself after comparing with the main row.")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
