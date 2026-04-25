#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#  vera_langfuse.py — VERA Observability Layer
#  §204.6 · Liga IA+H · Human Dragon · 25 Abril 2026
#
#  "Langfuse é o satélite. Observa tudo em tempo real."
#
#  STACK COMPLETO:
#  - DeepEval    → Avalia qualidade (espelho)
#  - Shadow Audit → Detecta violações (polícia)
#  - Quality Gate → Mede admissibilidade (juiz)
#  - Langfuse    → Observa tudo (satélite)
#
#  FUNCIONALIDADES:
#  - Tracing de cada chamada LLM
#  - Cost tracking por request
#  - Latency monitoring
#  - Session tracking por DID
#  - Span hierarchy (VERA → Gateway → Model)
# ═══════════════════════════════════════════════════════════════════════════════

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from functools import wraps
from contextlib import contextmanager

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [LANGFUSE] %(message)s")
log = logging.getLogger("vera.langfuse")

# ─── LANGFUSE CONFIGURATION ──────────────────────────────────────────────────
# Get keys from environment or .env.local
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Initialize Langfuse client
LANGFUSE_ENABLED = False
langfuse_client = None

try:
    if LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY:
        from langfuse import Langfuse
        langfuse_client = Langfuse(
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY,
            host=LANGFUSE_HOST,
        )
        LANGFUSE_ENABLED = True
        log.info(f"Langfuse v4.5.1 initialized — host={LANGFUSE_HOST}")
    else:
        log.warning("Langfuse keys not configured — observability disabled")
        log.info("Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in environment")
except ImportError:
    log.warning("Langfuse not installed — run: pip install langfuse")
