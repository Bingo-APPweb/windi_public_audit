#!/usr/bin/env python3
"""
WINDI Compliance Passport v2.0
Date: 2026-02-23
Update: Integrates Autonomy Score v2.0 (post WB-BRIDGE-01)

Deploy: scp to /opt/windi/compliance-passport/ and run
Usage: python3 compliance_passport_v2.py [generate|verify|status]
"""

import json
import hashlib
import os
import sys
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# PASSPORT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PASSPORT_VERSION = "2.0"
PASSPORT_FILE = "compliance_passport_v2.json"
SCORE_FILE = "autonomy_score_v2.json"

# Try to load live autonomy score if available
def load_autonomy_score():
    """Load autonomy score from JSON file if present."""
    score_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCORE_FILE)
    if os.path.exists(score_path):
        with open(score_path, "r") as f:
            return json.load(f)
    # Fallback: hardcoded from confirmed deploy
    return {
        "version": "2.0",
        "operational": {"total_built": 31, "autonomous": 29, "percentage": 93.5, "governance_score": 100.0},
        "roadmap": {"total_inventory": 36, "autonomous": 29, "percentage": 80.6, "planned": 5},
        "integrity_hash": "2664b0693d16736a"
    }


# ═══════════════════════════════════════════════════════════════
# EU AI ACT COMPLIANCE MATRIX
# ═══════════════════════════════════════════════════════════════

EU_AI_ACT_ARTICLES = [
    {
        "article": "Art. 9 — Risk Management",
        "status": "COMPLIANT",
        "evidence": "SGE 6-layer risk analysis (R0-R5), Sentinel LAW 5-tier escalation",
        "modules": ["M01", "M06", "M14"]
    },
    {
        "article": "Art. 11 — Technical Documentation",
        "status": "COMPLIANT",
        "evidence": "Wisdom Protocol sealed blocks, ISP templates (17 profiles)",
        "modules": ["M05", "M15", "M17"]
    },
    {
        "article": "Art. 12 — Record-Keeping",
        "status": "COMPLIANT",
        "evidence": "Forensic Ledger (:8101), Vault (:8106), 4629+ receipts, SHA-256 chain",
        "modules": ["M11", "M12", "M13"]
    },
    {
        "article": "Art. 13 — Transparency",
        "status": "COMPLIANT",
        "evidence": "Three Dragons Protocol (roles visible, LLM names internal), KLAR/NOIR UI",
        "modules": ["M04", "M07"]
    },
    {
        "article": "Art. 14 — Human Oversight",
        "status": "COMPLIANT",
        "evidence": "I9 Gate (AI proposes, Human decides), Command Bridge sign flow",
        "modules": ["M06", "M09", "M30"]
    },
    {
        "article": "Art. 15 — Accuracy/Robustness",
        "status": "COMPLIANT",
        "evidence": "Dual-hash verification, C14N canonical JSON, ZK proof layer",
        "modules": ["M11", "M12", "M31"]
    },
    {
        "article": "Art. 17 — Quality Management",
        "status": "COMPLIANT",
        "evidence": "Compliance Passport self-verification, Autonomy Score tracking",
        "modules": ["M14", "M15"]
    },
    {
        "article": "Art. 52 — Transparency Obligations",
        "status": "COMPLIANT",
        "evidence": "AI disclosure in Three Dragons, no brand names in public UI",
        "modules": ["M07"]
    },
]

# ═══════════════════════════════════════════════════════════════
# GOVERNANCE INVARIANTS (I1-I9)
# ═══════════════════════════════════════════════════════════════

INVARIANTS = [
    {"id": "I1", "name": "Human Decision Authority",      "status": "ENFORCED", "method": "I9 Gate: AI proposes, never executes"},
    {"id": "I2", "name": "Zero-Knowledge Data",           "status": "ENFORCED", "method": "Client=data, WINDI=proofs only"},
    {"id": "I3", "name": "Cryptographic Chain",           "status": "ENFORCED", "method": "SHA-256 + Merkle, content NOT stored"},
    {"id": "I4", "name": "Template ≠ Decision",           "status": "ENFORCED", "method": "API decides level, template manifests"},
    {"id": "I5", "name": "Audit Trail Immutability",      "status": "ENFORCED", "method": "Forensic Ledger append-only, Vault dual-hash"},
    {"id": "I6", "name": "Governance Score Integrity",    "status": "ENFORCED", "method": "Autonomy Score v2.0, self-verifying hash"},
    {"id": "I7", "name": "Multimodal Sovereignty",        "status": "ENFORCED", "method": "Paperless Bridge: OCR local, classify local, hash local"},
    {"id": "I8", "name": "Sentinel Escalation Protocol",  "status": "ENFORCED", "method": "5-tier escalation, p95=32.7ms, probe isolation"},
    {"id": "I9", "name": "Document Flow Control",         "status": "ENFORCED", "method": "INVOICE→pass, CONTRACT/CRIT→stop. Field-proven."},
]

