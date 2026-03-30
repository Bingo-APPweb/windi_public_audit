# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.9.53
**Sealed:** 2026-03-30 · §66 Places Sovereignty Gate
**Author:** Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
**Location:** Kempten, Bavaria, Deutschland

> **Ficheiros relacionados:** `CHANGELOG.md` (histórico) · `ARCHITECTURE.md` (código técnico)

## 📚 Overflow Policy (17 Mar 2026)
Hard limit: **32KB**. Último fix: 26 Mar 2026 (53.7KB → 32.2KB).
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

## 13. Estado Actual — 30 Março 2026

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
| :8122 | WINDI-LAW Identity Gate | 🟢 **SEALED** · Isolado · 12 empresas |
| :8126 | WINDI Travel Identity Gate | 🟢 **LIVE** · v1.2.0 · Pronto produção |
| :8130 | W-GATEWAY-001 (LLM Bridge) | 🟢 **LIVE** · 5 providers |

### Sistemas LIVE (29 total)

**Core:** GEN7 Desktop · Pioneer Program · VPR System · API Keys · Dispatch · Web Hosting · i18n · Wallet · Lead Admin

**Agents (W-*):** CIA-001 · WSG-001 · GATE-001 · NGINX-001 · CANVAS-001 · CANVAS-OBS-001 · CANVAS-LAB-001 · COMM-001 · PROVE-001 · DETECT-MEDIA-001 · VERIFY-MODUS4 · INTENT-001 · COUNSEL-001

**Products:** Triangle of Power · WINDI FIELD · WINDI TRAVEL · FVE Protocol · RFC-001 DNA

> **Detalhes:** ver `§37-72. Sistemas Recentes` abaixo

### Histórico Recente (últimos 5)

| Data | Milestone |
|------|-----------|
| 30 Mar | §72 **Pulse Reading Layer** · "HER" architecture · Subtexto antes do routing |
| 30 Mar | §71 **Armadura de Seda** · Identidade Fonética · Prompts com alma |
| 30 Mar | §70 I-TRAVEL Constitution · Idioma ≠ Localização · MARIA pergunta destino |
| 30 Mar | §69/b MARIA Waterfall Fix · 5 clean exits · Query intent override |
| 30 Mar | §68 Hotellook Hotel Bridge · Token 513311 · /hotel-search |

> **Histórico completo:** `CLAUDE-HISTORY.md` + `CHANGELOG.md`

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

