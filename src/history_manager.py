"""
Gerenciador de histórico de perfis processados.
Evita reprocessamento de perfis já analisados pelo GPT (economia de tokens).

V4: Sistema otimizado com separação entre perfis processados e aprovados.
"""

import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, List, Optional
from filelock import FileLock

from config import DATA_DIR, HISTORY_FILE, APPROVED_FILE, PENDING_FILE

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Gerencia histórico de perfis processados para evitar reprocessamento.
    
    Arquivos:
    - processed_profiles.json: Todos os perfis já analisados pelo GPT
    - approved_influencers.csv: Influenciadores aprovados (output final)
    - pending_profiles.json: Perfis coletados aguardando triagem
    """
    
    def __init__(self):
        self._ensure_data_dir()
        self._processed_cache: Dict[str, dict] = {}
        self._load_history()
    
    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_profile_key(self, username: str, platform: str) -> str:
        """Gera chave única para um perfil."""
        return f"{platform}:{username.lower()}"
    
    def _load_history(self):
        """Carrega histórico de perfis processados."""
        if HISTORY_FILE.exists():
            try:
                with FileLock(str(HISTORY_FILE) + ".lock"):
                    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                self._processed_cache = data.get("profiles", {})
                logger.info(f"Histórico carregado: {len(self._processed_cache)} perfis processados")
                
            except Exception as e:
                logger.error(f"Erro ao carregar histórico: {e}")
                self._processed_cache = {}
    
    def _save_history(self):
        """Salva histórico de perfis processados."""
        try:
            with FileLock(str(HISTORY_FILE) + ".lock"):
                total = len(self._processed_cache)
                approved = sum(1 for p in self._processed_cache.values() if p.get("approved"))
                
                data = {
                    "last_updated": datetime.now().isoformat(),
                    "total_processed": total,
                    "total_approved": approved,
                    "total_rejected": total - approved,
                    "profiles": self._processed_cache
                }
                
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
    
    def is_processed(self, username: str, platform: str) -> bool:
        """Verifica se um perfil já foi processado pelo GPT."""
        key = self._get_profile_key(username, platform)
        return key in self._processed_cache
    
    def is_prospected(self, username: str, platform: str) -> bool:
        """Alias para is_processed (compatibilidade)."""
        return self.is_processed(username, platform)
    
    def get_processed_profile(self, username: str, platform: str) -> Optional[dict]:
        """Retorna dados de um perfil processado."""
        key = self._get_profile_key(username, platform)
        return self._processed_cache.get(key)
    
    def mark_as_processed(
        self,
        username: str,
        platform: str,
        name: str,
        approved: bool,
        screening_result: dict,
        profile_data: dict = None
    ):
        """
        Marca um perfil como processado pelo GPT.
        
        Args:
            username: Username do perfil
            platform: Plataforma (instagram, tiktok, youtube)
            name: Nome do influenciador
            approved: Se foi aprovado na triagem
            screening_result: Resultado completo da triagem GPT
            profile_data: Dados adicionais do perfil
        """
        key = self._get_profile_key(username, platform)
        
        self._processed_cache[key] = {
            "username": username,
            "platform": platform,
            "name": name,
            "processed_at": datetime.now().isoformat(),
            "approved": approved,
            "screening_result": screening_result,
            "profile_data": profile_data or {}
        }
        
        self._save_history()
        logger.debug(f"Perfil marcado como processado: {key} (aprovado: {approved})")
    
    def add_prospected(self, username: str, platform: str, name: str, metadata: dict = None):
        """Adiciona um perfil ao histórico (compatibilidade com versão anterior)."""
        self.mark_as_processed(
            username=username,
            platform=platform,
            name=name,
            approved=True,
            screening_result=metadata or {},
            profile_data=metadata
        )
    
    def filter_unprocessed(self, profiles: List[dict]) -> List[dict]:
        """
        Filtra lista de perfis, retornando apenas os não processados.
        
        Args:
            profiles: Lista de perfis coletados
            
        Returns:
            Lista de perfis que ainda não foram processados pelo GPT
        """
        unprocessed = []
        
        for profile in profiles:
            username = profile.get("username", "")
            platform = profile.get("platform", "")
            
            if not self.is_processed(username, platform):
                unprocessed.append(profile)
        
        logger.info(f"Filtro de histórico: {len(profiles)} total, {len(unprocessed)} não processados")
        
        return unprocessed
    
    def get_statistics(self) -> dict:
        """Retorna estatísticas do histórico."""
        total = len(self._processed_cache)
        approved = sum(1 for p in self._processed_cache.values() if p.get("approved"))
        rejected = total - approved
        
        # Contar por plataforma
        by_platform = {}
        for key, profile in self._processed_cache.items():
            platform = profile.get("platform", key.split(":")[0])
            if platform not in by_platform:
                by_platform[platform] = {"total": 0, "approved": 0}
            by_platform[platform]["total"] += 1
            if profile.get("approved"):
                by_platform[platform]["approved"] += 1
        
        return {
            "total_processed": total,
            "total_approved": approved,
            "total_rejected": rejected,
            "approval_rate": round((approved / max(total, 1)) * 100, 2),
            "by_platform": by_platform
        }
    
    def get_prospected_count(self) -> int:
        """Retorna o total de perfis processados."""
        return len(self._processed_cache)
    
    # =========================================================================
    # Gerenciamento de Perfis Pendentes
    # =========================================================================
    
    def get_pending_count(self) -> int:
        """Retorna quantidade de perfis pendentes de triagem."""
        if not PENDING_FILE.exists():
            return 0
        
        try:
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return len(data.get("profiles", []))
        except:
            return 0
    
    def save_pending_profiles(self, profiles: List[dict]):
        """Salva perfis pendentes de triagem."""
        try:
            existing = []
            if PENDING_FILE.exists():
                with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                    existing = json.load(f).get("profiles", [])
            
            # Adicionar novos perfis (evitar duplicatas)
            existing_keys = {
                f"{p.get('platform')}:{p.get('username', '').lower()}"
                for p in existing
            }
            
            added = 0
            for profile in profiles:
                key = f"{profile.get('platform')}:{profile.get('username', '').lower()}"
                if key not in existing_keys and not self.is_processed(profile.get('username', ''), profile.get('platform', '')):
                    existing.append(profile)
                    existing_keys.add(key)
                    added += 1
            
            with open(PENDING_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "total": len(existing),
                    "profiles": existing
                }, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Salvos {added} novos perfis pendentes (total: {len(existing)})")
            
        except Exception as e:
            logger.error(f"Erro ao salvar perfis pendentes: {e}")
    
    def get_pending_profiles(self, limit: int = 100) -> List[dict]:
        """Retorna perfis pendentes de triagem (não processados)."""
        if not PENDING_FILE.exists():
            return []
        
        try:
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profiles = data.get("profiles", [])
                
            # Filtrar apenas os não processados
            unprocessed = self.filter_unprocessed(profiles)
            
            return unprocessed[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao carregar perfis pendentes: {e}")
            return []
    
    def remove_from_pending(self, usernames_platforms: List[tuple]):
        """Remove perfis da lista de pendentes após processamento."""
        if not PENDING_FILE.exists():
            return
        
        try:
            with open(PENDING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profiles = data.get("profiles", [])
            
            # Criar set de chaves a remover
            to_remove = {
                f"{platform}:{username.lower()}"
                for username, platform in usernames_platforms
            }
            
            # Filtrar perfis
            remaining = [
                p for p in profiles
                if f"{p.get('platform')}:{p.get('username', '').lower()}" not in to_remove
            ]
            
            with open(PENDING_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "total": len(remaining),
                    "profiles": remaining
                }, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Removidos {len(profiles) - len(remaining)} perfis dos pendentes")
            
        except Exception as e:
            logger.error(f"Erro ao remover perfis pendentes: {e}")
    
    # =========================================================================
    # Gerenciamento de Influenciadores Aprovados (CSV)
    # =========================================================================
    
    def append_to_approved_csv(self, influencer_data: dict):
        """
        Adiciona um influenciador aprovado ao CSV final.
        
        Args:
            influencer_data: Dados do influenciador aprovado
        """
        try:
            file_exists = APPROVED_FILE.exists()
            
            with open(APPROVED_FILE, 'a', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'data_aprovacao',
                    'nome',
                    'username',
                    'plataforma',
                    'seguidores',
                    'taxa_engajamento',
                    'url_perfil',
                    'bio',
                    'idade_25_plus',
                    'sobrepeso_obeso',
                    'classe_ab',
                    'brasileiro',
                    'confianca_ia',
                    'motivo_aprovacao',
                    'hashtag_origem'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'data_aprovacao': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'nome': influencer_data.get('name', ''),
                    'username': influencer_data.get('username', ''),
                    'plataforma': influencer_data.get('platform', ''),
                    'seguidores': influencer_data.get('followers', 0),
                    'taxa_engajamento': influencer_data.get('engagement_rate', 0),
                    'url_perfil': influencer_data.get('profile_url', ''),
                    'bio': influencer_data.get('bio', '')[:200],
                    'idade_25_plus': influencer_data.get('screening', {}).get('idade_25_plus', ''),
                    'sobrepeso_obeso': influencer_data.get('screening', {}).get('sobrepeso_obeso', ''),
                    'classe_ab': influencer_data.get('screening', {}).get('classe_ab', ''),
                    'brasileiro': influencer_data.get('screening', {}).get('brasileiro', ''),
                    'confianca_ia': influencer_data.get('screening', {}).get('confianca', ''),
                    'motivo_aprovacao': influencer_data.get('screening', {}).get('motivo', ''),
                    'hashtag_origem': influencer_data.get('source_hashtag', '')
                })
                
            logger.debug(f"Influenciador adicionado ao CSV: {influencer_data.get('username')}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar ao CSV: {e}")
    
    def get_approved_count(self) -> int:
        """Retorna quantidade de influenciadores aprovados no CSV."""
        if not APPROVED_FILE.exists():
            return 0
        
        try:
            with open(APPROVED_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                return sum(1 for _ in reader) - 1  # Menos o header
        except:
            return 0
    
    def get_today_approved_count(self) -> int:
        """Retorna quantidade de influenciadores aprovados hoje."""
        if not APPROVED_FILE.exists():
            return 0
        
        today = datetime.now().strftime('%Y-%m-%d')
        count = 0
        
        try:
            with open(APPROVED_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('data_aprovacao', '').startswith(today):
                        count += 1
        except:
            pass
        
        return count
    
    def clear_history(self):
        """Limpa todo o histórico (usar com cuidado)."""
        self._processed_cache = {}
        self._save_history()
        
        if PENDING_FILE.exists():
            PENDING_FILE.unlink()
            
        logger.warning("Histórico limpo completamente")
