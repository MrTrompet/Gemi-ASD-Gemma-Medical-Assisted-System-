# views/pulsometro.py

import flet as ft
import winsound
import asyncio

def build_pulsometer_tab(page: ft.Page, app_state: dict, set_tab) -> ft.Control:
    """
    Pestaña Pulsómetro:
      • Tutorial a la izquierda
      • Cronómetro de 15s con botón INICIAR/REINICIAR en el centro
      • Teclado numérico a la derecha + display debajo
      • Resultado grande centrado bajo el cronómetro
      • Botón 'Analizar con Gemi' abajo a la derecha
    """
    # ─── Estado inicial ─────────────────────────────────────
    app_state.setdefault("pulse_input", "")
    app_state.setdefault("timer_running", False)

    # ─── Controles ──────────────────────────────────────────
    timer_text    = ft.Text("00:00", size=64, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300)
    input_display = ft.Text("", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    result_text   = ft.Text("", size=20, color=ft.Colors.WHITE)

    # ─── Cronómetro ────────────────────────────────────────
    async def _run_timer():
        for i in range(1, 16):
            if not app_state["timer_running"]:
                return
            timer_text.value = f"00:{i:02d}"
            page.update()
            await asyncio.sleep(1)
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)

    async def _start_or_reset(e: ft.ControlEvent):
        if not app_state["timer_running"]:
            app_state["timer_running"] = True
            timer_text.value = "00:00"
            start_btn.text  = "RESET"
            page.update()
            await _run_timer()
        else:
            app_state["timer_running"] = False
            timer_text.value = "00:00"
            start_btn.text  = "START"
            page.update()

    # ─── Teclado ────────────────────────────────────────────
    def _append_digit(_, d):
        app_state["pulse_input"] += str(d)
        input_display.value       = app_state["pulse_input"]
        page.update()

    def _backspace(_):
        app_state["pulse_input"] = app_state["pulse_input"][:-1]
        input_display.value      = app_state["pulse_input"]
        page.update()

    def _compute_bpm(_):
        s = app_state["pulse_input"]
        if not s.isdigit() or int(s) == 0:
            result_text.value = "🔴 N.º Invalid"
        else:
            bpm = int(s) * 4
            estado = (
                "🔵 Bradycardia" if bpm < 60 else
                "🔴 Tachycardia"  if bpm > 100 else
                "🟢 Normal Rhythm"
            )
            result_text.value = f"{bpm} bpm → {estado}"
        page.update()

    # ─── Tutorial ──────────────────────────────────────────
    tutorial = ft.Container(
        content=ft.Column(
            [
                ft.Text("How to use the Heart Rate Monitor", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300),
                ft.Divider(color=ft.Colors.BLUE_GREY_700),

                ft.Text("🔹 Before you start:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • Make sure you are rested and seated.", color=ft.Colors.WHITE),
                ft.Text("  • Avoid coffee, tea, or stimulants 30 min before.", color=ft.Colors.WHITE),
                ft.Text("  • Sit with your back straight and relax your arm.", color=ft.Colors.WHITE),

                ft.Container(height=8),

                ft.Text("1️⃣ Locate your pulse:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • Use two fingers (index and middle).", color=ft.Colors.WHITE),
                ft.Text("  • On the wrist: just below the base of the thumb.", color=ft.Colors.WHITE),
                ft.Text("  • On the neck: next to the trachea.", color=ft.Colors.WHITE),

                ft.Container(height=8),

                ft.Text("2️⃣ Prepare the stopwatch:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • Press START when you are ready.", color=ft.Colors.WHITE),
                ft.Text("  • Count each beat for 15 seconds.", color=ft.Colors.WHITE),

                ft.Container(height=8),

                ft.Text("3️⃣ Enter your count:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • After the beep, tap the number of beats 😮‍💨.", color=ft.Colors.WHITE),
                ft.Text("  • Use the keyboard to enter each digit.", color=ft.Colors.WHITE),
                ft.Text("  • Review and correct with ⌫ if you make a mistake.", color=ft.Colors.WHITE),

                ft.Container(height=8),

                ft.Text("4️⃣ Calculate your frequency:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • Press OK to multiply by 4 (bpm).", color=ft.Colors.WHITE),
                ft.Text("  • Wait for the result to appear.", color=ft.Colors.WHITE),

                ft.Container(height=8),

                ft.Text("5️⃣ Interpret your rhythm:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • < 60 bpm = Bradycardia (slow)", color=ft.Colors.WHITE),
                ft.Text("  • 60–100 bpm = Normal rhythm", color=ft.Colors.WHITE),
                ft.Text("  • > 100 bpm = Tachycardia (fast)", color=ft.Colors.WHITE),

                ft.Container(height=8),

                ft.Text("ℹ️ Final tips:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Text("  • Repeat the measurement if you notice discrepancies.", color=ft.Colors.WHITE),
                ft.Text("  • Consult a professional for any anomalies.", color=ft.Colors.WHITE),
                ft.Text("  • Use 'Analyze with Gemi' for more guidance.", color=ft.Colors.WHITE),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            expand=True,
        ),
        width=300,
        padding=ft.padding.symmetric(vertical=12, horizontal=14),
        bgcolor=ft.Colors.BLUE_GREY_800,
        border_radius=8,
    )

    # ─── Construir teclado ──────────────────────────────────
    keypad_rows = []
    for row in ((1,2,3),(4,5,6),(7,8,9),("⌫",0,"OK")):
        btns = []
        for c in row:
            if c == "⌫":
                btn = ft.ElevatedButton("⌫", width=60, height=60, on_click=_backspace)
            elif c == "OK":
                btn = ft.ElevatedButton("OK", width=60, height=60, on_click=_compute_bpm)
            else:
                btn = ft.ElevatedButton(str(c), width=60, height=60,
                    on_click=lambda e, d=c: _append_digit(e, d))
            btns.append(btn)
        keypad_rows.append(ft.Row(btns, spacing=8, alignment=ft.MainAxisAlignment.CENTER))
    keypad = ft.Column(keypad_rows, spacing=8)

    # ─── Botón 'Analizar con Gemi' ─────────────────────────
    def _go_analysis(e):
        page.snack_bar = ft.SnackBar(ft.Text("Future analysis function"))
        page.snack_bar.open = True
        page.update()

    heart_btn = ft.IconButton(
        icon=ft.Icons.FAVORITE,
        icon_color=ft.Colors.CYAN_300,
        tooltip="Analyze with Gemi",
        on_click=_go_analysis
    )

    # ─── Botón Volver ──────────────────────────────────────
    back_btn = ft.IconButton(
        ft.Icons.ARROW_BACK,
        icon_color=ft.Colors.CYAN_300,
        on_click=lambda e: set_tab(None)
    )

    # ─── Botón INICIAR / REINICIAR ─────────────────────────
    start_btn = ft.FilledButton(
        "START",
        on_click=_start_or_reset,
        bgcolor=ft.Colors.CYAN_400,
        color=ft.Colors.BLACK,
        width=160
    )

    # ─── Ensamblar layout principal ────────────────────────
    main_view = ft.Column(
        [
            # Encabezado fijo: volver, texto y corazón
            ft.Row(
                [
                    back_btn,
                    ft.Text("Heart Rate Monitor", size=24, color=ft.Colors.CYAN_300),
                    heart_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                height=50
            ),
            ft.Divider(color=ft.Colors.BLUE_GREY_700),

            # Cuerpo: tutorial | centro | teclado + display
            ft.Row(
                [
                    tutorial,  # esta columna tiene su propio scroll
                    ft.Column(
                        [ timer_text, start_btn ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20
                    ),
                    ft.Column(
                        [ keypad, input_display ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12
                    ),
                ],
                spacing=40,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True
            ),

            # ─── Ahora la fila de resultado va por debajo, centrada ───
            ft.Row(
                [
                    result_text
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                expand=False
            ),
        ],
        expand=True,
        # scroll=ft.ScrollMode.AUTO,  <- ¡quítalo de aquí!
        spacing=24
    )

    return ft.Container(
        content=main_view,
        padding=ft.padding.all(16),
        expand=True
    )
