# Conformidade, qualidade e trilha de auditoria

**Status:** diretrizes normativas internas e registro das condições externas verificadas em **19/10/2026**.

## 1. GNOME: o que é convenção e o que é requisito

Construir com GTK4/libadwaita não transforma um aplicativo automaticamente em projeto oficial GNOME. A estrutura de diretórios de um repositório **não é imposta de forma única** pelo GNOME.

O GTasks seguirá voluntariamente as práticas da plataforma: GNOME Human Interface Guidelines, recursos da GTK, metadados Desktop/AppStream, ícone adequado, acessibilidade, localização Gettext e integração com o sistema. Meson, Blueprint e organização em `data/`, `po/` e fontes são **decisões do GTasks**, alinhadas a convenções observadas no ecossistema, não certificações.

### GNOME Circle

O GNOME Circle distingue projetos independentes que utilizam a plataforma e passam por critérios de qualidade e manutenção. Sua participação não é pressuposta:

- O projeto deve ter licença aprovada pela OSI, utilizar ou estender a plataforma e atender aos critérios do comitê.
- Não é necessário hospedar o código no GitLab do GNOME.
- O projeto não poderá usar marcas ou textos que sugiram ser software oficial do GNOME antes de autorização.
- A candidatura demanda revisão humana e não é garantida.

**Situação temporal:** em 29/05/2026, o comitê anunciou suspensão temporária de novas candidaturas; atualização publicada em 07/10/2026 indicava trabalho para reduzir a fila, ainda sem garantia de reabertura. Reavaliar o estado no momento de uma candidatura. Também há política de IA para novas submissões ao Circle; consultar a versão vigente antes de submetê-las.

