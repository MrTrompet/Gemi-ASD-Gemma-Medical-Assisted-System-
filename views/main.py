#main.py
import flet as ft
from pathlib import Path
from utils import save_user_data
from views.emergency import build_emergency_tab
from views.medichat import build_medichat_tab
from views.settings import build_settings_view
from views.calendario import build_calendar_view
from views.pulsometro import build_pulsometer_tab
from datetime import datetime
import asyncio
import os

# ——— Carpeta de datos en APPDATA ————————————————————————
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ——— Ahora leemos/escribimos el JSON ahí ——————————————————
DATA_PATH = APPDATA_DIR / "gemi_user_data.json"

def build_main_view(page: ft.Page, app_state: dict, logo_data_uri: str) -> ft.View:
    # Inicializar estado
    selected = app_state.get("selected_tab", None)
    app_state.setdefault("pinned", False)

    # ─── Reloj ─────────────────────────────────────────────────
    clock = ft.Text(datetime.now().strftime("%H:%M:%S"), color=ft.Colors.CYAN_200, size=14)
    async def _clock_loop():
        while True:
            clock.value = datetime.now().strftime("%H:%M:%S")
            page.update()
            await asyncio.sleep(1)
    # arrancar el loop sin bloquear
    asyncio.create_task(_clock_loop())

    # ─── Drawer ───────────────────────────────────────────────
    drawer = ft.NavigationDrawer(
        controls=[
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.PERSON, size=20, color=ft.Colors.CYAN_300),
                label="Profile"
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.CYAN_300),
                label="Settings"
            ),
        ],
        tile_padding=ft.padding.symmetric(vertical=8, horizontal=16),
        open=False,
    )
    def on_drawer_change(e: ft.ControlEvent):
        drawer.open = False
        page.go("/settings" if e.control.selected_index == 1 else "/profile")
        page.update()
    drawer.on_change = on_drawer_change

    def toggle_menu(e):
        drawer.open = not drawer.open
        page.update()

    # ─── Cambio de pestaña ────────────────────────────────────
    def set_tab(idx):
        app_state["selected_tab"] = idx
        _update_tab_colors(idx)
        update_body()
        page.update()

    def _update_tab_colors(idx):
        for i, btn in enumerate((btn_e, btn_m, btn_c, btn_p)):
            btn.bgcolor = ft.Colors.CYAN_300 if i == idx else ft.Colors.BLUE_GREY_700

    # ─── AppBar con reloj y ayuda ─────────────────────────────
    leading = (
        ft.IconButton(icon=ft.Icons.MENU, on_click=toggle_menu)
        if selected is None else
        ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: set_tab(None))
    )
    help_btn = ft.IconButton(
        icon=ft.Icons.NOTIFICATION_ADD,
        icon_color=ft.Colors.CYAN_300,
        tooltip="Future Help Feature",
        on_click=lambda e: (
            setattr(page, "snack_bar", ft.SnackBar(ft.Text("Future Help Feature"))),
            setattr(page.snack_bar, "open", True),
            page.update()
        )
    )
    app_bar = ft.AppBar(
        leading=leading,
        title=ft.Text("Gemi", color=ft.Colors.CYAN_300, size=25),
        actions=[clock, help_btn],
        bgcolor=ft.Colors.BLUE_GREY_900,
        elevation=5,
    )

    # ─── Feed / Guía de usuario ──────────────────────────────
