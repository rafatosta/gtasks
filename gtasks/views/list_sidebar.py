from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Pango

from gtasks.models.task_list import TaskList


class ListSidebar(Gtk.ScrolledWindow):
    """Navigation for local lists and Google accounts."""

    def __init__(
        self,
        on_create_list: Callable[[str], None],
        on_select_list: Callable[[str, str], None],
    ) -> None:
        super().__init__(vexpand=True)
        self._on_create_list = on_create_list
        self._on_select_list = on_select_list
        self._groups: dict[str, Gtk.ListBox] = {}
        self._rows: dict[Gtk.ListBoxRow, tuple[str, str]] = {}
        self._updating = False

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        sidebar.set_size_request(250, -1)
        sidebar.set_margin_top(18)
        sidebar.set_margin_start(12)
        sidebar.set_margin_end(12)
        sidebar.set_margin_bottom(12)

        local = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="Neste dispositivo", xalign=0, hexpand=True)
        title.add_css_class("heading")
        header.append(title)
        header.append(self._add_button("local", "Criar lista local"))
        local.append(header)
        local.append(self._new_list_box("local"))
        sidebar.append(local)

        google = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        google_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        google_header.append(Gtk.Image.new_from_icon_name("network-server-symbolic"))
        google_title = Gtk.Label(label="Google Tasks", xalign=0, hexpand=True)
        google_title.add_css_class("heading")
        google_header.append(google_title)
        google.append(google_header)
        self._accounts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        google.append(self._accounts_box)
        sidebar.append(google)

        self._status = Gtk.Label(label="", xalign=0, wrap=True)
        self._status.add_css_class("dim-label")
        sidebar.append(self._status)

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_child(sidebar)

    def _add_button(self, source: str, tooltip: str) -> Gtk.Button:
        button = Gtk.Button(icon_name="list-add-symbolic")
        button.add_css_class("flat")
        button.set_tooltip_text(tooltip)
        button.connect("clicked", lambda _button: self._on_create_list(source))
        return button

    def _new_list_box(self, source: str) -> Gtk.ListBox:
        box = Gtk.ListBox()
        box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        box.add_css_class("navigation-sidebar")
        box.connect("row-selected", self._on_row_selected)
        self._groups[source] = box
        return box

    def set_status(self, message: str) -> None:
        self._status.set_label(message)

    def set_accounts(self, accounts: list[tuple[str, str]]) -> None:
        self._updating = True
        for source in list(self._groups):
            if source != "local":
                del self._groups[source]
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

        for source, identity in accounts:
            group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=identity, xalign=0, hexpand=True)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.add_css_class("dim-label")
            label.set_tooltip_text(identity)
            header.append(label)
            header.append(self._add_button(source, "Criar lista no Google Tasks"))
            group.append(header)
            group.append(self._new_list_box(source))
            self._accounts_box.append(group)
        self._updating = False

    def set_lists(self, lists: list[TaskList], selected: TaskList | None) -> None:
        self._updating = True
        self._rows.clear()
        for box in self._groups.values():
            while row := box.get_row_at_index(0):
                box.remove(row)

        selected_row: tuple[Gtk.ListBox, Gtk.ListBoxRow] | None = None
        for task_list in lists:
            box = self._groups.get(task_list.source)
            if box is None:
                continue
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=task_list.name, xalign=0)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            label.set_margin_start(12)
            label.set_margin_end(12)
            row.set_child(label)
            box.append(row)
            self._rows[row] = (task_list.source, task_list.id)
            if task_list == selected:
                selected_row = (box, row)

        if selected_row is not None:
            selected_row[0].select_row(selected_row[1])
        self._updating = False

    def _on_row_selected(
        self, _box: Gtk.ListBox, row: Gtk.ListBoxRow | None
    ) -> None:
        if self._updating or row is None:
            return
        source, list_id = self._rows[row]
        self._updating = True
        for other_source, box in self._groups.items():
            if other_source != source:
                box.unselect_all()
        self._updating = False
        self._on_select_list(source, list_id)
