"""
Modelos de dados para representar influenciadores e métricas.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class Platform(Enum):
    """Plataformas de redes sociais suportadas."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class InfluencerSize(Enum):
    """Classificação de tamanho do influenciador por número de seguidores."""
    NANO = "nano"
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    BIG = "big"
    MEGA = "mega"


@dataclass
class SocialProfile:
    """Representa um perfil em uma rede social específica."""
    platform: Platform
    username: str
    url: str
    followers: int = 0
    engagement_rate: float = 0.0
    avg_likes: int = 0
    avg_comments: int = 0
    avg_views: int = 0
    verified: bool = False
    
    def to_dict(self) -> Dict:
        """Converte o perfil para dicionário."""
        return {
            "platform": self.platform.value,
            "username": self.username,
            "url": self.url,
            "followers": self.followers,
            "engagement_rate": round(self.engagement_rate, 2),
            "avg_likes": self.avg_likes,
            "avg_comments": self.avg_comments,
            "avg_views": self.avg_views,
            "verified": self.verified,
        }


@dataclass
class Influencer:
    """Representa um influenciador prospectado."""
    name: str
    primary_platform: Platform
    profiles: List[SocialProfile] = field(default_factory=list)
    bio: str = ""
    niche: str = "emagrecimento"
    size: InfluencerSize = InfluencerSize.SMALL
    total_followers: int = 0
    best_engagement_rate: float = 0.0
    prospected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_keyword: str = ""
    notes: str = ""
    
    def __post_init__(self):
        """Calcula métricas agregadas após inicialização."""
        if self.profiles:
            self.total_followers = sum(p.followers for p in self.profiles)
            self.best_engagement_rate = max(
                (p.engagement_rate for p in self.profiles), 
                default=0.0
            )
            self._classify_size()
    
    def _classify_size(self):
        """Classifica o tamanho do influenciador baseado no total de seguidores."""
        from config import INFLUENCER_SIZE_RANGES
        
        for size_name, (min_followers, max_followers) in INFLUENCER_SIZE_RANGES.items():
            if min_followers <= self.total_followers < max_followers:
                self.size = InfluencerSize(size_name)
                break
    
    def add_profile(self, profile: SocialProfile):
        """Adiciona um perfil social ao influenciador."""
        self.profiles.append(profile)
        self.total_followers = sum(p.followers for p in self.profiles)
        self.best_engagement_rate = max(
            (p.engagement_rate for p in self.profiles), 
            default=0.0
        )
        self._classify_size()
    
    def get_profile(self, platform: Platform) -> Optional[SocialProfile]:
        """Retorna o perfil de uma plataforma específica."""
        for profile in self.profiles:
            if profile.platform == platform:
                return profile
        return None
    
    def meets_criteria(self, min_engagement: float = 2.5) -> bool:
        """Verifica se o influenciador atende aos critérios mínimos."""
        return self.best_engagement_rate >= min_engagement
    
    def to_dict(self) -> Dict:
        """Converte o influenciador para dicionário."""
        return {
            "name": self.name,
            "primary_platform": self.primary_platform.value,
            "profiles": [p.to_dict() for p in self.profiles],
            "bio": self.bio,
            "niche": self.niche,
            "size": self.size.value,
            "total_followers": self.total_followers,
            "best_engagement_rate": round(self.best_engagement_rate, 2),
            "prospected_at": self.prospected_at,
            "source_keyword": self.source_keyword,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Influencer":
        """Cria um influenciador a partir de um dicionário."""
        profiles = [
            SocialProfile(
                platform=Platform(p["platform"]),
                username=p["username"],
                url=p["url"],
                followers=p.get("followers", 0),
                engagement_rate=p.get("engagement_rate", 0.0),
                avg_likes=p.get("avg_likes", 0),
                avg_comments=p.get("avg_comments", 0),
                avg_views=p.get("avg_views", 0),
                verified=p.get("verified", False),
            )
            for p in data.get("profiles", [])
        ]
        
        return cls(
            name=data["name"],
            primary_platform=Platform(data["primary_platform"]),
            profiles=profiles,
            bio=data.get("bio", ""),
            niche=data.get("niche", "emagrecimento"),
            size=InfluencerSize(data.get("size", "small")),
            prospected_at=data.get("prospected_at", datetime.now().isoformat()),
            source_keyword=data.get("source_keyword", ""),
            notes=data.get("notes", ""),
        )


@dataclass
class ProspectionResult:
    """Resultado de uma execução de prospecção."""
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    influencers: List[Influencer] = field(default_factory=list)
    total_found: int = 0
    total_qualified: int = 0
    keywords_used: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Converte o resultado para dicionário."""
        return {
            "date": self.date,
            "influencers": [i.to_dict() for i in self.influencers],
            "total_found": self.total_found,
            "total_qualified": self.total_qualified,
            "keywords_used": self.keywords_used,
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "errors": self.errors,
        }
