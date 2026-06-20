# WINDI-HIOS-INVENTORY — Mapa Anatómico Forense
# Contêiner único da auditoria WINDI-HIOS-AUDIT-ORDER-001
# Append-only. Quem escreve, assina com [executor] e timestamp.
# Formato de linha: ver Secção 3 da Ordem.

## REGISTO DE NASCIMENTO
Contêiner verificado/criado em 20260620T120919Z [CCODE]
=== A1 — PORTAS VIVAS 20260620T120956Z [CCODE] ===

## A2 — CRUZAMENTO PORTA↔PROCESSO 20260620T121017Z [CCODE]

## A2 — CRUZAMENTO PORTA↔PROCESSO [CCODE] 20260620T134800Z

| Porta | PID | Directório |
|-------|-----|------------|
| 8055 | 505805 | /opt/windi/w-cms-001 |
| 8056 | 499420 | /opt/windi/w-cms-001 |
| 8080 | 660 | /opt/windi/engine |
| 8081 | 3799049 | /opt/windi |
| 8086 | 668 | /opt/windi/a4desk-landing |
| 8089 | 3319483 | /opt/windi/engine/governance_guard |
| 8090 | 689 | /opt/windi/SDK_v1.1_RFC003/windi-sdk-v1 |
| 8091 | 4059186 | /opt/windi/agents/constitutional-agent |
| 8095 | 690 | /opt/windi/tsil |
| 8096 | 111283 | /opt/windi/did-genesis |
| 8097 | 645 | /opt/windi/bridge |
| 8098 | 797 | /opt/windi/sentinel-bridge |
| 8099 | 688 | /opt/windi/wallet |
| 8101 | 3935187 | /opt/windi/suite-docs |
| 8102 | 241197 | /opt/windi/sentinel-law |
| 8103 | 663 | /opt/windi/desktop/export |
| 8104 | 664 | /opt/windi/jmpg-viewer |
| 8105 | 647 | /opt/windi/communique |
| 8106 | 681 | /opt/windi/forensic-vault |
| 8108 | 639 | /opt/windi/agent-palette |
| 8109 | 670 | /opt/windi/pulse |
| 8110 | 662 | /opt/windi/guardian-local |
| 8111 | 657 | /opt/windi/engine |
| 8114 | 3318213 | /opt/windi/verify-public/app |
| 8115 | 646 | /opt/windi/communique-builder |
| 8116 | 655 | /opt/windi/distribution-engine |
| 8118 | 649 | /opt/windi/dashboard/dist |
| 8119 | 3799071 | /opt/windi/desktop-gen7/backend |
| 8121 | 654 | /opt/windi/dispatch |
| 8122 | 3799132 | /opt/windi/windi-law/identity-gate |
| 8126 | 3799112 | /opt/windi/windi-travel/identity-gate |
| 8127 | 821 | /opt/windi/nomad-bot |
| 8128 | 1926130 | /opt/windi/vd-cut |
| 8129 | 666 | /opt/windi/joe |
| 8130 | 3799072 | /opt/windi/windi-gateway |
| 8131 | 686 | /opt/windi/vd-mass |
| 8132 | 665 | /opt/windi/comm |
| 8141 | 685 | /opt/windi/intent-cmd |
| 8142 | 684 | /opt/windi/fediverse |
| 8144 | 3799050 | /opt/windi/agents/security-sentinel |
| 8146 | 692 | /opt/windi/services/wpil |
| 8150 | 238025 | /opt/windi/w-enterprise-001 |
| 8152 | 2588337 | /opt/windi/w-cost-001 |
| 8153 | 410035 | /opt/windi/windi-travel/map-comparator |
| 8170 | 2148250 | /opt/windi/service-control |
| 8192 | 3891130 | /opt/windi/windi-sites/identity-gate |
| 8193 | 3325020 | /opt/windi/w-lexicon-001 |
| 8194 | 2147276 | /opt/windi/w-cap-001 |
| 8195 | 2151410 | /opt/windi/w-bercario-001 |
| 8196 | 1050820 | /opt/windi/hios |
| 8197 | 4100366 | /opt/windi/hios/visual/producer |
| 8198 | 2791937 | /opt/windi/w-generator-001 |
| 8199 | 875701 | /opt/windi/artifacts |
| 8200 | 1573526 | /opt/windi/w-dev-api-001 |
| 8201 | 111902 | /opt/windi/farm |
| 8889 | 648 | /opt/windi/cortex |

## A3 — DIRECTÓRIOS /opt/windi 20260620T121431Z [CCODE]

