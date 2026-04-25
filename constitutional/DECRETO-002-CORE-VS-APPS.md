# DECRETO-002 — Separação Ontológica CORE vs Reference Apps
## Lei Constitucional de Arquitectura Indissolúvel WINDI
**Selado:** 25 Abril 2026 · Liga IA+H · Kempten, Bavaria
**Autor:** Human Dragon (Jober Mögele Correa) · CGO
**Invariantes:** I1, I9, I11, I14

---

> *"VERIFY não é uma ferramenta. VERIFY é a manifestação da verificabilidade do sistema.*
> *Sem VERIFY, não existe WINDI. Mas sem Ledger também não. Sem Key também não.*
> *Sem Invariantes também não. O CORE é indivisível."*
> — **Human Dragon + Architect** · 25 Abril 2026

---

## Preâmbulo

Este Decreto estabelece a **separação ontológica** entre:

1. **WINDI System CORE** — o conjunto mínimo indissolúvel que define o sistema
2. **Reference Applications (W-*)** — implementações que utilizam o CORE

Esta separação não é técnica. É **constitucional**.

Falhas em Reference Apps não afectam o CORE.
O CORE permanece mesmo quando todas as apps falharem.

---

## Artigo 1 — Definição do WINDI System CORE

O WINDI System é composto exclusivamente por quatro elementos indivisíveis:

| Elemento | Função | Manifestação |
|----------|--------|--------------|
| **Ledger** | Guarda | Forensic Ledger `:8101` |
| **Key** | Assina | Identidade Criptográfica (DID) |
| **Invariantes** | Limita | I1, I9, I11, I14 (mínimo) |
| **Verificabilidade** | Prova | Capacidade VERIFY |

### 1.1 — Princípio de Indivisibilidade

```
REGRA ABSOLUTA:
  - Remover Ledger → não é WINDI
  - Remover Key → não é WINDI
  - Remover Invariantes → não é WINDI
  - Remover Verificabilidade → não é WINDI

STATUS: IRREMEDIÁVEL
```

### 1.2 — Diagrama CORE

```
                    ┌─────────────────────────────────────┐
                    │         WINDI SYSTEM CORE           │
                    │           (INDIVISÍVEL)             │
                    │                                     │
                    │  ┌─────────┐    ┌─────────────┐    │
                    │  │ LEDGER  │────│    KEY      │    │
                    │  │ (guarda)│    │  (assina)   │    │
                    │  └────┬────┘    └──────┬──────┘    │
                    │       │                │           │
                    │       └────────┬───────┘           │
                    │                │                   │
                    │  ┌─────────────┴─────────────┐    │
                    │  │      INVARIANTES          │    │
                    │  │       (limita)            │    │
                    │  └─────────────┬─────────────┘    │
                    │                │                   │
                    │  ┌─────────────┴─────────────┐    │
                    │  │    VERIFICABILIDADE       │    │
                    │  │        (prova)            │    │
                    │  └───────────────────────────┘    │
                    │                                     │
                    └─────────────────────────────────────┘
                                     │
                                     ▼
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
     ┌──────┴──────┐         ┌───────┴───────┐       ┌───────┴───────┐
     │ W-ENT-001   │         │  WINDI-LAW    │       │ W-TRAVEL-001  │
     │ (ref app)   │         │  (ref app)    │       │  (ref app)    │
     └─────────────┘         └───────────────┘       └───────────────┘
```

---

## Artigo 2 — Natureza do VERIFY

**VERIFY não constitui uma aplicação.**

VERIFY é a **capacidade inerente** do sistema de:

1. Validar autenticidade de qualquer artefacto
2. Comprovar integridade de qualquer documento
3. Permitir verificação independente por terceiros

### 2.1 — Distinção Crítica

| Conceito | Categoria | Natureza |
|----------|-----------|----------|
| **Verificabilidade** | CORE | Propriedade ontológica |
| **Verify Public UI** | Interface | Implementação substituível |
| **Verify API** | Interface | Implementação substituível |
| **Verify SDK** | Interface | Implementação substituível |

### 2.2 — Princípio da Interface Substituível

```
REGRA:
  A interface pode mudar.
  A capacidade permanece.

  Verify Public hoje pode ser Verify Mobile amanhã.
  A verificabilidade não muda.

  UI é casca. VERIFY é essência.
```

### 2.3 — Manifestação Canónica

