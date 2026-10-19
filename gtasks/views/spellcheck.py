"""Native, offline spelling for multiline and single-line text inputs."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
gi.require_version("Spelling", "1")
from gi.repository import Gio, GLib, Gtk, GtkSource, Pango, Spelling


def _create_adapter(buffer, settings):
    Spelling.init()
    provider = Spelling.Provider.get_default()
    requested = settings.get_string("spelling-language") if settings else "pt_BR"
    language = requested if provider.supports_language(requested) else provider.get_default_code()
    checker = Spelling.Checker.new(provider, language)
    adapter = Spelling.TextBufferAdapter.new(buffer, checker)
    if settings is not None:
        settings.bind("spell-check-enabled", adapter, "enabled", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("spelling-language", adapter, "language", Gio.SettingsBindFlags.DEFAULT)
        if language and not provider.supports_language(adapter.get_language()):
            adapter.set_language(language)
    else:
        adapter.set_enabled(True)
    return adapter


def create_details_view(text: str, settings: Gio.Settings | None = None) -> Gtk.TextView:
    Spelling.init()
    buffer = GtkSource.Buffer()
    buffer.set_highlight_syntax(False)
    buffer.set_text(text)
    view = Gtk.TextView(buffer=buffer, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                        top_margin=12, bottom_margin=12,
                        left_margin=12, right_margin=12)
    view.add_css_class("inline")
    adapter = _create_adapter(buffer, settings)
    view.insert_action_group("spelling", adapter)
    view.set_extra_menu(adapter.get_menu_model())

    # In libspelling 0.4, context-click does not move the text cursor by itself.
    # Match the library's example so suggestions belong to the clicked word.
    gesture = Gtk.GestureClick(button=0)
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    def context_pressed(controller, count, x, y):
        event = controller.get_current_event()
        if count != 1 or event is None or not event.triggers_context_menu():
            return
        if not buffer.get_has_selection():
            bx, by = view.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(x), int(y))
            _found, iterator = view.get_iter_at_location(bx, by)
            buffer.place_cursor(iterator)
        adapter.update_corrections()
    gesture.connect("pressed", context_pressed)
    view.add_controller(gesture)
    # Retain the adapter for the buffer's lifetime, including asynchronous checks.
    view._spelling_adapter = adapter
    return view


def attach_entry_spellcheck(editable, settings: Gio.Settings | None = None) -> None:
    """Bridge a native GtkEditable to libspelling without replacing its widget.

    The source buffer provides asynchronous checking and the standard correction
    menu. Its spelling tags become Pango attributes on the original text input.
    """
    text_widget = editable
    while not isinstance(text_widget, Gtk.Text):
        text_widget = text_widget.get_delegate()
        if text_widget is None:
            raise TypeError("The editable must delegate to Gtk.Text")
    buffer = GtkSource.Buffer()
    buffer.set_highlight_syntax(False)
    buffer.set_text(editable.get_text())
    adapter = _create_adapter(buffer, settings)
    original_attributes = text_widget.get_attributes()
    if original_attributes is not None:
        original_attributes = original_attributes.copy()
    original_menu = text_widget.get_extra_menu()
    menu = Gio.Menu()
    if original_menu is not None:
        menu.append_section(None, original_menu)
    menu.append_section(None, adapter.get_menu_model())
    text_widget.insert_action_group("spelling", adapter)
    text_widget.set_extra_menu(menu)
    updating = False
    action_depth = 0
    paint_pending = None

    def paint():
        nonlocal paint_pending
        paint_pending = None
        attributes = original_attributes.copy() if original_attributes else Pango.AttrList()
        value = editable.get_text()
        if adapter.get_enabled():
            iterator = buffer.get_start_iter()
            tag = adapter.get_tag()
            while not iterator.is_end():
                start = iterator.get_offset()
                marked = iterator.has_tag(tag)
                if not iterator.forward_to_tag_toggle(tag):
                    iterator = buffer.get_end_iter()
                if marked:
                    underline = Pango.attr_underline_new(Pango.Underline.ERROR)
                    first = len(value[:start].encode("utf-8"))
                    last = len(value[:iterator.get_offset()].encode("utf-8"))
                    underline.start_index = first
                    underline.end_index = last
                    attributes.insert(underline)
                    color = tag.get_property("underline-rgba")
                    if color is not None:
                        ink = Pango.attr_underline_color_new(
                            int(color.red * 65535), int(color.green * 65535), int(color.blue * 65535)
                        )
                        ink.start_index, ink.end_index = first, last
                        attributes.insert(ink)
        # EntryRow also styles its title; only decorate the Gtk.Text delegate.
        text_widget.set_attributes(attributes)
        return GLib.SOURCE_REMOVE

    def queue_paint(*_args):
        nonlocal paint_pending
        if paint_pending is None:
            paint_pending = GLib.idle_add(paint)

    def sync_cursor(*_args):
        if updating:
            return
        position = max(0, editable.get_position())
        bounds = editable.get_selection_bounds()
        selected = bool(bounds)
        start, end = bounds if selected else (position, position)
        bound = start if position == end else end
        buffer.select_range(buffer.get_iter_at_offset(position),
                            buffer.get_iter_at_offset(bound if selected else position))

    def from_entry(*_args):
        nonlocal updating
        if updating:
            return
        updating = True
        buffer.delete(*buffer.get_bounds())
        buffer.insert(buffer.get_start_iter(), editable.get_text())
        updating = False
        sync_cursor()
        queue_paint()

    def from_buffer(*_args):
        nonlocal updating
        if updating or action_depth:
            return
        new = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        old = editable.get_text()
        if new == old:
            return
        # Replace only the affected range, preserving the native editable and
        # its selection/clipboard behavior instead of rebuilding the control.
        start = 0
        while start < min(len(old), len(new)) and old[start] == new[start]:
            start += 1
        end = 0
        while end < min(len(old), len(new)) - start and old[-end - 1] == new[-end - 1]:
            end += 1
        cursor = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()
        updating = True
        editable.delete_text(start, len(old) - end)
        editable.insert_text(new[start:len(new) - end if end else None], start)
        editable.set_position(cursor)
        updating = False
        # Entry max-length can reject an expanded suggestion. Keep both texts
        # identical so later corrections never use stale character offsets.
        if editable.get_text() != new:
            from_entry()
        queue_paint()

    def begin_action(*_args):
        nonlocal action_depth
        action_depth += 1

    def end_action(*_args):
        nonlocal action_depth
        action_depth -= 1
        from_buffer()

    editable.connect("changed", from_entry)
    editable.connect("notify::cursor-position", sync_cursor)
    editable.connect("notify::selection-bound", sync_cursor)
    buffer.connect("changed", from_buffer)
    buffer.connect("begin-user-action", begin_action)
    buffer.connect("end-user-action", end_action)
    buffer.connect_after("apply-tag", queue_paint)
    buffer.connect_after("remove-tag", queue_paint)
    adapter.connect("notify::enabled", queue_paint)

    gesture = Gtk.GestureClick(button=0)
    gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    def context_pressed(controller, count, x, _y):
        event = controller.get_current_event()
        if count != 1 or event is None or not event.triggers_context_menu():
            return
        if not editable.get_selection_bounds():
            position = min(range(len(editable.get_text()) + 1), key=lambda offset:
                           abs(text_widget.compute_cursor_extents(offset).strong.get_x() - x))
            editable.set_position(position)
        sync_cursor()
        adapter.update_corrections()
    gesture.connect("pressed", context_pressed)
    text_widget.add_controller(gesture)
    def unmapped(*_args):
        nonlocal paint_pending
        if paint_pending is not None:
            GLib.source_remove(paint_pending)
            paint_pending = None
    editable.connect("unrealize", unmapped)
    editable._spelling_adapter = adapter
    editable._spelling_buffer = buffer
    sync_cursor()
    queue_paint()
