#!/usr/bin/env python3
"""
WINDI Session Cookie Manager
Soberania operacional entre sessões.

Uso:
  python3 cookie-manager.py read              → mostra estado actual
  python3 cookie-manager.py update <json>     → actualiza campos
  python3 cookie-manager.py done §103 abc1234 → marca § como done
  python3 cookie-manager.py progress §113 "status" → adiciona/actualiza in_progress
  python3 cookie-manager.py note "texto"      → actualiza nota
  python3 cookie-manager.py seal              → snapshot + seal no Ledger

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
"""

import json
import sys
import hashlib
import shutil
import requests
from datetime import datetime, timezone
from pathlib import Path

COOKIE_PATH = Path("/opt/windi/session/windi-cookie.json")
HISTORY_DIR = Path("/opt/windi/session/cookie-history")
LEDGER_URL = "http://localhost:8101/api/receipts"


def load():
    """Load cookie from disk."""
    COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    if not COOKIE_PATH.exists():
        return {}
    return json.loads(COOKIE_PATH.read_text())


def save(data):
    """Save cookie to disk with updated timestamp."""
    data.setdefault("meta", {})
    data["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["meta"]["updated_by"] = "gemeo"
    COOKIE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"✅ Cookie actualizado: {COOKIE_PATH}")


def cmd_read():
    """Display current cookie state."""
    data = load()
    if not data:
        print("❌ Cookie vazio — inicializa com update ou cria manualmente")
        return

    meta = data.get("meta", {})
    sprint = data.get("sprint", {})
    paras = data.get("paragraphs", {})
    pending_commits = data.get("pending_commits", [])
    pending_seals = data.get("pending_seals", [])
    decisions = data.get("decisions", [])
    blockers = data.get("blockers", [])
    notes = data.get("notes", "")
    context = data.get("context", {})

    print()
    print("=" * 60)
    print(f"🐉 WINDI Session Cookie — Sprint {sprint.get('current', '?')}")
    print("=" * 60)
    print(f"   Produto  : {sprint.get('product', '?')}")
    print(f"   Princípio: {sprint.get('principle', '?')}")
    print(f"   Session  : {meta.get('session_id', 'N/A')}")
    print(f"   Updated  : {meta.get('updated_at', '?')[:19] if meta.get('updated_at') else '?'}")

    # Done
    done = paras.get("done", [])
    print(f"\n✅ DONE ({len(done)}):")
    for p in done[-5:]:  # Show last 5
        sealed = "🔒" if p.get("sealed") else "⏳"
        print(f"   {sealed} {p['id']} {p.get('name', '')} — {p.get('commit', '')[:7] if p.get('commit') else ''}")
    if len(done) > 5:
        print(f"   ... e mais {len(done) - 5}")

    # In Progress
    in_prog = paras.get("in_progress", [])
    print(f"\n⏳ IN PROGRESS ({len(in_prog)}):")
    for p in in_prog:
        print(f"   → {p['id']} {p.get('name', '')} — {p.get('status', '')}")

    # Next
    next_items = paras.get("next", [])
    if next_items:
        print(f"\n📋 NEXT ({len(next_items)}):")
        for p in next_items[:3]:
            print(f"   ○ {p['id']} {p.get('name', '')} — {p.get('status', '')}")

    # Pending commits
    if pending_commits:
        print(f"\n📦 PENDING COMMITS ({len(pending_commits)}):")
        for c in pending_commits:
            print(f"   → {c}")

    # Pending seals
    if pending_seals:
        print(f"\n🔐 PENDING SEALS ({len(pending_seals)}):")
        for s in pending_seals:
            print(f"   → {s}")

    # Decisions (last 3)
    if decisions:
        print(f"\n🎯 DECISÕES RECENTES ({len(decisions)}):")
        for d in decisions[-3:]:
            print(f"   D{d.get('id', '?')}: {d.get('topic', '')} → {d.get('decision', '')[:50]}")

    # Blockers
    if blockers:
        print(f"\n🚫 BLOCKERS ({len(blockers)}):")
        for b in blockers:
            print(f"   ❌ {b}")

    # Context
    if context:
        print(f"\n🔧 CONTEXT:")
        if context.get("last_working_file"):
            print(f"   Último ficheiro: {context['last_working_file']}")
        if context.get("last_test"):
            print(f"   Último teste: {context['last_test'][:60]}")

    # Notes
    if notes:
        print(f"\n📝 NOTA: {notes}")

    print()
    print("=" * 60)
    print()


def cmd_done(para_id, commit_hash):
    """Mark a paragraph as done."""
    data = load()
    paras = data.setdefault("paragraphs", {})
    in_prog = paras.get("in_progress", [])

    # Find item in in_progress or create new
    item = next((p for p in in_prog if p["id"] == para_id), None)
    if not item:
        item = {"id": para_id, "name": para_id}

    item["commit"] = commit_hash
    item["sealed"] = False
    item["done_at"] = datetime.now(timezone.utc).isoformat()[:10]

    # Move to done
    paras.setdefault("done", []).append(item)
    paras["in_progress"] = [p for p in in_prog if p["id"] != para_id]

    # Remove from pending commits
    data["pending_commits"] = [
        c for c in data.get("pending_commits", [])
        if para_id not in c
    ]

    save(data)
    print(f"✅ {para_id} marcado como DONE — commit {commit_hash[:7]}")


