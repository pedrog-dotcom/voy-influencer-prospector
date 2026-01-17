# Configuração do GitHub Actions para Prospecção Diária

Este guia explica como configurar o GitHub Actions para executar a prospecção de influenciadores automaticamente todos os dias.

## Passo 1: Configurar os Secrets do Instagram

Para que a integração com o Instagram funcione, você precisa adicionar suas credenciais como secrets no GitHub.

### 1.1 Acesse as configurações do repositório

1. Vá para o repositório: https://github.com/pedrog-dotcom/voy-influencer-prospector
2. Clique em **Settings** (Configurações)
3. No menu lateral, clique em **Secrets and variables** > **Actions**

### 1.2 Adicione os secrets

Clique em **New repository secret** e adicione os seguintes secrets:

| Nome do Secret | Valor |
|----------------|-------|
| `INSTAGRAM_ACCESS_TOKEN` | Seu token de acesso da Graph API do Instagram |
| `INSTAGRAM_USER_ID` | O ID da sua página do Instagram (ex: `17841466934369795`) |

**Importante:** Os valores dos secrets são criptografados e nunca serão exibidos nos logs.

## Passo 2: Adicionar o Workflow

O arquivo de workflow precisa ser adicionado manualmente devido a restrições de permissão.

### 2.1 Crie o arquivo de workflow

1. No repositório, clique em **Add file** > **Create new file**
2. No campo de nome, digite: `.github/workflows/daily_prospection.yml`
3. Cole o conteúdo do arquivo `daily_prospection.yml` que está na pasta `.github/workflows/` do projeto
4. Clique em **Commit changes**

## Passo 3: Verificar a Configuração

### 3.1 Executar manualmente

1. Vá para a aba **Actions** do repositório
2. Clique em **Daily Influencer Prospection** na lista de workflows
3. Clique em **Run workflow**
4. Selecione as opções desejadas e clique em **Run workflow**

### 3.2 Verificar os resultados

Após a execução:
- Os resultados serão salvos na pasta `data/` do repositório
- Um resumo será exibido na página do workflow
- Os arquivos também estarão disponíveis como artefatos para download

## Agendamento Automático

O workflow está configurado para executar automaticamente:

- **Horário:** 9h da manhã (horário de Brasília)
- **Frequência:** Todos os dias
- **Cron:** `0 12 * * *` (12h UTC = 9h BRT)

## Formatos de Saída

A cada execução, os seguintes arquivos são gerados:

| Arquivo | Descrição |
|---------|-----------|
| `prospects_YYYY-MM-DD.json` | Dados completos em JSON |
| `prospects_YYYY-MM-DD.csv` | Planilha para Excel/Sheets |
| `prospects_YYYY-MM-DD.md` | Relatório em Markdown |

## Solução de Problemas

### O workflow falhou

1. Verifique se os secrets estão configurados corretamente
2. Confira os logs na aba Actions para identificar o erro
3. Certifique-se de que o token do Instagram não expirou

### Token do Instagram expirou

Tokens de longa duração do Instagram duram aproximadamente 60 dias. Para renovar:

1. Acesse o Graph API Explorer do Meta
2. Gere um novo token com as permissões necessárias
3. Atualize o secret `INSTAGRAM_ACCESS_TOKEN` no GitHub

### Nenhum influenciador do Instagram encontrado

A API do Instagram só retorna dados de perfis **Business** ou **Creator**. Perfis pessoais não são acessíveis via API.

## Suporte

Se encontrar problemas, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.
