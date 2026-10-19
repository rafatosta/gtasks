import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AboutMetadataTest(unittest.TestCase):
    def test_appstream_has_about_details(self):
        xml = ET.parse(
            ROOT / "data" / "io.github.rafatosta.gtasks.metainfo.xml"
        ).getroot()

        self.assertEqual(xml.findtext("id"), "io.github.rafatosta.gtasks")
        self.assertEqual(xml.findtext("name"), "GTasks")
        self.assertEqual(xml.findtext("developer/name"), "Rafael Tosta")
        self.assertEqual(xml.findtext("project_license"), "GPL-3.0-or-later")
        urls = {node.get("type"): node.text for node in xml.findall("url")}
        self.assertEqual(urls["homepage"], "https://github.com/rafatosta/gtasks")
        self.assertEqual(
            urls["bugtracker"], "https://github.com/rafatosta/gtasks/issues"
        )


if __name__ == "__main__":
    unittest.main()
