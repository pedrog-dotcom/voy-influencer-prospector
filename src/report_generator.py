"""
Gerador de relatórios para prospecção de influenciadores.
Gera relatórios em diferentes formatos para análise.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import DATA_DIR
from models import ProspectionResult, Influencer


class ReportGenerator:
    """Gera relatórios de prospecção em diferentes formatos."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Inicializa o gerador de relatórios.
        
        Args:
            data_dir: Diretório de dados (opcional).
        """
        self.data_dir = data_dir or DATA_DIR
    
    def generate_daily_report(
        self, 
        result: ProspectionResult,
        format_type: str = "markdown"
    ) -> str:
        """
        Gera relatório diário de prospecção.
        
        Args:
            result: Resultado da prospecção.
            format_type: Tipo de formato (markdown, html, text).
            
        Returns:
            Conteúdo do relatório.
        """
        if format_type == "markdown":
            return self._generate_markdown_report(result)
        elif format_type == "html":
            return self._generate_html_report(result)
        else:
            return self._generate_text_report(result)
    
    def _generate_markdown_report(self, result: ProspectionResult) -> str:
        """Gera relatório em formato Markdown."""
        lines = [
            f"# 📊 Relatório de Prospecção - {result.date}",
            "",
            "## 📈 Resumo Executivo",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Data | {result.date} |",
            f"| Total Encontrados | {result.total_found} |",
            f"| Total Qualificados | {result.total_qualified} |",
            f"| Selecionados | {len(result.influencers)} |",
            f"| Tempo de Execução | {result.execution_time_seconds:.2f}s |",
            "",
            "## 🎯 Influenciadores Prospectados",
            "",
        ]
        
        # Tabela de influenciadores
        lines.extend([
            "| # | Nome | Plataforma | Username | Seguidores | Engajamento |",
            "|---|------|------------|----------|------------|-------------|",
        ])
        
        for i, inf in enumerate(result.influencers, 1):
            profile = inf.profiles[0] if inf.profiles else None
            if profile:
                lines.append(
                    f"| {i} | {inf.name[:25]} | {inf.primary_platform.value} | "
                    f"@{profile.username[:15]} | {profile.followers:,} | "
                    f"{profile.engagement_rate}% |"
                )
        
        lines.append("")
        
        # Detalhes por influenciador
        lines.extend([
            "## 📋 Detalhes dos Influenciadores",
            "",
        ])
        
        for i, inf in enumerate(result.influencers, 1):
            profile = inf.profiles[0] if inf.profiles else None
            
            lines.extend([
                f"### {i}. {inf.name}",
                "",
            ])
            
            if profile:
                lines.extend([
                    f"- **Plataforma:** {inf.primary_platform.value.capitalize()}",
                    f"- **Username:** @{profile.username}",
                    f"- **URL:** {profile.url}",
                    f"- **Seguidores:** {profile.followers:,}",
                    f"- **Taxa de Engajamento:** {profile.engagement_rate}%",
                    f"- **Média de Likes:** {profile.avg_likes:,}",
                    f"- **Verificado:** {'✅ Sim' if profile.verified else '❌ Não'}",
                ])
            
            if inf.bio:
                lines.append(f"- **Bio:** {inf.bio[:150]}...")
            
            if inf.source_keyword:
                lines.append(f"- **Palavra-chave:** {inf.source_keyword}")
            
            lines.append("")
        
        # Palavras-chave utilizadas
        if result.keywords_used:
            lines.extend([
                "## 🔍 Palavras-chave Utilizadas",
                "",
            ])
            for kw in result.keywords_used:
                lines.append(f"- {kw}")
            lines.append("")
        
        # Erros
        if result.errors:
            lines.extend([
                "## ⚠️ Erros Encontrados",
                "",
            ])
            for error in result.errors:
                lines.append(f"- {error}")
            lines.append("")
        
        lines.extend([
            "---",
            f"*Relatório gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ])
        
        return "\n".join(lines)
    
    def _generate_html_report(self, result: ProspectionResult) -> str:
        """Gera relatório em formato HTML."""
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Prospecção - {result.date}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .metric {{
            text-align: center;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 8px;
        }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
        .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        th {{ background: #2c3e50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 12px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
        .platform-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .instagram {{ background: #e1306c; color: white; }}
        .tiktok {{ background: #000000; color: white; }}
        .youtube {{ background: #ff0000; color: white; }}
        .engagement {{ color: #27ae60; font-weight: bold; }}
        .verified {{ color: #3498db; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>📊 Relatório de Prospecção - {result.date}</h1>
    
    <div class="summary">
        <h2>📈 Resumo Executivo</h2>
        <div class="summary-grid">
            <div class="metric">
                <div class="metric-value">{result.total_found}</div>
                <div class="metric-label">Encontrados</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.total_qualified}</div>
                <div class="metric-label">Qualificados</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(result.influencers)}</div>
                <div class="metric-label">Selecionados</div>
            </div>
            <div class="metric">
                <div class="metric-value">{result.execution_time_seconds:.1f}s</div>
                <div class="metric-label">Tempo</div>
            </div>
        </div>
    </div>
    
    <h2>🎯 Influenciadores Prospectados</h2>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Nome</th>
                <th>Plataforma</th>
                <th>Username</th>
                <th>Seguidores</th>
                <th>Engajamento</th>
                <th>Link</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for i, inf in enumerate(result.influencers, 1):
            profile = inf.profiles[0] if inf.profiles else None
            if profile:
                platform_class = inf.primary_platform.value
                html += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{inf.name}</strong></td>
                <td><span class="platform-badge {platform_class}">{platform_class.upper()}</span></td>
                <td>@{profile.username}</td>
                <td>{profile.followers:,}</td>
                <td class="engagement">{profile.engagement_rate}%</td>
                <td><a href="{profile.url}" target="_blank">Visitar</a></td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <footer style="margin-top: 40px; text-align: center; color: #7f8c8d;">
        <p>Relatório gerado automaticamente pelo sistema de prospecção Voy Saúde</p>
    </footer>
</body>
</html>
"""
        return html
    
    def _generate_text_report(self, result: ProspectionResult) -> str:
        """Gera relatório em formato texto simples."""
        lines = [
            "=" * 60,
            "RELATÓRIO DE PROSPECÇÃO - VOY SAÚDE",
            "=" * 60,
            f"Data: {result.date}",
            "",
            "RESUMO:",
            f"  - Total encontrados: {result.total_found}",
            f"  - Total qualificados: {result.total_qualified}",
            f"  - Selecionados: {len(result.influencers)}",
            f"  - Tempo de execução: {result.execution_time_seconds:.2f}s",
            "",
            "-" * 60,
            "INFLUENCIADORES:",
            "-" * 60,
        ]
        
        for i, inf in enumerate(result.influencers, 1):
            profile = inf.profiles[0] if inf.profiles else None
            lines.append(f"\n{i}. {inf.name}")
            if profile:
                lines.extend([
                    f"   Plataforma: {inf.primary_platform.value}",
                    f"   Username: @{profile.username}",
                    f"   Seguidores: {profile.followers:,}",
                    f"   Engajamento: {profile.engagement_rate}%",
                    f"   URL: {profile.url}",
                ])
        
        lines.extend([
            "",
            "=" * 60,
            f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ])
        
        return "\n".join(lines)
    
    def save_report(
        self, 
        result: ProspectionResult, 
        format_type: str = "markdown"
    ) -> Path:
        """
        Salva o relatório em arquivo.
        
        Args:
            result: Resultado da prospecção.
            format_type: Tipo de formato.
            
        Returns:
            Caminho do arquivo salvo.
        """
        extensions = {
            "markdown": ".md",
            "html": ".html",
            "text": ".txt",
        }
        
        ext = extensions.get(format_type, ".txt")
        filename = f"report_{result.date}{ext}"
        filepath = self.data_dir / filename
        
        content = self.generate_daily_report(result, format_type)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
