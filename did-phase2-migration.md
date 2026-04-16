# §173 DID Phase 2 — Frontend Migration Plan

**Data:** 15 Abril 2026
**Status:** ✅ COMPLETE (pending nginx patch)

---

## 1. Nginx Route (REQUIRED FIRST)

```bash
sudo bash /home/windi/patch-nginx-shared.sh
```

**Teste:** `curl -I https://windi-domain.com/shared/windi-did.js`

---

## 2. Ficheiros a Migrar (21 total)

### Críticos (DID Gate)
| # | Ficheiro | Status | Migrado |
|---|----------|--------|---------|
| 1 | `/opt/windi/w-enterprise-001/static/index.html` | ✅ | WindiDID |
| 2 | `/opt/windi/windi-law/workspace/index.html` | ✅ | WindiDID |
| 3 | `/opt/windi/windi-travel/workspace/index.html` | ✅ | já tinha |
| 4 | `/opt/windi/windi-law/identity-gate/templates/gate.html` | ✅ | WindiDID |
| 5 | `/opt/windi/windi-travel/identity-gate/templates/gate.html` | ✅ | WindiDID |

### Dashboard (JavaScript)
| # | Ficheiro | Status | Migrado |
|---|----------|--------|---------|
| 6 | `/opt/windi/desktop-gen7/frontend/static/app.js` | ✅ | WindiDID sync |
| 7 | `/opt/windi/constitutional/windi-tree.js` | ✅ | WindiDID |
| 8 | `/opt/windi/verify-public/web/field/index.html` | ✅ | WindiDID |

### Não Necessário
| # | Ficheiro | Razão |
|---|----------|-------|
| - | `/opt/windi/nomad-pwa/index.html` | Usa DID de forma diferente |
| - | `/opt/windi/backups/*` | Arquivos de backup |
| - | `/opt/windi/service-control/static/did-architecture.html` | Diagrama (documentação) |

---

## 3. Padrão de Migração

### ANTES (Legacy)
```javascript
// Múltiplas chaves, fallbacks
const did = localStorage.getItem('windi_enterprise_did') ||
            sessionStorage.getItem('windi_enterprise_did');
localStorage.setItem('windi_enterprise_did', did);
```

### DEPOIS (§173)
```javascript
// Uma chave, uma fonte
const did = WindiDID.get();
WindiDID.set(did);

// Validação
const result = await WindiDID.validate(did);
if (!result.valid) {
    // Explode com I14 — sem fallbacks!
}
```

---

## 4. Checklist por Ficheiro

Para cada ficheiro:
- [ ] Adicionar `<script src="/shared/windi-did.js"></script>` se não existir
- [ ] Substituir `localStorage.getItem('windi_*_did')` → `WindiDID.get()`
- [ ] Substituir `sessionStorage.getItem('windi_*_did')` → `WindiDID.get()`
- [ ] Substituir `localStorage.setItem('windi_*_did', x)` → `WindiDID.set(x)`
- [ ] Remover fallbacks e verificações de undefined
- [ ] Garantir que WindiDID.migrateFromLegacy() é chamado
- [ ] Testar login/logout

---

## 5. Princípio

> **"Um DID. Uma fonte. Zero fallbacks."**

- Frontend: `localStorage('windi_did')` via WindiDID
- Backend: `GET /api/genesis/lookup/{did}` via shared/did_validator.py
- Falha: HTTP 401/403 explícito, nunca fallback

---

*Liga IA+H · 15 Abril 2026*
