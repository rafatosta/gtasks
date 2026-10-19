from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Pango

from gtasks.models.task_list import TaskList


class SourceListGroup(Gtk.Box):
    """A list group bound to one data source (local or an online account)."""

    def __init__(
        self,
        source_id: str,
        title: str,
        on_create: Callable[[str], None],
        on_select: Callable[[str, str], None],
        on_edit: Callable[[TaskList], None],
        on_delete: Callable[[TaskList], None],
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.source_id = source_id
        self._on_select = on_select
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._rows: dict[Gtk.ListBoxRow, str] = {}
        self._updating = False

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon_name = (
            "drive-harddisk-symbolic"
            if source_id == "local"
            else "network-server-symbolic"
        )
        header.append(Gtk.Image.new_from_icon_name(icon_name))

        label = Gtk.Label(label=title, xalign=0, hexpand=True)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_tooltip_text(title)
        label.add_css_class("heading" if source_id == "local" else "dim-label")
        header.append(label)

        create = Gtk.Button(icon_name="list-add-symbolic")
        create.add_css_class("flat")
        create.set_tooltip_text("Criar lista")
        create.connect("clicked", lambda _button: on_create(self.source_id))
        header.append(create)
        self.append(header)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list_box.add_css_class("navigation-sidebar")
        self._list_box.connect("row-selected", self._row_selected)
        self.append(self._list_box)

    def set_lists(self, lists: list[TaskList], selected: TaskList | None) -> None:
        self._updating = True
        self._rows.clear()
        while row := self._list_box.get_row_at_index(0):
            self._list_box.remove(row)

        selected_row = None
        for task_list in lists:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=task_list.name, xalign=0)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            label.set_margin_start(12)
            label.set_margin_end(12)
            label.set_hexpand(True)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_tooltip_text(task_list.name)
            content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            content.append(label)
            menu = Gtk.MenuButton(icon_name="view-more-symbolic", valign=Gtk.Align.CENTER)
            menu.add_css_class("flat")
            menu.set_tooltip_text(f"Opções de {task_list.name}")
            popover = Gtk.Popover()
            actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            for title, callback in (("Editar lista", self._on_edit),
                                    ("Excluir lista", self._on_delete)):
                button = Gtk.Button(label=title)
                button.add_css_class("flat")
                def activate(_button, item=task_list, action=callback, popup=popover):
                    popup.popdown()
                    action(item)
                button.connect("clicked", activate)
                actions.append(button)
            popover.set_child(actions)
            menu.set_popover(popover)
            content.append(menu)
            row.set_child(content)
            self._list_box.append(row)
            self._rows[row] = task_list.id
            if selected is not None and task_list.id == selected.id:
                selected_row = row

        if selected_row is not None:
            self._list_box.select_row(selected_row)
        self._updating = False

    def unselect(self) -> None:
        self._updating = True
        self._list_box.unselect_all()
        self._updating = False

    def _row_selected(
        self, _box: Gtk.ListBox, row: Gtk.ListBoxRow | None
    ) -> None:
        if not self._updating and row is not None:
            self._on_select(self.source_id, self._rows[row])


class ListSidebar(Gtk.ScrolledWindow):
    """Displays one SourceListGroup for every available data source."""

    def __init__(
        self,
        on_create_list: Callable[[str], None],
        on_select_list: Callable[[str, str], None],
        on_edit_list: Callable[[TaskList], None],
        on_delete_list: Callable[[TaskList], None],
    ) -> None:
        super().__init__(vexpand=True)
        self._on_edit_list = on_edit_list
        self._on_delete_list = on_delete_list
        self._on_create_list = on_create_list
        self._on_select_list = on_select_list
        self._groups: dict[str, SourceListGroup] = {}
        self._updating = False

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        sidebar.set_size_request(250, -1)
        sidebar.set_margin_top(18)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_margin_bottom(12)

        local = self._new_group("local", "Neste dispositivo")
        sidebar.append(local)

        google = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        google_header = Gtk.Label(label="Google Tasks", xalign=0)
        google_header.add_css_class("heading")
        google.append(google_header)

        self._accounts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        google.append(self._accounts_box)
        sidebar.append(google)

        self._status = Gtk.Label(label="", xalign=0, wrap=True)
        self._status.add_css_class("dim-label")
        sidebar.append(self._status)

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_child(sidebar)

    def _new_group(self, source_id: str, title: str) -> SourceListGroup:
        group = SourceListGroup(
            source_id=source_id,
            title=title,
            on_create=self._on_create_list,
            on_select=self._selected,
            on_edit=self._on_edit_list,
            on_delete=self._on_delete_list,
        )
        self._groups[source_id] = group
        return group

    def set_status(self, message: str) -> None:
        self._status.set_label(message)

    def set_accounts(self, accounts: list[tuple[str, str]]) -> None:
        self._updating = True
        for source_id in list(self._groups):
            if source_id != "local":
                del self._groups[source_id]
        while child := self._accounts_box.get_first_child():
            self._accounts_box.remove(child)

        if not accounts:
            hint = Gtk.Label(
                label="Adicione uma conta Google em Configurações → Contas Online.",
                xalign=0,
                wrap=True,
            )
            hint.add_css_class("dim-label")
            self._accounts_box.append(hint)

        for source_id, identity in accounts:
            self._accounts_box.append(self._new_group(source_id, identity))
        self._updating = False

    def set_lists(self, lists: list[TaskList], selected: TaskList | None) -> None:
        grouped: dict[str, list[TaskList]] = {
            source_id: [] for source_id in self._groups
        }
        for task_list in lists:
            if task_list.source in grouped:
                grouped[task_list.source].append(task_list)

        self._updating = True
        for source_id, group in self._groups.items():
            group.set_lists(
                grouped[source_id],
                selected if selected is not None and selected.source == source_id else None,
            )
        self._updating = False

    def _selected(self, source_id: str, list_id: str) -> None:
        if self._updating:
            return
        self._updating = True
        for other_id, group in self._groups.items():
            if other_id != source_id:
                group.unselect()
        self._updating = False
        self._on_select_list(source_id, list_id)
