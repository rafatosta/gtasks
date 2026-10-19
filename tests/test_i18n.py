import ast
import gettext
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from gtasks import i18n

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("msgfmt") and shutil.which("msgcmp"), "Requires GNU Gettext")
class InternationalizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.folder.cleanup)
        cls.locale_dir = Path(cls.folder.name)
        destination = cls.locale_dir / "pt_BR/LC_MESSAGES/gtasks.mo"
        destination.parent.mkdir(parents=True)
        subprocess.run(["msgfmt", "--check", "--check-format", "-o", str(destination),
                        str(ROOT / "po/pt_BR.po")], check=True)
        cls.catalog = gettext.translation("gtasks", str(cls.locale_dir), languages=["pt_BR"])

    def tearDown(self):
        i18n.configure()

    def test_english_fallback_and_portuguese_translation(self):
        i18n.configure(self.locale_dir, ["en_US"])
        self.assertEqual(i18n._("Save"), "Save")
        i18n.configure(self.locale_dir, ["pt_BR"])
        self.assertEqual(i18n._("Save"), "Salvar")
        self.assertEqual(i18n._("Preferences"), "Preferências")
        i18n.configure(self.locale_dir, ["fr"])
        self.assertEqual(i18n._("Save"), "Save")

    def test_user_content_is_not_translated_or_reinterpreted(self):
        i18n.configure(self.locale_dir, ["pt_BR"])
        name = "Save {name} & <custom>"
        message = i18n._("Options for {name}").format(name=name)
        self.assertEqual(message, "Opções de " + name)
        self.assertEqual(i18n._("Subtask of {title}").format(title="Save"), "Subtarefa de Save")

    def test_every_marked_source_message_has_a_translation(self):
        covered = 0
        for path in (ROOT / "gtasks").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == "_" and node.args
                        and isinstance(node.args[0], ast.Constant)):
                    message = node.args[0].value
                    self.assertIn(message, self.catalog._catalog, f"Missing translation in {path}: {message}")
                    covered += 1
        self.assertGreater(covered, 100)
        subprocess.run(["msgcmp", str(ROOT / "po/pt_BR.po"), str(ROOT / "po/gtasks.pot")], check=True)

    def test_locale_environment_selects_interface_and_date_format(self):
        code = "from gtasks.i18n import _; from datetime import date; print(_('Save')); print(date(2026, 10, 19).strftime('%x'))"
        for language, locale, expected in [("en_US", "en_US.UTF-8", "Save\n10/19/2026"),
                                            ("pt_BR", "pt_BR.UTF-8", "Salvar\n19/10/2026")]:
            with self.subTest(language=language):
                env = {**os.environ, "GTASKS_LOCALEDIR": str(self.locale_dir),
                       "LANGUAGE": language, "LC_ALL": locale}
                result = subprocess.run([shutil.which("python3"), "-c", code], cwd=ROOT,
                                        env=env, capture_output=True, text=True, check=True)
                # CI images may only provide C.UTF-8; translation must still work.
                self.assertEqual(result.stdout.splitlines()[0], expected.splitlines()[0])
                available = subprocess.run(["locale", "-a"], capture_output=True, text=True).stdout
                if locale.lower().replace("-", "") in available.lower().replace("-", ""):
                    self.assertEqual(result.stdout.strip(), expected)

    def test_desktop_and_appstream_metadata_are_translated(self):
        with tempfile.TemporaryDirectory() as folder:
            for kind, suffix in [("desktop", "desktop"), ("xml", "metainfo.xml")]:
                output = Path(folder) / suffix
                subprocess.run(["msgfmt", "--" + kind,
                    "--template=" + str(ROOT / ("data/io.github.rafatosta.gtasks." + suffix + ".in")),
                    "-d", str(ROOT / "po"), "-o", str(output)], check=True)
                self.assertIn("Tarefas para GNOME", output.read_text())
                self.assertIn("Tasks for GNOME", output.read_text())
