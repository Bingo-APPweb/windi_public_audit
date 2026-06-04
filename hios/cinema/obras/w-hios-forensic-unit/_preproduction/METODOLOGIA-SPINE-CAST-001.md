# METODOLOGIA SPINE-CAST 001
## Sistema de Continuidade de Identidade Facial para Cinema Generativo

**Status:** SEALED
**Created:** 02 Jun 2026
**Version:** 1.0.0
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Invariants:** I1, I9, I11, I14, I19

---

## PREÂMBULO

> "O passaporte ancora identidade facial, não guarda-roupa."
> — Human Dragon · 02 Jun 2026

Este documento codifica a metodologia SPINE-CAST desenvolvida para produção cinematográfica generativa com continuidade de identidade verificável.

---

## 1. ARQUITECTURA CONCEPTUAL

### 1.1 Problema

Geradores de vídeo IA (Runway, SORA, Kling) não garantem consistência facial entre gerações. Cada invocação pode produzir variações que quebram a continuidade de personagem.

### 1.2 Solução

**SPINE-CAST** — Sistema de ancoragem facial que:
1. Estabelece identidade canónica (PASSPORT)
2. Extrai embedding biométrico (ANCHOR)
3. Valida cada plano gerado contra o anchor (VALIDATION)
4. Usa dois eixos de validação conforme distância de câmara

---

## 2. COMPONENTES DO SISTEMA

### 2.1 PASSPORT (Documento de Identidade)

**Definição:** Prompt textual que descreve a aparência canónica do personagem.

**Características obrigatórias:**
- Idade e etnia
- Estrutura facial (olhos, nariz, boca, maxilar)
- Textura de pele
- Cabelo (cor, estilo)
- Expressão neutra
- Iluminação flat de estúdio
- Fundo neutro

**Exemplo:**
```plaintext
Photographic portrait for character reference, a 45-year-old European
corporate man, executive security chief, impeccably slicked-back grey hair,
sharp chiseled jawline, perfectly clean-shaven face. Symmetrical facial
structure, cold piercing dark brown eyes looking directly into the camera
lens, arrogant polite neutral expression. Wearing a high-end black cashmere
tailored overcoat over a sharp corporate suit.

Flat diffuse neutral studio lighting, no shadows, 50mm lens, sharp focus
on facial anchors, cinematic photorealistic texture, zero facial distortion.
```

### 2.2 ANCHOR (Âncora Biométrica)

**Definição:** Imagem + embedding facial extraído via InsightFace/ArcFace.

**Componentes:**
| Ficheiro | Descrição |
|----------|-----------|
| `{character}.anchor.v1.png` | Imagem do rosto (frame extraído) |
| `{character}.anchor.v1.embedding.npy` | Vector 512D ArcFace |
| `{character}.anchor.v1.provenance.json` | Metadados de geração |

**Métricas de qualidade:**
| Métrica | Threshold |
|---------|-----------|
| Detection Score | ≥ 0.80 (recomendado) |
| Embedding Norm | ~15-18 (típico) |

### 2.3 VALIDATION (Sistema de Validação)

**Dois eixos de validação conforme DECRETO-001 + ADITAMENTO:**

#### EIXO F — Facial Criptográfico
| Parâmetro | Valor |
|-----------|-------|
| **Aplicação** | Close-ups, Medium shots |
| **Sujeito** | Rosto (alta densidade de pixels) |
| **Mecanismo** | ArcFace cosine similarity |
| **Threshold Anchor** | ≥ 0.75 |
| **Threshold Shot** | ≥ 0.65 |

#### EIXO D — Distância / Silhueta
| Parâmetro | Valor |
|-----------|-------|
| **Aplicação** | Full shots, Wide shots |
| **Sujeito** | Silhueta (baixa densidade facial) |
| **Mecanismo** | VC-Matrix (Visual Continuity) |
| **ArcFace** | Informativo, não gate |

---

## 3. VC-MATRIX — CRITÉRIOS DE CONTINUIDADE

Para planos onde o rosto ocupa poucos pixels:

| Critério | Limiar | Base Científica |
|----------|--------|-----------------|
| **Vestuário** | ±20% histograma RGB (máscara pessoa) | Color science ΔE~15 JND |
| **Cabelo** | ≥70% IoU silhueta | CV standard overlap |
| **Postura** | ±15° eixo vertical | Percepção humana |
| **Cenário** | Match exacto `env_*` | Binário |
| **Proporção** | ±15% altura SE de pé; N.A. SE outra pose | Mecânico |
| **Ancoragem** | Plano Eixo F adjacente obrigatório | Identidade requer prova facial |

