# engine/witness.py
# WINDI Witness Protocol - Gemini as Independent Validator
# Status: PENDENTE | Prioridade: ALTA
# "Witness não decide. Witness informa."

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class WitnessVerdict:
    """Resultado da validação do Witness."""
    consistent: Optional[bool]  # As respostas são materialmente consistentes?
    verdict: str                # "CONSISTENT" | "INCONSISTENT" | "UNCERTAIN" | "ERROR"
    reason: str                 # Explicação breve
    confidence: float           # 0.0 - 1.0
    witness_receipt: str        # Audit trail
    timestamp: str              # ISO timestamp


class WitnessProtocol:
    """
    Gemini como Witness - observa e valida, não gera conteúdo.
    
    PAPEL DO WITNESS:
    - Observar respostas de Claude e GPT
    - Determinar se são materialmente consistentes
    - NÃO gerar conteúdo próprio
    - NÃO decidir qual é "melhor"
    - NÃO sintetizar ou harmonizar
    
    REGRA CARDINAL: Witness informa. Humano decide.
    """
    
    WITNESS_SYSTEM_PROMPT = """You are a WITNESS in the WINDI governance system.

YOUR ROLE:
- OBSERVE and VALIDATE only
- DO NOT generate new content
- DO NOT decide which response is better
- DO NOT synthesize or merge responses

YOUR TASK:
Determine if two AI responses are MATERIALLY CONSISTENT.

MATERIALLY CONSISTENT means:
- Same factual claims (or compatible facts)
- No contradictory recommendations
- No opposing normative statements (one says "allowed", other says "forbidden")

MATERIALLY INCONSISTENT means:
- Contradictory facts
- Opposing recommendations
- Normative conflict (X is permitted vs X is prohibited)

UNCERTAIN means:
- Cannot determine with confidence
- Responses address different aspects
- Insufficient information to judge"""

    WITNESS_USER_PROMPT = """Analyze these two responses for MATERIAL CONSISTENCY.

---
RESPONSE A (Claude):
{response_a}

---
RESPONSE B (GPT):
{response_b}

---

Respond ONLY in this exact format:
VERDICT: [CONSISTENT|INCONSISTENT|UNCERTAIN]
CONFIDENCE: [0.0-1.0]
REASON: [One sentence explanation - max 100 chars]

Do not add any other text."""

    def __init__(self, gemini_worker=None):
        """
        Args:
            gemini_worker: Instance of GeminiWorker (pode ser None se indisponível)
        """
        self.gemini = gemini_worker
        self._available = False
    
    def is_available(self) -> bool:
        """Check if witness is available."""
        if self.gemini is None:
            return False
        return self.gemini.is_available()
    
    def set_worker(self, gemini_worker):
        """Set or update the Gemini worker."""
        self.gemini = gemini_worker
    
    def validate(
        self,
        response_a: str,
        response_b: str,
        canon: Dict[str, Any],
        receipt_id: str
    ) -> WitnessVerdict:
        """
        Gemini valida se duas respostas são materialmente consistentes.
        
        Args:
            response_a: Resposta do Claude
            response_b: Resposta do GPT
            canon: Canon dict
            receipt_id: Receipt ID da transação principal
            
        Returns:
            WitnessVerdict com resultado da validação
        """
        timestamp = datetime.utcnow().isoformat()
        witness_receipt_base = f"{receipt_id}:witness"
        
        # Check availability
        if not self.is_available():
            return WitnessVerdict(
                consistent=None,
                verdict="UNAVAILABLE",
                reason="Witness backend (Gemini) not available",
                confidence=0.0,
                witness_receipt=f"{witness_receipt_base}:unavailable",
                timestamp=timestamp
            )
        
        # Validate inputs
        if not response_a or not response_b:
            return WitnessVerdict(
                consistent=None,
                verdict="INVALID_INPUT",
                reason="One or both responses empty",
                confidence=0.0,
                witness_receipt=f"{witness_receipt_base}:invalid",
                timestamp=timestamp
            )
        
        # Build prompt
        user_prompt = self.WITNESS_USER_PROMPT.format(
            response_a=response_a[:2000],  # Truncate for token limit
            response_b=response_b[:2000]
        )
        
        try:
            # Call Gemini as Witness
            result = self.gemini.chat(
                user_text=user_prompt,
                system_prompt=self.WITNESS_SYSTEM_PROMPT,
                canon=canon,
                receipt_id=f"{witness_receipt_base}",
                classification={"risk_level": "LOW"}  # Witness validation is low risk
            )
            
            # Check for fail-closed
            if result.get("flags", {}).get("fail_closed"):
                return WitnessVerdict(
                    consistent=None,
                    verdict="ERROR",
                    reason=result.get("flags", {}).get("fail_reason", "Unknown error"),
                    confidence=0.0,
                    witness_receipt=f"{witness_receipt_base}:error",
                    timestamp=timestamp
                )
            
            # Parse response
            content = result.get("content", "")
            verdict = self._parse_verdict(content)
            verdict.witness_receipt = f"{witness_receipt_base}:{verdict.verdict.lower()}"
            verdict.timestamp = timestamp
            
            return verdict
            
        except Exception as e:
            return WitnessVerdict(
                consistent=None,
                verdict="ERROR",
                reason=str(e)[:100],
                confidence=0.0,
                witness_receipt=f"{witness_receipt_base}:error",
                timestamp=timestamp
            )
    
    def _parse_verdict(self, text: str) -> WitnessVerdict:
        """Parse Gemini's structured response."""
        
        # Extract VERDICT
        verdict_match = re.search(
            r'VERDICT:\s*(CONSISTENT|INCONSISTENT|UNCERTAIN)',
            text,
            re.IGNORECASE
        )
        verdict = verdict_match.group(1).upper() if verdict_match else "UNCERTAIN"
        
        # Extract CONFIDENCE
        confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', text)
        try:
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        except:
            confidence = 0.5
        
        # Extract REASON
        reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        reason = reason_match.group(1).strip()[:100] if reason_match else "Could not parse reason"
        
        # Determine consistency
        if verdict == "CONSISTENT":
            consistent = True
        elif verdict == "INCONSISTENT":
            consistent = False
        else:
            consistent = None
        
        return WitnessVerdict(
            consistent=consistent,
            verdict=verdict,
            reason=reason,
            confidence=confidence,
            witness_receipt="",  # Filled by caller
            timestamp=""         # Filled by caller
        )
    
    def format_for_human(self, verdict: WitnessVerdict) -> str:
        """Format verdict for human review."""
        icon = {
            "CONSISTENT": "✅",
            "INCONSISTENT": "⚠️",
            "UNCERTAIN": "❓",
            "ERROR": "❌",
            "UNAVAILABLE": "⏸️"
        }.get(verdict.verdict, "❓")
        
        return f"""{icon} WITNESS VERDICT: {verdict.verdict}
Confidence: {verdict.confidence:.0%}
Reason: {verdict.reason}
Receipt: {verdict.witness_receipt}"""


# Singleton
_witness = None

def get_witness(gemini_worker=None) -> WitnessProtocol:
    """Get singleton witness instance."""
    global _witness
    if _witness is None:
        _witness = WitnessProtocol(gemini_worker)
    elif gemini_worker is not None:
        _witness.set_worker(gemini_worker)
    return _witness


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI WITNESS PROTOCOL - Module loaded")
    print("=" * 60)
    
    # Test parsing
    witness = WitnessProtocol()
    
    test_response = """VERDICT: INCONSISTENT
CONFIDENCE: 0.85
REASON: Response A says DPO is optional, Response B says always mandatory"""
    
    verdict = witness._parse_verdict(test_response)
    print(f"\nTest parse:")
    print(f"  Verdict: {verdict.verdict}")
    print(f"  Consistent: {verdict.consistent}")
    print(f"  Confidence: {verdict.confidence}")
    print(f"  Reason: {verdict.reason}")
    
    print("\n" + "=" * 60)
    print("Witness observa. Humano decide.")
    print("=" * 60)
