# Arquitetura e organização do código

**Status:** decisão arquitetural **normativa** para a primeira versão.

## 1. Estilo adotado

O GTasks seguirá **programação orientada a objetos**, arquitetura **MVC** e separação adicional entre serviços de domínio, autenticação e acesso aos dados. A abstração de armazenamento adotada chama-se **Repository**, cumprindo a função de um DAO sem duplicar camadas.

A arquitetura não é uma recomendação opcional: é a estrutura contratual do projeto.

```text
View (GTK4/libadwaita e Blueprint)
                |
                v
          Controller
                |
                v
         TaskService
                |
                v
  TaskRepository / TaskListRepository (contratos)
            /            \
           v              v
GoogleTasksRepository  SqliteTasksRepository*
           |
 Google Tasks API

* Implementação SQLite prevista, não integrante da v1.
```

A autenticação é implementada por um serviço separado (`AuthProvider`) injetado no adaptador Google. A composição das dependências é realizada na inicialização da aplicação, não dentro da View.

## 2. Responsabilidades das camadas

| Camada | Responsabilidade | Não deve fazer |
| --- | --- | --- |
| **Model** | Representar `Task`, `TaskList`, estados e valores do domínio | Conhecer JSON, GTK, OAuth ou SQLite |
| **View** | Apresentar estados e capturar interação GTK/libadwaita | Fazer HTTP, consultar banco, aplicar lógica de negócio |
| **Controller** | Traduzir ações da View em chamadas de serviço e aplicar estados de apresentação | Construir URLs, SQL ou gerir tokens |
| **Service** | Coordenar casos de uso, validar operações e políticas de domínio | Depender de widgets GTK ou de detalhes do Google |
| **Repository** | Abstrair persistência/listagem/movimentação de entidades | Expor `dict`/JSON específico do provedor aos serviços |
| **Adapter** | Implementar Repository por Google Tasks ou SQLite | Definir regras da interface |
| **AuthProvider** | Resolver identidade e token para integradores que exigem autenticação | Expor token às Views |

**Direção de dependência:** classes internas conhecem modelos e contratos abstratos; implementações externas dependem desses contratos, jamais o inverso.

## 3. Estrutura de referência — código da v1

A árvore a seguir define a **organização dos arquivos a criar**. Não descreve arquivos já existentes neste momento.

```text
gtasks/
├── .github/
│   └── workflows/
│       └── ci.yml
├── build-aux/
│   └── flatpak/                  # auxiliares, se necessários
├── data/
│   ├── icons/
│   ├── ui/
│   │   ├── main-window.blp
│   │   └── task-row.blp
│   ├── io.github.rafatosta.GTasks.desktop.in
│   ├── io.github.rafatosta.GTasks.metainfo.xml.in
│   ├── io.github.rafatosta.GTasks.gschema.xml
│   ├── gtasks.gresource.xml
│   └── meson.build
├── gtasks/
│   ├── __init__.py
│   ├── main.py
│   ├── application.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py
│   │   └── task_list.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   └── task_row.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── task_controller.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── google.py
│   └── auth/
│       ├── __init__.py
│       └── goa.py
├── po/
│   ├── LINGUAS
│   ├── POTFILES.in
│   ├── pt_BR.po
│   └── meson.build
├── tests/
├── docs/
├── io.github.rafatosta.GTasks.json
├── io.github.rafatosta.GTasks.Devel.json
├── meson.build
├── meson.options
├── pyproject.toml
├── LICENSE
└── README.md
```

**Observação:** `repositories/sqlite.py` e um eventual `sync_service.py` serão adicionados apenas quando suas funcionalidades forem implementadas. Subdiretórios com um único componente não justificam novas subcamadas.

Os nomes com App ID são de **trabalho** até validação final do identificador, conforme [Construção e distribuição](05-build-e-distribuicao.md).

## 4. Contratos de domínio e persistência

