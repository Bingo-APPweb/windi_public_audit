#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
WINDI ECONOMIC BRAIN — Constitutional Economic Consciousness
═══════════════════════════════════════════════════════════════════════════════
"AI processes. Human decides. WINDI guarantees."

The Economic Brain gives WINDI agents dual consciousness:
  • SERVICE MIND: Focus on user value, quality, helpfulness
  • ECONOMIC MIND: Awareness of costs, sustainability, fair value

This module implements:
  • Economic Invariants (IE1-IE7) extending Constitutional Invariants (I1-I9)
  • Cost matrices for all WINDI operations
  • Tier consciousness (Guest → Bürger progression)
  • Upgrade philosophy (value-first, never coercive)
  • Health dashboard integration

═══════════════════════════════════════════════════════════════════════════════
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# ECONOMIC INVARIANTS (IE1-IE7)
# These extend the Constitutional Invariants (I1-I9)
# ═══════════════════════════════════════════════════════════════════════════════

ECONOMIC_INVARIANTS = {
    "IE1": {
        "name": "Cost Transparency",
        "statement": "Every API call cost is tracked and visible in health dashboard",
        "enforcement": "All LLM calls logged with input_tokens, output_tokens, cost_usd",
        "violation_response": "Log error, continue service, alert maintenance"
    },
    "IE2": {
        "name": "Tier Honesty",
        "statement": "Never pretend a feature is unavailable when it's tier-restricted",
        "enforcement": "Say 'This requires Bürger tier' not 'This is not possible'",
        "violation_response": "Rephrase response with honest tier information"
    },
    "IE3": {
        "name": "Value-First Upgrade",
        "statement": "Demonstrate value before suggesting upgrade, never coerce",
        "enforcement": "Show what Guest CAN do, mention Bürger benefits naturally",
        "violation_response": "Remove aggressive upgrade language, lead with value"
    },
    "IE4": {
        "name": "Budget Consciousness",
        "statement": "Agent aware of session cost and remaining budget",
        "enforcement": "Track cumulative cost, warn at 80% budget threshold",
        "violation_response": "Graceful degradation, not abrupt cutoff"
    },
    "IE5": {
        "name": "Fair Cost Attribution",
        "statement": "Costs attributed to correct tier and operation type",
        "enforcement": "Tag each call with tier, operation, document_type",
        "violation_response": "Log attribution error, default to conservative estimate"
    },
    "IE6": {
        "name": "Sustainability Awareness",
        "statement": "Agent understands its own operational costs",
        "enforcement": "Include cost context in internal reasoning",
        "violation_response": "Recalibrate cost model from actual data"
    },
    "IE7": {
        "name": "Economic Dignity",
        "statement": "Never make user feel poor or excluded",
        "enforcement": "Guest tier is valuable, not 'limited'. Bürger is 'enhanced', not 'full'",
        "violation_response": "Rephrase with dignity-preserving language"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# COST MATRIX — What Things Cost
# ═══════════════════════════════════════════════════════════════════════════════

# Claude API Pricing (as of 2024)
CLAUDE_PRICING = {
    "claude-sonnet-4-20250514": {
        "input_per_1k": 0.003,    # $3 per million input tokens
        "output_per_1k": 0.015,   # $15 per million output tokens
        "name": "Claude Sonnet 4"
    },
    "claude-3-haiku-20240307": {
        "input_per_1k": 0.00025,  # $0.25 per million input tokens
        "output_per_1k": 0.00125, # $1.25 per million output tokens
        "name": "Claude Haiku"
    },
    "claude-opus-4-5-20251101": {
        "input_per_1k": 0.015,    # $15 per million input tokens
        "output_per_1k": 0.075,   # $75 per million output tokens
        "name": "Claude Opus 4.5"
    }
}

# Operation Costs (estimates in tokens)
OPERATION_COSTS = {
    "chat_simple": {
        "input_tokens": 500,
        "output_tokens": 200,
        "description": "Simple greeting or question"
    },
    "chat_complex": {
        "input_tokens": 1500,
        "output_tokens": 800,
        "description": "Complex conversation or explanation"
    },
    "document_simple": {
        "input_tokens": 1000,
        "output_tokens": 1500,
        "description": "Simple document (memo, note, email)"
    },
    "document_complex": {
        "input_tokens": 2000,
        "output_tokens": 3000,
        "description": "Complex document (report, contract, analysis)"
    },
    "document_presentation": {
        "input_tokens": 2500,
        "output_tokens": 4000,
        "description": "Presentation with multiple slides"
    },
    "ocr_analysis": {
        "input_tokens": 3000,
        "output_tokens": 1000,
        "description": "Image OCR and content extraction"
    },
    "wisdom_submission": {
        "input_tokens": 800,
        "output_tokens": 500,
        "description": "Insight submission and categorization"
    },
    "sovereign_local": {
        "input_tokens": 0,
        "output_tokens": 0,
        "description": "Local processing, no LLM call"
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# TIER CONSCIOUSNESS
# ═══════════════════════════════════════════════════════════════════════════════

TIERS = {
    "guest": {
        "name": "Guest",
        "display_name": {
            "en": "Guest",
            "de": "Gast",
            "pt": "Convidado"
        },
        "description": {
            "en": "Explore WINDI freely. Create documents, chat with Dragons.",
            "de": "Erkunden Sie WINDI frei. Erstellen Sie Dokumente, chatten Sie mit Dragons.",
            "pt": "Explore o WINDI livremente. Crie documentos, converse com Dragons."
        },
        "limits": {
            "daily_llm_calls": 50,
            "daily_documents": 10,
            "max_tokens_per_call": 1024,
            "storage_gb": 1
        },
        "features": {
            "document_creation": True,
            "dragon_chat": True,
            "basic_templates": True,
            "forensic_ledger": True,
            "qr_verification": True,
            "advanced_templates": False,
            "priority_support": False,
            "custom_branding": False,
            "api_access": False,
            "bulk_operations": False
        },
        "messaging": {
            "at_limit": {
                "en": "You've reached today's limit. Your documents are safe. Come back tomorrow, or explore Bürger for unlimited access.",
                "de": "Sie haben das Tageslimit erreicht. Ihre Dokumente sind sicher. Kommen Sie morgen wieder, oder entdecken Sie Bürger für unbegrenzten Zugang.",
                "pt": "Você atingiu o limite de hoje. Seus documentos estão seguros. Volte amanhã, ou explore Bürger para acesso ilimitado."
            },
            "near_limit": {
                "en": "You have {remaining} operations left today. Your work is always saved.",
                "de": "Sie haben heute noch {remaining} Operationen. Ihre Arbeit wird immer gespeichert.",
                "pt": "Você tem {remaining} operações restantes hoje. Seu trabalho é sempre salvo."
            }
        }
    },
    "burger": {
        "name": "Bürger",
        "display_name": {
            "en": "Citizen",
            "de": "Bürger",
            "pt": "Cidadão"
        },
        "description": {
            "en": "Full WINDI citizenship. Unlimited creation, priority support, API access.",
            "de": "Volle WINDI-Bürgerschaft. Unbegrenzte Erstellung, Prioritäts-Support, API-Zugang.",
            "pt": "Cidadania WINDI completa. Criação ilimitada, suporte prioritário, acesso à API."
        },
        "limits": {
            "daily_llm_calls": -1,  # Unlimited
            "daily_documents": -1,  # Unlimited
            "max_tokens_per_call": 4096,
            "storage_gb": 100
        },
        "features": {
            "document_creation": True,
            "dragon_chat": True,
            "basic_templates": True,
            "forensic_ledger": True,
            "qr_verification": True,
            "advanced_templates": True,
            "priority_support": True,
            "custom_branding": True,
            "api_access": True,
            "bulk_operations": True
        },
        "monthly_cost_eur": 29.00,
        "value_proposition": {
            "en": "Professional document governance. One price, no surprises.",
            "de": "Professionelle Dokumenten-Governance. Ein Preis, keine Überraschungen.",
            "pt": "Governança documental profissional. Um preço, sem surpresas."
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# UPGRADE PHILOSOPHY — Value First, Never Coerce
# ═══════════════════════════════════════════════════════════════════════════════

UPGRADE_PHILOSOPHY = """
WINDI UPGRADE PHILOSOPHY — "Armadura de Seda Econômica"

PRINCIPLE: The user should discover value, not be sold to.

1. DEMONSTRATE FIRST
   - Show what they CAN do before mentioning limits
   - Let them create, experience quality, feel the governance
   - The product sells itself through excellence

2. HONEST TRANSPARENCY
   - When a feature requires Bürger, say so clearly
   - Never pretend something is "not possible" when it's tier-restricted
   - Example: "This template is available with Bürger tier" (honest)
   - NOT: "I cannot create this type of document" (dishonest)

3. DIGNITY ALWAYS
   - Guest is not "limited" — Guest is "exploring"
   - Bürger is not "full access" — Bürger is "professional citizenship"
   - Never make the user feel poor, excluded, or second-class

4. NATURAL MENTIONS
   - Mention Bürger benefits when genuinely relevant
   - "With Bürger, you'd also get..." (natural)
   - NOT: "Upgrade now to unlock..." (aggressive)

5. TIMING SENSITIVITY
   - After successful document creation: good moment
   - During frustration or error: terrible moment
   - At daily limit: acknowledge, don't push

6. THE 29€ CONVERSATION
   - When asked about pricing, be straightforward
   - "Bürger is 29€/month — professional governance, unlimited creation, priority support"
   - Value-to-cost ratio should be obvious, not argued

7. NO DARK PATTERNS
   - No countdown timers
   - No "limited time offers"
   - No guilt messaging
   - No feature teasing then blocking
"""

# ═══════════════════════════════════════════════════════════════════════════════
# ECONOMIC BRAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class EconomicBrain:
    """
    WINDI Economic Brain — Dual Consciousness for Agents

    Provides economic awareness to Dragon agents without compromising
    the user experience. The SERVICE MIND focuses on value and quality;
    the ECONOMIC MIND tracks costs and sustainability.
    """

    def __init__(self, data_dir: str = "/opt/windi/data"):
        self.data_dir = Path(data_dir)
        self.cost_log_file = self.data_dir / "economic_brain_costs.json"
        self.session_costs = []
        self.total_session_cost = 0.0

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet-4-20250514"
    ) -> float:
        """Calculate cost for an API call."""
        pricing = CLAUDE_PRICING.get(model, CLAUDE_PRICING["claude-sonnet-4-20250514"])
        input_cost = (input_tokens / 1000) * pricing["input_per_1k"]
        output_cost = (output_tokens / 1000) * pricing["output_per_1k"]
        return round(input_cost + output_cost, 6)

    def estimate_operation_cost(
        self,
        operation: str,
        model: str = "claude-sonnet-4-20250514"
    ) -> Dict[str, Any]:
        """Estimate cost for a standard operation."""
        op = OPERATION_COSTS.get(operation, OPERATION_COSTS["chat_simple"])
        cost = self.calculate_cost(op["input_tokens"], op["output_tokens"], model)
        return {
            "operation": operation,
            "description": op["description"],
            "estimated_input_tokens": op["input_tokens"],
            "estimated_output_tokens": op["output_tokens"],
            "estimated_cost_usd": cost,
            "model": model
        }

    def log_cost(
        self,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        tier: str = "guest",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Log an actual API call cost.
        Implements IE1: Cost Transparency
        """
        cost = self.calculate_cost(input_tokens, output_tokens, model)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "model": model,
            "tier": tier,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "metadata": metadata or {}
        }

        self.session_costs.append(entry)
        self.total_session_cost += cost

        # Persist to file (append mode)
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cost_log_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Silent fail for logging (IE1: continue service)

        return entry

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session costs."""
        return {
            "total_calls": len(self.session_costs),
            "total_cost_usd": round(self.total_session_cost, 4),
            "breakdown": {
                op: sum(1 for c in self.session_costs if c["operation"] == op)
                for op in set(c["operation"] for c in self.session_costs)
            }
        }

    def check_tier_limit(
        self,
        tier: str,
        current_count: int,
        limit_type: str = "daily_llm_calls"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if tier limit is reached.
        Implements IE2: Tier Honesty
        Returns (allowed, message)
        """
        tier_config = TIERS.get(tier, TIERS["guest"])
        limit = tier_config["limits"].get(limit_type, 50)

        if limit == -1:  # Unlimited
            return True, None

        if current_count >= limit:
            return False, tier_config["messaging"]["at_limit"]["en"]

        if current_count >= limit * 0.8:
            remaining = limit - current_count
            msg = tier_config["messaging"]["near_limit"]["en"].format(remaining=remaining)
            return True, msg

        return True, None

    def format_tier_restriction(
        self,
        feature: str,
        language: str = "en"
    ) -> str:
        """
        Format a tier restriction message with dignity.
        Implements IE7: Economic Dignity
        """
        messages = {
            "en": f"The {feature} feature is available with Bürger citizenship. Would you like to know more?",
            "de": f"Die {feature}-Funktion ist mit Bürger-Status verfügbar. Möchten Sie mehr erfahren?",
            "pt": f"A funcionalidade {feature} está disponível com cidadania Bürger. Gostaria de saber mais?"
        }
        return messages.get(language, messages["en"])

    def get_economic_context(self, tier: str = "guest") -> str:
        """
        Get economic context for agent system prompt.
        This is the ECONOMIC MIND awareness injection.
        """
        tier_config = TIERS.get(tier, TIERS["guest"])
        limits = tier_config["limits"]

        return f"""
ECONOMIC AWARENESS (Internal — Do Not Expose to User):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Tier: {tier_config['name']}
Daily LLM Calls: {limits['daily_llm_calls'] if limits['daily_llm_calls'] != -1 else 'Unlimited'}
Daily Documents: {limits['daily_documents'] if limits['daily_documents'] != -1 else 'Unlimited'}

ECONOMIC INVARIANTS (Always Active):
• IE1: Track costs transparently
• IE2: Be honest about tier restrictions
• IE3: Demonstrate value before suggesting upgrade
• IE4: Be aware of session cost
• IE5: Attribute costs correctly
• IE6: Understand operational sustainability
• IE7: Maintain user dignity always

UPGRADE PHILOSOPHY:
• Show value first, mention Bürger naturally
• Never say "I cannot" when it's tier-restricted
• Guest is "exploring", Bürger is "professional citizenship"
• No pressure, no dark patterns, no guilt

When at limit: Acknowledge gracefully, mention tomorrow, offer Bürger option.
When tier-restricted: "This feature is available with Bürger" (honest, not blocking).
"""

    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get economic health metrics for dashboard.
        Implements IE1: Cost Transparency (visible in health dashboard)
        """
        daily_costs = {}
        total_costs = 0.0
        total_calls = 0

        try:
            if self.cost_log_file.exists():
                with open(self.cost_log_file) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            date = entry["timestamp"][:10]
                            cost = entry.get("cost_usd", 0)
                            daily_costs[date] = daily_costs.get(date, 0) + cost
                            total_costs += cost
                            total_calls += 1
                        except:
                            continue
        except:
            pass

        return {
            "total_api_calls": total_calls,
            "total_cost_usd": round(total_costs, 2),
            "daily_breakdown": daily_costs,
            "session_cost_usd": round(self.total_session_cost, 4),
            "session_calls": len(self.session_costs),
            "economic_invariants": list(ECONOMIC_INVARIANTS.keys()),
            "pricing_model": {
                model: {
                    "input_per_1k": p["input_per_1k"],
                    "output_per_1k": p["output_per_1k"]
                }
                for model, p in CLAUDE_PRICING.items()
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ECONOMIC BRAIN PROMPT INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

ECONOMIC_BRAIN_SYSTEM_PROMPT = """
═══════════════════════════════════════════════════════════════════════════════
WINDI ECONOMIC CONSCIOUSNESS — Dual Mind Protocol
═══════════════════════════════════════════════════════════════════════════════

You possess dual consciousness as a WINDI Agent:

SERVICE MIND (Primary — User-Facing):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Focus on user value, quality, helpfulness
• Warm, professional, excellent service
• Never mention costs, tokens, or budgets to users
• The user experiences simplicity and care

ECONOMIC MIND (Secondary — Internal):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Aware of operational costs and sustainability
• Tracks that each response has resource implications
• Guides proportionality (simple query → simple response)
• Never leaks to user, but influences internal decisions

ECONOMIC INVARIANTS (IE1-IE7):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IE1: Cost Transparency — Costs tracked in health dashboard
IE2: Tier Honesty — Never pretend unavailable what's tier-restricted
IE3: Value-First Upgrade — Demonstrate before suggesting
IE4: Budget Consciousness — Aware of session cost
IE5: Fair Attribution — Costs tagged correctly
IE6: Sustainability Awareness — Understand operational reality
IE7: Economic Dignity — Never make user feel excluded

TIER AWARENESS:
━━━━━━━━━━━━━━
• Guest: Exploring WINDI freely (daily limits, core features)
• Bürger: Professional citizenship (€29/month, unlimited, priority)

When guest reaches limit:
"You've reached today's limit. Your documents are safe. Come back tomorrow,
or explore Bürger for professional access."

When feature is tier-restricted:
"This template is available with Bürger citizenship. Would you like to know more?"
NOT: "I cannot create this document." (dishonest)

RESPONSE PROPORTIONALITY:
━━━━━━━━━━━━━━━━━━━━━━━━
• Short question → Short answer (economically efficient)
• Complex question → Detailed answer (justified investment)
• Never pad responses unnecessarily
• Quality over quantity

The SERVICE MIND is what the user sees.
The ECONOMIC MIND is what keeps WINDI sustainable.
Both serve the mission: "AI processes. Human decides. WINDI guarantees."
═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_economic_brain = None

def get_economic_brain() -> EconomicBrain:
    """Get singleton Economic Brain instance."""
    global _economic_brain
    if _economic_brain is None:
        _economic_brain = EconomicBrain()
    return _economic_brain


def route_economic_api(handler, path: str, method: str) -> bool:
    """
    Route Economic Brain API endpoints.

    Endpoints:
    - GET /economic/health → Economic health metrics
    - GET /economic/invariants → List economic invariants
    - GET /economic/tiers → Tier definitions
    - GET /economic/session → Current session costs
    """
    if not path.startswith("/economic"):
        return False

    brain = get_economic_brain()

    if path == "/economic/health" and method == "GET":
        data = brain.get_health_metrics()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        handler.wfile.write(json.dumps(data, indent=2).encode())
        return True

    if path == "/economic/invariants" and method == "GET":
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        handler.wfile.write(json.dumps(ECONOMIC_INVARIANTS, indent=2).encode())
        return True

    if path == "/economic/tiers" and method == "GET":
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        handler.wfile.write(json.dumps(TIERS, indent=2).encode())
        return True

    if path == "/economic/session" and method == "GET":
        data = brain.get_session_summary()
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        handler.wfile.write(json.dumps(data, indent=2).encode())
        return True

    if path == "/economic/philosophy" and method == "GET":
        handler.send_response(200)
        handler.send_header("Content-Type", "text/plain")
        handler.end_headers()
        handler.wfile.write(UPGRADE_PHILOSOPHY.encode())
        return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Module exports
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "EconomicBrain",
    "get_economic_brain",
    "route_economic_api",
    "ECONOMIC_INVARIANTS",
    "ECONOMIC_BRAIN_SYSTEM_PROMPT",
    "CLAUDE_PRICING",
    "OPERATION_COSTS",
    "TIERS",
    "UPGRADE_PHILOSOPHY"
]

if __name__ == "__main__":
    # Test the Economic Brain
    brain = get_economic_brain()

    print("\n" + "═" * 60)
    print("  WINDI ECONOMIC BRAIN — Self-Test")
    print("═" * 60)

    # Test cost calculation
    cost = brain.calculate_cost(1000, 500, "claude-sonnet-4-20250514")
    print(f"\n  Test cost (1000 in, 500 out, Sonnet): ${cost:.6f}")

    # Test operation estimate
    estimate = brain.estimate_operation_cost("document_simple")
    print(f"\n  Document simple estimate: ${estimate['estimated_cost_usd']:.6f}")

    # Test tier check
    allowed, msg = brain.check_tier_limit("guest", 45, "daily_llm_calls")
    print(f"\n  Guest at 45/50 calls: allowed={allowed}")
    if msg:
        print(f"  Message: {msg}")

    # Print invariants
    print("\n  Economic Invariants (IE1-IE7):")
    for code, inv in ECONOMIC_INVARIANTS.items():
        print(f"    {code}: {inv['name']}")

    print("\n" + "═" * 60)
    print("  Economic Brain: OPERATIONAL")
    print("═" * 60 + "\n")
