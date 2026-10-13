"""Historique des burgers (SQLite).

Le schéma d'origine (name, ingredients, sauce, diet, calories, created_at,
burger_type) est conservé ; une colonne `data` (JSON du burger complet, sans
langue) est ajoutée automatiquement. Les anciennes lignes restent lisibles.
"""
import json
import sqlite3
from datetime import datetime


class BurgerStore:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS burgers
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                ingredients TEXT,
                sauce TEXT,
                diet TEXT,
                calories INTEGER,
                created_at TEXT,
                burger_type TEXT)"""
        )
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(burgers)")}
        if "data" not in columns:
            self.conn.execute("ALTER TABLE burgers ADD COLUMN data TEXT")
        self.conn.commit()

    def save(self, burger: dict, title: str) -> int:
        cur = self.conn.execute(
            """INSERT INTO burgers
               (name, ingredients, sauce, diet, calories, created_at, burger_type, data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                title,
                json.dumps(burger["ingredients"], ensure_ascii=False),
                burger.get("sauce", ""),
                burger.get("diet", ""),
                burger["calories"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                burger["kind"],
                json.dumps(burger, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def recent(self, limit: int = 20):
        """Retourne [(id, name, data_json_ou_None), ...], du plus récent au plus ancien."""
        return self.conn.execute(
            "SELECT id, name, data FROM burgers ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    def get(self, burger_id: int):
        """Retourne (burger, titre_sauvegardé) ou None si l'id n'existe plus."""
        row = self.conn.execute(
            "SELECT name, ingredients, sauce, diet, calories, burger_type, data FROM burgers WHERE id=?",
            (burger_id,),
        ).fetchone()
        if row is None:
            return None
        name, ingredients, sauce, diet, calories, kind, data = row
        if data:
            return json.loads(data), name
        # Ancienne ligne : textes libres dans la langue d'origine, non traduisibles.
        return {
            "kind": kind or "classic",
            "title": name,
            "ingredients": json.loads(ingredients) if ingredients else [],
            "sauce": sauce or "",
            "calories": calories or 0,
            "diet": diet or "",
        }, name

    def delete(self, burger_id: int) -> None:
        self.conn.execute("DELETE FROM burgers WHERE id=?", (burger_id,))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
