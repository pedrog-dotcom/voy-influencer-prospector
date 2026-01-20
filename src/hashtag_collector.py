"""
Módulo de coleta de perfis via hashtags.
V4.1: Lista de perfis seed otimizada + coleta via hashtags.

Estratégia:
1. Usar Instagram Graph API para buscar mídias por hashtag
2. Usar Business Discovery para obter métricas dos perfis
3. Manter lista de perfis seed do nicho para garantir resultados
4. Enviar apenas perfis qualificados (10k+ seguidores e 2.5%+ engajamento) para triagem GPT
"""

import os
import time
import logging
import requests
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime

from config import (
    get_active_hashtags,
    MIN_FOLLOWERS,
    MIN_ENGAGEMENT_RATE,
    API_DELAYS,
    INSTAGRAM_API_BASE,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15

# Lista de perfis seed do nicho de emagrecimento/plus size no Brasil
# Focando em micro/médio influenciadores (10k-500k) com maior engajamento
SEED_PROFILES = [
        "mamuteofficial",
    "descobridepoisdeadultapod",
    "colodeamiga",
    "giovannaantonelli",
    "galisteuoficial",
    "perrengue_chique",
    "tiagoabravanel",
    "thaiscarla",
    "alexiatamiraa",
    "sabrinamotta_40",
    "ohanareal",
    "riziacerqueira",
    "juliasouzaj",
    "mathylemoss",
    "tamtaum",
    "trincaa_",
    "nathhiramos",
    "soaresrayane",
    "denisekulmann_",
    "jelindsay_",
    "rafaa.mmz",
    "gabismith",
    "dinhasobral",
    "douradaaaa",
    "brenao_",
    "anapaulasouza03",
    "emagrecercomsara",
    "cassioblancooficial",
    "lucyroag",
    "elenslles",
    "sthe_vick",
    "manuelaelenoreels",
    "camilarossado",
    "betaboechat",
    "taciaranasciment",
    "michellefariasof",
    "nahymo",
    "relaxaaifofa",
    "marialuisaneves",
    "minabemestar",
    "laaripereira",
    "fatfamilyoficial",
    "aline.olmacedo",
    "mayararussi",
    "_acasa125",
    "kahenar",
    "ola_soualidia",
    "sophiajanoti",
    "ludimilagfit",
    "laris.fittreels",
    "oficialbrunamedeiros",
    "pam_frison",
    "instadazanda",
    "miguena_",
    "majuhbarbosa",
    "felipecampus",
    "brunahaurani",
    "magalhaesca",
    "lidiacardosofer",
    "marilimaplus",
    "isapbf",
    "isabellaassiis",
    "baridacints",
    "carinacampeao_",
]


@dataclass
class CollectedProfile:
    """Perfil coletado de uma hashtag."""
    username: str
    name: str
    platform: str
    followers: int
    engagement_rate: float
    bio: str
    location: str
    profile_url: str
    avatar_url: str
    content_description: str
    source_hashtag: str
    collected_at: str
    raw_data: dict = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        # Remover raw_data do dict para economizar espaço
        data.pop('raw_data', None)
        return data
    
    def meets_criteria(self) -> bool:
        """Verifica se o perfil atende aos critérios mínimos."""
        return (
            self.followers >= MIN_FOLLOWERS and
            self.engagement_rate >= MIN_ENGAGEMENT_RATE
        )


class HashtagCollector:
    """Coletor de perfis via hashtags focado em Instagram."""
    
    def __init__(self):
        self.instagram_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_user_id = os.environ.get("INSTAGRAM_USER_ID")
        self.collected_usernames: Set[str] = set()
        self.all_collected: List[CollectedProfile] = []  # Todos os coletados (para debug)
        
    def collect_from_all_hashtags(self, max_per_hashtag: int = 20) -> List[CollectedProfile]:
        """
        Coleta perfis de hashtags e lista seed.
        
        Args:
            max_per_hashtag: Máximo de perfis por hashtag
            
        Returns:
            Lista de perfis coletados que atendem aos critérios mínimos
        """
        all_profiles = []
        
        if not self.instagram_token or not self.instagram_user_id:
            logger.error("Token do Instagram não configurado!")
            return all_profiles
        
        # 1. Coletar de perfis seed primeiro
        logger.info("Coletando perfis da lista seed...")
        seed_profiles = self._collect_from_seed_list()
        all_profiles.extend(seed_profiles)
        logger.info(f"Perfis seed coletados: {len(seed_profiles)}")
        
        # 2. Coletar de hashtags
        active_hashtags = get_active_hashtags()
        hashtags_to_process = active_hashtags[:10]  # Limitar a 10 hashtags
        
        logger.info(f"Coletando perfis de {len(hashtags_to_process)} hashtags...")
        
        for i, hashtag in enumerate(hashtags_to_process):
            try:
                logger.info(f"[{i+1}/{len(hashtags_to_process)}] Processando #{hashtag}")
                
                profiles = self._collect_from_instagram_hashtag(hashtag, max_per_hashtag)
                all_profiles.extend(profiles)
                
                logger.info(f"  Encontrados: {len(profiles)} perfis")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Erro ao coletar #{hashtag}: {e}")
                continue
        
        # Log de todos os coletados (para debug)
        logger.info(f"\nResumo de todos os perfis coletados:")
        for p in self.all_collected:
            status = "✓" if p.meets_criteria() else "✗"
            logger.info(f"  {status} @{p.username}: {p.followers:,} seg, {p.engagement_rate:.2f}% eng")
        
        # Log de estatísticas
        qualified = [p for p in all_profiles if p.meets_criteria()]
        logger.info(f"\nTotal coletado: {len(all_profiles)}")
        logger.info(f"Qualificados (10k+, 2.5%+): {len(qualified)}")
        logger.info("Retornando apenas perfis qualificados para triagem GPT")
        
        # Retornar apenas perfis qualificados
        # Ordenar por seguidores para priorizar maiores
        sorted_profiles = sorted(qualified, key=lambda x: x.followers, reverse=True)
        
        return sorted_profiles
    
    def _collect_from_seed_list(self) -> List[CollectedProfile]:
        """Coleta dados dos perfis da lista seed."""
        profiles = []
        
        for username in SEED_PROFILES:
            if username in self.collected_usernames:
                continue
                
            profile = self._get_instagram_profile(username, "seed_list")
            
            if profile:
                profiles.append(profile)
                self.all_collected.append(profile)
                self.collected_usernames.add(username)
                logger.debug(f"  ✓ @{username}: {profile.followers:,} seg, {profile.engagement_rate:.2f}% eng")
            else:
                logger.debug(f"  ✗ @{username}: não encontrado ou privado")
            
            time.sleep(0.3)  # Rate limiting
        
        return profiles
    
    def _collect_from_instagram_hashtag(self, hashtag: str, max_results: int) -> List[CollectedProfile]:
        """Coleta perfis do Instagram via hashtag."""
        profiles = []
        
        try:
            # Buscar ID da hashtag
            hashtag_url = f"{INSTAGRAM_API_BASE}/ig_hashtag_search"
            hashtag_params = {
                "user_id": self.instagram_user_id,
                "q": hashtag,
                "access_token": self.instagram_token
            }
            
            response = requests.get(hashtag_url, params=hashtag_params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                logger.debug(f"Hashtag search failed: {response.status_code}")
                return profiles
            
            data = response.json()
            hashtag_data = data.get("data", [])
            
            if not hashtag_data:
                return profiles
            
            hashtag_id = hashtag_data[0].get("id")
            
            # Buscar mídias recentes
            media_url = f"{INSTAGRAM_API_BASE}/{hashtag_id}/recent_media"
            media_params = {
                "user_id": self.instagram_user_id,
                "fields": "id,caption,permalink",
                "limit": min(max_results * 2, 50),
                "access_token": self.instagram_token
            }
            
            response = requests.get(media_url, params=media_params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                return profiles
            
            media_data = response.json().get("data", [])
            
            # Extrair usernames das captions e permalinks
            usernames_found = set()
            
            for media in media_data:
                caption = media.get("caption", "")
                
                # Extrair menções da caption
                mentions = re.findall(r'@([a-zA-Z0-9_.]+)', caption)
                usernames_found.update(mentions)
            
            # Buscar dados de cada username encontrado
            for username in list(usernames_found)[:max_results]:
                if username in self.collected_usernames or len(username) < 3:
                    continue
                
                profile = self._get_instagram_profile(username, hashtag)
                
                if profile:
                    profiles.append(profile)
                    self.all_collected.append(profile)
                    self.collected_usernames.add(username)
                
                time.sleep(0.3)
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na busca de #{hashtag}")
        except Exception as e:
            logger.debug(f"Erro ao coletar #{hashtag}: {e}")
        
        return profiles
    
    def _get_instagram_profile(self, username: str, source_hashtag: str) -> Optional[CollectedProfile]:
        """Busca dados de um perfil Instagram via Business Discovery."""
        try:
            url = f"{INSTAGRAM_API_BASE}/{self.instagram_user_id}"
            params = {
                "fields": f"business_discovery.username({username}){{username,name,biography,followers_count,media_count,media{{like_count,comments_count}}}}",
                "access_token": self.instagram_token
            }
            
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            business = data.get("business_discovery", {})
            
            if not business:
                return None
            
            followers = business.get("followers_count", 0)
            
            # Calcular engajamento médio
            media = business.get("media", {}).get("data", [])
            if media:
                total_engagement = sum(
                    m.get("like_count", 0) + m.get("comments_count", 0)
                    for m in media[:10]
                )
                avg_engagement = total_engagement / len(media[:10])
                engagement_rate = (avg_engagement / max(followers, 1)) * 100
            else:
                engagement_rate = 0
            
            bio = business.get("biography", "")
            
            # Detectar localização Brasil
            brasil_indicators = ["brasil", "brazil", "br", "são paulo", "rio", "sp", "rj", "mg", "ba", "🇧🇷"]
            is_brazil = any(ind in bio.lower() for ind in brasil_indicators)
            
            return CollectedProfile(
                username=business.get("username", username),
                name=business.get("name", username),
                platform="instagram",
                followers=followers,
                engagement_rate=round(engagement_rate, 2),
                bio=bio,
                location="Brasil" if is_brazil else "",
                profile_url=f"https://www.instagram.com/{username}/",
                avatar_url="",
                content_description=bio,
                source_hashtag=source_hashtag,
                collected_at=datetime.now().isoformat(),
                raw_data=business
            )
            
        except requests.exceptions.Timeout:
            logger.debug(f"Timeout ao buscar @{username}")
        except Exception as e:
            logger.debug(f"Erro ao buscar @{username}: {e}")
        
        return None


def collect_profiles_from_hashtags(max_per_hashtag: int = 20) -> List[CollectedProfile]:
    """
    Função principal para coletar perfis de hashtags.
    
    Args:
        max_per_hashtag: Máximo de perfis por hashtag
        
    Returns:
        Lista de perfis qualificados (10k+ seguidores, 2.5%+ engajamento)
    """
    collector = HashtagCollector()
    return collector.collect_from_all_hashtags(max_per_hashtag)
