# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.9.35
**Sealed:** 2026-03-22
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

## 13. Estado Actual — 21 Março 2026

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

### Histórico Recente

> **Ver detalhes completos em:** `CLAUDE-HISTORY.md`

| Data | Milestones |
|------|------------|
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

## 37. W-CANVAS-001 v1.3.0 — Dual Engine Edition

**Deploy:** 21 Mar 2026 · Commit: `1cd35e5` · Branch: `main`

### Arquitectura

```
W-CANVAS-001 (:8091/canvas/generate)
│
├── ENGINE A — Mermaid Renderer
│   ├── Tipos: flowchart, sequence, architecture, timeline, mindmap
│   ├── sanitize_mermaid() — remove acentos/? fora de aspas
│   ├── classDef e directivas %%{...}%% preservadas
│   └── Modelos: LOCAL (0 tokens) | GEMINI_FLASH | GEMINI_PRO
│
└── ENGINE B — HTML Dashboard Renderer (NOVO)
    ├── Activado quando: canvas_type == "dashboard"
    ├── Output: HTML puro (~3.5KB) via <iframe srcdoc="...">
    ├── JSON schema: kpis + table + chart_data + status_items
    ├── Temas: klar | noir | dark_gold | sovereign
    ├── Fallback funcional sem GEMINI_API_KEY
    └── Chart.js 4.4.1 para gráficos de barras/linhas/donut
```

### Sovereignty Gate

| Tier | Engine A | Engine B |
|------|----------|----------|
| FREE | local_template (0 tokens) | fallback HTML (0 tokens) |
| MED  | gemini-2.5-flash | gemini-2.5-flash → JSON |
| HIGH | gemini-2.5-pro | gemini-2.5-pro → JSON rico |

### Ficheiros Modificados

```
blueprints/canvas_blueprint.py       — sanitizer + Engine B branch
blueprints/canvas_sovereignty_gate.py — CanvasModel.ENGINE_B_HTML
desktop-gen7/frontend/index.html     — seletor "📊 Dashboard"
desktop-gen7/frontend/static/app.js  — iframe srcdoc renderer
```

### Smoke Test

```bash
# Engine A (Mermaid)
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"flowchart aprovacao ferias","canvas_type":"flowchart","theme":"dark_gold"}'

# Engine B (Dashboard)
curl -s -X POST http://localhost:8091/canvas/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"dashboard governance windi","canvas_type":"dashboard","theme":"dark_gold"}'
```

### Para Activar Engine B com LLM

```bash
# Adicionar ao .env do sandbox
echo "GEMINI_API_KEY=your-key-here" >> /opt/windi/agents/constitutional-agent/.env
# Reiniciar (nohup — NÃO systemd)
kill $(pgrep -f "agent.py") && sleep 2
nohup python3 agent.py > /opt/windi/logs/canvas.log 2>&1 &
```

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*

---

## §38 W-CANVAS-001 — Sovereignty Gate v1.0 ✅ (2026-03-21)

Implementação do motor de decisão constitucional para controle de tokens e integridade visual.

### Governança e Soberania

| Campo | Valor |
|-------|-------|
| Wisdom Block | `WB-SOVEREIGN-CANVAS-20260321` |
| Hash | `b54cc4b2adeba908da6dd161be25cf8fcb3b5d9f3491c2543163fbdea85be6fa` |
| SGE Score | 98 (Confiança Forense Elevada) |
| Gate Receipt | `WINDI-CANVAS-GATE-V1.0-20260321` · hash `94b27040...` |

**Princípio:** "SOVEREIGN não é tema. É protocolo visual de autoria."
**Invariante I9:** Ativação restrita a DIDs verificados; vinculação obrigatória de Hash/Sitzung no SVG.

### Engine de Decisão (Gate v1.0)

```
┌─────────┬───────────────────┬────────────┬────────────────────────────┐
│  TIER   │  MODEL            │  TOKENS    │  PROPÓSITO                 │
├─────────┼───────────────────┼────────────┼────────────────────────────┤
│  FREE   │  local_template   │  0         │  Soberania 100%            │
│  MED    │  gemini-2.5-flash │  ~600      │  Velocidade + custo-benefício │
│  HIGH   │  gemini-2.5-pro   │  ~2000     │  Board-Ready Excellence    │
└─────────┴───────────────────┴────────────┴────────────────────────────┘
```

