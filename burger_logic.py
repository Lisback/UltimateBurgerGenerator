"""Logique métier de l'Ultimate Burger Generator.

Aucune dépendance à tkinter : tout ce qui est calcul, données et mise en forme
vit ici pour pouvoir être testé sans interface graphique.

Un burger est un dict indépendant de la langue :
    {"kind": "classic" | "extreme" | "zodiac",
     "params": {...},              # ce qui a servi à le générer
     "ingredients": [ids...],      # un id peut se répéter (double steak)
     "sauce": id,
     "calories": int,
     "diet": "" | "vegan"}
Les noms affichés viennent des fichiers translations_<langue>.json.
"""
import json
import os
import random
from dataclasses import dataclass
from typing import List, Optional

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LANGUAGES = ("fr", "en")

# --- Données (indépendantes de la langue) -------------------------------

BURGER_TYPES = {
    "hamburger":      {"kcal": 500, "components": ("bun", "beef_patty"), "patty": "beef_patty"},
    "cheeseburger":   {"kcal": 600, "components": ("bun", "beef_patty", "cheese"), "patty": "beef_patty"},
    "bacon_burger":   {"kcal": 750, "components": ("bun", "beef_patty", "cheese", "bacon"), "patty": "beef_patty"},
    "chicken_burger": {"kcal": 450, "components": ("bun", "chicken_fillet"), "patty": "chicken_fillet"},
    "fish_burger":    {"kcal": 400, "components": ("bun", "fish_fillet"), "patty": "fish_fillet"},
    "veggie_burger":  {"kcal": 350, "components": ("bun_whole", "veggie_patty"), "patty": "veggie_patty"},
}

# taille -> (nombre de steaks, multiplicateur de calories)
SIZES = {"simple": (1, 1.0), "double": (2, 1.8), "triple": (3, 2.5)}

# suppléments proposés sur l'onglet Classique -> calories ajoutées
EXTRAS = {"cheese": 70, "bacon": 90, "egg": 80, "pickles": 5, "tomato": 10, "lettuce": 5}

CLASSIC_SAUCES = ("ketchup", "mayo", "bbq", "special")

EXTREME_MIN_LEVEL, EXTREME_MAX_LEVEL = 1, 10
EXTREME_MAX_INGREDIENTS = 6
EXTREME_TIERS = {
    "standard": {
        1: ("cornflakes", "ketchup_item"),
        3: ("nutella", "fries"),
        5: ("sashimi", "vanilla_ice_cream"),
        7: ("foie_gras", "caviar"),
        10: ("ghost_pepper", "edible_gold"),
    },
    "vegan": {
        1: ("cereal", "vegan_ketchup"),
        3: ("vegan_chocolate", "sweet_potatoes"),
        5: ("tofu", "coconut_ice_cream"),
        7: ("truffles", "eggplant_caviar"),
        10: ("vegan_pepper", "edible_glitter"),
    },
}
EXTREME_SAUCES = ("rainbow_mayo", "banana_ketchup", "spice_1000")

ZODIAC_SIGNS = {  # signe -> (élément, emoji)
    "aries": ("fire", "♈"), "taurus": ("earth", "♉"), "gemini": ("air", "♊"),
    "cancer": ("water", "♋"), "leo": ("fire", "♌"), "virgo": ("earth", "♍"),
    "libra": ("air", "♎"), "scorpio": ("water", "♏"), "sagittarius": ("fire", "♐"),
    "capricorn": ("earth", "♑"), "aquarius": ("air", "♒"), "pisces": ("water", "♓"),
}
ZODIAC_INGREDIENTS = {
    "fire": ("bun_spicy", "spicy_steak", "grilled_onions", "chili"),
    "earth": ("bun_whole", "charolais", "bacon", "mushrooms"),
    "air": ("bun_light", "chicken_escalope", "lettuce", "cucumber"),
    "water": ("bun_soft", "fish_fillet", "avocado", "shrimp"),
}
ZODIAC_SAUCES = {
    "fire": ("spicy", "bbq"),
    "earth": ("forest", "truffle"),
    "air": ("light", "lemon"),
    "water": ("hollandaise", "tartar"),
}
ZODIAC_KCAL_RANGE = (600, 900)

