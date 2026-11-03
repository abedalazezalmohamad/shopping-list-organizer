# Abed Alazez Al Mohamad - 2309116389

**Role:** API & Testing

## My Contributions

### Code: Exchange Rate API (`currency_api.py`)
*   `get_rates()`: calls the free ExchangeRate-API with `requests.get()` and a time limit, and reads the JSON answer.
*   Checks the answer before using it: `result` must be `success`, `rates` must be a dictionary, and every rate must be a positive number (rejects `nan` / `inf`).
*   `is_currency_code()`: only 3 English capital letters can be put inside the API link.
*   `convert()` and a small cache (dictionary), so each currency is requested only once per check.

### Tests (`tests/test_price_watch.py`)
*   16 `unittest` tests for input validation (including malicious links like `http://127.0.0.1/admin` and `https://books.toscrape.com@evil.com/x`), scraping, the API, alerts, damaged files and scheduling.
*   The internet is replaced with saved HTML and fake API answers (`unittest.mock`), and files are written in a temporary folder.

### Other
*   `.gitignore` for the generated data files.
*   Prepared the PPTX slides.

## Topics I Worked With
APIs with `requests`, JSON, dictionaries as a cache, `try/except`, `unittest` and `mock`.
