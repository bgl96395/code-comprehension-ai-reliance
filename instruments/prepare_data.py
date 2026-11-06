#!/usr/bin/env python3
"""
prepare_data.py -- turns the Google Forms export into the input of analysis.py.

Runs locally only. Raw responses must never be given to an external AI service.
The script prints and logs COUNTS ONLY, never individual answers.

Stage 1 (scoring, exclusions, coder files):
    python instruments/prepare_data.py data/forms_export.csv data/prepared
    -> coding_coder1.csv, coding_coder2.csv, sample_summary.csv,
       collection_by_date.csv, preparation_log.txt

Stage 2 (after both coders filled the 'strategy' column):
    python instruments/prepare_data.py data/forms_export.csv data/prepared \
        --coder1 data/prepared/coding_coder1.csv --coder2 data/prepared/coding_coder2.csv
    -> disagreements.csv  (if there are none, the final files are written at once)

Stage 3 (after the disagreements were resolved together):
    python instruments/prepare_data.py data/forms_export.csv data/prepared \
        --coder1 ... --coder2 ... --resolved data/prepared/resolved.csv
    -> responses.csv, responses_no_help.csv, responses_se_only.csv

Utility:
    python instruments/prepare_data.py data/forms_export.csv --show-columns
    prints the column headers (question titles) only, no answers.

Answer key: instruments/answer_key.json (never show it to participants):
    {"answers": {"C1": "B", ..., "C6": "D", "B1": "Line 3", "B2": "Line 2", "B3": "Line 4"}}
An answer counts as correct if it equals the key text or starts with it
(so "B" matches "B) 42", and "Line 3" matches "Line 3: total += x").
"Don't know" never matches, so it scores 0.
Optional "columns" in the same file overrides the question-ID prefixes below
(set a value to null to skip an optional question).
"""
import argparse
import json
import os
import re
import sys

import warnings
import numpy as np
import pandas as pd

SEED_CODER1, SEED_CODER2 = 11, 22
STRATEGIES = ["manual_tracing", "print_or_debugger", "reprompt_ai", "other"]
PROGRAMMES = {"software engineering": "Software Engineering",
              "computer science": "Computer Science",
              "big data analysis": "Big Data Analysis",
              "cybersecurity": "Cybersecurity"}
KNOWN_TOOLS = ["ChatGPT", "GitHub Copilot", "Claude", "Gemini", "Cursor", "DeepSeek"]
C_ITEMS = [f"C{i}" for i in range(1, 7)]
B_ITEMS = [f"B{i}" for i in range(1, 4)]

# question-ID prefixes at the start of the form's column headers
DEFAULT_COLUMNS = {
    "consent": "Consent", "code": "Participant code",
    "programme": "D1", "year": "D2", "experience": "D3", "paid_dev": "D4",
    "pilot": "D5",                      # optional
    "ai_write": "R1", "ai_fix": "R2", "ai_explain": "R3", "tools": "R4",
    "st1": "ST1", "st2": "ST2",         # st2 optional
    "help": "H1",
    **{k: k for k in C_ITEMS + B_ITEMS},
}
OPTIONAL = {"pilot", "st2"}
TIMESTAMP_NAMES = ["timestamp", "отметка времени"]

warnings.filterwarnings("ignore", category=UserWarning)
log = []


def say(msg=""):
    log.append(msg)
    print(msg)


# ------------------------------------------------------------- helpers
def find_col(columns, prefix, role):
    pat = re.compile(rf"^{re.escape(prefix.casefold())}(?![0-9a-z])")
    hits = [c for c in columns if pat.match(str(c).strip().casefold())]
    if len(hits) != 1:
        sys.exit(f"Expected one column starting with '{prefix}' ({role}); found {len(hits)}. "
                 f"Check the column header in the CSV "
                 f"(run with --show-columns to list the headers).")
    return hits[0]


def yes_no(v):
    if pd.isna(v):
        return np.nan
    s = str(v).strip().casefold()
    if s.startswith("yes"):
        return 1.0
    if s.startswith("no"):
        return 0.0
    return np.nan


