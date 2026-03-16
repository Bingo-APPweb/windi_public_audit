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

# ─── GATE CONTROLLER ─────────────────────────────────────
# WINDI_TIER controls feature access across the ecosystem.
# FREE  → No dragons. 100% local motor only. Zero external LLM calls.
# MED   → Claude only (Guardian). ISP read-only. Basic export.
# HIGH  → Claude + GPT + Gemini (Full Council). Full sovereignty.
# Principle: The gate opens with trust, not payment.

WINDI_TIER = os.environ.get('WINDI_TIER', 'FREE').upper()

TIER_GATES = {
    "FREE": {
        "dragons": [],
        "max_tokens": 0,
        "isp_access": False,
        "export_enabled": False,
        "ledger_write": False,
        "seal_enabled": False,
        "label": "Lokal (Local Motor)",
    },
    "MED": {
        "dragons": ["claude"],
        "max_tokens": 1024,
        "isp_access": True,       # read-only
        "export_enabled": True,    # basic formats
        "ledger_write": False,
        "seal_enabled": False,
        "label": "Wächter (Guardian)",
    },
    "HIGH": {
        "dragons": ["claude", "gpt", "gemini"],
        "max_tokens": 2048,
        "isp_access": True,       # full (read + resolve)
        "export_enabled": True,    # all formats
        "ledger_write": True,
        "seal_enabled": True,
        "label": "Souverän (Full Council)",
    },
}

def get_gate():
    """Return the active gate configuration for the current tier."""
    return TIER_GATES.get(WINDI_TIER, TIER_GATES["FREE"])

def check_gate(dragon_name: str) -> bool:
    """Check if a dragon is allowed under the current tier."""
    return dragon_name.lower() in get_gate()["dragons"]

def gate_status() -> Dict:
    """Return full gate status for health/diagnostics."""
    gate = get_gate()
    return {
        "tier": WINDI_TIER,
        "label": gate["label"],
        "allowed_dragons": gate["dragons"],
        "max_tokens": gate["max_tokens"],
        "isp_access": gate["isp_access"],
        "export_enabled": gate["export_enabled"],
        "ledger_write": gate["ledger_write"],
        "seal_enabled": gate["seal_enabled"],
    }
# ─── END GATE CONTROLLER ─────────────────────────────────

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

    def _check_gate(self) -> Dict:
        """Gate check before any query. Returns error dict if blocked, None if allowed."""
        if not check_gate(self.name):
            gate = get_gate()
            return {
                "success": False,
                "error": f"GATE_BLOCKED: {self.name} not available in {WINDI_TIER} tier",
                "tier": WINDI_TIER,
                "allowed_dragons": gate["dragons"],
                "upgrade_hint": f"Current: {gate['label']}. {self.name} requires a higher tier."
            }
        return None

    def _get_max_tokens(self) -> int:
        """Return max tokens allowed for current tier."""
        return get_gate()["max_tokens"]

    def _receipt(self, prompt: str, response: str) -> str:
        ts = datetime.utcnow().strftime("%d%b%y").upper()
        h = hashlib.sha256(f"{self.name}{prompt}{response}".encode()).hexdigest()[:8]
        return f"WINDI-{self.name.upper()}-{ts}-{h}"


