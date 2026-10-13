import argparse
import sys

# Global dictionary to map store sections to their corresponding shopping list file names.
# The user never types a file name directly, so a section like "../secret" can never reach open().
# W03-B1: Dictionaries
SECTION_FILES = {
    "vegetables": "vegetables_list.txt",
    "fruits": "fruits_list.txt",
    "dairy": "dairy_list.txt",
    "meat": "meat_list.txt",
    "bakery": "bakery_list.txt",
    "cleaning": "cleaning_list.txt",
    "other": "other_list.txt",
}
BUDGET_FILE = "budget.txt"

# Validation limits (protect the program against huge or malicious input)
# W01: Variables
MAX_NAME_LENGTH = 40
MAX_QUANTITY = 1000
MAX_PRICE = 100000.0
MAX_BUDGET = 1000000.0
ALLOWED_SYMBOLS = " -'."
SEPARATOR = "|"
PREVIEW_LENGTH = 20


# W03-B1: Functions
def preview(text):
    """
    Shortens user input before showing it in an error message, so a huge input cannot flood the screen.
    W03-B2: String slicing
    """
    text = str(text)
    if len(text) > PREVIEW_LENGTH:
        return text[:PREVIEW_LENGTH] + "..."
    return text


# ---------------------------------------------------------------------------
# Input validation
# Every validator returns a tuple: (clean_value, error_message).
# W03-B1: Tuples / Multiple Returns
# ---------------------------------------------------------------------------

# W03-B1: Functions
def validate_item(text):
    """
    Checks an item name: not empty, not too long, and only safe characters.
    W03-B2: String Operations (.strip(), .split(), .join(), .isalnum())
    """
    name = " ".join(str(text).split())  # Removes extra spaces, tabs and newlines

    # W01: if/elif/else statements
    if not name:
        return None, "Item name cannot be empty."
    if len(name) > MAX_NAME_LENGTH:
        return None, f"Item name is too long (max {MAX_NAME_LENGTH} characters)."

    # W02: for loops
    for char in name:
        # W01: Logical operators (or, not)
        if not (char.isalnum() or char in ALLOWED_SYMBOLS):
            return None, f"Item name contains an invalid character: '{char}'."

    return name, None


# W03-B1: Functions
def validate_quantity(text):
    """
    Checks that the quantity is a whole number between 1 and MAX_QUANTITY.
    W01: Type conversion with int()
    """
    try:
        quantity = int(str(text).strip())
    except ValueError:
        return None, f"Quantity must be a whole number. Received: '{preview(text)}'."

    # W01: Comparison operators
    if quantity < 1 or quantity > MAX_QUANTITY:
        return None, f"Quantity must be between 1 and {MAX_QUANTITY}. Received: {quantity}."

    return quantity, None


# W03-B1: Functions
def validate_amount(text, label, maximum):
    """
    Checks a money amount (price or budget): a real number between 0 and maximum.
    Also rejects 'nan' and 'inf', which float() would otherwise accept.
    W01: Type conversion with float()
    """
    try:
        amount = float(str(text).strip())
    except ValueError:
        return None, f"{label} must be a number. Received: '{preview(text)}'."

    # 'nan' fails every comparison, and 'inf' is bigger than maximum, so both are rejected here
    # W01: Comparison operators
    if not (0 <= amount <= maximum):
        return None, f"{label} must be between 0 and {maximum:,.0f}. Received: '{preview(text)}'."

    return round(amount, 2), None


# W03-B1: Functions
def validate_section(text):
    """
    Checks that the section is one of the known sections.
    W03-B1: Dictionaries (membership test with 'in')
    """
    section = str(text).strip().lower()
    if section not in SECTION_FILES:
        valid = ", ".join(SECTION_FILES)
        return None, f"Unknown section '{preview(section)}'. Choose one of: {valid}."
    return section, None


# ---------------------------------------------------------------------------
# File storage
# Each line in a section file looks like:  Milk|2|1.25   (name|quantity|price)
# ---------------------------------------------------------------------------

# W03-B1: Functions
def load_items(section):
    """
    Reads all items of a section into a list of dictionaries.
    Damaged lines are skipped with a warning instead of crashing the program.
    W02: File I/O using with open() in read mode ("r")
    W02: Lists
    """
    filename = SECTION_FILES[section]
    items = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            # W02: for loops
            for line_number, line in enumerate(file, start=1):
                parts = line.strip().split(SEPARATOR)

                # W01: if/elif/else statements
                if len(parts) != 3:
                    print(f"Warning: skipped damaged line {line_number} in {filename}.", file=sys.stderr)
                    continue

                name, name_error = validate_item(parts[0])
                quantity, quantity_error = validate_quantity(parts[1])
                price, price_error = validate_amount(parts[2], "Price", MAX_PRICE)

                if name_error or quantity_error or price_error:
                    print(f"Warning: skipped invalid line {line_number} in {filename}.", file=sys.stderr)
                    continue

                # W03-B1: Dictionaries
                items.append({"name": name, "quantity": quantity, "price": price})
    except FileNotFoundError:
        # No file yet means the section is simply empty
        return []

    return items