def likert(v):
    if pd.isna(v):
        return np.nan
    m = re.match(r"\s*([1-5])\b", str(v))
    return float(m.group(1)) if m else np.nan


def year_of(v):
    if pd.isna(v):
        return np.nan
    s = str(v).strip().casefold()
    if re.match(r"^(1|first)", s):
        return 1.0
    if re.match(r"^(2|second)", s):
        return 2.0
    return np.nan


def programme_of(v):
    if pd.isna(v):
        return "Other"
    s = str(v).strip().casefold()
    for k, name in PROGRAMMES.items():
        if s.startswith(k):
            return name
    return "Other"


def is_correct(ans, key):
    if pd.isna(ans):
        return False
    a, k = str(ans).strip().casefold(), str(key).strip().casefold()
    if not a or not k:
        return False
    return a == k or re.match(rf"^{re.escape(k)}(?![0-9a-z])", a) is not None


def placeholder_code(digits):
    if len(digits) != 4:
        return False
    d = [int(c) for c in digits]
    steps = {d[i + 1] - d[i] for i in range(3)}
    return len(set(d)) == 1 or steps == {1} or steps == {-1}


def load_key(path):
    if not os.path.exists(path):
        sys.exit(f"Answer key not found: {path}. Copy instruments/answer_key.template.json "
                 f"to answer_key.json and fill it from the real form.")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    answers = raw.get("answers", raw)
    missing = [q for q in C_ITEMS + B_ITEMS if q not in answers]
    if missing:
        sys.exit(f"Answer key is missing: {', '.join(missing)}")
    if any("FILL" in str(answers[q]).upper() for q in C_ITEMS + B_ITEMS):
        sys.exit("answer_key.json still contains FILL_ME placeholders.")
    cols = dict(DEFAULT_COLUMNS)
    cols.update(raw.get("columns", {}))
    return answers, cols


