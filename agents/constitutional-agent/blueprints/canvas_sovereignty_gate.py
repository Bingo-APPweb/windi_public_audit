"""
W-CANVAS-001 — Canvas Sovereignty Gate v1.0
============================================
Blueprint constitucional para controlo de tokens Gemini.

Princípio: "Economy enables Quality."
Frase: "O externo sustenta. O interno orienta. A qualidade decide."

Wisdom Block: WB-KNOW-SOVEREIGNTY-Q-20260318
Invariantes: I1 · I9 · I10 · I11
Autor: Human Dragon + Liga IA+H · Kempten, Bavaria · 2026
"""

import re
import json
import hashlib
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("W-CANVAS-001")

# ═══════════════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

class CanvasTier(str, Enum):
    FREE   = "FREE"   # 0 tokens externos — soberania absoluta
    MED    = "MED"    # Gemini Flash — ~300-600 tokens
    HIGH   = "HIGH"   # Gemini Pro   — ~800-2000 tokens

class DiagramType(str, Enum):
    FLOWCHART  = "flowchart"
    MINDMAP    = "mindmap"
    TIMELINE   = "timeline"
    SEQUENCE   = "sequence"
    GANTT      = "gantt"

class CanvasModel(str, Enum):
    LOCAL            = "local_template"       # 0 tokens — FREE
    GEMINI_FLASH     = "gemini-1.5-flash"     # rápido, barato — MED
    GEMINI_PRO       = "gemini-1.5-pro"       # qualidade máxima — HIGH

# Orçamento máximo de tokens por tier (input + output estimado)
TOKEN_BUDGET = {
    CanvasTier.FREE:  0,
    CanvasTier.MED:   600,
    CanvasTier.HIGH:  2000,
}

# Custo estimado por token (USD) — Gemini pricing
COST_PER_TOKEN = {
    CanvasModel.LOCAL:        0.0,
    CanvasModel.GEMINI_FLASH: 0.000000075,   # $0.075 / 1M tokens
    CanvasModel.GEMINI_PRO:   0.00000125,    # $1.25  / 1M tokens
}

# ═══════════════════════════════════════════════════════════════════════
# TEMPLATES LOCAIS — FREE TIER (zero tokens externos)
# ═══════════════════════════════════════════════════════════════════════

LOCAL_TEMPLATES = {
    DiagramType.FLOWCHART: {
        "windi_pipeline": """flowchart TD
    A([Utilizador]) --> B[Cria Documento]
    B --> C{Dragon\nProcessa}
    C -->|Aprovado| D[Ledger\nSela]
    C -->|Revisar| B
    D --> E[QR\nForense]
    E --> F([Download\nReceipt])
    style A fill:#8B6914,color:#fff
    style D fill:#2D5016,color:#fff
    style F fill:#8B6914,color:#fff""",

        "agentes_windi": """flowchart TD
    CA([Constitutional\nAgent]) --> L[W-LEGAL-001]
    CA --> N[W-NOTARY-001]
    CA --> C[W-COMPLY-001]
    CA --> J[W-JOURN-001]
    CA --> AU[W-AUDIT-001]
    CA --> AC[W-ACCT-001]
    CA --> CM[W-COMM-001]
    L & N & C & J & AU & AC & CM --> LG[(Ledger\n:8101)]
    style CA fill:#1a1a2e,color:#fff
    style LG fill:#8B6914,color:#fff""",

        "did_flow": """flowchart TD
    A([Anon 5min]) --> B{Wallet\nBanner}
    B -->|Criar DID| C[Ed25519\nGerado]
    B -->|Mais tarde| D[Modo\nLeitura]
    C --> E[UUIDv7\nPioneer]
    E --> F[Ledger\nAuto-Seal]
    F --> G([Identidade\nSoberana])
    style A fill:#666,color:#fff
    style G fill:#8B6914,color:#fff
    style D fill:#cc0000,color:#fff""",
    },

    DiagramType.MINDMAP: {
        "constellation": """mindmap
  root((WINDI))
    Constitutional Agent
      I1 Soberania
      I9 Anti-Autonomia
      I11 Permanencia
    Agentes
      W-LEGAL-001
      W-NOTARY-001
      W-COMPLY-001
      W-JOURN-001
      W-AUDIT-001
      W-ACCT-001
      W-COMM-001
    Ledger
      56k+ Receipts
      SHA-256
      QR Forense
    Identidade
      DID Wallet
      Ed25519
      Pioneers""",
    },

    DiagramType.TIMELINE: {
        "windi_evolution": """timeline
    title Evolucao WINDI
    2025 : Basic Setup
    Jan 2026 : Integration
    Mar 2026 : Canvas Live
    Dec 2026 : Full Autonomy""",
    },

    DiagramType.SEQUENCE: {
        "document_seal": """sequenceDiagram
    actor U as Utilizador
    participant D as Dragon
    participant L as W-LEGAL-001
    participant LG as Ledger
    U->>D: Cria documento
    D->>D: Processa + SGE
    D-->>U: Rascunho gerado
    U->>D: Aprova
    D->>LG: POST /api/records
    LG-->>D: receipt_id + hash
    D->>U: QR + Download
    Note over LG: IRREMEDIAVEL""",
    },
}