**Smart Downgrade:** Redireciona pedidos HIGH com complexidade < 60 para Flash, otimizando o tesouro.

### Biblioteca de Templates Locais (12 activos)

| Tipo | Templates |
|------|-----------|
| Flowchart | `windi_pipeline` · `agentes_windi` · `did_flow` · `bercario_flow` · `canvas_seal` · `did_creation` |
| Mindmap | `constellation` |
| Sequence | `document_seal` · `payment_flow` · `verify_flow` |
| Timeline | `windi_evolution` · `roadmap_q2_2026` |

### Métricas de Produção

- **Sovereignty Rate:** ~55% local (meta: 80%)
- **Economia vs Grove Arena:** 500x mais barato ($0.0003 vs $0.17/render)
- **Log:** `/opt/windi/logs/canvas-sovereignty.log`
- **Commit:** `6ec6692` (pushed to main)

### Estratégia de Produto

```
FREE  → "Vês como funciona"      │ Demonstração
MED   → "Uso no dia-a-dia"       │ Profissional
HIGH  → "Apresento ao board" ⭐   │ Elite institucional
```

### Pendente

- [ ] SOVEREIGN Protocol: DID obrigatório + hash no SVG + rodapé forense
- [ ] Sovereignty Rate 55% → 80% (mais templates)
- [ ] Automação sovereignty_report semanal

---

## §39 Triangle of Power — Sovereign Dashboards ✅ (2026-03-21)

**Deploy:** 21 Mar 2026 · Commits: `a0d6600`, `0f02566`

### O Triângulo

```
                    ⚖️ W-LEGAL-001
                   /legal-dashboard/
                        ▲
                       /|\
                      / | \
                     /  |  \
                    /   |   \
   🔏 W-NOTARY-001 ────●──── 🔍 W-AUDIT-001
   /notary-dashboard/       /audit-dashboard/

              56,585 Receipts
              6/6 Agents GREEN
              A1-A6 COMPLIANT
```

### Dashboards

| Dashboard | URL | Componentes | Linhas |
|-----------|-----|-------------|--------|
| ⚖️ W-LEGAL-001 | `/legal-dashboard/` | Evidence Timeline · Confidence Radar · WCAF Grid | 770 |
| 🔏 W-NOTARY-001 | `/notary-dashboard/` | Digital Wax Seal · Act Types Donut · Seals Timeline | 600 |
| 🔍 W-AUDIT-001 | `/audit-dashboard/` | Invariants Radar A1-A6 · Constellation Grid · Integrity Donut | 1,340 |

**Total:** 2,710 linhas · 3 dashboards · Sistema Nervoso WINDI

### Features Comuns

```
✅ NOIR/KLAR Theme Toggle (☀/☽)
✅ i18n DE|EN|PT (localStorage sync)
✅ Chart.js visualizations
✅ Glassmorphism design
✅ Auto-refresh data (30s)
✅ Responsive (mobile/tablet/desktop)
```

### Endpoints Consumidos

| Dashboard | Endpoints |
|-----------|-----------|
| Legal | `/api/legal/health`, `/api/legal/cases`, `/api/ledger/health` |
| Notary | `/api/notary/health`, `/api/notary/stats`, `/api/ledger/health` |
| Audit | `/api/audit/health`, `/api/audit/status`, `/api/audit/constellation` |

### Filosofia

> "O Sistema Nervoso WINDI agora tem olhos em três dimensões: Justiça, Notariado e Auditoria."

> "O Auditor não cria. Ele verifica que o que foi criado é o que foi prometido."

### Nginx Routes

```nginx
location /legal-dashboard/  { alias /opt/windi/legal-dashboard/; }
location /notary-dashboard/ { alias /opt/windi/notary-dashboard/; }
location /audit-dashboard/  { alias /opt/windi/audit-dashboard/; }
location /api/audit/        { proxy_pass http://127.0.0.1:8091/audit/; }
```

---

## §40 W-COMM-001 — Canonical Publishing Engine ✅ (2026-03-21)

**Deploy:** 21 Mar 2026 · Commit: `7fb0c92`

