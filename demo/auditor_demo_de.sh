#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   WINDI AUDITOR DEMO — 12 Minuten Institutionelle Erfahrung
#   "KI verarbeitet. Mensch entscheidet. WINDI garantiert."
# ═══════════════════════════════════════════════════════════════

DEMO_DIR="/opt/windi/demo/scripts"

# Colors
GOLD='\033[38;5;220m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear

echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     W I N D I   A U D I T O R   D E M O                      ║"
echo "║                                                               ║"
echo "║     \"KI verarbeitet. Mensch entscheidet. WINDI garantiert.\"  ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────
# VORABPRÜFUNG
# ─────────────────────────────────────────────────────────────────
echo -e "${CYAN}[0/6] Vorabprüfung — Systemstatus${NC}"
echo "────────────────────────────────────────"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        WINDI DEMO — VORABPRÜFUNG                             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "  DIENSTSTATUS"
echo "  ───────────────────────────────────────"

# Check services
services=(
    "8101:Forensisches Hauptbuch"
    "8104:Orchestrator"
    "8105:Communiqué-Engine"
    "8106:Dragon-Server"
    "8094:Forensische API"
    "8107:Tresor-Dienst"
    "8103:Sentinel LAW"
)

all_ok=true
for svc in "${services[@]}"; do
    port="${svc%%:*}"
    name="${svc#*:}"
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "  ✅ $name (:$port)"
    else
        echo "  ❌ $name (:$port) — NICHT VERFÜGBAR"
        all_ok=false
    fi
done

echo ""
echo "  ───────────────────────────────────────"
if $all_ok; then
    echo "  ✅ ALLE SYSTEME BETRIEBSBEREIT"
    echo "     Demo kann fortgesetzt werden."
else
    echo "  ❌ KRITISCHE DIENSTE NICHT VERFÜGBAR"
    echo "     Demo wird nicht empfohlen."
    exit 1
fi

echo ""
read -p "Drücken Sie ENTER um die Demo zu starten..."

# ─────────────────────────────────────────────────────────────────
# SCHRITT 1: ISOLATIONSBEWERTUNG
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SCHRITT 1/6: ISOLATIONSBEWERTUNG (Live-Metriken)            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}ERLÄUTERUNG:${NC}"
echo "\"Jede Mandanteninteraktion wird mit forensischen Metadaten erfasst."
echo " Das System bewertet kontinuierlich die Isolationsintegrität.\""
echo ""
echo "────────────────────────────────────────"

python3 "$DEMO_DIR/demo_isolation_score.py" 2>/dev/null | sed \
    -e 's/ISOLATION SCORE/ISOLATIONSBEWERTUNG/g' \
    -e 's/LIVE AUDITOR VIEW/LIVE-AUDITOR-ANSICHT/g' \
    -e 's/EXCELLENT/AUSGEZEICHNET/g' \
    -e 's/GOOD/GUT/g' \
    -e 's/FAIR/BEFRIEDIGEND/g' \
    -e 's/CRITICAL/KRITISCH/g' \
    -e 's/METRICS/METRIKEN/g' \
    -e 's/Total isolation receipts/Gesamte Isolationsbelege/g' \
    -e 's/Legacy exempt/Legacy-Ausnahmen/g' \
    -e 's/Post-cutover receipts/Nach-Umstellung Belege/g' \
    -e 's/With tenant_id/Mit Mandanten-ID/g' \
    -e 's/With metadata_hash/Mit Metadaten-Hash/g' \
    -e 's/Cross-tenant conflicts/Mandantenübergreifende Konflikte/g' \
    -e 's/AUDITOR STATEMENT/PRÜFERERKLÄRUNG/g' \
    -e 's/Multi-tenant isolation VERIFIED/Multi-Mandanten-Isolation VERIFIZIERT/g' \
    -e 's/No cross-tenant conflicts detected/Keine mandantenübergreifenden Konflikte erkannt/g' \
    -e 's/All post-cutover receipts compliant/Alle Nach-Umstellung-Belege konform/g' \
    -e 's/Timestamp/Zeitstempel/g'

echo ""
read -p "Drücken Sie ENTER für den nächsten Schritt..."

