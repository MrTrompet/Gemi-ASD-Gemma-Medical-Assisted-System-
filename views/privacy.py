import flet as ft

def build_privacy_view(page: ft.Page) -> ft.View:
    """Privacy notice screen within a centered box."""
    message = (
        "This application is designed with your privacy at its core. "
        "It operates entirely offline, leveraging the advanced capabilities of the "
        "Gemma3n model directly on your device. This means your sensitive "
        "medical history and personal data are never uploaded to the cloud, "
        "external servers, or shared with any third parties. "
        "All your information remains securely stored on your personal computer, "
        "giving you complete control and peace of mind regarding your health data."
    )
    # Caja tipo diálogo centrada
    dialog_box = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    message,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                    size=16,
                ),
                ft.FilledButton(
                    text="Agree",
                    on_click=lambda e: page.go("/session"),
                    bgcolor=ft.Colors.CYAN_500,
                    color=ft.Colors.BLACK,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        width=400,
        padding=ft.padding.all(24),
        bgcolor=ft.Colors.BLUE_GREY_800,
        border_radius=12,
    )
    # Lo centramos en la pantalla
    container = ft.Container(
        content=dialog_box,
        expand=True,
        alignment=ft.alignment.center,
    )
    return ft.View(
        route="/privacy",
        controls=[container],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
