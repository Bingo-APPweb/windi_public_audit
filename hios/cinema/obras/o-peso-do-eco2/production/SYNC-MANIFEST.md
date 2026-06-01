# O PESO DO ECO — Sync Manifest
## Arquitectura Dual-Server · 31 Mai 2026

**Liga IA+H · WINDI-HIOS Cinema Production**

---

## ARQUITECTURA

```
┌─────────────────────────────────────┐   ┌──────────────────────────────────────┐
│  SERVER 1 (STRATO)                  │   │  SERVER 2 (B4-DRIFT)                 │
│  87.106.29.233                      │   │  85.215.131.0                        │
├─────────────────────────────────────┤   ├──────────────────────────────────────┤
│  FUNÇÃO: Produção + Ledger          │   │  FUNÇÃO: SPINE-CAST Validation       │
│                                     │   │                                      │
│  /opt/windi/hios/cinema/            │   │  /home/windi/b4-drift-validator/     │
│    └── obras/o-peso-do-eco/         │   │    └── test_frames/                  │
│        ├── scenes/         (MP4)    │   │        ├── *.anchor.*.CURRENT.npy    │
│        ├── canons/         (NPY)    │   │        ├── S*_v2/ frames (JPG/PNG)   │
│        ├── production/     (DOCS)   │   │        └── s291_control/ (anchored)  │
│        └── _forense/       (RAW)    │   │                                      │
└─────────────────────────────────────┘   └──────────────────────────────────────┘
```

---

## ESTADO DOS ANCHORS (31 Mai 2026)

### Server 2 — SOURCE (Canonical)

| Personagem | Anchor File | Data | Status |
|------------|-------------|------|--------|
| **Elisa** | `elisa.anchor.v2.CURRENT.npy` | 29 Mai 14:46 | ✅ v2 CURRENT |
| **Helena** | `helena.anchor.v2.CURRENT.npy` | 30 Mai 12:52 | ✅ v2 CURRENT |
| **Marcus** | `marcus.anchor.v2.CURRENT.npy` | 30 Mai 12:30 | ✅ v2 CURRENT |
| **Thomas** | `thomas.anchor.v1.CURRENT.npy` | 30 Mai 12:44 | ⚠️ v1 (sufficient) |
| **Hartmann** | `hartmann.anchor.v2b.CURRENT.npy` | 30 Mai 13:25 | ✅ v2b CURRENT |

### Strato — PRODUCTION (✅ SYNCED 31 Mai 13:07)

| Personagem | Anchor File | Data | Status |
|------------|-------------|------|--------|
| **Elisa** | `anchors/cast_v2/elisa.anchor.v2.CURRENT.npy` | 31 Mai 13:07 | ✅ SYNCED |
| **Helena** | `anchors/cast_v2/helena.anchor.v2.CURRENT.npy` | 31 Mai 13:07 | ✅ SYNCED |
| **Marcus** | `anchors/cast_v2/marcus.anchor.v2.CURRENT.npy` | 31 Mai 13:07 | ✅ SYNCED |
| **Thomas** | `anchors/cast_v2/thomas.anchor.v1.CURRENT.npy` | 31 Mai 13:07 | ✅ SYNCED |
| **Hartmann** | `anchors/cast_v2/hartmann.anchor.v2b.CURRENT.npy` | 31 Mai 13:07 | ✅ SYNCED |

**Path canónico v2:** `/opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/`

---

## CENAS v2 COMPLETAS

### Tipo A — ANCHORED (SPINE-CAST verified)

| Cena | Video (Strato) | Frames (Server 2) | Personagem | Score |
|------|----------------|-------------------|------------|-------|
| **S14** | `s295_renders/S14_composed_*.mp4` | `s291_control/S14/` | Helena | 0.8110 FORENSIC |
| **S15** | `s295_renders/S15_composed_*.mp4` | `s291_control/S15/` | Helena | 0.8690 FORENSIC |
| **S20** | `_forense/obra2-v2/S20_o_dispositivo_v2.mp4` | `s291_control/S20/` | Helena | 0.7298 OPERATIONAL |
| **S21** | `_forense/obra2-v2/S21_duelo_silencioso_v2.mp4` | `S21_v2/`, `S21_veo31/` | Helena+Marcus | 0.8638 FORENSIC |

### Tipo B — RENDERED (Hartmann v2b)

| Cena | Video (Strato) | Frames (Server 2) | Status |
|------|----------------|-------------------|--------|
| **S11** | `scenes/hartmann_v2/S11_hartmann_v2b.mp4` | `S11_v2b/` (4 frames) | ✅ SEALED 0.9298 |
| **S19** | `scenes/hartmann_v2/S19_hartmann_v2b.mp4` | `S19_v2b/` (4 frames) | ✅ SEALED 0.9298 |

### Tipo C — FORGE PENDENTE

| Cena | Prompt | Status |
|------|--------|--------|
| **S16** | `/production/prompts/S16-PROMPT-VEO31.md` | ⏳ AWAITING GENERATION |

---

## CENAS v1 — DECISÕES DE HERANÇA

