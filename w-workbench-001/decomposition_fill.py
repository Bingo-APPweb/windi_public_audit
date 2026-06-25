"""
W-WORKBENCH-001 — Decomposition Fill (Peça 2)
WINDI Publishing House · 2026

O preenchimento do Project Graph.
Recebe a gramática como CONTRATO e preenche via motor plugável.

Engines disponíveis:
- DRAGON_HUB: Mistral API (FREE) / Anthropic (HIGH) via :8108
- OLLAMA_LOCAL: Quando rota para windi-b estiver disponível (futuro)

Invariante: O resultado é sempre [estimado] até confirmação humana.
"""

import json
import hashlib
import requests
from datetime import datetime
from typing import Optional, Literal
from dataclasses import dataclass

from decomposition_grammar import (
    ProjectGraph,
    Dimension,
    DimensionID,
    Gap,
    Assumption,
    Provenance,
    get_grammar_contract,
    minimize_intent
)


# ============================================================================
# ENGINE CONFIGURATION
# ============================================================================

@dataclass
class EngineConfig:
    """Configuração de um motor de preenchimento."""
    name: str
    endpoint: str
    model: Optional[str] = None
    tier: Literal["FREE", "HIGH"] = "FREE"
    timeout: int = 30


# Mistral API Key (loaded from environment or config)
import os
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "qpSubOv2M5oKoiF4NhQzaObUYQGWAYkp")

# Available engines
ENGINES = {
    "MISTRAL_DIRECT": EngineConfig(
        name="Mistral Direct",
        endpoint="https://api.mistral.ai/v1/chat/completions",
        model="mistral-large-latest",
        tier="MED"
    ),
    "DRAGON_HUB": EngineConfig(
        name="Dragon Hub",
        endpoint="http://localhost:8108/api/dragon/chat",
        model=None,  # Dragon Hub selects based on tier
        tier="MED"  # MED uses Mistral API for real LLM calls
    ),
    "DRAGON_HUB_HIGH": EngineConfig(
        name="Dragon Hub (HIGH)",
        endpoint="http://localhost:8108/api/dragon/chat",
        model=None,
        tier="HIGH"
    ),
    "OLLAMA_LOCAL": EngineConfig(
        name="Ollama Local",
        endpoint="http://windi-b:11434/api/generate",
        model="mistral:7b",
        tier="FREE"
    )
}

# Default engine - MISTRAL_DIRECT bypasses Dragon Hub's routing
DEFAULT_ENGINE = "MISTRAL_DIRECT"


# ============================================================================
# SYSTEM PROMPT (Constitutional)
# ============================================================================

SYSTEM_PROMPT = """You are a Project Compiler for the WINDI system.

Your task is to decompose a human intent into a structured Project Graph.

RULES:
1. You MUST output ONLY valid JSON, no prose before or after
2. You MUST fill ALL 5 dimensions, marking "applicable": "false" for non-relevant ones
3. Gaps MUST be questions (end with ?)
4. Assumptions MUST be statements about what you're assuming to be true
5. Be concise - each content field should be 1-2 sentences max
6. DO NOT invent specific details not present in the intent

OUTPUT FORMAT:
{
  "project_name": "Short descriptive name",
  "project_type": "software|document|business|creative|research|other",
  "inferred_mission": "The macro mission in 3-5 words (e.g., 'healthcare_management', 'legal_compliance', 'financial_analysis')",
  "dimensions": {
    "product": {"applicable": "true|false|uncertain", "content": "...", "confidence": 0.0-1.0},
    "regulatory": {"applicable": "true|false|uncertain", "content": "...", "confidence": 0.0-1.0},
    "users": {"applicable": "true|false|uncertain", "content": "...", "confidence": 0.0-1.0},
    "technology": {"applicable": "true|false|uncertain", "content": "...", "confidence": 0.0-1.0},
    "costs": {"applicable": "true|false|uncertain", "content": "...", "confidence": 0.0-1.0}
  },
  "gaps": [
    {"question": "Essential question 1?", "dimension": "product|regulatory|users|technology|costs", "priority": "high|medium|low"},
    {"question": "Essential question 2?", "dimension": "...", "priority": "..."}
  ],
  "assumptions": [
    {"statement": "We assume X is true", "dimension": "...", "confidence": "confirmed|assumed|uncertain"}
  ],
  "confidence": 0.0-1.0
}
"""


# ============================================================================
# DECOMPOSITION FILL
# ============================================================================