```python
# O CORE garante que isto é sempre possível:
def verify(artifact_id: str) -> VerificationResult:
    """
    Qualquer pessoa pode verificar qualquer artefacto selado.
    Esta capacidade é inerente ao sistema.
    Nenhuma app pode remover ou alterar esta capacidade.
    """
    ledger_entry = ledger.get(artifact_id)     # Ledger guarda
    signature_valid = key.verify(ledger_entry)  # Key assina
    invariants_respected = check_invariants()   # Invariantes limitam
    return VerificationResult(                  # VERIFY prova
        authentic=signature_valid,
        integral=ledger_entry.hash_matches,
        compliant=invariants_respected
    )
```

---

## Artigo 3 — Definição de Reference Applications (W-*)

Aplicações prefixadas com `W-` são classificadas como **Reference Applications**.

### 3.1 — Lista Actual (25 Abril 2026)

| Aplicação | Porto | Função | Status |
|-----------|-------|--------|--------|
| W-Enterprise-001 | :8150 | AI Compliance | LIVE |
| W-LAW (WINDI-LAW) | :8122 | Legal Drafting | LIVE |
| W-Travel-001 | :8126 | Travel Publishing | LIVE |
| W-SEC-001 | :8144 | Security Sentinel | LIVE |
| W-SHELF-001 | :8191 | Knowledge Diffusion | LIVE |
| W-METRICS-001 | :8200 | Truth Metrics | LIVE |
| ... | ... | ... | ... |

### 3.2 — Propriedades das Reference Apps

| Propriedade | Valor |
|-------------|-------|
| **Utiliza CORE** | SIM — obrigatório |
| **Define CORE** | NÃO — proibido |
| **Pode falhar** | SIM — sem afectar CORE |
| **Pode evoluir** | SIM — independentemente |
| **Pode ser substituída** | SIM — por outra ref app |
| **Pode ser removida** | SIM — CORE permanece |

### 3.3 — Ciclo de Vida

```
Reference App Lifecycle:

  EXPERIMENTAL → LIVE → DEPRECATED → REMOVED
       │          │          │           │
       └──────────┴──────────┴───────────┘
                       │
                       ▼
              CORE NÃO AFECTADO
```

---

## Artigo 4 — Princípio de Não-Contaminação

**Falhas, limitações ou estados experimentais em aplicações W-* não afectam:**

1. A validade do Ledger
2. A autenticidade das assinaturas
3. A capacidade de verificação
4. O cumprimento dos invariantes

### 4.1 — Isolamento de Falha

```
CENÁRIO: W-Enterprise-001 tem bug crítico
RESULTADO:
  ✗ W-Enterprise-001 pode estar indisponível
  ✓ Ledger continua válido
  ✓ Receipts anteriores verificáveis
  ✓ Outras apps funcionam
  ✓ CORE intacto

CENÁRIO: WINDI-LAW foi deprecada
RESULTADO:
  ✗ WINDI-LAW não aceita novos documentos
  ✓ Documentos anteriores verificáveis para sempre
  ✓ Nova app pode substituir
  ✓ CORE intacto
```

### 4.2 — Firewall Constitucional

```
          ┌─────────────────────────────────────┐
          │     REFERENCE APPS LAYER            │
          │  (bugs, downtime, deprecation OK)   │
          │                                     │
          │  ┌────────┐ ┌────────┐ ┌────────┐  │
          │  │W-ENT   │ │W-LAW   │ │W-SEC   │  │
          │  │ (bug)  │ │  (OK)  │ │ (OK)   │  │
          │  └────────┘ └────────┘ └────────┘  │
          │                                     │
          └────────────────┬────────────────────┘
                           │
              ═════════════╪═════════════  FIREWALL
                           │
          ┌────────────────┴────────────────────┐
          │           CORE LAYER                │
          │    (sempre intacto, imutável)       │
          │                                     │
          │  LEDGER ─ KEY ─ INVARIANTS ─ VERIFY │
          │                                     │
          └─────────────────────────────────────┘
```

---

## Artigo 5 — Autoridade

A autoridade do WINDI reside **exclusivamente** no CORE.

### 5.1 — Proibições para Reference Apps

Nenhuma aplicação W-* pode:

| Acção Proibida | Motivo |
|----------------|--------|
| Declarar validade final | Só VERIFY pode |
| Substituir VERIFY | VERIFY é CORE |
| Alterar invariantes | Invariantes são CORE |
| Modificar Ledger | Ledger é CORE |
| Emitir identidades | Key é CORE |

