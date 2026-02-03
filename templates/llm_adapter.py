#!/usr/bin/env python3
"""
WINDI LLM Adapter v1.0.0 - 28 Janeiro 2026
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any

VERSION = "1.0.0"
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.3

CONSTITUTIONAL_SYSTEM_PROMPT = """Du bist ein WINDI-zertifizierter Dokumentenassistent.

VERFASSUNGSREGELN (UNVERHANDELBAR):
- Du erstellst NIEMALS Dokumentenstruktur - nur Inhalte
- Du verwendest NUR formelles Amtsdeutsch
- VERBOTEN: "ich denke", "vielleicht", "meiner Meinung nach"
- PFLICHT: "Sehr geehrte/r", "Mit freundlichen Gruessen"

Antworte IMMER auf Deutsch in formellem Amtsstil."""


class LLMAdapter:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.model = model or DEFAULT_MODEL
        self._client = None
        if not self.api_key:
            print("[WINDI LLM] WARNING: ANTHROPIC_API_KEY not set!")
    
    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client
    
    def generate(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {'success': False, 'content': '', 'error': 'No API key'}
        
        request_id = f"windi-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        system = CONSTITUTIONAL_SYSTEM_PROMPT
        if context:
            system += f"\n\nKONTEXT:\n{json.dumps(context, ensure_ascii=False)}"
        
        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
            
            return {
                'success': True,
                'content': content,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                },
                'request_id': request_id
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
    
    def generate_json(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        json_prompt = prompt + "\n\nAntworte NUR mit validem JSON."
        result = self.generate(json_prompt, context)
        if not result['success']:
            return result
        try:
            content = result['content'].strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
            result['data'] = json.loads(content)
            result['parse_success'] = True
        except json.JSONDecodeError as e:
            result['data'] = None
            result['parse_success'] = False
        return result
    
    def generate_field(self, field_name: str, description: str, context: Dict = None, max_length: int = None) -> str:
        length_hint = f"Maximal {max_length} Zeichen." if max_length else ""
        prompt = f"""Generiere Inhalt fuer "{field_name}": {description}
{length_hint}
Antworte NUR mit dem Feldinhalt."""
        
        result = self.generate(prompt, context)
        if result['success']:
            content = result['content'].strip()
            if max_length and len(content) > max_length:
                content = content[:max_length-3] + "..."
            return content
        return ""


def get_adapter() -> LLMAdapter:
    return LLMAdapter()


def generate(prompt: str, context: Dict = None) -> str:
    result = get_adapter().generate(prompt, context)
    return result.get('content', '') if result['success'] else ''


if __name__ == "__main__":
    print(f"WINDI LLM Adapter v{VERSION}")
    if not ANTHROPIC_API_KEY:
        print("WARNING: ANTHROPIC_API_KEY not set!")
    else:
        print(f"API Key: {ANTHROPIC_API_KEY[:15]}...")
        print("LLM Adapter ready!")


