# Integrações, autenticação e segurança

**Status:** decisões de integração e segurança; compatibilidade GOA/Flatpak pendente de validação prática.

## 1. Fontes de dados

Na primeira versão, o GTasks usa a **Google Tasks REST API v1** como implementação do contrato Repository. Sua URL de serviço é `https://tasks.googleapis.com`.

Operações previstas:

| Entidade | Operações | Observações |
| --- | --- | --- |
| Listas | listar, criar, atualizar, excluir | Recursos `tasklists` da API |
| Tarefas | listar, criar, atualizar, excluir | Recursos `tasks` da API |
| Ordem/hierarquia | mover tarefa, alterar relação pai/filho | Utilizar endpoint `tasks.move` e suas restrições |
| Estado | concluir, reabrir, consultar pendentes/concluídas | Traduzir estados do provedor para o domínio |

O adaptador deve implementar paginação, limites da API e erros HTTP; não poderá apresentar listas parciais como se estivessem completas. A utilização de parâmetros que ocultam tarefas concluídas, excluídas ou atribuídas precisa ser explícita.

Referências:
- [Google Tasks REST v1](https://developers.google.com/workspace/tasks/reference/rest)
- [Recurso tasks](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks)
- [Método tasks.list](https://developers.google.com/workspace/tasks/reference/rest/v1/tasks/list)

### Semântica e limites

A data agendada retornada no campo `due` deve ser modelada como **data**, sem horário artificial. O Google informa que a parte de hora é descartada; não há API pública para leitura/escrita do horário de agendamento. Recorrência e outros recursos não expostos não podem ser simulados como se fossem suportados pelo provedor.

O adaptador também respeitará operações indisponíveis para tarefas atribuídas ou de origem externa. A aplicação não deverá apagar ou alterar silenciosamente itens de outra origem.

## 2. Autenticação

A estratégia inicial é o **GNOME Online Accounts (GOA)**:

1. Descobrir contas Google disponíveis no serviço GOA.
2. Selecionar a conta e obter token de acesso pelo método `OAuth2Based.GetAccessToken` quando disponibilizado.
3. Verificar, com chamada real à API, se o token tem escopo e autorização suficientes para Google Tasks.
4. Utilizar o token apenas durante sua validade; reobtê-lo quando necessário, sem bloquear a UI.
5. Se autenticação/escopo falhar, apresentar erro compreensível sem coletar senha do Google.

A interface OAuth2Based existe na API pública do GOA, mas **a existência do método não comprova que o token contém o escopo Tasks em toda versão/configuração**. A disponibilidade do escopo e a comunicação D-Bus de dentro do Flatpak são critérios explícitos da prova de conceito.

Referência: [GOA — OAuth2Based](https://gnome.pages.gitlab.gnome.org/gnome-online-accounts/iface.OAuth2Based.html).

### Separação de responsabilidades

- `auth/goa.py`: identificação de conta e obtenção de credenciais temporárias.
- `repositories/google.py`: API HTTP, cabeçalhos autorizados, paginação e mapeamento para modelos.
- `services/task_service.py`: fluxos e validações de negócio.
- Views/Controllers: nenhuma referência a OAuth, token, `Authorization` ou endpoint REST.

A estratégia de autenticação deve ser substituível sem alterar os contratos de tarefa. Um OAuth independente poderá ser criado **somente se necessário**, por exemplo para garantir portabilidade fora do GNOME ou viabilizar uma candidatura ao Flathub.

## 3. Segurança de tokens e dados

- Utilizar HTTPS; não desabilitar validação TLS.
- Não registrar tokens, cabeçalhos `Authorization`, segredos OAuth, títulos ou notas de tarefas em logs de diagnóstico.
- Não salvar token em texto puro, GSettings, banco SQLite, relatórios ou arquivos exportados.
- Não solicitar senha Google diretamente no aplicativo.
- Não enviar conteúdos de tarefas para analítica, métricas ou infraestrutura própria na v1.
- Informar erros sem expor payloads sensíveis.
- Minimizar informações em memória e descartar referências a credenciais assim que possível.
- Permitir alteração/revogação de acesso por meio do provedor de identidade.
- Antes de habilitar várias contas, isolar resultados e identificadores por conta para evitar mistura de tarefas.

GSettings é adequado a **preferências não sensíveis**, como última lista selecionada ou dimensões da janela, e não a segredos.

## 4. Permissões Flatpak — matriz de decisão

A concessão de permissões ocorre no manifesto durante a fase de empacotamento. Não confundir permissões **planejadas** com permissões já testadas.

| Permissão/integração | Status | Justificativa |
| --- | --- | --- |
| `--share=network` | Necessária para Google | Chamadas HTTPS ao serviço Tasks |
| `--socket=wayland` | Prevista | Interface gráfica no Wayland |
| `--socket=fallback-x11` | Avaliar | Compatibilidade quando Wayland não estiver disponível |
| `--talk-name=org.gnome.OnlineAccounts` | **Validar** | Acesso estritamente nomeado ao serviço GOA por D-Bus |
| XDG Desktop Portals | Utilizar quando aplicável | Abrir URLs, arquivos e outras integrações mediadas |
| `--filesystem=home` ou `host` | **Não conceder** | A v1 não precisa de acesso amplo aos arquivos do usuário |
| `--socket=session-bus` / `system-bus` | **Não conceder** | Evitar acesso D-Bus indiscriminado |
| Microfone, câmera, dispositivos, áudio | **Não conceder** | Incompatíveis com o escopo funcional |

A permissão específica de GOA deve ser confirmada em execução, inspecionando o tráfego D-Bus e os requisitos do runtime. Se existir portal adequado, priorizá-lo. O manifesto está sujeito à revisão de permissões exigida pelo Flathub.

Referências:
- [Flatpak — Sandbox permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Flathub — Requirements](https://docs.flathub.org/docs/for-app-authors/requirements)

## 5. Erros, robustez e consistência

- Tratar timeout, perda de rede, token expirado, resposta incompleta, `429`/quota e erros `5xx`.
- Distinguir erro temporário de remoção/permissão negada.
- Evitar repetição infinita; usar recuo limitado quando apropriado.
- Alterações destrutivas requerem confirmação e tratamento explícito de falha.
- Recarregar resultados após escritas que impactem ordem/hierarquia, conforme necessário.
- Não interpretar uma resposta vazia decorrente de falha como lista sem tarefas.
- Não prometer modo offline nem persistência local de tarefas na primeira versão.

## 6. Pontos de verificação antes de publicar

1. Obtenção de token GOA em instalação GNOME real.
2. Chamada bem-sucedida a `tasklists.list` e a `tasks.list`.
3. Leitura e escrita dentro do Flatpak usando somente permissões mínimas.
4. Comportamento quando conta não existe, token é revogado ou rede está indisponível.
5. Revisão de eventual dependência obrigatória do host: o Flathub restringe aplicativos dependentes de serviços externos do ambiente para suas funções essenciais.
6. Validação de ausência de segredos nos logs, artefatos de CI e mensagens de erro.

Os itens acima representam **critérios de teste pendentes**. Não devem ser documentados como concluídos antes da execução e registro dos resultados.
