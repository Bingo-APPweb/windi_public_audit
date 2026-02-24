#!/usr/bin/env python3
"""
WINDI Paperless-OCR Bridge — Unified Document Pipeline
Connects: OCR Local → Paperless QES → Forensic Ledger → Wisdom Loop

Pipeline:
  1. INGEST: Receive physical document image
  2. OCR: Extract text locally (Tesseract, zero cloud)
  3. CATEGORIZE: Auto-classify document type (rule-based)
  4. HASH: Generate SHA-256 integrity proof of original + extracted text
  5. PREPARE: Format for Paperless submission (if signing required)
  6. ANCHOR: Write receipt to Forensic Ledger (:8101)
  7. WISDOM: Generate wisdom candidate if relevant pattern detected

Principle: "AI processes. Human decides. WINDI guarantees."
Invariant I9: No automated signing — human MUST approve.
"""

import hashlib
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent paths for imports
sys.path.insert(0, '/opt/windi/engine')
sys.path.insert(0, '/opt/windi/engine/wisdom')

from multimodal_ocr import WindiOCR
from auto_categorizer import WisdomCategorizer


class PaperlessBridge:
    """Unified pipeline: Physical Document → Digital Sovereign Proof."""

    VERSION = "1.0.0"
    LEDGER_URL = "http://localhost:8101"

    # Document type mapping: OCR keywords → WINDI metadata categories
    DOC_TYPE_RULES = {
        "CONTRACT": {
            "keywords_de": ["vertrag", "vereinbarung", "kontrakt", "geschäftsbedingungen"],
            "keywords_en": ["contract", "agreement", "terms"],
            "keywords_pt": ["contrato", "acordo", "termos"],
            "impact": "HIGH",
            "requires_signing": True
        },
        "INVOICE": {
            "keywords_de": ["rechnung", "rechnungsnummer", "rechnungsdatum", "mwst", "netto", "brutto"],
            "keywords_en": ["invoice", "invoice number", "total due", "payment"],
            "keywords_pt": ["fatura", "nota fiscal", "valor total"],
            "impact": "MED",
            "requires_signing": False
        },
        "APPROVAL": {
            "keywords_de": ["genehmigung", "genehmigt", "freigabe", "bewilligt", "bescheid"],
            "keywords_en": ["approval", "approved", "authorized", "granted"],
            "keywords_pt": ["aprovação", "aprovado", "autorizado", "deferido"],
            "impact": "HIGH",
            "requires_signing": True
        },
        "RECEIPT": {
            "keywords_de": ["quittung", "beleg", "kassenbon", "empfangsbestätigung"],
            "keywords_en": ["receipt", "confirmation", "acknowledgment"],
            "keywords_pt": ["recibo", "comprovante", "confirmação"],
            "impact": "LOW",
            "requires_signing": False
        },
        "REPORT": {
            "keywords_de": ["bericht", "analyse", "gutachten", "protokoll"],
            "keywords_en": ["report", "analysis", "assessment", "protocol"],
            "keywords_pt": ["relatório", "análise", "parecer", "protocolo"],
            "impact": "MED",
            "requires_signing": False
        },
        "GOVERNANCE": {
            "keywords_de": ["beschluss", "satzung", "richtlinie", "verordnung"],
            "keywords_en": ["resolution", "statute", "directive", "regulation", "governance"],
            "keywords_pt": ["resolução", "estatuto", "diretriz", "regulamento", "governança"],
            "impact": "CRIT",
            "requires_signing": True
        }
    }

    def __init__(self):
        self.ocr = WindiOCR()
        self.categorizer = WisdomCategorizer()
        self.requires_api_key = False  # Bridge itself is autonomous

    def ingest_document(self, image_path: str, lang: str = 'auto',
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Full pipeline: Image → OCR → Classify → Hash → Ledger Receipt.

        Args:
            image_path: Path to document image (scan/photo)
            lang: OCR language ('de', 'en', 'pt', 'auto')
            metadata: Optional extra metadata (department, submitter, etc.)

        Returns:
            Complete pipeline result with receipt hash
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        pipeline_id = f"PB-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        result = {
            "pipeline_id": pipeline_id,
            "timestamp": timestamp,
            "source_file": os.path.basename(image_path),
            "stages": {},
            "success": False
        }

        # ── STAGE 1: OCR ──
        ocr_result = self.ocr.extract_with_confidence(image_path, lang=lang)
        result["stages"]["ocr"] = {
            "success": ocr_result.get("success", False),
            "word_count": ocr_result.get("word_count", 0),
            "avg_confidence": ocr_result.get("avg_confidence", 0),
            "engine": ocr_result.get("engine", "unknown"),
        }

        if not ocr_result.get("success"):
            result["stages"]["ocr"]["error"] = ocr_result.get("error")
            result["error"] = "OCR extraction failed"
            return result

        extracted_text = ocr_result.get("text", "")

        # ── STAGE 2: DOCUMENT CLASSIFICATION ──
        doc_type, impact, requires_signing = self._classify_document(extracted_text)
        result["stages"]["classification"] = {
            "doc_type": doc_type,
            "impact_level": impact,
            "requires_signing": requires_signing,
            "method": "rule_based_trilingual"
        }

        # ── STAGE 3: WISDOM CATEGORIZATION ──
        wisdom_result = self.categorizer.categorize(extracted_text[:500])
        result["stages"]["wisdom"] = {
            "category": wisdom_result.get("category"),
            "confidence": wisdom_result.get("confidence"),
            "is_candidate": wisdom_result.get("confidence", 0) >= 0.5
        }

        # ── STAGE 4: INTEGRITY HASHING ──
        # Hash the original image
        with open(image_path, 'rb') as f:
            image_hash = hashlib.sha256(f.read()).hexdigest()

        # Hash the extracted text
        text_hash = hashlib.sha256(extracted_text.encode('utf-8')).hexdigest()

        # Combined proof hash
        combined = f"{image_hash}:{text_hash}:{timestamp}"
        proof_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()

        result["stages"]["integrity"] = {
            "image_hash": image_hash,
            "text_hash": text_hash,
            "proof_hash": proof_hash,
            "method": "SHA-256"
        }

        # ── STAGE 5: FORENSIC LEDGER RECEIPT ──
        receipt = {
            "id": f"VR-PB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "actor": "paperless-bridge",
            "app": "windi-paperless-bridge",
            "doc_name": os.path.basename(image_path),
            "doc_type": doc_type.lower(),
            "content_hash": proof_hash,
            "governance_level": impact,
            "sge_score": 0.0,
            "tags": ["paperless-bridge", f"type-{doc_type.lower()}", f"impact-{impact.lower()}"],
            "metadata": {
                "pipeline_id": pipeline_id,
                "image_hash": image_hash,
                "text_hash": text_hash,
                "word_count": ocr_result.get("word_count", 0),
                "ocr_confidence": ocr_result.get("avg_confidence", 0),
                "requires_signing": requires_signing,
                "wisdom_category": wisdom_result.get("category"),
                "timestamp": timestamp,
            }
        }
        if metadata:
            receipt["metadata"].update(metadata)

        ledger_result = self._anchor_to_ledger(receipt)
        result["stages"]["ledger"] = ledger_result

        # ── STAGE 6: PAPERLESS ROUTING DECISION ──
        if requires_signing:
            result["stages"]["paperless"] = {
                "status": "AWAITING_HUMAN_DECISION",
                "action": "Document classified as requiring QES signature",
                "invariant_i9": "Human must initiate signing via Schnittstelle",
                "command": f"python3 /opt/windi/tsil/schnittstelle.py sign"
            }
        else:
            result["stages"]["paperless"] = {
                "status": "NOT_REQUIRED",
                "reason": f"Document type {doc_type} does not require digital signature"
            }

        # ── FINAL RESULT ──
        result["success"] = True
        result["summary"] = {
            "pipeline_id": pipeline_id,
            "doc_type": doc_type,
            "impact": impact,
            "words_extracted": ocr_result.get("word_count", 0),
            "confidence": ocr_result.get("avg_confidence", 0),
            "proof_hash": proof_hash[:24] + "...",
            "signing_required": requires_signing,
            "ledger_anchored": ledger_result.get("success", False),
            "autonomous": True
        }

        return result

    def _classify_document(self, text: str) -> tuple:
        """Classify document type from extracted text using trilingual rules."""
        text_lower = text.lower()
        scores = {}

        for doc_type, rules in self.DOC_TYPE_RULES.items():
            score = 0
            for lang_key in ["keywords_de", "keywords_en", "keywords_pt"]:
                for kw in rules.get(lang_key, []):
                    if kw in text_lower:
                        score += 1

            if score > 0:
                scores[doc_type] = {
                    "score": score,
                    "impact": rules["impact"],
                    "requires_signing": rules["requires_signing"]
                }

        if not scores:
            return ("UNKNOWN", "LOW", False)

        best = max(scores.items(), key=lambda x: x[1]["score"])
        return (best[0], best[1]["impact"], best[1]["requires_signing"])

    def _anchor_to_ledger(self, receipt: Dict) -> Dict:
        """Anchor receipt to Forensic Ledger via API (:8101).

        Format compatible with Forensic Ledger SQLite schema:
        - id: "VR-PB-{hash}" (VR = Virtue Receipt)
        - created_at: unix epoch seconds (INTEGER)
        - actor: "paperless-bridge"
        - app: "paperless-bridge"
        - doc_name, doc_type, content_hash
        - governance_level: LOW|MEDIUM|HIGH
        - sge_score: 0.0 - 1.0
        - metadata: extensible JSON
        """
        import time as _time

        # Map impact level to governance level
        impact_to_gov = {"LOW": "LOW", "MED": "MEDIUM", "HIGH": "HIGH", "CRIT": "HIGH"}
        gov_level = impact_to_gov.get(receipt.get("governance_level", "LOW"), "MEDIUM")

        try:
            # Build Ledger-compatible payload matching SQLite schema
            # doc_type must be: doc|xlsx|pptx|jmpg|communique|compliance_passport
            # We use "doc" for scanned documents, classification goes in metadata
            ledger_payload = {
                "id": receipt.get("id"),
                "created_at": int(_time.time()),  # Unix epoch seconds
                "actor": "paperless-bridge",
                "device_id": None,
                "app": "windi-paperless-bridge",
                "doc_name": receipt.get("doc_name", "unknown"),
                "doc_type": "doc",  # Scanned documents → doc type
                "local_filename": None,
                "content_hash": receipt.get("content_hash"),
                "bytes": None,
                "governance_level": gov_level,
                "sge_score": 0.0,  # Paperless docs not scored by SGE
                "isp_context": "",
                "template_id": None,
                "tags": receipt.get("tags", []),
                "flags": [],
                "status": "sealed",
                "metadata": {
                    **receipt.get("metadata", {}),
                    "classification_type": receipt.get("doc_type", "unknown"),
                    "source": "paperless-ocr-bridge"
                }
            }

            data = json.dumps(ledger_payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.LEDGER_URL}/api/receipts",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode())
                return {"success": True, "receipt_id": result.get("id", receipt["id"]), "status": "ANCHORED"}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:200]
            return {"success": False, "error": f"HTTP {e.code}: {body}", "status": "LEDGER_ERROR"}
        except urllib.error.URLError as e:
            return {"success": False, "error": str(e), "status": "LEDGER_UNREACHABLE"}
        except Exception as e:
            return {"success": False, "error": str(e), "status": "ERROR"}

    def health(self) -> Dict:
        """Full pipeline health check."""
        ocr_health = self.ocr.health()
        cat_health = self.categorizer.health()

        # Check Ledger
        try:
            req = urllib.request.Request(f"{self.LEDGER_URL}/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                ledger_ok = resp.status == 200
        except Exception:
            ledger_ok = False

        # Check Schnittstelle exists
        schnittstelle_exists = os.path.exists("/opt/windi/tsil/schnittstelle.py")

        return {
            "service": "windi-paperless-bridge",
            "version": self.VERSION,
            "status": "ok" if all([
                ocr_health.get("status") == "ok",
                cat_health.get("status") == "ok"
            ]) else "degraded",
            "components": {
                "ocr": ocr_health.get("status", "unknown"),
                "categorizer": cat_health.get("status", "unknown"),
                "ledger": "ok" if ledger_ok else "unreachable",
                "schnittstelle": "available" if schnittstelle_exists else "missing"
            },
            "pipeline": "OCR → Classify → Hash → Ledger → [Paperless QES]",
            "autonomous": True,
            "requires_api_key": False
        }


# ═══ CLI ═══
if __name__ == "__main__":
    bridge = PaperlessBridge()

    if len(sys.argv) < 2:
        print(json.dumps(bridge.health(), indent=2))
        print("\nUsage:")
        print("  python3 paperless_bridge.py health        — Pipeline health check")
        print("  python3 paperless_bridge.py ingest <img>  — Ingest document image")
        print("  python3 paperless_bridge.py test          — Run with test image")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(bridge.health(), indent=2))

    elif cmd == "ingest":
        if len(sys.argv) < 3:
            print("Usage: python3 paperless_bridge.py ingest <image_path> [lang]")
            sys.exit(1)
        img = sys.argv[2]
        lang = sys.argv[3] if len(sys.argv) > 3 else 'auto'
        result = bridge.ingest_document(img, lang=lang)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "test":
        # Use existing test image or create one
        test_img = "/tmp/windi_ocr_test.png"
        if not os.path.exists(test_img):
            print("Creating test image...")
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (600, 300), 'white')
            draw = ImageDraw.Draw(img)
            lines = [
                'Rechnung Nr. INV-2026-0042',
                'Rechnungsdatum: 23. Februar 2026',
                'Netto: EUR 2.100,00',
                'MwSt 19%: EUR 399,00',
                'Brutto: EUR 2.499,00',
                'Zahlungsziel: 30 Tage',
                'Status: APPROVED'
            ]
            y = 20
            for line in lines:
                draw.text((30, y), line, fill='black')
                y += 35
            img.save(test_img)

        result = bridge.ingest_document(test_img, lang='auto')
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("success"):
            s = result["summary"]
            print(f"\n🐉 PIPELINE COMPLETE")
            print(f"   Type: {s['doc_type']} | Impact: {s['impact']}")
            print(f"   Words: {s['words_extracted']} | Conf: {s['confidence']}%")
            print(f"   Proof: {s['proof_hash']}")
            print(f"   Signing: {'⚠️ REQUIRED (I9: Human decides)' if s['signing_required'] else '✅ Not required'}")
            print(f"   Ledger: {'✅ Anchored' if s['ledger_anchored'] else '⚠️ Not anchored'}")
    else:
        print(f"Unknown command: {cmd}")
