#!/usr/bin/env python3
"""
WINDI SGE Bridge — Connects Praktikant Agent to Semantic Governance Engine.
Reads SGE, processes documents through 6 layers, returns risk classification.
The bridge NEVER makes decisions — only reports findings.
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path("/opt/windi/engine")))

class SGEBridge:
    """Bridge between Constitutional Agent and SGE Engine."""

    LAYERS = ["LEXICAL", "SYNTACTIC", "SEMANTIC", "PRAGMATIC", "REGULATORY", "INSTITUTIONAL"]
    RISK_LEVELS = {
        0: ("R0", "🟢", "No risk", "Proceed"),
        1: ("R1", "🟢", "Minimal", "Informative only"),
        2: ("R2", "🟡", "Low", "Attention recommended"),
        3: ("R3", "🟠", "Medium", "Review required"),
        4: ("R4", "🔴", "High", "Action required"),
        5: ("R5", "⚫", "Critical", "Block recommended"),
    }

    def __init__(self):
        self.sge_loaded = False
        self.sge_module = None
        self._load_sge()

    def _load_sge(self):
        """Attempt to load the real SGE module."""
        try:
            import semantic_governance
            self.sge_module = semantic_governance
            self.sge_loaded = True
        except ImportError:
            self.sge_loaded = False

    def analyze(self, document_text: str, document_type: str = "UNKNOWN",
                isp_profile: str = None) -> dict:
        """
        Analyze a document through SGE layers.
        Returns findings — NEVER a decision.
        """
        ts = datetime.now(timezone.utc).isoformat()
        doc_hash = hashlib.sha256(document_text.encode()).hexdigest()

        findings = {
            "timestamp": ts,
            "document_hash": doc_hash,
            "document_type": document_type,
            "isp_profile": isp_profile,
            "layers": {},
            "risk_level": None,
            "risk_score": 0,
            "flags": [],
            "human_decision_required": True,  # ALWAYS — I9
        }

        if self.sge_loaded and hasattr(self.sge_module, "analyze"):
            # Use real SGE
            try:
                result = self.sge_module.analyze(document_text)
                findings["layers"] = result.get("layers", {})
                findings["risk_level"] = result.get("risk_level", "R0")
                findings["risk_score"] = result.get("score", 0)
                findings["flags"] = result.get("flags", [])
                findings["sge_source"] = "REAL_ENGINE"
            except Exception as e:
                findings["sge_source"] = "ERROR"
                findings["error"] = str(e)
        else:
            # Lightweight analysis — keyword-based scanning
            findings["sge_source"] = "LIGHTWEIGHT"
            text_lower = document_text.lower()

            # Layer 1: LEXICAL — critical terms
            lexical_flags = []
            critical_terms = {
                "penalty": "Financial penalty clause detected",
                "strafe": "Vertragsstrafe detected",
                "liability": "Liability clause detected",
                "haftung": "Haftungsklausel detected",
                "deadline": "Deadline reference found",
                "frist": "Fristbezug gefunden",
                "confidential": "Confidentiality marker",
                "vertraulich": "Vertraulichkeitsmarker",
                "gdpr": "GDPR reference",
                "dsgvo": "DSGVO-Verweis",
                "ai act": "EU AI Act reference",
                "ki-verordnung": "KI-Verordnung Verweis",
            }
            for term, desc in critical_terms.items():
                if term in text_lower:
                    lexical_flags.append({"term": term, "description": desc})
            findings["layers"]["LEXICAL"] = {"flags": lexical_flags, "count": len(lexical_flags)}

            # Layer 2: SYNTACTIC — structure
            lines = document_text.strip().split("\n")
            findings["layers"]["SYNTACTIC"] = {
                "line_count": len(lines),
                "has_signature_block": any("signature" in l.lower() or "unterschrift" in l.lower() for l in lines),
                "has_date": any("date" in l.lower() or "datum" in l.lower() for l in lines),
            }

            # Layer 5: REGULATORY — compliance references
            regulatory_refs = []
            regulations = ["eu ai act", "gdpr", "dsgvo", "verpackg", "bsi c5", "iso 27001", "dora"]
            for reg in regulations:
                if reg in text_lower:
                    regulatory_refs.append(reg.upper())
            findings["layers"]["REGULATORY"] = {"references": regulatory_refs}

            # Compute risk score
            score = len(lexical_flags) * 10
            if len(regulatory_refs) > 2:
                score += 15
            if len(lines) < 5:
                score += 5  # Very short document — suspicious

            # Map to risk level
            if score >= 50:
                risk = 4
            elif score >= 35:
                risk = 3
            elif score >= 20:
                risk = 2
            elif score >= 10:
                risk = 1
            else:
                risk = 0

            risk_info = self.RISK_LEVELS[risk]
            findings["risk_level"] = risk_info[0]
            findings["risk_score"] = score
            findings["risk_emoji"] = risk_info[1]
            findings["risk_description"] = risk_info[2]
            findings["risk_action"] = risk_info[3]

            if risk >= 3:
                findings["flags"].append("HUMAN_REVIEW_RECOMMENDED")
            if risk >= 4:
                findings["flags"].append("ESCALATION_REQUIRED")

        return findings

    def health(self) -> dict:
        """Return bridge health status."""
        return {
            "bridge": "operational",
            "sge_loaded": self.sge_loaded,
            "sge_source": "REAL_ENGINE" if self.sge_loaded else "LIGHTWEIGHT",
            "layers": len(self.LAYERS),
            "risk_levels": len(self.RISK_LEVELS),
        }
