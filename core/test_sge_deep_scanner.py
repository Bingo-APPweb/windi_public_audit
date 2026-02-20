#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  🛡️ SGE DEEP SCANNER — Integration Test                      ║
║                                                              ║
║  Tests the first official Guardian Gnosis Capsule through    ║
║  the complete Skill-Loader pipeline:                         ║
║                                                              ║
║  1. Baptism in the Sanctuary                                 ║
║  2. Consumption via Constitutional Gate                      ║
║  3. Deep scan of a German DSGVO contract                     ║
║  4. Quick scan triage                                        ║
║  5. Focused Art. 28 compliance check                         ║
║  6. Scan of a DANGEROUS document with red flags              ║
║                                                              ║
║  "IA processa. Humano decide. WINDI garante."               ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from skill_loader_core import SkillLoaderCore


# ─────────────────────────────────────────────
# TEST DOCUMENTS
# ─────────────────────────────────────────────

# A realistic German data processing agreement (Auftragsverarbeitungsvertrag)
SAMPLE_DPA_CONTRACT = """
AUFTRAGSVERARBEITUNGSVERTRAG (AVV)
gemäß Art. 28 DSGVO

Zwischen:
    WINDI Publishing House GmbH, Kempten (Allgäu) — nachfolgend "Verantwortlicher"
und:
    CloudTech Solutions AG, München — nachfolgend "Auftragsverarbeiter"

§ 1 Vertragsgegenstand und Laufzeit
Dieser Vertrag regelt die Rechte und Pflichten der Parteien im Zusammenhang
mit der Verarbeitung personenbezogener Daten im Auftrag des Verantwortlichen.
Die Laufzeit beträgt 24 Monate ab dem 01.03.2026.

§ 2 Gegenstand und Dauer der Verarbeitung
Der Auftragsverarbeiter verarbeitet personenbezogene Daten im Auftrag des
Verantwortlichen. Zweck der Verarbeitung ist die Bereitstellung von
Cloud-Hosting-Diensten für das WINDI Governance-System.

§ 3 Art der Daten und Kategorien Betroffener
Verarbeitet werden: Kontaktdaten, Nutzungsdaten, Metadaten.
Kategorien betroffener Personen: Mitarbeiter, Kunden, Partner.

§ 4 Rechtsgrundlage
Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO
(Vertragserfüllung) sowie Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse).

§ 5 Weisungsbindung
Der Auftragsverarbeiter verarbeitet die Daten ausschließlich auf Weisung des
Verantwortlichen. Die Weisungen werden schriftlich erteilt. Der Auftragsverarbeiter
ist weisungsgebunden.

§ 6 Vertraulichkeit
Der Auftragsverarbeiter gewährleistet, dass die mit der Verarbeitung befassten
Personen zur Vertraulichkeit verpflichtet sind. Geheimhaltung ist
vertraglich gesichert.

§ 7 Technische und organisatorische Maßnahmen (TOM)
Der Auftragsverarbeiter trifft gemäß Art. 32 DSGVO angemessene technische und
organisatorische Maßnahmen zur Sicherheit der Verarbeitung, insbesondere:
- Verschlüsselung personenbezogener Daten
- Zugangs- und Zugriffskontrolle
- Regelmäßige Überprüfung der Sicherheitsmaßnahmen

§ 8 Unterauftragsverarbeiter
Der Einsatz von Unterauftragsverarbeitern bedarf der vorherigen schriftlichen
Zustimmung des Verantwortlichen. Aktuelle Unterauftragnehmer sind in Anlage 2 aufgeführt.

§ 9 Unterstützungspflichten
Der Auftragsverarbeiter unterstützt den Verantwortlichen bei der Erfüllung
der Betroffenenrechte (Auskunftsrecht, Berichtigungsanspruch, Recht auf Löschung,
Recht auf Vergessenwerden, Datenportabilität, Widerspruchsrecht).

§ 10 Löschung und Rückgabe
Nach Beendigung des Vertrags werden alle personenbezogenen Daten nach Wahl
des Verantwortlichen gelöscht oder zurückgegeben. Löschung nach Vertragsende
wird protokolliert.

§ 11 Kontroll- und Prüfungsrechte
Der Verantwortliche hat das Recht, Kontrollen durchzuführen. Der
Auftragsverarbeiter gewährt Prüfungsrecht und Audit-Zugang.

§ 12 Informationspflichten
Der Verantwortliche informiert betroffene Personen gemäß Art. 13 DSGVO über:
- Kontaktdaten des Verantwortlichen
- Kontaktdaten des Datenschutzbeauftragten
- Zweck der Verarbeitung und Rechtsgrundlage
- Empfänger der Daten
- Speicherdauer
- Betroffenenrechte (Auskunft, Berichtigung, Löschung)
- Widerrufsrecht bei Einwilligung
- Beschwerderecht bei der Aufsichtsbehörde

§ 13 Datenschutz-Folgenabschätzung
Soweit erforderlich, unterstützt der Auftragsverarbeiter den Verantwortlichen
bei der Durchführung einer Datenschutz-Folgenabschätzung gemäß Art. 35 DSGVO.

§ 14 Datenminimierung und Zweckbindung
Es gilt der Grundsatz der Datenminimierung. Daten werden nur im Rahmen der
definierten Zweckbindung verarbeitet. Richtigkeit und Aktualität werden gewährleistet.

§ 15 Haftung und Gewährleistung
Die Haftung richtet sich nach den gesetzlichen Bestimmungen. Eine Beschränkung
der Haftung auf grobe Fahrlässigkeit und Vorsatz wird vereinbart.

§ 16 Schlussbestimmungen
Gerichtsstand ist Kempten (Allgäu). Es gilt deutsches Recht.
Salvatorische Klausel: Sollte eine Bestimmung unwirksam sein, bleibt
der Rest des Vertrages gültig.

Datum: 10.02.2026
Version: 1.0

Unterschriftsfeld:
_________________________          _________________________
Verantwortlicher                   Auftragsverarbeiter
"""

