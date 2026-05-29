# W-GENERATOR-001 — Sovereign Content Generation Abstraction

**Port:** 8198
**Version:** 0.1.0
**Status:** SEALED
**Date:** 2026-05-29
**Invariants:** I9, I9-G, I11, I14

## Doctrine

> "A invocacao de geradores de conteudo e ferramenta tecnica.
>  O selo do resultado e acto humano."

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
│  │  ✅  │  │  ✅  │  │  🔲  │  │  🔲  │  │  🔲  │        │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
B4 GATE → I9 GATE → LEDGER SEAL
```

## DOORs (Adapters)

| DOOR | Generator | Status | Supports | Quality | Cost/sec |
|------|-----------|--------|----------|---------|----------|
| DOOR_SORA | OpenAI SORA | ✅ ACTIVE | video | 5/5 | $0.33 |
| DOOR_RUNWAY | Runway Gen-3 | ✅ ACTIVE | video, image | 4/5 | $0.17 |
| DOOR_KLING | Kling AI | 🔲 FUTURE | video | 4/5 | $0.08 |
| DOOR_GROK | GROK Images | 🔲 FUTURE | image | 3/5 | $0.01 |
| DOOR_MIDJOURNEY | Midjourney | 🔲 FUTURE | image | 5/5 | $0.05 |
| DOOR_LOCAL | Stable Diffusion | 🔲 FUTURE | image | 3/5 | $0.00 |

## API Endpoints

### GET /health
Health check and active DOORs.

### GET /doors
List all DOORs with status and capabilities.

### POST /generate
Generate content through specified or auto-selected DOOR.

```json
{
    "prompt": "Elisa in a garden with autumn leaves",
    "door": "runway",  // or "sora" or "auto"
    "content_type": "video",
    "params": {
        "duration": 5,
        "aspect_ratio": "16:9"
    },
    "workflow_id": "obra2_s01"
}
```

### GET /status/{job_id}
Check generation job status.

### GET /i9-g
Display I9-G doctrine for transparency.

## I9-G Corollaries

| # | Corollary |
|---|-----------|
| C1 | CCode pode invocar qualquer gerador dentro de workflow aprovado |
| C2 | A escolha de qual gerador usar e optimizacao tecnica, nao governanca |
| C3 | O utilizador externo tem soberania sobre o resultado, nao sobre a infra |
| C4 | B4 permanece gate obrigatorio entre geracao e proposta |
| C5 | Selo final requer human_approved=true (I9 intacto) |

## Running

```bash
cd /opt/windi/w-generator-001
source /opt/windi/venv/bin/activate
nohup python3 generator_service.py > /var/log/windi/w-generator-001.log 2>&1 &
```

## Adding New DOORs

1. Create new adapter class extending `GeneratorAdapter`
2. Implement: `generate()`, `check_status()`, `download()`, `health_check()`
3. Add API key to `/opt/windi/.env`
4. Register in `GeneratorRegistry._load_adapters()`
5. Test with `/doors` endpoint

## Sealed By

- **Human Dragon** — Approval
- **Guardian** — Constitutional Review
- **Architect** — Implementation

---

*WINDI Publishing House — 2026*
*"AI processes. Human decides. WINDI guarantees."*