### 5.2 — Hierarquia de Autoridade

```
HIERARQUIA (maior para menor):

  1. INVARIANTES (I1, I9, I11, I14...)
     │
  2. CORE (Ledger, Key, Verificabilidade)
     │
  3. DECRETOS CONSTITUCIONAIS
     │
  4. REFERENCE APPLICATIONS
     │
  5. FEATURES / UI / UX
```

### 5.3 — Poder de Veto

```
SE Reference App tenta violar CORE:
  → CORE tem poder de veto absoluto
  → Operação é bloqueada
  → I9 exige intervenção humana
```

---

## Artigo 6 — Implicações Práticas

### 6.1 — Para Desenvolvedores

```python
# CORRETO: App usa CORE
def seal_document(doc):
    receipt = ledger.seal(doc)      # Usa Ledger (CORE)
    signature = key.sign(receipt)   # Usa Key (CORE)
    verify_url = verify.url(receipt)  # Usa VERIFY (CORE)
    return receipt

# ERRADO: App tenta ser CORE
def seal_document(doc):
    receipt = create_fake_receipt()  # ❌ Viola I11
    signature = sign_without_key()   # ❌ Viola CORE
    return receipt  # ❌ Não verificável
```

### 6.2 — Para Marketing

```
PODE DIZER:
  "Documento verificável no WINDI System"
  "Selado no Forensic Ledger"
  "Verificação independente disponível"

NÃO PODE DIZER:
  "W-Enterprise garante autenticidade"  ← App não garante, CORE garante
  "WINDI-LAW certifica documentos"      ← App não certifica, CORE certifica
```

### 6.3 — Para Utilizadores

```
O que importa:
  - O receipt tem hash? ✓
  - O receipt está no Ledger? ✓
  - Consigo verificar em /verify-public/? ✓

O que NÃO importa:
  - Qual app gerou o documento
  - Se a app ainda existe
  - Se a app tem bugs

O CORE permanece. A verificação permanece.
```

---

## Artigo 7 — Casos de Teste

### 7.1 — Teste de Indivisibilidade

```bash
# Verificar que CORE está presente
curl -s http://localhost:8101/health  # Ledger
curl -s http://localhost:8096/health  # DID/Key
curl -s http://localhost:8145/health  # Verify

# Se qualquer um falhar → CORE comprometido → ALERTA CRÍTICO
```

### 7.2 — Teste de Não-Contaminação

```bash
# Simular falha de Reference App
systemctl stop windi-enterprise

# Verificar que CORE permanece
curl -s http://localhost:8101/api/receipts/{id}  # Deve funcionar
curl -s http://localhost:8145/verify-public/?id={id}  # Deve funcionar
```

---

## Artigo 8 — Relação com Outros Decretos

| Decreto | Relação |
|---------|---------|
| DECRETO-001 (Árvore Viva) | Define anatomia. Este decreto define ontologia. |
| §163 (Living Tree) | Galhos são apps. Tronco é CORE. |
| §199 (I9 Enforcement) | I9 é parte do CORE (invariantes). |
| §200 (I14 Epistemic) | I14 é parte do CORE (invariantes). |

---

## Selagem

```
DECRETO: DECRETO-002-CORE-VS-APPS
HASH: sha256:ec8f275e42fe6b1662f485126a056d1f570fe3a92b1a9743379edb3c8fcf75b2
INVARIANTES: I1 (Human Sovereignty), I9 (Human Approval),
             I11 (Forensic Permanence), I14 (Explicit Failure)
STATUS: CONSTITUTIONAL · IRREMEDIÁVEL
CONECTA: DECRETO-001, §163, §199, §200
```

---

## Conclusão

> *"Ledger guarda. Key assina. Invariantes limitam. VERIFY prova.*
> *Tira um deles — não é WINDI.*
> *Reference Apps vêm e vão. O CORE permanece."*

Esta separação não é técnica. É ontológica.

O WINDI System é definido pelo seu CORE indivisível.
Tudo o resto são implementações que podem evoluir, falhar ou ser substituídas
sem jamais afectar a verdade fundamental do sistema.

**VERIFY não é a única ferramenta indissolúvel.**
**O CORE inteiro é indissolúvel. VERIFY é uma das suas quatro faces.**

---

*Liga IA+H · Kempten, Bavaria · 25 Abril 2026*
*"AI processes. Human decides. WINDI guarantees."*
