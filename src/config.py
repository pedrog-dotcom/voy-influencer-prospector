"""
Configurações do sistema de prospecção de influenciadores.
Voy Saúde - V4: Fluxo otimizado com triagem GPT
"""

from pathlib import Path

# Diretórios
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Arquivos de dados
HISTORY_FILE = DATA_DIR / "processed_profiles.json"  # Perfis já processados (não reprocessar)
APPROVED_FILE = DATA_DIR / "approved_influencers.csv"  # Influenciadores aprovados
PENDING_FILE = DATA_DIR / "pending_profiles.json"  # Perfis coletados aguardando triagem

# Configurações de prospecção
DAILY_OUTPUT_COUNT = 20  # Número de influenciadores aprovados por dia
MIN_FOLLOWERS = 10000  # Mínimo de seguidores (10k)
MIN_ENGAGEMENT_RATE = 2.5  # Taxa de engajamento mínima (%)
RECENT_MEDIA_DAYS = 30  # Janela de recência para posts com hashtag

# =============================================================================
# HASHTAGS PARA COLETA DE PERFIS
# Selecione as hashtags que deseja monitorar (True = ativa, False = inativa)
# =============================================================================

HASHTAGS_CONFIG = {
    # Jornada de Emagrecimento
    "emagrecimento": True,
    "perdadepeso": True,
    "antesedepois": True,
    "minhatransformacao": True,
    "diariodeemagrecimento": True,
    "reeducacaoalimentar": True,
    "mudancadevida": True,
    
    # Medicamentos (experiências pessoais)
    "ozempic": True,
    "semaglutida": True,
    "mounjaro": True,
    "wegovy": True,
    "saxenda": True,
    
    # Plus Size / Body Positive
    "plussize": True,
    "plussizebrasil": True,
    "modaplussize": True,
    "curvygirl": True,
    "bodypositive": True,
    "gordasestilosas": True,
    "gordinhafashion": True,
    
    # Lifestyle Saudável
    "vidasaudavel": True,
    "rotinasaudavel": True,
    "habitossaudaveis": True,
    "qualidadedevida": True,
    "bemestar": True,
    
    # Autocuidado
    "autocuidado": True,
    "selfcare": True,
    "amorproprio": True,
    "autoestima": True,
    
    # Culinária Saudável
    "receitassaudaveis": True,
    "comidadeverdade": True,
    "alimentacaosaudavel": True,
    "lowcarb": True,
    "fitfood": True,
    
    # Moda e Beleza
    "modafeminina": True,
    "lookdodia": True,
    "fashionblogger": True,
    "beleza": True,
    "maquiagem": True,
}


def get_active_hashtags() -> list:
    """Retorna lista de hashtags ativas para coleta."""
    return [tag for tag, enabled in HASHTAGS_CONFIG.items() if enabled]


# =============================================================================
# CRITÉRIOS DE TRIAGEM GPT
# =============================================================================

SCREENING_CRITERIA = {
    "min_age": 25,  # Idade mínima aparente
    "body_types": ["sobrepeso", "obeso", "plus_size", "gordo", "acima_do_peso"],
    "target_classes": ["A", "B"],  # Classes de renda alvo
    "nationality": "brasileiro",  # Nacionalidade
}

# Prompt para triagem GPT
SCREENING_PROMPT = """
Você é um especialista em análise de perfis de influenciadores para campanhas de marketing de produtos de emagrecimento.

Analise o perfil abaixo e responda às perguntas de forma objetiva.

**DADOS DO PERFIL:**
- Nome: {name}
- Username: @{username}
- Plataforma: {platform}
- Seguidores: {followers:,}
- Taxa de Engajamento: {engagement_rate:.2f}%
- Bio: {bio}
- Localização: {location}
- Descrição do conteúdo: {content_description}

**PERGUNTAS DE TRIAGEM:**

1. **IDADE:** A pessoa aparenta ter mais de 25 anos? (Sim/Não/Incerto)

2. **TIPO CORPORAL:** A pessoa aparenta ter sobrepeso ou ser obesa? (Sim/Não/Incerto)
   - Considere: plus size, gordo(a), acima do peso, curvy, em processo de emagrecimento

3. **CLASSE SOCIAL:** O conteúdo parece ser consumido por pessoas de classe A ou B? (Sim/Não/Incerto)
   - Considere: qualidade das fotos, locais frequentados, produtos mencionados, estilo de vida

4. **NACIONALIDADE:** A pessoa é brasileira? (Sim/Não/Incerto)
   - Considere: idioma da bio, localização, hashtags em português

5. **PESSOA REAL:** É uma pessoa real (não marca, loja, clínica ou profissional vendendo serviços)? (Sim/Não)

**RESPONDA APENAS NO FORMATO JSON (sem markdown, sem explicações extras):**
{{"idade_25_plus": true, "sobrepeso_obeso": true, "classe_ab": true, "brasileiro": true, "pessoa_real": true, "aprovado": true, "motivo": "Breve explicação", "confianca": 85}}

**REGRAS:**
- "aprovado" = true APENAS se TODAS as condições forem verdadeiras
- Use true/false (não null)
- Se houver dúvida significativa em qualquer critério, marque como false
- "confianca" é um número de 0 a 100
"""

# =============================================================================
# CONFIGURAÇÕES DE API
# =============================================================================

# TikTok API (via RapidAPI - Manus)
MANUS_API_BASE = "https://api.manus.ai"

# Instagram Graph API
INSTAGRAM_API_BASE = "https://graph.facebook.com/v18.0"

# OpenAI API
OPENAI_MODEL = "gpt-4.1-mini"
OPENAI_MAX_TOKENS = 500
OPENAI_TEMPERATURE = 0.1

# =============================================================================
# RATE LIMITING
# =============================================================================

API_DELAYS = {
    "tiktok": 2.0,  # segundos entre requisições
    "instagram": 1.0,
    "youtube": 1.0,
    "openai": 1.0,
}
