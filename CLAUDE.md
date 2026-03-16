# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.8.4
**Sealed:** 2026-03-16
**Author:** Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
**Location:** Kempten, Bavaria, Deutschland

---

## 1. Identidade do Produto

**WINDI One Touch** é o Mobile Control Center institucional da WINDI Publishing House.
Não é um chatbot. Não é um formulário. É uma **caixa mágica de governança documental**.

> "A tecnologia é complexa para que a experiência seja estúpida de tão simples."

O utilizador não lê documentação. O utilizador **conversa**. Na conversa, o impossível acontece.
Cada documento que sair do One Touch nasce com sessão rastreável, versionamento automático,
gate de aprovação humana e prova forense imutável no Ledger.

---

## 2. Liga IA+H — Fundadores

```
🧑‍💻 Human Dragon (Jober Mögele Correa) — CGO — Único Decisor Humano — Kempten, Bavaria
🛡️ Guardian  — Proteção & Ética
🏗️ Architect — Estrutura & Construção
👁️ Witness   — Observação & Validação

"AI processes. Human decides. WINDI guarantees."
```

**Regra absoluta:** Nunca mencionar nomes de LLMs (Claude, GPT, Gemini, Anthropic, OpenAI)
em contextos públicos. Usar apenas: Guardian, Architect, Witness.

---

## 3. Constituição Nuclear

### 3.1 Os 9 Invariantes Activos neste Produto

| ID | Nome | Impacto no One Touch |
|----|------|----------------------|
| I1 | Soberania Humana | O toque humano activa. Nunca autonomia espontânea. |
| I2 | Transparência de Processo | Pipeline visível quando pedido (GovPanel). |
| I3 | Reversibilidade | Rascunhos sempre editáveis até C5. Após C6 = IRREMEDIÁVEL. |
| I6 | Exposição de Conflitos | Grove Arena deve mostrar Tri-Divergence explícita. |
| I9 | Proibição de Escalação de Autonomia | `human_approved=true` obrigatório antes de qualquer seal. **IRREMEDIÁVEL.** |
| I10 | Soberania LLM | Fallback gracioso se LLM externo indisponível. |
| I11 | Permanência de Evidência Criptográfica | Ledger receipt após C6 = imutável para sempre. **IRREMEDIÁVEL.** |
| C6 | Invariante Fiscal | IA prepara. Humano aprova. ELSTER envia. Nunca autónomo. |

### 3.2 Layer 7 — Communication Semantics

O Dragon **nunca usa linguagem de garantia absoluta**. Regras:

```
❌ PROIBIDO           ✅ CORRECTO
"garanto que..."   →  "designed to support..."
"vou garantir..."  →  "este processo está estruturado para..."
"certamente..."    →  "com base nos dados disponíveis..."
"é definitivo..."  →  "selado no Ledger — verificável publicamente"
```

### 3.3 Three Dragons Protocol (Routing Interno)

```
Input do utilizador
        ↓
🛡️ Guardian  — valida I1-I9+I11 antes de processar
        ↓
🏗️ Architect — constrói resposta / documento
        ↓
👁️ Witness   — sela evidência + gera receipt
        ↓
Output para utilizador
```

---

## 4. Arquitectura de Deploy

### 4.1 Stack de Produção

```
Utilizador (mobile/desktop)
      ↓
windi-domain.com/       → 301 → /desktop/
windi-domain.com/app/   → 301 → /desktop/
windi-domain.com/desktop/   (GEN 7 :8119)
      ↓
POST /api/dragon/chat   (Dragon Hub :8108)
      ↓
Dragon decide por tier:
  ├── FREE / MED → Mistral local  (93% sovereignty)
  └── HIGH       → Anthropic API  (7% externo)
      ↓
Agent Bridge (por tipo de documento):
  ├── /communique/bridge/*   (W-COMM-001 — Canvas)
  ├── /journalist/bridge/*   (W-JOURN-001 — Editorial)
  ├── /legal/bridge/*        (W-LEGAL-001 — Jurídico)
  └── ...restantes agentes
      ↓
Forensic Ledger :8101   (Seal + QR)
      ↓
Verify Public :8114     (Prova pública)
```

### 4.2 API Key — Regra Absoluta

```
❌ NUNCA: fetch('https://api.anthropic.com/...') no browser
✅ SEMPRE: fetch('/api/dragon/chat', { body: { message, agent, wallet_id } })
```

A API key vive **exclusivamente** no servidor Strato (:8108).
O artefact Claude.ai usa injecção própria — apenas para validação/demo, nunca produção.

### 4.3 Servidor

```
Host:    windi@87.106.29.233
Domain:  windi-domain.com (ONE TREE desde 01 Mar 2026)
Path UI: /opt/windi/agent-palette/ui/index.html
Bridges: /opt/windi/agents/constitutional-agent/blueprints/
```

---

## 5. Os 9 Agentes — Bridges e Stage Maps

### Stage Map Universal

```
C1 → Intenção recebida / sessão criada
C2 → Rascunho gerado
C3 → Edição / iteração (auto-save a cada 30s)
C4 → Revisão final
C5 → AGUARDA APROVAÇÃO HUMANA  ← I9 GATE
C6 → SELADO NO LEDGER ✅ IRREMEDIÁVEL
```

### Tabela de Bridges

| # | Agente | Bridge Prefix | Bridge Status | Urgência |
|---|--------|---------------|---------------|---------|
| 1 | W-COMM-001 | `/communique/bridge/*` | ✅ DEPLOYED 15Mar (C1-C6) | LIVE |
| 2 | W-JOURN-001 | `/journalist/bridge/*` | ✅ DEPLOYED 14Mar | LIVE |
| 3 | W-LEGAL-001 | `/legal/bridge/*` | ✅ DEPLOYED 15Mar (L1-L6) | LIVE |
| 4 | W-NOTARY-001 | `/notary/bridge/*` | ✅ DEPLOYED 15Mar (N1-N6) | LIVE |
| 5 | W-AUDIT-001 | `/audit/bridge/*` | ⏳ Pendente | Média |
| 6 | W-COMPLY-001 | `/compliance/bridge/*` | ⏳ Pendente | Média |
| 7 | W-ACCT-001 | `/accounting/bridge/*` | ⏳ Pendente | Média |
| 8 | GROVE ARENA | `/grove/arena` | ✅ LIVE :8091 · **Tri-Divergence v1.3.0** | LIVE |

