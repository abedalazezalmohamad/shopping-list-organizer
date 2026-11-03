# Ahmed Rakha - 2409115172

**Role:** Presenter & Web Scraping

## My Contributions

### Code: Web Scraping (`scraper.py`)
*   `download_page()`: downloads the product page with `requests`, with a 10-second time limit. Refuses error pages, answers that are not HTML, and pages over 2 MB.
*   `parse_product()`: reads the product name, price and stock status with `BeautifulSoup` and CSS selectors.
*   `parse_price()`: turns a text like `£51.77` into a number and a currency code, and rejects wrong prices like `£abc` or `£nan`.
*   `fetch_product()`: joins the two steps and returns a `(product, error)` tuple.

### Presentation
*   Presents the project live: the problem, the code and the robustness tests, within 2 minutes.

## Topics I Worked With
Web scraping with `requests` and `BeautifulSoup`, HTTP status codes, string operations, dictionaries, `try/except`.
