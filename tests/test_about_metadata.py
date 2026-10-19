import struct
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AboutMetadataTest(unittest.TestCase):
    def test_appstream_has_about_details(self):
        xml = ET.parse(
            ROOT / "data" / "io.github.rafatosta.gtasks.metainfo.xml.in"
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

    def test_screenshots_reference_localized_pngs_at_immutable_urls(self):
        xml = ET.parse(ROOT / "data/io.github.rafatosta.gtasks.metainfo.xml.in")
        scenes = xml.findall("screenshots/screenshot")
        self.assertEqual(len(scenes), 3)
        self.assertEqual(scenes[0].get("type"), "default")
        for scene in scenes:
            self.assertTrue(scene.findtext("caption"))
            images = scene.findall("image")
            self.assertEqual(
                {image.get("{http://www.w3.org/XML/1998/namespace}lang") for image in images},
                {None, "pt-BR"},
            )
            for image in images:
                self.assertRegex(image.text, r"^https://raw\.githubusercontent\.com/rafatosta/gtasks/[0-9a-f]{40}/data/screenshots/[^/]+\.png$")
                png = (ROOT / "data/screenshots" / image.text.rsplit("/", 1)[1]).read_bytes()
                self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", png[16:24]),
                                 (int(image.get("width")), int(image.get("height"))))


if __name__ == "__main__":
    unittest.main()