KIND_EMOJI = {"classic": "🍔", "extreme": "🌶️", "zodiac": "♈"}


# --- Traductions --------------------------------------------------------

def translation_path(language: str) -> str:
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language!r}")
    return os.path.join(APP_DIR, f"translations_{language}.json")


def load_translations(language: str) -> dict:
    """Charge un fichier de traduction (lève OSError / JSONDecodeError)."""
    with open(translation_path(language), "r", encoding="utf-8") as f:
        return json.load(f)


def required_translation_ids() -> dict:
    """Ids dont une traduction complète doit fournir le nom (sert aux tests)."""
    items = set()
    for spec in BURGER_TYPES.values():
        items.update(spec["components"])
    items.update(EXTRAS)
    for tiers in EXTREME_TIERS.values():
        for names in tiers.values():
            items.update(names)
    for names in ZODIAC_INGREDIENTS.values():
        items.update(names)
    sauces = set(CLASSIC_SAUCES) | set(EXTREME_SAUCES)
    for names in ZODIAC_SAUCES.values():
        sauces.update(names)
    return {
        "items": items,
        "sauces": sauces,
        "burger_types": set(BURGER_TYPES),
        "sizes": set(SIZES),
        "elements": set(ZODIAC_INGREDIENTS),
        "zodiac_signs": set(ZODIAC_SIGNS),
        "zodiac_predictions": set(ZODIAC_SIGNS),
    }


def missing_translations(trans: dict) -> List[str]:
    """Liste les ids manquants dans une traduction (vide si tout est là)."""
    missing = []
    for section, ids in required_translation_ids().items():
        present = trans.get(section, {})
        missing.extend(f"{section}/{i}" for i in sorted(ids) if i not in present)
    return missing


# --- Génération ---------------------------------------------------------

def generate_classic(burger_type: str, size: str, sauce: str, extras=()) -> dict:
    if burger_type not in BURGER_TYPES:
        raise ValueError(f"Unknown burger type: {burger_type!r}")
    if size not in SIZES:
        raise ValueError(f"Unknown size: {size!r}")
    if sauce not in CLASSIC_SAUCES:
        raise ValueError(f"Unknown sauce: {sauce!r}")
    unknown = set(extras) - set(EXTRAS)
    if unknown:
        raise ValueError(f"Unknown extras: {sorted(unknown)}")

    spec = BURGER_TYPES[burger_type]
    patties, multiplier = SIZES[size]
    ingredients = []
    for item in spec["components"]:
        ingredients.extend([item] * (patties if item == spec["patty"] else 1))

    calories = int(spec["kcal"] * multiplier)
    for extra in EXTRAS:  # ordre stable, pas celui de l'appelant
        if extra in extras and extra not in ingredients:
            ingredients.append(extra)
            calories += EXTRAS[extra]

    return {
        "kind": "classic",
        "params": {"type": burger_type, "size": size, "extras": [e for e in EXTRAS if e in extras]},
        "ingredients": ingredients,
        "sauce": sauce,
        "calories": calories,
        "diet": "",
    }


def generate_extreme(level: int, vegan: bool = False, rng=random) -> dict:
    level = max(EXTREME_MIN_LEVEL, min(EXTREME_MAX_LEVEL, int(level)))
    tiers = EXTREME_TIERS["vegan" if vegan else "standard"]
    unlocked = [item for lvl in sorted(tiers) if level >= lvl for item in tiers[lvl]]
    # On garde les plus extrêmes : les paliers hauts ne doivent jamais être coupés.
    ingredients = unlocked[-EXTREME_MAX_INGREDIENTS:]
    sauce = rng.choice(EXTREME_SAUCES[:min(level, len(EXTREME_SAUCES))])
    return {
        "kind": "extreme",
        "params": {"level": level, "vegan": bool(vegan)},
        "ingredients": ingredients,
        "sauce": sauce,
        "calories": 500 + level * 150,
        "diet": "vegan" if vegan else "",
    }


