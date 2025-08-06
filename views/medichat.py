#medichat
import typing
import re
from pathlib import Path
import threading

import pyttsx3
import flet as ft

from text_utils import clean_emoji_text
from utils import run_gemma_medichat_async, save_chat_data
from llm.prompt_builder import build_chat_prompt  # prompt centralizado

# Se añade 'set_tab' para poder usarlo en el botón de volver
def build_medichat_tab(page: ft.Page, app_state: dict, set_tab: typing.Callable) -> ft.Container:
    page.title = "Gemi ASD – Medical Assistant"
    app_state.setdefault("chat_messages", [])

    def max_bubble_w() -> float:
        w = getattr(page, "window_width", None) or page.width or 800
        return min(600, w * 0.75)

    _TOK = re.compile(r"(\*\*|\*|__|_|~~|```)")
    _CODE = re.compile(r"`[^`]+`")
    _LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")

    def strip_md(text: str) -> str:
        text = _LINK.sub(r"\1", text)
        text = _CODE.sub("", text)
        return _TOK.sub("", text)

    def render_message(msg: dict) -> ft.Row:
        is_user = msg["role"] == "user"
        action_buttons: list[ft.Control] = []

        # Botón Copiar
        copy_btn = ft.IconButton(
            icon=ft.Icons.COPY_ALL_OUTLINED,
            icon_size=16,
            tooltip="Copy message",
            icon_color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            style=ft.ButtonStyle(padding=ft.padding.only(left=4, right=0)),
        )
        def on_copy(e=None):
            page.set_clipboard(msg["content"])
            copy_btn.icon = ft.Icons.CHECK
            page.update()
            async def revert_async():
                copy_btn.icon = ft.Icons.COPY_ALL_OUTLINED
                page.update()
            threading.Timer(3, lambda: page.run_task(revert_async)).start()
        copy_btn.on_click = on_copy
        action_buttons.append(copy_btn) 

        if not is_user:
            # Botón TTS
            play_btn = ft.IconButton(
                icon=ft.Icons.VOLUME_UP,
                icon_size=18,
                tooltip="Listen",
                icon_color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                style=ft.ButtonStyle(padding=ft.padding.only(left=0, right=4)),
            )
            play_btn.tts_engine = None

            def on_stop(e=None):
                if play_btn.tts_engine:
                    play_btn.tts_engine.stop()

            def on_play(e=None):
                play_btn.icon = ft.Icons.STOP
                play_btn.tooltip = "Stop"
                play_btn.on_click = on_stop
                page.update()

                def run_tts():
                    engine = pyttsx3.init()
                    play_btn.tts_engine = engine
                    engine.setProperty("rate", 175)
                    engine.setProperty("volume", 1.0)
                    text = strip_md(msg["content"])
                    engine.say(text)
                    engine.runAndWait()

                    async def restore_async():
                        play_btn.icon = ft.Icons.VOLUME_UP
                        play_btn.tooltip = "Listen"
                        play_btn.on_click = on_play
                        play_btn.tts_engine = None
                        page.update()

                    page.run_task(restore_async)

                threading.Thread(target=run_tts, daemon=True).start()

            play_btn.on_click = on_play
            action_buttons.insert(0, play_btn)

        buttons_row = ft.Row(
            controls=action_buttons,
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
        )

        bubble = ft.Container(
            content=ft.Column(
                [
                    ft.Markdown(
                        msg["content"],
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.COMMON_MARK,
                        code_theme="atom-one-dark",
                    ),
                    buttons_row,
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor=ft.Colors.CYAN_300 if is_user else ft.Colors.BLUE_GREY_700,
            padding=12,
            border_radius=12,
            width=None if is_user else max_bubble_w(),
        )

        return ft.Row(
            [bubble],
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
        )

    # ListView de mensajes
    lv = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
    for m in app_state["chat_messages"]:
        lv.controls.append(render_message(m))

    # --- Manejo de envío con prompt centralizado ---
    async def handle_send(e: ft.ControlEvent | None = None):
        raw = input_field.value.strip()
        if not raw:
            return
        current_input = raw
        input_field.value = ""
        page.update()

        # Mostrar user
        usr_msg = {"role": "user", "content": clean_emoji_text(current_input)}
        app_state["chat_messages"].append(usr_msg)
        lv.controls.append(render_message(usr_msg))
        page.update()

        # Indicador "escribiendo"
        typing = ft.Row(
            [ft.Container(
                ft.ProgressRing(width=16, height=16, stroke_width=2),
                bgcolor=ft.Colors.BLUE_GREY_700,
                width=40, height=32,
                border_radius=16,
                alignment=ft.alignment.center,
            )],
            alignment=ft.MainAxisAlignment.START,
        )
        lv.controls.append(typing)
        page.update()

        # Construir prompt y llamar al LLM local
        history, _ = build_chat_prompt(current_input)
        try:
            bot_reply = await run_gemma_medichat_async(history)
        except Exception as ex:
            print("Error Gemi:", ex)
            bot_reply = "I'm sorry, I can't respond at this moment."

        # Mostrar assistant
        lv.controls.remove(typing)
        bot_msg = {"role": "assistant", "content": clean_emoji_text(bot_reply)}
        app_state["chat_messages"].append(bot_msg)
        lv.controls.append(render_message(bot_msg))
        page.update()

        # Persistir solo user+assistant en chat_data.json
        save_chat_data(
            app_state["chat_messages"],
            Path(__file__).parent.parent / "data" / "chat_data.json",
        )

    # Input y botón de enviar
    input_field = ft.TextField(
        expand=True, multiline=True, max_lines=4, filled=True,
        bgcolor=ft.Colors.BLUE_GREY_800, color=ft.Colors.WHITE,
        border_radius=20, on_submit=handle_send,
        # --- MODIFICACIÓN: Placeholder con opacidad ---
        hint_text="Ask Gemi...",
        hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE))
    )
    send_btn = ft.IconButton(
        icon=ft.Icons.SEND, icon_color=ft.Colors.CYAN_300,
        on_click=lambda e: page.run_task(handle_send),
        tooltip="Send message"
    )

    # Enter sin Shift = enviar
    focus_flag = {"val": False}
    input_field.on_focus = lambda e: focus_flag.update(val=(e.data or "").lower() == "true")
    def key_handler(e: ft.KeyboardEvent):
        if e.key == "Enter" and not getattr(e, "shift", False) and focus_flag["val"]:
            page.run_task(handle_send)
            e.prevent_default = True
    page.on_keyboard_event = key_handler

    # Resize handler
    def on_resize(e):
        new_w = max_bubble_w()
        for row in lv.controls:
            if isinstance(row, ft.Row) and row.controls and row.alignment == ft.MainAxisAlignment.START:
                bubble = row.controls[0]
                if isinstance(bubble, ft.Container):
                    bubble.width = new_w
        page.update()
    page.on_resize = on_resize

    # --- NUEVO: Barra superior con botón de volver y título centrado ---
    top_bar = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                tooltip="Return to Menu",
                icon_color=ft.Colors.CYAN_300,
                on_click=lambda _: set_tab(None)
            ),
            ft.Text(
                "Medichat", 
                size=20, 
                weight=ft.FontWeight.BOLD, 
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.CYAN_300,
                expand=True
            ),
            # Contenedor vacío para balancear el botón y centrar el título
            ft.Container(width=48)
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    # --- MODIFICACIÓN: Estructura final de la Columna ---
    return ft.Column(
        controls=[
            top_bar,
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, "white")),
            lv, 
            ft.Row([input_field, send_btn], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START)
        ],
        expand=True, 
    )  