# views/pdf_image_viewer.py
import base64
from collections import OrderedDict
from io import BytesIO
import gc

import flet as ft
import fitz
from PIL import Image


def _page_to_jpeg_b64(page: fitz.Page, scale: float, quality: int = 70) -> str:
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class LRUCache:
    def __init__(self, max_items=8):
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


def build_pdf_image_viewer(page: ft.Page, pdf_path: str):
    doc = fitz.open(pdf_path)
    total = len(doc)

    BASE_MAIN = 1.2
    BASE_THUMB = 0.25
    MIN_ZOOM, MAX_ZOOM = 0.7, 1.4

    cache = LRUCache(8)

    usable_w = 850
    scale_fit = usable_w / doc[0].rect.width
    initial_zoom = max(MIN_ZOOM, min(MAX_ZOOM, scale_fit / BASE_MAIN))

    def get_img(i: int, zoom: float, thumb=False):
        k = ("t" if thumb else "m", i, round(zoom, 2))
        val = cache.get(k)
        if val:
            return val
        scale = BASE_THUMB if thumb else BASE_MAIN * zoom
        b64 = _page_to_jpeg_b64(doc[i], scale)
        cache.put(k, b64)
        return b64

    state = {"idx": 0, "zoom": initial_zoom}

    main_img = ft.Image(src_base64=get_img(0, state["zoom"]), fit=ft.ImageFit.NONE)
    main_frame = ft.Container(content=main_img, alignment=ft.alignment.center)
    main_scroll = ft.ListView(expand=True, controls=[main_frame], spacing=0, padding=0)

    page_label = ft.Text(f"Page 1/{total}", size=12, color=ft.Colors.WHITE)

    def set_page(i: int):
        state["idx"] = i
        main_img.src_base64 = get_img(i, state["zoom"])
        page_label.value = f"Page {i+1}/{total}"
        page.update()

    def on_zoom_change(e):
        state["zoom"] = e.control.value
        main_img.src_base64 = get_img(state["idx"], state["zoom"])
        page.update()

    zoom = ft.Slider(min=MIN_ZOOM, max=MAX_ZOOM, divisions=14, value=state["zoom"], on_change=on_zoom_change)

    def reset_zoom(e):
        state["zoom"] = initial_zoom
        zoom.value = initial_zoom
        main_img.src_base64 = get_img(state["idx"], state["zoom"])
        page.update()

    def on_search(e):
        term = e.control.value.strip()
        if not term:
            return
        try:
            hits = [i for i, pg in enumerate(doc) if pg.search_for(term, hit_max=1)]
            if hits:
                set_page(hits[0])
                msg = f"{len(hits)} match(es). First: page {hits[0]+1}"
            else:
                msg = "No matches"
            page.snack_bar = ft.SnackBar(ft.Text(msg))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error searching: {ex}"))
            page.snack_bar.open = True
            page.update()

    thumbs = ft.ListView(height=600, spacing=5)
    for i in range(total):
        thumbs.controls.append(
            ft.GestureDetector(
                content=ft.Image(src_base64=get_img(i, 1.0, thumb=True), width=80, height=110, fit=ft.ImageFit.COVER),
                on_tap=lambda e, idx=i: set_page(idx),
            )
        )

    tools = ft.Row(
        [ft.TextField(hint_text="Search text...", width=250, on_submit=on_search),
         ft.Text("Zoom", color=ft.Colors.WHITE, size=12),
         zoom, page_label],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    viewer = ft.Column(
        [tools, ft.GestureDetector(content=main_scroll, on_double_tap=reset_zoom)],
        spacing=10,
        expand=True,
    )

    sidebar = ft.Container(width=110, bgcolor=ft.Colors.BLUE_GREY_800, padding=5, border_radius=8, content=thumbs)

    ctrl = ft.Row([sidebar, viewer], spacing=15)

    def dispose():
        try: doc.close()
        except: pass
        cache.clear()
        main_img.src_base64 = ""
        try: fitz.TOOLS.store_gc()
        except: pass
        gc.collect()

    return ctrl, dispose
