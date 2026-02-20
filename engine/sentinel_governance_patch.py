#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  WINDI SENTINEL L2 — Governance API Integration Patch            ║
║  v1.0.0 · Adds /api/sentinel/* to windi_governance_api.py       ║
║                                                                  ║
║  "O Sentinel não precisa de casa nova.                           ║
║   A Governance API JÁ É a casa dele."                            ║
║                                                                  ║
║  Endpoints adicionados:                                          ║
║    GET  /api/sentinel/status     → Estado do Sentinel + resumo   ║
║    GET  /api/sentinel/proposals  → Propostas pendentes           ║
║    GET  /api/sentinel/history    → Histórico de decisões         ║
║    POST /api/sentinel/authorize  → Humano autoriza proposta      ║
║    POST /api/sentinel/veto       → Humano veta proposta          ║
║    GET  /api/sentinel/rules      → Regras de pré-autorização     ║
║    POST /api/sentinel/heal       → Trigger manual (Nível 3)      ║
║                                                                  ║
║  DEPLOY:                                                         ║
║    1. Copiar sentinel_level2.py para /opt/windi/engine/          ║
║    2. Executar este patch: python3 sentinel_governance_patch.py   ║
║    3. Restart: sudo systemctl restart windi-governance            ║
║       (ou kill/restart do nohup na :8080)                        ║
║                                                                  ║
║  I9: Nenhuma ação sem autorização humana explícita.              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import shutil
from datetime import datetime

GOVERNANCE_API = "/opt/windi/engine/windi_governance_api.py"
SENTINEL_L2 = "/opt/windi/engine/sentinel_level2.py"
BACKUP_DIR = "/opt/windi/backups"

# ─────────────────────────────────────────────────────────
# The code block to inject into windi_governance_api.py
# ─────────────────────────────────────────────────────────

SENTINEL_ROUTES_CODE = '''

# ══════════════════════════════════════════════════════════
# SENTINEL L2 — Human Intervention Protocol
# Integrated: {timestamp}
# "Sentinel propõe. Humano autoriza. WINDI garante."
# ══════════════════════════════════════════════════════════

try:
    from sentinel_level2 import ProposalEngine, ActionType, ProposalStatus
    from sentinel_level2 import PRE_AUTHORIZATION_RULES, get_authorization_level
    _sentinel_engine = ProposalEngine()
    _sentinel_l2_available = True
    print("[GOVERNANCE] ✅ Sentinel L2 engine loaded")
except ImportError as e:
    _sentinel_l2_available = False
    _sentinel_engine = None
    print(f"[GOVERNANCE] ⚠️  Sentinel L2 not available: {{e}}")


@app.route("/api/sentinel/status", methods=["GET"])
def api_sentinel_status():
    """
    Estado completo do Sentinel — combina dados do daemon (via Bridge)
    com dados do motor L2 (propostas pendentes).
    """
    from datetime import datetime, timezone
    import json

    result = {{
        "sentinel_l2": _sentinel_l2_available,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "principle": "Sentinel propõe. Humano autoriza. WINDI garante.",
    }}

    if _sentinel_l2_available:
        pending = _sentinel_engine.get_pending()
        history = _sentinel_engine.get_history(limit=10)
        result["proposals"] = {{
            "pending": len(pending),
            "total_history": len(_sentinel_engine.proposals),
            "latest_pending": pending[:3] if pending else [],
        }}
        result["authorization_levels"] = {{
            "pre_authorized": "Ações de baixo impacto (restart cortex, clone, etc.)",
            "human_explicit": "Requer clique de aprovação no Dashboard",
            "human_confirmed": "Requer aprovação + passphrase/PIN",
            "forbidden": "Nunca permitido via Sentinel (ex: restart do próprio Sentinel)",
        }}

    # Try to get daemon status from Sentinel Bridge
    try:
        import urllib.request
        req = urllib.request.urlopen("http://127.0.0.1:8098/api/status", timeout=5)
        daemon_data = json.loads(req.read().decode())
        result["daemon"] = {{
            "status": daemon_data.get("status", "UNKNOWN"),
            "total_checks": daemon_data.get("total_checks", 0),
            "healthy": daemon_data.get("summary", {{}}).get("healthy", 0),
            "total_services": daemon_data.get("summary", {{}}).get("total", 0),
            "started_at": daemon_data.get("started_at", ""),
        }}
        result["services"] = daemon_data.get("services", {{}})
    except Exception as e:
        result["daemon"] = {{"status": "UNREACHABLE", "error": str(e)}}

    return jsonify(result)


@app.route("/api/sentinel/proposals", methods=["GET"])
def api_sentinel_proposals():
    """Lista propostas pendentes — o que o Sentinel quer fazer."""
    if not _sentinel_l2_available:
        return jsonify({{"error": "Sentinel L2 not available"}}), 503

    from datetime import datetime, timezone
    lang = request.args.get("lang", "EN").upper()
    pending = _sentinel_engine.get_pending()

    proposals_display = []
    for p in pending:
        proposals_display.append({{
            "id": p["proposal_id"],
            "service": p["trigger_service"],
            "reason": p["trigger_reason"],
            "severity": p["trigger_severity"],
            "action": p["action_description"],
            "command": p["action_command"],
            "impact": p["impact_level"],
            "auth_required": p["authorization_required"],
            "created_at": p["created_at"],
            "hash": p["proposal_hash"],
            "description": p.get(f"description_{{lang.lower()}}", p["action_description"]),
        }})

    return jsonify({{
        "proposals": proposals_display,
        "total_pending": len(proposals_display),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }})


@app.route("/api/sentinel/history", methods=["GET"])
def api_sentinel_history():
    """Histórico de todas as propostas — autorizadas, vetadas, expiradas."""
    if not _sentinel_l2_available:
        return jsonify({{"error": "Sentinel L2 not available"}}), 503

    limit = request.args.get("limit", 50, type=int)
    history = _sentinel_engine.get_history(limit=limit)

    return jsonify({{
        "history": history,
        "total": len(history),
    }})


@app.route("/api/sentinel/authorize", methods=["POST"])
def api_sentinel_authorize():
    """
    Humano autoriza uma proposta.
    
    POST body:
      {{"proposal_id": "SEN-20260215-0001", "decided_by": "human_dragon"}}
    
    Para HIGH impact, adicionar:
      {{"proposal_id": "...", "decided_by": "...", "passphrase_hash": "..."}}
    """
    if not _sentinel_l2_available:
        return jsonify({{"error": "Sentinel L2 not available"}}), 503

    data = request.get_json(silent=True) or {{}}
    proposal_id = data.get("proposal_id")
    decided_by = data.get("decided_by", "human_dragon")

    if not proposal_id:
        return jsonify({{"error": "proposal_id required"}}), 400

    # Check if proposal requires confirmed auth
    proposal = _sentinel_engine._find_proposal(proposal_id)
    if proposal and proposal.get("authorization_required") == "HUMAN_CONFIRMED":
        passphrase = data.get("passphrase_hash")
        if not passphrase:
            return jsonify({{
                "error": "This action requires passphrase confirmation",
                "authorization_required": "HUMAN_CONFIRMED",
                "proposal_id": proposal_id,
            }}), 403

    result = _sentinel_engine.authorize(proposal_id, decided_by=decided_by)
    return jsonify(result)


@app.route("/api/sentinel/veto", methods=["POST"])
def api_sentinel_veto():
    """
    Humano veta uma proposta.
    
    POST body:
      {{"proposal_id": "SEN-20260215-0001", "reason": "Falso alarme", "decided_by": "human_dragon"}}
    """
    if not _sentinel_l2_available:
        return jsonify({{"error": "Sentinel L2 not available"}}), 503

    data = request.get_json(silent=True) or {{}}
    proposal_id = data.get("proposal_id")
    reason = data.get("reason", "")
    decided_by = data.get("decided_by", "human_dragon")

    if not proposal_id:
        return jsonify({{"error": "proposal_id required"}}), 400

    result = _sentinel_engine.veto(proposal_id, reason=reason, decided_by=decided_by)
    return jsonify(result)


@app.route("/api/sentinel/rules", methods=["GET"])
def api_sentinel_rules():
    """
    Regras de pré-autorização — mostra o que o Sentinel pode/não pode fazer.
    Transparência total para o Human Dragon.
    """
    if not _sentinel_l2_available:
        return jsonify({{"error": "Sentinel L2 not available"}}), 503

    rules = []
    for (action, service), level in PRE_AUTHORIZATION_RULES.items():
        rules.append({{
            "action": action.value if hasattr(action, 'value') else str(action),
            "service": service,
            "authorization": level.value if hasattr(level, 'value') else str(level),
        }})

    return jsonify({{
        "rules": rules,
        "total": len(rules),
        "invariant": "I9: Proibição de Escalação de Autonomia",
        "principle": "O Sentinel NUNCA pode reiniciar a si mesmo",
    }})


@app.route("/api/sentinel/heal", methods=["POST"])
def api_sentinel_heal():
    """
    Trigger manual de auto-heal — Nível 3 (futuro).
    
    Por enquanto, cria uma proposta explícita que precisa de autorização.
    Não executa nada diretamente.
    
    POST body:
      {{"service": "windi-forensic", "action": "RESTART_SERVICE"}}
    """
    if not _sentinel_l2_available:
        return jsonify({{"error": "Sentinel L2 not available"}}), 503

    data = request.get_json(silent=True) or {{}}
    service = data.get("service")
    action_str = data.get("action", "RESTART_SERVICE")

    if not service:
        return jsonify({{"error": "service required"}}), 400

    try:
        action_type = ActionType(action_str)
    except ValueError:
        return jsonify({{"error": f"Unknown action: {{action_str}}"}}), 400

    # Check authorization level
    auth_level = get_authorization_level(action_type, service)
    if auth_level.value == "FORBIDDEN":
        return jsonify({{
            "error": f"Action {{action_str}} on {{service}} is FORBIDDEN by I9",
            "invariant": "I9: Proibição de Escalação de Autonomia",
        }}), 403

    proposal = _sentinel_engine.create_proposal(
        service=service,
        reason=f"Manual heal request via Governance API",
        severity="MANUAL",
        consecutive_failures=0,
        action_type=action_type,
    )

    if proposal:
        return jsonify({{
            "status": "PROPOSAL_CREATED",
            "proposal_id": proposal.proposal_id,
            "authorization_required": proposal.authorization_required,
            "message": "Proposal created. Authorize via /api/sentinel/authorize",
        }})
    else:
        return jsonify({{
            "status": "SKIPPED",
            "message": "Proposal already pending or blocked by I9",
        }})


# ══════════════════════════════════════════════════════════
# END SENTINEL L2
# ══════════════════════════════════════════════════════════
'''


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  SENTINEL L2 → Governance API Integration Patch                 ║")
    print("║  Adicionando /api/sentinel/* à casa que já existe               ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # Pre-flight
    if not os.path.exists(GOVERNANCE_API):
        print(f"  ❌ Governance API não encontrada: {GOVERNANCE_API}")
        print(f"     Verifique o path e tente novamente.")
        sys.exit(1)

    # Check if sentinel_level2.py is in place
    if not os.path.exists(SENTINEL_L2):
        print(f"  ⚠️  sentinel_level2.py não encontrado em {SENTINEL_L2}")
        print(f"     Copiando de /opt/windi/sentinel/ se existir...")
        alt_path = "/opt/windi/sentinel/sentinel_level2.py"
        if os.path.exists(alt_path):
            shutil.copy2(alt_path, SENTINEL_L2)
            print(f"  ✅ Copiado de {alt_path}")
        else:
            print(f"  ❌ Nenhuma cópia encontrada. Faça upload do sentinel_level2.py primeiro.")
            sys.exit(1)

    # Backup
    print("── Step 1: Backup ──")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_dir = os.path.join(BACKUP_DIR, f"pre_sentinel_l2_patch_{ts}")
    os.makedirs(bk_dir, exist_ok=True)
    shutil.copy2(GOVERNANCE_API, os.path.join(bk_dir, "windi_governance_api.py"))
    print(f"  ✅ Backup: {bk_dir}")
    print()

    # Read current API
    print("── Step 2: Reading Governance API ──")
    with open(GOVERNANCE_API, "r") as f:
        content = f.read()
    print(f"  ✅ {len(content)} chars loaded")

    # Check if already patched
    if "/api/sentinel/status" in content:
        print(f"  ℹ️  Sentinel L2 routes already present! Skipping patch.")
        print(f"     To re-patch, remove the SENTINEL L2 block from the API first.")
        sys.exit(0)

    # Check for required imports (request, jsonify)
    if "from flask" not in content:
        print(f"  ⚠️  Flask imports not found — this may not be a Flask app!")
        print(f"     Proceeding anyway...")
    print()

    # Inject the routes
    print("── Step 3: Injecting Sentinel L2 routes ──")

    # Format the code with current timestamp
    inject_code = SENTINEL_ROUTES_CODE.replace("{timestamp}", datetime.now().isoformat())

    # Find the best injection point:
    # Option A: Before if __name__ == "__main__"
    # Option B: At the end of the file
    injection_point = None

    if 'if __name__' in content:
        # Inject BEFORE the main block
        idx = content.rfind('if __name__')
        # Find the start of that line
        line_start = content.rfind('\n', 0, idx)
        if line_start == -1:
            line_start = 0
        injection_point = line_start
        print(f"  ✅ Injection point: before __main__ (char {injection_point})")
    else:
        # Append at end
        injection_point = len(content)
        print(f"  ✅ Injection point: end of file")

    # Inject
    new_content = content[:injection_point] + inject_code + content[injection_point:]
    print()

    # Write
    print("── Step 4: Writing patched API ──")
    with open(GOVERNANCE_API, "w") as f:
        f.write(new_content)
    print(f"  ✅ Written: {len(new_content)} chars (added {len(inject_code)} chars)")
    print()

    # Summary
    print("══════════════════════════════════════════════════════════════════")
    print("  PATCH APLICADO COM SUCESSO!")
    print()
    print("  Novos endpoints na Governance API (:8080):")
    print()
    print("    GET  /api/sentinel/status      → Estado completo")
    print("    GET  /api/sentinel/proposals    → Propostas pendentes")
    print("    GET  /api/sentinel/history      → Histórico de decisões")
    print("    POST /api/sentinel/authorize    → Autorizar proposta")
    print("    POST /api/sentinel/veto         → Vetar proposta")
    print("    GET  /api/sentinel/rules        → Regras de pré-autorização")
    print("    POST /api/sentinel/heal         → Trigger manual (Nível 3)")
    print()
    print("  PRÓXIMOS PASSOS:")
    print()
    print("    # 1. Restart da Governance API")
    print("    # Se nohup:")
    print("    kill $(pgrep -f windi_governance_api) && sleep 2")
    print("    cd /opt/windi/engine && nohup python3 windi_governance_api.py &")
    print()
    print("    # Se systemd:")
    print("    sudo systemctl restart windi-governance")
    print()
    print("    # 2. Verificar")
    print("    curl -s http://localhost:8080/api/sentinel/status | python3 -m json.tool")
    print("    curl -s http://localhost:8080/api/sentinel/rules | python3 -m json.tool")
    print()
    print("    # 3. Testar via HTTPS (nginx)")
    print("    curl -s https://admin.windia4desk.tech/governance/api/sentinel/status")
    print()
    print("══════════════════════════════════════════════════════════════════")
    print()
    print("  🐉 'O Sentinel encontrou sua casa na Governance.'")
    print("  🛡️ 'Agora cada proposta passa pelo mesmo portão que")
    print("      governa documentos, submissions e compliance.'")
    print()


if __name__ == "__main__":
    main()
