"""Adaptive native editor for the task fields exposed by Google Tasks."""
from datetime import date, timedelta
from collections.abc import Callable

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, GLib, Gtk

from gtasks.models.task import Task


def create_task_editor(task: Task, on_save: Callable) -> Adw.Dialog:
    dialog = Adw.Dialog(title="Editar tarefa", content_width=440, content_height=550)
    toolbar = Adw.ToolbarView()
    header = Adw.HeaderBar(show_start_title_buttons=False, show_end_title_buttons=False)
    cancel = Gtk.Button(label="Cancelar")
    cancel.connect("clicked", lambda _button: dialog.close())
    header.pack_start(cancel)
    save = Gtk.Button(label="Salvar")
    save.add_css_class("suggested-action")
    header.pack_end(save)
    toolbar.add_top_bar(header)

    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    for side in ("top", "bottom", "start", "end"):
        getattr(body, f"set_margin_{side}")(18)
    group = Adw.PreferencesGroup()
    title = Adw.EntryRow(title="Título", text=task.title)
    group.add(title)
    body.append(group)

    details_group = Adw.PreferencesGroup(title="Detalhes")
    notes = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR,
                         top_margin=12, bottom_margin=12,
                         left_margin=12, right_margin=12)
    notes.get_buffer().set_text(task.notes)
    notes.set_sensitive(not task.assigned)
    if task.assigned:
        details_group.set_description("Os detalhes desta tarefa são gerenciados pelo Google.")
    notes_scroll = Gtk.ScrolledWindow(min_content_height=100)
    notes_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    notes_scroll.add_css_class("card")
    notes_scroll.set_child(notes)
    notes.update_property([Gtk.AccessibleProperty.LABEL], ["Detalhes da tarefa"])
    details_group.add(notes_scroll)
    body.append(details_group)

    date_group = Adw.PreferencesGroup(title="Data", description="Dia programado para realizar a tarefa.")
    enabled = Adw.SwitchRow(title="Definir uma data", active=task.due is not None)
    date_group.add(enabled)
    calendar = Gtk.Calendar()
    calendar.set_show_day_names(True)
    if task.due:
        calendar.select_day(GLib.DateTime.new_from_iso8601(task.due + "T12:00:00Z", None))
    popover = Gtk.Popover()
    popover.set_child(calendar)
    date_button = Gtk.MenuButton(popover=popover, hexpand=True)
    date_button.set_sensitive(enabled.get_active())

    def update_date(*_args):
        date_button.set_label(calendar.get_date().format("%d/%m/%Y"))

    calendar.connect("day-selected", update_date)
    update_date()
    enabled.connect("notify::active", lambda *_: date_button.set_sensitive(enabled.get_active()))
    dates = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    dates.set_margin_top(8)
    dates.append(date_button)
    for label, offset in (("Hoje", 0), ("Amanhã", 1)):
        button = Gtk.Button(label=label)
        def choose(_button, days=offset):
            day = date.today() + timedelta(days=days)
            calendar.select_day(GLib.DateTime.new_from_iso8601(day.isoformat() + "T12:00:00Z", None))
            enabled.set_active(True)
        button.connect("clicked", choose)
        dates.append(button)
    date_group.add(dates)
    body.append(date_group)

    error_label = Gtk.Label(wrap=True, xalign=0, visible=False)
    error_label.add_css_class("error")
    body.append(error_label)
    scroll = Gtk.ScrolledWindow(vexpand=True)
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_child(body)
    toolbar.set_content(scroll)
    dialog.set_child(toolbar)

    def validate(*_args):
        save.set_sensitive(bool(title.get_text().strip()))
    title.connect("changed", validate)
    validate()

    def submit(_button):
        buffer = notes.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        due = calendar.get_date().format("%Y-%m-%d") if enabled.get_active() else None
        toolbar.set_sensitive(False)
        dialog.set_can_close(False)
        def succeeded(_result):
            dialog.set_can_close(True)
            dialog.close()
        def failed(error):
            dialog.set_can_close(True)
            toolbar.set_sensitive(True)
            error_label.set_label(str(error) if isinstance(error, (ValueError, RuntimeError))
                                  else "Não foi possível salvar a tarefa. Tente novamente.")
            error_label.set_visible(True)
        on_save(title.get_text(), None if task.assigned else text, due, succeeded, failed)
    save.connect("clicked", submit)
    return dialog
