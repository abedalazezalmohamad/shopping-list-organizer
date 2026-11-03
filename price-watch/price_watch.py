import argparse
import json
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

import currency_api
import scraper

# Files used by the program
WATCHLIST_FILE = "watchlist.json"
ALERTS_FILE = "alerts.log"

# Only these websites can be watched. The program never downloads a link from any other host,
# so it cannot be used to reach local or private addresses.
ALLOWED_SITES = {"books.toscrape.com"}

# Validation limits (protect the program against huge or malicious input)
MAX_URL_LENGTH = 200
MAX_TARGET = 1_000_000.0
MAX_ITEMS = 20
MAX_MINUTES = 1440  # one day
MAX_TIMES = 1000
DEFAULT_CURRENCY = "GBP"
PREVIEW_LENGTH = 30


# Functions
def preview(text):
    """
    Shortens user input before showing it in an error message, so a huge input cannot flood the screen.
    """
    text = str(text)
    if len(text) > PREVIEW_LENGTH:
        return text[:PREVIEW_LENGTH] + "..."
    return text


# ---------------------------------------------------------------------------
# Input validation
# Every validator returns a tuple: (clean_value, error_message).
# ---------------------------------------------------------------------------

# Functions
def validate_url(text):
    """
    Checks a product link: http/https only, an allowed website, no hidden tricks.
    """
    url = str(text).strip()

    if not url:
        return None, "The link cannot be empty."
    if len(url) > MAX_URL_LENGTH:
        return None, f"The link is too long (max {MAX_URL_LENGTH} characters)."
    for char in url:
        if char.isspace() or not char.isprintable():
            return None, "The link contains spaces or invisible characters."

    try:
        parts = urlparse(url)
        port = parts.port
    except ValueError:
        return None, f"Invalid link: '{preview(url)}'."

    if parts.scheme not in ("http", "https"):
        return None, "The link must start with http:// or https://."
    # '@' and ports can hide the real website, e.g. https://books.toscrape.com@evil.com
    if parts.username or parts.password or port is not None:
        return None, "The link must not contain a user name, password or port."
    if parts.hostname not in ALLOWED_SITES:
        return None, f"Website not supported. Allowed: {', '.join(sorted(ALLOWED_SITES))}."

    return url, None


# Functions
def validate_target(text):
    """
    Checks the target price: a real number between 0 and MAX_TARGET, rounded to 2 decimals.
    Also rejects 'nan' and 'inf', which float() would otherwise accept.
    """
    try:
        target = float(str(text).strip())
    except ValueError:
        return None, f"Target price must be a number. Received: '{preview(text)}'."

    # 'nan' fails every comparison, and 'inf' is bigger than MAX_TARGET
    if not (0 < target <= MAX_TARGET):
        return None, f"Target price must be more than 0 and at most {MAX_TARGET:,.0f}. Received: '{preview(text)}'."

    return round(target, 2), None


# Functions
def validate_currency(text):
    """
    Checks a currency code like USD (the exchange rate service checks that it really exists).
    """
    code = str(text).strip().upper()
    if not currency_api.is_currency_code(code):
        return None, f"Currency must be a 3-letter code like USD or EUR. Received: '{preview(text)}'."
    return code, None


# Functions
def validate_whole_number(text, label, maximum):
    """
    Checks a whole number between 1 and maximum (item number, minutes, times).
    """
    try:
        number = int(str(text).strip())
    except ValueError:
        return None, f"{label} must be a whole number. Received: '{preview(text)}'."
    if number < 1 or number > maximum:
        return None, f"{label} must be between 1 and {maximum}. Received: {number}."
    return number, None


# Functions with *args
def first_error(*results):
    """
    Takes several (value, error) tuples and returns the first error message, or None.
    """
    for value, error in results:
        if error:
            return error
    return None


# ---------------------------------------------------------------------------
# Storage (JSON file)
# ---------------------------------------------------------------------------

# Functions
def is_valid_entry(entry):
    """
    Checks one saved watchlist entry, so a damaged or edited file cannot break the program.
    """
    if not isinstance(entry, dict):
        return False
    url = validate_url(entry.get("url", ""))[1] is None
    target = validate_target(entry.get("target", ""))[1] is None
    currency = validate_currency(entry.get("currency", ""))[1] is None
    name = isinstance(entry.get("name"), str)
    last = entry.get("last_price")
    last_ok = last is None or (isinstance(last, (int, float)) and 0 <= last <= MAX_TARGET * 1000)
    return url and target and currency and name and last_ok