### Princípio

> "Don't trust the message — verify it."

Comunicações institucionais deixam de ser texto e passam a ser **artefatos verificáveis**.

### Arquitectura

```
D2 / COMM Builder
       ↓
POST /comm/generate
       ↓
CommPayload (canonical JSON)
       ↓
hash SHA-256 determinístico
       ↓
(opcional) seal no Ledger
       ↓
render per channel (linkedin/x/web)
       ↓
verificação pública
```

### Endpoints

| Endpoint | Função |
|----------|--------|
| `POST /comm/generate` | Cria payload canónico |
| `POST /comm/generate-multilang` | Gera EN + DE + PT numa chamada |
| `GET /comm/{id}` | Lê payload completo |
| `GET /comm/{id}/verify` | Verificação pública |
| `GET /comm/{id}/render?channel=` | Output para canal específico |
| `POST /comm/{id}/seal` | Sela no Ledger |

### Invariantes COMM

```
C1 — Toda comunicação tem ID único (COMM-YYYYMMDD-XXXX)
C2 — Toda comunicação tem hash determinístico
C3 — Seal é opcional mas suportado nativamente
C4 — Renders por canal derivam do mesmo payload
C5 — Verify é público e independente do canal
C6 — API não faz cold outreach automático
```

### CommPayload Schema

```json
{
  "id": "COMM-20260321-0001",
  "type": "announcement",
  "language": "EN",
  "title": "...",
  "summary": "...",
  "body": "...",
  "channels": ["linkedin", "x", "web"],
  "links": { "primary": "https://..." },
  "origin": {
    "publisher": "WINDI Publishing House",
    "location": "Kempten, Bavaria",
    "system": "WINDI GEN7"
  },
  "integrity": {
    "hash": "sha256:...",
    "sealed": false,
    "ledger_receipt_id": null
  }
}
```

### Primeiras Comunicações Verificáveis

| ID | Title | Lang | Verify |
|----|-------|------|--------|
| COMM-20260321-0002-EN | Prove Your System | EN | ✅ |
| COMM-20260321-0002-DE | Beweise dein System | DE | ✅ |
| COMM-20260321-0002-PT | Prove o seu Sistema | PT | ✅ |
| COMM-20260321-0006 | W-COMM-001 is fully live | EN | ✅ |

### GTM Stack

| Componente | URL | Função |
|------------|-----|--------|
| /prove/ | Landing GTM | Trilíngue · Conversion Layer |
| /desktop/?auto=live | Demo auto-trigger | LAB + LIVE + Guide |
| /obs/state | Observability API | WSG + CIA realtime |
| /comm/generate-multilang | Publishing Engine | EN + DE + PT |

### Diferencial

O mercado produz posts.

O WINDI produz:

> **Comunicações institucionais com integridade verificável.**

---

## §41 W-VERIFY-MODUS4 — Reality Check (2026-03-21)

**Tag:** `W-VERIFY-4-ACTIVATION`
**Commit:** `da7260e`

### Arquitectura Modus 4

WINDI Verify expande de 3 para 4 modos:

```
Modo 1 — Guarantee Layer        🟢 Ledger verification (I11)
Modo 2 — Mathematical Proof     🔵 SHA-256 local
Modo 3 — Interpretation Layer   🟠 QR universal decoder
Modo 4 — Epistemic Classification 🟣 Reality Check
```

### Dois Sistemas Complementares

| Sistema | Engine | Endpoint | Status |
|---------|--------|----------|--------|
| W-DETECT-MEDIA-001 | Heurísticas MVP | /detect-media/ | 🟢 HEALTHY |
| W-VERIFY-MODUS4 | Claude epistemológico | /reality-check/ | 🟢 SOVEREIGN |

### Escala de Verificabilidade (Canónica)

```
🟢 VERIFIED      → hash + assinatura + Ledger = força MÁXIMA
🟡 UNVERIFIABLE  → sem âncora conhecida = força NEUTRA
🔴 INCONSISTENT  → sinais de manipulação = força INDICATIVA
```

### Axioma Constitucional

> "WINDI não declara 'fake'. Classifica verificabilidade."