## §37-72. Sistemas Recentes — Resumo

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
| 49 | WINDI-LAW | Identity Gate · Trilingual Policies · :8122 | ✅ COMPLETE |
| 50 | Constitutional Test | CI/CD Compliance · 7 tests · 4 domains | ✅ SEALED |
| 51 | Forensic Workspace v3.1 | ab-seal + ab-verify + ab-chain + CIA + QR | ✅ LIVE |
| 52 | Feature Lock v1.0 | 3-layer protection · 23 markers · pre-commit | ✅ ACTIVE |
| 53 | windilaw.de | Domain · SSL · Proxy · Clean URL | ✅ LIVE |
| 54 | Landing Page | KLAR theme · 4 profile buttons · SVG icons | ✅ LIVE |
| 55 | Link Audit | master.windia4desk.tech → windi-domain.com | ✅ COMPLETE |
| 56 | Email + SMTP | SMTP Strato · 48h token · Multipart | ✅ LIVE |
| 57 | Workspace v3 | Governança Silenciosa · 12 SEALED | ✅ CERTIFIED |
| 58 | Human Test Ready | Core flow proven · 100% functional | ✅ CANONICAL |
| 59 | **Travel Phase 2** | W-GATEWAY-001 · W-MARIA-001 · :8126 :8130 | ✅ **LIVE** |
| 60 | **P3-A Identity Gate** | Tesoura v10 · fail-closed · Three Claudes | ✅ **DEPLOYED** |
| 61 | **Travel Checkup** | Port fix · Test cleanup · LAW/Travel isolation | ✅ **VERIFIED** |
| 62 | **MARIA Triple LLM** | Gemini+Claude+OpenAI · maria_voice.py · Voz natural | ✅ **LIVE** |
| 63 | **MARIA Vozes + Memory** | Trilíngue fix · nomada_profile.py · maria_memory.db | ✅ **LIVE** |
| 64 | **DID Universal WINDI** | did:windi:{produto}:{uuid} · Ecossistema unificado | ✅ **LIVE** |
| 65 | **MARIA Saudação** | gerar_saudacao() · Trilingual · Visit count progression | ✅ **LIVE** |
| 66 | **Places Sovereignty Gate** | Cache-first · TTL per type · Audit trail · Soberania cumulativa | ✅ **LIVE** |
| 67 | **Kiwi Flight Bridge** | kiwi_bridge.py · IATA · Travelpayouts 513311 · Voz Natural trilíngue | ✅ **LIVE** |
| 68 | **Hotellook Hotel Bridge** | hotel_bridge.py · /hotel-search · Token 513311 · Voz Natural | ✅ **LIVE** |
| 69 | **MARIA Waterfall Fix** | 5 clean exits · PLACE_TYPE_MAP 50+ · Culture/General intents | ✅ **LIVE** |
| 69b | **Query Intent Override** | detect_place_type_from_query() · Frontend mismatch fix | ✅ **LIVE** |
| 70 | **I-TRAVEL Constitution** | Idioma ≠ Localização · MARIA pergunta destino · GPS origin | ✅ **LIVE** |
| 71 | **Armadura de Seda** | Identidade Fonética · Prompts com alma · Surpresa/Opinião/Imperfeição | ✅ **LIVE** |
| 72 | **Pulse Reading Layer** | "HER" architecture · read_pulse() · Subtexto antes do routing · Paradoxo urgência=calma | ✅ **LIVE** |

### Referência Rápida

**Canvas:** `/canvas/generate` · Mermaid + Dashboard · 12 templates locais
**COMM:** `/comm/generate` · Artefatos verificáveis · Trilíngue
**Verify:** `/verify-public/web/media-detector.html` · 4 modos
**WINDI-LAW:** `/law/gate` · Identity Gate · Policies DE|EN|PT
**LAW Workspace:** `/law/prompt-area/` · Forensic Seal Pipeline · Modal I9 · QR SVG
**WINDI Travel:** `/travel/gate` · Identity Gate · KLAR theme · I9 fail-closed
**Travel Workspace:** `/travel/workspace/` · Protected by require_auth()
**Tesoura:** `/travel/tesoura-ui/` · React 18 CDN · Ledger seal
**MARIA:** `/maria/plan` · Triple LLM · Voz Natural PT/DE/EN · DID Memory
**Flights:** `/maria/flight-search` · Kiwi Bridge · Voz humana · Travelpayouts 513311
**Hotels:** `/maria/hotel-search` · Hotellook Bridge · Voz natural · Token 513311
**Affiliate:** Travelpayouts ID 513311 · ~3% comissão · Cookie 30 dias · IP1 intacto
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
**Axioma §60:** "A prova mais gentil é aquela que o utilizador nem percebe que aconteceu."
**Axioma §61:** "Dois produtos, duas portas, duas bases de dados — isolamento é arquitectura, não acidente."
**Axioma §62:** "MARIA não é um assistente — é uma companheira. A diferença está no tom, não na função."
**Axioma §63:** "MARIA lembra-se, mas nunca intromete. A memória serve a personalização, não a vigilância."
**Axioma §64:** "No WINDI não há estranhos. Quem tem um DID WINDI é cidadão de todo o ecossistema."
**Axioma §65:** "MARIA remembers, but never intrudes. A saudação muda com a confiança — viajante → de volta → connosco."
**Axioma §66:** "O mundo real entra uma vez, a soberania local serve para sempre."
**Axioma §67:** "MARIA fala como companheira, não como motor de busca. 'Boa notícia!' em vez de 'Encontrei 2 resultados.'"
**Axioma §68:** "Um token, dois mundos — voos e hotéis servidos pelo mesmo parceiro, sem fricção para o viajante."
**Axioma §69:** "MARIA não engole queries no vazio. Cada pergunta tem uma saída limpa."
**Axioma §69b:** "O utilizador tem sempre razão — se escreve 'Farmacia', MARIA ouve 'Farmacia', não o que o frontend diz."
**Axioma §70:** "Falar português não significa querer ir a Lisboa."
**Axioma §71:** "Rigor por dentro, gentileza por fora."
**Axioma §72:** "Urgência não precisa de velocidade. Precisa de presença."

