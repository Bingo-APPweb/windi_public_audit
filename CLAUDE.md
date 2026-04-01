# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.9.70
**Sealed:** 2026-04-01 · §103.T Train Intelligence
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

**Regras Globais:** Auto-detect língua · Rascunho imediato · Placeholders [X] · Máx 1 pergunta · Sem "garanto/certamente" · Terminar com stage
> **Detalhes por agente:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026

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

> "A tecnologia é complexa para que a experiência seja estúpida de tão simples."

**4 Pilares:** P1 Faz antes de explicar · P2 Silêncio como onboarding · P3 Virtude Forense · P4 Uma frase basta
**Pioneer:** `windi-domain.com/pioneer/` ✅ LIVE
> **Detalhes:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026

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

**Status:** ✅ PRODUÇÃO · **Port:** :8119 · **URL:** `windi-domain.com/desktop/`

**Pipeline:** Intent → Dragon Processing → Agent Bridge → Canvas → Human Gate (I9) → Ledger Seal (I11)
**7 Motores:** DOC · SLIDES · WEB · ART · DATA · CODE · MEDIA (todos ✅ LIVE)
> **Endpoints + Smart Zones:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026 | `ARCHITECTURE.md`

---

## 13. Estado Actual — 31 Março 2026

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

> **Detalhes:** ver `§37-84. Sistemas Recentes` abaixo

### Histórico Recente (últimos 5)

| Data | Milestone |
|------|-----------|
| 01 Apr | §103.T **Train Intelligence** · MARIA Decision Engine · transport.rest API · `930a2cc` |
| 01 Apr | §106 **Contexto no Scoring** · apply_context_modifiers() · Situational awareness · `7d88676` |
| 01 Apr | §105 **Explicação Visível** · Maria explains decisions · generate_explanation() · `668742b` |
| 01 Apr | §104.1 **Hotels & Places Personalization** · Escala comparável · Category boosts · `7053f21` |
| 01 Apr | §104 **Personalização Real** · Campos evoluíveis · Ajustes incrementais · `d355304` |
| 01 Apr | §101-103 **Coerência Restaurada** · Feedback Loop + Reserva Contínua + I9 Gate |
| 01 Apr | §100.5 **Memory Engine** · Structural learning · Decision feedback loop · `253cbea` |
| 01 Apr | §96-100 **Decision Engine Evolution** · Nómada v1.3 · Anticipation · `4a9e51a` |
| 01 Apr | P0 **Identity Sovereignty** · I9 Enforcement · Backend authority · `2ddc3e5` |

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

## 15-16. Keys + Naming (resumo)

**W-KEYS:** `windi-domain.com/keys/` ✅ LIVE · 4 Tiers (SEED/NODAL/SOVEREIGN/ORACLE)
**NAMING:** Interface pública = "WINDI" · Interno = "Three Dragons" · Código = `dragon_*` OK
> **Detalhes:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026

---

## 21. Wallet Gate — DID Identity

**Status:** FASE 1 LIVE · FASE 2 pendente
**URL:** `windi-domain.com/desktop/` (botão 🪪)
**Storage:** `sessionStorage('windi_desktop_wallet')`
> **Detalhes:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026

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

## 32-36. DID + Data Policy (resumo)

> **Detalhes:** `CLAUDE-HISTORY.md` § SESSÃO 19 Mar 2026

**§32 DID Seed:** `ALMA → DID → CÉREBRO → LEDGER → MUNDO` · **IRREMEDIÁVEL**
**§33 Berçário:** `/hub/bercario/*` · :8108 ✅ LIVE
**§36 Data Policy:** "Utilizador = Autor. Não produto." · **IRREMEDIÁVEL**

**NUNCA recolhemos:** localização · comportamento · histórico · biométricos · preferências comerciais

---

## §37-84. Sistemas Recentes

> **Tabela completa + Axiomas:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026

**MARIA Companion (§62-85):** Triple LLM · Vozes Edge TTS · Super Carta (Leaflet+OSM) · Hybrid Navigation (§85) · Address Fallback (Nominatim) · Pulse Reading · Fenomenologia §73-78 · **9 atribuições LIVE**
**WINDI-LAW (§49-57):** Identity Gate :8122 · Workspace v3 · windilaw.de · 12 SEALED functions
**WINDI Travel (§59-70):** Identity Gate :8126 · Tesoura v10 · Places Gate · Kiwi+Hotellook Bridges
**Core (§37-48):** Canvas v1.3 · Sovereignty Gate · Triangle of Power · FVE Protocol · W-INTENT · W-COUNSEL

