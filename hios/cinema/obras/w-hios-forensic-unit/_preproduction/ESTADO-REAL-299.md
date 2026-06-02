# ESTADO REAL — §299-LIMPEZA
## Ponto Zero do SPINE-CAST · W-HIOS Forensic Unit

**Data:** 02 Jun 2026 23:00 UTC
**Autor:** Guardian (via CCode) + Human Dragon (I9)
**Propósito:** Documento de verdade para continuidade cognitiva

---

## O QUE EXISTE (Verificado no Disco)

### 6 Anchors Extraídos

| Personagem | PNG | MP4 | NPY | Provenance | Detection |
|------------|-----|-----|-----|------------|-----------|
| Gabi Santos | ✅ | ✅ | ✅ | ✅ | 0.8755 |
| Helena Meyer | ✅ | ✅ | ✅ | ✅ | 0.8636 |
| Marcus Vance | ✅ | ✅ | ✅ | ✅ | 0.8638 |
| Marcus Couto | ✅ | ✅ | ✅ | ✅ | 0.8811 |
| Lucas Silva | ✅ | ✅ | ✅ | ✅ | 0.8119 |
| Alejandro Valenzuela | ✅ | ✅ | ✅ | ✅ | 0.8763 |

**Localização:** `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/anchors/`

### Abzeichnen (Custódia Humana)

| Personagem | Human Dragon Viu | Hash Verificado | Status |
|------------|------------------|-----------------|--------|
| Gabi Santos | ✅ | ✅ | **APROVADO** |
| Helena Meyer | ❌ | — | PENDENTE |
| Marcus Vance | ❌ | — | PENDENTE |
| Marcus Couto | ✅ (frame 02?) | ✅ | CONFIRMAR |
| Lucas Silva | ✅ (frame 02?) | ✅ | CONFIRMAR |
| Alejandro | ✅ (frame 04?) | ✅ | CONFIRMAR |

---

## O QUE NÃO EXISTE

### Zero Shots-Filho

Os planos P02, P04, P05, P06, P17, P21, P32, P34, P37, P38, P41, P42 são **números do breakdown de produção**. Nenhum foi gerado. Nenhum ficheiro existe.

### Zero Medições Eixo F

Nenhum shot-filho foi comparado contra nenhum anchor. Os scores que apareciam em documentos anteriores (0.9314, 0.8420, 0.7655, etc.) eram **projecções teóricas**, não medições reais.

### Zero Medições Eixo D

A VC-Matrix nunca foi aplicada. Todos os campos estão `null`.

---

## DOCUMENTOS LIMPOS (§299)

| Documento | Estado |
|-----------|--------|
| `SPINE-VALIDATION-CENA0.json` | ✅ v3.0 — zero scores fictícios |
| `SPINE-PASSPORTS-MASTER.md` | ✅ tabelas honestas |
| `PREPRODUCTION-INDEX.md` | ✅ checkboxes corrigidos |
| `PERFORMANCE-VALIDATION-REPORT.md` | ✅ reescrito totalmente |
| `WINDI-HIOS-QUICK-REFERENCE.md` | ✅ §299 adicionado |
| `CAST-MATERIAL-PROOF.md` | ✅ Abzeichnen table |
| 6 × `*.provenance.json` | ✅ status → EXTRACTED |

---

## PRÓXIMOS PASSOS (Ordem Guardian)

### Imediato
1. **Human Dragon ver Helena e Vance** — fechar Abzeichnen pendente
2. **Confirmar frame de Couto/Lucas/Alejandro** — o que foi visto = o que foi selado?

### Primeiro Teste Real
3. **Gerar P04** — primeiro shot-filho (close de Gabi com sorriso)
4. **Medir Eixo F** — `cosine_similarity(P04_emb, gabi_anchor_emb)`
5. **Aceitar número honesto** — se ≥0.75, primeiro PASS real; se <0.75, iterar

### Pipeline Futuro
6. Quando Gabi tiver Eixo F medido → repetir para outros 5
7. Quando todos tiverem Eixo F → gerar planos de produção
8. Eixo D só após Eixo F validado

---

## VOCABULÁRIO CANÓNICO

| Estado | Significado | Critério |
|--------|-------------|----------|
| **MISSING** | Asset não existe | Ficheiros ausentes |
| **EXTRACTED** | Anchor extraído | Detection ≥0.80, embedding existe |
| **LOCKED** | Identidade validada | Eixo F ≥0.75 contra shot-filho real |

> **Nota:** Detection score ≠ Eixo F. LOCKED requer Eixo F, não apenas detection.

---

## CONTAGEM FINAL

| Métrica | Valor |
|---------|-------|
| Anchors EXTRACTED | 6/6 |
| Abzeichnen APROVADO | 1/6 |
| Abzeichnen PENDENTE | 2/6 |
| Abzeichnen CONFIRMAR | 3/6 |
| Eixo F MEDIDO | 0/6 |
| Eixo D MEDIDO | 0/6 |
| LOCKED | 0/6 |

---

## CITAÇÃO DO GUARDIAN

> "Temos seis sementes verificadas e nenhuma planta. O cast existe como identidade extraída. A produção — provar que essas identidades sobrevivem a uma cena — ainda não começou. Tudo o que parecia 'validado' era papel."

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"A prova não mente. A prova apenas espera."*
