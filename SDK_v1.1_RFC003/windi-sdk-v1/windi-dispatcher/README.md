# WINDI Sovereign Dispatcher v1.0
## Integration Guide for Day-by-Day Server

### Quick Integration

Add these lines to your `day-by-day-server.js`:

```javascript
// After your existing routes, add:
const dispatchRoute = require("../dispatcher/dispatch-route");
app.use("/api", dispatchRoute);
```

This gives you three new endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dispatch` | Send briefing to one recipient |
| POST | `/api/dispatch/all` | Send to all whitelisted recipients |
| GET | `/api/dispatch/status` | View recent dispatch log |

### API Usage

```bash
# Single recipient
curl -X POST http://127.0.0.1:8090/api/dispatch \
  -H "Content-Type: application/json" \
  -d '{"recipient": "jober@windi.ai"}'

# All whitelisted recipients
curl -X POST http://127.0.0.1:8090/api/dispatch/all

# Check status
curl http://127.0.0.1:8090/api/dispatch/status
```

### File Structure

```
/opt/windi/
├── dispatcher/
│   ├── windi-dispatcher.js    # Core dispatch logic
│   ├── dispatch-route.js      # Express routes
│   ├── run.js                 # Cron runner
│   ├── test-dispatch.js       # Test suite
│   ├── deploy.sh              # Deploy script
│   ├── .env.example           # Config template
│   └── package.json
└── SDK_v1.1_RFC003/
    └── windi-sdk-v1/
        └── day-by-day-server.js  # Mount dispatch-route here
```

### Cron Schedule

```
# /etc/crontab or crontab -e
# 09:00 CET weekdays (08:00 UTC in winter)
0 8 * * 1-5 cd /opt/windi/dispatcher && node run.js >> /var/log/windi-dispatch.log 2>&1
```

### Security Checklist

- [ ] `.env` has SMTP credentials (never commit!)
- [ ] `WINDI_RECIPIENTS` whitelist populated
- [ ] SMTP uses port 465 with `secure: true`
- [ ] Forensic headers (X-WINDI-*) verified in test email
- [ ] Ledger endpoint logging dispatch events

### Three Dragons Protocol

- **Guardian (Claude)**: Built the Dispatcher
- **Witness (Gemini)**: Certified the architecture
- **Architect (GPT)**: Designed the flow

*AI processes. Human decides. WINDI guarantees.* 🐉
