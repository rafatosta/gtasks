# GTasks — documentação do projeto

> **Estado:** desenvolvimento ativo; armazenamento local e integração Google Tasks implementados.  
> **Data-base:** 19 de outubro de 2026.  
> **Repositório:** https://github.com/rafatosta/gtasks

## Finalidade desta documentação

Este diretório registra as decisões técnicas, os limites funcionais, os contratos arquiteturais, as regras de segurança e os critérios de distribuição do **GTasks**. É a referência para implementação, revisão de mudanças e auditoria técnica, não um manual do usuário nem um conjunto de instruções para ferramentas de IA.

As decisões descritas como **normativas** devem orientar a primeira versão. Itens explicitamente assinalados como **dependentes de validação** não são funcionalidades prontas nem garantias de compatibilidade. Alterações posteriores exigem atualização da documentação correspondente no mesmo conjunto de mudanças.

## Documentos

Para executar ou testar o código atual, comece pelo [guia de desenvolvimento](08-desenvolvimento.md). A apresentação do aplicativo fica no [README para usuários](../README.md).

| Documento | Conteúdo |
| --- | --- |
| [01 — Objetivo e escopo](01-visao-e-escopo.md) | Propósito, funcionalidades da primeira versão e exclusões |
| [02 — Arquitetura e organização](02-arquitetura-e-organizacao.md) | Organização fonte → listas → tarefas; componentes reutilizáveis; MVC e Repository/DAO |
| [03 — Integrações e segurança](03-integracoes-e-seguranca.md) | Google Tasks API, GNOME Online Accounts, autenticação, isolamento e tratamento de erros |
| [04 — Internacionalização](04-internacionalizacao.md) | Idiomas, Gettext, traduções Python/Blueprint e revisão linguística |
| [05 — Construção e distribuição](05-build-e-distribuicao.md) | Meson, recursos GNOME, Flatpak, identificadores, releases e Flathub |
| [06 — Conformidade e qualidade](06-conformidade-e-qualidade.md) | GNOME HIG/Circle, políticas Flathub, testes, auditoria e referências |
| [07 — Interface adaptativa](07-interface-adaptativa.md) | Revisão de UX/UI, navegação responsiva, tamanhos e validação visual |
| [08 — Desenvolvimento](08-desenvolvimento.md) | Dependências, execução, testes, capturas e notas de implementação |
| [09 — Preparação para o Flathub](09-preparacao-flathub.md) | Evidências, pendências e etapas da submissão manual |

## Decisões consolidadas

| Assunto | Decisão |
| --- | --- |
| Produto | **GTasks**, cliente de tarefas nativo para o desktop GNOME |
| Linguagem | Python 3, com PyGObject |
| Interface | GTK4/libadwaita com componentes Python; Blueprint é uma opção futura |
| Arquitetura | MVC orientado a objetos com camada Service e abstração Repository |
| Persistência/integradores | Contrato comum e roteamento por fonte (`local`, `google:<id>`) |
| Armazenamento local | SQLite implementado; fonte independente das contas Google |
| Autenticação inicial | GNOME Online Accounts (GOA), integrado e testado no GNOME |
| Build | Meson + Ninja |
| Traduções | GNU Gettext; inglês como idioma-fonte, português brasileiro como tradução inicial |
| Distribuição | Flatpak como formato principal; Flathub como objetivo, não como publicação realizada |
| Qualidade | Testes automatizados, validação de metadados e revisão humana das alterações |
| Filosofia | Aplicativo enxuto, sem WebView, Electron, serviço residente ou arquitetura de plugins na v1 |

## Decisões ainda sujeitas a validação

1. **GOA + Google Tasks:** integração funcional no ambiente de desenvolvimento; requisitos de distribuição em outros desktops ainda dependem de validação.
2. **Application ID:** o código usa `io.github.rafatosta.gtasks`. Validar requisitos finais do Flathub antes de publicar.
3. **Runtime e SDK GNOME:** selecionar uma versão suportada na data de implementação/publicação e mantê-la atualizada; nenhum número de versão é uma obrigação permanente.
4. **Licença:** `GPL-3.0-or-later`, registrada em `LICENSE` e nos metadados AppStream.
5. **Distribuição universal:** validar alternativa de autenticação caso a dependência de GOA impeça o uso fora do GNOME ou conflite com as políticas do Flathub.

## Registro de auditoria

Os documentos registram decisões e estado conhecido do código, sem presumir que funcionalidades futuras já estejam disponíveis. A cada alteração relevante:

- registrar o motivo e o impacto no documento pertinente;
- manter consistentes interface, contratos de domínio, manifestos, metadados e permissões;
- distinguir comportamento implementado de funcionalidades planejadas;
- vincular, quando pertinente, commits, issues ou PRs;
- revisar novamente os requisitos externos na época de uma candidatura ao GNOME Circle ou publicação no Flathub.

Referências primárias e regras externas estão identificadas em [Conformidade e qualidade](06-conformidade-e-qualidade.md).