# ------------------------------------------------------------- stage 1
def prepare(export_path, key_path):
    raw = pd.read_csv(export_path, dtype=str, encoding="utf-8-sig")
    raw = raw.replace(r"^\s*$", np.nan, regex=True)
    answers, colmap = load_key(key_path)

    cols = {}
    for role, prefix in colmap.items():
        if prefix is None:
            continue
        if role in OPTIONAL and not any(
                re.match(rf"^{re.escape(prefix.casefold())}(?![0-9a-z])", str(c).strip().casefold())
                for c in raw.columns):
            say(f"Optional question '{prefix}' ({role}) not found: step skipped.")
            continue
        cols[role] = find_col(raw.columns, prefix, role)
    ts_col = next((c for c in raw.columns if str(c).strip().casefold() in TIMESTAMP_NAMES), None)

    say(f"Source file: {os.path.basename(export_path)}")
    say(f"Raw form submissions: {len(raw)}")
    df = pd.DataFrame(index=raw.index)
    df["consent"] = raw[cols["consent"]].map(lambda v: str(v).strip().casefold().startswith("yes")
                                             if pd.notna(v) else False)
    digits = raw[cols["code"]].fillna("").astype(str).str.replace(r"\D", "", regex=True)
    df["digits"] = digits
    df["participant_code"] = [("P" + d) if d else f"PX{i:03d}" for i, d in zip(range(len(df)), digits)]
    df["programme"] = raw[cols["programme"]].map(programme_of)
    df["year_of_study"] = raw[cols["year"]].map(year_of)
    df["prog_experience"] = raw[cols["experience"]].map(yes_no)
    df["paid_dev"] = raw[cols["paid_dev"]].map(yes_no)
    df["pilot"] = raw[cols["pilot"]].map(yes_no) if "pilot" in cols else 0.0
    for r in ["ai_write", "ai_fix", "ai_explain"]:
        df[r] = raw[cols[r]].map(likert)
    df["tools"] = raw[cols["tools"]] if "tools" in cols else np.nan
    df["used_help"] = raw[cols["help"]].map(
        lambda v: np.nan if pd.isna(v) else (0.0 if str(v).strip().casefold().startswith("no") else 1.0))
    df["comp_correct"] = sum(raw[cols[q]].map(lambda a, q=q: is_correct(a, answers[q])).astype(int)
                             for q in C_ITEMS)
    df["bug_found"] = sum(raw[cols[q]].map(lambda a, q=q: is_correct(a, answers[q])).astype(int)
                          for q in B_ITEMS)
    df["st1"] = raw[cols["st1"]].fillna("")
    df["st2"] = raw[cols["st2"]].fillna("") if "st2" in cols else ""
    dup_cols = ["programme", "year_of_study", "prog_experience", "paid_dev", "ai_write", "ai_fix",
                "ai_explain", "comp_correct", "bug_found"]

    # collection by date (counts only)
    if ts_col is not None:
        t = raw[ts_col].astype(str).str.replace(r"\s*GMT.*$", "", regex=True)
        dayfirst = t.str.contains(r"^\d{1,2}\.\d{1,2}\.\d{4}", regex=True).any()
        dt = pd.to_datetime(t, errors="coerce", dayfirst=dayfirst)
        if dt.notna().any():
            by_day = dt.dt.date.value_counts().sort_index()
            cdf = pd.DataFrame({"date": by_day.index, "responses_that_day": by_day.values})
            cdf["total_so_far"] = cdf["responses_that_day"].cumsum()
            say(f"Collection dates: {cdf['date'].iloc[0]} to {cdf['date'].iloc[-1]} "
                f"({dt.notna().sum()} timestamps parsed of {len(raw)})")
        else:
            cdf = None
            say("Timestamps could not be parsed: collection_by_date.csv not written.")
    else:
        cdf = None
        say("No timestamp column found: collection_by_date.csv not written.")

    # code quality diagnostics (information only)
    cons = df[df["consent"]]
    n_bad_fmt = int((cons["digits"].str.len() != 4).sum())
    n_pattern = int(cons["digits"].map(placeholder_code).sum())
    say(f"Participant codes not exactly 4 digits (consenting): {n_bad_fmt}")
    say(f"Codes that look like placeholders (same or sequential digits): {n_pattern} (kept, informational)")

    # funnel (Table 5 order)
    say("")
    say("Step | removed | remaining")
    remaining = df.copy()
    say(f"Raw form submissions | - | {len(remaining)}")

    def step(label, keep_mask):
        nonlocal remaining
        removed = int((~keep_mask).sum())
        remaining = remaining[keep_mask]
        say(f"{label} | {removed} | {len(remaining)}")

    step("No consent", remaining["consent"])
    step("Not in an eligible IT programme", remaining["programme"] != "Other")
    step("Not in year 1 or 2", remaining["year_of_study"].isin([1.0, 2.0]))
    step("Paid software developer (incl. unanswered)", remaining["paid_dev"] == 0.0)
    step("Took part in the pilot", remaining["pilot"] != 1.0)

    # Repeated participant codes. Participants invent their own 4-digit code, so two
    # different people can choose the same one. A repeat is removed only when its
    # background and score answers are IDENTICAL to an earlier submission with that code
    # (a real double submission). A repeat with different answers is kept as a separate
    # person and gets a suffixed code (P1234-b, P1234-c). This differs from the
    # Assignment 3 rule "same code, first kept" and is reported as a deviation.
    remaining = remaining.copy()
    keep_mask = pd.Series(True, index=remaining.index)
    seen = {}
    n_split = 0
    for idx, r in remaining.iterrows():
        code = r["participant_code"]
        sig = tuple(None if pd.isna(r[c]) else r[c] for c in dup_cols)
        if code not in seen:
            seen[code] = [sig]
        elif sig in seen[code]:
            keep_mask[idx] = False
        else:
            seen[code].append(sig)
            remaining.at[idx, "participant_code"] = f"{code}-{chr(ord('a') + len(seen[code]) - 1)}"
            n_split += 1
    say(f"Repeated codes with DIFFERENT answers, kept as separate people (code suffixed -b, -c): {n_split}")
    step("Repeat submission (identical answers to an earlier one, first kept)", keep_mask)

    elig = remaining.copy()
    n_help = int((elig["used_help"] == 1.0).sum())
    say(f"Flagged, kept in the main analysis: reported outside help | {n_help} | {len(elig)}")
    n_nohelp_unknown = int(elig["used_help"].isna().sum())
    if n_nohelp_unknown:
        say(f"Outside-help question unanswered (not in the no-help file): {n_nohelp_unknown}")
    say(f"Eligible participants: {len(elig)}")
    if len(elig) < 10:
        say("WARNING: fewer than 10 eligible participants; report results as descriptive only.")
    say(f"Programme of eligible: " + ", ".join(
        f"{k} {v}" for k, v in elig["programme"].value_counts().items()))
    return elig.reset_index(drop=True), cdf


