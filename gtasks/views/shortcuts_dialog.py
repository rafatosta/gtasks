import gi

gi.require_version("Adw", "1")

from gi.repository import Adw

from gtasks.i18n import _


def create_shortcuts_dialog() -> Adw.ShortcutsDialog:
    """Show the registered accelerators using GNOME's native adaptive dialog."""
    dialog = Adw.ShortcutsDialog(title=_("Keyboard Shortcuts"))
    general = Adw.ShortcutsSection.new(_("General"))
    for title, action in (
        (_("Quit Application"), "app.quit"),
        (_("Close Window or Dialog"), "win.close"),
        (_("Preferences"), "app.preferences"),
        (_("Keyboard Shortcuts"), "app.shortcuts"),
        (_("Refresh Lists and Tasks"), "win.refresh"),
    ):
        general.add(Adw.ShortcutsItem(title=title, action_name=action))
    dialog.add(general)
    navigation = Adw.ShortcutsSection.new(_("Navigation"))
    navigation.add(Adw.ShortcutsItem.new(_("Open Main Menu"), "F10"))
    navigation.add(Adw.ShortcutsItem.new(_("Go Back"), "<Alt>Left"))
    navigation.add(Adw.ShortcutsItem.new(_("Close Dialog or Menu"), "Escape"))
    dialog.add(navigation)
    return dialog
