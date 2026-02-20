#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI — Communiqué Inaugural: Linhagem de Ferro
# Creates DRAFT → REVIEW → PUBLISH
# ═══════════════════════════════════════════════════════════════

set -e

API="http://127.0.0.1:8105"

echo "🛡️ Creating Inaugural Communiqué..."
echo ""

# ─── 1. CREATE DRAFT ──────────────────────────────────────────

RESULT=$(curl -s -X POST "$API/api/communique/create" \
  -H "Content-Type: application/json" \
  -d '{
  "title_de": "Linhagem de Ferro: Digitale Vertrauenskette Operationell",
  "title_en": "Iron Lineage: Digital Chain of Trust Operational",
  "title_pt": "Linhagem de Ferro: Cadeia de Confiança Digital Operacional",
  "body_de": "Am 18. Februar 2026 gibt WINDI Publishing House die vollständige Operationalisierung der digitalen Vertrauenskette \"Linhagem de Ferro\" (Eisenlinie) bekannt.\n\nDie unabhängige Integritätsprüfung bestätigte 13 von 13 Verifizierungen ohne Fehler — eine lückenlose kryptografische Kette vom Dokumenteneditor bis zum Forensic Ledger.\n\nTechnische Errungenschaften:\n\n• Dual-Hash-Architektur: Jedes Dokument wird doppelt gesichert — SHA-256 für den semantischen Inhalt (content_hash) und SHA-256 für das Gesamtpaket (bundle_hash). Manipulation am Inhalt ODER am Paket wird sofort erkannt.\n\n• Forensic Ledger: Über 192 versiegelte Quittungen bilden eine lückenlose Beweiskette. Jede Quittung enthält Hash, Zeitstempel und Kategorie — ohne sensible Daten zu speichern.\n\n• Sentinel LAW: Das konstitutionelle Überwachungssystem prüft alle 30 Sekunden sechs permanente Invarianten. Kein Hash-Drift, keine Event-Drops, keine Kettenbrüche.\n\n• Zero-Knowledge-Architektur: Der Client behält seine Daten. WINDI speichert nur den Beweis der Tugend — Hashes, Kategorien und Governance-Metadaten. Niemals sensible Inhalte.\n\nDie vollständige Kette:\n\nDesktop → Export Engine → SHA-256(content) → SHA-256(bundle) → Forensic Ledger → sealed → Verification\n\nDies ist keine Produktankündigung. Dies ist eine Infrastrukturgarantie.\n\nWINDI Publishing House · Kempten, Bayern\n\"AI processes. Human decides. WINDI guarantees.\"",
  "body_en": "On February 18, 2026, WINDI Publishing House announces the full operationalization of the digital chain of trust known as \"Linhagem de Ferro\" (Iron Lineage).\n\nThe independent integrity check confirmed 13 out of 13 verifications with zero failures — a seamless cryptographic chain from the document editor to the Forensic Ledger.\n\nTechnical Achievements:\n\n• Dual-Hash Architecture: Every document is double-secured — SHA-256 for semantic content (content_hash) and SHA-256 for the complete package (bundle_hash). Tampering with either the content OR the package is immediately detected.\n\n• Forensic Ledger: Over 192 sealed receipts form a continuous chain of evidence. Each receipt contains hash, timestamp, and category — without storing any sensitive data.\n\n• Sentinel LAW: The constitutional monitoring system checks six permanent invariants every 30 seconds. No hash drift, no event drops, no chain breaks.\n\n• Zero-Knowledge Architecture: The client retains their data. WINDI stores only the proof of virtue — hashes, categories, and governance metadata. Never sensitive content.\n\nThe complete chain:\n\nDesktop → Export Engine → SHA-256(content) → SHA-256(bundle) → Forensic Ledger → sealed → Verification\n\nThis is not a product announcement. This is an infrastructure guarantee.\n\nWINDI Publishing House · Kempten, Bavaria\n\"AI processes. Human decides. WINDI guarantees.\"",
  "body_pt": "Em 18 de fevereiro de 2026, a WINDI Publishing House anuncia a operacionalização completa da cadeia de confiança digital \"Linhagem de Ferro\".\n\nA verificação independente de integridade confirmou 13 de 13 verificações com zero falhas — uma cadeia criptográfica ininterrupta do editor de documentos ao Forensic Ledger.\n\nConquistas Técnicas:\n\n• Arquitetura Dual-Hash: Cada documento é duplamente protegido — SHA-256 para o conteúdo semântico (content_hash) e SHA-256 para o pacote completo (bundle_hash). Adulteração no conteúdo OU no pacote é imediatamente detectada.\n\n• Forensic Ledger: Mais de 192 recibos selados formam uma cadeia contínua de evidências. Cada recibo contém hash, timestamp e categoria — sem armazenar dados sensíveis.\n\n• Sentinel LAW: O sistema de monitoramento constitucional verifica seis invariantes permanentes a cada 30 segundos. Zero drift de hash, zero perda de eventos, zero quebra de cadeia.\n\n• Arquitetura Zero-Knowledge: O cliente mantém seus dados. WINDI armazena apenas a prova de virtude — hashes, categorias e metadados de governança. Nunca conteúdo sensível.\n\nA cadeia completa:\n\nDesktop → Export Engine → SHA-256(content) → SHA-256(bundle) → Forensic Ledger → sealed → Verification\n\nIsto não é um anúncio de produto. Isto é uma garantia de infraestrutura.\n\nWINDI Publishing House · Kempten, Baviera\n\"AI processes. Human decides. WINDI guarantees.\"",
  "category": "LAUNCH",
  "impact_level": "HIGH",
  "author_role": "Chief Governance Officer",
  "author_name": "Jober Mögele Correa",
  "tags": ["linhagem-de-ferro", "dual-hash", "forensic-ledger", "sentinel-law", "zero-knowledge"]
}')

echo "CREATE response:"
echo "$RESULT" | python3 -m json.tool

# Extract ID
COM_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -z "$COM_ID" ]; then
    echo "❌ Failed to create communiqué"
    exit 1
fi

echo ""
echo "✅ Created: $COM_ID"
echo ""

# ─── 2. TRANSITION TO REVIEW ─────────────────────────────────

echo "📋 Moving to REVIEW..."
curl -s -X POST "$API/api/communique/$COM_ID/review" \
  -H "Content-Type: application/json" \
  -d '{"actor": "Jober Mögele Correa"}' | python3 -m json.tool

echo ""

# ─── 3. PUBLISH (SEAL) ───────────────────────────────────────

echo "🔐 PUBLISHING (sealing in Forensic Ledger)..."
PUBLISH_RESULT=$(curl -s -X POST "$API/api/communique/$COM_ID/publish" \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "Jober Mögele Correa"}')

echo "PUBLISH response:"
echo "$PUBLISH_RESULT" | python3 -m json.tool

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🛡️🐉 COMMUNIQUÉ INAUGURAL PUBLISHED"
echo ""
echo "  ID: $COM_ID"
echo ""
echo "  Public URL:  https://admin.windia4desk.tech/communique/$COM_ID"
echo "  Verify URL:  https://admin.windia4desk.tech/communique/$COM_ID/verify"
echo "  PDF URL:     https://admin.windia4desk.tech/communique/$COM_ID/pdf"
echo "  Feed URL:    https://admin.windia4desk.tech/communique/feed"
echo ""
echo "  \"A Linhagem de Ferro está forjada. Agora ela fala.\""
echo "═══════════════════════════════════════════════════════════"