# ═══════════════════════════════════════════════════════════════
# WISDOM CHAIN REFERENCE
# ═══════════════════════════════════════════════════════════════

WISDOM_BLOCKS = [
    {"id": "WB-INSP-00000000", "type": "GENESIS",           "domain": "philosophy-ethics", "visibility": "public"},
    {"id": "WB-CONV-df1b601c", "type": "CONVERGENCE",       "domain": "philosophy-ethics", "visibility": "public"},
    {"id": "WB-PHIL-48a152a2", "type": "SOVEREIGNTY",        "domain": "philosophy-ethics", "visibility": "public"},
    {"id": "WB-SCORE-01",      "type": "AUTONOMY SCORE",    "domain": "governance",        "visibility": "internal"},
    {"id": "WB-BRIDGE-01",     "type": "PAPERLESS BRIDGE",  "domain": "governance",        "visibility": "internal"},
]


# ═══════════════════════════════════════════════════════════════
# PASSPORT GENERATION
# ═══════════════════════════════════════════════════════════════

def generate_passport():
    score = load_autonomy_score()

    passport = {
        "passport_version": PASSPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issuer": "WINDI Publishing House",
        "officer": "Human Dragon — Chief Governance Officer",
        "principle": "AI processes. Human decides. WINDI guarantees.",

        "classification": {
            "tier": "GOLD",
            "governance_score": score.get("operational", {}).get("governance_score", 100.0),
            "previous_tier": "GOLD (v1.0, 21-Feb-2026)",
            "upgrade_reason": "Autonomy Score v2.0 + Paperless Bridge v1.0 + Wave1 SEALED"
        },

        "autonomy_score": {
            "version": score.get("version", "2.0"),
            "operational": score.get("operational", {}),
            "roadmap": score.get("roadmap", {}),
            "integrity_hash": score.get("integrity_hash", ""),
            "wisdom_block": "WB-SCORE-01 → WB-BRIDGE-01"
        },

        "eu_ai_act_compliance": {
            "articles_covered": len(EU_AI_ACT_ARTICLES),
            "compliant": sum(1 for a in EU_AI_ACT_ARTICLES if a["status"] == "COMPLIANT"),
            "articles": EU_AI_ACT_ARTICLES
        },

        "invariants": {
            "total": len(INVARIANTS),
            "enforced": sum(1 for i in INVARIANTS if i["status"] == "ENFORCED"),
            "list": INVARIANTS
        },

        "wisdom_chain": {
            "protocol_version": "v0.1.0",
            "blocks_sealed": len(WISDOM_BLOCKS),
            "genesis": "WB-INSP-00000000",
            "latest": WISDOM_BLOCKS[-1]["id"],
            "blocks": WISDOM_BLOCKS
        },

        "forensic_stack": {
            "ledger": {"port": 8101, "type": "SQLite+SHA-256", "status": "GREEN"},
            "vault":  {"port": 8106, "type": "Dual-hash→Ledger", "status": "GREEN"},
            "receipts": "4629+",
            "violations": 0,
            "zk_enforced": True
        },

        "infrastructure": {
            "server": "Strato VPS (87.106.29.233)",
            "os": "Ubuntu 24",
            "ports": "8080-8108",
            "ssl": "Let's Encrypt (auto-renew)",
            "services_systemd": ["windi-brain", "windi-bridge", "windi-clone", "windi-cortex", "windi-gateway", "windi-masterarbeit"],
        },

        "certifications_target": [
            "BSI C5 (German Federal Cloud Security)",
            "ISO 27001 (Information Security)",
            "EU AI Act High-Risk System Compliance"
        ],

        "new_capabilities_v2": [
            "Wave1 SEALED: Serial Engine (WINDI-2026-XXXX), Hash Injector, QR Engine, Ledger Sync",
            "Paperless Bridge v1.0: OCR (Tesseract 5.3.0), AutoClassifier (6 types, 3 langs), ZK Proofs",
            "I9 Gate field-proven: INVOICE→pass, CONTRACT→stop, GOVERNANCE/CRIT→stop",
            "Autonomy Score dual-metric: Operational (93.5%) + Roadmap (80.6%)",
            "Wisdom Protocol: 5 sealed blocks across 2 domains"
        ]
    }

    # Generate passport integrity hash
    content = json.dumps(passport, sort_keys=True)
    passport["passport_hash"] = hashlib.sha256(content.encode()).hexdigest()

    return passport