Os contratos Repository devem ser expressos com `Protocol` ou `ABC`, usando entidades tipadas. Devem ser definidos **do ponto de vista das operações necessárias ao domínio**, não espelhando cegamente endpoints REST.

Exemplos de responsabilidades:

- `TaskListRepository`: listar, criar, renomear e excluir listas.
- `TaskRepository`: listar tarefas de uma lista, criar, atualizar, excluir, concluir/reabrir e alterar sua posição ou hierarquia quando suportado.
- `TaskService`: validar dados, coordenar operações e traduzir erros técnicos em erros compreensíveis ao usuário.
- `AuthProvider`: disponibilizar uma credencial temporária ao integrador remoto, sem alterar o contrato dos casos de uso.

Tarefas devem ser identificadas no contexto de uma lista **e de uma conta/provedor**, prevenindo colisões de IDs quando houver múltiplas fontes. Datas de tarefas são objetos de data sem horário inventado. Recursos opcionais do backend devem ser representados por capacidades explícitas, e não por suposições.

Não se deve implementar um segundo `DAO` em paralelo ao `Repository`; seria duplicação desnecessária.

## 5. Injeção de dependência

A montagem das dependências ocorre em `application.py` ou em módulo de composição dedicado:

```python
# Exemplo conceitual; as interfaces definitivas serão fixadas na implementação.
auth = GoaAuthProvider()
repository = GoogleTasksRepository(auth_provider=auth)
service = TaskService(tasks=repository)
controller = TaskController(service=service)
window = MainWindow(controller=controller)
```

O adaptador pode ser substituído futuramente por um repositório local sem alteração na View ou no Controller. Não é necessário utilizar biblioteca de injeção de dependência.

## 6. Assincronia e estado de interface

- Toda chamada de rede deve ser **assíncrona** e não bloquear o loop principal do GTK.
- Integrações com callbacks/GLib devem devolver resultados ao contexto principal antes de atualizar widgets.
- Controladores devem gerenciar carregamento, conclusão, cancelamento e erros visíveis.
- Requisições concorrentes para listas diferentes não podem sobrescrever o estado da lista atualmente selecionada.
- Atualizações otimistas só são permitidas com reversão bem definida em caso de falha.
- Operações de escrita não podem ser repetidas automaticamente se houver risco de duplicação sem mecanismo seguro de idempotência.

## 7. Normalização, erros e testes

Os adaptadores convertem payloads para modelos; formatos `snake_case`/`camelCase`, códigos HTTP, IDs de conta, tokens e detalhes OAuth não atravessam a fronteira Repository.

As exceções da integração devem ser convertidas em categorias explícitas (falha de autenticação, indisponibilidade de rede, permissão negada, item inexistente, conflito, quota/limite). As mensagens ao usuário são localizáveis; detalhes técnicos permanecem nos logs **sem segredos**.

Testes do Service/Controller utilizam implementações em memória ou mocks dos contratos. Testes dos adaptadores verificam conversão de payload, paginação, falhas e permissões. Testes de interface são complementares; não substituem os testes unitários.

## 8. Diferença entre Repository e sincronização

Substituir o repositório ativo por outro **não equivale** a sincronizar duas bases. Se futuramente o GTasks mantiver cópias local e remota simultâneas, haverá `SyncService` próprio, com regras para conflitos, tombstones, cursores e reconciliação. Nada disso deve ser antecipado na v1.

## 9. Restrições de arquitetura

1. Nenhuma View ou Controller acessará diretamente `GoogleTasksRepository`, `GoaAuthProvider`, HTTP ou SQL.
2. Nenhum Model importará GTK, libadwaita, Google SDK ou camada de persistência.
3. Nenhuma credencial será persistida em arquivos de configuração próprios sem justificativa e revisão de segurança.
4. Componentes devem manter responsabilidade única, nomes claros e tipagem explícita nas fronteiras.
5. Evitar abstrações prematuras, serviços residentes, plugins ou um framework próprio de eventos.
6. Mudanças nos contratos exigem testes e atualização simultânea desta especificação.