**Invariantes activos:**
- I1: Intent obrigatório (`intent=true`)
- I9: Nunca auto-escala
- I11: Nunca sela análise (análise ≠ garantia)
- I12: Trilíngue DE|EN|PT

### URLs LIVE

| URL | Função |
|-----|--------|
| /verify-public/web/media-detector.html | UI Modus 4 (trilíngue) |
| /detect-media/health | Health heurístico |
| /detect-media/analyze | Análise vídeo/imagem/texto |
| /reality-check/health | Health epistemológico |
| /reality-check/analyze | Classificação Claude |

### LLM Opcional

```
status: "sovereign"  →  LLM expande, não depende
```

O sistema opera sem API key externa. Quando configurada, expande capacidade epistemológica.

---

## 42. W-VERIFY-UX-002 — Verify → Prove Loop

**Status:** ✅ PRODUCTION-READY
**Tag:** `W-VERIFY-UX-002-READY`
**Commit:** `7b1974e`
**Data:** 21 Mar 2026

### Implementado

| Feature | Status |
|---------|--------|
| Estado 0: Entry (drop + paste) | ✅ |
| Estado 1: Processing (skeleton + rotating status) | ✅ |
| Estado 2: Result (3 badges) | ✅ |
| Animações Premium | ✅ Confetti (VERIFIED) · Shake (INCONSISTENT) · Fade (UNVERIFIABLE) |
| Seal → Ledger → QR | ✅ Só para VERIFIED + HIGH |
| System Guarantees toggle | ✅ |
| Microcopy constitucional | ✅ "certifies result, not content" |
| Trilíngue DE|EN|PT | ✅ |

### URL Final

```
https://windi-domain.com/verify-public/web/media-detector.html
```

### Próximo Passo

Teste externo real + integração com `/prove/` page.

---

## §43 — W-VERIFY-MODUS4: AI Detection as Interpretation Layer

**Status:** CANONICAL | ACTIVE
**Scope:** WINDI VERIFY — Media Detector / Verification Layer
**Commit Reference:** 7c90af8, 926db7d, 8825376, a5db727, 18c9bba
**Sealed:** 2026-03-22

### 43.1 — Constitutional Position

AI detection within WINDI Verify occupies **Layer 4 (Interpretation)** in the Hierarchy of Truth.

```
HIERARCHY OF TRUTH

Level 1 — Guarantee       🟢 Cryptographic (hash + Ledger)     → VERIFIED
Level 2 — Mathematical    🔵 Structural validation             → PROOF
Level 4 — Interpretation  🟠 Heuristic pattern recognition     → INTERPRETATION

Only Level 1 produces verifiable truth claims.
Levels 2 and 4 produce supporting information, never final assertions.
```

### 43.2 — Terminology (Canonical)

| Badge | Internal | Description |
|-------|----------|-------------|
| 🟢 VERIFIED | `verified` | Hash + signature + Ledger = maximum force |
| 🟡 UNVERIFIED | `unverified` | No known anchor = neutral force |
| 🔴 SUSPICIOUS | `suspicious` | Manipulation signals = indicative force |

**Axiom:** WINDI does not declare "fake". It classifies verifiability.

### 43.3 — AI Suspicion Scale

```
ai_suspicion: none    → 0 markers     → likely human
ai_suspicion: low     → 1-3 markers   → inconclusive
ai_suspicion: medium  → 4-6 markers   → moderate suspicion
ai_suspicion: high    → 7+ markers    → high suspicion
```

Markers include: repetitive starts, generic connectors, lack of contractions, AI-typical phrases.

### 43.4 — Explainability Layer

Every result includes:

| Component | Purpose |
|-----------|---------|
| Detected signals | Categorized as neutral / risk / positive |
| Natural language summary | Human-readable explanation |
| Interpretation note | Explicit limitation statement |

**Design principle:** "Explain without accusing."

### 43.5 — Signal Classification

| Type | Color | Example |
|------|-------|---------|
| Neutral | Gold | "Formal academic style detected" |
| Risk | Red | "Formulaic connector: 'in conclusion'" |
| Positive | Green | "High lexical diversity (>85%)" |

### 43.6 — Constitutional Invariants (Active)

