# 🐉 CCODE INTEGRATION — Architect Dragon Design Reference
# Upload these files to Strato, then point CCode to them

## FILES TO UPLOAD (4 artifacts)

```
CCODE_PROMPT_RESPIRADOURO.md          — 14 KB — Original BIG Prompt (Phase 1 spec)
CCODE_PALETTE_DEEP_AUDIT.md           — 19 KB — Deep Audit + Evolution Prompt (full analysis)
WINDI_Respiradouro_v0.9.0-R.jsx       — 24 KB — React Design Reference (single-language)
WINDI_Respiradouro_v0.9.0-R_Trilingual.jsx — 33 KB — React Design Reference (PT/DE/EN trilingual)
```

## SCP COMMANDS — Run from your local machine

After downloading the 4 files from Claude, run:

```bash
# Upload all design references to a dedicated folder on Strato
ssh windi@87.106.29.233 "mkdir -p /opt/windi/agent-palette/design-ref"

scp CCODE_PROMPT_RESPIRADOURO.md windi@87.106.29.233:/opt/windi/agent-palette/design-ref/
scp CCODE_PALETTE_DEEP_AUDIT.md windi@87.106.29.233:/opt/windi/agent-palette/design-ref/
scp WINDI_Respiradouro_v0.9.0-R.jsx windi@87.106.29.233:/opt/windi/agent-palette/design-ref/
scp WINDI_Respiradouro_v0.9.0-R_Trilingual.jsx windi@87.106.29.233:/opt/windi/agent-palette/design-ref/
```

Or all at once:
```bash
scp CCODE_PROMPT_RESPIRADOURO.md CCODE_PALETTE_DEEP_AUDIT.md WINDI_Respiradouro_v0.9.0-R.jsx WINDI_Respiradouro_v0.9.0-R_Trilingual.jsx windi@87.106.29.233:/opt/windi/agent-palette/design-ref/
```

## THEN TELL CCODE:

```
Lê os ficheiros de referência de design do Architect Dragon em:
/opt/windi/agent-palette/design-ref/

Estes ficheiros contêm:

1. WINDI_Respiradouro_v0.9.0-R_Trilingual.jsx
   → O DESIGN REFERENCE PRINCIPAL — React component completo com:
   - Sistema LANG trilíngue (PT/DE/EN) com 40+ strings por idioma
   - LivingOrb: Canvas 60fps, breathing animation baseada em CogScore
   - NerveStrand: 20 partículas com flow/stop por serviço
   - SovereigntyGauge: CSS bar 93/7 com labels
   - CogPanel: breakdown de Sovereignty/Confidence/Stability/Learning
   - PulsePanel: grid 2-col com 20 serviços + status dots
   - SovPanel: sovereignty ratio + 3 tiers (P/M/G) + citação
   - Progressive disclosure: click → expand, click fora → collapse
   - Theme system KLAR/NOIR com 20+ variáveis por tema
   - LangSwitcher component com flags 🇧🇷/🇩🇪/🇬🇧

2. CCODE_PALETTE_DEEP_AUDIT.md
   → Auditoria profunda do Palette com:
   - Análise zona-a-zona (5 zonas, scoring individual)
   - Gap analysis: 10 dimensões, current vs target
   - Priority matrix P0→P4 com estimativas de tempo
   - Design principles (6 mandamentos)
   - Micro-interactions spec (7 items)
   - Typography/spacing audit
   - Smoke test checklist (10 checks)

3. CCODE_PROMPT_RESPIRADOURO.md
   → Spec técnico original do Respiradouro Phase 1

4. WINDI_Respiradouro_v0.9.0-R.jsx
   → Versão single-language (referência simplificada)

Usa o ficheiro Trilingual.jsx como DESIGN REFERENCE para:
- Validar que as inside features no Palette actual correspondem ao design
- Copiar/adaptar patterns que faltem (trilingual strings, panel layouts, etc.)
- Garantir que hover states, animations e progressive disclosure estão alinhados
- Verificar consistência de cores KLAR/NOIR entre o design e a implementação
```