Referências:
- [GNOME Circle](https://circle.gnome.org/)
- [Política de software GNOME (arquivo)](https://wiki.gnome.org/Foundation%282f%29SoftwarePolicy.html)
- [Circle — comunicado de maio de 2026](https://blogs.gnome.org/sophieh/2026/05/29/updates-from-the-circle-committee/)
- [Circle — atualização de outubro de 2026](https://blogs.gnome.org/psauberz/2026/10/07/fellowship-update-2026-10-07/)
- [GNOME HIG](https://developer.gnome.org/hig/)

## 2. Políticas Flathub

A publicação no Flathub é uma **etapa futura** com análise própria. As políticas atuais incluem:

- Conteúdo funcional, manutenção demonstrável e histórico de desenvolvimento consistente.
- Construção das fontes e dependências reproduzível, sem downloads no build do serviço.
- Runtime ainda suportado, metadados válidos, licenças corretas e traduções de qualidade.
- Permissões estritamente necessárias e uso de portais quando exigido.
- Restrições a aplicativos cujo funcionamento essencial dependa de componentes do host ou de um ambiente gráfico específico.
- Processo de envio por submissão e revisão, independente do repositório upstream.

A versão de desenvolvimento não é substituta de uma release estável para a submissão inicial. Um projeto recém-criado pode não atender imediatamente às exigências de histórico/manutenção, ainda que compile corretamente.

### Material assistido por IA

O mantenedor pode usar ferramentas assistidas por IA como apoio à implementação **com controle das decisões e revisão humana**. Para um eventual envio ao Flathub, as regras atuais devem ser respeitadas independentemente dessa revisão:

1. Declarar materiais gerados ou assistidos por IA incorporados ao aplicativo ou ao empacotamento, identificando as partes e a extensão aproximada.
2. Não incluir conteúdo gerado ou assistido por IA nos **manifestos submetidos ao Flathub**; a preparação do manifesto oficial é manual.
3. Não automatizar por agente de IA a criação ou as interações da pull request de submissão ao Flathub.
4. Confirmar políticas atualizadas na data de publicação.

Essas regras são obrigações externas de um canal de distribuição, não restrições arbitrárias de arquitetura do GTasks. A documentação técnica pode registrar decisões e apresentar origem e revisão de alterações para fins de auditabilidade.

Referências:
- [Flathub — Requirements e política de IA](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub — Submission](https://docs.flathub.org/docs/for-app-authors/submission)

### Dependência do host para Google Tasks

A integração com Google Tasks usa o serviço de sessão D-Bus
`org.gnome.OnlineAccounts`, fornecido pelo GNOME Online Accounts (GOA) no host.
O Flatpak permite acesso a esse serviço, mas não o inclui. Uma conta Google
precisa estar configurada e autorizada no GOA. As listas e tarefas locais têm
armazenamento próprio e não dependem desse serviço.

Essa separação oferece funcionalidade local sem Google, mas não comprova, por
si só, conformidade com as regras sobre aplicações dependentes do host ou de
ambientes específicos. Antes da submissão, verificar o Flatpak em uma sessão
sem GOA e em outro ambiente gráfico: inicialização, criação e edição de listas
e tarefas locais, persistência e tratamento da indisponibilidade da integração
Google. Verificar também a integração em um host com GOA autorizado.
Esses cenários continuam pendentes de comprovação para a submissão; a decisão
de inclusão cabe aos revisores do Flathub, caso a caso.

## 3. Critérios internos de qualidade

As seguintes validações devem fazer parte do desenvolvimento:

| Área | Evidência esperada |
| --- | --- |
| Código Python | Revisão de arquitetura, Ruff e tipagem nas interfaces principais |
| Domínio | `pytest` para criação, edição, conclusão e regras de listas/tarefas |
| Repository | Mocks/in-memory nos casos de uso; testes específicos da conversão JSON e HTTP |
| Assincronia | Interface não bloqueia; erros de rede e cancelamentos são tratados |
| Traduções | Compilação Gettext e inspeção manual em inglês e pt_BR |
| Desktop | `desktop-file-validate`, validação AppStream, GSettings e recursos |
| Flatpak | Build local, `flatpak-builder-lint` e teste com permissões mínimas |
| Segurança | Nenhum token ou conteúdo privado nos logs; testes de autenticação revogada |
| Interface | Testes de janela estreita, empty/loading/error states e acessibilidade básica |
| Releases | Tag, changelog/notas, versão rastreável e atualização do metainfo |

A lista representa critérios a **implementar** no CI ou na revisão técnica. Não há pipeline executável no repositório inicial.

## 4. Padrões de revisão

- Alterações que afetem contratos devem preservar isolamento entre MVC, Service e Repository e atualizar os testes.
- Novas permissões de sandbox exigem justificativa escrita em [Integrações e segurança](03-integracoes-e-seguranca.md).
- Novos provedores exigem implementação do contrato e testes; nunca condicionar Widgets ao provedor.
- Novos textos visíveis precisam de marcação Gettext e revisão da tradução brasileira.
- Novas dependências devem ter finalidade, licença, compatibilidade com runtime e impacto no Flatpak verificados.
- Mudanças de identidade, App ID, licença, fluxo de autenticação ou dados persistidos exigem justificativa documentada.
- Desativar validações automatizadas exige registro do motivo e solução de acompanhamento.
- Revisão humana confirma legibilidade, segurança e aderência ao escopo, independentemente de como os trechos foram redigidos.

## 5. Auditoria e mudanças de decisão

Os documentos em `docs/` são a **linha de base**. Uma alteração arquitetural significativa deverá modificar o documento correspondente na mesma PR/commit; quando necessário, incluir um pequeno registro de decisão com:

- contexto e problema;
- decisão tomada e alternativas consideradas;
- consequências/compatibilidade;
- necessidade de migração e de testes;
- referência ao commit ou PR.

É indispensável separar **decisão aprovada**, **implementação concluída** e **comprovação por testes**. Nenhum documento deve sugerir que uma integração, release ou conformidade já foi verificada quando ainda for apenas intenção.

## 6. Fontes externas para revalidação

- [GNOME Developer Documentation](https://developer.gnome.org/documentation/)
- [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/)
- [GNOME Online Accounts — OAuth2Based](https://gnome.pages.gitlab.gnome.org/gnome-online-accounts/iface.OAuth2Based.html)
- [Blueprint — traduções](https://gnome.pages.gitlab.gnome.org/blueprint-compiler/translations.html)
- [Google Tasks REST](https://developers.google.com/workspace/tasks/reference/rest)
- [Flatpak — permissões de sandbox](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Flathub — requisitos](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub — submissão](https://docs.flathub.org/docs/for-app-authors/submission)

*Revisar estas fontes no marco de cada release importante e, especialmente, antes de qualquer submissão externa.*