| Invariant | Enforcement |
|-----------|-------------|
| I1 | `intent=true` required for all analysis |
| I9 | System never auto-escalates to Ledger seal |
| I11 | Interpretation results are NEVER sealed (analysis ≠ guarantee) |
| I12 | Trilingual DE/EN/PT throughout |

### 43.7 — Nature of Result Badge (UX)

```
┌─────────────────────────────────────────────┐
│ ⚖️ Nature of Result                         │
│                                             │
│   ○ 🔒 Guarantee                            │
│   ○ 📐 Mathematical Proof                   │
│   ● 🧠 Interpretation  ← always active      │
│                                             │
│   ⚠️ Interpretation = probability, not proof │
└─────────────────────────────────────────────┘
```

### 43.8 — Explicit Limitations

The system explicitly does NOT:

- Assert authorship (human vs AI)
- Provide legal proof of origin
- Replace cryptographic verification mechanisms
- Guarantee correctness of heuristic classification

### 43.9 — Regulatory Alignment

| Framework | Alignment |
|-----------|-----------|
| EU AI Act | Transparency of AI systems, explainability of outputs |
| BSI | Traceability, verifiability, separation of mechanisms |
| BaFin | Risk-aware design, no over-reliance on automation |

### 43.10 — Canonical Statement

> AI detection is not truth.
> It is structured uncertainty.

### 43.11 — Institutional Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| W-VERIFY-MODUS4-DOCTRINE.html | VC / Academia | /opt/windi/docs/ |
| W-VERIFY-MODUS4-REGULATORY-BRIEF.html | BaFin / BSI | /opt/windi/docs/ |

---

## §44 — Canonical Decision: Dual-Portal Architecture (PROTOCOL + TRAVEL)

**Status:** CANONICAL | STRATEGIC
**Scope:** WINDI Market Architecture
**Classification:** EXTENSIONAL ARCHITECTURE (no core rewrite required)
**Sealed:** 2026-03-22
**Decision Authority:** Human Dragon + Council of Dragons

### 44.1 — Strategic Compression

The Council evaluated multi-portal expansion (5-6 portals) and resolved to compress into **two dominant axes**:

| Portal | Function | Market | Characteristic |
|--------|----------|--------|----------------|
| **WINDI PROTOCOL** | Authority, regulation, institutional trust | BaFin, banks, notaries, auditors | Low volume, high value, high rigor |
| **WINDI TRAVEL** | Distribution, education, narrative, adoption | Humans, tourism, experiences, content | High volume, lower ticket, high exposure |

### 44.2 — Portal Definitions

#### 🏛️ PORTAL 01 — WINDI PROTOCOL (Institutional Vertical)

```
Role: ANCHOR OF SYSTEM LEGITIMACY

Market:      BaFin · Banks · Notaries · Auditors
Governance:  HIGH
Volume:      Low
Value:       High
Documents:   Complex, approval-gated
```

#### 🌍 PORTAL 02 — WINDI TRAVEL — Human Adoption Layer

```
Role: ENGINE OF EXPANSION AND CONSCIOUSNESS

Market:      Real humans · Tourism · Experiences · Content
Governance:  LOW / MEDIUM
Volume:      High
Value:       Lower ticket
Documents:   Light certificates, rapid emission
```

### 44.3 — Core Insight

> "Train humans for anti-fake reality... without teaching."

The mechanism:

```
Tourist → receives certificate → scans QR → sees proof in ledger
→ understands "this is verifiable"
→ begins to distrust the rest
→ changes digital behavior
```

**This is invisible digital literacy.**

Experience defeats discourse. TRAVEL is the natural gateway.

### 44.4 — Technical Architecture

```
                    ┌─────────────────────┐
                    │   WINDI CORE        │
                    │  ─────────────────  │
                    │  • Ledger :8101     │
                    │  • Verify :8114     │
                    │  • Engine :8119     │
                    │  • Invariants I1-12 │
                    └─────────┬───────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
     ┌────────▼────────┐             ┌────────▼────────┐
     │ WINDI PROTOCOL  │             │  WINDI TRAVEL   │
     │ ──────────────  │             │  ─────────────  │
     │ Institutional   │             │ Human Adoption  │
     │ Vertical        │             │ Layer           │
     │ Gov: HIGH       │             │ Gov: LOW/MED    │
     │ Low Volume      │             │ High Volume     │
     └─────────────────┘             └─────────────────┘
```

