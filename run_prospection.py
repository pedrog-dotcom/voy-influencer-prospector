#!/usr/bin/env python3
"""
Voy Saúde - Sistema de Prospecção de Influenciadores V4

Fluxo otimizado:
1. Coleta perfis via hashtags (Instagram)
2. Filtra por 10k+ seguidores e 2.5%+ engajamento
3. Verifica histórico para não reprocessar perfis (economia de tokens)
4. Triagem GPT: idade 25+, sobrepeso/obeso, classe A/B, brasileiro
5. Salva 20 aprovados por dia em CSV

Uso:
    python run_prospection.py [--collect] [--screen]
    
    --collect: Apenas coleta novos perfis
    --screen: Apenas faz triagem dos pendentes
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    DATA_DIR,
    LOGS_DIR,
    DAILY_OUTPUT_COUNT,
    MIN_FOLLOWERS,
    MIN_ENGAGEMENT_RATE,
    get_active_hashtags,
)
from history_manager import HistoryManager
from hashtag_collector import collect_profiles_from_hashtags
from gpt_screener import screen_profiles, GPTScreener

# Configurar logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"prospection_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProspectionPipeline:
    """Pipeline completo de prospecção de influenciadores."""
    
    def __init__(self):
        self.history = HistoryManager()
        self.screener = GPTScreener()
        
    def run_collection(self, max_per_hashtag: int = 30) -> int:
        """
        Etapa 1: Coleta perfis de hashtags.
        
        Returns:
            Número de novos perfis coletados
        """
        logger.info("=" * 60)
        logger.info("ETAPA 1: COLETA DE PERFIS VIA HASHTAGS")
        logger.info("=" * 60)
        
        active_hashtags = get_active_hashtags()
        logger.info(f"Hashtags ativas: {len(active_hashtags)}")
        logger.info(f"Critérios: {MIN_FOLLOWERS:,}+ seguidores, {MIN_ENGAGEMENT_RATE}%+ engajamento")
        logger.info("NOTA: Apenas perfis qualificados serão enviados para triagem GPT")
        
        # Coletar perfis (retorna todos, não apenas qualificados)
        collected = collect_profiles_from_hashtags(max_per_hashtag)
        
        if not collected:
            logger.warning("Nenhum perfil coletado das hashtags")
            return 0
        
        # Converter para dict - apenas perfis qualificados
        profiles_data = [p.to_dict() for p in collected]
        logger.info(f"Total de perfis coletados: {len(profiles_data)}")
        
        # Filtrar não processados
        new_profiles = self.history.filter_unprocessed(profiles_data)
        
        if new_profiles:
            # Salvar como pendentes
            self.history.save_pending_profiles(new_profiles)
            logger.info(f"✓ {len(new_profiles)} novos perfis salvos para triagem")
        else:
            logger.info("Nenhum perfil novo (todos já processados)")
        
        return len(new_profiles)
    
    def run_screening(self, target_approved: int = DAILY_OUTPUT_COUNT) -> dict:
        """
        Etapa 2: Triagem GPT dos perfis pendentes.
        
        Args:
            target_approved: Meta de aprovados
            
        Returns:
            Estatísticas da triagem
        """
        logger.info("=" * 60)
        logger.info("ETAPA 2: TRIAGEM GPT DOS PERFIS")
        logger.info("=" * 60)
        
        # Verificar quantos já foram aprovados hoje
        today_approved = self.history.get_today_approved_count()
        remaining_target = max(0, target_approved - today_approved)
        
        if remaining_target == 0:
            logger.info(f"Meta diária já atingida ({today_approved} aprovados hoje)")
            return {
                "status": "meta_atingida",
                "today_approved": today_approved,
                "new_approved": 0,
                "analyzed": 0
            }
        
        logger.info(f"Meta: {remaining_target} aprovações (já temos {today_approved} hoje)")
        
        # Obter perfis pendentes
        pending = self.history.get_pending_profiles(limit=100)
        
        if not pending:
            logger.warning("Nenhum perfil pendente para triagem")
            return {
                "status": "sem_pendentes",
                "today_approved": today_approved,
                "new_approved": 0,
                "analyzed": 0
            }
        
        logger.info(f"Perfis pendentes para análise: {len(pending)}")
        
        # Estimar tokens
        estimate = self.screener.estimate_tokens(min(len(pending), remaining_target * 3))
        logger.info(f"Estimativa de tokens: ~{estimate['estimated_total_tokens']:,} (${estimate['estimated_cost_usd']:.4f})")
        
        # Realizar triagem
        approved_results, rejected_results = screen_profiles(pending, remaining_target)
        
        # Processar resultados
        processed_profiles = []
        new_approved_count = 0
        
        for result in approved_results:
            # Encontrar dados originais do perfil
            profile_data = next(
                (p for p in pending if p.get("username") == result.username),
                {}
            )
            
            # Marcar como processado
            self.history.mark_as_processed(
                username=result.username,
                platform=result.platform,
                name=profile_data.get("name", result.username),
                approved=True,
                screening_result=result.to_dict(),
                profile_data=profile_data
            )
            
            # Adicionar ao CSV de aprovados
            self.history.append_to_approved_csv({
                **profile_data,
                "screening": result.to_dict()
            })
            
            processed_profiles.append((result.username, result.platform))
            new_approved_count += 1
        
        for result in rejected_results:
            profile_data = next(
                (p for p in pending if p.get("username") == result.username),
                {}
            )
            
            self.history.mark_as_processed(
                username=result.username,
                platform=result.platform,
                name=profile_data.get("name", result.username),
                approved=False,
                screening_result=result.to_dict(),
                profile_data=profile_data
            )
            
            processed_profiles.append((result.username, result.platform))
        
        # Remover dos pendentes
        self.history.remove_from_pending(processed_profiles)
        
        logger.info(f"✓ Triagem concluída: {new_approved_count} aprovados, {len(rejected_results)} rejeitados")
        
        return {
            "status": "sucesso",
            "today_approved": today_approved + new_approved_count,
            "new_approved": new_approved_count,
            "analyzed": len(approved_results) + len(rejected_results),
            "rejected": len(rejected_results)
        }
    
    def run_full_pipeline(self) -> dict:
        """
        Executa pipeline completo: coleta + triagem.
        
        Returns:
            Estatísticas completas da execução
        """
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("VOY SAÚDE - PROSPECÇÃO DE INFLUENCIADORES V4")
        logger.info(f"Início: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Estatísticas iniciais
        stats = self.history.get_statistics()
        logger.info(f"Histórico: {stats['total_processed']} processados, {stats['total_approved']} aprovados")
        
        # Etapa 1: Coleta
        new_collected = self.run_collection()
        
        # Etapa 2: Triagem
        screening_result = self.run_screening()
        
        # Resumo final
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        final_stats = self.history.get_statistics()
        
        result = {
            "execution_date": start_time.strftime("%Y-%m-%d"),
            "execution_time": start_time.strftime("%H:%M:%S"),
            "duration_seconds": round(duration, 2),
            "new_profiles_collected": new_collected,
            "profiles_analyzed": screening_result.get("analyzed", 0),
            "new_approved": screening_result.get("new_approved", 0),
            "total_approved_today": screening_result.get("today_approved", 0),
            "total_processed_all_time": final_stats["total_processed"],
            "total_approved_all_time": final_stats["total_approved"],
            "pending_profiles": self.history.get_pending_count(),
            "status": screening_result.get("status", "concluido")
        }
        
        logger.info("=" * 60)
        logger.info("RESUMO DA EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Duração: {duration:.2f} segundos")
        logger.info(f"Novos perfis coletados: {new_collected}")
        logger.info(f"Perfis analisados: {result['profiles_analyzed']}")
        logger.info(f"Novos aprovados: {result['new_approved']}")
        logger.info(f"Total aprovados hoje: {result['total_approved_today']}")
        logger.info(f"Perfis pendentes: {result['pending_profiles']}")
        logger.info("=" * 60)
        
        # Salvar resultado da execução
        self._save_execution_result(result)
        
        return result
    
    def _save_execution_result(self, result: dict):
        """Salva resultado da execução em arquivo JSON."""
        results_file = DATA_DIR / "execution_results.json"
        
        try:
            existing = []
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            
            existing.append(result)
            
            # Manter apenas últimos 30 dias
            existing = existing[-30:]
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar resultado: {e}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Voy Saúde - Prospecção de Influenciadores V4"
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Apenas coleta novos perfis"
    )
    parser.add_argument(
        "--screen",
        action="store_true",
        help="Apenas faz triagem dos pendentes"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=DAILY_OUTPUT_COUNT,
        help=f"Meta de aprovados (padrão: {DAILY_OUTPUT_COUNT})"
    )
    # Argumentos de compatibilidade com workflow antigo
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Alias para --target (compatibilidade)"
    )
    
    args = parser.parse_args()
    
    # Usar --count como alias para --target se fornecido
    if args.count is not None:
        args.target = args.count
    
    pipeline = ProspectionPipeline()
    
    if args.collect:
        pipeline.run_collection()
    elif args.screen:
        pipeline.run_screening(args.target)
    else:
        result = pipeline.run_full_pipeline()
        
        # Imprimir resultado para GitHub Actions (usando Environment Files)
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"approved={result['new_approved']}\n")
                f.write(f"total_today={result['total_approved_today']}\n")
        else:
            # Fallback para execução local
            print(f"\nResultado: {result['new_approved']} aprovados, {result['total_approved_today']} total hoje")


if __name__ == "__main__":
    main()