# ─── Feed / User Guide ──────────────────────────────
    guide = [
       ft.Text("Welcome to Gemi", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300),
       ft.Text("Your AI-powered medical diagnostic assistant and health companion", size=16, color=ft.Colors.WHITE),
       ft.Divider(color=ft.Colors.BLUE_GREY_700),
       ft.Text("• In Emergency: Select symptoms from a comprehensive list to evaluate potential risks of critical conditions like strokes, heart attacks, or cardiac arrests. Gemi provides immediate insights to help you act fast.", color=ft.Colors.WHITE),
       ft.Text("• In Medichat: Engage in conversations with our friendly AI-powered first-aid assistant. It offers quick answers and basic health advice based on a vast knowledge base, ready to assist you anytime.", color=ft.Colors.WHITE),
       ft.Text("• In Calendar: Effortlessly schedule your medication doses and appointments using natural language. Gemi understands your commands and sends automatic alerts and reminders, so you never miss a beat.", color=ft.Colors.WHITE),
       ft.Text("• In Pulse Monitor: Measure your heart rate in real-time. Our new interactive tool provides instant and accurate readings, helping you monitor your cardiovascular health on the go.", color=ft.Colors.WHITE),
       ft.Text("• Use Settings: Customize your Gemi experience. Reset your stored data, configure personalized notification preferences, or adjust other app settings to fit your needs.", color=ft.Colors.WHITE),
       ft.Divider(color=ft.Colors.BLUE_GREY_700),
       ft.Text("Quick Tips:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
       ft.Text("• Keep your profile updated with your latest health information to ensure Gemi provides the most accurate and personalized analysis.", color=ft.Colors.WHITE),
       ft.Text("• Review your Medichat history. It can be a useful resource to look back at previous advice, especially during emergencies.", color=ft.Colors.WHITE),
       ft.Text("• Schedule not only medication but also appointments and check-ups in the Calendar to stay on top of your health commitments.", color=ft.Colors.WHITE),
       ft.Text("• Remember: Gemi is a supportive tool, not a substitute for professional medical advice. Always contact a healthcare specialist if you notice serious or persistent symptoms.", color=ft.Colors.WHITE),
    ]
    feed_content = ft.Column(
        guide,
        scroll=ft.ScrollMode.ALWAYS,
        spacing=12,
        expand=True,
    )
    feed = ft.Container(
        content=feed_content,
        padding=ft.padding.all(20),
        bgcolor=ft.Colors.BLUE_GREY_800,
        border_radius=12,
        expand=True,
        animate_opacity=ft.Animation(duration=200, curve=ft.AnimationCurve.EASE_IN_OUT), 
    )

    # ─── Contenedor dinámico ──────────────────────────────────
    body_container = ft.Container(expand=True, alignment=ft.alignment.center)
    def update_body():
        sel = app_state.get("selected_tab", None)
        if sel is None:
            body_container.content = feed
        elif sel == 0:
            body_container.content = build_emergency_tab(page, app_state, set_tab)
        elif sel == 1:
            body_container.content = build_medichat_tab(page, app_state,set_tab)
        elif sel == 2:
            body_container.content = build_calendar_view(page, app_state, set_tab)
        elif sel == 3:
            body_container.content = build_pulsometer_tab(page, app_state, set_tab)
    update_body()  

    # ─── Botones de pestaña + hover ───────────────────────────
    def _on_enter(e, btn):
        btn.bgcolor = ft.Colors.CYAN_300; page.update()
    def _on_exit(e, btn, idx):
        btn.bgcolor = ft.Colors.CYAN_300 if app_state.get("selected_tab") == idx else ft.Colors.BLUE_GREY_700
        page.update()

    btn_e = ft.Container(
        content=ft.Text("Emergency", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.CYAN_300 if selected==0 else ft.Colors.BLUE_GREY_700,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=8,
        on_click=lambda e: set_tab(0),
    )
    btn_e.on_hover = lambda e: _on_enter(e, btn_e) if e.data=="true" else _on_exit(e, btn_e, 0)

    btn_m = ft.Container(
        content=ft.Text("Medichat", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.CYAN_300 if selected==1 else ft.Colors.BLUE_GREY_700,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=8,
        on_click=lambda e: set_tab(1),
    )
    btn_m.on_hover = lambda e: _on_enter(e, btn_m) if e.data=="true" else _on_exit(e, btn_m, 1)

    btn_c = ft.Container(
        content=ft.Text("Calendar", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.CYAN_300 if selected==2 else ft.Colors.BLUE_GREY_700,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=8,
        on_click=lambda e: set_tab(2),
    )
    btn_c.on_hover = lambda e: _on_enter(e, btn_c) if e.data=="true" else _on_exit(e, btn_c, 2)

    btn_p = ft.Container(
        content=ft.Text("Heart Rate", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.CYAN_300 if selected==3 else ft.Colors.BLUE_GREY_700,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        border_radius=8,
        on_click=lambda e: set_tab(3),
    )
    btn_p.on_hover = lambda e: _on_enter(e, btn_p) if e.data=="true" else _on_exit(e, btn_p, 3)

    tabs_row = ft.Row([btn_e, btn_m, btn_c, btn_p],
                      alignment=ft.MainAxisAlignment.CENTER,
                      spacing=10)

    # ─── Botón “Pin” ─────────────────────────────────────────
    def toggle_pin(e):
        pinned = not app_state["pinned"]
        app_state["pinned"] = pinned
        # esta es la forma correcta:
        page.window.always_on_top = pinned
        # actualizamos el icono y tooltip
        pin_btn.icon    = ft.Icons.PUSH_PIN if pinned else ft.Icons.PUSH_PIN_OUTLINED
        pin_btn.tooltip = "Unpin" if pinned else "Pin"
        page.update()

    pin_btn = ft.IconButton(
        icon=ft.Icons.PUSH_PIN_OUTLINED,
        tooltip="Pin",
        icon_color=ft.Colors.CYAN_300,
        on_click=toggle_pin,
    )


    # ─── Vista final ─────────────────────────────────────────
    return ft.View(
        route="/main",
        appbar=app_bar,
        drawer=drawer,
        floating_action_button=pin_btn,
        controls=[
            ft.Divider(thickness=1, color=ft.Colors.BLUE_GREY_700),
            tabs_row,
            ft.Divider(thickness=1, color=ft.Colors.BLUE_GREY_700),
            body_container,
            ft.Container(
                content=ft.Text("Powered by Google DeepMind", size=10, color=ft.Colors.WHITE, opacity=0.6),
                alignment=ft.alignment.bottom_center,
                height=30,
            ),
        ],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
