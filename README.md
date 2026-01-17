# 🎯 Voy Saúde - Prospecção de Influenciadores

Sistema automatizado de prospecção diária de influenciadores para a marca Voy Saúde, focado em perfis relacionados a emagrecimento, sobrepeso e obesidade.

## 📋 Descrição

Este projeto automatiza a busca e qualificação de influenciadores nas plataformas TikTok e YouTube, com foco em:

- **Nicho**: Emagrecimento, sobrepeso, obesidade, transformação corporal
- **Critério de qualificação**: Taxa de engajamento mínima de 2,5%
- **Volume diário**: 20 influenciadores únicos por dia
- **Controle de duplicatas**: Sistema de histórico para evitar repetições

## 🚀 Funcionalidades

- ✅ Busca automatizada no TikTok e YouTube
- ✅ Cálculo de taxa de engajamento
- ✅ Filtro por palavras-chave relevantes
- ✅ Controle de histórico para evitar duplicatas
- ✅ Exportação em múltiplos formatos (JSON, CSV, Markdown)
- ✅ Geração de relatórios detalhados
- ✅ Execução agendada via GitHub Actions

## 📁 Estrutura do Projeto

```
voy-influencer-prospector/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configurações do projeto
│   ├── models.py           # Modelos de dados
│   ├── history_manager.py  # Gerenciamento de histórico
│   ├── prospector.py       # Lógica principal de prospecção
│   └── report_generator.py # Geração de relatórios
├── data/
│   ├── prospected_influencers.json  # Histórico de influenciadores
│   └── prospects_YYYY-MM-DD.json    # Resultados diários
├── logs/
│   └── prospection_YYYYMMDD.log     # Logs de execução
├── .github/
│   └── workflows/
│       └── daily_prospection.yml    # Pipeline de automação
├── run_prospection.py      # Script principal
├── requirements.txt        # Dependências
└── README.md
```

## 🛠️ Instalação

### Pré-requisitos

- Python 3.11+
- Acesso às APIs do Manus (TikTok, YouTube)

### Instalação Local

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/voy-influencer-prospector.git
cd voy-influencer-prospector

# Instalar dependências
pip install -r requirements.txt
```

## 💻 Uso

### Execução Manual

```bash
# Prospecção padrão (20 influenciadores)
python run_prospection.py

# Especificar quantidade
python run_prospection.py --count 30

# Exportar em todos os formatos
python run_prospection.py --output-format all
```

### Opções de Linha de Comando

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `--count N` | Número de influenciadores a prospectar | 20 |
| `--output-format` | Formato de saída (json, csv, markdown, all) | json |
| `--dry-run` | Executa sem salvar no histórico | False |

## 📊 Formatos de Saída

### JSON
```json
{
  "date": "2026-01-17",
  "influencers": [
    {
      "name": "Nome do Influenciador",
      "primary_platform": "tiktok",
      "profiles": [...],
      "best_engagement_rate": 5.2
    }
  ],
  "total_found": 150,
  "total_qualified": 45
}
```

### CSV
Arquivo com colunas: Nome, Plataforma, Username, URL, Seguidores, Engajamento, etc.

### Markdown
Relatório formatado com tabelas e detalhes de cada influenciador.

## 🔄 Automação (GitHub Actions)

O projeto inclui um workflow do GitHub Actions que executa automaticamente a prospecção diariamente às 9h (horário de Brasília).

### Configuração

1. Faça fork do repositório
2. Configure os secrets necessários no GitHub:
   - `MANUS_API_KEY` (se necessário)
3. O workflow será executado automaticamente

### Execução Manual do Workflow

1. Vá para a aba "Actions" no GitHub
2. Selecione "Daily Influencer Prospection"
3. Clique em "Run workflow"

## 📈 Palavras-chave de Busca

### Português
- emagrecimento, perda de peso, dieta
- obesidade, sobrepeso, reeducação alimentar
- antes e depois, transformação corporal
- ozempic, semaglutida, mounjaro, wegovy

### Inglês
- weight loss journey, obesity transformation
- overweight fitness, before and after weight loss
- body transformation, weight loss motivation

## 🎯 Critérios de Qualificação

| Critério | Requisito |
|----------|-----------|
| Taxa de Engajamento | ≥ 2,5% |
| Plataformas | TikTok, YouTube (Instagram prioritário quando disponível) |
| Nicho | Emagrecimento, saúde, bem-estar |
| Histórico | Não prospectado anteriormente |

## 📝 Logs e Monitoramento

Os logs são salvos em `logs/prospection_YYYYMMDD.log` com informações sobre:
- Início e fim da execução
- Quantidade de perfis encontrados por plataforma
- Erros e exceções
- Tempo de execução

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é proprietário da Voy Saúde. Todos os direitos reservados.

## 📞 Suporte

Para dúvidas ou suporte, entre em contato com a equipe de marketing da Voy Saúde.

---

**Desenvolvido para Voy Saúde** | Prospecção Automatizada de Influenciadores
