#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  🐉 WINDI ISP-COM-01 — GENESIS BLOCK
#  "O primeiro decreto da confiança verificável"
#  18 de Fevereiro de 2026
# ═══════════════════════════════════════════════════════════════

BASE="http://127.0.0.1:8105"

echo "═══════════════════════════════════════════════════════════"
echo "  🐉 WINDI GENESIS — ISP-COM-01"
echo "  O Decreto da Confiança Verificável"
echo "═══════════════════════════════════════════════════════════"

# ── PASSO 1: CREATE (DRAFT) ──
echo ""
echo "▶ [1/3] Criando DRAFT..."
CREATE=$(curl -s -X POST "$BASE/api/communique/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title_de": "WINDI GENESIS — Dekret des verifizierbaren Vertrauens",
    "title_en": "WINDI GENESIS — Decree of Verifiable Trust",
    "title_pt": "WINDI GENESIS — Decreto da Confiança Verificável",
    "body_de": "An diesem Tag, dem 18. Februar 2026, erklärt die WINDI Publishing House das Ende der Ära flüchtiger Information. Ab diesem Moment ist jedes von der WINDI-Infrastruktur versiegelte Dokument kryptografisch verifizierbar, forensisch auditierbar und institutionell unveränderlich. Der Trust Cycle ist geschlossen: content_hash_match, ledger_verified, ledger_status sealed. Dies ist keine Marketingaussage. Dies ist mathematischer Beweis. AI verarbeitet. Der Mensch entscheidet. WINDI garantiert.",
    "body_en": "On this day, February 18th 2026, WINDI Publishing House declares the end of the era of volatile information. From this moment, every document sealed by the WINDI infrastructure is cryptographically verifiable, forensically auditable, and institutionally immutable. The Trust Cycle is sealed: content_hash_match, ledger_verified, ledger_status sealed. This is not a marketing statement. This is mathematical proof. AI processes. Human decides. WINDI guarantees.",
    "body_pt": "Nesta data, 18 de fevereiro de 2026, a WINDI Publishing House declara o fim da era da informação volátil. A partir deste momento, cada documento selado pela infraestrutura WINDI é criptograficamente verificável, forense auditável e institucionalmente imutável. O Ciclo de Confiança está selado: content_hash_match, ledger_verified, ledger_status sealed. Isto não é marketing. Isto é prova matemática. AI processa. Humano decide. WINDI garante.",
    "author_name": "Jober Moegele Correa",
    "author_role": "Chief Governance Officer",
    "doc_type": "INSTITUTIONAL_ANNOUNCEMENT",
    "impact_level": "HIGH",
    "tags": ["genesis", "trust-cycle", "institutional"]
  }')

COM_ID=$(echo "$CREATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','FAILED'))" 2>/dev/null)
echo "   ID: $COM_ID"

if [ "$COM_ID" = "FAILED" ] || [ -z "$COM_ID" ]; then
    echo "❌ CREATE falhou: $CREATE"
    exit 1
fi
echo "✅ DRAFT criado: $COM_ID"

# ── PASSO 2: REVIEW ──
echo ""
echo "▶ [2/3] Submetendo para REVIEW..."
REVIEW=$(curl -s -X POST "$BASE/api/communique/$COM_ID/review" \
  -H "Content-Type: application/json" \
  -d '{"reviewer": "Guardian Dragon", "notes": "Genesis Block — Three Dragons Protocol approved"}')
echo "   $REVIEW"
echo "✅ Em REVIEW"

# ── PASSO 3: PUBLISH (SEAL) ──
echo ""
echo "▶ [3/3] PUBLICANDO + SELANDO no Ledger..."
PUBLISH=$(curl -s -X POST "$BASE/api/communique/$COM_ID/publish" \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "Jober Moegele Correa — CGO"}')

echo "$PUBLISH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print()
print('══════════════════════════════════════════════════════════')
print('  🐉 WINDI GENESIS — ISP-COM-01 RESULTADO')
print('══════════════════════════════════════════════════════════')
print(f'  ID:              {d.get(\"id\", \"?\")}'  )
print(f'  Status:          {d.get(\"status\", \"?\")}'  )
print(f'  Content Hash:    {str(d.get(\"content_hash\", \"?\"))[:40]}...'  )
print(f'  Receipt ID:      {d.get(\"receipt_id\", \"?\")}'  )
print(f'  Ledger:          {\"✅ SEALED\" if d.get(\"ledger_status\") == \"sealed\" else d.get(\"ledger_status\", \"?\")}'  )
print('══════════════════════════════════════════════════════════')
print()
print('  Verify:  $BASE/communique/' + str(d.get('id','')) + '/verify')
print('  HTML:    $BASE/communique/' + str(d.get('id','')))
print('  PDF:     $BASE/communique/' + str(d.get('id','')) + '/pdf')
print('  Feed:    $BASE/communique/feed.json')
print()
" 2>/dev/null || echo "Raw: $PUBLISH"

echo "═══════════════════════════════════════════════════════════"
echo "  🐉🔥⚔️ AI processes. Human decides. WINDI guarantees."
echo "═══════════════════════════════════════════════════════════"
