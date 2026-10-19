"""Native, offline spelling for the multiline task editor."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
gi.require_version("Spelling", "1")
from gi.repository import Gio, Gtk, GtkSource, Spelling


def create_details_view(text: str, settings: Gio.Settings | None = None) -> Gtk.TextView:
    Spelling.init()
    buffer = GtkSource.Buffer()
    buffer.set_highlight_syntax(False)
    buffer.set_text(text)
    view = Gtk.TextView(buffer=buffer, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                        top_margin=12, bottom_margin=12,
                        left_margin=12, right_margin=12)
    view.add_css_class("inline")
    provider = Spelling.Provider.get_default()
    requested = settings.get_string("spelling-language") if settings else "pt_BR"
    language = requested if provider.supports_language(requested) else provider.get_default_code()
    checker = Spelling.Checker.new(provider, language)
    adapter = Spelling.TextBufferAdapter.new(buffer, checker)
    view.insert_action_group("spelling", adapter)
    view.set_extra_menu(adapter.get_menu_model())
    if settings is not None:
        settings.bind("spell-check-enabled", adapter, "enabled", Gio.SettingsBindFlags.DEFAULT)
        adapter.connect("notify::language", lambda *_: settings.set_string(
            "spelling-language", adapter.get_language() or requested
        ))
    else:
        adapter.set_enabled(True)

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
