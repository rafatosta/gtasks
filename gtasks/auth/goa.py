"""Access GNOME Online Accounts via its public session D-Bus interface."""

from dataclasses import dataclass

from gi.repository import Gio, GLib


_BUS = "org.gnome.OnlineAccounts"
_ROOT = "/org/gnome/OnlineAccounts"
_ACCOUNT = "org.gnome.OnlineAccounts.Account"
_OAUTH2 = "org.gnome.OnlineAccounts.OAuth2Based"


class GoaError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GoogleAccount:
    id: str
    identity: str
    object_path: str

    @property
    def source(self) -> str:
        return f"google:{self.id}"


def _value(value):
    return value.unpack() if isinstance(value, GLib.Variant) else value


class GoaAuthProvider:
    """No credentials are written to disk by GTasks."""

    def _connection(self):
        return Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def list_accounts(self) -> list[GoogleAccount]:
        try:
            reply = self._connection().call_sync(
                _BUS,
                _ROOT,
                "org.freedesktop.DBus.ObjectManager",
                "GetManagedObjects",
                None,
                None,
                Gio.DBusCallFlags.NONE,
                20000,
                None,
            )
            objects = reply.unpack()[0]
        except GLib.Error as error:
            raise GoaError("Não foi possível acessar as Contas Online do GNOME.") from error

        accounts = []
        for path, interfaces in objects.items():
            info = interfaces.get(_ACCOUNT)
            if not info or _OAUTH2 not in interfaces:
                continue
            if _value(info.get("ProviderType")) != "google":
                continue
            if _value(info.get("AttentionNeeded", False)):
                continue
            account_id = _value(info.get("Id")) or path.rsplit("/", 1)[-1]
            identity = _value(info.get("PresentationIdentity")) or str(account_id)
            accounts.append(GoogleAccount(str(account_id), str(identity), path))
        return accounts

    def get_access_token(self, account: GoogleAccount) -> str:
        try:
            reply = self._connection().call_sync(
                _BUS,
                account.object_path,
                _OAUTH2,
                "GetAccessToken",
                None,
                None,
                Gio.DBusCallFlags.NONE,
                30000,
                None,
            )
            token = reply.unpack()[0]
        except GLib.Error as error:
            raise GoaError(
                "Não foi possível obter autorização. Verifique a conta Google nas Contas Online."
            ) from error
        if not token:
            raise GoaError("O GNOME não retornou um token de acesso.")
        return token