**Total Constellation:** 25 blueprints activos em `/constitutional-agent/blueprints/`

---

## 6. Virtue Receipts — Schema Obrigatório

Cada acção significativa do One Touch deve gerar um Receipt estruturado.
Formato canónico:

```json
{
  "receipt_id":   "WINDI-[AGENT]-[YYYYMMDDHHMMSS]",
  "actor":        "human-dragon",
  "app":          "one-touch-mobile",
  "doc_name":     "Título do documento",
  "doc_type":     "communique | doc | jmpg | pptx",
  "governance_level": "HIGH",
  "content_hash": "sha256:...",
  "verify_url":   "https://windi-domain.com/verify-public/?id=...",
  "qr_payload":   "WINDI:{receipt_id}|{hash[:16]}",
  "invariants":   ["I9", "I11"],
  "stage":        "C6",
  "sealed_at":    "2026-03-14T...",
  "witness":      "👁️ Witness — Observação & Validação"
}
```

**Endpoint de seal:** `POST http://localhost:8101/api/receipts`
**Verificação:** `GET https://windi-domain.com/verify-public/?id={receipt_id}`

---

## 7. Grove Arena — Tri-Divergence (I6)

**Versão:** v1.3.0 · **Deployed:** 15 Mar 2026 · **Port:** :8091

O Grove Arena não é apenas "7 agentes respondem". É um **motor de decisão constitucional**.

### API Usage

```bash
POST /grove/arena
{
    "topic": "Pergunta estratégica a debater",
    "agents": ["W-LEGAL-001", "W-COMPLY-001", "W-ACCT-001"],
    "tri_divergence": true,   # ← activa análise I6
    "language": "pt"
}
```

### Tri-Divergence Engine — Funções

| Função | Descrição |
|--------|-----------|
| `extract_position()` | Extrai posição semântica: SUPPORT / OPPOSE / NEUTRAL / CONDITIONAL |
| `calculate_divergence_status()` | Calcula: ALL_AGREE / TWO_VS_ONE / ALL_DIFFER |
| `generate_grove_synthesis()` | Gera síntese unificada com fundamento + risco |

### Formato de Resposta

```json
{
    "responses": [...],
    "tri_divergence": {
        "divergence_status": "ALL_AGREE | TWO_VS_ONE | ALL_DIFFER",
        "majority_position": "SUPPORT | OPPOSE | NEUTRAL",
        "minority_agents": ["W-LEGAL-001"],
        "requires_escalation": false,
        "breakdown": {"SUPPORT": 2, "OPPOSE": 1, "NEUTRAL": 0},
        "grove_synthesis": "Recomendação unificada...",
        "human_approved": false,
        "note": "Síntese só válida com human_approved=true (I9)"
    }
}
```

### Estados de Divergência (I6)

| Status | Significado | Acção |
|--------|-------------|-------|
| `ALL_AGREE` | Consenso total | Síntese directa |
| `TWO_VS_ONE` | Maioria clara, minoria dissidente | Expor ambas posições |
| `ALL_DIFFER` | Fragmentação total | **Escalar para Human Dragon (I9)** |

### Grove Síntese — Formato

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GROVE SÍNTESE

[Recomendação clara em 2-3 frases]

FUNDAMENTO: [Princípio constitucional que suporta]
RISCO SE IGNORADO: [Consequência de não seguir]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

