# GTasks — documentação do projeto

> **Estado:** especificação inicial aprovada; aplicação ainda não implementada.  
> **Data-base:** 19 de outubro de 2026.  
> **Repositório:** https://github.com/rafatosta/gtasks

## Finalidade desta documentação

Este diretório registra as decisões técnicas, os limites funcionais, os contratos arquiteturais, as regras de segurança e os critérios de distribuição do **GTasks**. É a referência para implementação, revisão de mudanças e auditoria técnica, não um manual do usuário nem um conjunto de instruções para ferramentas de IA.

As decisões descritas como **normativas** devem orientar a primeira versão. Itens explicitamente assinalados como **dependentes de validação** não são funcionalidades prontas nem garantias de compatibilidade. Alterações posteriores exigem atualização da documentação correspondente no mesmo conjunto de mudanças.

## Documentos

| Documento | Conteúdo |
| --- | --- |
| [01 — Objetivo e escopo](01-visao-e-escopo.md) | Propósito, funcionalidades da primeira versão e exclusões |
| [02 — Arquitetura e organização](02-arquitetura-e-organizacao.md) | MVC orientado a objetos, serviços, Repository/DAO, dependências e árvore do código |
| [03 — Integrações e segurança](03-integracoes-e-seguranca.md) | Google Tasks API, GNOME Online Accounts, autenticação, isolamento e tratamento de erros |
| [04 — Internacionalização](04-internacionalizacao.md) | Idiomas, Gettext, traduções Python/Blueprint e revisão linguística |
| [05 — Construção e distribuição](05-build-e-distribuicao.md) | Meson, recursos GNOME, Flatpak, identificadores, releases e Flathub |
| [06 — Conformidade e qualidade](06-conformidade-e-qualidade.md) | GNOME HIG/Circle, políticas Flathub, testes, auditoria e referências |

## Decisões consolidadas

| Assunto | Decisão |
| --- | --- |
| Produto | **GTasks**, cliente de tarefas nativo para o desktop GNOME |
| Linguagem | Python 3, com PyGObject |
| Interface | GTK4, libadwaita e arquivos declarativos Blueprint |
| Arquitetura | MVC orientado a objetos com camada Service e abstração Repository |
| Persistência/integradores | Contratos independentes do provedor; Google Tasks será a implementação inicial |
| Armazenamento local | Possível implementação SQLite posterior, sem alterar View/Controller |
| Autenticação inicial | GNOME Online Accounts (GOA), **sujeito a prova de integração** |
| Build | Meson + Ninja |
| Traduções | GNU Gettext; inglês como idioma-fonte, português brasileiro como tradução inicial |
| Distribuição | Flatpak como formato principal; Flathub como objetivo, não como publicação realizada |
| Qualidade | Testes automatizados, validação de metadados e revisão humana das alterações |
| Filosofia | Aplicativo enxuto, sem WebView, Electron, serviço residente ou arquitetura de plugins na v1 |

## Decisões ainda sujeitas a validação

1. **GOA + Google Tasks:** comprovar disponibilidade do escopo correto e uso do token dentro do sandbox Flatpak; a interface D-Bus não garante por si só autorização suficiente.
2. **Application ID:** `io.github.rafatosta.GTasks` é o identificador de trabalho anteriormente adotado. O repositório usa `gtasks` em minúsculas; a exigência de correspondência de endereço no Flathub será verificada antes de congelar o ID. Não alterar IDs após publicação sem processo de migração.
3. **Runtime e SDK GNOME:** selecionar uma versão suportada na data de implementação/publicação e mantê-la atualizada; nenhum número de versão é uma obrigação permanente.
4. **Licença:** a opção de projeto é `GPL-3.0-or-later`; formalizar no arquivo `LICENSE` e nos metadados quando o código inicial for criado.
5. **Distribuição universal:** validar alternativa de autenticação caso a dependência de GOA impeça o uso fora do GNOME ou conflite com as políticas do Flathub.

## Registro de auditoria

Este repositório começou vazio; estes documentos representam decisões de arquitetura e governança, **não evidência de que os componentes já foram desenvolvidos**. A cada alteração relevante:

- registrar o motivo e o impacto no documento pertinente;
- manter consistentes interface, contratos de domínio, manifestos, metadados e permissões;
- distinguir comportamento implementado de funcionalidades planejadas;
- vincular, quando pertinente, commits, issues ou PRs;
- revisar novamente os requisitos externos na época de uma candidatura ao GNOME Circle ou publicação no Flathub.

Referências primárias e regras externas estão identificadas em [Conformidade e qualidade](06-conformidade-e-qualidade.md).