# W03-B1: Functions
def save_items(section, items):
    """
    Writes the full list of items of a section back to its file.
    W02: File I/O using with open() in write mode ("w")
    """
    filename = SECTION_FILES[section]
    with open(filename, "w", encoding="utf-8") as file:
        for entry in items:
            # W03-B2: F-Strings
            file.write(f"{entry['name']}{SEPARATOR}{entry['quantity']}{SEPARATOR}{entry['price']:.2f}\n")


# W03-B1: Functions
def find_item(items, name):
    """
    Returns the position of an item in the list (case-insensitive), or -1 if it is not there.
    W03-B2: String Operations (.lower())
    """
    for index, entry in enumerate(items):
        if entry["name"].lower() == name.lower():
            return index
    return -1


# W03-B1: Functions
def load_budget():
    """
    Reads the saved budget. Returns None if no budget has been set or the file is damaged.
    """
    try:
        with open(BUDGET_FILE, "r", encoding="utf-8") as file:
            text = file.read()
    except FileNotFoundError:
        return None

    budget, error = validate_amount(text, "Budget", MAX_BUDGET)
    if error:
        print(f"Warning: {BUDGET_FILE} is damaged and was ignored.", file=sys.stderr)
        return None
    return budget


# ---------------------------------------------------------------------------
# Features
# Each feature returns (success, message) so both modes can reuse it.
# ---------------------------------------------------------------------------

# W03-B1: Functions
def add_item(item, quantity, price, section):
    """
    Adds an item to a section. If the item already exists, its quantity is increased
    and its price is updated, so the list never contains duplicates.
    """
    items = load_items(section)
    index = find_item(items, item)

    if index == -1:
        items.append({"name": item, "quantity": quantity, "price": price})
        message = f"SUCCESS: '{item}' x{quantity} added to {section}."
    else:
        new_quantity = items[index]["quantity"] + quantity
        if new_quantity > MAX_QUANTITY:
            return False, f"Error: '{item}' would exceed the maximum quantity of {MAX_QUANTITY}."
        items[index]["quantity"] = new_quantity
        items[index]["price"] = price
        message = f"UPDATED: '{items[index]['name']}' is now x{new_quantity} in {section}."

    save_items(section, items)
    return True, message


# W03-B1: Functions
def remove_item(item, section):
    """
    Removes an item from a section.
    """
    items = load_items(section)
    index = find_item(items, item)

    if index == -1:
        return False, f"Error: '{item}' was not found in {section}."

    removed = items.pop(index)
    save_items(section, items)
    return True, f"REMOVED: '{removed['name']}' from {section}."


# W03-B1: Functions
def calculate_totals():
    """
    Calculates the cost of every section and the grand total.
    W03-B1: Tuples / Multiple Returns
    """
    section_totals = {}
    grand_total = 0.0

    for section in SECTION_FILES:
        subtotal = 0.0
        for entry in load_items(section):
            subtotal += entry["quantity"] * entry["price"]
        if subtotal > 0:
            section_totals[section] = round(subtotal, 2)
        grand_total += subtotal

    return section_totals, round(grand_total, 2)


# W03-B1: Functions
def show_list(section=None):
    """
    Prints the items of one section, or of every section that has items.
    """
    # W01: if/elif/else statements
    if section:
        sections = [section]
    else:
        sections = list(SECTION_FILES)

    found_any = False
    for current in sections:
        items = load_items(current)
        if not items:
            continue
        found_any = True
        print(f"\n[{current.upper()}]")
        for entry in items:
            subtotal = entry["quantity"] * entry["price"]
            # W03-B2: F-Strings (with alignment and number formatting)
            print(f"  - {entry['name']:<25} x{entry['quantity']:<5} @ {entry['price']:>9.2f} = {subtotal:>10.2f}")

    if not found_any:
        print("The shopping list is empty.")


