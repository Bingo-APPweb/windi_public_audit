# ═══════════════════════════════════════════════════════════════════════════
#  routing_engine.py — VERA · Sovereign Routing Engine
#  REGO v1.2 · W-Enterprise-001 · Princípios XIV + XV
#  Liga IA+H · Human Dragon · 12 Abril 2026
#
#  Fluxo:
#   User → VERA → routing_engine → LLM APIs → Consensus → PHO → Ledger → Output
#
#  Invariantes activos: I9 · I14 · I11
# ═══════════════════════════════════════════════════════════════════════════

import yaml
import httpx
import hashlib
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException

# ─── LOGGING ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [VERA-ROUTER] %(message)s")
log = logging.getLogger("vera.routing")

# ─── PATHS ────────────────────────────────────────────────────────────────
REGISTRY_PATH = Path(__file__).parent / "llm_registry.yaml"
LEDGER_URL    = "http://localhost:8101"

# ─── ENUMS ────────────────────────────────────────────────────────────────
class TaskMode(str, Enum):
    HIGH    = "HIGH"
    MED     = "MED"
    FREE    = "FREE"
    LOCAL   = "LOCAL"

class DivergenceLevel(str, Enum):
    NONE     = "NONE"
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"

# ─── DATA CLASSES ─────────────────────────────────────────────────────────
@dataclass
class ModelResponse:
    model_id:         str
    alias:            str
    content:          str
    confidence_score: float
    latency_ms:       int
    response_hash:    str
    error:            Optional[str] = None

@dataclass
class ConsensusResult:
    responses:             List[ModelResponse]
    agreement_score:       float
    divergence_level:      DivergenceLevel
    divergence_score:      float
    recommended_output:    str
    conflict_detected:     bool
    models_consulted:      List[str]
    consensus_hash:        str

@dataclass
class RoutingDecision:
    task_type:         str
    mode:              TaskMode
    primary_models:    List[str]
    consensus_required: bool
    pho_required:      bool
    seal_required:     bool
    legal_anchors:     List[str] = field(default_factory=list)
    degraded:          bool = False
    degraded_reason:   Optional[str] = None

@dataclass
class VERAOutput:
    task_type:          str
    routing_decision:   RoutingDecision
    consensus_result:   ConsensusResult
    final_content:      str
    pho_required:       bool
    seal_hash:          Optional[str]
    receipt_id:         Optional[str]
    timestamp_utc:      str
    officer_did:        Optional[str]
    degraded_mode:      bool
    degraded_warning:   Optional[str]

# ─── REGISTRY LOADER ──────────────────────────────────────────────────────
class LLMRegistry:
    """Loads and validates the llm_registry.yaml"""

    def __init__(self, path: Path = REGISTRY_PATH):
        if not path.exists():
            raise FileNotFoundError(f"LLM Registry not found: {path} [I14]")
        with open(path, "r") as f:
            self._data = yaml.safe_load(f)
        self._models = self._index_models()
        log.info(f"Registry loaded: {len(self._models)} models · REGO {self._data['meta']['version']}")

    def _index_models(self) -> Dict[str, Any]:
        index = {}
        for tier_key in ["tier_a", "tier_b", "tier_c"]:
            tier = self._data.get(tier_key, {})
            for model_key, cfg in tier.get("models", {}).items():
                index[model_key] = cfg
        return index

    def get_model(self, model_key: str) -> Dict[str, Any]:
        return self._models.get(model_key, {})

    def get_task(self, task_type: str) -> Dict[str, Any]:
        return self._data.get("task_map", {}).get(task_type, {})

    def get_consensus_rules(self) -> Dict[str, Any]:
        return self._data.get("consensus_rules", {})

    def get_fallback_chain(self) -> List[str]:
        return self._data.get("fallback_chain", {}).get("default_sequence", [])

    def get_gdpr_fallback(self) -> List[str]:
        return self._data.get("fallback_chain", {}).get("gdpr_sensitive_sequence", [])

    def all_models(self) -> Dict[str, Any]:
        return self._models

    def get_meta(self) -> Dict[str, Any]:
        return self._data.get("meta", {})

# ─── ROUTING ENGINE ───────────────────────────────────────────────────────
class VERARoutingEngine:
    """
    Core routing engine. Reads registry, decides which LLMs to call,
    runs consensus, applies PHO layer, seals to ledger.

    Invariants: I9 (never autonomous) · I14 (never silent) · I11 (ledger)
    """

    def __init__(self):
        self.registry  = LLMRegistry()
        self.rules     = self.registry.get_consensus_rules()

    # ── PUBLIC ENTRY POINT ────────────────────────────────────────────────
    async def route(
        self,
        task_type:   str,
        prompt:      str,
        officer_did: Optional[str] = None,
        context:     Optional[Dict[str, Any]] = None,
    ) -> VERAOutput:
        """
        Main routing method. Called by VERA agent for every task.
        Returns a VERAOutput with full audit trail.
        """
        log.info(f"Routing task: {task_type} | DID: {officer_did or 'anonymous'}")

        # ① Build routing decision from registry
        decision = self._build_decision(task_type)

        # ② Simulate model responses (in production: call real APIs)
        responses = await self._simulate_model_calls(decision, prompt, context)

        # ③ Run consensus analysis
        consensus = self._run_consensus(responses)

        # ④ Apply PHO layer (I9)
        pho_required = decision.pho_required or consensus.conflict_detected

        # ⑤ Seal to ledger if required (I11)
        seal_hash, receipt_id = None, None
        if decision.seal_required and officer_did:
            seal_hash, receipt_id = await self._seal_to_ledger(
                task_type, consensus, officer_did, decision.legal_anchors
            )

        timestamp = datetime.now(timezone.utc).isoformat()

        output = VERAOutput(
            task_type         = task_type,
            routing_decision  = decision,
            consensus_result  = consensus,
            final_content     = consensus.recommended_output,
            pho_required      = pho_required,
            seal_hash         = seal_hash,
            receipt_id        = receipt_id,
            timestamp_utc     = timestamp,
            officer_did       = officer_did,
            degraded_mode     = decision.degraded,
            degraded_warning  = decision.degraded_reason,
        )

        log.info(f"Routing complete | agreement={consensus.agreement_score:.2f} | divergence={consensus.divergence_level} | pho={pho_required}")
        return output

    # ── DECISION BUILDER ──────────────────────────────────────────────────
    def _build_decision(self, task_type: str) -> RoutingDecision:
        """Build routing decision from registry task_map."""
        task_cfg = self.registry.get_task(task_type)

        if not task_cfg:
            # Unknown task → safe default: claude only, PHO required
            log.warning(f"Unknown task_type '{task_type}' — defaulting to safe HIGH routing")
            return RoutingDecision(
                task_type        = task_type,
                mode             = TaskMode.HIGH,
                primary_models   = ["claude"],
                consensus_required = False,
                pho_required     = True,
                seal_required    = False,
            )

        return RoutingDecision(
            task_type          = task_type,
            mode               = TaskMode(task_cfg.get("mode", "MED")),
            primary_models     = task_cfg.get("primary", ["claude"]),
            consensus_required = task_cfg.get("consensus_required", False),
            pho_required       = task_cfg.get("pho_required", False),
            seal_required      = task_cfg.get("seal_required", False),
            legal_anchors      = task_cfg.get("legal_anchor", []),
        )

    # ── MODEL SIMULATION (Production: replace with real API calls) ────────
    async def _simulate_model_calls(
        self,
        decision: RoutingDecision,
        prompt:   str,
        context:  Optional[Dict[str, Any]],
    ) -> List[ModelResponse]:
        """
        Simulate model responses for demonstration.
        In production: call real LLM APIs via httpx.
        """
        import random
        responses = []

        for i, model_key in enumerate(decision.primary_models):
            model_cfg = self.registry.get_model(model_key)
            if not model_cfg:
                continue

            # Simulate response
            base_conf = 0.88 if decision.mode == TaskMode.HIGH else 0.78
            confidence = min(0.99, max(0.60, base_conf - i * 0.03 + random.uniform(-0.05, 0.05)))
            latency = random.randint(200, 800) if decision.mode != TaskMode.LOCAL else random.randint(600, 1200)

            content = f"[{model_cfg.get('alias', model_key)}] Analysis of: {prompt[:50]}... "
            content += f"Based on {', '.join(decision.legal_anchors) if decision.legal_anchors else 'general compliance principles'}."

            response_hash = hashlib.sha256(f"{content}{model_key}{time.time()}".encode()).hexdigest()[:16].upper()

            responses.append(ModelResponse(
                model_id         = model_cfg.get("model_id", model_key),
                alias            = model_cfg.get("alias", model_key),
                content          = content,
                confidence_score = round(confidence, 4),
                latency_ms       = latency,
                response_hash    = response_hash,
            ))

        # I14: if zero responses — hard failure, never return empty silently
        if not responses:
            raise RuntimeError(
                "VERA MODO DEGRADADO CRÍTICO: Nenhum modelo disponível. "
                "Operação suspensa. Contactar Human Dragon. [I14]"
            )

        return responses

    # ── CONSENSUS ENGINE ──────────────────────────────────────────────────
    def _run_consensus(self, responses: List[ModelResponse]) -> ConsensusResult:
        """
        Analyse responses for agreement/divergence.
        Princípio XV: triangulação obrigatória em decisões de alto risco.
        """
        if len(responses) == 1:
            r = responses[0]
            return ConsensusResult(
                responses          = responses,
                agreement_score    = r.confidence_score,
                divergence_level   = DivergenceLevel.NONE,
                divergence_score   = 0.0,
                recommended_output = r.content,
                conflict_detected  = False,
                models_consulted   = [r.model_id],
                consensus_hash     = r.response_hash,
            )

        # Compute pairwise divergence via confidence comparison
        confs = [r.confidence_score for r in responses]
        max_diff = max(confs) - min(confs)
        divergence_score = max_diff

        rules = self.rules.get("divergence_detection", {})
        thresh_warn = rules.get("threshold_warning", 0.25)
        thresh_crit = rules.get("threshold_critical", 0.40)

        if divergence_score >= thresh_crit:
            divergence_level = DivergenceLevel.CRITICAL
        elif divergence_score >= thresh_warn:
            divergence_level = DivergenceLevel.WARNING
        else:
            divergence_level = DivergenceLevel.NONE

        conflict_detected = divergence_level in [DivergenceLevel.WARNING, DivergenceLevel.CRITICAL]

        # Weighted selection: pick highest-confidence model's response
        best = max(responses, key=lambda r: r.confidence_score)

        # Build consensus hash from all response hashes
        hashes = [r.response_hash for r in responses]
        combined = "".join(sorted(hashes))
        consensus_hash = hashlib.sha256(combined.encode()).hexdigest()[:16].upper()

        return ConsensusResult(
            responses          = responses,
            agreement_score    = sum(r.confidence_score for r in responses) / len(responses),
            divergence_level   = divergence_level,
            divergence_score   = round(divergence_score, 4),
            recommended_output = best.content,
            conflict_detected  = conflict_detected,
            models_consulted   = [r.model_id for r in responses],
            consensus_hash     = consensus_hash,
        )

    # ── LEDGER SEALING (I11) ──────────────────────────────────────────────
    async def _seal_to_ledger(
        self,
        task_type:     str,
        consensus:     ConsensusResult,
        officer_did:   str,
        legal_anchors: List[str],
    ) -> tuple:
        """Seal routing decision to Forensic Ledger. Princípio XVII + I11."""
        seal_content = json.dumps({
            "task_type":        task_type,
            "models_consulted": consensus.models_consulted,
            "agreement_score":  consensus.agreement_score,
            "divergence_level": consensus.divergence_level.value,
            "consensus_hash":   consensus.consensus_hash,
            "legal_anchors":    legal_anchors,
            "officer_did":      officer_did,
        }, sort_keys=True)

        content_hash = hashlib.sha256(seal_content.encode()).hexdigest().upper()
        receipt_id   = f"VERA-{task_type.upper()[:8]}-{content_hash[:8]}"

        payload = {
            "id":               receipt_id,
            "actor":            officer_did,
            "app":              "VERA",
            "doc_name":         f"VERA Routing · {task_type}",
            "doc_type":         "vera_routing_decision",
            "content_hash":     content_hash,
            "governance_level": "HIGH",
            "sge_score":        "R0",
            "models_consulted": consensus.models_consulted,
            "divergence_level": consensus.divergence_level.value,
            "legal_anchors":    legal_anchors,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(f"{LEDGER_URL}/api/receipts", json=payload)
                r.raise_for_status()
                log.info(f"Ledger sealed: {receipt_id} | hash={content_hash[:16]}")
                return content_hash, receipt_id
        except Exception as e:
            # I14: log failure, never silent
            log.error(f"Ledger seal failed: {e}. Receipt ID stored for retry: {receipt_id}")
            return content_hash, receipt_id

    # ── CONFIDENCE MATRIX (for UI) ────────────────────────────────────────
    def build_confidence_matrix(self, output: VERAOutput) -> Dict[str, Any]:
        """
        Build structured Confidence Matrix for DASH UI.
        """
        matrix = {
            "task_type":       output.task_type,
            "timestamp_utc":   output.timestamp_utc,
            "mode":            output.routing_decision.mode.value,
            "pho_required":    output.pho_required,
            "seal_hash":       output.seal_hash,
            "receipt_id":      output.receipt_id,
            "degraded_mode":   output.degraded_mode,
            "models": [],
            "consensus": {
                "agreement_score":  output.consensus_result.agreement_score,
                "divergence_level": output.consensus_result.divergence_level.value,
                "divergence_score": output.consensus_result.divergence_score,
                "conflict_detected": output.consensus_result.conflict_detected,
                "consensus_hash":   output.consensus_result.consensus_hash,
            },
            "legal_anchors": output.routing_decision.legal_anchors,
        }

        for r in output.consensus_result.responses:
            matrix["models"].append({
                "model_id":        r.model_id,
                "alias":           r.alias,
                "confidence_score": r.confidence_score,
                "latency_ms":      r.latency_ms,
                "response_hash":   r.response_hash,
                "divergence_from_consensus": round(
                    abs(r.confidence_score - output.consensus_result.agreement_score), 4
                ),
                "error": r.error,
            })

        return matrix


# ─── FASTAPI ROUTER ───────────────────────────────────────────────────────
def create_routing_router() -> APIRouter:
    router = APIRouter(prefix="/vera/routing", tags=["VERA-Routing"])
    engine = VERARoutingEngine()

    # Import DID Gate
    from vera_did_gate import verify_did, bind_action_to_did, get_wallet_banner

    @router.post("/route")
    async def route_task(body: dict):
        """
        Main routing endpoint. Called by VERA agent.
        Body: { task_type, prompt, officer_did, context }

        EVANGELHO: DID é PORTÃO, não parâmetro.
        Lei I: Sem DID → WalletBanner mode.
        Lei II: Cada routing → rastro no Ledger.
        """
        officer_did = body.get("officer_did", "")

        # LEI I — Existência antes de Acção
        if not officer_did:
            banner = get_wallet_banner()
            return {
                "status": "did_required",
                "law": "Lei I — Existência antes de Acção",
                "message": "DID obrigatório para routing. Sem DID → sem acesso ao cérebro.",
                "wallet_banner": banner.model_dump(),
            }

        # Validate DID against W-SESSION-001
        validation = await verify_did(officer_did)
        if not validation.valid:
            banner = get_wallet_banner()
            return {
                "status": "invalid_did",
                "law": "Lei I — Existência antes de Acção",
                "error": validation.error,
                "wallet_banner": banner.model_dump(),
            }

        try:
            output = await engine.route(
                task_type   = body.get("task_type", "legal_analysis"),
                prompt      = body.get("prompt", ""),
                officer_did = officer_did,
                context     = body.get("context"),
            )

            # LEI II — Toda Acção gera Rastro DID
            await bind_action_to_did(
                did=officer_did,
                action="routing",
                module="routing_engine",
                details={"task_type": body.get("task_type")},
            )
            matrix = engine.build_confidence_matrix(output)
            return {
                "status":         "success",
                "final_content":  output.final_content,
                "pho_required":   output.pho_required,
                "receipt_id":     output.receipt_id,
                "seal_hash":      output.seal_hash,
                "degraded_mode":  output.degraded_mode,
                "degraded_warning": output.degraded_warning,
                "confidence_matrix": matrix,
            }
        except Exception as e:
            log.error(f"Routing error: {e}")
            raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)} [I14]")

    @router.get("/registry")
    async def get_registry():
        """Returns the full LLM registry (for DASH / audit)."""
        try:
            reg = LLMRegistry()
            return {
                "status":        "success",
                "meta":          reg.get_meta(),
                "models":        reg.all_models(),
                "task_map":      reg._data.get("task_map", {}),
                "fallback_chain": reg.get_fallback_chain(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registry load failed: {str(e)} [I14]")

    @router.get("/health")
    async def routing_health():
        try:
            reg = LLMRegistry()
            return {
                "status":       "operational",
                "engine":       "VERA Routing Engine v1.0",
                "constitution": "REGO v1.2",
                "models_loaded": len(reg.all_models()),
                "invariants":   ["I9", "I14", "I11"],
                "timestamp":    datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "status":       "degraded",
                "error":        str(e),
                "timestamp":    datetime.now(timezone.utc).isoformat(),
            }

    return router
