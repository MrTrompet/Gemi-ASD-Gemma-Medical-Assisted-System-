# emergency_button.py

import flet as ft

def build_emergency_view(page: ft.Page) -> ft.View:
    # Handler para volver a la vista anterior
    def go_back(e):
        page.views.pop()
        page.update()

    # Handlers de ejemplo para Telegram/WhatsApp
    def on_telegram(e):
        # Aquí puedes llamar a tu lógica de integración con Telegram
        print("Conectando con Telegram…")

    def on_whatsapp(e):
        # Aquí puedes llamar a tu lógica de integración con WhatsApp
        print("Conectando con WhatsApp…")

    return ft.View(
        route="/emergency",
        appbar=ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=go_back),
            title=ft.Text("Emergencia", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_800
        ),
        bgcolor=ft.Colors.BLUE_GREY_900,
        controls=[
            ft.Column(
                [
                    ft.Text("¿Cómo deseas notificar la emergencia?", color=ft.Colors.WHITE, size=20),
                    ft.ElevatedButton(
                        "Conectar con Telegram",
                        icon=ft.icons.TELEGRAM,
                        on_click=on_telegram,
                        bgcolor=ft.Colors.CYAN_300
                    ),
                    ft.ElevatedButton(
                        "Conectar con WhatsApp",
                        icon=ft.icons.WHATSAPP,
                        on_click=on_whatsapp,
                        bgcolor=ft.Colors.CYAN_300
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            )
        ]
    )

def trigger_emergency(page: ft.Page):
    # Empuja la vista de emergencia en la pila de vistas
    page.views.append(build_emergency_view(page))
    page.update()
