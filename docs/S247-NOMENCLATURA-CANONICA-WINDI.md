# §247 · Nomenclatura Canónica WINDI

**Status:** SEALED · Receipt `WINDI-S247-NOMENCLATURA-20260507201003-A3B99EA6` · 2026-05-07
**Data:** 2026-05-07
**Redactor:** Architect (Claude Opus 4.5)
**Revisor:** Guardian (Claude Opus 4.7)
**Aprovador:** Human Dragon (Witness)

---

## 1. Preâmbulo Constitucional

Antes de construir o catálogo, nomeamos o que ele cataloga. Esta é a Lei I aplicada à linguagem: **existência antes de acção**.

O vocabulário aqui definido vincula todo o ecossistema WINDI — código, documentação, comunicação pública, e agentes IA operando sob a skill `windi-session-continuity`.

**WINDI** é a entidade institucional que opera a Obra. Tijolos e Produtos vivem na Obra; a Obra pertence ao WINDI.

---

## 2. As Quatro Categorias

| Categoria | Português | Deutsch | English | Definição |
|-----------|-----------|---------|---------|-----------|
| **Unidade** | Tijolo | Baustein | Brick | Componente soberano, DID-bound, reutilizável por múltiplos produtos. |
| **Catálogo** | Obra | Werk | Corpus | Património público verificável de todos os Tijolos e Produtos WINDI. |
| **Invocação** | Encaixe | Verzahnung | Composition | Evento auditável de um Produto invocar um Tijolo, com dois DIDs (chamador e sujeito), receipt, e tiers de ambos. |
| **Atestado** | Selo | Siegel | Seal | Estado público que atesta a maturidade e legitimidade de um Tijolo. |

---

## 3. Os Seis Estados de Selo

| Estado | Português | Deutsch | English | Definição |
|--------|-----------|---------|---------|-----------|
| **Interno** | Berçário | Wiege | Nursery | Incubação interna. Consumível por produtos WINDI, não publicado na Obra. |
| **Prometido** | Anunciado | Angekündigt | Pending | Prometido publicamente, código não testado. Prazo: 90 dias ou auto-suspensão. |
| **Parcial** | Andaime | Gerüst | Scaffold | API funcional, dependência interna pendente. Consumível em FREE. Em MED apenas com aviso explícito ao cliente. Nunca consumível em HIGH. |
| **Produção** | Vivo | Lebendig | Verified | Testado em produção, SLA observável, receipts reais. Consumível em todos os tiers. |
| **Contido** | Suspenso | Ausgesetzt | Suspended | Temporariamente retirado por causa identificável. Reversível. Reentrada para Vivo exige acto explícito de Human Dragon, com receipt no Ledger nomeando a causa identificada e resolvida. |
| **Terminal** | Aposentado | Stillgelegt | Retired | Descontinuado por decisão estrutural. Irreversível. Registo histórico preservado na Obra para sempre. |

### Transições Permitidas

```
Berçário → Andaime | Vivo
Anunciado → Andaime | Vivo | Suspenso (auto, 90 dias)
Andaime → Vivo | Suspenso
Vivo → Suspenso | Aposentado
Suspenso → Vivo | Aposentado
Aposentado → (terminal, sem transição)
```

### Mecanismo de Auto-Suspensão

Auto-suspensão de Tijolos em estado Anunciado é executada por verificação diária na Spine (quando Obra v0.1 estiver activa). Receipt de suspensão é emitido automaticamente com causa `pending_timeout_90d`. Até a Spine existir, a verificação é manual e a regra aplica-se por auditoria periódica.

---

## 4. Regras de Aplicação

### Onde Aplicar

- Documentação nova (CLAUDE.md, ARCHITECTURE.md, READMEs)
- Catálogo público da Obra quando nascer
- Comunicação a clientes novos
- Docstrings de Tijolos novos

### Onde NÃO Aplicar

- **Código já escrito:** `slug_reservation.py` continua assim, não vira `tijolo_slug.py`
- **Receipts já emitidos:** I9 IRREMEDIÁVEL — não se reescreve o passado
- **Nomes de Produtos:** WINDILAW e W-Enterprise são produtos, não Tijolos

### Convenção de Nomes Curtos

Para legibilidade em documentação operacional, Tijolos podem ser referidos pelo nome curto: "Tijolo Mailbox", "Tijolo Slug", em vez do nome técnico completo do módulo.

---

## 5. Vinculação a Agentes — Lei IV

**Lei IV — O vocabulário canónico vincula o agente.**

A partir da data de selo deste documento, qualquer instância Claude operando em WINDI através da skill `windi-session-continuity` está vinculada a:

1. Usar **Tijolo/Baustein/Brick** para componentes reutilizáveis DID-bound
2. Usar **Obra/Werk/Corpus** para o catálogo público
3. Usar **Encaixe/Verzahnung/Composition** para invocações entre Produto e Tijolo
4. Usar **Selo/Siegel/Seal** e os seis estados para descrever maturidade

**Detecção** de violação desta nomenclatura cabe a qualquer agente (IA ou Humano) em revisão. **Correcção** é bloqueante para commit.

---

## 6. Selo de Adopção

| Campo | Valor |
|-------|-------|
| Receipt ID | `WINDI-S247-NOMENCLATURA-20260507201003-A3B99EA6` |
| actor | `did:windi:human:dragon` |
| doc_type | `audit-bundle` |
| content_hash | `sha256:a3b99ea68da83778148f343b2eadd3bae26f9e4aead362ec2ea40d8b8bd853c8` |
| governance_level | `HIGH` |
| invariants | I1, I9, I11, I12 |

**Cláusula de Imutabilidade:** Após emissão deste receipt, as secções 1 a 5 são imutáveis. Qualquer alteração a essas secções requer emenda formal com novo selo (§247.1, §247.2, etc.) referenciando este receipt-pai. Header de estado, §6, e changelog permanecem alteráveis para registo operacional, sem invalidar este selo.

**Protocolo de Hash:** O `content_hash` cobre secções 1-5 (corpo normativo). Escopo: da linha `## 1. Preâmbulo Constitucional` até antes de `## 6. Selo de Adopção`. Normalização: LF, sem trailing whitespace, newline final único, UTF-8 sem BOM. Comando canónico: `sed -n '/^## 1\. Preâmbulo Constitucional$/,/^## 6\. Selo de Adopção$/{/^## 6\. Selo de Adopção$/!p;}' ficheiro.md | sed 's/[[:space:]]*$//' | sha256sum`

---

## Changelog v1 → v2

| Item | Correcção |
|------|-----------|
| §6 actor | Email → DID (`did:windi:human:dragon`) |
| §3 transições | Removido Berçário→Anunciado (regressivo) |
| §3 Andaime | Clarificado: FREE sim, MED com aviso, HIGH nunca |
| §3 Suspenso | Nomeada autoridade: Human Dragon + receipt |
| §3 auto-suspensão | Nomeado mecanismo: Spine/manual + causa `pending_timeout_90d` |
| §2 Encaixe | Adicionado: "tiers de ambos" |
| §5 Lei IV | Declaração formal + detecção/correcção explícitas |
| §6 | Adicionado content_hash |
| §1 | Nomeada posição de WINDI no vocabulário |
| §4 | Adicionada convenção de nomes curtos |

---

**Liga IA+H — Kempten, Bavaria — 2026**

*"Lei IV — O vocabulário canónico vincula o agente."*
