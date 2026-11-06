#!/usr/bin/env python3
"""
analysis.py  --  Analysis pipeline for the study
"Reliance on generative AI assistants and code comprehension / debugging
among novice SE students" (Assignment 3 -> Assignment 4 version).

Usage:
    python analysis.py <input.csv> <output_dir>

Input columns (one row per participant):
    participant_code, year_of_study (1/2), prog_experience (0/1),
    ai_write, ai_fix, ai_explain (1-5), comp_correct (0-6), bug_found (0-3),
    strategy (codebook category, final decision)
Optional columns (for inter-coder agreement):
    strategy_coder1, strategy_coder2

Random procedures (bootstrap, permutation) use a fixed seed, so identical
input gives identical output.

Additions in the Assignment 4 final version:
    reliance_item_frequencies.csv  (Table 8)
    reliance_group_profile.csv     (Table 13)
    ceiling_floor.csv              (share of scores at the scale maximum/minimum)
    tertile ties are split by participant_code (independent of row order),
    and the log reports how many participants share a score across groups
    a warning is logged when fewer than 10 participants are analysed
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------- config
COMP_ITEMS = 6
BUG_ITEMS = 3
LIKERT_COLS = ["ai_write", "ai_fix", "ai_explain"]
STRATEGIES = ["manual_tracing", "print_or_debugger", "reprompt_ai", "other"]
CONTROLS = ["year_of_study", "prog_experience"]
SEED = 42
N_BOOT = 5000
N_PERM = 10000
MIN_N = 3

log = []


def say(msg):
    log.append(msg)
    print(msg)


# ------------------------------------------------------------ cleaning
def clean(df):
    say(f"Raw records: {len(df)}")
    before = len(df)
    df = df.drop_duplicates("participant_code", keep="first").copy()
    say(f"Duplicate participant codes removed: {before - len(df)}")

    for c in LIKERT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        bad = df[c].notna() & ~df[c].between(1, 5)
        say(f"{c}: out-of-range (not 1-5) set to missing: {bad.sum()}")
        df.loc[bad, c] = np.nan

    for c, hi in [("comp_correct", COMP_ITEMS), ("bug_found", BUG_ITEMS)]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        bad = df[c].notna() & ~df[c].between(0, hi)
        say(f"{c}: out-of-range (not 0-{hi}) set to missing: {bad.sum()}")
        df.loc[bad, c] = np.nan

    for c, allowed in [("year_of_study", (1, 2)), ("prog_experience", (0, 1))]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        bad = df[c].notna() & ~df[c].isin(allowed)
        say(f"{c}: values not in {allowed} set to missing: {bad.sum()}")
        df.loc[bad, c] = np.nan

    for c in ["strategy", "strategy_coder1", "strategy_coder2"]:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip().str.lower()
            bad = df[c].notna() & ~df[c].isin(STRATEGIES)
            say(f"{c}: codes not in codebook (set to missing): {bad.sum()}")
            df.loc[bad, c] = pd.NA

    df["reliance"] = df[LIKERT_COLS].mean(axis=1, skipna=False)
    df["comp_prop"] = df["comp_correct"] / COMP_ITEMS
    df["bug_prop"] = df["bug_found"] / BUG_ITEMS

    complete = df[LIKERT_COLS].notna().all(axis=1)
    say(f"Incomplete reliance questionnaire (excluded from reliance analyses): "
        f"{(~complete).sum()}")
    d = df[complete].copy()
    say(f"Analysed participants: {len(d)}")
    return df, d


# ---------------------------------------------------------- statistics
def cronbach_alpha(items):
    items = items.dropna()
    k = items.shape[1]
    if len(items) < 2 or k < 2:
        return float("nan")
    var_sum = items.var(axis=0, ddof=1).sum()
    tot_var = items.sum(axis=1).var(ddof=1)
    if tot_var == 0:
        return float("nan")
    return k / (k - 1) * (1 - var_sum / tot_var)


def describe(d):
    rows = []
    for c in LIKERT_COLS + ["reliance", "comp_prop", "bug_prop"]:
        x = d[c].dropna()
        rows.append({
            "variable": c, "n": len(x),
            "mean": x.mean(), "sd": x.std(ddof=1) if len(x) > 1 else np.nan,
            "median": x.median(), "q1": x.quantile(.25), "q3": x.quantile(.75),
            "min": x.min(), "max": x.max()})
    return pd.DataFrame(rows).round(3)


def normality(d):
    rows = []
    for c in ["reliance", "comp_prop", "bug_prop"]:
        x = d[c].dropna()
        if len(x) >= 3 and x.nunique() > 1:
            w, p = stats.shapiro(x)
        else:
            w, p = float("nan"), float("nan")
        rows.append({"variable": c, "n": len(x),
                     "shapiro_W": round(w, 4), "p_value": round(p, 4)})
    return pd.DataFrame(rows)


def boot_ci(x, y, fn, rng):
    n = len(x)
    vals = []
    for _ in range(N_BOOT):
        i = rng.integers(0, n, n)
        if np.unique(x[i]).size < 2 or np.unique(y[i]).size < 2:
            continue
        vals.append(fn(x[i], y[i]))
    if len(vals) < 100:
        return float("nan"), float("nan")
    return tuple(np.percentile(vals, [2.5, 97.5]))


def correlations(d):
    rng = np.random.default_rng(SEED)
    rows = []
    for name, col in [("Code-reading", "comp_prop"), ("Bug-finding", "bug_prop")]:
        pair = d[["reliance", col]].dropna()
        n = len(pair)
        if n >= MIN_N and pair["reliance"].nunique() > 1 and pair[col].nunique() > 1:
            x, y = pair["reliance"].to_numpy(), pair[col].to_numpy()
            rho, p = stats.spearmanr(x, y)
            tau, p_tau = stats.kendalltau(x, y)
            lo, hi = boot_ci(x, y, lambda a, b: stats.spearmanr(a, b)[0], rng)
        else:
            rho = p = tau = p_tau = lo = hi = float("nan")
        rows.append({"outcome": name, "n": n,
                     "spearman_rho": rho, "p_value": p,
                     "ci95_low": lo, "ci95_high": hi,
                     "kendall_tau": tau, "kendall_p": p_tau})
    return pd.DataFrame(rows).round(4)


def ols(y, X, names):
    """OLS with intercept: coefficients, SE, t, p, 95% CI, R2, VIF."""
    n = len(y)
    Xm = np.column_stack([np.ones(n), X])
    k = Xm.shape[1]
    df_res = n - k
    if df_res < 1:
        return None
    beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
    resid = y - Xm @ beta
    rss = (resid ** 2).sum()
    tss = ((y - y.mean()) ** 2).sum()
    s2 = rss / df_res
    cov = s2 * np.linalg.pinv(Xm.T @ Xm)
    se = np.sqrt(np.diag(cov))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = beta / se
    p = 2 * stats.t.sf(np.abs(t), df_res)
    tc = stats.t.ppf(.975, df_res)
    r2 = 1 - rss / tss if tss > 0 else float("nan")
    adj = 1 - (1 - r2) * (n - 1) / df_res if tss > 0 else float("nan")
    coef = pd.DataFrame({"term": ["intercept"] + names, "coef": beta, "se": se,
                         "t": t, "p_value": p,
                         "ci95_low": beta - tc * se, "ci95_high": beta + tc * se})
    vif = []
    for j, nm in enumerate(names):
        others = np.delete(X, j, axis=1)
        if others.shape[1] == 0:
            vif.append(1.0)
            continue
        Z = np.column_stack([np.ones(n), others])
        b, *_ = np.linalg.lstsq(Z, X[:, j], rcond=None)
        r = X[:, j] - Z @ b
        tot = ((X[:, j] - X[:, j].mean()) ** 2).sum()
        r2j = 1 - (r ** 2).sum() / tot if tot > 0 else float("nan")
        vif.append(1 / (1 - r2j) if r2j < 1 else float("inf"))
    return {"coef": coef, "r2": r2, "adj_r2": adj, "n": n, "df": df_res,
            "fitted": Xm @ beta, "resid": resid,
            "vif": pd.DataFrame({"predictor": names, "vif": vif})}


def regressions(d):
    out_c, out_v, fits = [], [], {}
    preds = ["reliance"]
    for c in CONTROLS:
        if c in d.columns and d[c].dropna().nunique() > 1:
            preds.append(c)
        else:
            say(f"Regression: control '{c}' dropped (missing or no variation).")
    for name, col in [("Code-reading", "comp_prop"), ("Bug-finding", "bug_prop")]:
        sub = d[preds + [col]].dropna()
        if len(sub) <= len(preds) + 1:
            say(f"Regression {name}: not enough complete cases ({len(sub)}).")
            continue
        fit = ols(sub[col].to_numpy(float), sub[preds].to_numpy(float), preds)
        if fit is None:
            continue
        c = fit["coef"].copy()
        c.insert(0, "outcome", name)
        c["n"] = fit["n"]
        c["r2"] = fit["r2"]
        c["adj_r2"] = fit["adj_r2"]
        out_c.append(c)
        v = fit["vif"].copy()
        v.insert(0, "outcome", name)
        out_v.append(v)
        fits[name] = fit
    coef = pd.concat(out_c).round(4) if out_c else pd.DataFrame()
    vif = pd.concat(out_v).round(3) if out_v else pd.DataFrame()
    return coef, vif, fits


def chi2_stat(table):
    exp = table.sum(1, keepdims=True) * table.sum(0, keepdims=True) / table.sum()
    return ((table - exp) ** 2 / exp).sum(), exp


def strategy_comparison(d):
    note = {"text": f"Not computed: fewer than {MIN_N} analysed participants."}
    ct = None
    if len(d) >= MIN_N:
        shared = assign_reliance_groups(d)
        say(f"Reliance tertiles: ties split by participant_code; participants "
            f"sharing a score with someone in another group: {shared}")
        s = d[d["strategy"].isin(STRATEGIES)]
        ct = pd.crosstab(s["reliance_group"], s["strategy"])
        ct = ct.loc[ct.sum(axis=1) > 0, ct.sum(axis=0) > 0]
        if ct.shape[0] > 1 and ct.shape[1] > 1:
            tab = ct.to_numpy(float)
            chi2, exp = chi2_stat(tab)
            dof = (tab.shape[0] - 1) * (tab.shape[1] - 1)
            p = stats.chi2.sf(chi2, dof)
            share_small = float((exp < 5).mean())
            n = tab.sum()
            v = float(np.sqrt(chi2 / (n * (min(tab.shape) - 1))))
            # Monte-Carlo permutation p-value (valid when expected counts are small)
            rng = np.random.default_rng(SEED)
            g = pd.factorize(s["reliance_group"])[0]
            st = pd.factorize(s["strategy"])[0]
            ng, ns = g.max() + 1, st.max() + 1
            hits = 0
            for _ in range(N_PERM):
                perm = rng.permutation(st)
                t = np.zeros((ng, ns))
                np.add.at(t, (g, perm), 1)
                t = t[t.sum(1) > 0][:, t.sum(0) > 0]
                if chi2_stat(t)[0] >= chi2 - 1e-9:
                    hits += 1
            p_perm = (hits + 1) / (N_PERM + 1)
            text = (f"chi2={chi2:.3f}, df={dof}, p={p:.4f}; Cramer's V={v:.3f}; "
                    f"permutation p={p_perm:.4f} ({N_PERM} permutations); "
                    f"share of expected counts below 5: {share_small:.0%}; n={int(n)}")
            if share_small > 0.2:
                text += (" | WARNING: chi-square approximation unreliable; "
                         "use the permutation p-value / report descriptively.")
            note = {"text": text, "chi2": chi2, "dof": dof, "p": p, "V": v,
                    "p_perm": p_perm, "share_small": share_small}
        else:
            note = {"text": "Chi-square not computed: a table dimension has only one level."}
    return ct, note


def cohen_kappa(a, b):
    m = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(m) == 0:
        return float("nan"), 0
    cats = sorted(set(m["a"]) | set(m["b"]))
    t = pd.crosstab(m["a"], m["b"]).reindex(index=cats, columns=cats, fill_value=0).to_numpy(float)
    n = t.sum()
    po = np.trace(t) / n
    pe = (t.sum(1) * t.sum(0)).sum() / n ** 2
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return k, int(n)


def sensitivity(d):
    rows = []
    # (a) alternative composite without ai_explain
    alt = d[["ai_write", "ai_fix"]].mean(axis=1)
    for name, col in [("Code-reading", "comp_prop"), ("Bug-finding", "bug_prop")]:
        pair = pd.DataFrame({"x": alt, "y": d[col]}).dropna()
        if len(pair) >= MIN_N and pair["x"].nunique() > 1 and pair["y"].nunique() > 1:
            r, p = stats.spearmanr(pair["x"], pair["y"])
        else:
            r, p = float("nan"), float("nan")
        rows.append({"check": "Spearman, composite without ai_explain",
                     "outcome": name, "n": len(pair), "estimate": r, "p_value": p})
    # (b) median split, Mann-Whitney U with rank-biserial effect size
    med = d["reliance"].median()
    hi, lo = d[d["reliance"] > med], d[d["reliance"] <= med]
    for name, col in [("Code-reading", "comp_prop"), ("Bug-finding", "bug_prop")]:
        a, b = hi[col].dropna(), lo[col].dropna()
        if len(a) >= 2 and len(b) >= 2 and pd.concat([a, b]).nunique() > 1:
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            rb = 2 * u / (len(a) * len(b)) - 1
        else:
            rb, p = float("nan"), float("nan")
        rows.append({"check": "Median split (high vs low), rank-biserial r",
                     "outcome": name, "n": len(a) + len(b), "estimate": rb, "p_value": p})
    return pd.DataFrame(rows).round(4)



# ------------------------------------------------- additional outputs
LIKERT_LABELS = {1: "Never", 2: "Rarely", 3: "Sometimes", 4: "Often", 5: "Almost always"}


def reliance_item_frequencies(d):
    """Table 8: number of participants giving each response, per item."""
    rows = []
    for k, lab in LIKERT_LABELS.items():
        row = {"response": k, "label": lab}
        for c in LIKERT_COLS:
            row[c] = int((d[c] == k).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def ceiling_floor(d):
    """Share of scores at the theoretical maximum/minimum (ceiling/floor check)."""
    spec = [("ai_write", 1, 5), ("ai_fix", 1, 5), ("ai_explain", 1, 5),
            ("reliance", 1, 5), ("comp_prop", 0, 1), ("bug_prop", 0, 1)]
    rows = []
    for c, lo, hi in spec:
        x = d[c].dropna()
        n = len(x)
        row = {"variable": c, "n": n,
               "scale_min": lo, "scale_max": hi,
               "share_at_max": (x >= hi - 1e-9).mean() if n else np.nan,
               "share_at_min": (x <= lo + 1e-9).mean() if n else np.nan}
        if hi == 5:
            row["share_4_or_5"] = (x >= 4).mean() if n else np.nan
        else:
            row["share_4_or_5"] = np.nan
        rows.append(row)
    return pd.DataFrame(rows).round(3)


def assign_reliance_groups(d):
    """Tertiles of reliance. Tied scores are split by participant_code, so the
    grouping does not depend on row order. Returns the number of participants
    whose score is shared with someone in another group."""
    order = d.sort_values(["reliance", "participant_code"], kind="mergesort").index
    ranks = pd.Series(np.arange(len(order)), index=order)
    d["reliance_group"] = pd.qcut(ranks.loc[d.index], 3,
                                  labels=["low", "moderate", "high"])
    shared = 0
    for _, g in d.groupby("reliance"):
        if g["reliance_group"].nunique() > 1:
            shared += len(g)
    return shared


def reliance_group_profile(d):
    """Table 13: performance and strategy profile by reliance group."""
    rows = []
    for g in ["low", "moderate", "high"]:
        sub = d[d["reliance_group"] == g]
        if len(sub) == 0:
            continue
        strat = sub["strategy"].dropna()
        strat = strat[strat.isin(STRATEGIES)]
        if len(strat):
            vc = strat.value_counts()
            top = vc[vc == vc.max()].index.tolist()
            top_txt = " / ".join(sorted(top))
            top_n = int(vc.max())
        else:
            top_txt, top_n = "n/a", 0
        rows.append({
            "group": g, "n": len(sub),
            "reliance_min": sub["reliance"].min(), "reliance_max": sub["reliance"].max(),
            "median_comp_correct": sub["comp_correct"].median(),
            "median_comp_prop": sub["comp_prop"].median(),
            "median_bug_found": sub["bug_found"].median(),
            "median_bug_prop": sub["bug_prop"].median(),
            "n_with_strategy": len(strat),
            "most_common_strategy": top_txt, "most_common_n": top_n})
    return pd.DataFrame(rows).round(3)


# ------------------------------------------------------------- figures
def figures(d, ct, fits, outdir):
    fd = os.path.join(outdir, "figures")
    os.makedirs(fd, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.hist(d["reliance"].dropna(), bins=np.arange(1, 5.51, .5), edgecolor="black")
    ax.set(xlabel="Reliance score (mean of 3 items, 1-5)", ylabel="Participants",
           title="Distribution of AI reliance")
    fig.tight_layout(); fig.savefig(os.path.join(fd, "fig1_reliance_distribution.png"), dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    for ax, (name, col) in zip(axes, [("Code-reading", "comp_prop"), ("Bug-finding", "bug_prop")]):
        pair = d[["reliance", col]].dropna()
        jitter = np.random.default_rng(SEED).normal(0, .01, len(pair))
        ax.scatter(pair["reliance"], pair[col] + jitter, alpha=.7)
        ax.set(xlabel="Reliance score", ylabel="Proportion correct / found", title=name)
    fig.tight_layout(); fig.savefig(os.path.join(fd, "fig2_reliance_vs_performance.png"), dpi=200)
    plt.close(fig)

    if ct is not None and ct.shape[0] > 0:
        pct = ct.div(ct.sum(axis=1), axis=0) * 100
        ax = pct.plot(kind="bar", stacked=True, figsize=(6, 4), edgecolor="black")
        ax.set(xlabel="Reliance group (tertiles)", ylabel="% of group",
               title="Debugging strategy by reliance group")
        ax.legend(title="Strategy", fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.xticks(rotation=0)
        plt.tight_layout(); plt.savefig(os.path.join(fd, "fig3_strategy_by_group.png"), dpi=200)
        plt.close()

    for name, fit in fits.items():
        fig, ax = plt.subplots(figsize=(5, 3.5))
        ax.scatter(fit["fitted"], fit["resid"], alpha=.7)
        ax.axhline(0, color="black", lw=1)
        ax.set(xlabel="Fitted values", ylabel="Residuals", title=f"Residuals: {name}")
        fig.tight_layout()
        fig.savefig(os.path.join(fd, f"fig4_residuals_{name.lower().replace('-', '_')}.png"), dpi=200)
        plt.close(fig)


# ---------------------------------------------------------------- main
def main(inp, outdir):
    os.makedirs(outdir, exist_ok=True)
    raw = pd.read_csv(inp)
    df, d = clean(raw)

    alpha = cronbach_alpha(d[LIKERT_COLS])
    say(f"Cronbach's alpha: {alpha:.3f}" if not np.isnan(alpha) else "Cronbach's alpha: not computable")

    if len(d) < 10:
        say(f"WARNING: only {len(d)} analysed participants (< 10); "
            "treat all results below as descriptive, not as evidence.")

    desc = describe(d)
    norm = normality(d)
    corr = correlations(d)
    coef, vif, fits = regressions(d)
    ct, note = strategy_comparison(d)
    say("Strategy x reliance group: " + note["text"])

    if {"strategy_coder1", "strategy_coder2"} <= set(df.columns):
        k, nk = cohen_kappa(df["strategy_coder1"], df["strategy_coder2"])
        say(f"Cohen's kappa (coder 1 vs coder 2): {k:.3f} (n={nk})")
    else:
        say("Cohen's kappa: not computed (coder columns absent)")

    sens = sensitivity(d)
    item_freq = reliance_item_frequencies(d)
    ceil = ceiling_floor(d)
    profile = (reliance_group_profile(d)
               if "reliance_group" in d.columns else pd.DataFrame())

    df.to_csv(os.path.join(outdir, "cleaned_analysis_data.csv"), index=False)
    desc.to_csv(os.path.join(outdir, "descriptives.csv"), index=False)
    norm.to_csv(os.path.join(outdir, "normality_shapiro.csv"), index=False)
    corr.to_csv(os.path.join(outdir, "correlations.csv"), index=False)
    coef.to_csv(os.path.join(outdir, "regression_coefficients.csv"), index=False)
    vif.to_csv(os.path.join(outdir, "regression_vif.csv"), index=False)
    sens.to_csv(os.path.join(outdir, "sensitivity_checks.csv"), index=False)
    item_freq.to_csv(os.path.join(outdir, "reliance_item_frequencies.csv"), index=False)
    ceil.to_csv(os.path.join(outdir, "ceiling_floor.csv"), index=False)
    profile.to_csv(os.path.join(outdir, "reliance_group_profile.csv"), index=False)
    if ct is not None:
        ct.to_csv(os.path.join(outdir, "strategy_by_reliance_group.csv"))
    figures(d, ct, fits, outdir)

    say(f"Outputs written to: {outdir}")
    with open(os.path.join(outdir, "cleaning_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python analysis.py <input.csv> <output_dir>")
    main(sys.argv[1], sys.argv[2])