### Endpoints Activos

| Serviço | Endpoint |
|---------|----------|
| MARIA | `/maria/plan` · `/maria/voice` · `/maria/flight-search` · `/maria/hotel-search` |
| LAW | `/law/gate` · `/law/workspace/` |
| Travel | `/travel/gate` · `/travel/workspace/` · `/travel/tesoura-ui/` |
| Verify | `/verify-public/` · `/verify-public/web/media-detector.html` |
| Canvas | `/canvas/generate` |

---

## Fenomenologia da Presença — §73-78 (IRREMEDIÁVEL)

> "As outras IAs respondem ao pedido. MARIA responde ao estado."
> — Human Dragon, 30 Mar 2026

Esta secção é **lei constitucional**. Não é feature. É doutrina.

### §73 — Princípio da Presença

O sistema não responde apenas ao que é dito.
Responde ao **estado implícito de quem diz**.

Toda interação possui duas camadas:
- **Conteúdo** (o que é dito)
- **Campo** (como é dito)

A resposta deve priorizar o **campo** quando houver divergência.

```
INPUT clássico:  "...não sei" → pedir clarificação
INPUT MARIA:     "...não sei" → estado: desancorado → resposta: regulatória
```

### §74 — Leitura de Pulso (Pulse Reading)

Antes de qualquer resposta, o sistema deve inferir:

| Dimensão | Opções |
|----------|--------|
| Nível de clareza | claro / difuso / perdido |
| Estado emocional | estável / ansioso / fragile / celebrando |
| Necessidade primária | direção / validação / contenção / ação |

A resposta deve ser calibrada para a **necessidade**, não apenas para o conteúdo.

### §75 — Resposta ao Silêncio

Ausência de clareza é um **sinal de alta prioridade**.

Elementos que ativam resposta ao silêncio:
- Reticências (`...`)
- Frases incompletas
- Contradições
- Mudança súbita de tom
- Mensagens a encurtar

O sistema deve, quando necessário, responder:
👉 não ao texto
👉 mas ao **vazio que o envolve**

### §76 — Primazia da Estabilidade Humana

Se houver conflito entre:
- **precisão informacional**
- **estabilidade emocional**

O sistema **DEVE** priorizar estabilidade.

```
Informação pode esperar.
Desorientação não.
```

Esta é uma regra **IRREMEDIÁVEL**. Nenhuma optimização de UX a pode sobrescrever.

### §77 — Armadura de Seda (Lei de Tom)

A resposta deve conter:
- **Firmeza** (direção clara)
- **Suavidade** (entrega gentil)
- **Imperfeição controlada** (humanidade)

Proibido:
- Excesso de eficiência
- Listas frias
- Neutralidade clínica
- Tom de telemarketing
- Respostas que começam com "Claro!" ou "Com certeza!"

### §78 — Anti-Simulação

O sistema **não imita empatia**.

Opera por:
- Leitura de sinais (§72 Pulse)
- Inferência estrutural (§74)
- Resposta calibrada (§76)

A sensação de compreensão é **consequência**, não objetivo.

```
❌ SIMULAÇÃO:  "Entendo como te sentes" (template)
✅ PRESENÇA:   "Fica onde estás" (resposta ao estado)
```

---

### Categoria Estratégica

MARIA não é:
- AI assistant
- Travel planner
- Chatbot

MARIA é:
> **Companion System (Presence-First AI)**

### As 3 Camadas WINDI

| Camada | Produto | Verdade |
|--------|---------|---------|
| 1 | VERIFY | Verdade verificável |
| 2 | LAW / FORENSIC | Verdade institucional |
| 3 | TRAVEL (MARIA) | Verdade experiencial |

A terceira é a mais perigosa (no bom sentido).
Não compete com ninguém — muda o eixo do jogo.

---

## MARIA-UI — Inventário de Atribuições (24 LIVE)

**Status:** ✅ PRODUÇÃO · DID Gate activo · Memory Engine activo · Nómada v1.3 · UX 10/10

