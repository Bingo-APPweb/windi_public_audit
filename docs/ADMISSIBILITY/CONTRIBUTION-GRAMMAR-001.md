# CONTRIBUTION-GRAMMAR-001

**Status:** CANDIDATE  
**Mission:** Participation Layer Research Lead  
**Date:** 2026-06-13  
**Scope:** WINDI-HIOS Participation Layer, discovery phase  
**Blocking Gate:** `ALIAS-RESOLUTION-001`

## 1. Pergunta Central

O que constitui uma contribuicao verificavel dentro do WINDI-HIOS?

## 2. Principio

> O Ledger carrega o facto.  
> A Participation Layer carrega o significado contributivo desses factos.

Este documento nao modela token, wallet, mercado, distribuicao automatica ou recompensa financeira. Nesta fase, a missao e descobrir a gramatica verificavel da contribuicao.

## 3. Ordem Arquitetural

```text
Activity
  -> Contribution
  -> Validation
  -> Impact
  -> Recognition
  -> Reward / Token optional
```

O token, se existir, pertence ao fim da cadeia. Nao e origem, fundacao ou metrica primaria.

## 3.1 Gate Bloqueante: Alias Resolution

Antes de criar um schema operacional de Contribution Event, a Participation Layer precisa resolver uma pergunta de identidade:

```text
actor_original
  -> canonical_did
```

Sem isso, `contributors[]`, agregacao por participante e reconhecimento futuro ficam estatisticamente corrompidos.

Regra de guarda:

```text
actor_original nunca deve ser substituido.
canonical_did e uma normalizacao adicional, nullable e auditavel.
```

Ver: `ALIAS-RESOLUTION-001`.

## 4. Fontes Factuais Existentes

Primeira leitura no STRATO identificou as seguintes fontes ja vivas:

| Fonte | Caminho / Base | Relevancia |
|---|---|---|
| Receipt schema | `/home/windi/windi-proof-spec-v1/schemas/receipt.schema.json` | Define `actor`, `app`, `content_hash`, `governance_level`, `human_approved`, `policy_decision`, `invariants` |
| Ledger SQLite | `/opt/windi/data/forensic_ledger.sqlite3` | Tabela `receipts`; agrega fatos por `actor` e `app` |
| DID Genesis | `/opt/windi/did-genesis/` | Identidades, sessoes, aliases e tiers DID |
| DID database | `/opt/windi/did-genesis/did_genesis.db` | Tabelas `identities`, `did_aliases`, `sessions`, `login_events` |
| W-COST-001 | `/opt/windi/w-cost-001/cost_ledger.db` | Tabela `cost_events`; evidencia auxiliar de custo operacional |
| Cinema provenance | `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/` | Proveniencia por artefato, autoria de prompt, decisoes canonicas, invariantes |
| Memoria institucional | `/home/windi/CLAUDE.md`, `/home/windi/CLAUDE-HISTORY.md` | Liga IA+H, invariantes, sessoes, decisoes e receipts historicos |

## 5. Contribution Event

Um **Contribution Event** nao substitui um receipt.

Ele interpreta, de forma auditavel, um ou mais fatos registrados como uma contribuicao atribuivel.

### Exemplo

Receipt:

```text
did:windi:dragon-001 criou documento X no app windi-law
```

Contribution Event:

```text
DID dragon-001 realizou PRODUCAO_DOCUMENTAL no processo Y,
com evidencia receipt Z,
governance HIGH,
human_approved true,
impact_status pending.
```

## 6. Taxonomia Inicial

### A. Producao

Codigo produzido, documento criado, schema criado, API criada, artefato, video, peticao.

### B. Revisao

Erro identificado, falha evitada, correcao tecnica, correcao constitucional, revisao critica.

### C. Governanca

Aprovacao humana, validacao I9, decisao de politica, seal, classificacao de admissibilidade.

### D. Intelectual

Hipotese criada, arquitetura proposta, principio definido, doutrina criada, sintese decisiva.

### E. Operacional

Deploy, monitoramento, execucao, manutencao, resposta a incidente, consumo de infraestrutura.

### F. Evidencial

Receipt, prova, provenance, assinatura, verificacao, anchor, reproducibilidade.

## 7. Campos Obrigatorios Candidatos

| Campo | Funcao |
|---|---|
| `contribution_event_id` | Identificador unico do evento de contribuicao |
| `event_type` | Tipo da taxonomia: producao, revisao, governanca, intelectual, operacional, evidencial |
| `event_subtype` | Subtipo opcional/nullable em v0.1 para evitar migracao destrutiva futura |
| `actor` | Ator original observado no fato registrado |
| `canonical_did` | DID resolvido quando houver binding confiavel |
| `contributors` | Lista reservada para contribuicao coletiva; obrigatoria quando o fato tiver multiplos participantes identificaveis |
| `source_app` | App ou modulo de origem |
| `evidence_refs` | Receipts, hashes, commits, provenance files ou ledger anchors |
| `activity_timestamp` | Momento da atividade original |
| `created_at` | Momento em que a interpretacao contributiva foi criada |
| `governance_level` | Nivel herdado ou atribuido |
| `human_approved` | Se houve passagem explicita por I9 |
| `validation_status` | `pending`, `validated`, `rejected`, `superseded` |
| `impact_status` | Reservado em v0.1; nao operacional ate existir uma gramatica de impacto por dominio |
| `interpretation_basis` | Base estruturada e reconstruivel da classificacao; nao deve ser texto livre opaco |

### 7.1 `interpretation_basis` Estruturado

`interpretation_basis` nao deve ser uma opiniao serializada.

Forma candidata:

| Campo | Funcao |
|---|---|
| `rule_id` | Regra que permite classificar o fato como contribuicao |
| `rule_version` | Versao da regra aplicada |
| `evidence_refs` | Evidencias usadas pela regra |
| `matched_fields` | Campos concretos observados no fato original |
| `classifier` | Humano, agente ou processo que fez a classificacao |
| `classifier_version` | Versao do classificador, quando aplicavel |
| `confidence` | Confianca operacional, nao valor humano |
| `human_override` | Se houve correcao humana explicita |
| `review_required` | Se a classificacao exige revisao posterior |

Um Contribution Event admissivel nao e aquele que parece razoavel. E aquele cuja classificacao pode ser reproduzida por outro observador a partir das mesmas evidencias.

### 7.2 Contribuicao Coletiva

O WINDI-HIOS produz frequentemente por Liga IA+H, sessoes, sprints e pipelines multi-mao. Por isso, `actor` singular preserva o fato original, mas nao basta para representar contribuicao.

Forma candidata para `contributors[]`:

| Campo | Funcao |
|---|---|
| `actor` | Identificador observado no fato ou documento |
| `canonical_did` | DID resolvido, quando houver |
| `role` | `originator`, `author`, `reviewer`, `approver`, `witness`, `implementer`, `operator`, `classifier` |
| `evidence_refs` | Evidencias que sustentam este papel |
| `attribution_status` | `observed`, `claimed`, `validated`, `contested`, `superseded` |

Esta estrutura preserva causalidade. Nao distribui recompensa.

### 7.3 Criacao e Supersession

Pergunta constitucional aberta: quem pode criar ou superseder um Contribution Event?

Restricao candidata para v0.1:

- O ator nao deve ser juiz autonomo da propria admissibilidade contributiva.
- Eventos gerados por agente devem iniciar como `validation_status=pending`.
- `superseded` deve exigir referencia para o evento substituto e uma razao auditavel.
- Supersession de evento HIGH ou I9 deve exigir passagem humana explicita.

## 8. Campos Proibidos Nesta Fase

