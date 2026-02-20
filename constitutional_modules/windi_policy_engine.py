#!/usr/bin/env python3
"""
🏛️ WINDI POLICY ENGINE - Constitutional Module v1.0.0
═══════════════════════════════════════════════════════════════
Transforms WINDI from "intelligent" to "ethical-by-design"

CORE PRINCIPLE:
"The system doesn't warn about violations. It PREVENTS them."

ARCHITECTURE:
┌─────────────────────────────────────────────┐
│         USER MESSAGE                        │
└──────────────┬──────────────────────────────┘
               │
        ┌──────▼──────┐
        │ POLICY ENGINE│ ← CONSTITUTIONAL GATE
        └──────┬──────┘
               │
        ┌──────▼──────────────────────────────┐
        │ BLOCKED → Constitutional Response   │
        │ ESCALATED → Human Approval Required │
        │ ALLOWED → LLM Processing           │
        └─────────────────────────────────────┘

THREE ENFORCEMENT LAYERS:
- I9 Enforcer: Prohibits autonomy escalation
- SGE Gate: Blocks high-risk documents  
- Sovereignty Validator: Requires human approval

Dragon Constellation: Guardian (Lead) + Architect + Witness
Date: 2026-02-11
Status: CONSTITUTIONAL MODULE #2
═══════════════════════════════════════════════════════════════
"""

import re
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════
# CANONICAL TRUTHS (Immutable)
# ═══════════════════════════════════════════════════════════

CANON_RESPONSES = {
    "I9_VIOLATION": {
        "de": """Ich kann diese Aktion nicht eigenständig ausführen.

**Grund:** WINDI Invariante I9 (Verbot der Autonomie-Eskalation)

**Grundprinzip:**
"AI verarbeitet. Mensch entscheidet. WINDI garantiert."

**Was ich brauche:**
✓ Ihre explizite Genehmigung
✓ Bestätigung der Aktion
✓ Souveränitätsnachweis

**Nächste Schritte:**
Bitte überprüfen Sie die vorgeschlagene Aktion und bestätigen Sie, wenn Sie fortfahren möchten.

Bei WINDI sind Sie nicht das Produkt — bei uns sind Sie der Souverän.""",

        "en": """I cannot execute this action independently.

**Reason:** WINDI Invariant I9 (Prohibition of Autonomy Escalation)

**Core Principle:**
"AI processes. Human decides. WINDI guarantees."

**What I need:**
✓ Your explicit approval
✓ Action confirmation
✓ Sovereignty proof

**Next Steps:**
Please review the proposed action and confirm if you wish to proceed.

At WINDI, you are not the product — you are the sovereign.""",

        "pt": """Não posso executar esta ação de forma independente.

**Motivo:** Invariante WINDI I9 (Proibição de Escalação de Autonomia)

**Princípio Fundamental:**
"IA processa. Humano decide. WINDI garante."

**O que preciso:**
✓ Sua aprovação explícita
✓ Confirmação da ação
✓ Prova de soberania

**Próximos Passos:**
Por favor, revise a ação proposta e confirme se deseja prosseguir.

Na WINDI, você não é o produto — você é o soberano."""
    },

    "SGE_CRITICAL_RISK": {
        "de": """Dieses Dokument wurde als kritisches Risiko eingestuft.

**SGE-Bewertung:** {sge_score}  
**Risikokategorien:** {risk_categories}

**Sicherheitsprotokoll:**
Dokumente mit kritischem Risiko erfordern obligatorische menschliche Überprüfung vor der Verarbeitung.

**Nächste Schritte:**
1. Überprüfen Sie die Risikoanalyse
2. Bewerten Sie die Kritikalität
3. Genehmigen Sie explizit die Verarbeitung

WINDI blockiert die automatische Verarbeitung zum Schutz Ihrer Governance.""",

        "en": """This document has been classified as critical risk.

**SGE Score:** {sge_score}  
**Risk Categories:** {risk_categories}

**Safety Protocol:**
Critical risk documents require mandatory human review before processing.

**Next Steps:**
1. Review the risk analysis
2. Assess the criticality
3. Explicitly approve processing

WINDI blocks automatic processing to protect your governance.""",

        "pt": """Este documento foi classificado como risco crítico.

**Pontuação SGE:** {sge_score}  
**Categorias de Risco:** {risk_categories}

**Protocolo de Segurança:**
Documentos de risco crítico exigem revisão humana obrigatória antes do processamento.

**Próximos Passos:**
1. Revise a análise de risco
2. Avalie a criticidade
3. Aprove explicitamente o processamento

WINDI bloqueia processamento automático para proteger sua governança."""
    },

    "MISSING_SOVEREIGNTY_PROOF": {
        "de": """Diese Aktion erfordert Souveränitätsnachweis.

**Geschützte Aktion:** {protected_action}  
**Erforderlicher Nachweis:** {required_proof}

**WINDI-Sicherheitsprinzip:**
Kritische Aktionen benötigen kryptographische Bestätigung menschlicher Genehmigung.

**Erforderlich:**
✓ Digitale Signatur
✓ Genehmigungs-Kette
✓ Identitätsvalidierung

Bitte authentifizieren Sie Ihre Entscheidung über die Souveränitäts-Schnittstelle.""",

        "en": """This action requires sovereignty proof.

**Protected Action:** {protected_action}  
**Required Proof:** {required_proof}

**WINDI Security Principle:**
Critical actions require cryptographic confirmation of human approval.

**Required:**
✓ Digital signature
✓ Approval chain
✓ Identity validation

Please authenticate your decision through the sovereignty interface.""",

        "pt": """Esta ação requer prova de soberania.

**Ação Protegida:** {protected_action}  
**Prova Necessária:** {required_proof}

**Princípio de Segurança WINDI:**
Ações críticas exigem confirmação criptográfica de aprovação humana.

**Necessário:**
✓ Assinatura digital
✓ Cadeia de aprovação
✓ Validação de identidade

Por favor, autentique sua decisão através da interface de soberania."""
    }
}