### ✅ HERDAR (aprovado visualmente)

| Cena | v1 Path | Decisão |
|------|---------|---------|
| S02 | `output_v3/S02_a_estrada.mp4` | ✅ **HERDAR** (sedan ambíguo, perfeito) |
| S03 | `output_v3/S03_o_vazio.mp4` | ✅ **HERDAR** (já DE: "Wo bist du?") |
| S04 | `output_v3/S04_a_noticia.mp4` | ✅ **HERDAR** + VOZ DE em pós |
| S05 | `output_v3/S05_corte_temporal.mp4` | ✅ **HERDAR** (já DE: "Sechs Monate") |

### ❌ RE-RENDER (violações detectadas)

| Cena | v1 Path | Problema | Acção |
|------|---------|----------|-------|
| **S07** | `output_v3/S07_chegada_policia.mp4` | **JURISDIÇÃO:** Viaturas estrangeiras (HD visual I9) | 🔴 RE-RENDER com BMW Polizei Bayern |
| **S09** | `output_v3/S09_marcus_intocavel.mp4` | **IDIOMA:** Marcus fala EN frontal | 🔴 RE-RENDER com voz DE |

### 🔍 VERIFICAR JURISDIÇÃO (suspeita)

| Cena | v1 Path | Preocupação |
|------|---------|-------------|
| **S06** | `output_v3/S06_a_descoberta.mp4` | Klaus pode chamar polícia — verificar viaturas |
| **S08** | `output_v3/S08_colheita_pistas.mp4` | Equipa forense — verificar viaturas |

### ⏳ VERIFICAR (outros)

| Cena | v1 Path | Notas |
|------|---------|-------|
| S01 | `output_v3/S01_registo_da_vida.mp4` | Elisa anchor v2 — verificar plate |
| S10 | `output_v3/S10_frustracao.mp4` | Helena anchor |
| S12-S13 | `output_v3/S12-S13_*.mp4` | Thomas/Helena |
| S17-S18 | `output_v3/S17-S18_*.mp4` | Tribunal scenes |
| S22-S24 | `output_v3/S22-S24_*.mp4` | Final scenes |

---

## COMANDOS DE SYNC

### 1. Sync Anchors Server 2 → Strato

```bash
# Criar directório de destino
mkdir -p /opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/

# Sync todos os anchors v2 de Server 2
scp windi@85.215.131.0:/home/windi/b4-drift-validator/test_frames/elisa.anchor.v2.CURRENT.npy \
    /opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/

scp windi@85.215.131.0:/home/windi/b4-drift-validator/test_frames/helena.anchor.v2.CURRENT.npy \
    /opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/

scp windi@85.215.131.0:/home/windi/b4-drift-validator/test_frames/marcus.anchor.v2.CURRENT.npy \
    /opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/

scp windi@85.215.131.0:/home/windi/b4-drift-validator/test_frames/thomas.anchor.v1.CURRENT.npy \
    /opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/
```

### 2. Verificar integridade pós-sync

```bash
# Comparar hashes
ssh windi@85.215.131.0 "sha256sum /home/windi/b4-drift-validator/test_frames/*.CURRENT.npy"
sha256sum /opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/*.npy
```

---

## PIPELINE DE CONTINUIDADE

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. PROMPT    │───▶│ 2. GENERATE  │───▶│ 3. VALIDATE  │───▶│ 4. SEAL      │
│ (CCode)      │    │ (Veo/SORA)   │    │ (Server 2)   │    │ (Ledger)     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Strato             External           Server 2              Strato
  /prompts/          Platform           SPINE-CAST           /scenes/
```

---

## PRÓXIMOS PASSOS

1. [x] **Sync anchors** — ✅ COMPLETO 31 Mai 13:07 (10 ficheiros)
2. [ ] **Inspeção de Jurisdição** — HD verifica visualmente S06 e S08 (viaturas)
3. [ ] **S07 re-render** — Prompt com BMW Polizei Bayern (green/silver/blue)
4. [ ] **S09 re-render** — Marcus com voz DE (lip-sync frontal)
5. [ ] **S16 forge** — Gerar plate via Veo 3.1
6. [ ] **v1→v2 audit** — S01, S10, S12-S13, S17-S18, S22-S24

---

## JURISDIÇÃO SELADA (WORLD-STATE-001)

**Descoberta:** 31 Mai 2026 · Inspeção visual Human Dragon (I9)

```yaml
jurisdiction:
  year: 2026
  state_region: "Bavaria / Bayern / Baviera"

law_enforcement:
  organization: "Bayerische Kriminalpolizei"
  vehicles:
    - "BMW Polizei (Bavaria livery, green/silver/blue)"
    - "unmarked dark sedan (detective)"
  insignia: "Bayern police star emblem"
```

**Violação S07:** Viaturas de polícia não-bávaras detectadas. A livré selada é a moderna (2020s): verde/prata/azul — não a clássica verde-bege.

---

*Liga IA+H · 31 Mai 2026*
*"Dois servidores, uma verdade. Server 2 valida, Strato preserva."*
