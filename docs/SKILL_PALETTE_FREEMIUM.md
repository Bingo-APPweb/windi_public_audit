# Palette Freemium Quick Reference

## Endpoints
- POST /api/dragon/render → signed download URL + ledger_status
- GET /api/dragon/download/{file}?token=X&expires=Y
- GET /api/dragon/quota/status
- POST /api/dragon/quota/check
- GET /api/dragon/renderer/health

## Tiers: ANON(3/d,pdf+docx) | FREE(10/d,all) | PRO(200/d,all)

## Files: renderer/{render_api,render_engine,quota_engine,download_security,ledger_sync,spec_sanitizer}.py

## Deploy Pattern: Claude gera .sh → SCP → bash /tmp/faseN.sh

## Restart: kill $(ss -tlnp|grep 8108|grep -oP 'pid=\K\d+'); sleep 2; cd /opt/windi/agent-palette; nohup python3 agent_dragon_server.py > /tmp/dragon_debug.log 2>&1 &

## Smoke: curl -s -X POST localhost:8108/api/dragon/render -H "Content-Type: application/json" -d '{"text":"# Test","intent":{"doc_type":"memo"},"tier":"FREE"}' | python3 -m json.tool
