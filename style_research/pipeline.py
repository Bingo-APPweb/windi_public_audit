#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Pipeline Orchestrator v2.0.0
==========================================================
Com hash de fonte e confidence score
28 Janeiro 2026 - Three Dragons Protocol
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from domains import is_allowed, get_domain_category, ALLOWED_STYLE_DOMAINS
from fetcher import fetch_html, safe_fetch, FetchError
from extractor import extract_all
from profiler import build_profile, save_profile, load_profile, list_profiles, StyleProfile

VERSION = "2.0.0"

KNOWN_STYLE_SOURCES: Dict[str, Dict[str, Any]] = {
    "mit_technical": {
        "name": "MIT Technical Report",
        "category": "ACADEMIC",
        "urls": ["https://libraries.mit.edu/distinctive-collections/thesis-specs/"],
        "description": "Estilo técnico/acadêmico do MIT",
    },
    "eu_official": {
        "name": "EU Official Document",
        "category": "GOVERNMENT",
        "urls": ["https://europa.eu/european-union/abouteuropa/legal_notices_en"],
        "description": "Estilo oficial da União Europeia",
    },
    "german_government": {
        "name": "German Government Official",
        "category": "GOVERNMENT",
        "urls": ["https://www.bundesregierung.de/breg-de"],
        "description": "Estilo oficial do governo alemão",
    },
    "bmbf_research": {
        "name": "BMBF Research Format",
        "category": "GOVERNMENT",
        "urls": ["https://www.bmbf.de/bmbf/de/forschung/forschung_node.html"],
        "description": "Formato de pesquisa do Ministério alemão",
    },
    "iso_standard": {
        "name": "ISO Standard Document",
        "category": "ORGANIZATION",
        "urls": ["https://www.iso.org/standards.html"],
        "description": "Formato de padrões ISO",
    },
}


def detect_style_request(user_input: str) -> Optional[str]:
    input_lower = user_input.lower()
    keyword_map = {
        "mit": "mit_technical",
        "eu": "eu_official",
        "europa": "eu_official",
        "european": "eu_official",
        "união europeia": "eu_official",
        "german": "german_government",
        "deutsch": "german_government",
        "bundesregierung": "german_government",
        "bmbf": "bmbf_research",
        "forschung": "bmbf_research",
        "iso": "iso_standard",
    }
    for keyword, style_key in keyword_map.items():
        if keyword in input_lower:
            return style_key
    return None


def research_style(
    style_key: str,
    force_refresh: bool = False,
    max_sources: int = 3
) -> Tuple[Optional[StyleProfile], Dict[str, Any]]:
    """
    Pesquisa e cria/carrega um perfil de estilo.
    VERSÃO 2.0: Com hash de fonte e confidence score.
    """
    metadata = {
        "style_key": style_key,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": None,
        "sources_fetched": 0,
        "errors": [],
    }
    
    if style_key not in KNOWN_STYLE_SOURCES:
        metadata["action"] = "error"
        metadata["errors"].append(f"Estilo desconhecido: {style_key}")
        return None, metadata
    
    style_config = KNOWN_STYLE_SOURCES[style_key]
    style_id = f"style_{style_key}_v1"
    
    # CACHE: Verificar cache PRIMEIRO
    if not force_refresh:
        cached = load_profile(style_id)
        if cached:
            metadata["action"] = "cached"
            print(f"[WINDI] 💾 Cache HIT: {style_id}")
            return cached, metadata
    
    # Só faz fetch se não tem cache
    print(f"[WINDI] 🔍 Pesquisando estilo: {style_config['name']}")
    print(f"[WINDI] 📡 Cache MISS - iniciando pesquisa controlada")
    metadata["action"] = "researched"
    
    extractions = []
    successful_urls = []
    source_contents = {}  # NOVO: guardar HTML para hash
    
    for url in style_config["urls"][:max_sources]:
        print(f"[WINDI]    Fetching: {url}")
        result = safe_fetch(url)
        if result:
            html, fetch_meta = result
            extraction = extract_all(html)
            extractions.append(extraction)
            successful_urls.append(url)
            source_contents[url] = html  # NOVO: guardar conteúdo
            metadata["sources_fetched"] += 1
            print(f"[WINDI]    ✅ Extraído: {extraction['structure']['heading_count']} headings")
            print(f"[WINDI]    📊 Seções: {extraction['structure'].get('detected_sections', [])}")
        else:
            metadata["errors"].append(f"Falha: {url}")
    
    if not extractions:
        metadata["action"] = "error"
        metadata["errors"].append("Nenhuma fonte acessada")
        return None, metadata
    
    # NOVO: passar source_contents para hash
    profile = build_profile(
        style_name=style_config["name"],
        sources=successful_urls,
        extractions=extractions,
        domain_category=style_config["category"],
        source_contents=source_contents
    )
    
    profile.style_id = style_id
    save_profile(profile)
    
    # Log de explicabilidade
    print(f"[WINDI] 🎓 Aprendizado institucional completo:")
    print(f"[WINDI]    Fonte: {style_config['category']}")
    print(f"[WINDI]    Confiança: {profile.confidence_score}")
    print(f"[WINDI]    Frozen: {profile.frozen}")
    
    return profile, metadata


def get_style_for_generator(style_key: str) -> Optional[Dict[str, Any]]:
    profile, meta = research_style(style_key)
    if not profile:
        return None
    return {
        "style_id": profile.style_id,
        "style_name": profile.style_name,
        "sections": profile.recommended_sections,
        "heading_style": profile.heading_style,
        "tone": profile.tone,
        "voice": profile.voice,
        "density": profile.density,
        "avg_paragraph_length": profile.avg_paragraph_length,
        "uses_lists": profile.uses_lists,
        "uses_tables": profile.uses_tables,
        "confidence_score": profile.confidence_score,
        "frozen": profile.frozen,
        "from_cache": meta["action"] == "cached",
    }


def list_available_styles() -> List[Dict[str, str]]:
    styles = []
    for key, config in KNOWN_STYLE_SOURCES.items():
        style_id = f"style_{key}_v1"
        cached_profile = load_profile(style_id)
        styles.append({
            "key": key,
            "name": config["name"],
            "category": config["category"],
            "description": config["description"],
            "cached": cached_profile is not None,
            "confidence": cached_profile.confidence_score if cached_profile else 0,
            "frozen": cached_profile.frozen if cached_profile else False,
        })
    return styles


if __name__ == "__main__":
    print(f"WINDI Pipeline v{VERSION} - Blindagem de Produção")
    print("=" * 60)
    
    # Listar estilos
    print("\n📚 ESTILOS DISPONÍVEIS:")
    for s in list_available_styles():
        cached = "💾" if s["cached"] else "🌐"
        frozen = "🔒" if s["frozen"] else ""
        conf = f"({s['confidence']:.0%})" if s["confidence"] else ""
        print(f"   {cached}{frozen} {s['key']}: {s['name']} {conf}")
    
    print("\n" + "=" * 60)
    print("✅ Pipeline v2.0.0 operacional!")
