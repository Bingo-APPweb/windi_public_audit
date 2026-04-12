# DECRETO-001 — A Árvore Viva
## Lei Constitucional de Interconexão Orgânica WINDI
**Selado:** 12 Abril 2026 · Liga IA+H · Kempten, Bavaria
**Autor:** Human Dragon (Jober Mögele Correa) · CGO
**Invariantes:** I1, I9, I11, I12, I14

---

> *"O servidor WINDI é uma Árvore Viva. Cada serviço é um galho.*
> *A seiva (DID) flui do tronco às folhas. Nenhum galho vive sozinho.*
> *Quando um fruto amadurece, toda a árvore sabe."*
> — **Human Dragon** · 12 Abril 2026

---

## Artigo 1 — Definição da Árvore

O servidor WINDI (`windi-domain.com`) é uma **Árvore Viva** composta por:

| Componente | Significado | Exemplos |
|------------|-------------|----------|
| **Tronco** | Forensic Ledger `:8101` | Imutável, distribui verdade |
| **Seiva** | DID (Decentralized Identifier) | Flui por todos os galhos |
| **Galhos** | Produtos/Órgãos | W-Enterprise, WINDI-LAW, Travel |
| **Folhas** | Endpoints/Features | `/api/*`, `/vera/*`, UI pages |
| **Frutos** | Receipts selados | PHO, documentos, provas |
| **Raízes** | W-SEC-001 + Verify Public | Segurança e verificação |

---

## Artigo 2 — Lei da Origem Preservada

**Todo órgão WINDI deve preservar e respeitar a origem do utilizador.**

```
REGRA: Quando um utilizador sai de um órgão para outro,
       o órgão de destino DEVE saber de onde ele veio
       e oferecer caminho de retorno.

IMPLEMENTAÇÃO:
  1. URL param: ?return=/enterprise/
  2. sessionStorage: windi_origin
  3. Referrer detection como fallback
  4. Default: produto mais próximo na hierarquia
```

### 2.1 — Mapa de Origens

```javascript
const WINDI_TREE = {
  '/enterprise/': { name: 'W-Enterprise', port: 8150, tier: 'organ' },
  '/law/':        { name: 'WINDI-LAW',    port: 8122, tier: 'organ' },
  '/travel/':     { name: 'WINDI Travel', port: 8126, tier: 'organ' },
  '/wallet/':     { name: 'WINDI Wallet', port: 8099, tier: 'root' },
  '/sec/':        { name: 'W-SEC-001',    port: 8144, tier: 'root' },
  '/verify-public/': { name: 'Verify',    port: 8145, tier: 'leaf' },
  '/dev-api/':    { name: 'W-DEV-API',    port: 8200, tier: 'leaf' },
  '/desktop/':    { name: 'GEN7 Legacy',  port: 8119, tier: 'deprecated' },
};
```

### 2.2 — Função Canónica

```javascript
// windi-tree.js — Canonical Origin Detection
function detectWindiOrigin() {
  // 1. URL param
  const params = new URLSearchParams(window.location.search);
  const returnParam = params.get('return');
  if (returnParam?.startsWith('/')) return returnParam;

  // 2. sessionStorage
  const stored = sessionStorage.getItem('windi_origin');
  if (stored) return stored;

  // 3. Referrer
  const ref = document.referrer;
  if (ref?.includes('windi-domain.com')) {
    const path = new URL(ref).pathname;
    for (const [route, info] of Object.entries(WINDI_TREE)) {
      if (path.startsWith(route) && info.tier !== 'deprecated') {
        return route;
      }
    }
  }

  // 4. Default — never desktop (deprecated)
  return '/enterprise/';
}

function storeWindiOrigin() {
  const origin = detectWindiOrigin();
  sessionStorage.setItem('windi_origin', origin);
  return origin;
}

function goToOrigin() {
  const origin = sessionStorage.getItem('windi_origin') || '/enterprise/';
  window.location.href = origin;
}
```

---

## Artigo 3 — Lei da Navegação Universal

**Todo órgão WINDI deve oferecer navegação aos outros órgãos da árvore.**

