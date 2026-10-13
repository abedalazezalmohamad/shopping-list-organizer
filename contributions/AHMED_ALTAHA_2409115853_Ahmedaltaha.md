# Ahmed Altaha - 2409115853

**Role:** Lead Developer

## My Contributions

### Code: Core Design and Storage (`shopping_list.py`)
*   Designed the program structure and the `SECTION_FILES` dictionary that maps each section to its file.
*   File storage: `load_items()`, `save_items()` and the `name|quantity|price` line format.
*   Features: `add_item()` (merges duplicates by increasing the quantity) and `remove_item()`, using `find_item()` for case-insensitive search.

### Code: Input Validation
*   `validate_item()`, `validate_quantity()`, `validate_amount()`, `validate_section()`: every input returns a `(value, error)` tuple.
*   Protection against bad input: blocking `|` and new lines in names, rejecting `nan` / `inf`, limiting lengths and number ranges, and accepting only known sections.
*   `preview()` shortens huge input in error messages; damaged data-file lines are skipped with a warning.

### Code: Budget and Reports
*   `set_budget()` and `load_budget()`: saving and reading the budget.
*   `calculate_totals()`, `show_total()` and `show_list()`: cost per section, grand total, and the within / over budget message.

### Code: Command-Line Interface
*   `build_parser()`: the `argparse` interface with sub-commands `add`, `remove`, `list`, `total`, `budget`, including the `--help` texts.
*   `run_command()` and `main()`: validating arguments, running the command and returning exit codes (`0` / `1`).

## Topics I Worked With
Dictionaries, Lists, File I/O with `with open()` (`"r"` and `"w"`), `argparse` sub-commands, type conversion and `try/except`, F-Strings, functions with multiple returns.
