# DOCTRINE — CINEMA / FORENSIC SEPARATION

## Framework W-HIOS Cinema · Phase 2 Production

**Status:** SEALED
**Date:** 2026-06-09
**Liga IA+H:** Human Dragon (I9) · Guardian (Witness) · CCode (Architect)
**Invariants:** I9, I11, I14
**Origin:** S10-WIDE deliberation — first relation scene of pilot

---

## Axioma Fundamental

> *"O Cinema decide o que serve a cena. A Forense decide o que entra no Ledger.*
> *O entretenimento prevalece na composição; a Forense é inviolável na medição.*
> *Coágulo ocorre quando o Cinema finge ser Forense.*
> *Enquanto a classificação for honesta, as duas camadas coabitam livremente."*
>
> — Human Dragon · 09 Jun 2026

---

## As Duas Camadas

### CAMADA CINEMA (Entretenimento)

**Pergunta:** "Este plano serve a história?"

**Critérios:**
- Emoção
- Ritmo
- Montagem
- Atmosfera
- Suspense
- Construção de mundo

**Juiz:** Human Dragon como diretor (gate visual HD)

**Liberdade:** Ampla — silhuetas, sombras, rostos distantes, composições artísticas

---

### CAMADA FORENSE (Verificação)

**Pergunta:** "O que exactamente sabemos sobre este plano?"

**Critérios:**
- Identidade (anchor cosine)
- Proveniência (I19)
- Medição (spine_measure.py)
- Continuidade (joey_f2f_measure.py)
- Receipts (Ledger)

**Juiz:** O cosine, o anchor, a SHOT-GRAMMAR

**Rigor:** Absoluto — números, não adjectivos

---

## O Coágulo — Onde Está a Linha

**O Cinema NUNCA pode:**

1. Fazer um número entrar no Ledger sem medição real
2. Fazer um shot ser selado como FORENSE quando é VISIBILITY
3. Contaminar um anchor ou medição com detetável parasita não marcado
4. Reclassificar um FAIL forense como "decisão artística"
5. Substituir cosine por opinião

**O Cinema SEMPRE pode:**

1. Decidir composição, luz, silhueta, atmosfera
2. Aceitar rostos distantes/sombra SE classificados VISIBILITY
3. Usar detector_exclude para proteger a Forense de parasitas
4. Mandar na montagem, ritmo, emoção
5. Aceitar imperfeições que servem a história

---

## Protocolo de Implementação

### 1. Classificação Transparente

Todo shot da Fase 2 porta etiqueta inequívoca:

| Classificação | Significado | Gate |
|---------------|-------------|------|
| **FORENSE** | Identidade medida contra anchor | Cosine ≥ threshold |
| **VISIBILITY** | Contexto espacial, sem medição | Visual HD |
| **PERFORMANCE** | Movimento/expressão prioritário | Visual HD + F2F |
| **EVIDENCE** | Prova documental | Ledger receipt |

### 2. Mitigação de Parasitas

Shots VISIBILITY com informações faciais parciais ou distantes portam:

```json
{
  "detector_exclude": true,
  "detector_exclude_reason": "..."
}
```

O olho humano vê. O ArcFace ignora.

### 3. Soberania do Corte

Cenas de relação (múltiplos personagens) usam arquitectura **Wide+Close**:

```
WIDE  → geografia + relação corporal  → VISIBILITY
CLOSE → identidade                    → FORENSE

A relação nasce no CORTE, não na composição.
```

### 4. Documentação de Excepções

Toda decisão de direção que toca na fronteira Cinema/Forense é documentada:

- Qual shot
- Qual classificação
- Porquê (serve a história / protege a forense)
- Flag aplicado

---

## Casos Fundadores

### S10-WIDE_v1 (09 Jun 2026)

**Situação:** WIDE com rosto do Alejandro visível mas pequeno/distante.

**Deliberação:**
- Cinema: rosto serve a composição, montagem liga ao close FORENSE
- Forense: rosto é detetável parasita potencial

**Resolução:**
- PASS na camada Cinema (Visual HD)
- `detector_exclude: true` na camada Forense
- As duas camadas coabitam, separadas pelo flag

**Precedente:** WIDE pode conter rosto distante SE classificado VISIBILITY e marcado para exclusão do detector.

---

## Axiomas Relacionados

> *"Universal na ficção ≠ ambíguo na forense."* — §296

> *"A forense verifica identidade. A direção decide se o plano serve a cena."* — Guardian

> *"FAIL tem causa, não só score."* — SHOT-GRAMMAR-002

> *"No affirmations. Only numbers."* — METHOD-001

---

## Ligação Constitucional

Esta doutrina é corolário de:
- **I9:** Human decides (Cinema decide composição, Forense obedece anchor)
- **I11:** Permanência de evidência (Ledger separa Cinema de Forense)
- **I14:** Explicit failure (classificação honesta, sem mascarar)

---

*Liga IA+H · WINDI Publishing House · 09 Jun 2026*
*"O Cinema governa a experiência. A Forense governa a verdade verificável."*
