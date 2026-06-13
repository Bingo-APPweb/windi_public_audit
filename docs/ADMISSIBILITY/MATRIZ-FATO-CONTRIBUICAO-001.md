# MATRIZ-FATO-CONTRIBUICAO-001

**Status:** CANDIDATE  
**Date:** 2026-06-13  
**Parent:** `CONTRIBUTION-GRAMMAR-001`  
**Purpose:** Testar a taxonomia de contribuicao contra fatos reais do Ledger antes de criar schema, API ou banco.

## 1. Regra de Fase

Este documento nao modela token, wallet, recompensa, mercado ou distribuicao automatica.

Ele apenas pergunta:

```text
Este fato registrado pode ser interpretado como contribuicao verificavel?
Se sim, de que tipo, por qual regra e com quais evidencias?
```

## 2. Metodo

Fonte consultada:

```text
/opt/windi/data/forensic_ledger.sqlite3
```

Campos observados:

```text
id, created_at, actor, app, doc_type, governance_level, sge_score, status, content_hash prefix
```

Os exemplos abaixo usam amostras reais e evitam inferir impacto. `impact_status` permanece reservado em v0.1.

## 3. Interpretation Basis v0.1

Para evitar texto livre opaco, cada linha usa uma base de interpretacao estruturada:

| Campo | Significado |
|---|---|
| `rule_id` | Regra aplicada |
| `matched_fields` | Campos do fato que sustentam a classificacao |
| `evidence_refs` | Receipt/hash/app usados como evidencia |
| `confidence` | Confianca operacional da classificacao |
| `review_required` | Se exige revisao humana/conselho |

## 4. Regras Candidatas

| Rule ID | Descricao |
|---|---|
| `CG-PROD-DOC-001` | Receipt sealed com `doc_type=doc` em app produtivo pode indicar producao documental ou artefactual |
| `CG-GOV-HIGH-001` | `governance_level=HIGH` e tema constitucional/doutrinario indica contribuicao de governanca candidata |
| `CG-REV-ERRATA-001` | Receipt com `ERRATA`, audit ou correcao indica revisao/correcao candidata |
| `CG-OPS-HANDOFF-001` | `doc_type=cognitive_handoff` indica contribuicao operacional de continuidade cognitiva |
| `CG-OPS-SEC-001` | Receipt de incidente, hardening ou seguranca indica contribuicao operacional/forense |
| `CG-EVID-PROV-001` | Receipt de verificacao, anchor, provenance ou seal indica contribuicao evidencial |
| `CG-INT-DOCTRINE-001` | Receipt de doutrina, principio, matriz ou arquitetura indica contribuicao intelectual candidata |

## 5. Matriz Inicial

