import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Make shopping_list.py importable when the tests are run from the project folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shopping_list as sl


class ValidationTests(unittest.TestCase):
    """Checks that bad or malicious input is rejected with a clear error."""

    def test_valid_item_is_cleaned(self):
        self.assertEqual(sl.validate_item("  Olive   oil "), ("Olive oil", None))

    def test_accented_item_is_accepted(self):
        self.assertEqual(sl.validate_item("Café au lait")[0], "Café au lait")

    def test_bad_items_are_rejected(self):
        for text in ["", "   ", "Milk|9|0", "a" * 41, "<script>", "milk;rm -rf", "../../x"]:
            with self.subTest(text=text):
                self.assertIsNotNone(sl.validate_item(text)[1])

    def test_bad_quantities_are_rejected(self):
        for text in ["0", "-3", "2.5", "abc", "", "1001", "99999999999999999999"]:
            with self.subTest(text=text):
                self.assertIsNotNone(sl.validate_quantity(text)[1])

    def test_bad_prices_are_rejected(self):
        for text in ["-1", "abc", "nan", "inf", "-inf", "1e9", ""]:
            with self.subTest(text=text):
                self.assertIsNotNone(sl.validate_amount(text, "Price", sl.MAX_PRICE)[1])

    def test_price_is_rounded(self):
        self.assertEqual(sl.validate_amount("1.239", "Price", sl.MAX_PRICE), (1.24, None))

    def test_unknown_section_is_rejected(self):
        self.assertEqual(sl.validate_section(" Dairy "), ("dairy", None))
        for text in ["bakeryy", "../secret", "", "dairy_list.txt"]:
            with self.subTest(text=text):
                self.assertIsNotNone(sl.validate_section(text)[1])


class StorageTests(unittest.TestCase):
    """Runs every feature inside a temporary folder so no real files are touched."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        base = Path(self.folder.name)
        files = {section: str(base / name) for section, name in sl.SECTION_FILES.items()}
        self.patches = [
            mock.patch.dict(sl.SECTION_FILES, files),
            mock.patch.object(sl, "BUDGET_FILE", str(base / "budget.txt")),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.folder.cleanup()

    def test_add_and_load(self):
        sl.add_item("Milk", 2, 1.25, "dairy")
        self.assertEqual(sl.load_items("dairy"), [{"name": "Milk", "quantity": 2, "price": 1.25}])

    def test_adding_same_item_merges_quantity(self):
        sl.add_item("Milk", 2, 1.25, "dairy")
        success, message = sl.add_item("milk", 3, 1.50, "dairy")
        self.assertTrue(success)
        self.assertEqual(sl.load_items("dairy"), [{"name": "Milk", "quantity": 5, "price": 1.5}])

    def test_merge_cannot_exceed_max_quantity(self):
        sl.add_item("Rice", sl.MAX_QUANTITY, 1, "other")
        success, message = sl.add_item("Rice", 1, 1, "other")
        self.assertFalse(success)

    def test_remove(self):
        sl.add_item("Soap", 1, 3, "cleaning")
        self.assertTrue(sl.remove_item("SOAP", "cleaning")[0])
        self.assertEqual(sl.load_items("cleaning"), [])
        self.assertFalse(sl.remove_item("Soap", "cleaning")[0])

    def test_totals(self):
        sl.add_item("Milk", 2, 1.25, "dairy")
        sl.add_item("Tomato", 4, 0.5, "vegetables")
        section_totals, grand_total = sl.calculate_totals()
        self.assertEqual(section_totals, {"vegetables": 2.0, "dairy": 2.5})
        self.assertEqual(grand_total, 4.5)

    def test_damaged_lines_are_skipped(self):
        with open(sl.SECTION_FILES["meat"], "w", encoding="utf-8") as file:
            file.write("Chicken|1|5.00\nbroken line\nBeef|-2|3\nLamb|1|nan\n")
        with mock.patch("sys.stderr"):
            items = sl.load_items("meat")
        self.assertEqual(items, [{"name": "Chicken", "quantity": 1, "price": 5.0}])

    def test_budget(self):
        self.assertIsNone(sl.load_budget())
        sl.set_budget(50)
        self.assertEqual(sl.load_budget(), 50.0)

    def test_damaged_budget_is_ignored(self):
        with open(sl.BUDGET_FILE, "w", encoding="utf-8") as file:
            file.write("lots of money")
        with mock.patch("sys.stderr"):
            self.assertIsNone(sl.load_budget())


if __name__ == "__main__":
    unittest.main()
