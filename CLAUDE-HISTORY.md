# WINDI — Histórico Institucional
# Arquivo vivo. Append-only. Nunca editar entradas seladas.
# Criado: 17 Mar 2026 — migrado de CLAUDE.md por overflow (45.2k → 32k)
#
# REGRA: CLAUDE.md = presente + futuro (≤ 32KB)
#        CLAUDE-HISTORY.md = passado selado (ilimitado)
# ---

## § SESSÃO 17 Mar 2026
**Commits:** a3accb5 · f1603d7 · a30360e
**CLAUDE.md:** v1.9.10

### Deployado
- Dispatch Gateway v1.0.2 — p95=76ms (28x boost), :8121
- JMPG Viewer v2.2 — Antessala 4 fases, I5 enforcement
- Jornal Composer v4 — 5 canais dispatch, multimédia real
- DID Wallet Modal FASE 1 — login gate, sessionStorage, API real

### Lições Aprendidas
- heredoc falha com JS `${}` e `Math.floor` → usar python3 r-string
- Relatório do Gêmeo é obrigatório — paths reais diferem do curl remoto
- desktop-gen7/frontend/ ≠ desktop/ (confirmado)
- nginx sites-enabled must be kept in sync with sites-available

### Pending → FASE 2
- G1: OneTouch wallet_id injection
- G2: Ledger seal attribution
- G4: Trust score increments with receipts

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

---
*Migrado de CLAUDE.md 17 Mar 2026 22:50*

---

## § SESSÃO 18 Mar 2026
**Commits:** 9ab7548 · 72dac22
**CLAUDE.md:** v1.9.12 → v1.9.13

### Missão Principal
Documentar e selar as métricas de soberania do WINDI — quanto o sistema "aprendeu" a reduzir dependência de LLM externo.

### Investigação Realizada
- Auditado `sovereign_router.py` em `/opt/windi/agent-palette/`
- Extraídas métricas do audit ref: AUDIT-SOVEREIGNTY-20260224
- Calculado progresso de redução de tokens externos

### Métricas Descobertas

| Métrica | Valor |
|---------|-------|
| Total funções | 45 |
| Funções locais | 42 (93.3%) |
| Funções semânticas | 3 (6.7%) — requerem LLM externo |
| Baseline tokens | 4000 tk/sessão |
| Meta tokens | 1500 tk/sessão |
| Actual tokens | ~268 tk/sessão |
| **Progresso** | **149.3%** ✓ META ULTRAPASSADA |

### As 3 Funções Semânticas (ainda requerem LLM externo)

| Intent | Fallback Local | Handler |
|--------|----------------|---------|
| `CHAT_INTERPRETIVE` | `HELP` | llm_semantic |
| `SEMANTIC_ANALYSIS` | `CHECK_RISK` | llm_semantic |
| `TEXT_GENERATION` | `HELP` | llm_semantic |

### Deployado

| Item | Descrição |
|------|-----------|
| §22 Sovereignty Metrics | Documentação I13 Token Independence em CLAUDE.md |
| §23 Qualidade Soberana | Princípio constitucional + Wisdom Block selado |
| Espelho HTML | `/opt/windi/docs/espelho-qualidade-soberana.html` |
| Wisdom Block | WB-KNOW-SOVEREIGNTY-Q-20260318 · HIGH · Ledger :8101 |
| SKILL.md | Instalado no sistema Claude Code |

### Wisdom Block Selado

```
ID:          WB-KNOW-SOVEREIGNTY-Q-20260318
Actor:       human_dragon
App:         windi-wisdom
Doc:         Espelho de Qualidade Soberana v1.0
Governance:  HIGH
Hash:        sha256:66d542fcc2118f8e174f32d0c9caea336205dc3f73ee735122149fe9716e2d3b
Invariants:  I1, I9, I10, I11
Princípio:   "Economy enables Quality"
Frase:       "O externo sustenta. O interno orienta. A qualidade decide."
```

### Lições Aprendidas

1. **Ledger API** requer `content_hash` e `sge_score` (numérico, não string "R1")
2. **Git rebase** com ficheiros untracked conflituantes → remover local antes de pull
3. **Dois CLAUDE.md** existem: `/home/windi/` (repo git) e `/opt/windi/` (deploy) — usar o do repo
4. **Fórmula de soberania:**
   ```
   Tokens Externos = BASELINE × (1 - SOVEREIGNTY_RATIO)
   Progresso = (BASELINE - ACTUAL) / (BASELINE - META) × 100
   ```

### Impacto do Wisdom Block

O WB-KNOW-SOVEREIGNTY-Q-20260318 transforma "economizar tokens" de uma restrição numa **estratégia de qualidade**:
- FREE = escudo absoluto, zero LLM externo
- Token externo = investimento justificado por qualidade superior
- Fallback I10: SEMANTIC→LOCAL sempre disponível
- Wisdom Blocks crescem → tokens externos diminuem ao longo do tempo

---

### W-MGR-001 — Gerente do Composer

**Deployed:** 18 Mar 2026
**Ficheiro:** `/opt/windi/jornal/jornal-composer.html`
**Linhas adicionadas:** +222 (CSS + HTML + JS)

#### Arquitectura

```
jornal-composer.html
└── W-MGR-001 (injectado como script)
    ├── OBSERVER   → monitoriza estado dos blocos
    ├── ANALYSER   → detecta padrões / gaps
    ├── ROUTER     → decide sugestão por prioridade
    └── NOTIFIER   → sugere via HUD não-intrusivo
```

#### 4 Situações Detectadas

| Situação | Trigger | Acção Sugerida |
|----------|---------|----------------|
| Canvas vazio | `blocks.length === 0` após 2min | + Capa |
| Sem Evidence | Artigo sem bloco evidence | + Evidências |
| Sem Capa | 2+ blocos sem hero | + Capa |
| Sem Trust | 4+ blocos sem trust | + Trust Ribbon |

#### Componentes Implementados

| Componente | Descrição |
|------------|-----------|
| CSS `.mgr-*` | 26 linhas, usa design system WINDI |
| Botão topbar | `● MGR` junto ao CIA |
| HUD flutuante | Bottom-right, auto-dismiss 30s |
| i18n | DE/EN/PT completo |
| Integração CIA | `MGR.logToCIA()` silent POST |

#### Princípio Constitucional

> "O Gerente observa o que o Humano não consegue ver.
>  Propõe o que o Humano pode não saber.
>  Decide apenas quem tem o Toque Final." (I9)

#### Checklist Validado

- [x] Canvas vazio 2min → sugestão aparece
- [x] Sugestão auto-dismiss após 30s
- [x] Botão ✓ Sim executa acção
- [x] Botão Dispensar fecha sem acção
- [x] Máximo 1 sugestão simultânea
- [x] `● MGR` visível no topbar
- [x] I9 respeitado — nunca executa sem confirmação
- [x] Log enviado ao CIA endpoint

---
*Registado por Gêmeo · 18 Mar 2026 · OM SHANTI 🐉*
