#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WINDI Style Research Engine - Style Profiler v2.0.0
====================================================
BLINDAGEM DE PRODUÇÃO:
- Versionamento automático (nunca sobrescreve)
- Hash da fonte (detecta mudanças)
- Confidence score + extraction method
- Imutabilidade após criação

28 Janeiro 2026 - Three Dragons Protocol
"AI processes. Human decides. WINDI guarantees."
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import Counter

VERSION = "2.0.0"
STYLES_DIR = "/opt/windi/data/styles"


@dataclass
class StyleProfile:
    """Perfil de estilo institucional - IMUTÁVEL após criação."""
    
    # Identificação
    style_id: str
    style_name: str
    version: str = "1.0.0"
    
    # Fontes e rastreabilidade
    sources: List[str] = field(default_factory=list)
    source_hashes: Dict[str, str] = field(default_factory=dict)  # NOVO: hash de cada fonte
    domain_category: str = "UNKNOWN"
    
    # Estrutura
    recommended_sections: List[str] = field(default_factory=list)
    heading_style: str = "numbered"
    typical_heading_levels: Dict[str, int] = field(default_factory=dict)
    
    # Tom e voz
    tone: str = "formal"
    voice: str = "passive"
    
    # Formatação
    density: str = "medium"
    avg_paragraph_length: int = 200
    uses_lists: bool = True
    uses_tables: bool = False
    
    # Tipografia
    font_family_hint: List[str] = field(default_factory=list)
    font_size_hint: List[str] = field(default_factory=list)
    
    # Confiança e método (NOVO)
    confidence_score: float = 0.0
    extraction_method: str = "rule_based_v2"
    extraction_rules_version: str = "1.0.0"
    
    # Metadata
    created_at: str = ""
    created_by: str = "WINDI Style Research Engine"
    frozen: bool = False  # NOVO: imutabilidade
    frozen_at: str = ""
    profile_hash: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        self._compute_hash()
    
    def _compute_hash(self):
        content = f"{self.style_id}{self.style_name}{self.sources}{self.tone}{self.voice}"
        self.profile_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def freeze(self):
        """Congela o profile - não pode mais ser alterado."""
        self.frozen = True
        self.frozen_at = datetime.utcnow().isoformat() + "Z"
        self._compute_hash()
        print(f"[WINDI] 🔒 Profile FROZEN: {self.style_id}")
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StyleProfile':
        data = json.loads(json_str)
        return cls(**data)


def compute_source_hash(html_content: str) -> str:
    """Computa hash do conteúdo HTML para detectar mudanças futuras."""
    return hashlib.sha256(html_content.encode()).hexdigest()[:16]


def calculate_confidence(extractions: List[Dict]) -> float:
    """
    Calcula score de confiança baseado na qualidade das extrações.
    
    Fatores:
    - Quantidade de headings encontrados
    - Presença de seções reconhecidas
    - Consistência entre fontes
    """
    if not extractions:
        return 0.0
    
    scores = []
    
    for ext in extractions:
        score = 0.0
        
        # Headings encontrados (max 0.3)
        heading_count = ext.get('structure', {}).get('heading_count', 0)
        if heading_count >= 10:
            score += 0.3
        elif heading_count >= 5:
            score += 0.2
        elif heading_count >= 1:
            score += 0.1
        
        # Seções reconhecidas (max 0.3)
        sections = ext.get('structure', {}).get('detected_sections', [])
        if len(sections) >= 4:
            score += 0.3
        elif len(sections) >= 2:
            score += 0.2
        elif len(sections) >= 1:
            score += 0.1
        
        # Tom detectado (max 0.2)
        tone = ext.get('tone', {}).get('tone_classification', '')
        if tone in ['formal', 'highly_formal']:
            score += 0.2
        elif tone:
            score += 0.1
        
        # Formatação detectada (max 0.2)
        if ext.get('formatting', {}).get('paragraph_count', 0) > 0:
            score += 0.2
        
        scores.append(score)
    
    # Média das extrações
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    # Bonus por múltiplas fontes consistentes
    if len(extractions) > 1:
        avg_score = min(1.0, avg_score + 0.1)
    
    return round(avg_score, 2)


def get_next_version(style_key: str, directory: str = STYLES_DIR) -> str:
    """
    Encontra a próxima versão disponível para um estilo.
    Nunca sobrescreve - sempre incrementa.
    """
    path = Path(directory)
    if not path.exists():
        return "v1"
    
    existing = list(path.glob(f"style_{style_key}_v*.json"))
    if not existing:
        return "v1"
    
    # Extrair números de versão
    versions = []
    for f in existing:
        try:
            v = f.stem.split('_v')[-1]
            versions.append(int(v))
        except:
            pass
    
    if not versions:
        return "v1"
    
    return f"v{max(versions) + 1}"


