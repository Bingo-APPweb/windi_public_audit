# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.9.21
**Sealed:** 2026-03-19
**Author:** Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
**Location:** Kempten, Bavaria, Deutschland

> **Ficheiros relacionados:** `CHANGELOG.md` (histórico) · `ARCHITECTURE.md` (código técnico)

## 📚 Overflow Policy (17 Mar 2026)
Hard limit: **32KB**. Overflow detectado: 45.2KB → corrigido para 24.9KB.
- **CLAUDE.md** = presente + futuro + regras (≤ 32KB)
- **CLAUDE-HISTORY.md** = passado selado (ilimitado, append-only)
- **REGRA:** sessão encerrada → documentação detalhada migra para HISTORY

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
| I12 | Language Sovereign Principle | Conversa=Universal, Documento=Soberano. Babel Tower=IRREMEDIÁVEL. |
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

### 3.4 Language Sovereign Principle (I12)

```
CONVERSA  →  Universal Language
             Responde SEMPRE na língua em que o utilizador escreve.
             "Olá" → PT · "Hallo" → DE · "Hello" → EN

DOCUMENTO →  Língua Soberana
             Gera SEMPRE na língua do toggle/wallet do utilizador.
             Nunca misturar línguas dentro de um documento.
             Ao iniciar rascunho: "Documento em [DE/EN/PT]"

BABEL TOWER = anti-pattern WINDI (IRREMEDIÁVEL)
             Um documento = uma língua.
             Misturar PT/DE/EN no mesmo doc é violação constitucional.
```

**UX — Hint Visual (obrigatório):**
```
┌─────────────────────────────────────────────────────┐
│ Barra de acções do documento                        │
│                                                     │
│  [📎 Img] [🎬 Video] [🎙️ Voz]    📄 DE ▼  [🛡️ Finalizar] │
│                                  ↑                  │
│                        Clicável → abre toggle       │
└─────────────────────────────────────────────────────┘

Dragon também informa:
  "Documento parece pronto! Clica Finalizar. 🛡️
   📄 Documento em **DE**"
```

**Sealed:** 2026-03-17 · Dragon Alzheimer Fix → Language Sovereign Principle

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
Agent Bridge (por tipo de documento)
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

| # | Agente | Bridge Prefix | Status |
|---|--------|---------------|--------|
| 1 | W-COMM-001 | `/communique/bridge/*` | ✅ LIVE |
| 2 | W-JOURN-001 | `/journalist/bridge/*` | ✅ LIVE |
| 3 | W-LEGAL-001 | `/legal/bridge/*` | ✅ LIVE |
| 4 | W-NOTARY-001 | `/notary/bridge/*` | ✅ LIVE |
| 5 | W-AUDIT-001 | `/audit/bridge/*` | ⏳ Pendente |
| 6 | W-COMPLY-001 | `/compliance/bridge/*` | ⏳ Pendente |
| 7 | W-ACCT-001 | `/accounting/bridge/*` | ⏳ Pendente |
| 8 | GROVE ARENA | `/grove/arena` | ✅ LIVE v1.3.0 |

**Total:** 25 blueprints activos em `/constitutional-agent/blueprints/`

---

## 6. Virtue Receipts — Schema Obrigatório

