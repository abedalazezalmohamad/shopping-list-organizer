# Shopping List Organizer

A command-line tool that plans your shopping trip **by store section** and tells you **before checkout** whether you are within your budget.

COE203 - Project 1

## The Problem

Students and families on a fixed monthly budget usually find out they overspent only at the cash register. A paper list also does not follow the layout of the store, so people walk back and forth between aisles and forget items.

**Shopping List Organizer** solves both problems:

*   Items are grouped by **store section** (vegetables, dairy, meat, ...), so you go through each aisle once.
*   Every item has a **quantity** and a **unit price**, so the tool calculates the cost of each section and the **total**.
*   You set a **budget**, and the tool warns you if the list is over budget, while you can still remove items.

## Repository Structure

```
shopping-list-organizer/
├── shopping_list.py        # The CLI program (all features)
├── tests/
│   └── test_shopping_list.py   # Automated tests (unittest)
├── contributions/          # One file per team member explaining their contribution
├── README.md               # This file
└── .gitignore              # Keeps generated data files out of the repo
```

| File / Folder | Purpose |
|---|---|
| `shopping_list.py` | The whole application: input validation, file storage, features, Direct Mode (argparse) and Interactive Mode (menu). |
| `tests/test_shopping_list.py` | 15 automated tests for validation (including malicious input) and for every feature. They run in a temporary folder, so they never touch real data. |
| `contributions/` | `<STUDENT_NAME>_<STUDENT_ID>_<GITHUB_USERNAME>.md` for each member. |
| `.gitignore` | Ignores the `*_list.txt` and `budget.txt` data files and Python cache. |

## Requirements

*   Python 3.8 or newer
*   No external libraries (only the standard library: `argparse`, `sys`; the tests also use `unittest`, `tempfile`, `pathlib`)

## Usage

The program has two modes: **Direct Mode** (one command with arguments) and **Interactive Mode** (a menu).

### Direct Mode (with `argparse`)

| Command | What it does |
|---|---|
| `add --item --quantity --price --section` | Adds an item. If the item already exists in that section, its quantity is increased and its price updated (no duplicates). |
| `remove --item --section` | Removes an item. |
| `list [--section]` | Shows the whole list, or one section. |
| `total` | Shows the cost of each section, the total, and compares it with the budget. |
| `budget [--set AMOUNT]` | Shows or sets the budget. |

```bash
python shopping_list.py add --item "Milk" --quantity 2 --price 1.25 --section dairy
python shopping_list.py add --item "Tomato" --quantity 4 --price 0.5 --section vegetables
python shopping_list.py budget --set 10
python shopping_list.py list
python shopping_list.py total
python shopping_list.py remove --item "Milk" --section dairy
python shopping_list.py --help
```

**Example output of `total`:**

```
--- Cost Summary ---
  vegetables           2.00
  dairy                2.50
  TOTAL                4.50
Within budget: 5.50 left of 10.00.
```

Valid sections: `vegetables`, `fruits`, `dairy`, `meat`, `bakery`, `cleaning`, `other`.

The program returns exit code `0` on success and `1` on an error, so it can be used in scripts.

### Interactive Mode

Run the program without a command:

```bash
python shopping_list.py
```

```
--- Shopping List Interactive Mode ---

1) Add item   2) Remove item   3) Show list   4) Show total   5) Set budget   6) Exit
Choose an option (1-6): 1
Item name: Egg
Quantity: 0
Error: Quantity must be between 1 and 1000. Received: 0.
Quantity: 12
Price of one unit: 0.2
Section (vegetables, fruits, dairy, meat, bakery, cleaning, other): other
SUCCESS: 'Egg' x12 added to other.
```

If an answer is invalid, the program shows the error and asks **the same question again**.

## How the Data Is Stored

Each section has its own text file (e.g., `dairy_list.txt`). Each line is one item:

```
Milk|2|1.25
```

(name | quantity | unit price). The budget is stored in `budget.txt`.

## Robustness (Input Validation)

All input, from the command line, from the menu, **and from the data files**, goes through the same validators:

| Input | Rule | Rejected examples |
|---|---|---|
| Item name | 1–40 characters; only letters (any language), digits, spaces and `- ' .` | empty, `Milk\|9\|0`, `<script>`, `../../x`, text with new lines |
| Quantity | Whole number, 1–1000 | `0`, `-3`, `2.5`, `abc`, `1e3`, huge numbers |
| Price / Budget | Number, 0–100,000 (budget up to 1,000,000), rounded to 2 decimals | `-1`, `abc`, `nan`, `inf` |
| Section | Must be one of the known sections | `bakeryy`, `../secret`, `dairy_list.txt` |

Other protections:

*   File names come **only** from the `SECTION_FILES` dictionary, so the user can never choose which file is written.
*   The `|` character is not allowed in names, so a name cannot inject fake lines into the data file.
*   Damaged lines in a data file are **skipped with a warning** instead of crashing the program.
*   Long input is shortened in error messages, so it cannot flood the screen.
*   `Ctrl+C` and end of input exit cleanly; file permission errors show a clear message.

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

## Topics Demonstrated

*   **W01:** Variables, `print()`, `if/elif/else`, Logical and Comparison operators, Type conversion (`int()`, `float()`).
*   **W02:** `while` and `for` loops, Lists, File I/O using `with open()` in read (`"r"`) and write (`"w"`) modes.
*   **W03-B1:** Functions, Dictionaries (`SECTION_FILES`, item records), Tuples (multiple returns `(value, error)`), `*args`.
*   **W03-B2:** `input()`, `argparse` with sub-commands, String operations (`.strip()`, `.lower()`, `.split()`, `.join()`, slicing), F-Strings with formatting, `try/except`, and the `if __name__ == "__main__":` block.

**Note:** The program does not use the `os` or `shutil` modules. All file work is done with `with open()`.

## Team

| Name | Student ID | Role |
|---|---|---|
| Abed Alazez Al Mohamad | 2309116389 | Presenter, Testing & QA |
| Ahmed Altaha | 2409115853 | Lead Developer |
| Ahmed Rakha | 2409115172 | Team Member |
| Abdulsalam Badr Abdulsalam Mansour | 2409115802 | Documentation |

See the `contributions/` folder for each member's details.