---

## 4. PIPELINE DE GERAÇÃO

### 4.1 Fluxo Completo

```
PASSPORT (prompt)
    → Runway Gen-4.5 text-to-video (5s)
    → FFmpeg extract frames (fps=1)
    → Selecção frame_01 (ou melhor)
    → InsightFace ArcFace embedding
    → Provenance JSON
    → ANCHOR LOCKED
```

### 4.2 Comando de Geração

```python
payload = {
    "model": "gen4.5",
    "promptText": PASSPORT_PROMPT,
    "duration": 5,
    "ratio": "1280:720",
}
response = requests.post(f"{API_BASE}/text_to_video", headers=headers, json=payload)
```

### 4.3 Extracção de Frames

```bash
ffmpeg -i anchor.mp4 -vf "fps=1" frames/frame_%02d.png
```

### 4.4 Extracção de Embedding

```python
from insightface.app import FaceAnalysis
import numpy as np

app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

img = cv2.imread('anchor.png')
faces = app.get(img)
face = faces[0]

np.save('anchor.embedding.npy', face.embedding)
```

---

## 5. ESTRUTURA DE FICHEIROS

```
/opt/windi/hios/cinema/obras/{project}/anchors/
├── {character}.anchor.v1.png
├── {character}.anchor.v1.mp4           # Video fonte (opcional)
├── {character}.anchor.v1.embedding.npy
├── {character}.anchor.v1.provenance.json
└── {character}_frames/                  # Frames extraídos
    ├── frame_01.png
    ├── frame_02.png
    └── ...
```

---

## 6. PROVENANCE (I19)

Cada anchor DEVE ter proveniência atómica:

```json
{
  "anchor_id": "marcus.couto.anchor.v1",
  "passport_id": "marcus.couto.passport.v1",
  "character": "Marcus Couto",
  "project": "w-hios-forensic-unit",

  "source": {
    "method": "text-to-video",
    "generator": "Runway Gen-4.5",
    "video_file": "marcus.couto.anchor.v1.mp4",
    "frame_extracted": "frame_01.png",
    "generation_date": "2026-06-02",
    "task_id": "runway-task-id"
  },

  "anchor": {
    "file": "marcus.couto.anchor.v1.png",
    "hash": "sha256:...",
    "embedding_file": "marcus.couto.anchor.v1.embedding.npy",
    "embedding_norm": 16.8419,
    "detection_score": 0.8811,
    "validator": "InsightFace ArcFace-R100 (buffalo_l)"
  },

  "invariants": ["I9", "I11", "I14", "I19"],
  "status": "LOCKED",
  "approved_by": "Human Dragon",
  "created": "2026-06-02T19:26:00Z"
}
```

---

## 7. VALIDAÇÃO DE PLANOS

### 7.1 Comparação Pairwise

```python
def validate_shot(anchor_embedding, shot_image):
    """Validate shot against anchor."""
    faces = app.get(shot_image)
    if not faces:
        return {"status": "NO_FACE", "score": 0}

    shot_embedding = faces[0].embedding

    # Cosine similarity
    similarity = np.dot(anchor_embedding, shot_embedding) / (
        np.linalg.norm(anchor_embedding) * np.linalg.norm(shot_embedding)
    )

    if similarity >= 0.75:
        return {"status": "PASSED_ANCHOR", "score": similarity}
    elif similarity >= 0.65:
        return {"status": "PASSED_SHOT", "score": similarity}
    else:
        return {"status": "FAILED", "score": similarity}
```

### 7.2 Regra do Mínimo

> **SEMPRE usar o score MÍNIMO para classificação de tier, nunca a média.**

Se um personagem tem 4 planos com scores [0.93, 0.84, 0.76, 0.72], o MIN é 0.72.

---

## 8. INSIGHTS EPISTEMOLÓGICOS

### 8.1 Identidade vs Guarda-Roupa

> "Uma foto de documento é antiga e ligeiramente difere da imagem de hoje.
> O que importa são os traços invariantes: olhos, nariz, boca, textura de pele.
> Se está de cabelo preso ou solto é indiferente."
> — Human Dragon · 02 Jun 2026

**Corolário:** O passport spec descreve aparência ideal para geração, mas a validação foca em geometria facial, não em styling.

