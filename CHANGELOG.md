# CHANGELOG.md — WINDI One Touch
## Histórico de Milestones

---

## 17 Março 2026

| Milestone | Hora |
|---|---|
| **CLAUDE.md v1.9.0** — Refactor 45k→15k chars | 08:00 |
| CHANGELOG.md criado | 08:00 |
| ARCHITECTURE.md criado | 08:00 |
| **i18n Fix** — detect_language() respeita EN | 08:15 |
| Dragon restart + validação PT/DE/EN | 08:15 |
| **CLAUDE.md v1.9.1** | 08:20 |
| **Canvas ← Novo** — botão toolbar G2 | 08:30 |
| URL Fix: /app/api/dragon → /api/dragon | 08:30 |
| History Fix: human→user, text→content | 08:30 |
| **How it Works Landing** — /how-it-works/ LIVE | 10:55 |
| nginx patch + reload | 10:55 |
| **CLAUDE.md v1.9.2** | 10:55 |
| Nav link adicionado à landing principal | 11:00 |
| i18n: EN/DE/PT para "How it Works" | 11:00 |
| Nav link na header GEN 7 `/desktop/` | 11:05 |
| i18n sync: localStorage `windi-lang` | 11:10 |
| Back button trilíngue (← Voltar/Zurück/Back) | 11:15 |
| **§11.2 FRONTEND INVARIANTS** — i18n + NOIR/KLAR | 11:20 |
| Theme toggle ☀/☽ na `/how-it-works/` | 11:30 |
| CSS vars [data-theme="noir"] + [data-theme="klar"] | 11:30 |
| localStorage `windi-theme` sync | 11:30 |
| **CLAUDE.md v1.9.4** | 11:35 |

---

## 16 Março 2026

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
| email_sender import directo (dispatch) | 15:54 |
| DestinationsModel (Pydantic) | 15:54 |
| /api/onetouch/dispatch LIVE | 15:54 |
| **📧 DISPATCH PIPELINE LIVE** | **15:55** |
| **CLAUDE.md v1.8.5** | **16:00** |
| P1: Canvas scroll (overflow-y: auto) | 20:05 |
| P2: mailto ban (WEB + MEDIA prompts) | 20:08 |
| P3: exportWebStandalone() + 💾 button | 20:15 |
| P3: POST /api/export/web endpoint | 20:18 |
| P3: Ledger seal 201 fix | 20:22 |
| **🌐 WEB ENGINE P1+P2+P3 LIVE** | **20:25** |
| **CLAUDE.md v1.8.6** | **20:30** |
| P4A: nginx /sites/ + systemd patch | 21:29 |
| P4B: OG tags (og:title, og:image) | 21:25 |
| P4C: Short URL /s/{id} redirect | 21:29 |
| P4D: 📡 Publicar + 📲 WhatsApp buttons | 21:25 |
| POST /api/publish/web endpoint | 21:25 |
| **🚀 P4 WINDI HOSTING LIVE** | **21:30** |
| **CLAUDE.md v1.8.7** | **21:35** |
| Canvas debug logs (8 checkpoints) | 22:25 |
| EnvironmentFile fix (.env.gen7 clean) | 22:42 |
| Motor WEB timeout 15s→60s | 22:45 |
| Sanitize ```html wrapper | 22:48 |
| **🐉 MOTOR WEB OPERACIONAL — 13677 chars** | **22:50** |
| Footer placement fix (receipt separado) | 22:55 |
| **🎉 PIPELINE E2E COMPLETO** | **23:00** |
| **CLAUDE.md v1.8.8** | **23:05** |

---

## 15 Março 2026

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

---

## Receipts Selados

| Receipt ID | Data | Tipo |
|------------|------|------|
| WINDI-VIRTUE-ONEWOW-20260314 | 15 Mar 2026 | Marketing Milestone |
| WINDI-PAR-GENESIS-20260315 | 15 Mar 2026 | Pioneer Genesis |
| WINDI-PIONEER-MANIFESTO-20260315 | 15 Mar 2026 | Manifesto |

---

*Histórico completo de milestones — ver CLAUDE.md para estado actual*
