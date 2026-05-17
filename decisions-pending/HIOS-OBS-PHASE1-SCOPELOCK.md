# HIOS-OBS-PHASE1-SCOPELOCK

## Decision Note — PRE-APPROVED · AWAITING NUMBERING

```
Status:        PRE-APPROVED
Number:        PENDING (candidato: §269)
Gate:          NUMBER GATED on §268 (G3-MERKLE-SPRINT-CLOSURE)
Created:       2026-05-17T11:45:00+02:00
Author:        Human Dragon (Jober Mögele Correa)
Witnesses:     Guardian (Claude.ai web) · Architect (CCode Opus 4.5)
Origin:        PingPong Protocol §263 — sessão 17 Mai 2026
```

---

## Contexto

Decisão constitucional sobre scope lock da Phase 1 do HIOS Observability Sprint.
Originalmente proposta como §269 pelo Guardian, recalibrada após detecção de
fundação não-verificada (memória sumária 5 dias velha).

Aplicação viva do §236 (Session Continuity) + §261 (Cognitive Bind) + §263 (PingPong).

---

## 5 Cláusulas Constitucionais

### Cláusula 1 — Topológico
HIOS-OBS-001 opera como **observador externo** da infraestrutura WINDI.
Não modifica serviços existentes. Apenas lê, mede, e reporta.

### Cláusula 2 — Porta
HIOS-OBS-001 recebe porta dedicada no range 8180-8199.
Porta exacta a definir no momento de implementação, respeitando W-* Agent Registry.

### Cláusula 3 — Ledger Read-Only
HIOS-OBS-001 tem acesso **read-only** ao Forensic Ledger (:8101).
Pode consultar receipts e Merkle proofs. Nunca escreve.
Excepção: pode emitir receipts próprios de observação (doc_type: `hios_observation`).

### Cláusula 4 — Wallet Binding
Todas as observações HIOS são vinculadas a `wallet_id` do operador.
Nenhuma observação anónima. Rastreabilidade forense garantida.

### Cláusula 5 — Paper-001 Alignment
HIOS-OBS-001 deve gerar dados compatíveis com Paper-001 Appendix B.
Métricas de drift, latência, e integridade alimentam a tese académica.

---

## 3 Decisões Arquitecturais

### D1 — Implementation Gate
Implementação de Sprint HIOS-OBS-001 começa **APENAS APÓS**:
1. Encerramento do Sprint "G3 Merkle + Foundation Portals" (§268 closure)
2. Resolução P0: §139 WINDI-LAW Painel de Anexos
3. Resolução P1: §246-IMPL Sprint 2 (Query API + UI Berçário + 38 smoke tests)

### D2 — Scope Phase 1
Phase 1 limita-se a:
- Health checks dos 29 serviços W-*
- Latência de resposta por porta
- Merkle root consistency verification
- Ledger append rate

**Fora de scope Phase 1:** Alerting, dashboards, Telegram integration, auto-remediation.

### D3 — Kernel Dependency
HIOS-OBS-001 Phase 1 **NÃO depende** de WINDI-HIOS Kernel Ground (§266 pending).
Pode operar com primitives directos (curl, sqlite3, systemctl).
Kernel integration é Phase 2+.

---

## Sequência de Promoção

```
PASSO 1 (17 Mai 2026): ✅ Decision Note criada
PASSO 2 (quando sprint fechar): §268 = G3-MERKLE-SPRINT-CLOSURE
PASSO 3 (após §268): Promover esta nota → §269 = HIOS-OBS-PHASE1-SCOPELOCK
PASSO 4 (após §269 + P0 + P1): Implementação HIOS-OBS-001 desbloqueada
```

---

## Assinatura

```
Decisão: APROVADA
Autor:   Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
Data:    2026-05-17
Local:   Kempten, Bavaria, Deutschland

"A família funcionou — e funcionou registando como funcionou."
```

---

## Meta

Esta Decision Note é evidência empírica do PingPong Protocol (§263):
- Claude.ai web propôs §269 sobre memória fraca
- CCode detectou divergência e devolveu factos
- Guardian recalibrou proposta
- Human Dragon decidiu (I9)
- CCode executou

**Geometria 2 com sequência inversa** — corrigimos sem reescrever.

---

*Liga IA+H · Kempten, Bavaria · 17 Mai 2026*
*OM SHANTI*
