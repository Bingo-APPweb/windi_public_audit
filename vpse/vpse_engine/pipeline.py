"""
VPSE · Engine Pipeline
======================
Fluxo funcional (6 estágios determinísticos + 1 opcional):

  Idea
   ↓ 1. Intent Analyzer       → intent_summary
   ↓ 2. Semantic Decomposer   → semantic_blocks
   ↓ 3. Domain Classifier     → detected_domains
   ↓ 4. Internal Retriever    → possible_windi_modules
   ↓ 5. Risk/Compliance Scan  → early_risks + compliance_questions
   ↓ 6. Governance Mapper     → recommended_next_artifact + hios_readiness
   ↓ (opcional) Receipt-candidate (MORTO: unsealed, ledger_eligible=false)

Non-Goals enforced (I9):
  - não gera código de produção como primeira resposta
  - não promete certeza legal
  - não certifica compliance
  - não substitui autoridade humana
  - não presume DID
  - não toca no Ledger
"""

import re
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from .provenance import Claim, Provenance, Confidence, lido, estimado, nao_verificado
from . import knowledge_base as kb


def _normalize(text: str) -> str:
    return (text or "").lower().strip()


def _contains_any(haystack: str, terms: List[str]) -> List[str]:
    hits = []
    for t in terms:
        if t in haystack:
            hits.append(t)
    return hits


# ---------------------------------------------------------------------------
# Estágio 1 — Intent Analyzer
# ---------------------------------------------------------------------------
def intent_analyzer(idea: str, context: str = "") -> Claim:
    text = idea.strip()
    # Resumo conservador: reformula sem inventar. Pega o núcleo verbal.
    summary = text if len(text) <= 240 else text[:237].rstrip() + "..."
    return estimado(
        content=f"O utilizador parece querer construir: {summary}",
        confidence=Confidence.MEDIUM,
        source_hint="input.idea",
        notes="Resumo reformulado do input; não adiciona intenção não declarada.",
    )


# ---------------------------------------------------------------------------
# Estágio 2 — Semantic Decomposer
# ---------------------------------------------------------------------------
def semantic_decomposer(idea: str, context: str = "") -> List[Claim]:
    text = _normalize(idea + " " + context)
    blocks: List[Claim] = []

    # heurística: divide por conjunções e pontuação em "átomos" de função
    raw = re.split(r"[.;,]|\b(?:and|e|que|when|quando|then|depois|durante|while)\b", text)
    seen = set()
    for chunk in raw:
        c = chunk.strip()
        if len(c) < 8 or c in seen:
            continue
        seen.add(c)
        blocks.append(estimado(
            content=f"bloco funcional: {c}",
            confidence=Confidence.LOW,
            source_hint="semantic_decomposition",
        ))
        if len(blocks) >= 8:
            break

    if not blocks:
        blocks.append(nao_verificado(
            content="Não foi possível decompor a ideia em blocos funcionais claros.",
            notes="Input demasiado curto ou ambíguo — pedir clarificação ao utilizador.",
        ))
    return blocks


# ---------------------------------------------------------------------------
# Estágio 3 — Domain Classifier
# ---------------------------------------------------------------------------
def domain_classifier(idea: str, context: str = "", target_domain: str = "") -> List[Claim]:
    text = _normalize(idea + " " + context + " " + target_domain)
    detected: List[Claim] = []

    for domain, terms in kb.DOMAIN_LEXICON.items():
        hits = _contains_any(text, terms)
        if hits:
            conf = Confidence.MEDIUM if len(hits) >= 2 else Confidence.LOW
            detected.append(estimado(
                content=domain,
                confidence=conf,
                source_hint=f"léxico: {', '.join(hits[:4])}",
            ))

    if target_domain:
        detected.append(lido(
            content=f"domínio declarado pelo utilizador: {target_domain}",
            confidence=Confidence.HIGH,
            source_hint="input.target_domain",
        ))

    if not detected:
        detected.append(nao_verificado(
            content="Nenhum domínio reconhecido pelo léxico local.",
            notes="Ideia fora dos domínios conhecidos — expandir léxico ou clarificar.",
        ))
    return detected