```
REGRA: O sidebar/menu de cada órgão DEVE incluir secção
       "Server Operations" com links para:
       - W-SEC-001 (segurança)
       - W-DEV-API (developers)
       - Verify Public (verificação)
       - Outros órgãos relevantes

PROIBIDO: Links para /desktop/ (GEN7 deprecated)
          Excepto para migração documentada
```

### 3.1 — Navegação Canónica

```html
<!-- Sidebar section for all WINDI organs -->
<div class="sidebar-section" data-i18n="nav_server">Server Operations</div>
<a class="nav-item" href="/sec/dashboard/" target="_blank">
  <div class="nav-dot" style="background: var(--critical)"></div>
  🛡 W-SEC-001 · NOIR OPS
</a>
<a class="nav-item" href="/dev-api/" target="_blank">
  <div class="nav-dot" style="background: var(--gold)"></div>
  ⚡ W-DEV-API · Developers
</a>
<a class="nav-item" href="/verify-public/" target="_blank">
  <div class="nav-dot" style="background: var(--ok)"></div>
  ✓ Verify Public
</a>
```

---

## Artigo 4 — Lei da Seiva DID

**O DID flui por toda a árvore. Um DID válido num órgão é válido em todos.**

```
REGRA: Cross-validation obrigatória.
       Se DID existe em WINDI-LAW → válido em W-Enterprise
       Se DID existe em Wallet → válido em Travel
       Um DID, uma identidade, toda a árvore.

IMPLEMENTAÇÃO:
  1. Cada órgão tenta validação local
  2. Se falha, cross-valida com WINDI-LAW (:8122)
  3. Se falha, cross-valida com Wallet (:8099)
  4. Graceful pass para formato válido (did:windi:uuid)
```

### 4.1 — Endpoint de Cross-Validation

```python
# Canonical cross-validation pattern
WINDI_IDENTITY_GATES = [
    "http://localhost:8122",  # WINDI-LAW (primary)
    "http://localhost:8099",  # Wallet
    "http://localhost:8096",  # W-SESSION-001
]

async def cross_validate_did(did: str) -> bool:
    for gate_url in WINDI_IDENTITY_GATES:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{gate_url}/identity/{did}")
                if r.status_code == 200:
                    return True
        except:
            continue
    return False
```

---

## Artigo 5 — Lei dos Frutos Partilhados

**Quando um fruto (receipt) é selado, toda a árvore pode verificá-lo.**

```
REGRA: Receipts selados no Ledger (:8101) são verificáveis
       através de Verify Public (:8145) por qualquer pessoa,
       de qualquer órgão, sem autenticação.

ENDPOINT UNIVERSAL: /verify-public/?id={receipt_id}
```

---

## Artigo 6 — Proibições

| Acção | Motivo | Alternativa |
|-------|--------|-------------|
| Link para `/desktop/` | GEN7 deprecated | `/enterprise/` |
| DID hardcoded | Viola I14 | Cross-validation |
| Órgão isolado | Viola Árvore Viva | Implementar navegação |
| Return para origem externa | Segurança | Só origens WINDI |

---

## Artigo 7 — Verificação de Conformidade

**Skill `/tree-health` verifica se todos os órgãos seguem o Decreto.**

```bash
# Verificar conformidade da Árvore
curl https://windi-domain.com/api/tree/health

# Response esperado:
{
  "decree": "DECREE-001-LIVING-TREE",
  "status": "healthy",
  "organs": {
    "enterprise": { "origin_detection": true, "navigation": true, "did_cross": true },
    "law": { "origin_detection": true, "navigation": true, "did_cross": true },
    "travel": { "origin_detection": true, "navigation": true, "did_cross": true },
    "wallet": { "origin_detection": true, "navigation": true, "did_cross": true }
  },
  "sealed_at": "2026-04-12T..."
}
```

---

## Selagem

```
DECRETO: DECREE-001-LIVING-TREE
HASH: sha256:[será calculado no commit]
INVARIANTES: I1 (Human Sovereignty), I9 (Human Approval),
             I11 (Forensic Permanence), I12 (Language Sovereign),
             I14 (Explicit Failure)
STATUS: CONSTITUTIONAL · IRREMEDIÁVEL
```

---

*"A Árvore cresce. A seiva flui. Os frutos amadurecem.*
*Cada galho alimenta os outros. Nenhum vive sozinho."*

**Liga IA+H · Kempten, Bavaria · 2026**
