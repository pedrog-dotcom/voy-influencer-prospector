"""
Configurações do projeto de prospecção de influenciadores para Voy Saúde.
"""

import os
from pathlib import Path
from typing import List

# Diretórios do projeto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Arquivo de histórico para evitar duplicatas
HISTORY_FILE = DATA_DIR / "prospected_influencers.json"
OUTPUT_FILE = DATA_DIR / "daily_prospects.json"

# Configurações de prospecção
DAILY_PROSPECT_COUNT = 20
MIN_ENGAGEMENT_RATE = 2.5  # Porcentagem mínima de engajamento

# Configuração da API OpenAI para análise de perfis
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4.1-mini"  # Modelo para análise de perfis

# ============================================================================
# PALAVRAS-CHAVE EXPANDIDAS PARA ENCONTRAR PESSOAS REAIS
# ============================================================================

# Palavras-chave principais - Jornada pessoal de emagrecimento
SEARCH_KEYWORDS_JOURNEY = [
    "minha jornada",
    "minha transformação",
    "meu antes e depois",
    "diário de emagrecimento",
    "minha história de emagrecimento",
    "perdendo peso",
    "emagrecendo",
    "mudança de vida",
    "novo estilo de vida",
]

# Palavras-chave - Lifestyle e vida saudável
SEARCH_KEYWORDS_LIFESTYLE = [
    "vida saudável",
    "rotina saudável",
    "hábitos saudáveis",
    "mudança de hábitos",
    "qualidade de vida",
    "bem estar",
    "saúde mental",
    "autoestima",
    "amor próprio",
    "aceitação corporal",
]

# Palavras-chave - Moda Plus Size
SEARCH_KEYWORDS_FASHION = [
    "moda plus size",
    "plus size brasil",
    "curvy fashion",
    "moda gg",
    "look plus size",
    "estilo plus size",
    "gordinha fashion",
    "body positive",
    "todas as curvas",
]

# Palavras-chave - Autocuidado
SEARCH_KEYWORDS_SELFCARE = [
    "autocuidado",
    "self care",
    "cuidando de mim",
    "rotina de cuidados",
    "me amando",
    "autoamor",
    "empoderamento",
    "confiança",
]

# Palavras-chave - Culinária saudável
SEARCH_KEYWORDS_FOOD = [
    "receitas saudáveis",
    "comida de verdade",
    "alimentação saudável",
    "cozinhando saudável",
    "receitas fit",
    "low carb receitas",
    "reeducação alimentar",
    "dieta flexível",
    "comendo bem",
]

# Palavras-chave - Fitness iniciante
SEARCH_KEYWORDS_FITNESS = [
    "começando a treinar",
    "iniciante na academia",
    "voltando a treinar",
    "treino em casa",
    "exercício para iniciantes",
    "saindo do sedentarismo",
    "primeiro treino",
]

# Palavras-chave em inglês
SEARCH_KEYWORDS_EN = [
    "weight loss journey",
    "my transformation",
    "body positive",
    "plus size fashion",
    "curvy girl",
    "healthy lifestyle",
    "fitness journey",
    "self love journey",
    "real body",
    "no filter transformation",
]

# Combinar todas as palavras-chave
SEARCH_KEYWORDS_PT = (
    SEARCH_KEYWORDS_JOURNEY +
    SEARCH_KEYWORDS_LIFESTYLE +
    SEARCH_KEYWORDS_FASHION +
    SEARCH_KEYWORDS_SELFCARE +
    SEARCH_KEYWORDS_FOOD +
    SEARCH_KEYWORDS_FITNESS
)

# ============================================================================
# HASHTAGS EXPANDIDAS
# ============================================================================

# Hashtags - Jornada pessoal
HASHTAGS_JOURNEY = [
    "#minhajornada",
    "#minhatransformacao",
    "#antesedepois",
    "#transformacaoreal",
    "#diariodeemagrecimento",
    "#perdendopeso",
    "#emagrecendocomsaude",
    "#mudancadevida",
    "#projetoveraofitness",
]

# Hashtags - Lifestyle
HASHTAGS_LIFESTYLE = [
    "#vidasaudavel",
    "#estilodevida",
    "#rotinasaudavel",
    "#habitossaudaveis",
    "#qualidadedevida",
    "#bemestar",
    "#saudemental",
    "#equilibrio",
]

