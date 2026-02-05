# WINDI ISP Registry — Existing Profiles

Registry Version: 2.10.0 (as of 05 Feb 2026)
Server: Strato 87.106.29.233
Path: /opt/windi/isp/

## 🏛️ Administrative Hierarchy Complete!

```
╔═══════════════════════════════════════════════════════════════╗
║  BUND (Federal)                                               ║
║  └── Bundesregierung ✅ (MEDIUM)                              ║
║                                                               ║
║  LAND (State)                                                 ║
║  └── Freistaat Bayern ✅ 🆕 (MEDIUM)                          ║
║                                                               ║
║  KOMMUNE (Municipal)                                          ║
║  └── Stadt Kempten (Allgäu) ✅ 🆕 (LOW) — WINDI HOME!        ║
╚═══════════════════════════════════════════════════════════════╝
```

## Deployed Profiles (14)

### HIGH (2)
| Profile | Type | Templates | Keywords | Path |
|---------|------|-----------|----------|------|
| BIS Regulatory Authority | regulatory_authority | 8 | 28 | /opt/windi/isp/bis-style/ |
| BaFin | federal_regulatory_authority | 12 | 35 | /opt/windi/isp/bafin/ |

### MEDIUM (4) 🆙
| Profile | Type | Templates | Keywords | Path |
|---------|------|-----------|----------|------|
| Bundesregierung | government_institutional | 10 | 30 | /opt/windi/isp/bundesregierung/ |
| Bundesagentur für Arbeit | social_sensitive_institutional | 12 | 32 | /opt/windi/isp/agentur-fuer-arbeit/ |
| Sparkasse | public_financial_institution | 12 | 101 | /opt/windi/isp/sparkasse/ |
| **Freistaat Bayern** 🆕 | **state_government_institutional** | **10** | **61** | **/opt/windi/isp/freistaat-bayern/** |

### LOW (8) 🆙
| Profile | Type | Templates | Keywords | Path |
|---------|------|-----------|----------|------|
| Deutsche Bahn AG | public_enterprise | 6 | 20 | /opt/windi/isp/deutsche-bahn/ |
| IHK | public_law_chamber | 8 | 25 | /opt/windi/isp/ihk/ |
| HWK | public_law_chamber | 10 | 34 | /opt/windi/isp/hwk/ |
| TÜV | technical_inspection_organization | 12 | 45 | /opt/windi/isp/tuev/ |
| Siemens AG | industrial_technology_conglomerate | 10 | 40 | /opt/windi/isp/siemens/ |
| *(+1 untracked)* | — | — | — | — |
| Stadtwerke | municipal_utility_enterprise | 10 | 71 | /opt/windi/isp/stadtwerke/ |
| **Stadt Kempten** 🆕🏠 | **municipal_administration** | **10** | **61** | **/opt/windi/isp/stadt-kempten/** |

## New Profiles Highlights

### Freistaat Bayern (MEDIUM)
- **Governance Level**: MEDIUM (identity_license: required)
- **Templates**: 10 (Kabinettsbeschluss, Gesetzentwurf, Haushaltsplan...)
- **Keywords**: 61 (Staatsregierung, Landtag, Regierungsbezirk...)
- **Frameworks**: 11 (Bayerische Verfassung, BayDSG, BayEGovG...)
- **Key Feature**: First Bundesland profile — covers 7 Regierungsbezirke

### Stadt Kempten (LOW) — 🏠 WINDI HOME BASE!
- **Governance Level**: LOW (identity_license: optional)
- **Templates**: 10 (Stadtratsbeschluss, Baugenehmigung, Vergabevermerk...)
- **Keywords**: 61 (Stadtverwaltung, Oberbürgermeister, BürgerService...)
- **Frameworks**: 9 (Bayerische GO, KommHV, VOB/VOL/VgV...)
- **Key Feature**: First Kommune profile — WINDI's physical location!

## Cross-Reference Chain
```
Bundesregierung (MEDIUM)
       │
       ▼
Freistaat Bayern (MEDIUM) ──► Regierung von Schwaben
       │                              │
       ▼                              ▼
Stadt Kempten (LOW) ◄─────── Kommunalaufsicht
       │
       ▼
Stadtwerke Kempten (referenced)
```

## Planned Profiles (Next Wave)
- Deutsche Post / DHL Group (logistics) → LOW
- ADAC (automobile club) → LOW
- AOK / Krankenkasse (health insurance) → MEDIUM

## Registry Stats
| Metric | Value |
|--------|-------|
| Total Profiles | 14 |
| HIGH | 2 |
| MEDIUM | 4 🆙 |
| LOW | 8 🆙 |
| Total Templates | ~130 |
| Total Keywords | ~583 |
| Registry Version | 2.10.0 |

## Governance Pyramid v2.10
```
              ╔═════════════════════════════════════╗
    HIGH      ║  BIS · BaFin                        ║  (2)
              ╠═════════════════════════════════════╣
    MEDIUM    ║  Bundesreg · BA · SPARKASSE · BAYERN║  (4) 🆙
              ╠═════════════════════════════════════╣
    LOW       ║ DB·IHK·HWK·TÜV·SIE·?·STW·KEMPTEN🏠 ║  (8) 🆙
              ╚═════════════════════════════════════╝
                      14 PROFILES TOTAL
```

## Governance Config
- Main config: /opt/windi/engine/governance_levels.json
- Scanner: /opt/windi/isp_scanner_v1.1.py
- Factory: Claude ISP Factory v1.0
