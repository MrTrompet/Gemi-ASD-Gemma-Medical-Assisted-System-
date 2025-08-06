#onboarding.py
import flet as ft
import os
from pathlib import Path
from utils import save_user_data, load_user_data, clear_user_data
from views.medichat import build_medichat_tab

# ─── Carpeta de datos en APPDATA ───────────────────────────────
APPDATA_DIR = (
    Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    / "GemiASD"
)
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Rutas de perfil y chat en APPDATA ─────────────────────────
PROFILE_PATH = APPDATA_DIR / "gemi_user_data.json"
CHAT_PATH    = APPDATA_DIR / "chat_data.json"

# Ruta fija al JSON de datos
data_path = Path(__file__).parent.parent / "data" / "gemi_user_data.json"

# --- Vista de elección de sesión: crear o continuar ---
def build_session_choice_view(page: ft.Page, app_state: dict) -> ft.View:
    profile_exists = PROFILE_PATH.exists() and PROFILE_PATH.stat().st_size > 0

    def on_create(e: ft.ControlEvent):
        clear_user_data()
        app_state.clear()
        app_state["gender"] = None
        # NO guardamos aquí: esperamos hasta el final de onboarding
        page.go("/gender")

    def on_continue(e: ft.ControlEvent):
        page.go("/main")

    btn_new = ft.OutlinedButton(
        text="Create new profile",
        on_click=on_create,
        style=ft.ButtonStyle(
            side=ft.border.BorderSide(1, ft.Colors.CYAN_300),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            shape=ft.RoundedRectangleBorder(radius=4),
        ),
    )

    controls = [
        ft.Text("Welcome to Gemi", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300),
        ft.Text("Set up your profile to get started:", size=16, color=ft.Colors.WHITE),
    ]

    if profile_exists:
        btn_continue = ft.FilledButton(
            text="Continue Session",
            on_click=on_continue,
            bgcolor=ft.Colors.CYAN_300,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=20, vertical=12)),
        )
        controls.append(ft.Row([btn_new, btn_continue], spacing=20, alignment=ft.MainAxisAlignment.CENTER))
    else:
        controls.append(ft.Row([btn_new], alignment=ft.MainAxisAlignment.CENTER))

    content = ft.Column(
        controls=controls,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30,
        expand=True,
    )
    return ft.View(
        route="/session",
        controls=[ft.Container(content=content, expand=True, alignment=ft.alignment.center)],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
    
def on_create(page: ft.Page, app_state: dict):
    # Borra datos previos y cachés
    clear_user_data()
    app_state.clear()
    page.go("/gender")

def on_continue(page: ft.Page, app_state: dict):
    # Carga perfil existente y va al chat
    data = load_user_data(data_path)
    app_state.update(data)
    page.go("/main")

def build_gender_view(page: ft.Page, app_state: dict) -> ft.View:
    title = ft.Text(
        "What is your sex assigned at birth?",
        color=ft.Colors.WHITE,
        size=20,
        weight=ft.FontWeight.BOLD,
    )

    def on_gender_change(e: ft.ControlEvent):
        app_state["gender"] = e.control.value
        save_user_data(app_state, data_path)
        next_btn.disabled = False
        page.update()

    gender_group = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="Man", label="Man", active_color=ft.Colors.CYAN_300),
            ft.Radio(value="Women", label="Women", active_color=ft.Colors.CYAN_300),
        ], spacing=30, alignment=ft.MainAxisAlignment.CENTER),
        value=app_state.get("gender"),
        on_change=on_gender_change,
    )

    next_btn = ft.FilledButton(
        text="Continue",
        disabled=app_state.get("gender") is None,
        on_click=lambda e: page.go("/age"),
        bgcolor=ft.Colors.CYAN_500,
        color=ft.Colors.BLACK,
        width=150,
    )

    content = ft.Column(
        controls=[
            title,
            gender_group,
            next_btn,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30,
        expand=True,
    )
    return ft.View(
        route="/gender",
        controls=[
            ft.Container(content=content, expand=True, alignment=ft.alignment.center)
        ],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )


def build_age_view(page: ft.Page, app_state: dict) -> ft.View:
    title = ft.Text(
        "What is your age?",
        color=ft.Colors.WHITE,
        size=20,
        weight=ft.FontWeight.BOLD,
    )
    age_val = app_state.get("age", 30)
    label = ft.Text(str(age_val), color=ft.Colors.CYAN_300, size=24)

    def on_slider_change(e: ft.ControlEvent):
        new_age = int(e.control.value)
        app_state["age"] = new_age
        label.value = str(new_age)
        save_user_data(app_state, data_path)
        page.update()

    slider = ft.Slider(
        min=0,
        max=100,
        divisions=100,
        value=age_val,
        on_change=on_slider_change,
        active_color=ft.Colors.CYAN_300,
        inactive_color=ft.Colors.BLUE_GREY_700,
    )
    next_btn = ft.FilledButton(
        text="Continue",
        on_click=lambda e: page.go("/background"),
        bgcolor=ft.Colors.CYAN_500,
        color=ft.Colors.BLACK,
        width=150,
    )

    content = ft.Column(
        controls=[title, label, slider, next_btn],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30,
        expand=True,
    )
    return ft.View(
        route="/age",
        controls=[
            ft.Container(content=content, expand=True, alignment=ft.alignment.center)
        ],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )


def build_background_view(page: ft.Page, app_state: dict) -> ft.View:
    title = ft.Text(
        "Indicate your medical background:",
        color=ft.Colors.WHITE,
        size=18,
        weight=ft.FontWeight.BOLD,
    )

    base = [
        "Hypertension", "Diabetes", "High cholesterol",
        "Atrial fibrillation", "Prior stroke/TIA",
        "Smoking", "Cardiovascular disease",
    ]
    female_only = ["Hormonal contraceptives", "Migraine with aura"]
    opts = base + (female_only if app_state.get("gender") == "Female" else [])
    selected = {k: app_state.get("background", {}).get(k, False) for k in opts}

    rows = []
    # fijamos ancho para las etiquetas
    LABEL_WIDTH = 260

    for k in opts:
        def on_switch(e, key=k):
            selected[key] = e.control.value
            next_btn.disabled = not any(selected.values())
            page.update()

        sw = ft.Switch(
            value=selected[k],
            on_change=on_switch,
            thumb_color=ft.Colors.CYAN_300,
            track_color=ft.Colors.BLUE_GREY_700,
        )

        # Contenedor para el texto, ancho fijo, alineado a la izquierda
        label_container = ft.Container(
            content=ft.Text(k, color=ft.Colors.WHITE),
            width=LABEL_WIDTH,
            alignment=ft.alignment.center_left
        )

        rows.append(
            ft.Row(
                controls=[label_container, sw],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=LABEL_WIDTH + 100  # algo holgado para que no se comprima
            )
        )

    def on_next(e: ft.ControlEvent):
        app_state["background"] = {k: v for k, v in selected.items() if v}
        save_user_data(app_state, PROFILE_PATH)
        page.go("/main")

    next_btn = ft.FilledButton(
        text="Continue",
        on_click=on_next,
        bgcolor=ft.Colors.CYAN_500,
        color=ft.Colors.BLACK,
        width=150,
        disabled=not any(selected.values()),
    )

    content = ft.Column(
        controls=[title, *rows, next_btn],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        expand=True,
    )
    return ft.View(
        route="/background",
        controls=[
            ft.Container(content=content, expand=True, alignment=ft.alignment.center)
        ],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )