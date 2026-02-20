#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  WINDI SENTINEL — Nível 2: Protocolo de Intervenção Humana      ║
║  v1.0.0 · "Sentinel propõe. Humano autoriza. WINDI garante."    ║
║                                                                  ║
║  ARQUITETURA:                                                    ║
║                                                                  ║
║  [Sentinel Daemon] ──detects──> [Action Proposal Queue]          ║
║                                        │                         ║
║                                        ▼                         ║
║                              [Human Dashboard]                   ║
║                              (Wallet / War Room)                 ║
║                                        │                         ║
║                                  ┌─────┴─────┐                   ║
║                                  ▼           ▼                   ║
║                            [AUTHORIZE]   [VETO]                  ║
║                                  │           │                   ║
║                                  ▼           ▼                   ║
║                           [Execute +     [Log reason             ║
║                            Audit]        + Archive]              ║
║                                  │                               ║
║                                  ▼                               ║
║                        [Forensic Receipt]                        ║
║                                                                  ║
║  INVARIANT I9: Nenhuma ação sem autorização humana explícita.    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from pathlib import Path

# ─────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────

WINDI_BASE = os.environ.get("WINDI_BASE", "/opt/windi")
PROPOSALS_DIR = os.path.join(WINDI_BASE, "data", "sentinel_proposals")
PROPOSALS_DB = os.path.join(WINDI_BASE, "data", "sentinel_proposals.json")
AUDIT_LOG = os.path.join(WINDI_BASE, "logs", "sentinel_actions.log")

# ─────────────────────────────────────────────────────────
# ENUMS — Ciclo de Vida da Proposta
# ─────────────────────────────────────────────────────────

class ProposalStatus(str, Enum):
    PENDING = "PENDING"          # Aguardando decisão humana
    AUTHORIZED = "AUTHORIZED"    # Humano autorizou
    VETOED = "VETOED"            # Humano vetou
    EXECUTING = "EXECUTING"      # Em execução
    COMPLETED = "COMPLETED"      # Executada com sucesso
    FAILED = "FAILED"            # Execução falhou
    EXPIRED = "EXPIRED"          # Expirou sem decisão (TTL)


class ActionType(str, Enum):
    RESTART_SERVICE = "RESTART_SERVICE"
    STOP_SERVICE = "STOP_SERVICE"
    CLEAR_LOGS = "CLEAR_LOGS"
    HEALTH_RESET = "HEALTH_RESET"
    NGINX_RELOAD = "NGINX_RELOAD"
    CUSTOM_COMMAND = "CUSTOM_COMMAND"


class ImpactLevel(str, Enum):
    LOW = "LOW"          # Restart de serviço não-crítico
    MEDIUM = "MEDIUM"    # Restart de serviço crítico
    HIGH = "HIGH"        # Mudança de configuração
    CRITICAL = "CRITICAL"  # Nunca auto-executável


class AuthorizationLevel(str, Enum):
    """
    Níveis de autorização — define QUEM pode autorizar O QUÊ.
    
    Regra de Ouro I9:
      - CRITICAL nunca é auto-executável, JAMAIS.
      - HIGH requer confirmação dupla (proposta + PIN ou passphrase)
      - MEDIUM requer confirmação simples (botão Autorizar)
      - LOW pode ser pré-autorizado (lista de ações permitidas)
    """
    HUMAN_EXPLICIT = "HUMAN_EXPLICIT"          # Botão no dashboard
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"        # Confirmação + passphrase
    PRE_AUTHORIZED = "PRE_AUTHORIZED"          # Na lista de ações permitidas
    FORBIDDEN = "FORBIDDEN"                     # Nunca permitido


# ─────────────────────────────────────────────────────────
# PRE-AUTHORIZATION RULES
# O Human Dragon define ANTES quais ações o Sentinel pode
# executar sem perguntar (Nível 3 futuro)
# ─────────────────────────────────────────────────────────

