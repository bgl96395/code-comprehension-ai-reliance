"""Creates a SYNTHETIC Google-Forms-like export to test prepare_data.py end to end.
NOT STUDY DATA. Column headers follow the real form where known (from the summary
screenshots); C/B/ST/H headers are placeholders."""
import json, os
import numpy as np, pandas as pd

rng = np.random.default_rng(5)
os.makedirs("tests/synthetic", exist_ok=True)
H = {
    "ts": "Timestamp", "consent": "Consent to participate", "code": "Participant code",
    "D1": "D1. Your study programme at AITU", "D2": "D2. Your year of study",
    "D3": "D3. Did you have programming experience before university?",
    "D4": "D4. Do you currently have a paid job as a software developer?",
    "D5": "D5. Did you take part in the pilot of this survey?",
    "R1": "R1. How often do you use AI assistants to write code?",
    "R2": "R2. How often do you use AI assistants to fix errors in code?",
    "R3": "R3. How often do you use AI assistants to explain how code works?",
    "R4": "R4. Which AI assistants do you use for programming?",
    "ST1": "ST1. When your code has a bug, what do you usually do?",
    "ST2": "ST2. Describe the steps you took to find the bugs in section B.",
    "H1": "H1. Did you use any outside help during the tasks?",
    **{f"C{i}": f"C{i}. (code-reading question {i})" for i in range(1, 7)},
    **{f"B{i}": f"B{i}. (bug-finding task {i}) Which line contains the bug?" for i in range(1, 4)},
}
LIK = ["1 - Never", "2 - Rarely", "3 - Sometimes", "4 - Often", "5 - Almost always"]
KEYC = {f"C{i}": rng.choice(list("ABCD")) for i in range(1, 7)}
KEYB = {"B1": "Line 3", "B2": "Line 2", "B3": "Line 4"}
OPT = {"A": "A) option a", "B": "B) option b", "C": "C) option c", "D": "D) option d"}
ST = {"manual_tracing": "I read the code line by line and trace the values by hand.",
      "print_or_debugger": "I add print statements and run it with the debugger.",
      "reprompt_ai": "I paste the error into ChatGPT and ask again until it works.",
      "other": "I search the error on Stack Overflow."}
rows = []
codes = [f"{i:04d}" for i in rng.choice(np.arange(1000, 9999), 70, replace=False)]
for i in range(70):
    r = {h: np.nan for h in H.values()}
    r[H["ts"]] = f"2026/11/{2 + i // 20:02d} {1 + i % 11}:{i % 60:02d}:00 PM GMT+6"
    if rng.random() < 0.12:
        r[H["consent"]] = "No, I do not want to participate"
        rows.append(r); continue
    r[H["consent"]] = "Yes, I am 18 or older, I study at AITU, I have read the description and I agree to participate"
    r[H["code"]] = codes[i]
    r[H["D1"]] = rng.choice(["Software Engineering"] * 5 + ["Computer Science", "Big Data Analysis", "Cybersecurity", "Other"])
    r[H["D2"]] = rng.choice(["1st year", "2nd year", "2nd year", "Other"])
    r[H["D3"]] = rng.choice(["Yes", "No"], p=[.8, .2])
    r[H["D4"]] = rng.choice(["Yes", "No"], p=[.3, .7])
    r[H["D5"]] = rng.choice(["Yes", "No"], p=[.05, .95])
    for k in ["R1", "R2", "R3"]:
        r[H[k]] = rng.choice(LIK, p=[.05, .05, .2, .35, .35])
    r[H["R4"]] = ", ".join(rng.choice(["ChatGPT", "GitHub Copilot", "Claude", "Gemini", "Cursor", "DeepSeek", "my own tool"],
                                      size=rng.integers(1, 4), replace=False))
    strat = rng.choice(list(ST))
    r[H["ST1"]] = ST[strat]
    r[H["ST2"]] = "I looked at the lines and traced them."
    r[H["H1"]] = rng.choice(["No, I did not use any help", "Yes, I used an AI assistant"], p=[.85, .15])
    for q, k in KEYC.items():
        r[H[q]] = OPT[k] if rng.random() < .6 else rng.choice([OPT[x] for x in "ABCD" if x != k] + ["Don't know"])
    for q, k in KEYB.items():
        r[H[q]] = f"{k}: some code" if rng.random() < .6 else rng.choice(["Line 1: x", "Line 5: y", "Don't know"])
    rows.append(r)
df = pd.DataFrame(rows)
df.iloc[10, df.columns.get_loc(H["code"])] = df.iloc[3][H["code"]]     # repeat code
df.iloc[20, df.columns.get_loc(H["code"])] = "1111"                     # placeholder-like
df.to_csv("tests/synthetic/SYNTHETIC_forms_export.csv", index=False)
json.dump({"answers": {**{k: v for k, v in KEYC.items()}, **KEYB}},
          open("tests/synthetic/SYNTHETIC_answer_key.json", "w"))
print("synthetic export written:", len(df), "rows")
