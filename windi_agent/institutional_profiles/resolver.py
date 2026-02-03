"""
WINDI Institutional Style Profile Resolver
Phase 4 - ISP Resolution Engine

Resolves user prompts to institutional style profiles.
Supports both official (fixed) and dynamic (inferred) profiles.

Author: WINDI Publishing House
Version: 1.0
Date: 2026-01-30
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, Optional

# Base path for institutional profiles
ISP_BASE_PATH = "/opt/windi/windi_agent/institutional_profiles"


def load_official_profile(profile_id: str) -> Optional[Dict]:
    """Load an official profile from disk."""
    profile_path = os.path.join(ISP_BASE_PATH, f"{profile_id}.json")
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def list_official_profiles() -> list:
    """List all available official profiles."""
    profiles = []
    if os.path.exists(ISP_BASE_PATH):
        for f in os.listdir(ISP_BASE_PATH):
            if f.endswith('.json') and not f.startswith('_'):
                profiles.append(f.replace('.json', ''))
    return profiles


def resolve_institutional_style(user_prompt: str) -> Dict:
    """
    Resolve user prompt to an institutional style profile.
    
    Returns either:
    - An official profile (if keyword match found)
    - A dynamic profile (inferred from context)
    
    Args:
        user_prompt: The user's input text
        
    Returns:
        Dictionary with profile configuration
    """
    prompt = user_prompt.lower()

    # -----------------------------------------
    # 1. Check for official profile keywords
    # -----------------------------------------
    OFFICIAL_PROFILE_TRIGGERS = {
        # TUM / German Technical Universities
        "tum": "tum_munich_academic_v1",
        "technische universität münchen": "tum_munich_academic_v1",
        "technical university munich": "tum_munich_academic_v1",
        "tum münchen": "tum_munich_academic_v1",
        "tum munich": "tum_munich_academic_v1",
        
        # EU Policy (future)
        "eu commission": "eu_policy_style_v1",
        "european commission": "eu_policy_style_v1",
        "eu policy": "eu_policy_style_v1",
        
        # German Government (future)
        "bundesregierung": "german_government_admin_v1",
        "bundesministerium": "german_government_admin_v1",
        "german government": "german_government_admin_v1",
    }

    for keyword, profile_id in OFFICIAL_PROFILE_TRIGGERS.items():
        if keyword in prompt:
            # Try to load full profile from disk
            full_profile = load_official_profile(profile_id)
            if full_profile:
                return full_profile
            
            # Fallback: return minimal official reference
            return {
                "profile_id": profile_id,
                "profile_type": "official",
                "source": {
                    "derived_from": None,
                    "confidence": "high"
                },
                "_note": "Full profile not found on disk"
            }

    # -----------------------------------------
    # 2. Detect institutional domain
    # -----------------------------------------
    domain = "mixed"
    base_profile = "general_formal_base"
    
    academic_keywords = ["university", "universität", "academic", "research", 
                         "wissenschaft", "hochschule", "fakultät", "professor",
                         "dissertation", "thesis", "studien"]
    
    government_keywords = ["government", "ministerium", "policy", "behörde",
                          "public administration", "öffentlich", "amt", "verwaltung"]
    
    corporate_keywords = ["company", "corporate", "business", "unternehmen",
                         "firma", "gmbh", "ag", "enterprise"]
    
    ngo_keywords = ["ngo", "nonprofit", "stiftung", "foundation", "verein",
                   "gemeinnützig", "charity"]

    if any(word in prompt for word in academic_keywords):
        domain = "academic"
        base_profile = "academic_institution_base"
    elif any(word in prompt for word in government_keywords):
        domain = "governmental"
        base_profile = "government_admin_base"
    elif any(word in prompt for word in corporate_keywords):
        domain = "corporate"
        base_profile = "corporate_formal_base"
    elif any(word in prompt for word in ngo_keywords):
        domain = "ngo"
        base_profile = "ngo_formal_base"

    # -----------------------------------------
    # 3. Detect language preferences
    # -----------------------------------------
    languages = []
    
    if re.search(r'\b(de|german|deutsch|auf deutsch)\b', prompt):
        languages.append("de")
    if re.search(r'\b(en|english|englisch|auf englisch|in english)\b', prompt):
        languages.append("en")
    if re.search(r'\b(fr|french|français|französisch)\b', prompt):
        languages.append("fr")
    if re.search(r'\b(pt|portuguese|portugiesisch|português)\b', prompt):
        languages.append("pt")

    if not languages:
        languages = ["en"]  # Default fallback

    # -----------------------------------------
    # 4. Detect document archetype
    # -----------------------------------------
    archetype = "report"  # Default
    
    if any(word in prompt for word in ["memo", "memorandum", "vermerk"]):
        archetype = "memo"
    elif any(word in prompt for word in ["report", "bericht", "studie"]):
        archetype = "report"
    elif any(word in prompt for word in ["policy", "position paper", "positionspapier"]):
        archetype = "policy_brief"
    elif any(word in prompt for word in ["letter", "brief", "schreiben", "anschreiben"]):
        archetype = "letter"
    elif any(word in prompt for word in ["note", "notiz", "protokoll", "minutes"]):
        archetype = "academic_note"
    elif any(word in prompt for word in ["proposal", "antrag", "vorschlag"]):
        archetype = "proposal"

    # -----------------------------------------
    # 5. Build dynamic profile
    # -----------------------------------------
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    
    dynamic_profile = {
        "profile_id": f"dynamic_{domain}_{languages[0]}_{timestamp}",
        "profile_type": "dynamic",
        "institutional_domain": domain,
        "source": {
            "derived_from": base_profile,
            "confidence": "inferred"
        },
        "language_mode": {
            "primary": languages[0],
            "secondary": languages[1:] if len(languages) > 1 else [],
            "bilingual_balance": "symmetric" if len(languages) > 1 else "primary_dominant"
        },
        "tone_and_register": {
            "formality_level": "very_high" if domain == "academic" else "high",
            "voice": "academic" if domain == "academic" else "administrative",
            "directness": "balanced"
        },
        "structural_bias": {
            "document_archetype": archetype,
            "sectioning_style": "numbered" if domain in ["governmental", "corporate"] else "titled",
            "preferred_sections": _get_sections_for_archetype(archetype)
        },
        "terminology_preferences": {},
        "formatting_guidance": {
            "paragraph_style": "formal_block",
            "list_style": "numbered",
            "emphasis_usage": "minimal",
            "citation_expectation": "optional"
        },
        "interaction_rules": {
            "ask_clarification_before_structuring": True,
            "avoid_informal_language": True,
            "avoid_marketing_tone": True
        },
        "governance_constraints": {
            "cannot_override_human_authorship_notice": True,
            "cannot_modify_governance_ledger": True,
            "cannot_claim_authority": True,
            "must_preserve_audit_trail": True
        }
    }

    return dynamic_profile


def _get_sections_for_archetype(archetype: str) -> list:
    """Return recommended sections for document archetype."""
    sections_map = {
        "report": ["introduction", "background", "analysis", "findings", "conclusion"],
        "academic_note": ["introduction", "context", "analysis", "conclusion"],
        "policy_brief": ["executive_summary", "context", "analysis", "recommendations"],
        "memo": ["subject", "background", "discussion", "action_required"],
        "letter": ["greeting", "body", "closing"],
        "proposal": ["executive_summary", "problem_statement", "proposed_solution", "timeline", "budget"]
    }
    return sections_map.get(archetype, ["introduction", "body", "conclusion"])


def get_profile_summary(profile: Dict) -> str:
    """Generate human-readable summary of profile for agent context."""
    ptype = profile.get("profile_type", "unknown")
    pid = profile.get("profile_id", "unknown")
    domain = profile.get("institutional_domain", "mixed")
    lang = profile.get("language_mode", {})
    primary_lang = lang.get("primary", "en")
    secondary = lang.get("secondary", [])
    
    lang_str = primary_lang
    if secondary:
        lang_str += f" + {', '.join(secondary)}"
    
    tone = profile.get("tone_and_register", {})
    formality = tone.get("formality_level", "high")
    voice = tone.get("voice", "neutral")
    
    archetype = profile.get("structural_bias", {}).get("document_archetype", "report")
    
    summary = f"""
[ISP Active: {pid}]
Type: {ptype} | Domain: {domain}
Language: {lang_str}
Tone: {formality} {voice}
Document: {archetype}
""".strip()
    
    return summary


# -----------------------------------------
# CLI test
# -----------------------------------------
if __name__ == "__main__":
    test_prompts = [
        "Bitte im Stil der TUM München, akademisch, DE/EN",
        "Academic report in German and English",
        "Government policy brief in English",
        "Formal business memo auf Deutsch",
        "University research proposal",
        "Simple note"
    ]
    
    print("=" * 60)
    print("WINDI ISP Resolver - Test")
    print("=" * 60)
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: '{prompt}'")
        profile = resolve_institutional_style(prompt)
        print(f"   → Profile: {profile['profile_id']}")
        print(f"   → Type: {profile['profile_type']}")
        print(f"   → Domain: {profile.get('institutional_domain', 'N/A')}")
        print(f"   → Confidence: {profile['source']['confidence']}")
