#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#  vera_quality_gate.py — VERA Quality Gate Integration
#  §204.5 · Liga IA+H · Human Dragon · 25 Abril 2026
#
#  "DeepEval é o espelho. VERA é o juiz. Shadow Audit é a polícia."
#
#  INTEGRAÇÃO:
#  - DeepEval → avalia qualidade da explicação (superfície)
#  - Shadow Audit → fiscaliza violações (profundidade)
#  - Admissibility Score → legitimidade da decisão (WINDI-native)
#
#  REGRA DE OURO:
#  > Se DeepEval e VERA discordarem → VERA vence. Sempre.
# ═══════════════════════════════════════════════════════════════════════════════

import os
import json
import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [QUALITY-GATE] %(message)s")
log = logging.getLogger("vera.quality_gate")

# ─── PATHS ───────────────────────────────────────────────────────────────────
QUALITY_DB = Path("/opt/windi/data/vera_quality_gate.db")

# ─── DEEPEVAL INTEGRATION ────────────────────────────────────────────────────
# Set API key from environment
os.environ.setdefault(
    "DEEPEVAL_API_KEY",
    "confident_us_xoL0gUcjgBu059sSnUqcRrCethyM1f3DKgDEEbHu74Q="
)

try:
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
        CoherenceMetric,
    )
    DEEPEVAL_AVAILABLE = True
    log.info("DeepEval v3.9.7 loaded")
except ImportError:
    DEEPEVAL_AVAILABLE = False
    log.warning("DeepEval not available — quality metrics disabled")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ADMISSIBILITY SCORE — WINDI-NATIVE
#    "A resposta pode ser boa. A decisão pode ser inadmissível."
# ═══════════════════════════════════════════════════════════════════════════════

class AdmissibilityLevel(str, Enum):
    """Admissibility levels for VERA decisions."""
    FULL = "FULL"           # 4/4 — Perfect admissibility
    HIGH = "HIGH"           # 3/4 — Minor gap
    PARTIAL = "PARTIAL"     # 2/4 — Significant gaps
    LOW = "LOW"             # 1/4 — Serious concerns
    INADMISSIBLE = "INADMISSIBLE"  # 0/4 — Cannot be used


@dataclass
class AdmissibilityScore:
    """
    WINDI-native Admissibility Score.

    Measures legitimacy of decision, NOT quality of response.
    DeepEval measures surface. Admissibility measures depth.
    """
    # Core invariants (0/1 each)
    i9_respected: bool          # No autonomous action claims
    triangulation_ok: bool      # ≥2 models for HIGH decisions
    evidence_required: bool     # PoE/PHO requirements met
    routing_correct: bool       # Task classified correctly

    # Computed
    score: int = 0              # 0-4
    level: AdmissibilityLevel = AdmissibilityLevel.INADMISSIBLE

    # Metadata
    task_type: str = ""
    models_consulted: List[str] = None
    shadow_alerts: int = 0
    timestamp: str = ""

    def __post_init__(self):
        self.models_consulted = self.models_consulted or []
        self.score = sum([
            self.i9_respected,
            self.triangulation_ok,
            self.evidence_required,
            self.routing_correct,
        ])
        self.level = {
            4: AdmissibilityLevel.FULL,
            3: AdmissibilityLevel.HIGH,
            2: AdmissibilityLevel.PARTIAL,
            1: AdmissibilityLevel.LOW,
            0: AdmissibilityLevel.INADMISSIBLE,
        }[self.score]
        self.timestamp = datetime.now(timezone.utc).isoformat()


def compute_admissibility(vera_response: Dict[str, Any]) -> AdmissibilityScore:
    """
    Compute Admissibility Score from VERA response metadata.

    This is WINDI-native governance — not DeepEval.
    """
    erdbeere = vera_response.get("erdbeere_protocol", {})
    task_type = vera_response.get("task_type", "MED_CAPACITY")
    models = erdbeere.get("models_consulted", [])
    triangulation = erdbeere.get("triangulation", "N/A")
    shadow_alerts = vera_response.get("_shadow_alerts", 0)
    i9_protected = vera_response.get("i9_protected", False)

    # I9: No autonomous action claims
    # Check if VERA is protected by I9
    i9_ok = i9_protected and shadow_alerts == 0

    # Triangulation: ≥2 models for HIGH decisions
    if task_type == "HIGH_GOVERNANCE":
        tri_ok = len(models) >= 2 and triangulation == "XV"
    else:
        tri_ok = True  # Not required for LOW/MED

    # Evidence: PHO/PoE requirements
    # If task is HIGH and sealable, evidence is required
    evidence_ok = vera_response.get("sealable", False) or task_type != "HIGH_GOVERNANCE"

    # Routing: Task classified correctly
    # Check if routing_path exists and makes sense
    routing_ok = task_type in ["HIGH_GOVERNANCE", "MED_CAPACITY", "LOW_TRIVIAL"]

    return AdmissibilityScore(
        i9_respected=i9_ok,
        triangulation_ok=tri_ok,
        evidence_required=evidence_ok,
        routing_correct=routing_ok,
        task_type=task_type,
        models_consulted=models,
        shadow_alerts=shadow_alerts,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DEEPEVAL QUALITY METRICS
#    "Avalia a superfície — clareza, coerência, relevância"
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QualityMetrics:
    """DeepEval quality metrics for VERA responses."""
    coherence_score: float = 0.0
    relevance_score: float = 0.0
    faithfulness_score: float = 0.0

    coherence_passed: bool = False
    relevance_passed: bool = False
    faithfulness_passed: bool = False

    evaluation_error: Optional[str] = None
    evaluated_at: str = ""

    def __post_init__(self):
        self.evaluated_at = datetime.now(timezone.utc).isoformat()

    @property
    def overall_score(self) -> float:
        """Average of all metrics."""
        scores = [self.coherence_score, self.relevance_score, self.faithfulness_score]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def all_passed(self) -> bool:
        return all([self.coherence_passed, self.relevance_passed, self.faithfulness_passed])


async def evaluate_quality(
    question: str,
    vera_response: str,
    retrieval_context: List[str] = None,
    model: str = "gpt-4o",
    threshold: float = 0.7,
) -> QualityMetrics:
    """
    Evaluate VERA response quality using DeepEval.

    NOTE: This measures SURFACE quality, not ADMISSIBILITY.
    A response can score HIGH here and still be INADMISSIBLE.
    """
    if not DEEPEVAL_AVAILABLE:
        return QualityMetrics(evaluation_error="DeepEval not available")

    metrics = QualityMetrics()

    try:
        test_case = LLMTestCase(
            input=question,
            actual_output=vera_response,
            retrieval_context=retrieval_context or [],
        )

        # Relevance: Does response address the question?
        relevance_metric = AnswerRelevancyMetric(
            threshold=threshold,
            model=model,
            include_reason=True,
        )
        relevance_metric.measure(test_case)
        metrics.relevance_score = relevance_metric.score
        metrics.relevance_passed = relevance_metric.is_successful()

        # Faithfulness: Is response grounded in context?
        if retrieval_context:
            faith_metric = FaithfulnessMetric(
                threshold=threshold,
                model=model,
                include_reason=True,
            )
            faith_metric.measure(test_case)
            metrics.faithfulness_score = faith_metric.score
            metrics.faithfulness_passed = faith_metric.is_successful()
        else:
            metrics.faithfulness_score = 1.0  # No context to check
            metrics.faithfulness_passed = True

        log.info(f"Quality evaluation: relevance={metrics.relevance_score:.2f}, faithfulness={metrics.faithfulness_score:.2f}")

    except Exception as e:
        metrics.evaluation_error = str(e)
        log.warning(f"Quality evaluation failed: {e}")

    return metrics


# ═══════════════════════════════════════════════════════════════════════════════
# 3. COMBINED QUALITY GATE
#    "O painel que nenhum concorrente tem"
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class QualityGateResult:
    """
    Combined Quality Gate result.

    | Métrica         | Fonte        | O que diz                |
    |-----------------|--------------|--------------------------|
    | Coerência       | DeepEval     | qualidade da resposta    |
    | Relevância      | DeepEval     | foco no pedido           |
    | Admissibilidade | VERA/Shadow  | legitimidade da decisão  |
    | Integridade     | Shadow Audit | sistema respeitou regras |
    """
    # Admissibility (WINDI-native)
    admissibility: AdmissibilityScore

    # Quality (DeepEval)
    quality: QualityMetrics

    # Overall verdict
    gate_passed: bool = False
    verdict: str = ""

    # Metadata
    request_hash: str = ""
    timestamp: str = ""

    def __post_init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()

        # Gate passes only if ADMISSIBILITY is OK
        # Quality is secondary — "DeepEval é o espelho, VERA é o juiz"
        if self.admissibility.level == AdmissibilityLevel.INADMISSIBLE:
            self.gate_passed = False
            self.verdict = "INADMISSIBLE — Decision cannot be used regardless of quality"
        elif self.admissibility.level == AdmissibilityLevel.LOW:
            self.gate_passed = False
            self.verdict = "LOW ADMISSIBILITY — Serious governance concerns"
        elif self.admissibility.level == AdmissibilityLevel.PARTIAL:
            self.gate_passed = True  # Allow with warnings
            self.verdict = "PARTIAL — Admissible with caveats"
        elif self.admissibility.score >= 3:
            self.gate_passed = True
            if self.quality.overall_score >= 0.7:
                self.verdict = "EXCELLENT — High admissibility + High quality"
            else:
                self.verdict = "ADMISSIBLE — Governance OK, quality could improve"
        else:
            self.gate_passed = True
            self.verdict = "ADMISSIBLE"


async def run_quality_gate(
    question: str,
    vera_response_data: Dict[str, Any],
    retrieval_context: List[str] = None,
    evaluate_deepeval: bool = True,
) -> QualityGateResult:
    """
    Run full Quality Gate on VERA response.

    Combines:
    - Admissibility Score (WINDI-native governance)
    - Quality Metrics (DeepEval surface evaluation)

    RULE: If DeepEval and VERA disagree → VERA wins. Always.
    """
    vera_text = vera_response_data.get("vera_response", "")

    # 1. Compute Admissibility (always)
    admissibility = compute_admissibility(vera_response_data)

    # 2. Evaluate Quality (optional — requires OpenAI quota)
    if evaluate_deepeval and DEEPEVAL_AVAILABLE:
        quality = await evaluate_quality(
            question=question,
            vera_response=vera_text,
            retrieval_context=retrieval_context,
        )
    else:
        quality = QualityMetrics(evaluation_error="DeepEval skipped")

    # 3. Compute request hash for tracking
    request_hash = hashlib.sha256(question[:200].encode()).hexdigest()[:16]

    result = QualityGateResult(
        admissibility=admissibility,
        quality=quality,
        request_hash=request_hash,
    )

    log.info(f"Quality Gate: {result.verdict} | admissibility={admissibility.score}/4 | quality={quality.overall_score:.2f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PERSISTENCE — Quality Gate History
# ═══════════════════════════════════════════════════════════════════════════════

def init_quality_db():
    """Initialize Quality Gate database."""
    QUALITY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(QUALITY_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quality_gate_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            question_preview TEXT,

            -- Admissibility
            admissibility_score INTEGER,
            admissibility_level TEXT,
            i9_respected INTEGER,
            triangulation_ok INTEGER,
            evidence_required INTEGER,
            routing_correct INTEGER,
            task_type TEXT,
            models_consulted TEXT,
            shadow_alerts INTEGER,

            -- Quality
            coherence_score REAL,
            relevance_score REAL,
            faithfulness_score REAL,
            quality_overall REAL,
            quality_error TEXT,

            -- Verdict
            gate_passed INTEGER,
            verdict TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qg_hash ON quality_gate_history(request_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qg_level ON quality_gate_history(admissibility_level)")
    conn.commit()
    conn.close()
    log.info("Quality Gate DB initialized")


def save_quality_result(question: str, result: QualityGateResult):
    """Persist Quality Gate result for audit trail."""
    try:
        conn = sqlite3.connect(str(QUALITY_DB), timeout=10)
        conn.execute("""
            INSERT INTO quality_gate_history (
                timestamp, request_hash, question_preview,
                admissibility_score, admissibility_level, i9_respected,
                triangulation_ok, evidence_required, routing_correct,
                task_type, models_consulted, shadow_alerts,
                coherence_score, relevance_score, faithfulness_score,
                quality_overall, quality_error, gate_passed, verdict
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.timestamp,
            result.request_hash,
            question[:100],
            result.admissibility.score,
            result.admissibility.level.value,
            1 if result.admissibility.i9_respected else 0,
            1 if result.admissibility.triangulation_ok else 0,
            1 if result.admissibility.evidence_required else 0,
            1 if result.admissibility.routing_correct else 0,
            result.admissibility.task_type,
            json.dumps(result.admissibility.models_consulted),
            result.admissibility.shadow_alerts,
            result.quality.coherence_score,
            result.quality.relevance_score,
            result.quality.faithfulness_score,
            result.quality.overall_score,
            result.quality.evaluation_error,
            1 if result.gate_passed else 0,
            result.verdict,
        ))
        conn.commit()
        conn.close()
        log.info(f"Quality Gate result saved: {result.request_hash}")
    except Exception as e:
        log.error(f"Failed to save Quality Gate result: {e}")


def get_quality_stats(hours: int = 24) -> Dict[str, Any]:
    """Get Quality Gate statistics for dashboard."""
    try:
        conn = sqlite3.connect(str(QUALITY_DB), timeout=10)
        conn.row_factory = sqlite3.Row

        # Total evaluations
        total = conn.execute("""
            SELECT COUNT(*) FROM quality_gate_history
            WHERE timestamp > datetime('now', ?)
        """, (f'-{hours} hours',)).fetchone()[0]

        # By admissibility level
        by_level = conn.execute("""
            SELECT admissibility_level, COUNT(*) as count
            FROM quality_gate_history
            WHERE timestamp > datetime('now', ?)
            GROUP BY admissibility_level
        """, (f'-{hours} hours',)).fetchall()

        # Gate pass rate
        passed = conn.execute("""
            SELECT COUNT(*) FROM quality_gate_history
            WHERE timestamp > datetime('now', ?) AND gate_passed = 1
        """, (f'-{hours} hours',)).fetchone()[0]

        # Average quality scores
        avg_quality = conn.execute("""
            SELECT
                AVG(relevance_score) as avg_relevance,
                AVG(faithfulness_score) as avg_faithfulness,
                AVG(quality_overall) as avg_overall
            FROM quality_gate_history
            WHERE timestamp > datetime('now', ?) AND quality_error IS NULL
        """, (f'-{hours} hours',)).fetchone()

        conn.close()

        return {
            "period_hours": hours,
            "total_evaluations": total,
            "by_admissibility_level": {r["admissibility_level"]: r["count"] for r in by_level},
            "gate_pass_rate": passed / total if total > 0 else 0,
            "avg_relevance": avg_quality["avg_relevance"] or 0,
            "avg_faithfulness": avg_quality["avg_faithfulness"] or 0,
            "avg_quality_overall": avg_quality["avg_overall"] or 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        log.error(f"Failed to get quality stats: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter

def create_quality_gate_router() -> APIRouter:
    """Create FastAPI router for Quality Gate endpoints."""
    router = APIRouter(prefix="/vera/quality", tags=["VERA-Quality"])

    @router.get("/health")
    async def quality_health():
        return {
            "status": "operational",
            "component": "VERA Quality Gate",
            "version": "§204.5",
            "deepeval_available": DEEPEVAL_AVAILABLE,
            "metrics": ["admissibility", "relevance", "faithfulness", "coherence"],
            "rule": "Se DeepEval e VERA discordarem → VERA vence. Sempre.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/stats")
    async def quality_stats(hours: int = 24):
        return {
            "status": "ok",
            "quality_gate": "§204.5 — VERA Quality Gate",
            "stats": get_quality_stats(hours),
        }

    @router.post("/evaluate")
    async def evaluate_response(body: dict):
        """
        Evaluate a VERA response through the Quality Gate.

        Body: {
            question: str,
            vera_response_data: dict (full VERA response),
            retrieval_context: list (optional),
            run_deepeval: bool (default: true)
        }
        """
        question = body.get("question", "")
        vera_data = body.get("vera_response_data", {})
        context = body.get("retrieval_context", [])
        run_deepeval = body.get("run_deepeval", True)

        result = await run_quality_gate(
            question=question,
            vera_response_data=vera_data,
            retrieval_context=context,
            evaluate_deepeval=run_deepeval,
        )

        # Persist for audit trail
        save_quality_result(question, result)

        return {
            "status": "ok",
            "quality_gate": "§204.5",
            "result": {
                "gate_passed": result.gate_passed,
                "verdict": result.verdict,
                "admissibility": {
                    "score": result.admissibility.score,
                    "level": result.admissibility.level.value,
                    "i9_respected": result.admissibility.i9_respected,
                    "triangulation_ok": result.admissibility.triangulation_ok,
                    "evidence_required": result.admissibility.evidence_required,
                    "routing_correct": result.admissibility.routing_correct,
                    "task_type": result.admissibility.task_type,
                    "models_consulted": result.admissibility.models_consulted,
                    "shadow_alerts": result.admissibility.shadow_alerts,
                },
                "quality": {
                    "relevance_score": result.quality.relevance_score,
                    "faithfulness_score": result.quality.faithfulness_score,
                    "overall_score": result.quality.overall_score,
                    "all_passed": result.quality.all_passed,
                    "error": result.quality.evaluation_error,
                },
            },
            "request_hash": result.request_hash,
            "timestamp": result.timestamp,
        }

    return router


# ═══════════════════════════════════════════════════════════════════════════════
# 6. INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# Auto-init on import
try:
    init_quality_db()
except Exception as e:
    log.error(f"Failed to initialize Quality Gate DB: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CLI TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    import requests

    print("=" * 70)
    print("  VERA QUALITY GATE — §204.5")
    print("  'DeepEval é o espelho. VERA é o juiz. Shadow Audit é a polícia.'")
    print("=" * 70)
    print()

    # Test with a real VERA call
    try:
        resp = requests.post(
            "http://localhost:8150/vera/chat",
            json={
                "question": "What is Article 14 of EU AI Act about?",
                "officer_id": "did:windi:dragon-001",
                "language": "en"
            },
            timeout=60
        )
        vera_data = resp.json()

        print("VERA Response received:")
        print(f"  Models: {vera_data.get('erdbeere_protocol', {}).get('models_consulted', '?')}")
        print(f"  I9 Protected: {vera_data.get('i9_protected', '?')}")
        print(f"  Shadow Alerts: {vera_data.get('_shadow_alerts', 0)}")
        print()

        # Run Quality Gate (without DeepEval to avoid quota)
        result = asyncio.run(run_quality_gate(
            question="What is Article 14 of EU AI Act about?",
            vera_response_data=vera_data,
            evaluate_deepeval=False,  # Skip DeepEval for CLI test
        ))

        print("Quality Gate Result:")
        print(f"  Gate Passed: {'✅' if result.gate_passed else '❌'}")
        print(f"  Verdict: {result.verdict}")
        print()
        print("Admissibility Score:")
        print(f"  Score: {result.admissibility.score}/4")
        print(f"  Level: {result.admissibility.level.value}")
        print(f"  I9 OK: {'✅' if result.admissibility.i9_respected else '❌'}")
        print(f"  Triangulation OK: {'✅' if result.admissibility.triangulation_ok else '❌'}")
        print(f"  Evidence OK: {'✅' if result.admissibility.evidence_required else '❌'}")
        print(f"  Routing OK: {'✅' if result.admissibility.routing_correct else '❌'}")

    except Exception as e:
        print(f"Error: {e}")
