# 🍔 Ultimate Burger Generator Pro

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

Un générateur de burgers de bureau, bilingue (FR/EN), avec 3 modes : Classique, Extrême et Zodiaque.

[🇬🇧 English version](README.md)

## ✨ Fonctionnalités
- **Classique** : 6 types de burgers, taille simple/double/triple, 4 sauces, suppléments facultatifs (fromage, bacon, œuf, cornichons, tomate, salade) avec calories calculées.
- **Extrême** : un niveau de folie de 1 à 10 (plus il monte, plus c'est fou), version végane possible.
- **Zodiaque** : un burger et une prédiction pour chacun des 12 signes, selon leur élément.
- **🎲 Surprends-moi** : un burger aléatoire, tous modes confondus.
- **Bascule FR/EN** à tout moment, sans perdre le burger affiché ni vos choix.
- **Historique** (SQLite) : sauvegarder, revoir (double-clic), supprimer. Les burgers sauvegardés se réaffichent dans la langue courante.
- **Export** : PDF, copie dans le presse-papiers, partage sur X/Twitter.

## 🚀 Démarrage rapide
```bash
git clone https://github.com/Lisback/UltimateBurgerGenerator.git
cd UltimateBurgerGenerator
pip install -r requirements.txt
python UBGv2.py
```
tkinter est fourni avec Python sous Windows/macOS ; sous Debian/Ubuntu, installez `python3-tk`.
Facultatif : placez des images `.png`/`.jpg` dans un dossier `burger_images/` pour en voir une au hasard à chaque burger.

## 🗂️ Organisation du projet
| Fichier | Rôle |
|---------|------|
| `UBGv2.py` | interface tkinter uniquement |
| `burger_logic.py` | données, règles de génération, mise en forme (sans dépendance à l'interface) |
| `burger_store.py` | historique SQLite (`burgers.db`, créé à côté du script) |
| `burger_export.py` | export PDF |
| `translations_fr.json`, `translations_en.json` | tous les textes affichés |
| `tests/` | tests unitaires : `python -m unittest discover tests` |

Pour ajouter une langue : copiez un `translations_*.json`, traduisez-le et ajoutez son code à `LANGUAGES` dans `burger_logic.py` (et un bouton dans `UBGv2.py`). Les tests vérifient qu'aucun id ne manque.

## 📜 Licence
MIT, voir [LICENCE](LICENCE).
