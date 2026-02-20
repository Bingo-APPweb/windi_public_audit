"""
WINDI WALLET — Auto-Provision Bridge v1.0.0
=============================================
Conecta Lead Admin (ID Genesis :8096) ao WALLET Provisioning (Governance :8080).

Quando um lead é aprovado no Lead Admin, este módulo:
  1. Intercepta a aprovação
  2. Extrai dados do lead
  3. Chama POST /api/wallet/provision
  4. Registra resultado no Lead Admin
  5. Notifica o humano (opcional)

Três modos de integração:
  A) Import direto no Lead Admin (id_genesis app.py)
  B) Webhook callback (Lead Admin chama este módulo)
  C) Polling/watcher (observa DB de leads e provisiona automaticamente)

Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.

(c) 2026 WINDI Publishing House — Kempten, Bavaria
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── Configuração ───────────────────────────────────────────────────────────

GOVERNANCE_API_URL = os.environ.get(
    "GOVERNANCE_API_URL",
    "http://localhost:8080"
)

LEAD_DB_PATH = os.environ.get(
    "LEAD_DB_PATH",
    "/opt/windi/data/id_genesis.db"  # Ajustar ao DB real do Lead Admin
)

LOG_PATH = os.environ.get(
    "BRIDGE_LOG_PATH",
    "/opt/windi/logs/wallet_bridge.log"
)

# ─── Logging ────────────────────────────────────────────────────────────────

logger = logging.getLogger("windi.wallet.bridge")
logger.setLevel(logging.INFO)

_log_dir = Path(LOG_PATH).parent
_log_dir.mkdir(parents=True, exist_ok=True)

if not logger.handlers:
    _fh = logging.FileHandler(LOG_PATH)
    _fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))
    logger.addHandler(_fh)
    _ch = logging.StreamHandler()
    _ch.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logger.addHandler(_ch)


# ============================================================================
# MODO A: HOOK DIRETO — Importar no Lead Admin
# ============================================================================
# Usar dentro do Lead Admin (id_genesis app.py) quando o botão Approve é clicado.
#
# Exemplo de integração:
#
#   from wallet_bridge import on_lead_approved
#
#   @app.route('/api/leads/<lead_id>/approve', methods=['POST'])
#   def approve_lead(lead_id):
#       # ... lógica existente de aprovação ...
#       lead_data = get_lead(lead_id)  # sua função existente
#       update_lead_status(lead_id, 'APPROVED')  # sua função existente
#
#       # ─── AUTO-PROVISION WALLET ───
#       wallet_result = on_lead_approved(lead_data)
#       if wallet_result and wallet_result.get('status') == 'ok':
#           update_lead_windi_id(lead_id, wallet_result['wallet_id'])
#       # ─── END AUTO-PROVISION ──────
#
#       return jsonify({"status": "approved", "wallet": wallet_result})
# ============================================================================

def on_lead_approved(lead_data: dict) -> Optional[dict]:
    """
    Hook principal: chamado quando um lead é aprovado.

    Aceita dados no formato do Lead Admin e converte para o formato
    do /api/wallet/provision.

    Args:
        lead_data: dict com campos do Lead Admin:
            - lead_id: "LEAD-20260215-151736"
            - name: "Jober Mögele Correa"
            - email: "jober@a4desk.de"
            - company: "WINDI Publishing House" (ou "-" se PF)
            - interest: "governance" / "free" / "pro"
            - windi_id: "WINDI-..." (gerado pelo Lead Admin)
            - approved_by: "admin:jober" (opcional)

    Returns:
        dict com resultado do provisioning, ou None se falhou.
    """
    try:
        lead_id = lead_data.get("lead_id", "")
        name = lead_data.get("name", "")
        email = lead_data.get("email", "")
        company = lead_data.get("company", "")
        interest = lead_data.get("interest", "")
        approved_by = lead_data.get("approved_by", "admin:human")

        # ─── Detectar PF vs PJ ──────────────────────────────────────────
        is_pj = (
            company
            and company != "-"
            and company.lower() not in ("", "none", "null", "n/a", "personal")
        )

        # ─── Determinar role pelo interest ───────────────────────────────
        role_map = {
            "governance": "admin",
            "pro": "manager",
            "free": "operator",
            "test": "operator",
            "demo": "operator",
        }
        role = role_map.get(interest.lower(), "operator")

        # ─── Extrair domínio do email ────────────────────────────────────
        domain = None
        if is_pj and "@" in email:
            email_domain = email.split("@")[1]
            # Filtrar domínios genéricos
            generic_domains = {
                "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
                "protonmail.com", "icloud.com", "web.de", "gmx.de",
                "t-online.de", "freenet.de", "posteo.de",
            }
            if email_domain not in generic_domains:
                domain = email_domain

        # ─── Construir payload de provisioning ───────────────────────────
        provision_payload = {
            "lead_id": lead_id,
            "email": email,
            "display_name": name,
            "kind": "PJ" if is_pj else "PF",
            "role": role,
            "approved_by": approved_by,
            "interest": interest,
        }

        if is_pj:
            provision_payload["org"] = {
                "name": company,
                "domain": domain,
            }

        logger.info(
            "BRIDGE: Lead %s → %s provision (company=%s, role=%s)",
            lead_id, "PJ" if is_pj else "PF", company, role
        )

        # ─── Chamar Governance API ───────────────────────────────────────
        result = call_wallet_provision(provision_payload)

        if result and result.get("status") == "ok":
            logger.info(
                "BRIDGE: WALLET created → %s (human=%s)",
                result.get("wallet_id"), result.get("human_id")
            )
        else:
            logger.warning(
                "BRIDGE: Provision failed for lead %s: %s",
                lead_id, result
            )

        return result

    except Exception as e:
        logger.error("BRIDGE: Error processing lead %s: %s", lead_id, str(e))
        return {"status": "error", "error": str(e)}


def call_wallet_provision(payload: dict) -> Optional[dict]:
    """
    Chama POST /api/wallet/provision na Governance API.
    Tenta via HTTP request (remote), ou fallback local import.
    """

    # ─── Tentativa 1: HTTP Request (serviço separado) ────────────────────
    if HAS_REQUESTS:
        try:
            resp = requests.post(
                f"{GOVERNANCE_API_URL}/api/wallet/provision",
                json=payload,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                logger.warning(
                    "BRIDGE: Governance API responded %d: %s",
                    resp.status_code, resp.text[:200]
                )
        except requests.exceptions.ConnectionError:
            logger.warning("BRIDGE: Governance API unreachable, trying local import")
        except Exception as e:
            logger.warning("BRIDGE: HTTP request failed: %s", str(e))

    # ─── Tentativa 2: Import local (mesmo servidor) ──────────────────────
    try:
        import sys
        wallet_path = "/opt/windi/wallet"
        if wallet_path not in sys.path:
            sys.path.insert(0, wallet_path)

        from wallet_provisioning import provision_wallet, init_db
        init_db()
        return provision_wallet(payload)
    except ImportError:
        logger.error("BRIDGE: Cannot import wallet_provisioning locally")
        return None
    except Exception as e:
        logger.error("BRIDGE: Local provision failed: %s", str(e))
        return {"status": "error", "error": str(e)}


# ============================================================================
# MODO B: WEBHOOK — Lead Admin faz POST para este endpoint
# ============================================================================
# O Lead Admin pode chamar este webhook ao aprovar.
# Útil se o Lead Admin não quer importar Python.
#
# Configuração no Lead Admin:
#   WALLET_WEBHOOK_URL=http://localhost:8080/api/wallet/bridge/approve
# ============================================================================

def create_bridge_blueprint():
    """
    Flask Blueprint para receber webhooks do Lead Admin.
    Registrar na Governance API junto com o wallet Blueprint.
    """
    from flask import Blueprint, request, jsonify

    bp = Blueprint("wallet_bridge", __name__, url_prefix="/api/wallet/bridge")

    @bp.route("/approve", methods=["POST"])
    def bridge_approve():
        """
        Webhook: Lead Admin envia dados do lead aprovado.
        Este endpoint converte e chama /api/wallet/provision internamente.
        """
        data = request.get_json(force=True)

        if not data.get("lead_id"):
            return jsonify({"error": "lead_id required"}), 400

        result = on_lead_approved(data)

        if result and result.get("status") == "ok":
            return jsonify(result), 201
        elif result and result.get("idempotent"):
            return jsonify(result), 200
        else:
            return jsonify(result or {"error": "provision failed"}), 500

    @bp.route("/health", methods=["GET"])
    def bridge_health():
        return jsonify({
            "status": "healthy",
            "module": "WALLET Bridge v1.0.0",
            "governance_api": GOVERNANCE_API_URL,
            "lead_db": LEAD_DB_PATH,
        })

    return bp


# ============================================================================
# MODO C: WATCHER — Observa DB de leads e auto-provisiona
# ============================================================================
# Executar como processo independente ou cron job.
# Verifica a cada N segundos se há leads APPROVED sem WALLET.
#
# Uso:
#   python3 wallet_bridge.py watch
#   python3 wallet_bridge.py watch --interval 30
#   python3 wallet_bridge.py provision-all
# ============================================================================

def find_leads_without_wallet(db_path: str = None) -> list:
    """
    Busca leads APPROVED no Lead Admin DB que ainda não têm WALLET.

    NOTA: A estrutura exata da tabela de leads depende do Lead Admin.
    Abaixo temos variações comuns. O código tenta múltiplos schemas.
    """
    db_path = db_path or LEAD_DB_PATH

    if not Path(db_path).exists():
        logger.warning("Lead DB not found: %s", db_path)
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    leads = []

    # ─── Tentar schema do ID Genesis ─────────────────────────────────────
    schemas_to_try = [
        # Schema 1: tabela 'leads' com campo 'status'
        {
            "query": """
                SELECT * FROM leads
                WHERE status = 'APPROVED'
                AND (wallet_id IS NULL OR wallet_id = '')
                ORDER BY created_at ASC
            """,
            "mapping": lambda row: {
                "lead_id": row.get("lead_id") or row.get("id"),
                "name": row.get("name") or row.get("display_name"),
                "email": row.get("email"),
                "company": row.get("company") or row.get("organization"),
                "interest": row.get("interest") or row.get("tier"),
                "approved_by": row.get("approved_by") or "admin:auto",
            },
        },
        # Schema 2: tabela 'registrations'
        {
            "query": """
                SELECT * FROM registrations
                WHERE status = 'APPROVED'
                AND (wallet_id IS NULL OR wallet_id = '')
                ORDER BY created_at ASC
            """,
            "mapping": lambda row: {
                "lead_id": row.get("lead_id") or row.get("reg_id"),
                "name": row.get("name"),
                "email": row.get("email"),
                "company": row.get("company"),
                "interest": row.get("interest"),
                "approved_by": "admin:auto",
            },
        },
        # Schema 3: tabela 'applications' (certification style)
        {
            "query": """
                SELECT * FROM applications
                WHERE status = 'APPROVED'
                ORDER BY created_at ASC
            """,
            "mapping": lambda row: {
                "lead_id": row.get("id") or row.get("application_id"),
                "name": row.get("name") or row.get("agent_name"),
                "email": row.get("email") or row.get("contact_email"),
                "company": row.get("provider") or row.get("company"),
                "interest": row.get("intended_use") or "governance",
                "approved_by": "admin:auto",
            },
        },
    ]

    for schema in schemas_to_try:
        try:
            rows = conn.execute(schema["query"]).fetchall()
            for row in rows:
                row_dict = dict(row)
                mapped = schema["mapping"](row_dict)
                if mapped.get("lead_id") and mapped.get("email"):
                    leads.append(mapped)

            if leads:
                logger.info("Found %d unprovisioned leads (schema matched)", len(leads))
                break
        except sqlite3.OperationalError:
            continue  # tabela não existe, tentar próximo schema

    conn.close()
    return leads


def update_lead_with_wallet(db_path: str, lead_id: str, wallet_id: str):
    """
    Atualiza o lead no DB com o wallet_id gerado.
    Tenta múltiplas tabelas.
    """
    db_path = db_path or LEAD_DB_PATH
    conn = sqlite3.connect(db_path)

    tables_to_try = ["leads", "registrations", "applications"]

    for table in tables_to_try:
        try:
            # Verificar se coluna wallet_id existe
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]

            if "wallet_id" not in columns:
                # Adicionar coluna se não existe
                conn.execute(f"ALTER TABLE {table} ADD COLUMN wallet_id TEXT")
                logger.info("Added wallet_id column to %s", table)

            # Tentar com lead_id
            id_columns = ["lead_id", "id", "reg_id", "application_id"]
            for id_col in id_columns:
                if id_col in columns:
                    conn.execute(
                        f"UPDATE {table} SET wallet_id = ? WHERE {id_col} = ?",
                        (wallet_id, lead_id)
                    )
                    conn.commit()
                    logger.info("Updated %s.%s=%s with wallet_id=%s",
                                table, id_col, lead_id, wallet_id)
                    conn.close()
                    return True
        except sqlite3.OperationalError:
            continue

    conn.close()
    return False


def provision_all_pending(db_path: str = None) -> dict:
    """
    Provisiona todos os leads APPROVED que ainda não têm WALLET.
    Retorna resumo.
    """
    leads = find_leads_without_wallet(db_path)

    if not leads:
        logger.info("No pending leads to provision")
        return {"total": 0, "provisioned": 0, "errors": 0}

    results = {"total": len(leads), "provisioned": 0, "errors": 0, "wallets": []}

    for lead in leads:
        try:
            result = on_lead_approved(lead)
            if result and result.get("status") == "ok":
                wallet_id = result.get("wallet_id", "")
                results["provisioned"] += 1
                results["wallets"].append({
                    "lead_id": lead["lead_id"],
                    "wallet_id": wallet_id,
                    "kind": "PJ" if lead.get("company") else "PF",
                })

                # Atualizar lead DB
                update_lead_with_wallet(db_path or LEAD_DB_PATH,
                                        lead["lead_id"], wallet_id)
            else:
                results["errors"] += 1
                logger.warning("Failed to provision lead %s", lead["lead_id"])
        except Exception as e:
            results["errors"] += 1
            logger.error("Error provisioning lead %s: %s", lead["lead_id"], str(e))

    logger.info(
        "BATCH PROVISION: %d total, %d provisioned, %d errors",
        results["total"], results["provisioned"], results["errors"]
    )

    return results


def watch_and_provision(interval: int = 60, db_path: str = None):
    """
    Modo watcher: verifica periodicamente por leads sem wallet.
    Roda em loop infinito.

    Uso: python3 wallet_bridge.py watch --interval 60
    """
    logger.info("WATCHER: Starting with interval=%ds, db=%s", interval, db_path or LEAD_DB_PATH)
    print(f"WINDI Wallet Watcher — checking every {interval}s")
    print(f"DB: {db_path or LEAD_DB_PATH}")
    print(f"API: {GOVERNANCE_API_URL}")
    print("Press Ctrl+C to stop\n")

    cycle = 0
    while True:
        cycle += 1
        try:
            result = provision_all_pending(db_path)
            if result["provisioned"] > 0:
                print(f"[{datetime.now(timezone.utc).isoformat()}] "
                      f"Cycle {cycle}: Provisioned {result['provisioned']} wallets")
                for w in result.get("wallets", []):
                    print(f"  → {w['lead_id']} → {w['wallet_id']} ({w['kind']})")
            elif cycle % 10 == 0:
                # Log heartbeat a cada 10 ciclos
                print(f"[{datetime.now(timezone.utc).isoformat()}] "
                      f"Cycle {cycle}: No pending leads (heartbeat)")
        except KeyboardInterrupt:
            print("\nWatcher stopped.")
            break
        except Exception as e:
            logger.error("WATCHER: Error in cycle %d: %s", cycle, str(e))

        time.sleep(interval)


# ============================================================================
# SNIPPET DE INTEGRAÇÃO — Código exato para o Lead Admin
# ============================================================================

INTEGRATION_SNIPPET_PYTHON = """
# ============================================================================
# WALLET AUTO-PROVISION — Adicionar ao Lead Admin (id_genesis / app.py)
# ============================================================================
# Localizar a função que trata o botão APPROVE e adicionar DEPOIS
# da mudança de status para 'APPROVED':
#
# OPÇÃO 1: Import direto (recomendado se no mesmo servidor)
# ─────────────────────────────────────────────────────────────────────────────