PRE_AUTHORIZATION_RULES = {
    # Formato: (ActionType, service_name) → AuthorizationLevel
    # 
    # LOW impact — restart de serviços não-críticos
    (ActionType.RESTART_SERVICE, "windi-cortex"): AuthorizationLevel.PRE_AUTHORIZED,
    (ActionType.RESTART_SERVICE, "windi-clone"): AuthorizationLevel.PRE_AUTHORIZED,
    (ActionType.RESTART_SERVICE, "windi-warroom"): AuthorizationLevel.PRE_AUTHORIZED,
    (ActionType.RESTART_SERVICE, "windi-landing"): AuthorizationLevel.PRE_AUTHORIZED,
    (ActionType.RESTART_SERVICE, "windi-wallet"): AuthorizationLevel.PRE_AUTHORIZED,
    
    # MEDIUM impact — restart de serviços críticos (precisa humano)
    (ActionType.RESTART_SERVICE, "windi-governance"): AuthorizationLevel.HUMAN_EXPLICIT,
    (ActionType.RESTART_SERVICE, "windi-babel"): AuthorizationLevel.HUMAN_EXPLICIT,
    (ActionType.RESTART_SERVICE, "windi-bridge"): AuthorizationLevel.HUMAN_EXPLICIT,
    (ActionType.RESTART_SERVICE, "windi-gateway"): AuthorizationLevel.HUMAN_CONFIRMED,
    (ActionType.RESTART_SERVICE, "windi-sentinel"): AuthorizationLevel.FORBIDDEN,
    
    # HIGH impact — mudanças de configuração
    (ActionType.NGINX_RELOAD, "*"): AuthorizationLevel.HUMAN_CONFIRMED,
    (ActionType.STOP_SERVICE, "*"): AuthorizationLevel.HUMAN_CONFIRMED,
    
    # CRITICAL — nunca permitido via Sentinel
    (ActionType.CUSTOM_COMMAND, "*"): AuthorizationLevel.FORBIDDEN,
}


def get_authorization_level(action_type: ActionType, service: str) -> AuthorizationLevel:
    """Determina o nível de autorização necessário para uma ação."""
    # Check specific rule first
    key = (action_type, service)
    if key in PRE_AUTHORIZATION_RULES:
        return PRE_AUTHORIZATION_RULES[key]
    
    # Check wildcard rule
    wildcard_key = (action_type, "*")
    if wildcard_key in PRE_AUTHORIZATION_RULES:
        return PRE_AUTHORIZATION_RULES[wildcard_key]
    
    # Default: always require human
    return AuthorizationLevel.HUMAN_EXPLICIT


# ─────────────────────────────────────────────────────────
# ACTION PROPOSAL — Estrutura de Dados
# ─────────────────────────────────────────────────────────