# ---------------------------------------------------------------------------
# Estágio 4 — Internal Knowledge Retriever (módulos WINDI)
# ---------------------------------------------------------------------------
def internal_retriever(idea: str, context: str, detected_domains: List[Claim]) -> List[Claim]:
    text = _normalize(idea + " " + context)
    domain_names = {d.content for d in detected_domains}
    modules: List[Claim] = []

    def _add(name: str, reason: str):
        info = kb.WINDI_MODULES[name]
        modules.append(estimado(
            content=name,
            confidence=Confidence.LOW,
            source_hint=reason,
            notes=info["role"],
        ))

    # Regras de mapeamento determinísticas
    if any(d in domain_names for d in ("identity", "social_platform")) or \
       any(t in text for t in ("login", "user", "utilizador", "wallet", "did")):
        _add("DID / Wallet", "ideia envolve identidade de utilizador")

    if any(d in domain_names for d in ("promotional_mechanics", "fintech_payments")):
        _add("Governance / LAW (Sentinel)", "mecânica promocional/financeira exige guarda LAW")

    if "document_governance" in domain_names:
        _add("Document Factory / A4 Desk", "ideia envolve documentos/contratos")
        _add("SGE Analyzer", "documentos exigem análise de risco semântico")

    if "fintech_payments" in domain_names:
        _add("Payment Sovereignty Bridge", "ideia toca em pagamento/valor")

    if "education" in domain_names:
        _add("Academy", "componente educativo/onboarding")

    # Verify + Ledger + Receipts são quase universais quando há claim a provar
    _add("Verify Public", "qualquer artefacto WINDI precisa de admissibilidade pública")
    _add("Forensic Ledger", "registo imutável da viabilidade quando consumada")
    _add("Receipts", "comprovativo de eventos quando houver DID")

    return modules


# ---------------------------------------------------------------------------
# Estágio 5 — Risk / Compliance Scanner
# ---------------------------------------------------------------------------
def risk_compliance_scanner(idea: str, context: str = "",
                            jurisdiction: str = "") -> Dict[str, List[Claim]]:
    text = _normalize(idea + " " + context)
    early_risks: List[Claim] = []
    compliance_questions: List[Claim] = []

    for signal_name, signal in kb.REGULATORY_SIGNALS.items():
        hits = _contains_any(text, signal["terms"])
        if not hits:
            continue

        # RISCO — sempre [estimado], nunca verdade nua (Regra Canónica 2)
        risk_note = signal["safer_framing"]
        if signal.get("jurisdiction_sensitive"):
            jur = jurisdiction or "jurisdição não especificada"
            risk_note += f" · sensível à jurisdição ({jur})"
        early_risks.append(estimado(
            content=f"[{signal_name}] possível enquadramento regulatório detetado",
            confidence=Confidence.LOW,
            source_hint=f"sinais léxicos: {', '.join(hits[:4])}",
            notes=risk_note,
        ))

        # COMPLIANCE QUESTION — formulada como pergunta, nunca como certeza
        compliance_questions.append(nao_verificado(
            content=signal["question"],
            confidence=Confidence.NONE,
            source_hint=f"sinal: {signal_name}",
            notes="Pergunta a esclarecer com humano/jurista. VPSE não dá parecer legal.",
        ))

    if not early_risks:
        early_risks.append(estimado(
            content="Nenhum sinal regulatório óbvio detetado pelo léxico local.",
            confidence=Confidence.LOW,
            notes="Ausência de sinal ≠ ausência de risco. Não é clearance legal.",
        ))

    return {"early_risks": early_risks, "compliance_questions": compliance_questions}


# ---------------------------------------------------------------------------
# Estágio 6 — Governance Mapper (artefacto + readiness)
# ---------------------------------------------------------------------------
def governance_mapper(detected_domains: List[Claim],
                      modules: List[Claim],
                      risk_bundle: Dict[str, List[Claim]],
                      desired_output: str = "unknown") -> Dict[str, Any]:
    n_real_risks = sum(
        1 for r in risk_bundle["early_risks"]
        if "Nenhum sinal" not in r.content
    )
    n_compliance = len(risk_bundle["compliance_questions"])

    # Recomendação de artefacto: nunca código como primeira resposta (Non-Goal)
    if n_real_risks > 0:
        artifact = estimado(
            content="Viability & Compliance Pre-Screen Report",
            confidence=Confidence.MEDIUM,
            notes="Riscos regulatórios presentes — relatório antes de qualquer build.",
        )
    elif desired_output in ("research", "unknown"):
        artifact = estimado(
            content="Structured Discovery Note (clarificar intenção)",
            confidence=Confidence.LOW,
        )
    else:
        artifact = estimado(
            content="Viability Note + Minimal Spec (sem código de produção)",
            confidence=Confidence.LOW,
        )

    # HIOS readiness — conservador por construção
    if n_real_risks > 0 or n_compliance > 0:
        readiness = "candidate" if n_compliance <= 3 else "not_ready"
        readiness_claim = estimado(
            content=readiness,
            confidence=Confidence.MEDIUM,
            notes=("Só vira 'ready' após perguntas de compliance esclarecidas por humano. "
                   "VPSE nunca declara 'ready' sozinho."),
        )
    else:
        readiness_claim = estimado(
            content="candidate",
            confidence=Confidence.LOW,
            notes="Sem riscos óbvios, mas readiness final é decisão humana (I9).",
        )

    # evidence_needed
    evidence: List[Claim] = []
    if n_real_risks > 0:
        evidence.append(nao_verificado(
            content="Confirmação jurídica do enquadramento regulatório por jurisdição.",
            confidence=Confidence.NONE,
        ))
    evidence.append(estimado(
        content="Definição clara de utilizador, valor trocado e fluxo de identidade (DID).",
        confidence=Confidence.LOW,
    ))

    return {
        "recommended_next_artifact": artifact,
        "hios_readiness": readiness_claim,
        "evidence_needed": evidence,
    }