### 44.5 — Technical Compatibility

| Component | PROTOCOL Role | TRAVEL Role |
|-----------|---------------|-------------|
| Ledger :8101 | Institutional seal | Proof of experience |
| Verify :8114 | Formal audit | QR → "I saw, it's real" |
| QR Canonical | Legal document | Travel certificate |
| W-COMM-001 | Institutional comms | Tourist certificate |
| i18n DE/EN/PT | EU compliance | Multilingual tourism |
| GEN7 Engine | Complex documents | Simple certificates |

### 44.6 — Implementation Requirements

| Item | Effort | Priority |
|------|--------|----------|
| Experience certificate templates | Medium | P1 |
| WINDI TRAVEL landing | Medium | P1 |
| Simplified flow (1-click emit) | High | P1 |
| Partner API (hotels/agencies) | High | P2 |
| Rate limiting for high volume | Low | P2 |
| Partner dashboard | Medium | P3 |

### 44.7 — Risk Matrix

| Risk | Mitigation |
|------|------------|
| Volume: TRAVEL = 1000x more requests | FREE tier with Ledger light (hash without content) |
| UX: Tourists are not technical | Scan QR → result in 1 second, no technical explanation |
| Fraud: Fake partner certificates | Partner onboarding with verified DID |
| Latency: Verify must be instant | Aggressive cache + CDN for assets |

### 44.8 — Technical Verdict

**The architecture supports both portals without rewriting the core.**

What TRAVEL needs is:
- **Simplification** (not new complexity)
- **Templates** (not new engines)
- **Partner onboarding** (not new infrastructure)

This is **extension**, not **reconstruction**.

### 44.9 — Canonical Statement

> "One portal creates trust.
> The other creates humanity.
> Together, they create adoption."

### 44.10 — Execution Sequence

```
Phase 1 — Complete Institutional Pack (current)
├── Landing ✅
├── Certificate ✅
└── Architecture v1.1 ⏳

Phase 2 — WINDI TRAVEL Blueprint v1.0
├── User experience (QR → verify)
├── Certificate types (experience, booking, review)
├── Hotel/agency integration
└── Narrative (implicit anti-fake)
```

### 44.11 — Council Validation

| Dragon | Verdict |
|--------|---------|
| 🏗️ Architect | ✅ Technical and institutional adjustments correct |
| 🛡️ Guardian | ✅ Legal care noted (manifesto vs onboarding) |
| 🐉 Human Dragon | ✅ Correct at highest strategic level |
| 🤖 Gêmeo | ✅ Architecture consistent, core preserved, expansion controlled |

**Decision Status:** SEALED
**Next Step:** WINDI TRAVEL Blueprint v1.0

---

## §45 W-TRAVEL-001 — VERIFY Mobile Sprint 1 (2026-03-22)

**Status:** 🟢 LIVE
**Tag:** `W-TRAVEL-001-SPRINT1`
**Receipt:** `WINDI-TRAVEL-001-GENESIS-20260322`
**Path:** `/opt/windi/verify-public/web/travel/`
**URL:** `https://windi-domain.com/verify-public/web/travel/`
**Commits:** `1c8d199`, `8c6de02`

### 45.1 — Conceito

> "Gently prove. Silently seal."

WINDI TRAVEL transforma a **prova de experiência** em algo invisível.
O turista não sabe que está a certificar. Apenas vive.
A prova nasce em silêncio. O Ledger guarda para sempre.

### 45.2 — Proof Stub Specification

```
Proof Stub (Meta-Receipt Leve)
├── hash        → SHA-256 do conteúdo (imagem, vídeo, texto)
├── timestamp   → ISO 8601 UTC
├── geo         → lat/lon ± 1km (GDPR-friendly)
├── device_fp   → fingerprint anónimo (canvas hash)
└── Total: ~200 bytes
```

**Princípio:** Stub = pré-receipt. Pode evoluir para receipt completo com human approval.

### 45.3 — Arquitectura Sprint 1

