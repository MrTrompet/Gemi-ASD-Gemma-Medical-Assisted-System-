import flet as ft
import fitz
from collections import OrderedDict
import re, gc

# ----------------- Utils -----------------
class LRUCache:
    def __init__(self, max_items=30):
        self.max = max_items
        self.data: OrderedDict = OrderedDict()

    def get(self, k):
        if k in self.data:
            self.data.move_to_end(k)
            return self.data[k]
        return None

    def put(self, k, v):
        self.data[k] = v
        self.data.move_to_end(k)
        if len(self.data) > self.max:
            self.data.popitem(last=False)

    def clear(self):
        self.data.clear()


def _highlight(text: str, term: str) -> str:
    """Resalta coincidencias en markdown usando **...**."""
    if not term:
        return text
    try:
        pat = re.compile(re.escape(term), re.IGNORECASE)
        return pat.sub(lambda m: f"**{m.group(0)}**", text)
    except Exception:
        return text


# ----------------- Viewer -----------------
def build_pdf_text_viewer(page: ft.Page, pdf_path: str):
    """
    Devuelve (control, dispose_fn).
    Muestra el PDF como texto markdown, con búsqueda y slider de tamaño (escala).
    """
    # Tema local
    BG = "#2b2f33"
    PANEL = "#34393f"
    ACCENT = ft.Colors.CYAN_300
    TEXT = "#ECEFF1"

    page.bgcolor = BG

    doc = fitz.open(pdf_path)
    total = len(doc)
    cache = LRUCache(30)

    def get_text(i: int) -> str:
        hit = cache.get(i)
        if hit is not None:
            return hit
        md_txt = doc[i].get_text("markdown").strip()
        if not md_txt:
            md_txt = doc[i].get_text().strip() or f"[Page {i+1} no text]"
        cache.put(i, md_txt)
        return md_txt

    state = {"idx": 0, "term": "", "scale": 1.1}

    md = ft.Markdown(
        value=get_text(0),
        selectable=True,
        extension_set="gitHubWeb",
        code_theme="github-dark",
        expand=True,
    )

    # Contenedor para poder escalar
    md_holder = ft.Container(expand=True, content=md, scale=state["scale"])

    page_label = ft.Text(f"Page 1/{total}", size=12, color=TEXT)

    # --- Navegación ---
    def set_page(i: int):
        state["idx"] = i
        raw = get_text(i)
        md.value = _highlight(raw, state["term"])
        page_label.value = f"Page {i+1}/{total}"
        rail.selected_index = i
        page.update()

    # --- Búsqueda ---
    def do_search(term: str):
        state["term"] = term.strip()
        if not state["term"]:
            set_page(state["idx"])
            return

        hits = []
        low = state["term"].lower()
        for i in range(total):
            t = cache.get(i) or doc[i].get_text()
            if low in t.lower():
                hits.append(i)

        if hits:
            set_page(hits[0])
            msg = f"{len(hits)} cmatch(es). First: page {hits[0] + 1}"
        else:
            msg = "No matches"

        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    tf_search = ft.TextField(
        hint_text="Search...",
        width=250,
        on_submit=lambda e: do_search(e.control.value),   # <-- aquí el fix
        border_color=ACCENT,
        color=TEXT,
    )

    # --- Tamaño (escala) ---
    def on_scale_change(e):
        state["scale"] = float(e.control.value)
        md_holder.scale = state["scale"]
        md_holder.update()

    scale_slider = ft.Slider(
        min=0.8,
        max=1.8,
        divisions=10,
        value=state["scale"],
        on_change=on_scale_change,
        active_color=ACCENT,
        inactive_color=ft.Colors.BLUE_GREY_700,
        width=200,
    )

    # --- Rail izquierda ---
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=70,
        min_extended_width=120,
        extended=True,
        bgcolor=PANEL,
        group_alignment=-0.95,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DESCRIPTION_OUTLINED,
                selected_icon=ft.Icons.DESCRIPTION,
                label=f"Pág {i+1}",
            )
            for i in range(total)
        ],
        on_change=lambda e: set_page(e.control.selected_index),
    )

    # --- Toolbar ---
    tools = ft.Container(
        bgcolor=PANEL,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        content=ft.Row(
            [tf_search, ft.Text("Size", color=TEXT, size=12), scale_slider, page_label],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # --- Viewer (fondo claro para ver el texto negro del Markdown) ---
    viewer = ft.Container(
        expand=True,
        bgcolor="#ffffff",
        border_radius=8,
        padding=15,
        content=ft.ListView(controls=[md_holder], expand=True, auto_scroll=False),
    )

    layout = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1, color=ft.Colors.BLUE_GREY_800),
            ft.Column([tools, viewer], expand=True, spacing=10),
        ],
        spacing=10,
        expand=True,
    )

    def dispose():
        try:
            doc.close()
        except Exception:
            pass
        cache.clear()
        gc.collect()

    return layout, dispose