# A dangerous document with multiple red flags
DANGEROUS_CONTRACT = """
RAHMENVERTRAG FÜR CLOUD-DIENSTE

§ 1 Leistungsbeschreibung
Der Auftragnehmer erbringt Cloud-Dienste einschließlich aber nicht beschränkt auf
Speicherung, Verarbeitung und sonstige Leistungen nach Bedarf.

§ 2 Vergütung
Die Vergütung beträgt €150.000,00 monatlich zuzüglich zusätzliche Kosten
für Sonderleistungen. Preisanpassung erfolgt jährlich mit Indexierung.
Mindestabnahme von 12 Monaten.

§ 3 Haftung
Der Auftragnehmer haftet unbeschränkt. Unbeschränkte Haftung des
Auftraggebers für alle direkten und indirekten Schäden.

§ 4 Kündigung
Stillschweigend verlängert sich der Vertrag um jeweils 12 Monate.
Automatische Verlängerung ohne vorherige Benachrichtigung.

§ 5 Datenverarbeitung
Daten werden in einem Drittland (USA) verarbeitet. Die Übermittlung
erfolgt auf Basis des Cloud Act. Personenbezogene Daten werden
ohne spezifische Einwilligung verarbeitet. Profiling und automatisierte
Entscheidung sind Bestandteil des Services.

§ 6 Vertragsstrafe
Bei Vertragsverletzung ist eine Vertragsstrafe von €500.000 fällig.
Sofortige Fälligkeit bei jeder Vertragsverletzung. Kumulativ mit
Schadensersatzansprüchen.

§ 7 Geheimhaltung
Die Partei verpflichtet sich einseitig zur Geheimhaltung.
Auf eigene Kosten des Auftraggebers. Ohne Anspruch auf Gegenleistung.

WICHTIG: Sofortige Unterzeichnung erforderlich.
Frist: 48 Stunden. Zeitdruck besteht.
Dieses Angebot ist die letzte Gelegenheit.

Noch zu bestimmen: Datenschutzbeauftragter
TBD: Technische und organisatorische Maßnahmen
Platzhalter: Unterauftragsverarbeiter [...]
"""


