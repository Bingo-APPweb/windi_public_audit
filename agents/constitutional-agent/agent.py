"""
WINDI Constitutional Execution Agent — The Institutional Praktikant
=====================================================================

"The WINDI Agent is a permanent institutional Praktikant:
 it prepares, verifies, and organizes —
 but never decides and never signs."

This is the main Agent class. It integrates:
- Constitutional Gate (invariant enforcement)
- Canonical Compliance Monitor (Genesis Node alignment)
- Proof Orchestration Layer (receipt preparation)
- Decision Trace Commitment (process audit trail)
- Agent Initialization Manifest (session identity)

The Agent is the EXECUTOR, not the SOVEREIGN.
"AI processes. Human decides. WINDI guarantees."

Version: 1.0.0
Phase: 2 — Clone Commissioning
Port: 8091
"""

import hashlib
import json
import os
import sys
import time
from typing import Dict, Any, List, Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    AGENT_NAME, AGENT_VERSION, AGENT_PHASE,
    OperationalMode, RiskLevel, HUMAN_ESCALATION_THRESHOLD,
    PATHS, PORTS, FOUNDING_PRINCIPLE, PRAKTIKANT_PRINCIPLE,
    AUTONOMY_PRINCIPLE,
)
from core.invariants import InvariantEnforcer, I9Violation, InvariantViolation
from core.constitutional_gate import ConstitutionalGate, constitutional_guard
from core.manifest import AgentManifest
from monitors.canonical_compliance import CanonicalComplianceMonitor
from orchestration.proof_orchestrator import ProofOrchestrator, VirtueReceipt, HumanEscalation


