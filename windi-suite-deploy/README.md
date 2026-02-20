# WINDI Desktop — Deployment Package

**Wallet → Desktop → Suite · Sealing · War Room**

## Architecture

```
admin.windia4desk.tech
│
├── /              ← Wallet "O Espelho" (port 8099)
│                     [Abrir Desktop →]
│
└── /desktop/      ← WINDI Desktop (port 8100) ★ NEW
    ├── index.html      Landing page
    ├── suite.html      Guten Tag — Suite demo
    ├── sealing.html    Sealing Ritual
    ├── warroom.html    War Room — Controller dashboard
    └── pitch/
        └── WINDI_Suite_Pitch_Deck.pptx
```

## Deploy (3 commands)

```bash
scp -r windi-suite-deploy/ windi@87.106.29.233:/opt/windi/
ssh windi@87.106.29.233
bash /opt/windi/windi-suite-deploy/deploy.sh
```

## After Deploy

Update Wallet to link to Desktop:
```bash
bash /opt/windi/windi-suite-deploy/update-wallet.sh
```

## URLs

| Page | URL |
|------|-----|
| Wallet | https://admin.windia4desk.tech/ |
| Desktop | https://admin.windia4desk.tech/desktop/ |
| Suite | https://admin.windia4desk.tech/desktop/suite.html |
| Sealing | https://admin.windia4desk.tech/desktop/sealing.html |
| War Room | https://admin.windia4desk.tech/desktop/warroom.html |
| Health | https://admin.windia4desk.tech/desktop/health |
| Pitch | https://admin.windia4desk.tech/desktop/pitch/WINDI_Suite_Pitch_Deck.pptx |

## Service

```bash
sudo systemctl status windi-desktop
sudo systemctl restart windi-desktop
tail -f /opt/windi/logs/desktop.log
```

## Specs

- **Port:** 8100
- **Service:** windi-desktop (systemd)
- **Directory:** /opt/windi/desktop/
- **Access:** Public
- **Server:** Python HTTP with /health endpoint

---

*16. Feb 2026 — AI processes. Human decides. WINDI guarantees.*
