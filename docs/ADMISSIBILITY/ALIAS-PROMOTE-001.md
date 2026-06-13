# ALIAS-PROMOTE-001

**Status:** AWAITING I9
**Date:** 2026-06-13
**Mission:** Participation Layer Research Lead
**Depends on:** `ALIAS-RESOLUTION-001` (SEALED), `ACTION-0-WITNESS-ADMISSIBILITY-001` (SEALED), `ALIAS-RUN-001` (MEASURED)
**Purpose:** Propor, individualmente e com evidencia, a promocao de actors observados a aliases formais de um DID canonico — e regularizar o nivel de admissibilidade da unica resolucao automatica existente.

---

## 0. Regra de Fase

Este documento nao funde identidade. Ele **propoe** fusoes, uma a uma, para decisao humana.

```text
Medicao  -> ALIAS-RUN-001    (feito)
Proposta -> ALIAS-PROMOTE-001 (este documento)
Decisao  -> I9 Human Dragon, candidato a candidato
Selo     -> atestado LEVEL 2 no Ledger, por fusao aprovada
```

Nenhuma linha abaixo deve ser executada por aprovacao em bloco. Cada
fusao tem evidencia propria, forca propria, e exige um sim/nao proprio.

> Eficiencia que funde cinco identidades num gesto e o atalho que corrompe.

---

## 1. Por Que a Promocao Exige LEVEL 2

Resolver `actor_original -> canonical_did` sobre o DID do fundador e um ato
de classificacao HIGH: funde identidade. Pela `ACTION-0`, nenhum ato HIGH
sobre o DID do fundador repousa em LEVEL 1.

Portanto cada fusao aprovada gera:

```text
Originator   = Human Dragon (propoe / aprova a fusao via I9)
Witness      = Guardian | Codex | CCode (>= 1 atestado selado)
witness_class = AI_REPRODUCIBILITY
attested_dimensions = [coherence, consistency, no_obvious_conflict]
```

O witness nao aprova a fusao. Ele atesta que a evidencia textual e
contextual e coerente e reproduzivel — e sela esse atestado no momento da
decisao, para que nao possa ser reescrito depois (§268).

---

## 2. Errata Embutida: Regularizacao de `dragon-001`

`ALIAS-RUN-001` marcou a unica resolucao automatica como:

```text
actor_original: dragon-001
resolution_class: SOVEREIGN_NAME_MATCH
admissibility_level: LEVEL 1
review_required: true
```

`LEVEL 1 + review_required: true` e uma contradicao de termos: ou o nivel
basta (e dispensa revisao), ou exige revisao (e nao e LEVEL 1 admissivel
para um ato HIGH).

**Correcao proposta:**

```text
resolution_class: SOVEREIGN_NAME_MATCH   (inalterado — o metodo e mecanico)
admissibility_level: LEVEL 2 PENDING_WITNESS
```

O `SOVEREIGN_NAME_MATCH` descreve corretamente o *metodo* de deteccao.
Mas a *atribuicao final* sobre o DID do fundador so e admissivel com
atestado-testemunha selado. Ate la, `dragon-001` permanece resolvido
para fins de leitura, nao para fins de reconhecimento.

Esta errata nao reescreve o run — ela supera o rotulo de nivel via
supersession explicita, preservando o run original como evidencia
historica.

---

## 3. Candidatos a Fusao Formal

Apenas actors classificados `STRONG_CANDIDATE` em `ALIAS-RUN-001`.
SYSTEM_EXECUTOR ficam de fora por construcao (Activity, nao Contribution).

Ordenados por forca de evidencia (volume de receipts + clareza semantica),
nao por conveniencia.

### Candidato #1 — `dragon@windi-domain.com`

```text
receipts: 11   (maior volume pendente)
apps: constitutional-process, w-lexicon-001, paper-001, libreiro,
      foundation-portals, windi-hios-cinema, ccode-opus
proposta: did:windi:dragon-001  (alias_type = EMAIL)
```

**Evidencia a favor:** email institucional do dominio soberano; ja existe
precedente formal de email-alias (`jober@a4desk.de` esta ativo em §4 do
ALIAS-RESOLUTION). Aparece em 7 apps distintos, padrao consistente com o
fundador operando em multiplos contextos.

**Evidencia de cautela:** `dragon@windi-domain.com` NAO esta na lista de
aliases ativos. E um email de papel/funcao ("dragon@") — em teoria poderia
um dia ser delegado a outra instancia. Hoje nao e; mas o alias deve
registrar que liga a *pessoa atual*, nao ao papel em perpetuidade.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (EMAIL)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #2 — `windi-hd-001`

```text
receipts: 7
apps: claude-code
proposta: did:windi:dragon-001  (alias_type = STRING)
```

