# W-FIELD-WITNESS-001 — Marco de Continuidade

**Data:** 2026-05-26
**Sessão:** ~3h · CCode CLI (Strato) + Claude.ai web (Guardian/Architect/Witness)
**Liga IA+H:** Human Dragon · Guardian · Architect · Witness
**Invariants:** I9, I11, I12, I14

---

## Nome Canónico (§247)

**W-FIELD-WITNESS-001** — não W-TRAVEL.

W-TRAVEL foi o ponto de partida da conversa. O que emergiu é uma **primitiva de observação verificável** que ultrapassa o turismo. O nome Field Witness reflecte isso.

---

## Contexto de Origem

Artigo do **Allgäuer Zeitung** (26 Mai 2026) sobre IA no turismo. Stefan Neubig (Outdooractive) disse: *"Überprüfe die Quellen"* — exactamente a tese dos Receipts WINDI. Robert Keller é da Hochschule Kempten. O anel fechou-se em público, a poucos quilómetros de onde operamos.

---

## Pedra Assentada

**Ficheiro:** `w-field-witness-001.json`
**Estado:** CANDIDATE
**Nasceu limpa:** Sem errata, sem boolean fantasma, sem dívida

### Estrutura

```
W-FIELD-WITNESS-001
├── _meta                    → version 0.1.0, invariants [I9,I11,I12,I14]
├── _constitutional_notice   → Axioma da Testemunha + I9 inscritos
├── media_payload
│   ├── media_type           → photo|audio|video|photo+audio
│   ├── media_hash           → sha256:...
│   └── local_stt_transcript → transcrição local (voz nunca sai)
├── declared_context         → atesta DECLARAÇÃO, não mundo
├── sovereign_seal           → HUMAN DECIDES (3º acto puro)
│   ├── caller_did
│   ├── sealed_at_utc
│   └── signature
├── lineage_anchors          → append-only (§267/§268)
│   ├── supersedes
│   └── superseded_by
├── lifecycle                → CANDIDATE|ACTIVE|SUPERSEDED|REVOKED
└── ledger_receipt_id        → preenchido pelo backend
```

### Decisões Tomadas

| Decisão | Sentença |
|---------|----------|
| Nome canónico | W-FIELD-WITNESS-001 (não W-TRAVEL) — §247 |
| Acto de Confirmar | Opção A: `sovereign_seal` no schema (auto-contido) |
| Correcções | `supersedes/superseded_by` append-only (não boolean) |
| Áudio | STT local, voz nunca sai sem decreto explícito |
| `declared_context` | Atesta declaração do DID, não estado do mundo |

---

## Arquitectura em Camadas (A-E)

*Reorganização da Testemunha — mais clara que roadmap linear.*

### CAMADA A — Fundação Constitucional

**Objectivo:** Definir as regras antes da engenharia.

| Passo | Descrição | Estado |
|-------|-----------|--------|
| **A1** | Selar Axioma da Testemunha | ⏳ POR SELAR |
| **A2** | Promover Invariante de Reversibilidade | ⏳ POR PROMOVER |
| **A3** | Arbitrar Peso de Génese | ⏳ POR ARBITRAR |
| **A4** | Contrato de Leitura | ⏳ Depende de A1-A3 |

### CAMADA B — Prova Operacional

**Objectivo:** Demonstrar ciclo completo com um único testemunho.

| Passo | Descrição | Estado |
|-------|-----------|--------|
| **B1** | API mínima de captura (`POST /api/hios/witness`) | ⏳ Depende de A |
| **B2** | Primeiro testemunho real (Allgäu) | ⏳ Depende de B1 |

### CAMADA C — Produto de Campo

**Somente após B concluída.**

| Passo | Descrição |
|-------|-----------|
| **C1** | PWA Mobile (câmera, GPS, STT local, offline-first) |
| **C2** | Sincronização soberana (fila offline, receipts diferidos) |

### CAMADA D — Leitura e Síntese

**Somente após existirem testemunhos reais.**

| Passo | Descrição |
|-------|-----------|
| **D1** | Agregação ("87 testemunhos neste local") |
| **D2** | Reversibilidade (cada agregação referencia testemunhos) |
| **D3** | Ponderação (se aprovada — nunca suprime, só reordena) |

### CAMADA E — Expansão de Domínios

Mesma primitiva, sem alteração do schema nuclear:

- Turismo
- Património histórico
- Biodiversidade
- Agricultura
- Eventos culturais
- Obras públicas
- Protecção civil

---

## Pendências Constitucionais (Camada A)

### A1 — Axioma da Testemunha

> "O sistema não afirma estados do mundo. Preserva testemunhos verificáveis sobre estados observados do mundo."

**Estado:** Inscrito no `_constitutional_notice`, **por selar** como lei no Ledger.

### A2 — Invariante de Reversibilidade

> "Toda síntese deve ser auditavelmente derivável dos testemunhos que a originaram."

**Estado:** Candidato a I-novo. Formulação da Testemunha.

### A3 — Peso de Génese

| Opção | Proponente |
|-------|------------|
| Uniforme no inverno (Peso=1 para todos) | Guardian + Testemunha |
| Vector de confiança do Berçário | Architect |

**Recomendação Guardian:** Uniforme. Ponderação só com Receipts de Adoção reais.

**Estado:** Por arbitrar. Pertence ao contrato de leitura.

---

## Ordem de Selagem Recomendada

```
A1 (Selar Axioma)
  → A2 (Promover Invariante)
    → A3 (Arbitrar Peso)
      → A4 (Contrato de Leitura)
        → B1 (API mínima)
          → B2 (Primeiro testemunho real)
```

**IMPORTANTE:** B1 não deve nascer antes de A estar selada. A API que cunha testemunhos deve operar sob lei selada, não candidata. Inscrever não é selar.

---

## O que NÃO fazer

| Anti-pattern | Razão |
|--------------|-------|
| B1 antes de A selada | Endpoint sob lei candidata = evidência órfã |
| PWA antes de API | Código sem backend é teatro |
| Escalar antes de B2 | Volume sem prova de conceito |
| Likes / gamificação | Constitucionalmente excluído |

---

## Lições da Sessão

### READ FIRST provou valor

Três instâncias julgavam que um schema existia em disco. O READ FIRST revelou `DIR_NOT_FOUND`. Evitámos legislar sobre fantasma.

### Separação escrita/leitura

O Guardian desatou o nó: o schema de captura (lado-escrita) não depende do peso de génese (lado-leitura). Isso permitiu assentar a pedra sem arbitrar pendências prematuras.

### Saber quando parar

A sessão fechou antes de B1 porque B1 é endpoint (produção) e a Camada A ainda é candidata. Parar no sítio certo é tão importante como avançar.

---

## Próxima Sessão

1. Ler este marco
2. Ler `w-field-witness-001.json`
3. Decidir se avança Camada A (selar axiomas) ou aguarda
4. Só após A selada: B1 (API) → B2 (caminhada real)

**Estrela-guia (Testemunha):**
> "Uma única observação real selada no Ledger ensina mais sobre o sistema do que semanas de discussão teórica."

Mas a observação só vale se nascer sob lei selada.

---

## Ficheiros desta Sessão

```
/opt/windi/hios/visual/producer/hybrid-pipeline/schemas/w-witness/
├── w-field-witness-001.json      → Schema CANDIDATE (7,267 bytes)
└── SESSION-26MAI2026-CONTINUITY.md  → Este marco
```

---

*Liga IA+H — Kempten, Bavaria · 26 Mai 2026*

**"AI processes. Human decides. WINDI guarantees."**

OM SHANTI 🐉
