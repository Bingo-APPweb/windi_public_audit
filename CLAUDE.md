# CLAUDE.md — WINDI One Touch
## Institutional Memory & Constitutional Procedures
**Version:** 1.9.10
**Sealed:** 2026-03-17
**Author:** Human Dragon (Jober Mögele Correa) · CGO · WINDI Publishing House
**Location:** Kempten, Bavaria, Deutschland

> **Ficheiros relacionados:** `CHANGELOG.md` (histórico) · `ARCHITECTURE.md` (código técnico)

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

## 13. Estado Actual — 17 Março 2026

### Mapa de Portas

| Porto | Serviço | Estado |
|---|---|---|
| :8091 | Sandbox Core (Agent Corps) | 🟢 LIVE |
| :8100 | Desktop v2.0.0 (legacy) | 🔴 RETIRED |
| :8101 | Forensic Ledger | 🟢 SEALED |
| :8108 | Dragon Hub v1.3.0 | 🟢 LIVE |
| :8119 | Desktop GEN 7 | 🟢 **PRODUÇÃO** |
| :8120 | Pioneer Landing | 🟢 LIVE |
| :8121 | Dispatch Gateway | 🟢 **.jmpg Hydration Engine** · I5+I6+I9 |

### Sistemas LIVE

| Sistema | Status |
|---------|--------|
| GEN 7 Desktop | ✅ Smart Zones + 7 Motores |
| Pioneer Program | ✅ /pioneer/ trilíngue |
| VPR System | ✅ /verify-public/vpr/jober/ |
| API Key System | ✅ W-KEYS-001 SEALED |
| Dispatch Pipeline | ✅ email + whatsapp |
| Web Hosting | ✅ /sites/ + /s/ short URLs |
| i18n Dragon | ✅ PT/DE/EN auto-detect |

### Completado Hoje (17 Mar 2026)

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

## 17. Formato .JMPG — Sovereign File Format

**JMPG** (JOBER Mögele Publishing Governance) é o formato de ficheiro soberano da WINDI.
Não é apenas um contentor — é uma **prova criptográfica ambulante**.

### Estrutura Interna

| Camada | Conteúdo | Função |
|--------|----------|--------|
| **L1** | Payload original | PDF, HTML, imagem, vídeo, áudio |
| **L2** | Metadados governance | actor, timestamp, app, invariants |
| **L3** | SHA-256 hash | Integridade matemática |
| **L4** | Receipt ID | Ligação ao Forensic Ledger |
| **L5** | QR Payload | Verificação offline |
| **L6** | Assinatura Ed25519 | Prova de origem (DID) |

### Vantagens

| Característica | Benefício |
|----------------|-----------|
| Auto-verificável | Qualquer pessoa verifica sem contactar emissor |
| Imutável | Alteração = hash inválido = fraude detectada |
| Offline-capable | QR permite verificação sem internet |
| Jurisdição-agnóstico | Válido em DE/EU/BR/INT |
| Timestamped | Prova de existência num momento específico |

### Aplicações por Área

#### MULTIMEDIA
| Tipo | Problema Resolvido |
|------|-------------------|
| Fotografia | Prova de autoria, anti-deepfake |
| Vídeo | Certificação de footage original |
| Áudio | Podcasts/entrevistas anti-edição |
| 3D/CAD | Designs industriais protegidos |

#### COMMUNIQUÉ
| Tipo | Problema Resolvido |
|------|-------------------|
| Press Releases | Versão oficial imutável |
| Comunicados Internos | Prova de distribuição |
| Contratos | Versão única de verdade |
| Políticas RH | Aceitação documentada |
| Relatórios Financeiros | Números certificados |

#### JURÍDICO
| Tipo | Aplicação |
|------|-----------|
| Contratos | Versão única de verdade |
| Procurações | Validade temporal verificável |
| Evidências | Chain of custody inviolável |
| Notificações | Prova de envio e conteúdo |

#### FINANCEIRO
| Tipo | Aplicação |
|------|-----------|
| Facturas | GoBD/XRechnung compliant |
| Recibos | Prova fiscal imutável |
| Auditorias | Trail completo |

