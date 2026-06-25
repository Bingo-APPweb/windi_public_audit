"""VPSE — Viability Pre-Screen Engine. Pre-HIOS, pre-DID. Pre-Screen, não veredicto."""
from .pipeline import run_vpse, build_receipt_candidate
from .provenance import Claim, Provenance, Confidence

__version__ = "0.1.0-mvp"
__all__ = ["run_vpse", "build_receipt_candidate", "Claim", "Provenance", "Confidence"]
