import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, Gtk

from gtasks.i18n import _


SYNC_INTERVALS = (0, 5, 15, 30, 60)


def create_preferences_dialog(settings: Gio.Settings) -> Adw.PreferencesDialog:
    """Native GNOME preferences with persistent GSettings bindings."""
    dialog = Adw.PreferencesDialog()
    dialog.set_title(_("Preferences"))

    page = Adw.PreferencesPage()
    dialog.add(page)

    sync_group = Adw.PreferencesGroup(title=_("Synchronization"))
    page.add(sync_group)

    startup = Adw.SwitchRow(
        title=_("Synchronize on Startup"),
        subtitle=_("Refresh Google accounts when GTasks starts"),
    )
    settings.bind(
        "sync-on-startup", startup, "active", Gio.SettingsBindFlags.DEFAULT
    )
    sync_group.add(startup)

    intervals = Gtk.StringList.new(
        [_("Disabled"), _("Every 5 minutes"), _("Every 15 minutes"),
         _("Every 30 minutes"), _("Every 60 minutes")]
    )
    interval = Adw.ComboRow(
        title=_("Automatic Refresh"),
        subtitle=_("Check for changes while GTasks is open"),
        model=intervals,
    )
    configured = settings.get_int("sync-interval")
    interval.set_selected(
        SYNC_INTERVALS.index(configured) if configured in SYNC_INTERVALS else 0
    )

    def change_interval(row: Adw.ComboRow, _property) -> None:
        index = row.get_selected()
        if index < len(SYNC_INTERVALS):
            settings.set_int("sync-interval", SYNC_INTERVALS[index])

    interval.connect("notify::selected", change_interval)
    sync_group.add(interval)

    display_group = Adw.PreferencesGroup(title=_("Appearance"))
    page.add(display_group)

    completed = Adw.SwitchRow(
        title=_("Show Completed Tasks"),
        subtitle=_("Show completed tasks alongside pending tasks"),
    )
    settings.bind(
        "show-completed", completed, "active", Gio.SettingsBindFlags.DEFAULT
    )
    display_group.add(completed)

    restore = Adw.SwitchRow(
        title=_("Restore Last List"),
        subtitle=_("Reopen the last selected list on startup"),
    )
    settings.bind(
        "restore-last-list", restore, "active", Gio.SettingsBindFlags.DEFAULT
    )
    display_group.add(restore)

    spelling_group = Adw.PreferencesGroup(title=_("Writing"))
    spelling = Adw.SwitchRow(
        title=_("Check Spelling"),
        subtitle=_("Underline words and offer suggestions in text fields"),
    )
    settings.bind("spell-check-enabled", spelling, "active", Gio.SettingsBindFlags.DEFAULT)
    spelling_group.add(spelling)
    page.add(spelling_group)

    offline_group = Adw.PreferencesGroup(
        title=_("Storage"),
        description=(
            _("Local lists are saved on this device. Google accounts keep a copy for offline viewing; remote changes require a connection.")
        ),
    )
    page.add(offline_group)

    return dialog
