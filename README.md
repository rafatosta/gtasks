# GTasks

Native Google Tasks client for GNOME. **Initial stage:** a GTK4/libadwaita window and local Flatpak build, without Google integration yet.

## Build and run (Flatpak)

Requires `flatpak`, `flatpak-builder` and the Flathub remote:

```sh
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Sdk//51 org.gnome.Platform//51
flatpak-builder --user --install --force-clean build-dir io.github.rafatosta.gtasks.json
flatpak run io.github.rafatosta.gtasks
```

The **Flatpak** GitHub Actions workflow builds a testable `gtasks.flatpak` artifact on pushes and pull requests; it does not publish a release.

Project decisions: [docs/](docs/). License: GPL-3.0-or-later.
