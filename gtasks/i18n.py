"""Application-local Gettext helpers; content entered by users is never translated."""
import gettext
import locale
import os
from pathlib import Path

DOMAIN = "gtasks"
_translation: gettext.NullTranslations = gettext.NullTranslations()


def configure(locale_dir: str | Path | None = None, languages: list[str] | None = None) -> None:
    """Load installed catalogs, or an explicit catalog directory for development."""
    global _translation
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        locale.setlocale(locale.LC_ALL, "C.UTF-8")
    directory = str(locale_dir or os.environ.get(
        "GTASKS_LOCALEDIR", Path(__file__).resolve().parents[1] / "locale"
    ))
    gettext.bindtextdomain(DOMAIN, directory)
    gettext.textdomain(DOMAIN)
    _translation = gettext.translation(DOMAIN, directory, languages=languages, fallback=True)


def _(message: str) -> str:
    return _translation.gettext(message)


def ngettext(singular: str, plural: str, count: int) -> str:
    return _translation.ngettext(singular, plural, count)


def pgettext(context: str, message: str) -> str:
    return _translation.pgettext(context, message)


configure()
