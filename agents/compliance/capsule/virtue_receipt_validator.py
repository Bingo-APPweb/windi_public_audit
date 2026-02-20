#!/usr/bin/env python3
"""
WINDI Compliance Agent — Capsule: Virtue Receipt Validator
============================================================
UNIFIED VERSION — Three Dragons Fusion
  Guardian (Claude): Deep schema validation, Zero-Knowledge enforcement,
                     decision record integrity, override documentation
  Architect (GPT):   Signature verification, ledger cross-check,
                     forensic self-evidence, timestamp sanity
  Witness (Gemini):  Anomaly patterns (reserved for future Pulse integration)

═══════════════════════════════════════════════════════════════
A Virtue Receipt is the cryptographic proof that a governance
decision was made correctly. It is the DNA of WINDI's ethical
guarantee: "AI processes. Human decides. WINDI guarantees."

The Virtue Receipt canonical structure:
  - hash:       SHA-256 of the governed document
  - categories: type, impact, domain, value_range (R1-R5)
  - governance: sge_score, risk, validation
  - decision:   action, role, timestamp, ai_rec, override
  - flags:      array of governance flags
  - signature:  institutional digital signature (optional)

Zero-Knowledge: Validates structure, hashes, and signatures.
                NEVER accesses document content.

This module GUARANTEES:
  ✔ The receipt points to an existing event in the ledger
  ✔ The signature belongs to a valid institutional entity
  ✔ The proof was not forged outside the chain of custody
  ✔ Human decision is recorded and accountable (I1, I9)
  ✔ Override documentation is complete (I2, I6)
  ✔ Value ranges use R1-R5, never actual values (I3)
  ✔ Every validation generates its own forensic evidence

This module NEVER:
  ✗ Calculates Virtue
  ✗ Interprets document context
  ✗ Approves or blocks actions
  ✗ Alters any records
  ✗ Accesses sensitive content
═══════════════════════════════════════════════════════════════
"""

import json
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

logger = logging.getLogger("WINDI.Compliance.VirtueReceipt")


# ─────────────────────────────────────────────────────
# CANONICAL SCHEMA DEFINITIONS
# (Guardian: deep structural requirements)
# ─────────────────────────────────────────────────────
REQUIRED_ROOT_FIELDS = ["hash", "categories", "governance", "decision", "flags"]
REQUIRED_CATEGORY_FIELDS = ["type", "impact", "domain", "value_range"]
REQUIRED_GOVERNANCE_FIELDS = ["sge_score", "risk", "validation"]
REQUIRED_DECISION_FIELDS = ["action", "role", "timestamp", "ai_rec", "override"]

VALID_IMPACTS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
VALID_VALUE_RANGES = ["R1", "R2", "R3", "R4", "R5"]
VALID_DOC_TYPES = [
    "CONTRACT", "INVOICE", "APPROVAL", "REPORT", "MEMO",
    "POLICY", "REGULATION", "CORRESPONDENCE", "AUDIT"
]
VALID_ACTIONS = ["approved", "rejected", "escalated", "deferred", "archived"]
VALID_RISK_LEVELS = ["R0", "R1", "R2", "R3", "R4", "R5"]

# Timestamp bounds (Architect: sanity window)
MAX_RECEIPT_AGE_DAYS = 365 * 11   # 10yr HIGH retention + 1yr buffer
MAX_FUTURE_TOLERANCE_SECONDS = 60  # Clock skew tolerance


# ─────────────────────────────────────────────────────
# PROTOCOL INTERFACES
# (Architect: pluggable verification services)
# ─────────────────────────────────────────────────────
@runtime_checkable
class LedgerClient(Protocol):
    """Interface for Forensic Ledger hash existence checks."""
    def hash_exists(self, event_hash: str) -> bool: ...


@runtime_checkable
class SignatureVerifier(Protocol):
    """Interface for institutional digital signature verification."""
    def verify(self, signature: str, event_hash: str, issuer_id: str) -> bool: ...


class NullLedgerClient:
    """Default ledger client when no external ledger is connected."""
    def hash_exists(self, event_hash: str) -> bool:
        logger.debug("NullLedgerClient: ledger cross-check skipped (no client configured)")
        return True  # Permissive when not connected — findings will note this


class NullSignatureVerifier:
    """Default signature verifier when no crypto service is connected."""
    def verify(self, signature: str, event_hash: str, issuer_id: str) -> bool:
        logger.debug("NullSignatureVerifier: signature check skipped (no verifier configured)")
        return True  # Permissive when not connected — findings will note this


