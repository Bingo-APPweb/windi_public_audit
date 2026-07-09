# W-GENERATOR-001 — Sovereign Content Generation Abstraction

**Port:** 8198
**Version:** 0.2.0
**Status:** LIVE
**Updated:** 2026-06-28
**Invariants:** I9, I9-G, I11, I14, I19

## Doctrine

> "A invocacao de geradores de conteudo e ferramenta tecnica.
>  O selo do resultado e acto humano."

---

## Architecture

```
USER REQUEST
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    W-GENERATOR-001                          │
│                      Port :8198                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ROUTING INTELLIGENCE                    │   │
│  │         (auto-select by cost/quality/type)           │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│     ┌──────────┬──────────┼──────────┬──────────┐          │
│     ▼          ▼          ▼          ▼          ▼          │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │ SORA │  │RUNWAY│  │ KLING│  │ GROK │  │ MIDJ │        │
│  │DOOR_1│  │DOOR_2│  │DOOR_3│  │DOOR_4│  │DOOR_5│        │
│  │  🔲  │  │  ✅  │  │  🔲  │  │  🔲  │  │  🔲  │        │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
B4 GATE → I9 GATE → LEDGER SEAL
```

---

## DOORs (Adapters)

| DOOR | Generator | Status | Model | Quality | Cost/5s |
|------|-----------|--------|-------|---------|---------|
| DOOR_RUNWAY | Runway Gen-4 | ✅ LIVE | gen4_turbo | 4/5 | $0.85 |
| DOOR_SORA | OpenAI SORA | 🔲 STUB | — | 5/5 | — |
| DOOR_KLING | Kling AI | 🔲 FUTURE | — | 4/5 | — |
| DOOR_GROK | GROK Images | 🔲 FUTURE | — | 3/5 | — |
| DOOR_MIDJOURNEY | Midjourney | 🔲 FUTURE | — | 5/5 | — |

**Active:** DOOR_RUNWAY (validated CASE-0001, 28 Jun 2026)

---

## API Endpoints

### GET /health
Health check and active DOORs.

### GET /doors
List all DOORs with status and capabilities.

### POST /generate
Start async generation. Returns job_id for polling.

```json
{
    "prompt": "Slow cinematic push-in toward the shop entrance...",
    "door": "runway",
    "content_type": "video",
    "params": {
        "duration": 5,
        "aspect_ratio": "16:9",
        "model": "gen4_turbo",
        "source_image_url": "https://example.com/photo.jpg"
    },
    "workflow_id": "case-0001-scene-1"
}
```

**Response:**
```json
{
    "job_id": "runway_891d5ca7-68cd-45f0-acac-097dd0f1178e",
    "status": "pending",
    "door": "runway"
}
```

### GET /status/{job_id}
Check generation job status.

**Response:**
```json
{
    "job_id": "runway_891d5ca7-...",
    "status": "SUCCEEDED",
    "output_url": "https://runway-output-url...",
    "progress": 1.0
}
```

### GET /wait/{job_id}
Poll until job completes (max 5 minutes).

### GET /download/{job_id}?output_dir=/path
Download completed video to local filesystem.

### POST /generate-sync
Synchronous generation — waits until complete.

```json
{
    "prompt": "...",
    "door": "runway",
    "content_type": "video",
    "params": {...},
    "workflow_id": "...",
    "output_dir": "/path/to/save"
}
```

**Response:**
```json
{
    "job_id": "runway_...",
    "status": "SUCCEEDED",
    "output_url": "https://...",
    "local_file": "/path/to/save/runway_....mp4"
}
```

### GET /i9-g
Display I9-G doctrine for transparency.

---

## Runway API Integration

**Base URL:** `https://api.dev.runwayml.com/v1`
**API Version:** `2024-11-06`
**Auth:** Bearer token (RUNWAY_API_KEY in .env)

**Endpoints used:**
- `POST /image_to_video` — image-to-video generation
- `GET /tasks/{id}` — poll job status

**Pricing (Jun 2026):**
- Gen-4 Turbo: $0.17/sec → $0.85/5s clip

---

## I9-G Corollaries

| # | Corollary |
|---|-----------|
| C1 | CCode pode invocar qualquer gerador dentro de workflow aprovado |
| C2 | A escolha de qual gerador usar e optimizacao tecnica, nao governanca |
| C3 | O utilizador externo tem soberania sobre o resultado, nao sobre a infra |
| C4 | B4 permanece gate obrigatorio entre geracao e proposta |
| C5 | Selo final requer human_approved=true (I9 intacto) |

---

## Running

```bash
cd /opt/windi/w-generator-001
source /opt/windi/venv/bin/activate
nohup python3 generator_service.py > /var/log/windi/w-generator-001.log 2>&1 &
```

**Check:**
```bash
curl http://localhost:8198/health
curl http://localhost:8198/doors
```

---

## Environment Variables

```bash
# In /opt/windi/.env
RUNWAY_API_KEY=key_xxxxx
# SORA_API_KEY=sk-xxxxx (future)
```

---

## Validated Generation (CASE-0001)

| Metric | Value |
|--------|-------|
| Scenes | 3 |
| Duration | 14.0s |
| Cost | $2.55 |
| Generator | Runway Gen-4 Turbo |
| Receipt | WINDI-CASE0001-MICROFILM-V2-20260628 |

---

## Adding New DOORs

1. Create new adapter class extending `GeneratorAdapter`
2. Implement: `generate()`, `check_status()`, `download()`, `health_check()`
3. Add API key to `/opt/windi/.env`
4. Register in `GeneratorRegistry._load_adapters()`
5. Test with `/doors` endpoint

---

## Sealed By

- **Human Dragon** — Approval
- **Guardian** — Constitutional Review
- **Architect** — Implementation

---

*WINDI Publishing House — 2026*
*"AI processes. Human decides. WINDI guarantees."*
