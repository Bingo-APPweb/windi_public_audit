# WINDI-HIOS Video Studio

**Version:** 0.4.0
**Port:** 8196
**URL:** `windi-domain.com/hios/video-studio/`

---

## O Que É

Sistema de produção de vídeo verificável com governança constitucional WINDI.

**Princípio Central:**
> O selo prova PROVENIÊNCIA de intenção e fonte, NÃO veracidade dos eventos representados.
> Todo vídeo gerado é DRAMATIZAÇÃO SINTÉTICA inspirada em fontes reais.

---

## Arquitectura Three-Tier

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: EXTERNAL/OPAQUE                                    │
│  Veo 3.1 (Google) — Geração de keyframes                    │
│  Custo: API paga por geração                                │
├─────────────────────────────────────────────────────────────┤
│  TIER 2: CONTROLLED/RENTED                                  │
│  LTX 2.3 (vast.ai) — Extensão de vídeo                      │
│  Custo: GPU alugada à hora                                  │
├─────────────────────────────────────────────────────────────┤
│  TIER 3: LOCAL/SOVEREIGN                                    │
│  Strato Ledger (:8101) — Selo forense                       │
│  Custo: Zero (infraestrutura própria)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## W-PROMPT-001: Journalist Gate

O coração do sistema. Transforma factos brutos + intenção humana em prompts auditáveis.

### As 4 Camadas

| # | Camada | Descrição |
|---|--------|-----------|
| 1 | **Die Fakten** | Artigo/documento original (hash imutável) |
| 2 | **Der Menschliche Fokus** | Intenção editorial do jornalista |
| 3 | **Publikum** | Audiência-alvo + tom narrativo |
| 4 | **Constitutional Constraints** | I9 + Realismo Allgäu |

### Ciclo de Vida do Token

```
ENTITY_CONFIRMATION_PENDING  →  LOCKED  →  RENDERED  →  FINAL_SEAL
         ↑                         ↑
    mint-prompt              confirm-entities
                            (GATE HUMANO)
```

---

## Como Testar

### Passo 1: Aceder ao Video Studio

```
https://windi-domain.com/hios/video-studio/
```

Ou localmente:
```
http://localhost:8196/
```

### Passo 2: Tab "Journalist Gate"

1. **Die Fakten** — Cole um artigo de jornal (em DE, EN ou PT)
2. **Der Menschliche Fokus** — Descreva que cena quer mostrar
3. **Publikum** — Escolha audiência e tom
4. Click **"Mint Pre-Ledger Token"**

### Passo 3: Confirmar Entidades (GATE HUMANO)

- Revise as entidades extraídas automaticamente
- **PODE EDITAR** qualquer valor clicando no campo
- Se a máquina extraiu "7 Millionen" mas deveria ser "7 Milliarden", corrija
- Click **"I Confirm These Values Are Correct"**

### Passo 4: Token LOCKED

O sistema mostra:
- `compiled_prompt` — Master Prompt em inglês técnico
- `locked_constants` — Valores verificados
- `pre_ledger_receipt` — Receipt da pré-produção

---

## API Endpoints

### Health Check

```bash
curl http://localhost:8196/api/hios/health
```

### Mint Pre-Ledger Token

```bash
curl -X POST http://localhost:8196/api/hios/mint-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "journalist_did": "did:windi:test-001",
    "raw_facts": "Die VR-Bank Kempten hat Kredite vergeben...",
    "human_focus": "Zeigen Sie die Beraterin bei der Entscheidung.",
    "source_type": "NEWSPAPER_ARTICLE",
    "source_language": "de",
    "audience": "GENERAL_PUBLIC",
    "tone": "INFORMATIVE"
  }'
```

**Resposta:** Token com `lifecycle: ENTITY_CONFIRMATION_PENDING`

### Confirmar Entidades (com correções)

```bash
curl -X POST http://localhost:8196/api/hios/confirm-entities \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "WPMT-XXXXXXXX",
    "confirmer_did": "did:windi:test-001",
    "confirmed": true,
    "corrections": [
      {
        "original": "7 Millionen Euro",
        "corrected": "7 Milliarden Euro",
        "reason": "Erro no artigo original"
      }
    ]
  }'
```

**Resposta:** Token com `lifecycle: LOCKED`

### Obter Token

```bash
curl http://localhost:8196/api/hios/prompt/WPMT-XXXXXXXX
```

### Listar Media

```bash
curl http://localhost:8196/api/hios/media
```

---

## Provas do Gate (Testes de Integridade)

### Prova 1: Bypass Rejeitado

```bash
curl -i -X POST http://localhost:8196/api/hios/confirm-entities \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": "WPMT-FAKE", "confirmed": true}'
```

**Esperado:** `HTTP 404` + `TOKEN_NOT_FOUND`

### Prova 2: Correção Humana Registada

Após mint + confirm com correções, o token deve mostrar:

```json
{
  "extracted_entities": {
    "corrections_made": [
      {
        "original": "valor errado",
        "corrected": "valor certo",
        "reason": "..."
      }
    ],
    "entities": [
      {
        "value": "valor certo",
        "corrected": true
      }
    ],
    "human_confirmed": true
  }
}
```

### Prova 3: Dupla Linhagem

O token deve ter DOIS hashes distintos:
- `context_hash` — Hash do artigo original (imutável)
- `prompt_hash` — Hash do prompt final (após correções)

---

## Invariantes Constitucionais

| ID | Nome | Aplicação |
|----|------|-----------|
| I1 | Soberania Humana | Humano aprova antes de selar |
| I9 | Proibição de Escalação | `confirmed=true` obrigatório |
| I11 | Permanência de Evidência | Receipts imutáveis no Ledger |
| I14 | Explicit Failure | Campos ausentes = erro, não default |

---

## Ficheiros do Sistema

```
/opt/windi/hios/
├── hios_server.py              # Backend Flask (:8196)
├── README.md                   # Este ficheiro
└── visual/
    ├── video-studio.html       # Frontend completo
    └── producer/
        ├── veo_producer.py     # Integração Veo 3.1
        └── hybrid-pipeline/
            ├── schemas/
            │   ├── w-prompt-001.json   # Schema do token
            │   └── w-mails-001.json    # Schema de distribuição
            └── receipts/               # Receipts locais
```

---

## Troubleshooting

### Servidor não responde

```bash
# Verificar se está a correr
ps aux | grep hios_server

# Reiniciar
pkill -f hios_server
nohup python3 /opt/windi/hios/hios_server.py > /tmp/hios_server.log 2>&1 &
```

### Ver logs

```bash
tail -f /tmp/hios_server.log
```

### Testar health

```bash
curl -s http://localhost:8196/api/hios/health | python3 -m json.tool
```

---

## Próximos Passos

- [ ] W-COST-001 Integration (custo por render)
- [ ] `confirmer_did` obrigatório em produção (recusar anonymous)
- [ ] Integração LTX vast.ai (Tier 2)

---

*WINDI-HIOS v0.4.0 — "AI processes. Human decides. WINDI guarantees."*
