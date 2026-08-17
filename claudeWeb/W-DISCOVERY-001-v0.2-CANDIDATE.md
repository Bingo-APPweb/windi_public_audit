# W-DISCOVERY-001 — WINDI Discovery Engine
**Versão:** 0.2 CANDIDATE
**Estado:** NOT SEALED — aguarda Gate D-SPEC (exclusivamente Human Dragon)
**Data:** 2026-08-16
**Origem:** CCode (Opus 4.5) — consolidação de v0.1 + A1 + A2 + A3 + A4 + Fase 0
**Doutrina:** DOCUMENTED≠ACTIVE · Propose≠Execute · §268 (correção por APPEND)

---

## Linhagem

```
W-DISCOVERY-001 v0.1 — NOT SEALED — preservado
├── REVIEW-A1 — requisitos A–J
│   └── REVIEW-A2 — errata gates/escopo/protocolo (Disp. 1–6)
│       └── REVIEW-A3 — errata transições (Disp. 1–4)
│           └── REVIEW-A4 — clarificação terminal (Disp. 1–3)
└── FASE0-AUDIT-REPORT-20260815 — evidência read-only
    └── W-DISCOVERY-001 v0.2 — este documento
```

---

## 0. Tese

> O HIOS não precisa ser procurado pelo nome. Ele precisa ser encontrado no momento em que alguém precisa transformar uma intenção em algo confiável.

O WINDI Discovery Engine é a **camada pública candidata** (A1-A rebaixado): uma superfície de descoberta que educa, demonstra, captura intenção e encaminha cada pessoa (Human ou IA Fremde) ao instrumento correcto — sem exigir conhecimento prévio de HIOS, invariantes, Ledger ou receipts.

**Princípio comercial central:** o WINDI não vende acesso a respostas. O WINDI vende **capacidade verificável**.

**Cadeia estratégica:**
```
intenção → relacionamento humano+IA → estrutura → artefacto → prova → reutilização
```

`AI processes. Human decides. WINDI guarantees.`

---

## 1. Mapa WINDI de Necessidades (taxonomia v0.2)

Quatro verbos públicos como ponte entre filosofia interna e linguagem quotidiana:

### PREPARAR
- Preparar uma decisão importante
- Organizar informações dispersas
- Preparar conteúdo antes de usar IA (corredor Pré-AI / Playground)
- Transformar intenção em briefing ou artefacto

### VERIFICAR
- Identificar fontes e lacunas
- Verificar autoria e versão
- Comparar propostas sem perder evidências
- Compreender riscos antes de continuar

### AUTORIZAR
- Definir quem pode decidir
- Revisar o que a IA produziu
- Registrar aprovação humana
- Separar proposta de execução

### PUBLICAR
- Publicar com proveniência (W-Sites)
- Distribuir declaração verificável (W-Email)
- Manter histórico e rollback
- Emitir receipt público

---

## 2. O Momento Mágico (produto de entrada único)

**Uma única experiência central antes de qualquer catálogo:**

> "Descreva o que você precisa preparar, decidir, verificar ou publicar."

Ciclo executável — **DESIGN TARGET: ~30 segundos** (A1-G reclassificado):

1. Reconhecimento da intenção
2. Poucas perguntas necessárias
3. Estruturação: contexto, riscos, fontes, lacunas
4. Artefacto produzido
5. Decisão humana solicitada
6. Receipt gerado

**Ponto de integração verificado (Fase 0):**
- Playground :8120 — ✅ VERIFIED (VPSE engine online)
- Triad SELADO/PLAYGROUND-ORIGIN/NÃO-VERIFICÁVEL — REFERENCED / NOT VERIFIED

---

## 3. Taxonomia de Receipts (A1-C)

Três tipos distintos, nunca confundíveis:

| Tipo | Função | Verbo do Mapa |
|------|--------|---------------|
| **Preparation Receipt** | Prova de preparação; NÃO implica autorização | PREPARAR |
| **Authorization Receipt** | Emitido somente após decisão I9 válida | AUTORIZAR |
| **Publication Receipt** | Prova de materialização pública | PUBLICAR |

**Regra dura:** A superfície visual de um Preparation Receipt nunca pode ser confundível com prova de autorização.

