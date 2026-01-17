# 🎯 Voy Saúde - Prospecção de Influenciadores

Sistema automatizado de prospecção diária de influenciadores para a marca [Voy Saúde](https://www.voysaude.com.br/), focado em perfis relacionados a emagrecimento, sobrepeso e obesidade.

## 📋 Descrição

Este projeto automatiza a busca e qualificação de influenciadores nas plataformas **Instagram** (prioritário), **TikTok** e **YouTube**, com foco em:

- **Nicho**: Emagrecimento, sobrepeso, obesidade, transformação corporal
- **Critério de qualificação**: Taxa de engajamento mínima de 2,5%
- **Volume diário**: 20 influenciadores únicos por dia
- **Controle de duplicatas**: Sistema de histórico para evitar repetições

## 🚀 Funcionalidades

- ✅ Busca automatizada no **Instagram** (via Graph API)
- ✅ Busca automatizada no **TikTok** e **YouTube**
- ✅ Cálculo de taxa de engajamento
- ✅ Filtro por palavras-chave relevantes
- ✅ Controle de histórico para evitar duplicatas
- ✅ Exportação em múltiplos formatos (JSON, CSV, Markdown)
- ✅ Geração de relatórios detalhados
- ✅ Execução agendada via GitHub Actions (diariamente às 9h)

## 📊 Plataformas Suportadas

| Plataforma | Prioridade | Método de Busca |
|------------|------------|-----------------|
| Instagram | 1 (Alta) | Graph API - Business Discovery |
| TikTok | 2 (Média) | API de busca de vídeos |
| YouTube | 3 (Baixa) | API de busca de canais |

## 📁 Estrutura do Projeto

```
voy-influencer-prospector/
├── src/
│   ├── __init__.py
│   ├── config.py               # Configurações do projeto
│   ├── models.py               # Modelos de dados
│   ├── history_manager.py      # Gerenciamento de histórico
│   ├── instagram_prospector.py # Prospecção do Instagram
│   ├── prospector_v2.py        # Lógica principal de prospecção
│   └── report_generator.py     # Geração de relatórios
├── data/
│   ├── prospected_influencers.json  # Histórico de influenciadores
│   └── prospects_YYYY-MM-DD.*       # Resultados diários
├── logs/
│   └── prospection_YYYYMMDD.log     # Logs de execução
├── .github/
│   └── workflows/
│       └── daily_prospection.yml    # Pipeline de automação
├── run_prospection.py      # Script principal
├── requirements.txt        # Dependências
├── SETUP_GITHUB.md         # Instruções de configuração do GitHub
└── README.md
```

## 🛠️ Instalação

### Pré-requisitos

- Python 3.11+
- Token de acesso da Graph API do Instagram (opcional, mas recomendado)

### Instalação Local

```bash
# Clonar o repositório
git clone https://github.com/pedrog-dotcom/voy-influencer-prospector.git
cd voy-influencer-prospector

# Instalar dependências
pip install -r requirements.txt
```

### Configuração do Instagram

Para habilitar a prospecção do Instagram, configure as variáveis de ambiente:

```bash
export INSTAGRAM_ACCESS_TOKEN="seu_token_aqui"
export INSTAGRAM_USER_ID="id_da_sua_pagina"
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

# Modo verboso
python run_prospection.py --verbose
```

### Opções de Linha de Comando

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `--count N` | Número de influenciadores a prospectar | 20 |
| `--output-format` | Formato de saída (json, csv, markdown, all) | json |
| `--verbose` | Modo verboso com mais detalhes | False |

## 📊 Formatos de Saída

### JSON
```json
{
  "date": "2026-01-17",
  "influencers": [
    {
      "name": "personaltrainerbr",
      "primary_platform": "instagram",
      "profiles": [
        {
          "platform": "instagram",
          "username": "personaltrainerbr",
          "url": "https://www.instagram.com/personaltrainerbr/",
          "followers": 1858,
          "engagement_rate": 2.99
        }
      ]
    }
  ],
  "total_found": 42,
  "total_qualified": 30
}
```

### CSV
Arquivo com colunas: Nome, Plataforma, Username, URL, Seguidores, Engajamento, etc.

### Markdown
Relatório formatado com tabelas e detalhes de cada influenciador.

## 🔄 Automação (GitHub Actions)

O projeto inclui um workflow do GitHub Actions que executa automaticamente a prospecção diariamente às 9h (horário de Brasília).

### Configuração

Siga as instruções detalhadas em [SETUP_GITHUB.md](SETUP_GITHUB.md) para:

1. Configurar os secrets do Instagram no GitHub
2. Adicionar o arquivo de workflow
3. Executar manualmente ou aguardar a execução automática

### Secrets Necessários

| Secret | Descrição |
|--------|-----------|
| `INSTAGRAM_ACCESS_TOKEN` | Token de acesso da Graph API do Instagram |
| `INSTAGRAM_USER_ID` | ID da página do Instagram |

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
| Plataformas | Instagram (prioritário), TikTok, YouTube |
| Nicho | Emagrecimento, saúde, bem-estar |
| Histórico | Não prospectado anteriormente |

## 🔧 Manutenção

### Expandir Lista de Influenciadores do Instagram

Edite `src/instagram_prospector.py` e adicione usernames à lista `SEED_INFLUENCERS`.

### Adicionar Novas Palavras-chave

Edite `src/config.py` e adicione às listas `SEARCH_KEYWORDS_PT` ou `SEARCH_KEYWORDS_EN`.

### Renovar Token do Instagram

Tokens de longa duração expiram após ~60 dias. Para renovar:

1. Acesse o [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Gere um novo token com as permissões necessárias
3. Atualize o secret `INSTAGRAM_ACCESS_TOKEN` no GitHub

## 📝 Logs e Monitoramento

Os logs são exibidos durante a execução com informações sobre:
- Início e fim da execução
- Quantidade de perfis encontrados por plataforma
- Erros e exceções
- Tempo de execução

## 📄 Licença

Este projeto é proprietário da Voy Saúde. Todos os direitos reservados.

## 📞 Suporte

Para dúvidas ou suporte, entre em contato com a equipe de marketing da Voy Saúde.

---

**Desenvolvido para Voy Saúde** | Prospecção Automatizada de Influenciadores
