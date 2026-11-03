import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Make the project files importable when the tests are run from the project folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import currency_api
import price_watch as pw
import scraper

URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

# A small copy of a real product page, so the tests never use the internet
PAGE = b"""<html><body><div class="product_main">
<h1>A Light in the Attic</h1>
<p class="price_color">\xc2\xa351.77</p>
<p class="instock availability">  In stock (22 available)  </p>
</div></body></html>"""


def fake_product(price):
    return {"name": "A Light in the Attic", "price": price, "currency": "GBP", "stock": "In stock"}, None


class ValidationTests(unittest.TestCase):
    """Checks that bad or malicious input is rejected with a clear error."""

    def test_valid_url_is_accepted(self):
        self.assertEqual(pw.validate_url(f"  {URL} "), (URL, None))

    def test_bad_urls_are_rejected(self):
        for text in [
            "", "books.toscrape.com", "ftp://books.toscrape.com/x", "file:///C:/Windows/win.ini",
            "https://example.com/item", "http://localhost/admin", "http://127.0.0.1:8080/",
            "https://books.toscrape.com@evil.com/x", "https://books.toscrape.com:99999/",
            "https://books.toscrape.com/a b", "https://books.toscrape.com/a\nb", "https://books.toscrape.com/" + "a" * 300,
        ]:
            with self.subTest(text=text):
                self.assertIsNotNone(pw.validate_url(text)[1])

    def test_bad_targets_are_rejected(self):
        self.assertEqual(pw.validate_target("39.999"), (40.0, None))
        for text in ["0", "-5", "abc", "nan", "inf", "1e9", ""]:
            with self.subTest(text=text):
                self.assertIsNotNone(pw.validate_target(text)[1])

    def test_currency_codes(self):
        self.assertEqual(pw.validate_currency(" usd "), ("USD", None))
        for text in ["", "US", "USDD", "U$D", "../", "ÜSD"]:
            with self.subTest(text=text):
                self.assertIsNotNone(pw.validate_currency(text)[1])

    def test_bad_whole_numbers_are_rejected(self):
        for text in ["0", "-1", "2.5", "abc", "1441", "99999999999999999999"]:
            with self.subTest(text=text):
                self.assertIsNotNone(pw.validate_whole_number(text, "Minutes", pw.MAX_MINUTES)[1])


class ScraperTests(unittest.TestCase):
    """Checks the web scraping part on saved HTML."""

    def test_product_page_is_read(self):
        product, error = scraper.parse_product(PAGE)
        self.assertIsNone(error)
        self.assertEqual(product, {"name": "A Light in the Attic", "price": 51.77,
                                   "currency": "GBP", "stock": "In stock (22 available)"})

    def test_page_without_price_is_rejected(self):
        self.assertIsNotNone(scraper.parse_product(b"<html><h1>Hello</h1></html>")[1])

    def test_bad_price_texts_are_rejected(self):
        for text in ["", "51.77", "£abc", "£nan", "£inf", "£-3"]:
            with self.subTest(text=text):
                self.assertIsNotNone(scraper.parse_price(text)[2])


class CurrencyTests(unittest.TestCase):
    """Checks the API part with fake answers."""

    def setUp(self):
        currency_api.clear_cache()

    def answer(self, data):
        response = mock.Mock()
        response.json.return_value = data
        return mock.patch.object(currency_api.requests, "get", return_value=response)

    def test_convert_uses_the_rate(self):
        with self.answer({"result": "success", "rates": {"USD": 1.5}}):
            self.assertEqual(currency_api.convert(10, "GBP", "USD"), (15.0, None))

    def test_bad_api_answers_are_rejected(self):
        for data in [{"result": "error"}, {"result": "success"}, [],
                     {"result": "success", "rates": {"USD": "abc"}},
                     {"result": "success", "rates": {"USD": float("nan")}}]:
            with self.subTest(data=data):
                currency_api.clear_cache()
                with self.answer(data):
                    self.assertIsNotNone(currency_api.convert(10, "GBP", "USD")[1])


class FeatureTests(unittest.TestCase):
    """Runs every feature inside a temporary folder so no real files are touched."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        base = Path(self.folder.name)
        self.patches = [
            mock.patch.object(pw, "WATCHLIST_FILE", str(base / "watchlist.json")),
            mock.patch.object(pw, "ALERTS_FILE", str(base / "alerts.log")),
            mock.patch("builtins.print"),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.folder.cleanup()

    def add(self, target=60.0):
        with mock.patch.object(scraper, "fetch_product", return_value=fake_product(51.77)):
            return pw.add_product(URL, target, "GBP")

    def alerts(self):
        try:
            with open(pw.ALERTS_FILE, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return ""

    def test_add_and_remove(self):
        self.assertTrue(self.add()[0])
        self.assertTrue(self.add(45.0)[0])  # same link only updates the target
        items, _ = pw.load_watchlist()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["target"], 45.0)
        self.assertFalse(pw.remove_product(2)[0])
        self.assertTrue(pw.remove_product(1)[0])
        self.assertEqual(pw.load_watchlist(), ([], None))

    def test_alert_when_target_is_reached_only_once(self):
        self.add(target=60.0)
        with mock.patch.object(scraper, "fetch_product", return_value=fake_product(51.77)):
            pw.check_all()
            pw.check_all()
        self.assertEqual(self.alerts().count("reached your target"), 1)

    def test_alert_when_price_drops(self):
        self.add(target=10.0)
        with mock.patch.object(scraper, "fetch_product", return_value=fake_product(51.77)):
            pw.check_all()
        with mock.patch.object(scraper, "fetch_product", return_value=fake_product(49.00)):
            pw.check_all()
        self.assertIn("dropped from 51.77 to 49.00", self.alerts())

    def test_damaged_watchlist_is_not_overwritten(self):
        with open(pw.WATCHLIST_FILE, "w", encoding="utf-8") as file:
            file.write("{ not json")
        self.assertFalse(self.add()[0])
        with open(pw.WATCHLIST_FILE, "r", encoding="utf-8") as file:
            self.assertEqual(file.read(), "{ not json")

    def test_damaged_entries_are_skipped(self):
        self.add()
        with open(pw.WATCHLIST_FILE, "r", encoding="utf-8") as file:
            good = file.read().strip()[1:-1]
        with open(pw.WATCHLIST_FILE, "w", encoding="utf-8") as file:
            file.write(f'[{good}, {{"url": "http://127.0.0.1/", "target": 5}}, "text"]')
        with mock.patch("sys.stderr"):
            items, error = pw.load_watchlist()
        self.assertIsNone(error)
        self.assertEqual(len(items), 1)

    def test_watch_runs_on_schedule(self):
        with mock.patch.object(pw, "check_all", return_value=0) as check, \
             mock.patch.object(pw.time, "sleep") as sleep:
            pw.watch(5, 3)
        self.assertEqual(check.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_called_with(300)


if __name__ == "__main__":
    unittest.main()
