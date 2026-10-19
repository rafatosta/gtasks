import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gtk

from gtasks.i18n import _


def create_about_dialog(version: str) -> Adw.AboutDialog:
    """Construct the GNOME dialog; AboutDialog is a final GObject type."""
    return Adw.AboutDialog(
        application_name="GTasks",
        application_icon="io.github.rafatosta.gtasks",
        developer_name="Rafael Tosta",
        version=version,
        comments=_("A task manager for GNOME with local lists and Google Tasks."),
        copyright="© 2026 Rafael Tosta",
        website="https://github.com/rafatosta/gtasks",
        issue_url="https://github.com/rafatosta/gtasks/issues",
        license_type=Gtk.License.GPL_3_0,
        developers=["Rafael Tosta"],
    )
