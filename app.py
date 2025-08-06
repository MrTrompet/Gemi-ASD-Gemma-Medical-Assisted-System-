#app.py
import asyncio
import atexit


@atexit.register
def _print_pending_tasks():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # El loop ya está cerrado: no hay nada que imprimir
        return

    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    if not pending:
        return

    print(f"\n=== TAREAS PENDIENTES AL SALIR ({len(pending)}) ===")
    for t in pending:
        print(" •", t)

import flet as ft
import os
import base64
import multiprocessing
from pathlib import Path
import threading 

from utils import load_user_data, clear_user_data
from views.logo import build_logo_view
from views.privacy import build_privacy_view
from views.onboarding import (
    build_session_choice_view,
    build_gender_view,
    build_age_view,
    build_background_view,
)
from views.main import build_main_view
from views.profile import build_profile_view
from views.settings import build_settings_view
import sys

# --- Carpeta de datos en APPDATA ---
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Asegurar UTF-8 sin petar en EXE de PyInstaller ---
for stream_name in ("stdin", "stdout", "stderr"):
    stream = getattr(sys, stream_name, None)
    if stream is not None and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    

# --- Rutas de datos y assets ---
BASE_DIR   = Path(__file__).parent
DATA_FILE  = APPDATA_DIR / "gemi_user_data.json"
LOGO_FILE  = BASE_DIR / "gemi_logo.png"

TIMERS: list[threading.Timer] = []

async def main(page: ft.Page):
    # ──────────────────────────────────────────────────────────────
    # Configuración general de la página
    # ──────────────────────────────────────────────────────────────
    page.title       = "Gemi – Medical Assistant"
    page.theme_mode  = ft.ThemeMode.DARK
    page.bgcolor     = ft.Colors.BLUE_GREY_900

    # ──────────────────────────────────────────────────────────────
    # Fijar tamaño y comportamiento de ventana en Desktop
    # ──────────────────────────────────────────────────────────────
    
    
    page.window.width = 1220
    page.window.height = 700
    page.window.center()
    page.update()
    
    async def on_close(e):
        for t in TIMERS:
            t.cancel()
        page.on_close = on_close
    

    # Carga (o inicializa) el estado de la aplicación
    app_state = load_user_data(DATA_FILE)
    app_state.setdefault("gender", None)

    # Codifica el logo en base64 para el splash
    if LOGO_FILE.exists():
        b64 = base64.b64encode(LOGO_FILE.read_bytes()).decode()
        logo_data_uri = f"data:image/png;base64,{b64}"
    else:
        logo_data_uri = ""

    async def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        route = page.route or "/"

        # 1) Splash screen en "/"
        if route == "/":
            page.views.append(build_logo_view(page, logo_data_uri))
            page.update()
            # Inicializa el LLM en background (logs silenciados)
            llm_task = asyncio.get_event_loop().run_in_executor(None, lambda: None)
            await asyncio.sleep(2)
            await llm_task
            page.go("/privacy")
            return

        # 2) Privacy Notice
        if route == "/privacy":
            page.views.append(build_privacy_view(page))
            page.update()
            return

        # 3) Session choice (crear/continuar)
        if route == "/session":
            page.views.append(build_session_choice_view(page, app_state))
            page.update()
            return

        # 4) Si ya existe perfil y entran a /session, saltar a /main
        profile_exists = DATA_FILE.exists() and DATA_FILE.stat().st_size > 0
        if profile_exists and route == "/session":
            page.go("/main")
            return

        # 5) Onboarding paso a paso
        if route == "/gender":
            page.views.append(build_gender_view(page, app_state))
        elif route == "/age":
            page.views.append(build_age_view(page, app_state))
        elif route == "/background":
            page.views.append(build_background_view(page, app_state))

        # 6) Vistas principales de la app
        elif route == "/main":
            page.views.append(build_main_view(page, app_state, logo_data_uri))
        elif route == "/profile":
            page.views.append(build_profile_view(page, app_state))
        elif route == "/settings":
            page.views.append(build_settings_view(page, app_state))
        else:
            # Ruta desconocida
            page.views.append(
                ft.View(
                    route=route,
                    controls=[ft.Text(f"Unknown path: {route}", color=ft.Colors.WHITE)],
                    bgcolor=ft.Colors.BLUE_GREY_900,
                )
            )

        page.update()

    # Asigna el handler de rutas y arranca en "/"
    page.on_route_change = route_change
    page.go("/")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    ft.app(
        target=main,
        assets_dir="assets",
        view=ft.AppView.FLET_APP,
    )