# ═══════════════════════════════════════════════════════════════════════
# PATTERN MATCHER — detecta template local aplicável
# ═══════════════════════════════════════════════════════════════════════

PATTERN_MAP = [
    # (keywords, diagram_type, template_key)
    (["windi", "pipeline", "fluxo", "documento", "ledger", "dragon"], DiagramType.FLOWCHART, "windi_pipeline"),
    (["agente", "constelacao", "constellation", "legal", "notary", "audit"], DiagramType.FLOWCHART, "agentes_windi"),
    (["did", "wallet", "identidade", "pioneer", "sovereign"], DiagramType.FLOWCHART, "did_flow"),
    (["mindmap", "mapa mental", "constelacao windi", "windi overview"], DiagramType.MINDMAP, "constellation"),
    (["sequencia", "sequence", "seal", "documento selado", "document seal"], DiagramType.SEQUENCE, "document_seal"),
    (["timeline", "evolucao", "evolution", "cronologia", "linha do tempo"], DiagramType.TIMELINE, "windi_evolution"),
]

def match_local_template(prompt: str, diagram_type: DiagramType) -> Optional[str]:
    """
    Tenta encontrar um template local para o prompt dado.
    Retorna o código Mermaid se encontrado, None caso contrário.
    """
    prompt_lower = prompt.lower()

    for keywords, dtype, template_key in PATTERN_MAP:
        if dtype != diagram_type:
            continue
        matches = sum(1 for kw in keywords if kw in prompt_lower)
        if matches >= 2:  # mínimo 2 keywords para match
            templates = LOCAL_TEMPLATES.get(dtype, {})
            if template_key in templates:
                logger.info(f"[GATE] Template local encontrado: {dtype.value}/{template_key} ({matches} matches)")
                return templates[template_key]

    return None


# ═══════════════════════════════════════════════════════════════════════
# COMPLEXIDADE DETECTOR — quanto este prompt precisa de LLM?
# ═══════════════════════════════════════════════════════════════════════

def estimate_complexity(prompt: str, diagram_type: DiagramType) -> int:
    """
    Estima complexidade 0-100.
    0-30  → local suficiente
    31-60 → Gemini Flash (MED)
    61+   → Gemini Pro (HIGH)
    """
    score = 0
    prompt_lower = prompt.lower()

    # Comprimento do prompt
    words = len(prompt.split())
    if words > 30:  score += 20
    elif words > 15: score += 10

    # Entidades específicas (nomes próprios, números, datas)
    entities = re.findall(r'\b[A-Z][a-z]+\b|\b\d+[€$%]\b|\b\d{4}\b', prompt)
    score += min(len(entities) * 5, 25)

    # Palavras de alta complexidade semântica
    complex_words = ["arquitectura", "estrategia", "relacao", "dependencia",
                     "fluxo completo", "sistema completo", "todos os", "cada",
                     "integracao", "comparacao", "roadmap", "evolucao"]
    for word in complex_words:
        if word in prompt_lower:
            score += 8

    # Tipos inerentemente mais complexos
    if diagram_type in [DiagramType.GANTT, DiagramType.SEQUENCE]:
        score += 15

    # Limite
    return min(score, 100)


# ═══════════════════════════════════════════════════════════════════════
# SOVEREIGNTY GATE — decisão central
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class GateDecision:
    model:       CanvasModel
    tier:        CanvasTier
    max_tokens:  int
    cost_est:    float          # USD estimado
    justification: str
    local_template: Optional[str] = None
    complexity:  int = 0

