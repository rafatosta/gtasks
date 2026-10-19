# Interface adaptativa

## Análise e decisões

A composição anterior usava uma caixa horizontal permanente com barra lateral de
largura mínima fixa. Não havia navegação alternativa para janelas estreitas, o
nome da lista ocupava espaço adicional acima das tarefas e os erros apareciam
somente na barra lateral.

A interface agora usa os componentes nativos da libadwaita:

- `Adw.NavigationSplitView` mantém listas e tarefas lado a lado em janelas largas.
  Até 660sp, um `Adw.Breakpoint` muda para navegação entre páginas. Selecionar ou
  criar uma lista abre as tarefas; o cabeçalho fornece o botão de voltar.
- Cada página tem seu próprio `Adw.ToolbarView` e `Adw.HeaderBar`, com títulos e
  controles de janela administrados pela libadwaita. O cabeçalho das tarefas
  identifica a lista e sua origem. A restauração da última lista também abre a
  página correspondente no modo estreito.
- A janela aceita 360px de largura e 294px de altura mínima. A barra lateral
  varia entre 260sp e 320sp quando expandida. O conteúdo usa `Adw.Clamp` para
  manter a leitura confortável em telas largas.
- Títulos extensos são abreviados no cabeçalho e nas listas. Tarefas, URLs,
  mensagens e instruções de conta quebram linhas. As tarefas têm rolagem
  vertical independente e os controles de inclusão permanecem acima delas.
- Erros aparecem em `Adw.ToastOverlay`, além da mensagem na barra lateral, para
  permanecerem visíveis no modo estreito. Os diálogos de criação e edição
  desabilitam a confirmação quando o nome está vazio. A exclusão mantém a
  confirmação destrutiva e a proteção da última lista de uma conta.
- As tarefas usam `Adw.ActionRow` com caixa de seleção como prefixo:
  altura, espaçamento e estados de interação vêm da libadwaita. Clicar na linha
  abre o menu de opções; somente a caixa de seleção alterna a conclusão. Títulos são texto literal, sem markup.
- As caixas de seleção têm nomes acessíveis associados aos títulos das tarefas.
  Os controles usam os estilos, ícones e tamanhos nativos do tema.

## Opções por tarefa

O menu de cada linha oferece edição de título, detalhes e data, criação de
subtarefas, movimentação entre listas da mesma fonte e exclusão com confirmação.
O editor usa `Adw.Dialog`, `Adw.EntryRow`, `Adw.SwitchRow` e `Gtk.Calendar`, com
rolagem para acomodar janelas estreitas. Erros de salvamento mantêm os campos
preenchidos e permitem tentar novamente. O seletor de destino usa `Adw.ComboRow`.

As linhas mostram um resumo dos detalhes, a data e o nome da tarefa principal
quando aplicável. O vínculo entre subtarefas é preservado na sincronização e no
cache. Estrelas, anexos, horários e recorrência não são simulados como campos
editáveis da API. A data representa o dia programado, não um prazo com horário.

## Validação

Foram abertas janelas com dados temporários e preferências em memória nas
resoluções 360×294, 360×640, 600×500, 900×560 e 1440×900. As três primeiras
recolheram a navegação e as outras mantiveram as duas colunas. Foram verificados seleção,
retorno às listas, nomes longos e tarefas com URLs sem espaços, sem aumento da
largura mínima da janela. Capturas foram inspecionadas para verificar o layout.
A suíte de domínio e persistência continua sendo executada separadamente.

A revisão não substitui testes com leitor de tela, dispositivo de toque ou
fatores de escala distintos; esses cenários não foram validados nesta alteração.

## Referências

- [Scaling & Adaptiveness — GNOME HIG](https://developer.gnome.org/hig/guidelines/adaptive.html)
- [Sidebars — GNOME HIG](https://developer.gnome.org/hig/patterns/nav/sidebars.html)
- [Adw.NavigationSplitView](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/class.NavigationSplitView.html)