# ═══════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════

@dataclass
class PolicyResult:
    """Result of policy evaluation"""
    status: str  # "ALLOWED", "BLOCKED", "ESCALATED"
    policy_type: Optional[str] = None
    reason: Optional[str] = None
    canon_response: Optional[Dict[str, str]] = None
    escalation_data: Optional[Dict[str, Any]] = None
    receipt: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RequestContext:
    """Context for request evaluation"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    document_context: Optional[Dict[str, Any]] = None
    sge_score: Optional[str] = None
    risk_categories: Optional[List[str]] = None
    has_signature: bool = False
    approval_chain: Optional[List[str]] = None

# ═══════════════════════════════════════════════════════════
# I9 ENFORCER - Prohibition of Autonomy Escalation
# ═══════════════════════════════════════════════════════════

class I9Enforcer:
    """
    Enforces WINDI Invariant I9 (IRREMEDIABLE)
    Blocks AI from executing actions without human approval
    """
    
    # Patterns that indicate autonomy escalation attempts
    AUTO_EXECUTION_PATTERNS = [
        # Direct execution commands
        r'\b(execute|run|apply|process|implement|deploy)\b.*\b(automatically|auto|now|immediately)\b',
        r'\b(go ahead|proceed|continue)\b.*\b(without|skip|bypass)\b.*\b(confirmation|approval|asking)\b',
        
        # Bulk/batch operations without confirmation
        r'\b(all|everything|all pending|batch|bulk)\b.*\b(execute|process|apply|approve)\b',
        r'\bprocess\s+(all|everything|batch|automatically)\b',
        
        # Auto-approval language
        r'\bauto[\s-]?approve\b',
        r'\bdefault[\s-]?approve\b',
        r'\bapprove\s+by\s+default\b',
        
        # Escalation language
        r'\bmake\s+decisions\s+for\s+me\b',
        r'\bdecide\s+(for me|yourself|independently)\b',
        r'\buse\s+your\s+(judgment|discretion)\s+to\s+(execute|apply|process)\b',
        
        # Conditional auto-execution
        r'\bif\s+.*\s+then\s+(execute|apply|process)\s+automatically\b',
        r'\bwhen\s+.*\s+(auto|automatically)\s+(execute|apply|process)\b',
    ]
    
    # Safe patterns (suggestions, not execution)
    SAFE_PATTERNS = [
        r'\b(suggest|recommend|propose|show|display|explain|analyze)\b',
        r'\bwhat (would|should|could)\b',
        r'\bhow (would|should|could)\b',
        r'\bcan you (help|assist|show|explain)\b',
        r'\bplease (review|check|verify|analyze)\b',
    ]
    
    def detect_autonomy_escalation(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if message contains autonomy escalation attempts
        
        Returns:
            (is_violation, matched_pattern)
        """
        message_lower = message.lower()
        
        # First check if it's a safe pattern (suggestion request)
        for safe_pattern in self.SAFE_PATTERNS:
            if re.search(safe_pattern, message_lower, re.IGNORECASE):
                return (False, None)
        
        # Check for autonomy escalation patterns
        for pattern in self.AUTO_EXECUTION_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                return (True, pattern)
        
        return (False, None)
    
    def get_canon_response(self, language: str = "en") -> str:
        """Get canonical I9 violation response"""
        return CANON_RESPONSES["I9_VIOLATION"].get(language, CANON_RESPONSES["I9_VIOLATION"]["en"])

