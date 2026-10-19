import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, Gtk


SYNC_INTERVALS = (0, 5, 15, 30, 60)


def create_preferences_dialog(settings: Gio.Settings) -> Adw.PreferencesDialog:
    """Native GNOME preferences with persistent GSettings bindings."""
    dialog = Adw.PreferencesDialog()
    dialog.set_title("Preferências")

    page = Adw.PreferencesPage()
    dialog.add(page)

    sync_group = Adw.PreferencesGroup(title="Sincronização")
    page.add(sync_group)

    startup = Adw.SwitchRow(
        title="Sincronizar ao iniciar",
        subtitle="Atualizar as contas Google ao abrir o GTasks",
    )
    settings.bind(
        "sync-on-startup", startup, "active", Gio.SettingsBindFlags.DEFAULT
    )
    sync_group.add(startup)

    intervals = Gtk.StringList.new(
        ["Desativada", "A cada 5 minutos", "A cada 15 minutos",
         "A cada 30 minutos", "A cada 60 minutos"]
    )
    interval = Adw.ComboRow(
        title="Atualização periódica",
        subtitle="Verificar alterações enquanto o GTasks estiver aberto",
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

    display_group = Adw.PreferencesGroup(title="Apresentação")
    page.add(display_group)

    completed = Adw.SwitchRow(
        title="Mostrar tarefas concluídas",
        subtitle="Exibir tarefas concluídas junto das pendentes",
    )
    settings.bind(
        "show-completed", completed, "active", Gio.SettingsBindFlags.DEFAULT
    )
    display_group.add(completed)

    restore = Adw.SwitchRow(
        title="Restaurar última lista",
        subtitle="Reabrir a última lista selecionada ao iniciar",
    )
    settings.bind(
        "restore-last-list", restore, "active", Gio.SettingsBindFlags.DEFAULT
    )
    display_group.add(restore)

    spelling_group = Adw.PreferencesGroup(title="Escrita")
    spelling = Adw.SwitchRow(
        title="Verificar ortografia",
        subtitle="Destacar palavras e oferecer sugestões nos campos de texto",
    )
    settings.bind("spell-check-enabled", spelling, "active", Gio.SettingsBindFlags.DEFAULT)
    spelling_group.add(spelling)
    page.add(spelling_group)

    offline_group = Adw.PreferencesGroup(
        title="Armazenamento",
        description=(
            "Listas locais são salvas no dispositivo. As contas Google mantêm "
            "uma cópia para consulta offline; alterações remotas exigem conexão."
        ),
    )
    page.add(offline_group)

    return dialog
