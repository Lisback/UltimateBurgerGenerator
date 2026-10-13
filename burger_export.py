"""Export PDF d'un burger (fpdf2, sans tkinter)."""
from fpdf import FPDF

from burger_logic import describe

# Les polices PDF de base ne gèrent que le latin-1 : on translittère l'essentiel
# et on retire le reste (emoji, symboles du zodiaque).
_REPLACEMENTS = {
    "œ": "oe", "Œ": "Oe", "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...",
}


def pdf_safe(text: str) -> str:
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "ignore").decode("latin-1").strip()


def build_pdf(burger: dict, trans: dict) -> FPDF:
    view = describe(burger, trans)
    pdf = FPDF()
    pdf.add_page()

    def line(text, style="", size=12, align="L", height=9):
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, height, pdf_safe(text), align=align, new_x="LMARGIN", new_y="NEXT")

    line(view.title, "B", 18, "C", 12)
    pdf.ln(6)
    line(trans["ingredients_label"], "B")
    for ingredient in view.ingredients:
        line(f"- {ingredient}")
    if view.sauce:
        pdf.ln(3)
        line(f"{trans['sauce_label']} {view.sauce}", "B")
        if view.sauce_desc:
            line(view.sauce_desc, "I", 11)
    pdf.ln(3)
    line(f"{trans['calories_label']} {view.calories} kcal", "B")
    if view.prediction:
        pdf.ln(3)
        line(f"{trans['prediction_label']} {view.prediction}", "I")
    return pdf


def export_pdf(burger: dict, trans: dict, path: str) -> None:
    build_pdf(burger, trans).output(path)