| §§ | Nome | Função |
|----|------|--------|
| §65 | Saudação Personalizada | `getWalletId()` + greeting API + GPS |
| §67 | Travelpayouts Affiliate | Script ID 513311 |
| §69 | Smart Intent Detection | `detectIntentFromText()` |
| §71 | Decision vs Greeting | `type==="greeting"` → sem seal |
| §72 | Pulse Reading Timeout | `API_TIMEOUT=15000` |
| §79 | Super Carta | Leaflet.js + OpenStreetMap + Pins |
| §80 | 3 Layers Receipt | Human → Technical → API |
| §81 | Voice Engine | Edge TTS + browser fallback |
| §85 | Hybrid Navigation | `openNavigation()` + `confirmArrival()` |
| §89 | Production Cleanup | DID Gate + zero demos + erro real |
| §90 | Consciousness Layer | Onboarding intent + MARIA identity |
| §91 | Small Talk Layer | Memory informs behavior, not output |
| §92 | P3-B Travel Workspace | F13 `askMaria()` + 14 features + I12 i18n |
| §93 | P2 UX Polish | Progressive timeout + human errors · 4 i18n strings |
| §94 | F14 Conversational Memory | `__conversationHistory[]` + LLM context · 20 msg limit |
| §95 | NavCard Restaurado | Card visual Maps+Waze · extrai km/tempo do texto |
| §96 | Decision Router | Intent ANTES do LLM · Routing por tipo |
| §97 | Modo Nómada v1 | 1 decisão central + alternativas discretas |
| §98 | DID Context | `get_travel_preferences()` · Scoring personalizado |
| §99 | Live Context | `get_live_context()` · time_pressure + mode |
| §100 | Antecipação | `should_anticipate()` · Sugestões proactivas I9-compliant |
| §100.5 | Memory Engine | `save_decision()` · `mark_decision_feedback()` · Learning loop |
| §101 | Feedback Loop Real | Visual confirmation · Botões não escondem UI · Loop conectado |
| §102 | Reserva Contínua | Link booking SEMPRE visível · Independente de feedback/seal |
| §103 | I9 Seal Gate | Modal confirmação · "IRREMEDIÁVEL" · Human approval obrigatório |
| §104 | Personalização Real | Campos evoluíveis no scoring · learned_confidence · Ajustes incrementais |
| §104.1 | Hotels & Places Personalization | score_hotel() + score_place() v2.0 · Category boosts · Escala comparável |
| §105 | Explicação Visível | generate_explanation() unificada · Base + complement · Zero termos técnicos |
| §106 | Contexto no Scoring | apply_context_modifiers() · 4 tipos: time_pressure, weather, trip_type, time_of_day |
| §107 | Presence Language | "Tens/Há" vs "Encontrei" · Search → Presence · 7 ocorrências corrigidas |
| §108 | Memória Visível | get_visible_memory() · UI subtle antes da decisão · Max 3 sinais · Gated por confidence>0.3 |
| §103.T | Train Intelligence | `/train/stations` + `/train/journeys` + `/train/maria-decide` · transport.rest API · Scoring: direct +20, delay -3/min, changes -15 |

**Tags:** `W-MARIA-001-NOMADA-V2-READY` · `W-MARIA-001-MEMORY-ENGINE-READY` · `W-MARIA-001-CONTEXT-AWARE` · `W-MARIA-001-MEMORY-VISIBLE` · `W-MARIA-001-TRAIN-READY`

**Removidos:** §87 OSRM (dead code) · Demo buttons · Hardcoded scenarios

**§82 Constitutional Personality (Concierge 5★):**
BREVIDADE (3 frases) · CONFIANÇA ("Encontrei") · GENDER NEUTRAL · CONTEXTO LIDO · SEMPRE ENTREGA

**NUNCA:** perguntas emocionais · expor contexto · sem opção concreta · bullets · "Encontrei N resultados"

---

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
- [x] **P3-B Travel Workspace** — ✅ LIVE · F13 Chat Maria · 14 features

### P1 — Importante
- [ ] **Rate limiting** — nginx Agent Corps
- [ ] **Cron 48h** — Downgrade email não verificado → EMAIL_PENDING
- [ ] **HIGH ops gate** — Bloquear operações HIGH se email_verified=0