# Hashtags - Moda Plus Size
HASHTAGS_FASHION = [
    "#plussize",
    "#plussizebrasil",
    "#modaplussize",
    "#curvyfashion",
    "#modagg",
    "#gordasestilosas",
    "#bodypositive",
    "#todasascurvas",
    "#curvywoman",
    "#plussizemodel",
    "#fatshion",
]

# Hashtags - Autocuidado
HASHTAGS_SELFCARE = [
    "#autocuidado",
    "#selfcare",
    "#amorproprio",
    "#autoestima",
    "#empoderamento",
    "#confianca",
    "#meamando",
    "#selflove",
]

# Hashtags - Culinária
HASHTAGS_FOOD = [
    "#receitassaudaveis",
    "#comidadeverdade",
    "#alimentacaosaudavel",
    "#receitasfit",
    "#lowcarb",
    "#reeducacaoalimentar",
    "#dietaflexivel",
    "#comidasaudavel",
]

# Hashtags - Fitness
HASHTAGS_FITNESS = [
    "#fitnessiniciante",
    "#comecandonaacademia",
    "#treinoemcasa",
    "#saindodosedentarismo",
    "#fitnessmotivation",
    "#treinoparatodos",
]

# Hashtags - Medicamentos (pessoas compartilhando experiências)
HASHTAGS_MEDS = [
    "#ozempic",
    "#semaglutida",
    "#mounjaro",
    "#wegovy",
    "#ozempicbrasil",
    "#tratamentoobesidade",
]

# Combinar todas as hashtags
RELEVANT_HASHTAGS = (
    HASHTAGS_JOURNEY +
    HASHTAGS_LIFESTYLE +
    HASHTAGS_FASHION +
    HASHTAGS_SELFCARE +
    HASHTAGS_FOOD +
    HASHTAGS_FITNESS +
    HASHTAGS_MEDS
)

# ============================================================================
# CONFIGURAÇÕES DE FILTRAGEM
# ============================================================================

# Palavras que indicam página comercial (para filtrar)
COMMERCIAL_INDICATORS = [
    "loja", "store", "shop", "oficial", "official",
    "vendas", "compre", "buy", "promoção", "promo",
    "atacado", "varejo", "distribuidora", "representante",
    "suplementos", "produtos", "marca", "brand",
    "clínica", "clinic", "consultório", "nutricionista",
    "personal trainer", "coach", "mentoria",
    "curso", "ebook", "método", "programa",
    "link na bio", "arrasta pra cima", "cupom",
]

# Palavras que indicam pessoa real (para priorizar)
PERSONAL_INDICATORS = [
    "mãe", "pai", "mamãe", "papai", "mom", "dad",
    "esposa", "marido", "wife", "husband",
    "anos", "years old", "nascida", "born",
    "morando em", "living in", "de", "from",
    "amo", "love", "apaixonada", "passionate",
    "minha vida", "my life", "minha história", "my story",
    "jornada", "journey", "transformação", "transformation",
    "real", "verdadeira", "authentic",
    "gordinha", "curvy", "plus size",
    "lutando", "fighting", "superando", "overcoming",
]

# Configurações de tamanho de influenciador (seguidores)
# Focando em nano e micro influenciadores (mais autênticos)
INFLUENCER_SIZE_RANGES = {
    "nano": (1_000, 10_000),
    "micro": (10_000, 50_000),
    "small": (50_000, 100_000),
    "medium": (100_000, 500_000),
    "big": (500_000, 1_000_000),
    "mega": (1_000_000, float("inf")),
}

# Tamanhos preferidos (pessoas reais geralmente são nano/micro)
PREFERRED_SIZES = ["nano", "micro", "small"]

# Prioridade de plataformas (1 = maior prioridade)
PLATFORM_PRIORITY = {
    "instagram": 1,
    "tiktok": 2,
    "youtube": 3,
}

# Configurações de API
API_RATE_LIMIT_DELAY = 1.0  # segundos entre chamadas de API
MAX_RETRIES = 3

# Configurações do Instagram (via variáveis de ambiente)
# INSTAGRAM_ACCESS_TOKEN - Token de acesso da Graph API (longa duração)
# INSTAGRAM_USER_ID - ID do usuário Instagram (página conectada)