#### SAÚDE
| Tipo | Aplicação |
|------|-----------|
| Receitas médicas | Anti-falsificação |
| Consentimentos | Prova de informed consent |
| Certificados vacinação | Verificação instantânea |

#### EDUCAÇÃO
| Tipo | Aplicação |
|------|-----------|
| Diplomas | Anti-fraude académica |
| Certificados | Verificação por empregadores |
| Portfolios | Autoria verificável |

### Comparação com Alternativas

| Feature | PDF | Blockchain | **.JMPG** |
|---------|-----|------------|-----------|
| Auto-verificável | ❌ | ✅ | ✅ |
| Offline verification | ❌ | ❌ | ✅ |
| Custo/documento | €0 | €0.50-50 | €0 |
| Velocidade | Instant | 1-60min | Instant |
| Privacidade | ✅ | ❌ | ✅ |
| Compliance EU | Parcial | ❓ | ✅ |

### Endpoints WINDI

```
POST /api/onetouch/seal    → Gera .JMPG
GET  /verify-public/?id=   → Verifica receipt
POST /api/export/jmpg      → Download .JMPG
```

### Posicionamento

```
DocuSign    = Assinatura (quem assinou)
Blockchain  = Prova pública (sem privacidade)
.JMPG       = Integridade + Privacidade + Verificação
              + Governance + Offline + Zero-cost

"A prova viaja com o documento."
```

---

## 18. Dispatch Gateway — .jmpg Hydration Engine

**Version:** 1.0.2
**Port:** :8121
**Deployed:** 17 Mar 2026 (v1.0.0) · Updated 17 Mar 2026 21:00 (v1.0.2)
**Invariants:** I5 + I6 + I9
**Performance:** p95=76ms · Throughput ~150 req/s

### Função

O Dispatch Gateway é o motor de hidratação progressiva para ficheiros .JMPG.
Entrega assets em camadas P1→P4 baseado na qualidade da rede do utilizador.

```
Viewer solicita seed_id
        ↓
Gateway verifica I5+I6 contra Ledger (:8101)
        ↓
Detecta network_quality (2g/3g/4g/5g/wifi)
        ↓
Constrói manifest P1→P4
        ↓
Viewer hidrata progressivamente
```

### Network Tier Mapping

| Network | P-Layers | Tier |
|---------|----------|------|
| 2G | P1 only | CORE |
| 3G | P1+P2 | STANDARD |
| 4G | P1+P2+P3 | RICH |
| 5G/WiFi | P1+P2+P3+P4 | VAULT |

### P-Layer Structure

| Layer | Conteúdo | Size | Mandatory |
|-------|----------|------|-----------|
| **P1** | core.json (metadados + texto) | ~45KB | ✅ |
| **P2** | thumb.webp (preview visual) | ~180KB | ✅ |
| **P3** | media.mp4 (vídeo/rich media) | ~12MB | ❌ |
| **P4** | raw.zip (arquivo original) | ~850MB | ❌ |

### Evaporation Policy

| Network | Policy | Significado |
|---------|--------|-------------|
| 5G/WiFi | `session_end` | Assets pesados evaporam ao fechar documento |
| 4G/3G | `immediate` | P3/P4 evaporam quando viewport sai |
| 2G | `none` | Só P1 entregue — nada para evaporar |

### Endpoints

| Endpoint | Método | Função |
|----------|--------|--------|
| `/dispatch/health` | GET | Status do serviço |
| `/dispatch/activate` | POST | Activação principal |
| `/dispatch/verify/{seed_id}` | GET | Quick I5+I6 check |
| `/dispatch/tiers` | GET | Network mapping table |

### Invariant Enforcement

```
I5 — Hash match obrigatório contra Ledger
     Se falhar → 403 I5_INTEGRITY_VIOLATION

I6 — Provenance WINDI obrigatória
     Se falhar → Warning header (ainda permite leitura)

I9 — Gateway nunca activa sem pedido humano
     AI processes. Human decides.
```

### Ficheiros