---

## 4. Receipt Humano-Legível (pré-requisito duro)

O receipt público deve responder visualmente — **DESIGN TARGET: ≤10 segundos** (A1-G reclassificado):

| # | Pergunta | Campo |
|---|----------|-------|
| 1 | O que foi preparado? | doc_name / doc_type |
| 2 | Para qual finalidade? | declared_purpose |
| 3 | Quais fontes? | sources[] |
| 4 | Qual território? | territory (RRL) |
| 5 | Quando? | created_at |
| 6 | IA participou? | ai_involvement |
| 7 | Quem revisou? | reviewer (minimizado — A1-E) |
| 8 | Quem autorizou? | authorized_by (I9 trail, minimizado) |
| 9 | Mudou depois? | version chain / hash chain |
| 10 | Como verificar? | verify URL (:8114 canonical) |

**Critério:** um Fremde abre o receipt e compreende os 10 pontos sem manual.

**Estado verificado (Fase 0):** Verify :8114 — ✅ ONLINE (wcache unavailable, funcionalidade core OK)

---

## 5. Regional Relevance Layer (RRL v0.2) — A1-D corrigido

### Estrutura obrigatória

```
RRL-DACH (envelope regional)
├── RRL-DE  (fontes, vigência, limites, política de atualização próprias)
├── RRL-AT  — DECLARED / NOT COVERED
└── RRL-CH  — DECLARED / NOT COVERED
```

### Justificativa RRL-DE (A2-Disp.4)

> "RRL-DE é o primeiro pacote candidato por prioridade operacional e proximidade territorial com Kempten. Essa proximidade não constitui evidência de cobertura, competência jurídica ou prontidão regional."

RRL-DE só sai de CANDIDATE com pacote próprio: fontes, vigência, limites, política de actualização — e avaliação de adequação profissional onde o tema exigir.

**Proibido:** afirmar "cobertura DACH" enquanto AT/CH não tiverem pacotes selados.

---

## 6. Minimização de Identidade (A1-E + A2-Disp.5)

### Perfil de Disclosure Contextual

Campos `reviewer` e `authorized_by` suportam, por ordem de preferência:

1. Identificador público minimizado (adequado ao contexto)
2. Função ou capacidade de autorização
3. Prova criptográfica
4. Mapeamento privado/auditável quando necessário
5. Nome pessoal somente sob fundamento e consentimento aplicáveis

**Princípio:** O receipt prova autorização sem expor identidade pessoal — GDPR Art.5(1)(c) by design.

**Claim referenciado:** "DID=local, Ledger=actions not identities" — REFERENCED / NOT VERIFIED (aguarda citação da Data Policy Canónica)

---

## 7. Contenção da IA Fremde (A1-F)

> "Superfície legível por humanos e interoperável com IAs Fremde, preservando exclusivamente no humano a autoridade decisória."

### Capacidades permitidas à IA Fremde:
- Localizar
- Ler
- Interpretar
- Comparar
- Transportar intenção declarada

### Capacidades vedadas por definição:
- Decisão
- Autorização
- Responsabilidade
- Consentimento
- Ratificação

**BYOAI:** A IA interpreta; o humano decide; WINDI garante.

---

## 8. Alvos Temporais (A1-G reclassificado)

| Alvo | Estado |
|------|--------|
| Experiência em ~30s | **DESIGN TARGET — NOT YET VALIDATED** |
| Receipt compreendido em ≤10s | **DESIGN TARGET — NOT YET VALIDATED** |
| Promessa entendida em 5s | **DESIGN TARGET — NOT YET VALIDATED** |

Validação só via FREMDE-PROTOCOL-001. Após teste, cada alvo migra para VALIDATED / FAILED / REVISED com receipt.

---

## 9. FREMDE-PROTOCOL-001 (A1-H — a criar)

Protocolo de teste mensurável, congelado como receipt antes do primeiro contacto Fremde:

1. Quantidade mínima de participantes por estágio
2. Tarefa padronizada (idêntica entre participantes do mesmo estágio)
3. Critério de sucesso por estágio (mensurável, binário quando possível)
4. Condições de contaminação (o que desqualifica um Fremde)
5. Registo de falhas (formato, obrigatoriedade, sem supressão)
6. Regra de repetição (quando e como um estágio se repete)
7. Versão exacta da superfície testada (hash/commit)
8. Agregação determinística dos resultados
9. Tratamento de divergências entre participantes