def generate_zodiac(sign: str, rng=random) -> dict:
    if sign not in ZODIAC_SIGNS:
        raise ValueError(f"Unknown sign: {sign!r}")
    element, _emoji = ZODIAC_SIGNS[sign]
    return {
        "kind": "zodiac",
        "params": {"sign": sign},
        "ingredients": list(ZODIAC_INGREDIENTS[element]),
        "sauce": rng.choice(ZODIAC_SAUCES[element]),
        "calories": rng.randint(*ZODIAC_KCAL_RANGE),
        "diet": "",
    }


def generate_random(rng=random) -> dict:
    """Burger totalement aléatoire, tous modes confondus."""
    kind = rng.choice(("classic", "extreme", "zodiac"))
    if kind == "classic":
        extras = [e for e in EXTRAS if rng.random() < 0.3]
        return generate_classic(rng.choice(list(BURGER_TYPES)), rng.choice(list(SIZES)),
                                rng.choice(CLASSIC_SAUCES), extras)
    if kind == "extreme":
        return generate_extreme(rng.randint(EXTREME_MIN_LEVEL, EXTREME_MAX_LEVEL),
                                rng.random() < 0.3, rng)
    return generate_zodiac(rng.choice(list(ZODIAC_SIGNS)), rng)


# --- Mise en forme ------------------------------------------------------

@dataclass
class BurgerView:
    title: str
    emoji: str
    ingredients: List[str]
    sauce: Optional[str]
    sauce_desc: Optional[str]
    calories: int
    prediction: Optional[str]


def burger_title(burger: dict, trans: dict) -> str:
    """Titre dans la langue courante (ou titre brut pour un ancien burger)."""
    if "title" in burger:  # ancienne sauvegarde, sans données structurées
        return burger["title"]
    kind, params, titles = burger["kind"], burger["params"], trans["titles"]
    if kind == "classic":
        return titles["classic"].format(type=trans["burger_types"][params["type"]],
                                        size=trans["sizes"][params["size"]])
    if kind == "extreme":
        key = "extreme_vegan" if params["vegan"] else "extreme"
        return titles[key].format(level=params["level"])
    sign = params["sign"]
    return titles["zodiac"].format(sign=trans["zodiac_signs"][sign], emoji=ZODIAC_SIGNS[sign][1])


def describe(burger: dict, trans: dict) -> BurgerView:
    """Tout ce qu'il faut pour afficher un burger (GUI, PDF, partage)."""
    names = trans["items"]
    counts = {}
    for item in burger["ingredients"]:
        counts[item] = counts.get(item, 0) + 1
    lines = [f"{n}× {names.get(i, i)}" if n > 1 else names.get(i, i) for i, n in counts.items()]

    sauce_id = burger.get("sauce") or None
    sauce_name = sauce_desc = None
    if sauce_id:
        info = trans["sauces"].get(sauce_id)
        sauce_name = info["name"] if info else sauce_id  # id inconnu = ancien texte libre
        sauce_desc = info["desc"] if info else None

    prediction = None
    if burger["kind"] == "zodiac" and "params" in burger:
        prediction = trans["zodiac_predictions"].get(burger["params"]["sign"])

    return BurgerView(
        title=burger_title(burger, trans),
        emoji=KIND_EMOJI.get(burger["kind"], "🍔"),
        ingredients=lines,
        sauce=sauce_name,
        sauce_desc=sauce_desc,
        calories=burger["calories"],
        prediction=prediction,
    )


def share_text(burger: dict, trans: dict) -> str:
    view = describe(burger, trans)
    return trans["share_template"].format(
        name=view.title, ingredients=", ".join(view.ingredients), calories=view.calories)
