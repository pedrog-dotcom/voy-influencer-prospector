"""
Módulo otimizado de prospecção de influenciadores.
Versão 2.0 com estrutura correta das APIs.
"""

import sys
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

# Adicionar caminho da API Manus
sys.path.append('/opt/.manus/.sandbox-runtime')

from models import Influencer, SocialProfile, Platform, ProspectionResult
from history_manager import HistoryManager
from config import (
    SEARCH_KEYWORDS_PT,
    SEARCH_KEYWORDS_EN,
    MIN_ENGAGEMENT_RATE,
    DAILY_PROSPECT_COUNT,
    API_RATE_LIMIT_DELAY,
    DATA_DIR,
    OUTPUT_FILE,
)

logger = logging.getLogger(__name__)


class InfluencerProspectorV2:
    """Classe otimizada para prospecção de influenciadores."""
    
    def __init__(self):
        """Inicializa o prospector."""
        self.history = HistoryManager()
        self.api_client = None
        self._init_api_client()
        self.found_influencers: List[Influencer] = []
        self.errors: List[str] = []
        self.seen_usernames: Set[str] = set()
    
    def _init_api_client(self):
        """Inicializa o cliente de API."""
        try:
            from data_api import ApiClient
            self.api_client = ApiClient()
            logger.info("Cliente de API inicializado com sucesso")
        except ImportError as e:
            logger.warning(f"Não foi possível importar ApiClient: {e}")
            self.api_client = None
    
    def _rate_limit(self, delay: float = None):
        """Aplica rate limiting entre chamadas de API."""
        time.sleep(delay or API_RATE_LIMIT_DELAY)
    
    def search_tiktok(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """
        Busca no TikTok e extrai informações dos autores.
        
        A estrutura da API é:
        - data[].item.author (dados do autor)
        - data[].item.stats (estatísticas do vídeo)
        - data[].item.authorStats (estatísticas do autor)
        """
        if not self.api_client:
            return []
        
        results = []
        
        try:
            logger.info(f"Buscando no TikTok: {keyword}")
            
            response = self.api_client.call_api(
                'Tiktok/search_tiktok_video_general',
                query={'keyword': keyword}
            )
            
            self._rate_limit(0.5)
            
            if not response or 'data' not in response:
                return results
            
            videos = response.get('data', [])
            
            for video_data in videos[:max_results]:
                # A estrutura correta é data[].item
                item = video_data.get('item', {})
                if not item:
                    continue
                
                author = item.get('author', {})
                unique_id = author.get('uniqueId', '')
                
                if not unique_id:
                    continue
                
                # Verificar duplicatas
                key = f"tiktok:{unique_id.lower()}"
                if key in self.seen_usernames:
                    continue
                self.seen_usernames.add(key)
                
                # Verificar histórico
                if self.history.is_prospected(unique_id, 'tiktok'):
                    continue
                
                # Extrair estatísticas do autor
                author_stats = item.get('authorStats', {})
                followers = author_stats.get('followerCount', 0)
                hearts = author_stats.get('heartCount', 0)
                video_count = author_stats.get('videoCount', 0)
                
                # Estatísticas do vídeo
                video_stats = item.get('stats', {})
                likes = video_stats.get('diggCount', 0)
                comments = video_stats.get('commentCount', 0)
                plays = video_stats.get('playCount', 0)
                
                # Calcular engajamento
                # Método 1: baseado em total de hearts / followers
                if followers > 0 and video_count > 0:
                    avg_likes = hearts / video_count
                    engagement = (avg_likes / followers) * 100
                    engagement = min(engagement, 100)
                # Método 2: baseado no vídeo atual
                elif followers > 0:
                    engagement = ((likes + comments) / followers) * 100
                    engagement = min(engagement, 100)
                else:
                    engagement = 0.0
                
                results.append({
                    'platform': 'tiktok',
                    'username': unique_id,
                    'name': author.get('nickname', unique_id),
                    'followers': followers,
                    'engagement_rate': round(engagement, 2),
                    'avg_likes': int(hearts / video_count) if video_count > 0 else likes,
                    'avg_comments': comments,
                    'avg_views': plays,
                    'verified': author.get('verified', False),
                    'bio': author.get('signature', ''),
                    'url': f"https://www.tiktok.com/@{unique_id}",
                    'source_keyword': keyword,
                    'total_hearts': hearts,
                    'video_count': video_count,
                })
            
            logger.info(f"TikTok: {len(results)} perfis para '{keyword}'")
            
        except Exception as e:
            error_msg = f"Erro ao buscar no TikTok: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return results
    
    def search_youtube(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """Busca canais no YouTube."""
        if not self.api_client:
            return []
        
        results = []
        
        try:
            logger.info(f"Buscando no YouTube: {keyword}")
            
            response = self.api_client.call_api(
                'Youtube/search',
                query={'q': keyword, 'hl': 'pt', 'gl': 'BR'}
            )
            
            self._rate_limit(0.5)
            
            if not response or 'contents' not in response:
                return results
            
            contents = response.get('contents', [])
            
            for content in contents:
                if content.get('type') == 'video':
                    video = content.get('video', {})
                    channel_id = video.get('channelId', '')
                    channel_title = video.get('channelTitle', '')
                    
                    if not channel_id:
                        continue
                    
                    # Verificar duplicatas
                    key = f"youtube:{channel_id.lower()}"
                    if key in self.seen_usernames:
                        continue
                    self.seen_usernames.add(key)
                    
                    # Verificar histórico
                    if self.history.is_prospected(channel_id, 'youtube'):
                        continue
                    
                    # Extrair visualizações do vídeo
                    view_count = video.get('viewCountText', '0')
                    views = self._parse_count(view_count)
                    
                    # Criar perfil
                    results.append({
                        'platform': 'youtube',
                        'username': channel_id,
                        'name': channel_title,
                        'followers': 0,  # Não disponível na busca
                        'engagement_rate': 0.0,
                        'avg_likes': 0,
                        'avg_comments': 0,
                        'avg_views': views,
                        'verified': False,
                        'bio': '',
                        'url': f"https://www.youtube.com/channel/{channel_id}",
                        'source_keyword': keyword,
                        'needs_verification': True,
                    })
                    
                    if len(results) >= max_results:
                        break
            
            logger.info(f"YouTube: {len(results)} canais para '{keyword}'")
            
        except Exception as e:
            error_msg = f"Erro ao buscar no YouTube: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return results
    
    def _parse_count(self, text: str) -> int:
        """Converte texto de contagem para número."""
        if not text:
            return 0
        
        text = text.lower().replace(' views', '').replace(' visualizações', '')
        text = text.replace(',', '.').strip()
        
        multipliers = {
            'k': 1_000,
            'm': 1_000_000,
            'mi': 1_000_000,
            'mil': 1_000,
            'b': 1_000_000_000,
        }
        
        for suffix, multiplier in multipliers.items():
            if suffix in text:
                try:
                    number = float(text.replace(suffix, '').strip())
                    return int(number * multiplier)
                except ValueError:
                    pass
        
        try:
            return int(float(text.replace('.', '').replace(',', '')))
        except ValueError:
            return 0
    
    def _convert_to_influencer(self, profile_data: Dict) -> Influencer:
        """Converte dados de perfil para objeto Influencer."""
        platform = Platform(profile_data['platform'])
        
        social_profile = SocialProfile(
            platform=platform,
            username=profile_data['username'],
            url=profile_data['url'],
            followers=profile_data.get('followers', 0),
            engagement_rate=profile_data.get('engagement_rate', 0.0),
            avg_likes=profile_data.get('avg_likes', 0),
            avg_comments=profile_data.get('avg_comments', 0),
            avg_views=profile_data.get('avg_views', 0),
            verified=profile_data.get('verified', False),
        )
        
        notes = ""
        if profile_data.get('needs_verification'):
            notes = "Necessita verificação manual de engajamento"
        
        influencer = Influencer(
            name=profile_data.get('name', profile_data['username']),
            primary_platform=platform,
            profiles=[social_profile],
            bio=profile_data.get('bio', ''),
            source_keyword=profile_data.get('source_keyword', ''),
            notes=notes,
        )
        
        return influencer
    
    def run_prospection(self, target_count: int = DAILY_PROSPECT_COUNT) -> ProspectionResult:
        """Executa a prospecção diária."""
        start_time = time.time()
        all_profiles: List[Dict] = []
        keywords_used: List[str] = []
        
        logger.info(f"Iniciando prospecção de {target_count} influenciadores")
        
        # Selecionar keywords aleatórias
        all_keywords = SEARCH_KEYWORDS_PT[:10] + SEARCH_KEYWORDS_EN[:5]
        random.shuffle(all_keywords)
        
        # Buscar até ter perfis suficientes
        for keyword in all_keywords:
            if len(all_profiles) >= target_count * 2:
                break
            
            keywords_used.append(keyword)
            
            # Buscar no TikTok
            tiktok_results = self.search_tiktok(keyword, max_results=15)
            all_profiles.extend(tiktok_results)
            
            # Buscar no YouTube
            youtube_results = self.search_youtube(keyword, max_results=10)
            all_profiles.extend(youtube_results)
            
            # Pausa entre keywords
            self._rate_limit(0.3)
        
        logger.info(f"Total de perfis encontrados: {len(all_profiles)}")
        
        # Separar por qualificação
        qualified = [p for p in all_profiles if p.get('engagement_rate', 0) >= MIN_ENGAGEMENT_RATE]
        potential = [p for p in all_profiles if p.get('engagement_rate', 0) < MIN_ENGAGEMENT_RATE and p.get('followers', 0) > 0]
        unverified = [p for p in all_profiles if p.get('needs_verification', False)]
        
        logger.info(f"Qualificados: {len(qualified)}, Potenciais: {len(potential)}, Não verificados: {len(unverified)}")
        
        # Ordenar por engajamento/seguidores
        qualified.sort(key=lambda x: x.get('engagement_rate', 0), reverse=True)
        potential.sort(key=lambda x: x.get('followers', 0), reverse=True)
        unverified.sort(key=lambda x: x.get('avg_views', 0), reverse=True)
        
        # Selecionar os melhores
        selected = qualified[:target_count]
        
        # Completar com potenciais se necessário
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            selected.extend(potential[:remaining])
        
        # Completar com não verificados se necessário
        if len(selected) < target_count:
            remaining = target_count - len(selected)
            selected.extend(unverified[:remaining])
        
        # Converter para objetos Influencer
        influencers = []
        for profile in selected:
            influencer = self._convert_to_influencer(profile)
            influencers.append(influencer)
            
            # Adicionar ao histórico
            self.history.add_prospected(
                username=profile['username'],
                platform=profile['platform'],
                name=profile.get('name', profile['username']),
                metadata={
                    'engagement_rate': profile.get('engagement_rate', 0),
                    'followers': profile.get('followers', 0),
                }
            )
        
        execution_time = time.time() - start_time
        
        # Criar resultado
        result = ProspectionResult(
            influencers=influencers,
            total_found=len(all_profiles),
            total_qualified=len(qualified),
            keywords_used=keywords_used,
            execution_time_seconds=execution_time,
            errors=self.errors,
        )
        
        # Registrar execução
        self.history.add_daily_run({
            'influencers_count': len(influencers),
            'total_found': len(all_profiles),
            'total_qualified': len(qualified),
            'execution_time': execution_time,
        })
        
        # Salvar resultado
        self._save_result(result)
        
        logger.info(f"Prospecção concluída: {len(influencers)} influenciadores em {execution_time:.2f}s")
        
        return result
    
    def _save_result(self, result: ProspectionResult):
        """Salva o resultado da prospecção."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        output_file = DATA_DIR / f"prospects_{result.date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultado salvo em {output_file}")


def main():
    """Função principal."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    prospector = InfluencerProspectorV2()
    result = prospector.run_prospection(target_count=20)
    
    print("\n" + "=" * 60)
    print("RESULTADO DA PROSPECÇÃO")
    print("=" * 60)
    print(f"Data: {result.date}")
    print(f"Total encontrados: {result.total_found}")
    print(f"Total qualificados: {result.total_qualified}")
    print(f"Influenciadores selecionados: {len(result.influencers)}")
    print(f"Tempo de execução: {result.execution_time_seconds:.2f}s")
    
    print("\n" + "-" * 60)
    print("INFLUENCIADORES:")
    print("-" * 60)
    
    for i, inf in enumerate(result.influencers, 1):
        profile = inf.profiles[0] if inf.profiles else None
        platform = inf.primary_platform.value.upper()
        followers = f"{profile.followers:,}" if profile else "N/A"
        engagement = f"{profile.engagement_rate}%" if profile else "N/A"
        
        print(f"{i:2}. [{platform:7}] {inf.name[:30]:30} | "
              f"Seg: {followers:>12} | Eng: {engagement:>7}")
        if profile:
            print(f"    URL: {profile.url}")
    
    return result


if __name__ == "__main__":
    main()