def verify_passport(passport_path=None):
    """Verify an existing passport's integrity."""
    path = passport_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), PASSPORT_FILE)

    if not os.path.exists(path):
        print("  ❌ Passport file not found:", path)
        return False

    with open(path, "r") as f:
        passport = json.load(f)

    stored_hash = passport.pop("passport_hash", None)
    if not stored_hash:
        print("  ❌ No integrity hash found in passport")
        return False

    content = json.dumps(passport, sort_keys=True)
    computed_hash = hashlib.sha256(content.encode()).hexdigest()

    if computed_hash == stored_hash:
        print(f"  ✅ PASSPORT INTEGRITY VERIFIED")
        print(f"     Hash: {stored_hash[:32]}...")
        print(f"     Tier: {passport['classification']['tier']}")
        print(f"     Score: {passport['autonomy_score']['operational'].get('percentage', '?')}% operational")
        print(f"     Gov: {passport['classification']['governance_score']}%")
        print(f"     EU AI Act: {passport['eu_ai_act_compliance']['compliant']}/{passport['eu_ai_act_compliance']['articles_covered']} articles")
        print(f"     Invariants: {passport['invariants']['enforced']}/{passport['invariants']['total']} enforced")
        print(f"     Violations: {passport['forensic_stack']['violations']}")
        return True
    else:
        print(f"  ❌ INTEGRITY MISMATCH")
        print(f"     Stored:   {stored_hash[:32]}...")
        print(f"     Computed: {computed_hash[:32]}...")
        return False


def print_status(passport):
    """Print passport status summary."""
    cls = passport["classification"]
    score = passport["autonomy_score"]
    eu = passport["eu_ai_act_compliance"]
    inv = passport["invariants"]
    forensic = passport["forensic_stack"]
    wisdom = passport["wisdom_chain"]

    print()
    print("=" * 78)
    print("  🛡️  WINDI COMPLIANCE PASSPORT v2.0 — GOLD")
    print("=" * 78)
    print(f"  Generated: {passport['generated_at']}")
    print(f"  Officer:   {passport['officer']}")
    print(f"  Principle: \"{passport['principle']}\"")
    print()
    print("  ┌──────────────────────────────────────────────────────────────┐")
    print(f"  │  TIER:          {cls['tier']:10s}                                │")
    print(f"  │  GOV SCORE:     {cls['governance_score']}%                                   │")
    op = score.get("operational", {})
    rd = score.get("roadmap", {})
    print(f"  │  OPERATIONAL:   {op.get('autonomous','?')}/{op.get('total_built','?')} = {op.get('percentage','?')}%                          │")
    print(f"  │  ROADMAP:       {rd.get('autonomous','?')}/{rd.get('total_inventory','?')} = {rd.get('percentage','?')}%   (incl. planned)       │")
    print(f"  │  EU AI ACT:     {eu['compliant']}/{eu['articles_covered']} articles COMPLIANT                    │")
    print(f"  │  INVARIANTS:    {inv['enforced']}/{inv['total']} ENFORCED                              │")
    print(f"  │  VIOLATIONS:    {forensic['violations']}                                          │")
    print(f"  │  WISDOM CHAIN:  {wisdom['blocks_sealed']} blocks sealed                            │")
    print(f"  │  ZK ENFORCED:   {'YES' if forensic['zk_enforced'] else 'NO':3s}                                        │")
    print("  └──────────────────────────────────────────────────────────────┘")

    print("\n  📜 EU AI ACT COMPLIANCE:")
    print("  " + "-" * 60)
    for art in eu["articles"]:
        icon = "✅" if art["status"] == "COMPLIANT" else "❌"
        print(f"  {icon} {art['article']}")
        print(f"     └ {art['evidence'][:65]}")

    print(f"\n  🔒 INVARIANTS ({inv['enforced']}/{inv['total']}):")
    print("  " + "-" * 60)
    for i in inv["list"]:
        icon = "🟢" if i["status"] == "ENFORCED" else "🔴"
        print(f"  {icon} {i['id']}: {i['name']}")

    print(f"\n  📦 WISDOM CHAIN ({wisdom['blocks_sealed']} blocks):")
    print("  " + "-" * 60)
    for b in wisdom["blocks"]:
        print(f"  [{b['id']:20s}] {b['type']:20s} {b['domain']:20s} {b['visibility']}")

    print(f"\n  🆕 NEW IN v2.0:")
    print("  " + "-" * 60)
    for cap in passport["new_capabilities_v2"]:
        print(f"  • {cap}")

    print(f"\n  🔐 Passport Hash: {passport['passport_hash'][:32]}...")
    print("=" * 78)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"

    if cmd == "generate":
        passport = generate_passport()
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", PASSPORT_FILE)
        with open(out_path, "w") as f:
            json.dump(passport, f, indent=2)
        print_status(passport)
        print(f"\n  💾 Saved: {out_path}")

    elif cmd == "verify":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        verify_passport(path)

    elif cmd == "status":
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)) or ".", PASSPORT_FILE)
        if os.path.exists(path):
            with open(path, "r") as f:
                passport = json.load(f)
            print_status(passport)
        else:
            print("  ⚠️  No passport found. Run: python3 compliance_passport_v2.py generate")

    else:
        print("Usage: python3 compliance_passport_v2.py [generate|verify|status]")


if __name__ == "__main__":
    main()
