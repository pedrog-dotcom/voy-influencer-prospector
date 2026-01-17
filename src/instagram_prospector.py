"""
Módulo de prospecção de influenciadores do Instagram.
Utiliza a Graph API do Meta para Business Discovery.

Estratégia:
1. Manter lista de usernames conhecidos do nicho
2. Usar Business Discovery para obter métricas detalhadas
3. Calcular taxa de engajamento baseada nas últimas postagens
"""

import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configurações da API
GRAPH_API_BASE_URL = "https://graph.facebook.com/v19.0"
DEFAULT_RATE_LIMIT_DELAY = 1.0

# Lista de influenciadores conhecidos do nicho de emagrecimento/saúde para prospecção
# Esta lista pode ser expandida manualmente ou via outras fontes
SEED_INFLUENCERS = [
    # Influenciadores de emagrecimento e transformação corporal
    "draanneloures",
    "dralucianaricks",
    "drfelipebarros",
    "nutri.larissagomes",
    "nutricionistapatricia",
    "emagrecendocomamanda",
    "jornadadacarol",
    "transformacaodalu",
    "vidasaudavelcomana",
    "projetoverao2024",
    "emagrecimentoreal",
    "dietaflexivel",
    "lowcarbcomamor",
    "jejumintermitente",
    "mudancadehabitos",
    "saudenaprática",
    "corpoemtransformacao",
    "antesedepoisreal",
    "perdapesocomigo",
    "foconadieta",
    "motivacaofitness",
    "emagrecercomsaude",
    "nutricionistabrasil",
    "personaltrainerbr",
    "fitnessmotivacao",
    "bariátrica",
    "cirurgiabariatrica",
    "ozempicbrasil",
    "mounjaro_br",
    "wegovy_brasil",
    "semaglutida",
    "reeducacaoalimentar",
    "alimentacaosaudavel",
    "vidasaudavel",
    "qualidadedevida",
    "bemestar",
    "saudemental",
    "autoestima",
    "aceitacaocorporal",
    "bodypositive_br",
    "transformacao",
]


@dataclass
class InstagramProfile:
    """Representa um perfil do Instagram."""
    username: str
    user_id: str
    followers_count: int
    media_count: int
    biography: str = ""
    engagement_rate: float = 0.0
    avg_likes: int = 0
    avg_comments: int = 0
    profile_url: str = ""
    verified: bool = False
    source_hashtag: str = ""
    needs_verification: bool = False


