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
  abre o menu de opções; o duplo clique abre o editor. Somente a caixa de
  seleção alterna a conclusão. O clique simples aguarda o intervalo de duplo
  clique configurado no desktop antes de abrir o menu. Títulos são texto literal, sem markup.
- As caixas de seleção têm nomes acessíveis associados aos títulos das tarefas.
  Os controles usam os estilos, ícones e tamanhos nativos do tema.

## Contornos, sombras e estados vazios

As listas de tarefas usam `Gtk.ListBox` com `boxed-list` e linhas
`Adw.ActionRow`, os componentes nativos da libadwaita. A área de rolagem contém
uma caixa com margens internas de 6px: isso evita recortar o contorno e a sombra
do cartão quando ele toca os limites do viewport. As margens externas da janela
não substituem esse espaço dentro da área que faz o recorte.

O campo multilinha de detalhes usa `Gtk.TextView` com a classe oficial `inline`
dentro de um cartão. Assim, o fundo retangular do editor não cobre os cantos
arredondados do cartão. Bordas, sombras e cores continuam a cargo do tema.

O estado sem tarefas usa `Adw.StatusPage` em uma página separada, sem uma lista
vazia com aparência de cartão. O mesmo componente comunica estados de ausência
de seleção, carregamento ou indisponibilidade de cópia local.

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

## Correção ortográfica

O `Gtk.TextView` dos detalhes usa `GtkSource.Buffer` e
`Spelling.TextBufferAdapter`, com sublinhado e menu de correções nativos. O menu
oferece sugestões, idioma e ações sobre o dicionário. Um gesto de contexto atualiza
a posição da palavra antes de abrir as sugestões, conforme o exemplo oficial da
libspelling 0.4. A classe `inline` preserva a aparência do cartão.

A verificação e o idioma são persistidos com GSettings; a preferência de escrita
controla a mesma opção oferecida pelo menu de contexto. A escolha inicial é
`pt_BR`, com o padrão do provedor como alternativa se o dicionário não estiver
instalado. Não há substituição automática nem envio do texto a um serviço remoto.
A correção também atende a todos os campos de uma linha: inclusão rápida de
tarefas, títulos no editor, nomes de listas e títulos de subtarefas. Esses campos
mantêm `Gtk.Entry` e `Adw.EntryRow`. Um buffer auxiliar da libspelling verifica o
texto e fornece o menu nativo; os sublinhados são aplicados por atributos Pango ao
`Gtk.Text` interno, preservando o desenho do componente. Os índices Pango usam
bytes UTF-8, enquanto as seleções e os limites dos campos usam caracteres.

As sugestões alteram apenas o trecho correspondente. Edições e ações de desfazer
continuam sincronizadas com o buffer auxiliar. Uma sugestão maior que o limite de
um campo não pode deixar esse buffer diferente do texto efetivamente aceito.
Idioma e ativação são compartilhados em tempo real entre todos os campos.
Um idioma indisponível pode ser normalizado para `None` pela libspelling; esse
valor nunca é consultado como código de idioma nem gravado em GSettings. Sem um
dicionário utilizável, os campos continuam editáveis e a inicialização não falha.

Os testes GTK opcionais cobrem os dois componentes de uma linha, acentos,
sugestões, edição, desfazer, limites e preferências compartilhadas. Para executá-los
em uma sessão gráfica com as dependências e o dicionário português instalados:
`GTASKS_TEST_GTK=1 python3 -m unittest discover -s tests -p test_spellcheck_ui.py`.

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
- [Classes de estilo da libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.9/style-classes.html)
- [Adw.NavigationSplitView](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/class.NavigationSplitView.html)
