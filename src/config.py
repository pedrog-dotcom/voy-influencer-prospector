"""
Configurações do projeto de prospecção de influenciadores para Voy Saúde.
"""

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

# Palavras-chave para busca de influenciadores com perfil de emagrecimento/sobrepeso
SEARCH_KEYWORDS_PT = [
    "emagrecimento",
    "perda de peso",
    "dieta",
    "obesidade",
    "sobrepeso",
    "reeducação alimentar",
    "antes e depois",
    "transformação corporal",
    "saúde e bem estar",
    "vida saudável",
    "fitness iniciante",
    "minha jornada de emagrecimento",
    "ozempic",
    "semaglutida",
    "mounjaro",
    "wegovy",
]

SEARCH_KEYWORDS_EN = [
    "weight loss journey",
    "obesity transformation",
    "overweight fitness",
    "before and after weight loss",
    "body transformation",
    "weight loss motivation",
    "ozempic journey",
    "semaglutida",
    "mounjaro weight loss",
]

# Hashtags relevantes para busca
RELEVANT_HASHTAGS = [
    "#emagrecimento",
    "#perdadepeso",
    "#antesedepois",
    "#transformação",
    "#vidasaudavel",
    "#dietalowcarb",
    "#reeducaçãoalimentar",
    "#ozempic",
    "#semaglutida",
    "#mounjaro",
    "#weightlossjourney",
    "#weightlosstransformation",
]

# Configurações de tamanho de influenciador (seguidores)
INFLUENCER_SIZE_RANGES = {
    "nano": (1_000, 10_000),
    "micro": (10_000, 50_000),
    "small": (50_000, 100_000),
    "medium": (100_000, 500_000),
    "big": (500_000, 1_000_000),
    "mega": (1_000_000, float("inf")),
}

# Prioridade de plataformas (1 = maior prioridade)
PLATFORM_PRIORITY = {
    "instagram": 1,
    "tiktok": 2,
    "youtube": 3,
}

# Configurações de API
API_RATE_LIMIT_DELAY = 1.0  # segundos entre chamadas de API
MAX_RETRIES = 3
