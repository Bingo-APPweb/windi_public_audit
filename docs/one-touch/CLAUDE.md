# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.0.0
**Sealed:** 2026-03-14
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
Utilizador (mobile)
      ↓
windi-domain.com/app/   (One Touch UI)
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

### Tabela de Bridges — 8/8 COMPLETOS

| # | Agente | Bridge Prefix | Stage Map | Status |
|---|--------|---------------|-----------|--------|
| 1 | W-COMM-001 | `/communique/bridge/*` | C1-C6 | ✅ LIVE |
| 2 | W-JOURN-001 | `/journalist/bridge/*` | J1-J6 | ✅ LIVE |
| 3 | W-LEGAL-001 | `/legal/bridge/*` | L1-L6 | ✅ LIVE |
| 4 | W-NOTARY-001 | `/notary/bridge/*` | N1-N6 | ✅ LIVE |
| 5 | W-AUDIT-001 | `/audit/bridge/*` | A1-A6 | ✅ LIVE |
| 6 | W-COMPLY-001 | `/compliance/bridge/*` | P1-P6 | ✅ LIVE |
| 7 | W-ACCT-001 | `/accounting/bridge/*` | F1-F6 | ✅ LIVE |
| 8 | GROVE ARENA | `/grove/bridge/*` | G1-G6 | ✅ LIVE |

**Diferenciais por Bridge:**

| Bridge | Diferencial | Invariantes |
|--------|-------------|-------------|
| W-COMM-001 | Canvas Gen 7 integration | I9, I11 |
| W-JOURN-001 | Editorial Gate J1→J6 | I9, I11 |
| W-LEGAL-001 | 4 Jurisdições (DE/EU/BR/INT) | I9, I11 |
| W-NOTARY-001 | SHA-256 + QR + DID | I9, I11 |
| W-AUDIT-001 | READ-ONLY + Hash Chain | I9, I11 |
| W-COMPLY-001 | Risk R0-R5 + R5 Escalation | I9, I11 |
| W-ACCT-001 | C6 dupla confirmação + GoBD Gate | I9, I11, C6 |
| GROVE ARENA | Tri-Divergence I6 + 7 Sábios | I6, I9, I11 |

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

O Grove Arena não é apenas "7 agentes respondem". É um **Conselho com posições explícitas**.

### Formato de Resposta Obrigatório

```
GROVE ARENA — Tri-Divergence Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[W-LEGAL]    posição clara + reasoning
[W-NOTARY]   posição clara + reasoning
[W-COMPLY]   posição clara + reasoning
[W-JOURN]    posição clara + reasoning
[W-AUDIT]    posição clara + reasoning
[W-ACCT]     posição clara + reasoning
[W-COMM]     posição clara + reasoning

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIVERGENCE STATUS: ALL_AGREE | TWO_VS_ONE | ALL_DIFFER

GROVE SÍNTESE — recomendação institucional unificada
(só válida com human_approved=true)
```

### Estados de Divergência (I6)

```
ALL_AGREE    → consenso — síntese directa
TWO_VS_ONE   → conflito minoritário — expor ambas posições
ALL_DIFFER   → conflito total — escalar para Human Dragon (I9)
```

### Teste de Produção — Grove Bridge (14 Mar 2026)