except Exception as e:
    log.error(f"Langfuse initialization failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TRACE MANAGEMENT
#    "Cada request VERA = uma trace completa"
# ═══════════════════════════════════════════════════════════════════════════════

class VERATrace:
    """
    Manages a Langfuse trace for a VERA request.

    Trace hierarchy:
    └── VERA Request (trace)
        ├── Classification (span)
        ├── Prompt Building (span)
        ├── LLM Call: Guardian (generation)
        ├── LLM Call: Architect (generation)
        ├── Consensus (span)
        ├── Shadow Audit (span)
        └── Quality Gate (span)
    """

    def __init__(
        self,
        name: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.trace = None
        self.spans = {}
        self.generations = []
        self.start_time = datetime.now(timezone.utc)

        if LANGFUSE_ENABLED and langfuse_client:
            try:
                self.trace = langfuse_client.trace(
                    name=name,
                    session_id=session_id,
                    user_id=user_id,
                    metadata={
                        **self.metadata,
                        "component": "VERA",
                        "version": "§204.6",
                        "constitution": "REGO v1.2",
                    },
                )
                log.info(f"Trace started: {name} | session={session_id}")
            except Exception as e:
                log.warning(f"Failed to start trace: {e}")

    def span(
        self,
        name: str,
        input_data: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Create a span within the trace."""
        if not self.trace:
            return DummySpan()

        try:
            span = self.trace.span(
                name=name,
                input=input_data,
                metadata=metadata,
            )
            self.spans[name] = span
            return span
        except Exception as e:
            log.warning(f"Failed to create span {name}: {e}")
            return DummySpan()

    def generation(
        self,
        name: str,
        model: str,
        model_parameters: Optional[Dict[str, Any]] = None,
        input_messages: Optional[List[Dict]] = None,
        output: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record an LLM generation within the trace."""
        if not self.trace:
            return None

        try:
            gen = self.trace.generation(
                name=name,
                model=model,
                model_parameters=model_parameters,
                input=input_messages,
                output=output,
                usage=usage,
                metadata={
                    **(metadata or {}),
                    "principle_xv": True,  # Multi-model triangulation
                },
            )
            self.generations.append(gen)
            log.info(f"Generation recorded: {name} | model={model}")
            return gen
        except Exception as e:
            log.warning(f"Failed to record generation {name}: {e}")
            return None

    def end(
        self,
        output: Optional[Any] = None,
        level: str = "DEFAULT",
        status_message: Optional[str] = None,
    ):
        """End the trace with final output."""
        if not self.trace:
            return

        try:
            end_time = datetime.now(timezone.utc)
            latency_ms = int((end_time - self.start_time).total_seconds() * 1000)

            self.trace.update(
                output=output,
                level=level,
                status_message=status_message,
                metadata={
                    **self.metadata,
                    "latency_ms": latency_ms,
                    "generations_count": len(self.generations),
                },
            )
            log.info(f"Trace ended: {self.name} | latency={latency_ms}ms | level={level}")
        except Exception as e:
            log.warning(f"Failed to end trace: {e}")

    def score(
        self,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ):
        """Add a score to the trace."""
        if not self.trace:
            return

        try:
            self.trace.score(
                name=name,
                value=value,
                comment=comment,
            )
            log.info(f"Score added: {name}={value}")
        except Exception as e:
            log.warning(f"Failed to add score: {e}")


class DummySpan:
    """Dummy span when Langfuse is disabled."""
    def end(self, **kwargs): pass
    def update(self, **kwargs): pass


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DECORATORS FOR AUTOMATIC TRACING
#    "Instrumentação automática"
# ═══════════════════════════════════════════════════════════════════════════════

def trace_vera_request(func):
    """
    Decorator to automatically trace VERA requests.

    Usage:
        @trace_vera_request
        async def vera_chat(query: VeraQuery):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract metadata from kwargs if available
        officer_id = kwargs.get("officer_id") or (args[0].officer_id if args else None)
        question = kwargs.get("question") or (args[0].question if args else "unknown")

        trace = VERATrace(
            name=f"vera.{func.__name__}",
            session_id=officer_id,
            user_id=officer_id,
            metadata={
                "function": func.__name__,
                "question_preview": question[:100] if question else "",
            },
        )

        try:
            # Store trace in context for nested functions
            kwargs["_langfuse_trace"] = trace

            result = await func(*args, **kwargs)

            # End trace with success
            trace.end(
                output={"status": "success"},
                level="DEFAULT",
            )

            return result

        except Exception as e:
            # End trace with error
            trace.end(
                output={"error": str(e)},
                level="ERROR",
                status_message=str(e),
            )
            raise

    return wrapper


@contextmanager
def trace_span(trace: Optional[VERATrace], name: str, input_data: Any = None):
    """
    Context manager for tracing spans.

    Usage:
        with trace_span(trace, "classification", {"question": q}):
            task_type = classify(q)
    """
    span = None
    if trace:
        span = trace.span(name, input_data)

    try:
        yield span
    finally:
        if span and hasattr(span, 'end'):
            span.end()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. VERA-SPECIFIC TRACING HELPERS
#    "Funções específicas para VERA"
# ═══════════════════════════════════════════════════════════════════════════════

def trace_llm_call(
    trace: Optional[VERATrace],
    model_alias: str,
    model_id: str,
    prompt: str,
    response: str,
    latency_ms: int,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost: float = 0.0,
):
    """
    Record an LLM call in the trace.

    Called for each model in triangulation (Guardian, Architect, etc.)
    """
    if not trace:
        return

    trace.generation(
        name=f"llm.{model_alias.lower()}",
        model=model_id,
        model_parameters={"max_tokens": 600},
        input_messages=[{"role": "user", "content": prompt[:500]}],
        output=response[:500] if response else "",
        usage={
            "input": tokens_in,
            "output": tokens_out,
            "total": tokens_in + tokens_out,
        },
        metadata={
            "alias": model_alias,
            "latency_ms": latency_ms,
            "estimated_cost": cost,
        },
    )


def trace_classification(
    trace: Optional[VERATrace],
    task_type: str,
    eligibility: str,
    keywords_matched: List[str],
):
    """Record task classification in trace."""
    if not trace:
        return

    span = trace.span(
        name="classification",
        input_data={"keywords": keywords_matched},
        metadata={
            "task_type": task_type,
            "eligibility": eligibility,
        },
    )
    if span:
        span.end()


def trace_consensus(
    trace: Optional[VERATrace],
    models_consulted: List[str],
    consensus_achieved: bool,
    divergence_score: float,
):
    """Record consensus result in trace."""
    if not trace:
        return

    span = trace.span(
        name="consensus",
        input_data={"models": models_consulted},
        metadata={
            "consensus_achieved": consensus_achieved,
            "divergence_score": divergence_score,
            "principle_xv": len(models_consulted) >= 2,
        },
    )
    if span:
        span.end()


def trace_quality_gate(
    trace: Optional[VERATrace],
    admissibility_score: int,
    admissibility_level: str,
    gate_passed: bool,
    verdict: str,
):
    """Record Quality Gate result in trace."""
    if not trace:
        return

    # Add score to trace
    trace.score(
        name="admissibility",
        value=admissibility_score / 4.0,  # Normalize to 0-1
        comment=f"{admissibility_level}: {verdict}",
    )

    span = trace.span(
        name="quality_gate",
        metadata={
            "admissibility_score": admissibility_score,
            "admissibility_level": admissibility_level,
            "gate_passed": gate_passed,
            "verdict": verdict,
        },
    )
    if span:
        span.end()


def trace_shadow_audit(
    trace: Optional[VERATrace],
    alerts_count: int,
    alerts: List[Dict[str, Any]],
):
    """Record Shadow Audit result in trace."""
    if not trace:
        return

    # Add score (inverted — 0 alerts = 1.0, many alerts = lower)
    trace.score(
        name="shadow_integrity",
        value=1.0 if alerts_count == 0 else max(0, 1.0 - (alerts_count * 0.2)),
        comment=f"{alerts_count} backdoor alerts detected",
    )

    span = trace.span(
        name="shadow_audit",
        metadata={
            "alerts_count": alerts_count,
            "alert_types": [a.get("name") for a in alerts] if alerts else [],
        },
    )
    if span:
        span.end()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FLUSH & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════════

def flush_langfuse():
    """Flush all pending events to Langfuse."""
    if langfuse_client:
        try:
            langfuse_client.flush()
            log.info("Langfuse flushed")
        except Exception as e:
            log.warning(f"Langfuse flush failed: {e}")


def shutdown_langfuse():
    """Gracefully shutdown Langfuse client."""
    if langfuse_client:
        try:
            langfuse_client.shutdown()
            log.info("Langfuse shutdown complete")
        except Exception as e:
            log.warning(f"Langfuse shutdown failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter

def create_langfuse_router() -> APIRouter:
    """Create FastAPI router for Langfuse status endpoints."""
    router = APIRouter(prefix="/vera/observability", tags=["VERA-Observability"])

    @router.get("/health")
    async def langfuse_health():
        return {
            "status": "operational" if LANGFUSE_ENABLED else "disabled",
            "component": "VERA Langfuse Observability",
            "version": "§204.6",
            "langfuse_enabled": LANGFUSE_ENABLED,
            "langfuse_host": LANGFUSE_HOST if LANGFUSE_ENABLED else None,
            "stack": {
                "deepeval": "quality metrics (espelho)",
                "shadow_audit": "violation detection (polícia)",
                "quality_gate": "admissibility scoring (juiz)",
                "langfuse": "real-time observability (satélite)",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.post("/flush")
    async def flush_events():
        """Manually flush pending events to Langfuse."""
        flush_langfuse()
        return {"status": "flushed", "langfuse_enabled": LANGFUSE_ENABLED}

    return router


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  VERA LANGFUSE OBSERVABILITY — §204.6")
    print("  'Langfuse é o satélite. Observa tudo em tempo real.'")
    print("=" * 60)
    print()
    print(f"Langfuse Enabled: {'✅' if LANGFUSE_ENABLED else '❌'}")
    print(f"Host: {LANGFUSE_HOST}")
    print()

    if not LANGFUSE_ENABLED:
        print("To enable Langfuse, set these environment variables:")
        print("  LANGFUSE_SECRET_KEY=sk-lf-...")
        print("  LANGFUSE_PUBLIC_KEY=pk-lf-...")
        print()
        print("Get keys from: https://cloud.langfuse.com")
    else:
        # Test trace
        print("Testing trace...")
        trace = VERATrace(
            name="vera.test",
            session_id="test-session",
            user_id="did:windi:test",
        )
        trace.generation(
            name="llm.guardian",
            model="claude-sonnet-4",
            output="Test response",
        )
        trace.score("test_score", 0.95, "Test passed")
        trace.end(output={"test": "success"})
        flush_langfuse()
        print("✅ Test trace sent to Langfuse")
