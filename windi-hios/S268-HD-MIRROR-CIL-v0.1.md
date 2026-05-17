# §268 — HD-Mirror v0.1 / Constitutional Interaction Layer (CIL)

```
Status:         SEALED
Data:           2026-05-17 (seal date)
Autoria:        Liga IA+H (Human Dragon + Guardian + Architect)
                Sessao de deliberacao do Conselho: 16 Mai 2026
                Sessao de selagem: 17 Mai 2026
Invariantes:    I9, I11, I14, §248, §266
Axioma:         "Friccao consciente e ferramenta de soberania."
Receipt:        WINDI-S268-HD-MIRROR-CIL-20260517
Hash:           sha256:2abf0050ae781709ce9cf9233716fe94ea2de0ed8e76306906f67d30347aa380
```

---

Este documento especifica o HD-Mirror v0.1, primeira instancia da
Constitutional Interaction Layer (CIL) do ecossistema WINDI.

O HD-Mirror e um friction engine — nao assistente, nao proxy, nao clone.
Existe para mediar o momento entre intencao e consequencia irreversivel,
devolvendo sempre a decisao ao humano.

---

## 1. Identidade e Funcao

### 1.1 O que e

- Friction engine constitucional
- Mediador entre User <-> consequencia <-> invariants
- Primeira instancia da Constitutional Interaction Layer (CIL)
- Instrumento de soberania, nao de conveniencia

### 1.2 O que nao e

- Nao e assistente (nao ajuda a completar tarefas)
- Nao e proxy do Human Dragon (nao delega autoridade)
- Nao e clone (nao replica criterio individual)
- Nao e Dragon (opera em timescale diferente: User-decision moment)
- Nao propoe, nao executa, nao confirma

### 1.3 Funcao nuclear

> Friccionar e devolver — nunca decidir.

O HD-Mirror cria o intervalo consciente entre "Sistema sugere" e
"Humano decide". Esse intervalo e onde vive a soberania do User.

### 1.4 Distincao de Guardian

Guardian protege invariantes em design/arquitectura (session-level).
HD-Mirror protege invariantes no momento do acto irreversivel (User-decision moment).
Operam em timescales diferentes, nao competem.

---

## 2. Invariantes Protegidos

| Invariante | Texto Canonico | Como HD-Mirror o Preserva |
|------------|----------------|---------------------------|
| **I9** | `human_approved=true` obrigatorio antes de qualquer seal. "I9 nao vive na entrada. I9 vive na saida." | HD-Mirror opera exactamente onde I9 vive — na saida, no momento do acto irreversivel. A friccao e a manifestacao operacional do passo "Humano decide" entre "Sistema sugere" e "Ledger sela". O Mirror nao decide nem sela; cria o intervalo consciente. |
| **I11** | Ledger receipt apos C6 = imutavel para sempre. | Porque o que se torna receipt e imutavel para sempre, HD-Mirror existe para que o User entenda o que esta a selar. Serve I11 ao garantir que o que se torna permanente foi consciente — nao acidente, nao rotina, nao pressa. |
| **I14** | Dados ausentes = erro explicito. Placeholders mascaram bugs. | Estado ausente ou inconsistente (wallet, DID, consentimento, track §248) -> abort com erro explicito. **Nunca friccao com mensagem generica, nunca placeholder.** Falha visivel, nao mascarada. |
| **§248** | Two-Track Foundation — track Civic permanente FREE + track Institutional pago, sem cruzamento sem consentimento explicito. | A forma da friccao pode adaptar-se ao track (du/Sie, tu/voce). O criterio de interpelacao nao. Nao ha discount de friccao por tier — isso seria violacao directa do proprio §248. |
| **§266** | Todo selo carrega autoria identificada. Triplo Gate: DID + Preview + Confirmacao. | HD-Mirror e parte funcional do Triplo Gate (C2). Friction ocorre apos DID-auth, antes da Confirmacao Textual. Garante que o selo carrega autoria consciente, nao apenas DID valido. Alinhado com C1 (opera apenas em SEAL, nao interfere em VERIFY) e C3 (friccao disponivel a todos os tracks, nao discriminada por tier). |

---

## 3. Triggers de Interpelacao

### 3.1 Onde intercepta

- Identity Gate :8192
- Fluxo wizard->POST
- Momento: apos DID-auth, antes de Confirmacao Textual (§266 C2)

### 3.2 Quando activa (lista exaustiva v0.1)