### 8.2 ArcFace Mede Rosto, Não Personagem

O embedding ArcFace é prisioneiro da densidade de pixels. Num full shot, o rosto pode ocupar ~30 pixels — insuficiente para validação robusta. Por isso existe o Eixo D (VC-Matrix).

### 8.3 Eixo D Valida Continuidade, Não Identidade

Um plano Eixo D isolado prova que a silhueta é coerente. A identidade requer ligação a plano Eixo F adjacente na montagem.

---

## 9. CAST W-HIOS-FORENSIC-UNIT

### 9.1 Inventário de Anchors (02 Jun 2026)

| # | Personagem | Anchor ID | Detection | Generator |
|---|------------|-----------|-----------|-----------|
| 1 | Gabi Santos | gabi.santos.anchor.v1 | — | Runway (prévio) |
| 2 | Helena Meyer | helena.meyer.junior.anchor.v1 | 0.8636 | Runway (reused) |
| 3 | Marcus Vance | marcus.vance.anchor.v1 | 0.8638 | Runway (reused) |
| 4 | Marcus Couto | marcus.couto.anchor.v1 | 0.8811 | Gen-4.5 (novo) |
| 5 | Lucas Silva | lucas.silva.anchor.v1 | 0.8119 | Gen-4.5 (novo) |
| 6 | Alejandro Valenzuela | alejandro.valenzuela.anchor.v1 | 0.8763 | Gen-4.5 (novo) |

### 9.2 Espelho Narrativo (Vance vs Couto)

| Aspecto | Vance (Herói) | Couto (Vilão) |
|---------|---------------|---------------|
| Cabelo | Desalinhado | Perfeitamente penteado |
| Barba | Stubble leve | Clean-shaven |
| Roupa | Sobretudo gasto | Caxemira impecável |
| Expressão | Cansaço protector | Frieza predatória |
| Olheiras | Profundas | Ausentes |

---

## 10. COMPATIBILIDADE DE GERADORES

| Generator | SPINE Status | Avg Similarity | Notas |
|-----------|--------------|----------------|-------|
| Runway Gen-4 | FORENSIC | 0.7850 | Primary generator |
| Runway Gen-4.5 | FORENSIC | ~0.80+ | Testado nesta sessão |
| SORA 2 | INCOMPATIBLE | 0.4785 | Identity drift |
| Kling | UNTESTED | — | — |

---

## 11. DECRETOS CONSTITUCIONAIS

| Decreto | Título | Status |
|---------|--------|--------|
| DECRETO-001 | Dupla Régua SPINE | SEALED |
| ADITAMENTO | Lei da Escala e Distância | SEALED |

---

## 12. CHECKLIST DE PRODUÇÃO

### Para cada personagem novo:

- [ ] Escrever PASSPORT prompt
- [ ] Gerar video via Runway Gen-4.5
- [ ] Extrair frames (fps=1)
- [ ] Seleccionar melhor frame
- [ ] Extrair embedding ArcFace
- [ ] Calcular hash SHA-256
- [ ] Criar provenance.json
- [ ] Registar em SPINE-PASSPORTS-MASTER.md
- [ ] Human Dragon aprova (I9)

### Para cada plano gerado:

- [ ] Identificar tipo (Close/Medium/Full/Wide)
- [ ] Determinar eixo (F ou D)
- [ ] Se Eixo F: medir similarity vs anchor
- [ ] Se Eixo D: validar VC-Matrix
- [ ] Registar score em validation JSON
- [ ] Aplicar regra do mínimo para tier

---

## 13. LIGAÇÕES CONSTITUCIONAIS

| Invariante | Aplicação |
|------------|-----------|
| **I1** | Human Dragon aprova cada anchor |
| **I9** | Nenhum anchor locked sem gate humano |
| **I11** | Hash e embedding imutáveis após lock |
| **I14** | Dados ausentes = erro explícito |
| **I19** | Proveniência atómica (ficheiro + JSON) |

---

## 14. MEMORY LOOP — CONTINUIDADE

Este documento existe para que futuras instâncias possam:

1. **Compreender** a arquitectura SPINE-CAST
2. **Reproduzir** o processo de geração de anchors
3. **Validar** planos usando os mesmos critérios
4. **Expandir** o cast com novos personagens
5. **Manter** continuidade de identidade na série

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"A identidade é a raiz. A performance é o fruto."*
