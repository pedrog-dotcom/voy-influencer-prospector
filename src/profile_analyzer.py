"""
Módulo de análise de perfis usando IA (GPT) para identificar pessoas reais
com potencial para parceria de emagrecimento.

Este módulo usa a API do OpenAI para analisar perfis e determinar:
1. Se é uma pessoa real ou página comercial
2. Se o perfil indica sobrepeso/obesidade ou jornada de emagrecimento
3. Nível de autenticidade e potencial de parceria
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import (
    OPENAI_MODEL,
    COMMERCIAL_INDICATORS,
    PERSONAL_INDICATORS,
    PREFERRED_SIZES,
    INFLUENCER_SIZE_RANGES,
)

logger = logging.getLogger(__name__)


class ProfileType(Enum):
    """Tipo de perfil identificado."""
    REAL_PERSON = "pessoa_real"
    COMMERCIAL = "comercial"
    PROFESSIONAL = "profissional"
    UNKNOWN = "desconhecido"


class BodyType(Enum):
    """Tipo corporal identificado."""
    OVERWEIGHT = "sobrepeso"
    OBESE = "obeso"
    WEIGHT_LOSS_JOURNEY = "jornada_emagrecimento"
    PLUS_SIZE = "plus_size"
    FIT = "fitness"
    UNKNOWN = "desconhecido"


@dataclass
class ProfileAnalysis:
    """Resultado da análise de um perfil."""
    profile_type: ProfileType
    body_type: BodyType
    is_real_person: bool
    has_weight_journey: bool
    authenticity_score: float  # 0-100
    partnership_potential: float  # 0-100
    reasoning: str
    recommended: bool
    tags: List[str]


class ProfileAnalyzer:
    """
    Analisador de perfis usando IA para identificar pessoas reais
    com potencial para parceria de emagrecimento.
    """
    
    def __init__(self):
        """Inicializa o analisador."""
        self.client = None
        
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI()
                logger.info("Cliente OpenAI inicializado para análise de perfis")
            else:
                logger.warning("OPENAI_API_KEY não configurada - usando análise básica")
        else:
            logger.warning("OpenAI não disponível - usando análise básica")
    
    def analyze_profile(
        self,
        username: str,
        name: str,
        bio: str,
        followers: int,
        platform: str,
        recent_posts: Optional[List[str]] = None,
    ) -> ProfileAnalysis:
        """
        Analisa um perfil para determinar se é uma pessoa real
        com potencial para parceria.
        
        Args:
            username: Nome de usuário do perfil
            name: Nome de exibição
            bio: Biografia do perfil
            followers: Número de seguidores
            platform: Plataforma (instagram, tiktok, youtube)
            recent_posts: Lista de descrições de posts recentes (opcional)
        
        Returns:
            ProfileAnalysis com os resultados da análise
        """
        # Se temos IA disponível, usar análise avançada
        if self.client:
            return self._analyze_with_ai(
                username, name, bio, followers, platform, recent_posts
            )
        
        # Fallback para análise básica
        return self._analyze_basic(
            username, name, bio, followers, platform
        )
    
    def _analyze_with_ai(
        self,
        username: str,
        name: str,
        bio: str,
        followers: int,
        platform: str,
        recent_posts: Optional[List[str]] = None,
    ) -> ProfileAnalysis:
        """Análise avançada usando GPT."""
        
        # Preparar contexto
        posts_text = ""
        if recent_posts:
            posts_text = f"\n\nDescrições de posts recentes:\n" + "\n".join(
                f"- {post}" for post in recent_posts[:5]
            )
        
        prompt = f"""Analise este perfil de {platform} e determine se é uma PESSOA REAL com potencial para parceria de emagrecimento para uma marca de saúde.

PERFIL:
- Username: @{username}
- Nome: {name}
- Seguidores: {followers:,}
- Bio: {bio or 'Não disponível'}
{posts_text}

CRITÉRIOS IMPORTANTES:
1. Queremos PESSOAS REAIS, não páginas comerciais, lojas, ou profissionais vendendo serviços
2. Ideal: pessoas com sobrepeso/obesidade compartilhando sua jornada de vida
3. Também aceito: influenciadores plus size, lifestyle saudável, moda, autocuidado, culinária
4. Preferimos nano/micro influenciadores (1k-50k seguidores) - mais autênticos
5. Evitar: nutricionistas, personal trainers, coaches, lojas, marcas