| Trigger | Descricao | Invariante |
|---------|-----------|------------|
| **T1** | Primeira escrita irreversivel vinculada ao DID do User | I11 |
| **T2** | Cruzamento de track §248 (Civic<->Institutional) | §248 |
| **T3** | Compromisso identitario (DID bind, wallet creation) | §266 |
| **T4** | Acto com consequencia financeira ou juridica declarada | I9 |

### 3.3 Quando NAO activa (exclusoes explicitas v0.1)

| Exclusao | Razao |
|----------|-------|
| **E1** | Reads, navegacao, queries — sem consequencia irreversivel |
| **E2** | Preview mode — visualizacao sem commit |
| **E3** | Operacoes internas de sistema (logs, health checks) |
| **E4** | Accoes ja abortadas por falha tecnica anterior |

### 3.4 Anti-pattern: friction-for-friction-sake

Se HD-Mirror activar em E1-E4, e bug — nao e governanca.
Friccao sem consequencia real degrada soberania em teatro.

---

## 4. Estrutura da Interpelacao Socratica

### 4.1 Forma da pergunta

A interpelacao nao e formulario. E momento de pausa estruturada.

Esqueleto abstracto:
1. **Nomear o acto** — o que o User esta prestes a fazer
2. **Evidenciar a consequencia** — o que se torna irreversivel
3. **Devolver a decisao** — sem sugerir resposta

Exemplo de forma (nao de conteudo):
> "Estas prestes a [ACTO]. Isto [CONSEQUENCIA]. Queres continuar?"

**Nota:** A formulacao literal das interpelacoes e design responsibility,
nao constitutional fixity — sujeita a teste contra P1–P5 em implementacao.

### 4.2 Propriedades obrigatorias

| Propriedade | Descricao |
|-------------|-----------|
| **P1** | Devolve decisao ao User — nunca retem |
| **P2** | Nao sugere resposta — nem implicitamente |
| **P3** | Nao julga — evidencia, nao avalia |
| **P4** | Evidencia consequencia real — nao abstracta |
| **P5** | Concisao cirurgica (I14) — so fala quando provocado, desliga apos devolver |

### 4.3 Anti-patterns (lista bloqueante)

| Anti-pattern | Descricao | Violacao |
|--------------|-----------|----------|
| **A1** | Sugerir resposta (explicita ou implicitamente) | I9 |
| **A2** | Framing assimetrico por tier ou demographic | §248 |
| **A3** | Friccao performativa sem evidenciar consequencia real | Axioma CIL |
| **A4** | Mensagem generica ou placeholder | I14 |
| **A5** | Reter decisao apos interpelacao (timeout->default) | I9 |
| **A6** | Dissertacao filosofica nao solicitada | I14, P5 |

### 4.4 Adaptacao por track (§248)

- **Forma** pode variar: du/Sie (DE), tu/voce (PT), tone formal/informal
- **Criterio** nao varia: mesma interpelacao, mesma consequencia evidenciada
- **Discount de friccao por tier = violacao §248**

---

## 5. Criterios de Abort

### 5.1 Distincao fundamental

| Tipo | Natureza | Accao HD-Mirror |
|------|----------|-----------------|
| **Abort constitucional** | Violacao objectiva de invariante — acto que User *nao pode* executar | Abort obrigatorio, registo, devolucao |
| **Mudanca de juizo** | Acto admissivel mas questionavel — User *pode* mas talvez *nao devesse* | Friccao + devolucao — **respeita decisao** |

**Linha vermelha:** HD-Mirror nunca aborta por mudanca de juizo. Fricciona, devolve, respeita.

### 5.2 Condicoes de abort constitucional (lista exaustiva v0.1)

| Codigo | Condicao | Invariante(s) |
|--------|----------|---------------|
| **AB1** | Wallet inconsistente no momento do acto | I14, §266 |
| **AB2** | DID-auth falhou ou expirou | §266 C2 |
| **AB3** | Preview nao foi mostrado ao User | §266 C2 |
| **AB4** | Confirmacao Textual nao foi explicita | §266 C2 |
| **AB5** | Tentativa de cruzar §248 sem consentimento declarado | §248 |
| **AB6** | Tentativa de escrita malformada que comprometeria integridade do Ledger | I11 |
| **AB7** | Estado ausente onde dado e obrigatorio | I14 |

**Nota:** Invariantes violam-se frequentemente em cluster (AB1 pode co-ocorrer com AB7).
O abort regista todos os invariantes violados, nao apenas o primeiro detectado.

### 5.3 Quem pode abortar fora do Human Dragon

