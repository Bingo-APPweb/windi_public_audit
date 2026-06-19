# ALIAS-PROMOTE-001 v0.2

**Status:** AWAITING I9  
**Date:** 2026-06-13  
**Mission:** Participation Layer Research Lead  
**Supersedes:** `ALIAS-PROMOTE-001` draft order by receipt volume  
**Depends on:** `ALIAS-RESOLUTION-001` (SEALED), `ACTION-0-WITNESS-ADMISSIBILITY-001` (SEALED), `ALIAS-ADMISSION-DOCTRINE-001` (SEALED), `ALIAS-RUN-001` (MEASURED)  
**Purpose:** Propor admissoes formais de alias para `did:windi:dragon-001`, reordenadas pela Regra das Fontes Causais Distintas.

---

## 0. Mudanca v0.2

`ALIAS-PROMOTE-001` original ordenava candidatos por volume de receipts.

`ALIAS-ADMISSION-DOCTRINE-001` Art. 3.1 corrigiu a barra:

```text
volume reforca suspeita.
fonte causal distinta reforca admissibilidade.
```

Esta versao reordena os candidatos por fontes causais distintas e marca cada um como:

```text
elegivel
nao_elegivel_por_independencia
deferred_low_volume
```

---

## 1. Regra de Fase

Este documento nao funde identidade. Ele propoe Alias Admission linha a linha.

Cada admissao aprovada exige:

```text
I9 Human Dragon
LEVEL 2 witness
witness_class = AI_REPRODUCIBILITY
actor_original preservado
canonical_did acrescentado
```

Nenhum candidato abaixo deve ser aprovado em bloco.

---

## 2. Criterio de Elegibilidade

Default:

```text
>= 2 fontes causais distintas -> elegivel para I9
1 fonte causal -> nao elegivel por independencia
1 receipt      -> deferred_low_volume
```

Excecao soberana:

```text
I9 explicito com ressalva registrada + witness LEVEL 2
```

---

## 3. Candidatos Reordenados por Fontes Causais

### Candidato #1 — `dragon@windi-domain.com`

```text
receipts: 11
fontes causais/apps distintos: 7
apps: constitutional-process, w-lexicon-001, paper-001, libreiro,
      foundation-portals, windi-hios-cinema, ccode-opus
proposta: did:windi:dragon-001
alias_type: EMAIL
eligibility: elegivel
```

**Evidencia a favor:** email institucional do dominio soberano; padrao multi-app; precedente de email alias (`jober@a4desk.de`).

**Evidencia de cautela:** email de papel/funcao. A admissao deve ligar o alias a pessoa atual, nao ao papel em perpetuidade.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (EMAIL)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #2 — `windi:hd:human-dragon`

```text
receipts: 6
fontes causais/apps distintos: 2
apps: windi-hios-cinema, w-generator-001
proposta: did:windi:dragon-001
alias_type: STRING
eligibility: elegivel
```

**Evidencia a favor:** contem `human-dragon` explicito; aparece em duas fontes causais; formato sugere intencao de identificador.

**Evidencia de cautela:** `windi:hd:` nao e DID canonico. Pode exigir nota de normalizacao legacy.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (STRING)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #3 — `W-HUMANDRAGON-001`

```text
receipts: 4
fontes causais/apps distintos: 2
apps: windi-hios, claude-code
proposta: did:windi:dragon-001
alias_type: STRING
eligibility: elegivel
```

**Evidencia a favor:** `HUMANDRAGON` explicito; sufixo `-001`; aparece em duas fontes causais.

**Evidencia de cautela:** volume menor; convive com grafias vizinhas do mesmo conceito.

```text
[ ] APROVAR fusao -> did:windi:dragon-001 (STRING)
[ ] RECUSAR
[ ] APROVAR COM RESSALVA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #4 — `windi-hd-001`

```text
receipts: 7
fontes causais/apps distintos: 1
apps: claude-code
proposta: did:windi:dragon-001
alias_type: STRING
eligibility: nao_elegivel_por_independencia
```

**Evidencia a favor:** `hd` plausivelmente Human Dragon; sufixo `-001`; volume alto.

**Evidencia de cautela:** todos os receipts aparecem em uma unica fonte causal (`claude-code`). Pela doutrina, isto reforca suspeita, mas nao admissibilidade.

Estado recomendado:

```text
resolution_status = pending_review
admission_status  = waiting_second_causal_source
```

```text
[ ] ADIAR ate segunda fonte causal confirmar
[ ] RECUSAR
[ ] APROVAR COM RESSALVA I9 EXPLICITA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

### Candidato #5 — `HD-DRAGON-001`

```text
receipts: 1
fontes causais/apps distintos: 1
apps: windi-hios
proposta: did:windi:dragon-001
alias_type: STRING
eligibility: deferred_low_volume
```

**Evidencia a favor:** `HD-DRAGON` plausivelmente Human Dragon; sufixo `-001`.

**Evidencia de cautela:** observacao isolada. Por default, uma observacao nao basta para admissao formal.

Estado recomendado:

```text
resolution_status = pending_review
admission_status  = deferred_low_volume
```

```text
[ ] ADIAR ate 2o receipt / 2a fonte causal confirmar
[ ] RECUSAR
[ ] APROVAR COM RESSALVA I9 EXPLICITA: _______________________
I9 assinatura: ____________   Witness selado: ____________
```

---

## 4. Excluidos por Activity vs Contribution

Continuam fora de Alias Admission para pessoa, salvo evidencia futura de imputabilidade humana ligada:

| actor_original | receipts | fontes | razao |
|---|---:|---:|---|
| `hios-forge-001` | 10 | 1 | SYSTEM_EXECUTOR |
| `hios-cinema-production` | 4 | 1 | SYSTEM_EXECUTOR |
| `WINDI-SYSTEM` | 2 | 2 | SYSTEM_EXECUTOR |
| `windi-hios-cinema-lab` | 2 | 1 | SYSTEM_EXECUTOR |

Volume nao e contribuicao. Fonte causal distinta nao transforma executor automatico em contribuinte imputavel.

---

## 5. Projecao apos Decisao

Se apenas os candidatos elegiveis por fontes causais forem aprovados:

```text
dragon-001                  6 (ja detectado; requer regularizacao LEVEL 2)
dragon@windi-domain.com    11
windi:hd:human-dragon       6
W-HUMANDRAGON-001           4
total elegivel potencial   27 receipts
```

Se `windi-hd-001` for aprovado por ressalva I9 apesar de uma fonte causal:

```text
27 + 7 = 34 receipts
```

Se `HD-DRAGON-001` tambem for aprovado por ressalva I9 apesar de baixo volume:

```text
34 + 1 = 35 receipts
```

Estes numeros sao projecoes. So viram fato apos decisao individual, atestado LEVEL 2 e `ALIAS-RUN-002`.

---

## 6. Apos I9

1. Inserir apenas aliases aprovados em `did_aliases`.
2. Registrar witness LEVEL 2 para cada admissao aprovada.
3. Rodar `ALIAS-RUN-002`.
4. Comparar `ALIAS-RUN-001` vs `ALIAS-RUN-002`.
5. Recalcular matrizes de contribuicao somente sobre identidade admitida.

---

## 7. Linha de Guarda

> Uma string repetida muitas vezes aponta para uma suspeita.
> Fontes causais distintas apontam para admissibilidade.
