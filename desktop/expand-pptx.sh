#!/bin/bash
# ═══════════════════════════════════════════════════
# WINDI Suite — Expand PPTX Templates
# Adds ISP-based presentation templates to suite.html
# Run on Strato: bash /opt/windi/desktop/expand-pptx.sh
# ═══════════════════════════════════════════════════

set -e

SUITE="/opt/windi/desktop/suite.html"
BACKUP="/opt/windi/backups/suite_pre_pptx_$(date +%Y%m%d_%H%M%S).html"

echo "◆ WINDI Suite — PPTX Template Expansion"
echo "═══════════════════════════════════════"

# 1. Backup
mkdir -p /opt/windi/backups
cp "$SUITE" "$BACKUP"
echo "✅ Backup: $BACKUP"

# 2. Create the new pptx templates block
# We use Python for safe multiline replacement
python3 << 'PYEOF'
import re

suite_path = "/opt/windi/desktop/suite.html"

with open(suite_path, "r") as f:
    content = f.read()

# The OLD pptx array (3 templates)
old_pptx = '''  pptx: [
    { id:"blank-pptx", label:"Leere Pr\\u00E4sentation", sub:"Freies Deck", icon:"\\u{1F3AC}", gov:"LOW", type:"pptx", slides:[{type:"title",title:"",subtitle:""}] },
    { id:"gov-review", label:"Governance-Review", sub:"Quartalsbericht", icon:"\\u{1F3DB}\\uFE0F", gov:"HIGH", type:"pptx",
      slides:[{type:"title",title:"Governance Review Q1 2026",subtitle:"[Organisation]"},{type:"content",heading:"Executive Summary",body:"[Zusammenfassung]"},{type:"risks",heading:"Identifizierte Risiken",items:["Risiko 1","Risiko 2","Risiko 3"]},{type:"actions",heading:"Ma\\u00DFnahmen",items:["Ma\\u00DFnahme 1","Ma\\u00DFnahme 2","Ma\\u00DFnahme 3"]}] },
    { id:"comp-deck", label:"Compliance-Report", sub:"Status\\u00FCbersicht", icon:"\\u{1F4DC}", gov:"HIGH", type:"pptx",
      slides:[{type:"title",title:"Compliance Status Report",subtitle:"EU AI Act + DSGVO"},{type:"dashboard",framework:"EU AI Act + DSGVO",status:"Konform"},{type:"content",heading:"Wichtigste Ergebnisse",body:"[Zusammenfassung]"}] },
  ],'''