| Campo | Motivo |
|---|---|
| `token_amount` | Recompensa pertence a etapa posterior |
| `wallet_address` | Wallet nao faz parte da gramatica inicial |
| `financial_value` | Valor financeiro antes da contribuicao validada distorce incentivos |
| `human_worth_score` | O sistema mede contribuicoes, nao pessoas |
| `automatic_payout` | Distribuicao automatica e fora de escopo |
| `social_rank` | Visibilidade nao e contribuicao |
| `impact_score` | Impacto ainda nao possui gramatica operacional em v0.1 |

## 9. Relacao com Receipts

Receipts respondem:

```text
O que ocorreu?
Quem/qual actor registrou?
Onde ocorreu?
Como verificar?
```

Contribution Events respondem:

```text
Este fato registrado constitui uma contribuicao?
De que tipo?
Para qual processo?
Com qual evidencia?
Qual validacao possui?
Seu impacto ja foi observado?
```

## 10. Relacao com DID

DID Genesis fornece a base de identidade e capacidade:

- `identities`: DID, role, tier, status.
- `did_aliases`: binding entre aliases de actor e canonical DID.
- `sessions`: presenca ativa.
- `login_events`: rastro de acesso e agencia.

Participation Layer deve preferir `canonical_did` quando resolvivel, mas preservar o `actor` original como evidencia historica.

## 11. Relacao com W-COST

Regra:

```text
custo != valor
```

W-COST entra apenas como evidencia auxiliar:

- custo pode informar esforco operacional;
- custo pode informar consumo de infraestrutura;
- custo pode informar fase do processo;
- custo nao determina contribuicao;
- custo nao mede valor humano.

Uma chamada cara de API pode ter baixo impacto. Uma decisao arquitetural curta pode ter impacto alto.

## 12. Riscos Constitucionais

| Risco | Mitigacao |
|---|---|
| Premiar volume em vez de contribuicao | Separar activity, contribution e impact |
| Confundir custo com valor | W-COST apenas auxiliar |
| Confundir valor da contribuicao com valor da pessoa | Proibir qualquer score de dignidade ou valor humano |
| Incentivar captura por visibilidade | Evidencia e validacao acima de atencao |
| Automatizar recompensa cedo demais | Manter reward/token fora do v0.1 |
| Apagar autoria original via normalizacao | Preservar `actor` original e `canonical_did` resolvido |
| Criar metricas opacas | Todo calculo futuro deve ser reconstruivel |
| Reintroduzir opiniao por `interpretation_basis` | Usar base estruturada com regra, evidencia e campos observados |
| Apagar contribuicao coletiva | Modelar `contributors[]` sem recompensa associada |
| Prometer impacto antes da gramatica de impacto | Manter `impact_status` reservado em v0.1 |

## 13. Perguntas Abertas

1. Quais fatos registrados devem gerar Contribution Event automaticamente, e quais exigem revisao humana?
2. Como diferenciar atividade tecnica simples de contribuicao relevante sem depender de opiniao opaca?
3. Quais tipos de impacto podem ser observados por dominio: LAW, CINEMA, VERIFY, ENTERPRISE, TRAVEL?
4. Como registrar contribuicao intelectual sem inflacionar discussoes improdutivas?
5. Como lidar com contribuicoes coletivas em que o impacto so aparece meses depois?
6. Como versionar uma Contribution Grammar sem quebrar eventos antigos?
7. Onde deve viver o primeiro schema: `/opt/windi/schemas`, `windi-proof-spec`, ou novo modulo Participation?

## 14. Proxima Rodada

Antes de implementar schema ou API:

1. Mapear exemplos reais de receipts em LAW, CINEMA, VERIFY e ENTERPRISE.
2. Criar matriz de exemplos: fato registrado -> contribuicao candidata.
3. Identificar aliases de actor que ja resolvem para DID canonico.
4. Validar taxonomia com Conselho IA+H a partir dos exemplos reais.
5. So entao propor `contribution-event.schema.json`.

## 15. Frase de Guarda

> A Participation Layer nao nasceu para distribuir recompensas.  
> Ela nasceu para preservar a memoria verificavel da contribuicao humana e artificial.
