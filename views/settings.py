#settings.py
import flet as ft
import asyncio
import os
from pathlib import Path
from utils import clear_user_data, save_user_data

# ────────── Carpeta de datos en APPDATA ────────────────────────
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ────────── Subcarpetas y archivos de usuario ──────────────────
PDF_DIR         = APPDATA_DIR / "pdfs"
PHOTOS_DIR      = APPDATA_DIR / "photos"
USER_DATA_FILE  = APPDATA_DIR / "gemi_user_data.json"

async def _perform_reset(page: ft.Page, app_state: dict):
    """Borra JSON, PDFs y fotos, limpia estado y reinicia al splash (/)."""
    spinner = ft.AlertDialog(
        modal=True,
        content=ft.Column(
            [
                ft.ProgressRing(),
                ft.Text("Deleting your information...", color=ft.Colors.WHITE)
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )
    page.dialog = spinner
    spinner.open = True
    page.update()

    await asyncio.sleep(0.5)

    clear_user_data()
    app_state.clear()

    spinner.open = False
    page.update()
    page.views.clear()
    page.go("/")


def build_settings_view(page: ft.Page, app_state: dict) -> ft.View:
    """
    Vista de Configuración:
      • Notificaciones por correo
      • Restablecer aplicación con spinner
      • Botón de retroceso
    """
    def on_toggle_notify(e: ft.ControlEvent):
        app_state["notify_enabled"] = e.control.value
        save_user_data(app_state, USER_DATA_FILE)
        email_field.disabled = not e.control.value
        send_test_btn.disabled = not e.control.value
        page.update()

    def on_email_change(e: ft.ControlEvent):
        app_state["notify_email"] = e.control.value
        save_user_data(app_state, USER_DATA_FILE)

    def on_send_test(e: ft.ControlEvent):
        addr = app_state.get("notify_email", "").strip()
        if not addr or "@" not in addr:
            msg = "✉️ Enter a valid email to test."
        else:
            msg = f"📧 Test email sent to{addr}"
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    notify_toggle = ft.Switch(
        label="Send report by email",
        value=app_state.get("notify_enabled", False),
        on_change=on_toggle_notify,
        thumb_color=ft.Colors.CYAN_300,
        track_color=ft.Colors.BLUE_GREY_700,
    )

    email_field = ft.TextField(
        label="Email address",
        hint_text="user@example.com",
        value=app_state.get("notify_email", ""),
        on_change=on_email_change,
        disabled=not app_state.get("notify_enabled", False),
        expand=True,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )

    send_test_btn = ft.FilledButton(
        "Send test email",
        on_click=on_send_test,
        bgcolor=ft.Colors.CYAN_300,
        color=ft.Colors.BLACK,
        disabled=not app_state.get("notify_enabled", False),
    )

    dlg = ft.AlertDialog(modal=True)

    def on_confirm(e: ft.ControlEvent):
        dlg.open = False
        page.update()
        page.run_async(_perform_reset, page, app_state)

    dlg.title = ft.Text("¿Eliminar TODOS los datos?")
    dlg.content = ft.Text(
        "Perfiles, PDFs y fotos se borrarán. Esta acción es irreversible."
    )
    dlg.actions = [
        ft.TextButton("Cancelar",
                      on_click=lambda e: (setattr(dlg, "open", False), page.update())),
        ft.FilledButton("Borrar",
                        bgcolor=ft.Colors.RED_400,
                        color=ft.Colors.WHITE,
                        on_click=on_confirm),
    ]
    page.dialog = dlg

    reset_btn = ft.FilledButton(
        "Reset application",
        bgcolor=ft.Colors.RED_400,
        color=ft.Colors.WHITE,
        on_click=lambda e: (setattr(dlg, "open", True), page.update()),
    )

    app_bar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            icon_color=ft.Colors.CYAN_300,
            on_click=lambda e: page.go("/main"),
        ),
        title=ft.Text(
            "Configuration",
            color=ft.Colors.CYAN_300,
            size=20,
            weight=ft.FontWeight.BOLD,
        ),
        bgcolor=ft.Colors.BLUE_GREY_900,
    )

    body = ft.Container(
        padding=ft.padding.all(20),
        content=ft.Column(
            controls=[
                ft.Text("Notifications", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                notify_toggle,
                email_field,
                send_test_btn,
                ft.Divider(opacity=0.3),
                reset_btn,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        ),
    )

    return ft.View(
        route="/settings",
        controls=[app_bar, body],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
