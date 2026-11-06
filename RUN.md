# Assignment 4: порядок запуска (Windows, из папки проекта)

Структура: `analysis.py`, `assemble_table17.py`, `requirements.txt`, `instruments/`, `data/` (только на вашем компьютере).

## 0. Один раз
1. `instruments\answer_key.template.json` → скопируй как `instruments\answer_key.json` и впиши правильные ответы C1–C6 и B1–B3 из настоящей формы (ключ у Мухаммеджана / в build_instruments.py). Участникам не показывать, мне не присылать.
2. `pip install -r requirements.txt`, затем `python --version` и `pip list` (для 2.6 и Appendix B).
3. Положи экспорт в `data\forms_export.csv`.
4. Проверка заголовков (покажет только названия вопросов, без ответов): `python instruments\prepare_data.py data\forms_export.csv --show-columns`.
   Заголовки должны начинаться с `Consent`, `Participant code`, `D1`…`D4`, (`D5` по желанию), `R1`…`R4`, `ST1`, (`ST2`), `H1`, `C1`…`C6`, `B1`…`B3`. Если нет, поправь префиксы в `answer_key.json` → `columns`.

## 1. Подготовка
`python instruments\prepare_data.py data\forms_export.csv data\prepared`

## 2. Кодирование (по codebook.md, независимо)
Мухаммеджан: `coding_coder1.csv`, ты: `coding_coder2.csv`. Потом:
`python instruments\prepare_data.py data\forms_export.csv data\prepared --coder1 data\prepared\coding_coder1.csv --coder2 data\prepared\coding_coder2.csv`
Вместе разберите `disagreements.csv`, сохраните как `resolved.csv`:
`python instruments\prepare_data.py data\forms_export.csv data\prepared --coder1 data\prepared\coding_coder1.csv --coder2 data\prepared\coding_coder2.csv --resolved data\prepared\resolved.csv`

## 3. Анализ
```
python analysis.py data\prepared\responses.csv results_main
python analysis.py data\prepared\responses_no_help.csv results_no_help
python analysis.py data\prepared\responses_se_only.csv results_se_only
python assemble_table17.py results_main results_no_help results_se_only table17_robustness.csv
```

## Куда что (дополнение к Handoff)
- Table 3, 5: `data\prepared\preparation_log.txt` (воронка) + `results_main\cleaning_log.txt`
- Table C1: `data\prepared\collection_by_date.csv` (даты и накопленные ответы; каналы добавляет Мухаммеджан)
- Table 6: `sample_summary.csv`; Table 8: `reliance_item_frequencies.csv`; Table 13: `reliance_group_profile.csv`
- Ceiling effect: `ceiling_floor.csv`; Table 17: `table17_robustness.csv`

## Перед сдачей
Не класть в сдаваемую папку: `data\`, `coding_*.csv`, `disagreements.csv`, `resolved.csv`, `forms_export.csv`, `answer_key.json`, `cleaned_analysis_data.csv`.
Класть: `analysis.py`, `assemble_table17.py`, `prepare_data.py`, `requirements.txt`, `instruments/` (без answer_key.json), `responses.csv`, логи, `results_*` без cleaned_analysis_data.csv.
