import os
import sys
import pandas as pd
from scipy import stats

if len(sys.argv) < 3:
    sys.exit("Usage: python analysis.py <input.csv> <output_dir>")
INPUT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

COMP_ITEMS = 6   # number of code-reading test items
BUG_ITEMS = 3    # number of bugs in the bug-finding answer key
STRATEGIES = ["manual_tracing", "print_or_debugger", "reprompt_ai", "other"]
LIKERT_COLS = ["ai_write", "ai_fix", "ai_explain"]   # 1-5 scale
REQUIRED = ["participant_code", "year_of_study", "prog_experience",
            *LIKERT_COLS, "comp_correct", "bug_found", "strategy"]

log = []
df = pd.read_csv(INPUT)

missing_cols = [c for c in REQUIRED if c not in df.columns]
if missing_cols:
    sys.exit(f"Missing columns: {missing_cols}")

log.append(f"Raw records: {len(df)}")
dup = df["participant_code"].duplicated().sum()
df = df.drop_duplicates("participant_code", keep="first")
log.append(f"Duplicate participant codes removed: {dup}")

numeric = LIKERT_COLS + ["comp_correct", "bug_found"]
for c in numeric:
    df[c] = pd.to_numeric(df[c], errors="coerce")

for c in LIKERT_COLS:
    bad = df[c].notna() & ~df[c].between(1, 5)
    log.append(f"{c}: out-of-range (not 1-5) set to missing: {bad.sum()}")
    df.loc[bad, c] = float("nan")

bad = df["comp_correct"].notna() & ~df["comp_correct"].between(0, COMP_ITEMS)
log.append(f"comp_correct out of range: {bad.sum()}")
df.loc[bad, "comp_correct"] = float("nan")
bad = df["bug_found"].notna() & ~df["bug_found"].between(0, BUG_ITEMS)
log.append(f"bug_found out of range: {bad.sum()}")
df.loc[bad, "bug_found"] = float("nan")

unknown = df["strategy"].notna() & ~df["strategy"].isin(STRATEGIES)
log.append(f"Strategy codes not in codebook (excluded from strategy analysis): {unknown.sum()}")

complete = df[LIKERT_COLS].notna().all(axis=1)
log.append(f"Incomplete reliance questionnaire (excluded from reliance analyses): {(~complete).sum()}")
d = df[complete].copy()
d["reliance"] = d[LIKERT_COLS].mean(axis=1)
d["comp_prop"] = d["comp_correct"] / COMP_ITEMS
d["bug_prop"] = d["bug_found"] / BUG_ITEMS
log.append(f"Analysed participants: {len(d)}")

# Cronbach's alpha for the reliance items
k = len(LIKERT_COLS)
if len(d) > 1:
    item_var = d[LIKERT_COLS].var(ddof=1).sum()
    total_var = d[LIKERT_COLS].sum(axis=1).var(ddof=1)
    alpha = (k / (k - 1)) * (1 - item_var / total_var) if total_var > 0 else float("nan")
else:
    alpha = float("nan")

# Descriptives
desc = []
for name, col in [("Reliance composite (1-5)", "reliance"),
                  ("Code-reading proportion correct", "comp_prop"),
                  ("Bug-finding proportion found", "bug_prop")]:
    s = d[col].dropna()
    desc.append({
        "measure": name,
        "n": len(s),
        "mean": round(s.mean(), 3) if len(s) else None,
        "sd": round(s.std(ddof=1), 3) if len(s) > 1 else None,
        "median": round(s.median(), 3) if len(s) else None,
        "iqr": round(s.quantile(0.75) - s.quantile(0.25), 3) if len(s) else None,
    })
desc_df = pd.DataFrame(desc)
desc_df.to_csv(os.path.join(OUT, "descriptives.csv"), index=False)

# Objective 4: Spearman correlations (pairwise complete cases)
corr = []
for name, col in [("Code-reading", "comp_prop"), ("Bug-finding", "bug_prop")]:
    pair = d[["reliance", col]].dropna()
    if len(pair) >= 3:
        rho, p = stats.spearmanr(pair["reliance"], pair[col])
    else:
        rho, p = float("nan"), float("nan")
    corr.append({"outcome": name, "n": len(pair),
                 "spearman_rho": round(rho, 3), "p_value": round(p, 4)})
pd.DataFrame(corr).to_csv(os.path.join(OUT, "correlations.csv"), index=False)

# Reliance groups by tertile of the composite (rank-based, robust to ties)
strategy_note = "Not computed: fewer than 3 analysed participants."
if len(d) >= 3:
    d["reliance_group"] = pd.qcut(d["reliance"].rank(method="first"), 3,
                                  labels=["low", "moderate", "high"])
    s = d[d["strategy"].isin(STRATEGIES)]
    ct = pd.crosstab(s["reliance_group"], s["strategy"])
    ct = ct.loc[ct.sum(axis=1) > 0, ct.sum(axis=0) > 0]
    ct.to_csv(os.path.join(OUT, "strategy_by_reliance_group.csv"))
    if ct.shape[0] > 1 and ct.shape[1] > 1:
        chi2, p, dof, exp = stats.chi2_contingency(ct)
        share_small = (exp < 5).mean()
        strategy_note = (f"chi2={chi2:.3f}, df={dof}, p={p:.4f}; "
                         f"share of expected counts below 5: {share_small:.0%}")
    else:
        strategy_note = "Chi-square not computed: a table dimension has only one level."

d.to_csv(os.path.join(OUT, "cleaned_analysis_data.csv"), index=False)

with open(os.path.join(OUT, "cleaning_log.txt"), "w") as f:
    f.write("\n".join(log) + "\n")
    f.write(f"Cronbach's alpha (reliance items): {alpha:.3f}\n")
    f.write(f"Strategy x reliance group: {strategy_note}\n")

print("\n".join(log))
print(f"Cronbach's alpha: {alpha:.3f}")
print(f"Strategy x reliance group: {strategy_note}")
print(f"Outputs written to: {OUT}")