def sample_summary(elig):
    n = len(elig)
    rows = []

    def add(ch, cat, cnt):
        rows.append({"characteristic": ch, "category": cat, "n": int(cnt),
                     "pct": round(100 * cnt / n, 1) if n else np.nan})

    for p in PROGRAMMES.values():
        add("Programme", p, (elig["programme"] == p).sum())
    add("Year", "1st year", (elig["year_of_study"] == 1).sum())
    add("Year", "2nd year", (elig["year_of_study"] == 2).sum())
    add("Prior experience", "Yes", (elig["prog_experience"] == 1).sum())
    add("Prior experience", "No", (elig["prog_experience"] == 0).sum())
    add("Reported help", "Yes", (elig["used_help"] == 1).sum())
    add("Reported help", "No", (elig["used_help"] == 0).sum())
    chosen = elig["tools"].fillna("").map(
        lambda s: {(t.strip() if t.strip() in KNOWN_TOOLS else "Other")
                   for t in str(s).split(",") if t.strip()})
    for tool in KNOWN_TOOLS + ["Other"]:
        add("AI tool used (multiple choice)", tool, chosen.map(lambda s: tool in s).sum())
    return pd.DataFrame(rows)


def write_coder_files(elig, outdir):
    for i, seed in [(1, SEED_CODER1), (2, SEED_CODER2)]:
        out = elig[["participant_code", "st1", "st2"]].sample(frac=1, random_state=seed).copy()
        out["strategy"] = ""
        out.to_csv(os.path.join(outdir, f"coding_coder{i}.csv"), index=False, encoding="utf-8-sig")
    say("Coder files written (different row order; fill the 'strategy' column independently).")


# ------------------------------------------------------------- stages 2-3
def read_coder(path, name):
    c = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    if not {"participant_code", "strategy"} <= set(c.columns):
        sys.exit(f"{name}: columns participant_code and strategy are required.")
    c["strategy"] = c["strategy"].fillna("").str.strip().str.lower()
    bad = ~c["strategy"].isin(STRATEGIES)
    if bad.any():
        sys.exit(f"{name}: {int(bad.sum())} rows have an empty or unknown strategy code. "
                 f"Allowed: {', '.join(STRATEGIES)}.")
    if c["participant_code"].duplicated().any():
        sys.exit(f"{name}: duplicated participant_code values.")
    return c.set_index("participant_code")["strategy"]


def merge_coders(elig, p1, p2):
    c1, c2 = read_coder(p1, "coder1"), read_coder(p2, "coder2")
    codes = set(elig["participant_code"])
    if set(c1.index) != codes or set(c2.index) != codes:
        sys.exit("Coder files do not contain exactly the eligible participants. "
                 "Re-run stage 1 and do not edit the participant_code column.")
    m = elig.set_index("participant_code").copy()
    m["strategy_coder1"], m["strategy_coder2"] = c1, c2
    dis = m["strategy_coder1"] != m["strategy_coder2"]
    say(f"Coder agreement before resolution: {int((~dis).sum())} of {len(m)} "
        f"({100 * (~dis).mean():.1f}%); disagreements: {int(dis.sum())} "
        f"(Cohen's kappa is computed by analysis.py)")
    return m, dis


