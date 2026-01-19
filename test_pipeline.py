#!/usr/bin/env python3
"""
Script de teste do pipeline V4 de prospecção.
Testa coleta de perfis seed + triagem GPT.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import DATA_DIR, SCREENING_PROMPT, OPENAI_MODEL
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Perfis de teste (simulando coleta)
TEST_PROFILES = [
    {
        "username": "mayaborges_",
        "name": "Maya Borges",
        "platform": "instagram",
        "followers": 150000,
        "engagement_rate": 4.5,
        "bio": "🇧🇷 Minha jornada de emagrecimento | -30kg | Mãe | São Paulo",
        "location": "Brasil",
        "profile_url": "https://instagram.com/mayaborges_",
        "content_description": "Compartilho minha transformação, dicas de alimentação saudável e rotina fitness"
    },
    {
        "username": "flufranco",
        "name": "Flu Franco",
        "platform": "instagram",
        "followers": 280000,
        "engagement_rate": 5.2,
        "bio": "Plus Size | Body Positive | Moda | Rio de Janeiro 🇧🇷",
        "location": "Brasil",
        "profile_url": "https://instagram.com/flufranco",
        "content_description": "Influenciadora plus size, moda, autoestima e empoderamento feminino"
    },
    {
        "username": "fitstore_oficial",
        "name": "Fit Store",
        "platform": "instagram",
        "followers": 50000,
        "engagement_rate": 2.1,
        "bio": "Loja de suplementos | Whey, Creatina | Entrega todo Brasil",
        "location": "Brasil",
        "profile_url": "https://instagram.com/fitstore_oficial",
        "content_description": "Venda de suplementos alimentares e produtos fitness"
    },
    {
        "username": "carol_emagrece",
        "name": "Carol Silva",
        "platform": "instagram",
        "followers": 85000,
        "engagement_rate": 6.8,
        "bio": "32 anos | Eliminei 45kg com reeducação alimentar | Mãe de 2 | SP 🇧🇷",
        "location": "Brasil",
        "profile_url": "https://instagram.com/carol_emagrece",
        "content_description": "Diário de emagrecimento, receitas low carb, antes e depois"
    },
    {
        "username": "drnutri_joao",
        "name": "Dr. João Nutricionista",
        "platform": "instagram",
        "followers": 120000,
        "engagement_rate": 3.5,
        "bio": "Nutricionista CRN | Consultório em SP | Agenda: link na bio",
        "location": "Brasil",
        "profile_url": "https://instagram.com/drnutri_joao",
        "content_description": "Dicas de nutrição, consultas online, planos alimentares"
    },
    {
        "username": "gordinha_fashion",
        "name": "Ana Paula",
        "platform": "instagram",
        "followers": 45000,
        "engagement_rate": 8.2,
        "bio": "28 anos | Plus size com orgulho | Moda acessível | BH 🇧🇷",
        "location": "Brasil",
        "profile_url": "https://instagram.com/gordinha_fashion",
        "content_description": "Looks do dia, moda plus size, autoestima, lifestyle"
    },
]


def test_gpt_screening():
    """Testa a triagem GPT com perfis de exemplo."""
    client = OpenAI()
    
    logger.info("=" * 60)
    logger.info("TESTE DE TRIAGEM GPT")
    logger.info("=" * 60)
    
    results = []
    
    for profile in TEST_PROFILES:
        logger.info(f"\nAnalisando: @{profile['username']} ({profile['name']})")
        logger.info(f"  Seguidores: {profile['followers']:,} | Engajamento: {profile['engagement_rate']}%")
        
        # Preparar prompt
        prompt = SCREENING_PROMPT.format(
            name=profile.get("name", profile["username"]),
            username=profile["username"],
            platform=profile["platform"],
            followers=profile.get("followers", 0),
            engagement_rate=profile.get("engagement_rate", 0),
            bio=profile.get("bio", "Não disponível"),
            location=profile.get("location", "Não informado"),
            content_description=profile.get("content_description", "Não disponível")
        )
        
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
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
                max_tokens=500,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Limpar possíveis marcadores
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            status = "✅ APROVADO" if result.get("aprovado") else "❌ REJEITADO"
            logger.info(f"  Resultado: {status}")
            logger.info(f"  Motivo: {result.get('motivo', 'N/A')}")
            logger.info(f"  Confiança: {result.get('confianca', 0)}%")
            
            results.append({
                "username": profile["username"],
                "name": profile["name"],
                "approved": result.get("aprovado", False),
                "screening": result
            })
            
        except Exception as e:
            logger.error(f"  Erro: {e}")
            results.append({
                "username": profile["username"],
                "name": profile["name"],
                "approved": False,
                "error": str(e)
            })
    
    # Resumo
    approved = [r for r in results if r.get("approved")]
    rejected = [r for r in results if not r.get("approved")]
    
    logger.info("\n" + "=" * 60)
    logger.info("RESUMO DA TRIAGEM")
    logger.info("=" * 60)
    logger.info(f"Total analisados: {len(results)}")
    logger.info(f"Aprovados: {len(approved)}")
    logger.info(f"Rejeitados: {len(rejected)}")
    
    logger.info("\n✅ APROVADOS:")
    for r in approved:
        logger.info(f"  - @{r['username']} ({r['name']})")
        logger.info(f"    Motivo: {r.get('screening', {}).get('motivo', 'N/A')}")
    
    logger.info("\n❌ REJEITADOS:")
    for r in rejected:
        logger.info(f"  - @{r['username']} ({r['name']})")
        logger.info(f"    Motivo: {r.get('screening', {}).get('motivo', r.get('error', 'N/A'))}")
    
    # Salvar resultados
    output_file = DATA_DIR / "test_screening_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nResultados salvos em: {output_file}")
    
    return results


if __name__ == "__main__":
    test_gpt_screening()
