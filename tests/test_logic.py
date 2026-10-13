import json
import os
import random
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import burger_logic as bl
from burger_export import export_pdf, pdf_safe
from burger_store import BurgerStore


def flat_keys(d, prefix=""):
    for k, v in d.items():
        yield prefix + k
        if isinstance(v, dict):
            yield from flat_keys(v, prefix + k + "/")


class TranslationTests(unittest.TestCase):
    def test_all_ids_translated_in_every_language(self):
        for lang in bl.LANGUAGES:
            self.assertEqual(bl.missing_translations(bl.load_translations(lang)), [], lang)

    def test_languages_have_same_keys(self):
        fr, en = (set(flat_keys(bl.load_translations(l))) for l in bl.LANGUAGES)
        self.assertEqual(fr ^ en, set())

    def test_unsupported_language(self):
        with self.assertRaises(ValueError):
            bl.load_translations("de")


class GenerationTests(unittest.TestCase):
    def test_classic_sizes(self):
        simple = bl.generate_classic("hamburger", "simple", "mayo")
        double = bl.generate_classic("hamburger", "double", "mayo")
        triple = bl.generate_classic("veggie_burger", "triple", "bbq")
        self.assertEqual(simple["ingredients"], ["bun", "beef_patty"])
        self.assertEqual(double["ingredients"].count("beef_patty"), 2)
        self.assertEqual(simple["calories"], 500)
        self.assertEqual(double["calories"], 900)
        self.assertEqual(triple["ingredients"].count("veggie_patty"), 3)
        self.assertEqual(triple["calories"], int(350 * 2.5))

    def test_classic_extras(self):
        b = bl.generate_classic("cheeseburger", "simple", "ketchup", ["cheese", "egg"])
        self.assertEqual(b["ingredients"].count("cheese"), 1)  # déjà dans la recette
        self.assertEqual(b["calories"], 600 + 80)  # seul l'œuf ajoute des calories
        self.assertEqual(b["params"]["extras"], ["cheese", "egg"])

    def test_classic_rejects_unknown(self):
        for args in (("nope", "simple", "mayo"), ("hamburger", "huge", "mayo"),
                     ("hamburger", "simple", "nope"), ("hamburger", "simple", "mayo", ["nope"])):
            with self.assertRaises(ValueError):
                bl.generate_classic(*args)

    def test_extreme_levels(self):
        self.assertEqual(len(bl.generate_extreme(1)["ingredients"]), 2)
        top = bl.generate_extreme(10)["ingredients"]
        self.assertLessEqual(len(top), bl.EXTREME_MAX_INGREDIENTS)
        self.assertIn("ghost_pepper", top)  # le palier 10 n'est plus coupé
        self.assertEqual(bl.generate_extreme(99)["params"]["level"], 10)
        self.assertEqual(bl.generate_extreme(0)["params"]["level"], 1)
        self.assertEqual(bl.generate_extreme(1, rng=random.Random(1))["sauce"], "rainbow_mayo")

    def test_extreme_vegan(self):
        vegan = bl.generate_extreme(10, vegan=True)
        self.assertEqual(vegan["diet"], "vegan")
        self.assertIn("edible_glitter", vegan["ingredients"])
        standard_items = {i for t in bl.EXTREME_TIERS["standard"].values() for i in t}
        self.assertFalse(standard_items & set(vegan["ingredients"]))

    def test_zodiac_all_signs(self):
        rng = random.Random(0)
        for sign, (element, _) in bl.ZODIAC_SIGNS.items():
            b = bl.generate_zodiac(sign, rng)
            self.assertEqual(b["ingredients"], list(bl.ZODIAC_INGREDIENTS[element]))
            self.assertIn(b["sauce"], bl.ZODIAC_SAUCES[element])
            self.assertTrue(600 <= b["calories"] <= 900)

    def test_random_always_valid_and_describable(self):
        rng = random.Random(42)
        for _ in range(200):
            b = bl.generate_random(rng)
            for lang in bl.LANGUAGES:
                view = bl.describe(b, bl.load_translations(lang))
                self.assertTrue(view.title and view.ingredients)
            json.dumps(b)  # sérialisable pour la base


class DescribeTests(unittest.TestCase):
    def test_fr_en_titles_and_counts(self):
        b = bl.generate_classic("hamburger", "double", "special")
        fr = bl.describe(b, bl.load_translations("fr"))
        en = bl.describe(b, bl.load_translations("en"))
        self.assertEqual(fr.title, "Hamburger Double")
        self.assertEqual(en.title, "Double Hamburger")
        self.assertIn("2× Steak haché", fr.ingredients)
        self.assertIn("2× Beef patty", en.ingredients)
        self.assertEqual(fr.sauce, "Spéciale")
        self.assertTrue(fr.sauce_desc)

    def test_zodiac_has_prediction(self):
        view = bl.describe(bl.generate_zodiac("leo"), bl.load_translations("fr"))
        self.assertIn("Lion", view.title)
        self.assertIn("royal", view.prediction)

    def test_share_text(self):
        text = bl.share_text(bl.generate_extreme(3), bl.load_translations("en"))
        self.assertIn("Crazy Burger Level 3", text)
        self.assertIn("kcal", text)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "t.db")

    def tearDown(self):
        self.dir.cleanup()

    def test_roundtrip_delete_and_order(self):
        store = BurgerStore(self.path)
        a = bl.generate_classic("hamburger", "simple", "mayo")
        b = bl.generate_zodiac("aries", random.Random(1))
        ida, idb = store.save(a, "A"), store.save(b, "B")
        self.assertEqual([r[0] for r in store.recent()], [idb, ida])
        self.assertEqual(store.get(ida)[0], a)
        store.delete(ida)
        self.assertIsNone(store.get(ida))
        store.close()

    def test_legacy_rows_still_readable(self):
        conn = sqlite3.connect(self.path)
        conn.execute("""CREATE TABLE burgers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
            ingredients TEXT, sauce TEXT, diet TEXT, calories INTEGER, created_at TEXT, burger_type TEXT)""")
        conn.execute("INSERT INTO burgers (name, ingredients, sauce, diet, calories, created_at, burger_type)"
                     " VALUES ('Double Hamburger', '[\"Pain\", \"Steak haché\"]', 'Mayo', '', 900, 'x', 'classic')")
        conn.commit(); conn.close()
        store = BurgerStore(self.path)  # migre le schéma
        burger, _ = store.get(store.recent()[0][0])
        view = bl.describe(burger, bl.load_translations("en"))
        self.assertEqual(view.title, "Double Hamburger")
        self.assertEqual(view.ingredients, ["Pain", "Steak haché"])
        self.assertEqual(view.sauce, "Mayo")
        store.close()


class PdfTests(unittest.TestCase):
    def test_pdf_safe(self):
        self.assertEqual(pdf_safe("🍔 Œuf ♈ café"), "Oeuf  café")

    def test_export_every_kind_and_language(self):
        rng = random.Random(7)
        with tempfile.TemporaryDirectory() as d:
            for lang in bl.LANGUAGES:
                trans = bl.load_translations(lang)
                for b in (bl.generate_classic("bacon_burger", "triple", "bbq", ["egg"]),
                          bl.generate_extreme(10, True, rng), bl.generate_zodiac("pisces", rng)):
                    path = os.path.join(d, f"{lang}_{b['kind']}.pdf")
                    export_pdf(b, trans, path)
                    with open(path, "rb") as f:
                        self.assertEqual(f.read(5), b"%PDF-")


if __name__ == "__main__":
    unittest.main()
