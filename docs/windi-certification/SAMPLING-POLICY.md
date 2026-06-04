# SAMPLING-POLICY.md

**Política de Agregação Canónica — Selagem de Eventos no Ledger**
**Sistema:** W-HIOS-TWIN-PROTOCOL-001
**Governance:** `LedgerDisposition.SAMPLED` para `MessageClass.AUDIT_EVENT`
**Estado:** SEALED — §300
**Referência cruzada:** `W-HIOS-TWIN-PROTOCOL-001-CANDIDATE.ts:98-131, 102-109, 227-232`

---

## 0. Princípio

> "Liberdade no quando, obrigação no facto."

A amostragem é **livre no quando** corre. É **obrigatória no registo do facto**
observado. Esta política existe porque o código declara, em `CANDIDATE.ts:102-109`,
que *sampling ad-hoc por implementação NÃO É CONFORME* — a agregação tem de seguir
regra canónica, não a conveniência de cada serviço.

> "Não certificamos intenção. Certificamos comportamento observável."

---

## 1. O que esta política governa

`MessageClass` (`CANDIDATE.ts:98-131`) classifica cada mensagem por disposição no Ledger:

| MessageClass | Disposição | Selagem |
|--------------|-----------|---------|
| `TRANSPORT` | `NONE` | **Nunca** sela |
| `AUDIT_EVENT` | `SAMPLED` | Agregado **antes** de selar |
| `DECISION` | `SEALED` | Receipt individual |
| `STATE_TRANSITION` | `SEALED` | Receipt individual |

Esta política governa **exclusivamente** o ramo `AUDIT_EVENT → SAMPLED`. As classes
`DECISION` e `STATE_TRANSITION` selam individualmente (`SEALED`) e **não** são
amostradas — cada uma gera um receipt. `TRANSPORT` nunca toca o Ledger.

> A fronteira é dura: nenhuma `DECISION` ou `STATE_TRANSITION` pode ser desviada para
> `SAMPLED`. Amostrar uma decisão seria perder o facto que importa. A amostragem
> aplica-se **só** ao ruído de auditoria de alto volume.

---

## 2. Unidade de amostragem

A unidade é **um `AUDIT_EVENT`** — uma `TwinMessage` cujo `message_class` é
`AUDIT_EVENT`. Eventos das outras classes não entram na amostra (§1).

---

## 3. Regra de agregação canónica — MODELO HÍBRIDO (C)

**DECISÃO CONSTITUCIONAL (Human Dragon, 04 Jun 2026):**

A WINDI fixa o **Modelo Híbrido (C)** — Time-Flush Window + Batch Burst:

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `t_window` | **60 segundos** | Janela temporal máxima |
| `n_batch` | **100 eventos** | Tamanho máximo do batch |
| **Gatilho** | O que ocorrer primeiro | Flush imediato |

**Comportamento:**
- Se o buffer atingir 100 eventos → flush e seal imediato
- Se passarem 60 segundos sem atingir 100 → flush e seal do que houver
- O que vier primeiro força a criação do Bloco de Agregação

**Payload do Bloco Agregado:**
- Raiz Merkle dos eventos do lote
- Tupla estatística: `[count, min_latency, max_latency, error_rate]`

---

## 4. Amostragem dos estados de resolução

Cada payload percorre `PayloadResolutionState` (`CANDIDATE.ts:227-232`):

| Estado | Natureza | Disposição |
|--------|----------|------------|
| `PROVISIONAL` | aguarda vault | `SAMPLED` |
| `RESOLVED` | reconciliação OK | `SAMPLED` |
| `FAILED_TIMEOUT` | vault indisponível | `SAMPLED` |
| `FAILED_ABANDONED` | retries esgotados | `SAMPLED` |
| `FAILED_MISMATCH` | **fraude detectada** | **`SEALED` individual** ⚠️ |

### 4.1 Excepção dura — `FAILED_MISMATCH`

**ERRATA-001 (04 Jun 2026):** Um `FAILED_MISMATCH` é a acusação de fraude — o
`payload_hash` não reconcilia com o conteúdo real. **Não pode ser amostrado nem
agregado.**

**Comportamento:**
1. Transição para `FAILED_MISMATCH` dispara **upgrade de severidade imediato**
2. Evento é reclassificado de `AUDIT_EVENT` para `STATE_TRANSITION`
3. Sela com `LedgerDisposition.SEALED` (receipt individual)
4. **Nunca** entra no buffer de agregação

> Razão: agregar uma acusação de fraude com ruído de telemetria seria esconder a
> pedra na sombra. O facto acusatório exige selo próprio, rastreável, isolado.

---

## 5. Isolamento do ATR

**DECISÃO CONSTITUCIONAL (Human Dragon, 04 Jun 2026):**

A amostragem do Ledger **não afecta** os dados que alimentam o cálculo do threshold
ATR (`validation.identity ≥ 0.68`).

**Arquitectura:**
- O sensor ATR lê telemetria em **memória local** (tempo real)
- A agregação `SAMPLED` alivia o peso de gravação no **Ledger físico**
- São pipelines independentes

> O amortecimento de dados não cega os sensores de barramento I9. O `drift_max`
> e o `gap` são calculados sobre dados brutos, não sobre lotes agregados.

---

## 6. Anti-cherry-picking

A regra de agregação híbrida é **determinística e antecipada** — fixada antes de ver
os eventos. Não se escolhe a janela ou o batch que produz o resultado cómodo.

Um auditor que receba o mesmo fluxo de eventos tem de produzir **exactamente** os
mesmos receipts agregados. Qualquer não-determinismo (ex. `Math.random()` na
selecção — proibido, tal como `nonce` exige CSPRNG em `CANDIDATE.ts:369`) é
não-conforme.

---

## 7. Tabela de Conformidade

| Bloqueio | Resolução | Status |
|----------|-----------|--------|
| B1 | Modelo Híbrido (C): t=60s, n=100 | ✅ DECIDIDO |
| B2 | `FAILED_MISMATCH` → `STATE_TRANSITION`/`SEALED` (ERRATA-001) | ✅ DECIDIDO |
| B3 | ATR isolado do sampling (sensores leem memória local) | ✅ DECIDIDO |

---

*Política ancorada em `W-HIOS-TWIN-PROTOCOL-001-CANDIDATE.ts`.*
*AI processa. Human decide. WINDI garante.*
*Liga IA+H · 04 Jun 2026*
