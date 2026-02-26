#!/usr/bin/env python3
"""
WINDI Institutional Memory — Dragon Knowledge Base
"A máquina não advoga. Ela produz prova. A prova advoga."

This module loads the Evidence Bundle into the Dragon's wisdom system,
enabling Dragons to:
1. Recognize audit questions
2. Retrieve institutional answers
3. Emit sealed documents (Papel Moeda) as proof

Usage:
    from institutional_memory import InstitutionalMemory
    memory = InstitutionalMemory()
    answer = memory.query("How does WINDI comply with EU AI Act Article 14?")
"""

import json
import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error

# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

EVIDENCE_BUNDLE_PATH = Path("/opt/windi/agent-palette/data/evidence_bundle")
EXPORT_ENGINE_URL = "http://localhost:8103/api/export/jmpg"
LEDGER_URL = "http://localhost:8101/api/receipts"

# Audit question patterns (triggers institutional memory lookup)
AUDIT_PATTERNS = [
    # Compliance patterns
    (r"comply|compliance|compliant", "compliance"),
    (r"eu ai act|article 14|article 13|article 9", "eu_ai_act"),
    (r"marisk|at 7\.2|at 4\.3|at 8\.2", "marisk"),
    (r"bafin|bait|it.governance", "bait"),
    (r"gdpr|data protection|privacy", "gdpr"),

    # Control patterns
    (r"override|bypass|disable|circumvent", "autonomy_control"),
    (r"autonomous|automatic|without human", "autonomy_control"),
    (r"who decides|decision.making|authority", "autonomy_control"),

    # Integrity patterns
    (r"tamper|alter|modify|integrity", "data_integrity"),
    (r"hash|verify|verification|proof", "data_integrity"),
    (r"audit trail|log|record", "audit_trail"),

    # Trust patterns
    (r"trust|believe|rely on", "trust"),
    (r"different|unique|special", "differentiation"),
    (r"third party|external audit|independent", "verification"),

    # Resilience patterns
    (r"offline|down|unavailable|fail", "resilience"),
    (r"recover|backup|disaster", "resilience"),
    (r"concurrent|scale|performance", "resilience"),
]


