"""
WINDI Skills Loader v1.0
========================
Carrega skills de /opt/windi/skills/ e injeta no system prompt do WINDI Agent.

Estrutura de cada skill:
/opt/windi/skills/
├── sge-analyzer/
│   └── SKILL.md
├── virtue-receipt/
│   └── SKILL.md
├── three-dragons/
│   └── SKILL.md
└── ...

Cada SKILL.md tem YAML frontmatter com:
- name: nome da skill
- description: quando usar (usado para matching)
- triggers: palavras-chave que ativam a skill

Author: WINDI Publishing House
Date: 2026-02-04
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

SKILLS_DIR = "/opt/windi/skills"
SKILLS_ENABLED = True

# ═══════════════════════════════════════════════════════════════════════════════
# Skill Parser
# ═══════════════════════════════════════════════════════════════════════════════

def parse_skill_file(skill_path: str) -> Optional[Dict]:
    """
    Parse a SKILL.md file and extract metadata + content.
    
    Returns:
        {
            'name': str,
            'description': str,
            'triggers': list[str],
            'content': str (markdown body)
        }
    """
    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if not frontmatter_match:
            print(f"[Skills] Warning: No frontmatter in {skill_path}")
            return None
        
        yaml_content = frontmatter_match.group(1)
        markdown_body = frontmatter_match.group(2).strip()
        
        # Parse YAML
        metadata = yaml.safe_load(yaml_content)
        
        if not metadata.get('name') or not metadata.get('description'):
            print(f"[Skills] Warning: Missing name/description in {skill_path}")
            return None
        
        return {
            'name': metadata['name'],
            'description': metadata['description'],
            'triggers': metadata.get('triggers', []),
            'content': markdown_body,
            'path': skill_path
        }
        
    except Exception as e:
        print(f"[Skills] Error parsing {skill_path}: {e}")
        return None


def load_all_skills() -> List[Dict]:
    """
    Load all skills from SKILLS_DIR.
    
    Returns:
        List of parsed skill dictionaries
    """
    skills = []
    skills_path = Path(SKILLS_DIR)
    
    if not skills_path.exists():
        print(f"[Skills] Skills directory not found: {SKILLS_DIR}")
        return skills
    
    for skill_dir in skills_path.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skill = parse_skill_file(str(skill_file))
                if skill:
                    skills.append(skill)
                    print(f"[Skills] Loaded: {skill['name']}")
    
    print(f"[Skills] Total skills loaded: {len(skills)}")
    return skills


# ═══════════════════════════════════════════════════════════════════════════════
# Skill Matcher
# ═══════════════════════════════════════════════════════════════════════════════

def match_skills_to_message(message: str, skills: List[Dict]) -> List[Dict]:
    """
    Match relevant skills to a user message based on triggers and description.
    
    Args:
        message: User message
        skills: List of loaded skills
        
    Returns:
        List of matched skills (sorted by relevance)
    """
    message_lower = message.lower()
    matched = []
    
    for skill in skills:
        score = 0
        
        # Check triggers (high weight)
        for trigger in skill.get('triggers', []):
            if trigger.lower() in message_lower:
                score += 10
        
        # Check description keywords (medium weight)
        desc_words = skill['description'].lower().split()
        for word in desc_words:
            if len(word) > 4 and word in message_lower:
                score += 2
        
        # Check skill name (low weight)
        if skill['name'].lower().replace('-', ' ') in message_lower:
            score += 5
        
        if score > 0:
            matched.append({**skill, 'match_score': score})
    
    # Sort by match score
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matched


# ═══════════════════════════════════════════════════════════════════════════════
# System Prompt Injection
# ═══════════════════════════════════════════════════════════════════════════════

def inject_skills_into_prompt(base_prompt: str, matched_skills: List[Dict], max_skills: int = 3) -> str:
    """
    Inject matched skills into the system prompt.
    """
    if not matched_skills:
        return base_prompt
    
    skills_to_inject = matched_skills[:max_skills]
    
    # Build skills section with FORMAT OVERRIDE
    skills_section = "\n\n## ACTIVE SKILLS (FORMAT OVERRIDE)\n\n"
    skills_section += "IMPORTANT: The following skills are activated. When using these skills, "
    skills_section += "you MAY use structured formatting (headers, tables, lists) as specified "
    skills_section += "in the skill instructions below. The skill format takes precedence over "
    skills_section += "the default formatting rules for this response.\n\n"
    
    for skill in skills_to_inject:
        skills_section += f"### {skill['name']}\n"
        skills_section += f"{skill['content']}\n\n"
    
    skills_section += "---\n"
    
    if "## FINAL REMINDER" in base_prompt:
        return base_prompt.replace("## FINAL REMINDER", f"{skills_section}\n## FINAL REMINDER")
    else:
        return base_prompt + skills_section
    
    # Take top N skills
    skills_to_inject = matched_skills[:max_skills]
    
    # Build skills section
    skills_section = "\n\n## ACTIVE SKILLS\n\n"
    skills_section += "The following specialized skills are activated for this request:\n\n"
    
    for skill in skills_to_inject:
        skills_section += f"### {skill['name']}\n"
        skills_section += f"{skill['content']}\n\n"
    
    skills_section += "---\n"
    
    # Inject before the final reminder section
    if "## FINAL REMINDER" in base_prompt:
        return base_prompt.replace("## FINAL REMINDER", f"{skills_section}\n## FINAL REMINDER")
    else:
        return base_prompt + skills_section


# ═══════════════════════════════════════════════════════════════════════════════
# Main Interface
# ═══════════════════════════════════════════════════════════════════════════════

class WindiSkillsEngine:
    """
    WINDI Skills Engine - Manages skill loading and matching for the Agent.
    """
    
    def __init__(self, skills_dir: str = SKILLS_DIR):
        self.skills_dir = skills_dir
        self.skills = []
        self.enabled = SKILLS_ENABLED
        self.reload_skills()
    
    def reload_skills(self):
        """Reload all skills from disk."""
        self.skills = load_all_skills()
        return len(self.skills)
    
    def process_message(self, base_prompt: str, user_message: str) -> Tuple[str, List[str]]:
        """
        Process a user message and return enhanced prompt with matched skills.
        
        Args:
            base_prompt: Original system prompt
            user_message: User's message
            
        Returns:
            Tuple of (enhanced_prompt, list of activated skill names)
        """
        if not self.enabled or not self.skills:
            return base_prompt, []
        
        # Match skills
        matched = match_skills_to_message(user_message, self.skills)
        
        if not matched:
            return base_prompt, []
        
        # Inject into prompt
        enhanced_prompt = inject_skills_into_prompt(base_prompt, matched)
        
        # Return skill names for logging
        activated_names = [s['name'] for s in matched[:3]]
        
        return enhanced_prompt, activated_names
    
    def get_status(self) -> Dict:
        """Return engine status."""
        return {
            'enabled': self.enabled,
            'skills_count': len(self.skills),
            'skills_dir': self.skills_dir,
            'skills': [{'name': s['name'], 'description': s['description']} for s in self.skills]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_skills_engine = None

def get_skills_engine() -> WindiSkillsEngine:
    """Get or create the skills engine singleton."""
    global _skills_engine
    if _skills_engine is None:
        _skills_engine = WindiSkillsEngine()
    return _skills_engine


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI Skills Engine v1.0")
    print("=" * 60)
    
    engine = get_skills_engine()
    status = engine.get_status()
    
    print(f"\nStatus:")
    print(f"  Enabled: {status['enabled']}")
    print(f"  Skills Directory: {status['skills_dir']}")
    print(f"  Skills Loaded: {status['skills_count']}")
    
    if status['skills']:
        print(f"\nLoaded Skills:")
        for skill in status['skills']:
            print(f"  - {skill['name']}: {skill['description'][:60]}...")
    
    # Test matching
    test_messages = [
        "Analise o risco desse documento",
        "Gere um virtue receipt dessa decisão",
        "Preciso de um dashboard para o controller",
        "Qual a conformidade com EU AI Act?",
    ]
    
    print(f"\nTest Matching:")
    for msg in test_messages:
        matched = match_skills_to_message(msg, engine.skills)
        if matched:
            print(f"  '{msg[:40]}...' -> {[s['name'] for s in matched[:2]]}")
        else:
            print(f"  '{msg[:40]}...' -> No match")