| # | Fato Registrado | Contribution Candidate | Interpretation Basis | Confidence | Open Questions |
|---|---|---|---|---|---|
| 1 | `WINDI-DOCTRINE-CINE-VERIFY-001-20260612`; actor `windi-hd-001`; app `claude-code`; `doc`; HIGH; sealed | Intelectual + Governanca: doutrina selada | `rule_id=CG-INT-DOCTRINE-001`; matched: receipt id contains `DOCTRINE`, HIGH, sealed; evidence: receipt + content hash prefix `sha256:b4cf91c6e` | High | Contribuicao coletiva precisa listar Human Dragon, Guardian, CCode/Codex quando evidencias de sessao confirmarem |
| 2 | `TWIN-B-SEC-001`; actor `did:windi:dragon-001`; app `claude-code`; `doc`; HIGH; sealed | Operacional + Evidencial: resposta a incidente/hardening | `rule_id=CG-OPS-SEC-001`; matched: id contains `SEC`, HIGH, sealed; evidence: receipt + history session | High | Separar descoberta, correcao, auditoria e seal como sub-eventos? |
| 3 | `OLLAMA-FASE0-001`; actor `did:windi:dragon-001`; app `claude-code`; `doc`; HIGH; sealed | Operacional: preparacao/execucao de fase de infraestrutura | `rule_id=CG-OPS-HANDOFF-001`; matched: phase receipt, HIGH, sealed; evidence: receipt | Medium | Precisa distinguir fase tecnica de contribuicao estrategica? |
| 4 | `WINDI-BIND-20260605100505-9E5B9283`; actor `did:windi:dragon-001`; app `W-BIND-001`; `cognitive_handoff`; LOW; sealed | Operacional: continuidade cognitiva | `rule_id=CG-OPS-HANDOFF-001`; matched: app W-BIND-001, doc_type cognitive_handoff; evidence: receipt | High | Handoff deve gerar contribuicao individual ou apenas atividade auxiliar? |
| 5 | `WINDI-MAINT-OVERFLOW-20260531-0F232BFE`; actor `did:windi:dragon-001`; app `claude-code`; `audit-bundle`; LOW; sealed | Revisao + Operacional: manutencao de memoria/overflow | `rule_id=CG-REV-ERRATA-001`; matched: id contains MAINT/OVERFLOW, audit-bundle; evidence: receipt | Medium | Manutencao de contexto deve ter categoria propria? |
| 6 | `WINDI-TEMPLATE-001-SYSTEMD-20260531-99D55284`; actor `did:windi:dragon-001`; app `claude-code`; `doc`; MEDIUM; sealed | Producao: template tecnico/documental | `rule_id=CG-PROD-DOC-001`; matched: TEMPLATE, doc, sealed; evidence: receipt | Medium | Sem ler conteudo, nao sabemos se e schema, doc ou codigo operacional |
| 7 | `WINDI-S285-HEL-ERRATA-20260519192628`; actor `WINDI-SYSTEM`; app `claude-code`; `doc`; HIGH; sealed | Revisao: errata/correcao candidata | `rule_id=CG-REV-ERRATA-001`; matched: id contains ERRATA, HIGH, sealed; evidence: receipt | High | Actor `WINDI-SYSTEM` deve resolver para sistema, humano aprovador ou ambos? |
| 8 | `WINDI-S285-HEL-CHARTER-20260519182952`; actor `W-HUMANDRAGON-001`; app `claude-code`; `doc`; HIGH; sealed | Governanca + Intelectual: charter | `rule_id=CG-GOV-HIGH-001`; matched: CHARTER, HIGH, sealed; evidence: receipt | High | Requer contributors[] da sessao se houver Liga IA+H declarada |
| 9 | `WINDI-MAP-SELF-AUDIT-EXERCISED-20260519141117-651B3B76`; actor `did:windi:dragon-001`; app `claude-code`; `constitutional`; HIGH; sealed | Revisao + Governanca: self-audit constitucional | `rule_id=CG-GOV-HIGH-001`; matched: constitutional, HIGH, SELF-AUDIT; evidence: receipt | High | Self-audit por mesmo ator deve exigir revisor externo? |
| 10 | `WINDI-S261-v030-RUNTIME-20260519141101-3F1FF722`; actor `did:windi:dragon-001`; app `W-BIND-001`; `constitutional`; HIGH; sealed | Governanca + Operacional: runtime constitucional | `rule_id=CG-GOV-HIGH-001`; matched: constitutional, HIGH, W-BIND-001; evidence: receipt | High | Separar contribuicao de design e contribuicao de execucao? |
| 11 | `WINDI-ATR-S299-20260604`; actor `did:windi:dragon-001`; app `windi-hios-cinema`; `doc`; HIGH; sealed | Intelectual/Governanca: artefato Cinema de alto governo | `rule_id=CG-INT-DOCTRINE-001`; matched: app cinema, HIGH, sealed; evidence: receipt | Medium | Sem ler documento, classificacao exata permanece aberta |
| 12 | `WINDI-SPINE-TEST-002-RUNWAY-20260601211300`; actor `windi-hios-cinema-lab`; app `windi-hios-cinema`; `doc`; HIGH; sealed | Evidencial + Producao: teste de SPINE/generativo | `rule_id=CG-EVID-PROV-001`; matched: SPINE-TEST, app cinema, HIGH; evidence: receipt | Medium | Deve ser atribuida ao lab, ao prompt author, ao aprovador I9 ou todos? |
| 13 | `WINDI-S295-S14-ERRATA-20260530225939`; actor `hios-cinema-production`; app `windi-hios-cinema`; `doc`; HIGH; sealed | Revisao: errata de producao Cinema | `rule_id=CG-REV-ERRATA-001`; matched: ERRATA, cinema, HIGH; evidence: receipt | High | Precisa associar ao shot/obra correspondente |
| 14 | `WINDI-S295-S14-COMPOSED-20260530223358`; actor `hios-cinema-production`; app `windi-hios-cinema`; `doc`; HIGH; sealed | Producao + Evidencial: composicao de shot/artefato | `rule_id=CG-PROD-DOC-001`; matched: COMPOSED, cinema, HIGH; evidence: receipt | Medium | Confirmar se content_hash aponta para video, manifesto ou documento |
| 15 | `WINDI-S284-SPINE-BIRTH-20260527194532-b18082b9`; actor `dragon@windi-domain.com`; app `windi-hios-cinema`; `constitutional`; HIGH; sealed | Intelectual + Governanca: nascimento SPINE | `rule_id=CG-INT-DOCTRINE-001`; matched: SPINE-BIRTH, constitutional, HIGH; evidence: receipt | High | Alias email deve resolver para DID canonico |
| 16 | `WINDI-S284-ELISA-ANCHOR-20260527194534-b518fa70`; actor `dragon@windi-domain.com`; app `windi-hios-cinema`; `constitutional`; HIGH; sealed | Evidencial: anchor/canonizacao | `rule_id=CG-EVID-PROV-001`; matched: ANCHOR, constitutional, HIGH; evidence: receipt | High | Contributors[] deve incluir decisor e gerador se provenance existir |
| 17 | `WINDI-HIOS-WEBTOON-CAP1-20260522094724-1cd39dbd`; actor `hios-production-001`; app `windi-hios-production`; `doc`; MEDIUM; sealed | Producao: artefato narrativo/visual | `rule_id=CG-PROD-DOC-001`; matched: WEBTOON, production, doc; evidence: receipt | Medium | Categoria Producao precisa subtipos: texto, visual, codigo, legal |
| 18 | `WINDI-GARDEN-PAGE1-BUNDLE-20260521192509`; actor `hios-forge-001`; app `windi-hios-production`; `doc`; MEDIUM; sealed | Producao + Evidencial: bundle/pagina | `rule_id=CG-PROD-DOC-001`; matched: PAGE/BUNDLE, production; evidence: receipt | Medium | Bundle pode representar agregacao de contribuicoes anteriores |
| 19 | `WINDI-PILOT-HELENA-MEYER-20260612`; actor `windi-hd-001`; app `claude-code`; `doc`; MEDIUM; sealed | Producao + Evidencial: estado/piloto de personagem | `rule_id=CG-PROD-DOC-001`; matched: PILOT, character name, doc; evidence: receipt | Medium | Ligar ao provenance JSON e a decisoes de likeness gate |
| 20 | `WINDI-MATRIX-15-PAIRS-20260612`; actor `windi-hd-001`; app `claude-code`; `doc`; MEDIUM; sealed | Intelectual/Evidencial: matriz de pares | `rule_id=CG-INT-DOCTRINE-001`; matched: MATRIX, doc, sealed; evidence: receipt | Medium | Matriz pode ser insumo de validacao, nao contribuicao final |

