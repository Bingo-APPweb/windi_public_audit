import sqlite3
import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

WICK_DB = "/opt/windi/agents/constitutional-agent/data/wick_agent.db"
LEDGER_URL = "http://localhost:8101/api/receipts"

conn = sqlite3.connect(WICK_DB)
conn.row_factory = sqlite3.Row
artifacts = conn.execute(
    "SELECT id, title, type, author_actor_id, content_hash FROM artifacts WHERE visibility='public'"
).fetchall()
conn.close()

print(f"📦 {len(artifacts)} artifacts públicos encontrados\n")

ok, fail = 0, 0
for a in artifacts:
    payload = json.dumps({
        "id": a["id"],
        "doc_name": a["title"] or a["id"],
        "doc_type": a["type"] if a["type"] in ["doc","xlsx","pptx","jmpg","communique"] else "doc",
        "actor": a["author_actor_id"] or "windi-wick",
        "app": "windi-wick",
        "governance_level": "HIGH",
        "content_hash": a["content_hash"] or "0000000000000000000000000000000000000000000000000000000000000000",
        "sge_score": 0.95,
        "metadata": {"source": "wick-resync"}
    }).encode("utf-8")
    try:
        req = urllib.request.Request(LEDGER_URL, data=payload,
              headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print(f"  ✅ {a['id']} — {a['title'] or '(sem título)'}")
                ok += 1
            else:
                print(f"  ⚠️  {a['id']} — {result.get('error','?')}")
                fail += 1
    except Exception as e:
        print(f"  ❌ {a['id']} — {e}")
        fail += 1

print(f"\n{'═'*50}")
print(f"✅ Sincronizados: {ok}  ❌ Falhas: {fail}")