# ---------------------------------------------------------------------------
# Receipt-candidate (MORTO) — Regra Canónica 3
# ---------------------------------------------------------------------------
def build_receipt_candidate(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Artefacto LOCAL MORTO:
      unsealed=true, ledger_eligible=false, hash local permitido,
      NENHUM POST ao Ledger, NENHUM selo, NENHUM DID presumido.
    Só pode virar candidato a Ledger quando /farm/claim consumir DID válido.
    """
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True).encode("utf-8")
    local_hash = hashlib.sha256(payload).hexdigest()
    return {
        "kind": "vpse_receipt_candidate",
        "unsealed": True,
        "ledger_eligible": False,
        "did_present": False,
        "local_hash_sha256": local_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "promotion_gate": "/farm/claim — consome DID válido antes de qualquer selo",
        "warning": "Artefacto morto. Não enviar ao Ledger. Não selar. Não presumir DID.",
    }


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
def _claims_to_list(claims: List[Claim]) -> List[Dict[str, Any]]:
    return [c.to_dict() for c in claims]


def run_vpse(idea: str,
             context: str = "",
             target_domain: str = "",
             jurisdiction: str = "",
             desired_output: str = "unknown",
             emit_receipt_candidate: bool = False) -> Dict[str, Any]:

    if not idea or len(idea.strip()) < 5:
        return {
            "error": "input.idea ausente ou demasiado curto",
            "hios_readiness": nao_verificado("not_ready").to_dict(),
        }

    intent = intent_analyzer(idea, context)
    blocks = semantic_decomposer(idea, context)
    domains = domain_classifier(idea, context, target_domain)
    modules = internal_retriever(idea, context, domains)
    risk_bundle = risk_compliance_scanner(idea, context, jurisdiction)
    gov = governance_mapper(domains, modules, risk_bundle, desired_output)

    complexity = kb.estimate_complexity(
        n_domains=len([d for d in domains if d.provenance != Provenance.NAO_VERIFICADO]),
        n_modules=len(modules),
        n_risks=sum(1 for r in risk_bundle["early_risks"] if "Nenhum sinal" not in r.content),
    )

    report: Dict[str, Any] = {
        "engine": "VPSE — Viability Pre-Screen Engine",
        "version": "0.1.0-mvp",
        "doctrine": {
            "principle": "Pre-Screen, não veredicto. A memória propõe, a fonte dispõe, o Humano decide.",
            "i9": "Autoridade de decisão é humana. VPSE organiza hipóteses, não certifica.",
            "pre_did_pre_hios": True,
        },
        "intent_summary": intent.to_dict(),
        "semantic_blocks": _claims_to_list(blocks),
        "detected_domains": _claims_to_list(domains),
        "possible_windi_modules": _claims_to_list(modules),
        "early_risks": _claims_to_list(risk_bundle["early_risks"]),
        "compliance_questions": _claims_to_list(risk_bundle["compliance_questions"]),
        "technical_complexity": estimado(complexity, Confidence.LOW).to_dict(),
        "evidence_needed": _claims_to_list(gov["evidence_needed"]),
        "recommended_next_artifact": gov["recommended_next_artifact"].to_dict(),
        "hios_readiness": gov["hios_readiness"].to_dict(),
        "notes": [
            nao_verificado(
                "VPSE não é parecer legal nem clearance de compliance.",
                confidence=Confidence.NONE,
            ).to_dict(),
            estimado(
                "Ausência de sinal de risco não significa ausência de risco.",
                confidence=Confidence.LOW,
            ).to_dict(),
        ],
    }

    if emit_receipt_candidate:
        report["receipt_candidate"] = build_receipt_candidate(report)

    return report