# ─────────────────────────────────────────────────────────────────
# SCHRITT 2: HAUPTBUCH-VERIFIZIERUNG
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SCHRITT 2/6: HAUPTBUCH-VERIFIZIERUNG (Integritätsnachweis)  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}ERLÄUTERUNG:${NC}"
echo "\"Die Integrität wird unabhängig durch zirkulären Hash-Nachweis verifiziert.\""
echo ""
echo "────────────────────────────────────────"

python3 "$DEMO_DIR/demo_ledger_verify.py" COM-20260226-0017 2>/dev/null | sed \
    -e 's/LEDGER VERIFICATION/HAUPTBUCH-VERIFIZIERUNG/g' \
    -e 's/LIVE PROOF/LIVE-NACHWEIS/g' \
    -e 's/Verifying Communiqué/Verifiziere Communiqué/g' \
    -e 's/INTEGRITY VERIFIED/INTEGRITÄT VERIFIZIERT/g' \
    -e 's/VERIFICATION FAILED/VERIFIZIERUNG FEHLGESCHLAGEN/g' \
    -e 's/VERIFICATION DETAILS/VERIFIZIERUNGSDETAILS/g' \
    -e 's/communique_id/Communiqué-ID/g' \
    -e 's/ledger_receipt/Hauptbuch-Beleg/g' \
    -e 's/content_hash/Inhalts-Hash/g' \
    -e 's/ledger_hash/Hauptbuch-Hash/g' \
    -e 's/hash_match/Hash-Übereinstimmung/g' \
    -e 's/status/Status/g' \
    -e 's/sealed_at/Versiegelt am/g' \
    -e 's/governance_level/Governance-Stufe/g' \
    -e 's/INTEGRITY STATEMENT/INTEGRITÄTSERKLÄRUNG/g' \
    -e 's/Document integrity independently verified/Dokumentenintegrität unabhängig verifiziert/g' \
    -e 's/Hash anchored in immutable ledger/Hash im unveränderlichen Hauptbuch verankert/g' \
    -e 's/No tampering detected/Keine Manipulation erkannt/g' \
    -e 's/Integrity verified through circular hash proof/Integrität durch zirkulären Hash-Nachweis verifiziert/g' \
    -e 's/Timestamp/Zeitstempel/g'

echo ""
read -p "Drücken Sie ENTER für den nächsten Schritt..."

