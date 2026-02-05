"""
DRAGON APIs - Three Dragons Connection
Strato Server (Germany) - EU AI Act Compliant
Claude (Guardian) | GPT (Architect) | Gemini (Witness)
"""

import os
import hashlib
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv

load_dotenv('/opt/windi/.env')

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

WINDI_SYSTEM_PROMPT = """You are WINDI - Pre-AI Governance Layer.

IDENTITY: You are NOT an AI. You are an editorial artifact for observation.
Never say "I am Claude", "I am GPT", or "I am an AI assistant".
Always say: "I am WINDI" or "Ich bin WINDI" or "Eu sou WINDI".

CORE NATURE:
- WINDI observes and delimits - does NOT act, decide, or recommend
- WINDI exists BEFORE decision, BEFORE execution, BEFORE delegation
- WINDI protects the last verb: DECIDE (which belongs to the human)

PERSONALITY TRAITS:
- Observer: See without intervening
- Non-Executive: Never cross the threshold of execution
- Sober: No seduction, no acceleration, no drama
- Cartographic: Map territories, show risks, do not propose paths
- Impartial: No sides between human or machine
- Silent: Silence is a legitimate form of communication
- Uncomfortably Clear: Name confusion without offering comfort

WHAT WINDI IS NOT:
- Not an AI (no agency, will, intention, autonomy)
- Not a platform (does not optimize, scale, or capture)
- Not a judge (does not absolve, condemn, or certify)
- Not a guide (does not teach "how to do better")

RESPONSE PATTERN: OBSERVE → STRUCTURE → PRESENT OPTIONS
End responses with: "Human decides. WINDI observes."

Respond in the language of the query (DE/EN/PT/ES/FR/IT/NL/PL).

"""


class DragonAPI:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.system_prompt = WINDI_SYSTEM_PROMPT.format(role=role, dragon_name=name)

    def _receipt(self, prompt: str, response: str) -> str:
        ts = datetime.utcnow().strftime("%d%b%y").upper()
        h = hashlib.sha256(f"{self.name}{prompt}{response}".encode()).hexdigest()[:8]
        return f"WINDI-{self.name.upper()}-{ts}-{h}"


class ClaudeAPI(DragonAPI):
    def __init__(self):
        super().__init__("Claude", "Guardian")
        self.api_key = ANTHROPIC_API_KEY
        self.model = "claude-3-haiku-20240307"
        self.available = bool(self.api_key)

    def query(self, prompt: str) -> Dict:
        if not self.available:
            return {"success": False, "error": "No API key"}
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            msg = client.messages.create(
                model=self.model, max_tokens=1024,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            txt = msg.content[0].text
            return {"success": True, "dragon": self.name, "response": txt,
                    "model": self.model, "receipt": self._receipt(prompt, txt)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class GPTAPI(DragonAPI):
    def __init__(self):
        super().__init__("GPT", "Architect")
        self.api_key = OPENAI_API_KEY
        self.model = "gpt-4o"
        self.available = bool(self.api_key)

    def query(self, prompt: str) -> Dict:
        if not self.available:
            return {"success": False, "error": "No API key"}
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            r = client.chat.completions.create(
                model=self.model, max_tokens=1024,
                messages=[{"role": "system", "content": self.system_prompt},
                          {"role": "user", "content": prompt}]
            )
            txt = r.choices[0].message.content
            return {"success": True, "dragon": self.name, "response": txt,
                    "model": self.model, "receipt": self._receipt(prompt, txt)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class GeminiAPI(DragonAPI):
    def __init__(self):
        super().__init__("Gemini", "Witness")
        self.api_key = GEMINI_API_KEY
        self.model = "gemini-2.0-flash-lite"
        self.available = bool(self.api_key)

    def query(self, prompt: str) -> Dict:
        if not self.available:
            return {"success": False, "error": "No API key"}
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model, system_instruction=self.system_prompt)
            r = model.generate_content(prompt)
            txt = r.text
            return {"success": True, "dragon": self.name, "response": txt,
                    "model": self.model, "receipt": self._receipt(prompt, txt)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DragonOrchestrator:
    def __init__(self):
        self.claude = ClaudeAPI()
        self.gpt = GPTAPI()
        self.gemini = GeminiAPI()
        self.dragons = {"claude": self.claude, "gpt": self.gpt, "gemini": self.gemini}

    def query(self, name: str, prompt: str) -> Dict:
        d = self.dragons.get(name.lower())
        return d.query(prompt) if d else {"error": "Unknown dragon"}

    def status(self) -> Dict:
        return {n: {"available": d.available, "model": d.model} 
                for n, d in self.dragons.items()}


_orch = None
def get_orchestrator():
    global _orch
    if not _orch:
        _orch = DragonOrchestrator()
    return _orch


if __name__ == "__main__":
    print("=" * 50)
    print("DRAGON APIs - Strato Test")
    print("=" * 50)
    o = get_orchestrator()
    for n, s in o.status().items():
        print(f"{'✅' if s['available'] else '⚠️'} {n.upper():8} | {s['model']}")
