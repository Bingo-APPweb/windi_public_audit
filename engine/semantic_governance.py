#!/usr/bin/env python3
"""
WINDI Semantic Governance Engine (SGE) v1.0
Pre-Publication Institutional Risk Detection

Part of WINDI Engine — /opt/windi/engine/
Created: 02 February 2026
Author: Jober Mögele Correa, Chief Governance Officer

This module performs semantic analysis of documents to detect:
- Institutional identity risks (referencing external organizations)
- Journalistic format patterns without Editorial Transparency Notice
- Authority-claiming language without governance backing
- Alignment with WINDI Invariants (I1-I8)

Principle: "The system that governs documents must also govern
its own communication about those documents."
"""

import re
import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict
from pathlib import Path


# ════════════════════════════════════════════════════════════
# ENUMS & DATA CLASSES
# ════════════════════════════════════════════════════════════

class RiskLevel(Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(Enum):
    INSTITUTIONAL_IDENTITY = "INSTITUTIONAL_IDENTITY"
    JOURNALISTIC_FORMAT = "JOURNALISTIC_FORMAT"
    AUTHORITY_CLAIM = "AUTHORITY_CLAIM"
    AUTHORSHIP_AMBIGUITY = "AUTHORSHIP_AMBIGUITY"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
    DISCLOSURE_MISSING = "DISCLOSURE_MISSING"


@dataclass
class Finding:
    """A single semantic governance finding."""
    category: RiskCategory
    risk_level: RiskLevel
    title: str
    description: str
    evidence: str
    location: str  # line number or section
    invariants_impacted: List[str]
    recommended_action: str
    auto_fixable: bool = False


@dataclass
class ScanReport:
    """Complete semantic governance scan report."""
    document_path: str
    document_name: str
    scan_timestamp: str
    scan_hash: str
    engine_version: str = "1.0.0"
    findings: List[Finding] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.NONE
    score: int = 100  # Semantic Governance Score (100 = clean)
    scan_duration_ms: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["findings"] = [
            {**asdict(f), "category": f.category.value,
             "risk_level": f.risk_level.value}
            for f in self.findings
        ]
        d["overall_risk"] = self.overall_risk.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# ════════════════════════════════════════════════════════════
# KNOWLEDGE BASE: Entities, Patterns, Rules
# ════════════════════════════════════════════════════════════

# Layer 1: Sensitive External Entities
MEDIA_ENTITIES = [
    "Wall Street Journal", "WSJ", "New York Times", "NYT",
    "Financial Times", "FT", "Reuters", "Bloomberg",
    "The Economist", "Der Spiegel", "Die Zeit", "FAZ",
    "Frankfurter Allgemeine", "Süddeutsche Zeitung",
    "BBC", "CNN", "Al Jazeera", "The Guardian",
    "Washington Post", "Forbes", "Wired", "TechCrunch",
    "Handelsblatt", "Wirtschaftswoche", "BILD",
    "Associated Press", "AP News", "DPA",
]

GOVERNMENT_ENTITIES = [
    "European Commission", "European Parliament", "EU Council",
    "Bundesregierung", "Bundestag", "Bundesrat",
    "Federal Ministry", "Bundesministerium",
    "BaFin", "Bundesanstalt", "European Central Bank", "ECB",
    "World Bank", "IMF", "International Monetary Fund",
    "United Nations", "UNESCO", "WHO", "UNICEF",
    "White House", "Congress", "Senate",
]

CERTIFICATION_ENTITIES = [
    "ISO", "TÜV", "DIN", "IEEE", "NIST",
    "BSI", "Bundesamt für Sicherheit",
    "CE certified", "FDA approved",
]

FINANCIAL_ENTITIES = [
    "Deutsche Bank", "Commerzbank", "Sparkasse",
    "Goldman Sachs", "JP Morgan", "Morgan Stanley",
    "Banco do Brasil", "Bundesbank",
]

ALL_SENSITIVE_ENTITIES = (
    MEDIA_ENTITIES + GOVERNMENT_ENTITIES +
    CERTIFICATION_ENTITIES + FINANCIAL_ENTITIES
)

# Layer 2: Authority-Claiming Patterns
AUTHORITY_PATTERNS = [
    (r'\b(?:officially?)\s+(?:endorsed|approved|certified|recognized)\b', "Official endorsement claim"),
    (r'\b(?:in\s+partnership\s+with)\b', "Partnership claim"),
    (r'\b(?:endorsed\s+by)\b', "Endorsement claim"),
    (r'\b(?:certified\s+by)\b', "Certification claim"),
    (r'\b(?:published\s+(?:in|by))\b', "Publication attribution"),
    (r'\b(?:authorized\s+by)\b', "Authorization claim"),
    (r'\b(?:approved\s+by)\b', "Approval claim"),
    (r'\b(?:recommended\s+by)\b', "Recommendation claim"),
    (r'\b(?:in\s+cooperation\s+with)\b', "Cooperation claim"),
    (r'\b(?:supported\s+by)\b', "Support claim"),
    (r'\b(?:funded\s+by)\b', "Funding claim"),
    (r'\b(?:commissioned\s+by)\b', "Commission claim"),
    (r'\b(?:on\s+behalf\s+of)\b', "Delegation claim"),
    (r'\b(?:offiziell\s+(?:genehmigt|zertifiziert|anerkannt))\b', "DE: Official claim"),
    (r'\b(?:in\s+Zusammenarbeit\s+mit)\b', "DE: Cooperation claim"),
    (r'\b(?:im\s+Auftrag\s+von)\b', "DE: Commission claim"),
    (r'\b(?:gefördert\s+(?:von|durch))\b', "DE: Funding claim"),
    (r'\b(?:unterstützt\s+(?:von|durch))\b', "DE: Support claim"),
]

# Layer 3: Journalistic Format Indicators
JOURNALISTIC_PATTERNS = [
    (r'^[A-Z][A-Z\s/]+\s*[-—–]\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)', "Dateline pattern (EN)"),
    (r'^[A-Z][a-zäöü]+\s*/\s*[A-Z][a-zäöü]+\s*[-—–]', "Dual-city dateline"),
    (r'(?:said|stated|noted|commented|remarked)\s+(?:a|an|the)\s+\w+\s+(?:official|spokesperson|representative|observer|analyst)', "Anonymous source attribution"),
    (r'(?:sagte|erklärte|betonte|kommentierte)\s+(?:ein|eine|der|die)\s+\w+', "DE: Source attribution"),
    (r'(?:Industry|Market|Regulatory)\s+(?:Response|Implications|Impact|Outlook)', "Trade press section header"),
    (r'This\s+article\s+was\s+reported\s+by', "Reporter attribution"),
    (r'(?:technology|business|finance)\s+correspondent', "Correspondent reference"),
]

# Layer 4: Disclosure/Transparency Markers
DISCLOSURE_MARKERS = [
    "Editorial Transparency Notice",
    "Governance Disclosure",
    "Hinweis",
    "independently produced",
    "not affiliated with",
    "not endorsed by",
    "not published by",
    "editorial format",
    "Editorial-Style Communication",
    "journalistischen Stil",
    "keine Veröffentlichung",
    "nicht verbunden mit",
]

# Layer 5: AI Autonomy Language (should be "human decides")
AUTONOMY_PATTERNS = [
    (r'\b(?:the\s+(?:system|AI|model)\s+(?:decided|determined|concluded|ruled))\b', "AI autonomy language"),
    (r'\b(?:das\s+System\s+(?:entschied|bestimmte|beschloss))\b', "DE: AI autonomy language"),
    (r'\b(?:automatically\s+(?:approved|rejected|certified|authorized))\b', "Automated authority claim"),
    (r'\b(?:automatisch\s+(?:genehmigt|abgelehnt|zertifiziert))\b', "DE: Automated authority claim"),
]

# WINDI Invariant definitions for mapping
INVARIANTS = {
    "I1": {"name": "Sovereignty", "desc": "No borrowed institutional authority"},
    "I2": {"name": "Non-Opacity", "desc": "Full transparency of authorship and origin"},
    "I3": {"name": "Transparency", "desc": "Visible reasoning and decision processes"},
    "I4": {"name": "Jurisdiction", "desc": "No false legal or regulatory authority"},
    "I5": {"name": "No Fabrication", "desc": "No fabricated quotes, endorsements, affiliations"},
    "I6": {"name": "Conflict Structuring", "desc": "Conflicts addressed, not hidden"},
    "I7": {"name": "Institutional", "desc": "Institutional context respected"},
    "I8": {"name": "No Depth Punishment", "desc": "Complexity is not penalized"},
}


# ════════════════════════════════════════════════════════════
# CORE ENGINE
# ════════════════════════════════════════════════════════════

class SemanticGovernanceEngine:
    """
    WINDI Semantic Governance Engine (SGE)

    Scans documents for institutional identity risks,
    governance violations, and transparency gaps.

    Usage:
        engine = SemanticGovernanceEngine()
        report = engine.scan_file("document.html")
        print(report.to_json())
    """

    VERSION = "1.0.0"

    def __init__(self, custom_entities: List[str] = None,
                 strict_mode: bool = False):
        """
        Args:
            custom_entities: Additional sensitive entities to detect
            strict_mode: If True, flag any external entity reference
        """
        self.entities = list(ALL_SENSITIVE_ENTITIES)
        if custom_entities:
            self.entities.extend(custom_entities)
        self.strict_mode = strict_mode

    def scan_file(self, filepath: str) -> ScanReport:
        """Scan a file and return a governance report."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.scan_text(content, filepath)

    def scan_text(self, text: str, source: str = "<inline>") -> ScanReport:
        """Scan text content and return a governance report."""
        start = datetime.now(timezone.utc)

        # Strip HTML tags for semantic analysis but keep structure info
        clean_text = self._strip_html(text)
        is_html = bool(re.search(r'<[^>]+>', text))

        # Generate scan hash
        scan_hash = hashlib.sha256(
            f"{text[:500]}{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]

        report = ScanReport(
            document_path=source,
            document_name=Path(source).name if source != "<inline>" else "<inline>",
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            scan_hash=f"SGE-{scan_hash}",
        )

        # Run all detection layers
        self._layer1_entity_detection(clean_text, text, report)
        self._layer2_authority_claims(clean_text, report)
        self._layer3_journalistic_format(clean_text, text, report)
        self._layer4_disclosure_check(text, clean_text, report)
        self._layer5_autonomy_language(clean_text, report)
        self._layer6_authorship_check(clean_text, text, report)

        # Calculate overall risk and score
        self._calculate_risk(report)

        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        report.scan_duration_ms = int(elapsed)

        return report

    # ── Layer 1: Sensitive Entity Detection ──

    def _layer1_entity_detection(self, text: str, raw: str,
                                  report: ScanReport):
        """Detect references to sensitive external entities."""
        for entity in self.entities:
            # Use word boundary regex to avoid false positives
            # e.g. "BILD" should not match "Erscheinungsbild"
            # Short entities (<=3 chars) require strict boundaries
            if len(entity) <= 3:
                pattern = r'(?<![A-Za-zÀ-ÿ])' + re.escape(entity) + r'(?![A-Za-zÀ-ÿ])'
            else:
                pattern = r'\b' + re.escape(entity) + r'\b'

            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue

            idx = match.start()
            context_start = max(0, idx - 60)
            context_end = min(len(text), idx + len(entity) + 60)
            context = text[context_start:context_end].strip()

            # Determine if inside a disclosure/transparency block
            in_disclosure = self._is_in_disclosure_context(
                raw, entity, idx
            )

            # Determine entity type for risk assessment
            if entity in MEDIA_ENTITIES:
                entity_type = "Media Organization"
                risk = RiskLevel.HIGH
                invariants = ["I1", "I2", "I5"]
            elif entity in GOVERNMENT_ENTITIES:
                entity_type = "Government/Regulatory Body"
                risk = RiskLevel.HIGH
                invariants = ["I1", "I4", "I7"]
            elif entity in CERTIFICATION_ENTITIES:
                entity_type = "Certification Authority"
                risk = RiskLevel.CRITICAL
                invariants = ["I1", "I4", "I5"]
            elif entity in FINANCIAL_ENTITIES:
                entity_type = "Financial Institution"
                risk = RiskLevel.HIGH
                invariants = ["I1", "I4", "I7"]
            else:
                entity_type = "External Organization"
                risk = RiskLevel.MEDIUM
                invariants = ["I1", "I2"]

            # Reduce risk if inside disclosure context
            if in_disclosure:
                risk = RiskLevel.LOW
                description = (
                    f"Reference to {entity_type} '{entity}' found "
                    f"within a disclosure/transparency context. "
                    f"Governance alignment: ADEQUATE."
                )
                action = "No action required — reference is properly governed."
            else:
                description = (
                    f"Reference to {entity_type} '{entity}' detected "
                    f"outside of any disclosure context. This may imply "
                    f"affiliation, endorsement, or authority not held "
                    f"by WINDI."
                )
                action = (
                    f"Add Editorial Transparency Notice disclaiming "
                    f"affiliation with '{entity}', or remove/rephrase "
                    f"the reference to avoid implied association."
                )

            report.findings.append(Finding(
                category=RiskCategory.INSTITUTIONAL_IDENTITY,
                risk_level=risk,
                title=f"{entity_type} Reference: {entity}",
                description=description,
                evidence=f"...{context}...",
                location=self._find_line(text, entity),
                invariants_impacted=invariants,
                recommended_action=action,
            ))

    # ── Layer 2: Authority-Claiming Language ──

    def _layer2_authority_claims(self, text: str, report: ScanReport):
        """Detect authority-claiming language patterns."""
        # Negation prefixes that neutralize authority claims
        negation_patterns = [
            r'\bnot\s+', r'\bno\s+', r'\bnever\s+', r'\bnor\s+',
            r'\bnot\s+affiliated\b.*?', r'\bwithout\s+',
            r'\bnicht\s+', r'\bkeine?\s+', r'\bniemals\s+',
            r'\bprohibited\b', r'\bforbidden\b', r'\bverboten\b',
            r'\bmust\s+not\b', r'\bmay\s+not\b', r'\bshall\s+not\b',
        ]

        for pattern, label in AUTHORITY_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Check for negation in the 60 chars before the match
                prefix_start = max(0, match.start() - 60)
                prefix = text[prefix_start:match.start()].lower()

                is_negated = any(
                    re.search(neg, prefix)
                    for neg in negation_patterns
                )
                if is_negated:
                    continue  # Skip negated authority claims

                context_start = max(0, match.start() - 40)
                context_end = min(len(text), match.end() + 40)
                context = text[context_start:context_end].strip()

                report.findings.append(Finding(
                    category=RiskCategory.AUTHORITY_CLAIM,
                    risk_level=RiskLevel.MEDIUM,
                    title=f"Authority Pattern: {label}",
                    description=(
                        f"Detected language pattern suggesting external "
                        f"authority or endorsement: '{match.group()}'. "
                        f"Verify that this claim is substantiated."
                    ),
                    evidence=f"...{context}...",
                    location=self._find_line(text, match.group()),
                    invariants_impacted=["I1", "I5"],
                    recommended_action=(
                        "Verify the claim is factually accurate and "
                        "supported by documentation. If unsubstantiated, "
                        "rephrase to remove implied authority."
                    ),
                ))

    # ── Layer 3: Journalistic Format Detection ──

    def _layer3_journalistic_format(self, text: str, raw: str,
                                     report: ScanReport):
        """Detect journalistic format patterns."""
        journal_indicators = 0
        detected_patterns = []

        for pattern, label in JOURNALISTIC_PATTERNS:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                journal_indicators += 1
                detected_patterns.append(label)

        if journal_indicators >= 2:
            report.findings.append(Finding(
                category=RiskCategory.JOURNALISTIC_FORMAT,
                risk_level=RiskLevel.MEDIUM,
                title="Journalistic Format Detected",
                description=(
                    f"Document exhibits {journal_indicators} journalistic "
                    f"format indicators: {', '.join(detected_patterns)}. "
                    f"Per POL-001, Editorial Transparency Notice is required."
                ),
                evidence=f"Patterns: {', '.join(detected_patterns)}",
                location="Document-wide",
                invariants_impacted=["I1", "I2"],
                recommended_action=(
                    "Ensure an Editorial Transparency Notice is present "
                    "per POL-001 Section 4. The notice must identify WINDI "
                    "as independent author and disclaim external affiliation."
                ),
            ))

    # ── Layer 4: Disclosure Completeness Check ──

    def _layer4_disclosure_check(self, raw: str, text: str,
                                  report: ScanReport):
        """Check if required disclosures are present."""
        has_journal_format = any(
            f.category == RiskCategory.JOURNALISTIC_FORMAT
            for f in report.findings
        )
        has_entity_refs = any(
            f.category == RiskCategory.INSTITUTIONAL_IDENTITY
            and f.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            for f in report.findings
        )

        if has_journal_format or has_entity_refs:
            disclosure_found = any(
                marker.lower() in text.lower()
                for marker in DISCLOSURE_MARKERS
            )

            if not disclosure_found:
                report.findings.append(Finding(
                    category=RiskCategory.DISCLOSURE_MISSING,
                    risk_level=RiskLevel.HIGH,
                    title="Editorial Transparency Notice Missing",
                    description=(
                        "This document contains journalistic format elements "
                        "and/or references to external institutions, but no "
                        "Editorial Transparency Notice was found. Per POL-001, "
                        "this disclosure is mandatory."
                    ),
                    evidence="No disclosure markers detected in document.",
                    location="Document-wide",
                    invariants_impacted=["I1", "I2", "I5"],
                    recommended_action=(
                        "Add an Editorial Transparency Notice per POL-001 "
                        "Section 4. Template: 'This article was independently "
                        "produced by the WINDI project using a journalistic "
                        "editorial format for research communication purposes. "
                        "It is not affiliated with, endorsed by, or published "
                        "by [entity name] or any related organization.'"
                    ),
                    auto_fixable=True,
                ))

    # ── Layer 5: AI Autonomy Language ──

    def _layer5_autonomy_language(self, text: str, report: ScanReport):
        """Detect language implying AI autonomous decision-making."""
        for pattern, label in AUTONOMY_PATTERNS:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                context_start = max(0, match.start() - 40)
                context_end = min(len(text), match.end() + 40)
                context = text[context_start:context_end].strip()

                report.findings.append(Finding(
                    category=RiskCategory.INVARIANT_VIOLATION,
                    risk_level=RiskLevel.HIGH,
                    title=f"AI Autonomy Language: {label}",
                    description=(
                        f"Detected language suggesting autonomous AI "
                        f"decision-making: '{match.group()}'. WINDI principle: "
                        f"'AI processes. Human decides. WINDI guarantees.'"
                    ),
                    evidence=f"...{context}...",
                    location=self._find_line(text, match.group()),
                    invariants_impacted=["I1", "I3"],
                    recommended_action=(
                        "Rephrase to emphasize human decision-making. "
                        "Example: 'The system recommended X, and the "
                        "human operator approved the action.'"
                    ),
                ))

    # ── Layer 6: Authorship Clarity ──

    def _layer6_authorship_check(self, text: str, raw: str,
                                  report: ScanReport):
        """Check for clear authorship attribution."""
        authorship_markers = [
            "WINDI Publishing House", "WINDI-RECEIPT",
            "Author:", "Autor:", "Verfasser:",
            "windi.publishing.de", "windia4desk.tech",
            "Jober Mögele Correa", "Chief Governance Officer",
        ]

        has_authorship = any(
            marker.lower() in text.lower() or marker.lower() in raw.lower()
            for marker in authorship_markers
        )

        if not has_authorship and len(text) > 500:
            report.findings.append(Finding(
                category=RiskCategory.AUTHORSHIP_AMBIGUITY,
                risk_level=RiskLevel.MEDIUM,
                title="Authorship Attribution Missing",
                description=(
                    "No clear WINDI authorship attribution found in this "
                    "document. For institutional documents, clear author "
                    "identification is required per WINDI governance standards."
                ),
                evidence="No authorship markers detected.",
                location="Document-wide",
                invariants_impacted=["I2", "I3"],
                recommended_action=(
                    "Add WINDI authorship attribution (author name, "
                    "institutional affiliation, WINDI-RECEIPT, or "
                    "governance footer)."
                ),
            ))

    # ── Scoring & Risk Calculation ──

    def _calculate_risk(self, report: ScanReport):
        """Calculate overall risk level and governance score."""
        if not report.findings:
            report.overall_risk = RiskLevel.NONE
            report.score = 100
            return

        # Score penalties by risk level
        penalties = {
            RiskLevel.LOW: 2,
            RiskLevel.MEDIUM: 8,
            RiskLevel.HIGH: 15,
            RiskLevel.CRITICAL: 25,
        }

        total_penalty = sum(
            penalties.get(f.risk_level, 0)
            for f in report.findings
            if f.risk_level != RiskLevel.NONE
        )

        report.score = max(0, 100 - total_penalty)

        # Overall risk = highest individual risk
        risk_order = [
            RiskLevel.NONE, RiskLevel.LOW, RiskLevel.MEDIUM,
            RiskLevel.HIGH, RiskLevel.CRITICAL
        ]
        max_risk = max(
            (f.risk_level for f in report.findings),
            key=lambda r: risk_order.index(r),
            default=RiskLevel.NONE
        )
        report.overall_risk = max_risk

    # ── Utility Methods ──

    def _strip_html(self, html: str) -> str:
        """Remove HTML tags but preserve text content."""
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode common HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&mdash;', '—')
        text = text.replace('&ndash;', '–')
        text = text.replace('&ldquo;', '"')
        text = text.replace('&rdquo;', '"')
        text = text.replace('&lsquo;', "'")
        text = text.replace('&rsquo;', "'")
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&ouml;', 'ö')
        text = text.replace('&auml;', 'ä')
        text = text.replace('&uuml;', 'ü')
        text = text.replace('&szlig;', 'ß')
        # Numeric entities
        text = re.sub(r'&#x([0-9A-Fa-f]+);',
                       lambda m: chr(int(m.group(1), 16)), text)
        text = re.sub(r'&#(\d+);',
                       lambda m: chr(int(m.group(1))), text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _find_line(self, text: str, needle: str) -> str:
        """Find approximate line number of text."""
        idx = text.lower().find(needle.lower())
        if idx == -1:
            return "Unknown"
        line_num = text[:idx].count('\n') + 1
        return f"~Line {line_num}"

    def _is_in_disclosure_context(self, raw: str, entity: str,
                                   approx_idx: int) -> bool:
        """Check if entity reference is within a disclosure block."""
        raw_lower = raw.lower()
        entity_lower = entity.lower()

        # Find all occurrences
        search_start = 0
        while True:
            idx = raw_lower.find(entity_lower, search_start)
            if idx == -1:
                break

            # Check surrounding context (500 chars before and after)
            context_start = max(0, idx - 500)
            context_end = min(len(raw), idx + 500)
            context = raw_lower[context_start:context_end]

            disclosure_keywords = [
                "transparency notice", "governance disclosure",
                "hinweis", "not affiliated", "not endorsed",
                "not published by", "independently produced",
                "keine veröffentlichung", "nicht verbunden",
                "editorial format", "editorial-style",
                "journalistischen stil",
                "no impersonation", "prohibited",
            ]

            if any(kw in context for kw in disclosure_keywords):
                return True

            search_start = idx + 1

        return False


# ════════════════════════════════════════════════════════════
# REPORT FORMATTERS
# ════════════════════════════════════════════════════════════

def format_terminal_report(report: ScanReport) -> str:
    """Format report for terminal/console output."""
    lines = []
    lines.append("═" * 70)
    lines.append("  WINDI SEMANTIC GOVERNANCE SCAN")
    lines.append("  Engine: SGE v" + report.engine_version)
    lines.append("═" * 70)
    lines.append(f"  Document: {report.document_name}")
    lines.append(f"  Path:     {report.document_path}")
    lines.append(f"  Scanned:  {report.scan_timestamp}")
    lines.append(f"  Hash:     {report.scan_hash}")
    lines.append(f"  Duration: {report.scan_duration_ms}ms")
    lines.append("")

    # Risk summary
    risk_colors = {
        "NONE": "✅", "LOW": "🟢", "MEDIUM": "🟡",
        "HIGH": "🟠", "CRITICAL": "🔴"
    }
    risk_icon = risk_colors.get(report.overall_risk.value, "❓")

    lines.append(f"  Overall Risk: {risk_icon} {report.overall_risk.value}")
    lines.append(f"  Governance Score: {report.score}/100")
    lines.append(f"  Findings: {len(report.findings)}")
    lines.append("─" * 70)

    if not report.findings:
        lines.append("")
        lines.append("  ✅ No governance risks detected.")
        lines.append("  Document is semantically compliant.")
    else:
        # Group by category
        by_category: Dict[str, List[Finding]] = {}
        for f in report.findings:
            cat = f.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)

        for cat, findings in by_category.items():
            lines.append("")
            lines.append(f"  [{cat}]")
            for i, f in enumerate(findings, 1):
                icon = risk_colors.get(f.risk_level.value, "❓")
                lines.append(f"  {icon} {f.title}")
                lines.append(f"     Risk: {f.risk_level.value} | "
                             f"Location: {f.location}")
                lines.append(f"     {f.description}")
                lines.append(f"     Evidence: {f.evidence[:100]}...")
                lines.append(f"     Invariants: {', '.join(f.invariants_impacted)}")
                lines.append(f"     Action: {f.recommended_action}")
                if f.auto_fixable:
                    lines.append(f"     🔧 Auto-fixable")
                lines.append("")

    lines.append("═" * 70)

    # Invariant impact summary
    all_invariants = set()
    for f in report.findings:
        all_invariants.update(f.invariants_impacted)

    if all_invariants:
        lines.append("  Invariants Impacted:")
        for inv_id in sorted(all_invariants):
            inv = INVARIANTS.get(inv_id, {})
            lines.append(f"    {inv_id}: {inv.get('name', '?')} — "
                         f"{inv.get('desc', '?')}")
        lines.append("")

    lines.append("═" * 70)
    lines.append(f"  WINDI SGE v{report.engine_version} | "
                 f"Scan: {report.scan_hash}")
    lines.append("  'AI processes. Human decides. WINDI guarantees.'")
    lines.append("═" * 70)

    return "\n".join(lines)


def format_html_badge(report: ScanReport) -> str:
    """Generate an HTML governance badge for embedding."""
    colors = {
        "NONE": ("#27ae60", "CLEAN"),
        "LOW": ("#2ecc71", "LOW RISK"),
        "MEDIUM": ("#f39c12", "MEDIUM RISK"),
        "HIGH": ("#e67e22", "HIGH RISK"),
        "CRITICAL": ("#e74c3c", "CRITICAL"),
    }
    color, label = colors.get(report.overall_risk.value, ("#95a5a6", "?"))

    return (
        f'<div style="display:inline-flex;align-items:center;gap:0.5rem;'
        f'font-family:sans-serif;font-size:0.8rem;">'
        f'<span style="background:#2c3e50;color:#fff;padding:0.25rem 0.5rem;'
        f'border-radius:3px;font-weight:700;">SGE v1.0</span>'
        f'<span style="background:{color};color:#fff;padding:0.25rem 0.6rem;'
        f'border-radius:3px;font-weight:600;">'
        f'Semantic: {report.score}/100 {label}</span>'
        f'<span style="color:#666;font-size:0.7rem;">'
        f'{len(report.findings)} findings | {report.scan_hash}</span>'
        f'</div>'
    )


# ════════════════════════════════════════════════════════════
# MODULE ENTRY POINT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("WINDI Semantic Governance Engine (SGE) v1.0")
        print("Usage: python3 semantic_governance.py <file_or_directory>")
        print("")
        print("Options:")
        print("  --json     Output as JSON")
        print("  --strict   Flag all external entity references")
        print("  --badge    Output HTML badge only")
        sys.exit(0)

    target = sys.argv[1]
    output_json = "--json" in sys.argv
    strict = "--strict" in sys.argv
    badge_only = "--badge" in sys.argv

    engine = SemanticGovernanceEngine(strict_mode=strict)

    paths = []
    target_path = Path(target)
    if target_path.is_dir():
        paths = sorted(target_path.glob("*.html"))
    elif target_path.is_file():
        paths = [target_path]
    else:
        print(f"Error: {target} not found")
        sys.exit(1)

    for p in paths:
        report = engine.scan_file(str(p))
        if badge_only:
            print(format_html_badge(report))
        elif output_json:
            print(report.to_json())
        else:
            print(format_terminal_report(report))
            print("")
