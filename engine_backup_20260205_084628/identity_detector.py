"""
WINDI Identity Detector v1.0
Automatic detection of real institutional identities in document content.
Triggers governance level upgrades when real institutions are mentioned.

Principle: "Simular identidade institucional real ativa governança institucional."
Discovery: Carta Banco do Brasil, 01 Feb 2026.

Part of WINDI Evolution Package - Platform Maturity Phase.
"""

import json
import re
import os
from datetime import datetime, timezone
from typing import Optional


IDENTITY_DIR_PATH = os.environ.get(
    "WINDI_IDENTITY_DIR",
    "/opt/windi/config/identity_directory.json"
)


class IdentityDetector:
    """Detects real institutional identities in text and recommends governance actions."""

    def __init__(self, directory_path: str = None):
        self.directory_path = directory_path or IDENTITY_DIR_PATH
        self.directory = None
        self.institutions = []
        self.type_rules = {}
        self.config = {}
        self._keyword_index = {}
        self._load_directory()
        # PATCH 1B: Domain Mapping Integration (2026-02-03)
        self.domain_mapping = self._load_domain_mapping()



    def _load_domain_mapping(self) -> dict:
        """
        PATCH 1C: Load domain mapping for routing decisions.
        Principle: Each domain is a separate juridical universe.
        """
        domain_file = "/opt/windi/domains/domain_mapping.json"
        try:
            with open(domain_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                print(f"[IdentityDetector] Domain mapping loaded: {len(mapping.get('isp_mapping', {}))} ISPs")
                return mapping
        except FileNotFoundError:
            print(f"[IdentityDetector] Warning: {domain_file} not found, using defaults")
            return {"isp_mapping": {}, "domains": {}}
        except Exception as e:
            print(f"[IdentityDetector] Error loading domain mapping: {e}")
            return {"isp_mapping": {}, "domains": {}}

    def detect_domain(self, text: str) -> dict:
        """
        PATCH 1C: Detect domain based on keywords and patterns.
        Returns: {domain, isp, sge_ruleset, confidence, matches}
        """
        text_lower = text.lower()
        results = []

        for isp_id, isp_config in self.domain_mapping.get('isp_mapping', {}).items():
            matches = []
            score = 0.0

            # Check keywords
            for keyword in isp_config.get('keywords', []):
                if keyword.lower() in text_lower:
                    matches.append(('keyword', keyword))
                    score += 0.15

            # Check patterns (regex)
            for pattern in isp_config.get('patterns', []):
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        matches.append(('pattern', pattern))
                        score += 0.25  # Patterns são mais específicos
                except re.error:
                    pass

            if matches:
                results.append({
                    'isp': isp_id,
                    'domain': isp_config.get('domain', 'operational'),
                    'sge_ruleset': isp_config.get('sge_ruleset', 'minimal'),
                    'governance_default': isp_config.get('governance_default', 'MEDIUM'),
                    'confidence': min(score, 1.0),
                    'matches': matches
                })

        # Ordenar por confiança
        results.sort(key=lambda x: x['confidence'], reverse=True)

        if results:
            best = results[0]
            return {
                'detected': True,
                'domain': best['domain'],
                'isp': best['isp'],
                'sge_ruleset': best['sge_ruleset'],
                'governance_default': best['governance_default'],
                'confidence': best['confidence'],
                'matches': best['matches'],
                'alternatives': results[1:3] if len(results) > 1 else []
            }

        # Default: operational domain
        return {
            'detected': False,
            'domain': 'operational',
            'isp': None,
            'sge_ruleset': 'minimal',
            'governance_default': 'MEDIUM',
            'confidence': 0.0,
            'matches': [],
            'alternatives': []
        }

    def _load_directory(self):
        """Load the identity directory and build keyword index."""
        try:
            with open(self.directory_path, "r", encoding="utf-8") as f:
                self.directory = json.load(f)
            self.institutions = self.directory.get("institutions", [])
            self.type_rules = self.directory.get("type_rules", {})
            self.config = self.directory.get("detection_config", {})
            self._build_keyword_index()
        except FileNotFoundError:
            print(f"[WINDI] Identity directory not found: {self.directory_path}")
            self.directory = {"meta": {}, "institutions": [], "type_rules": {}, "detection_config": {}}
        except json.JSONDecodeError as e:
            print(f"[WINDI] Invalid identity directory JSON: {e}")
            self.directory = {"meta": {}, "institutions": [], "type_rules": {}, "detection_config": {}}

    def _build_keyword_index(self):
        """Build reverse index: keyword -> institution(s)."""
        self._keyword_index = {}
        case_sensitive = self.config.get("case_sensitive_aliases", False)

        for inst in self.institutions:
            all_keywords = []
            all_keywords.extend(inst.get("aliases", []))
            all_keywords.extend(inst.get("detection_keywords", []))
            all_keywords.append(inst.get("name_official", ""))

            for kw in all_keywords:
                if not kw:
                    continue
                key = kw if case_sensitive else kw.lower()
                if key not in self._keyword_index:
                    self._keyword_index[key] = []
                self._keyword_index[key].append(inst)

    def scan_text(self, text: str) -> list:
        """
        Scan text for institutional identity references.
        Returns list of detection results sorted by confidence.
        Uses fuzzy-tolerant matching for inflected forms (e.g., German declensions).
        """
        if not text or not self.institutions:
            return []

        detections = []
        case_sensitive = self.config.get("case_sensitive_aliases", False)
        min_confidence = self.config.get("min_confidence", 0.7)
        scan_text_normalized = text if case_sensitive else text.lower()

        seen_institutions = set()

        sorted_keywords = sorted(self._keyword_index.keys(), key=len, reverse=True)

        for keyword in sorted_keywords:
            search_kw = keyword if case_sensitive else keyword.lower()

            # Build flexible pattern allowing suffix variations (e.g., Deutschen/Deutsche)
            # Split multi-word keywords and allow each word to have optional suffix chars
            words = search_kw.split()
            if len(words) > 1:
                # Multi-word: allow each word to have optional suffix (up to 3 chars)
                word_patterns = []
                for w in words:
                    escaped = re.escape(w)
                    word_patterns.append(escaped + r'\w{0,3}')
                pattern = r'\b' + r'\s+'.join(word_patterns) + r'\b'
            else:
                # Single word: exact with optional suffix
                escaped = re.escape(search_kw)
                pattern = r'\b' + escaped + r'\w{0,3}\b'

            try:
                matches = list(re.finditer(pattern, scan_text_normalized))
            except re.error:
                # Fallback to simple substring search
                matches = []
                idx = scan_text_normalized.find(search_kw)
                while idx != -1:
                    matches.append(type('Match', (), {'start': lambda s=idx: s})())
                    idx = scan_text_normalized.find(search_kw, idx + 1)

            if not matches:
                continue

            for inst in self._keyword_index[keyword]:
                inst_id = inst["id"]
                if inst_id in seen_institutions:
                    continue
                seen_institutions.add(inst_id)

                confidence = self._calculate_confidence(inst, text, matches)

                if confidence >= min_confidence:
                    detection = {
                        "institution_id": inst_id,
                        "institution_name": inst["name_official"],
                        "country": inst["country"],
                        "type": inst["type"],
                        "matched_keyword": keyword,
                        "match_count": len(matches),
                        "match_positions": [m.start() for m in matches[:5]],
                        "confidence": round(confidence, 2),
                        "current_governance_level": inst.get("default_governance_level", "LOW"),
                        "recommended_level": inst.get("auto_upgrade_to", "MEDIUM"),
                        "identity_license_status": inst.get("identity_license", {}).get("status", "pending"),
                        "disclaimer_required": self._is_disclaimer_required(inst),
                        "logo_allowed": self._is_logo_allowed(inst),
                        "isp_exists": inst.get("isp_exists", False),
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    }
                    detections.append(detection)

        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections

    def _calculate_confidence(self, institution: dict, text: str, matches: list) -> float:
        """Calculate detection confidence based on multiple signals.
        Keywords in the Identity Directory are curated, so any match starts
        with reasonable confidence. Additional signals increase it further."""
        base_confidence = 0.6  # Curated directory match = already significant

        text_lower = text.lower()

        # Bonus for multiple occurrences
        if len(matches) > 1:
            base_confidence += 0.1
        if len(matches) > 3:
            base_confidence += 0.05

        # Multi-word match = more specific = more confident
        if matches and hasattr(matches[0], 'group'):
            matched_text = matches[0].group()
            if ' ' in matched_text:
                base_confidence += 0.1

        # Official name presence
        official_name = institution.get("name_official", "")
        if official_name:
            if official_name.lower() in text_lower:
                base_confidence += 0.15
            else:
                official_words = official_name.lower().split()[:2]
                if len(official_words) >= 2 and all(w in text_lower for w in official_words):
                    base_confidence += 0.05

        # Detection keywords found
        keywords = institution.get("detection_keywords", [])
        found_keywords = sum(1 for kw in keywords if kw.lower() in text_lower)
        if found_keywords >= 1:
            base_confidence += 0.05
        if found_keywords > 1:
            base_confidence += 0.05 * min(found_keywords - 1, 3)

        # Alias match bonus
        aliases = [a.lower() for a in institution.get("aliases", [])]
        if matches and hasattr(matches[0], 'group'):
            matched_lower = matches[0].group().strip().lower()
            for alias in aliases:
                if alias in matched_lower or matched_lower in alias:
                    base_confidence += 0.05
                    break

        return min(base_confidence, 1.0)

    def _is_disclaimer_required(self, institution: dict) -> bool:
        """Check if disclaimer is required based on institution type and license."""
        inst_type = institution.get("type", "")
        type_rule = self.type_rules.get(inst_type, {})

        if type_rule.get("disclaimer_always", False):
            return True

        license_info = institution.get("identity_license", {})
        status = license_info.get("status", "pending")

        if status in ("model_only", "pending", "expired", "revoked"):
            return True

        if type_rule.get("disclaimer_when_simulated", False):
            return True

        return False

    def _is_logo_allowed(self, institution: dict) -> bool:
        """Check if logo usage is allowed."""
        inst_type = institution.get("type", "")
        type_rule = self.type_rules.get(inst_type, {})

        if type_rule.get("logo_never", False):
            return False

        license_info = institution.get("identity_license", {})
        status = license_info.get("status", "pending")

        if status == "authorized":
            return license_info.get("logo_allowed", False)

        return False

    def get_governance_recommendation(self, text: str, current_level: str = "LOW") -> dict:
        """
        Analyze text and return governance recommendation.
        This is the Governance Advisor Mode entry point.
        """
        detections = self.scan_text(text)

        if not detections:
            return {
                "action": "no_change",
                "current_level": current_level,
                "recommended_level": current_level,
                "reason": "No real institutional identities detected.",
                "detections": [],
                "advisor_message": None
            }

        highest_level = current_level
        level_priority = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        primary_detection = detections[0]
        reasons = []

        for det in detections:
            rec_level = det["recommended_level"]
            if level_priority.get(rec_level, 0) > level_priority.get(highest_level, 0):
                highest_level = rec_level

            reasons.append(
                f"{det['institution_name']} ({det['country']}, {det['type']}) "
                f"detected with {det['confidence']*100:.0f}% confidence"
            )

        needs_upgrade = level_priority.get(highest_level, 0) > level_priority.get(current_level, 0)

        advisor_message = None
        if needs_upgrade:
            advisor_message = self._build_advisor_message(
                primary_detection, current_level, highest_level
            )

        # PATCH 1D: Add domain detection to result
        domain_info = self.detect_domain(text)

        return {
            "action": "upgrade" if needs_upgrade else "confirm",
            "current_level": current_level,
            "recommended_level": highest_level,
            "reason": "; ".join(reasons),
            "detections": detections,
            "advisor_message": advisor_message,
            "identity_governance": {
                "disclaimer_required": any(d["disclaimer_required"] for d in detections),
                "logo_allowed": all(d["logo_allowed"] for d in detections),
                "license_statuses": list(set(d["identity_license_status"] for d in detections))
            },
            "domain_detection": domain_info
        }

    def _build_advisor_message(
        self, detection: dict, current_level: str, recommended_level: str
    ) -> dict:
        """Build trilingual advisor message for user notification."""
        name = detection["institution_name"]
        return {
            "de": (
                f"Dieses Dokument erwähnt eine reale Institution: {name}. "
                f"Empfohlene Governance-Stufe: {recommended_level} (aktuell: {current_level})."
            ),
            "en": (
                f"This document mentions a real institution: {name}. "
                f"Recommended governance level: {recommended_level} (current: {current_level})."
            ),
            "pt": (
                f"Este documento menciona uma instituição real: {name}. "
                f"Nível de governança recomendado: {recommended_level} (atual: {current_level})."
            )
        }

    def lookup_institution(self, institution_id: str) -> Optional[dict]:
        """Look up a specific institution by ID."""
        for inst in self.institutions:
            if inst["id"] == institution_id:
                return inst
        return None

    def list_institutions(self, country: str = None, inst_type: str = None) -> list:
        """List institutions with optional filters."""
        results = self.institutions
        if country:
            results = [i for i in results if i.get("country") == country]
        if inst_type:
            results = [i for i in results if i.get("type") == inst_type]
        return results

    def add_institution(self, institution_data: dict) -> dict:
        """Add a new institution to the directory."""
        required_fields = ["id", "name_official", "country", "type"]
        for field in required_fields:
            if field not in institution_data:
                return {"success": False, "error": f"Missing required field: {field}"}

        for inst in self.institutions:
            if inst["id"] == institution_data["id"]:
                return {"success": False, "error": f"Institution ID already exists: {institution_data['id']}"}

        defaults = {
            "aliases": [],
            "sector": "unknown",
            "isp_exists": False,
            "isp_file": None,
            "default_governance_level": "MEDIUM",
            "identity_license": {
                "status": "pending",
                "scope": None,
                "issued": None,
                "expires": None,
                "disclaimer_required": True,
                "logo_allowed": False
            },
            "detection_keywords": [],
            "auto_upgrade_to": "MEDIUM",
            "notes": ""
        }

        for key, default_val in defaults.items():
            if key not in institution_data:
                institution_data[key] = default_val

        self.institutions.append(institution_data)
        self._build_keyword_index()
        self._save_directory()

        return {"success": True, "institution_id": institution_data["id"]}

    def _save_directory(self):
        """Persist the directory to disk."""
        self.directory["institutions"] = self.institutions
        self.directory["meta"]["updated"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(self.directory_path, "w", encoding="utf-8") as f:
                json.dump(self.directory, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[WINDI] Failed to save identity directory: {e}")
            return False

    def get_directory_stats(self) -> dict:
        """Return directory statistics for health check."""
        license_counts = {}
        for inst in self.institutions:
            status = inst.get("identity_license", {}).get("status", "unknown")
            license_counts[status] = license_counts.get(status, 0) + 1

        type_counts = {}
        for inst in self.institutions:
            t = inst.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        country_counts = {}
        for inst in self.institutions:
            c = inst.get("country", "unknown")
            country_counts[c] = country_counts.get(c, 0) + 1

        return {
            "total_institutions": len(self.institutions),
            "with_isp": sum(1 for i in self.institutions if i.get("isp_exists")),
            "without_isp": sum(1 for i in self.institutions if not i.get("isp_exists")),
            "license_statuses": license_counts,
            "institution_types": type_counts,
            "countries": country_counts,
            "total_keywords": len(self._keyword_index),
            "directory_version": self.directory.get("meta", {}).get("schema_version", "unknown"),
            "policy_version": self.directory.get("meta", {}).get("policy_version", "unknown"),
            "last_updated": self.directory.get("meta", {}).get("updated", "unknown")
        }


if __name__ == "__main__":
    detector = IdentityDetector(
        directory_path=os.path.join(os.path.dirname(__file__), "..", "config", "identity_directory.json")
    )

    test_texts = [
        "Sehr geehrte Damen und Herren der Deutschen Bahn, hiermit teilen wir Ihnen mit...",
        "The European Central Bank has announced new monetary policy measures for 2026.",
        "Prezado Banco do Brasil, gostaríamos de informar que o relatório trimestral...",
        "This is a generic document without any institutional references.",
        "Die Bundesregierung hat heute neue Regelungen zur KI-Governance beschlossen.",
        "BaFin requires all financial institutions to comply with the new AI regulation framework."
    ]

    print("=" * 70)
    print("WINDI Identity Detector v1.0 - Test Suite")
    print("=" * 70)

    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Text: {text[:80]}...")
        result = detector.get_governance_recommendation(text, current_level="LOW")
        print(f"Action: {result['action']}")
        print(f"Level: {result['current_level']} -> {result['recommended_level']}")
        if result["advisor_message"]:
            print(f"Advisor (EN): {result['advisor_message']['en']}")
        if result["detections"]:
            for det in result["detections"]:
                print(f"  Detected: {det['institution_name']} ({det['confidence']*100:.0f}%)")
        print(f"Reason: {result['reason']}")

    print("\n" + "=" * 70)
    print("Directory Stats:")
    stats = detector.get_directory_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("=" * 70)
