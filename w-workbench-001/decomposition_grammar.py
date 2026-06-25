"""
W-WORKBENCH-001 — Decomposition Grammar (Peça 1)
WINDI Publishing House · 2026

A gramática soberana do Project Compiler.
Define O QUE é uma dimensão, O QUE é uma lacuna, O QUE é um pressuposto.
O motor preenche dentro destas regras — nunca decide a estrutura.

Invariante: categorias expandem por doutrina, não por capricho do motor.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum
import json


# ============================================================================
# CORE DIMENSIONS (Fixas, Constitucionais)
# ============================================================================

class DimensionID(Enum):
    """As 5 dimensões nucleares do Project Graph."""
    PRODUCT = "product"
    REGULATORY = "regulatory"
    USERS = "users"
    TECHNOLOGY = "technology"
    COSTS = "costs"


# Trilingual labels for each dimension
DIMENSION_LABELS = {
    DimensionID.PRODUCT: {
        "pt": "Produto",
        "en": "Product",
        "de": "Produkt",
        "description": {
            "pt": "O que o produto fará, suas funcionalidades centrais",
            "en": "What the product does, its core functionalities",
            "de": "Was das Produkt tut, seine Kernfunktionen"
        }
    },
    DimensionID.REGULATORY: {
        "pt": "Regulatório",
        "en": "Regulatory",
        "de": "Regulatorisch",
        "description": {
            "pt": "Regras, jurisdições, conformidades aplicáveis",
            "en": "Rules, jurisdictions, applicable compliance",
            "de": "Regeln, Zuständigkeiten, anwendbare Compliance"
        }
    },
    DimensionID.USERS: {
        "pt": "Utilizadores",
        "en": "Users",
        "de": "Benutzer",
        "description": {
            "pt": "Quem são os atores e utilizadores afetados",
            "en": "Who are the actors and affected users",
            "de": "Wer sind die Akteure und betroffenen Benutzer"
        }
    },
    DimensionID.TECHNOLOGY: {
        "pt": "Tecnologia",
        "en": "Technology",
        "de": "Technologie",
        "description": {
            "pt": "Pilares técnicos, plataformas, integrações",
            "en": "Technical pillars, platforms, integrations",
            "de": "Technische Säulen, Plattformen, Integrationen"
        }
    },
    DimensionID.COSTS: {
        "pt": "Custos",
        "en": "Costs",
        "de": "Kosten",
        "description": {
            "pt": "Vetores de custo, hosting, desenvolvimento",
            "en": "Cost vectors, hosting, development",
            "de": "Kostenvektoren, Hosting, Entwicklung"
        }
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Dimension:
    """
    Uma dimensão do Project Graph.

    Invariante: as 5 dimensões são fixas.
    O campo 'applicable' indica se esta dimensão se aplica ao projecto.
    Um poema não tem Regulatório. Uma clínica tem Regulatório crítico.
    """
    id: DimensionID
    applicable: Literal["true", "false", "uncertain"] = "uncertain"
    content: str = ""  # Preenchido pelo motor
    confidence: float = 0.0  # 0.0-1.0

    def get_label(self, lang: str = "pt") -> str:
        """Retorna o label na língua especificada."""
        return DIMENSION_LABELS[self.id].get(lang, DIMENSION_LABELS[self.id]["pt"])

    def get_description(self, lang: str = "pt") -> str:
        """Retorna a descrição na língua especificada."""
        return DIMENSION_LABELS[self.id]["description"].get(lang)


@dataclass
class Gap:
    """
    Uma lacuna identificada no projecto.
    Sempre em formato de pergunta.
    """
    question: str
    dimension_id: Optional[DimensionID] = None  # A que dimensão pertence
    priority: Literal["high", "medium", "low"] = "medium"
    answered: bool = False
    answer: Optional[str] = None


@dataclass
class Assumption:
    """
    Um pressuposto do projecto.
    Memória de decisão: "Por que decidimos isto?"
    """
    statement: str
    dimension_id: Optional[DimensionID] = None
    confidence: Literal["confirmed", "assumed", "uncertain"] = "assumed"
    source: Optional[str] = None  # Quem/o quê originou este pressuposto


@dataclass
class Provenance:
    """
    Rastreio de origem de cada elemento do grafo.
    """
    source: Literal["human", "motor", "minimized"]
    timestamp: str
    engine: Optional[str] = None  # e.g., "dragon_hub", "ollama_local"
    original_hash: Optional[str] = None


@dataclass
class ProjectGraph:
    """
    O artefacto central do sistema.

    Tudo no WINDI Playground deriva deste grafo:
    - Editor → projecção do grafo
    - Buscas → anexadas a nós do grafo
    - Documentos → derivações do grafo
    - Ledger receipts → referenciam nós do grafo

    Princípio Constitucional (§300-candidate):
    "Modelos externos enriquecem um ProjectGraph; não compilam a intenção original."
    """
    # Core
    graph_id: str = ""
    intent_raw: str = ""  # Intenção original (NUNCA sai do território)
    intent_minimized: str = ""  # Intenção sem dados pessoais (pode sair)
    project_name: str = ""  # Nome curto inferido
    project_type: str = ""  # e.g., "software", "document", "business"

    # Fase 2 Hooks (preparados, não implementados)
    inferred_mission: str = ""  # Missão macro — gancho para Capability Planner futuro
    suggested_capabilities: list = field(default_factory=list)  # Vazio em v1

    # Estruturas
    dimensions: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)

    # Metadados
    confidence: float = 0.0  # Confiança geral do grafo
    status: Literal["draft", "confirmed", "sealed"] = "draft"
    provenance: list = field(default_factory=list)

    # Timestamps
    created_at: str = ""
    confirmed_at: Optional[str] = None

    def __post_init__(self):
        """Inicializa as 5 dimensões fixas se não existirem."""
        if not self.dimensions:
            self.dimensions = [
                Dimension(id=dim_id)
                for dim_id in DimensionID
            ]

    def get_dimension(self, dim_id: DimensionID) -> Optional[Dimension]:
        """Retorna uma dimensão específica."""
        for dim in self.dimensions:
            if dim.id == dim_id:
                return dim
        return None

    def to_dict(self, lang: str = "pt") -> dict:
        """Serializa o grafo para JSON com labels traduzidos."""
        return {
            "graph_id": self.graph_id,
            "intent_minimized": self.intent_minimized,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "inferred_mission": self.inferred_mission,
            "suggested_capabilities": self.suggested_capabilities,  # Vazio em v1
            "dimensions": [
                {
                    "id": dim.id.value,
                    "label": dim.get_label(lang),
                    "description": dim.get_description(lang),
                    "applicable": dim.applicable,
                    "content": dim.content,
                    "confidence": dim.confidence
                }
                for dim in self.dimensions
            ],
            "gaps": [
                {
                    "question": gap.question,
                    "dimension_id": gap.dimension_id.value if gap.dimension_id else None,
                    "priority": gap.priority,
                    "answered": gap.answered
                }
                for gap in self.gaps
            ],
            "assumptions": [
                {
                    "statement": ass.statement,
                    "dimension_id": ass.dimension_id.value if ass.dimension_id else None,
                    "confidence": ass.confidence
                }
                for ass in self.assumptions
            ],
            "confidence": self.confidence,
            "status": self.status,
            "created_at": self.created_at
        }

    def to_json(self, lang: str = "pt") -> str:
        """Serializa para JSON string."""
        return json.dumps(self.to_dict(lang), ensure_ascii=False, indent=2)


# ============================================================================
# GRAMMAR CONTRACT (Para enviar ao motor)
# ============================================================================

def get_grammar_contract(lang: str = "en") -> dict:
    """
    Retorna o contrato da gramática para enviar ao motor.
    O motor DEVE preencher dentro desta estrutura.
    """
    return {
        "schema_version": "1.0.0",
        "dimensions": [
            {
                "id": dim_id.value,
                "label": DIMENSION_LABELS[dim_id][lang],
                "description": DIMENSION_LABELS[dim_id]["description"][lang],
                "required_fields": ["applicable", "content"]
            }
            for dim_id in DimensionID
        ],
        "gaps": {
            "format": "question",
            "min_count": 1,
            "max_count": 5
        },
        "assumptions": {
            "format": "statement",
            "min_count": 0,
            "max_count": 3
        },
        "output_format": "json_strict"
    }


# ============================================================================
# QUERY MINIMIZATION (Privacidade)
# ============================================================================

# Patterns that indicate personal data (to be stripped before external call)
PERSONAL_DATA_PATTERNS = [
    r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Names like "John Smith"
    r'\bDr\.\s+[A-Z][a-z]+\b',  # Dr. Fulano
    r'\b[A-Z][a-z]+\s+(GmbH|AG|Ltd|Inc)\b',  # Company names
    r'\b\d{5}\b',  # ZIP codes
    r'\b[A-Za-z]+straße\b',  # German street names
    r'\b[A-Za-z]+\s+(Street|Avenue|Road)\b',  # English streets
    r'\bemail\s*[:=]\s*\S+@\S+\b',  # Email patterns
    r'\b\d{2,4}[-/]\d{2}[-/]\d{2,4}\b',  # Dates
]


def minimize_intent(raw_intent: str) -> tuple[str, list[str]]:
    """
    Remove dados pessoais da intenção antes de enviar ao motor externo.

    Returns:
        (minimized_intent, list_of_removed_items)

    Invariante: O que sai do território não identifica o utilizador.
    """
    import re

    minimized = raw_intent
    removed = []

    for pattern in PERSONAL_DATA_PATTERNS:
        matches = re.findall(pattern, minimized)
        for match in matches:
            removed.append(match)
            minimized = minimized.replace(match, "[REDACTED]")

    # Remove multiple [REDACTED] in sequence
    minimized = re.sub(r'\[REDACTED\](\s*\[REDACTED\])+', '[REDACTED]', minimized)

    return minimized.strip(), removed


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create a new project graph
    graph = ProjectGraph(
        graph_id="pg_test001",
        intent_raw="Quero criar um app para a clínica do Dr. Silva em Kempten",
        created_at="2026-06-25T22:00:00Z"
    )

    # Minimize intent before external call
    minimized, removed = minimize_intent(graph.intent_raw)
    graph.intent_minimized = minimized
    print(f"Original: {graph.intent_raw}")
    print(f"Minimized: {graph.intent_minimized}")
    print(f"Removed: {removed}")
    print()

    # Show grammar contract
    print("Grammar Contract:")
    print(json.dumps(get_grammar_contract("en"), indent=2))
    print()

    # Show empty graph
    print("Empty Graph:")
    print(graph.to_json("pt"))
