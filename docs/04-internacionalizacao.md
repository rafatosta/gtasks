# Internacionalização e traduções

**Status:** convenção obrigatória desde o primeiro componente de interface.

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
├── ui/*.blp
├── <APP_ID>.desktop.in
└── <APP_ID>.metainfo.xml.in

gtasks/
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
