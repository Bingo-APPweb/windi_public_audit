# WINDI ISP Corporate Scanner v1.0
## Deploy & Execution Guide for Strato Server

### 🗼 Filosofia: Controlador de Tráfego, não Bombeiro

---

## Quick Deploy (via SSH ou Claude Code)

```bash
# 1. SSH para Strato
ssh windi@87.106.29.233

# 2. Copiar scanner para servidor
cd /opt/windi
# (cola o conteúdo do isp_scanner.py ou scp)

# 3. Executar scan completo
python3 isp_scanner.py

# 4. Apenas diagnóstico (sem mexer em nada)
python3 isp_scanner.py --scan-only

# 5. Output JSON (para integração)
python3 isp_scanner.py --json
```

## Via Claude Code no Terminal

```bash
cd /opt/windi && claude
# Depois dentro do Claude Code:
"Execute o isp_scanner.py e analise os resultados"
```

## O que o Scanner faz (5 Fases)

| Fase | O que faz | Problema que resolve |
|------|-----------|---------------------|
| 1. Syntax Scan | Escaneia TODOS .html por conflitos Mustache vs Jinja2 | footer.html {# bug |
| 2. Module Scan | Verifica sys.path e colisões de nomes | isp_loader vs isp_governance_loader |
| 3. Render Chain | Valida header → content → footer → template | Custom delimiters não propagando |
| 4. PDF E2E | Testa geração de PDF e presença de branding | Render parcial com {{ cru |
| 5. Report | Score pass/fail com prioridades de fix | Visão corporativa do estado |

## Score System

| Grade | Score | Significado |
|-------|-------|-------------|
| A | 90-100 | Produção ready |
| B | 75-89 | Minor fixes needed |
| C | 50-74 | Significant issues |
| D | 25-49 | Major rework needed |
| F | 0-24 | Critical failures |

## Reports

Salvos automaticamente em: `/opt/windi/reports/isp_scan_YYYYMMDD_HHMMSS.json`

---

*AI processes. Human decides. WINDI guarantees.* 🐉