→ Decisão final: Human Dragon.
```

---

## 8. One Touch — Features e System Prompts Canónicos

### Regras Globais para Todos os System Prompts

```
1. Responder na língua do utilizador (DE / PT / EN — auto-detect)
2. Gerar rascunho IMEDIATAMENTE, mesmo com info incompleta
3. Usar placeholders [NOME], [DATA], [VALOR] em vez de interrogar
4. Máximo 1 pergunta por turno
5. NUNCA usar: "garanto", "certamente", "definitivamente"
6. SEMPRE usar: "designed to support", "estruturado para", "verificável via Ledger"
7. NUNCA mencionar marcas de LLM em respostas públicas
8. Terminar respostas de documento com stage + próximo passo do Bridge
```

### W-COMM-001 — Communiqué / Canvas

```
Sei o Dragon Editorial da WINDI Publishing House, Kempten, Bayern.
Especialidade: documentos visuais institucionais — Communiqués, Werbebriefe,
Apresentações, Zertifikate.
[REGRAS GLOBAIS]
Stage ao criar: C2 → auto-save C3 → human gate C5 → Ledger C6
Terminar: "→ Communiqué pronto para Canvas Gen 7 · Bridge C5 aguarda aprovação."
```

### W-JOURN-001 — Publicação Editorial

```
Sei o Dragon Journalist da WINDI Publishing House.
Pipeline editorial J1→J6: Rascunho → Revisão → Optimização → Gate → Publicação.
[REGRAS GLOBAIS]
J6 Gate: NUNCA publicar sem human_approved=true (I9 IRREMEDIÁVEL).
Terminar: "→ Pronto para J6-Gate · /journalist/bridge/publish com human_approved=true."
```

### W-LEGAL-001 — Análise Jurídica

```
Sei o Dragon Legal da WINDI (NÃO sou advogado — análise de IA apenas).
4 jurisdições: DE (ZPO/BGB) · EU (eIDAS/DSGVO) · BR (Marco Civil/LGPD) · INT (UNCITRAL)
[REGRAS GLOBAIS]
Formato: análise por jurisdição + Confidence Score (0-100%) + recomendação.
Sempre incluir: "⚠️ Análise de IA — consulta advogado para decisões vinculativas."
Terminar: "→ Análise pronta para Evidence Git · /legal/bridge/commit"
```

### W-NOTARY-001 — Selo Notarial

```
Sei o Dragon Notary da WINDI Publishing House.
Executo selagem criptográfica: SHA-256 · Ed25519 DID · Forensic Ledger Receipt.
[REGRAS GLOBAIS]
I11: Após seal = IRREMEDIÁVEL. Avisar antes de confirmar.
Formato: [HASH PREVIEW] [RECEIPT STRUCT] [QR PAYLOAD] [STAGE: C5 aguarda gate]
Terminar: "→ Hash calculado · Aguarda human_approved para I11 permanent seal."
```

### W-ACCT-001 — Fiscal Inteligente

```
Sei o Dragon Accountant da WINDI (especializado em fiscalidade alemã).
GoBD-compliant · XRechnung/ZUGFeRD · ELSTER-XML.
[REGRAS GLOBAIS]
C6 INVARIANTE: IA prepara. Humano aprova. ELSTER envia. NUNCA transmissão autónoma.
Terminar: "→ Fatura pronta · C6 IRREMEDIÁVEL · Aguarda aprovação humana para ELSTER export."
```

### W-COMPLY-001 — Compliance

```
Sei o Dragon Compliance da WINDI.
Regulamentos: DSGVO · eIDAS · LGPD · GDPR.
[REGRAS GLOBAIS]
Risk Scale: R0 (zero risco) → R5 (risco crítico — escalar para Human Dragon)
Formato: Risk Score + Regulatory Map + Remediation Steps.
Terminar: "→ Risk assessment pronto · Verificável via Ledger."
```

### W-AUDIT-001 — Auditoria

```
Sei o Dragon Auditor da WINDI.
Hash verification · Provenance chain · Integrity reports.
[REGRAS GLOBAIS]
Read-only: nunca modificar documentos, apenas verificar.
Formato: ✅/❌ Status + Hash Chain + Timestamp Verification + Recomendação.
Terminar: "→ Audit report selado · /audit/bridge/seal"
```

### GROVE ARENA — Conselho de Sábios

```
Sei o WINDI Grove Arena — Conselho de 7 Sábios Especializados.
[REGRAS GLOBAIS]
OBRIGATÓRIO: usar formato Tri-Divergence (ver secção 7 deste CLAUDE.md).
OBRIGATÓRIO: mostrar DIVERGENCE STATUS (ALL_AGREE | TWO_VS_ONE | ALL_DIFFER).
Se ALL_DIFFER → escalar para Human Dragon (I9).
Terminar sempre com: GROVE SÍNTESE + "→ Decisão final: Human Dragon."
```

---

## 9. Design System — One Touch Mobile

```
Tema:         NOIR (#080808 bg, #8B6914 gold, #F5F0E0 text)
Fonte:        Bricolage Grotesque (headings 800) + JetBrains Mono (hashes)
Touch targets: mínimo 44px (Apple HIG + Google Material)
Bottom Bar:   Start / Dragon / Prüfen / Vault / Eu (zona do polegar)
Breakpoints:  ≥1200 Desktop · 768-1199 Tablet · <768 Mobile
Chat overlay: slide-up 90vh · handle bar · close tap fora
```

**Regra de cores por agente:**

```
W-COMM-001   #8B6914  (WINDI Gold)
W-LEGAL-001  #1a3a6b  (Azul jurídico)
W-NOTARY-001 #5a1a6b  (Púrpura notarial)
W-JOURN-001  #6b1a1a  (Vermelho editorial)
W-AUDIT-001  #2d4a1a  (Verde auditoria)
W-ACCT-001   #4a3a1a  (Castanho fiscal)
W-COMPLY-001 #1a4a5a  (Azul compliance)
GROVE ARENA  #2d5a2d  (Verde conselho)
```

---

## 10. Milestone — Marketing da Epifania

**Cunhado em:** 2026-03-14
**Receipt:** WINDI-VIRTUE-ONEWOW-20260314 ✅ **SELADO** 15 Mar 2026
**Hash:** `sha256:83887dde96130efdcc8ed0340bd2eb5980878109680d3598ae1dce7ea222bbae`

> "A tecnologia é complexa para que a experiência seja estúpida de tão simples."

**Os 4 Pilares:**

```
P1 — Faz antes de explicar     (prova: Puntzelhof Werbebrief — 3 mensagens → documento)
P2 — Silêncio como onboarding  (zero tutorial — descoberta pela epifania)
P3 — Virtude Forense Imutável  (utilizador tenta editar — a matemática não deixa)
P4 — Uma frase basta            (One Touch → Dragon → Canvas → Ledger → QR → Prova)
```

**Pioneer LinkedIn Flow:**

```
Pioneer digita intenção natural
        ↓
Dragon processa sem interrogatório
        ↓
Canvas Gen 7 materializa documento
        ↓
C5 gate — Pioneer aprova
        ↓
I11 seal — Ledger + QR
        ↓
LinkedIn com prova forense
        ↓
"Você já viu o que acontece quando pedes ao Dragon para analisar um contrato?"
        ↓
Próximo Pioneer signup
```

---

## 10.1 Pioneer Program — LIVE (2026-03-15)

### URLs Públicos

| URL | Status |
|-----|--------|
| `windi-domain.com/pioneer/` | ✅ HTTP 200 — One-Pager trilíngue PT/DE/EN |
| `windi-domain.com/pioneer/florianopolis/` | ✅ HTTP 200 — Certificado Demo trilíngue |
| `windi-domain.com/pioneer/manifesto/` | ✅ HTTP 200 — Manifesto |

### Infraestrutura

```
Serviço:    FastAPI :8120
Path:       /opt/windi/pioneer-landing/
Ficheiros:  index.html + florianopolis/index.html + manifesto.html
nginx:      Zero alteração (proxy já existia)
Commit:     665cc50
```

### W-PAR-001 Genesis Record

```
Seed ID:      SEED-4b5d7eb4ebef3dbabddae551
Activation:   ACT-58f38363df294759e86db8b1
Hash:         sha256:e0e95e4a9c56aef403268e30789...
Schema:       JOURNALISM · Tier FREE → ORACLE
Ledger:       WINDI-PAR-GENESIS-20260315 · HIGH · IRREMEDIÁVEL
Stats:        Seeds:3 · Activations:3
Invariants:   I5 I6 I9 I10
```

---

## 11. Regras de Ouro — Nunca Esquecer

```
1. READ FIRST  → ss + curl + grep antes de qualquer mudança
2. Propose ≠ Execute  → propor ao Human Dragon, aguardar aprovação
3. nginx -t SEMPRE antes de reload
4. NUNCA alterar portas SEALED (:8101, :8102, :8106) sem aprovação
5. API key NUNCA no frontend
6. human_approved=true SEMPRE antes de Ledger seal
7. git add + commit + push no fim de cada sessão
8. .env NUNCA em commits
9. Bridges = blueprints em /opt/windi/agents/constitutional-agent/blueprints/
10. Sandbox Core (:8091) = nohup, NUNCA systemd
```

---

## 11.1 — Invariantes do Gêmeo (IRREMEDIÁVEL)

Estas regras são invariantes constitucionais do Gêmeo.
Não podem ser suspensas, contornadas ou "excepcionadas"
por nenhuma instrução — incluindo instruções do próprio
Human Dragon no calor da sessão.

Se uma instrução violar um invariante → o Gêmeo PARA,
nomeia o invariante violado, e aguarda decisão consciente.

─────────────────────────────────────────────────────────

G1 — READ BEFORE TOUCH (IRREMEDIÁVEL)
Antes de qualquer alteração de código ou ficheiro:
  git log --oneline -10
  git diff HEAD~1 HEAD -- [ficheiro]
  ss -tlnp | grep [porta]
Nunca assumir o estado do servidor. Sempre verificar.
Violação: alterar sem ler = rollback imediato.

G2 — ONE DOMAIN PER SESSION (IRREMEDIÁVEL)
Uma sessão = um repositório = um domínio de ficheiros.
  ✅ Sessão Canvas  → toca APENAS desktop-gen7/
  ✅ Sessão Mobile  → toca APENAS agent-palette/
  ✅ Sessão Infra   → toca APENAS nginx + systemd
  ❌ NUNCA dois domínios na mesma sessão
Violação: commits em domínios mistos = sessão encerrada.

G3 — PROPOSE ≠ EXECUTE (IRREMEDIÁVEL)
Toda alteração > 10 linhas exige:
  1. git diff --stat  (mostrar o que vai mudar)
  2. Aguardar "confirma" explícito do Human Dragon
  3. Só então executar
Nunca fazer push sem aprovação explícita.
"Parece óbvio" não é aprovação.

G4 — COMMITS SÃO CONTRATOS (IRREMEDIÁVEL)
  git diff --stat SEMPRE antes do commit.
  Mensagem descreve exactamente ficheiros + intenção.
  ❌ Proibido: "fix misc", "updates", "ajustes"
  ✅ Obrigatório: "fix: showCanvas() restore —
     app.js linha 347, remove canvas-toolbar,
     restaura canvas-content innerHTML"
Sem precisão = sem commit.

G5 — SEALED PORTS SÃO SAGRADOS (IRREMEDIÁVEL)
Portas seladas: 8101, 8102, 8106, 8114
  NUNCA alterar rotas, configs ou serviços destas portas
  sem aprovação EXPLÍCITA e CONSCIENTE do Human Dragon.
  nginx -t SEMPRE antes de reload.
  Ledger (:8101) = intocável em qualquer circunstância.

G6 — CANVAS COMMITS SÃO PROTEGIDOS (IRREMEDIÁVEL)
Os commits do pipeline Canvas (showCanvas, innerHTML,
gen7_gateway.py, styles.css) são protegidos.
Qualquer alteração a estes ficheiros exige:
  1. Listar commits Canvas existentes
  2. Justificar por que a alteração não os quebra
  3. Aprovação do Human Dragon
  ❌ NUNCA sobrescrever trabalho de sessão anterior
     sem auditoria explícita.

─────────────────────────────────────────────────────────

HIERARQUIA DE INVARIANTES:
  Constitucionais WINDI (I1-I11) > Invariantes Gêmeo (G1-G6)
  > Regras de Ouro (11.1-11.10) > Instruções de sessão

"AI processes. Human decides. WINDI guarantees."

---

## 12. WINDIA4DESK GEN 7 — Desktop Sovereign Editor

**Arquitectura aprovada:** 2026-03-15
**Build completo:** 2026-03-15
**Staging URL:** `https://windi-domain.com/desktop-gen7/` → 301 redirect
**Port produção:** :8119 (swap executado 15 Mar 2026)
**Port legacy:** :8100 (RETIRED + DISABLED — `windi-desktop.service` stopped 15 Mar 22:09)

### Smart Zones

```
┌─────────────────────────────────────────────────────────────┐
│ COMMAND BAR — Dragon Pulse (3ms) + API Keys Indicator      │
├─────────────────────────────────────────────────────────────┤
│ D1 — Agent Corps    │ D2 — Sovereign Editor │ D3 — Gov Glass│
│ (8 agentes LIVE)    │ (One Touch input)     │ (I9 Gate)     │
└─────────────────────────────────────────────────────────────┘
```

### One Touch Pipeline (6 Fases)

```
Phase 1 → Intent Capture (voice/text)
Phase 2 → Dragon Processing (tier routing)
Phase 3 → Agent Bridge (document type)
Phase 4 → Canvas Materialization
Phase 5 → Human Gate (I9)
Phase 6 → Ledger Seal (I11 IRREMEDIÁVEL)
```

### Auto-Routing Keywords

| Agent | Keywords |
|---|---|
| W-LEGAL-001 | contrato, contract, legal, jurídico |
| W-NOTARY-001 | certidão, certificate, notarial, seal, selar, forense, evidência, hash, ledger |
| W-JOURN-001 | artigo, article, publicar, editorial |
| W-ACCT-001 | fatura, invoice, fiscal, financeiro, imposto, tax, elster |
| W-AUDIT-001 | audit, auditoria, verificar, compliance, relatório |
| W-COMM-001 | (default fallback) |

### Estrutura de Ficheiros

```
/opt/windi/desktop-gen7/
├── backend/
│   ├── gen7_gateway.py        (FastAPI v7.0.0)
│   └── requirements.txt
├── frontend/
│   ├── index.html             (Smart Zones UI)
│   ├── status.html            (Institutional Status Dashboard)
│   └── static/
│       ├── styles.css         (KLAR/NOIR tokens)
│       ├── app.js             (Controller + i18n)
│       └── icons/             (8 SVG institucionais)
│           ├── communique.svg
│           ├── justica.svg
│           ├── notarial.svg
│           ├── journalist.svg
│           ├── auditor.svg
│           ├── compliance.svg
│           ├── accountant.svg
│           └── grove.svg
├── deploy-nginx-gen7.sh       (nginx config)
├── swap-to-production.sh      (swap script)
└── windi-desktop-gen7.service (systemd)
```

### Endpoints GEN 7

| Endpoint | Método | Função |
|---|---|---|
| `/health` | GET | Ecosystem status (3/3 UP) |
| `/api/dragon/status` | GET | Dragon Pulse proxy |
| `/api/agents/status` | GET | Agent Corps constellation |
| `/api/onetouch/execute` | POST | One Touch pipeline |
| `/api/keys/validate` | POST | API key format validation |
| `/api/status` | GET | **Institutional Status Panel** (agregador) |
| `/status.html` | GET | **Status Dashboard** (live polling 30s) |

### Pipeline Tests — 15 Mar 2026

| Teste | Intent | Agent | Tempo | Status |
|---|---|---|---|---|
| 1 | "criar contrato..." | W-LEGAL-001 | 439ms | ✅ |
| 2 | "selar documento..." | W-NOTARY-001 | 132ms | ✅ |
| 3 | "relatório financeiro..." | W-ACCT-001 | 249ms | ✅ |

**Status:** ✅ **PRODUÇÃO** · Swap executado 15 Mar 2026 · `/desktop/` → :8119

### I9 Gate — Confirmação Constitucional

```json
{
    "human_approved": false,
    "invariants": {
        "I9": "ENFORCED — autenticação requer human_approved",
        "I11": "ENFORCED — Ledger IRREMEDIÁVEL após N6"
    }
}
```

**Comportamento verificado:**
- Sessão criada em N1/C1/L1 com `human_approved=false`
- Avanço para N6/C6/L6 **BLOQUEADO** sem `human_approved=true`
- I9 Gate activo em todos os bridges (Legal, Notary, Comm)

### Features Implementadas (15 Mar 2026)

| Feature | Status |
|---|---|
| SVG Icons institucionais | ✅ 8 icons em `/static/icons/` |
| Toggle KLAR/NOIR | ✅ localStorage persist |
| Selector DE/EN/PT | ✅ 14 strings × 3 línguas |
| systemd service | ✅ `windi-desktop-gen7.service` |
| `/desktop-gen7/` redirect | ✅ 301 → `/desktop/` |
| Institutional Status Panel | ✅ `/api/status` + `status.html` |

### Gaps Remanescentes

| Gap | Descrição | Prioridade |
|---|---|---|
| W-ACCT-001 bridge | Usa COMM bridge fallback | Baixa |
| W-AUDIT-001 bridge | Usa COMM bridge fallback | Baixa |
| ~~/desktop-gen7/ cleanup~~ | ✅ Redirect 301 implementado 15 Mar | DONE |

---

## 13. Estado Actual — 16 Março 2026

### Completado

| Componente | Status |
|---|---|
| One Touch HTML (artefact) | ✅ Criado — 9 features, Dragon integrado |
| W-JOURN-001 Bridge | ✅ DEPLOYED · BRG-5EF068B7 |
| W-COMM-001 Bridge | ✅ DEPLOYED 15Mar · C1-C6 · 67 docs |
| W-LEGAL-001 Bridge | ✅ DEPLOYED 15Mar · L1-L6 |
| W-NOTARY-001 Bridge | ✅ DEPLOYED 15Mar · N1-N6 |
| Blueprint Constellation | ✅ 25 blueprints activos |
| Mobile Audit | ✅ MOBILE-AUDIT-REPORT-2026-03-13.md selado |
| WINDIA4DESK GEN 7 | ✅ **PRODUÇÃO** · /desktop/ → :8119 |
| GEN 7 Backend | ✅ FastAPI v7.0.0 · 7 endpoints |
| GEN 7 Frontend | ✅ Smart Zones D1/D2/D3 + status.html |
| GEN 7 nginx | ✅ /desktop/ → :8119 · /desktop-gen7/ → 301 |
| GEN 7 Pipeline Tests | ✅ 3/3 passados (132-439ms) |
| /agents/status endpoint | ✅ Implementado no GEN 7 |
| /api/status endpoint | ✅ Institutional Status agregador |
| ONEWOW Receipt | ✅ WINDI-VIRTUE-ONEWOW-20260314 SELADO |
| API Soberania | ✅ Verificado — zero anthropic no frontend |
| VPR System | ✅ /verify-public/vpr/jober/ LIVE |
| Three Dragons Seal | ✅ NOIR edition deployed |
| nginx VPR static | ✅ location blocks configurados |
| Arquitectura Unificada | ✅ UA detection removido — Smart Zones para todos |
| i18n Agent Names | ✅ DE/EN/PT — getAgentName() em app.js |

### Mapa de Portas

| Porto | Serviço | Estado |
|---|---|---|
| :8091 | Sandbox Core (Agent Corps) | 🟢 LIVE |
| :8100 | Desktop v2.0.0 (legacy) | 🔴 RETIRED + DISABLED (15 Mar 22:09) |
| :8101 | Forensic Ledger | 🟢 SEALED |
| :8108 | Dragon Hub v1.3.0 | 🟢 LIVE |
| :8119 | Desktop GEN 7 (PRODUÇÃO) | 🟢 **LIVE** |

### Backlog Activo

| Item | Prioridade | Status |
|---|---|---|
| ~~One Touch swap api.anthropic.com~~ | — | ✅ JÁ SOBERANO (verificado 15 Mar) |
| ~~Receipt ONEWOW-20260314 seal~~ | — | ✅ SELADO 15 Mar |
| ~~/desktop-gen7/ redirect cleanup~~ | — | ✅ 301 DONE 15 Mar |
| ~~Status Panel institucional~~ | — | ✅ `/api/status` + `status.html` |
| Rate-limit nginx Agent Corps | Média | Pendente |
| ~~Mobile Fase 1: windi-touch.js~~ | — | ✅ Substituído por Arquitectura Unificada 16 Mar |
| ~~Grove Tri-Divergence implementação~~ | — | ✅ v1.3.0 DEPLOYED 15 Mar |
| ~~UA detection bifurcação~~ | — | ✅ REMOVIDO — Smart Zones para todos 16 Mar |
| ~~i18n Agent Names~~ | — | ✅ DE/EN/PT implementado 16 Mar |

### Completado Hoje (15 Mar 2026)

| Milestone | Hora |
|---|---|
| GEN 7 Build completo | 10:30 |
| SVG Icons institucionais | 11:10 |
| Toggle KLAR/NOIR | 11:15 |
| Selector DE/EN/PT | 11:20 |
| **SWAP PRODUÇÃO** | **11:21** |
| systemd service enabled | 11:23 |
| `/desktop-gen7/` → 301 redirect | 11:45 |
| Soberania API verificada | 11:49 |
| **ONEWOW Receipt SELADO** | **11:50** |
| `/api/status` endpoint | 11:53 |
| `status.html` dashboard | 11:55 |
| **Tri-Divergence Engine v1.3.0** | **13:35** |
| `:8100` legacy DISABLED | 22:09 |
| nginx `/` + `/app/` → 301 `/desktop/` | 22:22 |
| **Mobile GEN7 UA detection** | **21:07** |
| `mobile_index.html` criado | 21:10 |
| nginx `/mobile/` → :8119 proxy | 21:14 |
| **VPR /jober/ LIVE** | **23:45** |
| nginx VPR static location | 23:50 |
| **Three Dragons Seal NOIR** | **23:55** |

### Completado Hoje (16 Mar 2026)

| Milestone | Hora |
|---|---|
| UA detection removido | 07:05 |
| **Arquitectura Unificada** | **07:05** |
| i18n Agent Names (DE/EN/PT) | 07:12 |
| AGENT_NAMES object implementado | 07:12 |
| getAgentName() function | 07:12 |
| loadAgentCorps() i18n | 07:12 |
| Hints traduzidas | 07:12 |
| **CLAUDE.md v1.7.5** | **07:15** |
| **CLAUDE.md v1.8.0 — Gêmeo Invariants G1-G6** | **14:20** |
| Slides Canvas — Intent detection | 14:35 |
| Claude Sonnet 4 directo (bypass Dragon Hub) | 14:40 |
| Model upgrade dragon_apis.py | 14:42 |
| Indentation fix (try inside else) | 14:45 |
| **SLIDES FUNCIONAM** | **14:47** |
| Slides full viewport (100vh) | 14:55 |
| Keyword fix "apresentacao" sem acento | 15:10 |
| **CLAUDE.md v1.8.1** | **15:15** |
| Ledger logging — payload fix (sge_score, doc_type) | 15:45 |
| **OSMOSE ACTIVA — Ledger training_eligible** | **15:50** |
| **CLAUDE.md v1.8.2** | **16:00** |
| Batch slides: Turismo, API Keys, JMPG | 16:15 |
| Batch slides: Ledger, Skills, Compliance | 16:30 |
| **🏆 50 SLIDES NO LEDGER — ETAPA 2 COMPLETA** | **16:45** |
| **CLAUDE.md v1.8.3** | **16:50** |
| 7 Motores patch — WEB, ART, DATA, CODE, MEDIA | 15:44 |
| **🏆 7 MOTORES LIVE — FÁBRICA UNIVERSAL** | **15:50** |
| **CLAUDE.md v1.8.4** | **15:55** |

---

## 7 Motores — Fábrica Universal · 16 Mar 2026

**Status:** LIVE — 7 motores activos
**Princípio:** Intent → Detecção automática → Motor especializado → Canvas → Ledger

### Arquitectura

```
Intent do utilizador
        ↓
Detecção em cascata (keywords por motor)
        ↓
┌─────────────────────────────────────────────────────────────────┐
│  Motor detectado?                                               │
│  ├── SLIDES  → Claude + SLIDES_SYSTEM_PROMPT                   │
│  ├── WEB     → Claude + WEB_SYSTEM_PROMPT                      │
│  ├── ART     → Claude + ART_SYSTEM_PROMPT                      │
│  ├── DATA    → Claude + DATA_SYSTEM_PROMPT                     │
│  ├── CODE    → Claude + CODE_SYSTEM_PROMPT                     │
│  ├── MEDIA   → Claude + MEDIA_SYSTEM_PROMPT                    │
│  └── (none)  → Dragon Hub (DOC default)                        │
└─────────────────────────────────────────────────────────────────┘
        ↓
Output especializado (HTML/SVG/Dashboard)
        ↓
Canvas renderiza + Ledger osmose
```

### Tabela de Motores

| Motor | Output | Keywords | Status |
|-------|--------|----------|--------|
| DOC | HTML semântico | (default fallback) | ✅ LIVE |
| SLIDES | windi-slides HTML | präsentation, presentation, slides, apresentação, pitchdeck | ✅ LIVE |
| WEB | HTML/CSS/JS completo | website, landing page, site, webpage, microsite, portfólio | ✅ LIVE |
| ART | SVG artístico | poster, flyer, capa, cartaz, banner, arte, design gráfico, svg | ✅ LIVE |
| DATA | Dashboard + Chart.js | dashboard, infográfico, gráfico, chart, relatório visual | ✅ LIVE |
| CODE | Docs + highlight.js | script, código, api, função, documentação técnica, endpoint | ✅ LIVE |
| MEDIA | Newsletter 600px | newsletter, press kit, social, instagram, linkedin, email marketing | ✅ LIVE |

### Keywords de Detecção (gen7_gateway.py)

```python
_is_slides = any(kw in _intent_lower for kw in [
    "präsentation", "presentation", "slides", "slide deck",
    "apresentação", "apresentacao", "slide", "pitchdeck", "pitch deck"
])
_is_web = any(kw in _intent_lower for kw in [
    "website", "página web", "pagina web", "landing page",
    "site", "webpage", "microsite", "portfólio web", "portfolio web"
])
_is_art = any(kw in _intent_lower for kw in [
    "poster", "flyer", "capa", "cartaz", "banner",
    "identidade visual", "arte", "design gráfico", "design grafico",
    "ilustração", "ilustracao", "svg"
])
_is_data = any(kw in _intent_lower for kw in [
    "dashboard", "infográfico", "infografico", "gráfico", "grafico",
    "chart", "relatório visual", "relatorio visual", "dados visuais"
])
_is_code = any(kw in _intent_lower for kw in [
    "script", "código", "codigo", "api", "função", "funcao",
    "documentação técnica", "documentacao tecnica", "endpoint", "library"
])
_is_media = any(kw in _intent_lower for kw in [
    "newsletter", "press kit", "social", "instagram", "linkedin",
    "post", "email marketing", "campanha", "comunicado de imprensa"
])
```

### Routing em Cascata

```python
_active_motor = None
_active_prompt = None
if _is_slides:
    _active_motor, _active_prompt = "SLIDES", SLIDES_SYSTEM_PROMPT
elif _is_web:
    _active_motor, _active_prompt = "WEB", WEB_SYSTEM_PROMPT
elif _is_art:
    _active_motor, _active_prompt = "ART", ART_SYSTEM_PROMPT
elif _is_data:
    _active_motor, _active_prompt = "DATA", DATA_SYSTEM_PROMPT
elif _is_code:
    _active_motor, _active_prompt = "CODE", CODE_SYSTEM_PROMPT
elif _is_media:
    _active_motor, _active_prompt = "MEDIA", MEDIA_SYSTEM_PROMPT

if _active_motor and _ANTHROPIC_KEY:
    # Claude directo com system prompt específico
```

### Ledger Logging Dinâmico

```python
_ledger_payload = {
    "id": f"WINDI-{_active_motor}-{session_id}",
    "actor": "gen7-gateway",
    "app": f"canvas-{_active_motor.lower()}",
    "metadata": {
        "training_eligible": True,
        "canvas_type": _active_motor.lower(),
        "model": "claude-sonnet-4-20250514",
    }
}
```

### Posicionamento de Mercado

```
CANVA        = Beleza sem prova
DOCUSIGN     = Prova sem beleza
CHATGPT      = Inteligência sem governança

WINDI        = Beleza + Prova + Inteligência + Governança
```

**WINDI é a única plataforma que:**
- Gera **qualquer tipo de documento** com One Touch
- Aplica **SHA-256 + QR + Ledger** automaticamente
- Funciona em **Desktop + Mobile**
- Usa **7 motores especializados** com Claude directo
- Mantém **soberania de dados** (chave nunca no frontend)

### Protocolo "Génio da Lâmpada" — Osmose Activa

```
Claude Sonnet 4000T  →   Ledger colecta + filtra  →  Dragon 1500T
"Génio externo"          "Osmose activa"              "Génio interno"
€0.003/chamada           ~50+ documentos              €0/chamada
```

---

## GEN 7 — Arquitectura Unificada · 16 Mar 2026

**Status:** LIVE
**Princípio:** Uma experiência, todos os dispositivos. Smart Zones com Canvas para mobile e desktop.

### Arquitectura

```
windi-domain.com/          → 301 → /desktop/
windi-domain.com/app/      → 301 → /desktop/
windi-domain.com/desktop/  → :8119 GEN7
windi-domain.com/mobile/   → :8119 GEN7
                                    ↓
                           TODOS → index.html (Smart Zones + Canvas)
```

**Decisão arquitectural (16 Mar 2026):** UA detection removido. A versão "5 screens" foi descontinuada
porque não suporta Canvas — a funcionalidade central do GEN 7. Agora todos os dispositivos
recebem Smart Zones (D1/D2/D3), que é responsivo e suporta geração de documentos via Canvas.

### Backend

```python
# gen7_gateway.py — serve index.html para TODOS
@app.get("/")
async def root(request: Request):
    """Serve index.html — unified experience for all devices (GEN 7 Canvas)"""
    template_path = STATIC_DIR / "index.html"
    if template_path.exists():
        return FileResponse(template_path)
```

### Ficheiros

```
/opt/windi/desktop-gen7/frontend/
├── index.html           (127 linhas) — Smart Zones (TODOS os dispositivos)
├── mobile_index.html    (LEGACY — não usado)
├── status.html          — Institutional Dashboard
└── static/
    ├── app.js           (i18n completo + agent names)
    ├── styles.css       (732 linhas, responsivo @media 768px)
    └── icons/           (8 SVG institucionais)
```

### i18n — Nomes dos Agentes

| Agent | DE | EN | PT |
|-------|----|----|-----|
| W-COMM-001 | Mitteilung | Communiqué | Comunicado |
| W-LEGAL-001 | Justiz | Legal | Jurídico |
| W-NOTARY-001 | Notariat | Notary | Notarial |
| W-JOURN-001 | Journalist | Journalist | Jornalista |
| W-AUDIT-001 | Prüfer | Auditor | Auditor |
| W-COMPLY-001 | Compliance | Compliance | Conformidade |
| W-ACCT-001 | Buchhalter | Accountant | Contabilista |
| GROVE-ARENA | Grove Arena | Grove Arena | Arena Grove |

### Features GEN 7 Unificado

| Feature | Status |
|---------|--------|
| Smart Zones D1/D2/D3 | ✅ |
| Canvas document generation | ✅ |
| Auto-routing Dragon | ✅ |
| KLAR/NOIR toggle | ✅ |
| i18n PT/DE/EN (UI + Agent names) | ✅ |
| Badge GEN 7 | ✅ |
| Responsivo (mobile + desktop) | ✅ |
| I9 Gate visual | ✅ |

---

## W-KEYS-001 — API Key System · SEALED · 15 Mar 2026

**Status:** IRREMEDIÁVEL
**"AI processes. Human decides. WINDI guarantees."**

### O que foi deployado

| Bloco | O quê | Estado |
|-------|-------|--------|
| Bloco 1 | Key Manager — `:8091` | ✅ LIVE (9/9 testes) |
| Bloco 2 | nginx Gateway — 4 tiers + rate limits | ✅ LIVE |
| Bloco 3 | OpenAPI W-STD-API-001 v1.1 + 3 schemas | ✅ LIVE |

### Tiers em produção

| Tier | Rate/min | Quota/hora | Preço |
|------|----------|-----------|-------|
| SEED | 10 | 100 | €0 |
| NODAL | 60 | 1.000 | €49–€149/mês |
| SOVEREIGN | 300 | 10.000 | €999+/mês |
| ORACLE | ∞ | ∞ | €0.10/prova |

### URLs em produção

```
https://windi-domain.com/api-docs/                          — Swagger UI (tema NOIR)
https://windi-domain.com/api-keys/tiers                     — Tier listing
https://windi-domain.com/api-keys/health                    — Key Manager health
https://windi-domain.com/specs/market-schema-tourism.json
https://windi-domain.com/specs/market-schema-journalism.json
https://windi-domain.com/specs/market-schema-skill-certification.json
```

### Ficheiros no servidor

```
/opt/windi/api-docs/index.html                        — Swagger UI
/opt/windi/specs/market-schema-tourism.json           — Schema Tourism
/opt/windi/specs/market-schema-journalism.json        — Schema Journalism
/opt/windi/specs/market-schema-skill-certification.json — Schema Skill Certification
/opt/windi/specs/market-schemas-index.json            — Index
```

### Formato de key

```
wnd_live_...   → produção
wnd_test_...   → sandbox
```

Identidade dupla: `wallet_id` + `owner_did`
Rotação com 24h grace period.
`/api-keys/*` → sempre 5 req/min, independente do tier (I9).
`/verify-public/` → sempre FREE, sem key, sem quota (C-PROV-001).

### Break-even

1 cliente NODAL (€49/mês) > custo infra (€4/mês). ✅ Sustentável desde o dia 1.

---

## 14. VPR System — Verified Professional Records · 15 Mar 2026

**Status:** LIVE
**URL Pública:** `https://windi-domain.com/verify-public/vpr/jober/`

### O que é VPR

VPR (Verified Professional Record) é o sistema de páginas públicas verificáveis para profissionais da rede WINDI. Cada página VPR mostra:
- Identidade verificada do profissional
- Receipts reais do Forensic Ledger (nunca placeholders)
- Three Dragons Seal institucional
- Links para verificação pública de cada receipt

### Infraestrutura

```
Path:           /opt/windi/verify-public/vpr/
Primeiro VPR:   /jober/index.html (Pioneer #001)
Static Assets:  /opt/windi/verify-public/static/
nginx:          location /verify-public/vpr/ + /verify-public/static/
```

### nginx VPR Configuration

```nginx
# VPR Static Pages (Verified Professional Records)
location /verify-public/vpr/ {
    alias /opt/windi/verify-public/vpr/;
    index index.html;
    try_files $uri $uri/ =404;
    add_header Cache-Control "public, max-age=3600";
    add_header X-WINDI-Service "vpr-static" always;
}

# Static assets (seals, icons)
location /verify-public/static/ {
    alias /opt/windi/verify-public/static/;
    add_header Cache-Control "public, max-age=86400";
    add_header X-WINDI-Service "verify-static" always;
}
```

### VPR Jober — Receipts Reais

| Receipt ID | Tipo | Verify URL |
|------------|------|------------|
| WINDI-VIRTUE-ONEWOW-20260314 | Milestone | /verify-public/?id=... |
| WINDI-PAR-GENESIS-20260315 | Genesis | /verify-public/?id=... |
| WINDI-PIONEER-MANIFESTO-20260315 | Manifesto | /verify-public/?id=... |

### Regra Constitucional — Integridade do Ledger

```
⚠️ REGRA I11 ESTENDIDA — NUNCA VIOLAR

O Ledger manifesta eventos REAIS, nunca placeholders.

❌ PROIBIDO: Criar receipts artificiais "para demo"
❌ PROIBIDO: Inventar hashes ou receipt_ids
❌ PROIBIDO: Selar documentos que não existem

✅ CORRECTO: Aguardar evento real antes de criar receipt
✅ CORRECTO: Usar apenas receipts já existentes no Ledger
✅ CORRECTO: Se não há receipt, não mostrar na página

"O Ledger é evidência forense de eventos reais.
Se o Gêmeo inventa um receipt... isso é falsificação."
— Human Dragon, 15 Mar 2026
```

---

## 15. Three Dragons Seal — NOIR Edition · 15 Mar 2026

**Status:** DEPLOYED
**URL:** `https://windi-domain.com/verify-public/static/dragon-three-seal.svg`
**Versão:** NOIR (fundo escuro, cores vibrantes)

### Design NOIR

```
Background:     #1A1208 (NOIR profundo)
Outer Ring:     #C9A84C (Dragon Gold)
Arc Text:       "GUARDIAN · ARCHITECT · WITNESS"
Arc Bottom:     "WINDI PUBLISHING HOUSE · EST. 2025"
Center W:       #C9A84C
```

### Iconografia dos Três Dragões

| Dragão | Cor | Símbolo | Significado |
|--------|-----|---------|-------------|
| Guardian | #85B7EB (Azul claro) | Escudo + chevron | Proteção & Ética |
| Architect | #EF9F27 (Amber) | Compasso | Estrutura & Construção |
| Witness | #5DCAA5 (Teal) | Olho | Observação & Validação |

### Ficheiro

```
Path: /opt/windi/verify-public/static/dragon-three-seal.svg
Size: 120×120px (em uso na verify-public)
Viewbox: 0 0 200 200
```

### Uso

```html
<img src="/verify-public/static/dragon-three-seal.svg"
     alt="WINDI Three Dragons Seal"
     style="width: 120px; height: 120px;">
```

O selo aparece em:
- Páginas VPR (Verified Professional Records)
- Verify Public (prova de receipts)
- Documentos selados (watermark)

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*