def decomposition_fill(
    intent: str,
    engine: str = DEFAULT_ENGINE,
    lang: str = "en",
    minimize: bool = True
) -> tuple[ProjectGraph, dict]:
    """
    Preenche um ProjectGraph a partir de uma intenção.

    Args:
        intent: A intenção crua do utilizador
        engine: O motor a usar (DRAGON_HUB, OLLAMA_LOCAL, etc.)
        lang: Língua para o output
        minimize: Se True, remove dados pessoais antes de enviar

    Returns:
        (ProjectGraph preenchido, metadata da operação)

    Invariante: O resultado é sempre [estimado] até confirmação humana.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Create graph
    graph = ProjectGraph(
        graph_id=f"pg_{hashlib.sha256(intent.encode()).hexdigest()[:16]}",
        intent_raw=intent,
        created_at=timestamp
    )

    # Minimize if external engine
    if minimize and engine != "OLLAMA_LOCAL":
        minimized, removed = minimize_intent(intent)
        graph.intent_minimized = minimized
    else:
        graph.intent_minimized = intent
        removed = []

    # Get engine config
    engine_config = ENGINES.get(engine)
    if not engine_config:
        raise ValueError(f"Unknown engine: {engine}")

    # Call engine
    try:
        response_data = _call_engine(
            engine_config=engine_config,
            intent=graph.intent_minimized,
            lang=lang
        )

        # Parse response into graph
        _parse_response_to_graph(graph, response_data)

        # Add provenance
        graph.provenance.append(Provenance(
            source="motor",
            timestamp=timestamp,
            engine=engine
        ))

        metadata = {
            "success": True,
            "engine": engine,
            "minimized": minimize,
            "removed_items": removed,
            "raw_response": response_data,
            "timestamp": timestamp
        }

    except Exception as e:
        # On error, return empty graph with error metadata
        metadata = {
            "success": False,
            "engine": engine,
            "error": str(e),
            "timestamp": timestamp
        }

    return graph, metadata


def _call_engine(engine_config: EngineConfig, intent: str, lang: str) -> dict:
    """
    Chama o motor de preenchimento.
    """
    if "mistral.ai" in engine_config.endpoint.lower():
        return _call_mistral_direct(engine_config, intent, lang)
    elif "dragon" in engine_config.endpoint.lower():
        return _call_dragon_hub(engine_config, intent, lang)
    elif "ollama" in engine_config.endpoint.lower():
        return _call_ollama(engine_config, intent, lang)
    else:
        raise ValueError(f"Unknown engine type: {engine_config.endpoint}")


def _call_mistral_direct(engine_config: EngineConfig, intent: str, lang: str) -> dict:
    """
    Chama Mistral API directamente (bypassa Dragon Hub routing).
    Mais rápido e confiável para Project Compilation.
    """
    grammar = get_grammar_contract(lang)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\n\nGrammar Contract:\n{json.dumps(grammar, indent=2)}\n\nOutput language: {lang}"
        },
        {
            "role": "user",
            "content": f"Decompose this intent into a Project Graph:\n\n{intent}"
        }
    ]

    payload = {
        "model": engine_config.model,
        "messages": messages,
        "temperature": 0.3,  # Lower temperature for structured output
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        engine_config.endpoint,
        json=payload,
        headers=headers,
        timeout=engine_config.timeout
    )

    if response.status_code != 200:
        raise Exception(f"Mistral API error: {response.status_code} - {response.text}")

    data = response.json()

    # Mistral returns response in choices[0].message.content
    response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return _extract_json(response_text)


def _call_dragon_hub(engine_config: EngineConfig, intent: str, lang: str) -> dict:
    """
    Chama o Dragon Hub (:8108).
    """
    grammar = get_grammar_contract(lang)

    payload = {
        "message": f"Decompose this intent into a Project Graph:\n\n{intent}",
        "agent": "architect",  # Use Architect persona
        "system_prompt": SYSTEM_PROMPT,
        "context": {
            "grammar_contract": grammar,
            "output_language": lang
        },
        "governance_level": engine_config.tier
    }

    response = requests.post(
        engine_config.endpoint,
        json=payload,
        timeout=engine_config.timeout
    )

    if response.status_code != 200:
        raise Exception(f"Dragon Hub error: {response.status_code} - {response.text}")

    data = response.json()

    # Dragon Hub returns response in 'message' field (not 'response')
    response_text = data.get("message", "") or data.get("response", "")
    return _extract_json(response_text)


def _call_ollama(engine_config: EngineConfig, intent: str, lang: str) -> dict:
    """
    Chama o Ollama local (quando disponível).
    """
    grammar = get_grammar_contract(lang)

    payload = {
        "model": engine_config.model,
        "prompt": f"{SYSTEM_PROMPT}\n\nGrammar Contract:\n{json.dumps(grammar)}\n\nIntent to decompose:\n{intent}\n\nOutput:",
        "stream": False
    }

    response = requests.post(
        engine_config.endpoint,
        json=payload,
        timeout=engine_config.timeout
    )

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.status_code} - {response.text}")

    data = response.json()
    response_text = data.get("response", "")
    return _extract_json(response_text)


def _extract_json(text: str) -> dict:
    """
    Extrai JSON de uma resposta que pode conter prosa.
    """
    import re

    # Try to find JSON block
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # If no valid JSON found, try parsing the whole text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise Exception(f"Could not extract JSON from response: {text[:500]}")


def _parse_response_to_graph(graph: ProjectGraph, data: dict):
    """
    Parseia a resposta do motor para o ProjectGraph.

    Princípio: O motor enriquece o grafo; não compila a intenção original.
    """
    # Project metadata
    graph.project_name = data.get("project_name", "Untitled Project")
    graph.project_type = data.get("project_type", "other")
    graph.confidence = data.get("confidence", 0.5)

    # Fase 2 Hook: Missão inferida (gancho para Capability Planner futuro)
    graph.inferred_mission = data.get("inferred_mission", "")
    # suggested_capabilities permanece vazio em v1 — será preenchido pelo Planner

    # Dimensions
    dimensions_data = data.get("dimensions", {})
    for dim in graph.dimensions:
        dim_data = dimensions_data.get(dim.id.value, {})
        if isinstance(dim_data, dict):
            dim.applicable = dim_data.get("applicable", "uncertain")
            dim.content = dim_data.get("content", "")
            dim.confidence = dim_data.get("confidence", 0.5)

    # Gaps
    gaps_data = data.get("gaps", [])
    for gap_data in gaps_data:
        if isinstance(gap_data, dict):
            dim_id = None
            if gap_data.get("dimension"):
                try:
                    dim_id = DimensionID(gap_data["dimension"])
                except ValueError:
                    pass

            graph.gaps.append(Gap(
                question=gap_data.get("question", ""),
                dimension_id=dim_id,
                priority=gap_data.get("priority", "medium")
            ))

    # Assumptions
    assumptions_data = data.get("assumptions", [])
    for ass_data in assumptions_data:
        if isinstance(ass_data, dict):
            dim_id = None
            if ass_data.get("dimension"):
                try:
                    dim_id = DimensionID(ass_data["dimension"])
                except ValueError:
                    pass

            graph.assumptions.append(Assumption(
                statement=ass_data.get("statement", ""),
                dimension_id=dim_id,
                confidence=ass_data.get("confidence", "assumed")
            ))


# ============================================================================
# API ENDPOINT HELPER
# ============================================================================

def create_decomposition_endpoint():
    """
    Retorna um handler para o endpoint /api/decompose.
    Para integrar no Flask existente.
    """

    def decompose_handler(request_data: dict) -> dict:
        """
        Handler para POST /api/decompose

        Request:
        {
            "intent": "Quero criar um app para clínica",
            "engine": "DRAGON_HUB",  // optional
            "lang": "pt"  // optional
        }

        Response:
        {
            "success": true,
            "graph": {...},
            "metadata": {...},
            "status": "estimated"  // Always "estimated" until human confirms
        }
        """
        intent = request_data.get("intent", "")
        if not intent:
            return {"success": False, "error": "Intent is required"}

        engine = request_data.get("engine", DEFAULT_ENGINE)
        lang = request_data.get("lang", "pt")

        graph, metadata = decomposition_fill(
            intent=intent,
            engine=engine,
            lang=lang,
            minimize=True
        )

        return {
            "success": metadata.get("success", False),
            "graph": graph.to_dict(lang),
            "metadata": {
                "engine": metadata.get("engine"),
                "minimized": metadata.get("minimized"),
                "removed_count": len(metadata.get("removed_items", [])),
                "timestamp": metadata.get("timestamp")
            },
            "status": "estimated",  # INVARIANTE: Sempre "estimated" até confirmação humana
            "requires_confirmation": True
        }

    return decompose_handler


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test minimization
    test_intent = "Quero criar um app para a clínica do Dr. Silva em Kempten"

    print("=" * 60)
    print("DECOMPOSITION FILL TEST")
    print("=" * 60)

    # Create handler
    handler = create_decomposition_endpoint()

    # Test request
    result = handler({
        "intent": test_intent,
        "engine": "DRAGON_HUB",
        "lang": "pt"
    })

    print(json.dumps(result, indent=2, ensure_ascii=False))