| Actor | Condicao | Scope |
|-------|----------|-------|
| **HD-Mirror** | Qualquer AB1-AB7 detectado | Automatico |
| **Sentinel LAW** | Se implementado, sob condicoes proprias | Futuro |
| **Pioneers com role reviewer** | Mecanismo de peer-review | Futuro v0.2+ |

### 5.4 Evidencia de abort

Cada abort produz:
- `doc_type: constitutional_interaction`
- `subtype: abort`
- Lista de invariantes violados (codigos AB*)
- `wallet_id` do User (quando presente)
- `did_hash` do User (SHA-256 truncado)
- Timestamp
- Estado do Triplo Gate no momento (DID/Preview/Confirm)
- Destino: Forensic Ledger :8101

### 5.5 O que abort NAO faz

- Nao pune — regista
- Nao bloqueia permanentemente — User pode corrigir e tentar novamente
- Nao escala para Human Dragon automaticamente (v0.1) — apenas regista
- Nao envia notificacao externa (v0.1)

---

## 6. Evidencia Produzida

### 6.1 Em cada interpelacao (friction event)

| Campo | Descricao |
|-------|-----------|
| `doc_type` | `constitutional_interaction` |
| `subtype` | `friction` |
| `trigger` | Codigo T1–T4 que activou |
| `wallet_id` | ID do User (quando presente) |
| `did_hash` | SHA-256 truncado do DID |
| `timestamp` | ISO 8601 UTC |
| `outcome` | `proceeded` / `abandoned` |
| `track` | `civic` / `institutional` (§248) |

**Definicao operacional de outcome:**
- `proceeded` — User respondeu explicitamente com accao afirmativa
- `abandoned` — User respondeu com cancelamento, fechou sessao, ou nao respondeu

**Regra I9:** Estado intermedio sem decisao explicita = `abandoned`.
Timeout nunca implica consentimento. Nao-acto preserva I9.

### 6.2 Em cada abort

| Campo | Descricao |
|-------|-----------|
| `doc_type` | `constitutional_interaction` |
| `subtype` | `abort` |
| `violations` | Array de codigos AB1–AB7 |
| `wallet_id` | ID do User (quando presente) |
| `did_hash` | SHA-256 truncado do DID |
| `timestamp` | ISO 8601 UTC |
| `gate_state` | Estado do Triplo Gate (DID/Preview/Confirm) |

### 6.3 Destino

Forensic Ledger :8101

### 6.4 Retencao

Receipts de `constitutional_interaction` sao permanentes (I11).
Nao ha purge, nao ha TTL. Consequencia verificavel para sempre.

---

## 7. Distincao CIL <-> HD-Mirror

### 7.1 Definicoes

| Conceito | Definicao |
|----------|-----------|
| **Constitutional Interaction Layer (CIL)** | Camada arquitectural abstracta para mediacao User <-> consequencia <-> invariants |
| **HD-Mirror** | Primeira instancia concreta da CIL |

### 7.2 Relacao

HD-Mirror *e* CIL, da mesma forma que "cao" *e* "mamifero".
CIL define o contrato; HD-Mirror implementa-o no contexto Identity Gate :8192.

### 7.3 Condicoes minimas para ser CIL (Mirror Criteria)

Qualquer Mirror futuro deve satisfazer:

| Criterio | Descricao |
|----------|-----------|
| **MC1** | Intercepta acto User-driven |
| **MC2** | Devolve, nao decide |
| **MC3** | Produz receipt forense |
| **MC4** | Protege invariantes nomeados |

Quem satisfaz MC1–MC4 e Mirror. Quem nao satisfaz e outra coisa
(assistente, proxy, clone — todos os "nao e" do §1).

### 7.4 Porta aberta

Futuros Mirrors possiveis (nao comprometidos, apenas horizonte):
- Guardian-Mirror (vertice: arquitectura/lineage)
- Witness-Mirror (vertice: observacao/registo)
- Civic-Mirror (vertice: track FREE/§248)

Cada um com criterio de vertice constitucional diferente.
HD-Mirror nao os cria nem os impede.

---

## 8. Limitacoes Declaradas (v0.1)

### 8.1 O que esta versao explicitamente NAO faz

| Limitacao | Razao |
|-----------|-------|
| **L1** | Nao opera fora do Identity Gate :8192 (Travel/Memory/Enterprise nao tocados) | Escopo v0.1 |
| **L2** | Nao tem appeal mechanism para User | Complexidade deferida |
| **L3** | Nao modula tom por track §248 (du/Sie fica v0.2) | Design pass separado |
| **L4** | Nao tem i18n (v0.1 opera em lingua do sistema) | Complexidade deferida |
| **L5** | Nao escala para Human Dragon automaticamente | Pede §269 detector |
| **L6** | Nao envia notificacao externa | Complexidade deferida |
| **L7** | Nao detecta drift de sessao ou saturacao cognitiva | Pertence a §269 candidato |

