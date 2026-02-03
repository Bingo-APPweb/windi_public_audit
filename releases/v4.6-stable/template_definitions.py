#!/usr/bin/env python3
"""
WINDI Template Definitions v4.4
===============================
Templates institucionais: EU Official, German Gov, WINDI Formal

KI verarbeitet. Mensch entscheidet. WINDI garantiert.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime


@dataclass
class CoreDNAConfig:
    """DNA comum a todos os templates - NUNCA muda."""
    human_authorship_notice: Dict[str, str] = field(default_factory=lambda: {
        "en": "This document was created and reviewed by human authors. AI assistance was used under human supervision and control. Final decisions and content approval: Human responsibility.",
        "de": "Dieses Dokument wurde von menschlichen Autoren erstellt und geprueft. KI-Unterstuetzung wurde unter menschlicher Aufsicht und Kontrolle eingesetzt. Endgueltige Entscheidungen und Inhaltsfreigabe: Menschliche Verantwortung.",
        "pt": "Este documento foi criado e revisado por autores humanos. Assistencia de IA foi utilizada sob supervisao e controle humano. Decisoes finais e aprovacao de conteudo: Responsabilidade humana."
    })
    governance_seal: str = "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
    compliance_declaration: str = "EU AI Act Compliant"
    publisher: str = "WINDI Publishing House"
    qr_enabled: bool = True
    hash_algorithm: str = "SHA-256"


CORE_DNA = CoreDNAConfig()

TEMPLATE_EU_OFFICIAL = {
    "id": "eu_official_v1",
    "name": {"en": "EU Official Document", "de": "EU Offizielles Dokument", "pt": "Documento Oficial UE"},
    "description": {"en": "Neutral language, multilingual-ready", "de": "Neutrale Sprache, mehrsprachig", "pt": "Linguagem neutra, multilingue"},
    "category": "eu_official",
    "formality": "diplomatic",
    "languages": ["en", "de", "fr", "es", "it", "pt", "nl", "pl"],
    "typography": {
        "font_family": "Arial, Helvetica, sans-serif",
        "font_size": 11,
        "line_height": 1.5,
        "text_align": "justify"
    },
    "colors": {
        "primary": "#003399",
        "secondary": "#FFCC00",
        "text": "#333333",
        "background": "#FFFFFF"
    },
    "sections": ["header", "reference", "subject", "body", "signature", "footer"],
    "css": """
        .eu-official { font-family: Arial, sans-serif; }
        .eu-official .header { border-bottom: 3px solid #003399; padding-bottom: 15px; }
        .eu-official .footer { border-top: 1px solid #FFCC00; padding-top: 10px; }
        .eu-official .seal { color: #003399; font-weight: bold; }
    """
}

TEMPLATE_GERMAN_GOV = {
    "id": "german_gov_v1",
    "name": {"en": "German Administrative Document", "de": "Deutsches Verwaltungsdokument", "pt": "Documento Administrativo Alemao"},
    "description": {"en": "DIN 5008 standard", "de": "DIN 5008 Standard", "pt": "Padrao DIN 5008"},
    "category": "german_gov",
    "formality": "administrative",
    "languages": ["de", "en"],
    "typography": {
        "font_family": "Arial, sans-serif",
        "font_size": 11,
        "line_height": 1.4,
        "text_align": "left"
    },
    "colors": {
        "primary": "#000000",
        "secondary": "#CC0000",
        "text": "#000000",
        "background": "#FFFFFF"
    },
    "sections": ["header", "absender", "empfaenger", "betreff", "bezug", "body", "grussformel", "anlage", "footer"],
    "fields": {
        "aktenzeichen": {"de": "Aktenzeichen", "en": "File Reference"},
        "ihr_zeichen": {"de": "Ihr Zeichen", "en": "Your Reference"},
        "unser_zeichen": {"de": "Unser Zeichen", "en": "Our Reference"},
        "datum": {"de": "Datum", "en": "Date"}
    },
    "css": """
        .german-gov { font-family: Arial, sans-serif; }
        .german-gov .betreff { font-weight: bold; margin: 8mm 0; }
        .german-gov .grussformel { margin-top: 17mm; }
        .german-gov .anlage { margin-top: 10mm; font-size: 10pt; }
    """
}

TEMPLATE_WINDI_FORMAL = {
    "id": "windi_formal_v1",
    "name": {"en": "WINDI Formal Document", "de": "WINDI Formelles Dokument", "pt": "Documento Formal WINDI"},
    "description": {"en": "WINDI institutional identity", "de": "WINDI institutionelle Identitaet", "pt": "Identidade institucional WINDI"},
    "category": "windi_formal",
    "formality": "professional",
    "languages": ["de", "en", "pt"],
    "typography": {
        "font_family": "Segoe UI, Arial, sans-serif",
        "font_size": 11,
        "line_height": 1.6,
        "text_align": "left"
    },
    "colors": {
        "primary": "#1a5f2a",
        "secondary": "#2d8a3e",
        "accent": "#d4af37",
        "text": "#2c3e50",
        "background": "#FFFFFF"
    },
    "sections": ["header", "subject", "body", "signature", "dragons_seal", "footer"],
    "css": """
        .windi-formal { font-family: 'Segoe UI', Arial, sans-serif; }
        .windi-formal .header { background: linear-gradient(135deg, #1a5f2a, #2d8a3e); color: white; padding: 15px 25px; }
        .windi-formal .logo { font-size: 20px; font-weight: bold; letter-spacing: 2px; }
        .windi-formal .dragons-seal { color: #d4af37; font-weight: bold; font-style: italic; }
        .windi-formal .footer { border-top: 2px solid #d4af37; padding-top: 10px; }
    """
}


ALL_TEMPLATES = {
    "eu_official_v1": TEMPLATE_EU_OFFICIAL,
    "german_gov_v1": TEMPLATE_GERMAN_GOV,
    "windi_formal_v1": TEMPLATE_WINDI_FORMAL
}


def get_template(template_id: str) -> dict:
    """Retorna template por ID."""
    return ALL_TEMPLATES.get(template_id)


def list_templates(lang: str = "en") -> list:
    """Lista todos os templates disponíveis."""
    result = []
    for tid, t in ALL_TEMPLATES.items():
        result.append({
            "id": tid,
            "name": t["name"].get(lang, t["name"].get("en")),
            "description": t["description"].get(lang, t["description"].get("en")),
            "category": t["category"],
            "formality": t["formality"],
            "languages": t["languages"],
            "colors": t["colors"]
        })
    return result

def generate_template_html(template_id: str, lang: str = "de") -> str:
    """Gera HTML estruturado do template."""
    t = get_template(template_id)
    if not t:
        return ""
    
    notice = CORE_DNA.human_authorship_notice.get(lang, CORE_DNA.human_authorship_notice["en"])
    seal = CORE_DNA.governance_seal
    
    html = f'''<div class="{t['category']}" data-template="{template_id}">
    <div class="header">
        <div class="logo">{t['name'].get(lang, t['name']['en'])}</div>
    </div>
    <div class="body" contenteditable="true" data-placeholder="Inhalt hier...">
    </div>
    <div class="human-authorship-notice">
        <p>{notice}</p>
        <p class="governance-seal">{seal}</p>
    </div>
    <div class="footer">
        <span>{CORE_DNA.publisher}</span> | 
        <span>{CORE_DNA.compliance_declaration}</span> |
        <span>A4 Desk BABEL v4.4</span>
    </div>
</div>
<style>{t['css']}</style>'''
    return html


def get_template_css(template_id: str) -> str:
    """Retorna CSS do template."""
    t = get_template(template_id)
    return t["css"] if t else ""


if __name__ == "__main__":
    print("WINDI Template Definitions v4.4")
    print("=" * 40)
    print(f"\nTemplates disponiveis: {len(ALL_TEMPLATES)}")
    for t in list_templates("de"):
        print(f"\n  {t['id']}")
        print(f"    {t['name']} ({t['category']})")
        print(f"    Idiomas: {', '.join(t['languages'])}")
    print("\nKI verarbeitet. Mensch entscheidet. WINDI garantiert.")