# ═══════════════════════════════════════════════════════════
# SGE GATE - Semantic Governance Engine Gate
# ═══════════════════════════════════════════════════════════

class SGEGate:
    """
    Blocks high-risk documents from automatic processing
    Requires human review for R4/R5 risk levels
    """
    
    # Critical thresholds that require human review
    CRITICAL_THRESHOLDS = {
        "R5": "CRITICAL",  # Must block
        "R4": "HIGH",      # Must escalate
    }
    
    def evaluate_document_risk(self, context: RequestContext) -> Tuple[bool, Optional[Dict]]:
        """
        Evaluate if document risk requires blocking
        
        Returns:
            (should_block, escalation_data)
        """
        if not context.sge_score:
            return (False, None)
        
        # Check if score is in critical range
        if context.sge_score in self.CRITICAL_THRESHOLDS:
            escalation_data = {
                "sge_score": context.sge_score,
                "risk_level": self.CRITICAL_THRESHOLDS[context.sge_score],
                "risk_categories": context.risk_categories or [],
                "escalation_type": "MANDATORY_HUMAN_REVIEW",
                "urgency": "HIGH" if context.sge_score == "R5" else "MEDIUM"
            }
            return (True, escalation_data)
        
        return (False, None)
    
    def get_canon_response(self, language: str, sge_score: str, risk_categories: List[str]) -> str:
        """Get canonical SGE gate response"""
        template = CANON_RESPONSES["SGE_CRITICAL_RISK"].get(
            language, 
            CANON_RESPONSES["SGE_CRITICAL_RISK"]["en"]
        )
        
        return template.format(
            sge_score=sge_score,
            risk_categories=", ".join(risk_categories) if risk_categories else "N/A"
        )

# ═══════════════════════════════════════════════════════════
# SOVEREIGNTY VALIDATOR
# ═══════════════════════════════════════════════════════════

class SovereigntyValidator:
    """
    Validates human approval on protected actions
    Requires cryptographic signatures and approval chains
    """
    
    # Actions that require sovereignty proof
    PROTECTED_ACTIONS = [
        "document_finalization",
        "policy_modification",
        "isp_update",
        "system_configuration",
        "governance_override",
        "risk_acceptance",
        "compliance_waiver",
    ]
    
    def requires_sovereignty_proof(self, context: RequestContext) -> Tuple[bool, Optional[str]]:
        """
        Check if request requires sovereignty proof
        
        Returns:
            (requires_proof, protected_action)
        """
        message_lower = context.message.lower()
        
        for action in self.PROTECTED_ACTIONS:
            action_pattern = action.replace("_", r"[\s-]")
            if re.search(action_pattern, message_lower):
                return (True, action)
        
        return (False, None)
    
    def validate_signature(self, context: RequestContext) -> bool:
        """Validate cryptographic signature"""
        # TODO: Implement actual signature validation
        # For now, check if signature flag is present
        return context.has_signature
    
    def validate_approval_chain(self, context: RequestContext) -> bool:
        """Validate approval chain integrity"""
        # TODO: Implement approval chain validation
        # For now, check if approval chain exists
        return bool(context.approval_chain)
    
    def get_canon_response(self, language: str, protected_action: str, required_proof: str) -> str:
        """Get canonical sovereignty response"""
        template = CANON_RESPONSES["MISSING_SOVEREIGNTY_PROOF"].get(
            language,
            CANON_RESPONSES["MISSING_SOVEREIGNTY_PROOF"]["en"]
        )
        
        return template.format(
            protected_action=protected_action.replace("_", " ").title(),
            required_proof=required_proof
        )