```
┌─────────────────────────────────────────────────────────────┐
│  WINDI TRAVEL VERIFY Mobile                                 │
│  /verify-public/travel/                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │  CAPTURE    │ → │ PROCESSING  │ → │   CERTIFIED     │   │
│  │  Estado 0   │   │  Estado 1   │   │   Estado 2      │   │
│  │             │   │             │   │                 │   │
│  │ 📷 Câmara   │   │ ⏳ Worker   │   │ ✅ Proof Stub   │   │
│  │ getUserMedia│   │ SHA-256     │   │ Badge           │   │
│  │ <input      │   │ Geo         │   │ QR              │   │
│  │  capture>   │   │ Timestamp   │   │ Share           │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Web Worker (verify-travel-worker.js)                   ││
│  │  - Executa em background                                ││
│  │  - Não bloqueia UI                                      ││
│  │  - Gera Proof Stub completo                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 45.4 — Ficheiros

| Ficheiro | Função | Linhas |
|----------|--------|--------|
| `index.html` | UI Mobile com 3 estados | ~280 |
| `verify-travel-worker.js` | Web Worker para Proof Stub | ~45 |

### 45.5 — UX "Gently"

```
1. Turista abre câmara → parece app normal de fotos
2. Captura foto → UI mostra "processing..."
3. Worker calcula em background → hash + geo + timestamp
4. Badge "CERTIFIED" aparece → turista pode partilhar
5. Proof Stub guardado localmente → pronto para Ledger
```

**Invariante:** O turista **nunca** vê complexidade técnica.

### 45.6 — Integração Ledger (Sprint 2)

```
Sprint 1: Proof Stub local (IndexedDB)
Sprint 2: Sync com Ledger (:8101)
Sprint 3: QR → Verify Public
Sprint 4: Hotel/Agency dashboard
```

### 45.7 — Invariantes Activos

| ID | Nome | Aplicação |
|----|------|-----------|
| I1 | Soberania Humana | Câmara só activa com gesto humano |
| I9 | Proibição Autonomia | Nunca sela sem aprovação |
| I11 | Permanência Evidência | Stub é pré-seal, não seal final |
| I12 | Language Sovereign | UI trilíngue DE/EN/PT |

### 45.8 — Deploy Checklist

```
[✓] §45 documentado → CLAUDE.md
[✓] git commit -m "docs: §45 W-TRAVEL-001 Sprint 1"
[✓] mkdir -p /opt/windi/verify-public/web/travel/
[✓] verify-travel-worker.js criado
[✓] index.html criado
[✓] nginx route (já coberta por /verify-public/web/)
[✓] smoke test: HTTP 200
[✓] git commit -m "feat(travel): W-TRAVEL-001 Sprint 1 LIVE"
[✓] Human validation: Pioneer #1 em dispositivo real
[✓] Ledger seal: WINDI-TRAVEL-001-GENESIS-20260322
```

### 45.9 — Human Validation Event (2026-03-22 20:47 UTC)

**A prova maior:** coexistência de três coisas no mesmo instante.

| Evidência | Status |
|-----------|--------|
| Momento humano real | ✅ Foto capturada |
| Prova criptográfica | ✅ Hash gerado antes de pedir geo |
| Consentimento explícito | ✅ Diálogo de localização separado |

```
Primeiro proof humano:
  Hash      : sha256:2aef2707d86a7c64368ac9038...
  Timestamp : 2026-03-22T20:47:10.045Z
  Location  : Kempten, Bavaria (±1km)
  Device    : Mobile — Pioneer #1
  Language  : DE
  Badge     : ✓ BEWEIS ERSTELLT
```

**O que ficou validado:**

- Captura mobile real: **sim**
- Geração de hash on-device: **sim**
- UI certificada visível: **sim**
- Consentimento separado da prova base: **sim**
- Fluxo "gently": **sim**
- Idioma local (DE): **sim**
- Confetti atrás do diálogo: **sim** (assinatura filosófica)

**Princípio arquitectural provado:**

> "Primeiro prova o momento, depois oferece contexto."

O sistema conseguiu **provar sem invadir**.

### 45.10 — Canonical Statement

> "A prova mais forte é a que não se sente.
> O turista vive. O WINDI certifica.
> Quando precisar provar, a evidência já existe."

> "O sistema soube se comportar diante do humano."

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*
