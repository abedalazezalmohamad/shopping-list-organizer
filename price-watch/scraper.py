"""
Web scraping: downloads a product page and reads its name, price and stock status.
"""
import requests
from bs4 import BeautifulSoup

# Safety limits for every download
TIMEOUT_SECONDS = 10
MAX_PAGE_SIZE = 2_000_000  # 2 MB, a normal product page is about 10 KB
HEADERS = {"User-Agent": "PriceWatch/1.0 (COE203 student project)"}

# Maps the currency symbol shown on the page to its currency code
# Dictionaries
CURRENCY_SYMBOLS = {"£": "GBP", "$": "USD", "€": "EUR"}

# Where each piece of data is on the page (CSS selectors)
NAME_SELECTOR = "div.product_main h1"
PRICE_SELECTOR = "div.product_main p.price_color"
STOCK_SELECTOR = "div.product_main p.availability"


# Functions
def download_page(url):
    """
    Downloads a web page and returns (html_bytes, error).
    Every network problem becomes an error message instead of a crash.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    except requests.Timeout:
        return None, f"The website did not answer within {TIMEOUT_SECONDS} seconds."
    except requests.RequestException:
        return None, "Could not connect to the website. Check your internet connection."

    if response.status_code != 200:
        return None, f"The website returned status {response.status_code} (page not found or not available)."
    if "text/html" not in response.headers.get("Content-Type", ""):
        return None, "The link is not a web page."
    if len(response.content) > MAX_PAGE_SIZE:
        return None, "The page is too large to be a product page."

    return response.content, None


# Functions
def parse_price(text):
    """
    Turns a price text like '£51.77' into (51.77, 'GBP', None).
    Returns (None, None, error) if the text is not a valid price.
    """
    text = text.strip()
    if not text or text[0] not in CURRENCY_SYMBOLS:
        return None, None, f"Unknown price format: '{text[:20]}'."

    currency = CURRENCY_SYMBOLS[text[0]]
    number = text[1:].replace(",", "")
    try:
        price = float(number)
    except ValueError:
        return None, None, f"Unknown price format: '{text[:20]}'."

    # 'nan' and 'inf' fail this check
    if not (0 <= price <= 1_000_000):
        return None, None, f"Price on the page is not realistic: '{text[:20]}'."

    return round(price, 2), currency, None


# Web scraping: BeautifulSoup
def parse_product(html):
    """
    Reads the product name, price, currency and stock status from the page.
    Returns (product_dict, error).
    """
    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.select_one(NAME_SELECTOR)
    price_tag = soup.select_one(PRICE_SELECTOR)
    stock_tag = soup.select_one(STOCK_SELECTOR)

    if name_tag is None or price_tag is None:
        return None, "This page is not a product page (no name or price found)."

    price, currency, error = parse_price(price_tag.get_text())
    if error:
        return None, error

    # .split() + .join() also removes new lines and extra spaces from the page text
    name = " ".join(name_tag.get_text().split())[:80]
    stock = "Unknown"
    if stock_tag is not None:
        stock = " ".join(stock_tag.get_text().split())[:40]

    product = {"name": name, "price": price, "currency": currency, "stock": stock}
    return product, None


# Functions
def fetch_product(url):
    """
    Downloads and reads one product page. Returns (product_dict, error).
    """
    html, error = download_page(url)
    if error:
        return None, error
    return parse_product(html)
