# Desenvolvimento e execução local

Este guia reúne as instruções técnicas de execução, testes e manutenção. Para
conhecer o aplicativo e seu uso, consulte o [README principal](../README.md).

## Dependências

O aplicativo usa Python 3 com PyGObject, GTK 4, libadwaita ≥ 1.8,
GtkSourceView ≥ 5.10 e libspelling ≥ 0.4.10. O build usa Meson ≥ 1.0,
Ninja e GNU Gettext. O manifesto Flatpak declara o runtime e as dependências
empacotadas; consulte `meson.build` e `io.github.rafatosta.gtasks.json`
ao preparar o ambiente.

## Testes

Execute na raiz do repositório:

```sh
python3 -m compileall -q gtasks
python3 -m unittest discover -s tests -v
```

Os testes de interface são opcionais e precisam das dependências gráficas e de
uma sessão com display:

```sh
GTASKS_TEST_GTK=1 python3 -m unittest discover -s tests -v
```

## Capturas e metadados

Veja [como gerar as capturas](../data/screenshots/README.md). As imagens usam
dados fictícios e configurações temporárias. O metainfo aponta para um commit
fixo: ao substituir as imagens, faça primeiro o commit dos PNGs e depois atualize
as URLs. Envie os commits ao GitHub para disponibilizar as imagens publicamente.

Para validar o metainfo com as traduções:

```sh
msgfmt --xml --template=data/io.github.rafatosta.gtasks.metainfo.xml.in -d po -o /tmp/gtasks.metainfo.xml
appstreamcli validate --no-net /tmp/gtasks.metainfo.xml
```

## Executar no GNOME Builder

Abra ou clone `https://github.com/rafatosta/gtasks.git` no Builder e use
**Run Project**. Configure uma conta Google nas Contas Online para testar a
integração real. As capturas de demonstração não validam essa integração.

Se uma compilação anterior informar `Settings schema 'io.github.rafatosta.gtasks'
is not installed`, use **Rebuild Project** e execute novamente. A instalação
Meson compila os esquemas GSettings no prefixo do aplicativo (`/app` no Flatpak).
Não é necessário apagar preferências ou dados.

## Construir e executar o Flatpak

```sh
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Sdk//51 org.gnome.Platform//51
flatpak-builder --user --install --force-clean build-dir io.github.rafatosta.gtasks.json
flatpak run io.github.rafatosta.gtasks
```

A versão do runtime acima corresponde ao manifesto atual. O GitHub Actions
executa os testes e constrói um Flatpak de desenvolvimento; o workflow não cria
releases. A integração GOA e as permissões devem ser verificadas com uma conta
Google real no ambiente de distribuição.

## Persistência e sincronização

As listas locais usam SQLite. As contas Google são isoladas por fonte e mantêm
um cache SQLite de listas e tarefas para consulta offline. O cache preserva
notas, datas e hierarquia; não implementa uma fila de escritas offline.
Alterações remotas exigem conexão. Migrações dos bancos existentes preservam
listas e tarefas. As preferências ficam em GSettings.

A data `due` é tratada como dia, sem horário. Estrelas, recorrência e anexos não
possuem campos editáveis equivalentes na integração implementada. Tarefas
atribuídas pelo Google têm restrições de edição, e a exclusão informa o efeito
na origem.

Referências da integração:
[campos de tarefas](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks)
e [movimentação entre listas](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks/move).

## Traduções

O idioma-fonte é inglês americano, com português brasileiro em `po/pt_BR.po`.
O manifesto usa `separate-locales: false` para incluir os catálogos no arquivo
`.flatpak` independente, sem uma extensão `.Locale`. As datas usam o formato
regional do sistema. Nomes de listas e conteúdo de tarefas não são traduzidos.

Veja [Internacionalização](04-internacionalizacao.md) para extração, atualização
e testes dos catálogos.

## Correção ortográfica e atalhos

A correção usa GtkSourceView 5 e libspelling 0.4.10. O manifesto inclui
libspelling; os dicionários vêm dos idiomas instalados do runtime GNOME.
Na instalação nativa, instale o dicionário desejado (por exemplo,
`hunspell-pt-BR` no Fedora). Quando o idioma selecionado não está disponível,
o corretor usa o padrão disponível no sistema. O idioma e a ativação são
compartilhados pelos campos abertos e persistidos nas preferências.

Os campos de entrada usam uma ponte com o buffer de correção. Mudanças nessa
integração devem ser verificadas também nos testes GTK opcionais.

A janela de atalhos usa `Adw.ShortcutsDialog`, disponível a partir da
libadwaita 1.8. A lista de atalhos para o usuário fica no
[README](../README.md#keyboard-shortcuts).
