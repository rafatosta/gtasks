import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application) -> None:
        super().__init__(application=application, title="GTasks")
        self.set_default_size(640, 480)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(
            Gtk.Label(
                label="GTasks",
                halign=Gtk.Align.CENTER,
                valign=Gtk.Align.CENTER,
                hexpand=True,
                vexpand=True,
            )
        )
        self.set_content(toolbar)