def build_profile(
    style_name: str,
    sources: List[str],
    extractions: List[Dict],
    domain_category: str,
    source_contents: Dict[str, str] = None  # NOVO: conteúdo HTML para hash
) -> StyleProfile:
    """
    Constrói um StyleProfile a partir de extrações.
    VERSÃO 2.0: Com hash de fonte e confidence score.
    """
    # Gerar ID base
    style_id_base = style_name.lower().replace(' ', '_').replace('-', '_')
    style_id_base = ''.join(c for c in style_id_base if c.isalnum() or c == '_')
    
    # Agregar dados de múltiplas extrações
    all_sections = []
    all_tones = []
    all_voices = []
    all_densities = []
    all_heading_levels = Counter()
    total_para_length = 0
    para_count = 0
    uses_lists = False
    uses_tables = False
    heading_styles = []
    font_families = []
    font_sizes = []
    
    for ext in extractions:
        structure = ext.get('structure', {})
        formatting = ext.get('formatting', {})
        tone_data = ext.get('tone', {})
        
        all_sections.extend(structure.get('detected_sections', []))
        
        if tone_data.get('tone_classification'):
            all_tones.append(tone_data['tone_classification'])
        if tone_data.get('voice_classification'):
            all_voices.append(tone_data['voice_classification'])
        
        if formatting.get('density_classification'):
            all_densities.append(formatting['density_classification'])
        
        for level, count in structure.get('heading_levels', {}).items():
            all_heading_levels[level] += count
        
        if formatting.get('avg_paragraph_length'):
            total_para_length += formatting['avg_paragraph_length']
            para_count += 1
        
        if formatting.get('list_count', 0) > 0:
            uses_lists = True
        if formatting.get('table_count', 0) > 0:
            uses_tables = True
        
        if structure.get('has_numbered_headings'):
            heading_styles.append('numbered')
        elif structure.get('has_caps_headings'):
            heading_styles.append('caps')
        else:
            heading_styles.append('unnumbered')
        
        font_families.extend(formatting.get('font_families', []))
        font_sizes.extend(formatting.get('font_sizes', []))
    
    # Determinar valores finais
    section_order = ['abstract', 'introduction', 'methodology', 'results', 
                     'discussion', 'conclusion', 'references', 'appendix']
    unique_sections = list(dict.fromkeys(all_sections))
    ordered_sections = [s for s in section_order if s in unique_sections]
    
    def most_common(lst, default):
        if not lst:
            return default
        return Counter(lst).most_common(1)[0][0]
    
    final_tone = most_common(all_tones, 'formal')
    final_voice = most_common(all_voices, 'passive')
    final_density = most_common(all_densities, 'medium')
    final_heading_style = most_common(heading_styles, 'numbered')
    
    avg_para = int(total_para_length / para_count) if para_count > 0 else 200
    
    # Calcular hashes das fontes
    source_hashes = {}
    if source_contents:
        for url, content in source_contents.items():
            source_hashes[url] = compute_source_hash(content)
    
    # Calcular confidence
    confidence = calculate_confidence(extractions)
    
    return StyleProfile(
        style_id=f"style_{style_id_base}",  # Sem versão ainda
        style_name=style_name,
        sources=sources,
        source_hashes=source_hashes,
        domain_category=domain_category,
        recommended_sections=ordered_sections,
        heading_style=final_heading_style,
        typical_heading_levels=dict(all_heading_levels),
        tone=final_tone,
        voice=final_voice,
        density=final_density,
        avg_paragraph_length=avg_para,
        uses_lists=uses_lists,
        uses_tables=uses_tables,
        font_family_hint=list(set(font_families))[:5],
        font_size_hint=list(set(font_sizes))[:5],
        confidence_score=confidence,
        extraction_method="rule_based_v2",
        extraction_rules_version=VERSION,
    )


def save_profile(profile: StyleProfile, directory: str = STYLES_DIR, auto_freeze: bool = True) -> str:
    """
    Salva perfil como JSON.
    VERSÃO 2.0: Versionamento automático + freeze.
    """
    Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Extrair base do style_id
    base_id = profile.style_id.replace('style_', '').split('_v')[0]
    
    # Determinar versão
    version = get_next_version(base_id, directory)
    
    # Atualizar style_id com versão
    profile.style_id = f"style_{base_id}_{version}"
    profile.version = version.replace('v', '') + ".0.0"
    
    # Auto-freeze após salvar
    if auto_freeze:
        profile.freeze()
    
    filename = f"{profile.style_id}.json"
    filepath = Path(directory) / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(profile.to_json())
    
    print(f"[WINDI] ✅ Style profile saved: {filepath}")
    print(f"[WINDI] 📊 Confidence: {profile.confidence_score} | Method: {profile.extraction_method}")
    
    return str(filepath)


def load_profile(style_id: str, directory: str = STYLES_DIR) -> Optional[StyleProfile]:
    """Carrega perfil do disco."""
    filepath = Path(directory) / f"{style_id}.json"
    
    if not filepath.exists():
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return StyleProfile.from_json(f.read())


def list_profiles(directory: str = STYLES_DIR) -> List[Dict[str, Any]]:
    """Lista todos os perfis disponíveis com metadados."""
    path = Path(directory)
    if not path.exists():
        return []
    
    profiles = []
    for f in path.glob("style_*.json"):
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                profiles.append({
                    'style_id': data.get('style_id'),
                    'style_name': data.get('style_name'),
                    'version': data.get('version'),
                    'confidence': data.get('confidence_score', 0),
                    'frozen': data.get('frozen', False),
                    'created_at': data.get('created_at'),
                })
        except:
            pass
    
    return sorted(profiles, key=lambda x: x.get('created_at', ''), reverse=True)


if __name__ == "__main__":
    print(f"WINDI Style Profiler v{VERSION} - Blindagem de Produção")
    print("=" * 60)
    
    # Listar profiles existentes
    profiles = list_profiles()
    print(f"\n📚 {len(profiles)} profiles encontrados:")
    for p in profiles[:5]:
        frozen_icon = "🔒" if p['frozen'] else "🔓"
        conf = p.get('confidence', 0)
        print(f"   {frozen_icon} {p['style_id']} (conf: {conf})")
    
    print("\n" + "=" * 60)
    print("✅ Profiler v2.0.0 com blindagem de produção!")
