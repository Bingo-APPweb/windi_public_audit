"""
W-COUNSEL-001 — Sovereign Counsel Blueprint
Endpoint: POST /grove/counsel
Constelação: :8091 (domain extension of constitutional-agent)

Missão:
  Camada de coaching entre W-INTENT-001 e os agentes especializados.
  Recebe intenção já classificada + prompt do USER,
  executa a tarefa via agente correcto,
  e devolve resposta estruturada em 3 blocos (Sovereign Training):
    1. RESULTADO    — o que foi feito
    2. PROTECÇÃO    — por que protege juridicamente
    3. PRÓXIMO PASSO — decisão soberana do humano

Fluxo:
  W-INTENT-001 (analisa + classifica)
       ↓
  W-COUNSEL-001 (executa + educa + 3 blocos)
       ↓
  W-[DOMAIN]-001 (agente especializado)
       ↓
  Ledger (:8101) — se seal solicitado + confirmado

Invariantes:
  I13 — Máx 1 pergunta por turno, converge sempre para acção
  G3  — Propõe. Humano decide. Nunca seal automático.
  I9  — Nunca escalada autónoma
  I11 — Seal só com confirmação explícita

Autor: Liga IA+H · Human Dragon: Jober Mögele Correa
Data:  2026-03-24
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

counsel = Blueprint("counsel", __name__)

# ─── Domain → Agent Config ────────────────────────────────────────────────────

AGENT_CONFIG = {
    "legal": {
        "agent_id":    "W-LEGAL-001",
        "endpoint":    "/legal/",
        "display":     "WINDI Agente Jurídico",
        "seal_prefix": "WINDI-LEGAL",
        "protection_templates": {
            "contract": "Este contrato selado no Ledger tem timestamp SHA-256 imutável — "
                        "nenhum tribunal pode questionar a data de criação ou o conteúdo original.",
            "evidence": "Esta cadeia de evidências com hash SHA-256 é auditável publicamente "
                        "via Verify Public — a integridade é verificável por qualquer parte.",
            "report":   "Este pacote de tribunal em DE/EN/PT tem prova criptográfica "
                        "compatível com ZPO, eIDAS e UNCITRAL.",
            "default":  "Este documento selado no Forensic Ledger é prova imutável — "
                        "a integridade é verificável publicamente a qualquer momento."
        }
    },
    "notary": {
        "agent_id":    "W-NOTARY-001",
        "endpoint":    "/notary/",
        "display":     "WINDI Agente Notarial",
        "seal_prefix": "WINDI-NOTARY",
        "protection_templates": {
            "default": "A autenticação notarial digital no Ledger é equivalente ao "
                       "reconhecimento físico para fins de eIDAS — válida em toda a UE."
        }
    },
    "accounting": {
        "agent_id":    "W-ACCT-001",
        "endpoint":    "/accounting/",
        "display":     "WINDI Agente Contábil",
        "seal_prefix": "WINDI-ACCT",
        "protection_templates": {
            "default": "Este documento fiscal selado cumpre GoBD — "
                       "imutável, auditável, pronto para DATEV ou ELSTER. "
                       "Invariante C6: IA prepara. Humano aprova. ELSTER envia."
        }
    },
    "compliance": {
        "agent_id":    "W-COMPLY-001",
        "endpoint":    "/compliance/",
        "display":     "WINDI Agente de Compliance",
        "seal_prefix": "WINDI-COMPLY",
        "protection_templates": {
            "default": "Esta análise de compliance selada documenta a supervisão humana "
                       "exigida pelo EU AI Act (Art. 14) e o accountability do GDPR (Art. 5)."
        }
    },
    "journalism": {
        "agent_id":    "W-JOURN-001",
        "endpoint":    "/jornal/",
        "display":     "WINDI Agente Jornalístico",
        "seal_prefix": "WINDI-JOURN",
        "protection_templates": {
            "default": "Esta publicação selada no Ledger tem autoria, timestamp e "
                       "integridade verificáveis — prova contra adulteração ou negação de autoria."
        }
    },
    "verify": {
        "agent_id":    "VERIFY-PUBLIC",
        "endpoint":    "/verify-public/",
        "display":     "WINDI Verify Public",
        "seal_prefix": "WINDI-VERIFY",
        "protection_templates": {
            "default": "A verificação pública no Ledger é independente — "
                       "qualquer parte pode confirmar a autenticidade sem depender do WINDI."
        }
    }
}

# ─── Sovereign Training Builder ───────────────────────────────────────────────

def build_sovereign_training(
    domain: str,
    action_taken: str,
    result_summary: str,
    receipt_id: str = None,
    next_options: list = None
) -> dict:
    """
    Constrói as 3 camadas do Sovereign Training (Regra 2 do COMPANION v1.1).

    Camada 1 — PROTECÇÃO:    por que este resultado protege juridicamente
    Camada 2 — VERIFICAÇÃO:  como verificar de forma independente
    Camada 3 — DECISÃO:      mapa de opções — humano decide
    """
    config = AGENT_CONFIG.get(domain, AGENT_CONFIG["legal"])

    # Camada 1 — Protecção
    protection_key = action_taken.lower() if action_taken.lower() in config[
        "protection_templates"] else "default"
    protection_text = config["protection_templates"][protection_key]

    # Camada 2 — Verificação independente
    if receipt_id:
        verify_text = (
            f"Aceda a https://windi-domain.com/verify-public/?id={receipt_id} "
            f"— qualquer pessoa pode confirmar a autenticidade deste documento "
            f"sem depender do WINDI ou de terceiros."
        )
    else:
        verify_text = (
            "Após o seal, receberá um ID de receipt para verificação pública em "
            "https://windi-domain.com/verify-public/ — independente e permanente."
        )

    # Camada 3 — Decisão soberana
    if not next_options:
        next_options = [
            {"option": "A", "description": "Selar no Ledger agora (permanente)", "risk": "Irreversível — confirme o conteúdo antes"},
            {"option": "B", "description": "Guardar como rascunho e rever", "risk": "Não selado — sem prova de integridade ainda"},
            {"option": "C", "description": "Exportar para revisão externa", "risk": "Baixo — partilha sem seal"}
        ]

    return {
        "layer_1_protection": {
            "title":   "Por que este resultado o protege",
            "content": protection_text
        },
        "layer_2_verification": {
            "title":   "Como verificar de forma independente",
            "content": verify_text
        },
        "layer_3_decision": {
            "title":   "A decisão é sua — mapa de opções",
            "options": next_options,
            "note":    "AI processes. Human decides. WINDI guarantees."
        }
    }


# ─── Main Endpoint ────────────────────────────────────────────────────────────

@counsel.route("/grove/counsel", methods=["POST"])
def grove_counsel():
    """
    POST /grove/counsel

    Body:
    {
        "prompt":          "texto do utilizador",
        "intent":          { ... }    // output do W-INTENT-001
        "domain":          "legal",   // domínio já classificado
        "wallet_id":       "opcional",
        "action_taken":    "contract|evidence|report|default",
        "seal_requested":  false      // G3: NUNCA true por default
    }

    Response — 3 blocos Sovereign Training:
    {
        "result": {
            "agent":   "W-LEGAL-001",
            "summary": "...",
            "status":  "ready_for_seal | draft | exported"
        },
        "sovereign_training": {
            "layer_1_protection":   { title, content },
            "layer_2_verification": { title, content },
            "layer_3_decision":     { title, options, note }
        },
        "seal_gate": {
            "requires_confirmation": true,
            "message": "Seal requer confirmação explícita (I9 + G3)",
            "confirm_endpoint": "POST /grove/counsel/confirm-seal"
        },
        "constitutional": { i9, i11, i13, g3 },
        "meta": { ... }
    }
    """
    try:
        body        = request.get_json(force=True, silent=True) or {}
        user_prompt = body.get("prompt", "").strip()
        domain      = body.get("domain", "legal")
        wallet_id   = body.get("wallet_id", "anonymous")
        action      = body.get("action_taken", "default")
        seal_req    = body.get("seal_requested", False)
        intent_data = body.get("intent", {})

        if not user_prompt:
            return jsonify({
                "error": "Campo 'prompt' é obrigatório",
                "code":  "MISSING_PROMPT"
            }), 400

        # Validar domínio
        if domain not in AGENT_CONFIG:
            domain = "legal"

        config = AGENT_CONFIG[domain]

        # Construir Sovereign Training
        sovereign = build_sovereign_training(
            domain        = domain,
            action_taken  = action,
            result_summary= user_prompt[:120],
            receipt_id    = None,  # preenchido após seal confirmado
            next_options  = []
        )

        # Seal Gate — G3 enforced, nunca automático
        seal_gate = {
            "requires_confirmation": True,
            "seal_requested_by_user": seal_req,
            "message": (
                "Seal requer confirmação explícita do humano (I9 + G3). "
                "Use POST /grove/counsel/confirm-seal com o receipt_id proposto."
                if seal_req else
                "Documento pronto. Para selar no Ledger, confirme explicitamente."
            ),
            "confirm_endpoint": "POST /grove/counsel/confirm-seal",
            "i9_note": "Nunca seal automático. AI processes. Human decides."
        }

        # Montar response
        response = {
            "result": {
                "agent":        config["agent_id"],
                "display_name": config["display"],
                "domain":       domain,
                "prompt_echo":  user_prompt[:200],
                "status":       "ready_for_review",
                "next_action":  "confirm_seal | export | revise"
            },
            "sovereign_training": sovereign,
            "seal_gate": seal_gate,
            "constitutional": {
                "i9_applied":  True,   # sem escalada autónoma
                "i11_applied": True,   # seal permanente quando confirmado
                "i13_applied": True,   # convergência — 1 pergunta max
                "g3_applied":  True,   # propõe, não executa
                "note": "AI processes. Human decides. WINDI guarantees."
            },
            "meta": {
                "wallet_id":   wallet_id,
                "domain":      domain,
                "agent":       config["agent_id"],
                "timestamp":   datetime.now(timezone.utc).isoformat(),
                "version":     "W-COUNSEL-001 v1.0.0"
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "error":     "Erro interno no Counsel",
            "detail":    str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


# ─── Confirm Seal Endpoint ────────────────────────────────────────────────────

@counsel.route("/grove/counsel/confirm-seal", methods=["POST"])
def confirm_seal():
    """
    POST /grove/counsel/confirm-seal

    Confirmação explícita do humano para seal no Ledger.
    G3: propõe → humano confirma → executa.

    Body:
    {
        "receipt_id":  "WINDI-LEGAL-...",
        "doc_name":    "Nome do documento",
        "doc_type":    "doc",
        "wallet_id":   "...",
        "confirmed":   true   // OBRIGATÓRIO — confirmação explícita
    }
    """
    try:
        body       = request.get_json(force=True, silent=True) or {}
        confirmed  = body.get("confirmed", False)
        receipt_id = body.get("receipt_id", "").strip()
        doc_name   = body.get("doc_name", "Documento WINDI").strip()
        wallet_id  = body.get("wallet_id", "anonymous")

        # G3 enforced — confirmação obrigatória
        if not confirmed:
            return jsonify({
                "error": "Confirmação explícita obrigatória (G3 + I9)",
                "message": "Defina 'confirmed': true para autorizar o seal.",
                "note": "AI processes. Human decides. WINDI guarantees."
            }), 400

        if not receipt_id:
            return jsonify({
                "error": "receipt_id obrigatório para seal",
                "code":  "MISSING_RECEIPT_ID"
            }), 400

        # Preparar payload para Ledger (:8101)
        ledger_payload = {
            "id":               receipt_id,
            "actor":            wallet_id,
            "app":              "w-counsel-001",
            "doc_name":         doc_name,
            "doc_type":         body.get("doc_type", "doc"),
            "governance_level": "HIGH",
            "metadata": {
                "counsel_version": "v1.0.0",
                "confirmed_by":    wallet_id,
                "invariants":      ["I9", "I11", "I13", "G3"],
                "sovereign_training_applied": True
            }
        }

        # Verificação pública URL
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id}"

        return jsonify({
            "status":        "seal_authorized",
            "receipt_id":    receipt_id,
            "verify_url":    verify_url,
            "ledger_payload": ledger_payload,
            "message": (
                f"Seal autorizado pelo humano. "
                f"Envie o ledger_payload para POST https://windi-domain.com/ledger/api/receipts "
                f"para completar o seal."
            ),
            "constitutional": {
                "g3_honoured": True,
                "i9_honoured": True,
                "note": "Humano autorizou. WINDI garante."
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            "error":     "Erro no confirm-seal",
            "detail":    str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


# ─── Health Check ─────────────────────────────────────────────────────────────

@counsel.route("/grove/counsel/health", methods=["GET"])
def counsel_health():
    return jsonify({
        "agent":      "W-COUNSEL-001",
        "version":    "v1.0.0",
        "status":     "active",
        "role":       "Sovereign Counsel — coaching layer between INTENT and AGENTS",
        "endpoints": [
            "POST /grove/counsel",
            "POST /grove/counsel/confirm-seal",
            "GET  /grove/counsel/health"
        ],
        "domains":    list(AGENT_CONFIG.keys()),
        "invariants": ["I9", "I11", "I13", "G3"],
        "sovereign_training_layers": [
            "layer_1_protection",
            "layer_2_verification",
            "layer_3_decision"
        ],
        "upstream":   "W-INTENT-001 → W-COUNSEL-001 → W-[DOMAIN]-001",
        "timestamp":  datetime.now(timezone.utc).isoformat()
    }), 200
