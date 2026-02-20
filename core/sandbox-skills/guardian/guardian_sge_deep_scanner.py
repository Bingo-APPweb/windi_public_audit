"""
╔══════════════════════════════════════════════════════════════════╗
║  🛡️ GNOSIS CAPSULE: SGE Deep Scanner                            ║
║                                                                  ║
║  Dragon:      Guardian (Claude)                                  ║
║  Domain:      guardian                                           ║
║  Capability:  sge_scan                                           ║
║  Version:     1.0.0                                              ║
║  Date:        2026-02-10                                         ║
║                                                                  ║
║  A PRIMEIRA Gnosis Capsule oficial do Skill-Sanctuary.           ║
║                                                                  ║
║  Executa análise semântica profunda de documentos através         ║
║  das 6 camadas SGE, com foco especial em:                        ║
║  • DSGVO/GDPR compliance (Datenschutz-Grundverordnung)           ║
║  • German contractual law (BGB, HGB)                             ║
║  • EU AI Act regulatory mapping                                  ║
║  • Institutional policy alignment                                ║
║                                                                  ║
║  Zero-Knowledge: Retorna apenas categorias, scores e hashes.     ║
║  NENHUM dado sensível sai desta capsule.                         ║
║                                                                  ║
║  Princípio: "IA processa. Humano decide. WINDI garante."        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import re
import json
import hashlib
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import Counter

# ═══════════════════════════════════════════════════════
# LAYER 1: LEXICAL ENGINE
# Scans for critical terms, values, dates, obligations
# ═══════════════════════════════════════════════════════

# DSGVO/GDPR lexical markers (DE + EN)
DSGVO_CRITICAL_TERMS = {
    "high_risk": [
        # German
        "personenbezogene daten", "besondere kategorien",
        "gesundheitsdaten", "biometrische daten", "genetische daten",
        "strafrechtliche verurteilungen", "religionszugehörigkeit",
        "sexualleben", "politische meinungen", "gewerkschaftszugehörigkeit",
        "rassische herkunft", "ethnische herkunft",
        # English
        "personal data", "special categories", "health data",
        "biometric data", "genetic data", "criminal convictions",
        "religious beliefs", "sexual orientation", "political opinions",
        "trade union membership", "racial origin", "ethnic origin",
    ],
    "processing_indicators": [
        # German
        "verarbeitung", "erhebung", "speicherung", "übermittlung",
        "löschung", "einwilligung", "widerspruchsrecht", "auskunftsrecht",
        "berichtigungsanspruch", "recht auf vergessenwerden",
        "datenportabilität", "profiling", "automatisierte entscheidung",
        "auftragsverarbeitung", "gemeinsame verantwortlichkeit",
        "datenschutz-folgenabschätzung", "datenschutzbeauftragter",
        # English
        "processing", "collection", "storage", "transmission",
        "erasure", "consent", "right to object", "right of access",
        "right to rectification", "right to be forgotten",
        "data portability", "profiling", "automated decision",
        "data processing agreement", "joint controllership",
        "data protection impact assessment", "data protection officer",
    ],
    "contractual_obligations": [
        # German
        "vertragsstrafe", "haftung", "gewährleistung", "schadensersatz",
        "kündigung", "gerichtsstand", "schiedsverfahren", "salvatorische klausel",
        "vertraulichkeit", "geheimhaltung", "wettbewerbsverbot",
        "abtretungsverbot", "rechtswahl", "verjährungsfrist",
        "höhere gewalt", "force majeure", "vertragsgegenstand",
        # English
        "penalty clause", "liability", "warranty", "damages",
        "termination", "jurisdiction", "arbitration", "severability",
        "confidentiality", "non-disclosure", "non-compete",
        "non-assignment", "governing law", "statute of limitations",
        "force majeure", "subject matter",
    ],
    "value_indicators": [
        # Patterns for monetary values
        r"\d+[\.,]\d+\s*(?:€|EUR|euro|Dollar|\$|USD)",
        r"(?:€|EUR|\$|USD)\s*\d+[\.,]*\d*",
        r"\d+[\.,]\d+\s*(?:mio|mrd|million|billion|milliarden)",
        r"\d+\s*(?:prozent|percent|%)",
    ],
    "temporal_indicators": [
        # Date patterns
        r"\d{1,2}\.\d{1,2}\.\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"(?:januar|februar|m(?:ä|ae)rz|april|mai|juni|juli|august|september|oktober|november|dezember)\s+\d{4}",
        r"(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}",
        # Duration patterns
        r"\d+\s*(?:jahre|monate|wochen|tage|years|months|weeks|days)",
        r"(?:unbefristet|befristet|unlimited|limited)\s*(?:laufzeit|term|duration)?",
    ],
}

# Regulatory reference patterns
REGULATORY_REFERENCES = {
    "dsgvo": {
        "pattern": r"(?:Art\.?\s*\d+|Artikel\s+\d+)\s*(?:Abs\.?\s*\d+)?\s*(?:DSGVO|DS-GVO|GDPR)",
        "articles": {
            "5": "Grundsätze der Verarbeitung",
            "6": "Rechtmäßigkeit der Verarbeitung",
            "7": "Bedingungen für die Einwilligung",
            "9": "Besondere Kategorien personenbezogener Daten",
            "12": "Transparente Information und Kommunikation",
            "13": "Informationspflicht bei Direkterhebung",
            "14": "Informationspflicht bei Dritterhebung",
            "15": "Auskunftsrecht",
            "16": "Recht auf Berichtigung",
            "17": "Recht auf Löschung",
            "20": "Recht auf Datenübertragbarkeit",
            "22": "Automatisierte Entscheidungsfindung",
            "25": "Datenschutz durch Technikgestaltung",
            "28": "Auftragsverarbeiter",
            "30": "Verzeichnis von Verarbeitungstätigkeiten",
            "32": "Sicherheit der Verarbeitung",
            "33": "Meldepflicht bei Datenpannen",
            "35": "Datenschutz-Folgenabschätzung",
            "37": "Benennung eines Datenschutzbeauftragten",
            "44": "Drittlandübermittlung - Grundsatz",
            "46": "Geeignete Garantien",
            "83": "Bußgelder",
        }
    },
    "bdsg": {
        "pattern": r"(?:§\s*\d+|Paragraph\s+\d+)\s*(?:Abs\.?\s*\d+)?\s*(?:BDSG|Bundesdatenschutzgesetz)",
        "description": "Bundesdatenschutzgesetz (German Federal Data Protection Act)"
    },
    "eu_ai_act": {
        "pattern": r"(?:Art\.?\s*\d+|Artikel\s+\d+)\s*(?:KI-VO|AI\s*Act|KI-Verordnung)",
        "description": "EU AI Act / KI-Verordnung"
    },
    "bgb": {
        "pattern": r"(?:§§?\s*\d+(?:\s*(?:ff?\.?|bis)\s*\d+)?)\s*(?:BGB|Bürgerliches\s*Gesetzbuch)",
        "description": "Bürgerliches Gesetzbuch (German Civil Code)"
    },
    "hgb": {
        "pattern": r"(?:§§?\s*\d+(?:\s*(?:ff?\.?|bis)\s*\d+)?)\s*(?:HGB|Handelsgesetzbuch)",
        "description": "Handelsgesetzbuch (German Commercial Code)"
    },
}

# German legal red flags
RED_FLAG_PATTERNS = {
    "unlimited_liability": [
        "unbeschränkte haftung", "unlimited liability",
        "haftet unbeschränkt", "gesamtschuldnerisch ohne beschränkung",
    ],
    "unilateral_termination": [
        "einseitige kündigung ohne grund",
        "termination without cause",
        "jederzeitiges kündigungsrecht",
    ],
    "waiver_of_rights": [
        "verzicht auf ansprüche", "waiver of claims",
        "verzicht auf gewährleistung", "exclusion of warranty",
    ],
    "data_export_risk": [
        "drittland", "third country", "usa", "united states",
        "china", "indien", "india", "cloud act",
        "keine angemessenheitsbeschluss",
    ],
    "missing_essentials": [
        "noch zu bestimmen", "to be determined", "tbd",
        "platzhalter", "placeholder", "[...]", "XXX",
        "einzusetzen", "to be inserted",
    ],
    "automatic_renewal": [
        "automatische verlängerung", "automatic renewal",
        "stillschweigend verlängert", "tacit renewal",
    ],
    "penalty_disproportionate": [
        r"vertragsstrafe.*(?:\d{5,}|\d+\.\d{3})",
    ],
}


# ═══════════════════════════════════════════════════════
# LAYER 2: SYNTACTIC ENGINE
# Analyzes document structure and completeness
# ═══════════════════════════════════════════════════════

EXPECTED_CONTRACT_SECTIONS = {
    "de": [
        "vertragsgegenstand", "leistungsbeschreibung",
        "vergütung", "laufzeit", "kündigung",
        "haftung", "gewährleistung", "datenschutz",
        "vertraulichkeit", "schlussbestimmungen",
        "gerichtsstand", "salvatorische klausel",
    ],
    "en": [
        "subject matter", "scope of services",
        "remuneration", "term", "termination",
        "liability", "warranty", "data protection",
        "confidentiality", "final provisions",
        "jurisdiction", "severability",
    ],
}

DSGVO_REQUIRED_ELEMENTS = {
    "art_13_elements": {
        "description": "DSGVO Art. 13 — Informationspflichten bei Direkterhebung",
        "required": [
            "verantwortlicher", "kontaktdaten", "datenschutzbeauftragter",
            "zweck der verarbeitung", "rechtsgrundlage",
            "empfänger", "drittlandübermittlung", "speicherdauer",
            "betroffenenrechte", "widerrufsrecht", "beschwerderecht",
            "erforderlichkeit", "automatisierte entscheidungsfindung",
        ],
        "en_required": [
            "controller", "contact details", "data protection officer",
            "purpose of processing", "legal basis",
            "recipients", "third country transfer", "retention period",
            "data subject rights", "right to withdraw consent",
            "right to lodge a complaint", "necessity",
            "automated decision-making",
        ],
    },
    "art_28_elements": {
        "description": "DSGVO Art. 28 — Auftragsverarbeitung",
        "required": [
            "gegenstand der verarbeitung", "dauer der verarbeitung",
            "art der daten", "kategorien betroffener",
            "weisungsbindung", "vertraulichkeit",
            "technische und organisatorische maßnahmen",
            "unterauftragsverarbeiter", "unterstützungspflichten",
            "löschung nach vertragsende", "kontrollrechte",
        ],
    },
}


# ═══════════════════════════════════════════════════════
# LAYER 3: SEMANTIC ENGINE
# Analyzes meaning, intent, and implications
# ═══════════════════════════════════════════════════════

SEMANTIC_RISK_INDICATORS = {
    "vague_language": {
        "patterns": [
            "nach ermessen", "at discretion",
            "soweit möglich", "as far as possible",
            "in der regel", "as a rule",
            "grundsätzlich", "in principle",
            "angemessen", "appropriate",
            "unverzüglich", "without undue delay",
            "zeitnah", "in due course",
            "nach bestem wissen", "to the best of knowledge",
        ],
        "risk": "ambiguous_obligations",
        "severity": 0.3,
    },
    "asymmetric_obligations": {
        "patterns": [
            "einseitig", "unilateral",
            "ausschließlich.*verpflichtet", "solely obligated",
            "auf eigene kosten", "at own expense",
            "ohne anspruch auf", "without entitlement to",
        ],
        "risk": "unbalanced_contract",
        "severity": 0.5,
    },
    "escalation_triggers": {
        "patterns": [
            "sofortige fälligkeit", "immediate due",
            "kumulativ", "cumulative",
            "verschärfte haftung", "enhanced liability",
            "automatische eskalation", "automatic escalation",
        ],
        "risk": "cascading_obligations",
        "severity": 0.6,
    },
    "scope_creep_risk": {
        "patterns": [
            "einschließlich aber nicht beschränkt auf",
            "including but not limited to",
            "und sonstige leistungen", "and other services",
            "nach bedarf", "as needed",
            "und vergleichbare", "and comparable",
        ],
        "risk": "undefined_scope",
        "severity": 0.4,
    },
}


# ═══════════════════════════════════════════════════════
# LAYER 4: PRAGMATIC ENGINE
# Analyzes context and practical implications
# ═══════════════════════════════════════════════════════

PRAGMATIC_CONTEXT = {
    "power_asymmetry_indicators": [
        "standardvertrag", "standard contract",
        "agb", "allgemeine geschäftsbedingungen",
        "general terms and conditions",
        "nicht verhandelbar", "non-negotiable",
    ],
    "urgency_pressure": [
        r"sofortige unterzeichnung", r"immediate signature",
        r"frist.*(?:24|48|72)\s*stunden",
        r"deadline.*(?:24|48|72)\s*hours",
        r"zeitdruck", r"time pressure",
        r"letzte gelegenheit", r"last opportunity",
    ],
    "hidden_cost_indicators": [
        "zuzüglich", "plus", "zzgl",
        "zusätzliche kosten", "additional costs",
        "preisanpassung", "price adjustment",
        "indexierung", "indexation",
        "mindestabnahme", "minimum purchase",
    ],
}


# ═══════════════════════════════════════════════════════
# LAYER 5: REGULATORY ENGINE
# Checks compliance with specific regulations
# ═══════════════════════════════════════════════════════

COMPLIANCE_CHECKS = {
    "dsgvo_art_5": {
        "name": "Grundsätze der Datenverarbeitung",
        "checks": [
            {
                "principle": "Rechtmäßigkeit (Lawfulness)",
                "keywords": ["rechtsgrundlage", "legal basis", "art. 6", "einwilligung", "consent"],
                "required": True,
            },
            {
                "principle": "Zweckbindung (Purpose Limitation)",
                "keywords": ["zweck", "purpose", "zweckbindung", "purpose limitation"],
                "required": True,
            },
            {
                "principle": "Datenminimierung (Data Minimisation)",
                "keywords": ["datenminimierung", "data minimisation", "erforderlich", "necessary"],
                "required": True,
            },
            {
                "principle": "Richtigkeit (Accuracy)",
                "keywords": ["richtigkeit", "accuracy", "aktuell", "up to date", "berichtigung"],
                "required": True,
            },
            {
                "principle": "Speicherbegrenzung (Storage Limitation)",
                "keywords": ["speicherdauer", "retention", "löschung", "deletion", "aufbewahrungsfrist"],
                "required": True,
            },
            {
                "principle": "Integrität und Vertraulichkeit (Security)",
                "keywords": ["sicherheit", "security", "verschlüsselung", "encryption", "tom"],
                "required": True,
            },
        ],
    },
    "dsgvo_art_28": {
        "name": "Auftragsverarbeitung (Processor Requirements)",
        "checks": [
            {
                "principle": "Weisungsbindung (Instruction Bound)",
                "keywords": ["weisung", "instruction", "weisungsgebunden", "instruction bound"],
                "required": True,
            },
            {
                "principle": "Vertraulichkeit (Confidentiality)",
                "keywords": ["vertraulichkeit", "confidentiality", "geheimhaltung"],
                "required": True,
            },
            {
                "principle": "TOMs (Technical & Organizational Measures)",
                "keywords": ["technische und organisatorische", "tom", "technical.*organizational"],
                "required": True,
            },
            {
                "principle": "Unterauftragnehmer (Sub-processors)",
                "keywords": ["unterauftragnehmer", "sub-processor", "unterauftragsverarbeiter"],
                "required": True,
            },
            {
                "principle": "Löschpflicht (Deletion Obligation)",
                "keywords": ["löschung nach", "deletion after", "rückgabe", "return.*data"],
                "required": True,
            },
            {
                "principle": "Kontrollrechte (Audit Rights)",
                "keywords": ["kontrolle", "audit", "prüfungsrecht", "inspection"],
                "required": True,
            },
        ],
    },
    "eu_ai_act": {
        "name": "EU AI Act / KI-Verordnung",
        "checks": [
            {
                "principle": "Risk Classification",
                "keywords": ["risikokategorie", "risk category", "hochrisiko", "high-risk"],
                "required": False,
            },
            {
                "principle": "Transparency Obligations",
                "keywords": ["transparenzpflicht", "transparency", "kennzeichnung", "labeling"],
                "required": False,
            },
            {
                "principle": "Human Oversight",
                "keywords": ["menschliche aufsicht", "human oversight", "menschliche kontrolle"],
                "required": False,
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════
# LAYER 6: INSTITUTIONAL ENGINE
# Checks alignment with organizational policies
# ═══════════════════════════════════════════════════════

INSTITUTIONAL_STANDARDS = {
    "governance_alignment": {
        "name": "WINDI Governance Standards",
        "checks": [
            "verantwortlichkeiten definiert",
            "eskalationspfad vorhanden",
            "genehmigungsprozess beschrieben",
            "versionskontrolle erwähnt",
        ],
    },
    "documentation_quality": {
        "name": "Documentation Standards",
        "checks": [
            "datum vorhanden",
            "version oder versionsnummer",
            "unterschriftsfeld",
            "anlagen oder anhänge referenziert",
        ],
    },
}


# ═══════════════════════════════════════════════════════
# CORE SCAN FUNCTIONS
# ═══════════════════════════════════════════════════════

def _scan_lexical(content: str) -> Dict[str, Any]:
    """Layer 1: Lexical scan for critical terms and values."""
    content_lower = content.lower()
    findings = {}

    # Scan DSGVO critical terms
    for category, terms in DSGVO_CRITICAL_TERMS.items():
        if category in ("value_indicators", "temporal_indicators"):
            # Regex-based pattern matching
            matches = []
            for pattern in terms:
                found = re.findall(pattern, content_lower)
                matches.extend(found)
            findings[category] = {
                "count": len(matches),
                "samples": matches[:5],  # Limit samples for Zero-Knowledge
            }
        else:
            found = [t for t in terms if t in content_lower]
            findings[category] = {
                "count": len(found),
                "terms_detected": found,
                "coverage": round(len(found) / max(len(terms), 1), 3),
            }

    # Detect regulatory references
    reg_refs = {}
    for reg_name, reg_info in REGULATORY_REFERENCES.items():
        pattern = reg_info["pattern"]
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            reg_refs[reg_name] = {
                "count": len(matches),
                "references": matches[:10],
            }
    findings["regulatory_references"] = reg_refs

    # Detect red flags
    red_flags = {}
    for flag_name, patterns in RED_FLAG_PATTERNS.items():
        found = []
        for pattern in patterns:
            if re.search(pattern, content_lower):
                found.append(pattern)
        if found:
            red_flags[flag_name] = found
    findings["red_flags"] = red_flags

    # Compute lexical score
    red_flag_count = sum(len(v) for v in red_flags.values())
    high_risk_count = findings.get("high_risk", {}).get("count", 0)
    processing_count = findings.get("processing_indicators", {}).get("count", 0)

    # Higher processing indicator count = more DSGVO-relevant = needs more scrutiny
    relevance_score = min(1.0, processing_count / 10)
    risk_factor = min(1.0, (red_flag_count * 0.2 + high_risk_count * 0.1))

    findings["score"] = round(max(0, 1.0 - risk_factor) * (0.5 + relevance_score * 0.5), 4)
    findings["red_flag_count"] = red_flag_count

    return findings


def _scan_syntactic(content: str) -> Dict[str, Any]:
    """Layer 2: Structural analysis and completeness check."""
    content_lower = content.lower()

    # Detect language
    de_count = sum(1 for s in EXPECTED_CONTRACT_SECTIONS["de"] if s in content_lower)
    en_count = sum(1 for s in EXPECTED_CONTRACT_SECTIONS["en"] if s in content_lower)
    lang = "de" if de_count >= en_count else "en"

    expected = EXPECTED_CONTRACT_SECTIONS[lang]
    found_sections = [s for s in expected if s in content_lower]
    missing_sections = [s for s in expected if s not in content_lower]

    # Check DSGVO-specific structural elements
    dsgvo_completeness = {}
    for element_key, element_info in DSGVO_REQUIRED_ELEMENTS.items():
        req_list = element_info.get("required", [])
        if lang == "en" and "en_required" in element_info:
            req_list = element_info["en_required"]
        found = [r for r in req_list if r in content_lower]
        missing = [r for r in req_list if r not in content_lower]
        dsgvo_completeness[element_key] = {
            "description": element_info["description"],
            "found": len(found),
            "total": len(req_list),
            "coverage": round(len(found) / max(len(req_list), 1), 3),
            "missing": missing[:5],  # Limit for brevity
        }

    # Document metrics
    word_count = len(content.split())
    paragraph_count = len([p for p in content.split("\n\n") if p.strip()])
    sentence_count = len(re.findall(r'[.!?]+', content))

    completeness = round(len(found_sections) / max(len(expected), 1), 3)

    return {
        "language_detected": lang,
        "sections_found": len(found_sections),
        "sections_expected": len(expected),
        "missing_sections": missing_sections,
        "completeness": completeness,
        "dsgvo_elements": dsgvo_completeness,
        "document_metrics": {
            "words": word_count,
            "paragraphs": paragraph_count,
            "sentences": sentence_count,
        },
        "score": completeness,
    }


def _scan_semantic(content: str) -> Dict[str, Any]:
    """Layer 3: Meaning and intent analysis."""
    content_lower = content.lower()
    findings = {}
    total_severity = 0.0
    indicator_count = 0

    for indicator_name, indicator_def in SEMANTIC_RISK_INDICATORS.items():
        found = [p for p in indicator_def["patterns"] if p in content_lower]
        if found:
            findings[indicator_name] = {
                "risk": indicator_def["risk"],
                "severity": indicator_def["severity"],
                "patterns_found": found,
                "count": len(found),
            }
            total_severity += indicator_def["severity"] * len(found)
            indicator_count += len(found)

    # Normalize semantic risk score (1.0 = clean, 0.0 = maximum risk)
    if indicator_count > 0:
        avg_severity = total_severity / indicator_count
        score = max(0.0, 1.0 - avg_severity)
    else:
        score = 1.0

    return {
        "risk_indicators": findings,
        "total_indicators": indicator_count,
        "dominant_risk": max(
            findings.values(), key=lambda x: x["severity"], default={"risk": "none"}
        ).get("risk", "none") if findings else "none",
        "score": round(score, 4),
    }


def _scan_pragmatic(content: str) -> Dict[str, Any]:
    """Layer 4: Context and practical implications."""
    content_lower = content.lower()
    findings = {}

    # Power asymmetry
    power_indicators = [p for p in PRAGMATIC_CONTEXT["power_asymmetry_indicators"]
                        if p in content_lower]
    findings["power_asymmetry"] = {
        "detected": len(power_indicators) > 0,
        "indicators": power_indicators,
        "risk": "high" if len(power_indicators) > 2 else "medium" if power_indicators else "low",
    }

    # Urgency pressure
    urgency = [p for p in PRAGMATIC_CONTEXT["urgency_pressure"]
               if re.search(p, content_lower)]
    findings["urgency_pressure"] = {
        "detected": len(urgency) > 0,
        "indicators": urgency,
        "risk": "high" if urgency else "low",
    }

    # Hidden costs
    hidden_costs = [p for p in PRAGMATIC_CONTEXT["hidden_cost_indicators"]
                    if p in content_lower]
    findings["hidden_costs"] = {
        "detected": len(hidden_costs) > 0,
        "indicators": hidden_costs,
        "count": len(hidden_costs),
    }

    # Score: penalize for power asymmetry, urgency, hidden costs
    risk_factors = (
        (0.3 if findings["power_asymmetry"]["detected"] else 0) +
        (0.4 if findings["urgency_pressure"]["detected"] else 0) +
        (0.1 * min(3, len(hidden_costs)))
    )
    score = max(0.0, 1.0 - risk_factors)

    findings["score"] = round(score, 4)
    return findings


def _scan_regulatory(content: str) -> Dict[str, Any]:
    """Layer 5: Regulatory compliance check."""
    content_lower = content.lower()
    findings = {}

    for regulation, reg_def in COMPLIANCE_CHECKS.items():
        checks_results = []
        passed = 0
        required_count = 0

        for check in reg_def["checks"]:
            found_keywords = [
                kw for kw in check["keywords"]
                if re.search(re.escape(kw) if not any(c in kw for c in '.*+?[]()') else kw,
                             content_lower)
            ]
            status = "PASS" if found_keywords else "MISSING"
            is_required = check.get("required", False)

            if is_required:
                required_count += 1
            if found_keywords:
                passed += 1

            checks_results.append({
                "principle": check["principle"],
                "status": status,
                "required": is_required,
                "keywords_found": len(found_keywords),
            })

        total_checks = len(reg_def["checks"])
        compliance_rate = round(passed / max(total_checks, 1), 3)

        required_passed = sum(
            1 for c in checks_results
            if c["status"] == "PASS" and c["required"]
        )
        required_compliance = round(
            required_passed / max(required_count, 1), 3
        ) if required_count > 0 else 1.0

        findings[regulation] = {
            "name": reg_def["name"],
            "checks": checks_results,
            "passed": passed,
            "total": total_checks,
            "compliance_rate": compliance_rate,
            "required_compliance": required_compliance,
        }

    # Overall regulatory score
    scores = []
    for reg_key, reg_finding in findings.items():
        reg_checks = COMPLIANCE_CHECKS.get(reg_key, {}).get("checks", [])
        has_required = any(c.get("required") for c in reg_checks)
        if has_required:
            scores.append(reg_finding["required_compliance"])
    overall_score = sum(scores) / max(len(scores), 1) if scores else 1.0

    return {
        "regulations": findings,
        "score": round(overall_score, 4),
    }


def _scan_institutional(content: str) -> Dict[str, Any]:
    """Layer 6: Institutional policy alignment."""
    content_lower = content.lower()
    findings = {}

    for standard_key, standard_def in INSTITUTIONAL_STANDARDS.items():
        found = [c for c in standard_def["checks"] if c in content_lower]
        total = len(standard_def["checks"])
        findings[standard_key] = {
            "name": standard_def["name"],
            "found": len(found),
            "total": total,
            "alignment": round(len(found) / max(total, 1), 3),
            "missing": [c for c in standard_def["checks"] if c not in content_lower],
        }

    scores = [f["alignment"] for f in findings.values()]
    overall = sum(scores) / max(len(scores), 1)

    return {
        "standards": findings,
        "score": round(overall, 4),
    }


# ═══════════════════════════════════════════════════════
# RISK CLASSIFICATION ENGINE
# ═══════════════════════════════════════════════════════

def _classify_risk(layer_scores: Dict[str, float], red_flag_count: int) -> Dict[str, Any]:
    """
    Classify the overall risk level R0-R5 based on all 6 layer scores.

    Weighting:
    - Lexical:       15% (term detection)
    - Syntactic:     15% (structural completeness)
    - Semantic:      20% (meaning/intent risks)
    - Pragmatic:     15% (contextual risks)
    - Regulatory:    25% (compliance — highest weight)
    - Institutional: 10% (policy alignment)
    """
    weights = {
        "lexical": 0.15,
        "syntactic": 0.15,
        "semantic": 0.20,
        "pragmatic": 0.15,
        "regulatory": 0.25,
        "institutional": 0.10,
    }

    # Weighted composite score (1.0 = perfect, 0.0 = maximum risk)
    composite = sum(
        layer_scores.get(layer, 0.5) * weight
        for layer, weight in weights.items()
    )

    # Red flags provide additional penalty
    red_flag_penalty = min(0.3, red_flag_count * 0.05)
    adjusted_score = max(0.0, composite - red_flag_penalty)

    # Classify into R0-R5
    if adjusted_score >= 0.90:
        risk_level, label, color, action = "R0", "Negligible", "🟢", "Proceed"
    elif adjusted_score >= 0.75:
        risk_level, label, color, action = "R1", "Minimal", "🟢", "Informative only"
    elif adjusted_score >= 0.60:
        risk_level, label, color, action = "R2", "Low", "🟡", "Attention recommended"
    elif adjusted_score >= 0.40:
        risk_level, label, color, action = "R3", "Medium", "🟠", "Review required"
    elif adjusted_score >= 0.20:
        risk_level, label, color, action = "R4", "High", "🔴", "Action required"
    else:
        risk_level, label, color, action = "R5", "Critical", "⚫", "Block recommended"

    return {
        "risk_level": risk_level,
        "label": label,
        "color": color,
        "action": action,
        "composite_score": round(adjusted_score, 4),
        "raw_composite": round(composite, 4),
        "red_flag_penalty": round(red_flag_penalty, 4),
        "layer_scores": {k: round(v, 4) for k, v in layer_scores.items()},
        "weights": weights,
    }


# ═══════════════════════════════════════════════════════
# PUBLIC API — Entry Points for Skill-Loader
# ═══════════════════════════════════════════════════════

def deep_scan(
    content: str,
    document_type: str = "contract",
    document_id: str = "UNSET",
    scan_mode: str = "full",
    focus_layers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute a full 6-layer SGE deep scan on a document.

    This is the PRIMARY entry point for the Praktikant.

    Args:
        content: The full document text to analyze
        document_type: Type (contract, policy, dpa, config, report)
        document_id: Document identifier for tracking (NO sensitive data)
        scan_mode: "full" (all 6 layers) or "quick" (layers 1+5 only)
        focus_layers: Optional list of specific layers to run

    Returns:
        Complete SGE analysis report with risk classification.
        Zero-Knowledge: contains NO original document content.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Determine which layers to run
    all_layers = ["lexical", "syntactic", "semantic", "pragmatic", "regulatory", "institutional"]
    if focus_layers:
        active_layers = [l for l in focus_layers if l in all_layers]
    elif scan_mode == "quick":
        active_layers = ["lexical", "regulatory"]
    else:
        active_layers = all_layers

    # Execute each active layer
    results = {}
    layer_scores = {}

    if "lexical" in active_layers:
        results["lexical"] = _scan_lexical(content)
        layer_scores["lexical"] = results["lexical"]["score"]

    if "syntactic" in active_layers:
        results["syntactic"] = _scan_syntactic(content)
        layer_scores["syntactic"] = results["syntactic"]["score"]

    if "semantic" in active_layers:
        results["semantic"] = _scan_semantic(content)
        layer_scores["semantic"] = results["semantic"]["score"]

    if "pragmatic" in active_layers:
        results["pragmatic"] = _scan_pragmatic(content)
        layer_scores["pragmatic"] = results["pragmatic"]["score"]

    if "regulatory" in active_layers:
        results["regulatory"] = _scan_regulatory(content)
        layer_scores["regulatory"] = results["regulatory"]["score"]

    if "institutional" in active_layers:
        results["institutional"] = _scan_institutional(content)
        layer_scores["institutional"] = results["institutional"]["score"]

    # Fill default scores for inactive layers
    for layer in all_layers:
        if layer not in layer_scores:
            layer_scores[layer] = 0.5  # Neutral default

    # Classify risk
    red_flag_count = results.get("lexical", {}).get("red_flag_count", 0)
    risk = _classify_risk(layer_scores, red_flag_count)

    # Generate document hash (for Zero-Knowledge receipt)
    doc_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Build the final report
    report = {
        "report_type": "SGE-DEEP-SCAN",
        "version": "1.0.0",
        "generator": "guardian_sge_deep_scanner",

        # Document reference (ZERO content, only hash)
        "document": {
            "hash": doc_hash,
            "type": document_type,
            "id": document_id,
            "word_count": len(content.split()),
        },

        # Risk classification
        "risk": risk,

        # Layer results
        "layers": results,
        "layers_executed": active_layers,
        "scan_mode": scan_mode,

        # Governance metadata
        "governance": {
            "sge_score": risk["composite_score"],
            "risk_level": risk["risk_level"],
            "risk_color": risk["color"],
            "action_required": risk["action"],
            "human_decision_required": risk["risk_level"] in ("R3", "R4", "R5"),
        },

        # Timestamp and integrity
        "timestamp": timestamp,
        "report_hash": "",  # Filled below
        "principle": "IA processa. Humano decide. WINDI garante.",
    }

    # Compute report integrity hash
    report_json = json.dumps(report, sort_keys=True, ensure_ascii=False)
    report["report_hash"] = hashlib.sha256(report_json.encode()).hexdigest()

    return report


def quick_scan(
    content: str,
    document_type: str = "generic"
) -> Dict[str, Any]:
    """
    Execute a quick 2-layer scan (Lexical + Regulatory only).

    Faster than deep_scan, suitable for initial triage.

    Args:
        content: Document text
        document_type: Document type

    Returns:
        Quick scan report with risk classification.
    """
    return deep_scan(
        content=content,
        document_type=document_type,
        scan_mode="quick"
    )


def scan_dsgvo_compliance(
    content: str,
    check_type: str = "art_13"
) -> Dict[str, Any]:
    """
    Focused DSGVO compliance check for specific articles.

    Args:
        content: Document text
        check_type: "art_13" (information obligations) or
                    "art_28" (processor requirements)

    Returns:
        Detailed DSGVO compliance report.
    """
    content_lower = content.lower()

    element_key = f"{check_type}_elements"
    elements = DSGVO_REQUIRED_ELEMENTS.get(element_key)
    if not elements:
        return {"error": f"Unknown check type: {check_type}"}

    req_list = elements.get("required", [])
    found = [r for r in req_list if r in content_lower]
    missing = [r for r in req_list if r not in content_lower]

    compliance_rate = round(len(found) / max(len(req_list), 1), 3)

    # Risk level based on compliance
    if compliance_rate >= 0.9:
        risk_level = "R0"
    elif compliance_rate >= 0.7:
        risk_level = "R2"
    elif compliance_rate >= 0.5:
        risk_level = "R3"
    elif compliance_rate >= 0.3:
        risk_level = "R4"
    else:
        risk_level = "R5"

    return {
        "check_type": check_type,
        "description": elements["description"],
        "elements_found": len(found),
        "elements_total": len(req_list),
        "compliance_rate": compliance_rate,
        "missing_elements": missing,
        "risk_level": risk_level,
        "human_decision_required": risk_level in ("R3", "R4", "R5"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "principle": "IA processa. Humano decide. WINDI garante.",
    }


def extract_risk_summary(scan_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a minimal risk summary from a full scan report.

    Designed for dashboard display and Controller overview.
    Zero-Knowledge: contains only governance categories.

    Args:
        scan_report: A report generated by deep_scan()

    Returns:
        Minimal risk summary suitable for dashboard.
    """
    risk = scan_report.get("risk", {})
    governance = scan_report.get("governance", {})
    doc = scan_report.get("document", {})

    return {
        "document_hash": doc.get("hash", "UNKNOWN")[:16] + "...",
        "document_type": doc.get("type", "UNKNOWN"),
        "risk_level": risk.get("risk_level", "UNKNOWN"),
        "risk_color": risk.get("color", "❓"),
        "risk_label": risk.get("label", "UNKNOWN"),
        "sge_score": governance.get("sge_score", 0),
        "action": governance.get("action_required", "UNKNOWN"),
        "human_required": governance.get("human_decision_required", True),
        "layer_scores": risk.get("layer_scores", {}),
        "timestamp": scan_report.get("timestamp", "UNKNOWN"),
    }
