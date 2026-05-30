"""
W-HIOS B4 — camada SPINE-CAST (continuidade multi-personagem)
=============================================================
Assenta por cima de spine.py SEM o alterar. Resolve o problema do "maior rosto":
numa cena com elenco (ex. S21 — Marcus à frente, Elisa ao fundo), medir só o
maior rosto mede a pessoa errada. Esta camada mede CADA rosto detetado contra
CADA âncora do elenco e atribui cada rosto à identidade certa.

Princípio de atribuição (com PISO DE IDENTIDADE):
  - Para cada rosto, calcula cosine contra todas as âncoras.
  - Atribui à âncora de maior cosine SE esse cosine >= IDENTITY_FLOOR.
  - Abaixo do piso: rosto fica UNIDENTIFIED (não se força a uma âncora).
    Isto evita atribuir, p.ex., o Marcus à Elisa só por vaga semelhança.

Invariantes herdados (de spine.py):
  - I14: rosto ilegível / cena sem rostos => falha explícita, sem veredicto inventado.
  - I11: resultado serializável para o Ledger.
  - I9: esta camada MEDE e ATRIBUI; não regenera. Quem regenera é o Human Dragon.

Deploy no Server B sob GOLDEN RULE (venv isolado, READ FIRST, sem tocar selados).

Liga IA+H · WINDI Publishing House · 2026
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional
import numpy as np

try:
    # Quando importado como módulo
    from .spine import cosine, classify, Verdict, THRESHOLD_OP, THRESHOLD_FORENSE
except ImportError:
    # Quando corrido directamente (python3 spine_cast.py)
    from spine import cosine, classify, Verdict, THRESHOLD_OP, THRESHOLD_FORENSE

# Piso de identidade: abaixo disto, um rosto NÃO é atribuído a nenhuma âncora.
# Deliberadamente >= ao gate operacional: para reivindicar uma identidade é
# preciso pelo menos a confiança operacional. Configurável pelo Human Dragon.
IDENTITY_FLOOR = 0.65

UNIDENTIFIED = "UNIDENTIFIED"


@dataclass
class FaceAssignment:
    """Um rosto detetado numa cena, atribuído (ou não) a uma âncora do elenco."""
    face_idx: int                       # índice do rosto no frame (ordem de deteção)
    bbox_area: float                    # área da bounding box (tamanho na imagem)
    assigned_to: str                    # character_id ou UNIDENTIFIED
    best_cosine: float                  # cosine com a âncora atribuída (ou o melhor)
    verdict: Verdict                    # veredicto SE atribuído; senão REJECT
    all_scores: dict[str, float] = field(default_factory=dict)  # cosine vs cada âncora

    def to_ledger(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["best_cosine"] = round(self.best_cosine, 4)
        d["bbox_area"] = round(self.bbox_area, 1)
        d["all_scores"] = {k: round(v, 4) for k, v in self.all_scores.items()}
        return d


@dataclass
class CharacterPresence:
    """Presença e fidelidade de UM personagem numa cena."""
    character_id: str
    present: bool                       # foi atribuído algum rosto a este personagem?
    cosine: Optional[float]             # melhor cosine do rosto atribuído
    verdict: Verdict
    bbox_area: Optional[float] = None   # tamanho do rosto (proeminência na cena)
    reason: str = ""

    def to_ledger(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        if d["cosine"] is not None:
            d["cosine"] = round(d["cosine"], 4)
        if d["bbox_area"] is not None:
            d["bbox_area"] = round(d["bbox_area"], 1)
        return d


def assign_faces(
    face_embeddings: list[tuple[float, np.ndarray]],
    cast_anchors: dict[str, np.ndarray],
    identity_floor: float = IDENTITY_FLOOR,
) -> list[FaceAssignment]:
    """
    Atribui cada rosto detetado num frame à âncora do elenco que melhor combina.

    face_embeddings: lista de (bbox_area, embedding) — um por rosto detetado.
                     (A camada facial deve devolver TODOS os rostos, não só o maior.)
    cast_anchors:    {character_id: anchor_embedding} — o elenco com âncora.

    Devolve uma FaceAssignment por rosto. Rostos abaixo do piso => UNIDENTIFIED.
    """
    assignments: list[FaceAssignment] = []
    for idx, (area, emb) in enumerate(face_embeddings):
        scores = {cid: cosine(emb, anc) for cid, anc in cast_anchors.items()}
        if not scores:
            best_id, best_score = UNIDENTIFIED, 0.0
        else:
            best_id = max(scores, key=scores.get)
            best_score = scores[best_id]

        if best_score >= identity_floor:
            verdict = classify(best_score)
            assigned = best_id
        else:
            verdict = Verdict.REJECT
            assigned = UNIDENTIFIED

        assignments.append(FaceAssignment(
            face_idx=idx,
            bbox_area=area,
            assigned_to=assigned,
            best_cosine=best_score,
            verdict=verdict,
            all_scores=scores,
        ))
    return assignments


def measure_scene_cast(
    scene_id: str,
    face_embeddings: list[tuple[float, np.ndarray]],
    cast_anchors: dict[str, np.ndarray],
    expected_characters: Optional[list[str]] = None,
    identity_floor: float = IDENTITY_FLOOR,
) -> dict:
    """
    Mede a continuidade de TODOS os personagens esperados numa cena.

    expected_characters: quem o canon diz que DEVE estar na cena. Permite
                         detectar ausências (esperado mas não encontrado) e
                         presenças não-atribuídas (rosto sem âncora => UNIDENTIFIED).

    Resolve o bug do "maior rosto": cada personagem é medido pelo rosto que
    REALMENTE lhe corresponde, não pelo rosto mais proeminente da cena.
    """
    if not face_embeddings:
        return {
            "scene_id": scene_id,
            "verdict": Verdict.FAIL_NO_FACE.value,
            "reason": "I14: nenhum rosto detectado na cena — sem veredicto.",
            "characters": [],
            "faces": [],
        }

    assignments = assign_faces(face_embeddings, cast_anchors, identity_floor)

    # Para cada personagem, escolher o melhor rosto que lhe foi atribuído.
    presences: list[CharacterPresence] = []
    cast_ids = expected_characters if expected_characters is not None else list(cast_anchors.keys())
    for cid in cast_ids:
        mine = [a for a in assignments if a.assigned_to == cid]
        if not mine:
            presences.append(CharacterPresence(
                character_id=cid, present=False, cosine=None,
                verdict=Verdict.FAIL_NO_FACE,
                reason="esperado no canon mas nenhum rosto atribuído — ausente ou abaixo do piso.",
            ))
            continue
        best = max(mine, key=lambda a: a.best_cosine)
        if best.verdict == Verdict.FORENSE:
            reason = f"cosine {best.best_cosine:.4f} >= {THRESHOLD_FORENSE} — fidelidade forense."
        elif best.verdict == Verdict.OPERACIONAL:
            reason = f"cosine {best.best_cosine:.4f} operacional; abaixo do gate forense."
        else:
            reason = f"cosine {best.best_cosine:.4f} — atribuído mas fraco."
        presences.append(CharacterPresence(
            character_id=cid, present=True, cosine=best.best_cosine,
            verdict=best.verdict, bbox_area=best.bbox_area, reason=reason,
        ))

    unidentified = [a for a in assignments if a.assigned_to == UNIDENTIFIED]

    return {
        "scene_id": scene_id,
        "characters": [p.to_ledger() for p in presences],
        "faces": [a.to_ledger() for a in assignments],
        "n_unidentified": len(unidentified),
        "identity_floor": identity_floor,
    }


# ── Testes unitários (correm sem o modelo) ───────────────────────────────────
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("SPINE-CAST B4 — Testes de Atribuição Multi-Personagem (sem modelo)")
    print("=" * 70)

    def make_embedding(target_cosine: float, anchor: np.ndarray) -> np.ndarray:
        """Cria embedding sintético com cosine-alvo aproximado contra âncora."""
        ortho = np.random.randn(512)
        ortho = ortho - np.dot(ortho, anchor) * anchor
        ortho = ortho / np.linalg.norm(ortho)
        theta = np.arccos(np.clip(target_cosine, -1, 1))
        emb = np.cos(theta) * anchor + np.sin(theta) * ortho
        return emb / np.linalg.norm(emb)

    # Âncoras do elenco (sintéticas)
    np.random.seed(42)
    anchor_elisa = np.random.randn(512)
    anchor_elisa = anchor_elisa / np.linalg.norm(anchor_elisa)

    np.random.seed(123)
    anchor_marcus = np.random.randn(512)
    anchor_marcus = anchor_marcus / np.linalg.norm(anchor_marcus)

    cast_anchors = {
        "elisa": anchor_elisa,
        "marcus": anchor_marcus,
    }

    tests_passed = 0
    tests_total = 0

    # Teste 1: Cenário S21 — Marcus grande à frente, Elisa pequena ao fundo
    print("\n[Teste 1] S21 — Marcus à frente (grande), Elisa ao fundo (pequena)...")
    tests_total += 1

    # Marcus: rosto grande (45000 px²), high cosine com anchor_marcus
    emb_marcus = make_embedding(0.88, anchor_marcus)
    # Elisa: rosto pequeno (6000 px²), operacional cosine com anchor_elisa
    emb_elisa = make_embedding(0.71, anchor_elisa)

    face_embeddings = [
        (45000.0, emb_marcus),  # Marcus à frente
        (6000.0, emb_elisa),    # Elisa ao fundo
    ]

    result = measure_scene_cast("S21", face_embeddings, cast_anchors, ["elisa", "marcus"])

    elisa_presence = next((c for c in result["characters"] if c["character_id"] == "elisa"), None)
    marcus_presence = next((c for c in result["characters"] if c["character_id"] == "marcus"), None)

    if (elisa_presence and elisa_presence["present"] and
        marcus_presence and marcus_presence["present"] and
        elisa_presence["verdict"] == "OPERACIONAL" and
        marcus_presence["verdict"] == "FORENSE"):
        print(f"  ✓ Elisa: {elisa_presence['cosine']:.4f} ({elisa_presence['verdict']})")
        print(f"  ✓ Marcus: {marcus_presence['cosine']:.4f} ({marcus_presence['verdict']})")
        print(f"  ✓ Bug do 'maior rosto' resolvido — cada personagem medido correctamente!")
        tests_passed += 1
    else:
        print(f"  ✗ Atribuição incorrecta: {result}")

    # Teste 2: Piso de identidade — intruso louro não deve ser atribuído à Elisa
    print("\n[Teste 2] Intruso louro (cosine 0.52) não deve ser forçado a Elisa...")
    tests_total += 1

    # Intruso com vaga semelhança à Elisa (0.52 < 0.65 floor)
    emb_intruso = make_embedding(0.52, anchor_elisa)
    face_embeddings = [(10000.0, emb_intruso)]

    result = measure_scene_cast("test", face_embeddings, cast_anchors, ["elisa"])

    elisa_presence = next((c for c in result["characters"] if c["character_id"] == "elisa"), None)
    intruso_face = result["faces"][0] if result["faces"] else None

    if (elisa_presence and not elisa_presence["present"] and
        intruso_face and intruso_face["assigned_to"] == UNIDENTIFIED):
        print(f"  ✓ Intruso ficou UNIDENTIFIED (cosine {intruso_face['best_cosine']:.4f} < 0.65)")
        print(f"  ✓ Elisa marcada como ausente (não forçada)")
        tests_passed += 1
    else:
        print(f"  ✗ Intruso deveria ser UNIDENTIFIED: {result}")

    # Teste 3: Personagem esperado mas ausente
    print("\n[Teste 3] Personagem esperado mas não encontrado...")
    tests_total += 1

    # Cena só com Marcus, mas esperamos Elisa também
    emb_marcus_only = make_embedding(0.85, anchor_marcus)
    face_embeddings = [(30000.0, emb_marcus_only)]

    result = measure_scene_cast("test", face_embeddings, cast_anchors, ["elisa", "marcus"])

    elisa_presence = next((c for c in result["characters"] if c["character_id"] == "elisa"), None)
    marcus_presence = next((c for c in result["characters"] if c["character_id"] == "marcus"), None)

    if (elisa_presence and not elisa_presence["present"] and
        marcus_presence and marcus_presence["present"]):
        print(f"  ✓ Elisa: present=False (esperada mas não encontrada)")
        print(f"  ✓ Marcus: present=True, {marcus_presence['cosine']:.4f} ({marcus_presence['verdict']})")
        tests_passed += 1
    else:
        print(f"  ✗ Detecção de ausência falhou: {result}")

    # Teste 4: I14 — cena sem rostos
    print("\n[Teste 4] I14 — cena sem rostos...")
    tests_total += 1

    result = measure_scene_cast("empty", [], cast_anchors, ["elisa"])

    if result["verdict"] == Verdict.FAIL_NO_FACE.value and "I14" in result["reason"]:
        print(f"  ✓ FAIL_NO_FACE com razão I14")
        tests_passed += 1
    else:
        print(f"  ✗ Deveria ser FAIL_NO_FACE: {result}")

    # Teste 5: Serialização Ledger
    print("\n[Teste 5] Serialização para Ledger...")
    tests_total += 1

    emb_e = make_embedding(0.80, anchor_elisa)
    face_embeddings = [(20000.0, emb_e)]
    result = measure_scene_cast("test", face_embeddings, cast_anchors, ["elisa"])

    # Verificar que é serializável JSON
    import json
    try:
        json_str = json.dumps(result)
        if "characters" in result and "faces" in result:
            print(f"  ✓ Payload serializável correctamente ({len(json_str)} bytes)")
            tests_passed += 1
        else:
            print(f"  ✗ Campos em falta no payload")
    except Exception as e:
        print(f"  ✗ Erro de serialização: {e}")

    # Teste 6: all_scores mostra comparação contra todas as âncoras
    print("\n[Teste 6] all_scores inclui comparação com todas as âncoras...")
    tests_total += 1

    emb_e = make_embedding(0.78, anchor_elisa)
    face_embeddings = [(20000.0, emb_e)]
    result = measure_scene_cast("test", face_embeddings, cast_anchors)

    face = result["faces"][0] if result["faces"] else {}
    if "all_scores" in face and "elisa" in face["all_scores"] and "marcus" in face["all_scores"]:
        print(f"  ✓ all_scores: elisa={face['all_scores']['elisa']:.4f}, marcus={face['all_scores']['marcus']:.4f}")
        tests_passed += 1
    else:
        print(f"  ✗ all_scores incompleto: {face}")

    # Resumo
    print("\n" + "=" * 70)
    print(f"RESULTADOS: {tests_passed}/{tests_total} testes passaram")
    print("=" * 70)

    sys.exit(0 if tests_passed == tests_total else 1)
