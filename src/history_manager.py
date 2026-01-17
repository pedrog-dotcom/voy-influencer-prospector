"""
Gerenciador de histórico para controle de influenciadores já prospectados.
Evita duplicatas entre execuções diárias.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, List, Optional
from filelock import FileLock

from config import HISTORY_FILE, DATA_DIR

logger = logging.getLogger(__name__)


class HistoryManager:
    """Gerencia o histórico de influenciadores prospectados."""
    
    def __init__(self, history_file: Optional[Path] = None):
        """
        Inicializa o gerenciador de histórico.
        
        Args:
            history_file: Caminho para o arquivo de histórico.
        """
        self.history_file = history_file or HISTORY_FILE
        self.lock_file = self.history_file.with_suffix(".lock")
        self._ensure_data_dir()
        self._history: Dict = self._load_history()
    
    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> Dict:
        """Carrega o histórico do arquivo."""
        if not self.history_file.exists():
            return {
                "prospected_usernames": {},
                "prospected_names": set(),
                "daily_runs": [],
                "last_updated": None,
            }
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Converter lista de nomes para set
                data["prospected_names"] = set(data.get("prospected_names", []))
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            return {
                "prospected_usernames": {},
                "prospected_names": set(),
                "daily_runs": [],
                "last_updated": None,
            }
    
    def _save_history(self):
        """Salva o histórico no arquivo com lock para evitar race conditions."""
        with FileLock(self.lock_file):
            self._history["last_updated"] = datetime.now().isoformat()
            
            # Converter set para lista para serialização JSON
            data_to_save = {
                **self._history,
                "prospected_names": list(self._history["prospected_names"]),
            }
            
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    
    def is_prospected(self, username: str, platform: str) -> bool:
        """
        Verifica se um usuário já foi prospectado.
        
        Args:
            username: Nome de usuário na plataforma.
            platform: Nome da plataforma (instagram, tiktok, youtube).
            
        Returns:
            True se já foi prospectado, False caso contrário.
        """
        key = f"{platform}:{username.lower()}"
        return key in self._history["prospected_usernames"]
    
    def is_name_prospected(self, name: str) -> bool:
        """
        Verifica se um nome já foi prospectado (independente da plataforma).
        
        Args:
            name: Nome do influenciador.
            
        Returns:
            True se já foi prospectado, False caso contrário.
        """
        return name.lower().strip() in self._history["prospected_names"]
    
    def add_prospected(
        self, 
        username: str, 
        platform: str, 
        name: str,
        metadata: Optional[Dict] = None
    ):
        """
        Adiciona um influenciador ao histórico.
        
        Args:
            username: Nome de usuário na plataforma.
            platform: Nome da plataforma.
            name: Nome do influenciador.
            metadata: Metadados adicionais (opcional).
        """
        key = f"{platform}:{username.lower()}"
        self._history["prospected_usernames"][key] = {
            "username": username,
            "platform": platform,
            "name": name,
            "prospected_at": datetime.now().isoformat(),
            **(metadata or {}),
        }
        self._history["prospected_names"].add(name.lower().strip())
        self._save_history()
    
    def add_daily_run(self, run_data: Dict):
        """
        Registra uma execução diária.
        
        Args:
            run_data: Dados da execução (data, quantidade, etc.).
        """
        self._history["daily_runs"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            **run_data,
        })
        self._save_history()
    
    def get_prospected_count(self) -> int:
        """Retorna o total de influenciadores prospectados."""
        return len(self._history["prospected_usernames"])
    
    def get_daily_runs(self, limit: int = 30) -> List[Dict]:
        """
        Retorna as últimas execuções diárias.
        
        Args:
            limit: Número máximo de execuções a retornar.
            
        Returns:
            Lista das últimas execuções.
        """
        return self._history["daily_runs"][-limit:]
    
    def get_all_usernames(self, platform: Optional[str] = None) -> Set[str]:
        """
        Retorna todos os usernames prospectados.
        
        Args:
            platform: Filtrar por plataforma (opcional).
            
        Returns:
            Set de usernames.
        """
        usernames = set()
        for key, data in self._history["prospected_usernames"].items():
            if platform is None or data["platform"] == platform:
                usernames.add(data["username"])
        return usernames
    
    def clear_history(self):
        """Limpa todo o histórico (usar com cuidado)."""
        self._history = {
            "prospected_usernames": {},
            "prospected_names": set(),
            "daily_runs": [],
            "last_updated": None,
        }
        self._save_history()
        logger.warning("Histórico limpo completamente")
