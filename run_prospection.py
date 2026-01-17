#!/usr/bin/env python3
"""
Script principal para execução da prospecção diária de influenciadores.
Voy Saúde - Prospecção de Influenciadores

Uso:
    python run_prospection.py [--count N] [--output-format FORMAT]

Opções:
    --count N           Número de influenciadores a prospectar (padrão: 20)
    --output-format     Formato de saída: json, csv, markdown (padrão: json)
"""

import sys
import argparse
import json
import csv
import logging
from pathlib import Path
from datetime import datetime

# Adicionar diretório src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from prospector_v2 import InfluencerProspectorV2
from models import ProspectionResult
from config import DATA_DIR, DAILY_PROSPECT_COUNT


def export_to_csv(result: ProspectionResult, output_path: Path):
    """Exporta resultado para CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Cabeçalho
        writer.writerow([
            'Nome',
            'Plataforma Principal',
            'Username',
            'URL',
            'Seguidores',
            'Taxa de Engajamento (%)',
            'Média de Likes',
            'Verificado',
            'Bio',
            'Palavra-chave Fonte',
            'Data Prospecção',
            'Notas',
        ])
        
        # Dados
        for influencer in result.influencers:
            profile = influencer.profiles[0] if influencer.profiles else None
            writer.writerow([
                influencer.name,
                influencer.primary_platform.value,
                profile.username if profile else '',
                profile.url if profile else '',
                profile.followers if profile else 0,
                profile.engagement_rate if profile else 0,
                profile.avg_likes if profile else 0,
                'Sim' if (profile and profile.verified) else 'Não',
                influencer.bio[:100] if influencer.bio else '',
                influencer.source_keyword,
                influencer.prospected_at,
                influencer.notes,
            ])


def export_to_markdown(result: ProspectionResult, output_path: Path):
    """Exporta resultado para Markdown."""
    lines = [
        f"# Prospecção de Influenciadores - {result.date}",
        "",
        "## Resumo",
        "",
        f"- **Data:** {result.date}",
        f"- **Total encontrados:** {result.total_found}",
        f"- **Total qualificados (engajamento >= 2.5%):** {result.total_qualified}",
        f"- **Selecionados:** {len(result.influencers)}",
        f"- **Tempo de execução:** {result.execution_time_seconds:.2f}s",
        "",
        "## Influenciadores Prospectados",
        "",
        "| # | Nome | Plataforma | Username | Seguidores | Engajamento | URL |",
        "|---|------|------------|----------|------------|-------------|-----|",
    ]
    
    for i, influencer in enumerate(result.influencers, 1):
        profile = influencer.profiles[0] if influencer.profiles else None
        if profile:
            lines.append(
                f"| {i} | {influencer.name[:25]} | {influencer.primary_platform.value} | "
                f"@{profile.username[:15]} | {profile.followers:,} | "
                f"{profile.engagement_rate}% | [Link]({profile.url}) |"
            )
    
    lines.append("")
    lines.append("## Detalhes")
    lines.append("")
    
    for i, influencer in enumerate(result.influencers, 1):
        profile = influencer.profiles[0] if influencer.profiles else None
        
        lines.extend([
            f"### {i}. {influencer.name}",
            "",
        ])
        
        if profile:
            lines.extend([
                f"- **Plataforma:** {influencer.primary_platform.value.capitalize()}",
                f"- **Username:** @{profile.username}",
                f"- **URL:** {profile.url}",
                f"- **Seguidores:** {profile.followers:,}",
                f"- **Taxa de Engajamento:** {profile.engagement_rate}%",
                f"- **Verificado:** {'Sim' if profile.verified else 'Não'}",
            ])
        
        if influencer.bio:
            lines.append(f"- **Bio:** {influencer.bio[:200]}")
        
        if influencer.notes:
            lines.append(f"- **Notas:** {influencer.notes}")
        
        lines.append("")
    
    if result.errors:
        lines.extend([
            "## Erros",
            "",
        ])
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Prospecção diária de influenciadores para Voy Saúde'
    )
    parser.add_argument(
        '--count', 
        type=int, 
        default=DAILY_PROSPECT_COUNT,
        help=f'Número de influenciadores a prospectar (padrão: {DAILY_PROSPECT_COUNT})'
    )
    parser.add_argument(
        '--output-format',
        choices=['json', 'csv', 'markdown', 'all'],
        default='json',
        help='Formato de saída (padrão: json)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verboso com mais detalhes'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("VOY SAÚDE - PROSPECÇÃO DE INFLUENCIADORES")
    print("=" * 60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Meta: {args.count} influenciadores")
    print(f"Formato de saída: {args.output_format}")
    print("=" * 60)
    print()
    
    # Executar prospecção
    prospector = InfluencerProspectorV2()
    result = prospector.run_prospection(target_count=args.count)
    
    # Garantir diretório de saída
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Exportar nos formatos solicitados
    date_str = result.date
    
    if args.output_format in ['json', 'all']:
        json_path = DATA_DIR / f"prospects_{date_str}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"Exportado: {json_path}")
    
    if args.output_format in ['csv', 'all']:
        csv_path = DATA_DIR / f"prospects_{date_str}.csv"
        export_to_csv(result, csv_path)
        print(f"Exportado: {csv_path}")
    
    if args.output_format in ['markdown', 'all']:
        md_path = DATA_DIR / f"prospects_{date_str}.md"
        export_to_markdown(result, md_path)
        print(f"Exportado: {md_path}")
    
    # Exibir resumo
    print()
    print("=" * 60)
    print("RESUMO DA PROSPECÇÃO")
    print("=" * 60)
    print(f"Total encontrados: {result.total_found}")
    print(f"Total qualificados (engajamento >= 2.5%): {result.total_qualified}")
    print(f"Influenciadores selecionados: {len(result.influencers)}")
    print(f"Tempo de execução: {result.execution_time_seconds:.2f}s")
    
    if result.errors:
        print(f"\nErros encontrados: {len(result.errors)}")
    
    print()
    print("-" * 60)
    print("INFLUENCIADORES PROSPECTADOS:")
    print("-" * 60)
    
    for i, influencer in enumerate(result.influencers, 1):
        profile = influencer.profiles[0] if influencer.profiles else None
        platform = influencer.primary_platform.value.upper()
        followers = f"{profile.followers:,}" if profile else "N/A"
        engagement = f"{profile.engagement_rate}%" if profile else "N/A"
        
        print(f"{i:2}. [{platform:7}] {influencer.name[:30]:30} | "
              f"Seg: {followers:>12} | Eng: {engagement:>7}")
        if profile:
            print(f"    URL: {profile.url}")
    
    print()
    print("=" * 60)
    print("Prospecção concluída com sucesso!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