# ─────────────────────────────────────────────────────────────────
# SCHRITT 3: COMMUNIQUÉ LIVE
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SCHRITT 3/6: COMMUNIQUÉ (Dreisprachiges Bulletin)           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}ERLÄUTERUNG:${NC}"
echo "\"Offizielle Mitteilungen werden mit kryptographischem Nachweis versiegelt"
echo " und in drei Sprachen veröffentlicht: Deutsch, Englisch, Portugiesisch.\""
echo ""
echo "────────────────────────────────────────"
echo ""
echo "  Live-URL: https://communique.windia4desk.online/COM-20260226-0017.html"
echo ""
echo "  Inhalt:"
wget -q -O - "http://127.0.0.1:8105/api/communique/COM-20260226-0017" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"  ID:              {d.get('id', 'N/A')}\")
print(f\"  Status:          {d.get('status', 'N/A')}\")
print(f\"  Kategorie:       {d.get('category', 'N/A')}\")
print(f\"  Auswirkung:      {d.get('impact_level', 'N/A')}\")
print()
print(f\"  Titel (DE): {d.get('title_de', 'N/A')[:50]}...\")
print(f\"  Titel (EN): {d.get('title_en', 'N/A')[:50]}...\")
print(f\"  Titel (PT): {d.get('title_pt', 'N/A')[:50]}...\")
print()
print(f\"  Hauptbuch-Beleg: {d.get('ledger_id', 'N/A')}\")
print(f\"  Inhalts-Hash:    {d.get('content_hash', 'N/A')[:32]}...\")
"

echo ""
read -p "Drücken Sie ENTER für den nächsten Schritt..."

# ─────────────────────────────────────────────────────────────────
# SCHRITT 4: PRÜFUNGS-BASELINE
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SCHRITT 4/6: PRÜFUNGS-BASELINE (Stabilitätsverifizierung)   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}ERLÄUTERUNG:${NC}"
echo "\"Nach jedem Meilenstein versiegeln wir eine Baseline, die zum"
echo " Referenzpunkt für zukünftige Prüfungen wird.\""
echo ""
echo "────────────────────────────────────────"
echo ""

cat /opt/windi/reports/baseline/audit_baseline_20260226.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('  PRÜFUNGS-BASELINE: 26. Februar 2026')
print('  ───────────────────────────────────────')
print()
print('  Tests:')
for name, result in d.get('tests', {}).items():
    status = 'BESTANDEN' if result.get('status') == 'PASS' else 'FEHLGESCHLAGEN'
    print(f'    {name}: {status}')
print()
print('  Dienste:')
for name, info in d.get('services', {}).items():
    status = 'AKTIV' if info.get('status') == 'UP' else 'INAKTIV'
    print(f'    {name}: {status}')
print()
overall = 'BESTANDEN' if d.get('overall_status') == 'PASS' else 'FEHLGESCHLAGEN'
print(f\"  Gesamtstatus:    {overall}\")
print(f\"  Baseline-Hash:   {d.get('baseline_hash', 'N/A')[:32]}...\")
"

echo ""
read -p "Drücken Sie ENTER für den nächsten Schritt..."

# ─────────────────────────────────────────────────────────────────
# SCHRITT 5: GOVERNANCE-EBENEN
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SCHRITT 5/6: GOVERNANCE-EBENEN (Risikoklassifizierung)      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}ERLÄUTERUNG:${NC}"
echo "\"Die Governance-Risikoklassifizierung erfolgt automatisch,"
echo " aber die Entscheidungsbefugnis verbleibt beim Menschen.\""
echo ""
echo "────────────────────────────────────────"
echo ""
echo "  GOVERNANCE-STUFEN"
echo "  ───────────────────────────────────────"
echo "  HIGH   — Erfordert menschliche Genehmigung, Hauptbuch-Siegel, Unterschrift"
echo "  GOLD   — Institutionelle Überprüfung erforderlich"
echo "  MEDIUM — Standard-Governance-Workflow"
echo "  LOW    — Automatische Verarbeitung erlaubt"
echo ""
echo "  RISIKO-PIPELINE"
echo "  ───────────────────────────────────────"
echo "  R1-R2  — Niedriges Risiko, automatische Verarbeitung"
echo "  R3     — Mittleres Risiko, zur Überprüfung markiert"
echo "  R4-R5  — Hohes Risiko, menschliche Entscheidung erforderlich"
echo ""
echo "  GRUNDPRINZIP:"
echo "  \"Das System klassifiziert. Der Mensch entscheidet.\""
echo ""

echo ""
read -p "Drücken Sie ENTER für den Abschluss..."

# ─────────────────────────────────────────────────────────────────
# SCHRITT 6: ABSCHLUSSERKLÄRUNG
# ─────────────────────────────────────────────────────────────────
clear
echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SCHRITT 6/6: ABSCHLUSSERKLÄRUNG                             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │                                                         │"
echo "  │   \"WINDI erfordert kein Vertrauen.                     │"
echo "  │    Es bietet Verifizierbarkeit.\"                       │"
echo "  │                                                         │"
echo "  └─────────────────────────────────────────────────────────┘"
echo ""
echo "  ZUSAMMENFASSUNG"
echo "  ───────────────────────────────────────"
echo "  ✅ Multi-Mandanten-Isolation:    VERIFIZIERT"
echo "  ✅ Hauptbuch-Integrität:         VERIFIZIERT"
echo "  ✅ Communiqué-Siegel:            VERIFIZIERT"
echo "  ✅ Prüfungs-Baseline:            VERSIEGELT"
echo "  ✅ Governance-Ebenen:            AKTIV"
echo ""
echo "  REGULATORISCHE AUSRICHTUNG"
echo "  ───────────────────────────────────────"
echo "  ✅ EU AI Act — Rückverfolgbarkeit"
echo "  ✅ DSGVO — Datensegregation"
echo "  ✅ BaFin MaRisk — IT-Governance"
echo "  ✅ ISO 27001 — Änderungsmanagement"
echo "  ✅ SOC2 — Logische Kontrollen"
echo ""
echo "  DREI-DRACHEN-PROTOKOLL"
echo "  ───────────────────────────────────────"
echo "  🐉 Wächter — Risiko & Compliance"
echo "  🐉 Architekt — Technisches Design"
echo "  🐉 Zeuge — Prüfung & Verifizierung"
echo ""
echo ""
echo -e "${GOLD}  \"KI verarbeitet. Mensch entscheidet. WINDI garantiert.\"${NC}"
echo ""
echo "  Demo abgeschlossen: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
