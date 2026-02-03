#!/usr/bin/env python3
"""
WINDI LLM Document Generator v1.0.0
28 Janeiro 2026 - Three Dragons Protocol
"""

import json
from typing import Dict, List, Any

try:
    from llm_adapter import LLMAdapter, get_adapter
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("[WINDI] WARNING: LLM Adapter not available")


class LLMDocumentGenerator:
    def __init__(self):
        self.adapter = get_adapter() if LLM_AVAILABLE else None
    
    def generate_sachverhalt(self, context: Dict[str, Any]) -> List[str]:
        if not self.adapter:
            return []
        prompt = f"""Erstelle 3-4 Sachverhaltspunkte fuer einen Baugenehmigungsbescheid.
Antragsteller: {context.get('recipient_name', 'Antragsteller')}
Bauvorhaben: {context.get('subject', 'Bauvorhaben')}
Adresse: {context.get('recipient_street', '')}, {context.get('recipient_city', '')}
Antworte als JSON-Array: ["Punkt 1", "Punkt 2", "Punkt 3"]"""
        result = self.adapter.generate_json(prompt, context)
        if result.get('parse_success') and isinstance(result.get('data'), list):
            return result['data']
        return []
    
    def generate_gruende(self, context: Dict[str, Any]) -> List[str]:
        if not self.adapter:
            return []
        decision = context.get('decision_type', 'GENEHMIGT')
        prompt = f"""Erstelle 4-5 rechtliche Begruendungen fuer einen Baugenehmigungsbescheid.
Entscheidung: {decision}
Bauvorhaben: {context.get('subject', 'Bauvorhaben')}
Verweise auf BayBO und BauGB.
Antworte als JSON-Array: ["Grund 1", "Grund 2"]"""
        result = self.adapter.generate_json(prompt, context)
        if result.get('parse_success') and isinstance(result.get('data'), list):
            return result['data']
        return []
    
    def generate_auflagen(self, context: Dict[str, Any]) -> List[str]:
        if not self.adapter:
            return []
        prompt = f"""Erstelle 3-4 Auflagen fuer eine Baugenehmigung.
Bauvorhaben: {context.get('subject', 'Bauvorhaben')}
Antworte als JSON-Array: ["Auflage 1", "Auflage 2"]"""
        result = self.adapter.generate_json(prompt, context)
        if result.get('parse_success') and isinstance(result.get('data'), list):
            return result['data']
        return []
    
    def generate_complete_bescheid(self, base_data: Dict[str, Any], use_llm: bool = True) -> Dict[str, Any]:
        result = base_data.copy()
        if not use_llm or not self.adapter:
            return result
        print("[WINDI LLM] Generating dynamic content...")
        if not result.get('facts') or len(result.get('facts', [])) == 0:
            facts = self.generate_sachverhalt(result)
            if facts:
                result['facts'] = facts
                print(f"[WINDI LLM] Generated {len(facts)} facts")
        if not result.get('reasoning') or len(result.get('reasoning', [])) == 0:
            reasoning = self.generate_gruende(result)
            if reasoning:
                result['reasoning'] = reasoning
                print(f"[WINDI LLM] Generated {len(reasoning)} reasoning points")
        if result.get('decision_type') == 'GENEHMIGT':
            if not result.get('conditions') or len(result.get('conditions', [])) == 0:
                conditions = self.generate_auflagen(result)
                if conditions:
                    result['conditions'] = conditions
                    print(f"[WINDI LLM] Generated {len(conditions)} conditions")
        return result


_generator = None

def get_generator() -> LLMDocumentGenerator:
    global _generator
    if _generator is None:
        _generator = LLMDocumentGenerator()
    return _generator


def generate_bescheid_content(base_data: Dict[str, Any]) -> Dict[str, Any]:
    return get_generator().generate_complete_bescheid(base_data)


if __name__ == "__main__":
    print("WINDI LLM Document Generator v1.0.0")
    if not LLM_AVAILABLE:
        print("ERROR: LLM Adapter not available!")
    else:
        print("Generator ready!")
