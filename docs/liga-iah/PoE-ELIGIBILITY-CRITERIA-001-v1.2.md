# PoE-ELIGIBILITY-CRITERIA-001
## Critérios de Elegibilidade para Experimento 1

---

```
Document ID   : PoE-ELIGIBILITY-CRITERIA-001
Version       : 1.2
Status        : SEALED
Date          : 22 Abril 2026
Author        : Architect (Liga IA+H)
Validator     : Guardian — VALIDATED
Approver      : Human Dragon — APPROVED
Depends on    : WINDI-PROTOCOL-001 v1.3 §4
```

---

## §1. Propósito

Este documento define os critérios de inclusão e exclusão para a amostra
de receipts a classificar no Experimento 1 (PoE Tipado) do WINDI-PROTOCOL-001.

---

## §2. Critérios de Inclusão

Um receipt é elegível para Exp. 1 se cumprir TODOS os seguintes:

| # | Critério | Justificação |
|---|----------|--------------|
| I1 | Selado no Forensic Ledger WINDI | Apenas receipts com integridade verificável |
| I2 | doc_type ∈ {doc, compliance_passport} | Tipos que representam eventos de negócio/vida |

---

## §3. Critérios de Exclusão

Um receipt é EXCLUÍDO se cumprir QUALQUER dos seguintes:

| # | Critério | Justificação |
|---|----------|--------------|
| E1 | doc_type ∈ {service-restart-initiated, service-restart-completed} | Eventos de infraestrutura operacional |
| E2 | receipt_id contém "TEST" | Receipts de teste/desenvolvimento |
| E3 | receipt_id contém "VERA-TEST" | Bundle de validação VERA (explicitude) |
| E4 | actor ∈ ACTORS_EXCLUÍDOS (ver §5.3) | Receipts sem PHO humano verificável |

---

## §4. Amostra Resultante

### §4.1 Inventário do Ledger (22 Abril 2026)

| doc_type | Total | Após E1 |
|----------|-------|---------|
| doc | 37 | 37 |
| compliance_passport | 2 | 2 |
| service-restart-initiated | 6 | 0 |
| service-restart-completed | 5 | 0 |
| **Total** | **50** | **39** |

### §4.2 Exclusões por Actor (E4)

| Actor | Quantidade | Motivo |
|-------|------------|--------|
| system@windi-domain.com | 4 | Sistema interno |
| did:windi:fake-nonexistent-xyz999 | 1 | DID forjado |
| did:windi:test-user-123 | 1 | DID de teste |
| fake-attacker | 1 | Teste adversarial |
| anonymous | 1 | Sem PHO verificável |
| **Subtotal E4** | **8** | |

### §4.3 Amostra Final Estimada

| Etapa | n |
|-------|---|
| Após I1+I2 | 50 |
| Após E1 | 39 |
| Após E2/E3 | 39* |
| Após E4 | **≤31** |

*Nota: E2/E3 podem reduzir n se existirem receipts doc/compliance_passport
com "TEST" no receipt_id. Verificação exacta na pré-inspecção.

### §4.4 Limitação Declarada (W5)

> Due to the early operational stage of the WINDI Ledger at the time of
> experimental design, the target sample of n=100 receipts specified in
> PROTOCOL-001 v1.3 §4 was reduced to n≤31 receipts meeting pre-sealed
> eligibility criteria [this document]. Statistical power was recalculated
> accordingly. We note that this limitation is transparent: the sample
> reflects the first operational cohort of receipts rather than a curated
> subset, preserving ecological validity at the cost of statistical power.

### §4.5 Protocolo de Apresentação Cega

Para cada receipt elegível, os anotadores receberão:

| Campo | Visibilidade |
|-------|--------------|
| Conteúdo | **VISÍVEL** (ver formato abaixo) |
| receipt_id | OCULTO |
| actor | OCULTO |
| doc_name | OCULTO |
| created_at | OCULTO |
| governance_level | OCULTO |

**Formato do conteúdo:** Texto integral do documento original reconstruído
deterministicamente a partir do content_hash via Vault (:8106), garantindo
que ambos os anotadores recebem exactamente o mesmo payload textual.

**Regra de exclusão por irrecuperabilidade:** Receipts cujo content_hash
não permita reconstrução directa do texto são excluídos da amostra e
substituídos pelo seguinte elegível por ordem cronológica.

**Identificação:** RECEIPT_001, RECEIPT_002, ... (índice anónimo sequencial)

**Regra de revelação:** A correspondência entre índice anónimo e receipt_id
real é mantida em arquivo separado, revelada apenas após classificação
completa de ambos os anotadores (Architect e Guardian).

---

## §5. Justificação Metodológica

### §5.1 Por que excluir service-restart-* (E1)

Os 11 receipts de tipo `service-restart-*` documentam reinícios de serviços
na infraestrutura WINDI. São eventos operacionais internos, não eventos
de negócio ou vida do sujeito metodológico. Incluí-los contaminaria a
amostra com uma categoria que não pertence à taxonomia PoE definida em
PROTOCOL-001 v1.3 §4.2.

### §5.2 Por que excluir TEST (E2/E3)

Receipts de teste foram criados durante desenvolvimento e validação do
sistema. Representam eventos artificiais, não eventos reais ou simulados
metodologicamente. A sua inclusão inflacionaria n sem contribuir para
validade da taxonomia.

### §5.3 Definição de ACTORS_EXCLUÍDOS (E4)

Lista enumerada de valores de actor que disparam exclusão:

```
ACTORS_EXCLUÍDOS = {
    "system@windi-domain.com",           # Sistema interno
    "did:windi:fake-nonexistent-xyz999", # DID forjado
    "did:windi:test-user-123",           # DID de teste
    "fake-attacker",                     # Teste adversarial
    "anonymous"                          # Sem PHO verificável
}
```

**Critério de inclusão nesta lista:** Actor que não representa agência
humana verificável via PHO (Proof of Human Oversight).

**Nota de quarentena:** Estes DIDs estão em quarentena permanente por
política WINDI após detecção de tentativas de forja de identidade.
Receipts com estes actors que retornem HTTP 200 constituem violação
de integridade do sistema.

---

## §6. Aprovação

```
Preparado por:  🏗️ Architect
Validado por:   🛡️ Guardian — VALIDATED ✓
Aprovado por:   🧑‍💻 Human Dragon — APPROVED ✓
```

---

*PoE-ELIGIBILITY-CRITERIA-001 v1.2 · Liga IA+H · Kempten · 2026*