class InstagramProspector:
    """
    Classe para prospecção de influenciadores no Instagram.
    
    Utiliza Business Discovery para obter métricas de perfis públicos
    Business/Creator do Instagram.
    """
    
    def __init__(
        self, 
        access_token: str = None,
        ig_user_id: str = None,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    ):
        """
        Inicializa o prospector do Instagram.
        
        Args:
            access_token: Token de acesso da Graph API.
            ig_user_id: ID do usuário Instagram (página conectada).
            rate_limit_delay: Delay entre requests para evitar rate limiting.
        """
        self.access_token = access_token or os.environ.get('INSTAGRAM_ACCESS_TOKEN')
        self.ig_user_id = ig_user_id or os.environ.get('INSTAGRAM_USER_ID')
        self.rate_limit_delay = rate_limit_delay
        self.seen_usernames: Set[str] = set()
        self.errors: List[str] = []
        
        if not self.access_token:
            logger.warning("Token de acesso do Instagram não configurado")
        if not self.ig_user_id:
            logger.warning("ID do usuário Instagram não configurado")
    
    def is_configured(self) -> bool:
        """Verifica se a API está configurada."""
        return bool(self.access_token and self.ig_user_id)
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any] = None
    ) -> Optional[Dict]:
        """
        Faz uma requisição à Graph API.
        
        Args:
            endpoint: Endpoint da API (sem a URL base).
            params: Parâmetros da query string.
            
        Returns:
            Resposta JSON ou None em caso de erro.
        """
        if not self.access_token:
            return None
        
        url = f"{GRAPH_API_BASE_URL}/{endpoint}"
        params = params or {}
        params['access_token'] = self.access_token
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            time.sleep(self.rate_limit_delay)
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro na requisição à API: {e}"
            logger.debug(error_msg)
            self.errors.append(error_msg)
            return None
    
    def get_user_profile(self, username: str) -> Optional[InstagramProfile]:
        """
        Obtém perfil de um usuário via Business Discovery.
        
        Args:
            username: Username do Instagram (sem @).
            
        Returns:
            Objeto InstagramProfile ou None.
        """
        if not self.ig_user_id:
            return None
        
        # Limpar username
        username = username.lower().strip().replace('@', '')
        
        # Verificar duplicatas
        if username in self.seen_usernames:
            return None
        
        response = self._make_request(
            self.ig_user_id,
            params={
                'fields': f'business_discovery.username({username})'
                          '{username,name,biography,followers_count,media_count,'
                          'profile_picture_url,media.limit(12)'
                          '{like_count,comments_count,media_type}}'
            }
        )
        
        if not response or 'business_discovery' not in response:
            logger.debug(f"Não foi possível obter perfil de @{username} (pode não ser Business/Creator)")
            return None
        
        bd = response['business_discovery']
        self.seen_usernames.add(username)
        
        # Calcular engajamento baseado nas últimas mídias
        followers = bd.get('followers_count', 0)
        media_data = bd.get('media', {}).get('data', [])
        
        total_likes = 0
        total_comments = 0
        media_count = len(media_data)
        
        for media in media_data:
            total_likes += media.get('like_count', 0)
            total_comments += media.get('comments_count', 0)
        
        if media_count > 0 and followers > 0:
            avg_likes = total_likes / media_count
            avg_comments = total_comments / media_count
            engagement_rate = ((avg_likes + avg_comments) / followers) * 100
        else:
            avg_likes = 0
            avg_comments = 0
            engagement_rate = 0.0
        
        return InstagramProfile(
            username=bd.get('username', username),
            user_id=bd.get('id', ''),
            followers_count=followers,
            media_count=bd.get('media_count', 0),
            biography=bd.get('biography', ''),
            engagement_rate=round(engagement_rate, 2),
            avg_likes=int(avg_likes),
            avg_comments=int(avg_comments),
            profile_url=f"https://www.instagram.com/{username}/",
            verified=False,
        )
    
    def prospect_from_seed_list(
        self,
        usernames: List[str] = None,
        min_followers: int = 1000,
        min_engagement: float = 2.5,
        max_results: int = 20
    ) -> List[InstagramProfile]:
        """
        Prospecta influenciadores a partir de uma lista de usernames.
        
        Args:
            usernames: Lista de usernames para verificar.
            min_followers: Mínimo de seguidores.
            min_engagement: Taxa mínima de engajamento.
            max_results: Número máximo de resultados.
            
        Returns:
            Lista de perfis qualificados.
        """
        if not self.is_configured():
            logger.warning("Instagram API não configurada")
            return []
        
        usernames = usernames or SEED_INFLUENCERS
        all_profiles = []
        
        logger.info(f"Verificando {len(usernames)} perfis do Instagram...")
        
        for username in usernames:
            if len(all_profiles) >= max_results * 2:
                break
            
            profile = self.get_user_profile(username)
            
            if profile:
                all_profiles.append(profile)
                logger.debug(f"@{username}: {profile.followers_count:,} seg, {profile.engagement_rate}% eng")
        
        logger.info(f"Instagram: {len(all_profiles)} perfis obtidos")
        
        # Filtrar por critérios
        qualified = [
            p for p in all_profiles
            if p.followers_count >= min_followers
            and p.engagement_rate >= min_engagement
        ]
        
        # Incluir potenciais
        potential = [
            p for p in all_profiles
            if p.followers_count >= min_followers
            and p.engagement_rate < min_engagement
            and p not in qualified
        ]
        
        # Ordenar por engajamento
        qualified.sort(key=lambda x: x.engagement_rate, reverse=True)
        potential.sort(key=lambda x: x.followers_count, reverse=True)
        
        # Combinar resultados
        results = qualified[:max_results]
        if len(results) < max_results:
            remaining = max_results - len(results)
            for p in potential[:remaining]:
                p.needs_verification = True
            results.extend(potential[:remaining])
        
        logger.info(f"Instagram: {len(qualified)} qualificados, retornando {len(results)}")
        
        return results
    
    def to_dict(self, profile: InstagramProfile) -> Dict:
        """Converte perfil para dicionário."""
        return {
            'platform': 'instagram',
            'username': profile.username,
            'name': profile.username,
            'user_id': profile.user_id,
            'followers': profile.followers_count,
            'media_count': profile.media_count,
            'engagement_rate': profile.engagement_rate,
            'avg_likes': profile.avg_likes,
            'avg_comments': profile.avg_comments,
            'avg_views': 0,
            'bio': profile.biography,
            'url': profile.profile_url,
            'verified': profile.verified,
            'source_keyword': profile.source_hashtag or 'seed_list',
            'needs_verification': profile.needs_verification,
        }


def test_instagram_api():
    """Testa a conexão com a API do Instagram."""
    print("=" * 60)
    print("TESTE DA API DO INSTAGRAM")
    print("=" * 60)
    
    prospector = InstagramProspector()
    
    if not prospector.is_configured():
        print("❌ API não configurada. Configure as variáveis:")
        print("   - INSTAGRAM_ACCESS_TOKEN")
        print("   - INSTAGRAM_USER_ID")
        return False
    
    print("✅ API configurada")
    
    # Testar Business Discovery com um perfil conhecido
    print("\nTestando Business Discovery...")
    
    test_usernames = ['voysaude', 'nutricaocomciencia', 'draanneloures']
    
    for username in test_usernames:
        profile = prospector.get_user_profile(username)
        
        if profile:
            print(f"\n✅ @{username}:")
            print(f"   Seguidores: {profile.followers_count:,}")
            print(f"   Posts: {profile.media_count}")
            print(f"   Engajamento: {profile.engagement_rate}%")
            print(f"   Média likes: {profile.avg_likes:,}")
        else:
            print(f"\n⚠️ @{username}: Não encontrado ou não é Business/Creator")
    
    print("\n" + "=" * 60)
    print("Teste concluído!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_instagram_api()
