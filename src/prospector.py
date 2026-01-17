"""
Módulo principal de prospecção de influenciadores.
Utiliza APIs disponíveis para TikTok e YouTube.
"""

import sys
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
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
    MAX_RETRIES,
    DATA_DIR,
    OUTPUT_FILE,
)

logger = logging.getLogger(__name__)


class InfluencerProspector:
    """Classe principal para prospecção de influenciadores."""
    
    def __init__(self):
        """Inicializa o prospector."""
        self.history = HistoryManager()
        self.api_client = None
        self._init_api_client()
        self.found_influencers: List[Influencer] = []
        self.errors: List[str] = []
    
    def _init_api_client(self):
        """Inicializa o cliente de API."""
        try:
            from data_api import ApiClient
            self.api_client = ApiClient()
            logger.info("Cliente de API inicializado com sucesso")
        except ImportError as e:
            logger.warning(f"Não foi possível importar ApiClient: {e}")
            self.api_client = None
    
    def _rate_limit(self):
        """Aplica rate limiting entre chamadas de API."""
        time.sleep(API_RATE_LIMIT_DELAY + random.uniform(0, 0.5))
    
    def _calculate_engagement_rate(
        self, 
        followers: int, 
        avg_likes: int, 
        avg_comments: int = 0,
        avg_views: int = 0
    ) -> float:
        """
        Calcula a taxa de engajamento.
        
        Para Instagram/TikTok: (likes + comments) / followers * 100
        Para YouTube: (likes + comments) / views * 100 ou likes / subscribers * 100
        
        Args:
            followers: Número de seguidores/inscritos.
            avg_likes: Média de curtidas.
            avg_comments: Média de comentários.
            avg_views: Média de visualizações (para YouTube).
            
        Returns:
            Taxa de engajamento em porcentagem.
        """
        if followers == 0:
            return 0.0
        
        engagement = (avg_likes + avg_comments) / followers * 100
        return round(engagement, 2)
    
    def search_tiktok(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        Busca influenciadores no TikTok por palavra-chave.
        
        Args:
            keyword: Palavra-chave para busca.
            max_results: Número máximo de resultados.
            
        Returns:
            Lista de perfis encontrados.
        """
        if not self.api_client:
            logger.warning("API client não disponível para TikTok")
            return []
        
        results = []
        
        try:
            logger.info(f"Buscando no TikTok: {keyword}")
            
            response = self.api_client.call_api(
                'Tiktok/search_tiktok_video_general',
                query={'keyword': keyword}
            )
            
            self._rate_limit()
            
            if not response or 'data' not in response:
                return results
            
            videos = response.get('data', [])
            seen_users = set()
            
            for video in videos[:max_results]:
                author = video.get('author', {})
                unique_id = author.get('uniqueId', '')
                
                if not unique_id or unique_id in seen_users:
                    continue
                
                seen_users.add(unique_id)
                
                # Verificar se já foi prospectado
                if self.history.is_prospected(unique_id, 'tiktok'):
                    continue
                
                # Extrair métricas
                stats = video.get('stats', {})
                author_stats = video.get('authorStats', {})
                
                followers = author_stats.get('followerCount', 0)
                likes = stats.get('diggCount', 0)
                comments = stats.get('commentCount', 0)
                views = stats.get('playCount', 0)
                
                # Calcular engajamento
                if followers > 0:
                    engagement = self._calculate_engagement_rate(
                        followers, likes, comments
                    )
                else:
                    engagement = 0.0
                
                results.append({
                    'platform': 'tiktok',
                    'username': unique_id,
                    'name': author.get('nickname', unique_id),
                    'followers': followers,
                    'engagement_rate': engagement,
                    'avg_likes': likes,
                    'avg_comments': comments,
                    'avg_views': views,
                    'verified': author.get('verified', False),
                    'bio': author.get('signature', ''),
                    'url': f"https://www.tiktok.com/@{unique_id}",
                    'source_keyword': keyword,
                })
            
            logger.info(f"TikTok: Encontrados {len(results)} perfis para '{keyword}'")
            
        except Exception as e:
            error_msg = f"Erro ao buscar no TikTok: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return results
    
    def search_youtube(self, keyword: str, max_results: int = 30) -> List[Dict]:
        """
        Busca influenciadores no YouTube por palavra-chave.
        
        Args:
            keyword: Palavra-chave para busca.
            max_results: Número máximo de resultados.
            
        Returns:
            Lista de perfis encontrados.
        """
        if not self.api_client:
            logger.warning("API client não disponível para YouTube")
            return []
        
        results = []
        
        try:
            logger.info(f"Buscando no YouTube: {keyword}")
            
            response = self.api_client.call_api(
                'Youtube/search',
                query={
                    'q': keyword,
                    'hl': 'pt',
                    'gl': 'BR'
                }
            )
            
            self._rate_limit()
            
            if not response:
                return results
            
            contents = response.get('contents', [])
            seen_channels = set()
            
            for content in contents[:max_results]:
                if content.get('type') != 'channel':
                    # Tentar extrair canal do vídeo
                    if content.get('type') == 'video':
                        video = content.get('video', {})
                        channel_id = video.get('channelId', '')
                        channel_title = video.get('channelTitle', '')
                        
                        if channel_id and channel_id not in seen_channels:
                            seen_channels.add(channel_id)
                            
                            # Verificar se já foi prospectado
                            if self.history.is_prospected(channel_id, 'youtube'):
                                continue
                            
                            # Buscar detalhes do canal
                            channel_details = self._get_youtube_channel_details(channel_id)
                            
                            if channel_details:
                                results.append(channel_details)
                    continue
                
                channel = content.get('channel', {})
                channel_id = channel.get('channelId', '')
                
                if not channel_id or channel_id in seen_channels:
                    continue
                
                seen_channels.add(channel_id)
                
                # Verificar se já foi prospectado
                if self.history.is_prospected(channel_id, 'youtube'):
                    continue
                
                # Extrair informações básicas
                subscribers_text = channel.get('subscriberCountText', '0')
                subscribers = self._parse_subscriber_count(subscribers_text)
                
                results.append({
                    'platform': 'youtube',
                    'username': channel_id,
                    'name': channel.get('title', ''),
                    'followers': subscribers,
                    'engagement_rate': 0.0,  # Será calculado depois
                    'avg_likes': 0,
                    'avg_comments': 0,
                    'avg_views': 0,
                    'verified': False,
                    'bio': channel.get('descriptionSnippet', ''),
                    'url': f"https://www.youtube.com/channel/{channel_id}",
                    'source_keyword': keyword,
                })
            
            logger.info(f"YouTube: Encontrados {len(results)} canais para '{keyword}'")
            
        except Exception as e:
            error_msg = f"Erro ao buscar no YouTube: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return results
    
    def _get_youtube_channel_details(self, channel_id: str) -> Optional[Dict]:
        """
        Obtém detalhes de um canal do YouTube.
        
        Args:
            channel_id: ID do canal.
            
        Returns:
            Dicionário com detalhes do canal ou None.
        """
        if not self.api_client:
            return None
        
        try:
            response = self.api_client.call_api(
                'Youtube/get_channel_details',
                query={'id': channel_id, 'hl': 'pt'}
            )
            
            self._rate_limit()
            
            if not response:
                return None
            
            stats = response.get('stats', {})
            subscribers = stats.get('subscribers', 0)
            views = stats.get('views', 0)
            videos = stats.get('videos', 0)
            
            # Estimar engajamento baseado em views/subscribers
            if subscribers > 0 and videos > 0:
                avg_views_per_video = views / videos if videos > 0 else 0
                engagement = (avg_views_per_video / subscribers) * 100
                engagement = min(engagement, 100)  # Cap em 100%
            else:
                engagement = 0.0
            
            return {
                'platform': 'youtube',
                'username': channel_id,
                'name': response.get('title', ''),
                'followers': subscribers,
                'engagement_rate': round(engagement, 2),
                'avg_likes': 0,
                'avg_comments': 0,
                'avg_views': int(views / videos) if videos > 0 else 0,
                'verified': 'verified' in response.get('badges', []),
                'bio': response.get('description', '')[:500],
                'url': f"https://www.youtube.com/channel/{channel_id}",
                'source_keyword': '',
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do canal {channel_id}: {e}")
            return None
    
    def _parse_subscriber_count(self, text: str) -> int:
        """
        Converte texto de contagem de inscritos para número.
        
        Args:
            text: Texto como "1.5M subscribers" ou "500K".
            
        Returns:
            Número de inscritos.
        """
        if not text:
            return 0
        
        text = text.lower().replace(' subscribers', '').replace(' inscritos', '')
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
            return int(float(text))
        except ValueError:
            return 0
    
    def get_tiktok_user_details(self, username: str) -> Optional[Dict]:
        """
        Obtém detalhes de um usuário do TikTok.
        
        Args:
            username: Nome de usuário do TikTok.
            
        Returns:
            Dicionário com detalhes do usuário ou None.
        """
        if not self.api_client:
            return None
        
        try:
            response = self.api_client.call_api(
                'Tiktok/get_user_info',
                query={'uniqueId': username}
            )
            
            self._rate_limit()
            
            if not response or 'userInfo' not in response:
                return None
            
            user_info = response.get('userInfo', {})
            user = user_info.get('user', {})
            stats = user_info.get('stats', {})
            
            followers = stats.get('followerCount', 0)
            hearts = stats.get('heartCount', 0)
            videos = stats.get('videoCount', 0)
            
            # Calcular engajamento estimado
            if followers > 0 and videos > 0:
                avg_likes = hearts / videos if videos > 0 else 0
                engagement = (avg_likes / followers) * 100
            else:
                engagement = 0.0
            
            return {
                'platform': 'tiktok',
                'username': user.get('uniqueId', username),
                'name': user.get('nickname', username),
                'followers': followers,
                'engagement_rate': round(engagement, 2),
                'avg_likes': int(hearts / videos) if videos > 0 else 0,
                'avg_comments': 0,
                'avg_views': 0,
                'verified': user.get('verified', False),
                'bio': user.get('signature', ''),
                'url': f"https://www.tiktok.com/@{username}",
                'sec_uid': user.get('secUid', ''),
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do TikTok user {username}: {e}")
            return None
    
    def _filter_qualified_profiles(
        self, 
        profiles: List[Dict], 
        min_engagement: float = MIN_ENGAGEMENT_RATE,
        include_unverified: bool = True
    ) -> List[Dict]:
        """
        Filtra perfis que atendem aos critérios mínimos.
        
        Args:
            profiles: Lista de perfis.
            min_engagement: Taxa mínima de engajamento.
            include_unverified: Incluir perfis sem dados de engajamento.
            
        Returns:
            Lista de perfis qualificados.
        """
        qualified = []
        
        for profile in profiles:
            engagement = profile.get('engagement_rate', 0)
            followers = profile.get('followers', 0)
            
            # Verificar engajamento
            if engagement >= min_engagement:
                profile['qualification_status'] = 'qualified'
                qualified.append(profile)
            # Se não temos dados de engajamento mas tem seguidores, incluir para verificação
            elif include_unverified and engagement == 0 and followers >= 1000:
                profile['qualification_status'] = 'needs_verification'
                profile['needs_verification'] = True
                qualified.append(profile)
            # Incluir perfis com engajamento baixo mas significativo número de seguidores
            elif followers >= 10000 and engagement > 0:
                profile['qualification_status'] = 'potential'
                profile['needs_verification'] = True
                qualified.append(profile)
        
        return qualified
    
    def _convert_to_influencer(self, profile_data: Dict) -> Influencer:
        """
        Converte dados de perfil para objeto Influencer.
        
        Args:
            profile_data: Dicionário com dados do perfil.
            
        Returns:
            Objeto Influencer.
        """
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
        
        influencer = Influencer(
            name=profile_data.get('name', profile_data['username']),
            primary_platform=platform,
            profiles=[social_profile],
            bio=profile_data.get('bio', ''),
            source_keyword=profile_data.get('source_keyword', ''),
        )
        
        return influencer
    
    def run_prospection(self, target_count: int = DAILY_PROSPECT_COUNT) -> ProspectionResult:
        """
        Executa a prospecção diária de influenciadores.
        
        Args:
            target_count: Número de influenciadores a prospectar.
            
        Returns:
            Resultado da prospecção.
        """
        start_time = time.time()
        all_profiles: List[Dict] = []
        keywords_used: List[str] = []
        
        logger.info(f"Iniciando prospecção de {target_count} influenciadores")
        
        # Combinar keywords em português e inglês
        all_keywords = SEARCH_KEYWORDS_PT + SEARCH_KEYWORDS_EN
        random.shuffle(all_keywords)
        
        # Buscar até ter perfis suficientes
        for keyword in all_keywords:
            if len(all_profiles) >= target_count * 3:  # Buscar 3x mais para ter margem
                break
            
            keywords_used.append(keyword)
            
            # Buscar no TikTok
            tiktok_results = self.search_tiktok(keyword)
            all_profiles.extend(tiktok_results)
            
            # Buscar no YouTube
            youtube_results = self.search_youtube(keyword)
            all_profiles.extend(youtube_results)
        
        logger.info(f"Total de perfis encontrados: {len(all_profiles)}")
        
        # Remover duplicatas
        seen = set()
        unique_profiles = []
        for profile in all_profiles:
            key = f"{profile['platform']}:{profile['username']}"
            if key not in seen:
                seen.add(key)
                unique_profiles.append(profile)
        
        logger.info(f"Perfis únicos: {len(unique_profiles)}")
        
        # Filtrar por engajamento
        qualified_profiles = self._filter_qualified_profiles(unique_profiles)
        logger.info(f"Perfis qualificados (engajamento >= {MIN_ENGAGEMENT_RATE}%): {len(qualified_profiles)}")
        
        # Ordenar por engajamento
        qualified_profiles.sort(key=lambda x: x.get('engagement_rate', 0), reverse=True)
        
        # Selecionar os melhores
        selected_profiles = qualified_profiles[:target_count]
        
        # Converter para objetos Influencer
        influencers = []
        for profile in selected_profiles:
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
            total_qualified=len(qualified_profiles),
            keywords_used=keywords_used,
            execution_time_seconds=execution_time,
            errors=self.errors,
        )
        
        # Registrar execução
        self.history.add_daily_run({
            'influencers_count': len(influencers),
            'total_found': len(all_profiles),
            'total_qualified': len(qualified_profiles),
            'execution_time': execution_time,
        })
        
        # Salvar resultado
        self._save_result(result)
        
        logger.info(f"Prospecção concluída: {len(influencers)} influenciadores em {execution_time:.2f}s")
        
        return result
    
    def _save_result(self, result: ProspectionResult):
        """Salva o resultado da prospecção em arquivo."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Salvar resultado do dia
        output_file = DATA_DIR / f"prospects_{result.date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Atualizar arquivo de saída principal
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultado salvo em {output_file}")


def main():
    """Função principal para execução do prospector."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                Path(__file__).parent.parent / 'logs' / f'prospection_{datetime.now().strftime("%Y%m%d")}.log'
            ),
        ]
    )
    
    # Executar prospecção
    prospector = InfluencerProspector()
    result = prospector.run_prospection()
    
    # Exibir resumo
    print("\n" + "=" * 60)
    print("RESULTADO DA PROSPECÇÃO")
    print("=" * 60)
    print(f"Data: {result.date}")
    print(f"Total encontrados: {result.total_found}")
    print(f"Total qualificados: {result.total_qualified}")
    print(f"Influenciadores selecionados: {len(result.influencers)}")
    print(f"Tempo de execução: {result.execution_time_seconds:.2f}s")
    
    if result.errors:
        print(f"\nErros: {len(result.errors)}")
        for error in result.errors[:5]:
            print(f"  - {error}")
    
    print("\n" + "-" * 60)
    print("INFLUENCIADORES PROSPECTADOS:")
    print("-" * 60)
    
    for i, influencer in enumerate(result.influencers, 1):
        profile = influencer.profiles[0] if influencer.profiles else None
        print(f"\n{i}. {influencer.name}")
        print(f"   Plataforma: {influencer.primary_platform.value}")
        if profile:
            print(f"   Username: @{profile.username}")
            print(f"   Seguidores: {profile.followers:,}")
            print(f"   Engajamento: {profile.engagement_rate}%")
            print(f"   URL: {profile.url}")
    
    return result


if __name__ == "__main__":
    main()