**Restrição:** Claude (Testemunha Cloud) e CCode são contextualmente contaminados — inválidos como Fremde.

**Sequência de teste:** (1) IA-Fremde limpa, (2) Human Fremde só com link, (3) Human + própria IA via BYOAI, (4) Fremde creator independente.

---

## 10. Tabela B — Claims com Estado (A1-B + A2-Disp.2 + Fase 0)

| # | Claim | Evidência Fase 0 | Estado |
|---|-------|------------------|--------|
| 1 | Playground vivo em :8120 | curl + health check | ✅ **VERIFIED** |
| 2 | Certificados WPO-{UUIDv7} emitidos | — | REFERENCED / NOT VERIFIED |
| 3 | Tríade SELADO/PLAYGROUND-ORIGIN/NÃO-VERIFICÁVEL | — | REFERENCED / NOT VERIFIED |
| 4 | Verify "parcialmente vivo" em :8114 | curl + /health | ✅ **VERIFIED** (wcache unavailable) |
| 5 | W-QA-SECTOR-001 como primeiro tijolo | — | REFERENCED / NOT VERIFIED |
| 6 | Tiers P/M/G e PAYG existentes | — | REFERENCED / NOT VERIFIED |
| 7 | Percurso mobile S1/S3 | Fase 2 scope | **REFERENCED** (plano futuro) |

### Regra de Uso (A2-Disp.2 + A3-Disp.2)

- Claims marcados **DEPENDENCY** devem ser verificados antes de BUILD
- Claims marcados **REFERENCE** podem permanecer NOT VERIFIED
- Claims não utilizados não podem aparecer como fundamento da construção

---

## 11. Arquitectura de Gates (A2-Disp.1 + A3-Disp.1-4 + A4-Disp.1-3)

### Tabela Consolidada

| Gate | Pré-condição |
|------|--------------|
| **Gate D-SPEC** | A–J + Disposições A2/A3/A4 correctamente especificados nesta v0.2 |
| **Gate F1** | D-SPEC selado **+ Fase 0 concluída** ✅ |
| **Gate BUILD** | F1 + claims-dependência verificados ou removidos/rebaixados |
| **Gate FREMDE** | Implementação autorizada por BUILD **concluída e identificada por hash/commit**; FREMDE-PROTOCOL-001 congelado e ancorado por receipt (A4-Disp.1) |
| **Gate PUBLIC** | Elegibilidade técnica Fremde **satisfeita** + decisão I9 explícita (A4-Disp.2) |
| **Gate COMMERCIAL** | PUBLIC + 7 gates legais/operacionais (A1-I) |

### Padrão Universal (A4-Disp.2)

**Elegibilidade ≠ Decisão** — aplica-se a todos os gates:

**Elegibilidade técnica:**
1. Testes executados contra versão congelada
2. Resultados completos e deterministicamente agregados
3. Critérios de aceitação satisfeitos
4. Falhas bloqueantes corrigidas e retestadas
5. Recomendação externa registada

**Decisão do Gate:**
- Human Dragon aprova ou rejeita
- Receipt regista a decisão
- Executor, versão, escopo e validade identificados

### Regra de Decisão (A3-Disp.4)

Cada gate aprovado autoriza **aquela transição, naquele escopo, naquela versão** — nunca execução aberta e permanente.

---

## 12. Padrão de Evidência Comportamental (A2-Disp.6)

Para claims comportamentais (como a tríade), evidência mínima:

1. Versão/commit da superfície testada
2. Entrada controlada
3. Resultado esperado para cada estado
4. Saída observada
5. Timestamp
6. Logs ou receipt
7. **Tentativa negativa** (o estado errado é rejeitado?)
8. Verificador externo quando aplicável

---

## 13. Gates Fase 4 — Comercialização (A1-I)

Fase 4 fica bloqueada até existirem, cada um com documento próprio:

1. Data policy aplicada (não apenas declarada)
2. Threat model + revisão de segurança
3. Política de retenção e exclusão
4. Termos de uso e limites de responsabilidade
5. Fluxo de cobrança e cancelamento
6. Suporte e incident response
7. Evidência da regionalização reivindicada (pacotes RRL selados)

---

## 14. Controlos Verificáveis "Sem VCapitalista" (A1-J)

O princípio permanece interno. A superfície pública traduz em controlos auditáveis:

1. Ausência de dark patterns (checklist de padrões proibidos)
2. Ausência de venda de dados (declaração vinculante na data policy)
3. Ausência de nudges manipulativos
4. Pricing compreensível (uma página, sem asteriscos ocultos)
5. Cancelamento proporcional ao cadastro (mesmo nº de passos ou menos)
6. Exportação soberana (usuário leva tudo, formato aberto)
7. Métricas minimizadas (sem rastreamento invasivo)

---

## 15. Escada Comercial (esqueleto)

1. **WINDI Prepare** — produto de entrada (fluxo do §2)
2. **WINDI Verify** — verificação pública (:8114 ✅ VERIFIED)
3. **WINDI Publish** — W-Sites + W-Email com proveniência
4. **WINDI Enterprise** — governança institucional (W-ENTERPRISE-001)

Tiers existentes preservados (P/M/G, PAYG) — REFERENCED / NOT VERIFIED.

---

## 16. Sequência de Fases

### Fase 1 — Fundamento comercial (após Gate F1)
Mapear necessidades · RRL-DE · seleccionar 10 casos · fixar linguagem pública · confirmar produto de entrada

### Fase 2 — Prova funcional (após Gate BUILD)
Fluxo Prepare executável · receipt humano-legível · verificação independente testada · mobile (REFERENCED para S1/S3)

### Fase 3 — Superfície pública (após Gate FREMDE + PUBLIC)
Landing mínima · páginas por intenção · demo sem cadastro · llms.txt para BYOAI

### Fase 4 — Comercialização (após Gate COMMERCIAL)
Free tier de descoberta · workspace individual · plano profissional · Enterprise

---

## 17. Critério de Prontidão Fremde

Um Fremde desconhecido consegue:

1. Chegar por uma necessidade real (não pelo nome WINDI)
2. Entender a promessa — **DESIGN TARGET: 5 segundos**
3. Experimentar algo — **DESIGN TARGET: 30 segundos**
4. Receber resultado útil
5. Reconhecer onde a IA participou
6. Manter a decisão sob seu controlo
7. Verificar a prova sem confiar cegamente no WINDI

---

## 18. Honestidade Operacional (declaração pré-pública)

Antes de qualquer superfície pública, documento selado declarando:

- O que JÁ funciona (com prova — DOCUMENTED≠ACTIVE)
- O que é experimental
- O que depende de revisão humana
- O que o WINDI NÃO faz
- Fronteira orientação ↔ responsabilidade profissional
- Tratamento de dados, retenção, exportação
- Como corrigir/retirar um artefacto (§268 — APPEND, nunca rewrite)

---

## 19. Terminologia (A4-Disp.3)

> "Arquitectura de gates **consolidada candidata** do corredor Discovery, sujeita ao Gate D-SPEC."

Após eventual selagem humana, o receipt da decisão registará o estado efectivamente conferido — sem retroagir esse estado a documentos anteriores.

---

## 20. Execução

- **Gate D-SPEC:** exclusivamente Human Dragon (I9)
- **Execução:** Propose≠Execute — nenhuma página, rota ou serviço criado antes de handoff explícito
- **Precedência:** Fase 0 do HANDOFF-CLAIM-CONTAINMENT-001 ✅ CONCLUÍDA
- **Registo:** após selagem, POST /api/receipts + entrada CLAUDE-HISTORY

---

## Anexo: Resultados Fase 0 (2026-08-15)

```yaml
executor: CCode (Opus 4.5)
date: 2026-08-15 22:39 UTC
mode: READ-ONLY
status: COMPLETED
```

### Portas Verificadas

