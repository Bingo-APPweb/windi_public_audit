# DIAG-MED-TIER — Diagnóstico do Tier MED
## Liga IA+H · 06 Jun 2026

**Receipt:** `WINDI-DIAG-MED-TIER-20260606`
**Status:** SEALED
**Invariants:** I14 (Explicit Failure)
**Decision:** Human Dragon · "SIM" · 06 Jun 2026

---

## 1. Contexto

A arquitectura §240–§241 definiu routing de 3 tiers:
- **FREE** → Ollama B local (mistral:7b)
- **MED** → Mistral API
- **HIGH** → Claude (claude-sonnet-4-20250514)

Débito registado: "MED runtime-untested, I14 em contradição activa."

---

## 2. Evidência Recolhida

### 2.1 Estado das Portas

```bash
$ ss -tlnp | grep -E "8112|8108"
LISTEN 0 5 0.0.0.0:8108 0.0.0.0:* users:(("python3",pid=639,fd=3))
```

| Porta | Serviço | Estado |
|-------|---------|--------|
| :8108 | Dragon Hub | LIVE |
| :8112 | Orchestrator | **DOWN** |

### 2.2 Teste de Endpoint

```bash
$ curl -s --connect-timeout 2 -X POST http://localhost:8112/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", "language": "en"}'
EXIT: 7  # Connection refused
```

### 2.3 Estado das Credenciais

```bash
$ grep -E "MISTRAL_API_KEY|ANTHROPIC_API_KEY" /opt/windi/.env | sed 's/=.*/=***/'
ANTHROPIC_API_KEY=***
# MISTRAL_API_KEY: NÃO PRESENTE
```

---

## 3. Diagnóstico por Sistema

| Sistema | MED Tier | I14 Status |
|---------|----------|------------|
| **W-SITES** (ai_writer_runtime.py) | Implementado | ✓ 503 `TierUnavailableError` se sem chave |
| **Dragon Chat** (:8112 Orchestrator) | NÃO IMPLEMENTADO | ✗ MED e HIGH usam o mesmo backend (Claude) |

### 3.1 W-SITES — Conforme I14

Ficheiro: `/opt/windi/windi-sites/identity-gate/ai_writer/ai_writer_runtime.py`

```python
# Linha 291-295
def _get_available_tiers() -> list:
    available = ["FREE"]
    if MISTRAL_API_KEY and MISTRAL_API_KEY != "SUBSTITUIR":
        available.append("MED")
    if ANTHROPIC_API_KEY:
        available.append("HIGH")
    return available

# Linha 306-311
if not MISTRAL_API_KEY or MISTRAL_API_KEY == "SUBSTITUIR":
    raise TierUnavailableError(
        tier="MED",
        reason="provider key not configured",
        available_tiers=_get_available_tiers()
    )
```

**Comportamento:** Falha explícita (503) quando MED é pedido sem chave. I14 satisfeito.

### 3.2 Dragon Chat — Viola I14

Ficheiro: `/opt/windi/orchestrator/windi_orchestrator.py`

```python
# Linha 72-73
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
MODEL = "claude-sonnet-4-20250514"
# Não há referência a Mistral
```

Ficheiro: `/opt/windi/engine/dragon_chat_service.py`

```python
# Linha 1201-1203
#   - FREE: local only, no orchestrator
#   - MED: orchestrator /generate
#   - HIGH: orchestrator /orchestrate

# Linha 1246-1248
mode = "orchestrate" if tier == "HIGH" else "generate"
result = query_orchestrator(message, tier, lang, mode)
```

**Comportamento:** MED e HIGH ambos chamam o mesmo backend (Anthropic Claude). MED não existe como tier distinto. Sistema declara capacidade que não tem.

---

## 4. Conclusão

| Aspecto | Estado |
|---------|--------|
| MED no W-SITES | Implementado, conforme I14 (503 se sem chave) |
| MED no Dragon Chat | **NÃO IMPLEMENTADO** — viola I14 |
| MISTRAL_API_KEY | Não configurada |
| Razão do adiamento | Económica: Mistral só a sério com 500+ users (break-even: 100×€0.50×4) |

---

## 5. Acção Tomada

**Opção 1 pura:** Selar diagnóstico como medição do estado actual.

A correção de comportamento (fazer Dragon Chat retornar 503 em MED, como W-SITES já faz) fica para sessão própria — será tratada como errata (§267, taxonomia G4: CORRIGIR) com receipt a citar §240–§241.

---

## 6. Débito Remanescente

- [ ] Dragon Chat :8112 — alinhar ao padrão I14 do W-SITES (MED sem Mistral → 503)
- [ ] MISTRAL_API_KEY — configurar quando economia justificar (500+ users)

---

*Liga IA+H · WINDI Publishing House · 06 Jun 2026*
*"A falha explícita é preferível à mentira silenciosa."*
*Invariants: I14*