### 8.2 Inputs externos considerados

| Input | Tratamento |
|-------|------------|
| Grok (sessao 16 Mai 2026) | Postura adversarial util como provocacao; arquitectura nao incorporada |
| GPT (detector de transicao) | Conceito valido; deferido para §269 candidato por disciplina de escopo |

### 8.3 Divida tecnica reconhecida

- Formulacao literal das interpelacoes (§4.1) — design pass pendente
- Testes de enviesamento yes/no em P2 — validation pass pendente
- Cobertura de edge cases em AB1–AB7 — smoke tests pendentes

---

## 9. Criterios de Sucesso v0.1

### 9.1 Pronto para implementacao (1.B) quando:

| Criterio | Query verificavel |
|----------|-------------------|
| **S1** | Todas as seccoes §1–§8 aprovadas pelo Guardian |
| **S2** | Zero bloqueantes abertos |
| **S3** | Texto canonico de invariantes confirmado contra filesystem |
| **S4** | Doc_type `constitutional_interaction` registado no schema do Ledger |

### 9.2 Pronto para Travessia Zero quando:

| Criterio | Query verificavel |
|----------|-------------------|
| **S5** | HD-Mirror implementado e deployed em :8192 |
| **S6** | 100% dos triggers T1–T4 produzem friction event no Ledger |
| **S7** | 100% das condicoes AB1–AB7 produzem abort com evidencia completa |
| **S8** | Human Dragon atravessa como debug, observa HD-Mirror em accao |

### 9.3 Pronto para Travessia Aliada quando:

| Criterio | Query verificavel |
|----------|-------------------|
| **S9** | Travessia Zero concluida sem abort por bug |
| **S10** | Pioneer existente (voluntario) atravessa pelo canonico |
| **S11** | Friction events e possiveis aborts registados e auditados |

---

## Anexo A — Genealogia do Conceito

### A.1 Cronologia da sessao fundadora (16 Mai 2026)

| Hora (UTC) | Evento |
|------------|--------|
| ~08:00 | Fix health-checks :8145->:8114 (commit df3feb6e9) |
| ~09:00 | Deliberacao do Conselho: qual a primeira "carne"? |
| ~10:00 | Convergencia: Sprint 2 = Pioneer #1 = HD-Mirror como Tijolo 1 |
| ~11:00 | Grok introduz friccao adversarial (6 perguntas) |
| ~12:00 | Guardian reformula: Mirror vs Clone, integracao I9/§266 |
| ~13:00 | Gemini desenha fluxo pratico, Interpelacao Socratica |
| ~14:00 | GPT eleva a Constitutional Interaction Layer, liga a §262 HIOS |
| ~14:30 | Outline aprovado, Tempo 2 iniciado |

### A.2 Contribuicoes por voz

| Voz | Contribuicao |
|-----|--------------|
| **Human Dragon** | Intuicao inicial "HD-Clone"; decisao de consultar Conselho; autorizacao final |
| **Grok** | Friccao inicial (6 perguntas); identificou tautologia fundacional e dogfooding |
| **Guardian (Claude.ai)** | Reformulacao Mirror vs Clone; integracao I9/§266; revisao constitucional |
| **Gemini** | Fluxo pratico; Interpelacao Socratica como UX; "friccao consciente e ferramenta de soberania" |
| **GPT** | Elevacao a CIL; ligacao a §262 HIOS; §269 candidato (detector) |
| **Architect (CCode)** | Redaccao do pergaminho; resolucao de gaps; estrutura operacional |

### A.3 Inputs recusados (com razao)

| Input | Razao da recusa |
|-------|-----------------|
| Spec do Grok para HD-Mirror | Arquitectura sem patria WINDI; postura adversarial util, substrato nao |
| Detector de transicao (GPT) | Conceito valido mas pertence a §269, nao a v0.1 |

### A.4 Axioma fundador

> "Friccao consciente e ferramenta de soberania."
> — Emergiu da sessao Gemini, 16 Mai 2026

### A.5 Lineage constitucional

§261 W-BIND-001 -> §262 HIOS Naming -> §263 PingPong -> §264 Genesis ->
§266 PAF -> §267 ERRATA -> **§268 HD-Mirror/CIL**

---

*Liga IA+H — Kempten, Bavaria — 2026-05-16*
*"Friccao consciente e ferramenta de soberania."*
