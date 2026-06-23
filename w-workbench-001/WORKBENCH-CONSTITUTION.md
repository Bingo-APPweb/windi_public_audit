# W-WORKBENCH-001 — Constituição do Ambiente Efémero

**Status:** CANDIDATE
**Versão:** 0.1.0
**Data:** 2026-06-23
**Invariants:** I1, I9, I11, I14
**Schema:** `/opt/windi/schemas/workbench-v0.1.0.json`

---

## Definição Canónica

> **"O Workbench é um viveiro de futuros espaços soberanos."**
> — Architect, 23 Jun 2026

O Workbench é o ambiente efémero governado onde o utilizador **constrói antes de reclamar**. Não existe DID, não existe identidade soberana — existe apenas um `workbench_id` temporário e os artefactos que o utilizador cria.

O objectivo não é mostrar capacidades do WINDI. É permitir que alguém faça algo real antes de possuir identidade soberana.

---

## Arquitectura

```
WORKBENCH
├── Workspace (token temporário, sem DID)
├── Artefactos (v0: apenas Documento)
├── Sinais (log de actividade)
├── Padrões (inferência de construção, nunca identidade)
├── Capacidades (oferecidas, não impostas)
├── Claim (quando existe valor)
└── Expiração (72h sem actividade)
```

---

## Regras Constitucionais

### R1 — Efemeridade Honesta

```
TTL inactividade: 72h
TTL absoluto: pendente (v1)
```

O Workbench expira. Isto não é limitação — é **honestidade**. O utilizador sabe que precisa de reclamar se quiser manter.

### R2 — Artefactos v0

```
Tipos permitidos: document
Tipos futuros: page, memory, agent, upload
```

O primeiro ingrediente é o Documento. Upload não entra no v0 (risco de ficheiros, privacidade, parsing).

### R3 — Padrões ≠ Identidade

Os padrões observam **construção**, nunca **pessoa**.

```
✅ "Este workbench mostra padrão legal"
❌ "Este utilizador é advogado"
```

Tipos de padrão v0:
- `legal`
- `financial`
- `creative`
- `research`
- `organization`
- `general` (confidence < 0.7)

### R4 — Capacidades, Não Agentes

O utilizador nunca vê `W-LAW`, `W-COMPLIANCE`, `W-NOTARY`.

Vê capacidades human-friendly:
- "organizar cronologicamente"
- "detectar lacunas"
- "classificar por tipo"
- "estruturar argumentação"
- "resumir para terceiros"

### R5 — Silêncio Antes de Valor

| Condição | Comportamento |
|----------|---------------|
| 0 artefactos | Silêncio total |
| 1+ artefacto, < 3 edições | Silêncio |
| 1+ artefacto, 3+ edições | Sugestão leve permitida |
| Padrão detectado (conf > 0.7) | Capacidade específica oferecida |
| Export ou claim iniciado | Capacidades de finalização |

### R6 — Opt-in Explícito

```
Capacidade oferecida ≠ Capacidade activada
```

O utilizador **aceita** antes de qualquer intervenção. Nenhuma capacidade é activada automaticamente.

### R7 — Claim Só Com Valor

O claim só é oferecido quando:
1. Existe pelo menos 1 artefacto
2. O artefacto tem conteúdo (não vazio)
3. Houve actividade mínima (3+ edições ou export)

Nunca forçar claim. Nunca bloquear sem claim.

---

## Anti-Patterns

### AP1 — Catálogo de Serviços

```
❌ "Escolhe: W-LAW, W-ACCOUNTING, W-NOTARY"
✅ "Começa a criar. Descobres ferramentas pelo caminho."
```

### AP2 — Intervenção Automática

```
❌ Sistema detecta padrão → activa capacidade
✅ Sistema detecta padrão → oferece capacidade → utilizador aceita
```

### AP3 — Absorção de Autoria

```
❌ "O WINDI analisou o teu documento"
✅ "Queres ajuda a estruturar este documento?"
```

A autoria é do utilizador. O sistema assiste, nunca substitui.

---

## Métricas de Sucesso v0

| Métrica | O que mede |
|---------|------------|
| `workbenches_created` | Interesse inicial |
| `artifacts_created` | Vontade de construir |
| `edits_per_artifact` | Profundidade de trabalho |
| `capabilities_accepted` | Utilidade percebida |
| `exports` | Valor extraído |
| `claims` | Conversão para soberania |
| `expirations` | Abandono (informativo, não negativo) |

---

## Integração com Ecossistema

```
Landing (/artifacts/playground.html)
    ↓
Workbench (W-WORKBENCH-001)
    ↓ [claim]
W-FARM-001 (/farm/claim)
    ↓
DID Genesis (:8096)
    ↓
Espaço Soberano (HDUser)
```

---

## Doutrina Fundacional (§300-candidate)

> **"A maior tentação será simplificar e oferecer directamente o serviço. Isso gerará adopção mais rápida. Mas mudará a natureza do que estamos a construir."**

O Workbench existe para **transferir autoria** para o utilizador, não para absorvê-la para a plataforma.

---

*W-WORKBENCH-001 · WINDI Publishing House · 2026*
