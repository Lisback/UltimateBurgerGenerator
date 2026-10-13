"""Ultimate Burger Generator Pro — interface tkinter.

La logique (génération, formats, historique, PDF) est dans burger_logic.py,
burger_store.py et burger_export.py ; ce fichier ne contient que l'interface.
"""
import json
import os
import random
import sys
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote

try:
    from PIL import Image, ImageTk
except ImportError:  # les images sont facultatives
    Image = ImageTk = None

import burger_logic as bl
from burger_export import export_pdf
from burger_store import BurgerStore

DB_PATH = os.path.join(bl.APP_DIR, "burgers.db")
IMAGE_DIR = os.path.join(bl.APP_DIR, "burger_images")
TWEET_URL = "https://twitter.com/intent/tweet?text="


class UltimateBurgerApp:
    def __init__(self, root, store=None, language="fr"):
        self.root = root
        self.language = language
        self.trans = bl.load_translations(language)
        self.store = store or BurgerStore(DB_PATH)
        self.current_burger = None
        self.history_ids = []
        self.selection = {"type": 0, "size": 0, "sauce": 0, "sign": 0, "tab": 0}

        # Variables Tk : elles survivent au changement de langue (reconstruction de l'UI).
        self.extra_vars = {e: tk.BooleanVar(master=root) for e in bl.EXTRAS}
        self.crazy_level = tk.IntVar(master=root, value=5)
        self.vegan_extreme = tk.BooleanVar(master=root)

        self.setup_styles()
        self.setup_ui()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----- Utilitaires -------------------------------------------------

    def t(self, key, **kwargs):
        text = self.trans.get(key, f"[{key}]")
        return text.format(**kwargs) if kwargs else text

    def item_name(self, section, item_id):
        return self.trans[section].get(item_id, item_id)

    def sauce_name(self, sauce_id):
        return self.trans["sauces"][sauce_id]["name"]

    def make_combo(self, parent, ids, label, selected):
        combo = ttk.Combobox(parent, values=[label(i) for i in ids], state="readonly")
        combo.current(min(selected, len(ids) - 1))
        return combo

    # ----- Construction de l'interface ------------------------------------

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#f5f5f5", foreground="#333", font=("Helvetica", 11))
        self.style.configure("TButton", padding=8, background="#4a7a96", foreground="white")
        self.style.configure("Zodiac.TFrame", background="#e6f9ff")
        self.style.configure("Zodiac.TLabel", background="#e6f9ff")

    def setup_ui(self):
        self.root.title(self.t("app_title"))
        self.root.geometry("1200x800")

        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)
        ttk.Button(control_frame, text="🇫🇷 FR", command=lambda: self.set_language("fr")).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🇬🇧 EN", command=lambda: self.set_language("en")).pack(side="left", padx=5)
        ttk.Button(control_frame, text=self.t("random_btn"), command=self.generate_random).pack(side="left", padx=20)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.setup_classic_tab()
        self.setup_extreme_tab()
        self.setup_zodiac_tab()
        self.notebook.select(self.selection["tab"])

        self.setup_result_display()
        self.setup_history_section()
        self.load_history()
        if self.current_burger:
            self.show_result(reload_image=False)

    def setup_classic_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=self.t("classic_tab"))

        self.type_ids = list(bl.BURGER_TYPES)
        self.size_ids = list(bl.SIZES)
        self.sauce_ids = list(bl.CLASSIC_SAUCES)

        ttk.Label(tab, text=self.t("type_label")).grid(row=0, column=0, padx=5, pady=5)
        self.type_combo = self.make_combo(tab, self.type_ids, lambda i: self.item_name("burger_types", i), self.selection["type"])
        self.type_combo.grid(row=1, column=0, padx=5, pady=5)

        ttk.Label(tab, text=self.t("size_label")).grid(row=0, column=1, padx=5, pady=5)
        self.size_combo = self.make_combo(tab, self.size_ids, lambda i: self.item_name("sizes", i), self.selection["size"])
        self.size_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(tab, text=self.t("sauce_label")).grid(row=0, column=2, padx=5, pady=5)
        self.sauce_combo = self.make_combo(tab, self.sauce_ids, self.sauce_name, self.selection["sauce"])
        self.sauce_combo.grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(tab, text="ℹ️", width=3, command=self.show_sauce_info).grid(row=1, column=3)

        extras_frame = ttk.LabelFrame(tab, text=self.t("extras_label"))
        extras_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=10, sticky="ew")
        for column, extra in enumerate(bl.EXTRAS):
            ttk.Checkbutton(extras_frame, text=self.item_name("items", extra),
                            variable=self.extra_vars[extra]).grid(row=0, column=column, padx=8, pady=4)

        ttk.Button(tab, text=self.t("generate_btn"), command=self.generate_classic).grid(row=3, columnspan=4, pady=10)

    def setup_extreme_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=self.t("extreme_tab"))

        ttk.Label(tab, text=self.t("crazy_level")).pack(pady=(10, 0))
        scale_row = ttk.Frame(tab)
        scale_row.pack()
        self.level_value = ttk.Label(scale_row, width=3, text=str(self.crazy_level.get()))
        scale = ttk.Scale(scale_row, from_=bl.EXTREME_MIN_LEVEL, to=bl.EXTREME_MAX_LEVEL, orient="horizontal",
                          length=250, command=self.on_level_change)
        scale.set(self.crazy_level.get())
        scale.pack(side="left")
        self.level_value.pack(side="left", padx=8)

        ttk.Checkbutton(tab, text=self.t("vegan_option"), variable=self.vegan_extreme).pack(pady=5)
        ttk.Button(tab, text=self.t("generate_btn"), command=self.generate_extreme).pack(pady=15)

    def on_level_change(self, value):
        level = round(float(value))
        self.crazy_level.set(level)
        self.level_value.config(text=str(level))

    def setup_zodiac_tab(self):
        tab = ttk.Frame(self.notebook, style="Zodiac.TFrame")
        self.notebook.add(tab, text=self.t("zodiac_tab"))

        ttk.Label(tab, text=self.t("choose_sign"), style="Zodiac.TLabel", font=("Georgia", 14)).pack(pady=10)
        self.sign_ids = list(bl.ZODIAC_SIGNS)
        self.sign_combo = self.make_combo(tab, self.sign_ids, lambda i: self.item_name("zodiac_signs", i), self.selection["sign"])
        self.sign_combo.pack(pady=5)
        self.sign_combo.bind("<<ComboboxSelected>>", self.update_zodiac_display)

        self.element_label = ttk.Label(tab, text="", style="Zodiac.TLabel", font=("Helvetica", 12))
        self.element_label.pack(pady=5)
        ttk.Button(tab, text=self.t("generate_btn"), command=self.generate_zodiac).pack(pady=15)
        self.update_zodiac_display()

    def setup_result_display(self):
        self.result_frame = ttk.Frame(self.root)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.img_label = ttk.Label(self.result_frame)
        self.img_label.pack(side="left", padx=10)

        self.result_text = tk.Text(self.result_frame, height=15, width=60, wrap="word", bg="white",
                                   fg="#333333", font=("Helvetica", 10), state="disabled")
        self.result_text.pack(side="left", fill="both", expand=True)
        self.result_text.tag_configure("title", font=("Helvetica", 14, "bold"))
        self.result_text.tag_configure("bold", font=("Helvetica", 10, "bold"))

    def setup_history_section(self):
        history_frame = ttk.LabelFrame(self.root, text=self.t("history_title"))
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        list_frame = ttk.Frame(history_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.history_list = tk.Listbox(list_frame, height=6, font=("Helvetica", 10))
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_list.yview)
        self.history_list.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.history_list.pack(side="left", fill="both", expand=True)
        self.history_list.bind("<Double-Button-1>", lambda _e: self.show_history())

        btn_frame = ttk.Frame(history_frame)
        btn_frame.pack(fill="x", pady=5)
        for key, command in (("view_btn", self.show_history), ("delete_btn", self.delete_history),
                             ("save_btn", self.save_burger), ("pdf_btn", self.export_pdf),
                             ("copy_btn", self.copy_burger), ("share_btn", self.share_burger)):
            ttk.Button(btn_frame, text=self.t(key), command=command).pack(side="left", padx=5)

    # ----- Génération ----------------------------------------------------

    def selected(self, combo, ids):
        return ids[combo.current()]

    def generate_classic(self):
        extras = [e for e, var in self.extra_vars.items() if var.get()]
        self.set_burger(bl.generate_classic(
            self.selected(self.type_combo, self.type_ids),
            self.selected(self.size_combo, self.size_ids),
            self.selected(self.sauce_combo, self.sauce_ids),
            extras,
        ))

    def generate_extreme(self):
        self.set_burger(bl.generate_extreme(self.crazy_level.get(), self.vegan_extreme.get()))

    def generate_zodiac(self):
        self.set_burger(bl.generate_zodiac(self.selected(self.sign_combo, self.sign_ids)))

    def generate_random(self):
        self.set_burger(bl.generate_random())

    def set_burger(self, burger):
        self.current_burger = burger
        self.show_result()

    # ----- Affichage -----------------------------------------------------

    def show_sauce_info(self):
        sauce = self.selected(self.sauce_combo, self.sauce_ids)
        info = self.trans["sauces"].get(sauce)
        messagebox.showinfo(self.t("info_title"), info["desc"] if info else self.t("no_description"),
                            parent=self.root)

    def update_zodiac_display(self, _event=None):
        sign = self.selected(self.sign_combo, self.sign_ids)
        element, emoji = bl.ZODIAC_SIGNS[sign]
        self.element_label.config(text=f"{self.t('element')} : {self.item_name('elements', element)} {emoji}")

    def show_result(self, reload_image=True):
        view = bl.describe(self.current_burger, self.trans)
        text = self.result_text
        text.config(state="normal")
        text.delete("1.0", tk.END)
        text.insert(tk.END, f"{view.emoji} {view.title} {view.emoji}\n\n", "title")
        text.insert(tk.END, f"{self.t('ingredients_label')}\n", "bold")
        for ingredient in view.ingredients:
            text.insert(tk.END, f"- {ingredient}\n")
        if view.sauce:
            text.insert(tk.END, f"\n{self.t('sauce_label')} {view.sauce}\n", "bold")
            if view.sauce_desc:
                text.insert(tk.END, f"({view.sauce_desc})\n")
        text.insert(tk.END, f"\n{self.t('calories_label')} {view.calories} kcal\n", "bold")
        if view.prediction:
            text.insert(tk.END, f"\n{self.t('prediction_label')} {view.prediction}\n", "bold")
        text.config(state="disabled")
        if reload_image:
            self.load_random_image()

    def load_random_image(self):
        if Image is None or not os.path.isdir(IMAGE_DIR):
            return
        images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not images:
            return
        try:
            img = Image.open(os.path.join(IMAGE_DIR, random.choice(images)))
            img.thumbnail((300, 300))
            self.burger_photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.burger_photo)
        except Exception as error:  # image illisible : on garde l'ancienne
            print(f"Error loading image: {error}", file=sys.stderr)

    # ----- Historique ----------------------------------------------------

    def load_history(self):
        try:
            rows = self.store.recent(20)
        except Exception as error:
            messagebox.showerror(self.t("error_title"), self.t("msg_history_error", error=error))
            return
        self.history_list.delete(0, tk.END)
        self.history_ids = []
        for burger_id, name, data in rows:
            title = name
            if data:  # re-titré dans la langue courante
                try:
                    title = bl.burger_title(json.loads(data), self.trans)
                except Exception:
                    pass
            self.history_ids.append(burger_id)
            self.history_list.insert(tk.END, f"{burger_id} - {title}")

    def selected_history_id(self):
        selection = self.history_list.curselection()
        return self.history_ids[selection[0]] if selection else None

    def show_history(self):
        burger_id = self.selected_history_id()
        if burger_id is None:
            return
        try:
            found = self.store.get(burger_id)
        except Exception as error:
            messagebox.showerror(self.t("error_title"), self.t("msg_history_error", error=error))
            return
        if found:
            self.set_burger(found[0])

    def delete_history(self):
        burger_id = self.selected_history_id()
        if burger_id is None:
            return
        if not messagebox.askyesno(self.t("confirm_title"), self.t("msg_confirm_delete")):
            return
        try:
            self.store.delete(burger_id)
            self.load_history()
            messagebox.showinfo(self.t("success_title"), self.t("msg_deleted"))
        except Exception as error:
            messagebox.showerror(self.t("error_title"), self.t("msg_delete_error", error=error))

    def save_burger(self):
        if not self.require_burger():
            return
        try:
            title = bl.burger_title(self.current_burger, self.trans)
            self.store.save(self.current_burger, title)
            self.load_history()
            messagebox.showinfo(self.t("success_title"), self.t("msg_saved"))
        except Exception as error:
            messagebox.showerror(self.t("error_title"), self.t("msg_save_error", error=error))

    # ----- Export / partage ----------------------------------------------

    def require_burger(self):
        if self.current_burger is None:
            messagebox.showinfo(self.t("confirm_title"), self.t("msg_no_burger"))
            return False
        return True

    def export_pdf(self):
        if not self.require_burger():
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                            title=self.t("pdf_dialog_title"))
        if not path:
            return
        try:
            export_pdf(self.current_burger, self.trans, path)
            messagebox.showinfo(self.t("success_title"), self.t("msg_pdf_saved", path=path))
        except Exception as error:
            messagebox.showerror(self.t("error_title"), self.t("msg_pdf_error", error=error))

    def copy_burger(self):
        if not self.require_burger():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(bl.share_text(self.current_burger, self.trans))
        messagebox.showinfo(self.t("success_title"), self.t("msg_copied"))

    def share_burger(self):
        if not self.require_burger():
            return
        webbrowser.open(TWEET_URL + quote(bl.share_text(self.current_burger, self.trans)))

    # ----- Langue / fermeture ----------------------------------------------

    def set_language(self, language):
        if language == self.language:
            return
        try:
            trans = bl.load_translations(language)
        except (OSError, ValueError) as error:
            messagebox.showerror(self.t("error_title"),
                                 self.t("msg_translation_error", file=bl.translation_path(language), error=error))
            return
        self.selection = {
            "type": self.type_combo.current(), "size": self.size_combo.current(),
            "sauce": self.sauce_combo.current(), "sign": self.sign_combo.current(),
            "tab": self.notebook.index(self.notebook.select()),
        }
        self.language, self.trans = language, trans
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

    def on_close(self):
        self.store.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        UltimateBurgerApp(root)
    except (OSError, ValueError) as error:  # traductions introuvables ou illisibles
        messagebox.showerror("Error", f"Cannot start: {error}")
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
