# WINDI Marketplace — Route Map

## Nginx Configuration (Strato)

```
clone.windia4desk.tech
├── /marketplace   → windi-marketplace-index.html   (Portal Central)
├── /human-eyes    → windi-human-eyes.html          (Safety messaging)
├── /flying        → windi-flying-tiers.html        (Pricing tiers)
├── /envelopes     → windi-envelopes-content.html   (Feature details)
├── /modules       → windi-clone-modules.html       (Module catalog)
└── /              → proxy:8092                     (W-a4Desk Editor)
```

---

## Route ↔ File Mapping

| Rota | Arquivo | Tamanho | Público |
|------|---------|---------|---------|
| `/marketplace` | `windi-marketplace-index.html` | 18 KB | Todos |
| `/human-eyes` | `windi-human-eyes.html` | 28 KB | Clientes, Investores |
| `/flying` | `windi-flying-tiers.html` | 32 KB | Controllers |
| `/envelopes` | `windi-envelopes-content.html` | 32 KB | Compliance, DPO |
| `/modules` | `windi-clone-modules.html` | 18 KB | Tech-Teams |

---

## Arquivos Servidos

```
/opt/windi/a4desk-editor/static/
├── windi-marketplace-index.html    ← Portal Central
├── windi-human-eyes.html           ← Human Eyes
├── windi-flying-tiers.html         ← Flying Tiers
├── windi-envelopes-content.html    ← Envelopes
├── windi-clone-modules.html        ← Modules
│
├── inside-the-envelopes.html       ← (Alternative envelopes)
├── marketplace.html                ← (Full technical catalog)
└── ... (outros dashboards)
```

---

## Nginx Config Completo

```nginx
server {
    server_name clone.windia4desk.tech;

    # WINDI Marketplace Index
    location = /marketplace {
        types { } default_type "text/html; charset=utf-8";
        alias /opt/windi/a4desk-editor/static/windi-marketplace-index.html;
    }

    # WINDI Marketplace Pages
    location = /human-eyes {
        types { } default_type "text/html; charset=utf-8";
        alias /opt/windi/a4desk-editor/static/windi-human-eyes.html;
    }
    location = /flying {
        types { } default_type "text/html; charset=utf-8";
        alias /opt/windi/a4desk-editor/static/windi-flying-tiers.html;
    }
    location = /envelopes {
        types { } default_type "text/html; charset=utf-8";
        alias /opt/windi/a4desk-editor/static/windi-envelopes-content.html;
    }
    location = /modules {
        types { } default_type "text/html; charset=utf-8";
        alias /opt/windi/a4desk-editor/static/windi-clone-modules.html;
    }

    # W-a4Desk Editor (Sanctuary)
    location / {
        proxy_pass http://127.0.0.1:8092;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # SSL (Certbot managed)
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/clone.windia4desk.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clone.windia4desk.tech/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    # HTTP → HTTPS redirect
    listen 80;
    server_name clone.windia4desk.tech;
    return 301 https://$host$request_uri;
}
```

---

## Fluxo de Navegação

```
         https://clone.windia4desk.tech/marketplace
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    /human-eyes      /flying         /envelopes        /modules
         │                │                │                │
         │    👁️ Safety   │   ✈️ Pricing   │   📦 Features  │   🧩 Tech
         │                │                │                │
         └────────────────┴────────────────┴────────────────┘
                                   │
                                   ▼
                    https://clone.windia4desk.tech/
                           W-a4Desk Editor
                            (proxy:8092)
```

---

## URLs Finais

```
https://clone.windia4desk.tech/marketplace   ← Portal Central
https://clone.windia4desk.tech/human-eyes    ← Human Eyes
https://clone.windia4desk.tech/flying        ← Flying Tiers
https://clone.windia4desk.tech/envelopes     ← Envelopes
https://clone.windia4desk.tech/modules       ← Modules
https://clone.windia4desk.tech/              ← W-a4Desk Editor
```

---

## Deploy Commands (Strato)

```bash
# 1. Copy files to server
scp /opt/windi/a4desk-editor/static/windi-*.html strato:/opt/windi/a4desk-editor/static/

# 2. Apply nginx config
sudo nginx -t && sudo systemctl reload nginx

# 3. Verify routes
curl -I https://clone.windia4desk.tech/marketplace
curl -I https://clone.windia4desk.tech/human-eyes
curl -I https://clone.windia4desk.tech/flying
curl -I https://clone.windia4desk.tech/envelopes
curl -I https://clone.windia4desk.tech/modules
```

---

*Generated: 2026-02-10*
*Nginx Config: clone.windia4desk.tech*
