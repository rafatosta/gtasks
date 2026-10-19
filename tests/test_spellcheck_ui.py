"""Opt-in GTK integration checks: GTASKS_TEST_GTK=1 with a display available."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.environ.get("GTASKS_TEST_GTK") == "1", "Requires an explicit GTK test session")
class SpellcheckUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        gi.require_version("GtkSource", "5")
        gi.require_version("Spelling", "1")
        from gi.repository import Adw, Gio, GLib, Gtk, Spelling
        cls.Adw, cls.Gio, cls.GLib, cls.Gtk = Adw, Gio, GLib, Gtk
        if not Gtk.init_check():
            raise unittest.SkipTest("No GTK display")
        Adw.init()
        Spelling.init()
        if not Spelling.Provider.get_default().supports_language("pt_BR"):
            raise unittest.SkipTest("Portuguese dictionary is not installed")
        cls.schemas = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.schemas.cleanup)
        schema = Path(__file__).resolve().parents[1] / "data/io.github.rafatosta.gtasks.gschema.xml"
        shutil.copy(schema, cls.schemas.name)
        subprocess.run(["glib-compile-schemas", "--strict", cls.schemas.name], check=True)
        cls.source = Gio.SettingsSchemaSource.new_from_directory(
            cls.schemas.name, Gio.SettingsSchemaSource.get_default(), False
        )

    def setUp(self):
        from gtasks.views.spellcheck import attach_entry_spellcheck
        self.settings = self.Gio.Settings.new_full(
            self.source.lookup("io.github.rafatosta.gtasks", False),
            self.Gio.memory_settings_backend_new(), None,
        )
        self.window = self.Adw.Window(default_width=440, default_height=300)
        self.addCleanup(self.window.destroy)
        box = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL)
        self.fields = [self.Gtk.Entry(), self.Adw.EntryRow(title="Título")]
        for field in self.fields:
            attach_entry_spellcheck(field, self.settings)
            field.set_text("Orientações para uma viageem.")
            field.set_position(len(field.get_text()))
            box.append(field)
        self.window.set_content(box)
        self.window.present()
        self.drain(1000)

    def drain(self, milliseconds=100):
        loop = self.GLib.MainLoop()
        self.GLib.timeout_add(milliseconds, lambda: (loop.quit(), False)[1])
        loop.run()

    def text_widget(self, field):
        while not isinstance(field, self.Gtk.Text):
            field = field.get_delegate()
        return field

    def test_unicode_underlines_and_corrections_for_both_native_inputs(self):
        for field in self.fields:
            with self.subTest(widget=type(field).__name__):
                self.assertIn("underline", self.text_widget(field).get_attributes().to_string())
                buffer = field._spelling_buffer
                buffer.place_cursor(buffer.get_iter_at_offset(field.get_text().index("viageem") + 2))
                field._spelling_adapter.update_corrections()
                field._spelling_adapter.activate_action("correct", self.GLib.Variant("s", "viagem"))
                self.assertEqual(field.get_text(), "Orientações para uma viagem.")
                self.assertEqual(buffer.get_text(*buffer.get_bounds(), False), field.get_text())
                field.insert_text("Nova ", 0)
                field.delete_text(0, 5)
                self.text_widget(field).activate_action("text.undo", None)
                self.drain()
                self.assertEqual(buffer.get_text(*buffer.get_bounds(), False), field.get_text())
                self.assertIsNotNone(self.text_widget(field).get_extra_menu())

    def test_enabled_and_language_settings_are_shared(self):
        self.settings.set_boolean("spell-check-enabled", False)
        self.drain()
        for field in self.fields:
            self.assertFalse(field._spelling_adapter.get_enabled())
            self.assertFalse(self.text_widget(field).get_attributes().to_string())
        self.fields[0]._spelling_adapter.set_language("en_US")
        self.assertEqual(self.fields[1]._spelling_adapter.get_language(), "en_US")
        self.assertEqual(self.settings.get_string("spelling-language"), "en_US")

    def test_long_suggestion_respects_entry_limit(self):
        entry = self.fields[0]
        entry.set_max_length(5)
        entry.set_text("viage")
        buffer = entry._spelling_buffer
        buffer.begin_user_action()
        buffer.delete(*buffer.get_bounds())
        buffer.insert(buffer.get_start_iter(), "viagem")
        buffer.end_user_action()
        self.assertEqual(entry.get_text(), "viage")
        self.assertEqual(buffer.get_text(*buffer.get_bounds(), False), "viage")
