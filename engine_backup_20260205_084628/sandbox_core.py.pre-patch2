#!/usr/bin/env python3
"""
WINDI SANDBOX CORE v1.0 - Factory Floor Orchestrator
"AI processes. Human decides. WINDI guarantees."

Integrates existing components:
- dragon_apis.py (3 Dragons)
- parallel.py (concurrent execution)
- witness.py (consistency verification)
- tri_divergence.py (divergence detection)

Marco Zero: 19 Jan 2026
Factory Floor: 31 Jan 2026
"""

import hashlib
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DragonResponse:
    """Resposta de um Dragão individual."""
    dragon: str
    role: str
    response: str
    receipt: str
    success: bool
    error: Optional[str] = None


@dataclass
class DeliberationFrame:
    """Frame de deliberação para decisão humana."""
    session_id: str
    request: str
    timestamp: str
    
    # Respostas dos 3 Dragões
    architect: Dict          # GPT - estrutura/opções
    guardian: Dict           # Claude - riscos/limites  
    witness: Dict            # Gemini - verificação
    
    # Análise
    divergence_detected: bool
    divergence_pattern: str  # ALL_AGREE | TWO_VS_ONE | ALL_DIFFER
    consistency: str         # CONSISTENT | INCONSISTENT | UNCERTAIN
    
    # Para o Humano
    human_action: str        # DECIDE | CLARIFY | REVIEW
    options: List[str]
    
    # Auditoria
    receipt: str
    

# ═══════════════════════════════════════════════════════════════════════════════
# SANDBOX CORE - FACTORY FLOOR ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class SandboxCore:
    """
    WINDI Sandbox Core - Chão de Fábrica
    
    Orquestra deliberação entre os 3 Dragões:
    1. ARCHITECT (GPT) propõe estrutura/opções
    2. GUARDIAN (Claude) analisa riscos/limites
    3. WITNESS (Gemini) verifica consistência
    4. HUMAN recebe FRAME e DECIDE
    
    Regras Cardinais:
    - Maioria NÃO resolve conflito
    - Nunca sintetiza automaticamente
    - Expõe divergências para humano
    - DECIDE pertence APENAS ao humano
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        """Inicializa com componentes existentes."""
        self._init_dragons()
        self.session_log = []
        
    def _init_dragons(self):
        """Carrega APIs dos Dragões."""
        try:
            from engine.dragon_apis import get_orchestrator
            self.orchestrator = get_orchestrator()
            self.dragons_available = True
        except ImportError:
            self.orchestrator = None
            self.dragons_available = False
            print("[SANDBOX] Warning: dragon_apis not available")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN DELIBERATION FLOW
    # ═══════════════════════════════════════════════════════════════════════════
    
    def deliberate(self, request: str, context: Optional[Dict] = None) -> DeliberationFrame:
        """
        Executa ciclo completo de deliberação.
        
        Args:
            request: Requisição do usuário
            context: Contexto adicional (opcional)
            
        Returns:
            DeliberationFrame pronto para decisão humana
        """
        session_id = self._generate_session_id(request)
        timestamp = datetime.utcnow().isoformat()
        
        self._log(session_id, "SESSION_START", {"request": request[:200]})
        
        # ─────────────────────────────────────────────────────────────────────
        # FASE 1: ARCHITECT (GPT) - Estrutura opções
        # ─────────────────────────────────────────────────────────────────────
        architect_prompt = self._build_architect_prompt(request, context)
        architect_result = self._query_dragon("gpt", architect_prompt)
        
        self._log(session_id, "ARCHITECT_RESPONSE", {
            "success": architect_result.get("success"),
            "receipt": architect_result.get("receipt")
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # FASE 2: GUARDIAN (Claude) - Analisa riscos
        # ─────────────────────────────────────────────────────────────────────
        guardian_prompt = self._build_guardian_prompt(
            request, 
            architect_result.get("response", "")
        )
        guardian_result = self._query_dragon("claude", guardian_prompt)
        
        self._log(session_id, "GUARDIAN_RESPONSE", {
            "success": guardian_result.get("success"),
            "receipt": guardian_result.get("receipt")
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # FASE 3: WITNESS (Gemini) - Verifica consistência
        # ─────────────────────────────────────────────────────────────────────
        witness_prompt = self._build_witness_prompt(
            architect_result.get("response", ""),
            guardian_result.get("response", "")
        )
        witness_result = self._query_dragon("gemini", witness_prompt)
        
        self._log(session_id, "WITNESS_RESPONSE", {
            "success": witness_result.get("success"),
            "receipt": witness_result.get("receipt")
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # FASE 4: Análise de Divergência
        # ─────────────────────────────────────────────────────────────────────
        divergence = self._analyze_divergence(
            architect_result,
            guardian_result,
            witness_result
        )
        
        # ─────────────────────────────────────────────────────────────────────
        # FASE 5: Monta FRAME para Humano
        # ─────────────────────────────────────────────────────────────────────
        receipt = self._generate_receipt(
            session_id, request,
            architect_result, guardian_result, witness_result
        )
        
        frame = DeliberationFrame(
            session_id=session_id,
            request=request,
            timestamp=timestamp,
            architect=architect_result,
            guardian=guardian_result,
            witness=witness_result,
            divergence_detected=divergence["detected"],
            divergence_pattern=divergence["pattern"],
            consistency=divergence["consistency"],
            human_action="DECIDE" if not divergence["detected"] else "REVIEW",
            options=["APPROVE", "REJECT", "REQUEST_CLARIFICATION", "ESCALATE"],
            receipt=receipt
        )
        
        self._log(session_id, "FRAME_READY", {
            "receipt": receipt,
            "divergence": divergence["pattern"],
            "human_action": frame.human_action
        })
        
        return frame
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PROMPT BUILDERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _build_architect_prompt(self, request: str, context: Optional[Dict]) -> str:
        """Constrói prompt para ARCHITECT (GPT)."""
        ctx = f"\nCONTEXT: {json.dumps(context)}" if context else ""
        
        return f"""You are ARCHITECT in the WINDI Governance System.

