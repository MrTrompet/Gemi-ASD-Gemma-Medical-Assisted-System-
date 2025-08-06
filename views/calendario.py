import atexit
import threading

import flet as ft
import calendar
import re
import winsound
import json
from datetime import timedelta, datetime
from pathlib import Path
from utils import save_json
import os

# --- LIMPIEZA DE TIMERS AL SALIR ---
TIMERS: list[threading.Timer] = []

@atexit.register
def _cleanup_timers():
    """
    Cancela todos los threading.Timer pendientes al cerrar la aplicación.
    """
    for t in TIMERS:
        try:
            t.cancel()
        except Exception:
            pass

# ─── Carpeta de datos en APPDATA ────────────────────────────────
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Ruta al JSON de tareas de medicación ───────────────────────
MED_TASKS_FILE = APPDATA_DIR / "medicine_tasks.json"

# ------------------------------------------------------------------
# LÓGICA DE DATOS
# ------------------------------------------------------------------

def _load_treatments():
    """
    Carga la lista de tratamientos, manejando formatos antiguos y nuevos.
    """
    if not MED_TASKS_FILE.exists():
        return []
    try:
        with open(MED_TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            treatments_list = [data]
        elif isinstance(data, list):
            treatments_list = data
        else:
            treatments_list = []
        for treatment in treatments_list:
            if isinstance(treatment, dict) and "schedule" in treatment:
                treatment["schedule"] = [datetime.fromisoformat(dt) for dt in treatment["schedule"]]
        return treatments_list
    except (json.JSONDecodeError, TypeError):
        try:
            MED_TASKS_FILE.unlink()
        except OSError:
            pass
        return []


def _save_treatments(treatments):
    """
    Guarda la lista completa de tratamientos en el JSON.
    """
    APPDATA_DIR.mkdir(exist_ok=True)
    serializable = []
    for t in treatments:
        serializable.append({
            "medicine": t["medicine"],
            "schedule": [dt.isoformat() for dt in t["schedule"]]
        })
    with open(MED_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)

# ------------------------------------------------------------------
# NOTIFICACIONES (threading.Timer)
# ------------------------------------------------------------------

def _show_notification(page: ft.Page, medicine_name: str):
    """
    Muestra la alerta en la UI de Flet.
    """
    winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
    page.snack_bar = ft.SnackBar(
        content=ft.Text(f"🔔 It's time for your medication: {medicine_name}"),
        bgcolor=ft.Colors.CYAN_800
    )
    page.snack_bar.open = True
    page.update()


def schedule_notifications_for_treatment(page: ft.Page, treatment: dict):
    medicine_name = treatment.get("medicine", "medication")
    for dt in treatment.get("schedule", []):
        delay = (dt - datetime.now()).total_seconds()
        if delay > 0:
            t = threading.Timer(
                delay,
                lambda mn=medicine_name: _show_notification(page, mn)
            )
            t.daemon = True         # ← marca el hilo como daemon
            t.start()
            TIMERS.append(t)

# ------------------------------------------------------------------
# GENERACIÓN DE HORARIOS
# ------------------------------------------------------------------

def _generate_schedule(page: ft.Page, app_state: dict, instruction: str):
    """
    Parsea la instrucción, añade el tratamiento, guarda y actualiza UI.
    Luego programa notificaciones.
    """
    pattern = r"(.+?)\s+every\s+(\d+)\s+(hours?)\s+x\s*(\d+)\s+(days?)"
    m = re.match(pattern, instruction.strip(), re.IGNORECASE)
    if not m:
        page.snack_bar = ft.SnackBar(ft.Text(
            "❌ Invalid format. Use: 'medication every 8 hours x 5 days'"
        ))
        page.snack_bar.open = True
        page.update()
        return

    med = m.group(1).strip().capitalize()
    hours = int(m.group(2))
    days = int(m.group(4))

    now = datetime.now()
    total_doses = days * 24 // hours
    schedule = [now + timedelta(hours=hours * i) for i in range(total_doses)]

    new_treatment = {"medicine": med, "schedule": schedule}
    app_state.setdefault("treatments", []).append(new_treatment)
    _save_treatments(app_state["treatments"])

    page.snack_bar = ft.SnackBar(ft.Text(
        f"✅ Added {total_doses} doses of {med}"
    ))
    page.snack_bar.open = True
    page.update()

    _build_calendar_and_events(page, app_state)
    schedule_notifications_for_treatment(page, new_treatment)

# ------------------------------------------------------------------
# CONSTRUCCIÓN DEL CALENDARIO
# ------------------------------------------------------------------

def _build_calendar_and_events(page: ft.Page, app_state: dict):
    year = app_state.get("calendar_year")
    month = app_state.get("calendar_month")
    cal_container = app_state.get("_calendar_container")
    cal_container.controls.clear()

    all_doses = []
    for t in app_state.get("treatments", []):
        all_doses.extend(t.get("schedule", []))

    days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cal_container.controls.append(
        ft.Row([
            ft.Text(d, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200)
            for d in days_header
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    )

    for week in calendar.monthcalendar(year, month):
        row_cells = []
        for day in week:
            cell = ft.Container(width=40, height=40, alignment=ft.alignment.center)
            if day != 0:
                date_obj = datetime(year, month, day).date()
                has_event = any(dt.date() == date_obj for dt in all_doses)
                items = [ft.Text(str(day), color=ft.Colors.WHITE)]
                if has_event:
                    items.append(ft.Container(
                        width=6, height=6, bgcolor=ft.Colors.CYAN_300, border_radius=3
                    ))
                cell.content = ft.Column(
                    items,
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
                cell.on_click = lambda _, d=day: _show_events_for_day(page, app_state, d)
            row_cells.append(cell)
        cal_container.controls.append(
            ft.Row(row_cells, alignment=ft.MainAxisAlignment.SPACE_AROUND)
        )

    _show_events_for_day(
        page,
        app_state,
        app_state.get("selected_day", datetime.now().day)
    )
    page.update()

# ------------------------------------------------------------------
# MUESTRA DE EVENTOS POR DÍA
# ------------------------------------------------------------------

def _show_events_for_day(page: ft.Page, app_state: dict, day: int):
    app_state["selected_day"] = day
    ev_container = app_state.get("_events_container")
    ev_container.controls.clear()

    date_sel = datetime(
        app_state.get("calendar_year"),
        app_state.get("calendar_month"),
        day
    ).date()
    items = []
    for t in sorted(app_state.get("treatments", []), key=lambda x: x.get("medicine", "")):
        for dt in sorted(t.get("schedule", [])):
            if dt.date() == date_sel:
                items.append(ft.Text(
                    f"• {dt.strftime('%H:%M')} — {t.get('medicine')}",
                    color=ft.Colors.WHITE
                ))

    if items:
        ev_container.controls.extend(items)
    else:
        ev_container.controls.append(ft.Text(
            "No scheduled doses for this day.",
            color=ft.Colors.WHITE, opacity=0.7
        ))
    page.update()

# ------------------------------------------------------------------
# NAVEGACIÓN DE MESES
# ------------------------------------------------------------------

def _change_month(page: ft.Page, app_state: dict, delta: int):
    new_date = datetime(
        app_state.get("calendar_year"),
        app_state.get("calendar_month"),
        1
    ) + timedelta(days=31 * delta)
    app_state["calendar_month"] = new_date.month
    app_state["calendar_year"] = new_date.year
    app_state.get("_month_label").value = f"{calendar.month_name[new_date.month]} {new_date.year}"
    _build_calendar_and_events(page, app_state)

# ------------------------------------------------------------------
# VISTA PRINCIPAL
# ------------------------------------------------------------------

def build_calendar_view(page: ft.Page, app_state: dict, set_tab: callable) -> ft.Container:
    """
    Construye toda la vista del calendario con su lógica de notificaciones.
    """
    today = datetime.today()
    app_state["treatments"] = _load_treatments()
    app_state.setdefault("calendar_year", today.year)
    app_state.setdefault("calendar_month", today.month)
    app_state.setdefault("selected_day", today.day)

    # Programa notificaciones al iniciar
    if not app_state.get("notifications_scheduled", False):
        for t in app_state["treatments"]:
            schedule_notifications_for_treatment(page, t)
        app_state["notifications_scheduled"] = True

    input_box = ft.TextField(
        label="E.g. Ibuprofen every 8 hours x 7 days",
        expand=True,
        border_color=ft.Colors.CYAN_400
    )
    schedule_btn = ft.FilledButton(
        "Add Treatment",
        on_click=lambda e: _generate_schedule(page, app_state, input_box.value)
    )

    cal_container = ft.Column(spacing=5, expand=True)
    events_container = ft.Column(spacing=4, scroll=ft.ScrollMode.ALWAYS, expand=True)
    month_lbl = ft.Text(
        f"{calendar.month_name[app_state['calendar_month']]} {app_state['calendar_year']}",
        weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.CYAN_300
    )

    app_state["_calendar_container"] = cal_container
    app_state["_events_container"] = events_container
    app_state["_month_label"] = month_lbl

    top_bar = ft.Row([
        ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=ft.Colors.CYAN_300,
            tooltip="Return to Menu",
            on_click=lambda _: set_tab(None)
        ),
        ft.Text(
            "Medication Calendar",
            size=20, weight=ft.FontWeight.BOLD,
            expand=True, text_align=ft.TextAlign.CENTER,
            color=ft.Colors.CYAN_300
        ),
        ft.Container(width=48)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    _build_calendar_and_events(page, app_state)

    # Contenedor raíz scrollable si la ventana es pequeña
    return ft.Column(
        controls=[
            top_bar,
            ft.Divider(height=1),
            ft.Row([input_box, schedule_btn], spacing=10),
            ft.Divider(),
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_LEFT, on_click=lambda e: _change_month(page, app_state, -1)),
                month_lbl,
                ft.IconButton(ft.Icons.ARROW_RIGHT, on_click=lambda e: _change_month(page, app_state, 1))
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(content=cal_container, height=300),
            ft.Divider(),
            ft.Text(
                "Doses for the selected day:",
                weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200
            ),
            ft.Container(
                content=events_container,
                height=150, padding=10,
                bgcolor=ft.Colors.BLUE_GREY_800, border_radius=8
            ),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )
