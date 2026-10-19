# AppStream screenshots

Three native application scenes are provided in English and Brazilian Portuguese:
`tasks` (lists and subtasks), `editor` (notes and date), and `compact` (adaptive layout).
The PNG files retain the original window transparency, rounded corners, and shadows.
They are captured at the desktop's 2× scale, without cropping or overlays.

All tasks, lists, and the account `alex@example.org` are fictional. Google Tasks is
represented by an in-memory repository; no account connection is required. Settings,
cache, schemas, and translation catalogs are isolated from the installed application.

To regenerate on a GNOME desktop with X11/XWayland, the application's Python/GI
dependencies, Pillow, gettext, and the en_US/pt_BR UTF-8 locales installed:

```sh
python3 tools/capture_screenshots.py --language en_US
python3 tools/capture_screenshots.py --language pt_BR
```

The helper captures only the demonstration window using its X11 window ID. It
decodes the native premultiplied pixel format to PNG while retaining its alpha.
Commit new images first, then update the immutable commit URLs in the metainfo.
The referenced commit must be pushed to GitHub before publishing the package.
