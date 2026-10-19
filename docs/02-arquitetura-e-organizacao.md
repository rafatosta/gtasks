# Arquitetura e organização dos dados

**Status:** arquitetura adotada e implementada no GTasks. Esta seção descreve o funcionamento atual; não é uma proposta.

## 1. Modelo de organização

Toda lista pertence a uma **fonte de dados**; toda tarefa pertence a uma **lista**.

```text
GTasks
├── Fonte "local" (este dispositivo)
│   ├── Lista "Pessoal"
│   │   ├── Tarefa A
│   │   └── Tarefa B
│   └── Lista "Compras"
└── Fontes online (uma por conta)
    ├── Fonte "google:<id-conta-1>"
    │   ├── Lista "Trabalho"
    │   │   └── Tarefa C
    │   └── Lista "Projetos"
    └── Fonte "google:<id-conta-2>"
        └── Lista "Estudos"
            └── Tarefa D
```

**A fonte local equivale a uma conta local do ponto de vista da interface**, mas não é uma conta autenticada. Cada conta Google cadastrada no GNOME Online Accounts (GOA) é uma fonte própria. Duas fontes podem ter listas com o mesmo nome ou o mesmo ID fornecido pelo backend sem se confundirem.

Os identificadores atuais são:

| Fonte | Identificador | Persistência |
| --- | --- | --- |
| Este dispositivo | `local` | SQLite no diretório de dados do aplicativo |
| Conta Google | `google:<id-da-conta-GOA>` | Google Tasks API, com autenticação via GOA |

O identificador é uma chave interna de roteamento, não um token de autenticação. Novos provedores poderão adotar outros prefixos sem mudar o modelo de tarefa ou a interface.

## 2. Entidades e identidade

- `TaskList`: `id`, `name`, `source`. O par **(`source`, `id`)** identifica a lista entre todos os provedores.
- `Task`: `id`, `list_id`, `title`, `completed`. A identidade completa é **(`source`, `list_id`, `id`)**; a fonte é herdada da lista à qual a tarefa pertence.
- `GoogleAccount`: identificação e caminho D-Bus de uma conta GOA, usados apenas na integração/autenticação. Não substitui `TaskList` ou `Task`.

A camada de domínio não contém objetos GTK, SQL, JSON de API ou tokens OAuth. As listas locais são mantidas no SQLite, e as listas Google são consultadas pela API; as cópias das listas e tarefas Google são mantidas no cache SQLite, separadas por fonte, lista e tarefa. O índice em memória serve apenas para a navegação.

Há **cache offline para leitura**, não edição offline: ao iniciar, o GTasks mostra dados já armazenados e atualiza as contas em segundo plano, com uma consulta por conta e snapshots completos por lista. Uma falha preserva o último snapshot válido. Escritas na conta Google continuam sendo feitas na API e, após sucesso, atualizam o cache. Não há fila de modificações offline nem sincronização bidirecional com as listas locais.

## 3. Componentes visuais compartilhados

A mesma classe de apresentação serve às fontes locais e às contas Google:

- `SourceListGroup` (em `views/list_sidebar.py`) recebe `source_id`, nome exibido e callbacks; cria o cabeçalho, botão de nova lista e linhas de listas daquela fonte.
- `ListSidebar` cria uma instância para `local` e uma para **cada** conta Google; mantém a seleção exclusiva entre grupos e exibe o estado das contas.
- `TaskPanel` (em `views/task_panel.py`) exibe e edita tarefas da lista selecionada, sem conhecer o Repository.
- `MainWindow` compõe os componentes e encaminha eventos ao Controller.

A aparência pode indicar dispositivo/nuvem pelo identificador da fonte, mas criar, selecionar e concluir tarefas utiliza **o mesmo fluxo**. Uma mudança de provedor não exige outra classe de widget.

## 4. MVC, Service e Repository/DAO

