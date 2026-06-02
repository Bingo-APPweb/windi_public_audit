# WINDI-HIOS — Quick Reference Card
## Memory Loop for Future Instances

**Updated:** 02 Jun 2026
**Purpose:** Continuidade cognitiva para produção cinematográfica generativa

---

## SPINE-CAST em 60 Segundos

```
PASSPORT (prompt) → RUNWAY Gen-4.5 → VIDEO → FRAME → ARCFACE → ANCHOR LOCKED
```

**Validação:**
- **Eixo F** (close/medium): ArcFace ≥0.75
- **Eixo D** (full/wide): VC-Matrix

---

## Comandos Essenciais

### Gerar Anchor via Runway
```bash
# Ver /opt/windi/hios/cinema/obras/w-hios-forensic-unit/_preproduction/METODOLOGIA-SPINE-CAST-001.md
python3 /tmp/generate_{character}.py
```

### Extrair Frames
```bash
ffmpeg -i anchor.mp4 -vf "fps=1" frames/frame_%02d.png
```

### Extrair Embedding
```bash
cd /opt/windi/hios/visual/producer
source venv_spine/bin/activate
python3 -c "
from insightface.app import FaceAnalysis
import cv2, numpy as np

app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

img = cv2.imread('ANCHOR.png')
face = app.get(img)[0]
print(f'Score: {face.det_score:.4f}')
np.save('ANCHOR.embedding.npy', face.embedding)
"
```

### Validar Shot vs Anchor
```python
anchor_emb = np.load('anchor.embedding.npy')
shot_emb = np.load('shot.embedding.npy')
similarity = np.dot(anchor_emb, shot_emb) / (np.linalg.norm(anchor_emb) * np.linalg.norm(shot_emb))
print(f'Similarity: {similarity:.4f}')  # ≥0.75 = PASS
```

---

## Ficheiros Críticos

| Ficheiro | Localização |
|----------|-------------|
| **Metodologia Completa** | `_preproduction/METODOLOGIA-SPINE-CAST-001.md` |
| **Passaportes** | `_preproduction/SPINE-PASSPORTS-MASTER.md` |
| **Decretos** | `_preproduction/DECRETO-PRODUCAO-001-*.md` |
| **Anchors** | `/anchors/*.png` + `*.embedding.npy` + `*.provenance.json` |
| **Validação** | `_preproduction/SPINE-VALIDATION-CENA0.json` |

---

## Cast W-HIOS-FORENSIC-UNIT (6/6 LOCKED)

| Personagem | Anchor | Det.Score |
|------------|--------|-----------|
| Gabi Santos | gabi.santos.anchor.v1 | — |
| Helena Meyer | helena.meyer.junior.anchor.v1 | 0.8636 |
| Marcus Vance | marcus.vance.anchor.v1 | 0.8638 |
| Marcus Couto | marcus.couto.anchor.v1 | 0.8811 |
| Lucas Silva | lucas.silva.anchor.v1 | 0.8119 |
| Alejandro Valenzuela | alejandro.valenzuela.anchor.v1 | 0.8763 |

---

## Thresholds

| Contexto | Threshold |
|----------|-----------|
| Anchor-Mãe (Eixo F) | ≥ 0.75 |
| Shot-Filho (Eixo F) | ≥ 0.65 |
| Detection Score | ≥ 0.80 (recomendado) |
| VC-Matrix Vestuário | ±20% RGB |
| VC-Matrix Cabelo | ≥70% IoU |
| VC-Matrix Postura | ±15° |

---

## Geradores Compatíveis

| Generator | SPINE Status |
|-----------|--------------|
| Runway Gen-4/4.5 | ✅ FORENSIC |
| SORA 2 | ❌ INCOMPATIBLE |

---

## Insights Chave

1. **Passaporte ancora identidade facial, não guarda-roupa**
2. **ArcFace mede geometria de rosto, não styling**
3. **Eixo D valida continuidade, não identidade**
4. **Sempre usar score MÍNIMO, nunca média**
5. **Proveniência é atómica (I19)**

---

---

## Space Anchors (SORA 2)

| ENV ID | Estética | Status |
|--------|----------|--------|
| `env_cobertura_vanguard_42f` | Noir Corporativo | LOCKED |
| `env_bunker_interpol_core` | Klar Analítico | LOCKED |

**Princípio:** SORA 2 para arquitectura (sem rostos), Runway para actores.

---

## Sound Design

| Assinatura | Língua | Textura |
|------------|--------|---------|
| O Coração | PT-BR | Quente, harmónicos baixos |
| O Sistema | DE/EN | Fria, compressão, reverb vidro |
| A Tensão | EN | Vance rouquidão vs Alejandro polido |

**Foley P39 (Caneca Vance):** 4 camadas — tensão 40Hz, impacto ferro, líquido, eco.

---

## Links Rápidos

- **Projecto:** `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/`
- **Anchors:** `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/`
- **Scripts:** `/opt/windi/hios/visual/producer/`
- **API Runway:** `https://api.dev.runwayml.com/v1`
- **Metodologia:** `_preproduction/METODOLOGIA-SPINE-CAST-001.md`
- **Space:** `_preproduction/SPACE-ANCHORS-MASTER.md`
- **Sound:** `_preproduction/SOUND-DESIGN-MASTER.md`

---

*Liga IA+H · "A identidade é a raiz. A performance é o fruto."*