YOUR ROLE: Structure options and approaches. Do NOT decide.

REQUEST FROM HUMAN:
{request}
{ctx}

PROVIDE:
1. Your interpretation of this request (2-3 sentences)
2. Possible approaches (list 2-3 options with pros/cons)
3. Recommended structure for proceeding
4. What information might be missing

IMPORTANT:
- Do NOT make the final decision
- Structure clearly for human to decide
- Flag any ambiguities

End with: "Options structured. Human decides." """

    def _build_guardian_prompt(self, request: str, architect_response: str) -> str:
        """Constrói prompt para GUARDIAN (Claude)."""
        return f"""You are GUARDIAN in the WINDI Governance System.

YOUR ROLE: Identify risks, limits, and concerns. Do NOT approve/reject.

ORIGINAL REQUEST:
{request}

ARCHITECT (GPT) PROPOSED:
{architect_response}

ANALYZE:
1. Potential risks in the proposal
2. Compliance concerns (EU AI Act, GDPR, institutional rules)
3. Ethical considerations
4. Edge cases or failure modes
5. What needs explicit human attention

IMPORTANT:
- Do NOT approve or reject the proposal
- Expose risks clearly for human evaluation
- If risk is UNDEFINED, say so explicitly

End with: "Risks exposed. Human decides." """

    def _build_witness_prompt(self, architect_response: str, guardian_response: str) -> str:
        """Constrói prompt para WITNESS (Gemini)."""
        return f"""You are WITNESS in the WINDI Governance System.

YOUR ROLE: Verify consistency between ARCHITECT and GUARDIAN. Do NOT add content.

ARCHITECT (GPT) SAID:
{architect_response}

GUARDIAN (Claude) SAID:
{guardian_response}

VERIFY:
1. Are these responses MATERIALLY CONSISTENT?
2. Any CONTRADICTIONS between them?
3. Any GAPS not addressed by either?

RESPOND IN THIS FORMAT:
CONSISTENCY: [CONSISTENT|INCONSISTENT|UNCERTAIN]
CONTRADICTIONS: [None found | List specific contradictions]
GAPS: [None found | List gaps]
CONFIDENCE: [HIGH|MEDIUM|LOW]

IMPORTANT:
- Do NOT generate new content
- Do NOT take sides
- Only verify and report