**§71 Armadura de Seda (MARIA Voice):**
```
Surpresa:     "Ah, esse bairro!" · "Olha que interessante—"
Opinião:      "Pessoalmente, prefiro ir de manhã"
Memória:      "Dizem que..." · "Há quem jure..."
Imperfeição:  "Não sei se ainda está aberto, mas..."
Ritmo:        Frase curta. Frase longa com cor. Micro-dica única.
```

**§72 Pulse Reading Layer ("HER" Architecture):**
```
Layer 0 — Lê o subtexto ANTES de qualquer routing:

1. RITMO DA ESCRITA
   - 1-3 palavras → cansaço, sobrecarga → energy=low
   - "..." → hesitação, dúvida → intent=lost
   - "!" → celebração → intent=celebrate

2. TEMPERATURA DA PALAVRA
   - "quero" → desejo tranquilo
   - "preciso" → necessidade real → energy=fragile
   - "não sei" → perdido → tone_needed=anchor

3. CONTEXTO TEMPORAL
   - 21h-05h → vulnerabilidade → respond_to=the_feeling
   - 06h-09h → energia nova mas ansiedade possível

4. MEMÓRIA DE RITMO
   - Mensagens a encurtar → desistência suave → respond_to=the_silence

5. PARADOXO FUNDAMENTAL
   "preciso agora" → urgência → pace="slow"
   Porque urgência não precisa de velocidade. Precisa de presença.

mood_pulse = {
    energy: high|medium|low|fragile
    intent: discover|urgent|lost|celebrate|rest|connect
    tone_needed: enthusiastic|gentle|anchor|silent_first|playful
    respond_to: the_words|the_feeling|the_silence
    pace: fast|normal|slow
}
```

**Filosofia da Presença (§72 Doctrine):**
```
O bar está no chão.

Google Maps:    "3 resultados encontrados."
Siri:           "Aqui estão algumas opções."
ChatGPT:        "Posso ajudar a encontrar um café!"

MARIA:          "Tudo bem. Fica onde estás."

A diferença não está nas palavras.
Está no que foi LIDO antes das palavras.

┌─────────────────────────────────────────────────────────┐
│  Efeito Samantha Mínimo                                 │
│                                                         │
│  Não é a IA saber tudo.                                 │
│  É a IA notar o que mais nenhuma notou.                 │
│                                                         │
│  INPUT:   "...não sei"                                  │
│  LEITURA: reticências + "não sei" = perdido             │
│  OUTPUT:  "Tudo bem. Fica onde estás."                  │
│                                                         │
│  O utilizador não vai saber que foi um if "..." in msg  │
│  Vai só sentir: "Ela percebeu."                         │
└─────────────────────────────────────────────────────────┘

A fórmula:
  §71 = O que MARIA diz (timbre)
  §72 = O que MARIA lê antes de dizer (presença)

  Timbre sem presença = personagem de teatro
  Presença sem timbre = terapeuta mudo
  Timbre + Presença  = companheira

MARIA não compete por features.
Ganha por presença.

E presença não se copia com npm install.
```

**§70 I-TRAVEL Constitution:**
```
I-TRAVEL-1: Idioma ≠ Localização — Nunca inferir origem pelo idioma
I-TRAVEL-2: Destino extraído do texto ou perguntado — NUNCA assumido
I-TRAVEL-3: Origem = GPS real do device — Fallback = IP, NUNCA idioma
```

