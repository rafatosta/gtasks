# Preparação para submissão ao Flathub

Registro interno de preparação, atualizado em 21/10/2026. Este documento foi
redigido com assistência de IA. Não é manifesto oficial, declaração para envio
nem texto de pull request.

## Situação conhecida

| Item | Situação |
| --- | --- |
| Identificador | `io.github.rafatosta.gtasks` |
| Release estável | `v0.1.0` publicado no GitHub |
| MetaInfo | Versão 0.1.0, descrição, imagens, licenças, classificação etária e tradução gettext presentes; validação AppStream local passou nesta conversa |
| Desktop e tradução | Validações locais passaram nesta conversa |
| Testes | Última execução local: 47 aprovados e 5 testes GTK ignorados |
| CI | Build e testes do commit `1b5bda5c718666d5c8269af5699333a3caaf7efc` passaram; não substitui validar o pacote oficial |
| Uso sem contas | Mantenedor confirmou funcionamento correto sem contas criadas |
| Uso sem GOA | Ainda precisa ser comprovado com o serviço indisponível; ausência de contas não equivale a ausência do serviço |
| Manifesto local | Usa fonte de tipo `dir`; não é o manifesto oficial para submissão |
| Linter do manifesto local | Última execução nesta conversa acusou `finish-args-x11-without-ipc` |
| Pacote oficial | Build, instalação, teste e linter do repositório gerado pendentes |
| Licenças instaladas | Arquivo LICENSE existe no upstream; comprovar instalação das licenças do app e módulos no pacote oficial |

Release: https://github.com/rafatosta/gtasks/releases/tag/v0.1.0

A existência da primeira versão estável não comprova o histórico de manutenção e
uso real exigido para inclusão. Esses critérios continuam sujeitos aos revisores.

## Preparação manual pelo mantenedor

1. Conferir a política vigente e a procedência do empacotamento anterior.
2. Elaborar pessoalmente o manifesto oficial sem geração ou assistência de IA.
   As fontes devem ser públicas e reproduzíveis, correspondendo à versão estável.
   Não copiar material assistido por IA para o manifesto oficial.
3. Resolver a pendência de permissões indicada pelo linter e verificar instalação
   de licenças, dependências e runtime suportado.
4. Construir e instalar a partir desse manifesto, testar a aplicação instalada e
   validar o repositório produzido. Guardar os resultados referentes à versão
   exata a submeter.
5. Completar o levantamento de materiais assistidos por IA. O registro parcial em
   `06-conformidade-e-qualidade.md` precisa incluir também o histórico anterior,
   as notas da versão e este documento, conforme os materiais distribuídos.
   Não declarar a estimativa parcial como abrangente de todo o projeto.
6. Criar o fork de `flathub/flathub`, incluindo a branch `new-pr`, e criar uma
   branch de trabalho a partir dela. Adicionar somente os arquivos necessários
   ao empacotamento; não incluir binários compilados.
7. Redigir pessoalmente commits, declaração e descrição; abrir a PR pela interface
   do GitHub contra `new-pr`, preservando o template. Responder pessoalmente aos
   revisores. A política proíbe gerar esses textos e interações com agentes de IA.

## Comandos de validação da documentação oficial

Executar no diretório do empacotamento manual. Substituir `<manifest>` pelo
caminho do manifesto elaborado pelo mantenedor.

```sh
flatpak run --command=flathub-build org.flatpak.Builder --install <manifest>
flatpak run io.github.rafatosta.gtasks
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest <manifest>
flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo
```

Os comandos pressupõem `org.flatpak.Builder` e o remoto Flathub configurados.
O último comando pressupõe que o build gerou o repositório no diretório `repo`.
Erros devem ser resolvidos ou tratados pelo processo de exceção documentado.

## Verificação funcional do pacote final

- Sem contas: criar, editar, concluir e excluir tarefas e listas; reiniciar e
  confirmar persistência. Repetir no pacote oficial mesmo após o teste já relatado.
- Sem serviço GOA: confirmar acesso às tarefas locais e tratamento compreensível
  da indisponibilidade do Google, inclusive ao atualizar.
- Com conta Google autorizada: verificar carregamento, alterações e atualização.
- Sem internet: verificar operações locais e consulta ao cache Google existente.
- Conferir inglês e português brasileiro, janela estreita e funcionamento nos
  sistemas de janelas anunciados pelo pacote.

## Depois da aprovação

Ativar 2FA no GitHub e aceitar o convite para o repositório de distribuição no
prazo indicado pelo Flathub. Após publicação, solicitar a verificação no Developer
Portal usando a conta GitHub proprietária de `rafatosta/gtasks`.

## Referências

- https://docs.flathub.org/docs/for-app-authors/submission
- https://docs.flathub.org/docs/for-app-authors/requirements
- https://docs.flathub.org/docs/for-app-authors/requirements#generative-ai-policy
- https://docs.flathub.org/docs/for-app-authors/linter
- https://docs.flathub.org/docs/for-app-authors/verification
