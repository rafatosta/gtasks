# GTasks

Aplicativo nativo de tarefas para GNOME (Python, GTK4 e libadwaita).

- **Neste dispositivo:** listas e tarefas persistidas localmente em SQLite.
- **Google Tasks:** listas da conta Google configurada em **Configurações → Contas Online**, com leitura e gravação diretas na API. Contas distintas são mantidas separadas.
- Acesso remoto exige conexão. Não há cache offline nem transferência automática de tarefas entre fontes.

## Executar no GNOME Builder

Abra ou clone `https://github.com/rafatosta/gtasks.git` no Builder e clique em **Run Project**. Configure sua conta Google no GNOME para testar a integração real.

## Executar pelo Flatpak

```sh
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Sdk//51 org.gnome.Platform//51
flatpak-builder --user --install --force-clean build-dir io.github.rafatosta.gtasks.json
flatpak run io.github.rafatosta.gtasks
```

O GitHub Actions executa os testes e constrói um Flatpak de desenvolvimento. Não publica releases. A integração GOA e as permissões ainda precisam de verificação com uma conta Google real no Fedora.

Arquitetura e decisões: [docs/](docs/). Licença: GPL-3.0-or-later.
