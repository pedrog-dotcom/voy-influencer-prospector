# Configuração do GitHub Actions para Prospecção Diária

Este guia explica como configurar o GitHub Actions para executar a prospecção de influenciadores automaticamente todos os dias.

## Passo 1: Configurar os Secrets

Para que a prospecção funcione corretamente, você precisa adicionar suas credenciais como secrets no GitHub.

### 1.1 Acesse as configurações do repositório

1. Vá para o repositório: https://github.com/pedrog-dotcom/voy-influencer-prospector
2. Clique em **Settings** (Configurações)
3. No menu lateral, clique em **Secrets and variables** > **Actions**

### 1.2 Adicione os secrets

Clique em **New repository secret** e adicione os seguintes secrets:

| Nome do Secret | Descrição | Obrigatório |
|----------------|-----------|-------------|
| `OPENAI_API_KEY` | API Key do OpenAI para análise de perfis com IA | ✅ Sim |
| `INSTAGRAM_ACCESS_TOKEN` | Token de acesso da Graph API do Instagram | Recomendado |
| `INSTAGRAM_USER_ID` | ID da página do Instagram (ex: `17841466934369795`) | Recomendado |

**Importante:** Os valores dos secrets são criptografados e nunca serão exibidos nos logs.

### 1.3 Obter API Key do OpenAI

Se você ainda não tem uma API Key do OpenAI:

1. Acesse https://platform.openai.com/
2. Faça login ou crie uma conta
3. Vá em **API Keys** no menu
4. Clique em **Create new secret key**
5. Copie a chave gerada e adicione como secret `OPENAI_API_KEY`

## Passo 2: Criar o Workflow

### 2.1 Criar o arquivo de workflow

1. No repositório, clique em **Add file** > **Create new file**
2. No campo de nome, digite: `.github/workflows/daily_prospection.yml`
3. Cole o conteúdo abaixo:

```yaml
name: Daily Influencer Prospection

on:
  schedule:
    - cron: '0 12 * * *'
  workflow_dispatch:
    inputs:
      count:
        description: 'Numero de influenciadores a prospectar'
        required: false
        default: '20'
        type: string
      output_format:
        description: 'Formato de saida'
        required: false
        default: 'all'
        type: choice
        options:
          - json
          - csv
          - markdown
          - all

env:
  PYTHON_VERSION: '3.11'

jobs:
  prospection:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Create directories
        run: mkdir -p data logs

      - name: Run prospection
        id: prospection
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          INSTAGRAM_ACCESS_TOKEN: ${{ secrets.INSTAGRAM_ACCESS_TOKEN }}
          INSTAGRAM_USER_ID: ${{ secrets.INSTAGRAM_USER_ID }}
        run: |
          COUNT=${{ github.event.inputs.count || '20' }}
          FORMAT=${{ github.event.inputs.output_format || 'all' }}
          echo "Running prospection with count=$COUNT and format=$FORMAT"
          python run_prospection.py --count $COUNT --output-format $FORMAT
          echo "date=$(date +%Y-%m-%d)" >> $GITHUB_OUTPUT

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: prospection-results-${{ steps.prospection.outputs.date }}
          path: |
            data/prospects_*.json
            data/prospects_*.csv
            data/prospects_*.md
          retention-days: 30

      - name: Commit and push results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Prospeccao diaria - $(date +%Y-%m-%d)"
            git push
          fi

      - name: Generate summary
        run: |
          DATE=$(date +%Y-%m-%d)
          echo "## Prospeccao de Influenciadores - $DATE" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          if [ -f "data/prospects_$DATE.json" ]; then
            python3 -c "
          import json
          with open('data/prospects_$DATE.json') as f:
              data = json.load(f)
          print('| Metrica | Valor |')
          print('|---------|-------|')
          print(f'| Total Encontrados | {data.get(\"total_found\", 0)} |')
          print(f'| Total Qualificados | {data.get(\"total_qualified\", 0)} |')
          print(f'| Selecionados | {len(data.get(\"influencers\", []))} |')
          " >> $GITHUB_STEP_SUMMARY
          else
            echo "Arquivo de resultados nao encontrado" >> $GITHUB_STEP_SUMMARY
          fi

  notify:
    needs: prospection
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Notify on failure
        if: needs.prospection.result == 'failure'
        run: echo "A prospeccao diaria falhou!"

      - name: Notify on success
        if: needs.prospection.result == 'success'
        run: echo "Prospeccao diaria concluida com sucesso!"
```

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

## O que a Análise com IA faz

A cada execução, o sistema:

1. **Busca perfis** no Instagram, TikTok e YouTube
2. **Analisa cada perfil com GPT** para determinar:
   - Se é uma pessoa real ou página comercial
   - Se tem sobrepeso/obesidade ou está em jornada de emagrecimento
   - Score de autenticidade (0-100)
   - Potencial de parceria (0-100)
3. **Filtra e prioriza** pessoas reais com alto potencial
4. **Gera relatórios** em múltiplos formatos

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
3. Certifique-se de que a API Key do OpenAI está válida
4. Verifique se o token do Instagram não expirou

### API Key do OpenAI inválida

1. Acesse https://platform.openai.com/api-keys
2. Verifique se a chave está ativa
3. Se necessário, gere uma nova chave
4. Atualize o secret `OPENAI_API_KEY` no GitHub

### Token do Instagram expirou

Tokens de longa duração do Instagram duram aproximadamente 60 dias. Para renovar:

1. Acesse o Graph API Explorer do Meta
2. Gere um novo token com as permissões necessárias
3. Atualize o secret `INSTAGRAM_ACCESS_TOKEN` no GitHub

### Nenhum influenciador do Instagram encontrado

A API do Instagram só retorna dados de perfis **Business** ou **Creator**. Perfis pessoais não são acessíveis via API.

### Poucos perfis recomendados

Se a IA está filtrando muitos perfis:
- Verifique os logs para entender os motivos
- Ajuste o `min_partnership_potential` em `prospector_v3.py` se necessário

## Custos

### OpenAI API

A análise com IA usa o modelo `gpt-4.1-mini`, que tem custo por token:
- Aproximadamente $0.01-0.05 por execução diária (20 perfis)
- Monitore seu uso em https://platform.openai.com/usage

### GitHub Actions

- Repositórios públicos: gratuito
- Repositórios privados: 2.000 minutos/mês gratuitos

## Suporte

Se encontrar problemas, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.
