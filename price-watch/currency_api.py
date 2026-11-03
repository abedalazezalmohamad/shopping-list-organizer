"""
API: gets live exchange rates, so a price in GBP can be compared with a target in USD, EUR, TRY, ...
Uses the free ExchangeRate-API (no API key needed): https://open.er-api.com
"""
import requests

API_URL = "https://open.er-api.com/v6/latest/{base}"
TIMEOUT_SECONDS = 10

# Rates downloaded during this run, so each base currency is requested only once
# Dictionaries: {"GBP": {"USD": 1.33, "EUR": 1.15, ...}}
_rates_cache = {}


# Functions
def is_currency_code(text):
    """
    A currency code is exactly 3 English capital letters, like USD.
    This check runs before the code is put inside the API link.
    """
    return len(text) == 3 and text.isascii() and text.isalpha() and text.isupper()


# API: requests.get() + .json()
def get_rates(base):
    """
    Downloads all exchange rates for one base currency. Returns (rates_dict, error).
    """
    if not is_currency_code(base):
        return None, f"Invalid currency code: '{base[:10]}'."
    if base in _rates_cache:
        return _rates_cache[base], None

    try:
        response = requests.get(API_URL.format(base=base), timeout=TIMEOUT_SECONDS)
        data = response.json()
    except requests.RequestException:
        return None, "Could not reach the exchange rate service."
    except ValueError:
        return None, "The exchange rate service sent an invalid answer."

    # Never trust the answer blindly: check its shape before using it
    if not isinstance(data, dict) or data.get("result") != "success":
        return None, f"The exchange rate service does not support '{base}'."
    rates = data.get("rates")
    if not isinstance(rates, dict):
        return None, "The exchange rate service sent an invalid answer."

    _rates_cache[base] = rates
    return rates, None


# Functions
def convert(amount, from_code, to_code):
    """
    Converts an amount between two currencies. Returns (converted_amount, error).
    """
    if from_code == to_code:
        return round(amount, 2), None

    rates, error = get_rates(from_code)
    if error:
        return None, error

    rate = rates.get(to_code)
    # A rate must be a positive number ('nan' and 'inf' fail this check)
    if not isinstance(rate, (int, float)) or not (0 < rate < 1_000_000):
        return None, f"No exchange rate from {from_code} to {to_code}."

    return round(amount * rate, 2), None


# Functions
def clear_cache():
    """
    Forgets the saved rates, so the next check downloads fresh ones.
    """
    _rates_cache.clear()
