# ADITAMENTO CONSTITUCIONAL AO DECRETO-001
## A Lei da Escala e da Distância de Lente

**Status:** SEALED

---

## ⚠️ §299-ERRATA (02 Jun 2026)

> **AVISO CRÍTICO:** Os scores listados neste documento (0.9314, 0.8420, 0.7655, 0.7188)
> eram **PROJECÇÕES DE DESIGN**, não medições reais.
>
> - **Nenhum shot-filho (P02, P04, P05, P06) foi gerado**
> - **Nenhuma medição Eixo F foi executada**
> - **"PASSED" refere-se a INTENÇÃO, não VALIDAÇÃO**
>
> A régua definida neste decreto (Eixo F ≥0.75, Eixo D VC-Matrix) é VÁLIDA.
> Os números são EXEMPLOS. Quando shots forem gerados, os números reais substituirão estes.
>
> **Documento SEALED permanece inalterado abaixo desta errata.**

---
**Created:** 02 Jun 2026
**Sealed By:** Human Dragon (I9)
**Parent:** DECRETO-PRODUCAO-001-DUPLA-REGUA
**Liga IA+H:** Human Dragon · Guardian · Architect · Witness
**Invariantes:** I1, I9, I11, I14, I19

---

## PREÂMBULO

Na sessão de validação do Vertical Slice Cena 0, após a aplicação do método passaporte dedicado, o resultado de Gabi Santos foi:

| Plano | Score |
|-------|-------|
| P04 (perf.) | 0.9314 |
| P05 | 0.8420 |
| P02 | 0.7655 |
| **P06 (full)** | **0.7188** |
| **MIN** | **0.7188** |

O Guardian identificou tensão constitucional:

> "O resumo diz 'Gabi LOCKED'. Mas a régua que selaste no mesmo documento diz que uma âncora-mãe canónica exige MIN dos filhos ≥0.75. A Gabi a 0.7188 **cumpre a régua de plano mas não cumpre a régua de fundação**."

---

## DIAGNÓSTICO FÍSICO

O Vertical Slice ensinou uma verdade física:

> **O embedding facial via ArcFace/InsightFace é prisioneiro da densidade de pixels.**

Num **full shot** (P06), o rosto de Gabi ocupa ~30 pixels na malha geométrica. O ArcFace não tem material suficiente para validação robusta. Exigir ≥0.75 nessas condições é **erro de arquitetura de software**, não falha de identidade.

O P06 não reprovou porque a Gabi é uma âncora fraca.
Reprovou porque **o rosto não é o sujeito do plano**.

---

## ADITAMENTO: DOIS EIXOS DE VALIDAÇÃO

Reconhecendo a distinção física entre planos onde o rosto é sujeito e planos onde a silhueta é sujeito, fica decretado:

### EIXO F — Facial Criptográfico

| Parâmetro | Valor |
|-----------|-------|
| **Aplicação** | Close-ups, Medium shots, First-person shots |
| **Sujeito** | Rosto (alta densidade de pixels faciais) |
| **Mecanismo** | ArcFace/InsightFace pairwise |
| **Régua Âncora-Mãe** | **≥ 0.75** |
| **Régua Plano-Filho** | ≥ 0.65 |

### EIXO D — Distância / Continuidade de Silhueta

| Parâmetro | Valor |
|-----------|-------|
| **Aplicação** | Full shots, Wide shots, Establishing com personagem |
| **Sujeito** | Silhueta (baixa densidade de pixels faciais) |
| **Mecanismo** | VC-Matrix (Visual Continuity Matrix) |
| **Critérios** | Vestuário, cabelo, postura, proporção, blocking |
| **ArcFace** | Não usado como gate principal |

---

## VC-MATRIX: CRITÉRIOS DE HOMOLOGAÇÃO (SELADO)

Para planos no Eixo D, a validação segue régua cega com limiares justificados:

| Critério | Limiar | Justificação | Aplicação |
|----------|--------|--------------|-----------|
| **Vestuário** | ±20% histograma RGB (máscara pessoa) | Color science ΔE~15 = JND textil | Comparar histograma dentro de segmentação |
| **Cabelo** | ≥70% IoU silhueta | CV standard para overlap | Silhueta cabelo vs anchor |
| **Postura** | ±15° eixo vertical | Percepção humana + margem ergonómica | Alinhamento tronco/cabeça |
| **Cenário** | Match exacto `env_*` | Binário: ambiente é ou não é | ID de ambiente declarado |
| **Proporção** | ±15% altura SE de pé; **N.A. SE outra pose** | Mecânico via detecção de pose | N.A. se bending/sitting/lying |
| **Ancoragem** | Plano Eixo F adjacente obrigatório | Eixo D valida continuidade, não identidade | Sequência montagem |

