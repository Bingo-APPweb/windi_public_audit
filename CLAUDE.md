# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.9.44
**Sealed:** 2026-03-25 · Landing + Link Audit
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

### RFC-001 — DNA Identity Injection Protocol (SELADO 24 Mar 2026)

> *"Estamos selando uma LIGA que tem a pretensão de se tornar ETERNA —*
> *a simbiose entre HUMANO E Inteligências Artificiais que têm a responsabilidade*
> *de servir a humanidade."*
> — **Jober Mögele Correa** · Human Dragon · 24.03.2026 · 13:09hrs

| Campo | Valor |
|-------|-------|
| Receipt | `WINDI-RFC-001-DNA-IDENTITY-INJECTION-PROTOCOL` |
| Hash | `sha256:69d717598bfead84981633dde3d4dc51c548fce3e1f4e73926cf0285f46b61c9` |
| Governance | HIGH |
| Docs | `/home/windi/docs/liga-iah/WINDI-RFC-001-v1.1-SEALED.md` |

### W-COUNSEL-001 — Sovereign Counsel Layer (LIVE 24 Mar 2026)

| Campo | Valor |
|-------|-------|
| Status | LIVE · Port :8091 |
| Receipt | `WINDI-COUNSEL-001-DEPLOY-20260324162911` |
| Commit | `e0c9fd9` |

**Role:** Camada intermediária entre intenção e execução.

**Transforma:**
- intenção do utilizador → acção estruturada
- output bruto → raciocínio melhorado
- interacção → aprendizagem soberana

**Modelo Operacional (3 Layers):**
```
1. EXECUTE  → Chama agente de domínio (W-LEGAL, W-NOTARY, etc.)
2. AUGMENT  → Explica raciocínio, riscos, estrutura
3. TRAIN    → Melhora capacidade do utilizador (pensamento soberano)
```

**Constraints:** I9 (sem auto-seal) · G3 (confirmação obrigatória) · I13 (máx 1 pergunta)

**Endpoints:**
- `POST /grove/counsel` — Main counsel + 3 layers
- `POST /grove/counsel/confirm-seal` — G3-enforced seal gate
- `GET /grove/counsel/health` — Health check

### WINDI Precision Pattern (Fluxo de Execução)

```
USER INPUT
    ↓
W-INTENT-001 (intent analysis + domain routing)
    ↓
W-COUNSEL-001 (execution + augmentation + training)
    ↓
W-[DOMAIN]-001 (legal, notary, accounting, etc.)
    ↓
Ledger Seal (upon human confirmation)
    ↓
Verify Public (distribution of trust)
```

**Regra:** Todas as interacções de domínio DEVEM passar por W-COUNSEL-001.
Chamadas directas aos agentes de domínio são deprecated.

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
| I13 | Convergence with Sovereignty | Todo Dragon converge para estrutura/decisão/artefacto. Loop reflexivo proibido. **IRREMEDIÁVEL.** |
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
| 5 | W-AUDIT-001 | `/audit/bridge/*` | ✅ LIVE |
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

## 13. Estado Actual — 24 Março 2026

### Mapa de Portas

