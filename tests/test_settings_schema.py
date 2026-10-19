import unittest
from pathlib import Path
from xml.etree import ElementTree


SCHEMA = Path(__file__).resolve().parents[1] / "data" / (
    "io.github.rafatosta.gtasks.gschema.xml"
)


class SettingsSchemaTest(unittest.TestCase):
    def test_schema_has_expected_defaults(self):
        schema = ElementTree.parse(SCHEMA).getroot().find("schema")
        self.assertEqual(schema.attrib["id"], "io.github.rafatosta.gtasks")
        self.assertEqual(schema.attrib["path"], "/io/github/rafatosta/gtasks/")
        keys = {
            key.attrib["name"]: (key.attrib["type"], key.findtext("default"))
            for key in schema.findall("key")
        }
        self.assertEqual(keys["sync-on-startup"], ("b", "true"))
        self.assertEqual(keys["sync-interval"], ("i", "15"))
        self.assertEqual(keys["show-completed"], ("b", "true"))
        self.assertEqual(keys["restore-last-list"], ("b", "true"))
        self.assertEqual(keys["spell-check-enabled"], ("b", "true"))
        self.assertEqual(keys["spelling-language"], ("s", "'pt_BR'"))
        self.assertEqual(keys["last-source"], ("s", "''"))
        self.assertEqual(keys["last-list-id"], ("s", "''"))


if __name__ == "__main__":
    unittest.main()