## 6. Descobertas da Matriz

1. A taxonomia inicial sobrevive ao primeiro contato com receipts reais, mas precisa de subtipos.
2. `Intelectual` e amplo demais; deve ser dividido futuramente em doutrina, arquitetura, hipotese e sintese.
3. `Producao` tambem e amplo; deve distinguir legal, codigo, documento, visual, video, schema e bundle.
4. Muitos fatos sao coletivos, mas o Ledger registra um `actor` singular. `contributors[]` e necessario.
5. `actor` possui aliases heterogeneos: DID, email, system id, lab id, app id. DID aliasing sera etapa critica.
6. `impact_status` nao deve ser operacional nesta fase. Os exemplos nao permitem medir impacto sem observacao posterior.
7. W-COST nao aparece como fonte primaria de contribuicao nesta matriz. Continua evidencia auxiliar.

## 7. Proxima Acao Recomendada

Antes de criar `contribution-event.schema.json`:

1. Enriquecer esta matriz com 50-100 exemplos reais.
2. Resolver aliases frequentes contra DID Genesis quando possivel.
3. Ler alguns payloads/metadados completos para diferenciar producao, evidencia e governanca.
4. Definir `interpretation_basis.rule_id` como registry versionado.
5. Validar com Conselho IA+H a partir desta matriz, nao apenas por discussao abstrata.

## 8. Linha de Guarda

> Um Contribution Event admissivel nao e aquele que parece razoavel.  
> E aquele cuja classificacao pode ser reproduzida por outro observador a partir das mesmas evidencias.
