#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Pattern Extractor
================================================
Extrai PADRÕES estruturais, NÃO conteúdo.
28 Janeiro 2026 - Three Dragons Protocol

Invariante I5: No Fabrication - extraímos estrutura, não copiamos texto
"""

from bs4 import BeautifulSoup
from collections import Counter
from typing import Dict, List, Any
import re

VERSION = "1.0.0"


def extract_structure(html: str) -> Dict[str, Any]:
    """
    Extrai estrutura de headings e seções.
    
    Returns:
        Dict com padrões estruturais detectados
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remover scripts e styles
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    
    # Extrair headings na ordem que aparecem
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = tag.get_text(" ", strip=True)
        if text and len(text) > 2:
            # Normalizar - só guardamos padrão, não conteúdo específico
            headings.append({
                "level": tag.name,
                "length": len(text),
                "has_number": bool(re.match(r'^\d+[\.\)]\s', text)),
                "is_caps": text.isupper(),
            })
    
    # Contar distribuição de níveis
    level_counts = Counter(h["level"] for h in headings)
    
    # Detectar padrões
    has_numbered_headings = any(h["has_number"] for h in headings)
    has_caps_headings = any(h["is_caps"] for h in headings)
    
    # Detectar seções típicas por keywords (sem guardar texto real)
    text_lower = soup.get_text().lower()
    detected_sections = []
    
    section_keywords = {
        "abstract": ["abstract", "zusammenfassung", "resumo"],
        "introduction": ["introduction", "einleitung", "einführung"],
        "methodology": ["method", "methodik", "metodologia"],
        "results": ["results", "ergebnisse", "resultados"],
        "discussion": ["discussion", "diskussion", "discussão"],
        "conclusion": ["conclusion", "fazit", "schlussfolgerung"],
        "references": ["references", "literatur", "referências", "bibliography"],
        "appendix": ["appendix", "anhang", "anexo"],
    }
    
    for section, keywords in section_keywords.items():
        if any(kw in text_lower for kw in keywords):
            detected_sections.append(section)
    
    return {
        "heading_count": len(headings),
        "heading_levels": dict(level_counts),
        "has_numbered_headings": has_numbered_headings,
        "has_caps_headings": has_caps_headings,
        "detected_sections": detected_sections,
        "headings_sample": headings[:20],  # Só metadados, não texto
    }


def extract_formatting(html: str) -> Dict[str, Any]:
    """
    Extrai sinais de formatação (CSS patterns, tipografia).
    """
    # Padrões CSS comuns
    font_families = re.findall(r'font-family\s*:\s*([^;}{]+)', html, re.I)
    font_sizes = re.findall(r'font-size\s*:\s*([^;}{]+)', html, re.I)
    line_heights = re.findall(r'line-height\s*:\s*([^;}{]+)', html, re.I)
    
    def top_values(values: List[str], n: int = 3) -> List[str]:
        cleaned = [v.strip().lower() for v in values if v.strip()]
        return [v for v, _ in Counter(cleaned).most_common(n)]
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Detectar densidade de parágrafos
    paragraphs = soup.find_all("p")
    para_lengths = [len(p.get_text()) for p in paragraphs if p.get_text().strip()]
    avg_para_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0
    
    # Detectar listas
    lists = soup.find_all(["ul", "ol"])
    list_items = soup.find_all("li")
    
    # Detectar tabelas
    tables = soup.find_all("table")
    
    return {
        "font_families": top_values(font_families),
        "font_sizes": top_values(font_sizes),
        "line_heights": top_values(line_heights),
        "avg_paragraph_length": round(avg_para_length),
        "paragraph_count": len(para_lengths),
        "list_count": len(lists),
        "list_items_count": len(list_items),
        "table_count": len(tables),
        "density": "dense" if avg_para_length > 300 else "medium" if avg_para_length > 150 else "light",
    }


def extract_tone_signals(html: str) -> Dict[str, Any]:
    """
    Detecta sinais de tom/voz do documento.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().lower()
    
    # Indicadores de formalidade
    formal_indicators = [
        "pursuant to", "hereby", "whereas", "therefore",
        "gemäß", "hiermit", "aufgrund", "dementsprechend",
        "conforme", "mediante", "portanto",
    ]
    
    informal_indicators = [
        "you'll", "we're", "don't", "can't", "let's",
        "awesome", "cool", "stuff", "guys",
    ]
    
    # Voz passiva (simplificado)
    passive_patterns = [
        r'\bis\s+\w+ed\b', r'\bare\s+\w+ed\b', r'\bwas\s+\w+ed\b',
        r'\bwird\s+\w+t\b', r'\bwerden\s+\w+t\b',
    ]
    
    formal_count = sum(1 for ind in formal_indicators if ind in text)
    informal_count = sum(1 for ind in informal_indicators if ind in text)
    passive_count = sum(len(re.findall(p, text)) for p in passive_patterns)
    
    # Determinar tom
    if formal_count > 3 and informal_count == 0:
        tone = "highly_formal"
    elif formal_count > informal_count:
        tone = "formal"
    elif informal_count > formal_count:
        tone = "informal"
    else:
        tone = "neutral"
    
    # Determinar voz predominante
    voice = "passive" if passive_count > 10 else "mixed" if passive_count > 3 else "active"
    
    return {
        "tone": tone,
        "voice": voice,
        "formal_indicator_count": formal_count,
        "informal_indicator_count": informal_count,
        "passive_constructions": passive_count,
    }


def extract_all(html: str) -> Dict[str, Any]:
    """
    Extrai todos os padrões de uma página.
    """
    return {
        "structure": extract_structure(html),
        "formatting": extract_formatting(html),
        "tone": extract_tone_signals(html),
        "extractor_version": VERSION,
    }


if __name__ == "__main__":
    # Teste com HTML de exemplo
    test_html = """
    <html>
    <head><style>body { font-family: Arial; font-size: 14px; }</style></head>
    <body>
        <h1>1. Introduction</h1>
        <p>This document describes the methodology pursuant to EU regulations.</p>
        <h2>1.1 Background</h2>
        <p>The approach was developed and is hereby presented for review.</p>
        <h2>2. METHODOLOGY</h2>
        <p>Data was collected and analyzed. Results were obtained through careful examination.</p>
        <h3>2.1 Data Collection</h3>
        <ul><li>Item 1</li><li>Item 2</li></ul>
        <h2>3. Results</h2>
        <p>The findings demonstrate significant improvements.</p>
        <h2>4. Conclusion</h2>
        <p>Therefore, the methodology is recommended for adoption.</p>
        <h2>References</h2>
        <p>Bibliography items here.</p>
    </body>
    </html>
    """
    
    print("WINDI Pattern Extractor Test")
    print("=" * 50)
    
    result = extract_all(test_html)
    
    print("\n📊 STRUCTURE:")
    print(f"   Headings: {result['structure']['heading_count']}")
    print(f"   Levels: {result['structure']['heading_levels']}")
    print(f"   Numbered: {result['structure']['has_numbered_headings']}")
    print(f"   Sections: {result['structure']['detected_sections']}")
    
    print("\n🎨 FORMATTING:")
    print(f"   Density: {result['formatting']['density']}")
    print(f"   Paragraphs: {result['formatting']['paragraph_count']}")
    print(f"   Lists: {result['formatting']['list_count']}")
    
    print("\n🎭 TONE:")
    print(f"   Tone: {result['tone']['tone']}")
    print(f"   Voice: {result['tone']['voice']}")
    print(f"   Formal indicators: {result['tone']['formal_indicator_count']}")
    
    print("\n✅ Extractor funcionando!")