import sys
sys.path.insert(0, '/opt/windi/wallet')
from wallet_bridge import on_lead_approved

# Dentro da função de aprovação, DEPOIS de marcar status = APPROVED:
def after_approve(lead_id, lead_data):
    \"\"\"Chamar esta função após aprovar o lead.\"\"\"
    wallet_result = on_lead_approved({
        "lead_id": lead_data.get("lead_id", lead_id),
        "name": lead_data.get("name", ""),
        "email": lead_data.get("email", ""),
        "company": lead_data.get("company", "-"),
        "interest": lead_data.get("interest", "free"),
        "approved_by": "admin:jober",
    })

    if wallet_result and wallet_result.get("status") == "ok":
        # Salvar wallet_id no lead
        # update_lead(lead_id, wallet_id=wallet_result["wallet_id"])
        return wallet_result
    return None


# OPÇÃO 2: HTTP Webhook (se o Lead Admin não pode importar Python)
# ─────────────────────────────────────────────────────────────────────────────

import requests

def after_approve_webhook(lead_id, lead_data):
    \"\"\"Chamar via HTTP para a Governance API.\"\"\"
    resp = requests.post(
        "http://localhost:8080/api/wallet/bridge/approve",
        json={
            "lead_id": lead_data.get("lead_id", lead_id),
            "name": lead_data.get("name", ""),
            "email": lead_data.get("email", ""),
            "company": lead_data.get("company", "-"),
            "interest": lead_data.get("interest", "free"),
            "approved_by": "admin:jober",
        },
        timeout=10,
    )
    if resp.status_code in (200, 201):
        return resp.json()
    return None
