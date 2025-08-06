#profile.py
import flet as ft
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from functools import partial



from utils import (
    load_profile_data,
    save_profile_data,
    save_profile_photo,
)

# ——— Boilterplate APPDATA ———
APPDATA_DIR = Path(
    os.getenv("APPDATA", Path.home()/ "AppData"/"Roaming")
) / "GemiASD"
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

PDF_DIR = APPDATA_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

DEBUG_PDF = True  # si quieres ver detalles de error

def trim_memory_windows():
    if os.name == "nt":
        import ctypes
        try:
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
        except Exception:
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
            
# Carpeta destino de los PDFs
PDF_DIR = APPDATA_DIR

def build_profile_view(page: ft.Page, app_state: dict) -> ft.View:
    profile = load_profile_data()
    anc = app_state.get("background")
    if isinstance(anc, list):
        # Convertimos la lista en { item: True }
        app_state["background"] = {item: True for item in anc}
    
    datos_basicos = [
        profile.get("first_name"),   # "Christian"
        profile.get("last_name"),    # "Montenegro"
        profile.get("location"),     # "Cabudare"
        profile.get("description"),  # "Me gusta fumar"
        profile.get("pronouns"),     # "He/him"
    ]
    primera_vez = not any(datos_basicos)   # ← True solo si TODOS vacíos

    # ------------------------------------------------------------------
    # 2) Flags de edición
    # ------------------------------------------------------------------
    if "profile_edit" not in app_state:
        # Solo se define la primera vez que abres la vista en esta sesión
        app_state["profile_edit"] = primera_vez
    # Los demás flags no cambian
    app_state.setdefault("emergency_edit", False)
    app_state.setdefault("allergies_edit", False)
    app_state.setdefault("blood_type_edit", False)

    # ---- Estados de edición ----
    app_state.setdefault("profile_edit", True)
    app_state.setdefault("emergency_edit", False)
    app_state.setdefault("allergies_edit", False)
    app_state.setdefault("blood_type_edit", False)

    # ---- Campos del perfil ----
    profile.setdefault("first_name", "")
    profile.setdefault("last_name", "")
    profile.setdefault("pronouns", "")
    profile.setdefault("location", "")
    profile.setdefault("description", "")
    profile.setdefault("profile_photo", None)
    profile.setdefault("emergency_contacts", ["", "", ""])
    profile.setdefault("allergies", ["", "", ""])
    profile.setdefault("blood_type", "")
    profile.setdefault("studies", [])

    # =====================================================================
    #                              HELPERS
    # =====================================================================

    def _build_avatar(path: str | None) -> ft.Control:
        outer = ft.Container(width=128, height=128, padding=4, border_radius=64, bgcolor=ft.Colors.CYAN_300)
        if path:
            outer.content = ft.Container(
                content=ft.Image(src=path, fit=ft.ImageFit.COVER),
                width=120, height=120, border_radius=60, clip_behavior=ft.ClipBehavior.HARD_EDGE
            )
        else:
            outer.content = ft.Container(
                width=120, height=120, border_radius=60, bgcolor=ft.Colors.BLUE_GREY_700,
                alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ADD_A_PHOTO, size=32, color=ft.Colors.CYAN_300),
                        ft.Text("Add\nphoto", size=12, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                    ],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        return outer

    def _spinner_dialog(text: str) -> ft.AlertDialog:
        dlg = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [ft.Text(text, color=ft.Colors.WHITE), ft.ProgressRing()],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
        )
        page.dialog = dlg
        dlg.open = True
        page.update()
        return dlg

    # =====================================================================
    #                            AVATAR / FOTO
    # =====================================================================

    def _on_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        dlg = _spinner_dialog("Loading photo...")
        src = e.files[0].path
        dest = save_profile_photo(src)
        profile["profile_photo"] = dest
        save_profile_data(profile)
        avatar_control.content = _build_avatar(dest)
        dlg.open = False
        page.update()

    file_picker = ft.FilePicker(on_result=_on_file_result)

    avatar_control = ft.GestureDetector(
        content=_build_avatar(profile.get("profile_photo")),
        on_tap=lambda e: file_picker.pick_files(allow_multiple=False),
    )

    # =====================================================================
    #                           SUBIR PDFs (sin hilos)
    # =====================================================================

    class CopyJob:
        def __init__(self, src: str, dst: str):
            self.src = src
            self.dst = dst
            self.pb = ft.ProgressBar(width=240, value=0)
            self.tx = ft.Text("0%", size=12, color=ft.Colors.WHITE)

    def _on_study_file(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        os.makedirs(PDF_DIR, exist_ok=True)

        # Dialogo con barras
        jobs_col = ft.Column(spacing=8, tight=True)
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Uploading documents...", color=ft.Colors.WHITE),
            content=jobs_col,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

        jobs: list[CopyJob] = []
        for f in e.files:
            src = f.path
            dst = os.path.join(PDF_DIR, os.path.basename(src))
            job = CopyJob(src, dst)
            jobs.append(job)
            jobs_col.controls.append(
                ft.Row(
                    [
                        ft.Text(os.path.basename(src), color=ft.Colors.WHITE, expand=True, size=12),
                        job.pb,
                        job.tx,
                    ],
                    spacing=6,
                )
            )
        page.update()

        # Copiar secuencialmente con progreso
        chunk = 1024 * 1024  # 1 MB
        new_paths = []

        for job in jobs:
            try:
                total = os.path.getsize(job.src)
                copied = 0
                with open(job.src, "rb") as fsrc, open(job.dst, "wb") as fdst:
                    while True:
                        data = fsrc.read(chunk)
                        if not data:
                            break
                        fdst.write(data)
                        copied += len(data)
                        val = copied / total if total else 1
                        job.pb.value = val
                        job.tx.value = f"{int(val*100)}%"
                        page.update()
                new_paths.append(job.dst)
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error copying {os.path.basename(job.src)}: {ex}"))
                page.snack_bar.open = True
                page.update()

        # Guardar, cerrar y refrescar
        profile["studies"].extend(new_paths)
        save_profile_data(profile)

        dlg.open = False
        page.update()

        update_studies_section()
        trim_memory_windows()
        if new_paths:
            open_pdf(new_paths[0])

    study_picker = ft.FilePicker(on_result=_on_study_file)
    page.overlay.extend([file_picker, study_picker])

    # =====================================================================
    #                      CAMPOS DEL PERFIL (handlers)
    # =====================================================================

    def on_fn(e): profile["first_name"] = e.control.value
    def on_ln(e): profile["last_name"] = e.control.value
    def on_pronouns(e):
        v = e.control.value
        profile["pronouns"] = "" if v == "Prefiero no decirlo" else v
    def on_location(e): profile["location"] = e.control.value
    def on_description(e): profile["description"] = e.control.value

    def on_save(e):
        app_state["profile_edit"] = False
        save_profile_data(profile)
        update_view()

    def on_edit(e):
        app_state["profile_edit"] = True
        update_view()

    # =====================================================================
    #                           APP BAR
    # =====================================================================

    app_bar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/main")),
        title=ft.Text("Perfil", color=ft.Colors.CYAN_300),
        bgcolor=ft.Colors.BLUE_GREY_900,
    )

    # =====================================================================
    #                        CONTROLES DE TEXTO
    # =====================================================================

    name_field = ft.TextField(
        hint_text="Name", value=profile.get("first_name", ""),
        on_change=on_fn, color=ft.Colors.WHITE,
        border_color=ft.Colors.CYAN_300, expand=True,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )
    last_field = ft.TextField(
        hint_text="Last Name", value=profile.get("last_name", ""),
        on_change=on_ln, color=ft.Colors.WHITE,
        border_color=ft.Colors.CYAN_300, expand=True,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )
    pronouns_field = ft.Dropdown(
        hint_text="Pronouns",
        options=[ft.dropdown.Option(x) for x in ["He/him", "She/her", "They/them", "Prefiero no decirlo"]],
        value=profile.get("pronouns") or None,
        on_change=on_pronouns,
        border_color=ft.Colors.CYAN_300,
        color=ft.Colors.WHITE,
        width=200,
    )
    location_field = ft.TextField(
        hint_text="Location", value=profile.get("location", ""),
        on_change=on_location, color=ft.Colors.WHITE,
        border_color=ft.Colors.CYAN_300, expand=True,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )
    description_field = ft.TextField(
        hint_text="Description: write a brief description...",
        value=profile.get("description", ""),
        on_change=on_description,
        color=ft.Colors.WHITE, border_color=ft.Colors.CYAN_300,
        expand=True, content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
        multiline=True,
    )

    name_section_container = ft.Container(expand=True, alignment=ft.alignment.center)

    # =====================================================================
    #                           ESTUDIOS (PDF)
    # =====================================================================
    studies_container = ft.Column(spacing=4, tight=True)

    from pathlib import Path
    import tempfile


    def open_pdf(path: str):
        print("open_pdf called with:", path)

        if not os.path.exists(path):
            page.snack_bar = ft.SnackBar(ft.Text("File not found"))
            page.snack_bar.open = True
            page.update()
            return

        # Usa pythonw si existe (así no hay consola negra)
        py = Path(sys.executable)
        if os.name == "nt" and py.name.lower() == "python.exe":
            pyw = py.with_name("pythonw.exe")
            if pyw.exists():
                py = pyw

        cmd = [str(py), "-m", "views.pdf_viewer_proc", path]

        # No mostrar consola (cuando no estamos debuggeando)
        flags = 0
        if os.name == "nt" and not DEBUG_PDF:
            flags = subprocess.CREATE_NO_WINDOW

        if DEBUG_PDF:
            log_file = Path(tempfile.gettempdir()) / "gemi_pdf_viewer.log"
            fh = open(log_file, "w", encoding="utf-8")
            subprocess.Popen(
                cmd,
                cwd=str(PDF_DIR),
                stdout=fh,
                stderr=fh,
                close_fds=True,
                creationflags=flags
            )
            page.snack_bar = ft.SnackBar(ft.Text(f"Viewer launched. Check log: {log_file}"))
            page.snack_bar.open = True
            page.update()
        else:
            subprocess.Popen(
                cmd,
                cwd=str(PDF_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=flags
            )

    def update_studies_section():
        rows = [
            ft.Row([
                ft.Text("Studies", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.IconButton(
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda e: study_picker.pick_files(allow_multiple=True, allowed_extensions=["pdf"]),
                    icon_color=ft.Colors.CYAN_300,
                ),
            ])
        ]
        for p in profile.get("studies", []):
            rows.append(
                ft.Row([
                    ft.Text(os.path.basename(p), color=ft.Colors.WHITE, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        on_click=lambda e, ruta=p: open_pdf(ruta),
                        icon_color=ft.Colors.CYAN_300,
                    ),
                ])
            )
        studies_container.controls = rows
        page.update()
        
    # =====================================================================
    #        EMERGENCIA / ALERGIAS / SANGRE (igual que tu versión)
    # =====================================================================

    def on_emergency_change(e, index): profile["emergency_contacts"][index] = e.control.value
    def on_edit_emergency(e): app_state["emergency_edit"] = True; update_view()
    def on_save_emergency(e): app_state["emergency_edit"] = False; update_view()

    emergency_fields = [
        ft.TextField(
            hint_text=f"Contact {i+1}",
            value=profile["emergency_contacts"][i],
            on_change=partial(on_emergency_change, index=i),
            color=ft.Colors.WHITE, border_color=ft.Colors.CYAN_300,
            content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
        ) for i in range(3)
    ]
    emergency_container = ft.Column(spacing=4, tight=True)

    def update_emergency_section():
        if app_state["emergency_edit"]:
            emergency_container.controls = [
                ft.Text("Edit Emergency Contacts", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                *emergency_fields,
                ft.FilledButton("Save", on_click=on_save_emergency,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_300, color=ft.Colors.BLACK))
            ]
        else:
            contacts_text = ", ".join(c for c in profile["emergency_contacts"] if c) or "Unspecified"
            emergency_container.controls = [
                ft.Row([
                    ft.Icon(ft.Icons.CONTACT_EMERGENCY, size=18, color=ft.Colors.CYAN_300),
                    ft.Text(f"Emergency Contacts: {contacts_text}", color=ft.Colors.WHITE, expand=True),
                    ft.IconButton(icon=ft.Icons.EDIT, on_click=on_edit_emergency, icon_color=ft.Colors.CYAN_300)
                ], spacing=8)
            ]

    def on_allergy_change(e, index): profile["allergies"][index] = e.control.value
    def on_edit_allergies(e): app_state["allergies_edit"] = True; update_view()
    def on_save_allergies(e): app_state["allergies_edit"] = False; update_view()

    allergy_fields = [
        ft.TextField(
            hint_text=f"Allergy {i+1}",
            value=profile["allergies"][i],
            on_change=partial(on_allergy_change, index=i),
            color=ft.Colors.WHITE, border_color=ft.Colors.CYAN_300,
            content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
        ) for i in range(3)
    ]
    allergies_container = ft.Column(spacing=4, tight=True)

    def update_allergies_section():
        if app_state["allergies_edit"]:
            allergies_container.controls = [
                ft.Text("Edit Known Allergies", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                *allergy_fields,
                ft.FilledButton("Save", on_click=on_save_allergies,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_300, color=ft.Colors.BLACK))
            ]
        else:
            allergies_text = ", ".join(a for a in profile["allergies"] if a) or "None known"
            allergies_container.controls = [
                ft.Row([
                    ft.Icon(ft.Icons.MEDICAL_SERVICES_OUTLINED, size=18, color=ft.Colors.CYAN_300),
                    ft.Text(f"Known Allergies: {allergies_text}", color=ft.Colors.WHITE, expand=True),
                    ft.IconButton(icon=ft.Icons.EDIT, on_click=on_edit_allergies, icon_color=ft.Colors.CYAN_300)
                ], spacing=8)
            ]

    def on_blood_type_change(e): profile["blood_type"] = e.control.value
    def on_edit_blood_type(e): app_state["blood_type_edit"] = True; update_view()
    def on_save_blood_type(e): app_state["blood_type_edit"] = False; update_view()

    blood_type_field = ft.TextField(
        hint_text="E.g: O+",
        value=profile["blood_type"],
        on_change=on_blood_type_change,
        color=ft.Colors.WHITE, border_color=ft.Colors.CYAN_300,
        content_padding=ft.padding.symmetric(vertical=4, horizontal=8),
    )
    blood_type_container = ft.Column(spacing=4, tight=True)

    def update_blood_type_section():
        if app_state["blood_type_edit"]:
            blood_type_container.controls = [
                ft.Text("Edit Blood Type", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                blood_type_field,
                ft.FilledButton("Save", on_click=on_save_blood_type,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_300, color=ft.Colors.BLACK))
            ]
        else:
            blood_text = profile["blood_type"] or "Unspecified"
            blood_type_container.controls = [
                ft.Row([
                    ft.Icon(ft.Icons.BLOODTYPE, size=18, color=ft.Colors.CYAN_300),
                    ft.Text(f"Blood type: {blood_text}", color=ft.Colors.WHITE, expand=True),
                    ft.IconButton(icon=ft.Icons.EDIT, on_click=on_edit_blood_type, icon_color=ft.Colors.CYAN_300)
                ], spacing=8)
            ]

    # =====================================================================
    #                     REGISTRO MEDICACIÓN (placeholder)
    # =====================================================================

    med_log = ft.Column(
        [
            ft.Text("Medication Log", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Container(
                expand=True, height=150,
                border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
                border_radius=8,
                alignment=ft.alignment.center,
                content=ft.Text("Here the medication schedule will go", color=ft.Colors.BLUE_GREY_500)
            ),
        ],
        spacing=10
    )

    # =====================================================================
    #                               INFO FIJA
    # =====================================================================

    info_controls = [
        ft.Divider(color=ft.Colors.BLUE_GREY_700),
        ft.Row([ft.Icon(ft.Icons.CAKE, size=18, color=ft.Colors.CYAN_300),
                ft.Text(f"Age: {app_state.get('age','?')}", color=ft.Colors.WHITE)], spacing=8),
        ft.Row([ft.Icon(ft.Icons.MALE if app_state.get("gender","")=="Man" else ft.Icons.FEMALE,
                        size=18, color=ft.Colors.CYAN_300),
                ft.Text(f"Gender: {app_state.get('gender','?')}", color=ft.Colors.WHITE)], spacing=8),
        ft.Row([ft.Icon(ft.Icons.HISTORY, size=18, color=ft.Colors.CYAN_300),
                ft.Text(f"Background: {', '.join(app_state.get('background',{}).keys()) or 'None'}",
                        color=ft.Colors.WHITE, expand=True)], spacing=8)
    ]

    # =====================================================================
    #                           UPDATE VIEW
    # =====================================================================

    def update_view():
        if app_state["profile_edit"]:
            name_section_container.content = ft.Column(
                [
                    name_field, last_field, pronouns_field, location_field, description_field,
                    ft.FilledButton("Save",
                                    on_click=on_save,
                                    style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_300, color=ft.Colors.BLACK),
                                    width=120, height=40)
                ],
                spacing=15, alignment=ft.MainAxisAlignment.CENTER
            )
            for c in [name_field, last_field, pronouns_field, location_field, description_field]:
                c.disabled = False
        else:
            full_name = f"{profile.get('first_name','')} {profile.get('last_name','')}".strip() or "First Name Last Name"
            bio_lines = []
            if profile.get("pronouns"):
                bio_lines.append(f"Pronouns: {profile['pronouns']}")
            if profile.get("location"):
                bio_lines.append(f"Location: {profile['location']}")
            if profile.get("description"):
                bio_lines.append(profile["description"])
            name_section_container.content = ft.Column(
                [ft.Row([
                    ft.Text(full_name, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.IconButton(icon=ft.Icons.EDIT, on_click=on_edit, icon_color=ft.Colors.CYAN_300)
                ])] + [ft.Text(line, color=ft.Colors.WHITE) for line in bio_lines],
                spacing=8
            )
            for c in [name_field, last_field, pronouns_field, location_field, description_field]:
                c.disabled = True

        update_emergency_section()
        update_allergies_section()
        update_blood_type_section()
        update_studies_section()
        save_profile_data(profile)
        page.update()

    # =====================================================================
    #                         BODY / LAYOUT
    # =====================================================================

    body = ft.Container(
        padding=ft.padding.all(20),
        content=ft.Column(
            [
                ft.Row([avatar_control, name_section_container], spacing=20),
                *info_controls,
                ft.Divider(color=ft.Colors.BLUE_GREY_700),
                ft.Text("Emergency Data", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Divider(color=ft.Colors.BLUE_GREY_700),
                emergency_container,
                allergies_container,
                blood_type_container,
                med_log,
                studies_container
            ],
            spacing=12,
        ),
    )

    update_view()

    return ft.View(
        route="/profile",
        appbar=app_bar,
        controls=[body],
        bgcolor=ft.Colors.BLUE_GREY_900,
        scroll=ft.ScrollMode.ADAPTIVE,
    )
