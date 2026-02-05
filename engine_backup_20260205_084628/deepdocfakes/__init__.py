"""
WINDI DeepDOCFakes — Document Security Division
=================================================
Anti-Deepfake & Provenance Engineering

Architecture:
    deepdocfakes/
    ├── __init__.py              ← you are here
    ├── structural_hash.py       → canonical structural fingerprinting
    ├── provenance_engine.py     → "digital birth certificate" generation
    ├── verify_engine.py         → VALID | UNKNOWN | TAMPERED verification
    ├── deepfake_risk.py         → resilience scoring (0-100)
    ├── pdf_metadata_embed.py    → XMP/custom metadata embedding in PDFs
    ├── registry_provenance.py   → provenance registry for HIGH/MEDIUM
    └── README.md                → department documentation

Principle: "Deepfake copies appearance. We protect origin."
Protocol: WINDI-SOF-v1 (Secure Origin Framework)

Three Dragons Contribution:
    Guardian (Claude)  — Core engine, scoring, verification logic
    Architect (GPT)    — Modular structure, API contracts, threat model
    Witness  (Gemini)  — Future: independent verification attestation

Author: WINDI Publishing House — Kempten (Allgäu), Bavaria, Germany
Version: 1.0.0
Date: 02 February 2026
"""

__version__ = "1.0.0"
__module__ = "WINDI DeepDOCFakes"
__division__ = "Document Security Division"
__protocol__ = "WINDI-SOF-v1"

from .structural_hash import compute_structural_hash, canonicalize, CANONICAL_VERSION
from .provenance_engine import (
    build_provenance_record,
    persist_provenance_record,
    load_provenance_record,
    PROVENANCE_VERSION
)
from .verify_engine import (
    verify_by_submission_id,
    verify_by_hash,
    VerificationStatus
)
from .deepfake_risk import (
    compute_resilience_score,
    resilience_rating,
    resilience_factors
)

__all__ = [
    # structural_hash
    "compute_structural_hash",
    "canonicalize",
    "CANONICAL_VERSION",
    # provenance_engine
    "build_provenance_record",
    "persist_provenance_record",
    "load_provenance_record",
    "PROVENANCE_VERSION",
    # verify_engine
    "verify_by_submission_id",
    "verify_by_hash",
    "VerificationStatus",
    # deepfake_risk
    "compute_resilience_score",
    "resilience_rating",
    "resilience_factors",
]