```text
SourceListGroup / ListSidebar / TaskPanel (GTK4/libadwaita)
                       |
                   MainWindow
                       |
                 TaskController
                       |
                  TaskService
                       |
                RepositoryRegistry
                     /       \
          SQLiteTaskRepository  GoogleTasksRepository (uma por conta)
                |                       |
              SQLite              Google Tasks API
```

O contrato `TaskRepository` (`repositories/base.py`, `Protocol`) reúne as operações básicas de listas e tarefas. Os adaptadores `sqlite.py`, `google.py` e `memory.py` implementam o contrato; `memory.py` é usado principalmente em testes. Não existe camada DAO paralela: **Repository cumpre esse papel**.

O `RepositoryRegistry` registra as fontes, encontra o adaptador pelo `source` e carrega o índice de listas remotas do cache SQLite. `RemoteTaskCache` armazena snapshots em tabelas separadas das listas locais, sem guardar tokens. O `TaskService` valida operações. O `TaskController` mantém a seleção e executa operações remotas fora do loop GTK; o resultado volta à thread gráfica antes de atualizar a interface. A montagem das dependências ocorre em `application.py`.

Exemplo de roteamento ao adicionar tarefa:

```text
Usuário seleciona lista (source="google:123", id="lista-A")
    → TaskPanel emite "adicionar"
    → MainWindow / TaskController / TaskService
    → Registry.resolve("google:123")
    → GoogleTasksRepository da conta correspondente
```

Para `source="local"`, o fluxo é idêntico, mas o registro resolve `SQLiteTaskRepository`.

## 5. Estrutura implementada

```text
gtasks/
├── application.py
├── main.py
├── models/
│   ├── task.py
│   ├── task_list.py
│   └── google_account.py
├── views/
│   ├── main_window.py
│   ├── list_sidebar.py    # SourceListGroup e ListSidebar
│   └── task_panel.py
├── controllers/
│   └── task_controller.py
├── services/
│   └── task_service.py
├── repositories/
│   ├── base.py
│   ├── registry.py
│   ├── cache.py
│   ├── sqlite.py
│   ├── google.py
│   └── memory.py
└── auth/
    └── goa.py
```

## 6. Regras de evolução

1. Cada fonte tem seu próprio adaptador e identificador; não misturar tarefas entre contas.
2. A interface nunca consulta HTTP ou SQLite diretamente; a troca do adaptador ocorre no Registry.
3. Uma nova funcionalidade compartilhada deve entrar no contrato e nos testes de seus adaptadores; recursos exclusivos de um provedor exigem capacidades explícitas.
4. O cache offline é apenas de leitura; não implementar fila de escritas ou sincronização bidirecional sem regras explícitas de conflito.
5. Não bloquear o loop principal GTK com chamadas de rede ou manipular widgets em threads de trabalho.
6. Testar seleção, criação e conclusão de tarefas nas fontes local e Google após mudanças no roteamento.

## 7. Preferências persistentes

O GTasks usa `Gio.Settings` com o esquema `io.github.rafatosta.gtasks`, instalado via Meson no diretório padrão de esquemas GLib. O diálogo é um `Adw.PreferencesDialog` separado da `MainWindow`.

- `sync-on-startup` controla a sincronização automática ao abrir (não impede a descoberta das contas e dos dados em cache).
- `sync-interval` controla o temporizador de atualização durante a execução (0, 5, 15, 30 ou 60 minutos). Não instala serviço residente nem sincroniza quando o aplicativo está fechado.
- `show-completed` filtra apenas a apresentação; não apaga tarefas concluídas do SQLite ou Google.
- `restore-last-list` recupera a lista e a fonte salvas pelas chaves `last-source` e `last-list-id`. Caso a lista já não exista, nenhuma seleção é forçada.

As preferências são persistidas no backend do GSettings e não devem ser confundidas com as tabelas locais nem com o cache de contas Google.