"""

INTEGRATION_SNIPPET_JS = """
// ============================================================================
// WALLET AUTO-PROVISION — JavaScript para o frontend do Lead Admin
// ============================================================================
// Adicionar ao click handler do botão APPROVE no admin dashboard.
// Este código chama a Governance API diretamente após a aprovação.
// ============================================================================

async function provisionWalletAfterApprove(leadData) {
    /**
     * Chamar após o botão APPROVE mudar o status para 'APPROVED'.
     *
     * @param {Object} leadData - Dados do lead aprovado
     * @param {string} leadData.lead_id - ID do lead
     * @param {string} leadData.name - Nome do humano
     * @param {string} leadData.email - Email
     * @param {string} leadData.company - Empresa (ou "-" se PF)
     * @param {string} leadData.interest - Interesse/tier
     */
    try {
        const response = await fetch('/api/wallet/bridge/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lead_id: leadData.lead_id,
                name: leadData.name,
                email: leadData.email,
                company: leadData.company || '-',
                interest: leadData.interest || 'free',
                approved_by: 'admin:jober',
            }),
        });

        const result = await response.json();

        if (result.status === 'ok') {
            console.log('WALLET PROVISIONED:', result.wallet_id);

            // Atualizar UI com wallet_id
            const row = document.querySelector(`[data-lead-id="${leadData.lead_id}"]`);
            if (row) {
                const walletCell = row.querySelector('.wallet-id');
                if (walletCell) {
                    walletCell.textContent = result.wallet_id;
                    walletCell.style.color = '#c9a227'; // gold
                }
            }

            // Feedback visual
            showNotification(`WALLET criado: ${result.wallet_id}`, 'success');

            return result;
        } else {
            console.error('Wallet provision failed:', result);
            showNotification('WALLET falhou: ' + (result.error || 'unknown'), 'error');
            return null;
        }
    } catch (err) {
        console.error('Wallet bridge error:', err);
        showNotification('WALLET bridge error', 'error');
        return null;
    }
}

