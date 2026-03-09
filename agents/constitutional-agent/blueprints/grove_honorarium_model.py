"""
grove_honorarium_model.py
===================================================================
WINDI Grove Arena - Sovereign Flow - Honorarium Engine v1.0.0
===================================================================

H = Sigma [fase x agente x contexto] x identidade

AI processes. Human decides. WINDI guarantees.
Kempten, Bavaria - 09.03.2026
"""

from __future__ import annotations

import uuid
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ---------------------------------------------
#  ENUMS
# ---------------------------------------------

class AgentTier(str, Enum):
    """Tier do agente - define custo base por rodada e por selo."""
    ELITE      = "elite"       # W-LEGAL, W-COMPLY
    ESTRUTURAL = "estrutural"  # W-NOTARY, W-AUDIT, W-ACCT
    NARRATIVO  = "narrativo"   # W-COMM, W-JOURN, W-ARCH


class IdentityMultiplier(str, Enum):
    """Multiplicador de identidade do usuario."""
    PIONEER  = "pioneer"   # 0.5x - fundador perpetuo
    DID      = "did"       # 0.8x - DID validado
    FREE     = "free"      # 1.0x - usuario free
    EMPRESA  = "empresa"   # 1.2x - PJ (mas gera NF dedutivel)


class FlowPhase(str, Enum):
    """As 3 fases do Sovereign Flow."""
    SEED  = "seed"   # EUR0 - registro de intencao
    ARENA = "arena"  # custo por rodada x agentes
    SEAL  = "seal"   # custo fixo + co-signatarios -> Virtue Receipt