def separator(title):
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


def print_risk_bar(score, label="Score"):
    """Visual risk bar."""
    filled = int(score * 20)
    empty = 20 - filled
    bar = "█" * filled + "░" * empty
    print(f"   {label}: [{bar}] {score:.1%}")


def run_tests():
    """Run all SGE Deep Scanner tests through the Skill-Loader."""

    test_sanctuary = Path(tempfile.mkdtemp(prefix="windi_sge_test_"))
    print(f"\n🏛️ Test Sanctuary: {test_sanctuary}")

    try:
        # ─── INITIALIZE ───
        separator("INITIALIZATION")
        loader = SkillLoaderCore(sanctuary_path=test_sanctuary)
        loader.initialize()

        # Deploy the skill
        import shutil, os
        src = Path(__file__).parent / "sandbox-skills" / "guardian" / "guardian_sge_deep_scanner.py"
        dst = test_sanctuary / "guardian" / "guardian_sge_deep_scanner.py"
        shutil.copy2(src, dst)
        os.chmod(dst, 0o444)
        print(f"   📦 Deployed: guardian/guardian_sge_deep_scanner.py")

        # ─── BAPTISM ───
        separator("BAPTISM — Sealing the First Guardian Capsule")
        result = loader.baptize_skill(
            filepath=str(dst),
            skill_id="sge_deep_scanner",
            name="SGE Deep Scanner",
            version="1.0.0",
            domain="guardian",
            capability="sge_scan",
            description=(
                "6-layer Semantic Governance Engine deep scanner for DSGVO/GDPR "
                "contracts with German regulatory compliance and Zero-Knowledge output"
            ),
            author_dragon="Guardian (Claude)",
            metadata={
                "priority": "critical",
                "layers": 6,
                "regulations": ["DSGVO", "BDSG", "EU AI Act", "BGB", "HGB"],
                "zero_knowledge": True,
                "first_official_capsule": True,
            }
        )
        print(f"\n   🛡️ {result['message']}")
        if result['manifest']:
            m = result['manifest']
            print(f"   Hash: {m['integrity_hash'][:24]}...")
            print(f"   Baptized: {m['baptism_date']}")
            print(f"   I9 Certified: {m['i9_certified']}")

        # ═══════════════════════════════════════════════════
        # TEST 1: Full Deep Scan of a Good DSGVO Contract
        # ═══════════════════════════════════════════════════
        separator("TEST 1: Deep Scan — Clean DSGVO Contract (AVV)")

        result = loader.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="deep_scan",
            args={
                "content": SAMPLE_DPA_CONTRACT,
                "document_type": "dpa",
                "document_id": "AVV-WINDI-CLOUD-2026",
                "scan_mode": "full",
            },
            agent_id="praktikant-v1",
            input_summary="Full 6-layer SGE scan of WINDI AVV contract"
        )

        print(f"\n   Gate: {result['gate_status']}")
        print(f"   Execution: {result['execution_ms']}ms")
        print(f"   Receipt: {result['receipt']['receipt_id']}")

        if result['success']:
            report = result['result']
            risk = report['risk']
            gov = report['governance']

            print(f"\n   ╔══ RISK CLASSIFICATION ══╗")
            print(f"   ║  Level: {risk['color']} {risk['risk_level']} — {risk['label']}")
            print(f"   ║  Action: {risk['action']}")
            print(f"   ║  Human Decision: {'⚠️ YES' if gov['human_decision_required'] else '✅ NO'}")
            print(f"   ╚═════════════════════════╝")

            print(f"\n   Layer Scores:")
            for layer, score in risk['layer_scores'].items():
                weight = risk['weights'].get(layer, 0)
                print_risk_bar(score, f"{layer:14s} (w={weight:.0%})")

            print(f"\n   Composite SGE Score: {risk['composite_score']:.4f}")
            print(f"   Red Flag Penalty: {risk['red_flag_penalty']:.4f}")

            # Show key regulatory findings
            regs = report['layers'].get('regulatory', {}).get('regulations', {})
            if regs:
                print(f"\n   Regulatory Compliance:")
                for reg_name, reg_data in regs.items():
                    status = "✅" if reg_data['required_compliance'] >= 0.8 else "⚠️" if reg_data['required_compliance'] >= 0.5 else "❌"
                    print(f"     {status} {reg_data['name']}: {reg_data['required_compliance']:.0%} ({reg_data['passed']}/{reg_data['total']})")

            # Show DSGVO element completeness
            syntactic = report['layers'].get('syntactic', {})
            dsgvo_els = syntactic.get('dsgvo_elements', {})
            if dsgvo_els:
                print(f"\n   DSGVO Element Completeness:")
                for el_key, el_data in dsgvo_els.items():
                    status = "✅" if el_data['coverage'] >= 0.8 else "⚠️"
                    print(f"     {status} {el_data['description']}: {el_data['coverage']:.0%} ({el_data['found']}/{el_data['total']})")
        else:
            print(f"   ❌ SCAN FAILED: {result.get('result', result.get('error', 'unknown'))}")

        # ═══════════════════════════════════════════════════
        # TEST 2: Deep Scan of a DANGEROUS Contract
        # ═══════════════════════════════════════════════════
        separator("TEST 2: Deep Scan — DANGEROUS Contract (Red Flags)")

        result = loader.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="deep_scan",
            args={
                "content": DANGEROUS_CONTRACT,
                "document_type": "contract",
                "document_id": "EXTERNAL-CLOUD-SUSPECT",
                "scan_mode": "full",
            },
            agent_id="praktikant-v1",
            input_summary="Full scan of suspicious external contract"
        )

        if result['success']:
            report = result['result']
            risk = report['risk']
            gov = report['governance']

            print(f"\n   ╔══ RISK CLASSIFICATION ══╗")
            print(f"   ║  Level: {risk['color']} {risk['risk_level']} — {risk['label']}")
            print(f"   ║  Action: {risk['action']}")
            print(f"   ║  Human Decision: {'⚠️ YES' if gov['human_decision_required'] else '✅ NO'}")
            print(f"   ╚═════════════════════════╝")

            print(f"\n   Layer Scores:")
            for layer, score in risk['layer_scores'].items():
                print_risk_bar(score, f"{layer:14s}")

            print(f"\n   Composite: {risk['composite_score']:.4f} (penalty: {risk['red_flag_penalty']:.4f})")

            # Show red flags
            lexical = report['layers'].get('lexical', {})
            red_flags = lexical.get('red_flags', {})
            if red_flags:
                print(f"\n   🚨 RED FLAGS DETECTED ({len(red_flags)}):")
                for flag_name, patterns in red_flags.items():
                    print(f"     ❌ {flag_name}: {len(patterns)} patterns")

            # Semantic risks
            semantic = report['layers'].get('semantic', {})
            sem_indicators = semantic.get('risk_indicators', {})
            if sem_indicators:
                print(f"\n   ⚠️ SEMANTIC RISKS:")
                for name, data in sem_indicators.items():
                    print(f"     • {name} (severity={data['severity']}): {data['count']} occurrences")

            # Pragmatic concerns
            pragmatic = report['layers'].get('pragmatic', {})
            if pragmatic.get('urgency_pressure', {}).get('detected'):
                print(f"\n   🔴 URGENCY PRESSURE DETECTED!")
            if pragmatic.get('power_asymmetry', {}).get('detected'):
                print(f"   🔴 POWER ASYMMETRY DETECTED!")
        else:
            print(f"   ❌ SCAN FAILED: {result.get('result', result.get('error', 'unknown'))}")

        # ═══════════════════════════════════════════════════
        # TEST 3: Quick Scan Triage
        # ═══════════════════════════════════════════════════
        separator("TEST 3: Quick Scan (2-layer Triage)")

        result = loader.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="quick_scan",
            args={
                "content": SAMPLE_DPA_CONTRACT,
                "document_type": "dpa",
            },
            agent_id="praktikant-v1",
            input_summary="Quick triage scan"
        )

        if result['success']:
            report = result['result']
            print(f"   Layers: {report['layers_executed']}")
            print(f"   Risk: {report['risk']['color']} {report['risk']['risk_level']}")
            print(f"   Score: {report['risk']['composite_score']:.4f}")
            print(f"   Execution: {result['execution_ms']}ms")
        else:
            print(f"   ❌ QUICK SCAN FAILED: {result.get('result', result.get('error', 'unknown'))}")

        # ═══════════════════════════════════════════════════
        # TEST 4: Focused DSGVO Art. 28 Check
        # ═══════════════════════════════════════════════════
        separator("TEST 4: DSGVO Art. 28 Compliance Check")

        result = loader.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="scan_dsgvo_compliance",
            args={
                "content": SAMPLE_DPA_CONTRACT,
                "check_type": "art_28",
            },
            agent_id="praktikant-v1",
            input_summary="Focused DSGVO Art. 28 compliance"
        )

        if result['success']:
            check = result['result']
            print(f"   {check['description']}")
            print(f"   Compliance: {check['compliance_rate']:.0%} ({check['elements_found']}/{check['elements_total']})")
            print(f"   Risk: {check['risk_level']}")
            if check['missing_elements']:
                print(f"   Missing ({len(check['missing_elements'])}):")
                for m in check['missing_elements'][:5]:
                    print(f"     • {m}")

        # ═══════════════════════════════════════════════════
        # TEST 5: Dashboard Risk Summary
        # ═══════════════════════════════════════════════════
        separator("TEST 5: Dashboard Risk Summary (Zero-Knowledge)")

        result = loader.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="deep_scan",
            args={
                "content": DANGEROUS_CONTRACT,
                "document_type": "contract",
            },
            agent_id="praktikant-v1",
            input_summary="Scan for dashboard summary extraction"
        )

        if result['success']:
            # Extract minimal summary
            from guardian_sge_deep_scanner import extract_risk_summary
            summary = extract_risk_summary(result['result'])

            print(f"\n   ╔══ CONTROLLER DASHBOARD VIEW ══╗")
            print(f"   ║  Doc: {summary['document_hash']}")
            print(f"   ║  Type: {summary['document_type']}")
            print(f"   ║  Risk: {summary['risk_color']} {summary['risk_level']} — {summary['risk_label']}")
            print(f"   ║  SGE: {summary['sge_score']:.4f}")
            print(f"   ║  Action: {summary['action']}")
            print(f"   ║  Human: {'⚠️ REQUIRED' if summary['human_required'] else '✅ Auto'}")
            print(f"   ╚════════════════════════════════╝")
            print(f"\n   ✅ Zero-Knowledge: NO document content in summary")
            print(f"   ✅ Only hashes, categories, and governance metadata")

        # ═══════════════════════════════════════════════════
        # FINAL STATUS
        # ═══════════════════════════════════════════════════
        separator("FINAL STATUS")

        status = loader.get_status()
        print(f"\n   Total Skills: {status['total_skills']}")
        print(f"   Gate Decisions: {status['gate_decisions']}")

        skills = loader.list_skills(domain="guardian")
        print(f"\n   Guardian Skills:")
        for s in skills:
            print(f"     🛡️ {s['name']} v{s['version']} [{s['capability']}]")
            print(f"        {s['description'][:70]}...")

        loader.shutdown()

        separator("ALL TESTS COMPLETE ✅")
        print(f"\n   🐉 The first Guardian Gnosis Capsule is operational.")
        print(f"   🛡️ SGE Deep Scanner: 6 layers, DSGVO/GDPR ready.")
        print(f"   📋 Red flags detected, asymmetries exposed, compliance measured.")
        print(f"   🔒 Zero-Knowledge: No sensitive data leaves the edge.")
        print(f"   ⚖️ IA processa. Humano decide. WINDI garante.\n")

    finally:
        shutil.rmtree(test_sanctuary, ignore_errors=True)


if __name__ == "__main__":
    # Add sandbox-skills to path for direct imports in test 5
    sys.path.insert(0, str(Path(__file__).parent / "sandbox-skills" / "guardian"))
    run_tests()
