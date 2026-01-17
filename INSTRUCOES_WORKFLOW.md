# ⚙️ Instruções para Adicionar o Workflow no GitHub

Para que a automação diária funcione, o arquivo de workflow do GitHub Actions precisa ser adicionado manualmente ao repositório. Siga os passos abaixo:

### 1. Acesse o Repositório

Clique no link abaixo para ir até o repositório que criei para o projeto:

[https://github.com/pedrog-dotcom/voy-influencer-prospector](https://github.com/pedrog-dotcom/voy-influencer-prospector)

### 2. Crie o Arquivo de Workflow

- No repositório, clique em **Add file** > **Create new file**.
- No campo de nome do arquivo, digite o seguinte caminho:

  ```
  .github/workflows/daily_prospection.yml
  ```

  **Atenção:** É muito importante que o caminho e o nome do arquivo estejam exatamente como acima.

### 3. Copie e Cole o Conteúdo do Workflow

- Abra o arquivo `daily_prospection.yml` que está no seu projeto (ou copie o conteúdo abaixo).
- Cole todo o conteúdo no editor de texto do GitHub.

```yaml
name: Daily Influencer Prospection

on:
  # Execução agendada diariamente às 9h (horário de Brasília = 12h UTC)
  schedule:
    - cron: '0 12 * * *'
  
  # Permite execução manual
  workflow_dispatch:
    inputs:
      count:
        description: 'Número de influenciadores a prospectar'
        required: false
        default: '20'
        type: string
      output_format:
        description: 'Formato de saída'
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
        run: |
          mkdir -p data logs
      
      - name: Run prospection
        id: prospection
        run: |
          COUNT=${{ github.event.inputs.count || '20' }}
          FORMAT=${{ github.event.inputs.output_format || 'all' }}
          
          echo "Running prospection with count=$COUNT and format=$FORMAT"
          
          python run_prospection.py --count $COUNT --output-format $FORMAT
          
          # Capturar data do resultado
          DATE=$(date +%Y-%m-%d)
          echo "date=$DATE" >> $GITHUB_OUTPUT
        env:
          PYTHONPATH: ${{ github.workspace }}/src
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: prospection-results-${{ steps.prospection.outputs.date }}
          path: |
            data/prospects_*.json
            data/prospects_*.csv
            data/prospects_*.md
            data/report_*.md
            data/report_*.html
          retention-days: 30
      
      - name: Commit and push results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          
          # Adicionar arquivos de dados e histórico
          git add data/
          git add logs/
          
          # Verificar se há mudanças
          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            DATE=$(date +%Y-%m-%d)
            git commit -m "🎯 Prospecção diária - $DATE"
            git push
          fi
      
      - name: Generate summary
        run: |
          DATE=$(date +%Y-%m-%d)
          
          echo "## 🎯 Prospecção de Influenciadores - $DATE" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          if [ -f "data/prospects_$DATE.json" ]; then
            TOTAL=$(python -c "import json; data=json.load(open('data/prospects_$DATE.json')); print(len(data.get('influencers', [])))")
            FOUND=$(python -c "import json; data=json.load(open('data/prospects_$DATE.json')); print(data.get('total_found', 0))")
            QUALIFIED=$(python -c "import json; data=json.load(open('data/prospects_$DATE.json')); print(data.get('total_qualified', 0))")
            
            echo "| Métrica | Valor |" >> $GITHUB_STEP_SUMMARY
            echo "|---------|-------|" >> $GITHUB_STEP_SUMMARY
            echo "| Total Encontrados | $FOUND |" >> $GITHUB_STEP_SUMMARY
            echo "| Total Qualificados | $QUALIFIED |" >> $GITHUB_STEP_SUMMARY
            echo "| Selecionados | $TOTAL |" >> $GITHUB_STEP_SUMMARY
          else
            echo "⚠️ Arquivo de resultados não encontrado" >> $GITHUB_STEP_SUMMARY
          fi

  notify:
    needs: prospection
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: Notify on failure
        if: needs.prospection.result == 'failure'
        run: |
          echo "⚠️ A prospecção diária falhou!"
          # Aqui você pode adicionar notificação por email, Slack, etc.
      
      - name: Notify on success
        if: needs.prospection.result == 'success'
        run: |
          echo "✅ Prospecção diária concluída com sucesso!"
```

### 4. Salve o Arquivo

- Clique no botão **Commit changes...** no canto superior direito.
- Você pode deixar a mensagem de commit padrão e clicar em **Commit changes** novamente.

Pronto! O workflow estará ativo e a prospecção será executada diariamente às 9h (horário de Brasília). Você também poderá executá-lo manualmente na aba **Actions** do repositório.