def sovereignty_gate(
    prompt: str,
    diagram_type: DiagramType,
    wallet_tier: str,           # "FREE" | "MED" | "HIGH"
    wallet_id: Optional[str] = None,
) -> GateDecision:
    """
    Gate constitucional — decide modelo, tokens e custo.

    REGRA SUPREMA: I9 é inviolável.
    O sistema NUNCA decide autonomamente escalar capacidade.
    """
    tier = CanvasTier(wallet_tier.upper()) if wallet_tier.upper() in CanvasTier.__members__ else CanvasTier.FREE

    # ── LEI I: FREE = Soberania absoluta ──────────────────────────────
    if tier == CanvasTier.FREE:
        local = match_local_template(prompt, diagram_type)
        if local:
            return GateDecision(
                model=CanvasModel.LOCAL,
                tier=tier,
                max_tokens=0,
                cost_est=0.0,
                justification="FREE tier + template local encontrado → soberania absoluta",
                local_template=local,
                complexity=0,
            )
        else:
            return GateDecision(
                model=CanvasModel.LOCAL,
                tier=tier,
                max_tokens=0,
                cost_est=0.0,
                justification="FREE tier → modo leitura. Simplifica o pedido ou activa DID para acesso completo.",
                local_template=_generate_simple_template(diagram_type),
                complexity=0,
            )

    # ── Verificar template local para todos os tiers ──────────────────
    local = match_local_template(prompt, diagram_type)
    complexity = estimate_complexity(prompt, diagram_type)

    if local and complexity < 40:
        return GateDecision(
            model=CanvasModel.LOCAL,
            tier=tier,
            max_tokens=0,
            cost_est=0.0,
            justification=f"Template local suficiente (complexidade {complexity}/100) → tokens poupados",
            local_template=local,
            complexity=complexity,
        )

    # ── MED: Gemini Flash ─────────────────────────────────────────────
    if tier == CanvasTier.MED or (tier == CanvasTier.HIGH and complexity < 60):
        budget = TOKEN_BUDGET[CanvasTier.MED]
        cost = budget * COST_PER_TOKEN[CanvasModel.GEMINI_FLASH]
        return GateDecision(
            model=CanvasModel.GEMINI_FLASH,
            tier=tier,
            max_tokens=budget,
            cost_est=cost,
            justification=f"Semantica real necessaria (complexidade {complexity}/100) → Gemini Flash justificado",
            complexity=complexity,
        )

    # ── HIGH: Gemini Pro ──────────────────────────────────────────────
    budget = TOKEN_BUDGET[CanvasTier.HIGH]
    cost = budget * COST_PER_TOKEN[CanvasModel.GEMINI_PRO]
    return GateDecision(
        model=CanvasModel.GEMINI_PRO,
        tier=tier,
        max_tokens=budget,
        cost_est=cost,
        justification=f"Alta complexidade ({complexity}/100) + HIGH tier → Gemini Pro · qualidade institucional",
        complexity=complexity,
    )


def _generate_simple_template(diagram_type: DiagramType) -> str:
    """Template mínimo local para FREE quando não há match."""
    defaults = {
        DiagramType.FLOWCHART: "flowchart TD\n    A([Inicio]) --> B[Processo]\n    B --> C{Decisao}\n    C -->|Sim| D([Fim])\n    C -->|Nao| B",
        DiagramType.MINDMAP:   "mindmap\n  root((Tema))\n    Ramo 1\n    Ramo 2\n    Ramo 3",
        DiagramType.TIMELINE:  "timeline\n    title Linha do Tempo\n    Evento 1 : Descricao\n    Evento 2 : Descricao",
        DiagramType.SEQUENCE:  "sequenceDiagram\n    actor A\n    actor B\n    A->>B: Mensagem\n    B-->>A: Resposta",
        DiagramType.GANTT:     "gantt\n    title Plano\n    dateFormat YYYY-MM\n    Fase 1: 2026-01, 30d\n    Fase 2: 2026-02, 30d",
    }
    return defaults.get(diagram_type, defaults[DiagramType.FLOWCHART])


# ═══════════════════════════════════════════════════════════════════════
# TOKEN LOGGER — registo soberano de consumo
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CanvasUsageRecord:
    canvas_id:     str
    wallet_id:     str
    timestamp:     str
    diagram_type:  str
    model:         str
    tokens_used:   int
    cost_usd:      float
    was_local:     bool
    complexity:    int
    prompt_hash:   str          # hash do prompt — não o prompt em si (GDPR)

