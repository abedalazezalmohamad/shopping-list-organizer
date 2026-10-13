# Ahmed Altaha - 2409115853

**Role:** Lead Developer

## My Contributions

### Code: Core Design and Storage (`shopping_list.py`)
*   Designed the program structure and the `SECTION_FILES` dictionary that maps each section to its file.
*   File storage: `load_items()`, `save_items()` and the `name|quantity|price` line format.
*   Features: `add_item()` (merges duplicates by increasing the quantity) and `remove_item()`, using `find_item()` for case-insensitive search.

### Code: Command-Line Interface
*   `build_parser()`: the `argparse` interface with sub-commands `add`, `remove`, `list`, `total`, `budget`.
*   `run_command()` and `main()`: validating arguments, running the command and returning exit codes (`0` / `1`).

## Topics I Worked With
Dictionaries, Lists, File I/O with `with open()` (`"r"` and `"w"`), `argparse` sub-commands, functions with multiple returns.