```json
{
  "receipt_id":   "WINDI-[AGENT]-[YYYYMMDDHHMMSS]",
  "actor":        "human-dragon",
  "app":          "one-touch-mobile",
  "doc_name":     "Título do documento",
  "doc_type":     "communique | doc | jmpg | pptx | web | slides",
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

**Versão:** v1.3.0 · **Port:** :8091

O Grove Arena é um **motor de decisão constitucional**.

### Estados de Divergência

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

## 8. System Prompts Canónicos

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

### Prompts por Agente (resumo)

| Agente | Especialidade | Terminar com |
|--------|---------------|--------------|
| W-COMM-001 | Communiqués, Werbebriefe, Certificados | "→ Bridge C5 aguarda aprovação" |
| W-JOURN-001 | Pipeline editorial J1→J6 | "→ J6-Gate com human_approved=true" |
| W-LEGAL-001 | 4 jurisdições: DE/EU/BR/INT | "→ /legal/bridge/commit" |
| W-NOTARY-001 | SHA-256 · Ed25519 DID · Ledger | "→ Aguarda human_approved para I11 seal" |
| W-ACCT-001 | GoBD · XRechnung · ELSTER | "→ C6 IRREMEDIÁVEL · Aguarda aprovação" |
| W-COMPLY-001 | DSGVO · eIDAS · LGPD | "→ Risk assessment pronto" |
| W-AUDIT-001 | Hash verification · Provenance | "→ /audit/bridge/seal" |
| GROVE ARENA | Tri-Divergence I6 | "→ Decisão final: Human Dragon" |

---

## 9. Design System — One Touch

```
Tema:         NOIR (#080808 bg, #8B6914 gold, #F5F0E0 text)
Fonte:        Bricolage Grotesque (headings 800) + JetBrains Mono (hashes)
Touch targets: mínimo 44px (Apple HIG + Google Material)
Breakpoints:  ≥1200 Desktop · 768-1199 Tablet · <768 Mobile
```

**Cores por agente:**

| Agente | Cor |
|--------|-----|
| W-COMM-001 | #8B6914 (WINDI Gold) |
| W-LEGAL-001 | #1a3a6b (Azul) |
| W-NOTARY-001 | #5a1a6b (Púrpura) |
| W-JOURN-001 | #6b1a1a (Vermelho) |
| W-AUDIT-001 | #2d4a1a (Verde) |
| W-ACCT-001 | #4a3a1a (Castanho) |
| W-COMPLY-001 | #1a4a5a (Azul compliance) |
| GROVE ARENA | #2d5a2d (Verde conselho) |

---

## 10. Marketing da Epifania

**Receipt:** WINDI-VIRTUE-ONEWOW-20260314 ✅ **SELADO**
**Hash:** `sha256:83887dde96130efdcc8ed0340bd2eb5980878109680d3598ae1dce7ea222bbae`

> "A tecnologia é complexa para que a experiência seja estúpida de tão simples."

**Os 4 Pilares:**

| Pilar | Princípio |
|-------|-----------|
| P1 | Faz antes de explicar |
| P2 | Silêncio como onboarding |
| P3 | Virtude Forense Imutável |
| P4 | Uma frase basta |

### Pioneer Program — LIVE

| URL | Status |
|-----|--------|
| `windi-domain.com/pioneer/` | ✅ HTTP 200 |
| `windi-domain.com/pioneer/florianopolis/` | ✅ HTTP 200 |
| `windi-domain.com/pioneer/manifesto/` | ✅ HTTP 200 |

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

### G1 — READ BEFORE TOUCH (IRREMEDIÁVEL)
Antes de qualquer alteração de código ou ficheiro:
```
git log --oneline -10
git diff HEAD~1 HEAD -- [ficheiro]
ss -tlnp | grep [porta]
```
Nunca assumir o estado do servidor. Sempre verificar.

### G2 — ONE DOMAIN PER SESSION (IRREMEDIÁVEL)
Uma sessão = um repositório = um domínio de ficheiros.
```
✅ Sessão Canvas  → toca APENAS desktop-gen7/
✅ Sessão Mobile  → toca APENAS agent-palette/
✅ Sessão Infra   → toca APENAS nginx + systemd
❌ NUNCA dois domínios na mesma sessão
```

### G3 — PROPOSE ≠ EXECUTE (IRREMEDIÁVEL)
Toda alteração > 10 linhas exige:
1. `git diff --stat` (mostrar o que vai mudar)
2. Aguardar "confirma" explícito do Human Dragon
3. Só então executar

### G4 — COMMITS SÃO CONTRATOS (IRREMEDIÁVEL)
```
git diff --stat SEMPRE antes do commit.
❌ Proibido: "fix misc", "updates", "ajustes"
✅ Obrigatório: mensagem precisa com ficheiros + intenção
```

### G5 — SEALED PORTS SÃO SAGRADOS (IRREMEDIÁVEL)
Portas seladas: **8101, 8102, 8106, 8114**
- NUNCA alterar sem aprovação EXPLÍCITA
- `nginx -t` SEMPRE antes de reload
- Ledger (:8101) = intocável

### G6 — CANVAS COMMITS SÃO PROTEGIDOS (IRREMEDIÁVEL)
Commits do pipeline Canvas são protegidos.
Qualquer alteração exige:
1. Listar commits Canvas existentes
2. Justificar por que não os quebra
3. Aprovação do Human Dragon

### Hierarquia

```
Constitucionais WINDI (I1-I11) > Invariantes Gêmeo (G1-G6)
> Regras de Ouro (11.1-11.10) > Invariantes Frontend (11.2) > Instruções de sessão
```

---

## 11.2 — FRONTEND INVARIANTS (Lei Constitucional UI)

**TODA criação de UI/página/componente WINDI deve cumprir DUAS leis:**

### A) I18N — Trilíngue Obrigatório

```
Toggle sempre: DE | EN | PT (esta ordem, sempre)
Auto-detect:   localStorage('windi-lang') → browser → fallback 'en'
Strings:       objecto I18N = { de:{}, en:{}, pt:{} }
setLang():     aplica + persiste + marca botão .active
```

### B) THEME — NOIR/KLAR Obrigatório

```
Temas:         NOIR (dark) = default | KLAR (light)
localStorage:  'windi-theme' → 'noir' | 'klar'
Toggle icon:   ☀ (está noir) | ☽ (está klar)
CSS vars:      [data-theme="noir"] e [data-theme="klar"]
initTheme():   ler localStorage + aplicar no body.dataset.theme
```

### Cores Canónicas

```
NOIR (dark):
  --bg:      #0A0A10
  --gold:    #C9A84C
  --text:    #E8E6E1
  --border:  #1A1A24

KLAR (light):
  --bg:      #FAFAF8
  --gold:    #8B7424
  --text:    #1A1A1A
  --border:  #E0DED8
```

### Anti-patterns PROIBIDOS

```
❌ Página só em PT (ou qualquer língua única)
❌ Página só em NOIR (sem toggle KLAR)
❌ Hardcode de texto visível fora do objecto I18N
❌ Hardcode de cores fora das CSS vars
❌ Ordem diferente no toggle idioma (ex: PT|EN|DE)
❌ Usar chave localStorage diferente de 'windi-lang' / 'windi-theme'
```

### Checklist Antes de Entregar

```
[ ] Título traduzido nas 3 línguas?
[ ] CTAs traduzidos?
[ ] Footer/labels traduzidos?
[ ] Toggle DE|EN|PT presente e funcional?
[ ] Toggle ☀/☽ NOIR/KLAR presente e funcional?
[ ] CSS vars para ambos os temas?
[ ] localStorage sync com outras páginas?
[ ] Botão voltar trilíngue?
```

**Violação = retrabalho imediato. Sem excepções.**

---

## 12. GEN 7 — Desktop Sovereign Editor

**Status:** ✅ PRODUÇÃO
**Port:** :8119
**URL:** `windi-domain.com/desktop/`

### Smart Zones

```
┌─────────────────────────────────────────────────────────────┐
│ COMMAND BAR — Dragon Pulse + API Keys Indicator             │
├─────────────────────────────────────────────────────────────┤
│ D1 — Agent Corps    │ D2 — Sovereign Editor │ D3 — Gov Glass│
└─────────────────────────────────────────────────────────────┘
```

### Pipeline (6 Fases)

```
Phase 1 → Intent Capture (voice/text)
Phase 2 → Dragon Processing (tier routing)
Phase 3 → Agent Bridge (document type)
Phase 4 → Canvas Materialization
Phase 5 → Human Gate (I9)
Phase 6 → Ledger Seal (I11 IRREMEDIÁVEL)
```

### Endpoints Principais

| Endpoint | Função |
|---|---|
| `/health` | Ecosystem status |
| `/api/dragon/status` | Dragon Pulse |
| `/api/agents/status` | Agent Corps |
| `/api/onetouch/execute` | Pipeline execution |
| `/api/onetouch/seal` | C5→C6 seal |
| `/api/onetouch/dispatch` | Envio (email/whatsapp) |
| `/api/export/web` | Export HTML standalone |
| `/api/publish/web` | Publish to /sites/ |

### 7 Motores

| Motor | Output | Status |
|-------|--------|--------|
| DOC | HTML semântico | ✅ LIVE |
| SLIDES | windi-slides HTML | ✅ LIVE |
| WEB | HTML/CSS/JS completo | ✅ LIVE |
| ART | SVG artístico | ✅ LIVE |
| DATA | Dashboard + Chart.js | ✅ LIVE |
| CODE | Docs + highlight.js | ✅ LIVE |
| MEDIA | Newsletter 600px | ✅ LIVE |

> **Código de detecção:** ver `ARCHITECTURE.md`

---

## 13. Estado Actual — 19 Março 2026

### Mapa de Portas

| Porto | Serviço | Estado |
|---|---|---|
| :8091 | Sandbox Core (Agent Corps) | 🟢 LIVE |
| :8100 | Desktop v2.0.0 (legacy) | 🔴 RETIRED |
| :8101 | Forensic Ledger | 🟢 SEALED |
| :8108 | Dragon Hub v1.3.0 | 🟢 LIVE |
| :8119 | Desktop GEN 7 | 🟢 **PRODUÇÃO** |
| :8096 | Lead Admin (ID Genesis) | 🟢 LIVE · systemd · env secured |
| :8099 | Wallet Service | 🟢 LIVE · Trust E2E · 11 pioneers |
| :8120 | Pioneer Landing | 🟢 LIVE |
| :8121 | Dispatch Gateway | 🟢 **.jmpg Hydration Engine** · I5+I6+I9 |

### Sistemas LIVE

| Sistema | Status |
|---------|--------|
| GEN 7 Desktop | ✅ Smart Zones + 7 Motores + W-CIA-001 |
| Pioneer Program | ✅ /pioneer/ trilíngue |
| VPR System | ✅ /verify-public/vpr/jober/ |
| API Key System | ✅ W-KEYS-001 SEALED |
| Dispatch Pipeline | ✅ email + whatsapp |
| Web Hosting | ✅ /sites/ + /s/ short URLs |
| i18n Dragon | ✅ PT/DE/EN auto-detect |
| Wallet System | ✅ 4/4 gaps · 11 pioneers · Trust E2E |
| Lead Admin | ✅ :8096 · systemd · env secured · G3 hook |
| W-CIA-001 | ✅ Health Pulse no GEN7 Desktop · 7 endpoints monitorizados |
| W-GATE-001 | ✅ API Schema Contracts · 15 endpoints · erro HUMANO trilíngue |
| W-NGINX-001 | ✅ Nginx Auto-Register · 302 rotas Flask · 64 locations · pre-commit hook |

### Completado Hoje (19 Mar 2026)

| Fix | Descrição |
|-----|-----------|
| **W-CIA-001 GEN7** | Health Pulse indicator no Desktop header · Panel com diagnóstico de 7 serviços |
| **nginx /api/onetouch/** | Rota adicionada → proxy :8119 (estava a retornar HTML 301) |
| **nginx /how-it-works/** | Rota adicionada → alias landing page trilíngue |
| **CTA How it Works** | `/app/` → `/desktop/` no botão "Começar" |
| **nginx /api/seal** | Rota adicionada → proxy :8119 |
| **nginx /api/export/web** | Rota adicionada → proxy :8119 |
| **nginx /api/publish/web** | Rota adicionada → proxy :8119 |
| **copyCanvasToClipboard** | Fix `event.target` undefined — adicionado parâmetro `e` |
| **CIA indicator layout** | Separador `\|` + ícone 🛡️ + dot posicionado |
| **Keys button CSS** | `.api-keys-indicator` clicável com z-index correcto |
| **nginx /keys/** | Rota adicionada → alias `/opt/windi/keys-pricing/` |
| **§27 W-GATE-001** | API Schema Contracts LIVE · 15 endpoints protegidos · Elimina Loop 2 |
| **§28 CIA Pre-Flight** | Validação frontend ANTES de API call · 4 funções · Toast trilíngue · Elimina Loop 3 |
| **§29 W-KEYS-002** | Technical Explainer Page — educa ANTES de mostrar preço · 52 strings i18n |
| **§30 W-NGINX-001** | Nginx Auto-Register LIVE · Detecta rotas Flask sem nginx · pre-commit hook · Elimina Loop 1 |

### Completado (18 Mar 2026)

| Fix | Descrição |
|-----|-----------|
| **§22 Sovereignty Metrics** | I13 Token Independence — 93.3% local, meta ultrapassada 149% |
| **§23 Qualidade Soberana** | WB-KNOW-SOVEREIGNTY-Q-20260318 SEALED · Espelho HTML + Princípio |
| **§24 W-CIA-001** | Detetive Constitucional BIRTH SEALED · Health Pulse no Composer · 5 nginx patches |
| **§25 W-MGR-001** | Gerente do Composer LIVE · HUD âmbar · i18n automático |
| **§26 W-SCH-001** | Instrutor do Composer LIVE · 6 dicas contextuais · Toggle ON/OFF |
| **WALLET 4/4** | G1 nginx ✅ · G2 env var ✅ · G3 Lead hook ✅ · G4 Trust E2E ✅ |
| **Lead Admin systemd** | nohup → systemd · boot resilient · 39 serviços total |
| **G3 Tools + Verify** | 🛡️ Verify adicionado à Tools section · `/verify-public/web/` |
| **Root Redirect** | `windi-domain.com/` → 301 → `/desktop/` · GEN 7 porta única |

### Completado (17 Mar 2026)

| Fix | Descrição |
|-----|-----------|
| CLAUDE.md v1.9.0 | Refactor 45k→15k chars (-65%) |
| CHANGELOG.md | Novo ficheiro — histórico de milestones |
| ARCHITECTURE.md | Novo ficheiro — código técnico |
| i18n Fix | `detect_language()` respeita EN (linha 1335) |
| Canvas ← Novo | Botão na toolbar G2 — volta ao home (DE/PT/EN) |
| URL Fix | `/app/api/dragon` → `/api/dragon` |
| History Fix | `human→user`, `text→content` |
| **How it Works** | Landing page trilíngue PT/DE/EN — `/how-it-works/` LIVE |
| Nav Link | Botão "How it Works" na header GEN 7 |
| i18n Sync | localStorage `windi-lang` partilhado entre páginas |
| Back Button | "← Voltar/Zurück/Back" trilíngue |
| **§11.2 FRONTEND INVARIANTS** | Lei constitucional: i18n + NOIR/KLAR obrigatórios |
| Theme Toggle | ☀/☽ NOIR/KLAR na `/how-it-works/` |
| **/keys/ Fix** | Back button + NOIR/KLAR + localStorage sync |
| **§17 .JMPG** | Documentação completa do formato soberano |
| **Dispatch Gateway** | :8121 LIVE — .jmpg Hydration Engine · I5+I6+I9 |

### Backlog Activo

| Item | Prioridade |
|---|---|
| Rate-limit nginx Agent Corps | Média |
| W-ACCT-001 bridge dedicado | Baixa |
| W-AUDIT-001 bridge dedicado | Baixa |

> **Histórico completo:** ver `CHANGELOG.md`

---

## 14. Integridade do Ledger — Regra I11

```
⚠️ NUNCA VIOLAR

O Ledger manifesta eventos REAIS, nunca placeholders.

❌ PROIBIDO: Criar receipts artificiais "para demo"
❌ PROIBIDO: Inventar hashes ou receipt_ids
❌ PROIBIDO: Selar documentos que não existem

✅ CORRECTO: Aguardar evento real antes de criar receipt
✅ CORRECTO: Usar apenas receipts já existentes no Ledger

"O Ledger é evidência forense de eventos reais.
Se o Gêmeo inventa um receipt... isso é falsificação."
— Human Dragon, 15 Mar 2026
```

---

## 15. W-KEYS P5 — Pricing Page · 17 Mar 2026

**Status:** ✅ LIVE
**URL:** `windi-domain.com/keys/`
**Path:** `/opt/windi/keys-pricing/index.html`

### Features

| Feature | Descrição |
|---------|-----------|
| i18n | PT/DE/EN com auto-detect + sync `windi_lang` |
| 4 Tiers | SEED €0 · NODAL €49 · SOVEREIGN €999+ · ORACLE interno |
| CTAs | `/api-keys/request?tier=X` |
| I9 Gate | Documentado no rodapé |

### Infraestrutura

```
nginx:  location ^~ /keys/ → alias /opt/windi/keys-pricing/
Botão:  🔑 Chaves no header GEN7 → onclick="/keys/"
```

### i18n Strings

| Key | PT | EN | DE |
|-----|----|----|-----|
| title | Leve o WINDI... | Bring WINDI... | WINDI für Ihre... |
| popular | Mais escolhido | Most popular | Meistgewählt |
| ctaNodal | Activar Nodal → | Activate Nodal → | Nodal aktivieren → |

---

## 16. NAMING — Interface Pública vs Interno · 17 Mar 2026

### Regra

| Contexto | Usar | Não usar |
|----------|------|----------|
| Interface pública | "WINDI", "Hey WINDI" | "Dragon", "Hey Dragon" |
| Documentação interna | "Three Dragons" | — |
| Código/API | `dragon_*` (legacy OK) | — |

### Razão

"Dragon" é palavra inglesa → confunde o `detect_language()` → resposta na língua errada.

### Implementação

```python
# sovereign_router.py — NEUTRAL_MARKERS
NEUTRAL_MARKERS = {"windi", "dragon", "guardian", "architect", "witness", "ledger", "vault"}

# detect_language() remove estes antes de contar scores
# Resultado: "Hallo WINDI" → detecta DE correctamente
```

### Three Dragons (conceito interno)

```
🛡️ Guardian  — Protege, valida, I9 gate
🏗️ Architect — Constrói documentos
👁️ Witness   — Observa, sela no Ledger
```

> Rebranding completo Dragon→WINDI: sessão futura dedicada.

---


## 21. Wallet Gate — DID Identity Modal (FASE 1)

**Version:** 1.0
**URL:** `https://windi-domain.com/desktop/` (botão 🪪 no header)
**Deployed:** 17 Mar 2026 22:30
**Status:** FASE 1 LIVE · FASE 2 pendente

### Função

O Wallet Gate é o sistema de autenticação por identidade soberana no GEN7.
Permite que utilizadores com WALLET DID acedam às suas credenciais directamente no Desktop.

### Arquitectura

```
Botão 🪪 Wallet (header)
        ↓
Modal abre → verifica sessionStorage
        ↓
┌─────────────────────────────────────────────────────────────┐
│  Estado A (sem wallet)          Estado B (com wallet)       │
│  ├── Input: WALLET-YYYYMMDD-N   ├── DID: WALLET-...         │
│  ├── Botão "Entrar"             ├── TIER: L1                │
│  └── Link "Criar Wallet"        ├── TRUST: T1 · 50          │
│                                 ├── FINGERPRINT: sha256...  │
│                                 └── Logout                  │
└─────────────────────────────────────────────────────────────┘
        ↓
Login → GET /api/wallet/me?wallet_id=
        ↓
sessionStorage.setItem('windi_desktop_wallet', JSON)
        ↓
window.__windiWallet   = data     ← Exposto para módulos
window.__windiWalletId = wallet_id ← Pronto para Ledger
```

### Endpoints Utilizados

| Endpoint | Método | Função |
|----------|--------|--------|
| `/api/wallet/me?wallet_id=` | GET | Obter wallet por ID |
| `/api/wallet/health` | GET | Health check |
| `/api/wallet/stats` | GET | Estatísticas públicas |

### Storage

```javascript
// SessionStorage key
const WM = { SESSION_KEY: 'windi_desktop_wallet' };

// Window globals (para integração)
window.__windiWallet    // Objeto wallet completo
window.__windiWalletId  // String WALLET-YYYYMMDD-NNNN
```

### Ficheiros Modificados

```
/opt/windi/desktop-gen7/frontend/
├── index.html           (+80 linhas — botão + modal HTML)
├── static/styles.css    (+180 linhas — CSS modal)
└── static/app.js        (+130 linhas — WM object + funções)
```

### FASE 2 — Pendente

| Gap | Descrição | Prioridade |
|-----|-----------|------------|
| **G1** | OneTouch inclui `wallet_id` no payload | ALTA |
| **G2** | Ledger seal associa receipt ao `wallet_id` | ALTA |
| **G4** | Trust score incrementa com receipts | MÉDIA |

### Integração G1 (1 linha)

```javascript
// Em executeOneTouch():
body: { ..., wallet_id: window.__windiWalletId }
```

### Integração G2 (Ledger)

```javascript
// Em sealCanvasToLedger():
payload.wallet_id = window.__windiWalletId;
payload.human_fingerprint = window.__windiWallet?.fingerprint;
```

---

## 22. Sovereignty Metrics — I13 Token Independence · 18 Mar 2026

**Audit Ref:** AUDIT-SOVEREIGNTY-20260224
**Source:** `/opt/windi/agent-palette/sovereign_router.py`
**Princípio:** "Integridade é universal. Interpretação é premium."

### Métricas Actuais

```
Total Funções:        45
Funções Locais:       42  (Mistral local / sem LLM externo)
Funções Semânticas:    3  (requerem Anthropic API)

RATIO:                93.3% soberano / 6.7% externo
```

### Progresso — Redução de Keys Externas

```
BASELINE (Jan 2026):   4000 tokens externos/sessão
META:                  1500 tokens externos/sessão
ACTUAL (Mar 2026):     ~268 tokens externos/sessão

PROGRESSO:             149.3% ✅ META ULTRAPASSADA
```

### As 3 Funções Semânticas

| Intent | Fallback Local | Handler |
|--------|----------------|---------|
| `CHAT_INTERPRETIVE` | `HELP` | llm_semantic |
| `SEMANTIC_ANALYSIS` | `CHECK_RISK` | llm_semantic |
| `TEXT_GENERATION` | `HELP` | llm_semantic |

### I10 Continuity — Fallback Gracioso

```
Se LLM externo falha → sistema NÃO quebra
                     → transiciona para alternativa local
                     → utilizador continua a trabalhar
```

### Fórmula de Cálculo

```
Tokens Externos = BASELINE × (1 - SOVEREIGNTY_RATIO)
                = 4000 × 0.067
                = ~268 tokens

Progresso = (BASELINE - ACTUAL) / (BASELINE - META) × 100
          = (4000 - 268) / (4000 - 1500) × 100
          = 149.3%
```

---

## 23. Princípio: Qualidade Soberana · 18 Mar 2026

**WB-KNOW-SOVEREIGNTY-Q-20260318 · SEALED · HIGH**
**Hash:** `sha256:66d542fcc2118f8e174f32d0c9caea336205dc3f73ee735122149fe9716e2d3b`

O WINDI não economiza tokens para gastar menos — economiza para investir onde a qualidade exige.

### Métricas Seladas

| Métrica | Valor |
|---------|-------|
| Soberania local | 93.3% (42/45 funções) |
| Tokens externos actuais | ~268tk |
| Meta estabelecida | 1500tk |
| Progresso | 149.3% ✓ META ULTRAPASSADA |

### Regras Constitucionais

- FREE = escudo absoluto, zero LLM externo
- Token externo = investimento justificado por qualidade superior
- Fallback I10: SEMANTIC→LOCAL sempre disponível
- Wisdom Blocks crescem → tokens externos diminuem ao longo do tempo

### Frase

> "O externo sustenta. O interno orienta. A qualidade decide."

### Artefactos

| Tipo | Path |
|------|------|
| HTML | `/opt/windi/docs/espelho-qualidade-soberana.html` |
| SKILL | Sistema Claude Code |

---

## 24. W-CIA-001 — Detetive Constitucional · 18 Mar 2026

**WINDI-CIA-001-BIRTH-20260318 · SEALED · HIGH**
**Verify:** `https://windi-domain.com/verify-public/document/WINDI-CIA-001-BIRTH-20260318`

O W-CIA-001 é o agente de diagnóstico e monitorização do ecossistema WINDI.
Nasceu de uma conversa matinal sobre Replit Agent 4 e tornou-se infraestrutura constitucional em 97 minutos.

### Capacidades

| Capacidade | Descrição |
|------------|-----------|
| Health Pulse | Diagnóstico de 4 serviços em paralelo (Dragon, Ledger, Export, Dispatch) |
| Indicador Visual | Dot pulsante no topbar do Composer (🟢/🟡/🔴) |
| Polling Autónomo | Verificação a cada 30 segundos |
| Painel Clicável | Detalhes de cada serviço com status LIVE/WARN/DOWN |

### Arquitectura

```
W-CIA-001
├── DIAGNÓSTICO  ← Fase actual (bug tracking + health monitoring)
├── SHIELD       ← Fase futura (anti-intrusion + rate-limit)
└── FORENSE      ← Maturidade (receipt por tentativa de ataque)
```

### Princípio

> "Observa. Regista. Propõe. Aguarda o Toque Soberano."

### Ficheiros

| Tipo | Path |
|------|------|
| Health Pulse | `/opt/windi/jornal/jornal-composer.html` (linhas 69-94, 359-372, 1448-1505) |
| Patch Dragon | `/home/windi/patch-nginx-dragon-health.sh` |
| Patch Dispatch | `/home/windi/patch-nginx-dispatch-health.sh` |
| Patch Verify | `/home/windi/patch-nginx-verify-api.sh` |

### Gaps Resolvidos na Sessão de Nascimento

| Gap | Descrição | Status |
|-----|-----------|--------|
| G4 | Ledger seal pipeline | ✅ 56562 receipts |
| G3 | Export Engine :8103 | ✅ SOVEREIGN M3 |
| G1 | Dragon /health via nginx | ✅ LIVE |
| G5 | Dispatch /health via nginx | ✅ LIVE |
| G6 | Verify API via nginx | ✅ LIVE |

---

## 25. W-MGR-001 — Gerente do Composer · 18 Mar 2026

**Status:** LIVE no Jornal Composer
**Princípio:** "O Gerente observa. Propõe. Nunca decide sem o Humano." (I9)

O W-MGR-001 observa o **documento** e sugere melhorias contextuais.

### Comportamento

| Trigger | Sugestão |
|---------|----------|
| Canvas vazio | "Começar com Cover-Block?" |
| Poucos blocos | "Adicionar mais conteúdo?" |
| Gaps detectados | Sugestões específicas |

### Características

- HUD âmbar no canto inferior direito
- i18n automático (DE/EN/PT)
- Botões: Aceitar / Dispensar
- Polling a cada 45s + idle 120s

---

## 26. W-SCH-001 — Instrutor do Composer · 18 Mar 2026

**Status:** LIVE no Jornal Composer
**Princípio:** "Ensina quando o Humano parou."

O W-SCH-001 observa o **Humano** e ensina quando detecta idle.

### 6 Dicas Contextuais

| Contexto | Dica |
|----------|------|
| Canvas vazio | 📰 "Começa pela Capa" |
| Bloco Evidências | 🛡️ "OCR directo disponível" |
| Bloco Capa | 🎯 "Título com impacto" |
| Inspector aberto | ✨ "AI Generate disponível" |
| 3+ blocos | 🚀 "Pronto para Despachar" |
| Fallback | 🌐 "3 línguas por bloco" |

### Características

- Toast centrado no fundo do ecrã
- Trigger: 60s idle
- Auto-dismiss: 10s
- Toggle ON/OFF no topbar
- localStorage: `windi_sch_enabled`
- Nunca repete dicas na mesma sessão

### Topbar do Composer

```
[🟢 CIA]  [● MGR]  [🟢 SCH]
     ↑         ↑         ↑
  Saúde    Gerente   Instrutor
ecossistema documento   humano
```

---

## 27. W-GATE-001 — API Schema Contracts · 19 Mar 2026

**Status:** LIVE no Constitutional Agent (:8091)
**Princípio:** "Nenhum endpoint novo sobe sem contrato."

Sistema de Contenção #1 — Elimina Loop 2 (campos faltando → erro críptico).

### Problema Resolvido

```
ANTES: POST /bridge/save com {} → "Unexpected token '<', <!DOCTYPE..."
AGORA: POST /bridge/save com {} → {"error": "session_id é obrigatório", "field": "session_id"}
```

### Arquitectura

```
/opt/windi/contracts/
├── bridge.json        # Contratos genéricos bridge
├── communique.json    # W-COMM-001 endpoints
├── dragon.json        # Dragon Hub + export + publish
├── journalist.json    # W-JOURN-001 endpoints
├── onetouch.json      # OneTouch pipeline
└── validate_payload.py # Validador Python (middleware Flask)
```

### Middleware Flask

```python
# agent.py — injectado em @app.before_request
@app.before_request
def validate_api_contracts():
    error_response = validate_request(request)
    if error_response:
        return jsonify(error_response[0]), error_response[1]
```

### Endpoints Protegidos (15)

| Endpoint | Required Fields |
|----------|-----------------|
| `/bridge/open` | `title` |
| `/bridge/save` | `session_id`, `content_blocks` |
| `/bridge/publish` | `session_id` |
| `/communique/bridge/*` | (mesmos) |
| `/journalist/bridge/*` | `title`, `session_id`, `blocks` |
| `/api/onetouch/execute` | `intent` |
| `/api/onetouch/seal` | `draft_id` |
| `/api/dragon/chat` | `message` |
| `/api/export/web` | `draft_id` |
| `/api/publish/web` | `draft_id` |

### Erros Trilíngues

| Lang | Exemplo |
|------|---------|
| PT | `session_id é obrigatório para guardar` |
| DE | `session_id ist erforderlich zum Speichern` |
| EN | `session_id is required for saving` |

### Regra Constitucional

```
Nenhum endpoint novo sobe sem contrato.
contracts/*.json é obrigatório antes do nginx reload.
W-CIA-001 valida. W-GATE-001 bloqueia. Humano decide.
```

---

## 28. CIA Pre-Flight Check — Sistema de Contenção #2 · 19 Mar 2026

**Status:** LIVE no GEN7 Desktop
**Princípio:** "Validar ANTES de chamar → erro nunca chega."

Sistema de Contenção #2 — Elimina Loop 3 (erro silencioso no frontend).

### Problema Resolvido

```
ANTES: Clicar "Selar" sem documento → API call → 500 → "unexpected token"
AGORA: Clicar "Selar" sem documento → Pre-Flight → Toast amigável → Sem API call
```

### Arquitectura

```javascript
// CIA.CONTRACTS — regras por endpoint
const CIA = {
    CONTRACTS: {
        '/api/onetouch/execute': { required: ['intent'], ... },
        '/api/seal': { required: ['draft_id'], ... },
        '/api/export/web': { required: ['draft_id'], ... },
        '/api/publish/web': { required: ['draft_id'], ... },
    },

    preflight(endpoint, payload, lang) { ... },
    showPreflightError(error, field) { ... }
};
```

### Funções Protegidas (4)

| Função | Validação |
|--------|-----------|
| `executeOneTouch()` | `intent` não vazio |
| `sealCanvasToLedger()` | `session_id` existe |
| `exportWebStandalone()` | `session_id` + `content` |
| `publishToWINDI()` | `session_id` + `content` |

### Toast Trilíngue

| Lang | Exemplo |
|------|---------|
| PT | `Nenhum documento para selar` |
| DE | `Kein Dokument zum Versiegeln` |
| EN | `No document to seal` |

### CSS

```css
.cia-preflight-toast { /* Toast centrado, animado, NOIR/KLAR */ }
```

---

## 29. W-KEYS-002 — Technical Explainer Page · 19 Mar 2026

**Status:** LIVE
**URL:** `windi-domain.com/keys/`
**Path:** `/opt/windi/keys-pricing/index.html`

### Princípio

> "O preço é o final do convencimento. Primeiro, explica o valor."

### Estrutura da Página

| Secção | Conteúdo |
|--------|----------|
| **Hero** | "A Key that certifies, not just authenticates" |
| **Conceito** | 3 pilares: Constitutional Governance · Forensic Seal · Ledger Receipt |
| **Arquitectura** | Pipeline visual de 6 etapas (User → Key → Dragon → Process → Seal → Receipt) |
| **Pricing** | 4 tiers NO FINAL (SEED €0 · NODAL €49 · SOVEREIGN €999 · ORACLE) |

### i18n

- 52 strings trilíngues via `data-i18n` attribute
- Auto-detect: `localStorage('windi-lang')` → browser → fallback 'en'
- Sync com outras páginas WINDI

### Theme

- NOIR/KLAR toggle funcional
- CSS vars para ambos os temas
- localStorage sync: `windi-theme`

### Backup

Versão anterior (só pricing) preservada: `index-pricing-only-backup.html`

---

## 30. W-NGINX-001 — Nginx Auto-Register · 19 Mar 2026

**Status:** LIVE
**Path:** `/opt/windi/contracts/nginx_audit.py`

### Função

Sistema de Contenção #3 que elimina **Loop 1**: "Criei endpoint mas esqueci nginx".

### Capacidades

| Comando | Função |
|---------|--------|
| `python3 nginx_audit.py` | Relatório completo |
| `python3 nginx_audit.py --generate` | Gera snippets nginx para rotas faltantes |
| `python3 nginx_audit.py --save` | Guarda relatório JSON |

### Métricas Actuais

```
Flask Routes:     302
Nginx Locations:   64
Missing:            0 (cobertura total)
Exit Code:          0 = PASS, 1 = FAIL
```

### Pre-Commit Hook

```bash
# Instalar
ln -sf /opt/windi/contracts/nginx_hook.sh /opt/windi/.git/hooks/pre-commit

# Ou executar manualmente
/opt/windi/contracts/nginx_hook.sh
```

### Directórios Scanned

- `/opt/windi/agents/constitutional-agent`
- `/opt/windi/desktop-gen7`
- `/opt/windi/ledger`
- `/opt/windi/dispatch`
- `/opt/windi/wallet`
- `/opt/windi/agent-palette`
- `/opt/windi/export-engine`
- `/opt/windi/verify-public`
- `/opt/windi/communique-engine`
- `/opt/windi/pioneer`

### Princípio

> "Nenhuma rota Flask vive sozinha. Nginx conhece todas."

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*

---

## 23. WINDI Verify v2 — Estado completo (18 Mar 2026)

### Arquitectura Multi-Reader (3 modos)

| Modo | Serviço | Garantia | Ledger |
|------|---------|----------|--------|
| 1 — WINDI Verify | `/verify-public/` `:8114` | WINDI GARANTE — I11 | Sim |
| 2 — Hash Inspector | `/verify-public/web/hash-inspector.html` | Prova matemática local | Não |
| 3 — QR Decoder | `/verify-public/web/qr-decoder.html` | WINDI interpreta | Não |

**Filosofia constitucional:** LER → ENTENDER → GARANTIR
**Fronteira irremediável:** Modo 1 garante. Modo 2 prova. Modo 3 interpreta. NUNCA misturar.

---

### W-VERIFY-001 — Agent Interpretador

- **Porto:** `:8091` (extensão do Sandbox Core — constellation pattern)
- **Prefixo:** `/verify-agent/`
- **Endpoints:**
  - `GET  /verify-agent/health`
  - `POST /verify-agent/interpret` — núcleo trilíngue PT/DE/EN
  - `POST /verify-agent/detect-qr-type` — router determinístico, zero IA
  - `GET  /verify-agent/patterns` — 8 padrões QR conhecidos
- **Blueprint:** `/opt/windi/agents/constitutional-agent/blueprints/w_verify_001_blueprint.py`
- **I9 enforced by design:** nunca calcula, nunca escreve no Ledger, nunca decide

---

### Modo 2 — Hash Inspector

- **Ficheiro:** `/opt/windi/verify-public/web/hash-inspector.html`
- **Motor:** `crypto.subtle.digest()` — 100% browser, zero rede
- **OCR:** `Tesseract.js` via CDN `cdn.jsdelivr.net` — extrai hash de foto
- **Suporta:** SHA-256 (64 hex) + SHA-512 (128 hex)
- **3 tabs:** Arrastar ficheiro / Foto+OCR / Colar hash manual
- **Fallback local:** funciona sem W-VERIFY-001 disponível

---

### Modo 3 — QR Decoder Universal

- **Ficheiro:** `/opt/windi/verify-public/web/qr-decoder.html`
- **Motor:** `jsQR` via CDN `cdn.jsdelivr.net`
- **I18N:** PT/DE/EN completo — seletor no header, auto-detect `navigator.language`
- **Commit I18N:** `bb0856d` — 28 strings × 3 idiomas, §11.2 compliant
- **8 padrões QR:**
  - `windi_doc` — QR WINDI → redireciona para Modo 1
  - `nfe_br` — Nota Fiscal Eletrônica (chave 44 dígitos)
  - `pix_br` — PIX (EMV-QR BACEN)
  - `gov_de_elster` — Documento fiscal alemão
  - `eu_covid` — EU Digital COVID Certificate (HC1)
  - `url_generic` — URL qualquer
  - `vcard` — Cartão de contacto
  - `wifi` — Configuração Wi-Fi
- **Router:** determinístico, regex pura — auditável, zero IA
- **Fricção intencional:** bloco âmbar para documentos não-WINDI

---

### Landing Unificada

- **URL:** `https://windi-domain.com/verify-public/web/`
- **Ficheiro:** `/opt/windi/verify-public/web/index.html`
- **Commit:** `7d4b6f9`
- **Estrutura:**
  ```
  Hero — 3 linhas + confidence pills (HIGH/MEDIUM/LOW)
  3 Cards — teal / blue / amber
  Philosophy Strip — "Quando as pessoas começam a verificar..."
  Constitution Table — faz / NÃO faz / Ledger
  ```
- **I18N:** PT/DE/EN, auto-detect, seletor no header

---

### PWA — Progressive Web App

- **Commit:** `040f704`
- **Status:** LIVE — instalável sem App Store
- **Ficheiros em** `/opt/windi/verify-public/web/`:
  ```
  manifest.json          — identidade PWA
  sw.js                  — Service Worker cache-first
  offline.html           — fallback trilíngue
  icons/
    icon-72.png   (2.5 KB)
    icon-96.png   (3.4 KB)
    icon-128.png  (4.7 KB)
    icon-192.png  (6.9 KB)
    icon-512.png  (19.8 KB)
    icon-maskable-192.png (4.6 KB)
    icon-maskable-512.png (12.3 KB)
  ```
- **Instalação:**
  - Android: banner automático após 3s (BeforeInstallPrompt)
  - iOS: instrução manual "Partilhar → Adicionar ao ecrã"
  - Desktop: ícone na barra de endereço Chrome/Edge
- **Offline:** Modo 2 (Hash) + Modo 3 (QR decode) funcionam sem rede
- **SW scope:** `/verify-public/` — não interfere com Ledger `:8101`
- **Estratégia cache:**
  - Assets estáticos → cache-first + revalidação silenciosa
  - APIs WINDI → network-first com fallback
  - CDNs externos → sempre network (jsQR, Tesseract)

---

### Roadmap Verify

| Fase | Estado | Descrição |
|------|--------|-----------|
| Modo 1 | ✅ SEALED | Ledger `:8114`, I11, 56.567+ receipts |
| Modo 2 | ✅ LIVE | Hash Inspector, OCR, crypto.subtle |
| Modo 3 | ✅ LIVE | QR Decoder, 8 padrões, I18N |
| W-VERIFY-001 | ✅ LIVE | Agent interpretador, `:8091` |
| Landing | ✅ LIVE | Unificada, trilíngue |
| PWA | ✅ LIVE | Instalável Android/iOS/Desktop |
| Capacitor | ⏳ FUTURO | App Store + Play Store — quando tração |

---

### URLs de produção

```
Landing:   https://windi-domain.com/verify-public/web/
Modo 1:    https://windi-domain.com/verify-public/
Modo 2:    https://windi-domain.com/verify-public/web/hash-inspector.html
Modo 3:    https://windi-domain.com/verify-public/web/qr-decoder.html
Agent:     http://localhost:8091/verify-agent/health
Manifest:  https://windi-domain.com/verify-public/web/manifest.json
SW:        https://windi-domain.com/verify-public/web/sw.js
```

---

*Sessão 18 Mar 2026 — WINDI Verify v2 completo*
*"É possível ler SHA por foto?" → PWA instalável em 8 horas*
