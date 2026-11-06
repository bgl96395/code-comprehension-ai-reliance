# Study instruments (as shown to participants)

Study instruments as shown to participants (answer key removed).

**Consent to participate**: Yes, I am 18 or older, I study at AITU, I have read the description and I agree to participate / No, I do not want to participate

## About you



**Participant code**

```text
Make up any 4 digits. Do not use your birth date or part of your student ID or phone number. The code is only used to remove repeat submissions.
```

**D1. Your study programme at AITU**

Options: Software Engineering / Computer Science / Big Data Analysis / Cybersecurity / Other

**D2. Your year of study**

Options: 1st year / 2nd year / Other

**D3. Did you have programming experience before university?**

```text
For example courses, school, self-study or personal projects.
```

Options: Yes / No

**D4. Do you currently have a paid job as a software developer?**

```text
Answer No if you only have a university internship.
```

Options: Yes / No

## Use of AI assistants

AI assistants include ChatGPT, GitHub Copilot, Claude, Gemini, Cursor and similar tools. There are no right or wrong answers. Please describe what you really do.

**R1. How often do you use AI assistants to write code?**

Options: 1 - Never / 2 - Rarely / 3 - Sometimes / 4 - Often / 5 - Almost always

**R2. How often do you use AI assistants to fix errors in code?**

Options: 1 - Never / 2 - Rarely / 3 - Sometimes / 4 - Often / 5 - Almost always

**R3. How often do you use AI assistants to explain how code works?**

Options: 1 - Never / 2 - Rarely / 3 - Sometimes / 4 - Often / 5 - Almost always

**R4. Which AI assistants do you use for programming?**

Options: ChatGPT / GitHub Copilot / Claude / Gemini / Cursor / DeepSeek / Other / I do not use any

**ST1. When your code does not work during your studies, what do you usually do? Describe your first steps.**

```text
Write it as it is, in 1-3 sentences.
```

## Reading code

Here are 6 questions in Python. Please try to finish within 10 minutes.

Please work on your own: no AI, internet, running the code or help from others. Pen and paper are fine. If you do not know the answer, choose "Don't know" instead of guessing.

**C1. What does this code print?**

```text
1.  x = 5
2.  y = 2
3.  for i in range(3):
4.      x = x - y
5.      y = y + 1
6.  print(x, y)
```

Options: -1 5 / -4 5 / -4 4 / 0 4 / Don't know


**C2. What does this code print?**

```text
1.  nums = [3, 8, 2, 9, 4]
2.  result = 0
3.  for n in nums:
4.      if n % 2 == 0:
5.          result += n
6.  print(result)
```

Options: 10 / 12 / 14 / 26 / Don't know


**C3. What does this code print?**

```text
1.  def f(s):
2.      out = ""
3.      for ch in s:
4.          out = ch + out
5.      return out
6.  
7.  print(f("code"))
```

Options: code / edoc / ceod / e / Don't know


**C4. What does this code print?**

```text
1.  a = [1, 2, 3]
2.  b = a
3.  b.append(4)
4.  print(len(a))
```

Options: 3 / 4 / 7 / Runtime error / Don't know


**C5. What does this code print?**

```text
1.  words = ["a", "b", "a", "c", "a", "b"]
2.  d = {}
3.  for w in words:
4.      d[w] = d.get(w, 0) + 1
5.  print(d["a"] - d["c"])
```

Options: 1 / 2 / 3 / Runtime error / Don't know


**C6. What does this code print?**

```text
1.  def g(n):
2.      if n <= 1:
3.          return 1
4.      return n + g(n - 1)
5.  
6.  print(g(4))
```

Options: 4 / 9 / 10 / 24 / Don't know


## Finding bugs

3 tasks. Each function contains exactly one bug. Please try to finish within 10 minutes. The same rules apply: no AI, internet or running the code.

**B1. Which line contains the bug?**

```text
The function should return the average of a list, but average([2, 4, 6]) returns 2.0 instead of 4.0.

1.  def average(nums):
2.      total = 0
3.      for n in nums:
4.          total = n
5.      return total / len(nums)
```

Options: Line 1 / Line 2 / Line 3 / Line 4 / Line 5 / Don't know


**B2. Which line contains the bug?**

```text
The function should return the sum of the numbers from 1 to n inclusive, but sum_to(4) returns 6 instead of 10.

1.  def sum_to(n):
2.      total = 0
3.      for i in range(1, n):
4.          total += i
5.      return total
```

Options: Line 1 / Line 2 / Line 3 / Line 4 / Line 5 / Don't know


**B3. Which line contains the bug?**

```text
The function should return True if the list contains a repeated value, but has_duplicate([1, 2, 1]) returns False instead of True.

1.  def has_duplicate(nums):
2.      seen = []
3.      for n in nums:
4.          if n in seen:
5.              return True
6.          seen = [n]
7.      return False
```

Options: Line 1 / Line 2 / Line 3 / Line 4 / Line 5 / Line 6 / Line 7 / Don't know


## Final questions



**ST2. How did you look for the bugs in these tasks? Describe your steps.**

```text
For example, what you looked at first and how you checked your idea.
```

**H1. Did you use any of the following while solving the tasks?**

```text
Your answer has no consequences. We need it for an honest analysis.
```

Options: No, I worked on my own / Yes, an AI assistant / Yes, the internet or running the code / Yes, help from another person
