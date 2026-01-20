# 🎯 Voy Saúde - Prospecção de Influenciadores

Sistema automatizado de prospecção diária de influenciadores para a marca [Voy Saúde](https://www.voysaude.com.br/), focado em **pessoas reais** com sobrepeso/obesidade ou em jornada de emagrecimento.

## 📋 Descrição

Este projeto automatiza a busca e qualificação de influenciadores no **Instagram** (via Graph API), utilizando **análise de IA (GPT)** para identificar pessoas reais e filtrar páginas comerciais.

### Foco Principal

- **Pessoas reais** compartilhando suas jornadas de vida
- **Sobrepeso/obesidade** ou processo de emagrecimento
- **Plus size**, lifestyle, autocuidado, culinária saudável
- **Micro influenciadores** (10k+ seguidores) - mais autênticos

### O que evitamos

- ❌ Páginas comerciais e lojas
- ❌ Nutricionistas e personal trainers vendendo serviços
- ❌ Coaches e mentores com cursos
- ❌ Perfis de marcas e empresas

## 🚀 Funcionalidades

- ✅ **Análise com IA (GPT)** para identificar pessoas reais
- ✅ Busca automatizada no **Instagram** (via Graph API)
- ✅ Cálculo de taxa de engajamento
- ✅ Filtro por hashtags configuráveis (lifestyle, plus size, autocuidado)
- ✅ Controle de histórico para evitar duplicatas e economizar tokens
- ✅ Registro incremental em CSV dos aprovados
- ✅ Execução agendada via GitHub Actions (diariamente às 9h)

## 🤖 Análise com IA

O sistema utiliza GPT para analisar cada perfil e determinar:

| Critério | Descrição |
|----------|-----------|
| **Idade** | Se aparenta ter mais de 25 anos |
| **Tipo corporal** | Sobrepeso, obeso, plus size, jornada de emagrecimento |
| **Classe social** | Conteúdo consumido por classe A/B |
| **Nacionalidade** | Indicadores de perfil brasileiro |
| **Pessoa real** | Não ser marca/loja/serviço |
| **Recomendação** | Se o perfil é adequado para parceria |

### Exemplo de Resultado

```
✓ Pessoa real | ✓ Jornada de emagrecimento | Tipo: plus_size
Análise: Perfil parece ser de pessoa real com indicadores de jornada de emagrecimento (tamanho: micro)
```

## 📊 Plataformas Suportadas

| Plataforma | Prioridade | Método de Busca |
|------------|------------|-----------------|
| Instagram | 1 (Alta) | Graph API - Business Discovery |

## 📁 Estrutura do Projeto

```
voy-influencer-prospector/
├── src/
│   ├── __init__.py
│   ├── config.py               # Configurações e palavras-chave expandidas
│   ├── history_manager.py      # Gerenciamento de histórico
│   ├── gpt_screener.py          # Triagem de perfis com IA (GPT)
│   └── hashtag_collector.py     # Coleta de perfis via hashtags
├── data/
│   ├── approved_influencers.csv     # Influenciadores aprovados
│   ├── processed_profiles.json      # Histórico de perfis processados
│   └── pending_profiles.json        # Perfis aguardando triagem
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
- API Key do OpenAI (para análise com IA)
- Token de acesso da Graph API do Instagram (opcional, mas recomendado)

### Instalação Local

```bash
# Clonar o repositório
git clone https://github.com/pedrog-dotcom/voy-influencer-prospector.git
cd voy-influencer-prospector

# Instalar dependências
pip install -r requirements.txt
```

### Configuração

Configure as variáveis de ambiente:

```bash
# Obrigatório para análise com IA
export OPENAI_API_KEY="sua_api_key_openai"

# Opcional - para prospecção do Instagram
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

# Modo verboso
python run_prospection.py --verbose
```

### Opções de Linha de Comando

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `--count N` | Número de influenciadores a aprovar | 20 |
| `--verbose` | Modo verboso com mais detalhes | False |

## 📊 Saída Principal

### CSV (Aprovados)
Arquivo com colunas: Nome, Plataforma, Username, URL, Seguidores, Engajamento, Pessoa Real, Jornada de Peso, etc. O arquivo é incrementado a cada execução.

## 🔄 Automação (GitHub Actions)

O projeto inclui um workflow do GitHub Actions que executa automaticamente a prospecção diariamente às 9h (horário de Brasília).

### Configuração

Siga as instruções detalhadas em [SETUP_GITHUB.md](SETUP_GITHUB.md) para:

1. Configurar os secrets no GitHub
2. Adicionar o arquivo de workflow
3. Executar manualmente ou aguardar a execução automática

### Secrets Necessários

| Secret | Descrição |
|--------|-----------|
| `OPENAI_API_KEY` | API Key do OpenAI para análise com IA |
| `INSTAGRAM_ACCESS_TOKEN` | Token de acesso da Graph API do Instagram |
| `INSTAGRAM_USER_ID` | ID da página do Instagram |

## 📈 Hashtags Monitoradas

As hashtags ativas ficam em `src/config.py` dentro de `HASHTAGS_CONFIG`.

## 🎯 Critérios de Qualificação

| Critério | Requisito |
|----------|-----------|
| Seguidores | ≥ 10.000 |
| Taxa de Engajamento | ≥ 2,5% |
| Tipo de Perfil | Pessoa real (validado por IA) |
| Plataforma | Instagram |
| Nicho | Emagrecimento, plus size, lifestyle, autocuidado |
| Histórico | Não prospectado anteriormente |

## 🔧 Manutenção

### Expandir Lista de Influenciadores Seed do Instagram

Edite `src/hashtag_collector.py` e adicione usernames à lista `SEED_PROFILES`.

### Adicionar/Remover Hashtags

Edite `src/config.py` e marque as hashtags desejadas como `True`/`False` no dicionário `HASHTAGS_CONFIG`.

### Renovar Token do Instagram

Tokens de longa duração expiram após ~60 dias. Para renovar:

1. Acesse o [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Gere um novo token com as permissões necessárias
3. Atualize o secret `INSTAGRAM_ACCESS_TOKEN` no GitHub

## 📝 Logs e Monitoramento

Os logs são exibidos durante a execução com informações sobre:
- Início e fim da execução
- Quantidade de perfis encontrados por plataforma
- Análise de IA (pessoas reais identificadas)
- Erros e exceções
- Tempo de execução

## 📄 Licença

Este projeto é proprietário da Voy Saúde. Todos os direitos reservados.

## 📞 Suporte

Para dúvidas ou suporte, entre em contato com a equipe de marketing da Voy Saúde.

---

**Desenvolvido para Voy Saúde** | Prospecção Automatizada de Influenciadores com IA