# File I/O: json.load()
def load_watchlist():
    """
    Reads the watchlist. Returns (items, error).
    Damaged entries are skipped with a warning; a broken file is reported and NOT overwritten.
    """
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return [], None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, f"{WATCHLIST_FILE} is damaged. Fix it or delete it to start a new watchlist."

    if not isinstance(data, list):
        return None, f"{WATCHLIST_FILE} is damaged. Fix it or delete it to start a new watchlist."

    items = []
    for number, entry in enumerate(data, start=1):
        if is_valid_entry(entry):
            items.append(entry)
        else:
            print(f"Warning: skipped damaged entry {number} in {WATCHLIST_FILE}.", file=sys.stderr)
    return items[:MAX_ITEMS], None


# File I/O: json.dump()
def save_watchlist(items):
    """
    Writes the whole watchlist back to the JSON file.
    """
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

# Functions
def send_alert(message):
    """
    Shows an alert on the screen and adds it to the alerts log with the date and time.
    File I/O: append mode ("a") keeps the old alerts.
    """
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{stamp}] {message}"
    print(f"  *** ALERT: {message}")
    with open(ALERTS_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


# Functions
def show_alerts(last):
    """
    Prints the most recent alerts from the log.
    """
    try:
        with open(ALERTS_FILE, "r", encoding="utf-8") as file:
            lines = [line.rstrip("\n") for line in file if line.strip()]
    except FileNotFoundError:
        lines = []

    if not lines:
        print("No alerts yet.")
        return

    print(f"\n--- Last {min(last, len(lines))} Alert(s) ---")
    for line in lines[-last:]:
        print(f"  {line[:200]}")


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

# Functions
def add_product(url, target, currency):
    """
    Downloads the product page once to make sure it works, then adds it to the watchlist.
    Returns (success, message).
    """
    items, error = load_watchlist()
    if error:
        return False, f"Error: {error}"

    for item in items:
        if item["url"] == url:
            item["target"] = target
            item["currency"] = currency
            save_watchlist(items)
            return True, f"UPDATED: '{item['name']}' target is now {target:.2f} {currency}."

    if len(items) >= MAX_ITEMS:
        return False, f"Error: The watchlist is full (max {MAX_ITEMS} products)."

    product, error = scraper.fetch_product(url)
    if error:
        return False, f"Error: {error}"

    # Makes sure the currency exists before saving it
    price, error = currency_api.convert(product["price"], product["currency"], currency)
    if error:
        return False, f"Error: {error}"

    items.append({
        "name": product["name"],
        "url": url,
        "target": target,
        "currency": currency,
        "last_price": None,
    })
    save_watchlist(items)
    return True, f"SUCCESS: Watching '{product['name']}' (now {price:.2f} {currency}, target {target:.2f} {currency})."


# Functions
def remove_product(number):
    """
    Removes a product by its number in the list. Returns (success, message).
    """
    items, error = load_watchlist()
    if error:
        return False, f"Error: {error}"
    if number > len(items):
        return False, f"Error: There is no product number {number}. The list has {len(items)}."

    removed = items.pop(number - 1)
    save_watchlist(items)
    return True, f"SUCCESS: '{removed['name']}' removed from the watchlist."


# Functions
def show_watchlist():
    """
    Prints every watched product with its target and last checked price.
    """
    items, error = load_watchlist()
    if error:
        print(f"Error: {error}")
        return False
    if not items:
        print("The watchlist is empty. Add a product with: add --url <link> --target <price>")
        return True

    print("\n--- Watchlist ---")
    for number, item in enumerate(items, start=1):
        last = "not checked yet"
        if item["last_price"] is not None:
            last = f"{item['last_price']:.2f} {item['currency']}"
        print(f"{number:>2}) {item['name']}")
        print(f"    target {item['target']:.2f} {item['currency']} | last price {last}")
    return True


# Functions
def check_item(item):
    """
    Checks one product: downloads the price, converts it, compares it with the target,
    and sends an alert when something important changed. Returns True if the check worked.
    """
    product, error = scraper.fetch_product(item["url"])
    if error is None:
        price, error = currency_api.convert(product["price"], product["currency"], item["currency"])

    print(f"- {item['name']}")
    if error:
        print(f"    could not check: {error}")
        return False

    currency = item["currency"]
    print(f"    price {price:.2f} {currency} | target {item['target']:.2f} {currency} | {product['stock']}")

    last = item["last_price"]
    if price <= item["target"] and (last is None or last > item["target"]):
        send_alert(f"'{item['name']}' reached your target: {price:.2f} {currency} (target {item['target']:.2f}).")
    elif last is not None and price < last:
        send_alert(f"'{item['name']}' price dropped from {last:.2f} to {price:.2f} {currency}.")

    item["last_price"] = price
    return True


# Functions
def check_all():
    """
    Checks every product once and saves the new prices. Returns an exit code (0 = success).
    """
    items, error = load_watchlist()
    if error:
        print(f"Error: {error}")
        return 1
    if not items:
        print("The watchlist is empty. Nothing to check.")
        return 0

    currency_api.clear_cache()  # fresh exchange rates for every check
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n--- Price Check {stamp} ---")

    failed = 0
    for item in items:
        if not check_item(item):
            failed += 1

    save_watchlist(items)
    print(f"Checked {len(items) - failed} of {len(items)} product(s).")
    return 1 if failed == len(items) else 0


# Scheduling: time.sleep()
def watch(minutes, times):
    """
    Runs a price check every few minutes, for a fixed number of times.
    """
    print(f"Watching prices every {minutes} minute(s), {times} time(s). Press Ctrl+C to stop.")
    for run in range(1, times + 1):
        check_all()
        if run < times:
            print(f"Next check in {minutes} minute(s)...")
            time.sleep(minutes * 60)
    print("Watching finished.")
    return 0


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

# argparse (sub-commands)
def build_parser():
    """
    Sets up the command-line interface with one sub-command per feature.
    """
    parser = argparse.ArgumentParser(
        description="Price Watch: watches product prices on a website and alerts you when they drop.",
        epilog="Supported website: " + ", ".join(sorted(ALLOWED_SITES)),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="Start watching a product (or change its target).")
    add.add_argument("--url", required=True, help="Link to the product page.")
    add.add_argument("--target", required=True, help="Alert me when the price is at or below this, e.g. 40.")
    add.add_argument("--currency", default=DEFAULT_CURRENCY, help=f"Currency of the target, e.g. USD (default {DEFAULT_CURRENCY}).")

    remove = commands.add_parser("remove", help="Stop watching a product.")
    remove.add_argument("--number", required=True, help="Product number from the 'list' command.")

    commands.add_parser("list", help="Show the watched products.")
    commands.add_parser("check", help="Check all prices once now.")

    watch_cmd = commands.add_parser("watch", help="Check all prices again and again on a schedule.")
    watch_cmd.add_argument("--every", required=True, help=f"Minutes between checks (1-{MAX_MINUTES}).")
    watch_cmd.add_argument("--times", default="10", help=f"How many checks to run (1-{MAX_TIMES}, default 10).")

    alerts = commands.add_parser("alerts", help="Show the latest alerts.")
    alerts.add_argument("--last", default="10", help="How many alerts to show (default 10).")

    return parser


# Functions
def run_command(args):
    """
    Validates the arguments of one command and runs it. Returns an exit code (0 = success, 1 = error).
    """
    if args.command == "add":
        url = validate_url(args.url)
        target = validate_target(args.target)
        currency = validate_currency(args.currency)
        error = first_error(url, target, currency)
        if error:
            print(f"Error: {error}")
            return 1
        success, message = add_product(url[0], target[0], currency[0])
        print(message)
        return 0 if success else 1

    if args.command == "remove":
        number, error = validate_whole_number(args.number, "Product number", MAX_ITEMS)
        if error:
            print(f"Error: {error}")
            return 1
        success, message = remove_product(number)
        print(message)
        return 0 if success else 1

    if args.command == "list":
        return 0 if show_watchlist() else 1

    if args.command == "check":
        return check_all()

    if args.command == "watch":
        minutes = validate_whole_number(args.every, "Minutes", MAX_MINUTES)
        times = validate_whole_number(args.times, "Times", MAX_TIMES)
        error = first_error(minutes, times)
        if error:
            print(f"Error: {error}")
            return 1
        return watch(minutes[0], times[0])

    if args.command == "alerts":
        last, error = validate_whole_number(args.last, "Number of alerts", 100)
        if error:
            print(f"Error: {error}")
            return 1
        show_alerts(last)
        return 0

    return 1


# Functions
def main():
    """
    Program entry point. Returns an exit code.
    """
    sys.stdout.reconfigure(encoding="utf-8")  # product names can contain any character
    args = build_parser().parse_args()
    try:
        return run_command(args)
    except KeyboardInterrupt:
        print("\nStopped by the user.")
        return 0
    except OSError as error:
        print(f"Error: Could not read or write a file ({error.strerror}).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
