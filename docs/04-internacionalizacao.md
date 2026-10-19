# Internacionalização e traduções

**Status:** implementado com Gettext, catálogo `pt_BR`, integração Meson e metadados localizados.

## 1. Política de idiomas

- **Idioma-fonte:** inglês (`en`), inclusive mensagens de erro, `.desktop`, metainfo e textos do aplicativo.
- **Primeira tradução:** português brasileiro (`pt_BR`).
- **Sistema:** GNU Gettext integrado ao Meson.
- **Seleção:** respeitar o locale do usuário pelo mecanismo padrão GNOME/GLib; não introduzir seletor próprio na primeira versão.
- **Evolução:** outros idiomas serão adicionados em arquivos `.po`, sem copiar componentes ou telas.

Inglês é a origem dos `msgid`; não devem existir textos em inglês escritos em duplicidade para cada idioma.

## 2. Estrutura adotada

```text
po/
├── LINGUAS
├── POTFILES.in
├── pt_BR.po
└── meson.build

data/
├── <APP_ID>.desktop.in
└── <APP_ID>.metainfo.xml.in

gtasks/
├── i18n.py
└── ... arquivos Python com strings marcadas
```

O arquivo `LINGUAS` lista os idiomas de tradução disponíveis. `POTFILES.in` identifica as fontes extraídas. `meson.build` registra o domínio Gettext do aplicativo e deve integrar a etapa de instalação.

Os arquivos `.po` são a **fonte de tradução versionada**. Os arquivos `.mo` são produzidos na construção/instalação e não devem ser mantidos manualmente no repositório.

## 3. Convenções de implementação

Em Python, strings exibidas ao usuário devem ser marcadas com `gettext`/`_` conforme a inicialização do domínio de tradução da aplicação. Mensagens técnicas internas não precisam ser traduzidas quando nunca forem exibidas.

Em Blueprint, marcar títulos, descrições, botões, estados vazios, avisos e acessibilidade com `_("English text")`. Se houver ambiguidade de contexto, usar `C_(context, text)` conforme documentação do compilador Blueprint.

Exemplo de Blueprint:

```blueprint
Label {
  label: _("My tasks");
}
```

Exemplo de Python (esquemático):

```python
title = _("Tasks could not be loaded")
```

Textos com plural devem empregar recursos de pluralização, em vez de concatenar sufixos manualmente. Datas, números e horários devem seguir formatação de locale, não formatação fixa da interface.

Referência: [Blueprint — Translations](https://gnome.pages.gitlab.gnome.org/blueprint-compiler/translations.html).

## 4. Metadados traduzíveis

A infraestrutura de construção deve gerar versões localizadas de:

- Nome, descrição e palavras-chave do arquivo `<APP_ID>.desktop`.
- Campos apropriados do AppStream `<APP_ID>.metainfo.xml`.
- Conteúdo visível de diálogos, avisos e descrições de acessibilidade.

O identificador do aplicativo, chaves internas, URLs, nomes D-Bus e parâmetros da API **não** são traduzidos.

## 5. Fluxo de manutenção

1. Desenvolver a funcionalidade com texto-fonte em inglês e marcas de tradução.
2. Atualizar o catálogo Gettext quando houver novos textos.
3. Revisar o `pt_BR.po` no mesmo ciclo da mudança.
4. Compilar e validar os catálogos, verificando placeholders, plurais e contextos.
5. Testar manualmente a interface em `en` e `pt_BR` nas telas alteradas.
6. Em mudanças extensas, verificar truncamento, labels acessíveis e disposição de botões.

Se uma tradução estiver incompleta, a aplicação deve recorrer naturalmente ao texto-fonte, sem deixar chaves ou identificadores técnicos visíveis.

## 6. Contribuições futuras

O uso de Weblate ou plataforma de tradução poderá ser incorporado quando o volume de traduções justificar. Nenhum serviço externo de tradução será obrigatório na v1.

A política do Flathub exige localização inglesa completa e rejeita traduções automáticas de baixa qualidade. O projeto mantém **revisão humana** da terminologia e do sentido, independentemente de ferramentas de apoio usadas na edição.

Referência: [Flathub — Localisation policy](https://docs.flathub.org/docs/for-app-authors/requirements#localisation-policy).

## 7. Implementação e validação

`gtasks/i18n.py` configura o locale e o domínio `gtasks`, com helpers explícitos
`_`, `ngettext` e `pgettext`. O launcher gerado por Meson informa o diretório de
catálogos instalado. Em execução a partir das fontes, `GTASKS_LOCALEDIR` permite
apontar para catálogos compilados sem alterar o idioma salvo no desktop.

O template `po/gtasks.pot` e a tradução `po/pt_BR.po` são versionados. Para
atualizar as mensagens em um ambiente com as dependências de construção:

```sh
meson compile -C _build gtasks-pot
meson compile -C _build gtasks-update-po
msgfmt --check --check-format -o /tmp/gtasks.mo po/pt_BR.po
```

Para testar a tradução sem instalar o aplicativo:

```sh
mkdir -p _build/locale/pt_BR/LC_MESSAGES
msgfmt -o _build/locale/pt_BR/LC_MESSAGES/gtasks.mo po/pt_BR.po
GTASKS_LOCALEDIR="$PWD/_build/locale" LANGUAGE=pt_BR LC_ALL=pt_BR.UTF-8 _build/gtasks
GTASKS_LOCALEDIR="$PWD/_build/locale" LANGUAGE=en_US LC_ALL=en_US.UTF-8 _build/gtasks
```

O locale indicado precisa estar instalado para validar também o formato das
datas. Sem um locale disponível, o aplicativo usa `C.UTF-8`; sem um catálogo de
tradução, usa o inglês de origem. O idioma do corretor ortográfico é independente
do idioma da interface.

O Meson gera `.desktop` e AppStream a partir dos templates `.in` e instala os
catálogos em `share/locale`. Os `.mo` não são versionados. Nomes próprios, IDs,
URLs, nomes das listas e textos das tarefas não são traduzidos automaticamente.
Mensagens parametrizadas são traduzidas por inteiro antes de inserir os valores.

Os testes verificam seleção de idioma, fallback, cobertura dos textos marcados,
placeholders, preservação de conteúdo e geração de metadados em inglês e
português. A compilação/instalação dos arquivos `po/meson.build` e
`data/meson.build` foi validada em um projeto Meson isolado. A interface foi
verificada nos dois idiomas, em larguras de 360 e 900 pixels. Isso não substitui
uma compilação integral do Flatpak.

## 8. Traduções no bundle independente

O artefato `gtasks.flatpak` do GitHub Actions é distribuído como um arquivo único.
O manifesto de desenvolvimento define `separate-locales: false` para manter os
catálogos em `/app/share/locale` dentro desse próprio arquivo. Sem essa opção,
o flatpak-builder separa as traduções em uma extensão `.Locale`, que não acompanha
a instalação de um bundle contendo apenas o aplicativo.

O CI verifica depois da construção que o catálogo `pt_BR/LC_MESSAGES/gtasks.mo`
está presente no pacote principal, não é um link para uma extensão separada e
traduz `Save` para `Salvar`. Isso complementa os testes do catálogo nas fontes.
A correção exige construir e instalar um novo bundle; não altera arquivos
`.flatpak` já baixados.

A configuração foi verificada com a construção e exportação de um Flatpak mínimo
local: o catálogo permaneceu como arquivo regular no pacote principal e sua
tradução foi lida com sucesso. Esse teste não recompilou o GTasks completo nem
substituiu a instalação existente do usuário.