// Helper: mostrar notificação
function showNotification(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = `notification notification-${type}`;
    el.textContent = msg;
    el.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        padding: 12px 20px; border-radius: 8px; font-size: 14px;
        background: ${type === 'success' ? '#1a3a2a' : '#3a1a1a'};
        color: ${type === 'success' ? '#22c55e' : '#ef4444'};
        border: 1px solid ${type === 'success' ? '#22c55e40' : '#ef444440'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 5000);
}

// ============================================================================
// INTEGRAÇÃO COM BOTÃO APPROVE EXISTENTE
// ============================================================================
// Localizar o handler do botão Approve e adicionar chamada:
//
// Exemplo (se o botão faz um fetch/POST para aprovar):
//
//   async function approveLead(leadId) {
//       // ... código existente de aprovação ...
//       const approveResponse = await fetch(`/api/leads/${leadId}/approve`, ...);
//
//       // ─── ADICIONAR AQUI ───
//       if (approveResponse.ok) {
//           const leadData = { lead_id: leadId, name: ..., email: ..., ... };
//           await provisionWalletAfterApprove(leadData);
//       }
//       // ─── FIM ──────────────
//   }
"""


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="WINDI Wallet Bridge — Auto-Provision"
    )
    subparsers = parser.add_subparsers(dest="command")

    # provision-all
    sub_provision = subparsers.add_parser(
        "provision-all",
        help="Provisiona todos os leads pendentes"
    )
    sub_provision.add_argument("--db", default=LEAD_DB_PATH)

    # watch
    sub_watch = subparsers.add_parser(
        "watch",
        help="Observa DB e auto-provisiona em loop"
    )
    sub_watch.add_argument("--interval", type=int, default=60)
    sub_watch.add_argument("--db", default=LEAD_DB_PATH)

    # show-snippets
    sub_snippets = subparsers.add_parser(
        "show-snippets",
        help="Mostra snippets de integração"
    )

    # test
    sub_test = subparsers.add_parser(
        "test",
        help="Testa provisioning com dados mock"
    )

    args = parser.parse_args()

    if args.command == "provision-all":
        result = provision_all_pending(args.db)
        print(json.dumps(result, indent=2))

    elif args.command == "watch":
        watch_and_provision(args.interval, args.db)

    elif args.command == "show-snippets":
        print("=" * 60)
        print("PYTHON INTEGRATION SNIPPET")
        print("=" * 60)
        print(INTEGRATION_SNIPPET_PYTHON)
        print("\n")
        print("=" * 60)
        print("JAVASCRIPT INTEGRATION SNIPPET")
        print("=" * 60)
        print(INTEGRATION_SNIPPET_JS)

    elif args.command == "test":
        print("=" * 60)
        print("WINDI Wallet Bridge — Test Mode")
        print("=" * 60)

        test_lead = {
            "lead_id": "LEAD-TEST-BRIDGE-001",
            "name": "Bridge Test Human",
            "email": "bridge@test.de",
            "company": "Test GmbH",
            "interest": "governance",
            "approved_by": "admin:test",
        }

        print(f"\nTest lead: {json.dumps(test_lead, indent=2)}")
        print("\nCalling on_lead_approved()...")

        result = on_lead_approved(test_lead)
        print(f"\nResult: {json.dumps(result, indent=2)}")

    else:
        parser.print_help()
        print("\n🐉 WINDI Wallet Bridge v1.0.0")
        print("   Modes: provision-all | watch | show-snippets | test")
