# ALIAS-RESOLUTION-001

**Status:** SEALED  
**Date:** 2026-06-13  
**Depends on:** `CONTRIBUTION-GRAMMAR-001`, `MATRIZ-FATO-CONTRIBUICAO-001`  
**Constitutional Gate:** `ACTION-0-WITNESS-ADMISSIBILITY-001`  
**Purpose:** Definir quando um `actor` observado no Ledger pode ser associado a um DID canonico sem apagar a evidencia historica.
**I9 Decision:** Selado pelo Human Dragon em 2026-06-13.

## 1. Gate de Fundacao

Alias Resolution e pre-requisito bloqueante para a Participation Layer.

Sem resolucao confiavel de aliases, `contributors[]`, agregacao por participante, reconhecimento e qualquer metrica futura nascem corrompidos.

Alias Resolution tambem depende de admissibilidade de testemunha. Uma resolucao numerica pode dizer quantos actors colapsam num DID, mas nao define sozinha quem tem autoridade para reconhecer esse colapso.

```text
Receipt
  -> Actor Observado
  -> Alias Resolution
  -> Canonical DID
  -> Contribution Event
```

## 2. Principio

Nunca substituir o ator historico.

Preservar sempre:

```text
actor_original = identificador exatamente observado no fato
canonical_did  = DID canonico resolvido, quando houver confianca suficiente
```

Historia e normalizacao devem coexistir.

## 3. Fontes Consultadas

| Fonte | Caminho |
|---|---|
| DID aliases | `/opt/windi/did-genesis/did_genesis.db`, tabela `did_aliases` |
| DID identities | `/opt/windi/did-genesis/did_genesis.db`, tabela `identities` |
| Ledger receipts | `/opt/windi/data/forensic_ledger.sqlite3`, tabela `receipts` |

## 4. Estado Atual em DID Genesis

Aliases ja formalmente mapeados para `did:windi:dragon-001`:

| canonical_did | alias_actor | alias_type | status | Nota |
|---|---|---|---|---|
| `did:windi:dragon-001` | `Human Dragon` | STRING | active | Ledger actor string |
| `did:windi:dragon-001` | `human-dragon` | STRING | active | Ledger actor lowercase |
| `did:windi:dragon-001` | `human_dragon` | STRING | active | Ledger actor underscore |
| `did:windi:dragon-001` | `jober@a4desk.de` | EMAIL | active | Email alias |
| `did:windi:dragon-001` | `did:windi:windi-dragon` | DID | active | Legacy DID |
| `did:windi:dragon-001` | `did:windi:JOBER-MOGELE-CORREA-001` | DID | active | Enterprise uppercase DID |
| `did:windi:dragon-001` | `did:windi:dc110410-993d-4395-b7e9-7dca1d08af4f` | DID | active | Reactivated / merged |

Identidade canonica:

```text
did:windi:dragon-001
display_name: Human Dragon
email: jober@a4desk.de
role: founder
tier: ORACLE
status: active
sovereign_name: dragon-001
classification: CANONICAL
```

## 5. Aliases Observados no Ledger Ainda Nao Resolvidos

Consulta inicial em receipts reais:

| actor_original | receipts | apps observados | Resolucao candidata |
|---|---:|---|---|
| `dragon@windi-domain.com` | 11 | constitutional-process, w-lexicon-001, paper-001, libreiro, foundation-portals, windi-hios-cinema, ccode-opus | Precisa decisao: email institucional deve resolver para `did:windi:dragon-001`? |
| `hios-forge-001` | 10 | windi-hios-production | Provavel executor/sistema, nao pessoa |
| `windi-hd-001` | 7 | claude-code | Provavel Human Dragon, precisa evidencia |
| `dragon-001` | 6 | claudeWeb-pingpong, genesis-ceremony-v1, constitutional-council-v1, claude-code, windi-hios-cinema | Forte candidato via sovereign_name |
| `windi:hd:human-dragon` | 6 | windi-hios-cinema, w-generator-001 | Forte candidato por semantica, precisa alias formal |
| `W-HUMANDRAGON-001` | 4 | windi-hios, claude-code | Forte candidato, precisa alias formal |
| `hios-cinema-production` | 4 | windi-hios-cinema | Provavel executor/sistema |
| `WINDI-SYSTEM` | 2 | claude-code, ccode-cli | Sistema/executor; nao contributor direto sem imputabilidade humana |
| `windi-hios-cinema-lab` | 2 | windi-hios-cinema | Lab/processo, nao pessoa por default |
| `HD-DRAGON-001` | 1 | windi-hios | Forte candidato, precisa alias formal |