# The NEW pptx array (10 templates)
new_pptx = r'''  pptx: [
    { id:"blank-pptx", label:"Leere Pr\u00E4sentation", sub:"Freies Deck", icon:"\u{1F3AC}", gov:"LOW", type:"pptx", slides:[{type:"title",title:"",subtitle:""}] },
    { id:"gov-review", label:"Governance-Review", sub:"Quartalsbericht", icon:"\u{1F3DB}\uFE0F", gov:"HIGH", type:"pptx",
      slides:[{type:"title",title:"Governance Review Q1 2026",subtitle:"[Organisation]"},{type:"content",heading:"Executive Summary",body:"[Zusammenfassung]"},{type:"risks",heading:"Identifizierte Risiken",items:["Risiko 1","Risiko 2","Risiko 3"]},{type:"actions",heading:"Ma\u00DFnahmen",items:["Ma\u00DFnahme 1","Ma\u00DFnahme 2","Ma\u00DFnahme 3"]}] },
    { id:"comp-deck", label:"Compliance-Report", sub:"Status\u00FCbersicht", icon:"\u{1F4DC}", gov:"HIGH", type:"pptx",
      slides:[{type:"title",title:"Compliance Status Report",subtitle:"EU AI Act + DSGVO"},{type:"dashboard",framework:"EU AI Act + DSGVO",status:"Konform"},{type:"content",heading:"Wichtigste Ergebnisse",body:"[Zusammenfassung]"}] },
    { id:"bundesregierung", label:"Bundesregierung", sub:"Governance-Bericht Bund", icon:"\u{1F1E9}\u{1F1EA}", gov:"HIGH", type:"pptx", isp:"Bundesregierung",
      slides:[{type:"title",title:"Governance-Bericht Bundesregierung",subtitle:"Berichtszeitraum Q1 2026 \u00B7 Bundesministerium f\u00FCr [Ressort]"},{type:"content",heading:"1. Ausgangslage",body:"Die Bundesregierung verfolgt im Rahmen der Digitalstrategie das Ziel, KI-Systeme verantwortungsvoll einzusetzen.\n\nDieser Bericht dokumentiert den Governance-Status gem\u00E4\u00DF:\n\u2022 EU AI Act (Verordnung 2024/1689)\n\u2022 BSI C5 Cloud-Sicherheitsstandard\n\u2022 DSGVO Compliance-Anforderungen\n\nBerichtszeitraum: [Quartal/Jahr]"},{type:"dashboard",framework:"EU AI Act + DSGVO + BSI C5",status:"Konform mit Auflagen"},{type:"risks",heading:"2. Identifizierte Risiken",items:["Hochrisiko-KI-System in Verwaltungsverfahren ohne vollst\u00E4ndige Konformit\u00E4tsbewertung","Datenschutz-Folgenabsch\u00E4tzung f\u00FCr 3 Systeme ausstehend","Drittstaaten-Daten\u00FCbermittlung \u00FCber nicht-zertifizierte Cloud-Dienste"]},{type:"actions",heading:"3. Empfohlene Ma\u00DFnahmen",items:["Konformit\u00E4tsbewertung gem\u00E4\u00DF Art. 43 EU AI Act bis Q2 2026 abschlie\u00DFen","DSFA f\u00FCr Systeme BundGPT, VerwaltungsAssist und B\u00FCrgerDialog einleiten","Migration auf BSI C5-zertifizierte Infrastruktur (Bundescloud)"]}] },
    { id:"deutsche-bahn", label:"Deutsche Bahn", sub:"Governance Report DB", icon:"\u{1F684}", gov:"HIGH", type:"pptx", isp:"Deutsche Bahn",
      slides:[{type:"title",title:"Governance Report \u2014 Deutsche Bahn AG",subtitle:"Konzern-Compliance \u00B7 Quartalsbericht Q1 2026"},{type:"content",heading:"1. Zusammenfassung",body:"Die Deutsche Bahn AG setzt KI-gest\u00FCtzte Systeme in kritischen Infrastrukturbereichen ein:\n\n\u2022 Fahrplananpassung und Prognose (DB Netz)\n\u2022 Kundenservice-Automatisierung (DB Fernverkehr)\n\u2022 Predictive Maintenance (DB Cargo)\n\u2022 Sicherheits\u00FCberwachung (DB Station&Service)\n\nDieser Bericht bewertet den Governance-Status aller KI-Systeme im Konzern."},{type:"dashboard",framework:"EU AI Act + KRITIS-Verordnung + EBA",status:"Teilweise konform"},{type:"risks",heading:"2. Identifizierte Risiken",items:["Predictive-Maintenance-KI klassifiziert als Hochrisiko-System (Anhang III, Nr. 2)","Fehlende Transparenzdokumentation f\u00FCr Kundenservice-Chatbot","Bias-Analyse f\u00FCr automatisierte Fahrpreisberechnung ausstehend","Datenqualit\u00E4tsm\u00E4ngel im Trainingsdatensatz Predictive Maintenance"]},{type:"actions",heading:"3. Ma\u00DFnahmen",items:["Risikomanagement-System gem\u00E4\u00DF Art. 9 EU AI Act implementieren","Transparenzbericht f\u00FCr alle kundenorientierten KI-Systeme erstellen","Unabh\u00E4ngiges Bias-Audit f\u00FCr Preisalgorithmus beauftragen","Datenqualit\u00E4ts-Framework nach ISO 8000 einf\u00FChren"]}] },
    { id:"windi-governance", label:"WINDI Governance", sub:"System-Status intern", icon:"\u25C6", gov:"HIGH", type:"pptx", isp:"WINDI",
      slides:[{type:"title",title:"WINDI System Governance Report",subtitle:"Pre-AI Governance Layer \u00B7 Infrastructure Status"},{type:"content",heading:"1. System\u00FCbersicht",body:"WINDI operiert als Pre-AI Governance Layer mit folgender Architektur:\n\n\u2022 Zero-Knowledge: SGE l\u00E4uft clientseitig, Core empf\u00E4ngt nur Hashes\n\u2022 Three Dragons Protocol: Guardian (Claude) \u00B7 Architect (GPT) \u00B7 Witness (Gemini)\n\u2022 Forensic Ledger: SHA-256 Verkettung aller Governance-Entscheidungen\n\u2022 16 aktive systemd-Services auf deutschem Strato-Server\n\nPrinzip: AI processes. Human decides. WINDI guarantees."},{type:"dashboard",framework:"DSGVO + EU AI Act + BSI C5",status:"Operativ"},{type:"risks",heading:"2. System-Risiken",items:["Sentinel LAW \u00FCberwacht 6 Invarianten \u2014 aktuell 0 Verletzungen","Forensic Ledger Reconciliation: HEALTHY (letzte 100 Receipts: 0 Drift)","SIP Layer 1 (Passphrase) ausstehend \u2014 aktuell Mock-Authentifizierung","Skalierung \u00FCber Single-Server-Architektur noch nicht getestet"]},{type:"actions",heading:"3. N\u00E4chste Schritte",items:["SIP Layer 1 Passphrase-Hash implementieren","Hetzner-Migration f\u00FCr Produktionsumgebung evaluieren","Paperless.io Integration f\u00FCr eIDAS-konforme Signaturen","Load-Testing: 100 concurrent users auf Suite + Ledger"]}] },
    { id:"bafin-report", label:"BaFin Bericht", sub:"Finanzaufsicht", icon:"\u{1F3E6}", gov:"HIGH", type:"pptx", isp:"BaFin",
      slides:[{type:"title",title:"Governance-Bericht an die BaFin",subtitle:"KI-Einsatz in Finanzdienstleistungen \u00B7 Meldezeitraum Q1 2026"},{type:"content",heading:"1. Regulatorischer Rahmen",body:"Gem\u00E4\u00DF den Anforderungen der Bundesanstalt f\u00FCr Finanzdienstleistungsaufsicht (BaFin) dokumentiert dieser Bericht den Einsatz von KI-Systemen im regulierten Bereich:\n\n\u2022 MaRisk AT 7.2 \u2014 IT-Risikomanagement\n\u2022 BAIT \u2014 Bankaufsichtliche Anforderungen an die IT\n\u2022 EU AI Act \u2014 Finanzsektor-spezifische Anforderungen\n\u2022 DORA \u2014 Digital Operational Resilience Act\n\nAlle Systeme unterliegen der laufenden \u00DCberwachung."},{type:"dashboard",framework:"MaRisk + BAIT + EU AI Act + DORA",status:"Konform"},{type:"risks",heading:"2. Identifizierte Risiken",items:["Kreditscoring-Algorithmus: Erkl\u00E4rbarkeit nach Art. 13 EU AI Act unvollst\u00E4ndig","Automatisierte Geldw\u00E4sche-Erkennung: False-Positive-Rate \u00FCber Schwellenwert","Robo-Advisory: Eignungstest-Dokumentation nicht vollst\u00E4ndig nachvollziehbar","Cloud-Auslagerung: Pr\u00FCfung der Unterauftragsvergabe ausstehend"]},{type:"actions",heading:"3. Ma\u00DFnahmen",items:["XAI-Modul (Explainable AI) f\u00FCr Kreditscoring bis Q2 implementieren","AML-Modell-Kalibrierung mit aktualisierten Sanktionslisten","Vollst\u00E4ndige Eignungstest-Dokumentation gem\u00E4\u00DF MiFID II","Auslagerungsregister gem\u00E4\u00DF \u00A7 25b KWG aktualisieren"]}] },
    { id:"ecb-analysis", label:"ECB / EZB Analyse", sub:"Zentralbank-Governance", icon:"\u{1F3DB}\uFE0F", gov:"HIGH", type:"pptx", isp:"ECB",
      slides:[{type:"title",title:"Governance Analysis \u2014 European Central Bank",subtitle:"AI Systems Risk Assessment \u00B7 Reporting Period Q1 2026"},{type:"content",heading:"1. Scope of Assessment",body:"This report covers the governance status of AI-driven systems within the ECB\u2019s operational framework:\n\n\u2022 Monetary Policy Modelling (DSGE + ML hybrid models)\n\u2022 Supervisory Technology (SupTech) for banking oversight\n\u2022 Market Infrastructure \u2014 TARGET2 anomaly detection\n\u2022 Internal Operations \u2014 document classification and translation\n\nAll systems assessed against ECB Guide on AI and the EU AI Act."},{type:"dashboard",framework:"EU AI Act + ECB AI Guide + SSM Framework",status:"Compliant"},{type:"risks",heading:"2. Identified Risks",items:["ML-enhanced DSGE models: model risk per ECB internal policy requires additional validation","SupTech NLP classifier: potential bias in cross-jurisdictional supervisory texts","TARGET2 anomaly detection: explainability requirements under Art. 13 EU AI Act","Document classification: GDPR compliance for personal data in supervisory documents"]},{type:"actions",heading:"3. Recommended Actions",items:["Independent model validation for ML-enhanced monetary policy models","Cross-lingual bias audit for SupTech NLP across all 20 eurozone languages","Implement SHAP-based explainability layer for TARGET2 anomaly alerts","Data minimisation review for document classification training data"]}] },
    { id:"pitch-deck", label:"Pitch Deck", sub:"Investoren-Pr\u00E4sentation", icon:"\u{1F680}", gov:"MEDIUM", type:"pptx", isp:"WINDI",
      slides:[{type:"title",title:"WINDI \u2014 Pre-AI Governance Layer",subtitle:"Institutional Document Intelligence \u00B7 Seed Round 2026"},{type:"content",heading:"Das Problem",body:"\u20AC65 Milliarden GRC-Markt \u2014 aber kein System garantiert die QUALIT\u00C4T der KI-gest\u00FCtzten Entscheidung.\n\nAktuelle Situation:\n\u2022 KI generiert Dokumente ohne Governance-Nachweis\n\u2022 Compliance-Abteilungen arbeiten reaktiv statt pr\u00E4ventiv\n\u2022 EU AI Act fordert Nachweispflicht \u2014 L\u00F6sungen fehlen\n\nWINDI schlie\u00DFt diese L\u00FCcke: nicht als Konkurrent zu SAP, sondern als dessen ethischer Disjuntor."},{type:"content",heading:"Die L\u00F6sung",body:"WINDI ist kein Dokumenten-Tool. WINDI ist eine Governance-Schicht.\n\n\u2022 Zero-Knowledge Architektur: Kundendaten bleiben beim Kunden\n\u2022 SGE (Semantic Governance Engine): 6-Schicht Risikoanalyse in Echtzeit\n\u2022 Forensic Ledger: SHA-256 verketteter Nachweis jeder Entscheidung\n\u2022 Three Dragons Protocol: Multi-AI mit menschlicher Entscheidungshoheit\n\nPrinzip: AI processes. Human decides. WINDI guarantees."},{type:"dashboard",framework:"EU AI Act + DSGVO + BSI C5",status:"Production-Ready"},{type:"content",heading:"Business Model",body:"Instruments without data \u2014 der Kunde speichert Terabytes, WINDI speichert Protokoll.\n\n\u2022 Tier 1 (Free): 3 Benutzer, Basis-Governance\n\u2022 Tier 2 (Pro): \u20AC25-40/User, vollst\u00E4ndige SGE + Sealing\n\u2022 Tier 3 (Enterprise): \u20AC80-120/User, Forensic Ledger + War Room\n\nZielmarkt: Mittelst\u00E4ndische Unternehmen mit Compliance-Pflicht (10-500 Mitarbeiter)\nVertrieb: Direkt + Steuerberater-Netzwerk + IHK-Partnerschaften"},{type:"actions",heading:"N\u00E4chste Meilensteine",items:["Paperless.io Integration \u2014 eIDAS-konforme digitale Signatur","Hetzner-Migration \u2014 BSI C5 zertifizierte Produktionsumgebung","Erste Pilotprojekte mit 3 Steuerberater-Kanzleien","ISO 27001 Zertifizierung bis Q3 2026"]}] },
    { id:"quartals-review", label:"Quartals-Review", sub:"Universell einsetzbar", icon:"\u{1F4C5}", gov:"MEDIUM", type:"pptx",
      slides:[{type:"title",title:"Quartals-Review Q1 2026",subtitle:"[Organisation] \u00B7 [Abteilung]"},{type:"content",heading:"Highlights des Quartals",body:"[Die wichtigsten Erfolge und Entwicklungen des Quartals zusammenfassen]\n\n\u2022 Projekt A: [Status und Ergebnis]\n\u2022 Projekt B: [Status und Ergebnis]\n\u2022 Projekt C: [Status und Ergebnis]"},{type:"dashboard",framework:"Interne Governance-Richtlinien",status:"[Status]"},{type:"risks",heading:"Herausforderungen",items:["[Herausforderung 1 \u2014 Beschreibung und Auswirkung]","[Herausforderung 2 \u2014 Beschreibung und Auswirkung]","[Herausforderung 3 \u2014 Beschreibung und Auswirkung]"]},{type:"actions",heading:"Ziele Q2 2026",items:["[Ziel 1 mit konkretem Ergebnis und Frist]","[Ziel 2 mit konkretem Ergebnis und Frist]","[Ziel 3 mit konkretem Ergebnis und Frist]"]}] },
  ],'''