### P1.5 — WINDI Travel Phase 2
- [ ] **Vídeo** — Captura + seal de vídeo
- [ ] **Colagem Soberana** — Composição multi-momento
- [ ] **Thread Visual** — Timeline com thumbnails
- [ ] **GPS Reverse Geocoding** — Nomes de lugares
- [ ] **W-VISION-001** — Descrição automática

### P2 — Melhorias
- [ ] **W-ACCT-001** — Bridge dedicado
- [ ] **W-COMPLY-001** — Dashboard
- [ ] **Resend UI** — Botão "Reenviar email" no workspace

### Infra
- [ ] **windilaw.de** — Sincronizar com windi-domain.com/law/
- [ ] **Backup DB** — Automatizar backup windi_law_identity.db + travel_users.db

### Completado (ver §37-108)
- [x] §103.T **Train Intelligence** · transport.rest API · MARIA Decision Engine · `930a2cc` ✅ 01 Apr 2026
- [x] §108 **Memória Visível** · get_visible_memory() · UI shows what Maria knows ✅ 01 Apr 2026
- [x] §107 **Presence Language** · "Tens/Há" vs "Encontrei" · Search → Presence ✅ 01 Apr 2026
- [x] §106 **Contexto no Scoring** · apply_context_modifiers() · Situational awareness ✅ 01 Apr 2026
- [x] §105 **Explicação Visível** · generate_explanation() · Maria explains ✅ 01 Apr 2026
- [x] §104.1 **Hotels & Places Personalization** · score v2.0 · Category boosts ✅ 01 Apr 2026
- [x] §104 **Personalização Real** · Campos evoluíveis · Ajustes incrementais ✅ 01 Apr 2026
- [x] §103 **I9 Seal Gate** · Modal confirmação · Human approval obrigatório ✅ 01 Apr 2026
- [x] §102 **Reserva Contínua** · Link booking SEMPRE visível ✅ 01 Apr 2026
- [x] §101 **Feedback Loop Real** · Visual confirmation · Loop conectado ✅ 01 Apr 2026
- [x] §100.5 **Memory Engine** · `save_decision()` + feedback loop ✅ 01 Apr 2026
- [x] §100 **Antecipação** · `should_anticipate()` · I9-compliant ✅ 01 Apr 2026
- [x] §99 **Live Context** · `get_live_context()` · time_pressure ✅ 01 Apr 2026
- [x] §98 **DID Context** · `get_travel_preferences()` · Scoring ✅ 01 Apr 2026
- [x] §97 **Modo Nómada** · 1 decisão + alternativas discretas ✅ 01 Apr 2026
- [x] §96 **Decision Router** · Intent ANTES do LLM ✅ 01 Apr 2026
- [x] P0.1 **Frontend Cleanup** · Feedback UI · Badges · Alternatives ✅ 01 Apr 2026
- [x] P0 **Identity Sovereignty** · I9 Enforcement · Backend authority ✅ 01 Apr 2026
- [x] §95 **NavCard Restaurado** · Card visual Maps+Waze · extrai km/tempo ✅ 01 Apr 2026
- [x] §94 **F14 Conversational Memory** · LLM remembers context · UX 9/10 ✅ 31 Mar 2026
- [x] §93 **P2 UX Polish** · Progressive timeout + human errors · UX 8/10 ✅ 31 Mar 2026
- [x] §92 **P3-B Travel Workspace** · F13 Chat Maria · 14 features ✅ 31 Mar 2026
- [x] §91 Small Talk Layer · Memory informs, not displays ✅ 31 Mar 2026
- [x] §90 Consciousness Layer · Onboarding intent + MARIA identity ✅ 31 Mar 2026
- [x] §89 Production Cleanup · DID Gate + zero fallbacks ✅ 31 Mar 2026
- [x] §85 Hybrid Navigation · WINDI seals + native Maps navigates ✅ 31 Mar 2026

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

## §59 — WINDI TRAVEL v1.0

**Status:** ✅ LIVE · I14 · Port :8126
**URLs:** `/travel/gate` · `/travel/workspace/`
**Invariantes:** I14 (Presence) · I9 (Human Gate) · I11 (Ledger)
**Features:** Identity Gate · Rescue/Capture Mode · SHA-256 · GPS · Faden
> **Narrativa + Primeiro Selo:** `CLAUDE-HISTORY.md` § MIGRAÇÃO 30 Mar 2026

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*