class ClaudeAPI(DragonAPI):
    def __init__(self):
        super().__init__("Claude", "Guardian")
        self.api_key = ANTHROPIC_API_KEY
        self.model = "claude-sonnet-4-20250514"
        self.available = bool(self.api_key)

    def query(self, prompt: str) -> Dict:
        gate_block = self._check_gate()
        if gate_block:
            return gate_block
        if not self.available:
            return {"success": False, "error": "No API key"}
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            msg = client.messages.create(
                model=self.model, max_tokens=self._get_max_tokens(),
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            txt = msg.content[0].text
            return {"success": True, "dragon": self.name, "response": txt,
                    "model": self.model, "tier": WINDI_TIER,
                    "receipt": self._receipt(prompt, txt)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class GPTAPI(DragonAPI):
    def __init__(self):
        super().__init__("GPT", "Architect")
        self.api_key = OPENAI_API_KEY
        self.model = "gpt-4o"
        self.available = bool(self.api_key)

    def query(self, prompt: str) -> Dict:
        gate_block = self._check_gate()
        if gate_block:
            return gate_block
        if not self.available:
            return {"success": False, "error": "No API key"}
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            r = client.chat.completions.create(
                model=self.model, max_tokens=self._get_max_tokens(),
                messages=[{"role": "system", "content": self.system_prompt},
                          {"role": "user", "content": prompt}]
            )
            txt = r.choices[0].message.content
            return {"success": True, "dragon": self.name, "response": txt,
                    "model": self.model, "tier": WINDI_TIER,
                    "receipt": self._receipt(prompt, txt)}
        except Exception as e:
            return {"success": False, "error": str(e)}


class GeminiAPI(DragonAPI):
    def __init__(self):
        super().__init__("Gemini", "Witness")
        self.api_key = GEMINI_API_KEY
        self.model = "gemini-2.0-flash-lite"
        self.available = bool(self.api_key)

    def query(self, prompt: str) -> Dict:
        gate_block = self._check_gate()
        if gate_block:
            return gate_block
        if not self.available:
            return {"success": False, "error": "No API key"}
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model, system_instruction=self.system_prompt)
            r = model.generate_content(prompt)
            txt = r.text
            return {"success": True, "dragon": self.name, "response": txt,
                    "model": self.model, "tier": WINDI_TIER,
                    "receipt": self._receipt(prompt, txt)}
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
        gate = get_gate()
        return {
            "gate": gate_status(),
            "dragons": {
                n: {
                    "available": d.available,
                    "model": d.model,
                    "gated": n not in gate["dragons"],
                }
                for n, d in self.dragons.items()
            },
        }


_orch = None
def get_orchestrator():
    global _orch
    if not _orch:
        _orch = DragonOrchestrator()
    return _orch


if __name__ == "__main__":
    import sys
    import json

    test_mode = "--test-gates" in sys.argv

    if test_mode:
        # Test all three tiers without making API calls
        print("=" * 60)
        print("  GATE CONTROLLER — Tier Test")
        print("=" * 60)
        for tier in ["FREE", "MED", "HIGH"]:
            gate = TIER_GATES[tier]
            print(f"\n{'─' * 60}")
            print(f"  TIER: {tier} — {gate['label']}")
            print(f"{'─' * 60}")
            print(f"  Dragons:    {', '.join(gate['dragons'])}")
            print(f"  Max tokens: {gate['max_tokens']}")
            print(f"  ISP:        {'YES' if gate['isp_access'] else 'NO'}")
            print(f"  Export:     {'YES' if gate['export_enabled'] else 'NO'}")
            print(f"  Ledger:     {'YES' if gate['ledger_write'] else 'NO'}")
            print(f"  Seal:       {'YES' if gate['seal_enabled'] else 'NO'}")
            for dragon in ["gemini", "claude", "gpt"]:
                allowed = dragon in gate["dragons"]
                icon = "\u2705" if allowed else "\u26d4"
                print(f"  {icon} {dragon.upper():8} {'OPEN' if allowed else 'BLOCKED'}")
        print(f"\n{'=' * 60}")
        print("  All gates validated. Human decides. WINDI guarantees.")
        print(f"{'=' * 60}")
    else:
        print("=" * 60)
        print(f"  DRAGON APIs — Gate Controller Active")
        print(f"  Tier: {WINDI_TIER} — {get_gate()['label']}")
        print("=" * 60)
        o = get_orchestrator()
        s = o.status()
        print(f"\n  Gate: {s['gate']['tier']} ({s['gate']['label']})")
        print(f"  Allowed: {', '.join(s['gate']['allowed_dragons'])}")
        print(f"  Max tokens: {s['gate']['max_tokens']}")
        print()
        for n, d in s["dragons"].items():
            if d["gated"]:
                icon = "\u26d4"
                state = "GATED"
            elif d["available"]:
                icon = "\u2705"
                state = "READY"
            else:
                icon = "\u26a0\ufe0f"
                state = "NO KEY"
            print(f"  {icon} {n.upper():8} | {d['model']:30} | {state}")
