"""
WINDI ISP Loader v2.0
Institutional Style Profile System with Templates Support

Version: 2.0.0
Date: 03-Feb-2026
Author: WINDI Publishing House

New in v2.0:
- load_tokens() - Design system tokens
- load_template() - HTML templates
- load_component() - Reusable components
- load_form() - Institutional forms
- list_templates() - Available templates
- list_forms() - Available forms
- render_isp_template() - Jinja2 rendering
"""
import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime

# Ensure ISP directory is in sys.path for module imports
ISP_PATH = "/opt/windi/isp"
if ISP_PATH not in sys.path:
    sys.path.insert(0, ISP_PATH)

# Jinja2 for template rendering
try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("⚠ Jinja2 not available - template rendering disabled")

ISP_BASE_PATH = Path("/opt/windi/isp")

def list_profiles():
    """Lista todos os ISPs disponíveis (supports both legacy and canonical schema)"""
    profiles = []
    for folder in sorted(ISP_BASE_PATH.iterdir()):
        if folder.is_dir() and not folder.name.startswith("_") and folder.name != "__pycache__":
            profile_file = folder / "profile.json"
            if profile_file.exists():
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Canonical schema: isp_profile wrapper
                    if "isp_profile" in data:
                        isp = data["isp_profile"]
                        meta = isp.get("metadata", {})
                        org = isp.get("organization", {})
                        profiles.append({
                            "id": meta.get("profile_id", folder.name),
                            "name": org.get("name_full", org.get("name", folder.name)),
                            "short_name": org.get("name_short", folder.name),
                            "governance_level": meta.get("governance_level", "LOW"),
                            "templates_count": len(isp.get("templates", [])),
                            "profile_type": meta.get("profile_type", "unknown")
                        })
                    # Legacy schema: flat root
                    else:
                        profiles.append({
                            "id": data.get("id", folder.name),
                            "name": data.get("name", data.get("name_display", folder.name)),
                            "short_name": data.get("short_name", folder.name),
                            "governance_level": data.get("governance_level", "LOW"),
                            "templates_count": 0,
                            "profile_type": data.get("type", "unknown")
                        })
                except Exception as e:
                    print(f"[ISP] Error loading {folder.name}: {e}")
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
# ISP TEMPLATES v2.0 - New Template System
# ============================================================

def load_tokens(profile_id):
    """
    Carrega design tokens de um ISP.

    Args:
        profile_id: ID do perfil institucional (ex: 'deutsche-bahn')

    Returns:
        dict: Design tokens (colors, typography, spacing, etc.)
    """
    tokens_path = ISP_BASE_PATH / profile_id / "tokens.json"
    if not tokens_path.exists():
        return {}
    try:
        with open(tokens_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ISP] Error loading tokens for {profile_id}: {e}")
        return {}


def load_template(profile_id, template_name):
    """
    Carrega um template HTML de um ISP.

    Args:
        profile_id: ID do perfil institucional
        template_name: Nome do template (sem extensão, ex: 'letter', 'form')

    Returns:
        str: Conteúdo HTML do template ou None se não existir
    """
    template_path = ISP_BASE_PATH / profile_id / "templates" / f"{template_name}.html"
    if not template_path.exists():
        return None
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ISP] Error loading template {template_name} for {profile_id}: {e}")
        return None


def load_component(profile_id, component_name):
    """
    Carrega um componente HTML reutilizável de um ISP.

    Args:
        profile_id: ID do perfil institucional
        component_name: Nome do componente (sem extensão, ex: 'header', 'footer')

    Returns:
        str: Conteúdo HTML do componente ou string vazia
    """
    comp_path = ISP_BASE_PATH / profile_id / "components" / f"{component_name}.html"
    if not comp_path.exists():
        return ""
    try:
        with open(comp_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ISP] Error loading component {component_name} for {profile_id}: {e}")
        return ""


def load_form(profile_id, form_name):
    """
    Carrega um formulário institucional específico.

    Args:
        profile_id: ID do perfil institucional
        form_name: Nome do formulário (sem extensão, ex: 'transportauftrag')

    Returns:
        str: Conteúdo HTML do formulário ou None se não existir
    """
    form_path = ISP_BASE_PATH / profile_id / "forms" / f"{form_name}.html"
    if not form_path.exists():
        return None
    try:
        with open(form_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ISP] Error loading form {form_name} for {profile_id}: {e}")
        return None


