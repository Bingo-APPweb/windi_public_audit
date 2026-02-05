# WINDI ISP Registry — Existing Profiles

Registry Version: 2.8.0 (as of 05 Feb 2026)
Server: Strato 87.106.29.233
Path: /opt/windi/isp/

## Deployed Profiles (12)

### HIGH (2)
| Profile | Type | Templates | Keywords | Path |
|---------|------|-----------|----------|------|
| BIS Regulatory Authority | regulatory_authority | 8 | 28 | /opt/windi/isp/bis-style/ |
| BaFin | federal_regulatory_authority | 12 | 35 | /opt/windi/isp/bafin/ |

### MEDIUM (3) 🆙
| Profile | Type | Templates | Keywords | Path |
|---------|------|-----------|----------|------|
| Bundesregierung | government_institutional | 10 | 30 | /opt/windi/isp/bundesregierung/ |
| Bundesagentur für Arbeit | social_sensitive_institutional | 12 | 32 | /opt/windi/isp/agentur-fuer-arbeit/ |
| **Sparkasse** 🆕 | **public_financial_institution** | **12** | **101** | **/opt/windi/isp/sparkasse/** |

### LOW (7)
| Profile | Type | Templates | Keywords | Path |
|---------|------|-----------|----------|------|
| Deutsche Bahn AG | public_enterprise | 6 | 20 | /opt/windi/isp/deutsche-bahn/ |
| IHK | public_law_chamber | 8 | 25 | /opt/windi/isp/ihk/ |
| HWK | public_law_chamber | 10 | 34 | /opt/windi/isp/hwk/ |
| TÜV | technical_inspection_organization | 12 | 45 | /opt/windi/isp/tuev/ |
| Siemens AG | industrial_technology_conglomerate | 10 | 40 | /opt/windi/isp/siemens/ |
| *(+1 untracked)* | — | — | — | — |
| Stadtwerke | municipal_utility_enterprise | 10 | 71 | /opt/windi/isp/stadtwerke/ |

## Sparkasse ISP Highlights
- **Governance Level**: MEDIUM (first financial institution at this level)
- **Compliance Frameworks**: 14 frameworks including KWG, MaRisk, BAIT, DORA, GwG
- **Templates**: 12 (including R5 AML/Incident templates)
- **Keywords**: 101 (highest density in registry)
- **Key Templates**:
  - TPL-SPK-003: Geldwäsche-Verdachtsmeldung (R5)
  - TPL-SPK-011: DORA-Vorfallmeldung (R5)
  - TPL-SPK-001: MaRisk-Risikobericht (R4)
  - TPL-SPK-002: BAIT-Sicherheitskonzept (R4)

## Planned Profiles (Next Wave)
- Deutsche Post / DHL Group (logistics) → LOW
- ADAC (automobile club) → LOW
- AOK / Krankenkasse (health insurance) → MEDIUM

## Governance Config
Main config: /opt/windi/engine/governance_levels.json
Scanner: /opt/windi/isp_scanner_v1.1.py

## Registry Stats
| Metric | Value |
|--------|-------|
| Total Profiles | 12 |
| HIGH | 2 |
| MEDIUM | 3 🆙 |
| LOW | 7 |
| Total Templates | ~110 |
| Total Keywords | ~461 |
| Registry Version | 2.8.0 |

## Pyramid Evolution
```
         ╔═══════════════════════════════╗
  HIGH   ║  BIS · BaFin                  ║  (2)
         ╠═══════════════════════════════╣
  MEDIUM ║  Bundesreg · BA · SPARKASSE 🆕 ║  (3)
         ╠═══════════════════════════════╣
  LOW    ║ DB·IHK·HWK·TÜV·SIE·?·STW     ║  (7)
         ╚═══════════════════════════════╝
              12 PROFILES TOTAL
```