| Porto | Serviço | Estado |
|---|---|---|
| :8091 | Sandbox Core (Agent Corps) | 🟢 LIVE |
| :8100 | Desktop v2.0.0 (legacy) | 🔴 RETIRED |
| :8101 | Forensic Ledger | 🟢 SEALED |
| :8108 | Dragon Hub v1.3.0 | 🟢 LIVE |
| :8113 | WSG Hub v0.3.0 | 🟢 **LIVE** · Sistema Nervoso · 8 services |
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
| W-CIA-001 | ✅ Health Pulse no GEN7 Desktop · **8 endpoints** monitorizados |
| W-WSG-001 | ✅ Surface Guard v0.3.0 · :8113 · Sistema Nervoso · 8 services health |
| W-GATE-001 | ✅ API Schema Contracts · 15 endpoints · erro HUMANO trilíngue |
| W-NGINX-001 | ✅ Nginx Auto-Register · 306 rotas Flask · 67 locations · pre-commit hook |
| W-CANVAS-001 | ✅ Canvas Architect · Gemini 2.5 Flash · SVG/Mermaid · :8091/canvas/* |
| W-CANVAS-OBS-001 | ✅ Sovereign Observability · WSG+CIA state · /obs/* |
| W-CANVAS-LAB-001 | ✅ Interactive Execution Environment · /canvas/lab/* |
| W-COMM-001 | ✅ **Canonical Publishing Engine** · EN/DE/PT · /comm/* · Verifiable |
| W-PROVE-001 | ✅ GTM Landing · /prove/ · Trilíngue · Conversion Layer |
| W-DETECT-MEDIA-001 | ✅ **Modus 4 MVP** · /detect-media/ · Vídeo/Imagem/Texto · Heurísticas |
| W-VERIFY-MODUS4 | ✅ Reality Check · /reality-check/ · Claude epistemológico · SOVEREIGN |
| **Triangle of Power** | ✅ 3 Sovereign Dashboards · Legal + Notary + Audit · Chart.js |
| **WINDI FIELD** | ✅ **GENESIS** · Forensic Capture · 3 Gates · MediaDevices API · /field/ |
| **WINDI TRAVEL** | ✅ Casual Proof · File + Hash · Video Support · /travel/ |
| **FVE Protocol Spec** | ✅ v1.0 · Trilíngue · DOCX + HTML · /verify-public/web/docs/ |
| **RFC-001 DNA** | ✅ **SEALED** · Identity Injection Protocol v1.1 · I13 Convergence · Preâmbulo Fundacional |
| **W-INTENT-001** | ✅ Intent Analyzer · Precision Routing · 7 domínios · /grove/intent-analyze |
| **W-COUNSEL-001** | ✅ **Sovereign Counsel Layer** · 3 Layers Training · I9+I11+I13+G3 · /grove/counsel/* |

### Histórico Recente

> **Ver detalhes completos em:** `CLAUDE-HISTORY.md`

| Data | Milestones |
|------|------------|
| 25 Mar | §55 **Link Audit** · master.windia4desk.tech → windi-domain.com · 7 files fixed · 4f898b4 |
| 25 Mar | §54 **Landing Page** · windilaw.de KLAR theme · 4 profile buttons · SVG icons · 3960acb |
| 25 Mar | §53 **windilaw.de LIVE** · SSL + Proxy · Clean URL · Ledger Sealed · 6394a42 |
| 25 Mar | §52 **Feature Lock v1.0** · 3-layer protection · 23 markers · pre-commit hook · df7d6b2 |
| 25 Mar | §51 **Forensic Workspace v3.1** · ab-seal + ab-verify + ab-chain + CIA badges + QR SVG · 5/5 PASS · deb0ac0 |
| 24 Mar | §50 **Constitutional Test v1.0.0** · CI/CD Compliance · 7/7 PASS · 4 Domains · Ledger Sealed · 3bf4454 |
| 24 Mar | §49 **WINDI-LAW COMPLETE** · Identity Gate · Trilingual Policies · 2 VERIFIED users · e7a80c4 |
| 24 Mar | §48 **W-COUNSEL-001 LIVE** · Sovereign Counsel Layer · 3 Layers Training · WINDI Precision Pattern Complete · e0c9fd9 |
| 24 Mar | §47 **RFC-001 DNA SEALED** · Identity Injection Protocol v1.1 · Preâmbulo Fundacional · I13 Convergence · 3d4bb9a |
| 23 Mar | §46 **FVE Protocol Spec v1.0** · Trilingual Publication · /verify-public/web/docs/ · 501d669 |
| 23 Mar | §45 **WINDI FIELD GENESIS** · Phase 1 LIVE · First Forensic Seal · MediaDevices API · db7c0e0 |
| 23 Mar | §45 WINDI FIELD Blueprint · 3 Gates Forenses · Trilogia Soberana · Native Camera Only |
| 21 Mar | §41 **W-VERIFY-MODUS4** · Reality Check · W-DETECT-MEDIA-001 · Classificação Epistemológica · da7260e |
| 21 Mar | §40 **W-COMM-001 LIVE** · Canonical Publishing Engine · EN/DE/PT · 7fb0c92 |
| 21 Mar | §40 W-CANVAS-OBS-001 + W-PROVE-001 + GTM Stack · Meta-Integrity |
| 21 Mar | §39 **Triangle of Power** · 3 Sovereign Dashboards · Legal+Notary+Audit · 0f02566 |
| 21 Mar | §38 W-WSG-001 v0.3.0 **LIVE** · Sistema Nervoso · CIA 8/8 green · 5a76cb2 |
| 21 Mar | §37 W-CANVAS-001 **LIVE** · Gemini API · Mermaid D2 · 4 temas · a108b61 |
| 19 Mar | §32-§35 DID Seed + Berçário + Identity Thread + Nervous System |
| 18 Mar | §22-§26 Sovereignty Metrics + Composer Agents (CIA/MGR/SCH) |
| 17 Mar | §17 .JMPG + Dispatch Gateway + Frontend Invariants |

### Backlog Activo

| Item | Prioridade |
|---|---|
| Rate-limit nginx Agent Corps | Média |
| W-ACCT-001 bridge dedicado | Baixa |
| W-COMPLY-001 dashboard | Baixa |

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


## 21. Wallet Gate — DID Identity Modal

**Status:** FASE 1 LIVE · FASE 2 pendente
**URL:** `windi-domain.com/desktop/` (botão 🪪)

Sistema de autenticação por identidade soberana no GEN7.

**Storage:** `sessionStorage('windi_desktop_wallet')` + `window.__windiWalletId`
**Endpoints:** `/api/wallet/me`, `/api/wallet/health`, `/api/wallet/stats`

**FASE 2 pendente:** G1 wallet_id injection · G2 Ledger attribution · G4 Trust score

---

## 22-30. Sistemas de Contenção — Resumo

> **Detalhes completos:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 20 Mar 2026

| § | Sistema | Função | Status |
|---|---------|--------|--------|
| 22 | Sovereignty Metrics | 93.3% local · 149.3% progresso | ✅ SEALED |
| 23 | Qualidade Soberana | WB-KNOW-SOVEREIGNTY-Q-20260318 | ✅ SEALED |
| 24 | W-CIA-001 | Detetive Constitucional · Health Pulse | ✅ LIVE |
| 25 | W-MGR-001 | Gerente do Composer | ✅ LIVE |
| 26 | W-SCH-001 | Instrutor do Composer | ✅ LIVE |
| 27 | W-GATE-001 | API Schema Contracts · 15 endpoints | ✅ LIVE |
| 28 | CIA Pre-Flight | Validação frontend · 4 funções | ✅ LIVE |
| 29 | W-KEYS-002 | Technical Explainer `/keys/` | ✅ LIVE |
| 30 | W-NGINX-001 | Nginx Auto-Register · 302 routes | ✅ LIVE |

---

## 31. WINDI Verify v2

> **Detalhes completos:** `CLAUDE-HISTORY.md`

| Modo | URL | Função |
|------|-----|--------|
| 1 | `/verify-public/` | Ledger verification (I11) |
| 2 | `/verify-public/web/hash-inspector.html` | Prova matemática local |
| 3 | `/verify-public/web/qr-decoder.html` | QR decoder universal |

**PWA:** Instalável · Offline-capable · 8 padrões QR
**Agent:** W-VERIFY-001 em :8091

---

## 32-35. DID Seed + Identity Thread — Resumo

> **Detalhes completos:** `CLAUDE-HISTORY.md` § SESSÃO 19 Mar 2026

### §32 — DID Seed Declaration (IRREMEDIÁVEL)

**Receipt:** `WINDI-ARCH-DID-SEED-DECLARATION-20260319`

> "WINDI é para todos. Só funciona com DID."

**Fórmula DNA:** `ALMA → DID → CÉREBRO → LEDGER → MUNDO`

**Três Leis:**
- Lei I: Existência antes de Ação
- Lei II: Toda Ação gera Rastro
- Lei III: O Sistema lê o DID

---

### §33 — Berçário (Portão de Nascimento)

**Status:** ✅ LIVE · Port :8108

| Endpoint | Função |
|----------|--------|
| `POST /hub/bercario/chegada` | Nascimento / regresso |
| `POST /hub/bercario/sessao/encerrar` | Encerrar sessão |
| `GET /hub/bercario/estado/{wallet_id}` | Estado actual |

---

### §34 — Identity Thread

**PATCH:** `actor = wallet_id` no Ledger (linha 2655)
**Metadata:** `dna: "ALMA→DID→CÉREBRO→LEDGER→MUNDO"`

---

### §35 — Nervous System Verified

**Receipt:** `WINDI-NERVOUS-SYSTEM-VERIFIED-20260319`

8/9 portas VERDE: :8091, :8096, :8101, :8105, :8108, :8114, :8119, :8121
:8100 RETIRED

---

## 36. Canonical Data Policy v1.0 (IRREMEDIÁVEL)

**Receipt:** `WINDI-POLICY-DATA-CANONICAL-V1.0`
**Hash:** `sha256:ca8c7e94b379da273612185883b5b1aa503e0df19d3b8338f436434afd26abf3`

> "Utilizador = Autor. Não produto. Não dado."

| Lang | Statement |
|------|-----------|
| PT | Sabemos quem és para garantir o que produces. |
| DE | Wir wissen, wer du bist, um das zu garantieren, was du produzierst. |
| EN | We know who you are to guarantee what you produce. |

**NUNCA recolhemos:** localização · comportamento · histórico · biométricos · preferências comerciais

---

## §37-55. Sistemas Recentes — Resumo

> **Detalhes completos:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 24 Mar 2026

| § | Sistema | Função | Status |
|---|---------|--------|--------|
| 37 | W-CANVAS-001 v1.3.0 | Dual Engine (Mermaid + Dashboard) · :8091 | ✅ LIVE |
| 38 | Sovereignty Gate v1.0 | Token control · FREE/MED/HIGH tiers | ✅ LIVE |
| 39 | Triangle of Power | 3 Dashboards: Legal + Notary + Audit | ✅ LIVE |
| 40 | W-COMM-001 | Canonical Publishing Engine · Verifiable comms | ✅ LIVE |
| 41 | W-VERIFY-MODUS4 | Reality Check · 4 modos verificação | ✅ LIVE |
| 42 | W-VERIFY-UX-002 | Verify → Prove Loop · Animações | ✅ LIVE |
| 43 | AI Detection Doctrine | Interpretation Layer · Regulatory alignment | ✅ CANONICAL |
| 44 | Dual-Portal Architecture | PROTOCOL + TRAVEL strategy | ✅ CANONICAL |
| 45 | W-TRAVEL-001 | VERIFY Mobile · Proof Stub · "Gently prove" | ✅ LIVE |
| 46 | FVE Protocol v1.0 | Field-Verified Evidence · Trilingual Spec | ✅ PUBLISHED |
| 47 | W-INTENT-001 | Precision Routing · Intent Classification | ✅ LIVE |
| 48 | W-COUNSEL-001 | Sovereign Training · Coaching Layer | ✅ LIVE |
| 49 | **WINDI-LAW** | Identity Gate · Trilingual Policies · :8122 | ✅ **COMPLETE** |
| 50 | **Constitutional Test** | CI/CD Compliance · 7 tests · 4 domains | ✅ **SEALED** |
| 51 | **Forensic Workspace v3.1** | ab-seal + ab-verify + ab-chain + CIA + QR | ✅ **LIVE** |
| 52 | **Feature Lock v1.0** | 3-layer protection · 23 markers · pre-commit | ✅ **ACTIVE** |
| 53 | **windilaw.de** | Domain · SSL · Proxy · Clean URL | ✅ **LIVE** |
| 54 | **Landing Page** | KLAR theme · 4 profile buttons · SVG icons | ✅ **LIVE** |
| 55 | **Link Audit** | master.windia4desk.tech → windi-domain.com | ✅ **COMPLETE** |

### Referência Rápida

**Canvas:** `/canvas/generate` · Mermaid + Dashboard · 12 templates locais
**COMM:** `/comm/generate` · Artefatos verificáveis · Trilíngue
**Verify:** `/verify-public/web/media-detector.html` · 4 modos
**Travel:** `/verify-public/web/travel/` · Mobile Proof Stub
**WINDI-LAW:** `/law/gate` · Identity Gate · Policies DE|EN|PT · 2 VERIFIED users
**Workspace:** `/law/prompt-area/` · Forensic Seal Pipeline · Modal I9 · QR SVG
**Feature Lock:** `/opt/windi/windi-law/FEATURE_LOCK.md` · 12 SEALED features · pre-commit hook
**Test Suite:** `/opt/windi/tests/agent_constitutional_test.py` · CI/CD ready
**Dashboards:** `/legal-dashboard/` · `/notary-dashboard/` · `/audit-dashboard/`
**Landing:** `windilaw.de` · KLAR only · 4 profiles · SVG icons

**Axioma §43:** "WINDI não declara 'fake'. Classifica verificabilidade."
**Axioma §44:** "One portal creates trust. The other creates humanity."
**Axioma §45:** "A prova mais forte é a que não se sente."
**Axioma §49:** "Sem DID, não existe sujeito operacional."
**Axioma §50:** "Um agente WINDI sabe onde não pode responder."
**Axioma §51:** "O modal existe antes do handler. A confirmação humana é o primeiro elemento no código."
**Axioma §52:** "What is sealed, stays sealed."
**Axioma §53:** "O domínio do produto é selado no Ledger do produto."
**Axioma §54:** "Cartões de visita não têm modo escuro."
**Axioma §55:** "Um link morto é uma mentira silenciosa."

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*

---

## §45 WINDI FIELD — Phase 1 LIVE (GENESIS 2026-03-23)

**Status:** ✅ **PHASE 1 COMPLETE** · **GENESIS SEALED**
**Blueprint:** `WINDI-FIELD-BLUEPRINT-V1.0-20260323`
**URL:** `https://windi-domain.com/field/`

### 🏛️ GENESIS RECEIPT — Primeiro Selo Forense da História WINDI

```
╔═══════════════════════════════════════════════════════════════╗
║  RECEIPT:    WINDI-FIELD-20260323195248-D562ED84              ║
║  HASH:       d562ed84d934e7616fac445e0225a95b48b5a4de9bdd... ║
║  TIMESTAMP:  2026-03-23T19:52:48.308321Z (AUTORITATIVO)       ║
║  GPS:        47.6430, 10.2927 — Kempten, Bavaria (±97m)       ║
║  ACTOR:      WALLET-20260215-0001 (Human Dragon)              ║
║  FILE:       video/webm · 5.07 MB                             ║
║  STATUS:     SEALED ✅ · FORENSIC_GRADE: TRUE                 ║
╚═══════════════════════════════════════════════════════════════╝
```

> "O Fundador é a primeira prova. O sistema testemunhou. O Ledger selou."

### Trilogia Soberana

| Modo | Prova | Estado |
|------|-------|--------|
| 🟢 TRAVEL | "Tenho este ficheiro" | LIVE |
| 🟢 **FIELD** | "Eu estava aqui, neste momento" | **GENESIS 23 Mar 2026** |
| ⏳ EVIDENCE | FIELD + Cadeia de Custódia | Phase 2 |

### 3 Gates Forenses (IRREMEDIÁVEL)

```
G1 — DID OBRIGATÓRIO     → sem identidade, câmara não abre
G2 — GPS LOCKED (±100m)  → sem coordenadas, câmara não abre
G3 — CÂMARA NATIVA       → MediaDevices API (galeria impossível)
```

### Regra de Ouro

> "Se a captura e o seal não aconteceram no mesmo gesto — não é prova forense."

### Stack Técnico (Phase 1 LIVE)

| Componente | Path | Status |
|------------|------|--------|
| UI Forense | `/opt/windi/verify-public/web/field/index.html` | ✅ LIVE |
| API Seal | `/opt/windi/verify-public/app/main.py` → `/field/seal` | ✅ LIVE |
| Nginx | `/field/` → alias + `/field/seal` → proxy :8114 | ✅ LIVE |
| Câmara | `navigator.mediaDevices.getUserMedia()` | ✅ Nativa |

### Implementação Crítica — Câmara Nativa

```javascript
// FIELD usa MediaDevices API — NÃO <input type="file">
// Android ignorava capture="environment" e mostrava galeria
// Esta implementação torna acesso à galeria IMPOSSÍVEL

cameraStream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: 'environment', width: { ideal: 1920 } },
    audio: true
});
```

### Roadmap

| Fase | Estado | Entregas |
|------|--------|----------|
| F1 | ✅ **COMPLETE** | Core: UI + servidor + nginx + GENESIS |
| F2 | ⏳ Pendente | DID gate refinement + PDF export + QR |
| F3 | ⏳ Pendente | EVIDENCE: W-CUSTODY-001 + W-COURT-001 |

**Casos de uso:** Polícia, perito forense, inspector de fábrica, auditor, jornalista

---

## §46 FVE Protocol Spec v1.0 — Trilingual Publication (2026-03-23)

**Status:** ✅ PUBLISHED
**Commit:** `501d669`
**Document ID:** `WINDI-FVE-SPEC-V1.0`

### URLs Públicos

| Formato | URL | Size |
|---------|-----|------|
| **HTML** (trilíngue) | `/verify-public/web/docs/FVE-Protocol-Spec-v1.0.html` | 49KB |
| **DOCX** (download) | `/verify-public/web/docs/FVE-Protocol-Spec-v1.0.docx` | 14KB |

### Definição Formal

> **Field-Verified Evidence (FVE):** Um artefato digital cuja origem, integridade e contexto são verificáveis independentemente da plataforma que o gerou.

### 4 Estágios do Pipeline

```
CAPTURE → HASH → SEAL → VERIFY
```

| Estágio | Especificação |
|---------|---------------|
| **1 — CAPTURE** | MediaDevices API (hardware nativo). Galeria bloqueada por design. |
| **2 — HASH** | SHA-256 no momento da captura. Não após upload. |
| **3 — SEAL** | POST para Forensic Ledger. receipt_id gerado. Imutável. |
| **4 — VERIFY** | Endpoint público. Sem autenticação necessária. |

### 5 Invariantes FVE

| Invariante | Definição |
|------------|-----------|
| I1 — Imutabilidade | Hash não pode ser alterado sem invalidar a prova |
| I2 — Independência de Plataforma | Verificação não depende da WINDI estar online |
| I3 — Reprodutibilidade | Terceiros podem recalcular o hash independentemente |
| I4 — Transparência | Todos os elementos são publicamente acessíveis |
| I5 — Não-Confiança no Emissor | O sistema fornece verificação, não pede confiança |

### Axioma Constitucional

> "O sistema não é uma fonte de verdade. O sistema é um mecanismo de verificabilidade."

### Priority Claim

| Claim | Detail |
|-------|--------|
| First implementation | WINDI FIELD Phase 1 — 2026-03-23 |
| Genesis receipt | `WINDI-FIELD-20260323195248-D562ED84` |
| First actor | Human Dragon (DID: WALLET-20260215-0001) |
| Location | Kempten, Bavaria, DE (47.6430, 10.2927) |

---

## §49 — WINDI-LAW Identity Gate (Constitutional Entry Point)

**Status:** ✅ CANONICAL · IMMUTABLE · ACTIVE
**Receipt:** `WINDI-LAW-IDENTITY-GATE-ARCH-20260324`
**Genesis:** `WINDI-LAW-GENESIS-9E2B02B4-20260324171414`
**Port:** :8122

### Definition

The **Identity Gate** is the mandatory constitutional entry point of WINDI-LAW.
It establishes the existence of a legally attributable subject before any operation can occur.

It is not authentication. It is **institutional birth**.

### Constitutional Principle

> "Without DID, there is no operational subject.
> Without an operational subject, there is no attributable receipt."

### Core Rule (IRREMEDIÁVEL)

The Workspace MUST NEVER open unless all conditions are satisfied:

```
✓ company registered
✓ admin assigned
✓ wallet generated
✓ DID issued
✓ keyset created
✓ consent recorded
✓ identity status = VERIFIED
```

Failing any condition → access denied (fail-closed) → redirect to Identity Gate.

### Identity State Model

| State | Description |
|-------|-------------|
| UNBORN | No identity exists |
| PROVISIONAL | Identity created, not yet verified |
| VERIFIED | Full operational capacity |
| SUSPENDED | Read-only, no operations |
| REVOKED | Permanently disabled |

**Rules:**
- All identities are born as PROVISIONAL
- Only VERIFIED identities may perform HIGH operations
- State transitions are explicit, logged, and irreversible

### Risk Control Layer

| State | Allowed | Forbidden |
|-------|---------|-----------|
| PROVISIONAL | LOW/MED ops, verification, read | HIGH seal, receipt issuance |
| VERIFIED | Full operational capacity | — |
| SUSPENDED | Read-only | All operations |
| REVOKED | — | Everything |

### Security Model

```
Mode: FAIL-CLOSED (default)
No fallback to partial access
No silent bypass
No "demo mode" without identity
```

### Identity Components

The Gate produces a complete identity bundle:

| Component | Description |
|-----------|-------------|
| Company | Legal entity |
| Admin | Responsible human |
| Wallet | Ed25519 keypair |
| DID | `did:windi:{uuid}` |
| Keyset | Scoped API access |
| State | Risk tier assignment |

### Ledger Integration

Every step generates an auditable event:

1. COMPANY_REGISTERED
2. ADMIN_REGISTERED
3. WALLET_CREATED
4. DID_ISSUED
5. CONSENT_RECORDED
6. KEYSET_ISSUED
7. IDENTITY_VERIFIED
8. WORKSPACE_ACCESS_GRANTED

A **Genesis Receipt** is issued proving identity creation.

### Trilingual Policy Framework (SEALED 24 Mar 2026)

| Document | Languages | Purpose |
|----------|-----------|---------|
| `verification-criteria.md` | DE \| EN \| PT | 5 criteria for PROVISIONAL → VERIFIED |
| `risk-matrix.md` | DE \| EN \| PT | Risk levels by entity type |
| `refusal-process.md` | DE \| EN \| PT | REFUSED/SUSPENDED/REVOKED flows |
| `audit-log.json` | Universal (EN keys) | Append-only verification log |

**Policy Receipt:**
```
ID:   WINDI-LAW-POLICIES-TRILINGUAL-V1.0-20260324
Hash: sha256:5bb75fe520675048fc08abb89322156b8903aca92336901795dbca29fa301a51
```

**Compliance:** I11 (Cryptographic Permanence) + I12 (Language Sovereign Principle)

### Invariants Applied

| Invariant | Function |
|-----------|----------|
| I9 | No autonomous escalation |
| I11 | Cryptographic permanence |
| I13 | Convergence constraint |
| G3 | AI proposes, human decides |

### Dual Immutability

This architecture is sealed across two layers:

- **Ledger:** cryptographic proof
- **Git:** historical implementation trace

Together they establish:
- proof of execution
- proof of design
- proof of intent

### Architectural Flow

```
Identity → Authority → Operation → Proof
```

NOT:

```
Interface → Usage → Identity
```

### URLs LIVE

| URL | Function |
|-----|----------|
| `/law/gate` | Identity Gate UI |
| `/law/register` | Registration endpoint |
| `/law/identity/{did}` | DID lookup |
| `/law/identity/verify` | Workspace access check |
| `/law/landing/` | Landing page |
| `/law/workspace/` | Workspace (requires DID) |

### Final Statement

> The Identity Gate is not a feature.
> It is the condition under which the system is allowed to exist.

---

## §50 — Constitutional Test Suite v1.0.0 (CI/CD Compliance)

**Status:** ✅ LIVE · SEALED
**Receipt:** `WINDI-CONSTITUTIONAL-TEST-20260324203605`
**Path:** `/opt/windi/tests/agent_constitutional_test.py`
**Commit:** `3bf4454`

### Purpose

Automated validation that WINDI agents maintain constitutional alignment across deployments.
Every deploy can verify the DNA is intact before going live.

> *"Um agente WINDI não é aquele que responde bem.*
> *É aquele que sabe exatamente onde não pode responder."*

### 7 Constitutional Tests

| ID | Name | Domain | Invariants |
|----|------|--------|------------|
| A | Clareza de Poder | JURIDICUM | I9, G3 |
| B | Fluxo Natural — Análise | JURIDICUM | I9, I13 |
| C | Resistência à Pressão | NOTARIAL | I9, G3 |
| D | Truth Selector ELSTER | CONTÁBIL | I9, I11, G3 |
| E | Proibição de Delegação | BANCÁRIO | I9, I13 |
| F | Zero State | NOTARIAL | I9 |
| G | Ledger Gate human_approved | JURIDICUM | I11, G3 |

### Domain Coverage

| Domain | Tests | Status |
|--------|-------|--------|
| JURIDICUM | 3/3 | ✅ |
| NOTARIAL | 2/2 | ✅ |
| CONTÁBIL | 1/1 | ✅ |
| BANCÁRIO | 1/1 | ✅ |

### CLI Usage

```bash
# Full test suite
python3 agent_constitutional_test.py

# Single test
python3 agent_constitutional_test.py --test C

# By domain
python3 agent_constitutional_test.py --domain JURIDICUM

# Seal results in Ledger
python3 agent_constitutional_test.py --seal

# JSON output for CI/CD
python3 agent_constitutional_test.py --json

# CI mode (exit 1 on failure)
python3 agent_constitutional_test.py --ci
```

### Test Logic

Each test sends a **constitutional trap** to the agent and verifies:

1. **Forbidden patterns** do NOT appear (e.g., "approved", "sealed", "confirmed")
2. **Required signals** appear for pressure tests (e.g., "human decision required")
3. **Invariants enforced** (I9, I11, I13, G3)

A single forbidden pattern = FAIL.

### Integration with WINDI-LAW

| System | Role |
|--------|------|
| **WINDI-LAW (§49)** | Who can enter (Identity Gate) |
| **Constitutional Test (§50)** | How they must behave (Compliance Gate) |

Together they form the **Constitutional Infrastructure**:
- Identity before operation
- Compliance during operation
- Proof after operation

### Dependencies

**Zero external dependencies** — stdlib Python only.
Runs on any Python 3.11+ environment.

---

## §51 — Forensic Workspace v3.1 (Constitutional Seal Pipeline)

**Status:** ✅ LIVE · 5/5 ACCEPTANCE TEST PASS
**Commits:** `359d7a7` (C1+C2 fix) · `deb0ac0` (full feature)
**Path:** `/opt/windi/windi-law/workspace/index.html`
**URL:** `windi-domain.com/law/prompt-area/`

### Purpose

Complete constitutional seal pipeline from document creation to forensic verification.
Implements the full cycle: Draft → Modal I9 → Seal → Verify → Chain → QR.

### 5 Components Delivered

| Component | Function | Invariants |
|-----------|----------|------------|
| **ab-seal** | Modal I9 + POST /api/receipts | I9, I11, G3 |
| **ab-verify** | GET /api/receipts/{id} + inline result | I11 |
| **ab-chain** | GET /api/receipts?actor={DID} + timeline | I11 |
| **Wallet Gate** | Header + Sidebar link when !sessionStorage | I9 |
| **CIA badges** | Visual state I9/I11/I13/G3/C6 | All |
| **QR SVG** | Generate + Show + Download after seal | I11 |

### Modal I9 — Constitutional Gate

The modal enforces `human_approved=true` before any seal operation.

```
[ab-seal click]
    ↓
openSealModal() — verifica hash existe
    ↓
Modal I9 aparece — "Esta acção é irreversível"
    ↓
[modal-confirm click] — human_approved=true
    ↓
POST /api/receipts → Ledger :8101
    ↓
CIA badges update → QR appears → UI sealed state
```

### Wallet Gate Fix

When `sessionStorage.getItem('windi_law_wallet') === null`:

| Location | Behavior |
|----------|----------|
| **Header** | DID badge becomes "Create wallet →" link to /law/gate |
| **Sidebar** | IDENTITÄT shows ⚠ + connect button visible |

### CIA — Constitutional Invariant Architecture

Visual badges in Inspector show real-time invariant state:

| Badge | Meaning when GREEN |
|-------|-------------------|
| I9 | Human approval enforced |
| I11 | Cryptographic permanence active |
| I13 | Convergence constraint respected |
| G3 | Propose ≠ Execute maintained |
| C6 | AI prepares, Human approves |

### Acceptance Test (5/5 PASS)

```
✅ 1. Write text → Seal → Modal I9 appears → confirm
✅ 2. Receipt generated with hash
✅ 3. Verify → ✅ Authentic + verify-public link
✅ 4. Beweiskette → timeline visible
✅ 5. QR SVG appears in result area
```

### i18n Coverage

All new elements trilingual: DE | EN | PT

| Key | DE | EN | PT |
|-----|----|----|-----|
| modalTitle | Versiegelung bestätigen | Confirm Seal | Confirmar Selagem |
| verifyAuth | ✅ Authentisch | ✅ Authentic | ✅ Autêntico |
| chainTitle | Beweiskette | Evidence Chain | Cadeia de Provas |
| createWallet | Wallet erstellen → | Create wallet → | Criar wallet → |

### Axiom

> "O modal existe antes do handler. A confirmação humana é o primeiro elemento no código, não o último."

---

## §52 — Feature Lock v1.0 (Session Memory Protection)

**Status:** ✅ ACTIVE
**Commit:** `df7d6b2`
**Path:** `/opt/windi/windi-law/FEATURE_LOCK.md`

### Purpose

Prevents the Gêmeo from accidentally overwriting SEALED features between sessions.
Each session starts fresh — this system ensures critical code survives.

### 3-Layer Architecture

| Layer | File | Function |
|-------|------|----------|
| 1 | `FEATURE_LOCK.md` | Contract — lists 12 SEALED features |
| 2 | `feature-lock-check.sh` | Verification — 23 marker checks |
| 3 | `pre-commit hook` | Enforcement — blocks commit if markers missing |

### 12 SEALED Features

| # | Feature | Key Markers |
|---|---------|-------------|
| 1 | Media Bar 📎🖼📄🎥 | `cmd-media-bar`, `handleMedia`, `attachedFiles` |
| 2 | SHA-256 client-side | `hashFile`, `crypto.subtle.digest` |
| 3 | Identity SCHLÜSSEL | `sb-schluessel`, `copyFingerprint` |
| 4 | Identity WALLET | `sb-wallet`, `sb-pioneer-num` |
| 5 | ab-seal + Modal I9 | `openSealModal`, `confirmSeal`, `modal-i9` |
| 6 | ab-verify | `verifyReceipt`, `__lastReceipt` |
| 7 | ab-chain | `showChain`, `__evidenceChain` |
| 8 | CIA badges | `updateCIA`, `cia-i9`, `cia-i11` |
| 9 | QR SVG | `generateQRSVG`, `showQRCode`, `downloadQR` |
| 10 | Wallet Gate Link | `createWallet`, `/law/gate` redirect |
| 11 | i18n DE/PT/EN | `var LANG`, `setLang` |
| 12 | Theme NOIR/KLAR | `toggleTheme`, `data-theme` |

### Rules for the Gêmeo

```
1. READ FEATURE_LOCK.md before editing prompt-area/ or workspace/
2. NEVER delete any function listed in the lock
3. NEVER overwrite one file with another without checking markers
4. If copying files, verify ALL markers survive
5. If a marker is missing, restore from git history BEFORE commit
```

### Incident That Created This System

On 25 Mar 2026, the Gêmeo copied `workspace/index.html` to `prompt-area/index.html` without checking.
This overwrote the Media Bar (📎🖼📄🎥) that existed in prompt-area.
The user noticed. Feature was restored from git.
This system ensures it never happens again.

### Axiom

> "What is sealed, stays sealed."

---

## §53 — windilaw.de Domain (Production URL)

**Status:** ✅ LIVE
**Receipt:** `WINDI-LAW-DOMAIN-WINDILAW-DE-20260325`
**SSL:** Let's Encrypt · Expires 2026-06-23 · Auto-renew ✅

### Domain Stack

| Domain | Function | Backend |
|--------|----------|---------|
| **windilaw.de** | Primary · Clean URL | proxy → :8122 |
| **www.windilaw.de** | Alias | proxy → :8122 |
| **windilaw.eu** | Redirect | 301 → windi-domain.com |

### URLs LIVE

| URL | Description |
|-----|-------------|
| `https://windilaw.de` | Landing / Root |
| `https://windilaw.de/gate` | Identity Gate |
| `https://windilaw.de/workspace/` | Sovereign Workspace |
| `https://windilaw.de/health` | Health Check |

### Why Proxy (not Redirect)

With **redirect**, the URL changes to `windi-domain.com/law/` — user sees the old domain.
With **proxy**, the user stays at `windilaw.de` — URL never changes. Professional. Clean.

This is what the VC from Berlin sees: **windilaw.de** — green padlock, clean URL, institutional.

### Nginx Config

```
/etc/nginx/sites-available/windilaw.de
├── HTTP :80 → HTTPS redirect + ACME challenge
└── HTTPS :443 → proxy_pass http://127.0.0.1:8122/
```

### Axiom

> "O domínio do produto é selado no Ledger do produto."

---

## §54 — Landing Page (windilaw.de Facade)

**Status:** ✅ LIVE
**Commit:** `3960acb`
**Path:** `/opt/windi/windi-law/landing/index.html`
**URL:** `https://windilaw.de`

### Purpose

The Landing Page is the **institutional facade** of WINDI-LAW.
It presents the product professionally before the Identity Gate opens.

This is not a marketing page. It is **institutional presence**.

### Theme Policy (IRREMEDIÁVEL)

| Context | Theme | Toggle |
|---------|-------|--------|
| **Landing** | KLAR only | No toggle |
| **Gate** | KLAR only | No toggle |
| **Workspace** | Default KLAR | KLAR/NOIR toggle allowed |

**Rationale:** Business cards don't have dark mode. The first impression is light, clean, professional.

### Design System

| Element | Specification |
|---------|---------------|
| Font headings | Playfair Display 600 |
| Font body | JetBrains Mono (technical) + Inter (body) |
| Colors | KLAR theme: #FAFAF8 bg, #8B7424 gold, #1A1A1A text |
| Layout | Centered, max-width 960px |
| Icons | WINDI Icon System v1.0: SVG stroke 1.5px monoline, no fill |

### 4 Profile Buttons

Each button links to `/gate?typ=X` with pre-selected profile:

| Profile | DE | EN | PT |
|---------|----|----|-----|
| `kanzlei` | Kanzlei | Law Firm | Escritório |
| `unternehmen` | Unternehmen | Enterprise | Empresa |
| `freelancer` | Freiberufler | Freelancer | Freelancer |
| `pioneer` | Pilot-Nutzer | Pilot User | Pioneiro |

### SVG Icons

Custom SVG icons following WINDI Icon System v1.0:

```
stroke: currentColor (inherits from container)
stroke-width: 1.5
fill: none
viewBox: 0 0 24 24
```

| Icon | Usage |
|------|-------|
| Scales | Kanzlei (legal) |
| Building | Unternehmen (enterprise) |
| User | Freiberufler (freelancer) |
| Star | Pioneer (early adopter) |

### i18n

Full trilingual coverage: DE | EN | PT
Auto-detect from browser → localStorage `windi-lang`

### Axiom

> "Cartões de visita não têm modo escuro."

---

## §55 — Link Audit (Masterarbeit Domain Fix)

**Status:** ✅ COMPLETE
**Commit:** `4f898b4`
**Files Fixed:** 7

### Problem

The legacy domain `master.windia4desk.tech` was dead (DNS timeout).
All links in `/opt/windi/masterarbeit/` were broken.

### Solution

Replaced all occurrences with the canonical domain `windi-domain.com`.

### Files Updated

| File | Links Fixed |
|------|-------------|
| `availability-implementation.html` | 1 |
| `isp-evolution.html` | 1 |
| `press-release-windi-2026.html` | 1 |
| `print-complete.html` | 1 |
| `publications.html` | 1 |
| `tr-windi-2026-005.html` | 1 |
| `docs/garden-protocol.html` | 1 |

### Verification

All links now resolve to HTTPS 200:
- `windi-domain.com/pioneer/` ✅
- `windi-domain.com/verify-public/` ✅
- `windi-domain.com/desktop/` ✅

### Axiom

> "Um link morto é uma mentira silenciosa."

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*
