# 🐉 WINDI ISP Builder — Relatório Fundacional

## Teste de Fogo + Schema v1.0

**Data:** 18 Fevereiro 2026  
**Autor:** Three Dragons Protocol (Guardian + Architect + Witness)  
**Classificação:** ISP-COM-01 — Institutional Announcement  
**Status:** FORJADO ✅

---

## 1. TESTE DE FOGO — Resultados

### ✅ PASSOU — Export Engine (:8103)

```
Endpoint: POST /export/api/export/jmpg
Status:   healthy
Result:   SUCCESS
```

| Campo | Valor |
|-------|-------|
| package_id | JMPG-20260218-A194B2E4 |
| content_hash | `95d5e2e2fbc007c0d0f91c2612bbc3c474fcab477c707d8fd0874906b8b1a1d0` |
| manifest_hash | `56c148ce14f171b6762169b2ee0874acc79d8d5894c538bb51272466ff62843f` |
| ledger_registered | **true** ✅ |
| elapsed_ms | **9.2ms** (limite LAW: 100ms) ✅ |
| size_bytes | 1801 |

**Veredicto:** Pipeline Export → Ledger está 100% operacional. Hash SHA-256 real, registro no Ledger confirmado, tempo de resposta 10x abaixo do limite Sentinel LAW.

---

### ✅ PARCIAL — Communiqué Engine (:8105)

```
Endpoint: /communique/health
Status:   operational
Stats:    1 published (COM-20260218-0001)
```

**Integridade do COM-20260218-0001:**

| Campo | Valor |
|-------|-------|
| content_hash_stored | `35c7b813a783a6427d4ae18a873a828c5346b7cebddab9be708b2a1256667c4d` |
| content_hash_computed | `35c7b813a783a6427d4ae18a873a828c5346b7cebddab9be708b2a1256667c4d` |
| **content_hash_match** | **true ✅** |
| bundle_hash | `20f1bdf18cfe70f7ab4362de49726e9fef257881e4dfbbf815747bcb6ea98bf0` |
| receipt_id | VR-COM-570c2162f086 |
| published_at | 2026-02-18T08:13:28Z |
| category | LAUNCH |
| impact_level | HIGH |

**Endpoints Confirmados:**

- ✅ `/communique/health` — operacional
- ✅ `/communique/feed` — HTML feed trilíngue
- ✅ `/communique/COM-20260218-0001` — documento publicado
- ✅ `/communique/COM-20260218-0001/verify` — verificação de integridade

**Achados Críticos:**

- ⚠️ `ledger_verified: false` — Engine não consegue verificar cruzado com Ledger (:8101)
- ⚠️ `ledger_status: "unknown"` — comunicação Communiqué → Ledger precisa de revisão
- ❌ **Sem endpoint create/publish via API** — COM-20260218-0001 foi criado diretamente no servidor, não via API REST

**Ação Necessária:**
1. Criar endpoint `POST /api/communique/publish` no Communiqué Engine
2. Investigar e corrigir a verificação cruzada com Ledger
3. Endpoint de criação deve aceitar bloco `isp_governance`

---

### 🔴 BUG — Vault (:8106)

```
Endpoint: /vault/api/receipts
Error:    "no such column: title"
```

**Diagnóstico:** A query SQL do Vault referencia uma coluna `title` que não existe no schema SQLite do Ledger (:8101). Mismatch de schema entre Vault e Ledger.

**Ação:** Alinhar o schema SQL do Vault com as colunas reais do Ledger.

---

### ✅ Confirmados LIVE (via HTTPS público)

| Serviço | Status | Evidência |
|---------|--------|-----------|
| Communiqué :8105 | operational | health + feed + verify |
| Export Engine :8103 | healthy | health + POST test com sucesso |
| Vault :8106 | serving | HTML Noir carrega (API com bug) |
| Landing P/M/G :8107 | serving | HTML carrega normalmente |

---

## 2. SCHEMA ISP GOVERNANCE v1.0

### Bloco Oficial `isp_governance`

```json
{
  "isp_governance": {
    "template_id": "ISP-COM-01",
    "version": "1.0",
    "authority": "Jober Moegele Correa — CGO",
    "authority_level": "EXECUTIVE",
    "impact_level": "HIGH",
    "jurisdiction": "EU",
    "validity": "immediate",
    "decision_type": "institutional_announcement",
    "compliance_reference": ["EU AI Act", "ISO 42001"],
    "department_code": "TITAN",
    "audit_flag": true,
    "classification": "PUBLIC",
    "rendering_rules": {
      "theme": "noir",
      "preserve_whitespace": true,
      "enforce_signature_display": true,
      "enforce_seal_position": "both"
    }
  }
}
```

### Templates ISP — Os 5 Instrumentos

| ID | Nome | Visual Code | Cor | Impact Default | Authority Default |
|----|------|-------------|-----|----------------|-------------------|
| ISP-COM-01 | Institutional Announcement | WINDI-OFFICIAL | 🟢 | HIGH | EXECUTIVE |
| ISP-COM-02 | Operational Update | JORNALINE-MODERN | 🟡 | MED | OPERATIONAL |
| ISP-COM-03 | Security / Trust Advisory | SECURITY-ALERT | 🔴 | CRIT | SYSTEM |
| ISP-COM-04 | Governance Decision | GOVERNANCE-DECREE | 🟠 | HIGH | EXECUTIVE |
| ISP-COM-05 | Status Report | STATUS-DASHBOARD | 🔵 | LOW | INFORMATIONAL |