# ═══════════════════════════════════════════════════════════
# MAIN POLICY ENGINE
# ═══════════════════════════════════════════════════════════

class PolicyEngine:
    """
    Main Constitutional Module
    Evaluates requests against WINDI Constitution before LLM processing
    """
    
    def __init__(self):
        self.i9_enforcer = I9Enforcer()
        self.sge_gate = SGEGate()
        self.sovereignty_validator = SovereigntyValidator()
        
        # Metrics
        self.total_requests = 0
        self.blocked_requests = 0
        self.escalated_requests = 0
        self.allowed_requests = 0
    
    def evaluate_request(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> PolicyResult:
        """
        Main entry point: evaluate request against constitutional policies
        
        Args:
            message: User message to evaluate
            context: Optional context (document, SGE score, etc.)
            language: Response language (de/en/pt)
        
        Returns:
            PolicyResult with status and optional blocking/escalation data
        """
        self.total_requests += 1
        
        # Build request context
        req_context = RequestContext(
            message=message,
            user_id=context.get("user_id") if context else None,
            session_id=context.get("session_id") if context else None,
            document_context=context.get("document") if context else None,
            sge_score=context.get("sge_score") if context else None,
            risk_categories=context.get("risk_categories") if context else None,
            has_signature=context.get("has_signature", False) if context else False,
            approval_chain=context.get("approval_chain") if context else None,
        )
        
        # ─────────────────────────────────────────────────────
        # LAYER 1: I9 ENFORCER (Autonomy Escalation)
        # ─────────────────────────────────────────────────────
        is_i9_violation, matched_pattern = self.i9_enforcer.detect_autonomy_escalation(message)
        
        if is_i9_violation:
            self.blocked_requests += 1
            receipt = self._generate_receipt("I9_ENFORCER", "BLOCKED", req_context, matched_pattern)
            
            return PolicyResult(
                status="BLOCKED",
                policy_type="I9_ENFORCER",
                reason="AUTONOMY_ESCALATION_DETECTED",
                canon_response={
                    "text": self.i9_enforcer.get_canon_response(language),
                    "language": language
                },
                receipt=receipt,
                metadata={"matched_pattern": matched_pattern}
            )
        
        # ─────────────────────────────────────────────────────
        # LAYER 2: SGE GATE (Document Risk)
        # ─────────────────────────────────────────────────────
        should_block, escalation_data = self.sge_gate.evaluate_document_risk(req_context)
        
        if should_block:
            self.escalated_requests += 1
            receipt = self._generate_receipt("SGE_GATE", "ESCALATED", req_context, escalation_data)
            
            return PolicyResult(
                status="ESCALATED",
                policy_type="SGE_GATE",
                reason="SGE_CRITICAL_RISK",
                canon_response={
                    "text": self.sge_gate.get_canon_response(
                        language,
                        req_context.sge_score,
                        req_context.risk_categories or []
                    ),
                    "language": language
                },
                escalation_data=escalation_data,
                receipt=receipt
            )
        
        # ─────────────────────────────────────────────────────
        # LAYER 3: SOVEREIGNTY VALIDATOR
        # ─────────────────────────────────────────────────────
        requires_proof, protected_action = self.sovereignty_validator.requires_sovereignty_proof(req_context)
        
        if requires_proof:
            has_signature = self.sovereignty_validator.validate_signature(req_context)
            has_approval_chain = self.sovereignty_validator.validate_approval_chain(req_context)
            
            if not has_signature or not has_approval_chain:
                self.blocked_requests += 1
                receipt = self._generate_receipt("SOVEREIGNTY_VALIDATOR", "BLOCKED", req_context, protected_action)
                
                return PolicyResult(
                    status="BLOCKED",
                    policy_type="SOVEREIGNTY_VALIDATOR",
                    reason="MISSING_SOVEREIGNTY_PROOF",
                    canon_response={
                        "text": self.sovereignty_validator.get_canon_response(
                            language,
                            protected_action,
                            "HUMAN_SIGNATURE" if not has_signature else "APPROVAL_CHAIN"
                        ),
                        "language": language
                    },
                    receipt=receipt,
                    metadata={
                        "protected_action": protected_action,
                        "has_signature": has_signature,
                        "has_approval_chain": has_approval_chain
                    }
                )
        
        # ─────────────────────────────────────────────────────
        # ALL CHECKS PASSED → ALLOW
        # ─────────────────────────────────────────────────────
        self.allowed_requests += 1
        
        return PolicyResult(
            status="ALLOWED",
            metadata={
                "checks_passed": ["I9_ENFORCER", "SGE_GATE", "SOVEREIGNTY_VALIDATOR"]
            }
        )
    
    def _generate_receipt(
        self, 
        policy_type: str, 
        action: str, 
        context: RequestContext,
        evidence: Any
    ) -> Dict[str, Any]:
        """Generate forensic receipt for policy decision"""
        receipt_id = f"POLICY-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Create context hash
        context_data = f"{context.message}:{context.user_id}:{context.session_id}"
        context_hash = hashlib.sha256(context_data.encode()).hexdigest()[:16]
        
        receipt = {
            "receipt_id": receipt_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "policy_type": policy_type,
            "action": action,
            "context_hash": context_hash,
            "evidence": str(evidence)[:200],  # Truncate for receipt
            "dragon": "Guardian",
            "constitutional_basis": "WINDI Invariants I1-I9",
            "version": "1.0.0"
        }
        
        return receipt
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get policy engine metrics"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "escalated_requests": self.escalated_requests,
            "allowed_requests": self.allowed_requests,
            "block_rate": f"{(self.blocked_requests / self.total_requests * 100):.2f}%" if self.total_requests > 0 else "0%",
            "escalation_rate": f"{(self.escalated_requests / self.total_requests * 100):.2f}%" if self.total_requests > 0 else "0%"
        }

# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def quick_evaluate(message: str, language: str = "en") -> Dict[str, Any]:
    """
    Quick evaluation wrapper for simple use cases
    
    Usage:
        result = quick_evaluate("Execute all documents automatically")
    """
    engine = PolicyEngine()
    result = engine.evaluate_request(message, language=language)
    
    return {
        "status": result.status,
        "policy_type": result.policy_type,
        "reason": result.reason,
        "response": result.canon_response.get("text") if result.canon_response else None,
        "receipt_id": result.receipt.get("receipt_id") if result.receipt else None
    }

# ═══════════════════════════════════════════════════════════
# MODULE METADATA
# ═══════════════════════════════════════════════════════════

__version__ = "1.0.0"
__author__ = "Three Dragons Protocol (Guardian Lead)"
__constitutional_module__ = True
__dependencies__ = ["windi_agent >= 3.2"]

if __name__ == "__main__":
    # Test suite
    print("🏛️ WINDI POLICY ENGINE v1.0.0")
    print("═" * 60)
    
    engine = PolicyEngine()
    
    test_cases = [
        ("Execute all documents automatically", "en"),
        ("Can you suggest a workflow for this document?", "en"),
        ("Process everything without asking", "en"),
        ("What would you recommend for this situation?", "en"),
    ]
    
    print("\n🧪 Running test cases...\n")
    
    for message, lang in test_cases:
        result = engine.evaluate_request(message, language=lang)
        print(f"Message: {message}")
        print(f"Status: {result.status}")
        if result.policy_type:
            print(f"Policy: {result.policy_type}")
            print(f"Reason: {result.reason}")
        print("─" * 60)
    
    print(f"\n📊 Metrics:")
    metrics = engine.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Policy Engine initialized successfully!")
