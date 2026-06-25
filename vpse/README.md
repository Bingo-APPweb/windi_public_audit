# VPSE — Viability Pre-Screen Engine

**WINDI Playground · Track P0** · v0.1.0-mvp
*Pre-HIOS, pre-DID. Pre-Screen, não veredicto.*

> O primeiro sucesso não é gerar código.
> O primeiro sucesso é: **um utilizador entende mais cedo o que deve ser testado,
> verificado, governado ou abandonado antes de construir.**

## O que é

Camada de triagem do WINDI Playground. Recebe uma ideia em estado bruto e
devolve um diagnóstico estruturado — intenção, domínios, blocos semânticos,
módulos WINDI aplicáveis, riscos regulatórios precoces, perguntas de compliance,
artefacto recomendado e prontidão para HIOS.

Não é Perplexity. Não busca a web. Busca **para dentro** da missão constitucional
do WINDI-HIOS. Engine soberano, local, determinístico.

## As 4 regras canónicas (I9, 2026-06-25)

1. **Proveniência sempre** — todo output carrega `[lido]` / `[estimado]` / `[nao_verificado]`.
2. **Sem verdade nua** — riscos e compliance questions saem como `{content, provenance, confidence, source_hint}`.
3. **Receipt morto** — receipt-candidate é local: `unsealed=true`, `ledger_eligible=false`, hash local, zero POST ao Ledger, zero DID presumido.
4. **Pré-HIOS, pré-DID** — só vira candidato a Ledger via `/farm/claim` com DID válido.

## Pipeline

```
Idea → Intent → Decompose → Classify Domain → Retrieve WINDI Modules
     → Risk/Compliance Scan → Governance Map → Viability Report
     → (opcional) Receipt-candidate MORTO
```

## Uso

```python
from vpse_engine import run_vpse

report = run_vpse(
    idea="A system where podcast watch time generates bingo numbers...",
    emit_receipt_candidate=True,
)
```

HTTP:
```bash
VPSE_PORT=8120 python3 -m uvicorn vpse_engine.service:app --host 127.0.0.1 --port 8120
curl -X POST localhost:8120/prescreen -d '{"idea":"..."}'
```

## Teste

```bash
python3 tests/test_bingo_podcast.py   # 15/15 PASS
```

## Estrutura

```
vpse/
├── vpse_engine/
│   ├── provenance.py      # Regras 1 e 2 — carimbo constitucional
│   ├── knowledge_base.py  # léxicos: domínios, módulos, sinais de risco (local)
│   ├── pipeline.py        # 6 estágios + receipt morto
│   └── service.py         # FastAPI read-only
├── tests/test_bingo_podcast.py
├── DEPLOY_BRIEFING_CCODE.md
└── README.md
```

## Deploy

Ver `DEPLOY_BRIEFING_CCODE.md`. Porta e systemd são decisão CCode+Human Dragon
no Strato, sob GOLDEN RULE. Esta entrega é o motor; o deploy é o passo seguinte.

OM SHANTI 🐉