def list_templates(profile_id):
    """
    Lista todos os templates disponíveis para um ISP.
    Checks both HTML files in templates/ dir AND JSON templates in profile.json.

    Args:
        profile_id: ID do perfil institucional

    Returns:
        list: Lista de dicts com template info
    """
    results = []
    
    # Source 1: HTML files in templates/ directory
    templates_dir = ISP_BASE_PATH / profile_id / "templates"
    if templates_dir.exists():
        for f in sorted(templates_dir.glob("*.html")):
            results.append({
                "id": f.stem,
                "name": f.stem.replace("_", " ").replace("-", " ").title(),
                "type": "html_file",
                "source": "file"
            })
    
    # Source 2: JSON templates in profile.json (canonical schema)
    profile_path = ISP_BASE_PATH / profile_id / "profile.json"
    if profile_path.exists():
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            isp = data.get("isp_profile", data)
            json_templates = isp.get("templates", [])
            for t in json_templates:
                tid = t.get("id", "")
                results.append({
                    "id": tid,
                    "name": t.get("name_de", t.get("name", tid)),
                    "name_en": t.get("name_en", ""),
                    "category": t.get("category", ""),
                    "risk_level": t.get("risk_level", "R1"),
                    "description": t.get("description", ""),
                    "type": "json_definition",
                    "source": "profile"
                })
        except Exception as e:
            print(f"[ISP] Error reading templates from profile.json: {e}")
    
    return results


def list_forms(profile_id):
    """
    Lista todos os formulários disponíveis para um ISP.
    Checks both HTML files in forms/ dir AND document_categories in profile.json.

    Args:
        profile_id: ID do perfil institucional

    Returns:
        list: Lista de dicts com form info
    """
    results = []
    
    # Source 1: HTML files in forms/ directory
    forms_dir = ISP_BASE_PATH / profile_id / "forms"
    if forms_dir.exists():
        for f in sorted(forms_dir.glob("*.html")):
            results.append({
                "id": f.stem,
                "name": f.stem.replace("_", " ").replace("-", " ").title(),
                "type": "html_file",
                "source": "file"
            })
    
    # Source 2: document_categories from profile.json (canonical schema)
    profile_path = ISP_BASE_PATH / profile_id / "profile.json"
    if profile_path.exists():
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            isp = data.get("isp_profile", data)
            categories = isp.get("document_categories", [])
            for c in categories:
                results.append({
                    "id": c.get("id", ""),
                    "name": c.get("name_de", c.get("name", "")),
                    "name_en": c.get("name_en", ""),
                    "description": c.get("description", ""),
                    "risk_level": c.get("typical_risk_level", "R1"),
                    "type": "category",
                    "source": "profile"
                })
        except Exception as e:
            print(f"[ISP] Error reading categories from profile.json: {e}")
    
    return results


def list_components(profile_id):
    """
    Lista todos os componentes disponíveis para um ISP.

    Args:
        profile_id: ID do perfil institucional

    Returns:
        list: Lista de nomes de componentes disponíveis
    """
    components_dir = ISP_BASE_PATH / profile_id / "components"
    if not components_dir.exists():
        return []
    return [f.stem for f in components_dir.glob("*.html")]


def get_logo_base64(profile_id):
    """
    Retorna o logo em base64 para embedding em HTML.

    Args:
        profile_id: ID do perfil institucional

    Returns:
        str: Logo em base64 ou string vazia
    """
    logo_path = get_logo_path(profile_id)
    if logo_path and logo_path.exists():
        try:
            with open(logo_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"[ISP] Error loading logo for {profile_id}: {e}")
    return ""


