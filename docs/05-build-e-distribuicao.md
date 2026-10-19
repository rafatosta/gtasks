# Construção, empacotamento e distribuição

**Status:** decisões de empacotamento da v1. Manifestos e artefatos ainda não foram criados.

## 1. Sistema de build

O GTasks usará **Meson + Ninja**, seguindo as convenções das aplicações GTK/GNOME.

Responsabilidades do build:

- Preparar o código Python e instalar o launcher do aplicativo.
- Compilar os arquivos `.blp` (Blueprint) em recursos GTK utilizáveis.
- Compilar e instalar recursos GLib (`.gresource.xml`).
- Instalar ícone principal e ícones simbólicos quando houver.
- Gerar e instalar arquivo `.desktop` e metainfo AppStream a partir dos modelos traduzíveis.
- Instalar esquemas GSettings somente para preferências de aplicação.
- Compilar e instalar catálogos GNU Gettext.
- Permitir a execução de testes locais e em CI.

Dependências diretas serão declaradas de maneira reprodutível. Não baixar dependências dinamicamente durante a construção submetida ao Flathub. Dependências Python fora do runtime devem ter origem rastreável e, quando necessário, ser incorporadas por módulos Flatpak construídos sem rede.

Referência: [GNOME Developer — Getting Started](https://developer.gnome.org/documentation/tutorials/beginners/getting_started.html).

## 2. Arquivos e convenções GNOME

| Arquivo/recurso | Função | Regra |
| --- | --- | --- |
| `meson.build` | Build do projeto e instalação | Fonte da configuração de build |
| `data/ui/*.blp` | Definição visual declarativa | Somente apresentação, não regras de negócio |
| `data/*.gresource.xml` | Registro de recursos | Recursos acessados pela aplicação com prefixo estável |
| `<APP_ID>.desktop` | Entrada no menu de aplicações | Execução, nome, ícone e categorias consistentes |
| `<APP_ID>.metainfo.xml` | Metadados AppStream | Descrição, licença, URL, screenshots e versões reais |
| `<APP_ID>.gschema.xml` | Preferências opcionais | Nunca guardar tokens ou conteúdos sensíveis |
| `data/icons/` | Identidade visual | Ícone original de acordo com GNOME HIG |
| `po/` | Catálogos de tradução | Extração e instalação automatizadas |

O nome do ícone, o arquivo `.desktop`, o AppStream e o ID Flatpak devem referir-se à mesma identidade da aplicação. O pacote não deverá usar `org.gnome.*`, reservado a projetos autorizados, nem alegar ser mantido oficialmente pelo GNOME.

Referências:
- [GNOME — Application ID](https://developer.gnome.org/documentation/tutorials/application-id.html)
- [GNOME HIG — App Icons](https://developer.gnome.org/hig/guidelines/app-icons)
- [Flathub — App ID](https://docs.flathub.org/docs/for-app-authors/requirements#application-id)

## 3. Identificador e variantes

Nome visível: **GTasks**. Repositório de origem: `https://github.com/rafatosta/gtasks`.

O identificador de **trabalho** discutido na fase de concepção é:

- Estável: `io.github.rafatosta.GTasks`.
- Desenvolvimento: `io.github.rafatosta.GTasks.Devel`.

**Verificação obrigatória antes da distribuição pública:** o Flathub estabelece convenções de correspondência do App ID com a URL de repositórios de hospedagem de código. A capitalização de `GTasks` não coincide exatamente com o nome real `gtasks` do repositório. Antes da geração dos arquivos definitivos e da submissão, avaliar o ID em minúsculas (`io.github.rafatosta.gtasks`) ou obter validação da exceção cabível. **Não publicar com um ID indefinido e não mudar IDs depois da distribuição sem plano de migração.**

Até essa decisão, `<APP_ID>` nos exemplos deste documento representa o identificador final a ser fixado.

A variante Devel deve manter preferências e caches isolados da estável. Ela não é automaticamente um canal beta do Flathub.

## 4. Flatpak como formato principal

Serão mantidos manifestos locais de construção para **desenvolvimento** e **release** no repositório upstream, após definição definitiva do App ID e do runtime.

Diretrizes do manifesto:

1. Runtime `org.gnome.Platform` e SDK `org.gnome.Sdk`, em versão suportada no momento do lançamento.
2. Fonte e dependências versionadas/reprodutíveis; sem dependência de baixar arquivos durante o build.
3. `finish-args` com permissões mínimas, justificadas em [Integrações e segurança](03-integracoes-e-seguranca.md).
4. Instalação correta do `.desktop`, metainfo, ícones, schemas e traduções.
5. Separação entre arquivos gerados de build e arquivos-fonte versionados.
6. Build e execução local verificados antes de disponibilizar um release.

O App ID de desenvolvimento deve carregar sufixo `.Devel` e identidade visual diferenciável, evitando que o usuário confunda instalações experimentais com a estável.

## 5. Exemplos de validação local

Os comandos abaixo representam o fluxo esperado **depois que o manifesto for implementado**. Eles não são, no estado atual, instruções executáveis completas para este repositório.

```sh
# Exemplo com o manifesto estável já existente:
flatpak-builder --user --install --force-clean build-dir <APP_ID>.json
flatpak run <APP_ID>

# Inspecionar permissões concedidas:
flatpak info --show-permissions <APP_ID>

# Validações complementares:
desktop-file-validate <arquivo.desktop>
appstreamcli validate <arquivo.metainfo.xml>
```

O CI deverá usar `flatpak-builder-lint` para os checks correspondentes ao manifesto e ao conteúdo construído, quando disponíveis. Publicar uma versão só depois de validá-la no sistema alvo, incluindo integração GOA dentro do sandbox.

## 6. Fluxo de releases

1. Desenvolvimento e revisões na branch principal com testes.
2. Revisão de dependências, permissões, traduções e metadados.
3. Versão identificada por tag Git; lançamento com notas de alterações.
4. Construção testável do Flatpak da versão marcada.
5. Publicação do código-fonte e do histórico do release.
6. Eventual distribuição pelo Flathub após aceitação de sua equipe.

Não haverá builds distribuídos como releases a cada commit, nem manutenção inicial de DEB, RPM ou AppImage. A documentação e o processo de publicação podem evoluir com a maturidade do projeto.

## 7. Distribuição no Flathub

O repositório `rafatosta/gtasks` é o **upstream**. Após aceitação no Flathub, os arquivos de distribuição deverão seguir o modelo de repositório e manutenção requerido pelo serviço.

A candidatura exige, entre outros pontos:
- aplicativo funcional e com histórico verificável de manutenção;
- manifesto válido em local e formato corretos;
- runtime suportado, build reprodutível a partir das fontes e licenças declaradas;
- metainfo AppStream, desktop file, ícone próprio e localização inglesa completa;
- permissões mínimas e integração adequada ao sandbox;
- respeito às políticas de inclusão e de uso de IA vigentes na data da submissão.

**Risco importante:** o Flathub restringe programas que dependem obrigatoriamente de componentes do host ou de um único desktop para funcionalidades essenciais. O acesso exclusivo via GOA deve ser avaliado antecipadamente; uma alternativa de autenticação poderá ser necessária.

**Política de IA vigente (outubro de 2026):** o Flathub proíbe conteúdo gerado ou assistido por IA nos manifestos de submissão. Os manifestos oficiais devem ser elaborados manualmente. Outros materiais gerados/assistidos por IA incorporados ao aplicativo ou ao empacotamento exigem declaração adequada e podem ser avaliados pelos revisores. A revisão humana não cria exceção à proibição específica sobre manifestos.

Referências:
- [Flathub — Requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub — Submission](https://docs.flathub.org/docs/for-app-authors/submission)

## 8. Licenciamento

A licença definida para o código é **GPL-3.0-or-later**, ainda a ser materializada no arquivo `LICENSE` quando o código for incorporado. O `project_license` do AppStream deve corresponder à licença efetiva do projeto, enquanto `metadata_license` usa uma licença adequada aos metadados (normalmente permissiva). Dependências e ícones de terceiros exigem análise de licenças separada.

Esta documentação não equivale a um certificado de publicação ou aprovação GNOME/Flathub.