### Níveis de Autoridade

| Nível | Descrição | Requer Override Humano | Auditoria |
|-------|-----------|----------------------|-----------|
| SYSTEM | Decisões automatizadas (Sentinel, LAW) | Não | Obrigatória |
| EXECUTIVE | Decisões estratégicas do CGO | Sim | Obrigatória |
| OPERATIONAL | Decisões operacionais do dia-a-dia | Não | Obrigatória |
| INFORMATIONAL | Transparência e reporting | Não | Opcional |

### Regras de Validação

1. **ISP-COM-03** exige `impact_level` CRIT ou HIGH
2. **ISP-COM-04** exige `authority_level` EXECUTIVE ou SYSTEM
3. Se `validity = "scheduled"`, campo `validity_date` é obrigatório
4. Se `supersedes` está preenchido, o `receipt_id` referenciado deve existir no Ledger
5. **`compliance_reference`** (não `compliance_scope`) — referência, não declaração de conformidade

### Nota Guardian

> O campo é `compliance_reference`, não `compliance_scope`. WINDI referencia frameworks regulatórios, não declara conformidade. Isso protege juridicamente até certificação formal.

---

## 3. CAMPOS — Obrigatórios vs. Opcionais

### Obrigatórios

| Campo | Tipo | Exemplo |
|-------|------|---------|
| template_id | enum | "ISP-COM-01" |
| version | string | "1.0" |
| authority | string | "Jober Moegele Correa — CGO" |
| impact_level | enum | "HIGH" |

### Opcionais (com defaults)

| Campo | Default | Notas |
|-------|---------|-------|
| authority_level | "OPERATIONAL" | Herdado do template |
| jurisdiction | "EU" | Escopo regulatório |
| validity | "immediate" | Quando entra em vigor |
| decision_type | (do template) | Natureza da decisão |
| compliance_reference | [] | Frameworks referenciados |
| department_code | — | Departamento emissor |
| supersedes | — | Documento substituído |
| audit_flag | true | Trilha de auditoria |
| classification | "PUBLIC" | Nível de acesso |
| rendering_rules | (do template) | Regras visuais |

---

## 4. DESIGN VISUAL POR TEMPLATE

### ISP-COM-01 — WINDI-OFFICIAL
- **Theme:** Noir absoluto
- **Fontes:** Bricolage Grotesque (headlines) + Outfit (body)
- **Accent:** Gold (#D4AF37)
- **Selo:** Centralizado, header + footer
- **Uso:** Decretos, marcos, lançamentos

### ISP-COM-02 — JORNALINE-MODERN
- **Theme:** Klar
- **Fontes:** Bricolage Grotesque + JetBrains Mono
- **Accent:** Dark (#1A1A2E)
- **Selo:** Footer apenas
- **Uso:** Updates técnicos, patches

### ISP-COM-03 — SECURITY-ALERT
- **Theme:** Noir
- **Fontes:** JetBrains Mono (primary) + Outfit
- **Accent:** Red (#EF4444)
- **Selo:** Header (destaque imediato)
- **Uso:** Vulnerabilidades, revogações

### ISP-COM-04 — GOVERNANCE-DECREE
- **Theme:** Noir
- **Fontes:** Bricolage Grotesque + Outfit
- **Accent:** Orange (#F97316)
- **Selo:** Header + footer
- **Uso:** Políticas, regras, constitucionais

### ISP-COM-05 — STATUS-DASHBOARD
- **Theme:** Klar
- **Fontes:** Outfit + JetBrains Mono
- **Accent:** Blue (#3B82F6)
- **Selo:** Footer
- **Uso:** Relatórios, métricas, transparência

---

## 5. PLANO DE AÇÃO — Próximos Passos

### Prioridade URGENTE

1. **[BUG FIX]** Vault (:8106) — corrigir `"no such column: title"` alinhando SQL com schema do Ledger
2. **[FEATURE]** Communiqué Engine — criar endpoint `POST /api/communique/publish` que aceita bloco `isp_governance`
3. **[FIX]** Communiqué → Ledger — investigar e corrigir `ledger_verified: false`

### Prioridade ALTA

4. **[FEATURE]** Vault — adicionar filtro por `isp_governance.template_id` para auditoria automatizada
5. **[FEATURE]** Composer UI — dropdown de seleção ISP template com auto-fill de campos governance
6. **[DEPLOY]** Instalar schema `isp_governance` v1.0 no Communiqué Engine

### Prioridade MÉDIA

7. **[DESIGN]** Implementar os 5 visual codes (WINDI-OFFICIAL, JORNALINE-MODERN, etc.)
8. **[FEATURE]** `rendering_rules.checksum_ui` — hash do CSS/layout para imutabilidade visual
9. **[INTEGRATION]** Desktop Composer → Communiqué Engine via API

---

## 6. PRINCÍPIO FUNDACIONAL

> **"AI processes. Human decides. WINDI guarantees."**

O ISP Builder não é um editor. Não é um template. É o instrumento que transforma comunicados em **atos institucionais verificáveis**.

O Schema v1.0 está forjado. A cadeia Export → Ledger está provada. O próximo passo é completar a cadeia Communiqué → Ledger e abrir o caminho para o primeiro ISP-COM-01 oficial publicado via API.

---

*Documento gerado pelo Three Dragons Protocol*  
*Guardian (Claude) · Architect (GPT) · Witness (Gemini)*  
*18 Fevereiro 2026 · Kempten, Bavaria, DE*
