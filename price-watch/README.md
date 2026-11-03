# Price Watch

A command-line tool that **watches product prices on a website**, converts them to **your currency** with a live exchange rate API, and **alerts you** when a price drops or reaches your target.

COE203 - Project 2 (Web Monitoring)

## The Problem

Students and small shops often buy online from stores in another currency. Prices change every week, so they either check the same pages again and again by hand, or they buy too early and miss a discount.

**Price Watch** does the checking for them:

*   **Web scraping:** it reads the product name, price and stock status directly from the product page.
*   **API:** it converts the price (for example GBP) to the currency you think in (USD, EUR, TRY, ...) using live exchange rates.
*   **Scheduling:** it can check all prices automatically every few minutes.
*   **Alerts:** it shows an alert and saves it in a log when a price **reaches your target** or **drops**.

The same idea is used by price comparison sites and by shops that monitor their competitors' prices.

## Repository Structure

This project lives in its own folder, `price-watch/`, inside our team repository. Project 1 (Shopping List Organizer) is in the root folder and was not changed.

```
price-watch/
├── price_watch.py          # Main program: CLI, validation, watchlist, checks, scheduling, alerts
├── scraper.py              # Web scraping: reads name, price and stock from a product page
├── currency_api.py         # API: live exchange rates and currency conversion
├── tests/
│   └── test_price_watch.py # Automated tests (unittest), no internet needed
├── contributions/          # One file per team member explaining their Project 2 contribution
├── requirements.txt        # External libraries to install
├── README.md               # This file
└── .gitignore              # Keeps generated data files out of the repo
```

| File / Folder | Purpose |
|---|---|
| `price_watch.py` | The program you run. Validates all input, stores the watchlist in `watchlist.json`, checks prices, runs the schedule and writes alerts to `alerts.log`. |
| `scraper.py` | Downloads a product page with `requests` (with a time limit and size limit) and reads it with `BeautifulSoup`. |
| `currency_api.py` | Calls the free ExchangeRate-API (`https://open.er-api.com`, no key needed), checks the answer, and converts prices. |
| `tests/test_price_watch.py` | 16 automated tests for validation (including malicious input), scraping, the API, alerts and scheduling. Internet calls are replaced with fake answers, and files are written in a temporary folder. |
| `contributions/` | `<STUDENT_NAME>_<STUDENT_ID>_<GITHUB_USERNAME>.md` for each member. |
| `requirements.txt` | `requests` and `beautifulsoup4`. |
| `.gitignore` | Ignores `watchlist.json`, `alerts.log` and Python cache. |

## Requirements

*   Python 3.8 or newer
*   Go to the project folder and install the libraries once:

```bash
cd price-watch
pip install -r requirements.txt
```

## Usage

| Command | What it does |
|---|---|
| `add --url LINK --target PRICE [--currency CODE]` | Starts watching a product. The page is downloaded once to make sure it works. Adding the same link again only changes the target. |
| `remove --number N` | Stops watching product number N (from `list`). |
| `list` | Shows the watched products, their targets and last prices. |
| `check` | Checks all prices once now. |
| `watch --every MINUTES [--times N]` | Checks all prices every few minutes, N times (default 10). |
| `alerts [--last N]` | Shows the latest alerts (default 10). |

```bash
python price_watch.py add --url "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html" --target 80 --currency USD
python price_watch.py add --url "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html" --target 40
python price_watch.py list
python price_watch.py check
python price_watch.py watch --every 30 --times 4
python price_watch.py alerts
python price_watch.py remove --number 2
python price_watch.py --help
```

**Example output of `check`:**

```
--- Price Check 2026-10-31 15:39 ---
- A Light in the Attic
    price 69.30 USD | target 80.00 USD | In stock (22 available)
  *** ALERT: 'A Light in the Attic' reached your target: 69.30 USD (target 80.00).
- Tipping the Velvet
    price 53.74 GBP | target 40.00 GBP | In stock (20 available)
Checked 2 of 2 product(s).
```

The supported website is `books.toscrape.com`, a public store made for practicing web scraping, so the project does not break any website's rules. The program returns exit code `0` on success and `1` on an error.

### When is an alert sent?

| Situation | Alert |
|---|---|
| The price is at or below your target, and it was not there in the last check | `reached your target` |
| The price is lower than in the last check | `price dropped from X to Y` |

The target alert is sent **once** when the price crosses the target, not again on every check.

## How the Data Is Stored

The watchlist is saved in `watchlist.json`:

```json
[
  {
    "name": "A Light in the Attic",
    "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "target": 80.0,
    "currency": "USD",
    "last_price": 69.3
  }
]
```

Alerts are added to the end of `alerts.log`, one line each, with the date and time:

```
[2026-10-31 15:39] 'A Light in the Attic' reached your target: 69.30 USD (target 80.00).
```

## Robustness (Input Validation)

All input, from the command line, **from the website, from the API and from the saved file**, is checked before it is used:

| Input | Rule | Rejected examples |
|---|---|---|
| Link | `http`/`https` only, allowed website only, max 200 characters, no spaces, no user name / password / port | `file:///C:/Windows/win.ini`, `http://127.0.0.1/admin`, `https://books.toscrape.com@evil.com/x`, `ftp://...` |
| Target price | Number, more than 0 and at most 1,000,000, rounded to 2 decimals | `0`, `-5`, `abc`, `nan`, `inf`, `1e9` |
| Currency | Exactly 3 English letters, and it must exist in the API | `US`, `U$D`, `../`, `XYZ` |
| Numbers (`--number`, `--every`, `--times`, `--last`) | Whole numbers in a fixed range | `0`, `-1`, `2.5`, `1441` |

Other protections:

*   **Allowed websites list:** the program only downloads from `books.toscrape.com`, so a user cannot make it open local or private addresses.
*   **Safe downloads:** every request has a 10-second time limit, non-HTML answers and pages over 2 MB are refused, and network errors become clear messages instead of crashes.
*   **The website and the API are not trusted:** a page without a price, a price like `£nan`, or an API answer with a wrong shape is rejected.
*   **Damaged `watchlist.json`:** broken entries are skipped with a warning. If the whole file is broken, the program stops and does **not** overwrite it, so no data is lost.
*   The watchlist is limited to 20 products, and long input is shortened in error messages.
*   `Ctrl+C` stops `watch` cleanly; file permission errors show a clear message.

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

## Topics Demonstrated

*   **APIs:** `requests.get()`, reading JSON with `.json()`, checking the answer, caching results in a dictionary.
*   **Web scraping:** `requests` + `BeautifulSoup`, CSS selectors with `select_one()`, cleaning page text.
*   **Scheduling:** repeating checks with a `for` loop and `time.sleep()`, timestamps with `datetime`.
*   **Files:** JSON with `json.load()` / `json.dump()`, append mode (`"a"`) for the alerts log.
*   **Earlier topics:** functions, dictionaries, lists, tuples (`(value, error)`), `*args`, `argparse` sub-commands, f-strings, `try/except`, `unittest` with `mock`.

## Team

| Name | Student ID | Role |
|---|---|---|
| Abed Alazez Al Mohamad | 2309116389 | API & Testing |
| Ahmed Altaha | 2409115853 | Lead Developer |
| Ahmed Rakha | 2409115172 | Presenter & Web Scraping |
| Abdulsalam Badr Abdulsalam Mansour | 2409115802 | Documentation |

See the `contributions/` folder for each member's details.