## 6. Classes de Resolucao

| Classe | Definicao | Pode gerar canonical_did? |
|---|---|---|
| `CANONICAL` | O actor ja e um DID canonico ativo | Sim |
| `FORMAL_ALIAS` | Existe em `did_aliases` com `status=active` | Sim |
| `SOVEREIGN_NAME_MATCH` | Actor igual ao `sovereign_name` de uma identidade ativa | Sim, com revisao |
| `EMAIL_MATCH` | Actor igual a email de identidade ativa ou alias email ativo | Sim, com normalizacao case-insensitive |
| `STRONG_CANDIDATE` | Padrao textual indica identidade, mas sem alias formal | Nao automatico; requer decisao |
| `SYSTEM_EXECUTOR` | Actor representa sistema, lab, forge, production, automation | Nao por default |
| `UNRESOLVED` | Sem correspondencia suficiente | Nao |

## 7. Regra v0.1

Resolucao automatica permitida apenas quando:

1. `actor_original` e DID canonico ativo em `identities`; ou
2. `actor_original` aparece em `did_aliases` com `status=active`; ou
3. `actor_original` corresponde exatamente a `sovereign_name` ativo, e a regra registra `resolution_class=SOVEREIGN_NAME_MATCH`; ou
4. `actor_original` corresponde a email ativo/alias email ativo, case-insensitive.

Todo o resto deve iniciar como:

```text
canonical_did = null
resolution_status = pending_review
```

## 8. Activity vs Contribution

Nem toda atividade e contribuicao.

Exemplo:

```text
actor_original = WINDI-SYSTEM
```

Pode representar execucao automatica, sincronizacao ou acao de infraestrutura. Isso e atividade verificavel, mas nao deve virar contribuicao atribuida sem imputabilidade observavel.

Regra candidata:

```text
SYSTEM_EXECUTOR pode gerar Activity Event.
SYSTEM_EXECUTOR so gera Contribution Event se houver actor humano/agente responsavel, aprovador ou originador ligado por evidencia.
```

## 9. Campos Candidatos para Contribution Event

Alias Resolution exige que o futuro Contribution Event preserve:

| Campo | Obrigacao |
|---|---|
| `actor_original` | Sempre obrigatorio |
| `canonical_did` | Nullable; preenchido apenas quando resolvido |
| `resolution_status` | `resolved`, `pending_review`, `unresolved`, `system_executor`, `contested` |
| `resolution_class` | Uma das classes da Secao 6 |
| `resolution_evidence` | Alias row, identity row, receipt, doc ou decisao humana |
| `resolved_at` | Timestamp da resolucao |
| `resolved_by` | Processo/agente/humano que aplicou a regra |
| `admissibility_level` | LEVEL 1, LEVEL 2 ou LEVEL 3 conforme `ACTION-0-WITNESS-ADMISSIBILITY-001` |
| `witness_class` | Obrigatorio para LEVEL 2; `AI_REPRODUCIBILITY` |
| `attested_at` | Timestamp do atestado de testemunha |
| `attestation_hash` | Hash do atestado selado no Ledger |
| `attested_dimensions` | `coherence`, `consistency`, `reproduction`, `no_obvious_conflict` |
| `witness_did` | DID da testemunha, quando aplicavel |
| `superseded_by` | Nullable; resolucao/atestado nunca e apagado, apenas superado |

## 10. Relacao com `contributors[]`

`contributors[]` e decorativo sem Alias Resolution.