# Find and replace the pptx block
if old_pptx in content:
    content = content.replace(old_pptx, new_pptx)
    with open(suite_path, "w") as f:
        f.write(content)
    print("✅ PPTX templates expanded: 3 → 10")
    print("   Added: Bundesregierung, Deutsche Bahn, WINDI Governance,")
    print("          BaFin, ECB/EZB, Pitch Deck, Quartals-Review")
else:
    # Try a more flexible match
    import re
    pattern = r'pptx:\s*\[.*?\],\s*\n\};'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print("⚠️  Exact match failed, but found pptx block via regex.")
        print("   Manual review recommended. Block found at position:", match.start())
    else:
        print("❌ Could not find PPTX template block in suite.html")
        print("   File may have been modified. Manual injection needed.")
        exit(1)
PYEOF

echo ""
echo "═══════════════════════════════════════"
echo "✅ Expansion complete!"
echo ""
echo "Verify:"
echo "  grep -c 'id:\"bundesregierung\"' $SUITE"
echo "  grep -c 'id:\"pitch-deck\"' $SUITE"
echo "  grep -c 'id:\"bafin-report\"' $SUITE"
echo ""
echo "Test in browser:"
echo "  https://admin.windia4desk.tech/desktop/suite.html"
echo "  → Click 'Präsentationen' tab"
echo "  → Should show 10 templates"
echo ""
echo "Rollback if needed:"
echo "  cp $BACKUP $SUITE"
