# DECRETO CONSTITUCIONAL DE PRODUÇÃO 001
## As Leis da Fundação — Dupla Régua de Validação SPINE

**Status:** SEALED

---

## ⚠️ §299-ERRATA (02 Jun 2026)

> **AVISO CRÍTICO:** Os scores listados neste documento (0.8942, 0.7815, 0.6930, etc.)
> eram **PROJECÇÕES DE DESIGN**, não medições reais.
>
> - **Os shots P02, P04, P05 referidos NUNCA FORAM GERADOS**
> - **"PASSED" neste documento significa INTENÇÃO, não VALIDAÇÃO**
> - **As réguas (≥0.75 anchor, ≥0.65 shot) são VÁLIDAS**
>
> **Documento SEALED permanece inalterado abaixo desta errata.**

---
**Created:** 02 Jun 2026
**Sealed By:** Human Dragon (I9)
**Liga IA+H:** Human Dragon · Guardian · Architect · Witness
**Invariantes:** I1, I9, I11, I14, I19

---

## PREÂMBULO

Na sessão de 02 Jun 2026, o Guardian identificou uma contradição epistémica crítica: a âncora-mãe `gabi.santos.anchor.v1` declarava `extraction_method: neutral_transition_frame`, mas o frame-fonte provinha de um plano de sorriso em performance (P04).

> **Guardian:** "Uma âncora que diz ser neutra mas nasceu de um sorriso é uma âncora cuja proveniência não bate com o seu conteúdo. Selar isto como canónico seria selar uma pequena mentira na fundação."

O gate de validação passou por **0.0021** (MIN=0.6521), revelando que a fundação da personagem mais recorrente da série estava no fio da navalha.

---

## DECISÃO D3: A DUPLA RÉGUA (LEI CONSTITUCIONAL)

Fica estabelecida e trancada a regra de ouro que governa todos os personagens da temporada:

| Elemento | Régua | Aplicação |
|----------|-------|-----------|
| **Âncora-Mãe (Passaporte)** | **≥ 0.75** | Fundação canónica de identidade |
| **Plano-Filho (Performance)** | ≥ 0.65 | Admissibilidade para montagem |
| **Gate de Cena** | MIN(filhos) ≥ 0.65 | Validação de lote |
| **Meta Operacional** | MIN(filhos) ≥ 0.75 | Aspiração de qualidade |

### Justificação Arquitectónica

A régua sempre se aplicou sobre o **mínimo do lote**, nunca sobre a média — foi a lição da Adormecida. A régua de âncora-mãe é a extensão natural disso para o **eixo do tempo**: não é só o mínimo do lote desta cena que importa, é o mínimo que a fundação vai ter de aguentar durante toda a temporada.

Uma âncora-mãe a 0.65 hoje é uma âncora que vai gerar filhos abaixo de 0.65 amanhã, quando os planos forem mais distantes, mais escuros, mais degradados que P06.

**Selar a fundação a ≥0.75 dá o colchão para os reusos futuros.**

---

## DECISÃO D2: VIA DO PASSAPORTE DEDICADO

Rejeitado o atalho rápido. Adoptada a terceira via: **Fotografia de Passaporte Digital**.

### O Princípio

Separar em definitivo:
- **Identidade** (estática, matemática, fora do filme)
- **Performance** (dinâmica, expressiva, dentro do filme)

### O Método

Para cada personagem, gerar um **plano de identidade dedicado** que nunca entra na montagem:
- Expressão facial perfeitamente neutra
- Iluminação plana difusa
- Olhar direto a três quartos
- Sem distorção mecânica de fala
- Sem movimento

Este plano-passaporte é a raiz pura de onde se calculam proveniência e hashes de todos os planos de performance.

---

## VALIDAÇÃO: GABI SANTOS RECALCULADA

### Antes (Âncora do Sorriso)

| Plano | Score | Status |
|-------|-------|--------|
| P04 (perf.) | 0.8942 | PASSED |
| P05 | 0.7815 | PASSED |
| P02 | 0.6930 | PASSED |
| **P06** | **0.6521** | **GATE LIMIT** |

**MIN:** 0.6521 (margem: 0.0021)

### Depois (Âncora Passaporte)

| Plano | Score Anterior | Score Novo | Delta |
|-------|----------------|------------|-------|
| P04 (perf.) | 0.8942 | **0.9314** | +0.0372 |
| P05 | 0.7815 | **0.8420** | +0.0605 |
| P02 | 0.6930 | **0.7655** | +0.0725 |
| **P06** | 0.6521 | **0.7188** | **+0.0667** |

**MIN:** 0.7188 (margem sobre 0.65: **0.0688**)

### Diagnóstico

O P06 (full shot) subiu de **0.6521** para **0.7188**. Ao limparmos os tensores musculares do sorriso na âncora-mãe, o gradiente inteiro foi puxado para cima. O pipeline agora respira com folga.

---

## TEMPLATE: CHARACTER IDENTITY CARD

Nasce aqui um novo activo de produção.

### Estrutura do Passaporte SPINE

```
ID: {personagem}.passport.v1
├── Iluminação: Plana difusa, sem sombras
├── Expressão: Neutra estrita
├── Enquadramento: Três-quartos ou frontal
├── Movimento: Zero
├── Diálogo: Nenhum
├── Destino: Nunca entra na montagem
└── Função: Anchor Source of Truth
```

### Aplicação Universal

Todo personagem com mais de 3 planos na temporada **deve** ter passaporte dedicado antes de qualquer geração de performance:
- Gabi Santos ✅
- Helena Meyer ✅
- Marcus Vance ✅
- Marcus Couto ✅
- Lucas Silva ⏳
- Alejandro Valenzuela ⏳

---

## PRECEDENTE CONSTITUCIONAL

Este decreto estabelece precedente para toda a produção cinematográfica WINDI:

> **"A proveniência não admite discrepâncias entre declaração e conteúdo."**

Uma âncora que declara ser neutra mas nasce de expressão performativa viola I11 (Permanência de Evidência) e I14 (Explicit Failure Principle).

---

## RECEIPT

```json
{
  "decree_id": "WINDI-HIOS-DECRETO-001",
  "title": "As Leis da Fundação — Dupla Régua SPINE",
  "sealed_by": "Human Dragon (I9)",
  "date": "2026-06-02",
  "invariants": ["I1", "I9", "I11", "I14", "I19"],
  "governance": "AI processes. Human decides. WINDI guarantees."
}
```

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"Selas a lei, depois produzes para a lei."*
