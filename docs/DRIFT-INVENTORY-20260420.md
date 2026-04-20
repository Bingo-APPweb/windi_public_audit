# DRIFT INVENTORY — 20 Abril 2026

**Autor:** Architect Agent (CCode)
**Sessão:** §196 Constitutional Seal Cycle
**Target:** drift = 0

---

## RESUMO EXECUTIVO

| Tipo | Count | Severidade |
|------|-------|------------|
| Estrutural | 4 | ⚠️ Médio |
| Operacional | 7 | ⚠️ Médio |
| Constitucional | 1 | ✅ Baixo (warning) |
| **TOTAL** | **12** | **Target: 0** |

---

## 1. DRIFT ESTRUTURAL

### 1.1 Portas declaradas mas não escutando

| Porta | Serviço | Causa | Acção |
|-------|---------|-------|-------|
| :8092 | windi-clone | `flask-cors` missing | `pip3 install flask-cors` |
| :8145 | W-STATE-CORE-006 | Serviço down | Investigar |

### 1.2 Systemd em crash-loop

| Serviço | Estado | Causa |
|---------|--------|-------|
| windi-babel.service | auto-restart | Conflito porta/dependência |
| windi-export.service | auto-restart | Conflito porta/dependência |

### 1.3 Portas não declaradas no CLAUDE.md

22 portas activas não documentadas. Exemplo:
- :4050, :8080, :8081, :8084, :8086, :8090, :8095, :8097, :8098

**Acção:** Auditar e documentar ou desligar.

---

## 2. DRIFT OPERACIONAL

### 2.1 Serviços sem /health endpoint

| Porta | Resposta | Notas |
|-------|----------|-------|
| :8085 | unreachable | Serviço down |
| :8089 | unreachable | Serviço down |
| :8094 | unreachable | Serviço down |
| :8107 | unreachable | Serviço down |
| :8096 | HTTP 404 | DID-Genesis (endpoint diferente) |
| :8200 | HTTP 404 | W-DEV-API (usa /v1/health) |

### 2.2 Gateway público vs localhost

| Endpoint | Localhost | Público | Status |
|----------|-----------|---------|--------|
| /enterprise/ | 404 | 200 | ✅ OK (nginx proxy) |
| /verify-public/ | 404 | 502 | ⚠️ Cosmético |
| /dev-api/v1/health | 404 | 200 | ✅ OK (nginx proxy) |
| /travel/ | 404 | 200 | ✅ OK (nginx proxy) |
| /actuary/ | 404 | 200 | ✅ OK (nginx proxy) |

**Nota:** `/verify-public/` raiz dá 502 porque não há location block para a raiz.
Path-based `/verify-public/WINDI-*` funciona correctamente (200 ✅).

---

## 3. DRIFT CONSTITUCIONAL

### 3.1 Invariantes testados

| Invariante | Status | Evidência |
|------------|--------|-----------|
| I9 (Human Approval) | ✅ PASS | 7 referências em seal_unified.py |
| I11 (Ledger Permanence) | ✅ PASS | 50 receipts activos |
| I14 (Explicit Failure) | ⚠️ WARNING | 11 possíveis placeholders |

### 3.2 I14 Violations a investigar

Ficheiros com possíveis placeholders (`"unknown"`, `"N/A"`, `"---"`):
```bash
grep -rE '"unknown"|"N/A"|"---"' /opt/windi/w-dev-api-001/app/
```

---

## 4. ACÇÕES PRIORITÁRIAS (PRE-BERLIN)

### P0 — Bloqueadores

- [ ] Nenhum bloqueador constitucional detectado

### P1 — Importante

- [ ] Fix :8092 (windi-clone): `pip3 install flask-cors`
- [ ] Investigar :8145 (W-STATE-CORE-006) down
- [ ] Auditar 4 portas unreachable (:8085, :8089, :8094, :8107)

### P2 — Cosmético

- [ ] Adicionar location `/verify-public/` raiz com redirect ou mensagem
- [ ] Documentar 22 portas não declaradas
- [ ] Verificar 11 possíveis placeholders I14

---

## 5. MÉTRICAS PARA /api/truth

```json
{
  "drift": {
    "structural": 4,
    "operational": 7,
    "constitutional": 0,
    "global": 11,
    "healthy": false
  }
}
```

**Target Berlin:** `global: 0` ou apenas warnings cosméticos.

---

*Inventário gerado: 2026-04-20T18:33+02:00*
*Próximo passo: Dia 2 — /api/truth endpoint*