Cada contributor deve preservar:

```text
actor_original
canonical_did
role
attribution_status
resolution_status
resolution_evidence
```

Contributors coletivos so sao confiaveis quando cada participante possui estado de resolucao explicito.

## 11. Regras de Status

`validation_status` e `attribution_status` sao ortogonais:

| Status | Escopo |
|---|---|
| `validation_status` | Estado do Contribution Event como interpretacao do fato |
| `attribution_status` | Estado de cada contributor dentro do evento |
| `resolution_status` | Estado do binding actor_original -> canonical_did |

Um evento pode ser `validation_status=validated` e ainda conter um contributor `attribution_status=contested`, desde que essa contestacao esteja explicita e nao seja usada para reconhecimento final ate resolucao.

Promocao para `validated`:

- eventos criados por agente: exigem revisao humana/I9 ou regra previamente aprovada;
- eventos HIGH/I9: seguem `ACTION-0-WITNESS-ADMISSIBILITY-001`;
- self-audit HIGH: LEVEL 1 proibido; exige LEVEL 2 na Liga atual ou LEVEL 3 quando houver segundo humano admissivel.

Niveis de admissibilidade herdados de `ACTION-0-WITNESS-ADMISSIBILITY-001`:

| Nivel | Descricao | Uso |
|---|---|---|
| LEVEL 1 | Self Attested | LOW/MEDIUM |
| LEVEL 2 | Self + Witnessed | HIGH na Liga atual, com `witness_class=AI_REPRODUCIBILITY` |
| LEVEL 3 | Independent Human Review | Padrao-ouro futuro |

Regra de honestidade:

```text
AI witness nao prova independencia de juizo.
AI witness prova reprodutibilidade temporal selada.
```

### 11.1 Admissibilidade da Propria Resolucao de Alias

Resolver um alias tambem e um ato interpretativo.

Especialmente:

```text
dragon@windi-domain.com -> did:windi:dragon-001
```

nao e detalhe tecnico; e decisao de identidade fundacional.

Regra:

- resolucao automatica por `CANONICAL`, `FORMAL_ALIAS`, `EMAIL_MATCH` ou `SOVEREIGN_NAME_MATCH` pode ser LEVEL 1 quando a regra ja esta formalmente registrada;
- resolucao de `STRONG_CANDIDATE` para o DID do fundador exige LEVEL 2 na Liga atual;
- resolucao de alias HIGH/I9 por agente deve registrar witness fields de `ACTION-0-WITNESS-ADMISSIBILITY-001` Secao 6;
- resolucao contestada ou ambigua permanece `pending_review`.

## 12. event_type + event_subtype

Para evitar migracao destrutiva:

```text
event_type     obrigatorio
event_subtype  nullable em v0.1
```

Exemplos:

| event_type | event_subtype |
|---|---|
| `intelectual` | `doctrine`, `architecture`, `hypothesis`, `synthesis` |
| `producao` | `document`, `schema`, `api`, `code`, `video`, `legal_petition`, `bundle` |
| `revisao` | `errata`, `audit`, `bugfix`, `constitutional_correction` |
| `governanca` | `i9_approval`, `policy_decision`, `seal`, `admissibility` |
| `operacional` | `deploy`, `handoff`, `maintenance`, `incident_response` |
| `evidencial` | `receipt`, `anchor`, `provenance`, `signature`, `verification` |

## 13. Proximas Acoes

1. Propor aliases formais para os candidatos fortes ligados a `did:windi:dragon-001`, com `dragon@windi-domain.com` como Priority Alias Candidate #1.
2. Manter executores de sistema como `SYSTEM_EXECUTOR` ate haver evidencia de imputabilidade.
3. Rodar a matriz fato-contribuicao com `actor_original`, `canonical_did`, `resolution_status` e `resolution_class`.
4. So depois criar `contribution-event.schema.json`.

## 14. Linha de Guarda

> A Participation Layer nao pode reconhecer contribuicao se antes nao sabe quem esta sendo reconhecido.