```
/opt/windi/dispatch/
├── dispatch_gateway.py    (FastAPI gateway)
├── dispatch_stress.py     (Stress test suite)
├── deploy_dispatch.sh     (7-phase deploy)
└── .env                   (PORT, LEDGER_URL, VAULT_URL)
```

### Princípio

> "P1 primeiro. Sempre. O texto + prova chegam instantaneamente.
> O resto hidrata progressivamente enquanto o leitor consome."

---

## 19. JMPG Viewer v2.2 — Antessala Soberana

**Version:** 2.2
**URL:** `https://windi-domain.com/verify-public/viewer/v2.2/`
**Deployed:** 17 Mar 2026 21:00
**Size:** 42KB

### Função

O JMPG Viewer é o visualizador verificável para ficheiros .JMPG.
A versão 2.2 introduz a **Antessala Soberana** — verificação forense antes de mostrar conteúdo.

### Antessala — 4 Fases

```
Fase 0 → Leitura do pacote ZIP
        ↓
Fase 1 → SHA-256 local (canonicalized JSON)
        ↓
Fase 2 → Consulta ao Ledger Forense via GET /api/verify/{receipt_id}
        ↓
Fase 3 → Avaliação I5 — se falhar, documento EVAPORA antes de ser lido
```

### Selo em Tempo Real

| Badge | Significado |
|-------|-------------|
| 🟢 Verified | I5 pass — documento íntegro |
| 🟡 Offline | Ledger inacessível — abre em modo offline |
| 🔴 Falha | I5 fail — documento corrompido ou adulterado |

### Features

- **Schema dual:** suporta formato v1.0 + legacy
- **Dispatch Tray:** 5 canais de partilha no rodapé
- **Offline-aware:** não bloqueia leitor se Ledger indisponível

### Ficheiros

```
/opt/windi/verify-public/viewer/v2.2/
└── index.html    (42KB — standalone viewer)
```

---

## 20. Jornal Composer v4 — Smart Zones

**Version:** 4.0
**URL:** `https://windi-domain.com/jornal/`
**Deployed:** 17 Mar 2026 21:00
**Size:** 64KB

### Função

O Jornal Composer é o editor de publicações jornalísticas da WINDI.
A versão 4 introduz o **Agent Invocation Panel** com 5 canais de dispatch.

### Smart Zones Layout

```
┌─────────────────────────────────────────────────────────────┐
│ G4 — TOPBAR — Edição, Preview, Export, 🚀 Despachar        │
├─────────────────────────────────────────────────────────────┤
│ G1 — Canvas    │ G2 — Block Palette │ G3 — Inspector       │
│ (Documento)    │ (Blocos + Drag)     │ (Propriedades)       │
└─────────────────────────────────────────────────────────────┘
```

### Agent Invocation Panel — 5 Canais

| Canal | Bloco | Função |
|-------|-------|--------|
| 💬 WhatsApp P1 | A | Link de verificação via wa.me |
| 🔗 Link Público P2 | A | URL para clipboard |
| 🗄 Archive P3 | B | Export HTML download imediato |
| 📡 Feed API P4 | C | POST `/dispatch/api/dispatch` |
| 🏛 Institucional P4 | C | Abre Workspace WINDI |

### Campos Multimédia Reais

| Tipo | Campo | Limite |
|------|-------|--------|
| **Imagem** | URL + upload local | 5MB (base64) |
| **Vídeo** | YouTube/Vimeo/MP4 (auto-detect) | URL embed |
| **Áudio** | URL + upload local | 20MB (auto-duration) |

### Blocos Disponíveis

- `hero` — Imagem de capa (16:9)
- `headline` — Título principal
- `body` — Texto rico
- `image` — Imagem com caption
- `video` — Embed YouTube/Vimeo/MP4
- `audio` — Player nativo com waveform
- `ocr` — Texto digitalizado de scan
- `quote` — Citação destacada
- `kicker` — Lead/subtítulo

### Ficheiros

```
/opt/windi/jornal/
└── jornal-composer.html    (64KB — standalone composer)
```

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

*LIGA IA+H — Kempten, Bavaria · 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
*"AI processes. Human decides. WINDI guarantees."*
