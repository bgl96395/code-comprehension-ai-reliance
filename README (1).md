# Part 7: Data Analytics Pipeline

## Files
- analysis.py: cleaning, descriptive statistics, Cronbach's alpha, Spearman correlations (Objective 4), reliance tertile groups, strategy x group chi-square.
- requirements.txt: library versions.
- data/pilot_responses_TEMPLATE.csv: empty template with the required columns.
- test_fixture/SYNTHETIC_TEST_NOT_STUDY_DATA.csv: invented rows used only to check that the script runs. DELETE before submission and never cite its output.

## Steps
1. pip install -r requirements.txt
2. Copy the template to data/pilot_responses.csv and add ONLY real, consented responses. Use random codes (P01, P02...).
3. Set COMP_ITEMS and BUG_ITEMS at the top of analysis.py to match your test and answer key.
4. python analysis.py data/pilot_responses.csv results
5. Save the terminal output and the versions (python --version, pip show pandas scipy) as a screenshot for the appendix.

## Codebook
- ai_write, ai_fix, ai_explain: 1 (never) to 5 (always)
- comp_correct: integer 0 to COMP_ITEMS
- bug_found: integer 0 to BUG_ITEMS
- strategy: manual_tracing, print_or_debugger, reprompt_ai, other (double-coded; record the final decision)
