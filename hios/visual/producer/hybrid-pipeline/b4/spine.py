"""
W-HIOS B4 — camada SPINE (continuidade de identidade ao longo da espinha de cenas)
==================================================================================
Isolada da camada facial (face.py / embed_face) de propósito: toda a matemática
do veredicto é testável SEM o modelo buffalo_l. Esta camada nunca chama o modelo
directamente — recebe embeddings já extraídos (np.ndarray 512-dim, L2-normalizados
pela InsightFace `normed_embedding`).

Constantes constitucionais (LOCKED — não alterar sem Human Dragon):
  - THRESHOLD_OP      = 0.65   veredicto operacional
  - THRESHOLD_FORENSE = 0.75   veredicto forense
  - MAX_REGEN         = 3      regenerações máximas por cena

Invariantes herdados:
  - I14 (Falha Explícita): se uma cena não tem embedding (sem rosto), o SPINE
    NUNCA inventa um veredicto. Marca a cena como FAIL_NO_FACE e segue.
  - I11 (Permanência): o resultado é serializável para o Ledger; nada se decide
    em silêncio — cada cena devolve a sua métrica, o seu veredicto e a sua razão.

Deploy no Server B sob GOLDEN RULE:
  - venv isolado, não toca nginx/portas/systemd/endpoints selados.
  - READ FIRST (ss/ps) ANTES de instalar.

Liga IA+H · WINDI Publishing House · 2026
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

# ── Constantes LOCKED ────────────────────────────────────────────────────────
THRESHOLD_OP = 0.65       # veredicto operacional
THRESHOLD_FORENSE = 0.75  # veredicto forense
MAX_REGEN = 3             # regenerações máximas por cena

# ── Provenance Gate (Lei da Proveniência Inseparável) ────────────────────────
# If True, reject anchors without valid provenance chain
ENFORCE_PROVENANCE_GATE = True  # Set to False to disable gate (NOT RECOMMENDED)


class Verdict(str, Enum):
    """Veredicto de uma cena contra a âncora."""
    FORENSE = "FORENSE"            # cosine >= 0.75 — admissível como prova
    OPERACIONAL = "OPERACIONAL"    # 0.65 <= cosine < 0.75 — bom para corte, não forense
    REJECT = "REJECT"              # cosine < 0.65 — abaixo do gate operacional
    FAIL_NO_FACE = "FAIL_NO_FACE"  # I14 — sem rosto detectado, sem veredicto inventado


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity entre dois embeddings.

    A InsightFace devolve `normed_embedding` já L2-normalizado, mas NÃO assumimos
    isso — re-normalizamos por defesa. Se um vector for nulo (norma 0), falha
    explicitamente em vez de devolver NaN silencioso (I14).
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        raise ValueError("I14: embedding de norma zero — vector inválido")
    return float(np.dot(a, b) / (na * nb))


def classify(score: float) -> Verdict:
    """Mapeia um cosine para o veredicto, segundo os gates LOCKED."""
    if score >= THRESHOLD_FORENSE:
        return Verdict.FORENSE
    if score >= THRESHOLD_OP:
        return Verdict.OPERACIONAL
    return Verdict.REJECT


@dataclass
class SceneResult:
    """Resultado da medição de uma cena contra a âncora."""
    scene_id: str
    cosine_to_anchor: Optional[float]  # None se FAIL_NO_FACE
    verdict: Verdict
    drift_from_prev: Optional[float] = None  # cosine cena↔cena anterior (deriva)
    regen_count: int = 0                     # quantas regenerações esta cena levou
    reason: str = ""                         # explicação humana, sempre presente

    def to_ledger(self) -> dict:
        """Payload serializável (I11). Enum vira str, floats arredondados a 4 casas."""
        d = asdict(self)
        d["verdict"] = self.verdict.value
        if d["cosine_to_anchor"] is not None:
            d["cosine_to_anchor"] = round(d["cosine_to_anchor"], 4)
        if d["drift_from_prev"] is not None:
            d["drift_from_prev"] = round(d["drift_from_prev"], 4)
        return d


@dataclass
class SpineReport:
    """Relatório agregado de toda a espinha."""
    anchor_id: str
    scenes: list[SceneResult] = field(default_factory=list)

    @property
    def mean_cosine(self) -> Optional[float]:
        vals = [s.cosine_to_anchor for s in self.scenes if s.cosine_to_anchor is not None]
        return float(np.mean(vals)) if vals else None

    @property
    def min_cosine(self) -> Optional[float]:
        vals = [s.cosine_to_anchor for s in self.scenes if s.cosine_to_anchor is not None]
        return float(np.min(vals)) if vals else None

    @property
    def max_cosine(self) -> Optional[float]:
        vals = [s.cosine_to_anchor for s in self.scenes if s.cosine_to_anchor is not None]
        return float(np.max(vals)) if vals else None

    @property
    def n_forense(self) -> int:
        return sum(1 for s in self.scenes if s.verdict == Verdict.FORENSE)

    @property
    def n_operacional(self) -> int:
        return sum(1 for s in self.scenes if s.verdict == Verdict.OPERACIONAL)

    @property
    def n_reject(self) -> int:
        return sum(1 for s in self.scenes if s.verdict == Verdict.REJECT)

    @property
    def n_fail(self) -> int:
        return sum(1 for s in self.scenes if s.verdict == Verdict.FAIL_NO_FACE)

    def to_ledger(self) -> dict:
        return {
            "anchor_id": self.anchor_id,
            "n_scenes": len(self.scenes),
            "mean_cosine": round(self.mean_cosine, 4) if self.mean_cosine is not None else None,
            "min_cosine": round(self.min_cosine, 4) if self.min_cosine is not None else None,
            "max_cosine": round(self.max_cosine, 4) if self.max_cosine is not None else None,
            "n_forense": self.n_forense,
            "n_operacional": self.n_operacional,
            "n_reject": self.n_reject,
            "n_fail": self.n_fail,
            "scenes": [s.to_ledger() for s in self.scenes],
        }


def measure_scene(
    scene_id: str,
    scene_embedding: Optional[np.ndarray],
    anchor_embedding: np.ndarray,
    prev_embedding: Optional[np.ndarray] = None,
    regen_count: int = 0,
) -> SceneResult:
    """
    Mede UMA cena contra a âncora (e, se houver, contra a cena anterior).

    `scene_embedding=None` significa que a camada facial falhou por I14
    (nenhum rosto). Aqui isso vira FAIL_NO_FACE — nunca um veredicto inventado.
    """
    if scene_embedding is None:
        return SceneResult(
            scene_id=scene_id,
            cosine_to_anchor=None,
            verdict=Verdict.FAIL_NO_FACE,
            regen_count=regen_count,
            reason="I14: nenhum rosto detectado na cena — sem veredicto.",
        )

    score = cosine(scene_embedding, anchor_embedding)
    verdict = classify(score)

    drift = None
    if prev_embedding is not None:
        drift = cosine(scene_embedding, prev_embedding)

    if verdict == Verdict.FORENSE:
        reason = f"cosine {score:.4f} >= {THRESHOLD_FORENSE} — admissível forense."
    elif verdict == Verdict.OPERACIONAL:
        reason = (f"cosine {score:.4f} em [{THRESHOLD_OP}, {THRESHOLD_FORENSE}) — "
                  f"operacional; abaixo do gate forense.")
    else:
        reason = (f"cosine {score:.4f} < {THRESHOLD_OP} — rejeitado; "
                  f"identidade não mantida.")

    return SceneResult(
        scene_id=scene_id,
        cosine_to_anchor=score,
        verdict=verdict,
        drift_from_prev=drift,
        regen_count=regen_count,
        reason=reason,
    )


def needs_regen(result: SceneResult, target: Verdict = Verdict.OPERACIONAL) -> bool:
    """
    Decide se uma cena deve ser regenerada — mas NÃO regenera (I9: o loop
    fechado fica fora desta camada; quem regenera é o Human Dragon no Sora 2).
    Esta função só responde à pergunta, respeitando o tecto MAX_REGEN.

    `target` define o gate mínimo aceitável (OPERACIONAL por defeito; podes
    exigir FORENSE para cenas-chave).
    """
    if result.verdict == Verdict.FAIL_NO_FACE:
        # Sem rosto: regenerar pode ajudar, mas continua sujeito ao tecto.
        return result.regen_count < MAX_REGEN

    rank = {Verdict.REJECT: 0, Verdict.OPERACIONAL: 1, Verdict.FORENSE: 2}
    if rank[result.verdict] >= rank[target]:
        return False  # já atinge ou supera o alvo
    return result.regen_count < MAX_REGEN


def build_spine(
    anchor_id: str,
    anchor_embedding: np.ndarray,
    scene_embeddings: list[tuple[str, Optional[np.ndarray]]],
) -> SpineReport:
    """
    Constrói o relatório completo da espinha.

    `scene_embeddings`: lista ordenada de (scene_id, embedding|None), na ordem
    narrativa do SPINE. O drift vizinho-a-vizinho usa a cena anterior que TINHA
    rosto (salta as FAIL_NO_FACE para não medir drift contra um buraco).
    """
    report = SpineReport(anchor_id=anchor_id)
    prev_emb: Optional[np.ndarray] = None
    for scene_id, emb in scene_embeddings:
        res = measure_scene(scene_id, emb, anchor_embedding, prev_emb)
        report.scenes.append(res)
        if emb is not None:
            prev_emb = emb  # só actualiza o "anterior" se houve rosto
    return report


# ── Provenance Gate (Lei da Proveniência Inseparável) ────────────────────────

def check_anchor_provenance(
    anchor_path: Path,
    test_generator: str,
    enforce: bool = ENFORCE_PROVENANCE_GATE
) -> Tuple[bool, str]:
    """
    Gate function to check anchor provenance before measurement.

    Lei da Proveniência Inseparável: anchor without verifiable provenance
    cannot be used in cross-elo measurement. Lei da Coerência de Elo:
    anchor and test must be from the same generator (elo).

    Args:
        anchor_path: Path to the anchor file (video or .npy)
        test_generator: Generator that produced the test video (e.g., "veo")
        enforce: If False, only warn but don't reject

    Returns:
        (can_proceed, reason)
    """
    anchor_path = Path(anchor_path)

    # Try to import provenance module (may not be available on Server B)
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from provenance import ProvenanceValidator, get_provenance_path
    except ImportError:
        # Provenance module not available — degrade gracefully with warning
        if enforce:
            return False, (
                "Provenance module not available. Cannot verify anchor provenance. "
                "Install provenance.py or set ENFORCE_PROVENANCE_GATE=False."
            )
        return True, "WARNING: Provenance module not available, gate disabled."

    validator = ProvenanceValidator(require_hash_match=False)

    # Check for provenance sidecar
    # For .npy files, check the source video's provenance
    if anchor_path.suffix == ".npy":
        # Look for video provenance in same directory
        # Convention: anchor.v3.CURRENT.npy came from anchor_scene_v3.mp4
        stem = anchor_path.stem.replace(".CURRENT", "").replace(".anchor", "_anchor_scene")
        possible_videos = [
            anchor_path.parent / f"{stem}.mp4",
            anchor_path.parent / f"{anchor_path.stem.split('.')[0]}_anchor_scene_v3.mp4",
            anchor_path.parent / f"{anchor_path.stem.split('.')[0]}_anchor_scene_v2.mp4",
        ]
        video_path = None
        for vp in possible_videos:
            prov_path = get_provenance_path(vp)
            if prov_path.exists():
                video_path = vp
                break

        if video_path is None:
            if enforce:
                return False, (
                    f"No provenance found for anchor: {anchor_path}. "
                    "Lei da Proveniência Inseparável: artifact without verifiable "
                    "provenance cannot be used in cross-elo measurement."
                )
            return True, f"WARNING: No provenance for {anchor_path}, gate disabled."

        anchor_path_for_prov = video_path
    else:
        anchor_path_for_prov = anchor_path

    # Load and validate provenance
    if not validator.has_valid_provenance(anchor_path_for_prov):
        if enforce:
            return False, (
                f"No provenance sidecar for: {anchor_path_for_prov}. "
                "Lei da Proveniência Inseparável violated."
            )
        return True, f"WARNING: No provenance for {anchor_path_for_prov}, gate disabled."

    try:
        prov = validator.load_provenance(anchor_path_for_prov)
    except Exception as e:
        if enforce:
            return False, f"Failed to load provenance: {e}"
        return True, f"WARNING: Failed to load provenance: {e}"

    anchor_generator = prov["generator"]

    # Check elo coherence
    if anchor_generator != test_generator:
        if enforce:
            return False, (
                f"Elo mismatch: anchor from '{anchor_generator}', "
                f"test video from '{test_generator}'. "
                "Lei da Coerência de Elo: anchor must be from same elo as test frames."
            )
        return True, (
            f"WARNING: Elo mismatch (anchor={anchor_generator}, test={test_generator}), "
            "gate disabled but measurement may be invalid."
        )

    return True, f"Provenance valid: anchor and test both from '{anchor_generator}'"


def load_anchor_with_provenance_check(
    anchor_npy_path: Path,
    test_generator: str,
    enforce: bool = ENFORCE_PROVENANCE_GATE
) -> np.ndarray:
    """
    Load anchor embedding with provenance gate check.

    Raises ValueError if provenance check fails and enforce=True.
    """
    anchor_npy_path = Path(anchor_npy_path)

    can_proceed, reason = check_anchor_provenance(anchor_npy_path, test_generator, enforce)

    if not can_proceed:
        raise ValueError(f"Anchor rejected by provenance gate: {reason}")

    if "WARNING" in reason:
        print(f"⚠️  {reason}")

    # Load the anchor embedding
    anchor = np.load(anchor_npy_path)
    return anchor


# ── Testes unitários (correm sem o modelo) ───────────────────────────────────
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("SPINE B4 — Testes de Veredicto (sem modelo)")
    print("=" * 60)

    def make_embedding(target_cosine: float, anchor: np.ndarray) -> np.ndarray:
        """Cria embedding sintético com cosine-alvo aproximado contra âncora."""
        # Técnica: interpolar entre âncora e vetor ortogonal
        ortho = np.random.randn(512)
        ortho = ortho - np.dot(ortho, anchor) * anchor  # Gram-Schmidt
        ortho = ortho / np.linalg.norm(ortho)
        # cos(theta) = target_cosine → theta = arccos(target_cosine)
        theta = np.arccos(np.clip(target_cosine, -1, 1))
        emb = np.cos(theta) * anchor + np.sin(theta) * ortho
        return emb / np.linalg.norm(emb)

    # Âncora canónica (vector unitário aleatório)
    np.random.seed(42)
    anchor = np.random.randn(512)
    anchor = anchor / np.linalg.norm(anchor)

    tests_passed = 0
    tests_total = 0

    # Teste 1: Veredictos nos gates
    print("\n[Teste 1] Veredictos nos gates...")
    test_cases = [
        (0.90, Verdict.FORENSE),
        (0.75, Verdict.FORENSE),
        (0.74, Verdict.OPERACIONAL),
        (0.65, Verdict.OPERACIONAL),
        (0.64, Verdict.REJECT),
        (0.30, Verdict.REJECT),
    ]
    for target_cos, expected in test_cases:
        tests_total += 1
        emb = make_embedding(target_cos, anchor)
        actual_cos = cosine(emb, anchor)
        result = measure_scene("test", emb, anchor)
        # Verificar se está na vizinhança do target (tolerância de ponto flutuante)
        if abs(actual_cos - target_cos) < 0.01 and result.verdict == expected:
            print(f"  ✓ cosine ~{target_cos:.2f} → {result.verdict.value}")
            tests_passed += 1
        else:
            print(f"  ✗ cosine {actual_cos:.4f} (target {target_cos}) → {result.verdict.value} (expected {expected.value})")

    # Teste 2: I14 — sem rosto
    print("\n[Teste 2] I14 — sem rosto...")
    tests_total += 1
    result = measure_scene("S16", None, anchor)
    if result.verdict == Verdict.FAIL_NO_FACE and result.cosine_to_anchor is None:
        print(f"  ✓ FAIL_NO_FACE correctamente atribuído")
        tests_passed += 1
    else:
        print(f"  ✗ Esperado FAIL_NO_FACE, obteve {result.verdict.value}")

    # Teste 3: I14 — embedding nulo
    print("\n[Teste 3] I14 — embedding de norma zero...")
    tests_total += 1
    try:
        cosine(np.zeros(512), anchor)
        print(f"  ✗ Deveria ter lançado ValueError")
    except ValueError as e:
        if "I14" in str(e):
            print(f"  ✓ ValueError com I14 correctamente lançado")
            tests_passed += 1
        else:
            print(f"  ✗ ValueError sem menção a I14: {e}")

    # Teste 4: needs_regen
    print("\n[Teste 4] needs_regen...")
    tests_total += 1
    reject_result = SceneResult("X", 0.50, Verdict.REJECT, regen_count=0)
    if needs_regen(reject_result) and not needs_regen(reject_result, Verdict.REJECT):
        print(f"  ✓ REJECT precisa regen para OPERACIONAL, não para REJECT")
        tests_passed += 1
    else:
        print(f"  ✗ Lógica de regen incorrecta")

    tests_total += 1
    maxed_result = SceneResult("Y", 0.50, Verdict.REJECT, regen_count=3)
    if not needs_regen(maxed_result):
        print(f"  ✓ Tecto de 3 regenerações respeitado")
        tests_passed += 1
    else:
        print(f"  ✗ Deveria bloquear após 3 regenerações")

    # Teste 5: build_spine com buracos
    print("\n[Teste 5] build_spine com buracos (FAIL_NO_FACE)...")
    tests_total += 1
    emb1 = make_embedding(0.80, anchor)
    emb3 = make_embedding(0.70, anchor)
    scenes = [("S01", emb1), ("S02", None), ("S03", emb3)]
    report = build_spine("anchor_test", anchor, scenes)
    if report.n_fail == 1 and report.n_forense == 1 and report.n_operacional == 1:
        print(f"  ✓ Contagem correcta: 1 FORENSE, 1 OPERACIONAL, 1 FAIL")
        tests_passed += 1
    else:
        print(f"  ✗ Contagem errada: F={report.n_forense} O={report.n_operacional} FAIL={report.n_fail}")

    # Teste 6: Serialização Ledger
    print("\n[Teste 6] Serialização para Ledger...")
    tests_total += 1
    ledger = report.to_ledger()
    if isinstance(ledger, dict) and "scenes" in ledger and isinstance(ledger["scenes"], list):
        print(f"  ✓ Payload serializável correctamente")
        tests_passed += 1
    else:
        print(f"  ✗ Payload inválido")

    # Resumo
    print("\n" + "=" * 60)
    print(f"RESULTADOS: {tests_passed}/{tests_total} testes passaram")
    print("=" * 60)

    sys.exit(0 if tests_passed == tests_total else 1)