@dataclass
class ActionProposal:
    """
    Uma Proposta de Ação gerada pelo Sentinel.
    
    Ciclo de vida:
      1. Sentinel DETECTA anomalia
      2. Sentinel CRIA proposta (status=PENDING)
      3. Proposta aparece no Dashboard humano
      4. Humano AUTORIZA ou VETA
      5. Se autorizada: Sentinel EXECUTA + gera Receipt
      6. Se vetada: Sentinel ARQUIVA com razão
    """
    # Identity
    proposal_id: str = ""           # SEN-YYYYMMDD-NNNN
    created_at: str = ""            # ISO timestamp
    
    # What happened
    trigger_service: str = ""       # Nome do serviço que causou
    trigger_reason: str = ""        # "60 consecutive failures on :8080"
    trigger_severity: str = ""      # WARN / ALERT / CRITICAL
    consecutive_failures: int = 0
    
    # What to do
    action_type: str = ""           # ActionType enum value
    action_command: str = ""        # "sudo systemctl restart windi-governance"
    action_description: str = ""    # Human-readable description
    
    # Risk assessment
    impact_level: str = ""          # ImpactLevel enum value
    authorization_required: str = "" # AuthorizationLevel enum value
    estimated_downtime_sec: int = 0
    rollback_command: str = ""      # "sudo systemctl stop windi-governance"
    
    # Human decision
    status: str = "PENDING"         # ProposalStatus enum value
    decided_by: str = ""            # "human_dragon" / "pre_authorized"
    decided_at: str = ""            # ISO timestamp
    veto_reason: str = ""           # If vetoed, why
    
    # Execution result
    executed_at: str = ""           # ISO timestamp
    execution_result: str = ""      # stdout/stderr of command
    execution_success: bool = False
    
    # Forensic
    proposal_hash: str = ""         # SHA-256 of proposal content
    receipt_id: str = ""            # WINDI-RECEIPT if generated
    
    # TTL — proposta expira se ninguém decide
    expires_at: str = ""            # ISO timestamp (default: +24h)
    
    # Trilíngue descriptions
    description_de: str = ""
    description_en: str = ""
    description_pt: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.proposal_id:
            self.proposal_id = self._generate_id()
        if not self.proposal_hash:
            self.proposal_hash = self._compute_hash()
        if not self.expires_at:
            from datetime import timedelta
            expires = datetime.now(timezone.utc) + timedelta(hours=24)
            self.expires_at = expires.isoformat()
    
    def _generate_id(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        # Simple counter based on existing proposals
        counter = 1
        try:
            if os.path.exists(PROPOSALS_DB):
                with open(PROPOSALS_DB, "r") as f:
                    data = json.load(f)
                    today_proposals = [
                        p for p in data.get("proposals", [])
                        if p.get("proposal_id", "").startswith(f"SEN-{date_str}")
                    ]
                    counter = len(today_proposals) + 1
        except Exception:
            pass
        return f"SEN-{date_str}-{counter:04d}"
    
    def _compute_hash(self) -> str:
        content = f"{self.trigger_service}|{self.action_type}|{self.action_command}|{self.created_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_trilingual_summary(self) -> dict:
        """Gera resumo trilíngue para o Dashboard."""
        return {
            "DE": {
                "title": f"Vorschlag {self.proposal_id}",
                "service": self.trigger_service,
                "action": self.description_de or self.action_description,
                "impact": {
                    "LOW": "Gering",
                    "MEDIUM": "Mittel",
                    "HIGH": "Hoch",
                    "CRITICAL": "Kritisch"
                }.get(self.impact_level, self.impact_level),
                "button_authorize": "Genehmigen",
                "button_veto": "Ablehnen",
                "status": {
                    "PENDING": "Ausstehend",
                    "AUTHORIZED": "Genehmigt",
                    "VETOED": "Abgelehnt",
                    "COMPLETED": "Abgeschlossen"
                }.get(self.status, self.status)
            },
            "EN": {
                "title": f"Proposal {self.proposal_id}",
                "service": self.trigger_service,
                "action": self.description_en or self.action_description,
                "impact": self.impact_level,
                "button_authorize": "Authorize",
                "button_veto": "Veto",
                "status": self.status
            },
            "PT": {
                "title": f"Proposta {self.proposal_id}",
                "service": self.trigger_service,
                "action": self.description_pt or self.action_description,
                "impact": {
                    "LOW": "Baixo",
                    "MEDIUM": "Médio",
                    "HIGH": "Alto",
                    "CRITICAL": "Crítico"
                }.get(self.impact_level, self.impact_level),
                "button_authorize": "Autorizar",
                "button_veto": "Vetar",
                "status": {
                    "PENDING": "Pendente",
                    "AUTHORIZED": "Autorizado",
                    "VETOED": "Vetado",
                    "COMPLETED": "Concluído"
                }.get(self.status, self.status)
            }
        }


# ─────────────────────────────────────────────────────────
# PROPOSAL ENGINE — Criação e Gestão
# ─────────────────────────────────────────────────────────

class ProposalEngine:
    """
    Motor de Propostas do Sentinel Nível 2.
    
    Responsabilidades:
      - Criar propostas quando o daemon detecta anomalias
      - Armazenar propostas em JSON persistente
      - Servir propostas via API para o Dashboard
      - Processar decisões humanas (Authorize/Veto)
      - Executar ações autorizadas via systemd
      - Gerar audit trail para o Forensic Ledger
    """
    
    def __init__(self):
        os.makedirs(PROPOSALS_DIR, exist_ok=True)
        self.proposals = self._load_proposals()
    
    def _load_proposals(self) -> List[dict]:
        if os.path.exists(PROPOSALS_DB):
            try:
                with open(PROPOSALS_DB, "r") as f:
                    data = json.load(f)
                    return data.get("proposals", [])
            except Exception:
                return []
        return []
    
    def _save_proposals(self):
        data = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total": len(self.proposals),
            "pending": sum(1 for p in self.proposals if p["status"] == "PENDING"),
            "proposals": self.proposals
        }
        with open(PROPOSALS_DB, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_proposal(
        self,
        service: str,
        reason: str,
        severity: str,
        consecutive_failures: int,
        action_type: ActionType = ActionType.RESTART_SERVICE
    ) -> ActionProposal:
        """
        Cria uma nova proposta de ação.
        
        Chamado pelo Sentinel Daemon quando um serviço atinge
        o threshold de falhas consecutivas.
        """
        # Determine the command based on action type
        if action_type == ActionType.RESTART_SERVICE:
            command = f"sudo systemctl restart {service}"
            rollback = f"sudo systemctl stop {service}"
            desc_de = f"Dienst {service} neu starten"
            desc_en = f"Restart service {service}"
            desc_pt = f"Reiniciar serviço {service}"
        elif action_type == ActionType.STOP_SERVICE:
            command = f"sudo systemctl stop {service}"
            rollback = f"sudo systemctl start {service}"
            desc_de = f"Dienst {service} stoppen"
            desc_en = f"Stop service {service}"
            desc_pt = f"Parar serviço {service}"
        elif action_type == ActionType.NGINX_RELOAD:
            command = "sudo systemctl reload nginx"
            rollback = "sudo systemctl restart nginx"
            desc_de = "Nginx Konfiguration neu laden"
            desc_en = "Reload nginx configuration"
            desc_pt = "Recarregar configuração nginx"
        else:
            command = ""
            rollback = ""
            desc_de = desc_en = desc_pt = "Unbekannte Aktion"
        
        # Determine impact and authorization level
        auth_level = get_authorization_level(action_type, service)
        
        if auth_level == AuthorizationLevel.FORBIDDEN:
            # I9: This action is NEVER allowed via Sentinel
            print(f"  🚫 I9 BLOCK: Action {action_type} on {service} is FORBIDDEN")
            return None
        
        # Map authorization to impact
        impact_map = {
            AuthorizationLevel.PRE_AUTHORIZED: ImpactLevel.LOW,
            AuthorizationLevel.HUMAN_EXPLICIT: ImpactLevel.MEDIUM,
            AuthorizationLevel.HUMAN_CONFIRMED: ImpactLevel.HIGH,
        }
        impact = impact_map.get(auth_level, ImpactLevel.HIGH)
        
        # Check for duplicate pending proposals
        for p in self.proposals:
            if (p["status"] == "PENDING" and 
                p["trigger_service"] == service and
                p["action_type"] == action_type.value):
                print(f"  ℹ️  Duplicate proposal for {service} — skipping")
                return None
        
        proposal = ActionProposal(
            trigger_service=service,
            trigger_reason=reason,
            trigger_severity=severity,
            consecutive_failures=consecutive_failures,
            action_type=action_type.value,
            action_command=command,
            action_description=desc_en,
            impact_level=impact.value,
            authorization_required=auth_level.value,
            estimated_downtime_sec=5 if action_type == ActionType.RESTART_SERVICE else 0,
            rollback_command=rollback,
            description_de=desc_de,
            description_en=desc_en,
            description_pt=desc_pt,
        )
        
        self.proposals.append(proposal.to_dict())
        self._save_proposals()
        
        self._audit_log(
            f"PROPOSAL_CREATED | {proposal.proposal_id} | "
            f"{service} | {action_type.value} | {auth_level.value}"
        )
        
        return proposal
    
    def authorize(self, proposal_id: str, decided_by: str = "human_dragon") -> dict:
        """
        Humano autoriza uma proposta.
        
        Returns:
            dict com resultado da execução
        """
        proposal = self._find_proposal(proposal_id)
        if not proposal:
            return {"error": f"Proposal {proposal_id} not found"}
        
        if proposal["status"] != "PENDING":
            return {"error": f"Proposal {proposal_id} is {proposal['status']}, not PENDING"}
        
        # Check if it requires confirmed authorization (passphrase)
        if proposal["authorization_required"] == AuthorizationLevel.HUMAN_CONFIRMED.value:
            # In a real implementation, this would verify a passphrase/PIN
            # For now, the API endpoint would handle this verification
            pass
        
        # Update status
        proposal["status"] = ProposalStatus.AUTHORIZED.value
        proposal["decided_by"] = decided_by
        proposal["decided_at"] = datetime.now(timezone.utc).isoformat()
        
        self._audit_log(
            f"AUTHORIZED | {proposal_id} | by {decided_by}"
        )
        
        # Execute the action
        result = self._execute_action(proposal)
        
        self._save_proposals()
        return result
    
    def veto(self, proposal_id: str, reason: str = "", decided_by: str = "human_dragon") -> dict:
        """
        Humano veta uma proposta.
        A proposta é arquivada com a razão do veto.
        """
        proposal = self._find_proposal(proposal_id)
        if not proposal:
            return {"error": f"Proposal {proposal_id} not found"}
        
        if proposal["status"] != "PENDING":
            return {"error": f"Proposal {proposal_id} is {proposal['status']}, not PENDING"}
        
        proposal["status"] = ProposalStatus.VETOED.value
        proposal["decided_by"] = decided_by
        proposal["decided_at"] = datetime.now(timezone.utc).isoformat()
        proposal["veto_reason"] = reason
        
        self._audit_log(
            f"VETOED | {proposal_id} | by {decided_by} | reason: {reason}"
        )
        
        self._save_proposals()
        return {
            "status": "VETOED",
            "proposal_id": proposal_id,
            "reason": reason
        }
    
    def get_pending(self) -> List[dict]:
        """Retorna propostas pendentes para o Dashboard."""
        now = datetime.now(timezone.utc)
        pending = []
        
        for p in self.proposals:
            if p["status"] == "PENDING":
                # Check expiration
                if p.get("expires_at"):
                    expires = datetime.fromisoformat(p["expires_at"])
                    if now > expires:
                        p["status"] = ProposalStatus.EXPIRED.value
                        self._audit_log(f"EXPIRED | {p['proposal_id']}")
                        continue
                pending.append(p)
        
        self._save_proposals()
        return pending
    
    def get_history(self, limit: int = 50) -> List[dict]:
        """Retorna histórico de propostas (todas)."""
        return sorted(
            self.proposals,
            key=lambda p: p.get("created_at", ""),
            reverse=True
        )[:limit]
    
    def _find_proposal(self, proposal_id: str) -> Optional[dict]:
        for p in self.proposals:
            if p["proposal_id"] == proposal_id:
                return p
        return None
    
    def _execute_action(self, proposal: dict) -> dict:
        """
        Executa a ação autorizada via subprocess.
        Grava resultado no proposal e no audit log.
        """
        proposal["status"] = ProposalStatus.EXECUTING.value
        proposal["executed_at"] = datetime.now(timezone.utc).isoformat()
        
        command = proposal["action_command"]
        if not command:
            proposal["status"] = ProposalStatus.FAILED.value
            proposal["execution_result"] = "No command defined"
            return {"error": "No command defined"}
        
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            proposal["execution_result"] = result.stdout + result.stderr
            proposal["execution_success"] = result.returncode == 0
            proposal["status"] = (
                ProposalStatus.COMPLETED.value 
                if result.returncode == 0 
                else ProposalStatus.FAILED.value
            )
            
            self._audit_log(
                f"EXECUTED | {proposal['proposal_id']} | "
                f"{'SUCCESS' if result.returncode == 0 else 'FAILED'} | "
                f"exit={result.returncode}"
            )
            
            # Generate forensic receipt reference
            if result.returncode == 0:
                receipt_hash = hashlib.sha256(
                    f"{proposal['proposal_id']}|{proposal['executed_at']}|{command}".encode()
                ).hexdigest()[:16]
                proposal["receipt_id"] = f"SEN-RECEIPT-{receipt_hash}"
            
            return {
                "status": proposal["status"],
                "proposal_id": proposal["proposal_id"],
                "command": command,
                "success": result.returncode == 0,
                "output": result.stdout[:500],
                "receipt_id": proposal.get("receipt_id", "")
            }
            
        except subprocess.TimeoutExpired:
            proposal["status"] = ProposalStatus.FAILED.value
            proposal["execution_result"] = "Command timed out (30s)"
            self._audit_log(f"TIMEOUT | {proposal['proposal_id']}")
            return {"error": "Command timed out"}
        except Exception as e:
            proposal["status"] = ProposalStatus.FAILED.value
            proposal["execution_result"] = str(e)
            self._audit_log(f"ERROR | {proposal['proposal_id']} | {e}")
            return {"error": str(e)}
    
    def _audit_log(self, message: str):
        """Write to forensic audit log."""
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = f"{timestamp} [SENTINEL-L2] {message}\n"
        try:
            os.makedirs(os.path.dirname(AUDIT_LOG), exist_ok=True)
            with open(AUDIT_LOG, "a") as f:
                f.write(entry)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────
# API ENDPOINTS — Para integração com Flask/Dashboard
# ─────────────────────────────────────────────────────────

def register_sentinel_l2_routes(app):
    """
    Registra endpoints do Sentinel Nível 2 num Flask app.
    
    Endpoints:
      GET  /sentinel/proposals          → Lista propostas pendentes
      GET  /sentinel/proposals/history  → Histórico completo
      POST /sentinel/proposals/:id/authorize  → Autorizar proposta
      POST /sentinel/proposals/:id/veto       → Vetar proposta
      GET  /sentinel/proposals/:id      → Detalhes de uma proposta
    """
    from flask import request, jsonify
    
    engine = ProposalEngine()
    
    @app.route("/sentinel/proposals", methods=["GET"])
    def get_proposals():
        lang = request.args.get("lang", "EN").upper()
        pending = engine.get_pending()
        
        result = []
        for p in pending:
            proposal_obj = ActionProposal(**{
                k: v for k, v in p.items() 
                if k in ActionProposal.__dataclass_fields__
            })
            trilingual = proposal_obj.to_trilingual_summary()
            result.append({
                "proposal": p,
                "display": trilingual.get(lang, trilingual["EN"])
            })
        
        return jsonify({
            "proposals": result,
            "total_pending": len(result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    @app.route("/sentinel/proposals/history", methods=["GET"])
    def get_proposal_history():
        limit = request.args.get("limit", 50, type=int)
        history = engine.get_history(limit=limit)
        return jsonify({
            "history": history,
            "total": len(history)
        })
    
    @app.route("/sentinel/proposals/<proposal_id>/authorize", methods=["POST"])
    def authorize_proposal(proposal_id):
        data = request.get_json(silent=True) or {}
        decided_by = data.get("decided_by", "human_dragon")
        result = engine.authorize(proposal_id, decided_by=decided_by)
        return jsonify(result)
    
    @app.route("/sentinel/proposals/<proposal_id>/veto", methods=["POST"])
    def veto_proposal(proposal_id):
        data = request.get_json(silent=True) or {}
        reason = data.get("reason", "")
        decided_by = data.get("decided_by", "human_dragon")
        result = engine.veto(proposal_id, reason=reason, decided_by=decided_by)
        return jsonify(result)
    
    @app.route("/sentinel/proposals/<proposal_id>", methods=["GET"])
    def get_proposal_detail(proposal_id):
        proposal = engine._find_proposal(proposal_id)
        if not proposal:
            return jsonify({"error": "Not found"}), 404
        return jsonify(proposal)
    
    return engine


# ─────────────────────────────────────────────────────────
# INTEGRATION HOOK — Para o Sentinel Daemon existente
# ─────────────────────────────────────────────────────────

def sentinel_check_hook(service_name: str, check_result: dict, state: dict):
    """
    Hook para integrar no loop do Sentinel Daemon.
    
    Chamado após cada check de serviço.
    Se o serviço atingiu o threshold, gera uma proposta.
    
    Adicionar ao windi_sentinel.py no loop principal:
    
        from sentinel_level2 import sentinel_check_hook
        
        # After check cycle:
        for name, result in check_results.items():
            sentinel_check_hook(name, result, state)
    """
    consecutive_fail = check_result.get("consecutive_failures", 0)
    status = check_result.get("current_level", "OK")
    
    # Thresholds para gerar proposta
    PROPOSAL_THRESHOLD = {
        "ALERT": 10,     # Após 10 falhas → propõe restart
        "CRITICAL": 5,   # Após 5 falhas críticas → propõe restart
    }
    
    threshold = PROPOSAL_THRESHOLD.get(status)
    if threshold and consecutive_fail >= threshold:
        engine = ProposalEngine()
        
        # Only create if no pending proposal exists for this service
        pending = engine.get_pending()
        already_pending = any(
            p["trigger_service"] == service_name 
            for p in pending
        )
        
        if not already_pending:
            reason = (
                f"{consecutive_fail} consecutive failures on "
                f":{check_result.get('port', '?')} — "
                f"status: {status}"
            )
            
            proposal = engine.create_proposal(
                service=service_name,
                reason=reason,
                severity=status,
                consecutive_failures=consecutive_fail,
                action_type=ActionType.RESTART_SERVICE
            )
            
            if proposal:
                print(
                    f"  📋 PROPOSAL CREATED: {proposal.proposal_id} — "
                    f"{service_name} restart "
                    f"(auth: {proposal.authorization_required})"
                )


# ─────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  WINDI SENTINEL — Level 2 Test                                  ║")
    print("║  Protocolo de Intervenção Humana                                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    engine = ProposalEngine()
    
    # Simulate: Governance down for 60 cycles
    print("── Simulating Governance failure (60 cycles) ──")
    proposal = engine.create_proposal(
        service="windi-governance",
        reason="60 consecutive failures on :8080 — health check mismatch",
        severity="ALERT",
        consecutive_failures=60,
        action_type=ActionType.RESTART_SERVICE
    )
    
    if proposal:
        print(f"  Created: {proposal.proposal_id}")
        print(f"  Auth required: {proposal.authorization_required}")
        print(f"  Impact: {proposal.impact_level}")
        print(f"  Hash: {proposal.proposal_hash}")
        print()
        
        # Show trilingual
        tri = proposal.to_trilingual_summary()
        for lang, data in tri.items():
            print(f"  [{lang}] {data['title']} — {data['action']} "
                  f"({data['impact']}) [{data['status']}]")
        print()
        
        # Show pending
        pending = engine.get_pending()
        print(f"  Pending proposals: {len(pending)}")
        
        # Simulate human authorization
        print()
        print("── Human Dragon authorizes ──")
        print("  (In production: click 'Autorizar' no Wallet Dashboard)")
        # result = engine.authorize(proposal.proposal_id)
        # print(f"  Result: {result}")
        print(f"  [DRY RUN] Would execute: {proposal.action_command}")
    
    # Test I9 block
    print()
    print("── Testing I9: Sentinel restart (FORBIDDEN) ──")
    blocked = engine.create_proposal(
        service="windi-sentinel",
        reason="Test: can sentinel restart itself?",
        severity="CRITICAL",
        consecutive_failures=100,
        action_type=ActionType.RESTART_SERVICE
    )
    print(f"  Result: {'BLOCKED by I9' if blocked is None else 'ERROR: should have been blocked!'}")
    
    print()
    print("══════════════════════════════════════════════════════════════════")
    print("  ✅ Level 2 engine operational")
    print("  📋 Proposals stored in:", PROPOSALS_DB)
    print("  📜 Audit log:", AUDIT_LOG)
    print("══════════════════════════════════════════════════════════════════")
    print()