# W03-B1: Functions
def show_total():
    """
    Prints the cost of each section, the grand total, and compares it with the budget.
    """
    section_totals, grand_total = calculate_totals()

    if not section_totals:
        print("The shopping list is empty. Total: 0.00")
        return

    print("\n--- Cost Summary ---")
    for section, subtotal in section_totals.items():
        print(f"  {section:<12} {subtotal:>12.2f}")
    print(f"  {'TOTAL':<12} {grand_total:>12.2f}")

    budget = load_budget()
    if budget is None:
        print("No budget set. Use: budget --set <amount>")
    elif grand_total <= budget:
        print(f"Within budget: {budget - grand_total:.2f} left of {budget:.2f}.")
    else:
        print(f"WARNING: Over budget by {grand_total - budget:.2f} (budget: {budget:.2f}).")


# W03-B1: Functions
def set_budget(amount):
    """
    Saves the shopping budget.
    W02: File I/O using with open() in write mode ("w")
    """
    with open(BUDGET_FILE, "w", encoding="utf-8") as file:
        file.write(f"{amount:.2f}\n")
    return True, f"SUCCESS: Budget set to {amount:.2f}."


# ---------------------------------------------------------------------------
# Direct mode (command-line arguments)
# ---------------------------------------------------------------------------

# W03-B1: Functions
def build_parser():
    """
    Sets up the command-line interface with one sub-command per feature.
    W03-B2: argparse (sub-commands)
    """
    parser = argparse.ArgumentParser(
        description="Shopping List Organizer: plan your shopping by store section and stay within your budget.",
    )
    commands = parser.add_subparsers(dest="command")

    add = commands.add_parser("add", help="Add an item (or increase its quantity).")
    add.add_argument("--item", required=True, help="Item name, e.g. Milk.")
    add.add_argument("--quantity", required=True, help=f"Whole number from 1 to {MAX_QUANTITY}.")
    add.add_argument("--price", required=True, help="Price of ONE unit, e.g. 1.25.")
    add.add_argument("--section", required=True, help="One of: " + ", ".join(SECTION_FILES) + ".")

    remove = commands.add_parser("remove", help="Remove an item from a section.")
    remove.add_argument("--item", required=True, help="Item name to remove.")
    remove.add_argument("--section", required=True, help="Section the item is in.")

    show = commands.add_parser("list", help="Show the shopping list.")
    show.add_argument("--section", help="Only show this section.")

    commands.add_parser("total", help="Show the cost per section and compare it with the budget.")

    budget = commands.add_parser("budget", help="Show or set the shopping budget.")
    budget.add_argument("--set", dest="amount", help="New budget amount, e.g. 50.")

    return parser


# W03-B1: Functions
def first_error(*results):
    """
    Takes several (value, error) tuples and returns the first error message, or None.
    W03-B1: Functions with *args
    """
    for value, error in results:
        if error:
            return error
    return None


# W03-B1: Functions
def run_command(args):
    """
    Validates the arguments of one command and runs it. Returns an exit code (0 = success).
    """
    # W01: if/elif/else statements
    if args.command == "add":
        item = validate_item(args.item)
        quantity = validate_quantity(args.quantity)
        price = validate_amount(args.price, "Price", MAX_PRICE)
        section = validate_section(args.section)
        error = first_error(item, quantity, price, section)
        if error:
            print(f"Error: {error}")
            return 1
        success, message = add_item(item[0], quantity[0], price[0], section[0])

    elif args.command == "remove":
        item = validate_item(args.item)
        section = validate_section(args.section)
        error = first_error(item, section)
        if error:
            print(f"Error: {error}")
            return 1
        success, message = remove_item(item[0], section[0])

    elif args.command == "list":
        section = None
        if args.section is not None:
            section, error = validate_section(args.section)
            if error:
                print(f"Error: {error}")
                return 1
        show_list(section)
        return 0

    elif args.command == "total":
        show_total()
        return 0

    else:  # budget
        if args.amount is None:
            budget = load_budget()
            print("No budget set." if budget is None else f"Current budget: {budget:.2f}")
            return 0
        amount, error = validate_amount(args.amount, "Budget", MAX_BUDGET)
        if error:
            print(f"Error: {error}")
            return 1
        success, message = set_budget(amount)

    print(message)
    return 0 if success else 1


# W03-B1: Functions
def main():
    """
    The main execution function for the Shopping List Organizer.
    """
    # Print Arabic or other non-English item names safely on any terminal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command is None:
            parser.print_help()
            return 0
        return run_command(args)
    except OSError as error:
        # File errors (e.g., no permission to write)
        print(f"ERROR: Could not access the shopping list files. Details: {error}")
        return 1


# W03-B2: Script Structure: if __name__ == "__main__":
if __name__ == "__main__":
    sys.exit(main())
