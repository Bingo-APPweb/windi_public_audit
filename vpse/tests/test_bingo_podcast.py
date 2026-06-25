"""
VPSE · Test Case Canónico — Bingo / Podcast
===========================================
Valida contra os Expected findings do spec (I9, 2026-06-25):
  - Domínio: live streaming, audience engagement, promotional mechanics
  - Early risk: pode ser lido como lotaria/gambling/sweepstake conforme jurisdição
  - Safer framing: engagement promocional, sem entrada paga, sem prémio em dinheiro
  - Recommended artifact: Viability & Compliance Pre-Screen Report
  - HIOS readiness: candidate só após compliance esclarecida
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpse_engine import run_vpse

CANONICAL_INPUT = {
    "idea": ("A system where podcast livestream interaction, view count and watch time "
             "generate bingo numbers during a show. Winners receive sponsor gifts, not money."),
    "context": "Early-stage promotional engagement idea, historical BBF lineage.",
    "target_domain": "",
    "jurisdiction": "",
    "desired_output": "unknown",
}


def _contents(items):
    return " || ".join(i.get("content", "") for i in items)


def run_and_validate():
    report = run_vpse(emit_receipt_candidate=True, **CANONICAL_INPUT)

    checks = []

    # 1. Domínios esperados
    domains = _contents(report["detected_domains"]).lower()
    checks.append(("domínio live_streaming", "live_streaming" in domains))
    checks.append(("domínio audience_engagement", "audience_engagement" in domains))
    checks.append(("domínio promotional_mechanics", "promotional_mechanics" in domains))

    # 2. Risco de gambling/lottery detetado e [estimado]
    risks = report["early_risks"]
    gambling = [r for r in risks if "gambling_lottery" in r.get("content", "")]
    checks.append(("risco gambling/lottery detetado", len(gambling) == 1))
    checks.append(("risco com proveniência [estimado]",
                   bool(gambling) and gambling[0]["provenance"] == "[estimado]"))
    checks.append(("risco NÃO sai como verdade nua (tem confidence)",
                   bool(gambling) and "confidence" in gambling[0]))

    # 3. Safer framing presente
    checks.append(("safer framing presente",
                   bool(gambling) and "sem entrada paga" in gambling[0].get("notes", "").lower()))

    # 4. Compliance question como pergunta [nao_verificado]
    cq = report["compliance_questions"]
    gambling_q = [q for q in cq if "gambling_lottery" in q.get("source_hint", "")]
    checks.append(("compliance question é [nao_verificado]",
                   bool(gambling_q) and gambling_q[0]["provenance"] == "[nao_verificado]"))

    # 5. Artefacto recomendado = Pre-Screen Report
    artifact = report["recommended_next_artifact"]["content"]
    checks.append(("artefacto = Pre-Screen Report", "Pre-Screen Report" in artifact))

    # 6. HIOS readiness = candidate (não ready, não código)
    readiness = report["hios_readiness"]["content"]
    checks.append(("hios_readiness = candidate", readiness == "candidate"))

    # 7. Receipt-candidate MORTO
    rc = report.get("receipt_candidate", {})
    checks.append(("receipt unsealed=true", rc.get("unsealed") is True))
    checks.append(("receipt ledger_eligible=false", rc.get("ledger_eligible") is False))
    checks.append(("receipt did_present=false", rc.get("did_present") is False))
    checks.append(("receipt tem hash local", bool(rc.get("local_hash_sha256"))))

    # 8. Non-Goal: nenhum campo de "production_code"
    checks.append(("não gera código de produção", "production_code" not in report))

    return report, checks


if __name__ == "__main__":
    report, checks = run_and_validate()

    print("=" * 70)
    print("VPSE · TEST CASE CANÓNICO — Bingo / Podcast")
    print("=" * 70)

    passed = 0
    for name, ok in checks:
        mark = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        print(f"  {mark} · {name}")

    print("-" * 70)
    print(f"  RESULTADO: {passed}/{len(checks)} checks PASS")
    print("=" * 70)

    print("\n--- RELATÓRIO COMPLETO (JSON) ---\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    sys.exit(0 if passed == len(checks) else 1)
