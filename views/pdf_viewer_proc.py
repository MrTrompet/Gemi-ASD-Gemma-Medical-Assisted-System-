# views/pdf_viewer_proc.py
import sys, gc
import flet as ft
import fitz

from .pdf_text_viewer import build_pdf_text_viewer
from .pdf_image_viewer import build_pdf_image_viewer

def _main(page: ft.Page, pdf_path: str):
    page.window_title = f"Visor PDF - {pdf_path.split('/')[-1]}"
    page.padding = 0
    page.bgcolor = "#2b2f33"

    has_text = False
    try:
        d = fitz.open(pdf_path)
        has_text = bool(d[0].get_text().strip())
        d.close()
    except Exception:
        pass

    ctrl, dispose = (build_pdf_text_viewer(page, pdf_path)
                     if has_text
                     else build_pdf_image_viewer(page, pdf_path))

    def close_and_exit(e=None):
        try: dispose()
        except Exception: pass
        gc.collect()
        sys.exit(0)

    page.appbar = ft.AppBar(
        title=ft.Text("Visor PDF"),
        actions=[ft.IconButton(ft.Icons.CLOSE, on_click=close_and_exit)],
        bgcolor="#1f2225"
    )
    page.add(ctrl)

    # eventos de cierre (según versión de Flet alguno puede no existir)
    page.on_disconnect = close_and_exit
    try:
        page.window_on_close = close_and_exit
    except AttributeError:
        pass
    try:
        page.window_destroy = close_and_exit
    except AttributeError:
        pass

def run(pdf_path: str):
    ft.app(
        target=lambda p: _main(p, pdf_path),
        assets_dir="assets",
        view=ft.AppView.FLET_APP
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m views.pdf_viewer_proc <ruta_pdf>")
        sys.exit(1)
    run(sys.argv[1])
