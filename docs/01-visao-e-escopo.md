# Visão do produto e escopo da primeira versão

**Status:** decisão de produto. **Projeto:** GTasks.

## 1. Propósito

O **GTasks** é um gerenciador de tarefas de desktop desenvolvido para a plataforma GNOME, com interface nativa em GTK4/libadwaita. Sua primeira integração de dados será o **Google Tasks**, sem incorporar o site do Google em WebView e sem criar um serviço próprio de tarefas.

O aplicativo oferece uma experiência coerente com as GNOME Human Interface Guidelines (HIG), respeita as configurações do ambiente e aproveita, quando tecnicamente possível, as contas já cadastradas no **GNOME Online Accounts (GOA)**.

A aplicação não será definida internamente como um mero cliente da API do Google: os modelos, casos de uso e controladores permanecem independentes do provedor. O Google Tasks será apenas a implementação inicial da interface de persistência.

## 2. Princípios de produto

1. **Natividade:** janelas e componentes GTK4/libadwaita, preferencialmente descritos em Blueprint; sem Electron, React ou navegador embutido.
2. **Simplicidade:** interface para tarefas e listas, sem módulos de produtividade alheios ao objetivo.
3. **Portabilidade do domínio:** a troca de Google Tasks por repositório local não altera View ou Controller.
4. **Previsibilidade:** alterações só serão confirmadas ao usuário depois do retorno bem-sucedido da camada de dados, ou devem ser revertidas em caso de falha.
5. **Leveza:** não executar processos residentes, atualizações frequentes ou sincronização offline complexa na primeira versão.
6. **Privacidade:** acesso somente aos recursos indispensáveis; dados de tarefas não devem ser enviados a serviços de telemetria.

## 3. Funcionalidades da v1

O primeiro lançamento funcional inclui:

- Reconhecer uma conta Google configurada no GOA, **desde que os testes de autorização e sandbox confirmem o funcionamento**.
- Exibir listas de tarefas disponíveis na conta selecionada.
- Criar, renomear e excluir listas (com confirmação para operações destrutivas).
- Consultar tarefas pendentes e concluídas, respeitando a paginação e os filtros do provedor.
- Criar, editar e excluir tarefas; editar título e notas, quando suportado.
- Marcar tarefas como concluídas ou pendentes.
- Definir ou remover **datas** das tarefas, respeitando a semântica do provedor.
- Exibir, criar e reorganizar subtarefas, dentro dos limites da API.
- Atualizar o conteúdo ao abrir a aplicação, ao mudar de lista e após operações de escrita.
- Exibir estados de carregamento, erro, ausência de conta e listas vazias.

Esses itens definem o **escopo a implementar**, não funcionalidade já entregue. Alterações de escopo devem ser documentadas antes de sua incorporação.

## 4. Limites conhecidos

A API pública do Google Tasks **não oferece paridade integral** com o aplicativo web oficial. Em particular:

- O campo `due` conserva somente a data; o horário de agendamento não pode ser lido ou gravado por essa API.
- A API não expõe uma interface completa de recorrência como a do aplicativo web.
- Recursos não documentados ou exclusivos de tarefas originadas de outros produtos Google não serão simulados silenciosamente.
- Operações que a API impeça ou considere somente leitura devem aparecer como indisponíveis, não falhar sem explicação.

Referência: [Google Tasks — recurso tasks](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks).

## 5. Fora da primeira versão

Não integrar inicialmente: SQLite para uso diário, sincronização bidirecional offline, serviços residentes, múltiplos provedores, notificações próprias, integração com GNOME Shell, arquitetura de plugins, calendário próprio, suporte a anexos ou edição de recorrências por uma API não documentada.

O projeto estará **preparado estruturalmente** para outro repositório de dados, sem implementar antecipadamente todas essas funções.

## 6. Critério de aceite da primeira versão

A primeira versão só será considerada funcional quando as operações de leitura e escrita da lista e das tarefas puderem ser executadas pelo fluxo **View → Controller → Service → Repository**, com tratamento de erro, autenticação verificável, interface não bloqueante, testes das regras de negócio e geração de um Flatpak de teste.

A publicação no Flathub ou a inclusão no GNOME Circle são objetivos posteriores e não constituem parte automática desse aceite.

## 7. Identidade

- **Nome público:** GTasks.
- **Descrição curta:** Google Tasks for GNOME.
- **Hospedagem:** https://github.com/rafatosta/gtasks.
- **Independência:** projeto comunitário, sem declaração de ser produto oficial do Google ou do GNOME.
- **Licença de código decidida:** GPL-3.0-or-later; formalização depende da inclusão de `LICENSE` antes de distribuir o software.
