"""Aplicación local de gestión de residuos."""
from datetime import date
from pathlib import Path
import flet as ft

from database.connection import initialize_database
from repositories.residuos import ResiduoRepository
from services.image_service import copy_image


ROOT_DIR = Path(__file__).resolve().parent
STATES = ["Almacenado", "Recolectado", "Reciclado", "Desechado", "En proceso"]
UNITS = ["piezas", "kg", "g", "litros", "bolsas", "cajas"]
TYPES = ["Reciclable", "No reciclable", "Orgánico", "Peligroso", "Especial"]
NAVY, GREEN, PALE = "#163A32", "#23835C", "#F3F7F4"


class WasteApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.repo = ResiduoRepository()
        self.view_name = "dashboard"
        self.selected_image = ""
        self.search = ft.TextField(hint_text="Buscar por nombre, ubicación o notas", prefix_icon=ft.Icons.SEARCH,
                                   expand=True, dense=True, border_radius=10, on_change=lambda _: self.render_content())
        self.category_filter = ft.Dropdown(label="Categoría", width=180, dense=True, on_select=lambda _: self.render_content())
        self.state_filter = ft.Dropdown(label="Estado", width=160, dense=True, on_select=lambda _: self.render_content())
        # En Flet 1.x los servicios se registran al crearse y sus métodos son asíncronos.
        self.file_picker = ft.FilePicker()

    def setup(self):
        self.page.title = "Gestor de Residuos"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = PALE
        self.page.padding = 0
        self.page.window.min_width = 950
        self.page.window.min_height = 650
        self.page.add(self.layout())
        self.render_content()

    def layout(self):
        self.content = ft.Container(expand=True, padding=28)
        self.title = ft.Text(size=28, weight=ft.FontWeight.BOLD, color=NAVY)
        self.subtitle = ft.Text(color="#62736B")
        self.nav_items = {}
        nav = ft.Column(spacing=5, controls=[
            ft.Text("ECOGESTOR", size=21, weight=ft.FontWeight.BOLD, color="white"),
            ft.Text("Control local de residuos", color="#B7D9C5", size=12),
            ft.Divider(height=32, color="#427564"),
            self.nav_button("dashboard", "Resumen", ft.Icons.DASHBOARD_OUTLINED),
            self.nav_button("residues", "Residuos", ft.Icons.RECYCLING_OUTLINED),
            self.nav_button("categories", "Categorías", ft.Icons.CATEGORY_OUTLINED),
            ft.Container(expand=True),
            ft.Text("Datos almacenados localmente", color="#B7D9C5", size=11),
        ])
        return ft.Row(expand=True, spacing=0, controls=[
            ft.Container(nav, width=225, bgcolor=NAVY, padding=22),
            ft.Column(expand=True, controls=[
                ft.Container(ft.Column([self.title, self.subtitle], spacing=2), padding=ft.Padding.only(left=28, right=28, top=23, bottom=8), bgcolor="white"),
                self.content,
            ])
        ])

    def nav_button(self, key, label, icon):
        button = ft.TextButton(label, icon=icon, style=ft.ButtonStyle(color="white", padding=14),
                               on_click=lambda _, page_name=key: self.go(page_name))
        self.nav_items[key] = button
        return button

    def go(self, name):
        self.view_name = name
        self.render_content()

    def render_content(self):
        labels = {"dashboard": ("Resumen", "Vista general de los registros almacenados."),
                  "residues": ("Residuos", "Registra, consulta y da seguimiento a los residuos."),
                  "categories": ("Categorías", "Clasificaciones disponibles para tus registros.")}
        self.title.value, self.subtitle.value = labels[self.view_name]
        for key, button in self.nav_items.items():
            button.style = ft.ButtonStyle(color="white", bgcolor="#2B6454" if key == self.view_name else None,
                                          padding=14, shape=ft.RoundedRectangleBorder(radius=8))
        if self.view_name == "dashboard":
            self.content.content = self.dashboard()
        elif self.view_name == "residues":
            self.content.content = self.residue_list()
        else:
            self.content.content = self.category_list()
        self.page.update()

    def card(self, title, value, color):
        return ft.Container(expand=True, bgcolor="white", border_radius=14, padding=18,
                            content=ft.Column([ft.Text(title, color="#62736B"), ft.Text(str(value), size=30, weight=ft.FontWeight.BOLD, color=color)]))

    def dashboard(self):
        data = self.repo.summary()
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(item["nombre"])), ft.DataCell(ft.Text(item["categoria"])),
                                  ft.DataCell(ft.Text(self.format_date(item["fecha_registro"])))]) for item in data["recent"]]
        chart_rows = [ft.Row([ft.Text(item["nombre"], width=150), ft.ProgressBar(value=item["total"] / max(data["total"], 1), color=GREEN, bgcolor="#DDEAE3", expand=True), ft.Text(str(item["total"]), width=25)]) for item in data["by_category"]]
        return ft.Column(scroll=ft.ScrollMode.AUTO, spacing=22, controls=[
            ft.Row([self.card("Total de registros", data["total"], GREEN), self.card("Categorías", data["categories"], "#4A6FA5"),
                    self.card("Reciclables", data["recyclable"], "#B27627"), self.card("Peligrosos", data["hazardous"], "#B34A4A")]),
            ft.Row(vertical_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Container(expand=True, bgcolor="white", border_radius=14, padding=20, content=ft.Column([
                    ft.Text("Registros por categoría", size=18, weight=ft.FontWeight.BOLD, color=NAVY),
                    *(chart_rows or [ft.Text("Aún no hay residuos registrados.", color="#62736B")])
                ], spacing=14)),
                ft.Container(expand=True, bgcolor="white", border_radius=14, padding=20, content=ft.Column([
                    ft.Row([ft.Text("Registros recientes", size=18, weight=ft.FontWeight.BOLD, color=NAVY), ft.Container(expand=True),
                            ft.TextButton("Ver todos", on_click=lambda _: self.go("residues"))]),
                    ft.DataTable(columns=[ft.DataColumn(ft.Text("Residuo")), ft.DataColumn(ft.Text("Categoría")), ft.DataColumn(ft.Text("Fecha"))],
                                 rows=rows, heading_row_color="#EAF3ED") if rows else ft.Text("Aún no hay registros.", color="#62736B")
                ]))
            ])
        ])

    def residue_list(self):
        categories = self.repo.categories()
        self.category_filter.options = [ft.DropdownOption("", "Todas")] + [ft.DropdownOption(str(c["id"]), c["nombre"]) for c in categories]
        self.state_filter.options = [ft.DropdownOption("", "Todos")] + [ft.DropdownOption(s) for s in STATES]
        category_id = int(self.category_filter.value) if self.category_filter.value else None
        records = self.repo.residues(self.search.value or "", category_id, self.state_filter.value or None)
        rows = []
        for r in records:
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(r["id"]))), ft.DataCell(ft.Text(r["nombre"])), ft.DataCell(ft.Text(r["categoria"])),
                ft.DataCell(ft.Text(f"{self.format_number(r['cantidad'])} {r['unidad']}")), ft.DataCell(ft.Text(r["estado"])),
                ft.DataCell(ft.Text(self.format_date(r["fecha_registro"]))),
                ft.DataCell(ft.Row([ft.IconButton(ft.Icons.EDIT_OUTLINED, tooltip="Editar", icon_color=GREEN, on_click=lambda _, item=r: self.residue_dialog(item)),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Eliminar", icon_color="#B34A4A", on_click=lambda _, item=r: self.confirm_delete_residue(item))], spacing=0))]))
        table = ft.DataTable(expand=True, column_spacing=22, heading_row_color="#EAF3ED", columns=[
            ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Residuo")), ft.DataColumn(ft.Text("Categoría")), ft.DataColumn(ft.Text("Cantidad")),
            ft.DataColumn(ft.Text("Estado")), ft.DataColumn(ft.Text("Fecha")), ft.DataColumn(ft.Text("Acciones"))], rows=rows)
        return ft.Column(expand=True, controls=[ft.Row([self.search, self.category_filter, self.state_filter, ft.Button("Nuevo residuo", icon=ft.Icons.ADD, bgcolor=GREEN, color="white", on_click=lambda _: self.residue_dialog())]),
            ft.Container(expand=True, bgcolor="white", border_radius=14, padding=12, content=ft.Column([table if rows else self.empty("No se encontraron residuos.", "Registrar residuo")], scroll=ft.ScrollMode.AUTO))])

    def category_list(self):
        rows = []
        for c in self.repo.categories():
            usage = self.repo.category_usage(c["id"])
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(c["id"]))), ft.DataCell(ft.Text(c["nombre"])), ft.DataCell(ft.Text(c["tipo"])),
                ft.DataCell(ft.Text(c["descripcion"] or "—")), ft.DataCell(ft.Text(str(usage))),
                ft.DataCell(ft.Row([ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=GREEN, tooltip="Editar", on_click=lambda _, item=c: self.category_dialog(item)),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#B34A4A", tooltip="Eliminar", on_click=lambda _, item=c: self.confirm_delete_category(item))], spacing=0))]))
        return ft.Column(expand=True, controls=[ft.Row([ft.Container(expand=True), ft.Button("Nueva categoría", icon=ft.Icons.ADD, bgcolor=GREEN, color="white", on_click=lambda _: self.category_dialog())]),
            ft.Container(expand=True, bgcolor="white", border_radius=14, padding=12, content=ft.Column([ft.DataTable(expand=True, heading_row_color="#EAF3ED", columns=[ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Nombre")), ft.DataColumn(ft.Text("Tipo")), ft.DataColumn(ft.Text("Descripción")), ft.DataColumn(ft.Text("Registros")), ft.DataColumn(ft.Text("Acciones"))], rows=rows)], scroll=ft.ScrollMode.AUTO))])

    def empty(self, message, action):
        return ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True, controls=[ft.Icon(ft.Icons.RECYCLING_OUTLINED, size=48, color="#9DB9AA"), ft.Text(message, color="#62736B"), ft.TextButton(action, on_click=lambda _: self.residue_dialog())])

    def category_dialog(self, item=None):
        name = ft.TextField(label="Nombre *", value=item["nombre"] if item else "", autofocus=True)
        description = ft.TextField(label="Descripción", value=item["descripcion"] if item else "", multiline=True, min_lines=2, max_lines=3)
        kind = ft.Dropdown(label="Tipo", value=item["tipo"] if item else "Reciclable", options=[ft.DropdownOption(x) for x in TYPES])
        dialog = ft.AlertDialog(modal=True, title=ft.Text("Editar categoría" if item else "Nueva categoría"), content=ft.Container(width=420, content=ft.Column([name, description, kind], tight=True)), actions=[])
        def save(_):
            if not name.value.strip(): self.notify("El nombre es obligatorio.", True); return
            try:
                self.repo.save_category((name.value.strip(), description.value.strip(), kind.value), item["id"] if item else None)
            except Exception:
                self.notify("Ya existe una categoría con ese nombre.", True); return
            self.close_dialog(); self.notify("Categoría guardada."); self.render_content()
        dialog.actions = [ft.TextButton("Cancelar", on_click=lambda _: self.close_dialog()), ft.Button("Guardar", bgcolor=GREEN, color="white", on_click=save)]
        self.open_dialog(dialog)

    def residue_dialog(self, item=None):
        categories = self.repo.categories()
        if not categories: self.notify("Crea al menos una categoría primero.", True); return
        self.selected_image = ""
        name = ft.TextField(label="Nombre *", value=item["nombre"] if item else "", autofocus=True)
        category = ft.Dropdown(label="Categoría *", value=str(item["categoria_id"]) if item else str(categories[0]["id"]), options=[ft.DropdownOption(str(c["id"]), c["nombre"]) for c in categories])
        description = ft.TextField(label="Descripción", value=item["descripcion"] if item else "", multiline=True, min_lines=2, max_lines=3)
        quantity = ft.TextField(label="Cantidad *", value=str(item["cantidad"]) if item else "", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        unit = ft.Dropdown(label="Unidad", value=item["unidad"] if item else "piezas", options=[ft.DropdownOption(x) for x in UNITS], expand=True)
        location = ft.TextField(label="Ubicación", value=item["ubicacion"] if item else "")
        state = ft.Dropdown(label="Estado", value=item["estado"] if item else "Almacenado", options=[ft.DropdownOption(x) for x in STATES])
        registered = ft.TextField(label="Fecha (AAAA-MM-DD)", value=item["fecha_registro"] if item else date.today().isoformat())
        notes = ft.TextField(label="Notas", value=item["notas"] if item else "", multiline=True, min_lines=2, max_lines=3)
        photo_label = ft.Text("Fotografía: sin seleccionar" if not item or not item["foto"] else f"Fotografía actual: {Path(item['foto']).name}", size=12, color="#62736B")
        self.photo_label = photo_label
        form = ft.Column([name, category, description, ft.Row([quantity, unit]), location, state, registered, notes,
                          ft.Row([ft.OutlinedButton("Seleccionar imagen", icon=ft.Icons.IMAGE_OUTLINED, on_click=self.select_image), photo_label])], tight=True, scroll=ft.ScrollMode.AUTO)
        dialog = ft.AlertDialog(modal=True, title=ft.Text("Editar residuo" if item else "Nuevo residuo"), content=ft.Container(width=520, height=570, content=form), actions=[])
        def save(_):
            if not name.value.strip(): self.notify("El nombre es obligatorio.", True); return
            try: amount = float(quantity.value.replace(",", "."))
            except (ValueError, AttributeError): self.notify("La cantidad debe ser un número válido.", True); return
            try: date.fromisoformat(registered.value)
            except ValueError: self.notify("Usa la fecha en formato AAAA-MM-DD.", True); return
            photo = copy_image(self.selected_image) if self.selected_image else (item["foto"] if item else "")
            self.repo.save_residue((name.value.strip(), description.value.strip(), int(category.value), amount, unit.value, registered.value, location.value.strip(), state.value, photo, notes.value.strip()), item["id"] if item else None)
            self.close_dialog(); self.notify("Residuo guardado."); self.render_content()
        dialog.actions = [ft.TextButton("Cancelar", on_click=lambda _: self.close_dialog()), ft.Button("Guardar", bgcolor=GREEN, color="white", on_click=save)]
        self.open_dialog(dialog)

    async def select_image(self, _):
        files = await self.file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png", "jpg", "jpeg", "webp"],
        )
        if files:
            selected = files[0]
            self.selected_image = selected.path
            if hasattr(self, "photo_label"):
                self.photo_label.value = f"Nueva fotografía: {selected.name}"
                self.page.update()

    def confirm_delete_residue(self, item):
        self.confirm("Eliminar residuo", f"¿Eliminar «{item['nombre']}»? Esta acción no se puede deshacer.", lambda: self.delete_residue(item["id"]))

    def delete_residue(self, item_id):
        self.repo.delete_residue(item_id); self.close_dialog(); self.notify("Residuo eliminado."); self.render_content()

    def confirm_delete_category(self, item):
        count = self.repo.category_usage(item["id"])
        if count:
            self.notify(f"No se puede eliminar: tiene {count} residuo(s) asociado(s).", True); return
        self.confirm("Eliminar categoría", f"¿Eliminar «{item['nombre']}»?", lambda: self.delete_category(item["id"]))

    def delete_category(self, item_id):
        self.repo.delete_category(item_id); self.close_dialog(); self.notify("Categoría eliminada."); self.render_content()

    def confirm(self, title, message, action):
        dialog = ft.AlertDialog(modal=True, title=ft.Text(title), content=ft.Text(message), actions=[ft.TextButton("Cancelar", on_click=lambda _: self.close_dialog()), ft.Button("Eliminar", bgcolor="#B34A4A", color="white", on_click=lambda _: action())])
        self.open_dialog(dialog)

    def open_dialog(self, dialog):
        self.page.show_dialog(dialog)

    def close_dialog(self):
        self.page.pop_dialog()

    def notify(self, message, error=False):
        self.page.show_dialog(ft.SnackBar(ft.Text(message), bgcolor="#B34A4A" if error else GREEN))

    @staticmethod
    def format_date(value):
        try: return date.fromisoformat(value).strftime("%d/%m/%Y")
        except ValueError: return value

    @staticmethod
    def format_number(value):
        return str(int(value)) if float(value).is_integer() else str(value)


def main(page: ft.Page):
    initialize_database()
    WasteApp(page).setup()


if __name__ == "__main__":
    ft.run(main, assets_dir=str(ROOT_DIR / "assets"))
