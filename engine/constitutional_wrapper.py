#!/usr/bin/env python3
"""
Constitutional Wrapper for WINDI Agent
Implements TÍTULO VII without modifying core agent
"""

import json
from typing import Dict, Tuple, Optional

class ConstitutionalRouter:
    """Article 18-22 Implementation"""
    
    def __init__(self, manifest_path="/opt/windi/skills/manifest.json"):
        self.manifest_path = manifest_path
        self.skills = []
        self.load_manifest()
    
    def load_manifest(self):
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            self.skills = sorted(
                manifest.get('skills', []),
                key=lambda s: s.get('priority', 0),
                reverse=True
            )
            print(f"[WINDI] Constitutional Router: {len(self.skills)} skills")
        except Exception as e:
            print(f"[WINDI] Router error: {e}")
            self.skills = []
    
    def match_trigger(self, message: str, triggers: list) -> bool:
        msg_lower = message.lower().strip()
        return any(trigger.lower() in msg_lower for trigger in triggers)
    
    def route(self, message: str) -> Tuple[Optional[Dict], Dict]:
        routing_log = {
            "skills_considered": [],
            "skill_selected": None,
            "reason": None,
            "priority": None
        }
        
        for skill in self.skills:
            name = skill.get('name')
            priority = skill.get('priority', 0)
            triggers = skill.get('triggers', [])
            
            routing_log['skills_considered'].append(name)
            
            if triggers and self.match_trigger(message, triggers):
                routing_log.update({
                    "skill_selected": name,
                    "reason": "trigger_match",
                    "priority": priority
                })
                print(f"[WINDI] 🎯 {name} (priority {priority})")
                return skill, routing_log
        
        # Fallback
        fallback = next((s for s in self.skills if not s.get('triggers')), None)
        if fallback:
            routing_log.update({
                "skill_selected": fallback.get('name'),
                "reason": "fallback",
                "priority": fallback.get('priority', 0)
            })
            return fallback, routing_log
        
        return None, routing_log
    
    def generate_tutorial(self, message: str) -> str:
        """Article 19: Tutorial responses"""
        msg = message.lower()
        
        if "template" in msg:
            return """**Template-Nutzung: Schritt für Schritt** 🎯

**1. Template auswählen**
   - BABEL Dashboard öffnen
   - Templates → Institutional Profiles
   - ISP wählen (z.B. "bundesregierung-v1")

**2. Neues Dokument erstellen** 📄
   - "Neues Dokument" klicken
   - Template automatisch geladen
   - BABEL-ID generiert

**3. Felder ausfüllen** ✍️
   - Pflichtfelder (rot) zuerst
   - Optionale Felder nach Bedarf
   - Governance-Level automatisch

**4. Validierung & Speichern** ✅
   - SGE-Konformität wird geprüft
   - Bei R2+ erscheint Warnung
   - WINDI-Receipt generiert

Möchten Sie ein konkretes Beispiel sehen?

Human decides. I guide."""
        
        elif "sge" in msg:
            return """**SGE-Nutzung: Semantic Governance Engine** 🔍

**Was ist SGE?**
Analysiert Dokumente auf 6 semantischen Ebenen.

**Wie nutzen?** 🚀
1. Dokument hochladen → SGE läuft automatisch
2. Score verstehen: >0.85=sicher, <0.70=kritisch
3. Handeln basierend auf Risk Level (R0-R5)

Was möchten Sie mit SGE analysieren?

Human decides. I analyze."""
        
        elif "isp" in msg or "profil" in msg:
            return """**ISP-Nutzung: Institutional Style Profiles** 🏛️

**Was sind ISPs?**
Governance-Profile für Ihre Organisation.

**Wie nutzen?** 📋
1. Settings → Institution → ISP wählen
2. Templates automatisch ISP-konform
3. Governance-Level pre-configured

Brauchen Sie ein neues ISP?

Human decides. I configure."""
        
        else:
            return """**WINDI-System: Quick Start Guide** 🚀

**Haupt-Features:**
1. Document Governance (SGE-Analyse)
2. Decision Protection (Mandatary-Workflow)
3. Zero-Knowledge Architecture

**Erste Schritte:**
Dokument hochladen → Template wählen → Entscheidung treffen

**Welchen Bereich möchten Sie vertiefen?**
- Templates, SGE-Analyse, ISP-Profile, Governance-Workflow

Human decides. I guide."""


# Global instance
ROUTER = ConstitutionalRouter()


def constitutional_process(message: str, lang: str = "de", institutional_profile: Dict = None) -> Dict:
    """
    Constitutional preprocessing before WINDI Agent
    Returns: response dict if handled, None if should pass to agent
    """
    
    skill, routing_log = ROUTER.route(message)
    
    if skill and skill.get('name') == 'tutorial-mode':
        # Article 19: Tutorial has absolute precedence
        return {
            'response': ROUTER.generate_tutorial(message),
            'document_type': 'tutorial',
            'model': 'windi-constitutional-router',
            'routing_decision': routing_log,
            'constitutional_routing': True,
            'receipt': f'WINDI-TUTORIAL-{message[:8]}'
        }
    
    # Pass to agent with routing context
    return None  # Signal to continue to agent