```
Session:     GROVE-5CDCF033
Question:    "Devemos aprovar este contrato de parceria?"
Positions:   SUPPORT:4 | NEUTRAL:2 | OPPOSE:1
Divergence:  ALL_DIFFER (nenhuma maioria clara)

I6+I9 Gate Test:
  ├── Attempt 1: human_approved=false → BLOCKED ✅
  │   Response: "awaiting_i6_approval" / "I6+I9 — divergência ALL_DIFFER"
  └── Attempt 2: human_approved=true  → SEALED  ✅

Receipt:     WINDI-GROVE-GROVE-5CDCF033-20260314213350
Hash:        0b3844f39b07cf9dfae18da6e964753602d0976a8cf327ebda16bc8093862ec2
Stage:       G6 — IRREMEDIÁVEL
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
**Receipt:** WINDI-VIRTUE-ONEWOW-20260314 *(pendente seal — executar via Gêmeo)*

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

## 12. Estado Actual — 14 Março 2026

| Componente | Status |
|---|---|
| One Touch HTML (artefact) | ✅ Criado — 9 features, Dragon integrado |
| W-COMM-001 Bridge | ✅ LIVE · COMM-B44469EE testado |
| W-JOURN-001 Bridge | ✅ LIVE · BRG-5EF068B7 testado |
| W-LEGAL-001 Bridge | ✅ LIVE · Blueprint deployed |
| W-NOTARY-001 Bridge | ✅ LIVE · Blueprint deployed |
| W-AUDIT-001 Bridge | ✅ LIVE · Blueprint deployed |
| W-COMPLY-001 Bridge | ✅ LIVE · Blueprint deployed |
| W-ACCT-001 Bridge | ✅ LIVE · Blueprint deployed |
| GROVE ARENA Bridge | ✅ LIVE · GROVE-5CDCF033 testado (I6+I9) |
| Bridges Total | **8/8 COMPLETOS** |
| One Touch em produção | ⏳ Aguarda swap API key |
| Receipt ONEWOW-20260314 | ⏳ Pendente seal via Gêmeo |

---

## 13. Test Log — Bridges de Produção

### W-COMM-001 — Communiqué Bridge

```
Session:     COMM-B44469EE
Subject:     "Teste COMM Bridge via CLI"
Stage:       C6 — SELADO
Receipt:     WINDI-COMM-B44469EE-20260314210845
Invariants:  I9 ✅ | I11 ✅
```

### GROVE ARENA — Tri-Divergence Bridge

```
Session:     GROVE-5CDCF033
Question:    "Devemos aprovar este contrato de parceria?"
Advisors:    7 (W-LEGAL, W-NOTARY, W-COMPLY, W-JOURN, W-AUDIT, W-ACCT, W-COMM)

Council Response:
  [W-LEGAL]   SUPPORT  → "Contrato viável — cláusulas standard"
  [W-NOTARY]  SUPPORT  → "Assinaturas verificáveis — proceder"
  [W-COMPLY]  NEUTRAL  → "Compliance check OK — sem riscos regulatórios"
  [W-JOURN]   NEUTRAL  → "Potencial editorial médio"
  [W-AUDIT]   SUPPORT  → "Cadeia documental íntegra"
  [W-ACCT]    SUPPORT  → "Impacto fiscal neutro — sem GoBD concerns"
  [W-COMM]    OPPOSE   → "Timing subóptimo para comunicação externa"

Divergence:  ALL_DIFFER (SUPPORT:4 | NEUTRAL:2 | OPPOSE:1)
I6 Gate:     ✅ Bloqueou sem aprovação humana
I9 Gate:     ✅ Desbloqueou com human_approved=true

Final Seal:
  Receipt:   WINDI-GROVE-GROVE-5CDCF033-20260314213350
  Hash:      0b3844f39b07cf9dfae18da6e964753602d0976a8cf327ebda16bc8093862ec2
  Stage:     G6 — IRREMEDIÁVEL
  QR:        WINDI:WINDI-GROVE-GROVE-5CDCF033-20260314213350|0b3844f39b07cf9d
```

### Test Commands Reference

```bash
# Open session
curl -s -X POST http://localhost:8091/grove/bridge/open \
  -H "Content-Type: application/json" \
  -d '{"question":"...", "wallet_id":"human-dragon"}'

# Call council
curl -s -X POST http://localhost:8091/grove/bridge/council \
  -H "Content-Type: application/json" \
  -d '{"session_id":"GROVE-XXX", "advisor_responses":[...]}'

# Publish (I6+I9 gate)
curl -s -X POST http://localhost:8091/grove/bridge/publish \
  -H "Content-Type: application/json" \
  -d '{"session_id":"GROVE-XXX", "human_approved":true}'