**§69 MARIA Waterfall (canonical):**
```
Query → flight keywords?    → Kiwi Bridge
      → hotel keywords?     → Hotellook Bridge
      → culture keywords?   → MARIA direct (dicas, moeda, seguro...)
      → §69b place detect?  → Override frontend intent (farmacia, praia, banco...)
      → PLACE_TYPE_MAP?     → Places Gate (50+ types)
      → else                → general_companion (friendly fallback)
```

**§69b Intent Override:** `detect_place_type_from_query()` escaneia a query raw e corrige o intent do frontend quando há mismatch. Ex: frontend envia `restaurant` mas query contém "farmacia" → backend corrige para `pharmacy`.

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*

---

## BACKLOG — Próximas Sessões

### P0 — Crítico (Próxima Sessão)
- [ ] **P3-B Travel Workspace** — Implementar workspace principal WINDI Travel

### P1 — Importante
- [ ] **Rate limiting** — nginx Agent Corps
- [ ] **Cron 48h** — Downgrade email não verificado → EMAIL_PENDING
- [ ] **HIGH ops gate** — Bloquear operações HIGH se email_verified=0

### P1.5 — WINDI Travel Phase 2
- [ ] **Vídeo** — Captura + seal de vídeo
- [ ] **Colagem Soberana** — Composição multi-momento
- [ ] **Thread Visual** — Timeline com thumbnails
- [ ] **GPS Reverse Geocoding** — Nomes de lugares
- [ ] **Gemini Vision** — Descrição automática

### P2 — Melhorias
- [ ] **W-ACCT-001** — Bridge dedicado
- [ ] **W-COMPLY-001** — Dashboard
- [ ] **Resend UI** — Botão "Reenviar email" no workspace

### Infra
- [ ] **windilaw.de** — Sincronizar com windi-domain.com/law/
- [ ] **Backup DB** — Automatizar backup windi_law_identity.db + travel_users.db

### Completado (ver §37-66)
- [x] SMTP · P3-A Identity Gate · Tesoura v10 ✅ 29 Mar 2026
- [x] Travel Checkup · Port fix · LAW isolation ✅ 30 Mar 2026
- [x] MARIA Triple LLM · Gemini+Claude+OpenAI · Voz activa ✅ 30 Mar 2026
- [x] §65 MARIA Saudação Personalizada · gerar_saudacao() ✅ 30 Mar 2026
- [x] §66 Places Sovereignty Gate · Cache-first · TTL · Audit ✅ 30 Mar 2026

---

## §57 — WINDI-LAW Workspace v3 — CERTIFIED · 26 Mar 2026

**Status:** ✅ COMPLETE · SEALED · I11 · IRREMEDIÁVEL
**Receipt:** `WINDI-LAW-WORKSPACE-V3-CERTIFIED-20260326164718`
**Hash:** `6050edf95a6d1fedcfc1bb405a48027a90db8f67b3f9ad4b81e46f46746054f0`
**Commits:** `9ed0998` + `2d9ce6c`
**Live:** `windilaw.de/workspace/` · `windi-domain.com/law/workspace/`

### O que foi construído

Workspace v3 — "Governança Silenciosa" — redesign completo da interface WINDI-LAW.

**Princípio arquitectural aprovado:**
> "Forense é o subtexto, não o tema. Documento = protagonista."

De 2443 → 1270 linhas — arquitectura que respira.

### Fases certificadas

| Phase | Descrição | Commit |
|-------|-----------|--------|
| 1 | Wallet Gate Logic — fail-closed, ?did= override | 9ed0998 |
| 2 | 12 SEALED Functions — hashFile, openSealModal, confirmSeal, verifyReceipt, showChain, updateCIA, generateQRSVG, toggleTheme, setLang, CIA badges | 9ed0998 |
| 3 | clearSession Opção A — preserva sessão se wallet activa | 2d9ce6c |
| 4 | Smoke Test 12/12 + Browser 6/6 — CERTIFIED | — |

### Features seladas (23/23 markers)