def log_canvas_usage(
    canvas_id: str,
    wallet_id: str,
    diagram_type: DiagramType,
    decision: GateDecision,
    tokens_actual: int = 0,
) -> CanvasUsageRecord:
    """
    Regista consumo de tokens de forma soberana.
    NUNCA armazena o prompt — só o hash (GDPR by design).
    """
    cost_actual = tokens_actual * COST_PER_TOKEN.get(decision.model, 0.0)

    record = CanvasUsageRecord(
        canvas_id=canvas_id,
        wallet_id=wallet_id or "anonymous",
        timestamp=datetime.utcnow().isoformat(),
        diagram_type=diagram_type.value,
        model=decision.model.value,
        tokens_used=tokens_actual,
        cost_usd=cost_actual,
        was_local=(decision.model == CanvasModel.LOCAL),
        complexity=decision.complexity,
        prompt_hash=hashlib.sha256(canvas_id.encode()).hexdigest()[:16],
    )

    logger.info(
        f"[CANVAS-USAGE] id={canvas_id[:8]} "
        f"model={record.model} "
        f"tokens={tokens_actual} "
        f"cost=${cost_actual:.6f} "
        f"local={record.was_local} "
        f"complexity={record.complexity}"
    )

    return record


# ═══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT BUILDER — Mermaid v10 safe
# ═══════════════════════════════════════════════════════════════════════

MERMAID_RULES = """
REGRAS CRITICAS Mermaid v10.9.5 — NUNCA violar:
1. flowchart TD  (nao graph TD)
2. Setas: --> e nao ->
3. SEM acentos ou caracteres especiais dentro de nos: [Texto], (Texto), {Texto}
4. Use texto ASCII dentro dos nos: Criacao (nao Criação)
5. MAXIMO 12 nos por diagrama
6. IDs de nos: apenas letras e numeros, sem espacos (ex: nodeA, node1)
7. Para texto com espacos no label: A["Texto com espacos"]
8. Subgraph: subgraph Nome\\n...\\nend
9. Retorna APENAS o codigo Mermaid — SEM markdown, SEM backticks, SEM explicacao
"""

def build_canvas_system_prompt(diagram_type: DiagramType, theme: str, model: CanvasModel) -> str:
    """Constrói system prompt optimizado por tier — menos tokens = melhor."""

    base = f"""Es o W-CANVAS-001, agente de visualizacao do WINDI Publishing House.
Geras diagramas Mermaid {diagram_type.value} em resposta a pedidos institucionais.
Tema visual: {theme.upper()}.
{MERMAID_RULES}"""

    # MED: prompt compacto
    if model == CanvasModel.GEMINI_FLASH:
        return base + "\nSe conciso. Maximo 10 nos. Prioriza clareza sobre completude."

    # HIGH: contexto institucional completo
    if model == CanvasModel.GEMINI_PRO:
        return base + f"""
Contexto institucional WINDI:
- Sistema de governanca documental soberano
- Agentes: W-LEGAL, W-NOTARY, W-COMPLY, W-JOURN, W-AUDIT, W-ACCT, W-COMM
- Ledger forense com 56k+ receipts SHA-256
- Principio: "AI processes. Human decides. WINDI guarantees."
- Gera diagrama rico, informativo, com maximo 12 nos bem organizados.
"""

    return base  # LOCAL — não vai ao Gemini


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT HANDLER — integração com canvas_blueprint.py
# ═══════════════════════════════════════════════════════════════════════