# Status
curl -s "http://localhost:8091/grove/bridge/status?session_id=GROVE-XXX"
```

---

## 14. Health Check — 8/8 Bridges LIVE

**Executado:** 2026-03-14T21:58Z
**Sandbox Core:** `:8091` — ONLINE

| # | Bridge | Endpoint | Session ID | Stage | Status |
|---|--------|----------|------------|-------|--------|
| 1 | W-COMM-001 | `/communique/bridge/open` | COMM-5665DC2B | C1 | ✅ LIVE |
| 2 | W-JOURN-001 | `/journalist/bridge/open` | BRG-E24346E4 | J4 | ✅ LIVE |
| 3 | W-LEGAL-001 | `/legal/bridge/open` | LEGAL-A89F2CBE | L1 | ✅ LIVE |
| 4 | W-NOTARY-001 | `/notary/bridge/open` | NOTARY-E6870DAB | N1 | ✅ LIVE |
| 5 | W-AUDIT-001 | `/audit/bridge/open` | AUDIT-9C2EFE50 | A1 | ✅ LIVE |
| 6 | W-COMPLY-001 | `/compliance/bridge/open` | COMPL-59E6D6E3 | CP1 | ✅ LIVE |
| 7 | W-ACCT-001 | `/accounting/bridge/open` | ACCT-4807A6D9 | F1 | ✅ LIVE |
| 8 | GROVE ARENA | `/grove/bridge/open` | GROVE-F3EACB9C | G1 | ✅ LIVE |

### Notas de Workflow

```
W-JOURN-001: Requer draft_id existente na DB (workflow editorial)
             Criar draft via POST /journalist/draft primeiro

W-ACCT-001:  Dual confirmation (human_approved + c6_confirmed)
             GoBD FAIL bloqueia stages F4+

GROVE ARENA: Tri-Divergence (I6) + Human Gate (I9)
             ALL_DIFFER escala automaticamente para Human Dragon
```

### Comando Health Check

```bash
# Quick health check all bridges
for bp in communique legal notary audit compliance accounting grove; do
  curl -s -X POST http://localhost:8091/$bp/bridge/open \
    -H "Content-Type: application/json" \
    -d '{"subject":"health","wallet_id":"test"}' | grep -o '"status":"[^"]*"'
done
```

---

## 15. UI Integration Test — 14 Março 2026

**Executado:** 2026-03-14T22:03Z

### Stack Verificada

| Componente | URL | Status |
|------------|-----|--------|
| One Touch UI | `https://windi-domain.com/app/` | ✅ 200 OK |
| Dragon Hub | `:8108/health` | ✅ Healthy v1.3.0 |
| Dragon Chat | `/api/dragon/chat` | ✅ 93.3% sovereign |
| Sandbox Core | `:8091` | ✅ 8/8 bridges |
| Verify Public | `/verify-public/` | ✅ Online |

### Dragon Hub Status

```json
{
  "status": "healthy",
  "version": "1.3.0",
  "dragons": ["guardian", "architect", "witness"],
  "model": "claude-sonnet-4-20250514",
  "api_key_configured": true,
  "sge_available": true
}
```

### Fluxo Completo Testado — COMM Bridge

```
Session:  COMM-1812733D
Wallet:   human-dragon

C1 → Sessão criada (2026-03-14T22:03:01Z)
C4 → Conteúdo guardado
     Hash: 7675279c3db1d8c1e6119a102c4fd83f597d4b4a8b7780c3a4956811e1ac7755
C5 → I9 Gate: BLOQUEOU sem human_approved ✅
C6 → Selado com human_approved=true ✅

Receipt:  WINDI-COMM-COMM-1812733D-20260314220321
QR:       WINDI:WINDI-COMM-COMM-1812733D-20260314220321|7675279c3db1d8c1
Verify:   https://windi-domain.com/verify-public/?id=WINDI-COMM-COMM-1812733D-20260314220321
```

### Dragon Chat — Teste HIGH Tier

```
Input:  "Cria um communiqué institucional: Anúncio de parceria
         estratégica com empresa XYZ para expansão europeia"
Tier:   HIGH
Dragon: Architect 🏗️

Output: Communiqué trilíngue (PT/DE/EN) gerado via LLM
        - Título: Parceria Estratégica para Expansão Europeia
        - Estrutura: Anúncio formal + contexto + próximos passos
        - Sovereignty: 93.3% local (I10 compliant)
```

### UI Tech Stack

```
Framework:    React 18.2.0 + Babel 7.23.9
Engine:       DragonEngine v2.0 (Modular Architecture)
QR:           qrcodejs 1.0.0
Monitor:      W-FERR-001 (O Ferreiro Health Monitor)
Theme:        NOIR (#080808 bg, #8B6914 gold)
Version:      WINDI Personal Editor v0.9.1-C — Forensic Cartaz
```

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*
