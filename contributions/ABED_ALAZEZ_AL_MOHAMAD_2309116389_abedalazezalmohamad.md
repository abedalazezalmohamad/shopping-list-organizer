# Abed Alazez Al Mohamad - 2309116389

**Role:** Presenter, Testing & QA

## My Contributions

### Code: Interactive Mode (`shopping_list.py`)
*   `run_interactive()`: the menu loop (`1) Add item ... 6) Exit`) that lets the user add, remove and review items in one session.
*   `ask(prompt, validator)`: a reusable helper that keeps asking the same question until the answer is valid, instead of restarting the whole entry.
*   Clean exit on `Ctrl+C` and end of input (`KeyboardInterrupt`, `EOFError`) in `main()`.

### Tests (`tests/test_shopping_list.py`)
*   Took over the testing part after our teammate Ahmed Rakha could not be reached.
*   15 `unittest` tests for input validation (including malicious input such as `Milk|9|0`, `nan`, `inf`, `../secret`) and for every feature: add, merge duplicates, remove, totals, budget, damaged data lines.
*   The tests run in a temporary folder (`tempfile` + `unittest.mock`) so they never touch real data.

### Presentation
*   Prepared the PPTX presentation: the code snippets, and how each one maps to the course topics (W01–W03).
*   Prepared and rehearsed the live explanation to fit within 2 minutes.

## Topics I Worked With
`while` loops, `input()`, `if/elif/else`, functions passed as arguments (validators and `lambda`), `try/except`, `unittest`.
