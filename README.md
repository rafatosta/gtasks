# GTasks

Aplicativo nativo de tarefas para GNOME (Python, GTK4 e libadwaita).

- **Neste dispositivo:** listas e tarefas persistidas localmente em SQLite.
- **Google Tasks:** listas da conta Google configurada em **Configurações → Contas Online**, com leitura e gravação diretas na API. Contas distintas são mantidas separadas.
- O aplicativo mantém um cache SQLite para **consultar listas e tarefas Google offline**, atualizado em segundo plano ao iniciar e ao clicar em atualizar. Criar e alterar tarefas Google ainda exige conexão; não há fila de edições offline nem transferência automática entre fontes.

## Executar no GNOME Builder

Abra ou clone `https://github.com/rafatosta/gtasks.git` no Builder e clique em **Run Project**. Configure sua conta Google no GNOME para testar a integração real.

Se uma compilação anterior encerrar com `Settings schema 'io.github.rafatosta.gtasks' is not installed`, use **Rebuild Project** no Builder e execute novamente. A instalação Meson compila os esquemas GSettings no prefixo do aplicativo (`/app` no Flatpak). Não é necessário apagar as preferências nem o diretório de dados do aplicativo.

## Executar pelo Flatpak

```sh
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Sdk//51 org.gnome.Platform//51
flatpak-builder --user --install --force-clean build-dir io.github.rafatosta.gtasks.json
flatpak run io.github.rafatosta.gtasks
```

O GitHub Actions executa os testes e constrói um Flatpak de desenvolvimento. Não publica releases. A integração GOA e as permissões ainda precisam de verificação com uma conta Google real no Fedora.

## Opções das tarefas

No menu **⋮** de cada tarefa é possível:

- Editar título e detalhes e definir ou remover uma **data**, com calendário e
  botões **Hoje** e **Amanhã**.
- Adicionar uma subtarefa e consultar sua relação com a tarefa principal.
- Mover a tarefa para outra lista da **mesma conta** ou entre listas locais.
- Excluir a tarefa e suas subtarefas, após confirmação.

Os detalhes, a data e a relação entre subtarefas são preservados no banco e no
cache offline. Alterações nas contas Google exigem conexão. O editor mantém o
texto digitado caso ocorra um erro ao salvar. Os bancos existentes são atualizados
sem apagar listas ou tarefas.

A data do campo `due` da API é o dia programado, sem horário. Não é um prazo
completo como os recursos adicionais do site. Estrelas, edição de recorrência e
anexos ficam fora desta implementação porque a API pública não oferece campos
editáveis equivalentes. Os detalhes de tarefas atribuídas pelo Google permanecem
somente para leitura; a confirmação de exclusão informa o efeito na origem.

Referências: [campos de tarefas](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks)
e [movimentação entre listas](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks/move).

## Atalhos de teclado

Abra **Menu principal → Atalhos de teclado** para consultar os atalhos.

| Atalho | Ação |
| --- | --- |
| Ctrl+Q | Sair do aplicativo |
| Ctrl+W | Fechar o diálogo aberto ou a janela |
| Ctrl+, | Abrir preferências |
| Ctrl+? ou Ctrl+F1 | Mostrar atalhos de teclado |
| Ctrl+R ou F5 | Atualizar listas e tarefas |
| F10 | Abrir o menu principal na página de listas |
| Alt+← | Voltar às listas no modo estreito |
| Esc | Fechar diálogo ou menu |

A janela de atalhos usa `Adw.ShortcutsDialog`, disponível na libadwaita 1.8 ou
mais recente (incluída no runtime GNOME 51 do projeto).

## Preferências

Abra **Menu principal → Preferências** ou pressione **Ctrl+,**. O GTasks salva as escolhas com GSettings:

- Sincronização das contas Google na inicialização (ativada por padrão).
- Atualização periódica enquanto o aplicativo estiver aberto (desativada, 5, 15, 30 ou 60 minutos; padrão: 15).
- Exibição de tarefas concluídas (ativada por padrão).
- Restauração da última lista selecionada (ativada por padrão).

O cache offline permanece ativo para que as listas Google já sincronizadas possam ser consultadas sem conexão. As alterações nas contas Google continuam exigindo internet.

Arquitetura e decisões: [docs/](docs/). Licença: GPL-3.0-or-later.
