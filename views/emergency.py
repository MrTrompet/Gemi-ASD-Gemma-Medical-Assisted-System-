# views/emergency.py
import asyncio
from pathlib import Path

import flet as ft
from text_utils import clean_emoji_text
from utils import run_gemma_emergency_async, save_user_data
import os

# ─── Carpeta de datos en APPDATA ────────────────────────────────
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── JSON de perfil en APPDATA ──────────────────────────────────
PROFILE_PATH = APPDATA_DIR / "gemi_user_data.json"

def build_emergency_tab(page: ft.Page, app_state: dict, on_back) -> ft.Container:
    # ─── 1. BACK BUTTON ────────────────────────────────────────────────────
    back_btn = ft.IconButton(
        icon=ft.Icons.ARROW_BACK,
        icon_color=ft.Colors.CYAN_300,
        tooltip="Back",
        on_click=lambda e: on_back(None),
    )

    # ─── 2. SÍNTOMAS ────────────────────────────────────────────────────────
    gender = app_state.get("gender")
    common = [
        {"key": "face", "label": "Sudden facial droop"},
        {"key": "arm", "label": "Arm weakness"},
        {"key": "speech", "label": "Slurred or incoherent speech"},
        {"key": "vomit", "label": "Vomiting or nausea"},
        {"key": "headache", "label": "Extreme headache"},
        {"key": "dizzy", "label": "Dizziness / Loss of balance"},
    ]
    female_extra = [
        {"key": "nausea", "label": "Sudden nausea"},
        {"key": "confusion", "label": "Sudden confusion"},
    ]
    symptoms_meta = common + (female_extra if gender == "Women" else [])
    app_state.setdefault("symptoms", {item["key"]: False for item in symptoms_meta})

    switch_refs: dict[str, ft.Switch] = {}

    def toggle_symptom(e: ft.ControlEvent, key: str):
        app_state["symptoms"][key] = e.control.value
        analyze_btn.disabled = not any(app_state["symptoms"].values())
        page.update()

    LABEL_WIDTH = 260
    ROW_WIDTH = LABEL_WIDTH + 80
    rows: list[ft.Row] = []
    for item in symptoms_meta:
        key, label = item["key"], item["label"]
        sw = ft.Switch(
            value=app_state["symptoms"][key],
            on_change=lambda e, k=key: toggle_symptom(e, k),
            thumb_color=ft.Colors.CYAN_500,
            track_color=ft.Colors.BLUE_GREY_700,
        )
        switch_refs[key] = sw
        label_box = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_OUTLINED, size=16, color=ft.Colors.CYAN_300),
                    ft.Text(label, color=ft.Colors.WHITE),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START
            ),
            width=LABEL_WIDTH,
            alignment=ft.alignment.center_left
        )
        rows.append(
            ft.Row(
                [label_box, sw],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=ROW_WIDTH,
            )
        )

    symptoms_container = ft.Column(
        rows,
        spacing=20,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    # ─── 3. SPINNER + LOGS ─────────────────────────────────────────────────
    loading_spinner = ft.ProgressRing(width=50, height=50, visible=False)
    log_text = ft.Text("", color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
    loading_box = ft.Column(
        [loading_spinner, log_text],
        spacing=20,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        visible=False,
        expand=True,
    )

    # ─── 4. BOTÓN “ANALIZAR” ───────────────────────────────────────────────
    analyze_btn = ft.FilledButton(
        "Analyze symptoms",
        bgcolor=ft.Colors.CYAN_300,
        color=ft.Colors.BLACK,
        disabled=True,
    )

    # ─── 5. HANDLERS AUXILIARES ────────────────────────────────────────────
    def reset_symptoms():
        for k, sw in switch_refs.items():
            sw.value = False
            app_state["symptoms"][k] = False
        analyze_btn.disabled = True

    def hide_result(e=None):
        result_panel.visible = False
        loading_box.visible = False
        reset_symptoms()
        symptoms_container.visible = True
        analyze_btn.visible = True
        page.update()

    async def on_copy_report(e):
        page.set_clipboard(risk_msg_md.value)
        copy_btn.icon = ft.Icons.CHECK
        page.snack_bar = ft.SnackBar(ft.Text("Report copied to clipboard"), open=True)
        page.update()
        await asyncio.sleep(3)
        copy_btn.icon = ft.Icons.COPY_ALL_OUTLINED
        if copy_btn.page:
            page.update()

    # ─── 6. PANEL DE RESULTADO (CON TAMAÑO FIJO y SCROLL) ────────────────
    risk_label = ft.Text("", size=20, weight=ft.FontWeight.BOLD)
    risk_msg_md = ft.Markdown(
        "",
        extension_set=ft.MarkdownExtensionSet.COMMON_MARK,
        selectable=True,
    )
    # Contenedor scrollable con altura fija
    msg_scroller = ft.Container(
        content=ft.Column(
            [risk_msg_md],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        ),
        width=500,   # ancho fijo
        height=260,  # altura fija para scroll
    )

    copy_btn = ft.IconButton(
        icon=ft.Icons.COPY_ALL_OUTLINED,
        tooltip="Copy report",
        icon_color=ft.Colors.CYAN_200,
        icon_size=15,
        on_click=on_copy_report,
    )
    
    ok_btn = ft.FilledButton(
        "OK", 
        bgcolor=ft.Colors.CYAN_500, 
        color=ft.Colors.BLACK,
        on_click=hide_result
    )

    result_panel = ft.Container(
        visible=False,
        padding=20,
        bgcolor=ft.Colors.BLUE_GREY_800,
        border_radius=12,
        width=500,    # ancho fijo (incluye padding)
        height=400,   # altura fija (incluye padding)
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Column(
            [
                risk_label,
                msg_scroller,
                ft.Row(
                    [copy_btn, ok_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
        ),
    )

    # ─── 7. LÓGICA DE ANÁLISIS ─────────────────────────────────────────────
    async def analyze(e: ft.ControlEvent):
        payload = {
            "profile": {
                "gender": gender,
                "age": app_state.get("age", 0),
            },
            "background": app_state.get("background", []),
            "symptoms": [
                k for k, v in app_state["symptoms"].items() if v
            ],
        }
        save_user_data(payload, PROFILE_PATH)

        symptoms_container.visible = False
        analyze_btn.visible = False
        loading_box.visible = True
        loading_spinner.visible = True
        page.update()

        for msg in [
            "Analyzing background…",
            "Analyzing age and gender…",
            "Analyzing symptoms…",
            "Processing current symptoms…",
            "Generating risk level…",
            "Generating risk message…",
            "Preparing final report…",
            "Generating final report…"
        ]:
            log_text.value = msg
            page.update()
            await asyncio.sleep(25)

        res = await run_gemma_emergency_async(payload)

        loading_box.visible = False
        result_panel.visible = True
        level = res.get("level", "yellow")
        message = clean_emoji_text(res.get("message", ""))
        risk_label.value = f"ALERT {level.upper()}"
        risk_label.color = {
            "green": ft.Colors.GREEN_400,
            "yellow": ft.Colors.AMBER_400,
            "red": ft.Colors.RED_400
        }[level]
        risk_msg_md.value = message
        page.update()
        
    analyze_btn.on_click = analyze

    # ─── 8. LAYOUT FINAL ───────────────────────────────────────────────────
    return ft.Column(
        expand=True,
        controls=[
            ft.Row([back_btn], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        symptoms_container,
                        analyze_btn,
                        loading_box,
                        result_panel,
                    ],
                    spacing=30,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
            ),
        ],
    )
