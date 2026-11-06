# Codebook: debugging strategy

Unit of coding: one participant. Text coded: answer to **ST1** (what the student usually does when code has a bug).
**ST2** (steps taken in the task) is supporting text only: use it only when ST1 is empty or impossible to classify.
Assign exactly **one** code: the primary strategy.

| Code | Use when the answer says the student mainly... | Typical wording |
| --- | --- | --- |
| `manual_tracing` | reads the code and follows values or control flow by hand, in the head or on paper, without running it | "read line by line", "trace the variables", "go through the logic", "check each condition", "dry run" |
| `print_or_debugger` | runs the code to observe it: print/log statements, a debugger, breakpoints, step-through, running tests or test inputs | "add print", "console.log", "use the debugger", "run it with different inputs", "run the unit tests" |
| `reprompt_ai` | gives the code or error to an AI assistant and asks again or refines the prompt until it works | "paste the error into ChatGPT", "ask Claude/Copilot to fix it", "ask the AI again" |
| `other` | uses none of the above as the main approach, or the answer is empty, unclear or "don't know" | "search Stack Overflow", "Google the error", "ask a friend or teacher", "read the documentation", "I don't know" |

## Decision rules

1. **One code per participant.** If several strategies are named, code the one the student puts first or stresses most ("mostly", "first of all").
2. **If equal emphasis,** use the first one mentioned.
3. **Running to observe is `print_or_debugger`,** even without print statements (running tests, trying inputs).
4. **Asking an AI is `reprompt_ai`** even if the student also reads the code afterwards, when the AI is named first or as the main step.
5. **Web search, forums and documentation are `other`,** not `reprompt_ai`. An AI assistant is only an AI tool (ChatGPT, Claude, Copilot, Gemini, Cursor, DeepSeek and similar).
6. **Empty, "I don't know", jokes or off-topic text are `other`.**
7. Code the text only. Do not use the participant's other answers (reliance, scores, programme) to decide.
8. **Reading the error message or stack trace is `print_or_debugger`,** even if the student does not run the code again.

## Procedure

1. Coder 1 (Beknazar) fills `coding_coder1.csv`; Coder 2 (Bigali) fills `coding_coder2.csv`. Row order differs on purpose.
2. Work independently and do not discuss until both files are finished.
3. Run `prepare_data.py` with both files. It writes `disagreements.csv`.
4. Resolve disagreements together by discussion, applying the rules above. Save as `resolved.csv`.
5. Agreement before resolution is reported as Cohen's kappa (computed by `analysis.py`).

Coder files and `disagreements.csv` contain participants' free text. They stay on team computers only.