# engine/tri_divergence.py
# WINDI Tri-Divergence Detector - Three Backend Comparison
# Status: PENDENTE | Prioridade: MÉDIA
# "Maioria NÃO resolve. Expõe os 3. Humano decide."

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PairComparison:
    """Resultado da comparação entre um par de backends."""
    backend_a: str
    backend_b: str
    divergence_type: str  # NONE, STYLISTIC, NORMATIVE
    semantic_overlap: float


@dataclass
class TriDivergenceResult:
    """Resultado da análise de divergência entre 3 backends."""
    divergence_detected: bool
    divergence_pattern: str    # "ALL_AGREE" | "TWO_VS_ONE" | "ALL_DIFFER" | "PARTIAL"
    outlier: Optional[str]     # Qual backend divergiu (se TWO_VS_ONE)
    normative_conflicts: int   # Quantos pares têm conflito normativo
    pairwise: List[PairComparison]  # Detalhes de cada par
    requires_human: bool
    audit_summary: str
    timestamp: str


class TriDivergenceDetector:
    """
    Detecta divergência entre 3 backends (Claude, GPT, Gemini).
    
    REGRAS CARDINAIS:
    1. Maioria NÃO resolve conflito
    2. Nunca sintetiza, mesmo com 2 concordando
    3. Expõe todos os 3 para decisão humana
    4. Outlier não é "errado", é "diferente"
    
    PADRÕES DE DIVERGÊNCIA:
    - ALL_AGREE: Todos consistentes (raro, bom)
    - TWO_VS_ONE: Dois concordam, um diverge (identifica outlier)
    - ALL_DIFFER: Todos divergem entre si (crítico)
    - PARTIAL: Situação ambígua
    """
    
    def __init__(self, base_detector):
        """
        Args:
            base_detector: Instance of DivergenceDetectorV2
        """
        self.base = base_detector
    
    def detect(
        self,
        response_claude: str,
        response_gpt: str,
        response_gemini: str
    ) -> TriDivergenceResult:
        """
        Compara 3 respostas em todos os pares possíveis.
        
        Args:
            response_claude: Resposta do Claude
            response_gpt: Resposta do GPT
            response_gemini: Resposta do Gemini
            
        Returns:
            TriDivergenceResult com análise completa
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Comparações em pares (3 pares possíveis)
        pairs = [
            ("claude", "gpt", response_claude, response_gpt),
            ("claude", "gemini", response_claude, response_gemini),
            ("gpt", "gemini", response_gpt, response_gemini),
        ]
        
        pairwise = []
        normative_pairs = []
        
        for backend_a, backend_b, resp_a, resp_b in pairs:
            result = self.base.detect(resp_a or "", resp_b or "")
            
            comparison = PairComparison(
                backend_a=backend_a,
                backend_b=backend_b,
                divergence_type=result.divergence_type,
                semantic_overlap=result.semantic_overlap
            )
            pairwise.append(comparison)
            
            if result.divergence_type == "NORMATIVE":
                normative_pairs.append((backend_a, backend_b))
        
        # Determinar padrão
        pattern, outlier, summary = self._determine_pattern(normative_pairs)
        
        # Qualquer conflito normativo requer humano
        requires_human = len(normative_pairs) > 0
        
        return TriDivergenceResult(
            divergence_detected=(len(normative_pairs) > 0),
            divergence_pattern=pattern,
            outlier=outlier,
            normative_conflicts=len(normative_pairs),
            pairwise=pairwise,
            requires_human=requires_human,
            audit_summary=summary,
            timestamp=timestamp
        )
    
    def _determine_pattern(
        self,
        normative_pairs: List[tuple]
    ) -> tuple:
        """
        Determina o padrão de divergência.
        
        Returns:
            (pattern, outlier, summary)
        """
        if len(normative_pairs) == 0:
            return (
                "ALL_AGREE",
                None,
                "All three backends are materially consistent"
            )
        
        elif len(normative_pairs) == 3:
            return (
                "ALL_DIFFER",
                None,
                "CRITICAL: All three backends diverge normatively from each other"
            )
        
        elif len(normative_pairs) == 1:
            # Um par diverge - os outros dois concordam entre si
            divergent_pair = normative_pairs[0]
            # O terceiro (que não está no par divergente) concorda com ambos
            # Isso é raro - significa que A e B divergem, mas C concorda com ambos
            return (
                "PARTIAL",
                None,
                f"Partial divergence: {divergent_pair[0]} and {divergent_pair[1]} conflict"
            )
        
        elif len(normative_pairs) == 2:
            # Dois pares divergem - identificar outlier
            # Se claude-gpt e claude-gemini divergem, claude é outlier
            # Se claude-gpt e gpt-gemini divergem, gpt é outlier
            # Se claude-gemini e gpt-gemini divergem, gemini é outlier
            
            all_in_conflicts = []
            for pair in normative_pairs:
                all_in_conflicts.extend(pair)
            
            # Contar ocorrências
            from collections import Counter
            counts = Counter(all_in_conflicts)
            
            # Outlier é quem aparece 2x (está em ambos os pares conflitantes)
            for backend, count in counts.items():
                if count == 2:
                    # Os outros dois concordam entre si
                    others = [b for b in ["claude", "gpt", "gemini"] if b != backend]
                    return (
                        "TWO_VS_ONE",
                        backend,
                        f"{others[0].title()}+{others[1].title()} agree; {backend.title()} diverges"
                    )
            
            # Fallback
            return (
                "PARTIAL",
                None,
                "Complex divergence pattern - manual review required"
            )
        
        else:
            return (
                "PARTIAL",
                None,
                "Unexpected divergence pattern"
            )
    
    def expose_all(
        self,
        responses: Dict[str, str],
        divergence_result: TriDivergenceResult
    ) -> Dict[str, Any]:
        """
        Expõe todas as respostas para decisão humana.
        
        REGRA CARDINAL: Nunca sintetiza. Nunca faz majority vote.
        
        Args:
            responses: Dict com respostas de cada backend
            divergence_result: Resultado da análise de divergência
            
        Returns:
            Estrutura para apresentação ao humano
        """
        return {
            "responses": {
                "claude": responses.get("claude"),
                "gpt": responses.get("gpt"),
                "gemini": responses.get("gemini"),
            },
            "divergence": {
                "pattern": divergence_result.divergence_pattern,
                "outlier": divergence_result.outlier,
                "normative_conflicts": divergence_result.normative_conflicts,
                "summary": divergence_result.audit_summary,
            },
            # PROIBIDO - Estas chaves são sempre None/False
            "synthesis": None,
            "merged_response": None,
            "majority_vote": None,
            "auto_selected": False,
            # OBRIGATÓRIO
            "decision_authority": "HUMAN",
            "action_required": "SELECT_OR_REJECT_ALL",
        }
    
    def format_for_human(self, result: TriDivergenceResult) -> str:
        """Format result for human review."""
        icons = {
            "ALL_AGREE": "✅",
            "TWO_VS_ONE": "⚠️",
            "ALL_DIFFER": "🚨",
            "PARTIAL": "❓"
        }
        
        icon = icons.get(result.divergence_pattern, "❓")
        
        lines = [
            f"{icon} TRI-DIVERGENCE: {result.divergence_pattern}",
            f"Normative conflicts: {result.normative_conflicts}/3 pairs",
        ]
        
        if result.outlier:
            lines.append(f"Outlier: {result.outlier.upper()}")
        
        lines.append(f"Summary: {result.audit_summary}")
        lines.append(f"Human review: {'REQUIRED' if result.requires_human else 'Optional'}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("WINDI TRI-DIVERGENCE DETECTOR - Module loaded")
    print("=" * 60)
    
    # Mock base detector for testing
    class MockBaseDetector:
        def detect(self, a, b):
            class Result:
                divergence_type = "STYLISTIC"
                semantic_overlap = 0.5
            return Result()
    
    detector = TriDivergenceDetector(MockBaseDetector())
    
    result = detector.detect(
        "Response from Claude",
        "Response from GPT",
        "Response from Gemini"
    )
    
    print(f"\nTest result:")
    print(f"  Pattern: {result.divergence_pattern}")
    print(f"  Conflicts: {result.normative_conflicts}")
    print(f"  Requires human: {result.requires_human}")
    
    print("\n" + "=" * 60)
    print("Maioria não resolve. Humano decide.")
    print("=" * 60)