def handle_canvas_request(payload: dict) -> dict:
    """
    Handler principal do W-CANVAS-001.

    Payload esperado:
    {
        "prompt": str,
        "diagram_type": str,   # "flowchart" | "mindmap" | ...
        "theme": str,          # "KLAR" | "NOIR" | "Dark Gold" | "Sovereign"
        "wallet_id": str,      # opcional — afecta tier
        "canvas_id": str,      # UUID gerado pelo frontend
        "tier": str,           # "FREE" | "MED" | "HIGH"
    }
    """
    prompt       = payload.get("prompt", "")
    diagram_type = DiagramType(payload.get("diagram_type", "flowchart").lower())
    theme        = payload.get("theme", "KLAR")
    wallet_id    = payload.get("wallet_id")
    canvas_id    = payload.get("canvas_id", "UNKNOWN")
    tier         = payload.get("tier", "FREE")

    # ── GATE DECISION ─────────────────────────────────────────────────
    decision = sovereignty_gate(prompt, diagram_type, tier, wallet_id)

    logger.info(
        f"[GATE] canvas_id={canvas_id[:8]} "
        f"tier={tier} model={decision.model.value} "
        f"budget={decision.max_tokens}tk "
        f"cost_est=${decision.cost_est:.6f} | {decision.justification}"
    )

    # ── RESPOSTA LOCAL ────────────────────────────────────────────────
    if decision.model == CanvasModel.LOCAL:
        log_canvas_usage(canvas_id, wallet_id, diagram_type, decision, tokens_actual=0)
        return {
            "success": True,
            "canvas_id": canvas_id,
            "agent": "W-CANVAS-001",
            "mermaid": decision.local_template,
            "model": "local",
            "tokens_used": 0,
            "cost_usd": 0.0,
            "sovereignty": "LOCAL",
            "gate": decision.justification,
        }

    # ── CHAMADA GEMINI ─────────────────────────────────────────────────
    # (integrar com gemini_client existente no canvas_blueprint.py)
    system_prompt = build_canvas_system_prompt(diagram_type, theme, decision.model)

    return {
        "success": True,
        "canvas_id": canvas_id,
        "agent": "W-CANVAS-001",
        "model": decision.model.value,
        "max_tokens": decision.max_tokens,
        "cost_est_usd": decision.cost_est,
        "system_prompt": system_prompt,
        "sovereignty": "EXTERNAL_JUSTIFIED",
        "gate": decision.justification,
        # mermaid será preenchido pelo canvas_blueprint.py após chamada Gemini
    }


# ═══════════════════════════════════════════════════════════════════════
# SOVEREIGNTY REPORT — para o D3 Governance-Glas
# ═══════════════════════════════════════════════════════════════════════

def sovereignty_report(records: list) -> dict:
    """
    Gera relatório de soberania para o D3 Governance-Glas.
    Mostra quanto poupámos vs quanto gastámos.
    """
    total     = len(records)
    local     = sum(1 for r in records if r.was_local)
    external  = total - local
    cost_total = sum(r.cost_usd for r in records)
    tokens_total = sum(r.tokens_used for r in records)

    # Custo hipotético se tudo fosse Gemini Pro
    hypothetical_cost = sum(
        (r.tokens_used or 600) * COST_PER_TOKEN[CanvasModel.GEMINI_PRO]
        for r in records
    )
    savings = hypothetical_cost - cost_total

    return {
        "total_renders":      total,
        "local_renders":      local,
        "external_renders":   external,
        "sovereignty_pct":    round((local / total * 100) if total > 0 else 100, 1),
        "tokens_consumed":    tokens_total,
        "cost_usd_actual":    round(cost_total, 6),
        "cost_usd_saved":     round(savings, 6),
        "cost_eur_month_est": round(cost_total * 0.92, 4),
        "gate_principle":     "Economy enables Quality — O externo sustenta. O interno orienta.",
    }


# ═══════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("\n🐉 W-CANVAS-001 — Canvas Sovereignty Gate v1.0 — Self-Test\n")
    print("=" * 60)

    tests = [
        ("fluxo windi com dragon e ledger", DiagramType.FLOWCHART, "FREE"),
        ("diagrama agentes constelacao windi", DiagramType.FLOWCHART, "MED"),
        ("arquitectura completa sistema WINDI com todos os agentes integracao ledger", DiagramType.FLOWCHART, "HIGH"),
        ("mapa mental windi overview", DiagramType.MINDMAP, "FREE"),
        ("roadmap Q2 2026 pagamentos mobile certificacao launch eIDAS", DiagramType.GANTT, "HIGH"),
    ]

    for prompt, dtype, tier in tests:
        d = sovereignty_gate(prompt, dtype, tier)
        print(f"\nPrompt : {prompt[:50]}...")
        print(f"Tier   : {tier}")
        print(f"Model  : {d.model.value}")
        print(f"Tokens : {d.max_tokens}  |  Cost: ${d.cost_est:.6f}")
        print(f"Gate   : {d.justification}")

    print("\n" + "=" * 60)
    print("✅ Self-test completo\n")
