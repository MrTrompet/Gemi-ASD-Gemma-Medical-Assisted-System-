import flet as ft

def build_logo_view(page: ft.Page, logo_data_uri: str) -> ft.View:
    """Pantalla de carga con logo y spinner, centrada vertical y horizontalmente."""
    control = (
        ft.Image(src=logo_data_uri, width=200, height=200)
        if logo_data_uri
        else ft.Icon(ft.Icons.MEDICAL_SERVICES, size=120, color=ft.Colors.CYAN_300)
    )
    loading = ft.Column(
        controls=[
            control,
            ft.ProgressRing(color=ft.Colors.CYAN_300, width=40, height=40),
            ft.Text("Cargando...", color=ft.Colors.CYAN_300),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
    )
    # Este Container expande y centra el contenido
    container = ft.Container(
        content=loading,
        expand=True,
        alignment=ft.alignment.center,
    )
    return ft.View(
        route="/",
        controls=[container],
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