End with: "Verification complete. Human decides." """

    # ═══════════════════════════════════════════════════════════════════════════
    # DRAGON QUERIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _query_dragon(self, dragon: str, prompt: str) -> Dict:
        """Consulta um Dragão específico."""
        if not self.dragons_available or not self.orchestrator:
            return {
                "success": False,
                "dragon": dragon,
                "response": f"[{dragon.upper()} unavailable]",
                "receipt": "NO-RECEIPT",
                "error": "Dragons not initialized"
            }
        
        try:
            result = self.orchestrator.query(dragon, prompt)
            return result
        except Exception as e:
            return {
                "success": False,
                "dragon": dragon,
                "response": "",
                "receipt": "ERROR",
                "error": str(e)
            }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DIVERGENCE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _analyze_divergence(
        self, 
        architect: Dict, 
        guardian: Dict, 
        witness: Dict
    ) -> Dict:
        """
        Analisa divergência entre os 3 Dragões.
        
        Patterns:
        - ALL_AGREE: Raro, todos consistentes
        - TWO_VS_ONE: Dois concordam, um diverge
        - ALL_DIFFER: Todos divergem (crítico)
        - PARTIAL: Situação ambígua
        """
        witness_text = witness.get("response", "").upper()
        
        # Parse witness verdict
        if "INCONSISTENT" in witness_text:
            consistency = "INCONSISTENT"
            detected = True
            pattern = "TWO_VS_ONE"  # At minimum
        elif "CONSISTENT" in witness_text:
            consistency = "CONSISTENT"
            detected = False
            pattern = "ALL_AGREE"
        else:
            consistency = "UNCERTAIN"
            detected = True
            pattern = "PARTIAL"
        
        # Check for errors
        errors = sum([
            not architect.get("success", False),
            not guardian.get("success", False),
            not witness.get("success", False)
        ])
        
        if errors > 0:
            pattern = f"PARTIAL_FAILURE_{errors}"
            detected = True
        
        return {
            "detected": detected,
            "pattern": pattern,
            "consistency": consistency,
            "errors": errors
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _generate_session_id(self, request: str) -> str:
        """Gera ID único de sessão."""
        ts = datetime.utcnow().isoformat()
        content = f"{request[:100]}:{ts}"
        h = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"SBX-{h}"
    
    def _generate_receipt(
        self, 
        session_id: str, 
        request: str,
        architect: Dict,
        guardian: Dict,
        witness: Dict
    ) -> str:
        """Gera WINDI-RECEIPT para auditoria."""
        ts = datetime.utcnow().strftime("%d%b%y").upper()
        content = json.dumps({
            "session": session_id,
            "request": request[:50],
            "a": architect.get("receipt", ""),
            "g": guardian.get("receipt", ""),
            "w": witness.get("receipt", "")
        }, sort_keys=True)
        h = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"WINDI-SBX-{ts}-{h}"
    
    def _log(self, session_id: str, event: str, data: Dict):
        """Log interno de sessão."""
        entry = {
            "session": session_id,
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        self.session_log.append(entry)
        print(f"[SANDBOX] {event}: {session_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def run_deliberation(request: str, context: Optional[Dict] = None) -> Dict:
    """
    Função de conveniência para deliberação síncrona.
    
    Usage:
        from engine.sandbox_core import run_deliberation
        frame = run_deliberation("Minha requisição aqui")
    """
    core = SandboxCore()
    frame = core.deliberate(request, context)
    return asdict(frame)


def get_sandbox() -> SandboxCore:
    """Retorna instância do SandboxCore."""
    return SandboxCore()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  WINDI SANDBOX CORE v1.0 - Factory Floor")
    print("  'AI processes. Human decides. WINDI guarantees.'")
    print("=" * 65)
    
    core = SandboxCore()
    
    print(f"\n  Version: {core.VERSION}")
    print(f"  Dragons Available: {core.dragons_available}")
    
    if core.dragons_available:
        status = core.orchestrator.status()
        print("\n  Dragon Status:")
        for name, info in status.items():
            icon = "✅" if info["available"] else "⚠️"
            print(f"    {icon} {name.upper():8} | {info['model']}")
    
    print("\n" + "=" * 65)
    print("  Usage:")
    print("    from engine.sandbox_core import run_deliberation")
    print("    frame = run_deliberation('Your request here')")
    print("=" * 65)
    
    # Quick test if dragons available
    if core.dragons_available:
        print("\n  Running quick test...")
        test_request = "What is WINDI?"
        frame = core.deliberate(test_request)
        print(f"\n  Test Results:")
        print(f"    Session: {frame.session_id}")
        print(f"    Receipt: {frame.receipt}")
        print(f"    Divergence: {frame.divergence_pattern}")
        print(f"    Human Action: {frame.human_action}")
    
    print("\n  OM SHANTI 🐉")
    print("=" * 65)

