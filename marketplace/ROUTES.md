# WINDI Marketplace — Route Map

## Portal Central (Index)

```
/marketplace → marketplace-index.html
```

O Portal Central é o hub de navegação para todas as prateleiras do Marketplace.

---

## 4 Prateleiras Principais

| Rota | Arquivo | Público | Cor |
|------|---------|---------|-----|
| `/human-eyes` | `windi-human-eyes.html` | Humanos, clientes, investores | 🟢 Verde |
| `/flying` | `windi-flying-tiers.html` | Controllers, decision-makers | 🟡 Gold |
| `/envelopes` | `inside-the-envelopes.html` | Compliance, DPO, Einkauf | 🔵 Azul |
| `/modules` | `marketplace.html` | Tech-teams, arquitetos | 🔴 Vermelho |

---

## Estrutura de Arquivos

```
/opt/windi/a4desk-editor/static/
│
├── 🏠 marketplace-index.html      ← PORTAL CENTRAL
│
├── 👁️ windi-human-eyes.html       ← Human Eyes (Safety messaging)
├── ✈️ windi-flying-tiers.html     ← Flying Tiers (Pricing visual)
├── 📦 inside-the-envelopes.html   ← Envelopes (Feature comparison)
├── 🧩 marketplace.html            ← Modules (Technical catalog)
│
├── 📄 windi-envelopes-content.html ← Envelope details
└── 📄 windi-clone-modules.html     ← Clone modules overview
```

---

## Nginx Configuration (Strato)

```nginx
# /etc/nginx/sites-available/clone.conf

server {
    listen 80;
    server_name clone.windia4desk.tech;
    root /var/www/clone;

    # Marketplace Portal
    location /marketplace {
        try_files /marketplace-index.html =404;
    }

    # Communication Layers
    location /human-eyes {
        try_files /windi-human-eyes.html =404;
    }

    location /flying {
        try_files /windi-flying-tiers.html =404;
    }

    location /envelopes {
        try_files /inside-the-envelopes.html =404;
    }

    location /modules {
        try_files /marketplace.html =404;
    }

    # Static files
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Fluxo de Navegação

```
                    ┌─────────────────────┐
                    │   MARKETPLACE       │
                    │   Portal Central    │
                    │  "Alles an einem    │
                    │      Ort."          │
                    └──────────┬──────────┘
                               │
         ┌─────────┬───────────┼───────────┬─────────┐
         │         │           │           │         │
         ▼         ▼           ▼           ▼         ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Human   │ │ Flying  │ │Envelopes│ │ Modules │
    │  Eyes   │ │  Tiers  │ │         │ │         │
    │   👁️    │ │   ✈️    │ │   📦    │ │   🧩    │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │           │
         │    "É seguro?"        │    "O que tem?"
         │           │           │           │
         └───────────┴───────────┴───────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  W-a4Desk   │
                  │   Editor    │
                  │     🛡️      │
                  └─────────────┘
```

---

## Audiências por Prateleira

| Prateleira | Tagline | Audiência | Consciência |
|------------|---------|-----------|-------------|
| **Human Eyes** | "Unterschreiben Sie nie wieder blind." | Clientes, investores | Emocional |
| **Flying Tiers** | "Flying High — Zero Turbulenz." | Controllers | Comercial |
| **Envelopes** | "Was steckt in jedem Umschlag?" | Compliance, DPO | Técnico |
| **Modules** | "Spezialisierte Module" | Arquitetos, devs | Engenharia |

---

## Estatísticas do Sistema

- **6** Analyse-Schichten (SGE Layers)
- **9** Invarianten (I1-I9)
- **17** ISP Profile
- **3** Sprachen (DE/EN/PT)
- **0** Daten gespeichert (Zero-Knowledge)

---

## Princípio

```
KI verarbeitet. Mensch entscheidet. WINDI garantiert.

THREE DRAGONS PROTOCOL — Guardian · Architect · Witness — I1-I9 ACTIVE
```

---

*Generated: 2026-02-10*
*Version: 1.0.0*