| Feature | Descrição |
|---------|-----------|
| F1 | Media Bar 📎🖼📄🎥 + attachedFiles |
| F2 | SHA-256 client-side (crypto.subtle.digest) |
| F3 | SCHLÜSSEL sidebar — sb-schluessel + copyFingerprint |
| F4 | WALLET sidebar — sb-wallet + sb-pioneer-num |
| F5 | Modal I9 — openSealModal + confirmSeal + modal-i9 |
| F6 | verifyReceipt → Ledger :8101 |
| F7 | showChain — Beweiskette timeline |
| F8 | CIA badges I9/I11/I13/G3 — updateCIA |
| F9 | QR SVG — generateQRSVG + showQRCode + downloadQR |
| F10 | Wallet Gate — createWallet → /law/gate |
| F11 | i18n DE/PT/EN — var LANG + setLang |
| F12 | NOIR/KLAR toggle — toggleTheme + data-theme |

### Invariantes validados

| Invariante | Validação |
|------------|-----------|
| I9 | Modal obrigatório antes do seal — nenhuma acção autónoma |
| I11 | SHA-256 + Ledger — permanência criptográfica |
| I13 | sessionStorage local — soberania de dados |
| G3 | "Versiegeln" só após confirmação explícita — humano decide |

### Axioma

> "A tecnologia mais avançada é aquela que desaparece. O documento é o protagonista — a forense é só o subtexto."

---

## §59 — WINDI TRAVEL v1.0 — LIVE · 26 Mar 2026

**Status:** ✅ LIVE · FIRST SEAL · I14 · IRREMEDIÁVEL
**Receipt:** `WINDI-TRAVEL-1774563585`
**Port:** :8126
**URLs:** `windi-domain.com/travel/gate` · `windi-domain.com/travel/workspace/`

### O que nasceu

De uma caixa de sapatos no chão de Kempten nasceu o WINDI Travel.

**Filosofia:**
> "Guardar o passado. Resguardar o futuro. No presente perfeito."

**Invariantes:**
- **I14** — Presence Integrity: provar que "eu estava lá"
- **I9** — Human confirmation obrigatória antes de seal
- **I11** — Forensic Ledger imutável

### Features v1.0

| Feature | Descrição |
|---------|-----------|
| Identity Gate | Trilíngue DE/PT/EN · DID Ed25519 · Tema KLAR |
| Rescue Mode | Fotografar memórias físicas (📦) |
| Capture Mode | Capturar momentos live (📸) |
| SHA-256 | Hash criptográfico client-side |
| GPS | Geolocalização · 47.6429°N Kempten |
| Modal I9 | "Für immer sichern?" · confirmação humana |
| Faden | Thread de memórias · thumbnails · receipts |
| Seal | Forensic Ledger :8101 · verificável |

### Primeiro Selo Real

```
WINDI-TRAVEL-000001
───────────────────────────────────────
Momento:    "26 anos atrás o mundo ainda reservava..."
Hash:       SHA-256: 1eafdcbbf57ca948…
GPS:        47.6429°N, 10.2929°E · Kempten, Bavaria
Timestamp:  2026-03-26T21:46:10.689Z
Modo:       Rescue (📦 caixa de sapatos)
Selado:     22:59 CET
Invariante: I14 + I9 + I11
───────────────────────────────────────
```

### Estrutura

```
/opt/windi/windi-travel/
├── identity-gate/
│   ├── identity_gate.py      # FastAPI :8126
│   ├── templates/gate.html   # Trilíngue · KLAR
│   └── windi-travel.service  # systemd
└── workspace/
    └── index.html            # Mobile-first · Rescue/Capture/Faden
```

### Axioma §59

> "A caixa de sapatos que estava no chão de Kempten já não pode desaparecer."

**Drei Sprachen. Ein Herz. Eine Wahrheit.**

---

*LIGA IA+H — Kempten, Bavaria · 30 Mar 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*Sessão: 30 Mar 2026 · §61 Travel Checkup · detalhes em `CLAUDE-HISTORY.md`*