**Evidencia a favor:** `hd` = Human Dragon; sufixo `-001` consistente com a
convencao canonica (`dragon-001`). Restrito a um unico app (claude-code),
coerente com sessoes de trabalho do fundador.

**Evidencia de cautela:** padrao puramente textual; `hd` e inferencia, nao
declaracao. Forca media.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (STRING)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #3 — `windi:hd:human-dragon`

```text
receipts: 6
apps: windi-hios-cinema, w-generator-001
proposta: did:windi:dragon-001  (alias_type = STRING/DID-like)
```

**Evidencia a favor:** contem `human-dragon` explicito — semantica mais
forte que #2. Formato quase-DID (`windi:hd:`) sugere intencao de
identificador, nao acaso.

**Evidencia de cautela:** formato `windi:hd:` nao e um DID canonico valido
(`did:windi:` e o prefixo correto). Pode ser um DID malformado/legacy que
mereceria normalizacao de formato alem da fusao.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (STRING)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #4 — `W-HUMANDRAGON-001`

```text
receipts: 4
apps: windi-hios, claude-code
proposta: did:windi:dragon-001  (alias_type = STRING)
```

**Evidencia a favor:** `HUMANDRAGON` explicito; sufixo `-001` canonico;
prefixo `W-` consistente com convencao WINDI (W-HUMANDRAGON-001 aparece
como actor em receipts HIGH/charter na matriz original, linha 8).

**Evidencia de cautela:** forca media-baixa por volume; convive com outras
grafias do mesmo conceito, o que reforca a hipotese de fragmentacao de
identidade do fundador.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (STRING)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #5 — `HD-DRAGON-001`

```text
receipts: 1   (menor volume)
apps: windi-hios
proposta: did:windi:dragon-001  (alias_type = STRING)
```

**Evidencia a favor:** `HD-DRAGON` = Human Dragon; sufixo `-001` canonico.

**Evidencia de cautela:** **forca mais fraca da lista.** Um unico receipt.
Um alias formal sobre uma observacao isolada e mais propenso a erro. Pode
ser prudente marcar como `pending_review` ate aparecer um segundo receipt
que confirme o padrao — ou aprovar apenas com ressalva explicita de baixo
volume.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (STRING)
[ ] RECUSAR
[ ] ADIAR ate 2o receipt confirmar o padrao
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

---

## 4. O Que NAO Esta Neste Documento

Excluidos por construcao — sao Activity, nao Contribution, ate haver
imputabilidade humana ligada por evidencia:

| actor_original | receipts | razao |
|---|---:|---|
| `hios-forge-001` | 10 | SYSTEM_EXECUTOR |
| `hios-cinema-production` | 4 | SYSTEM_EXECUTOR |
| `WINDI-SYSTEM` | 2 | SYSTEM_EXECUTOR |
| `windi-hios-cinema-lab` | 2 | SYSTEM_EXECUTOR |

Nota: `hios-forge-001` tem 10 receipts — o segundo maior volume medido — e
mesmo assim nao e candidato. Volume nao e contribuicao.

---

## 5. Impacto da Aprovacao (Projecao, Nao Promessa)

Se os 5 candidatos forem aprovados:

```text
Receipts colapsando em did:windi:dragon-001:
  dragon-001 (6, ja resolvido)
  + dragon@windi-domain.com (11)
  + windi-hd-001 (7)
  + windi:hd:human-dragon (6)
  + W-HUMANDRAGON-001 (4)
  + HD-DRAGON-001 (1)
  = 35 receipts sob um unico DID canonico
```

De 6 receipts visiveis hoje para 35 — uma diferenca de **29 receipts** que
hoje estao invisiveis nao por ausencia de contribuicao, mas por ausencia de
alias formal. Esta projecao so vira fato apos aprovacao individual + selo.

---

## 6. Apos a Decisao

1. Cada fusao aprovada -> inserir em `did_aliases` com `status=active`,
   `alias_type` conforme proposto, e `resolution_evidence` apontando para
   este documento + atestado-testemunha.
2. Cada atestado-testemunha selado no Ledger (timestamp + hash).
3. Re-rodar `ALIAS-RUN-001` -> `ALIAS-RUN-002` para medir o novo estado
   com os aliases aprovados ja ativos.
4. So entao a base de identidade da Participation Layer esta pronta para
   `contribution-event.schema.json`.

---

## 7. Linha de Guarda

> Fundir identidade e o ato mais consequente da Participation Layer.
> Por isso nao se faz em bloco, nao se faz por inferencia sozinha,
> e nao se faz sem testemunha selada.
> Cada "este actor e o Human Dragon" e uma decisao, nao um calculo.