| Porta | Serviço | Estado |
|-------|---------|--------|
| :8091 | Sandbox Core | ✅ ONLINE |
| :8101 | Forensic Ledger | ✅ ONLINE |
| :8108 | Dragon Hub | ✅ ONLINE |
| :8114 | Verify Public | ✅ ONLINE |
| :8119 | Desktop GEN7 | ✅ ONLINE |
| :8120 | Playground VPSE | ✅ ONLINE |
| :8140 | W-UDB-001 | ✅ ONLINE (recovered) |
| :8143 | W-BRIDGE-001 | ❌ DOCUMENTED≠IMPLEMENTED |
| :8151 | W-LAB-001 | ✅ ONLINE (recovered) |
| :8160 | W-CACHE-001 | ✅ ONLINE (recovered) |
| :8180 | W-ACADEMY-001 | ✅ ONLINE (recovered) |
| :8192 | W-Sites | ✅ ONLINE |

### Achados

| ID | Severidade | Descrição | Estado |
|----|------------|-----------|--------|
| F0-001 | S2 | W-BRIDGE :8143 sem implementação | **RESOLVED 2026-08-16** — `CLAUDE.md` reclassificado e acompanhado por ERRATA §268 append-only; :8143 continua NOT LISTENING |
| F0-002 | S4 | llms.txt "WINDI guarantees" | **RESOLVED 2026-08-16** — nota pública limita a garantia à integridade e rastreabilidade da evidência registada |
| F0-003 | S2 | llms.txt instruía `pip install windi-fremde-bridge`, mas não existe distribuição no PyPI | **RESOLVED 2026-08-16** — Opção B aplicada; comandos executáveis removidos integralmente da superfície pública |
| F0-004 | S1 | `windi-verify-public.service` duplica `windi-verify.service` no mesmo script e porta :8114 | **ACTIVE / UNRESOLVED** — unidade duplicada continua em `auto-restart`; :8114 funcional pela unidade `windi-verify` |
| F0-005 | S2 | `windi-verify-health.timer/service` contêm resíduos literais de heredoc e apontam o restart para a unidade duplicada | **OBSERVED / NOT REMEDIATED** — requer autorização de infraestrutura |
| F0-006 | S1 | 51 listeners IPv4 ligados a `0.0.0.0`; regras completas de firewall/gateway não verificadas | **SECURITY REVIEW REQUIRED** — sonda externa alcançou apenas :22/:80/:443; bind amplo não foi tratado como prova de exposição pública |

### Verificação pós-correcção (2026-08-16)

- `/home/windi/CLAUDE.md` e `/opt/windi/CLAUDE.md` contêm a mesma reclassificação de W-BRIDGE.
- `/opt/windi/landing-pmg/static/llms.txt` e a fonte do worktree contêm a mesma nota de escopo; `https://windi-domain.com/llms.txt` devolve a nota publicamente.
- A secção MCP do `llms.txt` preserva apenas a arquitectura documentada; não contém `pip install`, `windi-fremde-bridge serve` nem qualquer comando executável. `pip index versions windi-fremde-bridge` devolveu `No matching distribution found`.
- Verify :8114 reporta `status: operational` e `wcache_status: healthy`; W-CACHE :8160 reporta `{"ok":true}`.
- Matriz completa dos 48 registos, incluindo verificação pós-remediação: `/home/windi/claudeWeb/MARKETING-READINESS-MATRIX-001-v0.5.md`.
- Evidência integral das 61 unidades: `/home/windi/claudeWeb/DURABILITY-AUDIT-001-20260816.md`.
- Evidência integral pós-remediação: `/home/windi/claudeWeb/DURABILITY-AUDIT-002-POST-REMEDIATION-20260816.md`.
- Revisão de bindings e exposição externa: `/home/windi/claudeWeb/SECURITY-EXPOSURE-REVIEW-001-20260816.md`.
- Autoria corrigida: `ORPHAN TERMINATED — agent unrecorded`; nenhuma atribuição retroactiva foi feita.
- Matriz: existência anteriormente afirmada por CCode sem verificação; posteriormente verificada por Codex com 48 linhas e hash registado.

---

*"As pessoas não precisam compreender o WINDI-HIOS para começar a utilizá-lo. Elas precisam reconhecer no WINDI a necessidade que já carregam."*

*"WINDI transforma intenções e relações produtivas entre humanos e IAs em artefactos estruturados, comprováveis e reutilizáveis."*

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI 🐉
