# 🍔 Ultimate Burger Generator Pro

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

A bilingual (FR/EN) desktop burger generator with 3 modes: Classic, Extreme and Zodiac.

[🇫🇷 Version française](README-fr.md)

## ✨ Features
- **Classic**: 6 burger types, single/double/triple size, 4 sauces, optional extras (cheese, bacon, egg, pickles, tomato, lettuce) with calories computed.
- **Extreme**: a crazy level from 1 to 10 (the higher, the wilder), optional vegan version.
- **Zodiac**: a burger and a prediction for each of the 12 signs, based on their element.
- **🎲 Surprise me**: a random burger from any mode.
- **FR/EN switch** at any time, without losing the current burger or your selections.
- **History** (SQLite): save, view (double-click), delete. Saved burgers are re-displayed in the current language.
- **Export**: PDF, copy to clipboard, share on X/Twitter.

## 🚀 Quick start
```bash
git clone https://github.com/Lisback/UltimateBurgerGenerator.git
cd UltimateBurgerGenerator
pip install -r requirements.txt
python UBGv2.py
```
tkinter ships with Python on Windows/macOS; on Debian/Ubuntu install `python3-tk`.
Optional: drop `.png`/`.jpg` pictures in a `burger_images/` folder to see a random one with each burger.

## 🗂️ Project layout
| File | Role |
|------|------|
| `UBGv2.py` | tkinter interface only |
| `burger_logic.py` | data, generation rules, formatting (no GUI dependency) |
| `burger_store.py` | SQLite history (`burgers.db`, created next to the script) |
| `burger_export.py` | PDF export |
| `translations_fr.json`, `translations_en.json` | all displayed texts |
| `tests/` | unit tests: `python -m unittest discover tests` |

To add a language, copy a `translations_*.json`, translate it and add its code to `LANGUAGES` in `burger_logic.py` (and a button in `UBGv2.py`). The tests check that no id is missing.

## 📜 License
MIT, see [LICENCE](LICENCE).