class FileLedgerClient:
    """
    Ledger client that checks hash existence against local ledger files.
    Production-grade: searches /opt/windi/ledger/ for matching hashes.
    """
    def __init__(self, ledger_path: str = "/opt/windi/ledger/"):
        self.ledger_path = Path(ledger_path)
        self._hash_index: Optional[set] = None

    def hash_exists(self, event_hash: str) -> bool:
        if self._hash_index is None:
            self._build_index()
        return event_hash in self._hash_index

    def _build_index(self):
        """Build in-memory index of all hashes in the ledger."""
        self._hash_index = set()
        if not self.ledger_path.exists():
            return
        for json_file in self.ledger_path.rglob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    self._extract_hashes(data)
            except (json.JSONDecodeError, IOError):
                pass

    def _extract_hashes(self, data, depth: int = 0):
        """Recursively extract hash values from ledger records."""
        if depth > 5:  # Prevent infinite recursion
            return
        if isinstance(data, dict):
            for key in ("hash", "event_hash", "config_hash",
                        "integrity_hash", "report_hash", "proof_hash"):
                val = data.get(key)
                if isinstance(val, str) and len(val) in (64, 128):
                    self._hash_index.add(val)
            for v in data.values():
                self._extract_hashes(v, depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._extract_hashes(item, depth + 1)


# ─────────────────────────────────────────────────────
# VALIDATION RESULT
# (Architect: clean dataclass per receipt)
# (Guardian: extended with detailed findings)
# ─────────────────────────────────────────────────────
@dataclass
class ReceiptValidationResult:
    """
    Individual validation result for a single Virtue Receipt.

    Statuses:
      - "valid":           All checks passed
      - "invalid":         Critical failures found (broken hash, missing decision)
      - "review_required": Non-critical issues that need human attention
    """
    receipt_id: str
    status: str = "valid"                    # valid | invalid | review_required
    findings: list = field(default_factory=list)
    forensic_hash: str = ""                  # Hash of THIS validation event
    timestamp_utc: str = ""                  # When validation occurred
    checks_performed: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    invariants_at_risk: list = field(default_factory=list)

    def escalate(self, new_status: str):
        """Escalate status (valid → review_required → invalid)."""
        order = {"valid": 0, "review_required": 1, "invalid": 2}
        if order.get(new_status, 0) > order.get(self.status, 0):
            self.status = new_status

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────
# ZERO-KNOWLEDGE DETECTOR
# (Guardian: catches actual financial values in receipts)
# ─────────────────────────────────────────────────────
class ZeroKnowledgeDetector:
    """
    Detects potential Zero-Knowledge violations in receipt data.
    Value ranges must be R1-R5, NEVER actual monetary amounts.
    """

    SUSPICIOUS_PATTERNS = [
        # Currency patterns that should NEVER appear in a receipt
        "€", "$", "£", "¥", "CHF", "USD", "EUR", "GBP",
    ]

    @staticmethod
    def scan_for_violations(data: dict, path: str = "") -> list[str]:
        """Recursively scan receipt data for Zero-Knowledge violations."""
        violations = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                # value_range must be R1-R5, not numbers
                if key == "value_range" and isinstance(value, (int, float)):
                    violations.append(
                        f"Zero-Knowledge VIOLATION at {current_path}: "
                        f"Contains numeric value {value} instead of range (R1-R5)"
                    )

                # Check string values for currency/amount patterns
                if isinstance(value, str):
                    for pattern in ZeroKnowledgeDetector.SUSPICIOUS_PATTERNS:
                        if pattern in value:
                            violations.append(
                                f"Zero-Knowledge VIOLATION at {current_path}: "
                                f"Contains potential financial data ('{pattern}' detected)"
                            )

                # Recurse into nested structures
                violations.extend(
                    ZeroKnowledgeDetector.scan_for_violations(value, current_path)
                )

        elif isinstance(data, list):
            for i, item in enumerate(data):
                violations.extend(
                    ZeroKnowledgeDetector.scan_for_violations(item, f"{path}[{i}]")
                )

        return violations


# ─────────────────────────────────────────────────────
# MAIN VALIDATOR CLASS — UNIFIED
# ─────────────────────────────────────────────────────
class VirtueReceiptValidator:
    """
    WINDI Virtue Receipt Validator — Unified (Guardian + Architect).

    8 Validation Phases:
      Phase 1: Schema Completeness         [Guardian]
      Phase 2: Category Validation          [Guardian]
      Phase 3: Governance Field Validation  [Guardian]
      Phase 4: Decision Record Integrity    [Guardian — I1/I9 critical]
      Phase 5: Hash Integrity & Format      [Guardian + Architect]
      Phase 6: Ledger Cross-Check           [Architect — chain of custody]
      Phase 7: Signature Verification       [Architect — institutional trust]
      Phase 8: Override Documentation       [Guardian — I2/I6]

    Plus:
      - Zero-Knowledge Deep Scan            [Guardian — I3]
      - Timestamp Sanity Check              [Architect]
      - Forensic Self-Evidence              [Architect — I4]
    """

    CAPSULE_NAME = "VirtueReceiptValidator"

    def __init__(self, config: dict,
                 ledger_client: Optional[LedgerClient] = None,
                 signature_verifier: Optional[SignatureVerifier] = None):
        """
        Args:
            config: WINDI agent configuration dict
            ledger_client: Optional Forensic Ledger client for hash cross-checks.
                           If None, uses FileLedgerClient (local file-based).
            signature_verifier: Optional institutional signature verifier.
                                If None, signature checks are skipped with advisory note.
        """
        self.config = config
        self.ledger_path = Path(config.get("ledger_path", "/opt/windi/ledger/"))

        # Architect integration: pluggable verification services
        if ledger_client is not None:
            self.ledger = ledger_client
        elif self.ledger_path.exists():
            self.ledger = FileLedgerClient(str(self.ledger_path))
            logger.info("VirtueReceiptValidator: Using FileLedgerClient for hash cross-checks")
        else:
            self.ledger = NullLedgerClient()
            logger.warning("VirtueReceiptValidator: No ledger available — cross-checks advisory")

        self.signer = signature_verifier or NullSignatureVerifier()
        self._has_real_signer = not isinstance(self.signer, NullSignatureVerifier)
        self._has_real_ledger = not isinstance(self.ledger, NullLedgerClient)

        # Forensic evidence store for this validation session
        self._validation_evidence: list[dict] = []

    # ═════════════════════════════════════════════════
    # MAIN ENTRY POINT
    # ═════════════════════════════════════════════════
    def validate(self, report, target: str = "all"):
        """
        Execute full validation across all Virtue Receipts.

        Each receipt passes through 8 phases plus Zero-Knowledge scan.
        Every validation event generates its own forensic evidence (Architect).
        All findings feed into the unified ComplianceReport (Guardian).

        Args:
            report: ComplianceReport instance to receive findings
            target: "all" or specific receipt/submission ID
        """
        receipts = self._load_receipts(target)

        if not receipts:
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R1",
                message="No Virtue Receipts found for validation",
                details={"target": target}
            )
            return

        logger.info(f"═══ Virtue Receipt Validation: {len(receipts)} receipt(s) ═══")

        # Advisory notes for missing services
        if not self._has_real_ledger:
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R2",
                message="Ledger cross-check in advisory mode (no external ledger connected). "
                        "Hash existence cannot be verified against Forensic Ledger.",
                details={"service": "ledger_client", "status": "null_client"}
            )

        if not self._has_real_signer:
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R2",
                message="Signature verification skipped (no signature verifier configured). "
                        "Institutional signatures cannot be validated.",
                details={"service": "signature_verifier", "status": "null_verifier"}
            )

        # Validate each receipt
        results: list[ReceiptValidationResult] = []

        for receipt_id, receipt in receipts.items():
            result = self._validate_single_receipt(report, receipt_id, receipt)
            results.append(result)

        # Generate session summary
        self._generate_session_summary(report, results)

        # Write forensic evidence for this validation session (Architect)
        self._write_forensic_evidence(results)

        logger.info(f"═══ Validation complete: {len(results)} receipts processed ═══")

    # ═════════════════════════════════════════════════
    # SINGLE RECEIPT VALIDATION (8 PHASES)
    # ═════════════════════════════════════════════════
    def _validate_single_receipt(self, report, receipt_id: str,
                                  receipt: dict) -> ReceiptValidationResult:
        """Validate a single Virtue Receipt through all 8 phases."""
        result = ReceiptValidationResult(
            receipt_id=receipt_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat()
        )

        # Phase 1: Schema Completeness [Guardian]
        self._phase1_schema(report, result, receipt_id, receipt)

        # Phase 2: Category Validation [Guardian]
        self._phase2_categories(report, result, receipt_id, receipt)

        # Phase 3: Governance Fields [Guardian]
        self._phase3_governance(report, result, receipt_id, receipt)

        # Phase 4: Decision Record Integrity [Guardian — I1/I9 critical]
        self._phase4_decision(report, result, receipt_id, receipt)

        # Phase 5: Hash Integrity [Guardian format + Architect cross-check]
        self._phase5_hash_integrity(report, result, receipt_id, receipt)

        # Phase 6: Ledger Cross-Check [Architect — chain of custody]
        self._phase6_ledger_crosscheck(report, result, receipt_id, receipt)

        # Phase 7: Signature Verification [Architect — institutional trust]
        self._phase7_signature(report, result, receipt_id, receipt)

        # Phase 8: Override Documentation [Guardian — I2/I6]
        self._phase8_override(report, result, receipt_id, receipt)

        # Bonus: Zero-Knowledge Deep Scan [Guardian — I3]
        self._bonus_zero_knowledge_scan(report, result, receipt_id, receipt)

        # Bonus: Timestamp Sanity [Architect]
        self._bonus_timestamp_sanity(report, result, receipt_id, receipt)

        # Generate forensic hash of this validation event (Architect)
        result.forensic_hash = self._generate_forensic_hash(receipt_id, receipt, result)

        logger.info(
            f"Receipt {receipt_id}: status={result.status} | "
            f"checks={result.checks_passed}/{result.checks_performed} | "
            f"invariants_at_risk={result.invariants_at_risk or 'none'}"
        )

        return result

    # ─────────────────────────────────────────────
    # PHASE 1: Schema Completeness [Guardian]
    # ─────────────────────────────────────────────
    def _phase1_schema(self, report, result: ReceiptValidationResult,
                       receipt_id: str, receipt: dict):
        """Check all required root fields are present."""
        result.checks_performed += 1
        missing = [f for f in REQUIRED_ROOT_FIELDS if f not in receipt]

        if missing:
            result.checks_failed += 1
            result.escalate("invalid")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4",
                message=f"Receipt {receipt_id}: Missing required root fields: {missing}",
                details={"receipt_id": receipt_id, "missing_fields": missing,
                         "phase": "1_schema"}
            )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 2: Category Validation [Guardian]
    # ─────────────────────────────────────────────
    def _phase2_categories(self, report, result: ReceiptValidationResult,
                            receipt_id: str, receipt: dict):
        """Validate category fields and enum values."""
        categories = receipt.get("categories", {})

        # 2a: Required category fields
        result.checks_performed += 1
        missing = [f for f in REQUIRED_CATEGORY_FIELDS if f not in categories]
        if missing:
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: Missing category fields: {missing}",
                details={"receipt_id": receipt_id, "missing": missing,
                         "phase": "2_categories"}
            )
        else:
            result.checks_passed += 1

        if not categories:
            return

        # 2b: Impact level validation
        result.checks_performed += 1
        impact = categories.get("impact")
        if impact and impact not in VALID_IMPACTS:
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: Invalid impact level '{impact}'",
                details={"valid_values": VALID_IMPACTS, "phase": "2_categories"}
            )
        elif impact:
            result.checks_passed += 1

        # 2c: Document type validation
        result.checks_performed += 1
        doc_type = categories.get("type")
        if doc_type and doc_type not in VALID_DOC_TYPES:
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R2",
                message=f"Receipt {receipt_id}: Unrecognized document type '{doc_type}'",
                details={"valid_types": VALID_DOC_TYPES, "phase": "2_categories"}
            )
        elif doc_type:
            result.checks_passed += 1

        # 2d: Value range — CRITICAL Zero-Knowledge check [Guardian]
        result.checks_performed += 1
        value_range = categories.get("value_range")
        if value_range is not None:
            if isinstance(value_range, (int, float)):
                # ZERO-KNOWLEDGE VIOLATION: contains actual financial value!
                result.checks_failed += 1
                result.escalate("invalid")
                result.invariants_at_risk.append("I3")
                report.add_finding(
                    capsule=self.CAPSULE_NAME,
                    severity="R5",
                    message=f"Receipt {receipt_id}: ZERO-KNOWLEDGE VIOLATION — "
                            f"value_range contains numeric value ({value_range}) instead of "
                            f"range code (R1-R5). Actual financial data MUST NEVER appear.",
                    details={"value": value_range, "expected": "R1-R5",
                             "invariant": "I3", "phase": "2_categories"}
                )
            elif value_range not in VALID_VALUE_RANGES:
                result.checks_failed += 1
                result.escalate("review_required")
                report.add_finding(
                    capsule=self.CAPSULE_NAME,
                    severity="R4",
                    message=f"Receipt {receipt_id}: Invalid value_range '{value_range}'. "
                            f"Must be R1-R5 ranges, NEVER actual financial values.",
                    details={"valid_ranges": VALID_VALUE_RANGES, "phase": "2_categories"}
                )
            else:
                result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 3: Governance Fields [Guardian]
    # ─────────────────────────────────────────────
    def _phase3_governance(self, report, result: ReceiptValidationResult,
                            receipt_id: str, receipt: dict):
        """Validate governance fields including SGE score range."""
        governance = receipt.get("governance", {})

        # 3a: Required governance fields
        result.checks_performed += 1
        missing = [f for f in REQUIRED_GOVERNANCE_FIELDS if f not in governance]
        if missing:
            result.checks_failed += 1
            result.escalate("invalid")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4",
                message=f"Receipt {receipt_id}: Missing governance fields: {missing}",
                details={"receipt_id": receipt_id, "missing": missing,
                         "phase": "3_governance"}
            )
            return
        result.checks_passed += 1

        # 3b: SGE score range (0-100)
        result.checks_performed += 1
        sge_score = governance.get("sge_score")
        if not isinstance(sge_score, (int, float)) or not (0 <= sge_score <= 100):
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: SGE score out of range: {sge_score}",
                details={"expected_range": "0-100", "phase": "3_governance"}
            )
        else:
            result.checks_passed += 1

        # 3c: Risk level validity
        result.checks_performed += 1
        risk = governance.get("risk")
        if risk not in VALID_RISK_LEVELS:
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: Invalid risk level: {risk}",
                details={"valid_values": VALID_RISK_LEVELS, "phase": "3_governance"}
            )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 4: Decision Record [Guardian — I1/I9]
    # THE MOST CRITICAL PHASE
    # ─────────────────────────────────────────────
    def _phase4_decision(self, report, result: ReceiptValidationResult,
                          receipt_id: str, receipt: dict):
        """
        Validate human decision record.
        CRITICAL for I1 (Human Sovereignty) and I9 (No Autonomy Escalation).

        A Virtue Receipt without a valid human decision record is evidence
        of potential autonomous operation — an I9 IRREMEDIABLE violation.
        """
        decision = receipt.get("decision", {})

        # 4a: Required decision fields
        result.checks_performed += 1
        missing = [f for f in REQUIRED_DECISION_FIELDS if f not in decision]
        if missing:
            result.checks_failed += 1
            result.escalate("invalid")
            result.invariants_at_risk.extend(["I1", "I9"])
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R5",
                message=f"Receipt {receipt_id}: CRITICAL — Missing decision fields: {missing}. "
                        f"Human decision record incomplete. "
                        f"Potential I1/I9 violation (autonomous operation without human decision).",
                details={"receipt_id": receipt_id, "missing": missing,
                         "invariant_risk": ["I1", "I9"], "phase": "4_decision"}
            )
            return
        result.checks_passed += 1

        # 4b: Action validity
        result.checks_performed += 1
        action = decision.get("action")
        if action not in VALID_ACTIONS:
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: Invalid decision action: {action}",
                details={"valid_actions": VALID_ACTIONS, "phase": "4_decision"}
            )
        else:
            result.checks_passed += 1

        # 4c: Role identification (WHO decided?)
        result.checks_performed += 1
        role = decision.get("role")
        if not role or not isinstance(role, str) or len(role.strip()) == 0:
            result.checks_failed += 1
            result.escalate("invalid")
            result.invariants_at_risk.append("I1")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4",
                message=f"Receipt {receipt_id}: No decision role specified — "
                        f"cannot verify human sovereignty (I1). "
                        f"Every governance decision must trace to a human actor.",
                details={"invariant_risk": "I1", "phase": "4_decision"}
            )
        else:
            result.checks_passed += 1

        # 4d: Decision timestamp
        result.checks_performed += 1
        timestamp = decision.get("timestamp")
        if not timestamp:
            result.checks_failed += 1
            result.escalate("invalid")
            result.invariants_at_risk.append("I4")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4",
                message=f"Receipt {receipt_id}: No decision timestamp — "
                        f"audit trail broken (I4)",
                details={"invariant_risk": "I4", "phase": "4_decision"}
            )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 5: Hash Integrity [Guardian + Architect]
    # ─────────────────────────────────────────────
    def _phase5_hash_integrity(self, report, result: ReceiptValidationResult,
                                receipt_id: str, receipt: dict):
        """
        Validate document hash format and integrity.
        Guardian: Format validation (SHA-256 = 64 hex chars)
        Architect: Extended format acceptance (SHA-512 = 128 hex chars)
        """
        result.checks_performed += 1
        doc_hash = receipt.get("hash")

        if not doc_hash:
            result.checks_failed += 1
            result.escalate("invalid")
            result.invariants_at_risk.append("I4")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R5",
                message=f"Receipt {receipt_id}: CRITICAL — No document hash. "
                        f"Integrity chain completely broken.",
                details={"receipt_id": receipt_id, "invariant_risk": "I4",
                         "phase": "5_hash_integrity"}
            )
            return

        # Accept SHA-256 (64 chars) or SHA-512 (128 chars) [Architect extension]
        valid_lengths = {64: "SHA-256", 128: "SHA-512"}
        is_hex = isinstance(doc_hash, str) and all(
            c in "0123456789abcdef" for c in doc_hash.lower()
        )

        if not is_hex or len(doc_hash) not in valid_lengths:
            result.checks_failed += 1
            result.escalate("invalid")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4",
                message=f"Receipt {receipt_id}: Invalid hash format. "
                        f"Expected SHA-256 (64 hex) or SHA-512 (128 hex), "
                        f"got {'non-hex string' if not is_hex else f'{len(doc_hash)} chars'}",
                details={
                    "hash_length": len(doc_hash) if isinstance(doc_hash, str) else "N/A",
                    "accepted_formats": valid_lengths,
                    "phase": "5_hash_integrity"
                }
            )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 6: Ledger Cross-Check [Architect]
    # Chain of custody verification
    # ─────────────────────────────────────────────
    def _phase6_ledger_crosscheck(self, report, result: ReceiptValidationResult,
                                   receipt_id: str, receipt: dict):
        """
        Verify the document hash exists in the Forensic Ledger.
        [Architect contribution]

        If the hash is not in the ledger, the receipt may have been
        forged outside the governance chain.
        """
        doc_hash = receipt.get("hash")
        if not doc_hash:
            return  # Already caught in Phase 5

        result.checks_performed += 1

        if not self.ledger.hash_exists(doc_hash):
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4" if self._has_real_ledger else "R2",
                message=f"Receipt {receipt_id}: Document hash not found in Forensic Ledger. "
                        f"{'Possible out-of-chain receipt — investigate provenance.' if self._has_real_ledger else 'Ledger not connected — manual verification recommended.'}",
                details={
                    "hash_prefix": doc_hash[:16] + "...",
                    "ledger_connected": self._has_real_ledger,
                    "concern": "Receipt may exist outside governance chain of custody",
                    "phase": "6_ledger_crosscheck"
                }
            )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 7: Signature Verification [Architect]
    # Institutional trust chain
    # ─────────────────────────────────────────────
    def _phase7_signature(self, report, result: ReceiptValidationResult,
                           receipt_id: str, receipt: dict):
        """
        Verify institutional digital signature on the receipt.
        [Architect contribution]

        Ensures the receipt was issued by a recognized entity
        and hasn't been tampered with after signing.
        """
        signature = receipt.get("signature") or receipt.get("issuer_signature")
        issuer_id = receipt.get("issuer_id")
        doc_hash = receipt.get("hash")

        # Signature is optional but recommended for HIGH/MEDIUM
        if not signature:
            gov_level = receipt.get("governance", {}).get("level")
            if gov_level in ("HIGH", "MEDIUM"):
                result.checks_performed += 1
                result.checks_failed += 1
                result.escalate("review_required")
                report.add_finding(
                    capsule=self.CAPSULE_NAME,
                    severity="R3",
                    message=f"Receipt {receipt_id}: No institutional signature present. "
                            f"Recommended for HIGH/MEDIUM governance.",
                    details={"phase": "7_signature",
                             "recommendation": "Add institutional digital signature"}
                )
            return

        if not issuer_id or not doc_hash:
            result.checks_performed += 1
            result.checks_failed += 1
            result.escalate("review_required")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: Signature present but missing "
                        f"issuer_id or document hash for verification",
                details={"has_issuer_id": bool(issuer_id),
                         "has_hash": bool(doc_hash), "phase": "7_signature"}
            )
            return

        # Verify signature
        result.checks_performed += 1
        if not self.signer.verify(signature, doc_hash, issuer_id):
            result.checks_failed += 1
            result.escalate("invalid")
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R5",
                message=f"Receipt {receipt_id}: INVALID INSTITUTIONAL SIGNATURE. "
                        f"Receipt may be forged or tampered. Issuer: {issuer_id}",
                details={
                    "issuer_id": issuer_id,
                    "hash_prefix": doc_hash[:16] + "..." if doc_hash else "N/A",
                    "concern": "Signature verification failed",
                    "phase": "7_signature"
                }
            )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # PHASE 8: Override Documentation [Guardian]
    # I2 (Transparency) + I6 (Right to Explanation)
    # ─────────────────────────────────────────────
    def _phase8_override(self, report, result: ReceiptValidationResult,
                          receipt_id: str, receipt: dict):
        """
        If human overrode AI recommendation, ensure it's documented.
        A human override is POSITIVE for I1 — but must be documented for I2/I6.
        """
        decision = receipt.get("decision", {})
        override = decision.get("override")

        if override is not True:
            return  # No override — nothing to check

        result.checks_performed += 1
        ai_rec = decision.get("ai_rec")
        action = decision.get("action")
        role = decision.get("role")

        if ai_rec and action and ai_rec != action:
            # Human explicitly overrode AI — I1 sovereignty exercised!
            logger.info(
                f"Receipt {receipt_id}: Human override — "
                f"AI: '{ai_rec}', Human: '{action}'. I1 sovereignty exercised."
            )

            if not role:
                result.checks_failed += 1
                result.escalate("review_required")
                result.invariants_at_risk.extend(["I2", "I6"])
                report.add_finding(
                    capsule=self.CAPSULE_NAME,
                    severity="R4",
                    message=f"Receipt {receipt_id}: Override without identified role — "
                            f"WHO overrode the AI? Accountability gap (I2/I6)",
                    details={
                        "ai_recommendation": ai_rec,
                        "human_action": action,
                        "invariant_risk": ["I2", "I6"],
                        "phase": "8_override"
                    }
                )
            else:
                result.checks_passed += 1

        elif override is True and not ai_rec:
            result.checks_failed += 1
            result.escalate("review_required")
            result.invariants_at_risk.extend(["I2", "I6"])
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R3",
                message=f"Receipt {receipt_id}: Override flagged but no AI recommendation "
                        f"recorded. Cannot verify what was overridden (I2/I6).",
                details={"invariant_risk": ["I2", "I6"], "phase": "8_override"}
            )

    # ─────────────────────────────────────────────
    # BONUS: Zero-Knowledge Deep Scan [Guardian]
    # I3 enforcement across entire receipt
    # ─────────────────────────────────────────────
    def _bonus_zero_knowledge_scan(self, report, result: ReceiptValidationResult,
                                    receipt_id: str, receipt: dict):
        """
        Deep scan entire receipt for Zero-Knowledge violations.
        [Guardian — I3 enforcement]
        """
        result.checks_performed += 1
        violations = ZeroKnowledgeDetector.scan_for_violations(receipt)

        if violations:
            result.checks_failed += 1
            result.escalate("invalid")
            result.invariants_at_risk.append("I3")
            for violation in violations:
                report.add_finding(
                    capsule=self.CAPSULE_NAME,
                    severity="R5",
                    message=f"Receipt {receipt_id}: {violation}",
                    details={"invariant": "I3", "phase": "bonus_zero_knowledge"}
                )
        else:
            result.checks_passed += 1

    # ─────────────────────────────────────────────
    # BONUS: Timestamp Sanity [Architect]
    # ─────────────────────────────────────────────
    def _bonus_timestamp_sanity(self, report, result: ReceiptValidationResult,
                                 receipt_id: str, receipt: dict):
        """
        Verify receipt timestamps are within acceptable bounds.
        [Architect contribution]

        Catches future timestamps, impossibly old timestamps,
        and unparseable timestamp formats.
        """
        now = datetime.now(timezone.utc)

        timestamp_locations = [
            ("decision.timestamp", receipt.get("decision", {}).get("timestamp")),
            ("governance.validation", receipt.get("governance", {}).get("validation")),
        ]

        for location, ts_value in timestamp_locations:
            if not ts_value:
                continue

            result.checks_performed += 1
            try:
                if isinstance(ts_value, str):
                    ts_clean = ts_value.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts_clean)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)

                    # Future check
                    max_future = now + timedelta(seconds=MAX_FUTURE_TOLERANCE_SECONDS)
                    if dt > max_future:
                        result.checks_failed += 1
                        result.escalate("review_required")
                        report.add_finding(
                            capsule=self.CAPSULE_NAME,
                            severity="R4",
                            message=f"Receipt {receipt_id}: Future timestamp at {location} "
                                    f"({ts_value}). Possible clock manipulation.",
                            details={"location": location, "timestamp": ts_value,
                                     "phase": "bonus_timestamp_sanity"}
                        )
                        continue

                    # Age check
                    max_age = now - timedelta(days=MAX_RECEIPT_AGE_DAYS)
                    if dt < max_age:
                        result.checks_failed += 1
                        result.escalate("review_required")
                        report.add_finding(
                            capsule=self.CAPSULE_NAME,
                            severity="R3",
                            message=f"Receipt {receipt_id}: Timestamp at {location} older "
                                    f"than {MAX_RECEIPT_AGE_DAYS // 365} years. Possible corruption.",
                            details={"location": location, "timestamp": ts_value,
                                     "phase": "bonus_timestamp_sanity"}
                        )
                        continue

                    result.checks_passed += 1

            except (ValueError, TypeError) as e:
                result.checks_failed += 1
                result.escalate("review_required")
                report.add_finding(
                    capsule=self.CAPSULE_NAME,
                    severity="R3",
                    message=f"Receipt {receipt_id}: Unparseable timestamp at {location}: "
                            f"'{ts_value}' — expected ISO 8601",
                    details={"location": location, "error": str(e),
                             "phase": "bonus_timestamp_sanity"}
                )

    # ═════════════════════════════════════════════════
    # FORENSIC SELF-EVIDENCE [Architect]
    # Every validation generates its own proof
    # ═════════════════════════════════════════════════
    def _generate_forensic_hash(self, receipt_id: str, receipt: dict,
                                 result: ReceiptValidationResult) -> str:
        """
        Generate immutable forensic hash of this validation event.
        [Architect contribution — adapted for WINDI]

        Covers WHAT was validated, WHEN, and WHAT was found —
        without storing receipt content (Zero-Knowledge).
        """
        evidence = {
            "receipt_id": receipt_id,
            "receipt_hash": receipt.get("hash", ""),
            "validation_status": result.status,
            "checks_performed": result.checks_performed,
            "checks_passed": result.checks_passed,
            "checks_failed": result.checks_failed,
            "invariants_at_risk": sorted(set(result.invariants_at_risk)),
            "timestamp_utc": result.timestamp_utc,
            "validator_version": "1.0.0-unified"
        }

        serialized = "|".join(
            str(evidence.get(k, "")) for k in sorted(evidence.keys())
        )
        forensic_hash = hashlib.sha256(serialized.encode()).hexdigest()

        evidence["forensic_hash"] = forensic_hash
        self._validation_evidence.append(evidence)

        return forensic_hash

    # ═════════════════════════════════════════════════
    # SESSION SUMMARY & FORENSIC EVIDENCE
    # ═════════════════════════════════════════════════
    def _generate_session_summary(self, report, results: list[ReceiptValidationResult]):
        """Add session summary to the compliance report."""
        total = len(results)
        valid = sum(1 for r in results if r.status == "valid")
        invalid = sum(1 for r in results if r.status == "invalid")
        review = sum(1 for r in results if r.status == "review_required")

        all_invariants = set()
        for r in results:
            all_invariants.update(r.invariants_at_risk)

        if invalid > 0:
            report.add_finding(
                capsule=self.CAPSULE_NAME,
                severity="R4",
                message=f"Virtue Receipt Session: {invalid}/{total} INVALID. "
                        f"Valid: {valid}, Review: {review}. "
                        f"Invariants at risk: {sorted(all_invariants) or 'none'}.",
                details={
                    "total": total, "valid": valid, "invalid": invalid,
                    "review_required": review,
                    "invariants_at_risk": sorted(all_invariants),
                    "phase": "session_summary"
                }
            )

        logger.info(
            f"Session: {total} receipts | "
            f"{valid} valid | {invalid} invalid | {review} review"
        )

    def _write_forensic_evidence(self, results: list[ReceiptValidationResult]):
        """
        Write forensic evidence of validation session to disk.
        [Architect contribution]

        Creates immutable record without sensitive content (Zero-Knowledge).
        """
        if not self._validation_evidence:
            return

        evidence_dir = self.ledger_path / "compliance" / "virtue_receipt_validations"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        session_file = evidence_dir / f"validation_session_{session_id}.json"

        all_hashes = [e["forensic_hash"] for e in self._validation_evidence]
        session_hash = hashlib.sha256("|".join(all_hashes).encode()).hexdigest()

        session_record = {
            "session_id": session_id,
            "session_hash": session_hash,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "validator_version": "1.0.0-unified",
            "fusion": "Guardian(Claude) + Architect(GPT)",
            "receipts_validated": len(self._validation_evidence),
            "results_summary": {
                "valid": sum(1 for r in results if r.status == "valid"),
                "invalid": sum(1 for r in results if r.status == "invalid"),
                "review_required": sum(1 for r in results if r.status == "review_required"),
            },
            "individual_evidence": self._validation_evidence
        }

        try:
            with open(session_file, "w") as f:
                json.dump(session_record, f, indent=2, ensure_ascii=False)
            logger.info(f"Forensic evidence written: {session_file}")
        except IOError as e:
            logger.error(f"Failed to write forensic evidence: {e}")

        self._validation_evidence = []

    # ═════════════════════════════════════════════════
    # RECEIPT LOADING
    # ═════════════════════════════════════════════════
    def _load_receipts(self, target: str) -> dict:
        """Load Virtue Receipts from the Forensic Ledger."""
        receipts = {}
        ledger = self.ledger_path

        if not ledger.exists():
            logger.warning(f"Ledger path not found: {ledger}")
            return receipts

        pattern = f"*{target}*.json" if target != "all" else "*.json"

        # Search ledger root and common subdirectories
        search_paths = [ledger]
        for subdir in ("receipts", "virtue_receipts", "submissions"):
            sub = ledger / subdir
            if sub.exists():
                search_paths.append(sub)

        for search_path in search_paths:
            for receipt_file in search_path.glob(pattern):
                try:
                    with open(receipt_file) as f:
                        data = json.load(f)
                        if "virtue_receipt" in data:
                            receipts[receipt_file.stem] = data["virtue_receipt"]
                        elif "receipts" in data:
                            for rid, r in data["receipts"].items():
                                receipts[rid] = r
                        elif "hash" in data and "decision" in data:
                            receipts[receipt_file.stem] = data
                        elif "compliance_report" in data:
                            continue  # Skip reports
                        else:
                            receipts[receipt_file.stem] = data
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to load receipt {receipt_file}: {e}")

        return receipts
