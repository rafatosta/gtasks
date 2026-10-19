import gi

gi.require_version("Adw", "1")

from gi.repository import Adw


def create_shortcuts_dialog() -> Adw.ShortcutsDialog:
    """Show the registered accelerators using GNOME's native adaptive dialog."""
    dialog = Adw.ShortcutsDialog(title="Atalhos de teclado")
    general = Adw.ShortcutsSection.new("Geral")
    for title, action in (
        ("Sair do aplicativo", "app.quit"),
        ("Fechar janela ou diálogo", "win.close"),
        ("Preferências", "app.preferences"),
        ("Atalhos de teclado", "app.shortcuts"),
        ("Atualizar listas e tarefas", "win.refresh"),
    ):
        general.add(Adw.ShortcutsItem(title=title, action_name=action))
    dialog.add(general)
    navigation = Adw.ShortcutsSection.new("Navegação")
    navigation.add(Adw.ShortcutsItem.new("Abrir menu principal", "F10"))
    navigation.add(Adw.ShortcutsItem.new("Voltar", "<Alt>Left"))
    navigation.add(Adw.ShortcutsItem.new("Fechar diálogo ou menu", "Escape"))
    dialog.add(navigation)
    return dialog
