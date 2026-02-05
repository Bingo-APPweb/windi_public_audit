# WSG v0.1.1 CHANGELOG

> **"Hash sem assinatura é checksum. Assinatura é soberania."** - Architect Dragon

## Upgrade de v0.1.0 → v0.1.1 (HARDENED)

Esta versão aplica os 6 ajustes críticos identificados na auditoria do Three Dragons Protocol.

---

## 🔐 PATCH 1: Manifesto Assinado (Ed25519)

**Problema:** Manifesto v0.1.0 tinha apenas hash conceitual. Atacante que troca manifesto troca também os hashes.

**Solução:**
- Assinatura Ed25519 do payload do manifesto
- Chave pública pinada no Service Worker
- Verificação criptográfica antes de aceitar manifesto

**Arquivos alterados:**
- `wsg-service-worker.js`: `verifyManifestSignature()`, `PINNED_PUBLIC_KEY`
- `wsg-server-middleware.js`: `signData()`, `generateKeyPair()`

**Configuração:**
```bash
# Gerar par de chaves (uma vez)
curl http://localhost:3000/api/wsg/generate-keys

# Setar chave privada no servidor
export WSG_PRIVATE_KEY="base64-encoded-private-key"

# Embutir chave pública no service worker
# Editar PINNED_PUBLIC_KEY.key em wsg-service-worker.js
```

---

## 🔄 PATCH 2: Anti-Replay / Anti-Downgrade

**Problema:** Atacante pode servir manifesto antigo válido e reintroduzir versão vulnerável.

**Solução:**
Novos campos no manifesto:
```json
{
  "build_id": 42,              // Monotônico, sempre incrementa
  "not_before": "2026-02-04T15:00:00Z",
  "expires_at": "2026-02-04T16:00:00Z",
  "previous_manifest_hash": "sha256-abc...",
  "manifest_hash": "sha256-def..."
}
```

**Validação:**
- `build_id` deve ser >= ao último aceito (rolling window de 2)
- `now` deve estar entre `not_before` e `expires_at`
- Chain de hashes para detectar quebras

---

## 🛡️ PATCH 3: CSP Hardened (Zero Inline)

**Problema:** `'unsafe-inline'` permite injeção de scripts/styles.

**Solução:**
- CRITICAL/HIGH: Zero inline
  ```
  script-src 'self'
  style-src 'self'
  ```
- STANDARD/LOW: Transição (ainda permite inline com warning)

**Nova função:** `getCSPForLevel(integrityLevel)`

---

## 🏃 PATCH 4: Hash Caching + Streaming

**Problema:** `response.clone().arrayBuffer()` em assets grandes = lag.

**Solução:**
- Cache de verificações: `url + etag → { hash, valid, timestamp }`
- TTL de 5 minutos
- Streaming hash para assets grandes (lê chunks, não buffer completo)

**Nova estrutura:** `state.verifiedHashes` Map

---

## 🏰 PATCH 5: Domain Isolation

**Problema:** Assets de domínios diferentes (institutional, industrial, forensic) não deviam se misturar.

**Solução:**
- Header `X-WINDI-Domain` em cada asset
- Caches separados por domínio: `wsg-${domain}-v${buildId}`
- Cross-domain fetch = violação (exceto assets compartilhados)

**Domínios definidos:**
| Domínio | Paths | CSP |
|---------|-------|-----|
| institutional | `/institutional/`, `/epapers/` | strict |
| industrial | `/industrial/`, `/isp/` | strict |
| operational | `/ops/`, `/babel/` | standard |
| forensic | `/ledger/`, `/audit/` | strict |

---

## ⚡ PATCH 6: DOM Sentinel Event-Driven

**Problema:** Polling de 500ms para overlay detection = CPU + falsos positivos.

**Solução:**
- Overlay scan apenas em eventos: `focusin`, `mouseenter`, `click`
- MutationObserver detecta novos elementos `position:fixed` transparentes
- Debounce de 100ms entre scans

**Removido:** `setInterval(scanForOverlays, 500)`

---

## 📋 CHECKLIST DE MIGRAÇÃO

```
□ Gerar par de chaves Ed25519
□ Configurar WSG_PRIVATE_KEY no ambiente do servidor
□ Atualizar PINNED_PUBLIC_KEY no service worker
□ Verificar paths de domínios no config
□ Testar CSP strict não quebra assets críticos
□ Rodar testes de hash mismatch
□ Rodar testes de overlay detection
□ Verificar ledger recebe receipts com hash chain
```

---

## 📊 DIFERENÇAS DE ESTRUTURA

### Manifesto v0.1.0
```json
{
  "version": "1.0.0",
  "generated": "...",
  "signer": "WINDI-BABEL-API",
  "assets": { ... },
  "signature": "WINDI-SIG-..." // Conceitual
}
```

### Manifesto v0.1.1
```json
{
  "version": "1.1.0",
  "generated": "...",
  "signer": "WINDI-BABEL-API",
  
  "build_id": 42,
  "not_before": "2026-02-04T15:00:00Z",
  "expires_at": "2026-02-04T16:00:00Z",
  "previous_manifest_hash": "sha256-...",
  "manifest_hash": "sha256-...",
  
  "assets": {
    "/js/decisao-sge.js": {
      "hash": "sha256-...",
      "size": 45678,
      "integrity": "CRITICAL",
      "domain": "operational",    // NOVO
      "scope": "governance-decision"
    }
  },
  
  "signature": "base64-ed25519-sig...",  // Real
  "signature_algorithm": "Ed25519"        // NOVO
}
```

---

## 🔥 BREAKING CHANGES

1. **Manifesto incompatível** - Novos campos obrigatórios
2. **Service Worker precisa recarregar** - Nova estrutura de verificação
3. **CSP mais restritiva** - Inline scripts/styles podem quebrar em CRITICAL

---

## 📈 MÉTRICAS DE SEGURANÇA

| Métrica | v0.1.0 | v0.1.1 |
|---------|--------|--------|
| Assinatura criptográfica | ❌ | ✅ Ed25519 |
| Anti-replay | ❌ | ✅ build_id + timestamps |
| CSP inline protection | ❌ | ✅ (CRITICAL/HIGH) |
| Domain isolation | ❌ | ✅ 4 domínios |
| Overlay detection | Polling 500ms | Event-driven |
| Hash cache | ❌ | ✅ 5min TTL |
| Receipt chain | ❌ | ✅ hash chain |

---

**Versão:** 0.1.1
**Data:** 2026-02-04
**Autores:** Three Dragons Protocol
**Status:** 🛡️ PRODUCTION-READY