def render_isp_template(profile_id, template_html, context=None):
    """
    Renderiza um template ISP com Jinja2.

    Args:
        profile_id: ID do perfil institucional
        template_html: Conteúdo HTML do template
        context: Dicionário com variáveis para o template

    Returns:
        str: HTML renderizado ou template original se Jinja2 não disponível
    """
    if not JINJA2_AVAILABLE:
        print("[ISP] Jinja2 not available, returning raw template")
        return template_html

    if context is None:
        context = {}

    # Load tokens and profile for default context
    tokens = load_tokens(profile_id)
    profile = load_profile(profile_id)

    # Build default context
    default_context = {
        # Metadata
        "profile_id": profile_id,
        "doc_date": datetime.now().strftime("%d.%m.%Y"),
        "doc_datetime": datetime.now().isoformat(),
        "year": datetime.now().year,

        # Organization from profile
        "org_name": profile.get("organization", {}).get("organization_name", "") if profile else "",
        "org_type": profile.get("organization", {}).get("organization_type", "") if profile else "",
        "jurisdiction": profile.get("organization", {}).get("jurisdiction", "") if profile else "",

        # Logo
        "logo_base64": get_logo_base64(profile_id),

        # Colors from tokens
        "color_primary": tokens.get("colors", {}).get("primary", {}).get("red", "#000000"),
        "color_secondary": tokens.get("colors", {}).get("neutral", {}).get("gray_500", "#666666"),
        "color_text": tokens.get("colors", {}).get("neutral", {}).get("black", "#1E1E1E"),
        "color_background": tokens.get("colors", {}).get("background", {}).get("page", "#FFFFFF"),

        # Typography from tokens
        "font_family": tokens.get("typography", {}).get("font_family", {}).get("primary", "Arial, sans-serif"),
        "font_size_base": tokens.get("typography", {}).get("font_size", {}).get("base", "9pt"),

        # WINDI defaults
        "windi_level": "LOW",
        "windi_receipt": "",
        "windi_timestamp": datetime.now().isoformat(),
        "show_windi": True,
    }

    # Merge with provided context (provided context takes precedence)
    final_context = {**default_context, **context}

    try:
        # Custom env: prevent {# in CSS from being parsed as Jinja2 comment
        env = Environment(comment_start_string='{##', comment_end_string='##}')
        template = env.from_string(template_html)
        return template.render(**final_context)
    except Exception as e:
        print(f"[ISP] Template render error: {e}")
        return template_html


def build_full_document(profile_id, content_html, template_type="letter", form_id=None, context=None):
    """
    Constrói documento completo usando template ISP.

    Args:
        profile_id: ID do perfil institucional
        content_html: Conteúdo HTML do documento
        template_type: Tipo de template ('letter', 'form', 'memo', 'report')
        form_id: ID do formulário específico (se aplicável)
        context: Variáveis adicionais para o template

    Returns:
        str: HTML completo renderizado ou None se template não existir
    """
    if context is None:
        context = {}

    # Add content to context
    context["content"] = content_html

    # Try to load form first, then template
    template_html = None

    if form_id:
        template_html = load_form(profile_id, form_id)
        if template_html:
            print(f"[ISP] Using form: {form_id}")

    if not template_html:
        template_html = load_template(profile_id, template_type)
        if template_html:
            print(f"[ISP] Using template: {template_type}")

    if not template_html:
        print(f"[ISP] No template found, using fallback")
        return None

    # Load and inject components
    header_html = load_component(profile_id, "header")
    footer_html = load_component(profile_id, "footer")

    if header_html:
        context["isp_header"] = render_isp_template(profile_id, header_html, context)
    if footer_html:
        context["isp_footer"] = render_isp_template(profile_id, footer_html, context)

    # Render final template
    return render_isp_template(profile_id, template_html, context)


def get_isp_summary(profile_id):
    """
    Retorna resumo completo de um ISP para API/debug.

    Args:
        profile_id: ID do perfil institucional

    Returns:
        dict: Resumo com profile, templates, forms, components disponíveis
    """
    profile = load_profile(profile_id)
    tokens = load_tokens(profile_id)

    return {
        "profile_id": profile_id,
        "exists": profile is not None,
        "organization": profile.get("organization", {}) if profile else {},
        "governance": profile.get("governance", {}) if profile else {},
        "has_tokens": bool(tokens),
        "templates": list_templates(profile_id),
        "forms": list_forms(profile_id),
        "components": list_components(profile_id),
        "has_logo": bool(get_logo_base64(profile_id)),
        "css_available": bool(load_css(profile_id)),
    }


print("✓ ISP Templates v2.0 loaded")

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
    
    # Support canonical schema (isp_profile wrapper)
    if org_profile and "isp_profile" in org_profile:
        org_profile = org_profile["isp_profile"]
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