Responda APENAS com um JSON válido no seguinte formato:
{{
    "profile_type": "pessoa_real" | "comercial" | "profissional" | "desconhecido",
    "body_type": "sobrepeso" | "obeso" | "jornada_emagrecimento" | "plus_size" | "fitness" | "desconhecido",
    "is_real_person": true | false,
    "has_weight_journey": true | false,
    "authenticity_score": 0-100,
    "partnership_potential": 0-100,
    "reasoning": "explicação breve em português",
    "recommended": true | false,
    "tags": ["lista", "de", "tags", "relevantes"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de perfis de redes sociais para marketing de influência. Responda apenas com JSON válido."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Limpar resposta (remover markdown se houver)
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            return ProfileAnalysis(
                profile_type=ProfileType(result.get("profile_type", "desconhecido")),
                body_type=BodyType(result.get("body_type", "desconhecido")),
                is_real_person=result.get("is_real_person", False),
                has_weight_journey=result.get("has_weight_journey", False),
                authenticity_score=float(result.get("authenticity_score", 0)),
                partnership_potential=float(result.get("partnership_potential", 0)),
                reasoning=result.get("reasoning", ""),
                recommended=result.get("recommended", False),
                tags=result.get("tags", []),
            )
            
        except Exception as e:
            logger.error(f"Erro na análise com IA: {e}")
            return self._analyze_basic(username, name, bio, followers, platform)
    
    def _analyze_basic(
        self,
        username: str,
        name: str,
        bio: str,
        followers: int,
        platform: str,
    ) -> ProfileAnalysis:
        """Análise básica sem IA (fallback)."""
        
        bio_lower = (bio or "").lower()
        name_lower = (name or "").lower()
        username_lower = (username or "").lower()
        
        combined_text = f"{bio_lower} {name_lower} {username_lower}"
        
        # Verificar indicadores comerciais
        commercial_score = sum(
            1 for indicator in COMMERCIAL_INDICATORS
            if indicator.lower() in combined_text
        )
        
        # Verificar indicadores pessoais
        personal_score = sum(
            1 for indicator in PERSONAL_INDICATORS
            if indicator.lower() in combined_text
        )
        
        # Determinar tipo de perfil
        is_commercial = commercial_score > personal_score
        is_real_person = personal_score > 0 and not is_commercial
        
        # Verificar tamanho do influenciador
        size_category = self._get_size_category(followers)
        is_preferred_size = size_category in PREFERRED_SIZES
        
        # Verificar jornada de peso
        weight_keywords = [
            "emagrecimento", "perda de peso", "jornada", "transformação",
            "antes e depois", "sobrepeso", "obesidade", "plus size",
            "gordinha", "curvy", "weight loss", "journey"
        ]
        has_weight_journey = any(kw in combined_text for kw in weight_keywords)
        
        # Calcular scores
        authenticity_score = min(100, personal_score * 20 - commercial_score * 30)
        authenticity_score = max(0, authenticity_score)
        
        partnership_potential = 0
        if is_real_person:
            partnership_potential += 40
        if has_weight_journey:
            partnership_potential += 30
        if is_preferred_size:
            partnership_potential += 20
        if personal_score > 2:
            partnership_potential += 10
        
        # Determinar body type
        body_type = BodyType.UNKNOWN
        if "obeso" in combined_text or "obesidade" in combined_text:
            body_type = BodyType.OBESE
        elif "sobrepeso" in combined_text:
            body_type = BodyType.OVERWEIGHT
        elif "plus size" in combined_text or "curvy" in combined_text or "gordinha" in combined_text:
            body_type = BodyType.PLUS_SIZE
        elif has_weight_journey:
            body_type = BodyType.WEIGHT_LOSS_JOURNEY
        
        # Determinar profile type
        profile_type = ProfileType.UNKNOWN
        if is_commercial:
            profile_type = ProfileType.COMMERCIAL
        elif is_real_person:
            profile_type = ProfileType.REAL_PERSON
        elif commercial_score > 0:
            profile_type = ProfileType.PROFESSIONAL
        
        # Tags
        tags = []
        if has_weight_journey:
            tags.append("jornada_emagrecimento")
        if "plus size" in combined_text:
            tags.append("plus_size")
        if is_preferred_size:
            tags.append(f"tamanho_{size_category}")
        
        recommended = (
            is_real_person and
            partnership_potential >= 50 and
            not is_commercial
        )
        
        reasoning = self._generate_reasoning(
            is_real_person, is_commercial, has_weight_journey,
            size_category, personal_score, commercial_score
        )
        
        return ProfileAnalysis(
            profile_type=profile_type,
            body_type=body_type,
            is_real_person=is_real_person,
            has_weight_journey=has_weight_journey,
            authenticity_score=authenticity_score,
            partnership_potential=partnership_potential,
            reasoning=reasoning,
            recommended=recommended,
            tags=tags,
        )
    
    def _get_size_category(self, followers: int) -> str:
        """Retorna a categoria de tamanho do influenciador."""
        for category, (min_f, max_f) in INFLUENCER_SIZE_RANGES.items():
            if min_f <= followers < max_f:
                return category
        return "unknown"
    
    def _generate_reasoning(
        self,
        is_real_person: bool,
        is_commercial: bool,
        has_weight_journey: bool,
        size_category: str,
        personal_score: int,
        commercial_score: int,
    ) -> str:
        """Gera explicação da análise."""
        parts = []
        
        if is_real_person:
            parts.append("Perfil parece ser de pessoa real")
        elif is_commercial:
            parts.append("Perfil parece ser comercial/loja")
        else:
            parts.append("Tipo de perfil incerto")
        
        if has_weight_journey:
            parts.append("com indicadores de jornada de emagrecimento")
        
        parts.append(f"(tamanho: {size_category})")
        
        if personal_score > 0:
            parts.append(f"[{personal_score} indicadores pessoais]")
        if commercial_score > 0:
            parts.append(f"[{commercial_score} indicadores comerciais]")
        
        return ". ".join(parts)
    
    def batch_analyze(
        self,
        profiles: List[Dict[str, Any]],
    ) -> List[ProfileAnalysis]:
        """
        Analisa múltiplos perfis em lote.
        
        Args:
            profiles: Lista de dicionários com dados dos perfis
        
        Returns:
            Lista de ProfileAnalysis
        """
        results = []
        
        for profile in profiles:
            analysis = self.analyze_profile(
                username=profile.get("username", ""),
                name=profile.get("name", ""),
                bio=profile.get("bio", ""),
                followers=profile.get("followers", 0),
                platform=profile.get("platform", "instagram"),
                recent_posts=profile.get("recent_posts"),
            )
            results.append(analysis)
        
        return results
    
    def filter_recommended(
        self,
        profiles: List[Dict[str, Any]],
        min_partnership_potential: float = 50,
    ) -> List[Dict[str, Any]]:
        """
        Filtra perfis recomendados para parceria.
        
        Args:
            profiles: Lista de perfis para analisar
            min_partnership_potential: Score mínimo de potencial de parceria
        
        Returns:
            Lista de perfis recomendados com análise anexada
        """
        recommended = []
        
        for profile in profiles:
            analysis = self.analyze_profile(
                username=profile.get("username", ""),
                name=profile.get("name", ""),
                bio=profile.get("bio", ""),
                followers=profile.get("followers", 0),
                platform=profile.get("platform", "instagram"),
                recent_posts=profile.get("recent_posts"),
            )
            
            if analysis.recommended and analysis.partnership_potential >= min_partnership_potential:
                profile["analysis"] = {
                    "profile_type": analysis.profile_type.value,
                    "body_type": analysis.body_type.value,
                    "is_real_person": analysis.is_real_person,
                    "has_weight_journey": analysis.has_weight_journey,
                    "authenticity_score": analysis.authenticity_score,
                    "partnership_potential": analysis.partnership_potential,
                    "reasoning": analysis.reasoning,
                    "tags": analysis.tags,
                }
                recommended.append(profile)
        
        return recommended


# Teste do módulo
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    analyzer = ProfileAnalyzer()
    
    # Perfis de teste
    test_profiles = [
        {
            "username": "maria_jornada_fit",
            "name": "Maria Silva | Minha Jornada",
            "bio": "Mãe de 2 💕 Perdendo peso com amor próprio. 30kg eliminados! Compartilho minha transformação real 🦋",
            "followers": 15000,
            "platform": "instagram",
        },
        {
            "username": "loja_suplementos_oficial",
            "name": "Loja Suplementos BR",
            "bio": "🏪 Loja oficial de suplementos. Whey, creatina, termogênicos. Frete grátis! Link na bio 👇",
            "followers": 50000,
            "platform": "instagram",
        },
        {
            "username": "nutri_carol",
            "name": "Dra. Carol Nutricionista",
            "bio": "👩‍⚕️ Nutricionista CRN 12345. Consultório online. Emagreça com saúde! Agende sua consulta 📲",
            "followers": 80000,
            "platform": "instagram",
        },
        {
            "username": "ana_plussize",
            "name": "Ana | Plus Size & Lifestyle",
            "bio": "Gordinha e estilosa 💃 Moda plus size, autocuidado e muito amor próprio. Todas as curvas importam! 🌸",
            "followers": 8000,
            "platform": "instagram",
        },
    ]
    
    print("=" * 60)
    print("TESTE DO ANALISADOR DE PERFIS")
    print("=" * 60)
    
    for profile in test_profiles:
        print(f"\n--- @{profile['username']} ---")
        analysis = analyzer.analyze_profile(**profile)
        print(f"Tipo: {analysis.profile_type.value}")
        print(f"Corpo: {analysis.body_type.value}")
        print(f"Pessoa real: {analysis.is_real_person}")
        print(f"Jornada peso: {analysis.has_weight_journey}")
        print(f"Autenticidade: {analysis.authenticity_score}")
        print(f"Potencial: {analysis.partnership_potential}")
        print(f"Recomendado: {analysis.recommended}")
        print(f"Razão: {analysis.reasoning}")
        print(f"Tags: {analysis.tags}")