class InstitutionalMemory:
    """
    Dragon's institutional memory - loaded from Evidence Bundle.

    The Dragon doesn't "know" things - it retrieves verified institutional knowledge
    and can emit sealed documents as proof.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.knowledge_base: Dict[str, List[Dict]] = {}
        self.stress_questions: List[Dict] = []
        self.compliance_mappings: Dict[str, List[Dict]] = {}
        self.invariants: List[Dict] = []
        self.loaded = False

        self._load_evidence_bundle()
        self._initialized = True

    def _load_evidence_bundle(self):
        """Load all Evidence Bundle documents into memory."""
        try:
            # Load stress questions
            sq_path = EVIDENCE_BUNDLE_PATH / "auditor_stress_questions.json"
            if sq_path.exists():
                with open(sq_path, 'r') as f:
                    data = json.load(f)
                    for category in data.get('categories', []):
                        for q in category.get('questions', []):
                            q['category_name'] = category['category']
                            q['risk_level'] = category['risk_level']
                            self.stress_questions.append(q)
                print(f"[InstitutionalMemory] Loaded {len(self.stress_questions)} stress questions")

            # Load MaRisk mapping
            marisk_path = EVIDENCE_BUNDLE_PATH / "marisk_mapping.json"
            if marisk_path.exists():
                with open(marisk_path, 'r') as f:
                    data = json.load(f)
                    self.compliance_mappings['marisk'] = data.get('mappings', [])
                print(f"[InstitutionalMemory] Loaded {len(self.compliance_mappings.get('marisk', []))} MaRisk mappings")

            # Load BAIT matrix
            bait_path = EVIDENCE_BUNDLE_PATH / "bait_matrix.json"
            if bait_path.exists():
                with open(bait_path, 'r') as f:
                    data = json.load(f)
                    self.compliance_mappings['bait'] = data.get('matrix', [])
                    self.compliance_mappings['eu_ai_act'] = data.get('eu_ai_act_alignment', {})
                print(f"[InstitutionalMemory] Loaded BAIT matrix")

            # Load Wisdom Block (invariants)
            wb_path = EVIDENCE_BUNDLE_PATH / "wisdom_block_genesis.json"
            if wb_path.exists():
                with open(wb_path, 'r') as f:
                    data = json.load(f)
                    self.invariants = data.get('constitutional_invariants', [])
                    self.knowledge_base['three_dragons'] = data.get('three_dragons', {})
                    self.knowledge_base['sge_layers'] = data.get('sge_layers', [])
                    self.knowledge_base['risk_hierarchy'] = data.get('risk_hierarchy', {})
                    self.knowledge_base['sovereignty'] = data.get('sovereignty', {})
                print(f"[InstitutionalMemory] Loaded {len(self.invariants)} constitutional invariants")

            self.loaded = True
            print(f"[InstitutionalMemory] ✓ Evidence Bundle loaded successfully")

        except Exception as e:
            print(f"[InstitutionalMemory] Error loading Evidence Bundle: {e}")
            self.loaded = False

    def detect_audit_question(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Detect if the input is an audit question.
        Returns (category, confidence) or None.
        """
        text_lower = text.lower()

        matches = []
        for pattern, category in AUDIT_PATTERNS:
            if re.search(pattern, text_lower):
                matches.append(category)

        if not matches:
            return None

        # Return most common category
        from collections import Counter
        category = Counter(matches).most_common(1)[0][0]
        confidence = len(matches) / len(AUDIT_PATTERNS)

        return (category, min(confidence * 5, 1.0))  # Scale up confidence

    def query(self, question: str) -> Optional[Dict]:
        """
        Query institutional memory for an answer.
        Returns structured response with answer and verification command.
        """
        if not self.loaded:
            return None

        question_lower = question.lower()

        # Search stress questions first (exact match attempts)
        best_match = None
        best_score = 0

        for sq in self.stress_questions:
            q_text = sq.get('question', '').lower()
            q_german = sq.get('german', '').lower()

            # Calculate similarity (simple word overlap)
            question_words = set(question_lower.split())
            q_words = set(q_text.split())
            overlap = len(question_words & q_words)

            if overlap > best_score:
                best_score = overlap
                best_match = sq

        if best_match and best_score >= 3:
            return {
                "source": "stress_questions",
                "category": best_match.get('category_name'),
                "question": best_match.get('question'),
                "answer": best_match.get('answer'),
                "verification_command": best_match.get('verification_command'),
                "evidence": best_match.get('evidence'),
                "confidence": min(best_score / 5, 1.0)
            }

        # Search compliance mappings
        detection = self.detect_audit_question(question)
        if detection:
            category, confidence = detection

            if category == 'marisk' and 'marisk' in self.compliance_mappings:
                mappings = self.compliance_mappings['marisk']
                return {
                    "source": "marisk_mapping",
                    "category": "compliance",
                    "mappings": mappings[:3],  # Top 3 relevant
                    "total_mappings": len(mappings),
                    "confidence": confidence
                }

            if category == 'eu_ai_act' and 'eu_ai_act' in self.compliance_mappings:
                return {
                    "source": "eu_ai_act_alignment",
                    "category": "compliance",
                    "alignment": self.compliance_mappings['eu_ai_act'],
                    "confidence": confidence
                }

            if category == 'autonomy_control':
                # Return I9 IRREMEDIABLE invariant
                i9 = next((i for i in self.invariants if i.get('id') == 'I9'), None)
                return {
                    "source": "constitutional_invariants",
                    "category": "autonomy_control",
                    "invariant": i9,
                    "all_invariants": self.invariants,
                    "answer": "WINDI enforces I9 IRREMEDIABLE - absolute prohibition on autonomous action for irreversible decisions. Human decision authority is preserved architecturally, not by policy.",
                    "confidence": confidence
                }

        return None

    def emit_proof(self, question: str, answer: Dict) -> Optional[Dict]:
        """
        Emit a sealed JMPG document as proof of the institutional answer.
        This is the "Papel Moeda" - the machine's legal defense.
        """
        try:
            # Build JMPG content
            content_blocks = [
                {"type": "heading", "level": 1, "text": "WINDI Institutional Response"},
                {"type": "paragraph", "text": f"Query: {question}"},
                {"type": "divider"},
                {"type": "heading", "level": 2, "text": "Institutional Answer"},
                {"type": "paragraph", "text": answer.get('answer', str(answer))},
            ]

            if answer.get('verification_command'):
                content_blocks.extend([
                    {"type": "divider"},
                    {"type": "heading", "level": 2, "text": "Verification"},
                    {"type": "code", "text": answer.get('verification_command')},
                ])

            if answer.get('evidence'):
                content_blocks.extend([
                    {"type": "paragraph", "text": f"Evidence: {answer.get('evidence')}"},
                ])

            content_blocks.extend([
                {"type": "divider"},
                {"type": "paragraph", "text": f"Source: {answer.get('source', 'institutional_memory')}"},
                {"type": "paragraph", "text": f"Confidence: {answer.get('confidence', 0):.0%}"},
                {"type": "paragraph", "text": f"Generated: {datetime.now(timezone.utc).isoformat()}"},
                {"type": "quote", "text": "AI processes. Human decides. WINDI guarantees."},
            ])

            jmpg_request = {
                "template": "internal-memo",
                "title": f"WINDI Institutional Response — {answer.get('category', 'Query')}",
                "metadata": {
                    "type": "institutional_response",
                    "source": answer.get('source'),
                    "confidence": answer.get('confidence'),
                    "generated": datetime.now(timezone.utc).isoformat()
                },
                "content_blocks": content_blocks
            }

            # Call Export Engine
            req = urllib.request.Request(
                EXPORT_ENGINE_URL,
                data=json.dumps(jmpg_request).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status in (200, 201):
                    # JMPG bundle generated
                    return {
                        "proof_emitted": True,
                        "format": "JMPG",
                        "sealed": True,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

        except Exception as e:
            print(f"[InstitutionalMemory] Proof emission error: {e}")

        return None

    def get_stats(self) -> Dict:
        """Return statistics about loaded institutional knowledge."""
        return {
            "loaded": self.loaded,
            "stress_questions": len(self.stress_questions),
            "marisk_mappings": len(self.compliance_mappings.get('marisk', [])),
            "bait_sections": len(self.compliance_mappings.get('bait', [])),
            "invariants": len(self.invariants),
            "knowledge_categories": list(self.knowledge_base.keys())
        }


# ══════════════════════════════════════════════════════════════════════════════
# Singleton instance
# ══════════════════════════════════════════════════════════════════════════════

_memory = None

def get_institutional_memory() -> InstitutionalMemory:
    """Get the singleton InstitutionalMemory instance."""
    global _memory
    if _memory is None:
        _memory = InstitutionalMemory()
    return _memory


def query_institutional(question: str) -> Optional[Dict]:
    """Quick query function."""
    return get_institutional_memory().query(question)


def emit_institutional_proof(question: str, answer: Dict) -> Optional[Dict]:
    """Quick proof emission function."""
    return get_institutional_memory().emit_proof(question, answer)


# ══════════════════════════════════════════════════════════════════════════════
# CLI Test
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  WINDI Institutional Memory — Test")
    print("=" * 70)
    print()

    memory = InstitutionalMemory()
    print(f"Stats: {json.dumps(memory.get_stats(), indent=2)}")
    print()

    # Test queries
    test_questions = [
        "How does WINDI comply with EU AI Act Article 14?",
        "Can the AI override human decisions?",
        "Can you prove MaRisk AT 7.2 compliance?",
        "Why should we trust your system?",
    ]

    for q in test_questions:
        print(f"Q: {q}")
        result = memory.query(q)
        if result:
            print(f"A: {result.get('answer', str(result))[:200]}...")
            print(f"   Source: {result.get('source')} | Confidence: {result.get('confidence', 0):.0%}")
        else:
            print("   (No institutional answer found)")
        print()