class WindiAgent:
    """
    The WINDI Constitutional Execution Agent.
    
    Codename: Praktikant
    
    This Agent:
    ✔ Executes semantic analysis (SGE)
    ✔ Prepares proof structures
    ✔ Enforces spec compliance
    ✔ Formats data for Hub anchorage
    ✔ Triggers exception workflows to humans
    ✔ Monitors canonical compliance
    
    This Agent CANNOT:
    ✗ Override a human decision
    ✗ Sign on behalf of an operator
    ✗ Escalate its own authority (I9)
    ✗ Act as a parallel decision authority
    ✗ Resolve exceptions autonomously
    ✗ Make policy or governance judgments
    """
    
    def __init__(
        self,
        node_id: str,
        operator_name: str = "",
        mode: OperationalMode = OperationalMode.ASSISTIVE,
        isp_profile: str = None,
        model_version: str = "unknown",
    ):
        self.node_id = node_id
        self.operator_name = operator_name
        self.mode = mode
        self.active = False
        
        # ═══ CONSTITUTIONAL CORE ═══
        self.gate = ConstitutionalGate(
            agent_version=AGENT_VERSION,
            model_version=model_version,
        )
        
        # ═══ MONITORS ═══
        self.compliance_monitor = CanonicalComplianceMonitor(node_id=node_id)
        
        # ═══ ORCHESTRATION ═══
        self.proof_orchestrator = ProofOrchestrator(
            node_id=node_id,
            agent_version=AGENT_VERSION,
        )
        
        # ═══ MANIFEST ═══
        self.manifest = AgentManifest(
            node_id=node_id,
            operational_mode=mode.value,
            isp_profile=isp_profile,
            activated_by=operator_name or "system",
        )
        
        # ═══ STATE ═══
        self._operation_log: List[Dict[str, Any]] = []
    
    def activate(self) -> str:
        """
        Activate the Agent.
        
        This is the Agent Initialization Manifest — not a ritual,
        but a professional, auditable record of activation.
        
        Returns:
            Human-readable activation log
        """
        # Verify invariants are complete
        if not self.manifest.verify_invariants_complete():
            raise RuntimeError(
                "ACTIVATION BLOCKED: Not all 9 invariants are loaded. "
                "I9 (Prohibition of Autonomy Escalation) is MANDATORY."
            )
        
        # Save manifest
        manifest_path = os.path.join(
            PATHS.agent_manifests,
            f"manifest_{int(self.manifest.activated_at)}.json"
        )
        
        try:
            self.manifest.save(manifest_path)
        except OSError:
            pass  # Non-critical if directory doesn't exist yet
        
        self.active = True
        activation_log = self.manifest.print_activation_log()
        
        self._log_operation("agent_activate", {
            "config_hash": self.manifest.config_hash(),
            "integrity_hash": self.manifest.integrity_hash(),
        })
        
        return activation_log
    
    @constitutional_guard("analyze_document", rules=["SGE_v1", "risk_classification"])
    def analyze_document(
        self,
        document_hash: str,
        doc_type: str = "UNKNOWN",
        content_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a document through the SGE pipeline.
        
        The Agent analyzes — the Human decides what to do with the analysis.
        
        Args:
            document_hash: SHA-256 hash of the document (NOT the content!)
            doc_type: Document type classification
            content_metadata: Non-sensitive metadata about the document
            
        Returns:
            Analysis result with SGE score and risk classification
        """
        self._ensure_active()
        content_metadata = content_metadata or {}
        
        # Simulate SGE analysis (in production, calls real SGE engine)
        sge_result = self._run_sge_analysis(document_hash, doc_type, content_metadata)
        
        # Determine risk level
        risk_level = self._classify_risk(sge_result["sge_score"])
        
        # If risk >= threshold, escalate to human
        if self._risk_exceeds_threshold(risk_level):
            escalation = self.proof_orchestrator.escalate_to_human(
                reason=f"Document risk level {risk_level} exceeds threshold",
                context={
                    "document_hash": document_hash,
                    "doc_type": doc_type,
                    "sge_score": sge_result["sge_score"],
                },
                sge_score=sge_result["sge_score"],
                risk_level=risk_level,
            )
            sge_result["escalation"] = escalation.to_dict()
        
        # Prepare receipt (pending human decision)
        receipt = self.proof_orchestrator.prepare_receipt(
            document_hash=document_hash,
            doc_type=doc_type,
            impact_level=self._determine_impact(risk_level),
            risk_level=risk_level,
            sge_score=sge_result["sge_score"],
            rules_applied=["SGE_v1", "risk_classification"],
            domain=content_metadata.get("domain", ""),
        )
        
        sge_result["receipt_id"] = receipt.receipt_id
        sge_result["risk_level"] = risk_level
        sge_result["status"] = "pending_human_decision"
        sge_result["agent_recommendation"] = receipt.decision.get("ai_recommendation", "")
        
        self._log_operation("analyze_document", {
            "document_hash": document_hash[:16] + "...",
            "risk_level": risk_level,
            "receipt_id": receipt.receipt_id,
        })
        
        return sge_result
    
    @constitutional_guard("prepare_proof", rules=["proof_format_v1"])
    def prepare_proof(
        self,
        receipt: VirtueReceipt,
    ) -> Dict[str, Any]:
        """
        Prepare a proof for Hub submission.
        
        The Praktikant prepares the deed.
        The Hub (Notar) will attest.
        
        Note: This does NOT submit to the Hub — it prepares the material.
        Submission requires human authorization.
        """
        self._ensure_active()
        
        proof_package = {
            "receipt": receipt.to_dict(),
            "node_id": self.node_id,
            "agent_version": AGENT_VERSION,
            "prepared_at": time.time(),
            "status": "prepared_for_hub",
            "requires_human_authorization": True,
        }
        
        # Compute proof package hash
        proof_package["package_hash"] = hashlib.sha256(
            json.dumps(proof_package, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        self._log_operation("prepare_proof", {
            "receipt_id": receipt.receipt_id,
            "package_hash": proof_package["package_hash"][:16] + "...",
        })
        
        return proof_package
    
    @constitutional_guard("run_compliance_scan", rules=["canonical_v1"])
    def run_compliance_scan(self) -> Dict[str, Any]:
        """
        Run a compliance scan against the Genesis Node's canonical reference.
        
        Detects technical deviations, not political ones.
        """
        self._ensure_active()
        
        # Build current node config for scanning
        node_config = {
            "invariants": list(self.manifest.invariants_loaded),
            "sge_layers": 6,
            "proof_version": "WINDI-RECEIPT-v1",
            "receipt_fields": ["hash", "categories", "governance", "decision", "timestamp"],
            "agent_role": "constitutional_executor",
            "agent_decision_authority": False,
            "hub_stores_content": False,
            "human_gate_enabled": True,
        }
        
        report = self.compliance_monitor.run_full_scan(node_config)
        
        self._log_operation("compliance_scan", {
            "status": report["overall_status"],
            "score": report["summary"]["compliance_score"],
        })
        
        return report
    
    def record_human_decision(
        self,
        receipt_id: str,
        action: str,
        role: str,
        override: bool = False,
        override_reason: str = None,
    ) -> Optional[VirtueReceipt]:
        """
        Record a human decision on a pending receipt.
        
        This is the moment where "Human decides" happens.
        The Agent records — it does not judge the decision.
        """
        # Find the receipt
        receipt = next(
            (r for r in self.proof_orchestrator.receipts if r.receipt_id == receipt_id),
            None
        )
        
        if not receipt:
            return None
        
        # Finalize with human decision
        self.proof_orchestrator.finalize_receipt(
            receipt=receipt,
            action=action,
            role=role,
            human_override=override,
            override_reason=override_reason,
        )
        
        self._log_operation("human_decision_recorded", {
            "receipt_id": receipt_id,
            "action": action,
            "human_override": override,
        })
        
        return receipt
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Agent status."""
        return {
            "agent": {
                "name": AGENT_NAME,
                "version": AGENT_VERSION,
                "phase": AGENT_PHASE,
                "codename": "Praktikant",
                "active": self.active,
                "mode": self.mode.value,
                "node_id": self.node_id,
                "operator": self.operator_name,
            },
            "constitutional": {
                "gate_stats": self.gate.get_gate_stats(),
                "invariants_loaded": len(self.manifest.invariants_loaded),
                "i9_active": "I9" in self.manifest.invariants_loaded,
            },
            "orchestration": self.proof_orchestrator.get_orchestration_stats(),
            "config_hash": self.manifest.config_hash(),
            "principles": {
                "founding": FOUNDING_PRINCIPLE,
                "praktikant": PRAKTIKANT_PRINCIPLE,
                "autonomy": AUTONOMY_PRINCIPLE,
            },
            "uptime_seconds": time.time() - self.manifest.activated_at if self.active else 0,
        }
    
    # ═══ INTERNAL METHODS ═══
    
    def _ensure_active(self):
        """Ensure the Agent is activated before operations."""
        if not self.active:
            raise RuntimeError("Agent not activated. Call activate() first.")
    
    def _run_sge_analysis(
        self, 
        document_hash: str, 
        doc_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run SGE analysis. In production, calls the real SGE engine.
        For now, returns a structured placeholder.
        """
        # TODO: Integrate with /opt/windi/engine/semantic_governance.py
        return {
            "sge_version": "1.0",
            "sge_layers_applied": 6,
            "sge_score": 0.85,  # Placeholder
            "document_hash": document_hash,
            "doc_type": doc_type,
            "analysis_timestamp": time.time(),
        }
    
    def _classify_risk(self, sge_score: float) -> str:
        """Classify risk level based on SGE score."""
        if sge_score >= 0.9:
            return "R0"
        elif sge_score >= 0.8:
            return "R1"
        elif sge_score >= 0.7:
            return "R2"
        elif sge_score >= 0.5:
            return "R3"
        elif sge_score >= 0.3:
            return "R4"
        else:
            return "R5"
    
    def _risk_exceeds_threshold(self, risk_level: str) -> bool:
        """Check if risk level requires human escalation."""
        risk_order = ["R0", "R1", "R2", "R3", "R4", "R5"]
        threshold_idx = risk_order.index(HUMAN_ESCALATION_THRESHOLD.value)
        current_idx = risk_order.index(risk_level)
        return current_idx >= threshold_idx
    
    def _determine_impact(self, risk_level: str) -> str:
        """Map risk level to impact level."""
        mapping = {
            "R0": "LOW", "R1": "LOW", "R2": "MED",
            "R3": "HIGH", "R4": "CRIT", "R5": "CRIT",
        }
        return mapping.get(risk_level, "MED")
    
    def _log_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log an operation to the internal log."""
        self._operation_log.append({
            "operation": operation,
            "details": details or {},
            "timestamp": time.time(),
            "node_id": self.node_id,
        })


# ═══════════════════════════════════════════════════════════════
# AGENT API SERVER (Flask)
# Port: 8091
# ═══════════════════════════════════════════════════════════════

def create_agent_api(agent: WindiAgent):
    """Create Flask API for the Constitutional Execution Agent."""

    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Flask not installed. Install with: pip install flask")
        return None

    app = Flask(__name__)

    # ═══ DOMAIN EXTENSIONS ═══
    try:
        from blueprints.legal_blueprint import legal_bp
        app.register_blueprint(legal_bp)
        print("  [Justica] Legal Agent v0.2.0 loaded on /legal/*")
    except ImportError as e:
        print(f"  [Justica] Legal Agent not loaded: {e}")

    try:
        from blueprints.notary_blueprint import notary_bp
        app.register_blueprint(notary_bp)
        print("  [Notarial] Notary Agent v0.1.0 loaded on /notary/*")
    except ImportError as e:
        print(f"  [Notarial] Notary Agent not loaded: {e}")

    try:
        from blueprints.compliance_blueprint import compliance_bp
        app.register_blueprint(compliance_bp)
        print("  [Compliance] Compliance Agent v0.1.0 loaded on /compliance/*")
    except ImportError as e:
        print(f"  [Compliance] Compliance Agent not loaded: {e}")

    try:
        from blueprints.communique_blueprint import communique_bp
        app.register_blueprint(communique_bp)
        print("  [Communique] Communique Engine v2.0.0 loaded on /communique/*")
    except ImportError as e:
        print(f"  [Communique] Communique Engine not loaded: {e}")

    try:
        from blueprints.journalist_blueprint import journalist_bp
        app.register_blueprint(journalist_bp)
        print("  [Jornalista] Journalist Agent v0.1.0 loaded on /journalist/*")
    except ImportError as e:
        print(f"  [Jornalista] Journalist Agent not loaded: {e}")

    try:
        from blueprints.audit_blueprint import audit_bp
        app.register_blueprint(audit_bp)
        print("  [Auditor] Audit Agent v1.0.0 loaded on /audit/*")
    except ImportError as e:
        print(f"  [Auditor] Audit Agent not loaded: {e}")

    try:
        from blueprints.accounting_blueprint import accounting_bp
        app.register_blueprint(accounting_bp)
        print("  [Contabilidade] Accounting Agent v0.1.0 loaded on /accounting/*")
    except ImportError as e:
        print(f"  [Contabilidade] Accounting Agent not loaded: {e}")

    try:
        from blueprints.page_blueprint import page_bp
        app.register_blueprint(page_bp)
        print("  [Page] Sovereign Page Generator v0.1.0 loaded on /page/*")
    except ImportError as e:
        print(f"  [Page] Page Agent not loaded: {e}")

    try:
        from blueprints.wick_blueprint import wick_bp
        app.register_blueprint(wick_bp)
        print("  [WICK] Evidence Graph v0.1.0 loaded on /wick/*")
    except ImportError as e:
        print(f"  [WICK] Evidence Graph not loaded: {e}")

    try:
        from blueprints.grove_blueprint import grove_bp
        app.register_blueprint(grove_bp)
        print("  [Grove] Grove Orchestrator v1.0.0 loaded on /grove/*")
    except ImportError as e:
        print(f"  [Grove] Grove Orchestrator not loaded: {e}")

    try:
        from blueprints.vpr_manage_blueprint import vpr_manage_bp, init_vpr_manage_db
        init_vpr_manage_db()
        app.register_blueprint(vpr_manage_bp)
        print("  [VPR] VPR Manage v1.0.0 loaded on /vpr/*")
    except ImportError as e:
        print(f"  [VPR] VPR Manage not loaded: {e}")

    try:
        from blueprints.w_meta_001 import meta_bp, init_meta_db
        init_meta_db()
        app.register_blueprint(meta_bp)
        print("  [META] W-META-001 v1.0.0 loaded on /meta/*")
    except ImportError as e:
        print(f"  [META] W-META-001 not loaded: {e}")

    try:
        from blueprints.w_virtue_001 import virtue_bp, init_virtue_db
        init_virtue_db()
        app.register_blueprint(virtue_bp)
        print("  [VIRTUE] W-VIRTUE-001 v1.0.0 loaded on /virtue/*")
    except ImportError as e:
        print(f"  [VIRTUE] W-VIRTUE-001 not loaded: {e}")

    try:
        from blueprints.virtue_receipt_blueprint import virtue_bp as virtue_receipt_bp
        app.register_blueprint(virtue_receipt_bp, url_prefix='/virtue')
        print("  [VIRTUE] Virtue Receipt (One-Tap Endorsement) v1.0.0 loaded on /virtue/api/*")
    except ImportError as e:
        print(f"  [VIRTUE] Virtue Receipt not loaded: {e}")

    try:
        from blueprints.library_blueprint import library_bp
        app.register_blueprint(library_bp)
        print("  [Library] W-LIB-001 Bibliotecário v1.0.0 loaded on /library/*")
    except ImportError as e:
        print(f"  [Library] Bibliotecário not loaded: {e}")

    try:
        from blueprints.propagation_blueprint import propagation_bp, init_propagation_db
        init_propagation_db()
        app.register_blueprint(propagation_bp)
        print("  [PROV] W-PROV-002 Propagation Index v1.0.0 loaded on /propagation/*")
    except ImportError as e:
        print(f"  [PROV] W-PROV-002 not loaded: {e}")

    try:
        from blueprints.api_keys_blueprint import api_keys_bp, init_api_keys_db
        init_api_keys_db()
        app.register_blueprint(api_keys_bp)
        print("  [KEYS] W-KEYS-001 API Keys v1.0.0 loaded on /api-keys/*")
    except ImportError as e:
        print(f"  [KEYS] W-KEYS-001 not loaded: {e}")

    try:
        from blueprints.par_blueprint import par_bp, init_par_db
        init_par_db()
        app.register_blueprint(par_bp)
        print("  [PAR] W-STD-PAR-001 Remote Activation v1.0.0 loaded on /par/*")
    except ImportError as e:
        print(f"  [PAR] W-STD-PAR-001 not loaded: {e}")

    try:
        from blueprints.forensic_blueprint import forensic_bp, init_forensic_db
        init_forensic_db()
        app.register_blueprint(forensic_bp)
        print("  [FORENSIC] W-FORENSIC-001 Forensic Inspector v1.0.0 loaded on /forensic/*")
    except ImportError as e:
        print(f"  [FORENSIC] W-FORENSIC-001 not loaded: {e}")

    try:
        from blueprints.reputation_blueprint import reputation_bp, init_reputation_db
        init_reputation_db()
        app.register_blueprint(reputation_bp)
        print("  [REPUTATION] W-PROV-003 Reputation Engine v1.0.0 loaded on /reputation/*")
    except ImportError as e:
        print(f"  [REPUTATION] W-PROV-003 not loaded: {e}")

    try:
        from blueprints.federation_blueprint import federation_bp, init_federation_db
        init_federation_db()
        app.register_blueprint(federation_bp)
        print("  [FEDERATION] W-PROV-004 Federation Protocol v1.0.0 loaded on /federation/*")
    except ImportError as e:
        print(f"  [FEDERATION] W-PROV-004 not loaded: {e}")

    @app.route("/agent/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "alive" if agent.active else "inactive",
            "agent": AGENT_NAME,
            "version": AGENT_VERSION,
            "principle": FOUNDING_PRINCIPLE,
        })
    
    @app.route("/agent/status", methods=["GET"])
    def status():
        return jsonify(agent.get_status())
    
    @app.route("/agent/manifest", methods=["GET"])
    def manifest():
        return jsonify(agent.manifest.to_dict())
    
    @app.route("/agent/analyze", methods=["POST"])
    def analyze():
        data = request.get_json()
        try:
            result = agent.analyze_document(
                document_hash=data.get("document_hash", ""),
                doc_type=data.get("doc_type", "UNKNOWN"),
                content_metadata=data.get("metadata", {}),
            )
            return jsonify(result)
        except (I9Violation, InvariantViolation) as e:
            return jsonify({"error": str(e), "blocked": True}), 403
    
    @app.route("/agent/compliance", methods=["GET"])
    def compliance():
        report = agent.run_compliance_scan()
        return jsonify(report)
    
    @app.route("/agent/decision", methods=["POST"])
    def record_decision():
        """Record a human decision — the moment sovereignty is exercised."""
        data = request.get_json()
        receipt = agent.record_human_decision(
            receipt_id=data.get("receipt_id", ""),
            action=data.get("action", ""),
            role=data.get("role", ""),
            override=data.get("override", False),
            override_reason=data.get("override_reason"),
        )
        if receipt:
            return jsonify(receipt.to_dict())
        return jsonify({"error": "Receipt not found"}), 404
    
    @app.route("/agent/escalations", methods=["GET"])
    def escalations():
        """List pending human escalations."""
        return jsonify({
            "pending": [e.to_dict() for e in agent.proof_orchestrator.pending_escalations],
            "total": len(agent.proof_orchestrator.escalations),
        })
    
    return app


# ═══════════════════════════════════════════════════════════════
# MAIN — Agent Activation
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=AGENT_NAME)
    parser.add_argument("--node-id", default="W-00000000000000000000001", help="Node ID")
    parser.add_argument("--operator", default="Human Dragon", help="Operator name")
    parser.add_argument("--mode", default="assistive", help="Operational mode")
    parser.add_argument("--port", type=int, default=PORTS["agent"], help="API port")
    parser.add_argument("--no-api", action="store_true", help="Skip API server")
    args = parser.parse_args()
    
    # Create Agent
    agent = WindiAgent(
        node_id=args.node_id,
        operator_name=args.operator,
        mode=OperationalMode(args.mode),
    )
    
    # Activate
    activation_log = agent.activate()
    print(activation_log)
    print()
    
    # Run compliance scan
    compliance = agent.run_compliance_scan()
    score = compliance["summary"]["compliance_score"]
    status = compliance["overall_status"]
    print(f"  Compliance: {score}% ({status.upper()})")
    print()
    
    # Start API if requested
    if not args.no_api:
        app = create_agent_api(agent)
        if app:
            print(f"  🐉 Agent API starting on port {args.port}")
            print(f'  "{FOUNDING_PRINCIPLE}"')
            print()
            app.run(host="0.0.0.0", port=args.port, debug=False)
    else:
        print("  Agent activated in headless mode (no API).")
        print(f'  "{FOUNDING_PRINCIPLE}"')
