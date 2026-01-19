"""
Módulo principal de prospecção de influenciadores.
Versão 3.0 com análise de IA para identificar pessoas reais.

Foco: Encontrar pessoas reais com sobrepeso/obesidade ou em jornada de emagrecimento,
não páginas comerciais ou profissionais vendendo serviços.
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
from profile_analyzer import ProfileAnalyzer, ProfileType, BodyType
from config import (
    SEARCH_KEYWORDS_PT,
    SEARCH_KEYWORDS_EN,
    SEARCH_KEYWORDS_JOURNEY,
    SEARCH_KEYWORDS_LIFESTYLE,
    SEARCH_KEYWORDS_FASHION,
    SEARCH_KEYWORDS_SELFCARE,
    SEARCH_KEYWORDS_FOOD,
    SEARCH_KEYWORDS_FITNESS,
    RELEVANT_HASHTAGS,
    MIN_ENGAGEMENT_RATE,
    DAILY_PROSPECT_COUNT,
    API_RATE_LIMIT_DELAY,
    DATA_DIR,
    OUTPUT_FILE,
    PREFERRED_SIZES,
    INFLUENCER_SIZE_RANGES,
)

# Importar prospector do Instagram
try:
    from instagram_prospector import InstagramProspector
    INSTAGRAM_AVAILABLE = True
except ImportError:
    INSTAGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)


# Lista expandida de seed influencers - pessoas reais com jornada de emagrecimento
SEED_INFLUENCERS_REAL = [
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


class InfluencerProspectorV3:
    """
    Prospector de influenciadores com análise de IA.
    Foco em encontrar pessoas reais, não páginas comerciais.
    """
    
    def __init__(self):
        """Inicializa o prospector."""
        self.history = HistoryManager()
        self.api_client = None
        self.instagram_prospector = None
        self.profile_analyzer = ProfileAnalyzer()
        self._init_api_clients()
        self.found_influencers: List[Influencer] = []
        self.errors: List[str] = []
        self.seen_usernames: Set[str] = set()
        self.analyzed_profiles: List[Dict] = []
    
    def _init_api_clients(self):
        """Inicializa os clientes de API."""
        # API Manus para TikTok e YouTube
        try:
            from data_api import ApiClient
            self.api_client = ApiClient()
            logger.info("Cliente de API Manus inicializado")
        except ImportError as e:
            logger.warning(f"Não foi possível importar ApiClient: {e}")
            self.api_client = None
        
        # API do Instagram
        if INSTAGRAM_AVAILABLE:
            self.instagram_prospector = InstagramProspector()
            if self.instagram_prospector.is_configured():
                logger.info("Cliente de API Instagram inicializado")
            else:
                logger.warning("Instagram API não configurada")
                self.instagram_prospector = None
        
        # Verificar se análise com IA está disponível
        if self.profile_analyzer.client:
            logger.info("Análise de perfis com IA habilitada")
        else:
            logger.info("Análise de perfis usando método básico")
    
    def _rate_limit(self, delay: float = None):
        """Aplica rate limiting entre chamadas de API."""
        time.sleep(delay or API_RATE_LIMIT_DELAY)
    
    def _get_size_category(self, followers: int) -> str:
        """Retorna a categoria de tamanho do influenciador."""
        for category, (min_f, max_f) in INFLUENCER_SIZE_RANGES.items():
            if min_f <= followers < max_f:
                return category
        return "unknown"
    
    def _is_preferred_size(self, followers: int) -> bool:
        """Verifica se o influenciador está no tamanho preferido."""
        return self._get_size_category(followers) in PREFERRED_SIZES
    
    def search_instagram(self, max_results: int = 20) -> List[Dict]:
        """
        Busca influenciadores no Instagram usando lista de seeds expandida.
        """
        if not self.instagram_prospector:
            logger.info("Instagram API não disponível")
            return []
        
        results = []
        
        try:
            logger.info("Buscando no Instagram...")
            
            # Usar lista expandida de seeds
            all_seeds = SEED_INFLUENCERS_REAL.copy()
            
            # Filtrar usernames já prospectados
            available_usernames = [
                u for u in all_seeds
                if not self.history.is_prospected(u, 'instagram')
                and f"instagram:{u.lower()}" not in self.seen_usernames
            ]
            
            if not available_usernames:
                logger.warning("Todos os usernames da seed list já foram prospectados")
                return results
            
            # Embaralhar para variar os resultados
            random.shuffle(available_usernames)
            
            profiles = self.instagram_prospector.prospect_from_seed_list(
                usernames=available_usernames[:max_results * 2],
                min_followers=1000,
                min_engagement=MIN_ENGAGEMENT_RATE,
                max_results=max_results
            )
            
            for profile in profiles:
                profile_dict = self.instagram_prospector.to_dict(profile)
                
                # Verificar duplicatas
                key = f"instagram:{profile.username.lower()}"
                if key in self.seen_usernames:
                    continue
                self.seen_usernames.add(key)
                
                results.append(profile_dict)
            
            logger.info(f"Instagram: {len(results)} perfis encontrados")
            
        except Exception as e:
            error_msg = f"Erro ao buscar no Instagram: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        return results
    
    def search_tiktok(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """
        Busca no TikTok e extrai informações dos autores.
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
                
                # Extrair estatísticas
                author_stats = item.get('authorStats', {})
                followers = author_stats.get('followerCount', 0)
                hearts = author_stats.get('heartCount', 0)
                video_count = author_stats.get('videoCount', 0)
                
                video_stats = item.get('stats', {})
                likes = video_stats.get('diggCount', 0)
                comments = video_stats.get('commentCount', 0)
                plays = video_stats.get('playCount', 0)
                
                # Calcular engajamento
                if followers > 0 and video_count > 0:
                    avg_likes = hearts / video_count
                    engagement = (avg_likes / followers) * 100
                    engagement = min(engagement, 100)
                elif followers > 0:
                    engagement = ((likes + comments) / followers) * 100
                    engagement = min(engagement, 100)
                else:
                    engagement = 0.0
                
                bio = author.get('signature', '')
                name = author.get('nickname', unique_id)
                
                results.append({
                    'platform': 'tiktok',
                    'username': unique_id,
                    'name': name,
                    'followers': followers,
                    'engagement_rate': round(engagement, 2),
                    'avg_likes': int(hearts / video_count) if video_count > 0 else likes,
                    'avg_comments': comments,
                    'avg_views': plays,
                    'verified': author.get('verified', False),
                    'bio': bio,
                    'url': f"https://www.tiktok.com/@{unique_id}",
                    'source_keyword': keyword,
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
                    
                    key = f"youtube:{channel_id.lower()}"
                    if key in self.seen_usernames:
                        continue
                    self.seen_usernames.add(key)
                    
                    if self.history.is_prospected(channel_id, 'youtube'):
                        continue
                    
                    view_count = video.get('viewCountText', '0')
                    views = self._parse_count(view_count)
                    
                    results.append({
                        'platform': 'youtube',
                        'username': channel_id,
                        'name': channel_title,
                        'followers': 0,
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
        
        multipliers = {'k': 1_000, 'm': 1_000_000, 'mi': 1_000_000, 'mil': 1_000, 'b': 1_000_000_000}
        
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
    
    def analyze_and_filter_profiles(
        self,
        profiles: List[Dict],
        min_partnership_potential: float = 40,
    ) -> List[Dict]:
        """
        Analisa perfis com IA e filtra apenas pessoas reais recomendadas.
        
        Args:
            profiles: Lista de perfis para analisar
            min_partnership_potential: Score mínimo de potencial de parceria
        
        Returns:
            Lista de perfis recomendados
        """
        recommended = []
        
        logger.info(f"Analisando {len(profiles)} perfis com IA...")
        
        for i, profile in enumerate(profiles):
            try:
                analysis = self.profile_analyzer.analyze_profile(
                    username=profile.get('username', ''),
                    name=profile.get('name', ''),
                    bio=profile.get('bio', ''),
                    followers=profile.get('followers', 0),
                    platform=profile.get('platform', 'instagram'),
                )
                
                # Adicionar análise ao perfil
                profile['analysis'] = {
                    'profile_type': analysis.profile_type.value,
                    'body_type': analysis.body_type.value,
                    'is_real_person': analysis.is_real_person,
                    'has_weight_journey': analysis.has_weight_journey,
                    'authenticity_score': analysis.authenticity_score,
                    'partnership_potential': analysis.partnership_potential,
                    'reasoning': analysis.reasoning,
                    'tags': analysis.tags,
                    'recommended': analysis.recommended,
                }
                
                # Filtrar
                if analysis.recommended or analysis.partnership_potential >= min_partnership_potential:
                    # Priorizar pessoas reais
                    if analysis.is_real_person:
                        profile['priority_score'] = analysis.partnership_potential + 50
                    else:
                        profile['priority_score'] = analysis.partnership_potential
                    
                    # Bonus para jornada de peso
                    if analysis.has_weight_journey:
                        profile['priority_score'] += 30
                    
                    # Bonus para tamanho preferido
                    if self._is_preferred_size(profile.get('followers', 0)):
                        profile['priority_score'] += 20
                    
                    recommended.append(profile)
                    logger.debug(f"✓ {profile['username']}: {analysis.reasoning}")
                else:
                    logger.debug(f"✗ {profile['username']}: {analysis.reasoning}")
                
                # Rate limit para API OpenAI
                if self.profile_analyzer.client and i < len(profiles) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Erro ao analisar {profile.get('username', 'unknown')}: {e}")
                continue
        
        logger.info(f"Perfis recomendados após análise: {len(recommended)}")
        
        return recommended
    
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
        
        # Construir notas com análise
        notes_parts = []
        analysis = profile_data.get('analysis', {})
        
        if analysis:
            if analysis.get('is_real_person'):
                notes_parts.append("✓ Pessoa real")
            if analysis.get('has_weight_journey'):
                notes_parts.append("✓ Jornada de emagrecimento")
            if analysis.get('body_type') and analysis['body_type'] != 'desconhecido':
                notes_parts.append(f"Tipo: {analysis['body_type']}")
            if analysis.get('tags'):
                notes_parts.append(f"Tags: {', '.join(analysis['tags'])}")
            if analysis.get('reasoning'):
                notes_parts.append(f"Análise: {analysis['reasoning']}")
        
        if profile_data.get('needs_verification'):
            notes_parts.append("⚠️ Necessita verificação manual")
        
        notes = " | ".join(notes_parts) if notes_parts else ""
        
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
        """
        Executa a prospecção diária com análise de IA.
        
        Prioridade:
        1. Instagram (prioritário)
        2. TikTok
        3. YouTube
        
        Todos os perfis são analisados por IA para identificar pessoas reais.
        """
        start_time = time.time()
        all_profiles: List[Dict] = []
        keywords_used: List[str] = []
        
        logger.info(f"Iniciando prospecção de {target_count} influenciadores (com análise de IA)")
        
        # 1. INSTAGRAM (Prioridade máxima)
        instagram_target = min(target_count, 15)
        instagram_profiles = self.search_instagram(max_results=instagram_target)
        all_profiles.extend(instagram_profiles)
        
        # 2. TIKTOK - Usar keywords expandidas
        # Combinar diferentes categorias de keywords
        tiktok_keywords = []
        tiktok_keywords.extend(random.sample(SEARCH_KEYWORDS_JOURNEY, min(3, len(SEARCH_KEYWORDS_JOURNEY))))
        tiktok_keywords.extend(random.sample(SEARCH_KEYWORDS_LIFESTYLE, min(2, len(SEARCH_KEYWORDS_LIFESTYLE))))
        tiktok_keywords.extend(random.sample(SEARCH_KEYWORDS_FASHION, min(2, len(SEARCH_KEYWORDS_FASHION))))
        tiktok_keywords.extend(random.sample(SEARCH_KEYWORDS_SELFCARE, min(1, len(SEARCH_KEYWORDS_SELFCARE))))
        tiktok_keywords.extend(random.sample(SEARCH_KEYWORDS_FOOD, min(1, len(SEARCH_KEYWORDS_FOOD))))
        tiktok_keywords.extend(random.sample(SEARCH_KEYWORDS_EN, min(2, len(SEARCH_KEYWORDS_EN))))
        
        random.shuffle(tiktok_keywords)
        
        for keyword in tiktok_keywords[:10]:
            if len(all_profiles) >= target_count * 3:
                break
            
            keywords_used.append(keyword)
            tiktok_results = self.search_tiktok(keyword, max_results=10)
            all_profiles.extend(tiktok_results)
            
            self._rate_limit(0.3)
        
        # 3. YOUTUBE
        youtube_keywords = (
            SEARCH_KEYWORDS_JOURNEY[:3] +
            SEARCH_KEYWORDS_LIFESTYLE[:2] +
            SEARCH_KEYWORDS_FASHION[:2]
        )
        random.shuffle(youtube_keywords)
        
        for keyword in youtube_keywords[:5]:
            if len(all_profiles) >= target_count * 3:
                break
            
            if keyword not in keywords_used:
                keywords_used.append(keyword)
            
            youtube_results = self.search_youtube(keyword, max_results=8)
            all_profiles.extend(youtube_results)
            
            self._rate_limit(0.3)
        
        logger.info(f"Total de perfis encontrados: {len(all_profiles)}")
        
        # ANÁLISE COM IA
        # Filtrar primeiro por engajamento mínimo
        qualified_engagement = [
            p for p in all_profiles
            if p.get('engagement_rate', 0) >= MIN_ENGAGEMENT_RATE or p.get('needs_verification')
        ]
        
        logger.info(f"Perfis com engajamento qualificado: {len(qualified_engagement)}")
        
        # Analisar com IA para identificar pessoas reais
        recommended_profiles = self.analyze_and_filter_profiles(
            qualified_engagement,
            min_partnership_potential=40
        )
        
        # Se não tiver suficientes, analisar os outros também
        if len(recommended_profiles) < target_count:
            remaining_profiles = [
                p for p in all_profiles
                if p not in qualified_engagement
            ]
            
            additional = self.analyze_and_filter_profiles(
                remaining_profiles[:target_count * 2],
                min_partnership_potential=30
            )
            
            recommended_profiles.extend(additional)
        
        # Ordenar por priority_score (pessoas reais com jornada de peso primeiro)
        recommended_profiles.sort(
            key=lambda x: (
                -x.get('priority_score', 0),
                {'instagram': 0, 'tiktok': 1, 'youtube': 2}.get(x['platform'], 3),
                -x.get('engagement_rate', 0)
            )
        )
        
        # Selecionar os melhores
        selected = recommended_profiles[:target_count]
        
        logger.info(f"Perfis selecionados: {len(selected)}")
        
        # Converter para objetos Influencer
        influencers = []
        for profile in selected:
            influencer = self._convert_to_influencer(profile)
            influencers.append(influencer)
            
            self.history.add_prospected(
                username=profile['username'],
                platform=profile['platform'],
                name=profile.get('name', profile['username']),
                metadata={
                    'engagement_rate': profile.get('engagement_rate', 0),
                    'followers': profile.get('followers', 0),
                    'analysis': profile.get('analysis', {}),
                }
            )
        
        execution_time = time.time() - start_time
        
        # Estatísticas
        total_qualified = len([p for p in all_profiles if p.get('engagement_rate', 0) >= MIN_ENGAGEMENT_RATE])
        
        # Criar resultado
        result = ProspectionResult(
            influencers=influencers,
            total_found=len(all_profiles),
            total_qualified=total_qualified,
            keywords_used=keywords_used,
            execution_time_seconds=execution_time,
            errors=self.errors,
        )
        
        self.history.add_daily_run({
            'influencers_count': len(influencers),
            'total_found': len(all_profiles),
            'total_qualified': total_qualified,
            'total_analyzed': len(qualified_engagement),
            'total_recommended': len(recommended_profiles),
            'execution_time': execution_time,
            'ai_analysis_enabled': self.profile_analyzer.client is not None,
        })
        
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
    
    prospector = InfluencerProspectorV3()
    result = prospector.run_prospection(target_count=20)
    
    print("\n" + "=" * 60)
    print("RESULTADO DA PROSPECÇÃO (V3 - COM ANÁLISE DE IA)")
    print("=" * 60)
    print(f"Data: {result.date}")
    print(f"Total encontrados: {result.total_found}")
    print(f"Total qualificados: {result.total_qualified}")
    print(f"Influenciadores selecionados: {len(result.influencers)}")
    print(f"Tempo de execução: {result.execution_time_seconds:.2f}s")
    
    # Contar por plataforma
    platforms = {}
    for inf in result.influencers:
        p = inf.primary_platform.value
        platforms[p] = platforms.get(p, 0) + 1
    
    print(f"\nPor plataforma:")
    for p, count in sorted(platforms.items()):
        print(f"  - {p.capitalize()}: {count}")
    
    print("\n" + "-" * 60)
    print("INFLUENCIADORES (PESSOAS REAIS):")
    print("-" * 60)
    
    for i, inf in enumerate(result.influencers, 1):
        profile = inf.profiles[0] if inf.profiles else None
        platform = inf.primary_platform.value.upper()
        followers = f"{profile.followers:,}" if profile else "N/A"
        engagement = f"{profile.engagement_rate}%" if profile else "N/A"
        
        print(f"\n{i:2}. [{platform:9}] {inf.name[:35]}")
        print(f"    Seguidores: {followers} | Engajamento: {engagement}")
        if profile:
            print(f"    URL: {profile.url}")
        if inf.bio:
            print(f"    Bio: {inf.bio[:80]}...")
        if inf.notes:
            print(f"    Notas: {inf.notes[:100]}...")
    
    return result


if __name__ == "__main__":
    main()