def cmd_progress(para_id, name_or_status):
    """Add or update item in in_progress."""
    data = load()
    paras = data.setdefault("paragraphs", {})
    in_prog = paras.setdefault("in_progress", [])

    # Find existing or create new
    item = next((p for p in in_prog if p["id"] == para_id), None)
    if item:
        item["status"] = name_or_status
    else:
        in_prog.append({
            "id": para_id,
            "name": para_id,
            "status": name_or_status
        })

    save(data)
    print(f"⏳ {para_id} actualizado em IN_PROGRESS")


def cmd_note(text):
    """Update the notes field."""
    data = load()
    data["notes"] = text
    save(data)
    print(f"📝 Nota actualizada")


def cmd_decision(topic, decision, reason):
    """Add a decision."""
    data = load()
    decisions = data.setdefault("decisions", [])

    # Generate ID
    next_id = len(decisions) + 1

    decisions.append({
        "id": f"{next_id:03d}",
        "topic": topic,
        "decision": decision,
        "reason": reason,
        "date": datetime.now(timezone.utc).isoformat()[:10]
    })

    save(data)
    print(f"🎯 Decisão D{next_id:03d} registada")


def cmd_seal():
    """Create snapshot and seal in Ledger."""
    data = load()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    sid = f"SESSION-{ts}"

    # Snapshot local
    snap = HISTORY_DIR / f"cookie-{ts}.json"
    shutil.copy(COOKIE_PATH, snap)

    # Hash do snapshot
    content = snap.read_text()
    h = hashlib.sha256(content.encode()).hexdigest()

    # Seal no Ledger
    receipt = {
        "id": f"WINDI-COOKIE-{ts}",
        "actor": "gemeo",
        "app": "windi-session",
        "doc_name": f"Session Cookie Snapshot {sid}",
        "doc_type": "doc",
        "governance_level": "MEDIUM",
        "metadata": {
            "sprint": data.get("sprint", {}).get("current"),
            "done": len(data.get("paragraphs", {}).get("done", [])),
            "in_progress": len(data.get("paragraphs", {}).get("in_progress", [])),
            "snapshot": str(snap),
            "hash": h
        }
    }

    try:
        r = requests.post(LEDGER_URL, json=receipt, timeout=5)
        if r.status_code in (200, 201):
            receipt_id = r.json().get("id", "?")
            print(f"🔒 Selado no Ledger: {receipt_id}")

            # Mark recent done items as sealed
            for p in data.get("paragraphs", {}).get("done", []):
                if not p.get("sealed"):
                    p["sealed"] = True
        else:
            print(f"⚠️  Ledger respondeu {r.status_code}")
    except Exception as e:
        print(f"⚠️  Ledger indisponível: {e}")

    # Update session_id
    data["meta"]["session_id"] = sid
    save(data)

    print(f"📸 Snapshot: {snap}")
    print(f"🔑 SHA-256:  {h[:16]}…")


def cmd_context(key, value):
    """Update context field."""
    data = load()
    ctx = data.setdefault("context", {})
    ctx[key] = value
    save(data)
    print(f"🔧 Context[{key}] actualizado")


def cmd_help():
    """Show help."""
    print("""
WINDI Session Cookie Manager
=============================

Comandos:
  read                          Mostra estado actual
  done §ID COMMIT               Marca § como concluído
  progress §ID "status"         Adiciona/actualiza in_progress
  note "texto"                  Actualiza nota
  decision "topic" "dec" "why"  Regista decisão
  context KEY VALUE             Actualiza context
  seal                          Snapshot + seal no Ledger

Exemplos:
  python3 cookie-manager.py read
  python3 cookie-manager.py done §103 abc1234
  python3 cookie-manager.py progress §114 "em desenvolvimento"
  python3 cookie-manager.py note "Focus: deploy §103"
  python3 cookie-manager.py seal
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_read()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "read":
        cmd_read()
    elif cmd == "done" and len(sys.argv) >= 4:
        cmd_done(sys.argv[2], sys.argv[3])
    elif cmd == "progress" and len(sys.argv) >= 4:
        cmd_progress(sys.argv[2], sys.argv[3])
    elif cmd == "note" and len(sys.argv) >= 3:
        cmd_note(sys.argv[2])
    elif cmd == "decision" and len(sys.argv) >= 5:
        cmd_decision(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "context" and len(sys.argv) >= 4:
        cmd_context(sys.argv[2], sys.argv[3])
    elif cmd == "seal":
        cmd_seal()
    elif cmd in ("help", "-h", "--help"):
        cmd_help()
    else:
        cmd_help()
