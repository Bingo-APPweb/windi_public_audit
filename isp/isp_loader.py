"""
WINDI ISP Loader v1.0
Institutional Style Profile System
"""
import os
import json
from pathlib import Path

ISP_BASE_PATH = Path("/opt/windi/isp")

def list_profiles():
    """Lista todos os ISPs disponíveis"""
    profiles = []
    for folder in ISP_BASE_PATH.iterdir():
        if folder.is_dir() and not folder.name.startswith("_"):
            profile_file = folder / "profile.json"
            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    profiles.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "short_name": data.get("short_name")
                    })
    return profiles

def load_profile(profile_id):
    """Carrega um ISP completo"""
    profile_path = ISP_BASE_PATH / profile_id / "profile.json"
    if not profile_path.exists():
        return None
    with open(profile_path, 'r') as f:
        return json.load(f)

def load_css(profile_id):
    """Carrega o CSS de um ISP"""
    css_path = ISP_BASE_PATH / profile_id / "styles.css"
    if not css_path.exists():
        return ""
    with open(css_path, 'r') as f:
        return f.read()

def get_logo_path(profile_id):
    """Retorna caminho do logo"""
    profile = load_profile(profile_id)
    if profile and profile.get("logo"):
        return ISP_BASE_PATH / profile_id / profile["logo"]["file"]
    return None

def generate_html_header(profile_id, doc_title=""):
    """Gera header HTML com estilo institucional"""
    profile = load_profile(profile_id)
    if not profile:
        return ""
    
    logo_path = get_logo_path(profile_id)
    logo_b64 = ""
    if logo_path and logo_path.exists():
        import base64
        with open(logo_path, 'rb') as f:
            logo_b64 = base64.b64encode(f.read()).decode()
    
    colors = profile.get("colors", {})
    primary = colors.get("primary", "#000000")
    
    return f'''
    <div style="text-align:right;padding-bottom:10px;border-bottom:2px solid {primary};margin-bottom:15px;">
        <img src="data:image/svg+xml;base64,{logo_b64}" style="width:60px;"/>
    </div>
    '''

def generate_styled_html(profile_id, title, content, date_str=""):
    """Gera HTML completo com estilo ISP"""
    profile = load_profile(profile_id)
    css = load_css(profile_id)
    header = generate_html_header(profile_id, title)
    
    colors = profile.get("colors", {}) if profile else {}
    contact = profile.get("contact", {}) if profile else {}
    
    return f'''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{header}
<div class="db-content">{content}</div>
<div class="db-footer">
    <div>{date_str}</div>
    <div>{contact.get("company", "")} | {contact.get("website", "")}</div>
</div>
</body></html>'''
# ============================================================
# GOVERNANCE LEVELS - v1.1.0
# Document Security Classification System
# ============================================================

GOVERNANCE_LEVELS_FILE = ISP_BASE_PATH / "governance_levels.json"

def load_governance_levels():
    """Carrega configuração global de níveis de governança"""
    if not GOVERNANCE_LEVELS_FILE.exists():
        return None
    with open(GOVERNANCE_LEVELS_FILE, 'r') as f:
        return json.load(f)

def get_governance_config(profile_id, doc_type=None):
    """Determina configuração de governança para um documento."""
    global_config = load_governance_levels()
    org_profile = load_profile(profile_id) if profile_id else None
    
    level = "MEDIUM"
    
    if global_config and doc_type:
        mapping = global_config.get("document_type_mapping", {})
        if doc_type in mapping:
            level = mapping[doc_type]
    
    if org_profile and "governance" in org_profile:
        org_gov = org_profile["governance"]
        if org_gov.get("default_level"):
            level = org_gov["default_level"]
        if "watermark_visible" in org_gov:
            return {
                "level": level,
                "watermark_visible": org_gov.get("watermark_visible", False),
                "ledger_style": org_gov.get("ledger_style", "compact"),
                "footer_style": org_gov.get("footer_style", "discrete")
            }
    
    if global_config:
        levels = global_config.get("levels", {})
        lc = levels.get(level, levels.get("MEDIUM", {}))
        return {
            "level": level,
            "watermark_visible": lc.get("watermark_visible", False),
            "ledger_style": lc.get("ledger_style", "compact"),
            "footer_style": lc.get("footer_style", "discrete")
        }
    
    return {"level": "MEDIUM", "watermark_visible": False, "ledger_style": "compact", "footer_style": "discrete"}

def should_apply_watermark(profile_id, doc_type=None):
    """Verifica se deve aplicar watermark visível"""
    return get_governance_config(profile_id, doc_type).get("watermark_visible", False)

print("✓ ISP Governance Levels loaded")
