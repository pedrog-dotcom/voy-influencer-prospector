"""
Módulo de triagem de perfis usando GPT.
Analisa se o perfil atende aos critérios específicos para parceria.

Critérios:
- Idade aparente: +25 anos
- Tipo corporal: sobrepeso ou obesidade
- Classe social: conteúdo para classe A/B
- Nacionalidade: brasileiro(a)
- Autenticidade: pessoa real (não marca/loja)
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from openai import OpenAI

from config import (
    SCREENING_PROMPT,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    API_DELAYS,
)

logger = logging.getLogger(__name__)


@dataclass
class ScreeningResult:
    """Resultado da triagem de um perfil."""
    username: str
    platform: str
    idade_25_plus: bool
    sobrepeso_obeso: bool
    classe_ab: bool
    brasileiro: bool
    pessoa_real: bool
    aprovado: bool
    motivo: str
    confianca: int
    raw_response: dict
    
    def to_dict(self) -> dict:
        return asdict(self)


class GPTScreener:
    """
    Realiza triagem de perfis usando GPT para verificar critérios específicos.
    """
    
    def __init__(self):
        self.client = OpenAI()  # Usa OPENAI_API_KEY do ambiente
        self.model = OPENAI_MODEL
        logger.info(f"GPT Screener inicializado com modelo: {self.model}")
    
    def screen_profile(self, profile_data: dict) -> ScreeningResult:
        """
        Realiza triagem de um perfil individual.
        
        Args:
            profile_data: Dados do perfil a ser analisado
            
        Returns:
            ScreeningResult com resultado da triagem
        """
        username = profile_data.get("username", "")
        platform = profile_data.get("platform", "")
        
        try:
            # Preparar prompt com dados do perfil
            prompt = SCREENING_PROMPT.format(
                name=profile_data.get("name", username),
                username=username,
                platform=platform,
                followers=profile_data.get("followers", 0),
                engagement_rate=profile_data.get("engagement_rate", 0),
                bio=profile_data.get("bio", "Não disponível"),
                location=profile_data.get("location", "Não informado"),
                content_description=profile_data.get("content_description", "Não disponível")
            )
            
            # Chamar GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de perfis de influenciadores. Responda APENAS em JSON válido, sem markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=OPENAI_TEMPERATURE
            )
            
            # Extrair resposta
            response_text = response.choices[0].message.content.strip()
            
            # Limpar possíveis marcadores de código
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            # Parsear JSON
            try:
                result_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Tentar extrair JSON do texto
                import re
                json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                else:
                    raise ValueError(f"Não foi possível extrair JSON: {response_text[:200]}")
            
            # Criar resultado
            result = ScreeningResult(
                username=username,
                platform=platform,
                idade_25_plus=result_data.get("idade_25_plus", False),
                sobrepeso_obeso=result_data.get("sobrepeso_obeso", False),
                classe_ab=result_data.get("classe_ab", False),
                brasileiro=result_data.get("brasileiro", False),
                pessoa_real=result_data.get("pessoa_real", False),
                aprovado=result_data.get("aprovado", False),
                motivo=result_data.get("motivo", ""),
                confianca=result_data.get("confianca", 0),
                raw_response=result_data
            )
            
            logger.info(
                f"Triagem @{username}: {'✓ APROVADO' if result.aprovado else '✗ REJEITADO'} "
                f"(confiança: {result.confianca}%)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na triagem de @{username}: {e}")
            
            # Retornar resultado negativo em caso de erro
            return ScreeningResult(
                username=username,
                platform=platform,
                idade_25_plus=False,
                sobrepeso_obeso=False,
                classe_ab=False,
                brasileiro=False,
                pessoa_real=False,
                aprovado=False,
                motivo=f"Erro na análise: {str(e)[:100]}",
                confianca=0,
                raw_response={"error": str(e)}
            )
    
    def screen_profiles_batch(
        self,
        profiles: List[dict],
        max_approved: int = 20
    ) -> Tuple[List[ScreeningResult], List[ScreeningResult]]:
        """
        Realiza triagem de múltiplos perfis em lote.
        Para quando atingir o número máximo de aprovados.
        
        Args:
            profiles: Lista de perfis a serem analisados
            max_approved: Número máximo de aprovados desejados
            
        Returns:
            Tupla (aprovados, rejeitados)
        """
        approved = []
        rejected = []
        
        logger.info(f"Iniciando triagem de {len(profiles)} perfis (meta: {max_approved} aprovados)")
        
        for i, profile in enumerate(profiles):
            # Verificar se já atingiu a meta
            if len(approved) >= max_approved:
                logger.info(f"Meta de {max_approved} aprovados atingida. Parando triagem.")
                break
            
            # Realizar triagem
            result = self.screen_profile(profile)
            
            if result.aprovado:
                approved.append(result)
            else:
                rejected.append(result)
            
            # Log de progresso
            if (i + 1) % 10 == 0:
                logger.info(
                    f"Progresso: {i + 1}/{len(profiles)} analisados, "
                    f"{len(approved)} aprovados, {len(rejected)} rejeitados"
                )
            
            # Delay entre requisições
            time.sleep(API_DELAYS.get("openai", 1))
        
        logger.info(
            f"Triagem concluída: {len(approved)} aprovados, {len(rejected)} rejeitados "
            f"de {len(approved) + len(rejected)} analisados"
        )
        
        return approved, rejected
    
    def estimate_tokens(self, profiles_count: int) -> dict:
        """
        Estima uso de tokens para triagem.
        
        Args:
            profiles_count: Número de perfis a analisar
            
        Returns:
            Estimativa de tokens e custo
        """
        # Estimativa baseada no tamanho do prompt
        avg_input_tokens = 400  # Prompt médio
        avg_output_tokens = 150  # Resposta média
        
        total_input = profiles_count * avg_input_tokens
        total_output = profiles_count * avg_output_tokens
        
        # Custo aproximado (gpt-4.1-mini)
        input_cost = (total_input / 1000) * 0.00015
        output_cost = (total_output / 1000) * 0.0006
        
        return {
            "profiles_count": profiles_count,
            "estimated_input_tokens": total_input,
            "estimated_output_tokens": total_output,
            "estimated_total_tokens": total_input + total_output,
            "estimated_cost_usd": round(input_cost + output_cost, 4)
        }


def screen_profiles(
    profiles: List[dict],
    max_approved: int = 20
) -> Tuple[List[ScreeningResult], List[ScreeningResult]]:
    """
    Função principal para triagem de perfis.
    
    Args:
        profiles: Lista de perfis a serem analisados
        max_approved: Número máximo de aprovados desejados
        
    Returns:
        Tupla (aprovados, rejeitados)
    """
    screener = GPTScreener()
    return screener.screen_profiles_batch(profiles, max_approved)