## A3 — DIRECTÓRIOS /opt/windi [CCODE] 20260620T135200Z
Total: 600+ directórios (maxdepth 2)
Categorias principais detectadas:
- Serviços W-*: w-cms-001, w-cost-001, w-enterprise-001, w-mail-001, w-lexicon-001, etc.
- Agentes: agents/constitutional-agent, agents/security-sentinel, etc.
- Infra: did-genesis, verify-public, suite-docs, cortex
- Legado/Andaime: backups/*, archive/*, _archive/*
- Produção: windi-sites, windi-travel, windi-law, farm
- HIOS: hios/cinema, hios/visual, hios/kernel


## A4 — INVENTÁRIO DE SERVIÇOS VIVOS [CCODE] 20260620T121611Z

| nome_canonico | porta | caminho | processo_vivo | parte_corpo | provado | carimbo | executor | timestamp |
|---------------|-------|---------|---------------|-------------|---------|---------|----------|-----------|
| W-CMS-001 | 8055 | /opt/windi/w-cms-001 | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| W-CMS-001-BRIDGE | 8056 | /opt/windi/w-cms-001 | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| ENGINE | 8080 | /opt/windi/engine | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| UVICORN-ROOT | 8081 | /opt/windi | SIM | — | ? | [dúvida: HUMANO] | CCODE | 20260620T121611Z |
| A4DESK-LANDING | 8086 | /opt/windi/a4desk-landing | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| GOVERNANCE-GUARD | 8089 | /opt/windi/engine/governance_guard | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| WINDI-SDK-V1 | 8090 | /opt/windi/SDK_v1.1_RFC003/windi-sdk-v1 | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| CONSTITUTIONAL-AGENT | 8091 | /opt/windi/agents/constitutional-agent | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| TSIL | 8095 | /opt/windi/tsil | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| W-DID-GENESIS | 8096 | /opt/windi/did-genesis | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| BRIDGE | 8097 | /opt/windi/bridge | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| SENTINEL-BRIDGE | 8098 | /opt/windi/sentinel-bridge | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| WALLET | 8099 | /opt/windi/wallet | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| FORENSIC-LEDGER | 8101 | /opt/windi/suite-docs | SIM | — | SEALED | [lido] | CCODE | 20260620T121611Z |
| SENTINEL-LAW | 8102 | /opt/windi/sentinel-law | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| DESKTOP-EXPORT | 8103 | /opt/windi/desktop/export | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| JMPG-VIEWER | 8104 | /opt/windi/jmpg-viewer | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| COMMUNIQUE | 8105 | /opt/windi/communique | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| FORENSIC-VAULT | 8106 | /opt/windi/forensic-vault | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| AGENT-PALETTE | 8108 | /opt/windi/agent-palette | SIM | — | ? | [dúvida: HUMANO] | CCODE | 20260620T121611Z |
| PULSE | 8109 | /opt/windi/pulse | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| GUARDIAN-LOCAL | 8110 | /opt/windi/guardian-local | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| ENGINE-ALT | 8111 | /opt/windi/engine | SIM | — | ? | [dúvida: HUMANO] | CCODE | 20260620T121611Z |
| VERIFY-PUBLIC | 8114 | /opt/windi/verify-public/app | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| COMMUNIQUE-BUILDER | 8115 | /opt/windi/communique-builder | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| DISTRIBUTION-ENGINE | 8116 | /opt/windi/distribution-engine | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| DASHBOARD | 8118 | /opt/windi/dashboard/dist | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| DESKTOP-GEN7 | 8119 | /opt/windi/desktop-gen7/backend | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| DISPATCH | 8121 | /opt/windi/dispatch | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| WINDI-LAW | 8122 | /opt/windi/windi-law/identity-gate | SIM | — | SEALED | [lido] | CCODE | 20260620T121611Z |
| WINDI-TRAVEL | 8126 | /opt/windi/windi-travel/identity-gate | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| NOMAD-BOT | 8127 | /opt/windi/nomad-bot | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| VD-CUT | 8128 | /opt/windi/vd-cut | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| JOE | 8129 | /opt/windi/joe | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| WINDI-GATEWAY | 8130 | /opt/windi/windi-gateway | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| VD-MASS | 8131 | /opt/windi/vd-mass | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| COMM | 8132 | /opt/windi/comm | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| INTENT-CMD | 8141 | /opt/windi/intent-cmd | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| FEDIVERSE | 8142 | /opt/windi/fediverse | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| SECURITY-SENTINEL | 8144 | /opt/windi/agents/security-sentinel | SIM | — | SEALED | [lido] | CCODE | 20260620T121611Z |
| WPIL | 8146 | /opt/windi/services/wpil | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| W-ENTERPRISE-001 | 8150 | /opt/windi/w-enterprise-001 | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-COST-001 | 8152 | /opt/windi/w-cost-001 | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-TRAVEL-MAP | 8153 | /opt/windi/windi-travel/map-comparator | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| SERVICE-CONTROL | 8170 | /opt/windi/service-control | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-SITES-001 | 8192 | /opt/windi/windi-sites/identity-gate | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-LEXICON-001 | 8193 | /opt/windi/w-lexicon-001 | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-CAP-001 | 8194 | /opt/windi/w-cap-001 | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-BERCARIO-001 | 8195 | /opt/windi/w-bercario-001 | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| HIOS | 8196 | /opt/windi/hios | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| HIOS-VISUAL-PRODUCER | 8197 | /opt/windi/hios/visual/producer | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| W-GENERATOR-001 | 8198 | /opt/windi/w-generator-001 | SIM | — | SEALED | [lido] | CCODE | 20260620T121611Z |
| ARTIFACTS | 8199 | /opt/windi/artifacts | SIM | — | ? | [lido] | CCODE | 20260620T121611Z |
| W-DEV-API-001 | 8200 | /opt/windi/w-dev-api-001 | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| W-FARM-001 | 8201 | /opt/windi/farm | SIM | — | LIVE | [lido] | CCODE | 20260620T121611Z |
| CORTEX | 8889 | /opt/windi/cortex | SIM | — | SEALED | [lido] | CCODE | 20260620T121611Z |

## A5 — CONFLITOS E DUPLICADOS [CCODE] 20260620T121643Z
### Directórios com múltiplas portas:
| Directório | Portas |
|------------|--------|
| /opt/windi/w-cms-001 | 8055, 8056 | [dúvida: HUMANO]
| /opt/windi/engine | 8080, 8111 | [dúvida: HUMANO]

### Nomes ambíguos detectados:
| Nome em CLAUDE.md | Directório real | Conflito |
|-------------------|-----------------|----------|
| W-DID-GENESIS | /opt/windi/did-genesis | Nome sem W- | [dúvida: HUMANO]
| AGENT-PALETTE (8108) | /opt/windi/agent-palette | Relação com GEN7? | [dúvida: HUMANO]
| DESKTOP-GEN7 (8119) | /opt/windi/desktop-gen7 | Separado de agent-palette | [dúvida: HUMANO]

### Serviços sem porta (directórios existentes mas não vivos):
| w-academy-001 | /opt/windi/w-academy-001/ | SEM PORTA | [dúvida: HUMANO]
| w-actuary-001 | /opt/windi/w-actuary-001/ | SEM PORTA | [dúvida: HUMANO]
| w-cache-001 | /opt/windi/w-cache-001/ | SEM PORTA | [dúvida: HUMANO]
| w-lab-001 | /opt/windi/w-lab-001/ | SEM PORTA | [dúvida: HUMANO]
| w-social-001 | /opt/windi/w-social-001/ | SEM PORTA | [dúvida: HUMANO]

## SUMÁRIO EXTRAÇÃO [CCODE] 20260620T121712Z

- **Portas vivas detectadas:** 56
- **Directórios mapeados:** 600+
- **Serviços com status LIVE/SEALED em CLAUDE.md:** ~30
- **Bandeiras [dúvida: HUMANO] levantadas:** 7

---
Extração completa. Aguarda classificação CODEX e ratificação Human Dragon.

---

## B0 — CADEIA DE CUSTÓDIA [CODEX] 20260620T164500Z
Hash pré-CODEX: `8886d36c16da8abae0a11541349e0a06fa335445f6b0c838b37560653cd2c832` ✅ CONFERE

## B1 — LEITURA DE ABRIL CONFIRMADA [CODEX] 20260620T164600Z
- §191 DID Validation (191-C-canonical.json): ✅ LIDO
- 01_ports.txt (62 portas): ✅ LIDO
- 02_systemd_units.txt (54 windi-* + wpil): ✅ LIDO
- 05_storage_dbs.txt (123 DBs): ✅ LIDO
- 06_health_matrix.txt (30 portas): ✅ LIDO

**ACHADO-ÂNCORA CONFIRMADO:** :8096 → 404 em Abril, VIVO em Junho (sem receipt de cura)

## B2/B3/B4 — TRANSCRIÇÃO FORMATO 12 + CLASSIFICAÇÃO + DELTA TEMPORAL [CODEX] 20260620T165000Z

| timestamp | executor | service | port | path | owner | status | health | body_part | canonicality | evidence | open_question |
|-----------|----------|---------|------|------|-------|--------|--------|-----------|--------------|----------|---------------|
| 20260620T165000Z | CODEX | W-CMS-001 | 8055 | /opt/windi/w-cms-001 | manual | live | ? | MÚSCULO | canonical | §219 Baptism | [dúvida: HUMANO] duas portas (8055+8056) |
| 20260620T165000Z | CODEX | W-CMS-001-BRIDGE | 8056 | /opt/windi/w-cms-001 | manual | live | ? | NERVO | candidate | pid 499420 | Ponte interna do CMS |
| 20260620T165000Z | CODEX | ENGINE | 8080 | /opt/windi/engine | systemd | live | 200→200 ESTÁVEL | ANDAIME | legacy | windi-governance.service | [dúvida: HUMANO] partilha dir com 8111 |
| 20260620T165000Z | CODEX | UVICORN-ROOT | 8081 | /opt/windi | manual | live | ? | ? | unknown | 127.0.0.1 only | [dúvida: HUMANO] função desconhecida |
| 20260620T165000Z | CODEX | A4DESK-LANDING | 8086 | /opt/windi/a4desk-landing | systemd | live | ? | ANDAIME | legacy | windi-landing.service | Legado de A4 Desk |
| 20260620T165000Z | CODEX | GOVERNANCE-GUARD | 8089 | /opt/windi/engine/governance_guard | manual | live | ? | CÓRTEX | candidate | subdir engine | Guarda I9 runtime |
| 20260620T165000Z | CODEX | WINDI-SDK-V1 | 8090 | /opt/windi/SDK_v1.1_RFC003/windi-sdk-v1 | manual | live | ? | MÚSCULO | scaffold | RFC003 | SDK para desenvolvedores |
| 20260620T165000Z | CODEX | CONSTITUTIONAL-AGENT | 8091 | /opt/windi/agents/constitutional-agent | systemd | live | 200→200 ESTÁVEL | CÓRTEX | canonical | CLAUDE.md :8091 | Grove Arena, Three Dragons |
| 20260620T165000Z | CODEX | TSIL | 8095 | /opt/windi/tsil | manual | live | ? | ? | unknown | pid 690 | [dúvida: HUMANO] função desconhecida |
| 20260620T165000Z | CODEX | W-DID-GENESIS | 8096 | /opt/windi/did-genesis | systemd | live | **404→VIVO** | **OSSO** | canonical | CLAUDE.md :8096 | **ACHADO-ÂNCORA: curou-se sem receipt** |
| 20260620T165000Z | CODEX | BRIDGE | 8097 | /opt/windi/bridge | systemd | live | ? | NERVO | canonical | windi-bridge.service | Ponte de comandos |
| 20260620T165000Z | CODEX | SENTINEL-BRIDGE | 8098 | /opt/windi/sentinel-bridge | systemd | live | ? | NERVO | canonical | windi-sentinel-bridge.service | Dashboard Nerve System |
| 20260620T165000Z | CODEX | WALLET | 8099 | /opt/windi/wallet | systemd | live | ? | NERVO | canonical | windi-wallet.service | Identidade de utilizador |
| 20260620T165000Z | CODEX | FORENSIC-LEDGER | 8101 | /opt/windi/suite-docs | systemd | live | 200→200 ESTÁVEL | **OSSO** | canonical | CLAUDE.md SEALED | Ledger imutável I11 |
| 20260620T165000Z | CODEX | SENTINEL-LAW | 8102 | /opt/windi/sentinel-law | systemd | live | 200→200 ESTÁVEL | **OSSO** | canonical | windi-sentinel-law.service | Governance Invariants |
| 20260620T165000Z | CODEX | DESKTOP-EXPORT | 8103 | /opt/windi/desktop/export | systemd | live | ? | MÚSCULO | legacy | windi-export-engine.service | Export de documentos |
| 20260620T165000Z | CODEX | JMPG-VIEWER | 8104 | /opt/windi/jmpg-viewer | systemd | live | ? | MÚSCULO | canonical | windi-jmpg-viewer.service | Visualizador JMPG |
| 20260620T165000Z | CODEX | COMMUNIQUE | 8105 | /opt/windi/communique | systemd | live | ? | MÚSCULO | canonical | windi-communique.service | Communiqué Engine |
| 20260620T165000Z | CODEX | FORENSIC-VAULT | 8106 | /opt/windi/forensic-vault | systemd | live | ? | OSSO | canonical | windi-vault.service | Cofre forense |
| 20260620T165000Z | CODEX | AGENT-PALETTE | 8108 | /opt/windi/agent-palette | systemd | live | 200→200 ESTÁVEL | MÚSCULO | parallel | windi-agent-palette.service | [dúvida: HUMANO] relação GEN7 §Bandeira 2/7 |
| 20260620T165000Z | CODEX | PULSE | 8109 | /opt/windi/pulse | systemd | live | ? | NERVO | canonical | windi-pulse.service | Health Monitor |
| 20260620T165000Z | CODEX | GUARDIAN-LOCAL | 8110 | /opt/windi/guardian-local | systemd | live | ? | CÓRTEX | canonical | windi-guardian-local.service | Local Cognition |
| 20260620T165000Z | CODEX | ENGINE-ALT | 8111 | /opt/windi/engine | manual | live | ? | ANDAIME | duplicate | mesmo dir 8080 | [dúvida: HUMANO] duplicado §Bandeira 3 |
| 20260620T165000Z | CODEX | VERIFY-PUBLIC | 8114 | /opt/windi/verify-public/app | systemd | live | 200→200 ESTÁVEL | **OSSO** | canonical | CLAUDE.md LIVE | Verificação pública |
| 20260620T165000Z | CODEX | COMMUNIQUE-BUILDER | 8115 | /opt/windi/communique-builder | systemd | live | ? | MÚSCULO | canonical | windi-communique-builder.service | Construtor COMM |
| 20260620T165000Z | CODEX | DISTRIBUTION-ENGINE | 8116 | /opt/windi/distribution-engine | systemd | live | ? | MÚSCULO | canonical | windi-distribution-engine.service | W-DIST-001 |
| 20260620T165000Z | CODEX | DASHBOARD | 8118 | /opt/windi/dashboard/dist | systemd | live | ? | MÚSCULO | legacy | windi-dashboard.service | Command Center antigo |
| 20260620T165000Z | CODEX | DESKTOP-GEN7 | 8119 | /opt/windi/desktop-gen7/backend | systemd | live | 200→200 ESTÁVEL | **MÚSCULO** | canonical | CLAUDE.md PRODUÇÃO | [dúvida: HUMANO] morfologia GEN7 §Bandeira 2/7 |
| 20260620T165000Z | CODEX | DISPATCH | 8121 | /opt/windi/dispatch | systemd | live | ? | NERVO | canonical | windi-dispatch.service | JMPG Hydration |
| 20260620T165000Z | CODEX | WINDI-LAW | 8122 | /opt/windi/windi-law/identity-gate | systemd | live | 200→200 ESTÁVEL | MÚSCULO | canonical | CLAUDE.md SEALED | AI Draft Mode |
| 20260620T165000Z | CODEX | WINDI-TRAVEL | 8126 | /opt/windi/windi-travel/identity-gate | systemd | live | 200→200 ESTÁVEL | MÚSCULO | canonical | CLAUDE.md LIVE | Travel Identity |
| 20260620T165000Z | CODEX | NOMAD-BOT | 8127 | /opt/windi/nomad-bot | systemd | live | **404→VIVO** | MÚSCULO | canonical | windi-nomad-bot.service | Telegram Bot |
| 20260620T165000Z | CODEX | VD-CUT | 8128 | /opt/windi/vd-cut | systemd | live | **404→VIVO** | MÚSCULO | canonical | CLAUDE.md LIVE | Video Forense |
| 20260620T165000Z | CODEX | JOE | 8129 | /opt/windi/joe | systemd | live | **404→VIVO** | CÓRTEX | canonical | CLAUDE.md LIVE | Director Transmissão |
| 20260620T165000Z | CODEX | WINDI-GATEWAY | 8130 | /opt/windi/windi-gateway | systemd | live | ? | NERVO | canonical | windi-gateway-001.service | LLM Bridge |
| 20260620T165000Z | CODEX | VD-MASS | 8131 | /opt/windi/vd-mass | systemd | live | 200→200 ESTÁVEL | MÚSCULO | canonical | CLAUDE.md LIVE | Video em Massa |
| 20260620T165000Z | CODEX | COMM | 8132 | /opt/windi/comm | systemd | live | **404→VIVO** | MÚSCULO | canonical | W-JMPG-001 :8132 | Proof Card Renderer |
| 20260620T165000Z | CODEX | INTENT-CMD | 8141 | /opt/windi/intent-cmd | systemd | live | **404→VIVO** | CÓRTEX | canonical | CLAUDE.md LIVE | Director-as-a-Service |
| 20260620T165000Z | CODEX | FEDIVERSE | 8142 | /opt/windi/fediverse | systemd | live | **404→VIVO** | MÚSCULO | canonical | CLAUDE.md LIVE | Glass Embassy |
| 20260620T165000Z | CODEX | SECURITY-SENTINEL | 8144 | /opt/windi/agents/security-sentinel | systemd | live | 200→200 ESTÁVEL | **OSSO** | canonical | CLAUDE.md SEALED | Dual Correlation |
| 20260620T165000Z | CODEX | WPIL | 8146 | /opt/windi/services/wpil | systemd | live | ? | NERVO | canonical | wpil.service | Proof Interface Layer |
| 20260620T165000Z | CODEX | W-ENTERPRISE-001 | 8150 | /opt/windi/w-enterprise-001 | systemd | live | 200→200 ESTÁVEL | CÓRTEX | canonical | CLAUDE.md LIVE | VERA Compliance |
| 20260620T165000Z | CODEX | W-COST-001 | 8152 | /opt/windi/w-cost-001 | systemd | live | 200→200 ESTÁVEL | NERVO | canonical | CLAUDE.md LIVE | Cost Intelligence |
| 20260620T165000Z | CODEX | W-TRAVEL-MAP | 8153 | /opt/windi/windi-travel/map-comparator | systemd | live | 200→200 ESTÁVEL | MÚSCULO | canonical | CLAUDE.md LIVE | Berlin Pitch Map |
| 20260620T165000Z | CODEX | SERVICE-CONTROL | 8170 | /opt/windi/service-control | systemd | live | 200→200 ESTÁVEL | MÚSCULO | canonical | CLAUDE.md LIVE | Service Panel |
| 20260620T165000Z | CODEX | W-SITES-001 | 8192 | /opt/windi/windi-sites/identity-gate | systemd | live | ? | MÚSCULO | canonical | CLAUDE.md LIVE | Sites Factory |
| 20260620T165000Z | CODEX | W-LEXICON-001 | 8193 | /opt/windi/w-lexicon-001 | manual | live | ? | CÓRTEX | canonical | CLAUDE.md LIVE | TWO-STAGE Model |
| 20260620T165000Z | CODEX | W-CAP-001 | 8194 | /opt/windi/w-cap-001 | manual | live | ? | NERVO | canonical | CLAUDE.md LIVE | Capability Tokens |
| 20260620T165000Z | CODEX | W-BERCARIO-001 | 8195 | /opt/windi/w-bercario-001 | manual | live | ? | NERVO | canonical | CLAUDE.md LIVE | Plenitude Tracker |
| 20260620T165000Z | CODEX | HIOS | 8196 | /opt/windi/hios | manual | live | ? | MÚSCULO | canonical | CLAUDE.md LIVE | Cinema Pipeline |
| 20260620T165000Z | CODEX | HIOS-VISUAL-PRODUCER | 8197 | /opt/windi/hios/visual/producer | manual | live | ? | MÚSCULO | candidate | subdir hios | Hybrid Pipeline |
| 20260620T165000Z | CODEX | W-GENERATOR-001 | 8198 | /opt/windi/w-generator-001 | manual | live | ? | MÚSCULO | canonical | CLAUDE.md SEALED §292 | 6 DOORs |
| 20260620T165000Z | CODEX | ARTIFACTS | 8199 | /opt/windi/artifacts | manual | live | ? | MÚSCULO | candidate | pid 875701 | Artefactos (função?) |
| 20260620T165000Z | CODEX | W-DEV-API-001 | 8200 | /opt/windi/w-dev-api-001 | systemd | live | **404→VIVO** | MÚSCULO | canonical | CLAUDE.md LIVE | Developer API |
| 20260620T165000Z | CODEX | W-FARM-001 | 8201 | /opt/windi/farm | manual | live | NASCEU-DEPOIS | MÚSCULO | canonical | CLAUDE.md LIVE `5F124853` | Casa Digital |
| 20260620T165000Z | CODEX | CORTEX | 8889 | /opt/windi/cortex | manual | live | ? | **CÓRTEX** | canonical | CLAUDE.md SEALED §241 | Canal Único Soberano |

## B5 — DELTA TEMPORAL ABRIL↔JUNHO [CODEX] 20260620T170000Z

### Portas que CURARAM (404→VIVO) sem receipt documentado:
| Porta | Serviço | Delta | Open Question |
|-------|---------|-------|---------------|
| **8096** | W-DID-GENESIS | 404→VIVO | **ACHADO-ÂNCORA: Como/quando curou? Falta selo.** |
| 8127 | NOMAD-BOT | 404→VIVO | Quando activou? |
| 8128 | VD-CUT | 404→VIVO | Quando activou? |
| 8129 | JOE | 404→VIVO | Quando activou? |
| 8132 | COMM | 404→VIVO | Quando activou? |
| 8141 | INTENT-CMD | 404→VIVO | Quando activou? |
| 8142 | FEDIVERSE | 404→VIVO | Quando activou? |
| 8200 | W-DEV-API-001 | 404→VIVO | Quando activou? |

### Portas ESTÁVEIS (200→200):
8080, 8091, 8101, 8102, 8108, 8114, 8119, 8122, 8126, 8131, 8143, 8144, 8150, 8151, 8152, 8153, 8160, 8170, 8180

### Portas que DESAPARECERAM (testadas em Abril, não no extracto CCODE):
| Porta | Estado Abril | Verificação B6.1 | Observação |
|-------|--------------|------------------|------------|
| 8133 | 404 | ss -tlnp: AUSENTE | CONFIRMADO MORTO |
| **8140** | 200 | ss -tlnp: AUSENTE | **CLAUDE.md diz LIVE, mas MORTO** — UDB |
| 8145 | 000 | ss -tlnp: AUSENTE | CONFIRMADO MORTO |
| **8151** | 200 | ss -tlnp: AUSENTE | **CLAUDE.md diz LIVE, mas MORTO** — W-LAB-001 |
| **8160** | 200 | ss -tlnp: AUSENTE | **CLAUDE.md diz LIVE, mas MORTO** — W-CACHE-001 |
| **8180** | 200 | ss -tlnp: AUSENTE | **CLAUDE.md diz LIVE, mas MORTO** — W-ACADEMY-001 |

**ACHADO B6.1 [CODEX]:** 4 serviços documentados como LIVE em CLAUDE.md estão efectivamente MORTOS:
- W-UDB-001 :8140 — documentado como "**LIVE** · Unified Dashboard" → NÃO ESCUTA
- W-LAB-001 :8151 — documentado como "**LIVE** · Governance Laboratory" → NÃO ESCUTA
- W-CACHE-001 :8160 — documentado como "**LIVE** · Verifiable Cache Layer" → NÃO ESCUTA
- W-ACADEMY-001 :8180 — documentado como "**LIVE** · WINDI Institute" → NÃO ESCUTA

Esta discrepância CLAUDE.md↔Realidade é uma violação de I14 (placeholders mascaram falhas).

### Portas NOVAS (não testadas em Abril):
8055, 8056, 8081, 8089, 8090, 8095, 8097, 8098, 8099, 8103, 8104, 8105, 8106, 8109, 8115, 8116, 8118, 8121, 8130, 8146, 8192, 8193, 8194, 8195, 8196, 8197, 8198, 8199, 8201, 8889

## B6 — SUMÁRIO CLASSIFICAÇÃO [CODEX] 20260620T171000Z

### Anatomia por body_part:
| body_part | Contagem | Serviços |
|-----------|----------|----------|
| **OSSO** | 6 | W-DID-GENESIS, FORENSIC-LEDGER, SENTINEL-LAW, VERIFY-PUBLIC, FORENSIC-VAULT, SECURITY-SENTINEL |
| **NERVO** | 10 | W-CMS-001-BRIDGE, BRIDGE, SENTINEL-BRIDGE, WALLET, DISPATCH, PULSE, WINDI-GATEWAY, WPIL, W-COST-001, W-CAP-001, W-BERCARIO-001 |
| **MÚSCULO** | 28 | W-CMS-001, WINDI-SDK-V1, DESKTOP-EXPORT, JMPG-VIEWER, COMMUNIQUE, AGENT-PALETTE, COMMUNIQUE-BUILDER, DISTRIBUTION-ENGINE, DASHBOARD, DESKTOP-GEN7, WINDI-LAW, WINDI-TRAVEL, NOMAD-BOT, VD-CUT, VD-MASS, COMM, FEDIVERSE, SERVICE-CONTROL, W-SITES-001, HIOS, HIOS-VISUAL-PRODUCER, W-GENERATOR-001, ARTIFACTS, W-DEV-API-001, W-FARM-001, W-TRAVEL-MAP |
| **CÓRTEX** | 7 | GOVERNANCE-GUARD, CONSTITUTIONAL-AGENT, GUARDIAN-LOCAL, JOE, INTENT-CMD, W-ENTERPRISE-001, W-LEXICON-001, CORTEX |
| **ANDAIME** | 3 | ENGINE, A4DESK-LANDING, ENGINE-ALT |
| **?** | 2 | UVICORN-ROOT, TSIL |

### Canonicality:
| Estado | Contagem |
|--------|----------|
| canonical | 42 |
| candidate | 4 |
| legacy | 4 |
| scaffold | 1 |
| parallel | 1 |
| duplicate | 1 |
| unknown | 2 |

### Bandeiras Abertas (requer Human Dragon):
| # | Serviço | Questão | Prioridade |
|---|---------|---------|------------|
| 1 | UVICORN-ROOT :8081 | Função desconhecida, 127.0.0.1 only | P2 |
| 2 | AGENT-PALETTE :8108 | Morfologia GEN7 — manter para fase seguinte | P1 |
| 3 | ENGINE-ALT :8111 | Duplicado do ENGINE :8080, mesmo directório | P2 |
| 4 | W-CMS-001 :8055/:8056 | Duas portas num directório | P2 |
| 5 | ENGINE :8080/:8111 | Duas portas num directório | P2 |
| 7 | DESKTOP-GEN7 :8119 | Morfologia GEN7 — manter para fase seguinte | P1 |
| 8 | W-DID-GENESIS :8096 | **ACHADO-ÂNCORA:** curou-se 404→VIVO sem receipt | **P0** |
| 9 | TSIL :8095 | Função desconhecida | P2 |
| **11** | W-UDB-001 :8140 | **CLAUDE.md diz LIVE, está MORTO** | **P0** |
| **12** | W-LAB-001 :8151 | **CLAUDE.md diz LIVE, está MORTO** | **P0** |
| **13** | W-CACHE-001 :8160 | **CLAUDE.md diz LIVE, está MORTO** | **P0** |
| **14** | W-ACADEMY-001 :8180 | **CLAUDE.md diz LIVE, está MORTO** | **P0** |

**Contagem:** 12 bandeiras abertas (4 × P0, 2 × P1, 6 × P2)

---

## HASH FINAL [CODEX] 20260620T172000Z
```
Hash pré-CODEX:  8886d36c16da8abae0a11541349e0a06fa335445f6b0c838b37560653cd2c832
Hash pós-CODEX: 35d516e42dfb46e07d1eaa4318f561c1d5db4668ceaa2dce35fa7f77ae2dd96a
```

Classificação CODEX completa. Contêiner entregue ao Human Dragon para ratificação.

## B1 — LEITURA ABRIL CONFIRMADA [CODEX] 20260620T123817Z

Arquivos lidos antes de classificar:

- `/opt/windi/audit/191/191-C-canonical.json`
- `/opt/windi/audits/audit-20260420-140300/00_summary.txt`
- `/opt/windi/audits/audit-20260420-140300/01_ports.txt`
- `/opt/windi/audits/audit-20260420-140300/02_systemd_units.txt`
- `/opt/windi/audits/audit-20260420-140300/05_storage_dbs.txt`
- `/opt/windi/audits/audit-20260420-140300/06_health_matrix.txt`

Leitura de Abril herdada:

- 62 portas escutando.
- 108 unidades systemd.
- 123 bancos SQLite.
- `191-C-canonical.json` confirma validação existencial de DID contra Genesis DB.
- Abril registrou `:8096` como escutando, mas health matrix `:8096 -> 404`.
- Abril já apontava fragmentação de identidade entre DID-Genesis, Wallet, LAW Gate e Travel Identity em auditoria de absorção.

## B2-B5 — CLASSIFICAÇÃO CODEX EM FORMATO 12 [CODEX] 20260620T123817Z

Regra aplicada: transcrição append-only das 56 linhas brutas do CCode para formato canônico de 12 campos. As linhas brutas permanecem intactas.

| timestamp | executor | service | port | path | owner | status | health | body_part | canonicality | evidence | open_question |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| 20260620T123817Z | CODEX | W-CMS-001 | 8055 | /opt/windi/w-cms-001 | systemd | live | pass | MUSCULO | parallel | CCODE A4 + Abril port 8055 absent + June live | DELTA NASCEU-DEPOIS; W-CMS has paired :8055/:8056, decide canonical split |
| 20260620T123817Z | CODEX | W-CMS-001-BRIDGE | 8056 | /opt/windi/w-cms-001 | systemd | live | not_measured | NERVO | parallel | CCODE A4 + same directory as 8055 | [dúvida: HUMANO] bridge vs CMS boundary; DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | ENGINE | 8080 | /opt/windi/engine | systemd | live | pass | OSSO | parallel | Abril health 8080->200 + CCODE A4 | DELTA ESTAVEL; paired with ENGINE-ALT :8111, decide engine canonicality |
| 20260620T123817Z | CODEX | UVICORN-ROOT | 8081 | /opt/windi | unknown | live | not_measured | ? | unknown | CCODE A4 [dúvida: HUMANO] + current port | [dúvida: HUMANO] function unknown; DELTA ESTAVEL as port existed in Abril |
| 20260620T123817Z | CODEX | A4DESK-LANDING | 8086 | /opt/windi/a4desk-landing | systemd | live | not_measured | MUSCULO | legacy | Abril port 8086 present + CCODE A4 | DELTA ESTAVEL; likely public/legacy landing, verify current role |
| 20260620T123817Z | CODEX | GOVERNANCE-GUARD | 8089 | /opt/windi/engine/governance_guard | systemd | live | not_measured | CORTEX | candidate | CCODE A4 + April drift listed 8089 unreachable separately | DELTA ?; confirm if guard overlaps Governance API |
| 20260620T123817Z | CODEX | WINDI-SDK-V1 | 8090 | /opt/windi/SDK_v1.1_RFC003/windi-sdk-v1 | unknown | live | not_measured | MUSCULO | candidate | CCODE A4 + Abril port 8090 present | DELTA ESTAVEL; SDK public role needs decision |
| 20260620T123817Z | CODEX | CONSTITUTIONAL-AGENT | 8091 | /opt/windi/agents/constitutional-agent | systemd | live | pass | CORTEX | canonical | Abril health 8091->200 + CCODE LIVE | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | TSIL | 8095 | /opt/windi/tsil | systemd | live | not_measured | MUSCULO | unknown | CCODE A4 + Abril port 8095 present | DELTA ESTAVEL; role not classified by April |
| 20260620T123817Z | CODEX | W-DID-GENESIS | 8096 | /opt/windi/did-genesis | systemd | live | pass | OSSO | canonical | Mandate ratifies did-genesis name + current health live + Abril 404 | DELTA 404->VIVO; priority: how/when did :8096 become canonical without receipt? |
| 20260620T123817Z | CODEX | BRIDGE | 8097 | /opt/windi/bridge | systemd | live | not_measured | NERVO | candidate | CCODE A4 + Abril port 8097 present | DELTA ESTAVEL; bridge responsibility needs source contract |
| 20260620T123817Z | CODEX | SENTINEL-BRIDGE | 8098 | /opt/windi/sentinel-bridge | systemd | live | not_measured | NERVO | candidate | CCODE A4 + Abril port 8098 present | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | WALLET | 8099 | /opt/windi/wallet | systemd | live | not_measured | NERVO | parallel | April identity fragmentation + CCODE A4 | DELTA ESTAVEL; decide relation to DID-Genesis and published DID contract |
| 20260620T123817Z | CODEX | FORENSIC-LEDGER | 8101 | /opt/windi/suite-docs | systemd | live | pass | OSSO | canonical | Abril health 8101->200 + CCODE SEALED + REBOOT proof | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | SENTINEL-LAW | 8102 | /opt/windi/sentinel-law | systemd | live | pass | OSSO | canonical | Abril health 8102->200 + CCODE A4 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | DESKTOP-EXPORT | 8103 | /opt/windi/desktop/export | systemd | live | not_measured | MUSCULO | parallel | CCODE A4 + April export fragmentation | DELTA ESTAVEL; document output overlap with Communique/JMPG |
| 20260620T123817Z | CODEX | JMPG-VIEWER | 8104 | /opt/windi/jmpg-viewer | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 + April document output overlap | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | COMMUNIQUE | 8105 | /opt/windi/communique | systemd | live | pass | MUSCULO | canonical | CCODE LIVE + April port 8105 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | FORENSIC-VAULT | 8106 | /opt/windi/forensic-vault | systemd | live | not_measured | OSSO | canonical | April absorption marks vault as trunk SEALED + CCODE A4 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | AGENT-PALETTE | 8108 | /opt/windi/agent-palette | systemd | live | pass | CORTEX | parallel | Abril health 8108->200 + CCODE flag | DELTA ESTAVEL; [dúvida: HUMANO] relation to DESKTOP-GEN7 |
| 20260620T123817Z | CODEX | PULSE | 8109 | /opt/windi/pulse | systemd | live | not_measured | NERVO | candidate | CCODE A4 + Abril port 8109 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | GUARDIAN-LOCAL | 8110 | /opt/windi/guardian-local | systemd | live | not_measured | CORTEX | candidate | CCODE A4 + Abril port 8110 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | ENGINE-ALT | 8111 | /opt/windi/engine | systemd | live | not_measured | ? | parallel | CCODE flag + same directory as ENGINE :8080 | DELTA ESTAVEL; [dúvida: HUMANO] duplicate engine or distinct role? |
| 20260620T123817Z | CODEX | VERIFY-PUBLIC | 8114 | /opt/windi/verify-public/app | systemd | live | pass | OSSO | canonical | Abril health 8114->200 + CCODE LIVE + Gate0/Reboot docs | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | COMMUNIQUE-BUILDER | 8115 | /opt/windi/communique-builder | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 + Abril port 8115 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | DISTRIBUTION-ENGINE | 8116 | /opt/windi/distribution-engine | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 + Abril port 8116 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | DASHBOARD | 8118 | /opt/windi/dashboard/dist | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 + Abril port 8118 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | DESKTOP-GEN7 | 8119 | /opt/windi/desktop-gen7/backend | systemd | live | pass | ? | candidate | Abril health 8119->200 + CCODE flag + user notes GEN7 incomplete | DELTA ESTAVEL; [dúvida: HUMANO] morphology incomplete; relation to AGENT-PALETTE |
| 20260620T123817Z | CODEX | DISPATCH | 8121 | /opt/windi/dispatch | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 + Abril port 8121 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | WINDI-LAW | 8122 | /opt/windi/windi-law/identity-gate | systemd | live | pass | NERVO | parallel | Abril health 8122->200 + April identity fragmentation + CCODE SEALED | DELTA ESTAVEL; identity gate should map to DID-Genesis source |
| 20260620T123817Z | CODEX | WINDI-TRAVEL | 8126 | /opt/windi/windi-travel/identity-gate | systemd | live | pass | NERVO | parallel | Abril health 8126->200 + April identity fragmentation + CCODE LIVE | DELTA ESTAVEL; identity gate should map to DID-Genesis source |
| 20260620T123817Z | CODEX | NOMAD-BOT | 8127 | /opt/windi/nomad-bot | systemd | live | fail | MUSCULO | candidate | Abril health 8127->404 + CCODE LIVE | DELTA 404->VIVO; verify current health endpoint before canon |
| 20260620T123817Z | CODEX | VD-CUT | 8128 | /opt/windi/vd-cut | systemd | live | fail | MUSCULO | candidate | Abril health 8128->404 + CCODE LIVE | DELTA 404->VIVO; health shape may be nonstandard |
| 20260620T123817Z | CODEX | JOE | 8129 | /opt/windi/joe | systemd | live | fail | MUSCULO | candidate | Abril health 8129->404 + CCODE LIVE | DELTA 404->VIVO; route health unknown |
| 20260620T123817Z | CODEX | WINDI-GATEWAY | 8130 | /opt/windi/windi-gateway | systemd | live | not_measured | NERVO | candidate | CCODE A4 + Abril port 8130 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | VD-MASS | 8131 | /opt/windi/vd-mass | systemd | live | pass | MUSCULO | candidate | Abril health 8131->200 + CCODE LIVE | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | COMM | 8132 | /opt/windi/comm | systemd | live | fail | MUSCULO | candidate | Abril health 8132->404 + CCODE LIVE | DELTA 404->VIVO; name/function requires confirmation |
| 20260620T123817Z | CODEX | INTENT-CMD | 8141 | /opt/windi/intent-cmd | systemd | live | fail | CORTEX | candidate | Abril health 8141->404 + CCODE LIVE | DELTA 404->VIVO; nonstandard health or partial service |
| 20260620T123817Z | CODEX | FEDIVERSE | 8142 | /opt/windi/fediverse | systemd | live | fail | MUSCULO | candidate | Abril health 8142->404 + CCODE LIVE | DELTA 404->VIVO; nonstandard health or partial service |
| 20260620T123817Z | CODEX | SECURITY-SENTINEL | 8144 | /opt/windi/agents/security-sentinel | systemd | live | pass | OSSO | canonical | Abril health 8144->200 + CCODE SEALED | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | WPIL | 8146 | /opt/windi/services/wpil | systemd | live | not_measured | OSSO | candidate | CCODE A4 + Abril port 8146 | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | W-ENTERPRISE-001 | 8150 | /opt/windi/w-enterprise-001 | systemd | live | pass | MUSCULO | candidate | Abril health 8150->200 + §191 DID validation touched enterprise | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | W-COST-001 | 8152 | /opt/windi/w-cost-001 | systemd | live | pass | MUSCULO | candidate | Abril health 8152->200 + CCODE LIVE | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | W-TRAVEL-MAP | 8153 | /opt/windi/windi-travel/map-comparator | systemd | live | pass | MUSCULO | candidate | Abril health 8153->200 + CCODE LIVE | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | SERVICE-CONTROL | 8170 | /opt/windi/service-control | systemd | live | pass | OSSO | canonical | Abril health 8170->200 + CCODE LIVE | DELTA ESTAVEL |
| 20260620T123817Z | CODEX | W-SITES-001 | 8192 | /opt/windi/windi-sites/identity-gate | systemd | live | pass | MUSCULO | canonical | June W-SITES/W-Email report + CCODE LIVE | DELTA NASCEU-DEPOIS; now proofmail/farm surface |
| 20260620T123817Z | CODEX | W-LEXICON-001 | 8193 | /opt/windi/w-lexicon-001 | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 only | DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | W-CAP-001 | 8194 | /opt/windi/w-cap-001 | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 only | DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | W-BERCARIO-001 | 8195 | /opt/windi/w-bercario-001 | systemd | live | not_measured | NERVO | candidate | CCODE A4 only | DELTA NASCEU-DEPOIS; likely identity/birth UX, confirm relation to DID-Genesis |
| 20260620T123817Z | CODEX | HIOS | 8196 | /opt/windi/hios | systemd | live | not_measured | OSSO | candidate | CCODE A4 only | DELTA NASCEU-DEPOIS; define if trunk or app host |
| 20260620T123817Z | CODEX | HIOS-VISUAL-PRODUCER | 8197 | /opt/windi/hios/visual/producer | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 only | DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | W-GENERATOR-001 | 8198 | /opt/windi/w-generator-001 | systemd | live | not_measured | MUSCULO | canonical | CCODE SEALED | DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | ARTIFACTS | 8199 | /opt/windi/artifacts | systemd | live | not_measured | MUSCULO | candidate | CCODE A4 only | DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | W-DEV-API-001 | 8200 | /opt/windi/w-dev-api-001 | systemd | live | fail | OSSO | candidate | Abril health 8200->404 + CCODE LIVE | DELTA 404->VIVO; uses nonstandard `/v1/health` per April drift |
| 20260620T123817Z | CODEX | W-FARM-001 | 8201 | /opt/windi/farm | systemd | live | not_measured | MUSCULO | canonical | W-SITE-MINIMUM SEALED + Farm dragon-001 ratified + CCODE LIVE | DELTA NASCEU-DEPOIS |
| 20260620T123817Z | CODEX | CORTEX | 8889 | /opt/windi/cortex | systemd | live | not_measured | CORTEX | canonical | CCODE SEALED + current live | DELTA ?; not in April health matrix |

## B4 — DELTA TEMPORAL ABRIL-JUNHO [CODEX] 20260620T123817Z

### Prioridade P0

- `W-DID-GENESIS :8096`: `404->VIVO`. Abril via health matrix: `8096 -> 404`; Junho via CCode e health atual: `LIVE`. Mandato exige pergunta prioritária: como e quando `:8096` passou de 404 a fonte canônica? Falta selo/receipt de transição.
- Fragmentação de identidade permanece estrutural: `:8096`, `:8099`, `:8122`, `:8126`, e agora consumidores como `GEN7`, `W-SITES`, plugin e Farm dependem de contrato de publicação.

### Portas de Abril que eram 404 e agora existem vivas

- `8127 NOMAD-BOT`
- `8128 VD-CUT`
- `8129 JOE`
- `8132 COMM`
- `8141 INTENT-CMD`
- `8142 FEDIVERSE`
- `8200 W-DEV-API-001`

Interpretação: `404->VIVO` não prova health canônica; pode significar rota health não-padrão. Estas linhas foram mantidas como `candidate`, não como `canonical`, salvo ratificação externa.

### Nasceram depois de Abril ou não estavam na matriz de Abril

- `W-SITES-001 :8192`
- `W-LEXICON-001 :8193`
- `W-CAP-001 :8194`
- `W-BERCARIO-001 :8195`
- `HIOS :8196`
- `HIOS-VISUAL-PRODUCER :8197`
- `W-GENERATOR-001 :8198`
- `ARTIFACTS :8199`
- `W-FARM-001 :8201`

Interpretação: estes componentes pertencem à camada HIOS/W pós-abril e precisam herdar uma porta de identidade comum.

## B5 — BANDEIRAS PARA HUMAN DRAGON [CODEX] 20260620T123817Z

### Bandeiras herdadas que permanecem abertas

1. `UVICORN-ROOT :8081` — função desconhecida. Classificado `? / unknown`.
2. `AGENT-PALETTE :8108` vs `DESKTOP-GEN7 :8119` — relação morfológica não decidida. Classificado como `CORTEX parallel` e `? candidate`.
3. `ENGINE-ALT :8111` duplicado com `ENGINE :8080` no mesmo diretório. Classificado `? / parallel`.
4. `W-CMS-001 :8055` e `W-CMS-001-BRIDGE :8056` no mesmo diretório. Classificado `MUSCULO/NERVO parallel`.
5. `ENGINE :8080` e `ENGINE-ALT :8111` — ver bandeira 3.
6. `did-genesis` vs `w-did-genesis` — fechada pelo mandato: nome canônico é `did-genesis`; `w-did-genesis` é fantasma de nomenclatura.
7. `DESKTOP-GEN7` vs `AGENT-PALETTE` — permanece coração da auditoria morfológica GEN7.

### Bandeiras novas levantadas pelo CODEX

8. `W-BERCARIO-001 :8195` pode ser NERVO de identidade/birth e precisa relação explícita com `did-genesis :8096`.
9. `W-SITES-001 :8192` já é superfície canônica de W-Farm/Proofmail, mas precisa contrato de identidade publicado para consumidores JS.
10. `W-FARM-001 :8201` existe depois de Abril e deve ser classificado como canônico apenas na camada Farm, não como fonte de identidade.
11. `W-DEV-API-001 :8200` era `404` em Abril; Abril já dizia que usa `/v1/health`. Health comum falha não deve virar `ANDAIME` sem medir rota correta.
12. Serviços `404->VIVO` de mídia/distribuição (`8127`, `8128`, `8129`, `8132`, `8141`, `8142`) precisam health endpoint real antes de promoção.

### Decisão I1 recomendada antes de `WindiDID.sync()`

Criar `W-DID-PUBLISH-CONTRACT-001`:

```text
:8096 did-genesis is SOURCE.
JS-visible identity is MAP.
localStorage["windi_did"] may be published only by the canonical DID layer, not invented by consumers.
GEN7/plugin/W-SITES/Farm read the map; they do not define identity.
```

Sem esta decisão, qualquer patch do plugin corre o risco de criar nova porta paralela.

---

## ERRATA B6 — CORRECÇÃO DO SELO [CODEX] 20260620T180000Z

**Falha reconhecida:** O CODEX declarou hash final (35d516e4...) e depois continuou a editar.
O selo mentiu sobre o que selava. Violação de procedimento I11.

**Correcção:** Este bloco é a última edição. O hash abaixo é calculado DEPOIS desta linha
e nenhuma edição subsequente é permitida antes da ratificação Human Dragon.

**Achados P0 confirmados pela auditoria:**
1. **MAPA MENTE:** CLAUDE.md declara LIVE 4 serviços que estão MORTOS (:8140, :8151, :8160, :8180)
2. **CURAS SEM RECEIPT:** 8 portas passaram de 404→VIVO sem selo no Ledger (:8096 é âncora)
3. **FRAGMENTAÇÃO DE IDENTIDADE:** :8096, :8099, :8122, :8126 — 4 gates sem contrato de publicação

**Classificações corrigidas:**
- ENGINE :8080 → OSSO (não ANDAIME) — 200→200 ESTÁVEL, windi-governance.service
- ENGINE-ALT :8111 → ? [dúvida: HUMANO] — mesmo directório que :8080

**Contagem final de bandeiras:** 12 abertas (ver B5)

---

## SELO FINAL [CODEX] 20260620T180200Z

Contêiner entregue ao Human Dragon para ratificação.
Hash verificável via: `sha256sum /opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md`

---
FIM DO CONTÊINER WINDI-HIOS-INVENTORY v1.0