def finalize(m, outdir):
    cols = ["participant_code", "year_of_study", "prog_experience", "programme",
            "ai_write", "ai_fix", "ai_explain", "comp_correct", "bug_found",
            "strategy", "strategy_coder1", "strategy_coder2", "used_help"]
    out = m.reset_index().sort_values("participant_code")[cols]
    for c in ["year_of_study", "prog_experience", "ai_write", "ai_fix", "ai_explain",
              "comp_correct", "bug_found", "used_help"]:
        out[c] = out[c].astype("Int64")
    out.to_csv(os.path.join(outdir, "responses.csv"), index=False)
    nh = out[out["used_help"] == 0]
    nh.to_csv(os.path.join(outdir, "responses_no_help.csv"), index=False)
    se = out[out["programme"] == "Software Engineering"]
    se.to_csv(os.path.join(outdir, "responses_se_only.csv"), index=False)
    say(f"Written: responses.csv ({len(out)}), responses_no_help.csv ({len(nh)}), "
        f"responses_se_only.csv ({len(se)})")
    for name, n in [("no_help", len(nh)), ("se_only", len(se))]:
        if n < 10:
            say(f"WARNING: responses_{name}.csv has fewer than 10 participants; "
                f"do not draw conclusions from that check.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("outdir", nargs="?")
    ap.add_argument("--coder1")
    ap.add_argument("--coder2")
    ap.add_argument("--resolved")
    ap.add_argument("--key", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 "answer_key.json"))
    ap.add_argument("--show-columns", action="store_true")
    a = ap.parse_args()

    if a.show_columns:
        hdr = pd.read_csv(a.export, nrows=0, encoding="utf-8-sig").columns
        for i, c in enumerate(hdr):
            print(f"{i:2d}  {c}")
        return
    if not a.outdir:
        sys.exit("outdir is required")
    os.makedirs(a.outdir, exist_ok=True)

    elig, cdf = prepare(a.export, a.key)
    sample_summary(elig).to_csv(os.path.join(a.outdir, "sample_summary.csv"), index=False)
    if cdf is not None:
        cdf.to_csv(os.path.join(a.outdir, "collection_by_date.csv"), index=False)

    if not (a.coder1 and a.coder2):
        write_coder_files(elig, a.outdir)
    else:
        m, dis = merge_coders(elig, a.coder1, a.coder2)
        if not dis.any():
            m["strategy"] = m["strategy_coder1"]
            finalize(m, a.outdir)
        elif not a.resolved:
            d = m[dis].reset_index()[["participant_code", "st1", "st2",
                                      "strategy_coder1", "strategy_coder2"]].copy()
            d["strategy"] = ""
            d.to_csv(os.path.join(a.outdir, "disagreements.csv"), index=False, encoding="utf-8-sig")
            say("disagreements.csv written. Resolve together, fill 'strategy', "
                "save as resolved.csv and re-run with --resolved.")
        else:
            r = pd.read_csv(a.resolved, dtype=str, encoding="utf-8-sig")
            r["strategy"] = r["strategy"].fillna("").str.strip().str.lower()
            r = r.set_index("participant_code")["strategy"]
            need = m.index[dis]
            missing = [c for c in need if c not in r.index or r[c] not in STRATEGIES]
            if missing:
                sys.exit(f"resolved.csv: {len(missing)} disagreements have no valid strategy code.")
            m["strategy"] = m["strategy_coder1"]
            m.loc[need, "strategy"] = r.loc[need]
            say(f"Resolved disagreements applied: {len(need)}")
            finalize(m, a.outdir)

    with open(os.path.join(a.outdir, "preparation_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"Log written to: {os.path.join(a.outdir, 'preparation_log.txt')}")


if __name__ == "__main__":
    main()