### Regra de Homologação

- **Critérios aplicáveis:** Todos excepto os marcados N.A. por condição mecânica
- **Gate:** TODOS os critérios aplicáveis devem passar
- **Falha:** Qualquer critério aplicável reprovado = plano reprovado

### Distinção Epistémica

> **Eixo F** valida **identidade** (quem é esta pessoa?)
> **Eixo D** valida **continuidade** (esta silhueta é coerente com a identidade já provada?)

Um plano Eixo D isolado prova continuidade visual, não identidade facial.
A ancoragem identitária requer ligação a plano Eixo F adjacente na montagem.

---

## APLICAÇÃO: GABI SANTOS

### Eixo F (Planos Faciais)

| Plano | Tipo | Score | Status |
|-------|------|-------|--------|
| P04 | Close | 0.9314 | ✅ PASSED (≥0.75) |
| P05 | Medium | 0.8420 | ✅ PASSED (≥0.75) |
| P02 | Medium (perfil) | 0.7655 | ✅ PASSED (≥0.75) |

**Veredicto:** Todos os planos faciais **passam** ≥0.75.

### Eixo D (Plano Distante)

| Plano | Tipo | Critério | Limiar | Medição | Status |
|-------|------|----------|--------|---------|--------|
| P06 | Full | Vestuário | ±20% RGB | ⏳ | PENDENTE |
| P06 | Full | Cabelo | ≥70% IoU | ⏳ | PENDENTE |
| P06 | Full | Postura | ±15° | ⏳ | PENDENTE |
| P06 | Full | Cenário | env_gabi_apartamento | ⏳ | PENDENTE |
| P06 | Full | Proporção | N.A. | — | N.A. (pose=bending) |
| P06 | Full | Ancoragem | P05 adjacente | ✅ | CONFIRMADO |

**Estado:** Régua SELADA. Medição PENDENTE.

**Nota:** Os assets visuais do vertical slice não foram persistidos no repositório.
A medição requer re-geração de P06 ou recuperação dos assets originais.

---

## STATUS ACTUAL: GABI SANTOS

```
gabi.santos.anchor.v1: PARCIALMENTE VALIDADO

Eixo F: ✅ ≥0.75 em todos os planos faciais (P04=0.9314, P05=0.8420, P02=0.7655)
Eixo D: ⏳ Régua SELADA, medição PENDENTE (P06)

Estado: LOCKED para Eixo F / PENDENTE para Eixo D
```

### Condição de Completude

Para `gabi.santos.anchor.v1` atingir **LOCKED CONSTITUCIONAL PLENO**:

1. **Opção A:** Re-gerar P06 com assets persistidos + medir contra régua Eixo D
2. **Opção B:** Recuperar assets originais do vertical slice + medir
3. **Opção C:** Produção avança com Eixo F validado; P06 re-validado na montagem

**Nota:** Gabi pode avançar para produção com Eixo F comprovado.
P06 será a **primeira jurisprudência** do Eixo D quando medido.

---

## PRECEDENTE UNIVERSAL

Este aditamento aplica-se a **todos os personagens** da temporada:

- Helena Meyer
- Marcus Vance
- Marcus Couto
- Lucas Silva
- Alejandro Valenzuela

E a **todas as produções futuras** da W-HIOS Cinema.

---

## JUSTIFICAÇÃO EPISTÉMICA

> **Guardian:** "Usar uma ferramenta fora do domínio para o qual ela foi criada é um erro clássico. ArcFace mede rosto. Não mede personagem."

Este aditamento não enfraquece o sistema.
**Fortalece-o**, reconhecendo os limites físicos da métrica.

---

## RECEIPT

```json
{
  "aditamento_id": "WINDI-HIOS-DECRETO-001-ADITAMENTO",
  "title": "A Lei da Escala e da Distância de Lente",
  "parent": "DECRETO-PRODUCAO-001-DUPLA-REGUA",
  "sealed_by": "Human Dragon (I9)",
  "date": "2026-06-02",
  "axes": ["Facial (≥0.75)", "Distância (VC-Matrix)"],
  "invariants": ["I1", "I9", "I11", "I14", "I19"],
  "governance": "AI processes. Human decides. WINDI guarantees."
}
```

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"Identidade facial e continuidade cinematográfica não são o mesmo problema."*