class DebitStatus(str, Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    REJECTED  = "rejected"
    REFUNDED  = "refunded"


# ---------------------------------------------
#  TABELA DE HONORARIOS
# ---------------------------------------------

AGENT_REGISTRY: dict[str, dict] = {
    "W-LEGAL-001":  {"tier": AgentTier.ELITE,      "name": "Legal",      "icon": "⚖️"},
    "W-COMPLY-001": {"tier": AgentTier.ELITE,      "name": "Compliance", "icon": "🛡️"},
    "W-NOTARY-001": {"tier": AgentTier.ESTRUTURAL, "name": "Notary",     "icon": "🔏"},
    "W-AUDIT-001":  {"tier": AgentTier.ESTRUTURAL, "name": "Auditor",    "icon": "🔍"},
    "W-ACCT-001":   {"tier": AgentTier.ESTRUTURAL, "name": "Accounting", "icon": "📊"},
    "W-COMM-001":   {"tier": AgentTier.NARRATIVO,  "name": "Communique", "icon": "📡"},
    "W-JOURN-001":  {"tier": AgentTier.NARRATIVO,  "name": "Journalist", "icon": "📰"},
    "W-ARCH-001":   {"tier": AgentTier.NARRATIVO,  "name": "Arquitec",   "icon": "🏗️"},
}

TIER_CREDITS: dict[AgentTier, dict] = {
    AgentTier.ELITE:      {"per_round": 15, "per_seal": 12},
    AgentTier.ESTRUTURAL: {"per_round": 8,  "per_seal": 6},
    AgentTier.NARRATIVO:  {"per_round": 5,  "per_seal": 4},
}

IDENTITY_MULTIPLIERS: dict[IdentityMultiplier, float] = {
    IdentityMultiplier.PIONEER: 0.5,
    IdentityMultiplier.DID:     0.8,
    IdentityMultiplier.FREE:    1.0,
    IdentityMultiplier.EMPRESA: 1.2,
}

# 1 credito = EUR0.01 (ajustavel via config)
CREDIT_TO_EUR: float = 0.01


# ---------------------------------------------
#  DATACLASSES
# ---------------------------------------------

@dataclass
class AgentHonorarium:
    """Honorario calculado para um unico agente numa rodada."""
    agent_id:        str
    agent_name:      str
    agent_tier:      AgentTier
    icon:            str
    phase:           FlowPhase
    credits_raw:     int    # antes do multiplicador de identidade
    credits_final:   float  # apos multiplicador
    eur_value:       float  # valor em euro
    multiplier_used: float
    justification:   str    # texto explicativo para o receipt


@dataclass
class RoundEstimate:
    """Estimativa completa de custo antes do debate comecar."""
    estimate_id:     str
    session_id:      str
    wallet_id:       str
    identity:        IdentityMultiplier
    agents_selected: list[str]
    phase:           FlowPhase
    timestamp_utc:   str
    line_items:      list[AgentHonorarium]
    total_credits:   float
    total_eur:       float
    breakdown:       dict
    hash_sha256:     str = field(default="")

    def __post_init__(self):
        if not self.hash_sha256:
            payload = json.dumps({
                "estimate_id":   self.estimate_id,
                "session_id":    self.session_id,
                "wallet_id":     self.wallet_id,
                "total_credits": self.total_credits,
                "timestamp_utc": self.timestamp_utc,
            }, sort_keys=True)
            self.hash_sha256 = hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class ConsumeReceipt:
    """Receipt gerado apos debito confirmado no Wallet."""
    receipt_id:      str
    estimate_id:     str
    session_id:      str
    wallet_id:       str
    phase:           FlowPhase
    agents:          list[str]
    credits_debited: float
    eur_charged:     float
    identity:        IdentityMultiplier
    status:          DebitStatus
    timestamp_utc:   str
    ledger_payload:  dict   # pronto para POST no Forensic Ledger (:8101)
    hash_sha256:     str = field(default="")

    def __post_init__(self):
        if not self.hash_sha256:
            payload = json.dumps({
                "receipt_id":      self.receipt_id,
                "credits_debited": self.credits_debited,
                "wallet_id":       self.wallet_id,
                "timestamp_utc":   self.timestamp_utc,
            }, sort_keys=True)
            self.hash_sha256 = hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------
#  MOTOR PRINCIPAL
# ---------------------------------------------

class HonorariumEngine:
    """
    Motor de precificacao soberana do Grove Arena.

    Uso basico:
        engine = HonorariumEngine()
        estimate = engine.estimate(
            session_id="sess-abc",
            wallet_id="wallet-xyz",
            agents=["W-LEGAL-001", "W-COMPLY-001"],
            phase=FlowPhase.ARENA,
            identity=IdentityMultiplier.PIONEER,
        )
        receipt = engine.consume(estimate)
    """

    def __init__(self, credit_to_eur: float = CREDIT_TO_EUR):
        self.credit_to_eur = credit_to_eur

    # -- ESTIMATE --

    def estimate(
        self,
        session_id:    str,
        wallet_id:     str,
        agents:        list[str],
        phase:         FlowPhase,
        identity:      IdentityMultiplier = IdentityMultiplier.FREE,
        rounds:        int = 1,
    ) -> RoundEstimate:
        """
        Calcula o custo ANTES do debate.
        Endpoint: POST /grove/arena/estimate
        """
        multiplier = IDENTITY_MULTIPLIERS[identity]
        line_items: list[AgentHonorarium] = []
        total_credits: float = 0.0

        for agent_id in agents:
            if agent_id not in AGENT_REGISTRY:
                raise ValueError(f"Agente desconhecido: {agent_id}")

            meta  = AGENT_REGISTRY[agent_id]
            tier  = meta["tier"]
            rates = TIER_CREDITS[tier]

            credits_raw   = rates["per_round"] if phase == FlowPhase.ARENA else rates["per_seal"]
            credits_raw  *= rounds
            credits_final = round(credits_raw * multiplier, 2)
            eur_value     = round(credits_final * self.credit_to_eur, 4)

            justification = self._build_justification(
                agent_id, meta, tier, phase, rounds, credits_raw, credits_final, identity
            )

            item = AgentHonorarium(
                agent_id        = agent_id,
                agent_name      = meta["name"],
                agent_tier      = tier,
                icon            = meta["icon"],
                phase           = phase,
                credits_raw     = credits_raw,
                credits_final   = credits_final,
                eur_value       = eur_value,
                multiplier_used = multiplier,
                justification   = justification,
            )
            line_items.append(item)
            total_credits += credits_final

        total_eur = round(total_credits * self.credit_to_eur, 4)

        breakdown = self._build_breakdown(line_items, identity, multiplier, rounds, phase)

        return RoundEstimate(
            estimate_id     = f"EST-{uuid.uuid4().hex[:12].upper()}",
            session_id      = session_id,
            wallet_id       = wallet_id,
            identity        = identity,
            agents_selected = agents,
            phase           = phase,
            timestamp_utc   = datetime.now(timezone.utc).isoformat(),
            line_items      = line_items,
            total_credits   = round(total_credits, 2),
            total_eur       = total_eur,
            breakdown       = breakdown,
        )

    # -- CONSUME --

    def consume(
        self,
        estimate:       RoundEstimate,
        wallet_balance: float = 9999.0,  # mock - integrar com Wallet real (:8099)
    ) -> ConsumeReceipt:
        """
        Debita o Wallet e gera o receipt para o Forensic Ledger.
        Endpoint: POST /grove/arena/consume
        """
        if wallet_balance < estimate.total_credits:
            raise InsufficientCreditsError(
                f"Saldo insuficiente: {wallet_balance} creditos disponiveis, "
                f"{estimate.total_credits} necessarios."
            )

        receipt_id = f"GRV-{uuid.uuid4().hex[:14].upper()}"
        ts         = datetime.now(timezone.utc).isoformat()

        ledger_payload = self._build_ledger_payload(estimate, receipt_id, ts)

        return ConsumeReceipt(
            receipt_id      = receipt_id,
            estimate_id     = estimate.estimate_id,
            session_id      = estimate.session_id,
            wallet_id       = estimate.wallet_id,
            phase           = estimate.phase,
            agents          = estimate.agents_selected,
            credits_debited = estimate.total_credits,
            eur_charged     = estimate.total_eur,
            identity        = estimate.identity,
            status          = DebitStatus.CONFIRMED,
            timestamp_utc   = ts,
            ledger_payload  = ledger_payload,
        )

    # -- PRICING TABLE --

    def pricing_table(self) -> dict:
        """
        Retorna tabela de precos completa.
        Endpoint: GET /grove/arena/pricing
        """
        rows = []
        for agent_id, meta in AGENT_REGISTRY.items():
            tier  = meta["tier"]
            rates = TIER_CREDITS[tier]
            rows.append({
                "agent_id":          agent_id,
                "name":              meta["name"],
                "icon":              meta["icon"],
                "tier":              tier.value,
                "credits_per_round": rates["per_round"],
                "credits_per_seal":  rates["per_seal"],
                "eur_per_round":     round(rates["per_round"] * self.credit_to_eur, 4),
                "eur_per_seal":      round(rates["per_seal"]  * self.credit_to_eur, 4),
            })

        multipliers = {
            k.value: {"factor": v, "desc": self._multiplier_desc(k)}
            for k, v in IDENTITY_MULTIPLIERS.items()
        }

        return {
            "version":          "1.0.0",
            "credit_to_eur":    self.credit_to_eur,
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "agents":           rows,
            "identity_multipliers": multipliers,
            "tiers": {
                t.value: {"per_round": r["per_round"], "per_seal": r["per_seal"]}
                for t, r in TIER_CREDITS.items()
            },
        }

    # -- HELPERS --

    def _build_justification(
        self, agent_id, meta, tier, phase, rounds, credits_raw, credits_final, identity
    ) -> str:
        action = "consultoria" if phase == FlowPhase.ARENA else "ato notarial"
        discount = ""
        if identity == IdentityMultiplier.PIONEER:
            discount = " (50% desconto Pioneer perpetuo)"
        elif identity == IdentityMultiplier.DID:
            discount = " (20% desconto DID validado)"
        elif identity == IdentityMultiplier.EMPRESA:
            discount = " (+20% PJ - NF dedutivel incluida)"
        return (
            f"{meta['icon']} {meta['name']} [{tier.value.upper()}] - "
            f"{action} x {rounds} rodada(s): "
            f"{credits_raw} creditos brutos -> {credits_final} creditos liquidos{discount}."
        )

    def _build_breakdown(self, items, identity, multiplier, rounds, phase) -> dict:
        by_tier: dict[str, dict] = {}
        for item in items:
            t = item.agent_tier.value
            if t not in by_tier:
                by_tier[t] = {"agents": [], "credits": 0.0, "eur": 0.0}
            by_tier[t]["agents"].append(item.agent_id)
            by_tier[t]["credits"] += item.credits_final
            by_tier[t]["eur"]     += item.eur_value

        return {
            "by_tier":            by_tier,
            "identity":           identity.value,
            "multiplier":         multiplier,
            "rounds":             rounds,
            "phase":              phase.value,
            "formula":            "H = Sigma [fase x agente x contexto] x identidade",
        }

    def _build_ledger_payload(self, estimate: RoundEstimate, receipt_id: str, ts: str) -> dict:
        """Payload pronto para POST /api/receipts no Forensic Ledger (:8101)."""
        return {
            "id":             receipt_id,
            "actor":          estimate.wallet_id,
            "app":            "grove-arena",
            "doc_name":       f"Honorarium {estimate.phase.value.upper()} - {len(estimate.agents_selected)} agentes",
            "doc_type":       "doc",
            "governance_level": "HIGH",
            "metadata": {
                "estimate_id":    estimate.estimate_id,
                "session_id":     estimate.session_id,
                "phase":          estimate.phase.value,
                "agents":         estimate.agents_selected,
                "credits":        estimate.total_credits,
                "eur":            estimate.total_eur,
                "identity":       estimate.identity.value,
                "hash_estimate":  estimate.hash_sha256,
            },
            "timestamp": ts,
        }

    def _multiplier_desc(self, k: IdentityMultiplier) -> str:
        return {
            IdentityMultiplier.PIONEER:  "Fundador - 50% desconto perpetuo",
            IdentityMultiplier.DID:      "DID validado - 20% desconto",
            IdentityMultiplier.FREE:     "Usuario free - preco padrao",
            IdentityMultiplier.EMPRESA:  "PJ - +20% com NF dedutivel",
        }[k]


# ---------------------------------------------
#  EXCEPTIONS
# ---------------------------------------------

class InsufficientCreditsError(Exception):
    """Saldo insuficiente no Wallet para o honorario estimado."""


class UnknownAgentError(Exception):
    """Agent ID nao registrado no AGENT_REGISTRY."""


# ---------------------------------------------
#  FLASK ROUTES (para integrar ao grove_blueprint.py)
# ---------------------------------------------

def register_flask_routes(blueprint, engine: HonorariumEngine = None):
    """
    Registra os 3 endpoints do Sovereign Flow num Flask Blueprint.

    Uso no grove_blueprint.py:
        from grove_honorarium_model import HonorariumEngine, register_flask_routes
        engine = HonorariumEngine()
        register_flask_routes(grove_bp, engine)
    """
    from flask import request, jsonify
    from dataclasses import asdict

    if engine is None:
        engine = HonorariumEngine()

    @blueprint.route("/arena/pricing", methods=["GET"])
    def pricing_endpoint():
        """Tabela de precos publica por agente."""
        return jsonify(engine.pricing_table())

    @blueprint.route("/arena/estimate", methods=["POST"])
    def estimate_endpoint():
        """Oraculo de Custo - calcula honorario ANTES do debate."""
        data = request.get_json() or {}
        try:
            estimate = engine.estimate(
                session_id = data.get("session_id", f"SESS-{uuid.uuid4().hex[:8].upper()}"),
                wallet_id  = data.get("wallet_id", "anonymous"),
                agents     = data.get("agents", []),
                phase      = FlowPhase(data.get("phase", "arena")),
                identity   = IdentityMultiplier(data.get("identity", "free")),
                rounds     = data.get("rounds", 1),
            )
            result = asdict(estimate)
            # Convert enums to strings for JSON serialization
            result["identity"] = estimate.identity.value
            result["phase"] = estimate.phase.value
            for item in result["line_items"]:
                item["agent_tier"] = item["agent_tier"].value if hasattr(item["agent_tier"], "value") else item["agent_tier"]
                item["phase"] = item["phase"].value if hasattr(item["phase"], "value") else item["phase"]
            return jsonify({
                "ok":       True,
                "estimate": result,
                "message":  f"Esta deliberacao custa {estimate.total_credits} creditos = EUR{estimate.total_eur:.4f}",
            })
        except (ValueError, KeyError) as e:
            return jsonify({"ok": False, "error": str(e)}), 400

    @blueprint.route("/arena/consume", methods=["POST"])
    def consume_endpoint():
        """Debito Wallet + Receipt Ledger - executa o honorario."""
        data = request.get_json() or {}
        try:
            # Re-calcula estimate a partir do request (stateless)
            estimate = engine.estimate(
                session_id = data.get("session_id", f"SESS-{uuid.uuid4().hex[:8].upper()}"),
                wallet_id  = data.get("wallet_id", "anonymous"),
                agents     = data.get("agents", []),
                phase      = FlowPhase(data.get("phase", "arena")),
                identity   = IdentityMultiplier(data.get("identity", "free")),
                rounds     = data.get("rounds", 1),
            )
            wallet_balance = data.get("wallet_balance", 9999.0)
            receipt = engine.consume(estimate, wallet_balance=wallet_balance)

            result = asdict(receipt)
            # Convert enums to strings
            result["phase"] = receipt.phase.value
            result["identity"] = receipt.identity.value
            result["status"] = receipt.status.value

            return jsonify({
                "ok":             True,
                "receipt":        result,
                "ledger_payload": receipt.ledger_payload,
                "message":        f"Debito de {receipt.credits_debited} creditos confirmado.",
            })
        except InsufficientCreditsError as e:
            return jsonify({"ok": False, "error": str(e), "code": "INSUFFICIENT_CREDITS"}), 402
        except (ValueError, KeyError) as e:
            return jsonify({"ok": False, "error": str(e)}), 400


# ---------------------------------------------
#  SMOKE TEST
# ---------------------------------------------

if __name__ == "__main__":
    print("=" * 62)
    print("  WINDI Grove Arena - Honorarium Engine v1.0.0")
    print("  Sovereign Flow Smoke Test")
    print("=" * 62)

    engine = HonorariumEngine()

    # -- Cenario 1: Pioneer com 2 agentes Elite (ARENA)
    print("\n[ CENARIO 1 ] Pioneer + Legal + Comply -> Arena\n")
    est1 = engine.estimate(
        session_id = "sess-smoke-001",
        wallet_id  = "PIONEER-001",
        agents     = ["W-LEGAL-001", "W-COMPLY-001"],
        phase      = FlowPhase.ARENA,
        identity   = IdentityMultiplier.PIONEER,
        rounds     = 1,
    )
    for item in est1.line_items:
        print(f"  {item.icon} {item.agent_name:<12} {item.credits_raw:>3} creditos x 0.5 = {item.credits_final:>5} -> EUR{item.eur_value:.4f}")
    print(f"\n  TOTAL: {est1.total_credits} creditos = EUR{est1.total_eur:.4f}")
    print(f"  Hash:  {est1.hash_sha256[:24]}...")

    # -- Cenario 2: Empresa com todos os 8 agentes (ARENA, 3 rodadas)
    print("\n[ CENARIO 2 ] Empresa + 8 Agentes -> 3 Rodadas Arena\n")
    est2 = engine.estimate(
        session_id = "sess-smoke-002",
        wallet_id  = "EMPRESA-XYZ",
        agents     = list(AGENT_REGISTRY.keys()),
        phase      = FlowPhase.ARENA,
        identity   = IdentityMultiplier.EMPRESA,
        rounds     = 3,
    )
    for item in est2.line_items:
        print(f"  {item.icon} {item.agent_name:<12} {item.credits_raw:>3} creditos x 1.2 = {item.credits_final:>5} -> EUR{item.eur_value:.4f}")
    print(f"\n  TOTAL: {est2.total_credits} creditos = EUR{est2.total_eur:.4f}")

    # -- Cenario 3: SEAL pos-debate (DID validado)
    print("\n[ CENARIO 3 ] DID + Legal + Notary -> Seal\n")
    est3 = engine.estimate(
        session_id = "sess-smoke-003",
        wallet_id  = "DID-USER-001",
        agents     = ["W-LEGAL-001", "W-NOTARY-001"],
        phase      = FlowPhase.SEAL,
        identity   = IdentityMultiplier.DID,
    )
    for item in est3.line_items:
        print(f"  {item.icon} {item.agent_name:<12} Seal: {item.credits_raw:>2} creditos x 0.8 = {item.credits_final:>4} -> EUR{item.eur_value:.4f}")
    print(f"\n  TOTAL SEAL: {est3.total_credits} creditos = EUR{est3.total_eur:.4f}")

    # -- Consume (receipt)
    print("\n[ CONSUME ] Gerando receipt + ledger payload...\n")
    receipt = engine.consume(est3, wallet_balance=500.0)
    print(f"  Receipt ID:  {receipt.receipt_id}")
    print(f"  Status:      {receipt.status.value.upper()}")
    print(f"  Debito:      {receipt.credits_debited} creditos = EUR{receipt.eur_charged:.4f}")
    print(f"  Hash:        {receipt.hash_sha256[:24]}...")
    print(f"\n  Ledger payload pronto:")
    print(f"  -> POST :8101/api/receipts")
    print(f"  -> doc_name: {receipt.ledger_payload['doc_name']}")
    print(f"  -> governance: {receipt.ledger_payload['governance_level']}")

    # -- Pricing table
    print("\n[ PRICING TABLE ] /grove/arena/pricing\n")
    pricing = engine.pricing_table()
    for row in pricing["agents"]:
        print(f"  {row['icon']} {row['name']:<12} [{row['tier']:<10}] "
              f"Arena: {row['credits_per_round']:>2}cr (EUR{row['eur_per_round']:.4f})  "
              f"Seal: {row['credits_per_seal']:>2}cr (EUR{row['eur_per_seal']:.4f})")

    print("\n" + "=" * 62)
    print("  Smoke test concluido. Engine pronta para integracao.")
    print("  Proximo: integrar ao grove_blueprint.py via")
    print("  register_flask_routes(grove_bp, engine)")
    print("=" * 62)
